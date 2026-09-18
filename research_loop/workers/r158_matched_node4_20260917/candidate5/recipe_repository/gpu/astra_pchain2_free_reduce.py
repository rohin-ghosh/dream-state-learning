"""CPU-only exact-output reduction for the separate free-endpoint DEV material.

Missing, failed and invalid calls remain in their designated panel denominators.
No tokenizer, model, solver, protocol-clearance gate, or dose recommendation runs.
"""

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import re

from gpu import astra_pchain2_prepare as source
from gpu.astra_pchain2_free_material import MATERIAL_KIND


SCHEMA = "PCHAIN2_FREE_ENDPOINT_REDUCTION_V1"


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _key(slot):
    return slot["panel"], slot["index"]


def _calls(manifest, state):
    _require(manifest.get("material_kind") == MATERIAL_KIND and manifest.get("state") == state,
             "free_endpoint_state_manifest_required")
    roster = [asdict(slot) for slot in source.d1_readout_slots() if slot.state == state]
    _require([call["slot"] for call in manifest["calls"]] == roster, "exact_state_roster_required")
    result = {}
    for entry in manifest["calls"]:
        _require(type(entry.get("user")) is str and type(entry.get("expected")) is str,
                 "bound_held_questions_and_expected_bytes_required")
        _require("ENDPOINT CANDIDATES" not in entry["user"], "candidate_assisted_material_not_supported")
        expected = entry["expected"].encode("utf-8")
        _require(expected.endswith(b"\n") and not expected.endswith(b"\n\n"), "canonical_expected_newline_required")
        result[_key(entry["slot"])] = source.ReadoutCall(source.ReadoutSlot(**entry["slot"]), entry["user"], expected)
    return result


def _observation(call, record, *, eos_token_id):
    result = dict(slot=asdict(call.slot), status="MISSING", success=False, raw=None)
    if record is None:
        return result
    if record.get("status") in ("ERROR", "NOT_RUN"):
        result["status"] = record["status"]
        return result
    result["status"] = "INVALID_RAW"
    ids = record.get("token_ids")
    text = record.get("raw_utf8_hex")
    terminal, truncated = record.get("terminal"), record.get("truncated")
    if not (record.get("status") == "RAW" and type(ids) is list
            and all(type(token) is int and token >= 0 for token in ids) and len(ids) <= call.slot.max_new_tokens
            and type(text) is str and re.fullmatch(r"(?:[0-9a-fA-F]{2})*", text)
            and type(terminal) is bool and type(truncated) is bool):
        return result
    if terminal != (bool(ids) and ids[-1] == eos_token_id):
        return result
    if truncated != (len(ids) == call.slot.max_new_tokens and not terminal):
        return result
    raw = bytes.fromhex(text)
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return result
    result.update(status="RAW", raw=raw, token_ids=ids, terminal=terminal, truncated=truncated,
                  success=source.strict_match(call, raw, terminal=terminal, truncated=truncated))
    return result


def _counts(observations):
    return dict(n=len(observations), successes=sum(item["success"] for item in observations),
                raw=sum(item["status"] == "RAW" for item in observations),
                missing=sum(item["status"] == "MISSING" for item in observations),
                errors=sum(item["status"] == "ERROR" for item in observations),
                not_run=sum(item["status"] == "NOT_RUN" for item in observations),
                invalid_raw=sum(item["status"] == "INVALID_RAW" for item in observations))


def _identity(first, second):
    return (first["raw"] == second["raw"] and first["token_ids"] == second["token_ids"]
            and first["terminal"] == second["terminal"] and first["truncated"] == second["truncated"])


def _paired_identity(first_calls, second_calls, first_rows, second_rows, keys):
    result = dict(n=len(keys), comparable_raw_pairs=0, unavailable_pairs=0,
                  raw_bytes_identical=0, raw_identities=0, both_expected_hits=0)
    for key in keys:
        _require(first_calls[key].user == second_calls[key].user
                 and first_calls[key].expected == second_calls[key].expected, "common_question_or_target_mismatch")
        first, second = first_rows[key], second_rows[key]
        if first["status"] != "RAW" or second["status"] != "RAW":
            result["unavailable_pairs"] += 1
            continue
        result["comparable_raw_pairs"] += 1
        result["raw_bytes_identical"] += first["raw"] == second["raw"]
        result["raw_identities"] += _identity(first, second)
        result["both_expected_hits"] += first["success"] and second["success"]
    return result


def _redirected(first_calls, second_calls, first_rows, second_rows, keys):
    result = dict(n=len(keys), comparable_raw_pairs=0, unavailable_pairs=0, authentic_expected_hits=0,
                  deranged_expected_hits=0, both_correct_redirected=0, deranged_authentic_expected_hits=0)
    for key in keys:
        authentic, deranged = first_calls[key], second_calls[key]
        _require(authentic.user == deranged.user and authentic.expected != deranged.expected,
                 "same_question_distinct_redirection_targets_required")
        first, second = first_rows[key], second_rows[key]
        result["authentic_expected_hits"] += first["success"]
        result["deranged_expected_hits"] += second["success"]
        if second["status"] == "RAW":
            result["deranged_authentic_expected_hits"] += source.strict_match(
                authentic, second["raw"], terminal=second["terminal"], truncated=second["truncated"])
        if first["status"] != "RAW" or second["status"] != "RAW":
            result["unavailable_pairs"] += 1
            continue
        result["comparable_raw_pairs"] += 1
        result["both_correct_redirected"] += first["success"] and second["success"]
    return result


def reduce_material(manifests, records_by_state):
    """Reduce one fixed five-state roster; absent readouts count as missing slots."""
    _require(set(manifests) == set(source.STATES), "all_five_evaluation_manifests_required")
    _require(set(records_by_state) <= set(source.STATES), "unknown_readout_state")
    reference = manifests["BASE"]
    calls, observations, states = {}, {}, {}
    for state in source.STATES:
        manifest = manifests[state]
        _require(manifest["identifier_receipt_sha256"] == reference["identifier_receipt_sha256"]
                 and manifest["tokenizer"] == reference["tokenizer"], "mixed_material_or_tokenizer")
        eos = manifest["tokenizer"]["eos_token_id"]
        _require(type(eos) is int and eos >= 0, "declared_EOT_required")
        calls[state] = _calls(manifest, state)
        indexed = {}
        for record in records_by_state.get(state, []):
            _require(type(record) is dict and type(record.get("slot")) is dict, "raw_slot_required")
            slot = record["slot"]
            key = _key(slot)
            _require(key in calls[state] and slot == asdict(calls[state][key].slot), "unknown_or_changed_raw_slot")
            _require(key not in indexed, "duplicate_raw_slot_no_selection")
            indexed[key] = record
        rows = {key: _observation(call, indexed.get(key), eos_token_id=eos) for key, call in calls[state].items()}
        observations[state] = rows
        states[state] = dict(panels={panel: _counts([row for key, row in rows.items() if key[0] == panel])
                                    for panel in source.PANELS},
                             one_hop_by_hop={hop: _counts([row for key, row in rows.items()
                                                         if key[0] == "one_hop" and (key[1] < 16) == first])
                                             for hop, first in (("first", True), ("second", False))},
                             calls=[{key: value for key, value in row.items() if key not in ("raw", "token_ids")}
                                    for row in rows.values()])
    common = tuple(calls["BASE"])
    _require(len(common) == 80 and set(common) == set(calls["LR0"]), "exact_80_common_calls_required")
    identity = _paired_identity(calls["BASE"], calls["LR0"], observations["BASE"], observations["LR0"], common)
    identity.update(definition="exact raw bytes, token IDs, terminal and truncated flags; valid RAW records only")
    authentic, deranged = "ATOM-JUNCTION", "DERANGED-JUNCTION"
    redirects = {}
    for panel, start, stop in (("one_hop", 16, 32), ("eval_trace", 0, 16), ("eval_direct", 0, 16)):
        keys = tuple((panel, index) for index in range(start, stop))
        redirects["one_hop_second" if panel == "one_hop" else panel] = _redirected(
            calls[authentic], calls[deranged], observations[authentic], observations[deranged], keys)
    first_hop = _paired_identity(calls[authentic], calls[deranged], observations[authentic], observations[deranged],
                                tuple(("one_hop", index) for index in range(16)))
    return dict(schema=SCHEMA, material_kind=MATERIAL_KIND, model_calls=0,
                scoring="designated expected UTF-8 bytes, exact terminal newline, terminal EOT, nontruncated",
                original_protocol_compliance_assessed=False, null_clearance_assessed=False,
                identifier_receipt_sha256=reference["identifier_receipt_sha256"],
                states=states, lr0_vs_base_common80=identity,
                deranged_redirection=dict(reference_state=authentic, comparison_state=deranged, panels=redirects,
                                           first_hop_preservation=first_hop))


def _read_raw(path):
    if not path.exists():
        return [], dict(path=str(path), present=False, sha256=None, parse_errors=[])
    raw = path.read_bytes()
    records, errors = [], []
    for number, line in enumerate(raw.splitlines(), 1):
        try:
            records.append(json.loads(line))
        except (ValueError, UnicodeDecodeError):
            errors.append(dict(line=number, error="invalid_json_line_unassigned_to_slot"))
    return records, dict(path=str(path), present=True, sha256=sha256(raw).hexdigest(), parse_errors=errors)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-dir", required=True)
    parser.add_argument("--readouts-dir", required=True, help="Contains STATE/raw_readouts.jsonl; absent states remain missing")
    parser.add_argument("--raw", action="append", default=[], metavar="STATE=PATH", help="Explicit per-state JSONL path override")
    parser.add_argument("--output", required=True, help="New JSON report file; never overwrite")
    args = parser.parse_args(argv)
    overrides = {}
    for value in args.raw:
        state, separator, path = value.partition("=")
        _require(separator and path and state in source.STATES and state not in overrides, "unique_STATE_PATH_required")
        overrides[state] = Path(path)
    manifests, records, inputs = {}, {}, {}
    for state in source.STATES:
        manifest_path = Path(args.evaluation_dir) / (state + ".json")
        raw = manifest_path.read_bytes()
        manifests[state] = json.loads(raw)
        records[state], receipt = _read_raw(overrides.get(state, Path(args.readouts_dir) / state / "raw_readouts.jsonl"))
        inputs[state] = dict(evaluation=dict(path=str(manifest_path), sha256=sha256(raw).hexdigest()), readout=receipt)
    report = reduce_material(manifests, records)
    report["inputs"] = inputs
    report["reducer_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(str(output))


if __name__ == "__main__":
    main()
