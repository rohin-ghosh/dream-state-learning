"""Offline UNFINALIZED C0 capture inspection, never finalization or collection."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_zero_fit_analyze as audit

driver, native = audit.driver, audit.native
same, require = audit.same, audit.require
SCOPE = ("UNFINALIZED CAPTURE INSPECTION ONLY; diagnostic_usable=false; finalization_failed=true. "
         "Original failure preserved; no finalization or model-call retry. No collection or release attestation. "
         "Worker/GPU observations describe capture time, not current hardware or reservation release. "
         "Caller supplies copied outer evidence; capture does not record its original directory. " + audit.LIMITS)
CAPTURE_FILES = set(("context.json preflight_queue.json preflight_cvd.json preflight_gpu.json "
                     "stdout.log stderr.log spawn.json worker_start.json worker_wait.json "
                     "worker_release.json post_worker_gpu.json post_worker_cvd.json worker_exit.json").split())


def capture_lineage(data, outer, manifest_hash, capture_hash):
    same(data.inventory["manifest.json"]["sha256"], manifest_hash, "manifest byte pin")
    same(outer.inventory["capture_complete.json"]["sha256"], capture_hash, "capture byte pin")
    manifest, report, capture = data.read("manifest.json"), data.read("report.json"), outer.read("capture_complete.json")
    for sealed in (manifest, report):
        driver._unseal(sealed)
    same(capture["schema"], audit.OUTER + "/captured", "capture schema")
    same(data.inventory, capture["output_inventory"], "captured diagnostic inventory")
    same(sorted(capture["outer_files"]), sorted(CAPTURE_FILES), "capture receipt inventory")
    for name, checksum in capture["outer_files"].items():
        same(outer.inventory[name]["sha256"], checksum, "capture receipt byte pin")
    same([capture[key] for key in ("manifest_sha256", "report_sha256", "report_file_sha256")],
         [manifest["sha256"], report["sha256"], data.inventory["report.json"]["sha256"]], "capture seals")
    same([capture[key] for key in ("status", "finalized", "fits", "updates", "worker_group_released", "gpu_compute_vacant")],
         ["CAPTURED_AWAITING_RESERVATION_RELEASE", False, 0, 0, True, True], "capture completion")
    context, worker = outer.read("context.json"), outer.read("worker_start.json")
    same([context[key] for key in ("schema", "manifest_file_sha256", "output_dir")],
         [audit.OUTER, manifest_hash, manifest["output_dir"]], "context binding")
    original = Path(manifest["output_dir"])
    require(original.is_absolute() and original.parent != Path("/"), "original output path")
    for archive in (data, outer):
        require(not archive.root.is_relative_to(original) and not original.is_relative_to(archive.root), "relocate outside original diagnostic tree")
    same([worker["manifest_file_sha256"], worker["gpu_uuid"]], [manifest_hash, report["gpu_uuid"]], "worker binding")
    exited, release = outer.read("worker_exit.json"), outer.read("worker_release.json")
    same([exited["identity"], release["identity"]], [worker["identity"]] * 2, "worker ownership")
    same([exited["returncode"], outer.read("worker_wait.json")["value"], release["owned_group_released"]], [0, 0, True], "worker exit/release")
    same(outer.read("post_worker_gpu.json")["value"]["empty"], True, "capture GPU observation")
    cvd = outer.read("post_worker_cvd.json")["value"]
    same([capture[key] for key in ("reservation_released", "reservation_check_status", "complete_cvd_visibility")],
         [cvd[key] for key in ("device_unreserved", "reservation_check_status", "complete_cvd_visibility")], "capture visibility")
    phase = ["final_queue.json", "final_cvd.json"]
    if "final_cvd_after_gpu.json" in outer.inventory:
        phase += ["final_gpu.json", "final_cvd_after_gpu.json"]
    same(sorted(outer.inventory), sorted(CAPTURE_FILES | {"capture_complete.json", "finalize_claim.json", "finalize_failure.json"} | set(phase)), "unfinalized outer inventory")
    claim, failure = outer.read("finalize_claim.json"), outer.read("finalize_failure.json")
    same(claim["retry"], False, "finalization retry forbidden")
    expected_error = "late reservation/group appeared" if len(phase) == 4 else "CVD owner remains; release Main holder before finalization"
    same(failure, {"type": "ValueError", "error": expected_error}, "actual CVD finalization failure")
    cap = min(manifest["wall_seconds"], manifest["device_seconds"])
    times = [context["entry_monotonic"], worker["spawn_started_monotonic"], report["started_monotonic"],
             report["started_monotonic"] + report["wall_seconds_through_close"], exited["ended_monotonic"],
             context["entry_monotonic"] + capture["elapsed_seconds"], claim["started_monotonic"]]
    for name in phase:
        observation = outer.read(name)
        times.extend([observation["started_monotonic"], observation["ended_monotonic"]])
        if name != phase[-1]:
            value = observation["value"]
            require(value.get("matched") is True if name == "final_queue.json" else
                    value.get("empty") is True if name == "final_gpu.json" else
                    value.get("clear") is True and value["owners"] == [], "prior finalization observation")
    blocked = outer.read(phase[-1])["value"]
    require(blocked["clear"] is False and blocked["reservation_check_status"] == "BLOCKED"
            and blocked["complete_cvd_visibility"] is False and blocked["unresolved"], "unreadable CVD failure evidence")
    require(any(type(entry["pid"]) is int and entry["pid"] > 1 and entry["error_type"] == "PermissionError"
                for entry in blocked["unresolved"]), "unreadable PID evidence")
    for value in (*times, context["deadline_monotonic"], manifest["wall_seconds"], manifest["device_seconds"]):
        native.number(value)
    require(0 < cap <= 36000 and times == sorted(times) and times[-1] <= context["deadline_monotonic"]
            and times[-1] - times[0] <= cap, "capture/finalizer clocks")
    return manifest, report, {"failure": failure, "failed_observation": phase[-1], "observation": blocked,
                              "capture_elapsed_seconds": capture["elapsed_seconds"], "capture_visibility": cvd}


def replay_rows(data, manifest, report):
    replay, rows, groups, lengths = audit.Replay(data, manifest), [], defaultdict(Counter), {}
    for index, task in enumerate(manifest["plan"]["tasks"]):
        before = replay.stats.copy()
        row = {**replay._task(task), "execution": "SCORED"}
        same(data.read(f"task_{index:03}.json"), row, "raw scorer/task disagreement")
        rows.append(row)
        render = task["id"].split("/")[-2] if task["panel"] == "reachout" else "TASK"
        lengths[task["id"]] = len(replay.measured["initial/" + task["id"]]["token_ids"])
        try:
            (audit.core.parse_route if task["panel"] == "delayed" else audit.core.parse_probe)(row["raw"])
            invalid = 0
        except ValueError:
            invalid = 1
        counts = Counter(tasks=1, denominator=1, correct=int(row["success"]), invalid_final_syntax=invalid,
                         invalid_read=int(row["invalid_read"]), usable_false_rows=int(row["usable_false_row"]),
                         served_reads=len(row["reads"]), returned_tokens=row["returned_tokens"], initial_prompt_tokens=lengths[task["id"]])
        counts.update({key: replay.stats[key] - before[key] for key in replay.stats})
        counts["tasks_with_truncation"] = int(counts["truncated_calls"] > 0)
        for key in ("all", "root/" + row["root"], row["panel"], f"{row['panel']}/{row['projection']}",
                    f"{row['panel']}/{row['projection']}/{render}", f"{row['root']}/{row['panel']}/{row['projection']}/{render}"):
            groups[key].update(counts)
    same(report["results"], rows, "report task ordering/scores")
    panels = driver._panels(rows)
    same(report["panels"], panels, "panel audit")
    same(report["thresholds_passed"], all(panel["passed"] for panel in panels.values()), "threshold audit")
    same([report["actor_attempts"], report["actor_responses"]], [replay.calls, replay.calls], "call totals")
    for identifier, length in lengths.items():
        if "/RA/" in identifier:
            same(length - lengths[identifier.replace("/RA/", "/RB/")], 1, "declared RA/RB length difference")
    return replay, panels, groups, lengths


def inspect(diagnostic_dir, outer_dir, *, manifest_sha256, capture_sha256):
    data, outer = audit.Archive(diagnostic_dir), audit.Archive(outer_dir)
    require(not data.root.is_relative_to(outer.root) and not outer.root.is_relative_to(data.root), "archive overlap")
    manifest, report, failure = capture_lineage(data, outer, manifest_sha256, capture_sha256)
    same(manifest["schema"], driver.SCHEMA, "manifest schema")
    same([manifest[key] for key in ("test_only", "fits", "updates", "full_v22_release")], [False, 0, 0, False], "native zero-fit scope")
    same(manifest["plan"], driver.build_tasks(manifest["plan"]["roots"]), "fixed task IDs/prompts/slots")
    pinned = {Path(path).name: checksum for path, checksum in manifest["sources"].items()}
    require(len(pinned) == len(manifest["sources"]), "ambiguous source names")
    same(pinned, {Path(path).name: checksum for path, checksum in driver.source_snapshot().items()}, "local replay source drift")
    driver._check_measurements(manifest["measurements"])
    same(sorted(entry["id"] for entry in manifest["measurements"]["measurements"] if entry["id"].startswith("initial/")),
         sorted("initial/" + task["id"] for task in manifest["plan"]["tasks"]), "exact measured task coverage")
    same([manifest["measurements"][key] for key in ("schema", "kind", "plan_sha256", "binding")],
         [driver.SCHEMA + "/tokens", "ACTUAL_OFFLINE", manifest["plan"]["sha256"], driver.tokenizer_binding(manifest["actor"])], "tokenizer lineage")
    same(manifest["panels"], {"delayed": {key: list(value) for key, value in audit.runtime.DELAYED.items()},
                              "reachout": {key: list(value) for key, value in audit.runtime.REACHOUT.items()}}, "declared thresholds")
    same([report[key] for key in ("schema", "manifest_sha256", "actor_config_sha256", "source_files_sha256", "tokenizer_measurements_sha256", "test_only", "tasks", "scored_tasks", "fits", "updates", "full_v22_release", "diagnostic_usable", "error", "status")],
         [driver.SCHEMA + "/report", manifest["sha256"], audit.digest(manifest["actor"]), audit.digest(manifest["sources"]), manifest["measurements"]["sha256"], False, 800, 800, 0, 0, False, False, None, "COMPLETE_AWAITING_OUTER_RELEASE"], "report scope/completeness/pins")
    same([report["gpu_uuid"], report["wall_cap"], report["device_cap"]], [manifest["actor"]["gpu_uuid"], manifest["wall_seconds"], manifest["device_seconds"]], "report caps/GPU")
    same(data.read("actor/config.json"), manifest["actor"], "actor config")
    same([manifest["actor"][key] for key in ("engine", "max_calls", "max_output_tokens", "device_seconds_cap")], [native.ENGINE, 1952, 2048, manifest["device_seconds"]], "frozen actor")
    identity = data.read("actor/identity.json")
    same([identity["kind"], identity["config_sha256"]], ["NATIVE", audit.digest(manifest["actor"])], "actor identity")
    identity = identity["identity"]
    same([identity[key] for key in ("repository", "revision", "model_binding_sha256", "source_files", "environment", "gpu_uuid_expected", "mount", "lora_request", "clean_lineage_certified")],
         [native.MODEL_NAME, native.REVISION, manifest["actor"]["model_binding"]["sha256"], manifest["actor"]["source_files"], manifest["actor"]["environment"], manifest["actor"]["gpu_uuid"], "C0", None, False], "frozen Qwen identity")
    require(len(identity["model_files"]) == 14 and not any("adapter" in name.lower() for name in identity["model_files"]), "base file inventory")
    same(sorted(manifest["actor"]["tokenizer_files"]), sorted(native.TOKENIZER_FILES), "tokenizer inventory")
    for name, checksum in manifest["actor"]["tokenizer_files"].items():
        same(identity["model_files"][name], checksum, "tokenizer files")
    for path, checksum in manifest["sources"].items():
        same(identity["source_files"].get(path), checksum, "identity source")
    replay, panels, groups, lengths = replay_rows(data, manifest, report)
    close, load = data.read("actor/close.json"), data.read("actor/load.json")
    same(close, report["backend_close"], "close receipt")
    same([close[key] for key in ("kind", "error_type", "failed", "budget_exceeded", "calls_consumed", "token_count_calls")], ["NATIVE", None, False, False, replay.calls, replay.counts], "close completion")
    same([load[key] for key in ("kind", "mount", "lora_request")], ["NATIVE", "C0", None], "load identity")
    for value in (load["operation_started"], load["model_load_started"], load["ready_at"], close["elapsed_actor_seconds"]):
        native.number(value)
    require(report["started_monotonic"] <= load["operation_started"] <= load["model_load_started"] <= load["ready_at"] <= report["started_monotonic"] + report["wall_seconds_through_close"]
            and replay.stats["actor_call_operation_wall_seconds"] <= close["elapsed_actor_seconds"] <= report["wall_seconds_through_close"], "load/actor elapsed")
    same(sorted(data.inventory), sorted(replay.used | {f"task_{index:03}.json" for index in range(800)} |
         {"manifest.json", "report.json", "actor/config.json", "actor/identity.json", "actor/load.json", "actor/close.json"}), "extra/missing task or actor files")
    for archive in (data, outer):
        same(archive.snapshot(), archive.inventory, "archive changed during inspection")
    return {"schema": driver.SCHEMA + "/unfinalized_capture_inspection_v1", "evidence_audit": "UNFINALIZED_CAPTURE_REPLAY_MATCH",
            "diagnostic_usable": False, "finalization_failed": True, "full_v22_release": False,
            "fits": 0, "updates": 0, "parents": 0, "tasks": 800, "counts": dict(groups), "panels": panels,
            "failure_summary": failure, "initial_prompt_lengths": lengths, "scope": SCOPE,
            "manifest_file_sha256": manifest_sha256, "capture_file_sha256": capture_sha256, "report_sha256": report["sha256"],
            "outer_inventory": outer.inventory, "replay_source_sha256": pinned,
            "inspector_sha256": driver._file_hash(__file__), "analyzer_sha256": driver._file_hash(audit.__file__),
            "elapsed_costs_not_gpu_active": {**{key: value for key, value in replay.stats.items() if key.endswith("seconds")},
                "actor_operations_wall_seconds": close["elapsed_actor_seconds"], "cold_model_load_wall_seconds": load["ready_at"] - load["model_load_started"],
                "diagnostic_wall_seconds_through_close": report["wall_seconds_through_close"], "outer_entry_through_capture_seconds": failure["capture_elapsed_seconds"]}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("diagnostic", "outer", "manifest-sha256", "capture-sha256", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    require(not output.exists() and not output.is_symlink() and output.parent.resolve() == output.absolute().parent, "fresh unaliased output required")
    for path in (args.diagnostic, args.outer):
        require(not output.resolve().is_relative_to(Path(path).resolve()) and not Path(path).resolve().is_relative_to(output.resolve()), "output/archive overlap")
    result = inspect(args.diagnostic, args.outer, manifest_sha256=args.manifest_sha256, capture_sha256=args.capture_sha256)
    output.mkdir(exist_ok=False)
    with (output / "inspection.json").open("xb") as stream:
        stream.write(audit.canonical(result) + b"\n")
    with (output / "inspection.md").open("x", encoding="utf-8") as stream:
        stream.write("# UNFINALIZED C0 capture inspection\n\n" + SCOPE + "\n\n```json\n" + json.dumps(result, sort_keys=True, indent=2) + "\n```\n")


if __name__ == "__main__":
    main()
