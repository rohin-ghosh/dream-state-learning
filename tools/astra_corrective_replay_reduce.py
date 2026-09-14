"""Replay bounded captured corrective forks; never import native model libraries."""

import argparse
from collections import Counter
import importlib
import json
import math
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import astra_adult_cycle_reduce as adult_reduce


ARMS = ("CHILD_CORRECTIVE", "UNIFORM_REPLAY")
require = adult_reduce.require
read = adult_reduce.read
digest = adult_reduce.digest
IDENTITY = ("initial_training_result_sha256", "adult_source", "memory_source", "cue_source",
            "prior_adult_source", "prior_adult_training_result_sha256", "cycle", "master", "development_arm")


def indexes(update, arm, selected):
    require(type(update) is int and 1 <= update <= 100 and arm in ARMS, "schedule_bounds")
    require(1 <= len(selected) <= 4 and all(type(index) is int and 0 <= index < 4 for index in selected),
            "source_selection_bounds")
    pool = [84 + 4 * view + index for index in selected for view in range(8)]
    if arm == "UNIFORM_REPLAY":
        pool = list(range(84, 116))
    offset = update - 1
    shared = [offset % 64, 64 + offset % 20]
    return (shared + [pool[(2 * offset + slot) % len(pool)] for slot in range(2)],
            shared + [84 + (2 * offset + slot) % 32 for slot in range(2)])


def audit_schedule(masks, losses, arm, selected):
    require(len(masks) == 116 and len(losses) == 100, "terminal_116_masks_100_updates")
    for mask in masks:
        inputs, labels, targets = mask["input_ids"], mask["labels"], mask["target_ids"]
        require(len(inputs) == len(labels) and labels[0] == -100, "mask_prefix_length")
        positions = [index for index, label in enumerate(labels) if label != -100]
        require(positions and positions == list(range(positions[0], positions[-1] + 1)), "target_only_span")
        require(targets == [inputs[index] for index in positions] == [labels[index] for index in positions]
                and targets[-1] == 151645 and inputs[positions[-1] + 1:] == [198], "target_ids_eot_template")
    counts, actual_total, reference_total = Counter(), 0, 0
    for update, loss in enumerate(losses, 1):
        actual, reference = indexes(update, arm, selected)
        require(loss["update"] == update and loss["row_indexes"] == actual
                and loss["reference_row_indexes"] == reference, "actual_reference_schedule_drift")
        actual_labels = sum(len(masks[index]["target_ids"]) for index in actual)
        reference_labels = sum(len(masks[index]["target_ids"]) for index in reference)
        require(loss["actual_label_count"] == loss["active_label_count"] == actual_labels
                and loss["reference_label_count"] == loss["original_label_count"] == reference_labels
                and math.isclose(loss["loss_scale"], actual_labels / reference_labels, rel_tol=1e-12),
                "uniform_denominator_drift")
        require(math.isfinite(loss["loss"]) and math.isfinite(loss["actual_mean_loss"])
                and math.isclose(loss["loss"], loss["actual_mean_loss"] * loss["loss_scale"],
                                 rel_tol=2e-6, abs_tol=1e-9), "nonfinite_or_scaled_loss_drift")
        counts.update(actual)
        actual_total += actual_labels
        reference_total += reference_labels
    budgets = dict(old_memory_presentations=sum(counts[index] for index in range(64)),
                   old_cue_presentations=sum(counts[index] for index in range(64, 84)),
                   new_memory_presentations=sum(counts[index] for index in range(84, 116)),
                   original_bank_presentations=sum(counts[index] for index in range(32)),
                   first_adult_presentations=sum(counts[index] for index in range(32, 64)))
    require(list(budgets.values()) == [100, 100, 200, 64, 36], "group_doses")
    return dict(budgets=budgets, actual_supervised_tokens=actual_total, reference_supervised_tokens=reference_total,
                row_counts=dict(counts), new_event_presentations=[sum(counts[84 + 4 * view + index]
                    for view in range(8)) for index in range(4)], first_indexes=losses[0]["row_indexes"],
                last_indexes=losses[-1]["row_indexes"], loss_first=losses[0]["loss"], loss_last=losses[-1]["loss"],
                scale_min=min(loss["loss_scale"] for loss in losses), scale_max=max(loss["loss_scale"] for loss in losses))


def check_request(request, result, driver_hash, helper_hash=None):
    require(request["runner_sha256"] == driver_hash, "request_driver_source_drift")
    require(result["runner_sha256"] == (helper_hash or driver_hash), "result_source_role_drift")
    for key, value in request.items():
        if key != "runner_sha256":
            require(result[key] == value, "request_result_drift:" + key)


def check_files(root, hashes):
    for name, expected in hashes.items():
        require(not Path(name).is_absolute() and ".." not in Path(name).parts, "relative_evidence_path")
        require(digest(root / name) == expected, "source_file_drift:" + name)


def selection_summary(directory, before_root, collection, runtime, baseline):
    helper = importlib.import_module("organism_v6.experienced_event_corrective_replay")
    records = [read(before_root / "new_task" / ("OWN_PARAMETRIC_EPISODE_%02d.json" % number))
               for number in range(1, 5)]
    cases = helper.prepare_cases(collection, records)
    require(cases == read(directory / "CORRECTION_CASES.json"), "selection_case_replay")
    record, result = read(directory / "SELECTION.json"), read(directory / "RESULT.json")
    require(not (directory / "FAILED.json").exists() and result["fits"] == 0
            and result["parent_present"] is False, "selector_no_fit_parent")
    require(digest(directory / "SELECTION.json") == result["selection_sha256"], "selection_hash")
    captures = iter(record["captures"])

    def generate(messages):
        capture = next(captures)
        require(capture["messages"] == messages and capture["error"] is None, "selector_raw_prompt_or_error")
        return capture["response"]

    require(helper.collect_selection(cases, generate) == record and next(captures, None) is None,
            "selection_capture_replay")
    require(record["model_calls"] == result["model_calls"] == cases["expected_calls"]
            == record["admitted_selections"] and 1 <= record["model_calls"] <= 4, "selector_count")
    for capture in record["captures"]:
        stored = read(directory / ("CALL_%03d.json" % capture["call_index"]))
        require(stored == {key: capture[key] for key in ("call_index", "messages", "response", "error")},
                "selector_call_join")
        require(0 < capture["response"]["prompt_tokens"] <= 2048
                and 0 < len(capture["response"]["token_ids"]) <= 160, "selector_token_budget")
    source = read(directory / "CORRECTION_SOURCE.json")
    require(source == result["selection_source"] and source["helper_sha256"] == digest(Path(helper.__file__)),
            "selector_source_helper")
    check_files(before_root, source["source_files"])
    require(source["loaded_adapter_state_sha256"] == result["loaded_adapter_state_sha256"]
            == baseline["loaded_adapter_state_sha256"] and source["preparation_sha256"] == cases["preparation_sha256"],
            "selector_initial_actor")
    selected = record["chosen_source_indexes"]
    wrong = [index for index, episode in enumerate(records) if not episode["episode"]["reached_goal"]]
    require(wrong == [case["route_index"] for case in cases["cases"]], "actual_wrong_case_indices")
    return dict(selected_source_indexes=selected, initial_wrong_task_indexes=wrong,
                model_calls=record["model_calls"], selections=record["selections"],
                prompt_tokens=sum(capture["response"]["prompt_tokens"] for capture in record["captures"]),
                output_tokens=sum(len(capture["response"]["token_ids"]) for capture in record["captures"]))


def readout(directory, result, collection, prior, runtime, selected, wrong):
    require(result["reader_wrapper"] == 0, "primary_actual_reader_w0")
    summary = adult_reduce.readout_summary(directory, result, collection, runtime, prior)
    partitions = dict(selected=sorted(set(selected)), unselected=[index for index in range(4) if index not in selected],
                      initially_wrong=wrong, initially_right=[index for index in range(4) if index not in wrong])
    summary["partitions"] = {}
    for name, indexes_list in partitions.items():
        values = dict(indexes=indexes_list, denominator=len(indexes_list))
        for wrapper in (0, 8):
            panel = summary["panels"]["RECALL_W" + str(wrapper)]
            values["recall_w" + str(wrapper)] = sum(panel["raw_outputs"][index] == runtime.micro._event(collection["bank"][index])
                and result["panels"]["RECALL_W" + str(wrapper)]["rows"][index]["correct"] for index in indexes_list)
        values["own_goals"] = sum(summary["panels"]["OWN_PARAMETRIC"]["episodes"][index]["reached_goal"] for index in indexes_list)
        summary["partitions"][name] = values
    expected = {fact["event"]: runtime.micro._event(fact) for fact in collection["bank"]}
    summary["actual_own_readers"] = []
    for number, episode in enumerate(result["panels"]["OWN_PARAMETRIC"]["episodes"], 1):
        for trace in episode["episode"]["traces"]:
            if trace["kind"] == "memory":
                response = trace["response"]
                summary["actual_own_readers"].append(dict(episode=number, address=trace["address"],
                    raw=response["raw"], expected=expected.get(trace["address"]),
                    exact=response["terminal"] and not response["truncated"] and response["raw"] == expected.get(trace["address"])))
    calls = [read(path)["generation"] for path in sorted((directory / "new_task").glob("CALL_*.json"))]
    calls += [row["generation"] for wrapper in (0, 8) for row in result["panels"]["OLD_RECALL_W" + str(wrapper)]["rows"]]
    require(len(calls) == summary["model_calls"] and all(0 < call["prompt_tokens"] <= 2048
            and 0 < len(call["token_ids"]) <= 160 for call in calls), "readout_call_token_budget")
    summary["terminal_calls"] = sum(call["terminal"] for call in calls)
    summary["truncated_calls"] = sum(call["truncated"] for call in calls)
    return summary


def reduce_campaign(capture_root, reference_root, prior_root, cue_root, runtime):
    driver_hash = digest(runtime.root / "gpu/astra_experienced_event_adult_cycle.py")
    helper_hash = digest(runtime.root / "gpu/astra_corrective_sleep_train.py")
    collection_result = read(reference_root / "collect/RESULT.json")
    _, collection = adult_reduce.collection_summary(reference_root / "collect", collection_result, runtime)
    prior = adult_reduce.prior_binding(prior_root, "CUE_REPLAY", collection_result, runtime)
    baseline = read(reference_root / "before/RESULT.json")
    reference = read(reference_root / "train/RESULT.json")
    adult_reduce.training_summary(reference_root / "train", reference, collection, runtime, cue_root, prior)
    reference_masks = read(reference_root / "train/MASKS.json")
    selection_root = capture_root / "select_corrective"
    selection = selection_summary(selection_root, reference_root / "before", collection, runtime, baseline)
    selected, wrong = selection["selected_source_indexes"], selection["initial_wrong_task_indexes"]
    report = dict(selection=selection, before=readout(reference_root / "before", baseline, collection, prior,
                  runtime, selected, wrong), arms={}, pending=[], source=dict(driver_sha256=driver_hash, helper_sha256=helper_hash),
                  claim="ONE_MATCHED_DEV_FORK_SOURCE_VALID_SELECTION_NOT_AUTONOMOUS_SELECTION_OR_H2")
    for arm in ARMS:
        stages, training = {}, None
        for stage in ("train", "after"):
            directory = capture_root / "corrective_sleep" / arm / stage
            info = adult_reduce.terminal(directory)
            stages[stage] = info
            if info["status"] in ("FAILED", "PENDING"):
                if info["status"] == "PENDING":
                    report["pending"].append(arm + "/" + stage)
                continue
            result = info.pop("result")
            check_request(read(directory / "REQUEST.json"), result, driver_hash, helper_hash if stage == "train" else None)
            require(result["replay_arm"] == arm and result["selected_source_indexes"] == selected
                    and result["frozen_base_unchanged"] is True and result["parent_present"] is False,
                    "arm_selection_base")
            require(result["phase"] == ("train_corrective" if stage == "train" else "readout_corrective")
                    and result["state"] == ("BEFORE" if stage == "train" else "AFTER")
                    and result["material_sha256"] == digest(runtime.root / "organism_v6/experienced_event_adult_cycle.py"),
                    "stage_material_binding")
            for key in IDENTITY:
                require(result[key] == baseline[key], "same_initial_sources:" + key)
            for key in ("expected_base_sha256", "expected_initial_adapter_sha256", "initial_adapter_dir", "model_dir"):
                require(result["arguments"][key] == baseline["arguments"][key], "same_initial_argument:" + key)
            require(result["tokenizer"] == baseline["tokenizer"], "same_tokenizer")
            source = result["corrective_selection_source"]
            check_files(selection_root, source["source_files"])
            require(source["before_source"] == read(selection_root / "CORRECTION_SOURCE.json")
                    and source["result_sha256"] == digest(selection_root / "RESULT.json")
                    and source["selected_source_indexes"] == selected, "selection_source_join")
            info.update(loaded_adapter_state_sha256=result["loaded_adapter_state_sha256"])
            if stage == "train":
                training = result
                masks = read(directory / "MASKS.json")
                require(masks == reference_masks, "all_116_masks_match_source_faithful_reference")
                check_files(directory, result["training_artifact_sha256"])
                provenance = read(directory / "ADAPTER_PROVENANCE.json")
                require(all(provenance[key] == result[key] for key in provenance), "adapter_provenance_join")
                layout = read(directory / "SELECTION_LAYOUT.json")
                native_helper = importlib.import_module("gpu.astra_corrective_sleep_train")
                require(layout == native_helper.selection_layout(arm, selected), "source_layout_join")
                losses = [json.loads(line) for line in (directory / "LOSSES.jsonl").read_text().splitlines()]
                detail = audit_schedule(masks, losses, arm, selected)
                for key in ("budgets", "actual_supervised_tokens", "reference_supervised_tokens"):
                    require(detail[key] == result[key], "training_totals:" + key)
                require(all(result[key] == value for key, value in detail["budgets"].items()), "receipt_group_doses")
                require(result["supervised_tokens"] == detail["actual_supervised_tokens"]
                        and result["original_supervised_tokens"] == detail["reference_supervised_tokens"], "token_aliases")
                require(result["updates"] == 100 and result["fits"] == 1 and result["train_seed"] == 0
                        and result["optimizer"] == "FRESH_ADAMW" and result["learning_rate"] == 3e-5
                        and result["loss_normalization"] == "UNIFORM_BATCH_CAUSAL_LABEL_COUNT", "fixed_training_recipe")
                require(result["adapter_state_before"] == result["loaded_adapter_state_sha256"] == baseline["loaded_adapter_state_sha256"]
                        and result["adapter_state_after"] != result["adapter_state_before"], "same_initial_changed_adapter")
                info.update(detail, masks_sha256=digest(directory / "MASKS.json"), adapter_files=result["adapter_files"],
                            adapter_state_after=result["adapter_state_after"])
            else:
                require(training is not None and result["loaded_adapter_state_sha256"] == training["adapter_state_after"]
                        and result["corrective_training_result_sha256"] == stages["train"]["result_sha256"], "saved_after_reload_join")
                info.update(readout(directory, result, collection, prior, runtime, selected, wrong))
        report["arms"][arm] = stages
    report["status"] = "PARTIAL_TERMINAL_EVIDENCE" if report["pending"] else "ALL_STAGES_TERMINAL"
    report["no_native_imports"] = not any(name in sys.modules for name in ("torch", "transformers", "tokenizers", "peft"))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("capture-root", "reference-root", "prior-root", "cue-root", "source-root", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    report = reduce_campaign(args.capture_root, args.reference_root, args.prior_root, args.cue_root,
                             adult_reduce.load_source(args.source_root))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "pending", "no_native_imports")}))


if __name__ == "__main__":
    main()
