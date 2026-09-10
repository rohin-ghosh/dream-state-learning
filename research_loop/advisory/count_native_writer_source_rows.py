#!/usr/bin/env python3
"""Read-only feasibility counter for native-writer source rows.

The ledger is an append-only *physical* stream, but remote/local collection
can put a thought after its act (or interleave programs). This extractor
therefore reads the closed prefix first, assigns occurrence IDs, indexes acts,
and only then joins thoughts to acts. It emits no training corpus and grants
no run authority.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


WAKE_RE = re.compile(r"wake_(\d+)_(\d+)\.json$")
# The legacy floor intentionally differs from the permissive exploratory
# parser: colon is required and the marker must begin at column zero.
PREDICT_RE = re.compile(r"^PREDICT:(.*)$", re.MULTILINE)
ACT_RE = re.compile(r"^ACT:(.*)$", re.MULTILINE)
OUTCOME_RE = re.compile(
    r"^instructions ([0-9]+) -> ([0-9]+)(?: \([^\n]*\))?$"
)

# Do not treat arbitrary row/model digests as executable-source receipts.
SOURCE_CODE_HASH_FIELDS = (
    "source_code_sha256", "source_code_hash", "writer_source_sha256",
    "writer_source_hash", "extractor_source_sha256", "extractor_source_hash",
)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def payload_digest(payload: str) -> str:
    """Stable action identity for histograms without emitting action text."""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def this_source_sha256() -> str:
    """Digest the extractor itself for local/remote provenance checks."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _source_hashes(row: dict[str, Any]) -> dict[str, set[str]]:
    found: dict[str, set[str]] = collections.defaultdict(set)
    containers: list[dict[str, Any]] = [row]
    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        containers.append(provenance)
    for container in containers:
        for field in SOURCE_CODE_HASH_FIELDS:
            value = container.get(field)
            if isinstance(value, dict):
                value = value.get("sha256") or value.get("hash")
            if value is not None and str(value).strip():
                found[field].add(str(value).strip())
    return dict(found)


def source_code_report(
    rows: list[dict[str, Any]], *, expected_extractor_sha256: str | None = None,
    current_extractor_sha256: str | None = None,
) -> dict[str, Any]:
    """Report extractor provenance and receipts without claiming ancestry.

    The current digest is this counter's source, not ``organism_v6.batch_loop``
    or any other runtime writer.  A row receipt is therefore only compared to
    another row receipt (or an explicitly supplied expected extractor digest),
    never blindly to this counter's digest.
    """
    current = current_extractor_sha256 or this_source_sha256()
    expected = expected_extractor_sha256.strip() if expected_extractor_sha256 else None
    observed: dict[str, set[str]] = collections.defaultdict(set)
    for row in rows:
        for field, values in _source_hashes(row).items():
            observed[field].update(values)
    observed_values = sorted({value for values in observed.values() for value in values})
    conflicting_fields = {
        field: sorted(values)
        for field, values in observed.items()
        if len(values) > 1
    }
    expected_mismatch = expected is not None and current != expected
    return {
        "checked": bool(expected or observed_values),
        "drift": bool(conflicting_fields or expected_mismatch),
        "extractor_sha256": current,
        "expected_extractor_sha256": expected,
        "observed_source_receipts": observed_values,
        "conflicting_source_receipts": conflicting_fields,
    }


def manifest_occurrence_summaries(
    life: Path, boundary: int,
) -> tuple[dict[str, list[dict[str, int]]], list[dict]]:
    """Read wake summaries, including each occurrence's exact tick count."""
    files = []
    for path in life.glob("wake_*.json"):
        match = WAKE_RE.match(path.name)
        if match and int(match.group(2)) <= boundary:
            files.append((int(match.group(1)), int(match.group(2)), path))
    files.sort()
    cursor = 0
    by_program: dict[str, list[dict[str, int]]] = collections.defaultdict(list)
    receipts = []
    for start, end, path in files:
        if start != cursor or end <= start:
            raise ValueError(f"noncontiguous wake manifests at {path}")
        rows = json.loads(path.read_text())
        if len(rows) != end - start:
            raise ValueError(f"wake length mismatch at {path}")
        raw = path.read_bytes()
        receipts.append({"path": path.name, "sha256": hashlib.sha256(raw).hexdigest()})
        for ordinal, row in enumerate(rows, start):
            try:
                ticks = int(row["ticks"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"wake summary {path} lacks an integer ticks field"
                ) from exc
            if ticks < 1:
                raise ValueError(f"wake summary {path} has invalid ticks={ticks}")
            by_program[str(row["episode_id"])].append(
                {"manifest_ordinal": ordinal, "ticks": ticks}
            )
        cursor = end
    if cursor != boundary:
        raise ValueError(f"wake manifests stop at {cursor}, expected {boundary}")
    return dict(by_program), receipts


def manifest_occurrences(life: Path, boundary: int) -> tuple[dict[str, list[int]], list[dict]]:
    """Backward-compatible ordinal-only view of the wake summaries."""
    summaries, receipts = manifest_occurrence_summaries(life, boundary)
    return {
        program: [item["manifest_ordinal"] for item in items]
        for program, items in summaries.items()
    }, receipts


def read_ledger(life: Path) -> list[dict[str, Any]]:
    """Read once while retaining exact UTF-8 byte offsets."""
    rows: list[dict[str, Any]] = []
    with (life / "ledger.jsonl").open("rb") as handle:
        physical = 0
        while True:
            offset = handle.tell()
            raw = handle.readline()
            if not raw:
                break
            physical += 1
            if not raw.strip():
                continue
            try:
                row = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid ledger row at byte offset {offset}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"ledger row at byte offset {offset} is not an object")
            row = dict(row)
            row["_ledger_byte_offset"] = offset
            row["_ledger_physical_ordinal"] = physical - 1
            rows.append(row)
    return rows


def _row_tick(row: dict[str, Any]) -> int:
    try:
        return int(row.get("tick", -1))
    except (TypeError, ValueError) as exc:
        raise ValueError("act/thought tick must be an integer") from exc


def _assign_occurrences_from_wake_summaries(
    rows: list[dict[str, Any]],
    summaries: dict[str, list[dict[str, int]]],
    boundary: int,
) -> dict[tuple[str, int], int]:
    """Segment thoughts using wake ``ticks`` and attach acts by nearest thought.

    Tick-reset inference is invalid for consecutive one-tick episodes. Wake
    summaries are the segmentation oracle: each occurrence consumes exactly
    its declared number of ordered thought rows, whose ticks must be exactly
    ``1..T``. Acts have no reliable occurrence marker, so they join to the
    unique nearest same-program/same-tick thought; ties are rejected.
    """
    thought_by_program: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in rows:
        row["_manifest_ordinal"] = boundary
        if row.get("kind") == "thought":
            thought_by_program[str(row.get("episode_id"))].append(row)
    occurrence_to_ordinal: dict[tuple[str, int], int] = {}
    all_thoughts_by_program_tick: dict[tuple[str, int], list[dict[str, Any]]] = collections.defaultdict(list)

    for program, occurrences in summaries.items():
        program_thoughts = sorted(
            thought_by_program.get(program, []),
            key=lambda item: item["_ledger_byte_offset"],
        )
        cursor = 0
        for local, summary in enumerate(occurrences):
            tick_count = summary["ticks"]
            segment = program_thoughts[cursor:cursor + tick_count]
            expected_ticks = list(range(1, tick_count + 1))
            actual_ticks = [_row_tick(row) for row in segment]
            if len(segment) != tick_count or actual_ticks != expected_ticks:
                raise ValueError(
                    f"thought segmentation mismatch for {program} occurrence {local}: "
                    f"expected ticks {expected_ticks}, got {actual_ticks}"
                )
            manifest_ordinal = summary["manifest_ordinal"]
            occurrence_to_ordinal[(program, local)] = manifest_ordinal
            for row in segment:
                row["_occurrence"] = local
                row["_manifest_ordinal"] = manifest_ordinal
                all_thoughts_by_program_tick[(program, _row_tick(row))].append(row)
            cursor += tick_count
        # Rows after the closed prefix belong to later occurrences and stay
        # outside the source snapshot; they are never counted as candidates.

        for row in program_thoughts[cursor:]:
            all_thoughts_by_program_tick[(program, _row_tick(row))].append(row)

    # Associate acts only after all thought occurrences are known. A physical
    # reorder is tolerated when it leaves one nearest thought. Consecutive
    # one-tick episodes can produce an exact distance tie (T0,A0,T1,A1 or
    # A0,T0,A1,T1); resolve such ties only when another unambiguous act in the
    # same program establishes the before/after adjacency orientation.
    pending: list[tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]] = []
    orientation: dict[str, str] = {}
    for row in rows:
        if row.get("kind") != "act":
            continue
        program = str(row.get("episode_id"))
        candidates = all_thoughts_by_program_tick.get((program, _row_tick(row)), [])
        if not candidates:
            continue
        distances = [
            abs(row["_ledger_physical_ordinal"] - thought["_ledger_physical_ordinal"])
            for thought in candidates
        ]
        nearest = min(distances)
        nearest_rows = [thought for thought, distance in zip(candidates, distances)
                        if distance == nearest]
        pending.append((row, candidates, nearest_rows))
        if len(nearest_rows) == 1:
            thought = nearest_rows[0]
            if thought.get("_manifest_ordinal", boundary) < boundary:
                side = "before" if row["_ledger_physical_ordinal"] < thought["_ledger_physical_ordinal"] else "after"
                prior = orientation.get(program)
                if prior is not None and prior != side:
                    raise ValueError(f"inconsistent act/thought adjacency for {program}")
                orientation[program] = side

    for row, candidates, nearest_rows in pending:
        program = str(row.get("episode_id"))
        thought = nearest_rows[0] if len(nearest_rows) == 1 else None
        if thought is None:
            side = orientation.get(program)
            if side is None:
                raise ValueError(
                    f"ambiguous act association for {program} tick {_row_tick(row)}"
                )
            if side == "before":
                following = [candidate for candidate in nearest_rows
                             if candidate["_ledger_physical_ordinal"] > row["_ledger_physical_ordinal"]]
                if len(following) != 1:
                    raise ValueError(
                        f"ambiguous act association for {program} tick {_row_tick(row)}"
                    )
                thought = following[0]
            else:
                preceding = [candidate for candidate in nearest_rows
                              if candidate["_ledger_physical_ordinal"] < row["_ledger_physical_ordinal"]]
                if len(preceding) != 1:
                    raise ValueError(
                        f"ambiguous act association for {program} tick {_row_tick(row)}"
                    )
                thought = preceding[0]
        if thought.get("_manifest_ordinal", boundary) >= boundary:
            # This act belongs to an occurrence after the closed prefix.
            continue
        row["_occurrence"] = thought["_occurrence"]
        row["_manifest_ordinal"] = thought["_manifest_ordinal"]
    return occurrence_to_ordinal


def _typed_key(row: dict[str, Any]) -> tuple[int, str, int]:
    try:
        tick = int(row.get("tick", -1))
    except (TypeError, ValueError) as exc:
        raise ValueError("act/thought tick must be an integer") from exc
    return (int(row["_occurrence"]), str(row.get("episode_id")), tick)


def _validate_act_outcome(row: dict[str, Any]) -> tuple[str | None, float | None]:
    """Validate the independent outcome/score fields for one act row."""
    outcome = row.get("outcome")
    if not isinstance(outcome, str):
        return "invalid_outcome", None
    match = OUTCOME_RE.fullmatch(outcome)
    if match is None:
        return "invalid_outcome", None
    i0, i1 = int(match.group(1)), int(match.group(2))
    if i0 <= 0 or i1 < 0:
        return "invalid_outcome", None
    raw_score = row.get("score")
    if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
        return "invalid_score", None
    score = float(raw_score)
    if not math.isfinite(score):
        return "invalid_score", None
    expected = (i0 - i1) / i0
    if abs(score - expected) > 1e-12:
        return "score_mismatch", None
    return None, score


def _strict_note(note: object) -> tuple[str | None, bytes | None, str | None]:
    """Parse the exact legacy continuation markers without normalization."""
    if not isinstance(note, str) or not note:
        return None, None, "invalid_note"
    try:
        target = note.encode("utf-8")
    except UnicodeEncodeError:
        return None, None, "invalid_utf8"
    if len(target) >= 2000:
        return None, None, "utf8_cap"
    predictions = list(PREDICT_RE.finditer(note))
    actions = list(ACT_RE.finditer(note))
    if len(predictions) != 1 or len(actions) != 1:
        return None, None, "marker_count"
    if predictions[0].start() >= actions[0].start():
        return None, None, "marker_order"
    payload = actions[0].group(1)
    # Remove the literal marker and at most one ASCII space. Preserve every
    # remaining byte, including trailing spaces.
    if payload.startswith(" "):
        payload = payload[1:]
    if not payload:
        return None, None, "empty_act_payload"
    return payload, target, None


def _legacy_feasibility(
    rows: list[dict[str, Any]],
    acts: dict[tuple[int, str, int], list[dict[str, Any]]],
    boundary: int,
) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    """Apply the exact legacy floor and return counts, never row text."""
    reasons = collections.Counter()
    candidates_by_row: dict[int, dict[str, Any]] = {}
    raw_count = 0
    unique_by_hash: dict[str, dict[str, Any]] = {}
    for row in sorted(rows, key=lambda item: item["_ledger_byte_offset"]):
        if row.get("kind") != "thought":
            continue
        if row.get("_manifest_ordinal", boundary) >= boundary:
            continue
        row_id = row["_ledger_byte_offset"]
        payload, target, reason = _strict_note(row.get("note"))
        if reason:
            reasons[reason] += 1
            continue
        key = _typed_key(row)
        matched = acts.get(key, [])
        if len(matched) != 1:
            reasons["not_one_associated_act"] += 1
            continue
        act = matched[0]
        if act.get("valid_reason") is not None:
            reasons[str(act["valid_reason"])] += 1
            continue
        if not isinstance(act.get("action"), str) or payload != act["action"]:
            reasons["action_payload_mismatch"] += 1
            continue
        score = float(act["score_value"])
        if score <= float(act["best_before"]) + 1e-12:
            reasons["not_best_improvement"] += 1
            continue
        raw_count += 1
        record = {
            "row_id": row_id,
            "act_ledger_byte_offset": act["ledger_byte_offset"],
            "target": target,
            "target_sha256": hashlib.sha256(target).hexdigest(),
            "payload": payload,
            "score": score,
        }
        candidates_by_row[row_id] = record
        unique_by_hash.setdefault(record["target_sha256"], record)

    unique = list(unique_by_hash.values())
    payload_counts = collections.Counter(item["payload"] for item in unique)
    unique_count = len(unique)
    return {
        "qualifying_raw_count": raw_count,
        "unique_continuation_count": unique_count,
        "total_utf8_bytes": sum(len(item["target"]) for item in unique),
        "distinct_act_payloads": len(payload_counts),
        "max_payload_share": (
            max(payload_counts.values()) / unique_count if unique_count else 0.0
        ),
        "exclusion_reason_histogram": dict(sorted(reasons.items())),
    }, candidates_by_row


def inspect_life(
    life: Path, boundary: int, *, expected_extractor_sha256: str | None = None,
    current_extractor_sha256: str | None = None,
) -> dict:
    summaries, wake_receipts = manifest_occurrence_summaries(life, boundary)
    rows = read_ledger(life)
    occurrence_to_ordinal = _assign_occurrences_from_wake_summaries(
        rows, summaries, boundary
    )
    source_report = source_code_report(
        rows, expected_extractor_sha256=expected_extractor_sha256,
        current_extractor_sha256=current_extractor_sha256,
    )
    thought_rows = [
        row for row in rows
        if row.get("kind") == "thought"
        and row.get("_manifest_ordinal", boundary) < boundary
    ]
    prompt_present = sum("prompt" in row for row in thought_rows)
    prompt_absent = len(thought_rows) - prompt_present
    # The current batch writer is supposed to persist prompt bytes.  Missing
    # prompts are therefore a runtime/source-schema drift signal, not an
    # invitation to reconstruct C3 context from another file.
    source_report["prompt_present"] = prompt_present
    source_report["prompt_absent"] = prompt_absent
    source_report["runtime_schema_drift"] = bool(prompt_absent)

    occurrence_mapping = [
        {
            "program": program,
            "local_occurrence_ordinal": local,
            "manifest_ordinal": ordinal,
        }
        for (program, local), ordinal in sorted(occurrence_to_ordinal.items())
    ]

    acts: dict[tuple[int, str, int], list[dict[str, Any]]] = collections.defaultdict(list)
    action_histogram = collections.Counter()
    candidate_action_histogram = collections.Counter()
    # Pass 1: collect every act, including acts physically after their thought.
    for row in sorted(rows, key=lambda item: item["_ledger_byte_offset"]):
        if row.get("kind") != "act":
            continue
        program = str(row.get("episode_id"))
        if row.get("_manifest_ordinal", boundary) >= boundary:
            continue
        copy = dict(row)
        copy["ledger_byte_offset"] = row["_ledger_byte_offset"]
        acts[_typed_key(row)].append(copy)
        action = row.get("action")
        if isinstance(action, str):
            action_histogram[payload_digest(action)] += 1
        else:
            action_histogram["<non_string>"] += 1

    # Pass 2a: compute best-before in physical ledger order, before thoughts.
    best = collections.defaultdict(float)
    for key in sorted(acts, key=lambda item: acts[item][0]["ledger_byte_offset"]):
        for act in acts[key]:
            valid_reason, score = _validate_act_outcome(act)
            act["valid_reason"] = valid_reason
            act["score_value"] = score
            if valid_reason is not None:
                act["best_before"] = best[(key[0], key[1])]
                continue
            prior = best[(key[0], key[1])]
            act["best_before"] = prior
            best[(key[0], key[1])] = max(prior, float(score))

    legacy, legacy_candidates = _legacy_feasibility(rows, acts, boundary)

    counts = collections.Counter()
    selected = []
    mismatch_examples = []
    # Pass 2b: join exact candidates against the prompt-required gate. The
    # separate legacy feasibility pass above never authorizes training rows.
    for row in sorted(rows, key=lambda item: item["_ledger_byte_offset"]):
        if row.get("kind") != "thought":
            continue
        program = str(row.get("episode_id"))
        manifest_ordinal = row.get("_manifest_ordinal", boundary)
        if manifest_ordinal >= boundary:
            continue
        # Rows outside the closed prefix intentionally have no occurrence
        # assignment; never infer one merely to inspect or count them.
        if "_occurrence" not in row:
            raise ValueError(f"prefix thought lacks occurrence for {program}")
        occurrence = int(row["_occurrence"])
        key = _typed_key(row)
        counts["thought_rows"] += 1
        prompt_is_present = "prompt" in row
        if prompt_is_present:
            counts["prompt_present"] += 1
        else:
            counts["prompt_absent"] += 1
        candidate = legacy_candidates.get(row["_ledger_byte_offset"])
        if candidate is None:
            continue
        candidate_action_histogram[payload_digest(candidate["payload"])] += 1
        note = row.get("note") if isinstance(row.get("note"), str) else ""
        prompt = row.get("prompt") if isinstance(row.get("prompt"), str) else ""
        # This is intentionally a separate, non-authorizing diagnostic for
        # continuation-only C1/C2 feasibility.  Authentic C3 eligibility
        # requires a persisted, nonempty prompt and never uses reconstruction.
        if not prompt_is_present or not prompt:
            counts["legacy_note_candidate"] += 1
            continue
        counts["eligible"] += 1
        selected.append({
            "life_id": life.name,
            "occurrence_ordinal": manifest_ordinal,
            "local_occurrence_ordinal": occurrence,
            "program": program,
            "tick": int(row.get("tick", -1)),
            "act_ordinal": 0,
            "thought_ledger_byte_offset": row["_ledger_byte_offset"],
            "act_ledger_byte_offset": candidate["act_ledger_byte_offset"],
            "prompt": prompt,
            "note": note,
            "action": candidate["payload"],
            "score": candidate["score"],
        })

    # Keep the gate visible even when no prompt-qualified row exists; a missing
    # key must not be mistaken for an uncomputed eligibility count.
    counts.setdefault("eligible", 0)
    counts.setdefault("legacy_note_candidate", 0)
    counts.setdefault("prompt_present", 0)
    counts.setdefault("prompt_absent", 0)
    return {
        "life_id": life.name,
        "boundary": boundary,
        "wake_manifests": wake_receipts,
        "source_code": source_report,
        "source_code_drift": source_report["drift"],
        "runtime_or_source_drift": bool(source_report["drift"] or prompt_absent),
        "occurrence_mapping": occurrence_mapping,
        "legacy_continuation": legacy,
        "counts": dict(sorted(counts.items())),
        "action_histogram": dict(sorted(action_histogram.items())),
        "candidate_action_histogram": dict(sorted(candidate_action_histogram.items())),
        "selected_snapshot_sha256": hashlib.sha256(canonical(selected)).hexdigest(),
        "selected_rows": len(selected),
        "mismatch_examples": mismatch_examples,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.home() / "v6_out")
    parser.add_argument("--boundary", type=int, default=256)
    parser.add_argument(
        "--expected-extractor-source-sha256",
        help="pre-sealed counter/extractor digest; mismatch is reported as drift",
    )
    parser.add_argument("--lives", nargs="*", default=[
        "L_B_seed0", "L_B_seed1", "L_B_seed2"
    ])
    args = parser.parse_args()
    current = this_source_sha256()
    lives = [inspect_life(
        args.root / name, args.boundary,
        expected_extractor_sha256=args.expected_extractor_source_sha256,
        current_extractor_sha256=current,
    ) for name in args.lives]
    observed = sorted({
        digest for life in lives for digest in life["source_code"]["observed_source_receipts"]
    })
    drift = any(life["source_code_drift"] for life in lives) or len(observed) > 1
    runtime_or_source_drift = any(
        life["runtime_or_source_drift"] for life in lives
    ) or len(observed) > 1
    action_histogram = collections.Counter()
    candidate_action_histogram = collections.Counter()
    for life in lives:
        action_histogram.update(life["action_histogram"])
        candidate_action_histogram.update(life["candidate_action_histogram"])
    print(json.dumps({
        "status": "READ_ONLY_FEASIBILITY_ONLY",
        "source_code": {
            "checked": bool(args.expected_extractor_source_sha256 or observed),
            "drift": drift,
            "extractor_sha256": current,
            "expected_extractor_sha256": args.expected_extractor_source_sha256,
            "observed_source_receipts": observed,
            "runtime_schema_drift": any(
                life["source_code"]["runtime_schema_drift"] for life in lives
            ),
        },
        "source_code_drift": drift,
        "runtime_or_source_drift": runtime_or_source_drift,
        "action_histogram": dict(sorted(action_histogram.items())),
        "candidate_action_histogram": dict(sorted(candidate_action_histogram.items())),
        "lives": lives,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
