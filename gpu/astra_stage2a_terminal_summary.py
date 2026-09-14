"""Bounded terminal receipt summary, not independent trajectory replay or promotion."""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import statistics


CRITERIA = {name: (4, 3) for name in ("SEEK", "PROSPECT", "CHECK", "CONTINUE")}
CRITERIA.update(typed_interventions=(32, 30), whole_chains=(8, 6), useful_reads=(8, 7),
                typed_steps=(8, 7), canaries=(16, 15), chain_gain=(8, 2))


def validate_criteria(rows):
    if type(rows) is not list or len(rows) != len(CRITERIA):
        raise ValueError("exact_ten_criteria_required")
    counts = {}
    for row in rows:
        name = row.get("name")
        if name not in CRITERIA or name in counts:
            raise ValueError("unknown_or_duplicate_criterion")
        if any(type(row.get(key)) is not int for key in ("count", "denominator", "minimum")):
            raise ValueError("integer_criterion_required")
        denominator, minimum = CRITERIA[name]
        if (row["denominator"], row["minimum"]) != (denominator, minimum):
            raise ValueError("criterion_contract_changed")
        lower = -denominator if name == "chain_gain" else 0
        if not lower <= row["count"] <= denominator:
            raise ValueError("criterion_count_out_of_range")
        counts[name] = row["count"]
    baseline_chains = counts["whole_chains"] - counts["chain_gain"]
    if not 0 <= baseline_chains <= 8:
        raise ValueError("derived_baseline_chain_count_invalid")
    return counts


def inert_value(value):
    if type(value) in (str, int, float, bool) or value is None:
        return value
    if type(value) is not dict or len(value) != 1:
        raise ValueError("unsupported_training_receipt_value")
    if "mapping" in value:
        pairs = [(inert_value(key), inert_value(item)) for key, item in value["mapping"]]
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError("duplicate_training_receipt_key")
        return result
    if "list" in value or "tuple" in value:
        return [inert_value(item) for item in next(iter(value.values()))]
    raise ValueError("unsupported_training_receipt_tag")


def summarize(root):
    root = Path(root)
    pins = {}

    def read(name):
        path = root / name
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("receipt_byte_bound_exceeded")
        raw = path.read_bytes()
        pins[name] = sha256(raw).hexdigest()
        return json.loads(raw)

    result = read("RESULT.json")
    if result.get("status") != "REDUCED_NUMERICAL_DATA":
        raise ValueError("completed_reduced_result_required")
    counts = validate_criteria(result.get("criteria"))
    validation = result.get("reduction_validation")
    if validation is not None and (validation.get("reportable") is not True
                                  or validation.get("base_issues") or validation.get("atom_local_issues")):
        raise ValueError("nonreportable_reduction")
    observed = read("TRAINING_OBSERVATIONS.json")
    tokenization = read("tokenizer/receipt.json")
    if pins["TRAINING_OBSERVATIONS.json"] != result["training_observations"]["sha256"]:
        raise ValueError("training_observations_hash_mismatch")
    if pins["tokenizer/receipt.json"] != result["tokenizer_receipt_sha256"]:
        raise ValueError("tokenizer_receipt_hash_mismatch")
    rows = inert_value(observed["receipts"])
    if (observed["completed_updates"], observed["cursor"], observed["receipt_count"], len(rows)) != (256, 1024, 256, 256):
        raise ValueError("complete_d1_training_receipts_required")
    if [row["update_number"] for row in rows] != list(range(1, 257)):
        raise ValueError("training_update_order_mismatch")
    if any(row["arm"] != "ATOM_LOCAL" or not math.isfinite(row["loss"]) for row in rows):
        raise ValueError("invalid_training_loss_or_arm")
    losses = [row["loss"] for row in rows]
    failed = [name for name, count in counts.items() if count < CRITERIA[name][1]]
    return {"kind": "TERMINAL_SUMMARY_NOT_INDEPENDENT_REPLAY", "source_receipt_pins": pins,
            "criteria": [{**row, "passed": row["count"] >= row["minimum"]} for row in result["criteria"]],
            "failed_criteria": failed, "all_declared_criteria_passed": not failed,
            "baseline_whole_chains_inferred_from_declared_gain": counts["whole_chains"] - counts["chain_gain"],
            "training": {"updates": 256, "loss_first": losses[0], "loss_last": losses[-1],
                         "loss_first16_mean": statistics.mean(losses[:16]),
                         "loss_last16_mean": statistics.mean(losses[-16:])},
            "D1_ATOM_accounting": tokenization["accounting_by_stage"]["D1"]["ATOM_LOCAL"],
            "checkpoint_hashes": result["conductor_hashes"], "native_stages": result["stages"],
            "limits": ["One exploratory learner; no uncertainty across seeds.",
                       "Same-process checkpoint roundtrip, not fresh-process persistence.",
                       "Text-memory controller, not weights-only hopping or autonomous parenting.",
                       "D2 eligibility and scientific promotion require separate protocol adjudication."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    options = parser.parse_args()
    summary = summarize(options.root)
    with options.output.open("x") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
