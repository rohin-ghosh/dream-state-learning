"""Reduce captured adult-cycle evidence without models, tokenizers or remote IO.

Incomplete stages remain pending, even if partial panels or losses exist.
Replay establishes consistency; source/adapter authenticity requires the
separately retained file hashes and native receipts, not coherent JSON alone.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.abc
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace


ARMS = ("CUE_REPLAY", "CUE_LOSS_OFF")
STAGES = ("collect", "train", "before", "after")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("ascii")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 16 * 1024 * 1024,
            "bounded_regular_evidence_required:" + str(path))
    return json.loads(path.read_text())


class NoNativeImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"torch", "transformers", "tokenizers", "peft"}:
            raise RuntimeError("native_import_forbidden:" + fullname)


def load_source(directory):
    directory = Path(directory).resolve()
    sys.dont_write_bytecode = True
    sys.meta_path.insert(0, NoNativeImports())
    sys.path.insert(0, str(directory))
    modules = {}
    for label, name in dict(adult="organism_v6.experienced_event_adult_cycle",
                            micro="organism_v6.experienced_event_microloop",
                            controller="organism_v6.experienced_event_read_route",
                            world="organism_v6.pcfl_vertical_dev",
                            source="gpu.astra_experienced_event_microloop",
                            development="gpu.astra_experienced_event_cue_sleep").items():
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve() == directory / (name.replace(".", "/") + ".py"),
                "already_loaded_source_mismatch:" + name)
        modules[label] = module
    return SimpleNamespace(root=directory, **modules)


def terminal(directory):
    directory = Path(directory)
    if (directory / "FAILED.json").exists():
        return {"status": "FAILED", "failure": read(directory / "FAILED.json")}
    if not (directory / "RESULT.json").exists():
        return {"status": "PENDING", "request_present": (directory / "REQUEST.json").exists()}
    result = read(directory / "RESULT.json")
    require(result.get("status") in ("COMPLETE", "COLLECTION_COMPLETE", "COLLECTION_INCOMPLETE_NO_FIT"),
            "unknown_terminal_status")
    return {"status": result["status"], "result": result,
            "result_sha256": digest(directory / "RESULT.json"),
            "start_utc": datetime.fromtimestamp(result["started_unix"], timezone.utc).isoformat(),
            "finish_utc": datetime.fromtimestamp(result["finished_unix"], timezone.utc).isoformat(),
            "seconds": result["finished_unix"] - result["started_unix"]}


def generation(response):
    require(type(response) is dict and type(response.get("raw")) is str
            and type(response.get("terminal")) is bool and type(response.get("truncated")) is bool,
            "generation_schema")
    return response


def collection_summary(directory, result, runtime):
    record = read(directory / "COLLECTION.json")
    require(digest(directory / "COLLECTION.json") == result["collection_sha256"], "collection_file_drift")
    rows = runtime.adult.replay_collection(record)
    require(record["parent_present"] is False and record["clean_claim"] is False and record["fits"] == 0,
            "parent_free_new_material_boundary")
    require(result["accepted_events"] == record["accepted_events"]
            and result["model_calls"] == record["count"], "collection_counts")
    require((result["status"] == "COLLECTION_COMPLETE") == (len(rows) == 32), "collection_admission_status")
    summary = {"collection_sha256": result["collection_sha256"], "accepted_events": record["accepted_events"],
               "rows": len(rows), "model_calls": len(record["captures"]),
               "infrastructure_failures": record["infrastructure_failures"], "parent_present": False,
               "episodes": record["episodes"], "claim": record["claim"],
               "prompt_tokens": sum(capture["response"].get("prompt_tokens", 0) for capture in record["captures"]
                                    if type(capture["response"]) is dict),
               "output_tokens": sum(len(capture["response"].get("token_ids", [])) for capture in record["captures"]
                                    if type(capture["response"]) is dict)}
    return summary, record


def audit_mixture(masks, losses, arm, indexes):
    require(arm in ARMS and len(masks) == 84 and len(losses) == 400, "complete_fixed_adult_mixture")
    for mask in masks:
        inputs, labels, targets = mask["input_ids"], mask["labels"], mask["target_ids"]
        require(len(inputs) == len(labels) and labels[0] == -100, "first_label_or_length")
        positions = [index for index, label in enumerate(labels) if label != -100]
        require(positions and positions == list(range(positions[0], positions[-1] + 1)), "final_target_span")
        require([labels[index] for index in positions] == targets == [inputs[index] for index in positions],
                "target_ids_labels_mismatch")
        require(targets[-1] == 151645 and inputs[positions[-1] + 1:] == [198], "eot_and_masked_template_lf")
    counts, original_total, active_total = Counter(), 0, 0
    for update, loss in enumerate(losses, 1):
        selected = list(indexes(update, 20))
        require(type(loss["update"]) is int and loss["update"] == update
                and loss["row_indexes"] == selected and math.isfinite(loss["loss"]), "loss_or_index_drift")
        original = sum(sum(label != -100 for label in masks[index]["labels"][1:]) for index in selected)
        active = original if arm == "CUE_REPLAY" else original - len(masks[selected[1]]["target_ids"])
        require(loss["original_label_count"] == original and loss["active_label_count"] == active
                and math.isclose(loss["loss_scale"], active / original, rel_tol=1e-12, abs_tol=0),
                "original_denominator_or_active_label_drift")
        counts.update(selected)
        original_total += original
        active_total += active
    doses = [sum(counts[index] for index in group) for group in (range(32), range(32, 52), range(52, 84))]
    require(doses == [400, 400, 800], "group_dose_drift")
    return {"updates": 400, "old_memory_presentations": doses[0], "old_cue_presentations": doses[1],
            "new_memory_presentations": doses[2], "original_supervised_tokens": original_total,
            "supervised_tokens": active_total, "row_counts": dict(counts),
            "loss_first": losses[0]["loss"], "loss_last": losses[-1]["loss"],
            "loss_scale_min": min(loss["loss_scale"] for loss in losses),
            "loss_scale_max": max(loss["loss_scale"] for loss in losses)}


def training_summary(directory, result, collection, runtime, cue_capture=None):
    rows, masks = read(directory / "TRAINING_ROWS.json"), read(directory / "MASKS.json")
    require(set(rows) == {"old_memory", "cue", "new_memory"}, "training_groups")
    require([len(rows[key]) for key in ("old_memory", "cue", "new_memory")] == [32, 20, 32], "training_group_sizes")
    require(rows["new_memory"] == runtime.adult.replay_collection(collection), "new_targets_not_actual_child_rows")
    require(hashlib.sha256(canonical(rows["old_memory"]) + b"\n").hexdigest()
            == result["memory_source"]["compiled_rows_sha256"], "old_rows_provenance")
    require(hashlib.sha256(canonical(rows["cue"])).hexdigest() == result["cue_source"]["rows_sha256"],
            "cue_rows_provenance")
    new_ids_checked = 0
    for row, mask in zip(rows["new_memory"], masks[52:]):
        episode = next(episode for episode in collection["episodes"] if episode["fact"]["event"] == row["event"])
        if row["messages"][-1]["content"] == episode["event"]["raw"]:
            require(mask["target_ids"] == episode["event"]["token_ids"], "new_target_token_drift")
            new_ids_checked += 1
    if cue_capture is not None:
        for name, expected in result["cue_source"]["source_files"].items():
            require(digest(cue_capture / name) == expected, "upstream_cue_file_drift:" + name)
        for row, mask, origin in zip(rows["cue"], masks[32:52], result["cue_source"]["row_origins"]):
            captured = read(cue_capture / ("CALL_%03d.json" % origin["global_call_index"]))
            require(row["assistant"] == captured["response"]["raw"]
                    and mask["target_ids"] == captured["response"]["token_ids"], "actual_cue_target_drift")
    losses = [json.loads(line) for line in (directory / "LOSSES.jsonl").read_text().splitlines()]
    summary = audit_mixture(masks, losses, result["development_arm"], runtime.adult.adult_indexes)
    for key in ("updates", "old_memory_presentations", "old_cue_presentations", "new_memory_presentations",
                "original_supervised_tokens", "supervised_tokens"):
        require(result[key] == summary[key], "training_receipt_count:" + key)
    require(result["adapter_state_before"] == result["loaded_adapter_state_sha256"]
            and result["adapter_state_before"] != result["adapter_state_after"], "adapter_update_state")
    summary.update(new_target_id_rows_checked=new_ids_checked, cue_actual_ids_checked=cue_capture is not None,
                   training_rows_sha256=digest(directory / "TRAINING_ROWS.json"),
                   masks_sha256=digest(directory / "MASKS.json"),
                   adapter_files=result["adapter_files"], adapter_state_before=result["adapter_state_before"],
                   adapter_state_after=result["adapter_state_after"])
    return summary


def audit_route_panel(directory, name, bank, panel, consume, runtime):
    episodes = []
    for number, fact in enumerate(bank, 1):
        record = read(directory / (name + "_EPISODE_%02d.json" % number))
        require(record == panel["episodes"][number - 1] and record["event"] == fact["event"], "episode_panel_join")
        episode = record["episode"]
        actors = iter(trace for trace in episode["traces"] if trace["kind"] == "actor")
        readers = iter(trace for trace in episode["traces"] if trace["kind"] == "memory")

        def actor(messages):
            trace = next(actors)
            require(trace["messages"] == messages, "actor_prompt_drift")
            return consume(name, "actor", trace["response"], messages, False)

        def reader(address):
            trace = next(readers)
            require(trace["address"] == address, "reader_address_drift")
            response = trace["response"]
            if name.startswith("HELD_TEXT"):
                expected = runtime.micro._event(next(fact for fact in bank if fact["event"] == address))
                require(response == dict(raw=expected, terminal=True, truncated=False,
                                         source="RESEARCHER_SUPPLIED_EVAL_TEXT_NOT_PARAMETRIC_MEMORY"),
                        "held_external_bytes_drift")
                return response
            messages = memory_messages(runtime, address, 8)
            return consume(name, "reader", response, messages, name == "OWN_READER_OFF")

        transitions = {other["port"]: other["outcome"] for other in bank if other["node"] == fact["node"]}
        replayed = runtime.controller.run_episode(runtime.controller.public_task(fact), actor, reader, transitions.__getitem__)
        require(replayed == episode and next(actors, None) is None and next(readers, None) is None, "episode_replay_drift")
        episodes.append(dict(episode=number, event=fact["event"], goal=fact["outcome"], outcome=episode["outcome"],
                             reached_goal=episode["outcome"] == fact["outcome"], terminal_reason=episode["terminal_reason"],
                             commands=[trace["raw"] for trace in episode["traces"] if trace["kind"] == "actor"],
                             memories=[trace["raw"] for trace in episode["traces"] if trace["kind"] == "memory"]))
    summary = dict(denominator=len(episodes), reached_goal=sum(episode["reached_goal"] for episode in episodes),
                   with_reads=sum(bool(episode["memories"]) for episode in episodes),
                   second_reads=sum(len(episode["memories"]) == 2 for episode in episodes))
    require(all(panel[key] == value for key, value in summary.items()), "route_panel_totals_drift")
    summary.update(read_calls=sum(len(episode["memories"]) for episode in episodes), episodes=episodes)
    return summary


def memory_messages(runtime, address, wrapper):
    return [dict(role="system", content=runtime.world.MEMORY_SYSTEM),
            dict(role="user", content=runtime.world.WRAPPERS[wrapper].replace("{REQUEST}", "READ EVENT " + address))]


def audit_probes(rows, bank, wrapper, consume, runtime, miss=False):
    require(len(rows) == 4, "four_probe_denominator")
    correct, outputs = 0, []
    for row, fact in zip(rows, bank):
        response = generation(row["generation"])
        consume(response, memory_messages(runtime, fact["event"], wrapper))
        expected = "MISS\n" if miss else runtime.micro._event(fact)
        if not miss:
            require(row["expected"] == expected and row["event"] == fact["event"], "probe_expected_drift")
        success = response["terminal"] is True and response["truncated"] is False and response["raw"] == expected
        require(row["correct"] is success, "probe_score_drift")
        correct += success
        outputs.append(response["raw"])
    return dict(denominator=4, correct=correct, raw_outputs=outputs)


def readout_summary(directory, result, collection, runtime):
    require(result["parent_present"] is False and result["fits"] == 0, "readout_parent_or_fit")
    root = directory / "new_task"
    panels = read(root / "PANELS.json")
    require(all(result["panels"][key] == value for key, value in panels.items()), "nested_panels_result_join")
    paths = sorted(root.glob("CALL_*.json"))
    require([path.name for path in paths] == ["CALL_%03d.json" % index for index in range(1, len(paths) + 1)],
            "consecutive_call_files")
    calls = [read(path) for path in paths]
    cursor = 0

    def consume(panel, role, response, messages, disabled=False):
        nonlocal cursor
        require(cursor < len(calls), "missing_readout_call")
        capture = calls[cursor]
        cursor += 1
        require(capture == dict(panel=panel, role=role, reader_adapter_disabled=disabled, generation=response)
                and response["messages"] == messages, "readout_call_join")
        return generation(response)

    summaries = {}
    bank = collection["bank"]
    banks = {"OWN_PARAMETRIC": bank, "OWN_READER_OFF": bank}
    banks.update({"HELD_TEXT_" + str(index): runtime.micro.build_bank(runtime.development.HELD_MASTER + "-" + str(index))
                  for index in range(2)})
    for name, facts in banks.items():
        summaries[name] = audit_route_panel(root, name, facts, panels[name], consume, runtime)
    for name, wrapper, facts, miss in (
            ("RECALL_W0", 0, bank, False), ("RECALL_W8", 8, bank, False),
            ("UNSEEN_MISS", 8, runtime.micro.build_bank(runtime.source.MASTER + "-UNSEEN-MISS"), True)):
        summaries[name] = audit_probes(panels[name]["rows"], facts, wrapper,
                                      lambda response, messages: consume(name, "memory_probe", response, messages), runtime, miss)
        require(summaries[name]["correct"] == panels[name]["correct"] and panels[name]["denominator"] == 4,
                "probe_panel_total")
    require(cursor == len(calls), "unused_readout_calls")
    old_calls = []
    for wrapper in (0, 8):
        name = "OLD_RECALL_W" + str(wrapper)
        rows = [read(directory / (name + "_%02d.json" % number)) for number in range(1, 5)]
        require(result["panels"][name]["rows"] == rows, "old_recall_join")

        def old_consume(response, messages):
            require(response["messages"] == messages, "old_recall_prompt")
            old_calls.append(dict(role="old_memory_probe", generation=response))

        summaries[name] = audit_probes(rows, runtime.micro.build_bank(runtime.source.MASTER), wrapper, old_consume, runtime)
        require(summaries[name]["correct"] == result["panels"][name]["correct"]
                and result["panels"][name]["denominator"] == 4, "old_recall_total")
    require(len(calls) + len(old_calls) == result["model_calls"] <= 84, "complete_readout_call_count")
    all_calls = calls + old_calls
    return dict(panels=summaries, model_calls=len(all_calls),
                roles=dict(Counter(call["role"] for call in all_calls)),
                prompt_tokens=sum(call["generation"]["prompt_tokens"] for call in all_calls),
                output_tokens=sum(len(call["generation"]["token_ids"]) for call in all_calls))


def reduce_campaign(root, runtime, cue_capture=None):
    root = Path(root)
    report = {"arms": {}, "claim": "SINGLE_CYCLE_WHOLE_TRAJECTORY_CONFOUNDED_NOT_H2", "pending": []}
    collections = {}
    runner_hash = digest(runtime.root / "gpu/astra_experienced_event_adult_cycle.py")
    material_hash = digest(runtime.root / "organism_v6/experienced_event_adult_cycle.py")
    for arm in ARMS:
        summaries, results = {}, {}
        for stage in STAGES:
            directory = root / arm / stage
            info = terminal(directory)
            summaries[stage] = info
            if info["status"] in ("PENDING", "FAILED"):
                if info["status"] == "PENDING":
                    report["pending"].append(arm + "/" + stage)
                continue
            result = info.pop("result")
            results[stage] = result
            request = read(directory / "REQUEST.json")
            for key, value in request.items():
                require(result[key] == value, "request_result_drift:" + key)
            require(result["development_arm"] == arm and result["runner_sha256"] == runner_hash
                    and result["material_sha256"] == material_hash and result["frozen_base_unchanged"] is True,
                    "stage_source_arm_base_binding")
            info.update(initial_training_result_sha256=result["initial_training_result_sha256"],
                        initial_adapter_sha256=result["arguments"]["expected_initial_adapter_sha256"],
                        loaded_adapter_state_sha256=result["loaded_adapter_state_sha256"],
                        base_sha256=result["arguments"]["expected_base_sha256"])
            if stage == "collect":
                detail, collection = collection_summary(directory, result, runtime)
                collections[arm] = collection
            else:
                require("collect" in results, "terminal_collection_required_for_stage")
                for key in ("initial_training_result_sha256", "memory_source", "cue_source", "tokenizer"):
                    require(result[key] == results["collect"][key], "same_child_provenance:" + key)
                for key in ("expected_initial_adapter_sha256", "initial_adapter_dir", "model_dir", "expected_base_sha256"):
                    require(result["arguments"][key] == results["collect"]["arguments"][key], "same_child_argument:" + key)
                require(result["adult_source"]["collection_sha256"] == results["collect"]["collection_sha256"]
                        and result["adult_source"]["result_sha256"] == summaries["collect"]["result_sha256"],
                        "adult_input_receipt_join")
                expected_state = (results["train"]["adapter_state_after"] if stage == "after"
                                  else results["collect"]["loaded_adapter_state_sha256"])
                require(result["loaded_adapter_state_sha256"] == expected_state, "same_loaded_child_or_saved_after_state")
                detail = (training_summary(directory, result, collection, runtime, cue_capture) if stage == "train"
                          else readout_summary(directory, result, collection, runtime))
            info.update(detail)
        report["arms"][arm] = summaries
    if len(collections) == 2:
        report["same_collection_bytes"] = (report["arms"][ARMS[0]]["collect"]["collection_sha256"]
                                           == report["arms"][ARMS[1]]["collect"]["collection_sha256"])
        report["same_child_targets"] = collections[ARMS[0]]["rows"] == collections[ARMS[1]]["rows"]
        report["same_initial_adapter_between_arms"] = (report["arms"][ARMS[0]]["collect"]["loaded_adapter_state_sha256"]
                                                      == report["arms"][ARMS[1]]["collect"]["loaded_adapter_state_sha256"])
    report.update(runner_sha256=runner_hash, material_sha256=material_hash,
                  status="PARTIAL_TERMINAL_EVIDENCE" if report["pending"] else "ALL_STAGES_TERMINAL",
                  no_native_imports=not any(name in sys.modules for name in ("torch", "transformers", "tokenizers", "peft")))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-root", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--cue-capture", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    report = reduce_campaign(args.capture_root, load_source(args.source_root), args.cue_capture)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(dict(status=report["status"], pending=report["pending"], no_native_imports=report["no_native_imports"])))


if __name__ == "__main__":
    main()
