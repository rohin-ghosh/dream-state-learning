"""CPU-only reduction of locally captured selected-reader-repair cells.

Layout: ROOT/{AUDIT_SFT_SELECTED,AUDIT_SFT_UNIFORM,
              AUDIT_LOSS_OFF_SELECTED,AUDIT_LOSS_OFF_UNIFORM}/{train,after}/.
Both stages: REQUEST.json, INPUTS.json, RESULT.json or FAILED.json.
Train: TRAINING_ROWS.json, MASKS.json, RECIPE.json, LOSSES.jsonl,
ADAPTER_PROVENANCE.json. After: AFTER_HELD.json, CALL_*.json,
NEXT_ACTUAL_CASES.json, NEXT_ACTUAL_READERS.json, OLD_RECALL_W{0,8}_*.json,
and the complete new_task/ JSON tree. Keep failed/partial captures; no adapters.
Supply the original A2 COLLECTION.json and prior A1 COLLECTION.json separately.
Run with --source-root pointing at the matching captured source tree. Output is
JSON on stdout; missing/failed/invalid stages remain explicit, without scores.
Example: python3 tools/astra_selected_reader_repair_reduce.py CAPTURE_ROOT
         --source-root SOURCE --collection A2/COLLECTION.json
         --prior-collection A1/COLLECTION.json
Exit 0 means all eight stages and both within-state pairs validated; otherwise
exit 1. Missing stages need no collection/source inputs. Replayable failed-stage
panels are reported as partial, never as a terminal successful readout.
Receipt joins establish consistency, not independent adapter/base authenticity.
No tokenizer re-encoding, remote IO, models, writes, or fits are performed.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib
import json
import math
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import astra_adult_cycle_reduce as adult_reduce


PARENTS = ("AUDIT_SFT", "AUDIT_LOSS_OFF")
MATERIALS = ("SELECTED", "UNIFORM")
SELECTED = {"AUDIT_SFT": [1, 3, 3], "AUDIT_LOSS_OFF": [1]}
SCHEMA = "DEV_SELECTED_ACTUAL_READER_REPAIR_V1"
NORMALIZATION = "UNIFORM_BATCH_CAUSAL_LABEL_COUNT"
require, read, digest = adult_reduce.require, adult_reduce.read, adult_reduce.digest


def timing(receipt):
    started, finished = receipt.get("started_unix"), receipt.get("finished_unix")
    summary = dict(started_unix=started, finished_unix=finished, timing_status="UNAVAILABLE_OR_INVALID")
    if all(type(value) in (int, float) and math.isfinite(value) for value in (started, finished)) and finished >= started:
        try:
            summary.update(start_utc=datetime.fromtimestamp(started, timezone.utc).isoformat(),
                           finish_utc=datetime.fromtimestamp(finished, timezone.utc).isoformat(),
                           seconds=finished - started, timing_status="VALID_RECEIPT_WALL_TIME")
        except (ValueError, OverflowError, OSError):
            pass
    return summary


def terminal(directory):
    if (directory / "FAILED.json").exists():
        failure = read(directory / "FAILED.json")
        return dict(status="FAILED", failure=failure, **timing(failure))
    if not (directory / "RESULT.json").exists():
        return dict(status="PENDING", request_present=(directory / "REQUEST.json").exists())
    result = read(directory / "RESULT.json")
    require(result.get("status") == "COMPLETE", "unexpected_stage_terminal")
    return dict(status="COMPLETE", result=result, result_sha256=digest(directory / "RESULT.json"), **timing(result))


def indexes(update, material, selected):
    require(type(update) is int and 1 <= update <= 100 and material in MATERIALS, "schedule_bounds")
    require(type(selected) in (list, tuple) and 1 <= len(selected) <= 8
            and all(type(index) is int and 0 <= index < 4 for index in selected), "selection_bounds")
    pool = [162 + 4 * view + index for index in selected for view in range(8)]
    if material == "UNIFORM":
        pool = list(range(162, 194))
    offset = update - 1
    shared = [offset % 80, 80 + offset % 82]
    return (shared + [pool[(2 * offset + slot) % len(pool)] for slot in range(2)],
            shared + [162 + (2 * offset + slot) % 32 for slot in range(2)])


def audit_schedule(masks, losses, material, selected):
    require(len(masks) == 194 and len(losses) == 100, "terminal_194_masks_100_updates")
    for mask in masks:
        inputs, labels, targets = mask["input_ids"], mask["labels"], mask["target_ids"]
        require(inputs and len(inputs) == len(labels) and labels[0] == -100, "masked_prefix")
        positions = [index for index, label in enumerate(labels) if label != -100]
        require(positions and positions == list(range(positions[0], positions[-1] + 1)), "target_only_span")
        require(targets == [inputs[index] for index in positions] == [labels[index] for index in positions]
                and targets[-1] == 151645 and inputs[positions[-1] + 1:] == [198], "target_eot_template")
    counts, actual_total, reference_total = Counter(), 0, 0
    for update, loss in enumerate(losses, 1):
        actual, reference = indexes(update, material, selected)
        require(loss["update"] == update and loss["row_indexes"] == actual
                and loss["reference_row_indexes"] == reference, "schedule_drift")
        actual_count = sum(len(masks[index]["target_ids"]) for index in actual)
        reference_count = sum(len(masks[index]["target_ids"]) for index in reference)
        require(loss["actual_label_count"] == loss["active_label_count"] == actual_count
                and loss["reference_label_count"] == loss["original_label_count"] == reference_count
                and math.isclose(loss["loss_scale"], actual_count / reference_count, rel_tol=1e-12),
                "uniform_denominator_drift")
        require(math.isfinite(loss["loss"]) and math.isfinite(loss["actual_mean_loss"])
                and math.isclose(loss["loss"], loss["actual_mean_loss"] * loss["loss_scale"],
                                 rel_tol=2e-6, abs_tol=1e-9), "nonfinite_or_scaled_loss")
        counts.update(actual)
        actual_total += actual_count
        reference_total += reference_count
    budgets = dict(memory_presentations=sum(counts[index] for index in range(80)),
                   behavior_presentations=sum(counts[index] for index in range(80, 162)),
                   cue_presentations=sum(counts[index] for index in range(80, 100)),
                   lesson_presentations=sum(counts[index] for index in range(100, 162)),
                   new_memory_presentations=sum(counts[index] for index in range(162, 194)))
    require(list(budgets.values()) == [100, 100, 38, 62, 200], "group_doses")
    return dict(updates=100, budgets=budgets, actual_supervised_tokens=actual_total,
                reference_supervised_tokens=reference_total, row_counts=dict(counts),
                new_fact_presentations=[sum(counts[162 + 4 * view + index] for view in range(8))
                                        for index in range(4)],
                first_indexes=losses[0]["row_indexes"], last_indexes=losses[-1]["row_indexes"],
                loss_first=losses[0]["loss"], loss_last=losses[-1]["loss"],
                scale_min=min(loss["loss_scale"] for loss in losses),
                scale_max=max(loss["loss_scale"] for loss in losses))


def replay_captures(record, collect):
    captures = iter(record["captures"])

    def generate(messages):
        capture = next(captures, None)
        require(capture is not None and capture["messages"] == messages, "audit_prompt_or_call_drift")
        require(capture["error"] is None, "captured_inference_error_not_policy_failure")
        return capture["response"]

    replayed = collect(generate)
    require(next(captures, None) is None and replayed == record, "audit_record_replay_drift")
    return replayed


def audit_readers(bundle, record, runtime):
    replay_captures(record, lambda generate: runtime.actual.collect_cases(bundle, generate))
    return {key: record[key] for key in ("summary", "model_calls", "expected_calls", "task_denominator",
            "chosen_source_indexes", "admitted_selections", "row_source_indexes", "material_origins", "captures")}


def text_errors(rows, micro):
    errors = []
    for index, row in enumerate(rows):
        if row["correct"]:
            continue
        response = row["generation"]
        item = dict(index=index, event=row["event"], expected=row["expected"], actual=response["raw"],
                    terminal=response["terminal"], truncated=response["truncated"], strict_correct=False)
        try:
            expected = micro.parse_event_line(micro.canonical_event(row["expected"]))
            actual = micro.parse_event_line(micro.canonical_event(response["raw"]))
            item["different_fields"] = ["node" if key == "source" else key for key in expected
                                        if expected[key] != actual.get(key)]
            item["format_only"] = not item["different_fields"]
        except ValueError:
            item["parseable_event"] = False
        errors.append(item)
    return errors


def after_summary(directory, result, collection, prior, runtime):
    held_cases = runtime.lesson.build_cases([dict(event=episode["fact"]["event"], raw=episode["event"]["raw"])
                                            for episode in collection["episodes"]], "HELD")
    held = read(directory / "AFTER_HELD.json")
    replay_captures(held, lambda generate: runtime.lesson.collect_cases(held_cases, generate, coached=False))
    require(held["model_calls"] == 16 and held["rows"] == [] and held["parent_present"] is False,
            "held_parent_free_16_calls")
    bundle = runtime.actual.build_cases(collection, result["panels"]["OWN_PARAMETRIC"]["episodes"])
    require(read(directory / "NEXT_ACTUAL_CASES.json") == bundle, "next_actual_routes_join")
    next_readers = audit_readers(bundle, read(directory / "NEXT_ACTUAL_READERS.json"), runtime)
    captures = held["captures"] + next_readers["captures"]
    paths = sorted(directory.glob("CALL_*.json"))
    require([path.name for path in paths] == ["CALL_%03d.json" % index for index in range(len(captures))],
            "top_level_audit_call_count")
    for path, capture in zip(paths, captures):
        require(read(path) == {key: capture[key] for key in ("messages", "response", "error")}, "audit_call_join")
        response = adult_reduce.generation(capture["response"])
        require(type(response["prompt_tokens"]) is int and 0 < response["prompt_tokens"] <= 2048
                and len(response["token_ids"]) <= 160, "audit_token_budget")
    require(result["reader_wrapper"] == 0, "actual_reader_W0_required")
    view = dict(result, model_calls=result["model_calls"] - len(captures),
                arguments=dict(result.get("arguments", {}), reader_wrapper=0))
    summary = adult_reduce.readout_summary(directory, view, collection, runtime, prior)
    summary.update(classifier=dict(summary=held["summary"], captures=held["captures"]),
                   next_actual_readers=next_readers, routing_model_calls=summary["model_calls"],
                   audit_model_calls=len(captures), model_calls=result["model_calls"],
                   audit_prompt_tokens=sum(capture["response"]["prompt_tokens"] for capture in captures),
                   audit_output_tokens=sum(len(capture["response"]["token_ids"]) for capture in captures),
                   text_failures={name: text_errors(result["panels"][name]["rows"], runtime.micro)
                                  for name in ("RECALL_W0", "RECALL_W8", "OLD_RECALL_W0", "OLD_RECALL_W8")})
    summary["total_prompt_tokens"] = summary["prompt_tokens"] + summary["audit_prompt_tokens"]
    summary["total_output_tokens"] = summary["output_tokens"] + summary["audit_output_tokens"]
    return summary


def failed_after_summary(directory, failure, collection, prior, runtime):
    summary = dict(raw_panels=failure.get("panels"), replay_status="UNAVAILABLE",
                   terminal_base_verification=False, next_actual_status="NOT_REPLAYED")
    if not failure.get("panels") or runtime is None or collection is None or prior is None:
        return summary
    try:
        require(failure["reader_wrapper"] == 0, "actual_reader_W0_required")
        view = dict(failure, arguments=dict(failure.get("arguments", {}), reader_wrapper=0))
        routing = adult_reduce.readout_summary(directory, view, collection, runtime, prior)
        summary.update(routing=routing, replay_status="CAPTURED_ROUTING_REPLAYED_NOT_COMPLETE")
        held = read(directory / "AFTER_HELD.json")
        cases = runtime.lesson.build_cases([dict(event=episode["fact"]["event"], raw=episode["event"]["raw"])
                                           for episode in collection["episodes"]], "HELD")
        replay_captures(held, lambda generate: runtime.lesson.collect_cases(cases, generate, coached=False))
        summary["classifier"] = dict(summary=held["summary"], captures=held["captures"])
    except (ValueError, KeyError, TypeError, IndexError, OSError, StopIteration) as error:
        summary["replay_error"] = type(error).__name__ + ": " + str(error)
    summary["audit_call_files"] = {}
    for path in sorted(directory.glob("CALL_*.json")):
        try:
            summary["audit_call_files"][path.name] = read(path)
        except (ValueError, OSError) as error:
            summary["audit_call_files"][path.name] = dict(capture_error=str(error))
    summary["captured_audit_calls"] = failure.get("captured_audit_calls")
    return summary


def training_summary(directory, result, collection, prior, runtime):
    rows, masks = read(directory / "TRAINING_ROWS.json"), read(directory / "MASKS.json")
    require([len(rows[key]) for key in ("memory_rows", "cue_rows", "lesson_rows", "new_rows")]
            == [80, 20, 62, 32], "row_layout_80_20_62_32")
    new_rows = runtime.adult.replay_collection(collection)
    require(rows["new_rows"] == new_rows and rows["memory_rows"][32:64] == runtime.adult.replay_collection(prior)
            and rows["memory_rows"][64:] == [row for row in new_rows if row["event"] in
                {collection["bank"][index]["event"] for index in (0, 2)}], "source_memory_rows_drift")
    for row in rows["lesson_rows"]:
        runtime.lesson._validate_row(row)
    recipe = read(directory / "RECIPE.json")
    require(recipe == result["recipe"], "recipe_receipt_join")
    selected = result["source"]["selected_source_indexes"]
    pool = [162 + 4 * view + index for index in selected for view in range(8)]
    expected = dict(material_arm=result["material_arm"], selected_source_indexes=selected, updates=100,
                    batch_size=4, encoded_row_count=194, new_row_offset=162,
                    memory_row_count=80, cue_row_count=20, lesson_row_count=62, new_row_count=32,
                    loss_normalization=NORMALIZATION, actual_token_equality_claim=False,
                    arm_new_row_indexes=pool if result["material_arm"] == "SELECTED" else list(range(162, 194)),
                    uniform_new_row_indexes=list(range(162, 194)), expected_lora_rank=8, adapter_dtype="float32")
    require(all(recipe[key] == value for key, value in expected.items()), "fixed_recipe_drift")
    for key, value in dict(train_seed=0, learning_rate=3e-5, optimizer="FRESH_ADAMW").items():
        require(recipe[key] == result[key] == value, "optimizer_recipe_drift")
    provenance = read(directory / "ADAPTER_PROVENANCE.json")
    require(all(result[key] == value for key, value in provenance.items() if key != "schema"), "provenance_join")
    hashes = result["training_artifact_sha256"]
    require(set(hashes) == {"MASKS.json", "RECIPE.json", "LOSSES.jsonl"}, "training_hash_inventory")
    for name, expected_hash in hashes.items():
        require(digest(directory / name) == expected_hash, "training_hash_drift:" + name)
    loss_path = directory / "LOSSES.jsonl"
    require(not loss_path.is_symlink() and loss_path.stat().st_size <= 16 * 1024 * 1024, "bounded_losses")
    losses = [json.loads(line) for line in loss_path.read_text().splitlines()]
    summary = audit_schedule(masks, losses, result["material_arm"], selected)
    for key in ("updates", "budgets", "actual_supervised_tokens", "reference_supervised_tokens", "new_fact_presentations"):
        require(result[key] == summary[key], "training_totals:" + key)
    require(all(result[key] == value for key, value in summary["budgets"].items()), "receipt_doses")
    require(result["supervised_tokens"] == summary["actual_supervised_tokens"]
            and result["original_supervised_tokens"] == summary["reference_supervised_tokens"]
            and result["loss_normalization"] == NORMALIZATION and result["selected_source_indexes"] == selected
            and result["new_source_events"] == recipe["new_source_events"] == [row["event"] for row in new_rows[:4]],
            "training_aliases_or_events")
    require(result["fits"] == 1 and result["adapter_state_before"] == result["loaded_adapter_state_sha256"]
            == result["source"]["initial_adapter_state_sha256"]
            and result["adapter_state_after"] != result["adapter_state_before"], "initial_changed_adapter")
    summary.update(initial_state=result["adapter_state_before"], final_state=result["adapter_state_after"],
                   selected_source_indexes=selected, source=result["source"], masks_sha256=digest(directory / "MASKS.json"),
                   rows_sha256=digest(directory / "TRAINING_ROWS.json"))
    return summary


def check_receipt(directory, result, parent, material, phase, runtime, training=None):
    request = read(directory / "REQUEST.json")
    require(result["schema"] == SCHEMA and result["parent_arm"] == parent and result["material_arm"] == material
            and result["phase"] == phase and result["parent_present"] is False
            and result["frozen_base_unchanged"] is True, "stage_receipt_drift")
    for key in ("schema", "phase", "parent_arm", "material_arm", "arguments", "started_unix", "entry_sha256", "parent_present"):
        require(request[key] == result[key], "request_join:" + key)
    require(result["entry_sha256"] == digest(runtime.root / "gpu/astra_selected_reader_repair.py"), "driver_source_drift")
    require(result["source"] == read(directory / "INPUTS.json") and result["source"]["parent_arm"] == parent
            and result["source"]["selected_source_indexes"] == SELECTED[parent], "initial_inputs_or_pointers")
    if phase == "train":
        require(result["trainer_sha256"] == digest(runtime.root / "gpu/astra_selected_reader_repair_train.py"),
                "trainer_source_drift")
    else:
        require(training is not None, "after_requires_valid_terminal_train")
        require(result["source"] == training["source"] and result["training_result_sha256"] == training["result_sha256"]
                and result["loaded_adapter_state_sha256"] == training["final_state"], "saved_after_reload_join")


def pair_summary(cells):
    selected, uniform = (cells[material]["train"] for material in MATERIALS)
    if any(stage["status"] != "COMPLETE" for stage in (selected, uniform)):
        return dict(status="UNAVAILABLE", reason="requires_two_valid_terminal_trains")
    fields = ("initial_state", "source", "masks_sha256", "rows_sha256", "reference_supervised_tokens")
    mismatches = [key for key in fields if selected[key] != uniform[key]]
    return dict(status="MISMATCH" if mismatches else "MATCH", mismatches=mismatches,
                initial_state=selected["initial_state"], actual_token_equality_claim=False)


def reduce(root, collection=None, prior=None, runtime=None):
    root = Path(root)
    report = dict(cells={}, pairs={}, pending=[], failed=[], invalid=[],
        limitations=["Receipt consistency only; upstream actor/base and original cue/old-bank authenticity are external.",
                     "Target-only mask structure checked without tokenizer text-to-ID re-encoding.",
                     "Both parent states receive 62 lesson presentations; across-state comparisons confound weights and pointers.",
                     "Receipt-stage wall-time throughput includes setup/save overhead; it is not GPU utilization or kernel throughput.",
                     "No BEFORE deltas inferred; compare separately retained corresponding post-lesson baselines.",
                     "One exposed lineage/bank; pointers are source admission, not correctness, novelty or utility."])
    for parent in PARENTS:
        cells = report["cells"][parent] = {}
        for material in MATERIALS:
            stages = cells[material] = {}
            for phase in ("train", "after"):
                directory = root / (parent + "_" + material) / phase
                label = "/".join((parent, material, phase))
                try:
                    info = terminal(directory)
                    if info["status"] == "COMPLETE":
                        result = info.pop("result")
                        require(runtime is not None and collection is not None and prior is not None,
                                "completed_cell_requires_source_and_A2_A1_collections")
                        require(collection["cycle"] == 2 and prior.get("cycle", 1) == 1, "A2_A1_collections_required")
                        require(len(runtime.adult.replay_collection(collection)) == len(runtime.adult.replay_collection(prior)) == 32,
                                "grounded_four_fact_collections_required")
                        training = stages.get("train")
                        if training is not None and training["status"] != "COMPLETE":
                            training = None
                        check_receipt(directory, result, parent, material, phase, runtime, training)
                        detail = (training_summary(directory, result, collection, prior, runtime) if phase == "train"
                                  else after_summary(directory, result, collection, prior, runtime))
                        info.update(detail)
                        if phase == "train" and info.get("seconds", 0) > 0:
                            info["updates_per_receipt_second"] = info["updates"] / info["seconds"]
                            info["actual_supervised_tokens_per_receipt_second"] = info["actual_supervised_tokens"] / info["seconds"]
                            info["reference_supervised_tokens_per_receipt_second"] = info["reference_supervised_tokens"] / info["seconds"]
                    else:
                        require(info["status"] in ("PENDING", "FAILED"), "unexpected_stage_terminal")
                        if info["status"] == "FAILED" and phase == "after":
                            info["partial_evidence"] = failed_after_summary(
                                directory, info["failure"], collection, prior, runtime)
                except (ValueError, KeyError, TypeError, IndexError, OSError, StopIteration) as error:
                    info = dict(status="INVALID", error=type(error).__name__ + ": " + str(error))
                info["path"] = str(directory)
                stages[phase] = info
                if info["status"] in ("PENDING", "FAILED", "INVALID"):
                    report[{"PENDING": "pending", "FAILED": "failed", "INVALID": "invalid"}[info["status"]]].append(label)
        report["pairs"][parent] = pair_summary(cells)
    report["status"] = ("INVALID_EVIDENCE" if report["invalid"] or any(pair["status"] == "MISMATCH" for pair in report["pairs"].values())
                        else "FAILED_CELLS" if report["failed"] else "PARTIAL_EVIDENCE" if report["pending"] else "COMPLETE")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--collection", type=Path, help="A2 COLLECTION.json")
    parser.add_argument("--prior-collection", type=Path, help="A1 COLLECTION.json")
    options = parser.parse_args()
    runtime = adult_reduce.load_source(options.source_root) if options.source_root else None
    if runtime:
        for label, name in (("lesson", "experienced_event_reader_audit_lesson"), ("actual", "experienced_event_actual_reader_audit")):
            module = importlib.import_module("organism_v6." + name)
            require(Path(module.__file__).resolve() == runtime.root / "organism_v6" / (name + ".py"), "audit_source_mismatch")
            setattr(runtime, label, module)
    report = reduce(options.root, read(options.collection) if options.collection else None,
                    read(options.prior_collection) if options.prior_collection else None, runtime)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0 if report["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
