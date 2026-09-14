"""Local CPU reduction: ROOT/collect, ROOT/before, ROOT/{SELECTED,UNIFORM}/{train,after}.

Use --collection-root for the unchanged attempt1 collect directory if ROOT/collect
is not present (a directory symlink is also supported). Keep native JSON/JSONL,
CALL files and new_task/ trees, not model/tokenizer/adapter files. Supply frozen
--source-root and original --a1-collection / --a2-collection JSON files. The HELD
classifier remains A2; fresh recall/routing is A3. JSON goes to stdout; exit 0
requires six valid terminal stages and a matching pair. No evidence is written.

All stages: REQUEST.json, INPUTS.json, RESULT.json or FAILED.json.
Collect: COLLECTION.json, CALL_*.json. Before/after: HELD_AUDIT.json,
ACTUAL_CASES.json, ACTUAL_READERS.json, CALL_*.json, new_task/*.json,
OLD_RECALL_W{0,8}_{01..12}.json. Train: TRAINING_ROWS.json, MASKS.json,
RECIPE.json, LOSSES.jsonl, ADAPTER_PROVENANCE.json. Missing stages stay pending.
"""

import argparse
from collections import Counter
from hashlib import sha256
import importlib
import json
import math
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import astra_adult_cycle_reduce as adult
from tools import astra_selected_reader_repair_reduce as repair


ARMS = ("SELECTED", "UNIFORM")
SCHEMA = "DEV_FRESH_READER_AUDIT_CYCLE_V1"
AUDIT_POLICY = "ALL_CAPTURED_READS_WITHOUT_SYNTHETIC_TRANSITION_V2"
require, read, digest = adult.require, adult.read, adult.digest
ERRORS = (ValueError, KeyError, TypeError, IndexError, OSError, StopIteration)


def indexes(update, arm, selected):
    require(type(update) is int and 1 <= update <= 100 and arm in ARMS, "schedule_bounds")
    require(type(selected) in (list, tuple) and 1 <= len(selected) <= 8
            and all(type(index) is int and 0 <= index < 4 for index in selected), "source_pointer_bounds")
    pool = [178 + 4 * view + index for index in selected for view in range(8)]
    if arm == "UNIFORM":
        pool = list(range(178, 210))
    offset = update - 1
    shared = [offset % 96, 96 + offset % 82]
    return (shared + [pool[(2 * offset + slot) % len(pool)] for slot in range(2)],
            shared + [178 + (2 * offset + slot) % 32 for slot in range(2)])


def audit_schedule(masks, losses, arm, selected):
    require(len(masks) == 210 and len(losses) == 100, "terminal_210_masks_100_updates")
    for mask in masks:
        inputs, labels, targets = mask["input_ids"], mask["labels"], mask["target_ids"]
        require(inputs and len(inputs) == len(labels) and labels[0] == -100, "masked_prefix")
        positions = [index for index, label in enumerate(labels) if label != -100]
        require(positions and positions == list(range(positions[0], positions[-1] + 1)), "target_only_span")
        require(targets == [inputs[index] for index in positions] == [labels[index] for index in positions]
                and targets[-1] == 151645 and inputs[positions[-1] + 1:] == [198], "target_eot_template")
    counts, actual_total, reference_total = Counter(), 0, 0
    for update, loss in enumerate(losses, 1):
        actual, reference = indexes(update, arm, selected)
        require(loss["update"] == update and loss["row_indexes"] == actual
                and loss["reference_row_indexes"] == reference, "actual_reference_schedule_drift")
        actual_count = sum(len(masks[index]["target_ids"]) for index in actual)
        reference_count = sum(len(masks[index]["target_ids"]) for index in reference)
        require(loss["actual_label_count"] == loss["active_label_count"] == actual_count
                and loss["reference_label_count"] == loss["original_label_count"] == reference_count
                and math.isclose(loss["loss_scale"], actual_count / reference_count, rel_tol=1e-12), "uniform_denominator_drift")
        require(math.isfinite(loss["loss"]) and math.isfinite(loss["actual_mean_loss"])
                and math.isclose(loss["loss"], loss["actual_mean_loss"] * loss["loss_scale"], rel_tol=2e-6, abs_tol=1e-9),
                "nonfinite_or_scaled_loss_drift")
        counts.update(actual)
        actual_total += actual_count
        reference_total += reference_count
    budgets = dict(memory_presentations=sum(counts[index] for index in range(96)),
                   behavior_presentations=sum(counts[index] for index in range(96, 178)),
                   cue_presentations=sum(counts[index] for index in range(96, 116)),
                   lesson_presentations=sum(counts[index] for index in range(116, 178)),
                   new_memory_presentations=sum(counts[index] for index in range(178, 210)))
    require(list(budgets.values()) == [100, 100, 38, 62, 200], "group_doses")
    return dict(updates=100, budgets=budgets, actual_supervised_tokens=actual_total, reference_supervised_tokens=reference_total,
                new_fact_presentations=[sum(counts[178 + 4 * view + index] for view in range(8)) for index in range(4)],
                old_bank_presentations=[sum(counts[index] for index in range(start, start + 32)) for start in (0, 32, 64)],
                row_counts=dict(counts), first_indexes=losses[0]["row_indexes"], last_indexes=losses[-1]["row_indexes"],
                scale_min=min(loss["loss_scale"] for loss in losses), scale_max=max(loss["loss_scale"] for loss in losses))


def call_files(directory, captures):
    paths = sorted(directory.glob("CALL_*.json"))
    require([path.name for path in paths] == ["CALL_%03d.json" % index for index in range(len(captures))], "audit_call_count")
    for path, capture in zip(paths, captures):
        require(read(path) == {key: capture[key] for key in ("messages", "response", "error")}, "actual_call_join")
        response = adult.generation(capture["response"])
        require(type(response["prompt_tokens"]) is int and 0 < response["prompt_tokens"] <= 2048
                and len(response["token_ids"]) <= 160, "captured_token_budget")
    return dict(model_calls=len(captures), prompt_tokens=sum(capture["response"]["prompt_tokens"] for capture in captures),
                output_tokens=sum(len(capture["response"]["token_ids"]) for capture in captures))


def routing(directory, result, collection, a1, a2, runtime):
    require(result["fits"] == 0 and result["parent_present"] is False and result["reader_wrapper"] == 0, "readout_contract")
    panels = dict(result["panels"])
    extra_rows = {}
    for wrapper in (0, 8):
        name = "OLD_RECALL_W%d" % wrapper
        panel = panels[name]
        rows = [read(directory / (name + "_%02d.json" % index)) for index in range(1, 13)]
        require(panel["rows"] == rows and panel["denominator"] == 12, "all_twelve_old_records_required")
        extra_rows[name] = rows[8:]
        panels[name] = dict(panel, rows=rows[:8], denominator=8, correct=sum(row["correct"] for row in rows[:8]))
    native_calls = len(list((directory / "new_task").glob("CALL_*.json")))
    view = dict(result, panels=panels, model_calls=native_calls + 16,
                arguments=dict(result.get("arguments", {}), reader_wrapper=0))
    summary = adult.readout_summary(directory, view, collection, runtime, a1)
    extra = []
    for wrapper in (0, 8):
        name = "OLD_RECALL_W%d" % wrapper
        def consume(response, messages):
            require(response["messages"] == messages, "A2_old_probe_prompt_drift")
            extra.append(response)
        probes = adult.audit_probes(extra_rows[name], a2["bank"], wrapper, consume, runtime)
        panel = summary["panels"][name]
        panel.update(denominator=12, correct=panel["correct"] + probes["correct"], a2_correct=probes["correct"],
                     raw_outputs=panel["raw_outputs"] + probes["raw_outputs"])
        require(result["panels"][name]["correct"] == panel["correct"], "twelve_fact_retention_total")
    summary.update(model_calls=summary["model_calls"] + len(extra),
                   prompt_tokens=summary["prompt_tokens"] + sum(response["prompt_tokens"] for response in extra),
                   output_tokens=summary["output_tokens"] + sum(len(response["token_ids"]) for response in extra))
    summary["roles"]["old_memory_probe"] = 24
    summary["text_failures"] = {name: repair.text_errors(result["panels"][name]["rows"], runtime.micro)
                                for name in ("RECALL_W0", "RECALL_W8", "OLD_RECALL_W0", "OLD_RECALL_W8")}
    return summary


def readout(directory, result, collection, a1, a2, runtime):
    summary = routing(directory, result, collection, a1, a2, runtime)
    held_cases = runtime.lesson.build_cases([dict(event=episode["fact"]["event"], raw=episode["event"]["raw"])
                                           for episode in a2["episodes"]], "HELD")
    held = read(directory / "HELD_AUDIT.json")
    repair.replay_captures(held, lambda generate: runtime.lesson.collect_cases(held_cases, generate, coached=False))
    require(held["model_calls"] == 16 and not held["rows"] and held["parent_present"] is False, "held_A2_classifier_contract")
    cases = runtime.audit.build_cases(collection, result["panels"]["OWN_PARAMETRIC"]["episodes"])
    require(read(directory / "ACTUAL_CASES.json") == cases, "actual_v2_case_join")
    audit = read(directory / "ACTUAL_READERS.json")
    repair.replay_captures(audit, lambda generate: runtime.audit.collect_audit(cases, generate))
    counts = call_files(directory, held["captures"] + audit["captures"])
    require(result["model_calls"] == summary["model_calls"] + counts["model_calls"], "complete_native_call_accounting")
    summary.update(routing_model_calls=summary["model_calls"], audit_model_calls=counts["model_calls"],
                   model_calls=result["model_calls"], total_prompt_tokens=summary["prompt_tokens"] + counts["prompt_tokens"],
                   total_output_tokens=summary["output_tokens"] + counts["output_tokens"],
                   classifier=dict(bank="A2_HELD_NOT_A3", summary=held["summary"], captures=held["captures"]), actual_audit=audit)
    return summary


def training(directory, result, collection, a1, a2, selected, runtime):
    rows = read(directory / "TRAINING_ROWS.json")
    require([len(rows[key]) for key in ("memory_rows", "cue_rows", "lesson_rows", "new_rows")] == [96, 20, 62, 32], "row_layout")
    require(rows["new_rows"] == runtime.fresh.replay_collection(collection)
            and rows["memory_rows"][32:64] == runtime.adult.replay_collection(a1)
            and rows["memory_rows"][64:] == runtime.adult.replay_collection(a2), "source_rows_drift")
    require(sha256(adult.canonical(rows["memory_rows"]) + b"\n").hexdigest() == result["source"]["memory_rows_sha256"],
            "old_memory_document_join")
    for row in rows["lesson_rows"]:
        runtime.lesson._validate_row(row)
    config = runtime.trainer.recipe(result["arm"], selected, memory_count=96)
    config["new_source_events"] = [row["event"] for row in rows["new_rows"][:4]]
    require(read(directory / "RECIPE.json") == result["recipe"]
            and adult.canonical(result["recipe"]) == adult.canonical(config), "exact_native_recipe")
    provenance = read(directory / "ADAPTER_PROVENANCE.json")
    require(all(result[key] == value for key, value in provenance.items() if key != "schema"), "adapter_provenance_join")
    hashes = result["training_artifact_sha256"]
    require(set(hashes) == {"MASKS.json", "RECIPE.json", "LOSSES.jsonl"}, "training_inventory")
    for name, expected in hashes.items():
        require(digest(directory / name) == expected, "training_hash_drift:" + name)
    loss_path = directory / "LOSSES.jsonl"
    require(not loss_path.is_symlink() and loss_path.stat().st_size <= 16 * 1024 * 1024, "bounded_losses")
    summary = audit_schedule(read(directory / "MASKS.json"), [json.loads(line) for line in loss_path.read_text().splitlines()], result["arm"], selected)
    for key in ("updates", "budgets", "actual_supervised_tokens", "reference_supervised_tokens", "new_fact_presentations"):
        require(result[key] == summary[key], "training_receipt_total:" + key)
    require(all(result[key] == value for key, value in summary["budgets"].items()), "receipt_doses")
    require(result["fits"] == 1 and result["material_arm"] == result["arm"] and result["selected_source_indexes"] == selected
            and result["adapter_state_before"] == result["loaded_adapter_state_sha256"] == result["source"]["initial_adapter_state_sha256"]
            and result["adapter_state_after"] != result["adapter_state_before"], "matched_changed_adapter")
    require(result["supervised_tokens"] == summary["actual_supervised_tokens"]
            and result["original_supervised_tokens"] == summary["reference_supervised_tokens"]
            and result["loss_normalization"] == repair.NORMALIZATION, "token_aliases_and_normalization")
    require(all(result[key] == config[key] for key in ("train_seed", "learning_rate", "optimizer", "new_source_events")),
            "recipe_receipt_aliases")
    summary.update(initial_state=result["adapter_state_before"], final_state=result["adapter_state_after"], source=result["source"],
                   selected_source_indexes=selected, masks_sha256=digest(directory / "MASKS.json"), rows_sha256=digest(directory / "TRAINING_ROWS.json"))
    return summary


def check_receipt(directory, result, phase, arm, runtime):
    require(result["schema"] == SCHEMA and result["phase"] == phase and result["arm"] == arm
            and result["parent_present"] is False and result["frozen_base_unchanged"] is True, "stage_receipt")
    request = read(directory / "REQUEST.json")
    for key in ("schema", "phase", "arm", "arguments", "started_unix", "entry_sha256", "parent_present"):
        require(request[key] == result[key], "request_join:" + key)
    require(read(directory / "INPUTS.json") == result["source"], "source_inputs_join")
    require(result["source"]["fresh_helper_sha256"] == digest(runtime.root / "organism_v6/experienced_event_fresh_reader_cycle.py")
            and result["source"]["master"] == runtime.fresh.MASTER, "unchanged_fresh_collection_source")
    if phase != "collect":
        require(result["entry_sha256"] == digest(runtime.root / "gpu/astra_fresh_reader_cycle.py")
                and result["audit_policy"] == AUDIT_POLICY
                and result["audit_helper_sha256"] == digest(runtime.root / "organism_v6/experienced_event_fresh_reader_audit.py"), "v2_source_policy")
    if phase == "train":
        require(result["trainer_sha256"] == digest(runtime.root / "gpu/astra_selected_reader_repair_train.py"), "trainer_source")


def reduce(root, runtime=None, a1=None, a2=None, collection_root=None):
    root = Path(root)
    stages, results = {}, {}
    collection = None
    report = dict(stages=stages, pending=[], failed=[], invalid=[], limitations=[
        "Receipt consistency, not independent base/adapter authentication; no tokenizer re-encoding.",
        "Historical collect driver may precede v2; its unchanged collection-helper hash is checked.",
        "A2 HELD classifier and A3 recall are distinct; strict recall scores are never replaced by field diagnostics.",
        "Both arms cover all four A3 facts here: contrast order/repetition/dose, not coverage.",
        "Shared 62-lesson curriculum; one lineage/bank, not H1/H2. Wall-time rates are not GPU utilization."])
    specs = [("collect", Path(collection_root) if collection_root else root / "collect", None), ("before", root / "before", None)]
    specs += [(arm + "/" + phase, root / arm / phase, arm) for arm in ARMS for phase in ("train", "after")]
    for label, directory, arm in specs:
        phase = label.split("/")[-1]
        info = None
        try:
            info = repair.terminal(directory)
            if info["status"] == "COMPLETE":
                result = info.pop("result")
                require(runtime is not None and a1 is not None and a2 is not None, "source_A1_A2_inputs_required")
                require(a1.get("cycle", 1) == 1 and a2.get("cycle") == 2
                        and len(runtime.adult.replay_collection(a1)) == len(runtime.adult.replay_collection(a2)) == 32, "original_A1_A2_collections")
                check_receipt(directory, result, phase, arm, runtime)
                old_bank = runtime.micro.build_bank(runtime.source.MASTER) + a1["bank"] + a2["bank"]
                require(result["source"]["prior_event_ids"] == [fact["event"] for fact in old_bank], "all_twelve_prior_ids")
                if phase == "collect":
                    document = read(directory / "COLLECTION.json")
                    require(digest(directory / "COLLECTION.json") == result["collection_sha256"], "collection_hash")
                    require(len(runtime.fresh.replay_collection(document)) == 32 and result["accepted_events"] == document["accepted_events"] == 4
                            and result["fits"] == 0 and result["loaded_adapter_state_sha256"] == result["source"]["initial_adapter_state_sha256"], "initial_grounded_collection")
                    counts = call_files(directory, document["captures"])
                    require(result["model_calls"] == counts["model_calls"] == document["count"] == 8, "collection_calls")
                    collection = document
                    info.update(counts, rows=32, accepted_events=4, collection_sha256=result["collection_sha256"])
                else:
                    require(collection is not None and "collect" in results and result["source"] == results["collect"]["source"]
                            and result["collection_result_sha256"] == stages["collect"]["result_sha256"], "collection_parent_join")
                    if phase == "before":
                        require(result["loaded_adapter_state_sha256"] == result["source"]["initial_adapter_state_sha256"], "before_initial_actor")
                        info.update(readout(directory, result, collection, a1, a2, runtime))
                    else:
                        require("before" in results and result["before_result_sha256"] == stages["before"]["result_sha256"], "before_receipt_join")
                        selected = [index for index in stages["before"]["actual_audit"]["chosen_source_indexes"] if index is not None]
                        if phase == "train":
                            info.update(training(directory, result, collection, a1, a2, selected, runtime))
                            if info.get("seconds", 0) > 0:
                                info["updates_per_receipt_second"] = 100 / info["seconds"]
                                info["actual_supervised_tokens_per_receipt_second"] = info["actual_supervised_tokens"] / info["seconds"]
                        else:
                            require(arm + "/train" in results and result["training_result_sha256"] == stages[arm + "/train"]["result_sha256"]
                                    and result["loaded_adapter_state_sha256"] == stages[arm + "/train"]["final_state"], "saved_adapter_reload_join")
                            info.update(readout(directory, result, collection, a1, a2, runtime))
                results[label] = result
            elif info["status"] == "FAILED":
                failure = info["failure"]
                info["partial_raw_panels"] = failure.get("panels")
                if failure.get("panels") and collection is not None:
                    try:
                        info["partial_routing"] = routing(directory, failure, collection, a1, a2, runtime)
                        info["partial_only_no_terminal_base_verification"] = True
                    except ERRORS as error:
                        info["partial_replay_error"] = str(error)
                if phase == "collect" and runtime is not None and (directory / "COLLECTION.json").exists():
                    try:
                        document = read(directory / "COLLECTION.json")
                        info["failed_collection"] = dict(record=document, replayed_rows=len(runtime.fresh.replay_collection(document)))
                    except ERRORS as error:
                        info["partial_replay_error"] = str(error)
        except ERRORS as error:
            info = dict(status="INVALID", error=type(error).__name__ + ": " + str(error))
        info["path"] = str(directory)
        stages[label] = info
        if info["status"] != "COMPLETE":
            report[{"PENDING": "pending", "FAILED": "failed", "INVALID": "invalid"}[info["status"]]].append(label)
    report["pair"] = repair.pair_summary({arm: {"train": stages[arm + "/train"]} for arm in ARMS})
    if "before" in results:
        pointers = stages["before"]["actual_audit"]["chosen_source_indexes"]
        report["before_pointers"] = pointers
        report["both_materials_cover_all_four"] = set(index for index in pointers if index is not None) == set(range(4))
    report["status"] = ("INVALID_EVIDENCE" if report["invalid"] or report["pair"]["status"] == "MISMATCH" else
                        "FAILED_STAGES" if report["failed"] else "PARTIAL_EVIDENCE" if report["pending"] else "COMPLETE")
    return report


def load_source(root):
    runtime = adult.load_source(root)
    for label, name in dict(fresh="organism_v6.experienced_event_fresh_reader_cycle",
                            audit="organism_v6.experienced_event_fresh_reader_audit",
                            lesson="organism_v6.experienced_event_reader_audit_lesson",
                            trainer="gpu.astra_selected_reader_repair_train").items():
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve() == runtime.root / (name.replace(".", "/") + ".py"), "captured_source_mismatch")
        setattr(runtime, label, module)
    return runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path)
    for name in ("source-root", "collection-root", "a1-collection", "a2-collection"):
        parser.add_argument("--" + name, type=Path)
    options = parser.parse_args()
    report = reduce(options.root, load_source(options.source_root) if options.source_root else None,
                    read(options.a1_collection) if options.a1_collection else None,
                    read(options.a2_collection) if options.a2_collection else None, options.collection_root)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0 if report["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
