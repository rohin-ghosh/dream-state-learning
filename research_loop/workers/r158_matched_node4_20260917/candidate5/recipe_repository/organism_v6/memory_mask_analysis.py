"""Offline, exploratory original A1 versus measured prefix-mask comparison.

Run with python3 -B -m organism_v6.memory_mask_analysis BASELINE MASK
--output-new OUTPUT.json. No models, tokenizers, subprocesses, or input writes.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
import math
from pathlib import Path

from organism_v6 import memory_dose as native


CORPUS = "corpora/bank0/F_r16k16/across/sleep4/corpus.json"
ADAPTER = "adapters/bank0/F_r16k16/across/sleep4/r8"
TAG = "bank0__F_r16k16__across__sleep4__r8"
EVAL = "eval/" + TAG + "__lam1.json"
KEY = "F_r16k16__across__r8__lam1"
GATE_NAMES = ("G9_frame_binding", "G11_abstention")
SOURCE_HASH = "ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3"
BASE_HASHES = {
    "seed_run_receipt.json": "2939b7812d36f59d571659d02c2088fb727d87a59965b5cae13bef39d27dfc3d",
    ADAPTER + "/train_meta.json": "b046eb082ec8bc488d202e94fc1a09108e35b00d32a45bf2464534a8b5e3493c",
    EVAL: "970e1be480133cb81d62b53e9762bd4ef77b5c0b1d11e3a85d21b7e3dab64386",
}
INPUT_HASHES = {
    CORPUS: "f2388eaf9c2285d6c5fe109445a599a4fefb5d9b1ca0ce6223ef78bede01c37d",
    "manifest.json": "b2d82e650c51f9c453f7978a56840eade533f253e732b6c897c43b690ccaf35f",
    "distractor.json": "4ad56576f6d0a9ae211207ab06daef767ccca6a3968c7d9542505406137a9fdc",
    "banks/bank0.json": "87851da0b4229c1bed9523b653845873197866f5157031846e914d44dbf8fc31",
    "banks/bank1.json": "b63d649fa16a2b921c694e88a379fa01b174d5c101111c0ddaaf26e9c098e362",
    "banks/bank2.json": "a4ca0376a7cba887d2f571083ec5f4b0aa36b8fa366c1060fb01579a803a76e4",
}
MASK_CORPUS_HASH = "df293444d4bae6e0330039aa564132b545283d95c2ff55d1f3134abef0791d1a"
COUNTS = dict(items=12924, changed_masks=6720, changed_label_items=5376,
              input_tokens_per_epoch=249995, original_supervised_per_epoch=237071,
              supervised_per_epoch=140975, removed_labels=96096, boundary_straddles=5376,
              truncated_items=0, omitted_owner_prefix_tokens=5376)
KINDS = dict(fact=5376, lesson=1344, filler_colour=4096, filler=2108)
FIT = dict(recipe="memory_dose_v1 (mirrors train_adapter.py v1)",
           model="Qwen/Qwen2.5-7B-Instruct", rank=8, alpha=16, dropout=0.05,
           epochs=3, lr=1e-4, bsz=4, max_len=512, seed=2, steps=9693, total_steps=9693,
           n_items=12924, tokens=749985, truncated_items=0, measure_only=False,
           synthetic=True, ordering="chronological", writer="occurrences",
           representation="frames", shuffled=False,
           tokenization="joint context+target (encode_item)",
           targets=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
EVAL_META = dict(bank=0, model="hf", lam=1.0, n_cues=1313, synthetic=True,
                 template_check=True, boundary_straddles=512, tag=TAG,
                 meta=dict(cell="F_r16k16", arm="across", sleep=4, rank=8),
                 tokenization="joint prompt+candidate (joint_candidate_ids)")
ADAPTER_FIELDS = ("corpus_sha", "items_sha", "ordering", "writer", "representation",
                  "shuffled", "rank", "recipe")
FRAME_KINDS = ("frame", "frame_similar", "frame_bicycle")
ARTIFACT_ERRORS = (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError,
                   ZeroDivisionError, OverflowError)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    def reject(value):
        raise ValueError("nonfinite JSON literal: " + value)
    return json.loads(path.read_text(), parse_constant=reject)


def expect_fields(actual, expected, label):
    for field, value in expected.items():
        require(field in actual and type(actual[field]) is type(value)
                and actual[field] == value, label + "." + field)


def expected_mask_corpus(original):
    derived = copy.deepcopy(original)
    for item in derived["corpus"]:
        if item["kind"] in ("fact", "lesson"):
            item["mask_context"] = True
    derived["sha"] = native.sha_of([(native.render_item(item), item["weight"],
                                      item["mask_context"]) for item in derived["corpus"]])
    derived["items_sha"] = native.items_sha(derived["corpus"])
    derived["stats"]["supervised_tokens"] = COUNTS["supervised_per_epoch"]
    derived["stats"]["supervised_tokens_semantics"] = "joint tokenization, shifted causal labels, one epoch"
    derived["mask_ablation"] = dict(
        treatment="fact_and_lesson_context_mask_only", original_sha=original["sha"],
        original_items_sha=original["items_sha"], input_strings_order_weights_unchanged=True,
        original_supervised_stat=original["stats"].get("supervised_tokens"), clean_lineage_eligible=False)
    return derived


def validate_inputs(baseline, mask):
    receipt = load(mask / "mask_run_receipt.json")
    seed_receipt = load(baseline / "seed_run_receipt.json")
    expect_fields(receipt, dict(status="PREPARED_NOT_TRAINED", training_seed=2,
                  source_bank_seed=1, rank=8, epochs=3, lr=1e-4, expected_steps=9693,
                  treatment="fact_and_lesson_context_mask_only", clean_lineage_eligible=False,
                  source_corpus_sha256=INPUT_HASHES[CORPUS],
                  model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY"), "mask receipt")
    expect_fields(receipt["counts"], COUNTS, "receipt counts")
    require(set(receipt["counts"]) == set(COUNTS), "unexpected receipt count fields")
    require(receipt["source_inputs"] == INPUT_HASHES, "source input manifest")
    derived_hashes = dict(INPUT_HASHES, **{CORPUS: MASK_CORPUS_HASH})
    require(receipt["inputs"] == derived_hashes, "derived input manifest")
    hashes = {"baseline": {}, "mask": {"mask_run_receipt.json": digest(mask / "mask_run_receipt.json")}}
    for label, root, expected in (("baseline", baseline, INPUT_HASHES), ("mask", mask, derived_hashes)):
        for relative, expected_hash in expected.items():
            actual = digest(root / relative)
            hashes[label][relative] = actual
            require(actual == expected_hash, label + " input hash: " + relative)
            if label == "baseline":
                require(seed_receipt["inputs"][relative] == dict(sha256=actual, bytes=(root / relative).stat().st_size),
                        "baseline receipt binding: " + relative)
    original, derived = load(baseline / CORPUS), load(mask / CORPUS)
    rows = original["corpus"]
    require(len(rows) == COUNTS["items"] and collections.Counter(row["kind"] for row in rows) == KINDS,
            "original corpus inventory")
    for row in rows:
        require(row["mask_context"] is False and row["chat"] is False and row["weight"] == 1,
                "original mask/chat/weight")
        if row["kind"] == "fact":
            require(row["context"].endswith(" ") and row["target"].startswith("Owner"),
                    "unexpected factual textual boundary")
        else:
            require(row["context"] == "", "nonfactual context")
    require(derived == expected_mask_corpus(original), "derived transformation changed more than selected masks")
    for corpus in (original, derived):
        identities = [(native.render_item(item), item["weight"], item["mask_context"]) for item in corpus["corpus"]]
        require(corpus["sha"] == native.sha_of(identities)
                and corpus["items_sha"] == native.items_sha(corpus["corpus"]), "corpus short identities")
    require(receipt["source_corpora"] == {"0": seed_receipt["corpora"]["0"]}, "source corpus receipt metadata")
    for field in ("source", "destination"):
        require(Path(receipt[field]).is_absolute(), "remote receipt path: " + field)
    return original, derived, seed_receipt, receipt, hashes


def validate_fit(fit, corpus, masked):
    expected = dict(FIT, corpus_sha=corpus["sha"], items_sha=corpus["items_sha"],
                    supervised_tokens=3 * COUNTS["supervised_per_epoch" if masked else "original_supervised_per_epoch"],
                    boundary_straddles=COUNTS["boundary_straddles"] if masked else 0)
    expect_fields(fit, expected, "fit")
    require(fit["throughput"]["grad_checkpoint"] is False, "fit gradient checkpointing")
    require(type(fit["final_loss"]) in (int, float) and math.isfinite(fit["final_loss"]), "fit final_loss")


def validate_cues(evaluation, bank):
    rows = evaluation["cues"]
    require(len(rows) == 1313 and len({row["cue_id"] for row in rows}) == 1313, "1313 unique cues required")
    owners = {owner["id"]: owner for owner in bank["owners"]}
    require(len(owners) == 64 and collections.Counter(owner["dose"] for owner in owners.values())
            == {0: 16, 1: 16, 4: 16, 16: 16}, "owner roster")
    expected = {(kind, owner["id"]) for owner in owners.values()
                for kind in (["frame"] if owner["dose"] == 0 else FRAME_KINDS)}
    frames = [(row["kind"], row["owner"]) for row in rows if row["kind"] in FRAME_KINDS]
    require(len(frames) == len(expected) and set(frames) == expected, "frame control inventory")
    zero = {side: [] for side in ("OFF", "ON")}
    for row in rows:
        identity = row["cue_id"]
        if row["kind"] in FRAME_KINDS:
            owner = owners[row["owner"]]
            require(row["a"] == owner["colour"] and row["dose"] == owner["dose"]
                    and row.get("abstain") == [" not"], "frame source join: " + identity)
            if row["kind"] == "frame_similar":
                require(row["cue_id_used"] == owner["similar_id"], "similar ID: " + identity)
        for side in zero:
            score = row[side]
            require(set(score["p_raw"]) == set(score["logp"]) == set(row["cand_tokens"]), "candidate set: " + identity)
            values = [*score["p_raw"].values(), *score["logp"].values(), score["mass"]]
            if "abstain" in row:
                values.append(score["p_abstain"])
                require(score["p_abstain"] >= 0, "negative abstention: " + identity)
            require(all(type(value) in (int, float) and math.isfinite(value) for value in values),
                    "nonfinite score: " + identity)
            require(score["mass"] >= 0 and min(score["p_raw"].values()) >= 0, "negative probability: " + identity)
            if sum(score["p_raw"].values()) == 0 or score["mass"] == 0:
                require(row["kind"] not in FRAME_KINDS, "zero frame probability: " + identity)
                zero[side].append(identity)
    return zero


def compare_evals(before, after):
    first = {row["cue_id"]: row for row in before["cues"]}
    second = {row["cue_id"]: row for row in after["cues"]}
    ignored = {"cues", "adapter", "adapter_arg", "adapter_meta", "seconds", "scorer_calls"}
    metadata = sorted(field for field in before.keys() | after.keys()
                      if field not in ignored and before.get(field) != after.get(field))
    changed, order, off = [], [], []
    maximum = {field: 0.0 for field in ("p_raw", "mass", "logp", "p_abstain")}
    for identity in sorted(first.keys() & second.keys()):
        left, right = first[identity], second[identity]
        if {key: value for key, value in left.items() if key not in ("OFF", "ON")} != {
                key: value for key, value in right.items() if key not in ("OFF", "ON")}:
            changed.append(identity)
        if list(left["cand_tokens"]) != list(right["cand_tokens"]) or any(
                list(left[side][field]) != list(right[side][field])
                for side in ("OFF", "ON") for field in ("p_raw", "logp")):
            order.append(identity)
        if left["OFF"] != right["OFF"]:
            off.append(identity)
        for field in maximum:
            old, new = left["OFF"].get(field), right["OFF"].get(field)
            if isinstance(old, dict) and isinstance(new, dict):
                values = [abs(old[key] - new[key]) for key in old.keys() & new.keys()]
            elif old is not None and new is not None:
                values = [abs(old - new)]
            else:
                values = []
            maximum[field] = max([maximum[field], *values])
    missing, extra = sorted(first.keys() - second.keys()), sorted(second.keys() - first.keys())
    order_equal = list(first) == list(second)
    return dict(missing_ids=missing, extra_ids=extra, cue_order_equal=order_equal,
                eval_metadata_changed=metadata, cue_metadata_changed_ids=changed,
                candidate_order_changed_ids=order, off_changed_ids=off, off_changed_count=len(off),
                off_max_abs=maximum, cue_metadata_match=not any((missing, extra, metadata, changed, order)) and order_equal,
                off_exact_at_serialized_precision=not any((missing, extra, off)))


def check_report(report, gates, masked):
    thresholds = {key: list(value) if isinstance(value, tuple) else value for key, value in native.GATES.items()}
    require(report["gates_thresholds"] == thresholds, "report thresholds changed")
    entry = report["results"][KEY]
    require(0 in entry["banks"] and entry["ref_sleep"] == 4, "report bank0/ref_sleep")
    for name in GATE_NAMES:
        require(entry["per_bank"]["0"]["gates"][name] == gates[name], "report per_bank.0 " + name)
        if entry["banks"] == [0]:
            require(entry["frame"][name] == gates[name] and entry["gates"][name] == gates[name],
                    "report single-bank " + name)
    used_key = "F_r16k16__across__8__1.0__4__0"
    require(report["evals_used"].get(used_key) == TAG, "report eval tag selection")
    if masked:
        require(entry["banks"] == [0] and entry["sleeps"] == [4] and report["n_evals"] == 1
                and set(report["results"]) == {KEY} and report["evals_used"] == {used_key: TAG},
                "mask report contains extra evaluations")
    return dict(present=True, agreement=True, compared="per_bank.0 G9/G11",
                banks=entry["banks"], pooled_ignored=len(entry["banks"]) > 1)


def reduce_run(root, corpus, receipt, masked):
    result = dict(root=str(root), errors=[], warnings=[], hashes={})
    evaluation = None
    weights = [root / ADAPTER / filename for filename in ("adapter_model.safetensors", "adapter_model.bin")]
    result["adapter_weights_present"] = any(path.is_file() for path in weights)
    if not result["adapter_weights_present"]:
        result["warnings"].append("Adapter weights absent; cannot authenticate or replay fitted adapter from capsule.")
    try:
        if not masked:
            for relative, expected in BASE_HASHES.items():
                result["hashes"][relative] = digest(root / relative)
                require(result["hashes"][relative] == expected, "frozen baseline hash: " + relative)
        for relative in (ADAPTER + "/train_meta.json", ADAPTER + "/DONE", EVAL):
            result["hashes"][relative] = digest(root / relative)
        require((root / ADAPTER / "DONE").read_text().strip() == "ok", "fit DONE")
        fit = load(root / ADAPTER / "train_meta.json")
        validate_fit(fit, corpus, masked)
        result["fit"] = {field: fit.get(field) for field in (
            "lr", "steps", "seed", "rank", "tokens", "supervised_tokens", "boundary_straddles", "final_loss", "wall_seconds")}
        evaluation = load(root / EVAL)
        expect_fields(evaluation, EVAL_META, "eval")
        require(evaluation["abstain_check"].get("ok") is True, "eval abstain_check")
        remote = receipt["destination" if masked else "destination_run"]
        require(evaluation["adapter"] == evaluation["adapter_arg"] == str(Path(remote) / ADAPTER), "remote adapter binding")
        expect_fields(evaluation["adapter_meta"], {field: fit[field] for field in ADAPTER_FIELDS}, "eval adapter_meta")
        require(set(evaluation["adapter_meta"]) == set(ADAPTER_FIELDS), "eval adapter_meta field set")
        bank = load(root / "banks/bank0.json")
        result["rounded_zero_nonframe_scores"] = validate_cues(evaluation, bank)
        summary = native.summarize_eval(evaluation, bank)
        gates = native.evaluate_gates(summary, seed=0)
        dose = summary["per_dose"][16]
        require(gates["G9_frame_binding"]["n"] == 16 and gates["G11_abstention"]["passed"] is not None,
                "native G9/G11 unavailable")
        result["metrics"] = dict(
            acquisition={field: dose[field] for field in ("n", "frame_p_off", "frame_p_on", "frame_d_p",
                                                        "frame_mass_off", "frame_mass_on", "I_d_frame")},
            G9=gates["G9_frame_binding"], G11=gates["G11_abstention"],
            controls={field: value for field, value in summary["controls"].items()
                      if field.startswith(("frame_spill", "abstain_"))},
            frame_dose_curve={dose: summary["per_dose"][dose]["frame_d_p"] for dose in (0, 1, 4, 16)})
        report_path = root / "report/report.json"
        if report_path.exists():
            result["hashes"]["report/report.json"] = digest(report_path)
            result["report"] = check_report(load(report_path), gates, masked)
        else:
            result["report"] = dict(present=False, agreement=None)
            require(not masked, "mask native report missing; capture incomplete")
            result["warnings"].append("Baseline report absent: raw native reduction available, report agreement unavailable.")
    except ARTIFACT_ERRORS as error:
        result["errors"].append(type(error).__name__ + ": " + str(error))
    result["valid"] = not result["errors"]
    return result, evaluation


def compare_runs(baseline_root, mask_root):
    baseline, mask = Path(baseline_root).resolve(), Path(mask_root).resolve()
    result = dict(valid=False, errors=[], classification="exploratory mask-placement/supervision-allocation effect",
                  clean_lineage_eligible=False,
                  limitations=["Not equal supervised dose: 422925 mask versus 711213 original labels across three epochs.",
                               "Boundary/token counts are bound to the measured preparation receipt; no tokenizer replay here.",
                               "All 5376 conservative boundary omissions are the first target token ' Owner'.",
                               "Local source/input hashes and OFF agreement do not authenticate runtime model weights or deployed code.",
                               "No selective-writer or prefix-causality claim; cleanup/resources remain Main's responsibility."])
    try:
        source = Path(native.__file__)
        result["native_scorer"] = dict(path=str(source), sha256=digest(source), expected_sha256=SOURCE_HASH,
                                       reduction=["summarize_eval", "evaluate_gates"], bootstrap_seed=0)
        require(result["native_scorer"]["sha256"] == SOURCE_HASH, "native scorer differs from original frozen source")
        require(baseline != mask, "baseline and mask roots must differ")
        original, derived, seed_receipt, receipt, hashes = validate_inputs(baseline, mask)
        result["inputs"] = dict(valid=True, hashes=hashes, counts=receipt["counts"],
                                transformation="exact ordered corpus except selected masks and documented derived metadata",
                                remote_source=receipt["source"], remote_destination=receipt["destination"])
        result["baseline"], before = reduce_run(baseline, original, seed_receipt, False)
        result["mask"], after = reduce_run(mask, derived, receipt, True)
        if before is not None and after is not None:
            result["comparison"] = compare_evals(before, after)
        matched = result.get("comparison", {})
        result["valid"] = (result["baseline"]["valid"] and result["mask"]["valid"]
                           and matched.get("cue_metadata_match", False)
                           and matched.get("off_exact_at_serialized_precision", False))
        if result["valid"]:
            result["delta_mask_minus_baseline"] = {
                "I_d_frame": result["mask"]["metrics"]["G9"]["value"] - result["baseline"]["metrics"]["G9"]["value"],
                "frame_spill": result["mask"]["metrics"]["G9"]["spill"] - result["baseline"]["metrics"]["G9"]["spill"]}
    except ARTIFACT_ERRORS as error:
        result["errors"].append(type(error).__name__ + ": " + str(error))
    result["metrics_status"] = "validated_matched_artifacts" if result["valid"] else "unavailable_as_matched_evidence"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("mask", type=Path)
    parser.add_argument("--output-new", required=True, type=Path)
    args = parser.parse_args(argv)
    output = args.output_new.resolve()
    if any(output.is_relative_to(root.resolve()) for root in (args.baseline, args.mask)):
        parser.error("output must be outside input capsules")
    if args.output_new.exists() or args.output_new.is_symlink():
        parser.error("output already exists; refusing overwrite")
    result = compare_runs(args.baseline, args.mask)
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with args.output_new.open("x") as stream:
        stream.write(text)
    print(text, end="")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
