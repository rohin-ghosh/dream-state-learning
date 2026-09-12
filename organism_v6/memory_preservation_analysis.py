"""Offline 290a9ea0 lambda0/lambda0.1 comparison; optional historical bridge.

Use python -B -m organism_v6.memory_preservation_analysis ZERO POINT_ONE
--output-new RESULT.json [--historical BASELINE]. CPU PyTorch is needed to
validate the positive arm's captured OFF tensor. Never load a model or launch.
Pass --positive-implementation-sha256 explicitly for Main's cache-check repair.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re

from organism_v6 import memory_dose as native
from organism_v6 import memory_mask_analysis as shared
from organism_v6 import memory_preservation as producer


ADAPTER, EVAL, KEY, TAG = shared.ADAPTER, shared.EVAL, shared.KEY, shared.TAG
SOURCE_FILES = {
    "organism_v6/memory_dose.py": "ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3",
    "organism_v6/memory_preservation.py": "a361af202a85e041dad119d57da7a54f583045e9472a358ae8a5efd31a32ef9c",
    "gpu/astra_memory_preservation_diagnostic.py": "33611bfb9b66c8ce26e6aed3b017b1179cfe4bdc912dc25fa76b738b10ec9c4f",
}
HELPER_SHA = "d7ea29190e5f468e39f135bd1404c2b9c64e573ea122793649b75a59ee1aa906"
READER_PRODUCER_SHA = "9a5ad83a246c07e0bf2094bafc9473c66952d56071d7a9cc75e93c2000bdf574"
MODEL_INVENTORY_SHA = "f5d2f69828f4fcacd4a2712fdbe7d1798714fd3f072c309adf06d33eeabe16b7"
ANCHORS_SHA = "cf67c3f4939b09ae46d1dea316c503275f6c9c94af6ddbc9402f360885dd503b"
ORDER_SHA = "3c311ccb5ed8f0814334b928fa4ebaa2999a7a3fca2e0932e6ae5f103e42a55f"
ANCHOR_TOKENS_SHA = "d751daca9549a65f45115df7be4425a52989603b5225fa2b36803cebc0a61446"
VOCAB_SIZE = 152064
GATES = ("G9_frame_binding", "G11_abstention")
RECIPE_FIELDS = dict(rank=8, alpha=16, dropout=0.05, targets=native.LORA_TARGETS,
                     epochs=3, lr=1e-4, bsz=4, max_len=512, seed=2, n_items=12924,
                     steps=9693, total_steps=9693, tokens=749985, supervised_tokens=711213,
                     boundary_straddles=0, truncated_items=0, measure_only=False,
                     ordering="chronological", writer="occurrences", representation="frames",
                     shuffled=False, synthetic=True, tokenization="joint context+target (encode_item)")
ERRORS = shared.ARTIFACT_ERRORS + (ImportError, RuntimeError)
require, load, digest = producer.require, producer.load, producer.digest


def finite(value, label, nonnegative=False):
    require(type(value) in (float, int) and math.isfinite(value), "nonfinite/malformed " + label)
    require(not nonnegative or value >= 0, "negative " + label)
    return value


def fields(actual, expected, label):
    shared.expect_fields(actual, expected, label)


def check_sources():
    require(digest(native.__file__) == SOURCE_FILES["organism_v6/memory_dose.py"], "native frozen source changed")
    require(digest(producer.__file__) == READER_PRODUCER_SHA, "local preservation reader helper changed")
    require(digest(shared.__file__) == HELPER_SHA, "cue/OFF helper source changed")


def read_inputs(root, hashes):
    contents = {}
    for name, expected in producer.INPUT_HASHES.items():
        hashes[name] = digest(root / name)
        require(hashes[name] == expected, "original source hash: " + name)
        contents[name] = load(root / name)
    return contents


def read_artifact(root, name, hashes):
    hashes[name] = digest(root / name)
    return load(root / name)


def validate_plan(plan, root, contents, hashes, implementation):
    fields(plan, dict(status="PREPARED_NOT_TRAINED", clean_lineage=False,
                      worker_cap_seconds=3600, model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY"), "plan")
    expected_sources = dict(SOURCE_FILES, **{"organism_v6/memory_preservation.py": implementation})
    require(plan["source_files"] == expected_sources, "plan frozen source hashes; repair hash must be explicit")
    require(producer.object_hash(plan["model_files"]) == MODEL_INVENTORY_SHA, "plan model inventory hash")
    for field in ("root", "original", "source", "model"):
        require(isinstance(plan[field], str) and Path(plan[field]).is_absolute(), "plan remote " + field)
    require(plan["anchors_sha256"] == ANCHORS_SHA == digest(root / "anchors.json"), "plan anchor bytes")
    hashes["anchors.json"] = digest(root / "anchors.json")
    producer.validate_anchors(root / "anchors.json", contents)
    preflight = plan["token_preflight"]
    fields(preflight, dict(memory_order_sha256=ORDER_SHA, input_tokens_per_epoch=249995,
                          supervised_tokens_per_epoch=237071, truncated_items=0, boundary_straddles=0), "preflight")
    rows = preflight["anchor_input_ids"]
    require(producer.object_hash(rows) == ANCHOR_TOKENS_SHA and len(rows) == 48,
            "preflight anchor token identity")
    require(all(row and all(type(token) is int and 0 <= token < VOCAB_SIZE for token in row) for row in rows),
            "preflight anchor token values")


def validate_fit(fit, setup, plan, corpus, strength):
    implementation = plan["source_files"]["organism_v6/memory_preservation.py"]
    fields(fit, dict(RECIPE_FIELDS, corpus_sha=corpus["sha"], items_sha=corpus["items_sha"],
                     recipe=producer.RECIPE, native_ce_recipe="memory_dose_v1 (mirrors train_adapter.py v1)",
                     coefficient=strength, ce_coefficient=1.0, cache_used=strength > 0,
                     anchors_sha256=ANCHORS_SHA, memory_order_sha256=ORDER_SHA,
                     native_source_sha256=producer.SOURCE_SHA,
                     implementation_sha256=implementation,
                     source_inputs=producer.INPUT_HASHES, model_path=plan["model"]), "fit")
    require(fit["model"] in ("Qwen/Qwen2.5-7B-Instruct", plan["model"]), "fit model locator")
    fields(setup, dict(recipe=producer.RECIPE, coefficient=strength, source_inputs=producer.INPUT_HASHES,
                       native_source_sha256=producer.SOURCE_SHA,
                       implementation_sha256=implementation,
                       anchors_sha256=ANCHORS_SHA, model_files=plan["model_files"], model_path=plan["model"],
                       seed=2, rank=8, lr=1e-4, epochs=3, batch_size=4, expected_steps=9693), "setup")
    fields(fit, producer.BOUNDARY, "fit boundary")
    fields(setup, producer.BOUNDARY, "setup boundary")
    require(fit["throughput"]["grad_checkpoint"] is False, "gradient checkpointing changed")
    for field in ("final_loss", "final_objective", "mean_ce", "wall_seconds"):
        finite(fit[field], "fit." + field, nonnegative=True)
    finite(fit["throughput"]["sec_per_step"], "fit sec_per_step", nonnegative=True)
    require(fit["model_dtype"] == "torch.bfloat16" and fit["trainable_dtypes"]
            and all(dtype in ("torch.float32", "torch.bfloat16") for dtype in fit["trainable_dtypes"]), "fit dtype")
    names = fit["trainable_names"]
    require(names and len(names) == len(set(names)) and all(".lora_A." in name or ".lora_B." in name for name in names)
            and any(".lora_A." in name for name in names) and any(".lora_B." in name for name in names), "LoRA-only trainable inventory")
    require(re.fullmatch(r"[0-9a-f]{64}", fit["initial_lora_sha256"]) is not None, "initial LoRA hash")
    visits = [9693 // 48 + int(index < 9693 % 48) for index in range(48)] if strength else [0] * 48
    rows = plan["token_preflight"]["anchor_input_ids"]
    fields(fit, dict(anchor_visits=visits, anchor_forward_count=sum(visits),
                     anchor_distribution_positions=sum(visits), anchor_input_tokens=sum(len(row) * count for row, count in zip(rows, visits)),
                     kl_dtype="torch.float32" if strength else None), "fit anchor dose")
    if strength:
        finite(fit["final_kl"], "fit.final_kl")
        finite(fit["mean_kl"], "fit.mean_kl")
    else:
        require(fit["final_kl"] is fit["mean_kl"] is fit["cache_metadata"] is None, "lambda0 preservation not skipped")


def validate_losses(root, fit, strength, hashes):
    path = root / ADAPTER / "losses.jsonl"
    hashes[ADAPTER + "/losses.jsonl"] = digest(path)
    require(hashes[ADAPTER + "/losses.jsonl"] == fit["losses_sha256"], "loss log hash")
    tokens = supervised = count = 0
    ce_total = kl_total = seconds = 0.0
    with path.open() as stream:
        for index, line in enumerate(stream):
            row = json.loads(line)
            require(index < 9693, "extra loss records")
            fields(row, dict(step=index + 1, epoch=index // 3231, item_offset=(index % 3231) * 4,
                             anchor_index=index % 48 if strength else None), "loss ordering")
            require(type(row["tokens"]) is int and type(row["supervised_tokens"]) is int
                    and row["supervised_tokens"] > 0 and row["tokens"] - row["supervised_tokens"] == 4,
                    "whole-text loss token accounting")
            finite(row["ce"], "loss CE", nonnegative=True)
            finite(row["objective"], "loss objective")
            finite(row["seconds"], "loss seconds", nonnegative=True)
            if strength:
                finite(row["kl"], "loss KL")
            else:
                require(row["kl"] is None, "lambda0 KL must be absent")
            require(row["objective"] == row["ce"] + strength * (row["kl"] or 0.0), "loss objective scaling")
            tokens += row["tokens"]
            supervised += row["supervised_tokens"]
            ce_total += row["ce"]
            kl_total += row["kl"] or 0.0
            seconds += row["seconds"]
            count += 1
    require((count, tokens, supervised) == (9693, 749985, 711213), "loss log incomplete/dose mismatch")
    fields(fit, dict(final_loss=row["ce"], final_kl=row["kl"], final_objective=row["objective"],
                     mean_ce=ce_total / count, mean_kl=kl_total / count if strength else None), "fit/loss agreement")
    return dict(records=count, tokens=tokens, supervised_tokens=supervised, mean_ce=ce_total / count,
                mean_kl=kl_total / count if strength else None, step_seconds=seconds)


def validate_cache_tensor(path, expected_hash, vocabulary):
    import torch
    require(digest(path) == expected_hash, "cache hash mismatch")
    tensor = torch.load(path, map_location="cpu", weights_only=True)
    require(isinstance(tensor, torch.Tensor) and tensor.dtype == torch.float32
            and tuple(tensor.shape) == (48, vocabulary) and not tensor.requires_grad
            and bool(torch.isfinite(tensor).all()), "cache tensor shape/dtype/finite/detachment")
    sums = tensor.double().log_softmax(-1).exp().sum(-1)
    error = float((sums - 1).abs().max())
    require(torch.allclose(sums, torch.ones_like(sums), atol=1e-10, rtol=0), "cache float64 normalization")
    return dict(tensor_validation="CPU full-shape/finite/detached; float64 normalization only",
                normalization_dtype="torch.float64", normalization_max_error=error,
                cache_storage_dtype="torch.float32", training_kl_dtype="torch.float32")


def validate_cache(root, plan, fit, strength, hashes):
    if not strength:
        require(not (root / "off_cache").exists(), "lambda0 unexpected cache")
        return dict(used=False, seconds=0.0, tensor_validation="not_applicable")
    metadata = read_artifact(root, "off_cache/cache.json", hashes)
    require(metadata == fit["cache_metadata"], "fit/cache metadata disagreement")
    allowed_cache_sources = {SOURCE_FILES["organism_v6/memory_preservation.py"], plan["source_files"]["organism_v6/memory_preservation.py"]}
    require(metadata["implementation_sha256"] in allowed_cache_sources, "cache implementation provenance")
    fields(metadata, dict(model_files=plan["model_files"], model_path=plan["model"],
                          anchors_sha256=ANCHORS_SHA, native_source_sha256=producer.SOURCE_SHA,
                          shape=[48, VOCAB_SIZE], model_dtype="torch.bfloat16", dtype="torch.float32",
                          input_ids=plan["token_preflight"]["anchor_input_ids"], temperature=1.0,
                          adapter=None, position="last input token"), "cache")
    finite(metadata["seconds"], "cache seconds", nonnegative=True)
    tensor_validation = validate_cache_tensor(root / "off_cache/off_logits.pt", metadata["logits_sha256"], VOCAB_SIZE)
    hashes["off_cache/off_logits.pt"] = digest(root / "off_cache/off_logits.pt")
    return dict(used=True, seconds=metadata["seconds"], **tensor_validation,
                bytes=(root / "off_cache/off_logits.pt").stat().st_size, dtype=metadata["dtype"],
                implementation_sha256=metadata["implementation_sha256"],
                implementation_matches_fit=metadata["implementation_sha256"] == fit["implementation_sha256"],
                logits_sha256=metadata["logits_sha256"], torch_version=metadata["torch_version"])


def validate_report(report, gates, summary, historical=False):
    require(report["gates_thresholds"] == json.loads(json.dumps(native.GATES)), "native report thresholds changed")
    entry = report["results"][KEY]
    require(0 in entry["banks"] and entry["ref_sleep"] == 4, "report bank0/ref_sleep")
    require(report["evals_used"].get("F_r16k16__across__8__1.0__4__0") == TAG, "report eval selection")
    if not historical:
        require(entry["banks"] == [0] and entry["sleeps"] == [4] and report["n_evals"] == 1
                and set(report["results"]) == {KEY}
                and report["evals_used"] == {"F_r16k16__across__8__1.0__4__0": TAG}, "extra paired-run report evaluations")
    for name in GATES:
        require(entry["per_bank"]["0"]["gates"][name] == gates[name], "report bank0 " + name)
        if entry["banks"] == [0]:
            require(entry["gates"][name] == gates[name] and entry["frame"][name] == gates[name], "report pooled " + name)
    if entry["banks"] == [0]:
        dose = summary["per_dose"][16]
        for key in ("frame_p_off", "frame_p_on", "frame_d_p", "I_d_frame"):
            require(entry["headline"][key] == dose[key], "report headline " + key)
        require(entry["headline"]["frame_spill"] == summary["controls"]["frame_spill"], "report spill")
    return dict(agreement=True, compared="native per_bank.0 G9/G11", banks=entry["banks"],
                pooled_ignored=len(entry["banks"]) > 1)


def reduce_evaluation(root, fit, remote_root, bank, hashes, historical=False):
    evaluation = read_artifact(root, EVAL, hashes)
    expected = dict(shared.EVAL_META)
    expected.pop("model")
    fields(evaluation, expected, "eval")
    require(isinstance(evaluation["model"], str)
            and evaluation["model"] in ("hf", fit["model"], fit.get("model_path")), "eval model locator")
    require(evaluation["abstain_check"].get("ok") is True, "eval abstention token check")
    require(evaluation["adapter"] == evaluation["adapter_arg"] == str(Path(remote_root) / ADAPTER), "eval remote adapter binding")
    fields(evaluation["adapter_meta"], {field: fit[field] for field in shared.ADAPTER_FIELDS}, "eval fit identity")
    require(set(evaluation["adapter_meta"]) == set(shared.ADAPTER_FIELDS), "eval adapter metadata extras")
    zeros = shared.validate_cues(evaluation, bank)
    summary = native.summarize_eval(evaluation, bank)
    gates = native.evaluate_gates(summary, seed=0)
    require(gates["G9_frame_binding"]["n"] == 16 and gates["G11_abstention"]["passed"] is not None, "incomplete G9/G11")
    dose = summary["per_dose"][16]
    metrics = dict(G9=gates["G9_frame_binding"], G11=gates["G11_abstention"],
                   dose16={key: dose[key] for key in ("n", "frame_p_off", "frame_p_on", "frame_d_p", "frame_mass_off", "frame_mass_on", "I_d_frame")},
                   controls={key: value for key, value in summary["controls"].items() if key.startswith(("frame_spill", "abstain_"))},
                   frame_dose_curve={dose: summary["per_dose"][dose]["frame_d_p"] for dose in (0, 1, 4, 16)})
    report_path = root / "report/report.json"
    if historical and not report_path.exists():
        report = dict(agreement=None, warning="historical report absent; native raw reduction only")
    else:
        report = validate_report(read_artifact(root, "report/report.json", hashes), gates, summary, historical)
    return dict(metrics=metrics, report=report, rounded_zero_nonframe_scores=zeros,
                eval_seconds=finite(evaluation["seconds"], "eval seconds", nonnegative=True)), evaluation, summary


def adapter_availability(root, result):
    paths = [root / ADAPTER / name for name in ("adapter_model.safetensors", "adapter_model.bin")]
    present = [path for path in paths if path.is_file()]
    result["adapter_weights"] = dict(present=bool(present), hashes={path.name: digest(path) for path in present})
    if not present:
        result["warnings"].append("Adapter weights absent from capsule; fitted weights cannot be replayed/authenticated here.")


def reduce_run(root, strength, implementation):
    root = Path(root).resolve()
    result = dict(root=str(root), coefficient=strength, errors=[], warnings=[], hashes={})
    internal = {}
    try:
        contents = read_inputs(root, result["hashes"])
        plan = read_artifact(root, "plan.json", result["hashes"])
        fields(plan, dict(coefficient=strength), "plan")
        validate_plan(plan, root, contents, result["hashes"], implementation)
        fit = read_artifact(root, ADAPTER + "/train_meta.json", result["hashes"])
        setup = read_artifact(root, ADAPTER + "/setup.json", result["hashes"])
        require((root / ADAPTER / "DONE").read_text().strip() == "ok", "fit DONE")
        result["hashes"][ADAPTER + "/DONE"] = digest(root / ADAPTER / "DONE")
        validate_fit(fit, setup, plan, contents[producer.CORPUS], strength)
        result["losses"] = validate_losses(root, fit, strength, result["hashes"])
        result["cache"] = validate_cache(root, plan, fit, strength, result["hashes"])
        evaluation_result, evaluation, summary = reduce_evaluation(root, fit, plan["root"], contents["banks/bank0.json"], result["hashes"])
        result.update(evaluation_result)
        result["fit"] = fit
        result["model_inventory_sha256"] = producer.object_hash(plan["model_files"])
        result["model_evidence"] = "recorded model-file inventory bound across plan/setup/cache; base files not present/rehashed by this reducer"
        result["costs"] = dict(fit_wall_seconds=fit["wall_seconds"], cache_seconds=result["cache"]["seconds"],
                               eval_seconds=result["eval_seconds"], recorded_step_seconds=result["losses"]["step_seconds"],
                               captured_stage_seconds=fit["wall_seconds"] + result["cache"]["seconds"] + result["eval_seconds"],
                               scope="recorded stage clocks, not full controller/lease/billing time")
        internal = dict(plan=plan, fit=fit, evaluation=evaluation, summary=summary)
        launch_path = root / "logs/launch_receipt.json"
        if launch_path.exists():
            launch = read_artifact(root, "logs/launch_receipt.json", result["hashes"])
            require(launch["plan_sha256"] == result["hashes"]["plan.json"], "launch/plan byte binding")
            result["operational"] = {key: launch.get(key) for key in ("pid", "node", "device", "started_utc", "status")}
        result["warnings"].append("Operational cleanup/resource reconciliation is separate and remains Main's responsibility.")
    except ERRORS as error:
        result["errors"].append(type(error).__name__ + ": " + str(error))
    adapter_availability(root, result)
    result["valid"] = not result["errors"]
    return result, internal


def paired_metrics(left, right):
    before, after = left["summary"], right["summary"]
    owners = sorted(owner for owner, row in before["per_owner"].items() if row["dose"] == 16)
    differences = [after["per_owner"][owner]["I_d_frame"] - before["per_owner"][owner]["I_d_frame"] for owner in owners]
    return dict(direction="lambda0.1 minus lambda0", dose16={
        key: after["per_dose"][16][key] - before["per_dose"][16][key]
        for key in ("frame_p_off", "frame_p_on", "frame_d_p", "frame_mass_off", "frame_mass_on", "I_d_frame")},
        spill={key: after["controls"][key] - before["controls"][key]
               for key in ("frame_spill", "frame_spill_similar", "frame_spill_unexposed", "frame_spill_bicycle")},
        paired_owner_I_d_change=native.paired_bootstrap(differences, seed=0),
        interpretation="one exploratory fit pair; owner bootstrap is not replication over learner seeds")


def historical_bridge(root, current):
    root = Path(root).resolve()
    result = dict(root=str(root), errors=[], warnings=[], hashes={})
    try:
        contents = read_inputs(root, result["hashes"])
        fit = read_artifact(root, ADAPTER + "/train_meta.json", result["hashes"])
        receipt = read_artifact(root, "seed_run_receipt.json", result["hashes"])
        require(isinstance(fit.get("model"), str) and fit["model"], "historical model locator missing")
        fields(fit, dict(RECIPE_FIELDS, recipe="memory_dose_v1 (mirrors train_adapter.py v1)",
                         corpus_sha=contents[producer.CORPUS]["sha"], items_sha=contents[producer.CORPUS]["items_sha"]), "historical fit")
        finite(fit["final_loss"], "historical final_loss")
        require(fit["throughput"]["grad_checkpoint"] is False, "historical checkpointing")
        require((root / ADAPTER / "DONE").read_text().strip() == "ok", "historical DONE")
        reduced, evaluation, summary = reduce_evaluation(root, fit, receipt["destination_run"], contents["banks/bank0.json"], result["hashes"], historical=True)
        result.update(reduced)
        result["model_display"] = fit.get("model")
        result["historical_weight_inventory"] = "unavailable; never infer weight identity from model names or matching OFF scores"
        pins_path = root / "local_base_pins.json"
        if pins_path.exists():
            pins = read_artifact(root, "local_base_pins.json", result["hashes"])
            expected = current["plan"]["model_files"]
            result["historical_weight_inventory"] = dict(recorded_current_files_match=all(pins["files"].get(name) == checksum for name, checksum in expected.items()),
                                                        independently_rehashed_base_files=False)
        result["fit_metadata_differences"] = {key: dict(historical=fit.get(key), current=current["fit"].get(key))
            for key in sorted(fit.keys() | current["fit"].keys()) if fit.get(key) != current["fit"].get(key)}
        before, after = dict(evaluation), dict(current["evaluation"])
        result["eval_model_locator_difference"] = dict(historical=before.get("model"), current=after.get("model"))
        before["model"] = after["model"] = "model locator excluded for descriptive historical comparison only"
        result["comparison"] = shared.compare_evals(before, after)
        comparison = result["comparison"]
        if comparison["cue_metadata_match"] and comparison["off_exact_at_serialized_precision"]:
            result["current_lambda0_minus_historical"] = paired_metrics(dict(summary=summary), current)
            result["current_lambda0_minus_historical"]["direction"] = "current lambda0 minus historical native CE"
        result["interpretation"] = "descriptive bridge, not a third matched arm or proof of native/clone equivalence"
    except ERRORS as error:
        result["errors"].append(type(error).__name__ + ": " + str(error))
    adapter_availability(root, result)
    result["valid_artifacts"] = not result["errors"]
    return result


def compare_runs(zero_root, positive_root, historical=None, positive_implementation=None):
    result = dict(valid=False, errors=[], label="exploratory fixed-prefix OFF-preservation diagnostic",
                  claim_boundary="G9 acquisition/locality; G11 unchanged and measured; no readiness or OEL/SDFT reproduction claim")
    try:
        check_sources()
        original_implementation = SOURCE_FILES["organism_v6/memory_preservation.py"]
        positive_implementation = positive_implementation or original_implementation
        require(re.fullmatch(r"[0-9a-f]{64}", positive_implementation) is not None, "explicit implementation SHA256 required")
        require(Path(zero_root).resolve() != Path(positive_root).resolve(), "paired roots must differ")
        result["lambda0"], zero = reduce_run(zero_root, 0.0, original_implementation)
        result["lambda01"], positive = reduce_run(positive_root, 0.1, positive_implementation)
        result["native_sources"] = SOURCE_FILES
        result["implementation_provenance"] = dict(lambda0=original_implementation, lambda01=positive_implementation,
            equal=original_implementation == positive_implementation, reader_helper=READER_PRODUCER_SHA,
            differing_hash_scope="explicit caller authorization for cache-validation arithmetic only; no CE/KL objective change inferred from hash equality",
            actual_code_diff_verified_here=False)
        if result["lambda0"]["valid"] and result["lambda01"]["valid"]:
            comparisons = dict(model_file_inventories=zero["plan"]["model_files"] == positive["plan"]["model_files"])
            for key in ("initial_lora_sha256", "memory_order_sha256", "anchors_sha256", "model_dtype", "trainable_dtypes", "trainable_names", "torch_version"):
                comparisons[key] = zero["fit"][key] == positive["fit"][key]
            result["matched_fit_controls"] = comparisons
            result["comparison"] = shared.compare_evals(zero["evaluation"], positive["evaluation"])
            result["valid"] = all(comparisons.values()) and result["comparison"]["cue_metadata_match"] and result["comparison"]["off_exact_at_serialized_precision"]
            if result["valid"]:
                result["paired_effect"] = paired_metrics(zero, positive)
            else:
                result["errors"].append("paired fit controls or exact cue/OFF matching failed; no matched-effect claim")
        if historical is not None:
            result["historical_bridge"] = historical_bridge(historical, zero) if result["lambda0"]["valid"] else dict(
                valid_artifacts=False, errors=["current lambda0 unavailable; bridge not computed"])
    except ERRORS as error:
        result["errors"].append(type(error).__name__ + ": " + str(error))
    result["metrics_status"] = "validated_current_pair" if result["valid"] else "unavailable_as_matched_evidence"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zero", type=Path)
    parser.add_argument("point_one", type=Path)
    parser.add_argument("--historical", type=Path)
    parser.add_argument("--positive-implementation-sha256", help="explicitly approved cache-check-only retry trainer hash")
    parser.add_argument("--output-new", type=Path, required=True)
    args = parser.parse_args(argv)
    inputs = [args.zero, args.point_one] + ([args.historical] if args.historical else [])
    if any(args.output_new.resolve().is_relative_to(path.resolve()) for path in inputs):
        parser.error("output must be outside input capsules")
    if args.output_new.exists() or args.output_new.is_symlink():
        parser.error("output exists; refusing overwrite")
    result = compare_runs(args.zero, args.point_one, args.historical, args.positive_implementation_sha256)
    text = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    with args.output_new.open("x") as stream:
        stream.write(text)
    print(text, end="")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
