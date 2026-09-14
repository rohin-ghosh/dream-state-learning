"""Bounded local transfer-write reduction; no models, remote IO or fits.

ROOT/{train,after} is the new LOSS_OFF_SELECTOR fork. Supply --source-root,
--reference-root (SEQ245 capsule), --reference-receipt (verified SEQ245 JSON),
--replay-root (SEQ246 AUDIT_SFT/AUDIT_LOSS_OFF captures), --a1-collection and
--a2-collection. No adapters are read. JSON goes to stdout; exit 0 requires
both terminal stages and all reference/material joins. Missing stages stay
pending. Optional --prepare-failure is a CPU engineering receipt, not a fit.
"""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import astra_fresh_reader_cycle_reduce as fresh
from tools import astra_selected_reader_repair_reduce as repair


SCHEMA = "DEV_READER_AUDIT_TRANSFER_WRITE_V1"
ARM = "LOSS_OFF_SELECTOR"
INITIAL_STATE = "48dc1d6d77852bddba75e04ee7442f4ef2a8e72bce5719d39ade4ed974a2b042"
REFERENCE_SHA256 = "00a81f14e0517750d00697db2935c23577ffdcc88fd2866c6edd6e06218448cb"
SFT_CHOICES = [1, 0, 1, 0, 3, 2, 3, 2]
OFF_CHOICES = [1, None, 1, None, None, None, None, None]
KERNEL = dict(trainer="gpu/astra_selected_reader_repair_train.py",
              memory_and_new_encoder="gpu/astra_experienced_event_microloop.py",
              cue_encoder="organism_v6/experienced_event_cue_sleep.py",
              lesson_encoder="organism_v6/experienced_event_reader_audit_lesson.py",
              mask_validator="gpu/astra_reader_audit_lesson_train.py",
              adapter_setup="gpu/astra_experienced_event_cue_sleep.py",
              native_recipe="gpu/astra_pchain2_native.py", state_hash="organism_v6/pcfl_vertical_train.py")
read, digest, require = fresh.read, fresh.digest, fresh.require


def metrics(stage):
    return dict(panels={name: {key: value for key, value in panel.items() if key not in ("episodes", "raw_outputs")}
                        for name, panel in stage["panels"].items()}, classifier=stage["classifier"]["summary"],
                actual_audit=stage["actual_audit"]["summary"], choices=stage["actual_audit"]["chosen_source_indexes"])


def reference_check(root, receipt_path, expected_sha=REFERENCE_SHA256):
    require(digest(receipt_path) == expected_sha, "verified_SEQ245_receipt_hash")
    report = read(receipt_path)
    require(report["status"] == "COMPLETE" and report["pair"]["status"] == "MATCH"
            and report["pair"]["initial_state"] == INITIAL_STATE and report["before_pointers"] == SFT_CHOICES,
            "verified_reference_pair_and_roster")
    required = {"collect", "before", "SELECTED/train", "SELECTED/after", "UNIFORM/train", "UNIFORM/after"}
    require(set(report["stages"]) == required, "six_reference_stages")
    for name, stage in report["stages"].items():
        require(stage["status"] == "COMPLETE" and not (root / name / "FAILED.json").exists()
                and digest(root / name / "RESULT.json") == stage["result_sha256"], "reference_stage_hash:" + name)
    require(digest(root / "collect/COLLECTION.json") == report["stages"]["collect"]["collection_sha256"], "reference_collection_hash")
    return report


def replay_check(directory, binding, arm, reference_root, runtime):
    require(not (directory / "FAILED.json").exists(), "failed_matched_auditor")
    for name, expected in binding["files"].items():
        require(Path(name).name == name and digest(directory / name) == expected, "matched_replay_file_hash:" + name)
    result = read(directory / "RESULT.json")
    actor = binding["evaluated_auditor"]
    require(result["status"] == "COMPLETE" and result["schema"] == "DEV_READER_AUDIT_MATCHED_REPLAY_V1"
            and result["arm"] == arm and result["fits"] == 0 and result["model_calls"] == 14
            and result["evaluated_auditor"] == actor and result["stimuli"] == binding["stimuli"]
            and result["adapter_state_before"] == result["adapter_state_after"] == actor["adapter_state_sha256"]
            and result["adapter_files_after"] == actor["adapter_files"]
            and all(result[key] is True for key in ("adapter_unchanged", "adapter_files_unchanged", "frozen_base_unchanged")),
            "unchanged_original_auditor_receipt")
    require(read(directory / "INPUTS.json") == dict(evaluated_auditor=actor, stimuli=binding["stimuli"]), "matched_replay_inputs")
    packets = read(directory / "CASES.json")["packets"]
    require([packet["packet"] for packet in packets] == ["before", "SELECTED/after"], "two_matched_packets")
    collection = read(reference_root / "collect/COLLECTION.json")
    summaries, cursor, before_choices = [], 0, None
    for packet in packets:
        name = packet["packet"]
        source_result = read(reference_root / name / "RESULT.json")
        cases = runtime.audit.build_cases(collection, source_result["panels"]["OWN_PARAMETRIC"]["episodes"])
        require(cases == packet["cases"] == read(reference_root / name / "ACTUAL_CASES.json")
                and packet["source_actor_state_sha256"] == source_result["loaded_adapter_state_sha256"], "same_public_packet_source")
        wrapped_name = name.replace("/", "_") + "_AUDIT.json"
        wrapped = read(directory / wrapped_name)
        require(wrapped["training_allowed"] is False and wrapped["source_actor_state_sha256"] == packet["source_actor_state_sha256"],
                "third_party_stimulus_not_training")
        document = wrapped["audit"]
        repair.replay_captures(document, lambda generate: runtime.audit.collect_audit(cases, generate))
        prompts = [runtime.audit.document_sha256(case["messages"]) for case in cases["cases"]]
        require(packet["prompt_sha256"] == prompts and packet["prompt_multiplicity"] == dict(Counter(prompts))
                and packet["unique_prompts"] == len(set(prompts)), "prompt_multiplicity")
        for index, capture in enumerate(document["captures"]):
            call_name = "CALL_%03d.json" % cursor
            require(read(directory / call_name) == dict(call_index=cursor, packet=name, packet_call_index=index,
                    messages=capture["messages"], prompt_sha256=runtime.audit.document_sha256(capture["messages"]),
                    response=capture["response"], error=None), "actual_transfer_call_join")
            cursor += 1
        summaries.append(dict(packet=name, summary=document["summary"], chosen_source_indexes=document["chosen_source_indexes"],
                              audit_file=wrapped_name, audit_file_sha256=digest(directory / wrapped_name),
                              prompt_multiplicity=packet["prompt_multiplicity"], unique_prompts=packet["unique_prompts"], calls=document["model_calls"]))
        if name == "before":
            before_choices = document["chosen_source_indexes"]
    require(cursor == 14 and len(list(directory.glob("CALL_*.json"))) == 14 and result["packets"] == summaries,
            "all_matched_audit_calls_and_scores")
    require(before_choices == (SFT_CHOICES if arm == "AUDIT_SFT" else OFF_CHOICES), "fixed_actual_selector_roster")
    return dict(actor=actor, before_choices=before_choices, packets=summaries)


def binding_check(binding, reference_root, replay_root, reference, runtime):
    baseline = read(reference_root / "before/RESULT.json")
    require(binding["fresh_source"] == baseline["source"] and baseline["loaded_adapter_state_sha256"] == INITIAL_STATE
            and binding["fresh_source"]["initial_adapter_state_sha256"] == INITIAL_STATE
            and binding["collection_result_sha256"] == reference["stages"]["collect"]["result_sha256"]
            and binding["before_result_sha256"] == reference["stages"]["before"]["result_sha256"], "same_SEQ245_writer_parent")
    require(binding["selected_source_indexes"] == [1, 1] and binding["raw_source_choices"] == dict(AUDIT_SFT=SFT_CHOICES, AUDIT_LOSS_OFF=OFF_CHOICES)
            and binding["common_lesson_rehearsal"] is True and binding["selector_is_writer_on_policy"] is False, "counterfactual_material_roster")
    kernel = {name: digest(runtime.root / path) for name, path in KERNEL.items()}
    require(binding["kernel_hashes"] == kernel, "frozen_kernel_source_hashes")
    for arm in fresh.ARMS:
        directory = reference_root / arm / "train"
        result = read(directory / "RESULT.json")
        expected = dict(training_result_sha256=digest(directory / "RESULT.json"), adapter_state_after=result["adapter_state_after"],
                        masks_sha256=digest(directory / "MASKS.json"), training_rows_sha256=digest(directory / "TRAINING_ROWS.json"),
                        adapter_provenance_sha256=digest(directory / "ADAPTER_PROVENANCE.json"),
                        reference_supervised_tokens=result["reference_supervised_tokens"])
        require(binding["reused_references"][arm] == expected and result["adapter_state_before"] == INITIAL_STATE
                and result["selected_source_indexes"] == SFT_CHOICES
                and {name: entry["sha256"] for name, entry in result["code_provenance"].items()} == kernel, "immutable_reference_writer_contract")
        require(expected["masks_sha256"] == reference["stages"][arm + "/train"]["masks_sha256"]
                and expected["training_rows_sha256"] == reference["stages"][arm + "/train"]["rows_sha256"], "verified_reference_corpora")
    rows = read(reference_root / "UNIFORM/train/TRAINING_ROWS.json")
    require(sha256(fresh.adult.canonical(rows) + b"\n").hexdigest() == binding["training_rows_sha256"], "same_reference_row_document")
    transfers = {arm: replay_check(replay_root / arm, binding["transfer_sources"][arm], arm, reference_root, runtime)
                 for arm in ("AUDIT_SFT", "AUDIT_LOSS_OFF")}
    require(all(binding["transfer_sources"][arm]["stimuli"]["source"] == baseline["source"] for arm in transfers), "shared_stimulus_parent")
    return dict(kernel_hashes=kernel, matched_auditors=transfers, initial_writer_state=INITIAL_STATE)


def reduce(root, runtime=None, reference_root=None, reference_receipt=None, replay_root=None, a1=None, a2=None,
           reference_sha=REFERENCE_SHA256, prepare_failure=None):
    root = Path(root)
    report = dict(stages={}, pending=[], failed=[], invalid=[],
        interpretation="COUNTERFACTUAL_SELECTOR_MATERIAL_SHARED_WRITER_NOT_ON_POLICY_NOT_H1_H2",
        limitations=["Reused SELECTED/UNIFORM are verified SEQ245 references, not new runs or independent replications.",
                     "Same 62 lesson rows in all writers. Pointer validity differs from correctness or semantic judgment.",
                     "Exact mask/schedule replay without tokenizer re-encoding; adapter/base authenticity is receipt-based.",
                     "Actual versus reference label counts differ; no equal-token or learning-rate superiority claim."])
    bound_source, reference, collection, trained = None, None, None, None
    if prepare_failure is not None:
        failed_prepare = read(prepare_failure)
        require(failed_prepare.get("phase") == "prepare" and failed_prepare.get("fits") == 0
                and failed_prepare.get("model_calls") == 0, "CPU_prepare_failure_not_fit_failure")
        report["engineering_prepare_failure"] = dict(receipt=failed_prepare, sha256=digest(prepare_failure), classification="PRE_MODEL_CPU_PREPARE_FAILURE_NOT_FIT")
    for phase in ("train", "after"):
        directory = root / phase
        try:
            info = repair.terminal(directory)
            if info["status"] == "COMPLETE":
                result = info.pop("result")
                require(all(value is not None for value in (runtime, reference_root, reference_receipt, replay_root, a1, a2)), "local_reference_inputs_required")
                request = read(directory / "REQUEST.json")
                require(result["schema"] == SCHEMA and result["phase"] == phase and result["arm"] == ARM
                        and result["on_policy"] is False and result["parent_present"] is False and result["frozen_base_unchanged"] is True,
                        "counterfactual_terminal_receipt")
                for key in ("schema", "phase", "arm", "arguments", "started_unix", "entry_sha256", "on_policy", "parent_present"):
                    require(request[key] == result[key], "request_receipt_join:" + key)
                require(result["entry_sha256"] == digest(runtime.root / "gpu/astra_reader_audit_transfer_write.py")
                        and result["audit_policy"] == fresh.AUDIT_POLICY
                        and result["audit_helper_sha256"] == digest(runtime.root / "organism_v6/experienced_event_fresh_reader_audit.py"), "source_role_hashes")
                source = result["source"]
                require(read(directory / "INPUTS.json") == source, "input_binding")
                info.update(entry_sha256=result["entry_sha256"], audit_helper_sha256=result["audit_helper_sha256"],
                            inputs_sha256=digest(directory / "INPUTS.json"))
                if bound_source is None:
                    reference = reference_check(reference_root, reference_receipt, reference_sha)
                    report["bindings"] = binding_check(source, reference_root, replay_root, reference, runtime)
                    report["reference_receipt"] = dict(path=str(reference_receipt), sha256=digest(reference_receipt))
                    report["reference_outcomes"] = {arm: metrics(reference["stages"][arm + "/after"]) for arm in fresh.ARMS}
                    collection = read(reference_root / "collect/COLLECTION.json")
                    bound_source = source
                require(source == bound_source, "same_transfer_material_source")
                if phase == "train":
                    require(result["trainer_sha256"] == report["bindings"]["kernel_hashes"]["trainer"]
                            and {name: entry["sha256"] for name, entry in result["code_provenance"].items()} == report["bindings"]["kernel_hashes"],
                            "unchanged_writer_kernel")
                    view = dict(result, arm="SELECTED", source=source["fresh_source"])
                    info.update(fresh.training(directory, view, collection, a1, a2, [1, 1], runtime))
                    uniform = reference["stages"]["UNIFORM/train"]
                    require(info["masks_sha256"] == uniform["masks_sha256"] and info["rows_sha256"] == uniform["rows_sha256"]
                            and info["reference_supervised_tokens"] == uniform["reference_supervised_tokens"]
                            and info["new_fact_presentations"] == [0, 200, 0, 0], "210_same_masks_corpus_denominator_and_dose")
                    if info.get("seconds", 0) > 0:
                        info["updates_per_receipt_second"] = 100 / info["seconds"]
                    trained = result
                else:
                    require(trained is not None and result["training_result_sha256"] == report["stages"]["train"]["result_sha256"]
                            and result["loaded_adapter_state_sha256"] == result["adapter_state_after"] == trained["adapter_state_after"], "saved_unchanged_after_reload")
                    info.update(fresh.readout(directory, result, collection, a1, a2, runtime))
            elif info["status"] == "FAILED":
                info["partial_raw_panels"] = info["failure"].get("panels")
                if collection is not None and info["partial_raw_panels"]:
                    try:
                        info["partial_routing"] = fresh.routing(directory, info["failure"], collection, a1, a2, runtime)
                    except fresh.ERRORS as error:
                        info["partial_replay_error"] = str(error)
        except fresh.ERRORS as error:
            info = dict(status="INVALID", error=type(error).__name__ + ": " + str(error))
        info["path"] = str(directory)
        report["stages"][phase] = info
        if info["status"] != "COMPLETE":
            report[{"PENDING": "pending", "FAILED": "failed", "INVALID": "invalid"}[info["status"]]].append(phase)
    report["status"] = "INVALID_EVIDENCE" if report["invalid"] else "FAILED_STAGES" if report["failed"] else "PARTIAL_EVIDENCE" if report["pending"] else "COMPLETE"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path)
    for name in ("source-root", "reference-root", "reference-receipt", "replay-root", "a1-collection", "a2-collection", "prepare-failure"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--reference-receipt-sha256", default=REFERENCE_SHA256)
    options = parser.parse_args()
    report = reduce(options.root, fresh.load_source(options.source_root) if options.source_root else None,
                    options.reference_root, options.reference_receipt, options.replay_root,
                    read(options.a1_collection) if options.a1_collection else None,
                    read(options.a2_collection) if options.a2_collection else None,
                    options.reference_receipt_sha256, options.prepare_failure)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0 if report["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
