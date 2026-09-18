"""Read-only parenting dynamics audit over existing R3/R4 life ledgers.

The report is deliberately descriptive. It asks whether a valid v3 parent
brief was actually displayed, whether the child's *executed* behavior changed
afterward, and whether the realized adapter has an effect when parent text is
absent. It does not estimate a causal parenting effect: the historical lives
were neither randomized nor cleanly withdrawn from parenting.

Usage:
  python -m organism_v6.parenting_dynamics --root ~/v6_out \
      --out ~/v6_out/parenting_dynamics.json
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import re
import statistics

from .parent_brief import REHEARSAL_TAIL, _NOTE, _RECALL, ritual_metrics


STOP = set(
    "the and for you your that this with what was were are will each every "
    "episode before after into then than them they have has had not but its "
    "own about when how why more most some any all one two just also very can "
    "could should would from onto over under between repeat repeating instead"
    .split()
)
DEFAULT_PARENT_GLOBS = ("R4_B_seed*",)
DEFAULT_CONTROL_GLOBS = ("R3_B_seed*",)
WINDOWS = {
    "direct_32": (0, 32),
    "after_one_sleep_32": (32, 64),
    "after_four_sleeps_32": (128, 160),
}
CHANGE_INTENT = re.compile(
    r"\b(change|switch|different|alternative|rethink|revise|try another|"
    r"new route|new approach|instead)\b", re.I
)
PROBE_ON = re.compile(r"^probe_ep(\d+)\.ledger\.jsonl$")
WAKE = re.compile(r"^wake_\d+_(\d+)\.json$")


def toks(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in STOP}


def _mean(xs):
    return statistics.mean(xs) if xs else None


def _jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if (a or b) else 1.0


def load_json(path: str) -> dict:
    return json.load(open(path)) if os.path.exists(path) else {}


def load_rows_path(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_rows(life: str) -> list[dict]:
    return load_rows_path(os.path.join(life, "ledger.jsonl"))


def nominal_exposure(life: str) -> int | None:
    ends = []
    for path in glob.glob(os.path.join(life, "wake_*.json")):
        match = WAKE.match(os.path.basename(path))
        if match:
            ends.append(int(match.group(1)))
    return max(ends) if ends else None


def episode_texts(rows: list[dict]) -> list[dict]:
    """Reconstruct repeated instances and attach authoritative action rows.

    The batched driver writes zero or more `act` rows immediately before the
    corresponding `thought` row. We buffer those rows by program/tick and
    attach them when that thought arrives. ACT-like prose is never treated as
    an executed action.
    """
    records = collections.OrderedDict()
    last_tick: dict[object, int] = {}
    instance = collections.Counter()
    pending = collections.defaultdict(list)
    for row in rows:
        kind = row.get("kind")
        eid = row.get("episode_id")
        try:
            tick = int(row.get("tick", 0))
        except (TypeError, ValueError):
            tick = 0
        if kind == "act":
            pending[(eid, tick)].append(row)
            continue
        if kind != "thought" or not row.get("note"):
            continue
        if eid not in last_tick or tick <= last_tick[eid]:
            instance[eid] += 1
        last_tick[eid] = tick
        key = (eid, instance[eid])
        rec = records.setdefault(
            key, {"episode_id": eid, "steps": [], "thought_rows": []}
        )
        rec["steps"].append({
            "tick": tick,
            "text": str(row["note"]),
            "prompt": str(row.get("prompt", "")),
            "acts": pending.pop((eid, tick), []),
        })
        rec["thought_rows"].append(row)
    out = []
    for rec in records.values():
        out.append({
            "episode_id": rec["episode_id"],
            "steps": rec["steps"],
            "text": "\n".join(step["text"] for step in rec["steps"]),
            "prompts": [step["prompt"] for step in rec["steps"]],
            "thought_rows": rec["thought_rows"],
            "acts": [act for step in rec["steps"] for act in step["acts"]],
        })
    return out


def first_note(text: str) -> str | None:
    notes = _NOTE.findall(text)
    return notes[0] if notes else None


def _intent_and_realization(episode: dict) -> tuple[bool, bool]:
    """Was change considered, then realized in a predicted executed action?"""
    intent = False
    realized = False
    previous_action = None
    for step in episode["steps"]:
        step_intent = bool(CHANGE_INTENT.search(step["text"]))
        intent = intent or step_intent
        for act in step["acts"]:
            action = str(act.get("action", "")).strip()
            if (step_intent and previous_action is not None and action and
                    action != previous_action and
                    isinstance(act.get("prediction"), (int, float))):
                realized = True
            if action:
                previous_action = action
    return intent, realized


def window_stats(episodes: list[dict], start: int, stop: int,
                 lesson_tokens: set[str]) -> dict:
    requested_start, requested_stop = max(0, start), max(0, stop)
    realized_stop = min(len(episodes), requested_stop)
    window = episodes[requested_start:realized_stop]
    first_acts, all_actions, preds, errors = [], [], [], []
    note_sets, overlaps, recalls = [], [], []
    best_scores, attempts, thought_rows, output_words = [], [], [], []
    switch_hits = switch_ops = intent_n = realized_n = 0
    n_with_note = 0
    for episode in window:
        executed = episode["acts"]
        actions = [str(r.get("action", "")).strip() for r in executed
                   if str(r.get("action", "")).strip()]
        if actions:
            first_acts.append(actions[0])
            all_actions.extend(actions)
        attempts.append(len(executed))
        scores = [float(r["score"]) for r in executed
                  if isinstance(r.get("score"), (int, float))]
        if scores:
            best_scores.append(max(scores))
        for row in executed:
            if isinstance(row.get("prediction"), (int, float)):
                preds.append(float(row["prediction"]))
                if isinstance(row.get("score"), (int, float)):
                    errors.append(abs(float(row["prediction"]) -
                                      float(row["score"])))
        running = float("-inf")
        for i, row in enumerate(executed[:-1]):
            score = row.get("score")
            if not isinstance(score, (int, float)):
                continue
            improved = float(score) > running
            running = max(running, float(score))
            if not improved:
                switch_ops += 1
                if row.get("action") != executed[i + 1].get("action"):
                    switch_hits += 1
        note = first_note(episode["text"])
        if note is not None:
            n_with_note += 1
            nt = toks(note)
            note_sets.append(nt)
            overlaps.append(len(nt & lesson_tokens))
        intent, realized = _intent_and_realization(episode)
        intent_n += int(intent)
        realized_n += int(realized)
        thought_rows.append(len(episode["thought_rows"]))
        output_words.append(len(re.findall(r"\S+", episode["text"])))
        recalls.extend(q.strip().lower() for q in _RECALL.findall(episode["text"]))
    modal = (collections.Counter(first_acts).most_common(1)[0][1] /
             len(first_acts)) if first_acts else None
    adjacent_j = [_jaccard(note_sets[i], note_sets[i + 1])
                  for i in range(len(note_sets) - 1)]
    n = len(window)
    lesson_n = len(lesson_tokens)
    return {
        "requested_start_episode_ordinal": requested_start,
        "requested_stop_episode_ordinal": requested_stop,
        "realized_start_episode_ordinal": min(requested_start, len(episodes)),
        "realized_stop_episode_ordinal": realized_stop,
        "n_episodes": n,
        "n_with_first_act": len(first_acts),
        "n_with_first_note": n_with_note,
        "modal_first_act_share": modal,
        "unique_first_act_fraction": (
            len(set(first_acts)) / len(first_acts) if first_acts else None
        ),
        "unique_executed_actions": len(set(all_actions)),
        "mean_attempts": _mean(attempts),
        "mean_best_score": _mean(best_scores),
        "prediction_sd": statistics.pstdev(preds) if len(preds) > 1 else None,
        "prediction_mae": _mean(errors),
        "switch_after_nonimprovement_rate": (
            switch_hits / switch_ops if switch_ops else None
        ),
        "thought_change_intent_rate": intent_n / n if n else None,
        "intent_realized_deviation_rate": realized_n / n if n else None,
        "realization_given_intent_rate": (
            realized_n / intent_n if intent_n else None
        ),
        "recall_rate": (sum(bool(_RECALL.findall(ep["text"])) for ep in window) /
                        n if n else None),
        "mean_thought_rows": _mean(thought_rows),
        "mean_approx_output_words": _mean(output_words),
        "first_note_adjacent_jaccard": _mean(adjacent_j),
        "rehearsal_rate_ge4_given_note": (
            sum(x >= 4 for x in overlaps) / len(overlaps) if overlaps else None
        ),
        "mean_lesson_token_recall_given_note": (
            _mean([x / lesson_n for x in overlaps])
            if overlaps and lesson_n else None
        ),
    }


DELTA_KEYS = (
    "modal_first_act_share", "unique_first_act_fraction",
    "mean_attempts", "mean_best_score", "prediction_sd", "prediction_mae",
    "switch_after_nonimprovement_rate", "thought_change_intent_rate",
    "intent_realized_deviation_rate", "realization_given_intent_rate",
    "recall_rate", "mean_thought_rows", "mean_approx_output_words",
    "first_note_adjacent_jaccard", "rehearsal_rate_ge4_given_note",
    "mean_lesson_token_recall_given_note",
)


def _delta(after: dict, before: dict, key: str):
    a, b = after.get(key), before.get(key)
    return None if a is None or b is None else a - b


def brief_rows(life: str) -> list[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(life, "sleep_*", "parent_brief.txt"))):
        sleep_dir = os.path.basename(os.path.dirname(path))
        try:
            sleep = int(sleep_dir.removeprefix("sleep_"))
        except ValueError:
            continue
        raw = open(path, "rb").read()
        text = raw.decode(errors="replace").strip()
        lesson = text.replace(REHEARSAL_TAIL.strip(), "").strip()
        meta_path = os.path.join(os.path.dirname(path), "parent_brief.json")
        meta = load_json(meta_path)
        prompt_version = str(meta.get("prompt_version") or "")
        leak_hits = meta.get("hits")
        stored_matches_meta = (
            isinstance(meta.get("text"), str) and
            text == meta["text"].strip()[:1900]
        )
        explicit_error = any(meta.get(k) for k in
                             ("error", "room_error", "fallback", "skipped"))
        valid = bool(
            os.path.exists(meta_path) and meta.get("intervened") is True and
            prompt_version.startswith("v3") and leak_hits == [] and
            stored_matches_meta and not explicit_error and
            len(toks(lesson)) >= 4
        )
        reasons = []
        if not os.path.exists(meta_path):
            reasons.append("missing_metadata")
        if meta.get("intervened") is not True:
            reasons.append("not_intervened")
        if not prompt_version.startswith("v3"):
            reasons.append("not_parent_prompt_v3")
        if leak_hits != []:
            reasons.append("missing_or_nonempty_leak_scan")
        if not stored_matches_meta:
            reasons.append("stored_text_metadata_mismatch")
        if explicit_error:
            reasons.append("explicit_parent_error_or_fallback")
        if len(toks(lesson)) < 4:
            reasons.append("not_substantive")
        out.append({
            "sleep": sleep,
            "path": path,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "text": text,
            "lesson_tokens": toks(lesson),
            "lesson_token_count": len(toks(lesson)),
            "valid": valid,
            "invalid_reasons": reasons,
            "intervened": meta.get("intervened"),
            "parent_metrics": meta.get("metrics", {}),
            "parent_prompt_version": prompt_version or None,
            "parent_model": meta.get("parent_model"),
            "leak_hits": leak_hits,
            "stored_text_matches_metadata": stored_matches_meta,
        })
    return out


def delivered_ordinals(episodes: list[dict], brief_text: str,
                       at_or_after: int = 0) -> list[int]:
    return [i for i, ep in enumerate(episodes)
            if i >= at_or_after and
            any(brief_text in prompt for prompt in ep["prompts"])]


def delivery_stats(episodes: list[dict], brief_text: str,
                   start: int, stop: int) -> dict:
    window = episodes[max(0, start):min(len(episodes), max(0, stop))]
    delivered = sum(any(brief_text in p for p in ep["prompts"]) for ep in window)
    return {
        "n_episodes": len(window),
        "n_episodes_with_exact_brief": delivered,
        "coverage": delivered / len(window) if window else None,
    }


def _adapter_write_status(life: str, at: int) -> str | None:
    adapter = os.path.join(life, f"sleep_{at:04d}", "adapter")
    if not os.path.isdir(adapter):
        return None
    if os.path.exists(os.path.join(adapter, "DONE")):
        return "committed"
    rejected = glob.glob(os.path.join(adapter, "REJECTED*"))
    if rejected:
        return os.path.basename(rejected[0])
    return "attempted_unresolved"


def _active_committed_adapter(life: str, at: int) -> int | None:
    committed = []
    for path in glob.glob(os.path.join(life, "sleep_*", "adapter", "DONE")):
        try:
            sleep = int(os.path.basename(os.path.dirname(os.path.dirname(path)))
                        .removeprefix("sleep_"))
        except ValueError:
            continue
        if sleep <= at:
            committed.append(sleep)
    return max(committed) if committed else None


def write_events(life: str, start: int, stop: int) -> dict:
    """Writes surrounding a half-open wake window [start, stop).

    A write at ``start`` is the adapter active during the window. A write at
    ``stop`` is trained after the window and can only affect the next one.
    Keeping the two boundaries separate prevents calling the direct post-brief
    wake a post-consolidation window.
    """
    attempted = committed = rejected = 0
    for path in glob.glob(os.path.join(life, "sleep_*")):
        try:
            at = int(os.path.basename(path).removeprefix("sleep_"))
        except ValueError:
            continue
        if not (start < at < stop):
            continue
        adapter = os.path.join(path, "adapter")
        if os.path.isdir(adapter):
            attempted += 1
            committed += int(os.path.exists(os.path.join(adapter, "DONE")))
            rejected += int(bool(glob.glob(os.path.join(adapter, "REJECTED*"))))
    return {
        "start_boundary_write_status": _adapter_write_status(life, start),
        "active_committed_adapter_sleep": _active_committed_adapter(life, start),
        "writes_completed_strictly_inside_window": {
            "attempted": attempted, "committed": committed,
            "rejected": rejected,
        },
        "write_after_window_at_stop_boundary": _adapter_write_status(life, stop),
    }


def _probe_mean(path: str):
    value = load_json(path).get("mean")
    return float(value) if isinstance(value, (int, float)) else None


def parent_absent_probe_pairs(life: str, brief_texts: list[str]) -> list[dict]:
    pairs = []
    for on_path in sorted(glob.glob(os.path.join(life, "probe_ep*.ledger.jsonl"))):
        match = PROBE_ON.match(os.path.basename(on_path))
        if not match:
            continue
        at = int(match.group(1))
        stem = os.path.join(life, f"probe_ep{at:04d}")
        off_path = stem + "_adapterOFF.ledger.jsonl"
        if not os.path.exists(off_path):
            continue
        on_eps = episode_texts(load_rows_path(on_path))
        off_eps = episode_texts(load_rows_path(off_path))
        on = window_stats(on_eps, 0, len(on_eps), set())
        off = window_stats(off_eps, 0, len(off_eps), set())
        prompts = [p for ep in on_eps + off_eps for p in ep["prompts"]]
        prompt_lower = "\n".join(prompts).lower()
        parent_markers = ("=== your parent", "[parent]", "parent brief")
        brief_needles = [needle for text in brief_texts if text
                         for needle in (text, text[:80] if len(text) >= 40 else "")
                         if needle]
        parent_absent = (not any(marker in prompt_lower for marker in parent_markers)
                         and not any(needle in prompt
                                     for needle in brief_needles for prompt in prompts))
        on_mean = _probe_mean(stem + ".json")
        off_mean = _probe_mean(stem + "_adapterOFF.json")
        pairs.append({
            "episode": at,
            "parent_text_absent_from_stored_prompts": parent_absent,
            "on_mean": on_mean,
            "off_mean": off_mean,
            "qualifying_parent_absent_pair": parent_absent,
            "mean_delta": (on_mean - off_mean if parent_absent and
                           on_mean is not None and off_mean is not None else None),
            "on_stats": on,
            "off_stats": off,
            "delta": ({key: _delta(on, off, key) for key in DELTA_KEYS}
                      if parent_absent else None),
        })
    return pairs


def expand(root: str, patterns: tuple[str, ...]) -> list[str]:
    paths = []
    for pattern in patterns:
        paths.extend(glob.glob(os.path.join(root, pattern)))
    return sorted({p for p in paths if os.path.isdir(p) and
                   os.path.exists(os.path.join(p, "ledger.jsonl"))})


def _same_count_as_wakes(life: str, episodes: list[dict]) -> tuple[bool, int | None]:
    nominal = nominal_exposure(life)
    return nominal is not None and nominal == len(episodes), nominal


def _first_control_trigger(life: str, episodes: list[dict]) -> int | None:
    """First historical sleep where the frozen ritual rule would have fired."""
    sleeps = []
    for path in glob.glob(os.path.join(life, "sleep_*")):
        try:
            sleeps.append(int(os.path.basename(path).removeprefix("sleep_")))
        except ValueError:
            pass
    for at in sorted(sleeps):
        if at > len(episodes):
            continue
        rows = [row for ep in episodes[:at] for row in ep["thought_rows"]]
        if ritual_metrics(rows, last_episodes=32).get("ritual"):
            return at
    return None


def _event_windows(life: str, episodes: list[dict], t0: int,
                   lesson_tokens: set[str], all_briefs: list[dict],
                   indexed_brief_text: str = "", indexed_brief_sha: str = "") -> dict:
    pre = window_stats(episodes, t0 - 32, t0, lesson_tokens)
    windows = {}
    valid_deliveries = []
    seen_hashes = set()
    for brief in all_briefs:
        if brief.get("valid") and brief["sha256"] not in seen_hashes:
            seen_hashes.add(brief["sha256"])
            ordinals = delivered_ordinals(episodes, brief["text"], brief["sleep"])
            if ordinals:
                valid_deliveries.append((brief["sha256"], ordinals[0]))
    for label, (lo, hi) in WINDOWS.items():
        after = window_stats(episodes, t0 + lo, t0 + hi, lesson_tokens)
        windows[label] = {
            "stats": after,
            "delta_vs_pre32": {key: _delta(after, pre, key)
                               for key in DELTA_KEYS},
            "additional_valid_briefs_first_delivered": sum(
                t0 + lo <= at < t0 + hi and sha != indexed_brief_sha
                for sha, at in valid_deliveries
            ),
            "indexed_brief_delivery": (
                delivery_stats(episodes, indexed_brief_text,
                               t0 + lo, t0 + hi)
                if indexed_brief_text else None
            ),
            "write_events": write_events(life, t0 + lo, t0 + hi),
        }
    return {"pre32": pre, "windows": windows}


def analyze(root: str, parent_globs=DEFAULT_PARENT_GLOBS,
            control_globs=DEFAULT_CONTROL_GLOBS) -> dict:
    parents = expand(root, tuple(parent_globs))
    controls = expand(root, tuple(control_globs))
    parent_rows, control_rows, excluded = [], [], []

    for life in parents:
        episodes = episode_texts(load_rows(life))
        count_ok, nominal = _same_count_as_wakes(life, episodes)
        if not count_ok:
            excluded.append({"life": os.path.basename(life),
                             "reason": "episode_count_mismatch_resume_or_replay",
                             "reconstructed": len(episodes), "nominal": nominal})
            continue
        briefs = brief_rows(life)
        delivered = []
        for brief in briefs:
            ordinals = (delivered_ordinals(episodes, brief["text"], brief["sleep"])
                        if brief["valid"] else [])
            if ordinals:
                delivered.append((brief, ordinals))
        if not delivered:
            excluded.append({"life": os.path.basename(life),
                             "reason": "no_valid_exactly_delivered_v3_brief"})
            continue
        brief, ordinals = delivered[0]
        t0 = ordinals[0]
        event = _event_windows(life, episodes, t0, brief["lesson_tokens"],
                               briefs, brief["text"], brief["sha256"])
        public_brief = {k: v for k, v in brief.items()
                        if k not in ("text", "lesson_tokens", "path")}
        parent_rows.append({
            "life": os.path.basename(life),
            "event": "first_valid_exactly_delivered_parent_prompt_v3",
            "nominal_sleep": brief["sleep"],
            "first_delivery_episode_ordinal": t0,
            "total_exact_delivery_episodes": len(ordinals),
            "direct_window_delivery": delivery_stats(
                episodes, brief["text"], t0, t0 + 32),
            "brief": public_brief,
            "n_parent_brief_files": len(briefs),
            **event,
            "parent_absent_probe_pairs": parent_absent_probe_pairs(
                life, [b["text"] for b in briefs]
            ),
        })

    for life in controls:
        episodes = episode_texts(load_rows(life))
        count_ok, nominal = _same_count_as_wakes(life, episodes)
        if not count_ok:
            excluded.append({"life": os.path.basename(life),
                             "reason": "control_episode_count_mismatch_resume_or_replay",
                             "reconstructed": len(episodes), "nominal": nominal})
            continue
        t0 = _first_control_trigger(life, episodes)
        if t0 is None:
            excluded.append({"life": os.path.basename(life),
                             "reason": "no_threshold_aligned_ritual_trigger"})
            continue
        control_rows.append({
            "life": os.path.basename(life),
            "event": "first_sleep_meeting_same_frozen_ritual_threshold",
            "event_episode_ordinal": t0,
            **_event_windows(life, episodes, t0, set(), []),
            "parent_absent_probe_pairs": parent_absent_probe_pairs(life, []),
        })

    complete_s4 = [r for r in parent_rows + control_rows
                   if r["windows"]["after_four_sleeps_32"]["stats"]
                   ["n_episodes"] == 32]
    return {
        "status": "exploratory_descriptive_only",
        "root": os.path.realpath(root),
        "parent_globs": list(parent_globs),
        "control_globs": list(control_globs),
        "windows": WINDOWS,
        "n_parent_lives_found": len(parents),
        "n_control_lives_found": len(controls),
        "n_parent_events": len(parent_rows),
        "n_control_events": len(control_rows),
        "s4_minimum_for_interpretation": 4,
        "s4_sufficient": (len(parent_rows) >= 4 and len(control_rows) >= 4 and
                          len(complete_s4) == len(parent_rows) + len(control_rows)),
        "parent_events": parent_rows,
        "control_events": control_rows,
        "excluded": excluded,
        "limitations": [
            "Lexical rehearsal is an echo diagnostic, not behavioral transfer.",
            "Historical parent assignment and intervention timing were not randomized.",
            "R4 used a legacy brief parent and selected writes on the report panel.",
            "Later windows include adaptive parenting and therefore are not withdrawal.",
            "Ritual-triggered before/after changes are vulnerable to regression to the mean.",
            "Parent-absent ON/OFF probes isolate the realized adapter effect, not the causal effect of parenting.",
            "Generated ACT-like prose is never counted as action; only act ledger rows are authoritative.",
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.expanduser("~/v6_out"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--parent-glob", action="append", dest="parent_globs")
    ap.add_argument("--control-glob", action="append", dest="control_globs")
    args = ap.parse_args(argv)
    report = analyze(os.path.expanduser(args.root),
                     tuple(args.parent_globs or DEFAULT_PARENT_GLOBS),
                     tuple(args.control_globs or DEFAULT_CONTROL_GLOBS))
    out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(os.path.realpath(out)), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps({k: report[k] for k in (
        "status", "n_parent_events", "n_control_events", "s4_sufficient")},
        indent=1))


if __name__ == "__main__":
    main()
