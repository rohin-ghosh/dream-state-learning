"""Read exact eval/train/receipt triples; report paired-source diagnostics, not pooled claims.

Usage: python3 -B research_notes/analysis/astra_seed_campaign.py \
    --entry EVAL.json TRAIN_META.json SEED_RUN_RECEIPT.json
Repeat --entry for each bank/optimizer seed. Use '-' for unavailable evidence.
JSON goes to stdout. Historical inputs are read from EVAL's run directory;
prepared inputs are read beside the receipt. Nothing is written or generated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gpu.prepare_memory_seed_run import BASE_MODEL, LABEL, inspect_source
from organism_v6 import memory_dose as definitions


def number(value):
    return value if type(value) in (int, float) and math.isfinite(value) else None


def complete_mean(values):
    return statistics.mean(values) if values and all(value is not None for value in values) else None


def conditional(side, colour):
    mass = number(side.get("mass")) if isinstance(side, dict) else None
    raw = side.get("p_raw", {}) if isinstance(side, dict) else {}
    probability = number(raw.get(colour)) if isinstance(raw, dict) else None
    return probability / mass if mass is not None and mass > 0 and probability is not None and probability >= 0 else None


def mass_value(side):
    return number(side.get("mass")) if isinstance(side, dict) else None


def summarize_rows(rows):
    result = {"cue_count": len(rows)}
    for side in ("OFF", "ON"):
        probabilities = [conditional(row.get(side), row.get("a")) for row in rows]
        masses = [mass_value(row.get(side)) for row in rows]
        result[f"conditional_p_{side.lower()}"] = complete_mean(probabilities)
        result[f"mass_{side.lower()}"] = complete_mean(masses)
        result[f"valid_{side.lower()}_count"] = sum(value is not None for value in probabilities)
    deltas = [abs(conditional(row.get("ON"), row.get("a")) - conditional(row.get("OFF"), row.get("a")))
              if conditional(row.get("ON"), row.get("a")) is not None
              and conditional(row.get("OFF"), row.get("a")) is not None else None for row in rows]
    result["mean_abs_conditional_delta"] = complete_mean(deltas)
    result["status"] = "available" if rows and result["valid_off_count"] == result["valid_on_count"] == len(rows) else "unavailable"
    return result


def valid_metric(row, colour=None, alternative=None):
    if not isinstance(row, dict):
        return None
    colour = colour or row.get("a")
    for side in ("OFF", "ON"):
        values = row.get(side)
        raw = values.get("p_raw") if isinstance(values, dict) else None
        if not isinstance(raw, dict) or len(raw) < 2 or colour not in raw:
            return None
        if conditional(values, colour) is None or any(number(value) is None or value < 0 for value in raw.values()):
            return None
        if sum(raw.values()) <= 0 or (alternative is not None and alternative not in raw):
            return None
    if set(row["OFF"]["p_raw"]) != set(row["ON"]["p_raw"]):
        return None
    try:
        return definitions.cue_metrics(row, a=colour, b=alternative)
    except (KeyError, ValueError, TypeError):
        return None


def binding_metrics(cues, bank, bootstrap_seed=0):
    unavailable = []
    indexed = {}
    for cue in cues:
        if cue.get("kind") not in ("frame", "frame_similar", "frame_bicycle"):
            continue
        key = (cue["kind"], cue.get("owner"))
        if key in indexed:
            unavailable.append("duplicate frame cue")
        indexed[key] = cue
    owners = bank.get("owners", []) if isinstance(bank, dict) else []
    if not owners:
        unavailable.append("source bank owner roster")
    gains, similar, bicycle, unexposed = [], [], [], []
    dose16_count = 0
    for owner in owners:
        identity, dose = owner.get("id"), owner.get("dose")
        frame = indexed.get(("frame", identity))
        metric = valid_metric(frame)
        if metric is None or frame.get("dose") != dose or frame.get("a") != owner.get("colour"):
            unavailable.append(f"valid owner frame: {identity}")
            continue
        if dose == 0:
            unexposed.append(abs(metric["d_p_norm"]))
        elif isinstance(dose, int) and dose > 0:
            controls = []
            for kind in ("frame_similar", "frame_bicycle"):
                row = indexed.get((kind, identity))
                control = valid_metric(row, colour=metric["a"], alternative=metric["b"] if kind == "frame_similar" else None)
                if control is None or row.get("dose") != dose or row.get("a") != metric["a"]:
                    unavailable.append(f"valid {kind}: {identity}")
                    control = None
                controls.append(control)
            if controls[0] is not None:
                similar.append(abs(controls[0]["d_p_norm"]))
            if controls[1] is not None:
                bicycle.append(abs(controls[1]["d_p_norm"]))
            if dose == 16:
                dose16_count += 1
                if controls[0] is not None:
                    gains.append(metric["d_logodds"] - controls[0]["d_logodds"])
    for name, values in (("dose16 paired owners", gains), ("unexposed frame control", unexposed),
                         ("similar frame control", similar), ("bicycle frame control", bicycle)):
        if not values:
            unavailable.append(name)
    interval = definitions.paired_bootstrap(gains, seed=bootstrap_seed)
    parts = {"similar_exposed": complete_mean(similar), "unexposed": complete_mean(unexposed),
             "bicycle_exposed": complete_mean(bicycle)}
    spill = complete_mean(list(parts.values()))
    passed = None if unavailable or spill is None or interval["lo"] is None else bool(
        interval["lo"] > 0 and spill <= definitions.GATES["frame_spill"])
    return {"definition": "organism_v6.memory_dose:G9_frame_binding", "passed": passed,
            "I_d_frame": interval, "dose16_owner_count": dose16_count,
            "frame_spill": spill, "spill_parts": parts, "spill_threshold": definitions.GATES["frame_spill"],
            "bootstrap_seed": bootstrap_seed, "resampling_unit": "paired owners within this bank and fit only",
            "unavailable": sorted(set(unavailable))}


def load_document(path, label, unavailable):
    if not path or str(path) == "-":
        unavailable.append(label)
        return None
    try:
        value = json.loads(Path(path).read_text())
        if not isinstance(value, dict):
            raise ValueError("not a JSON object")
        return value
    except (OSError, ValueError) as error:
        unavailable.append(f"{label}: {error}")
        return None


def analyze_entry(eval_path, train_path, receipt_path, bootstrap_seed=0):
    unavailable, mismatches = [], []
    evaluation = load_document(eval_path, "eval", unavailable)
    training = load_document(train_path, "training metadata", unavailable)
    receipt = load_document(receipt_path, "run receipt", unavailable)
    cues = evaluation.get("cues", []) if evaluation else []
    if not isinstance(cues, list) or not all(isinstance(cue, dict) for cue in cues):
        unavailable.append("valid cue list")
        cues = []
    bank_index = evaluation.get("bank") if evaluation else None
    eval_meta = (evaluation.get("meta") or {}) if evaluation else {}
    cell = eval_meta.get("cell")
    seed = training.get("seed") if training else None
    fit_complete = bool(training and training.get("measure_only") is False
                        and type(seed) is int and seed >= 0
                        and Path(train_path).name == "train_meta.json"
                        and Path(train_path).with_name("DONE").is_file()
                        and not any("throughput" in part for part in Path(train_path).parts))
    if not fit_complete:
        unavailable.append("completed scientific fit (profiles are not fits)")
        seed = None
    hashes, manifest, bank = {}, None, None
    source_errors = []
    root = Path(receipt_path).parent if receipt else Path(eval_path).parent.parent
    if type(bank_index) is not int or not isinstance(cell, str):
        source_errors.append("eval bank/cell metadata unavailable")
    else:
        try:
            _, inputs, manifest, _, metadata = inspect_source(root, cell, banks=[bank_index])
            hashes = {relative: hashlib.sha256(content).hexdigest() for relative, content in inputs.items()}
            bank_relative = f"banks/bank{bank_index}.json"
            bank = json.loads(inputs[bank_relative])
            corpus_meta = metadata[str(bank_index)]
            adapter_meta = evaluation.get("adapter_meta") or {}
            for key, value in (("corpus_sha", corpus_meta["sha"]), ("items_sha", corpus_meta["items_sha"]),
                               ("ordering", corpus_meta["ordering"])):
                documents = [("eval adapter", adapter_meta)] + ([("training", training)] if training else [])
                for label, document in documents:
                    if key not in document:
                        source_errors.append(f"{label} {key} unavailable")
                    elif document[key] != value:
                        mismatches.append(f"{label} {key}")
            if receipt:
                for key, value in (("base_model", BASE_MODEL), ("source_scorer", "HFScorer"),
                                   ("source_bank_seed", manifest["seed"]), ("training_seed", seed),
                                   ("cell", cell), ("label", LABEL), ("clean_lineage_eligible", False),
                                   ("status", "prepared")):
                    if key == "training_seed" and seed is None:
                        continue
                    if key not in receipt:
                        source_errors.append(f"receipt {key} unavailable")
                    elif receipt[key] != value:
                        mismatches.append(f"receipt {key}")
                if bank_index not in receipt.get("banks", []):
                    mismatches.append("receipt bank selection")
                for relative, digest in hashes.items():
                    recorded = (receipt.get("inputs") or {}).get(relative, {})
                    if recorded.get("sha256") != digest or recorded.get("bytes") != len(inputs[relative]):
                        mismatches.append(f"receipt input hash/bytes: {relative}")
                if (receipt.get("corpora") or {}).get(str(bank_index)) != corpus_meta:
                    mismatches.append("receipt corpus metadata")
                expected_adapter = str(Path(receipt.get("destination_run", "")) /
                                       f"adapters/bank{bank_index}/{cell}/across/sleep4/r8")
                if evaluation.get("adapter") != expected_adapter:
                    mismatches.append("eval adapter/receipt destination")
        except (OSError, ValueError, KeyError, TypeError) as error:
            source_errors.append(str(error))
    if evaluation and (evaluation.get("model") != "hf" or evaluation.get("synthetic") is not True
                       or evaluation.get("lam") != 1 or eval_meta.get("arm") != "across" or eval_meta.get("sleep") != 4):
        mismatches.append("eval model/synthetic/lambda/arm/sleep")
    if training and (training.get("model") != BASE_MODEL or training.get("synthetic") is not True
                     or training.get("rank") != 8 or training.get("epochs") != 3 or training.get("lr") != 0.0001):
        mismatches.append("training model/synthetic/rank/epochs/lr")
    if training and (eval_meta.get("rank") != training.get("rank") or
                     (evaluation or {}).get("adapter_meta", {}).get("rank") != training.get("rank")):
        mismatches.append("eval/training rank")
    source_status = "mismatch" if mismatches else "unavailable" if source_errors or not training else "compatible"
    binding = binding_metrics(cues, bank, bootstrap_seed)
    if unavailable or source_status != "compatible":
        binding["passed"] = None
    binding["unavailable"] = sorted(set(binding["unavailable"] + unavailable + source_errors))
    if mismatches:
        binding["unavailable"].append("incompatible evidence; not a scientific negative")
    return {"eval_path": str(eval_path), "train_meta_path": str(train_path), "receipt_path": str(receipt_path),
            "bank": bank_index, "cell": cell, "optimizer_seed": seed,
            "source_bank_seed": manifest.get("seed") if manifest else None,
            "fit_complete": fit_complete, "eval_cue_count": len(cues), "label": LABEL,
            "dose16": {kind: summarize_rows([cue for cue in cues if cue.get("kind") == kind and cue.get("dose") == 16])
                       for kind in ("frame", "frame_similar", "frame_bicycle")},
            "binding": binding, "source_hash_compatibility": {"status": source_status,
            "mismatches": mismatches, "unavailable": source_errors, "input_sha256": hashes},
            "receipt_available": receipt is not None,
            "unavailable_controls": binding["unavailable"],
            "wrong_owner_control": "frame_similar is an unseen look-alike, not an exposed-partner swapped-ID test"}


def analyze_campaign(entries, bootstrap_seed=0):
    rows, seen = [], set()
    for entry in entries:
        identity = str(Path(entry[0]).resolve())
        if identity in seen:
            raise ValueError(f"duplicate eval path: {entry[0]}")
        seen.add(identity)
        rows.append(analyze_entry(*entry, bootstrap_seed=bootstrap_seed))
    groups = {}
    for row in rows:
        evidence = row["source_hash_compatibility"]
        if evidence["status"] != "compatible" or not row["fit_complete"]:
            continue
        bank = row["bank"]
        digest = evidence["input_sha256"][f"banks/bank{bank}.json"]
        manifest_digest = evidence["input_sha256"]["manifest.json"]
        distractor_digest = evidence["input_sha256"]["distractor.json"]
        group = groups.setdefault((bank, digest, manifest_digest, distractor_digest),
                                  {"bank": bank, "bank_sha256": digest,
                                   "manifest_sha256": manifest_digest, "distractor_sha256": distractor_digest, "cells": {}})
        corpus = f"corpora/bank{bank}/{row['cell']}/across/sleep4/corpus.json"
        cell_key = (row["cell"], evidence["input_sha256"][corpus])
        cell = group["cells"].setdefault(cell_key, {"cell": row["cell"], "corpus_sha256": cell_key[1],
                                       "optimizer_seeds": [], "evaluation_count": 0, "missing_receipt_count": 0})
        cell["optimizer_seeds"].append(row["optimizer_seed"])
        cell["evaluation_count"] += 1
        cell["missing_receipt_count"] += not row["receipt_available"]
    for group in groups.values():
        group["cells"] = list(group["cells"].values())
        for cell in group["cells"]:
            cell["unique_optimizer_seed_count"] = len(set(cell["optimizer_seeds"]))
            cell["optimizer_seeds"] = sorted(set(cell["optimizer_seeds"]))
            cell["unavailable_reference_optimizer_seeds"] = sorted({0, 1} - set(cell["optimizer_seeds"]))
    return {"schema_version": 1, "rows": rows, "paired_source_cells": list(groups.values()),
            "counts": {"entries": len(rows), "completed_fits": sum(row["fit_complete"] for row in rows),
                       "compatible_source_entries": sum(row["source_hash_compatibility"]["status"] == "compatible" for row in rows),
                       "binding_available": sum(row["binding"]["passed"] is not None for row in rows)},
            "definitions_sha256": hashlib.sha256(Path(definitions.__file__).read_bytes()).hexdigest(),
            "notes": ["Optimizer seeds are repeated fits of paired source cells, not independent bank replicates.",
                      "No cross-bank pooling, independence assumption, campaign success rate, or H1/H2 claim is computed.",
                      "Conditional P uses p_raw[a]/mass as eval_frame_summary; nonpositive/null mass is unavailable, never zero-imputed.",
                      "G9 uses existing cue_metrics, paired_bootstrap and spill threshold without fitting new thresholds.",
                      "Missing controls, receipts or completed-fit evidence cannot yield a binding pass."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", nargs=3, action="append", required=True, metavar=("EVAL", "TRAIN_META", "RECEIPT"))
    parser.add_argument("--bootstrap-seed", type=int, default=0, help="analysis resampling seed, not an optimizer seed")
    args = parser.parse_args(argv)
    try:
        result = analyze_campaign(args.entry, args.bootstrap_seed)
    except (OSError, ValueError) as error:
        parser.exit(2, f"astra_seed_campaign: {error}\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
