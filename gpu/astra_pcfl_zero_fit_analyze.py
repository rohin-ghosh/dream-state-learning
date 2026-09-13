"""Offline, fixed C0 receipt replay. Never collect, tokenize, generate, or release."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_zero_fit_dev as driver

core, runtime, native = driver.core, driver.runtime, driver.native
require, canonical, digest = native.require, native.canonical, native.digest
OUTER = "pcfl.zero_fit_outer.v2"
LIMITS = ("Excluded-root C0 interface diagnostic only; zero fits/updates/parents. "
          "RA prompts are one token longer than RB: no causal order-only comparison or full RA/RB qualification. "
          "No learning, H1/H2, clean ancestry, C11, or full-assay claim. "
          "Token IDs/decode are cross-receipt audits, not an independent tokenizer replay. "
          "Release observations are archived attestations, not fresh process/GPU checks.")


def same(actual, expected, label):
    require(canonical(actual) == canonical(expected), label)


class Archive:
    def __init__(self, root):
        self.root = Path(root).absolute()
        require(self.root.is_dir() and self.root.resolve() == self.root, "unaliased archive required")
        self.inventory = self.snapshot()

    def snapshot(self):
        inventory = {}
        for path in sorted(self.root.rglob("*")):
            require(not path.is_symlink(), "archive symlink")
            if path.is_dir():
                continue
            require(path.is_file(), "nonregular archive entry")
            with path.open("rb") as stream:
                checksum = hashlib.file_digest(stream, "sha256").hexdigest()
            inventory[path.relative_to(self.root).as_posix()] = {"size": path.stat().st_size, "sha256": checksum}
        return inventory

    def read(self, name):
        require(name in self.inventory, "missing archived file: " + name)
        data = (self.root / name).read_bytes()
        same({"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}, self.inventory[name], "archive changed")
        def unique(pairs):
            result = dict(pairs)
            require(len(result) == len(pairs), "duplicate JSON keys")
            return result
        value = json.loads(data, object_pairs_hook=unique)
        canonical(value)
        return value


def lineage(data, outer, manifest_hash, collection_hash):
    same(data.inventory["manifest.json"]["sha256"], manifest_hash, "manifest byte pin")
    same(outer.inventory["collection.json"]["sha256"], collection_hash, "collection byte pin")
    manifest, report = data.read("manifest.json"), data.read("report.json")
    collection, capture = outer.read("collection.json"), outer.read("capture_complete.json")
    final, receipt = outer.read("final.json"), outer.read("release_receipt.json")
    for sealed in (manifest, report, final):
        driver._unseal(sealed)
    require(collection["schema"] == OUTER + "/collection" and capture["schema"] == OUTER + "/captured", "outer schema")
    same({name: entry["sha256"] for name, entry in outer.inventory.items() if name != "collection.json"}, collection["files"], "outer inventory")
    require(not any("failure" in name or "error" in name for name in outer.inventory), "outer failure evidence")
    same(data.inventory, capture["output_inventory"], "captured diagnostic inventory")
    same(digest(data.inventory), collection["output_inventory_sha256"], "inventory seal")
    for name, checksum in capture["outer_files"].items():
        same(collection["files"].get(name), checksum, "capture receipt lineage")
    same(capture["manifest_sha256"], manifest["sha256"], "capture manifest")
    same(capture["report_sha256"], report["sha256"], "capture report")
    same(capture["report_file_sha256"], data.inventory["report.json"]["sha256"], "report byte pin")
    same([capture[key] for key in ("status", "finalized", "fits", "updates", "worker_group_released", "gpu_compute_vacant")], ["CAPTURED_AWAITING_RESERVATION_RELEASE", False, 0, 0, True, True], "capture completion")
    context = outer.read("context.json")
    same(context["manifest_file_sha256"], manifest_hash, "context manifest")
    same(context["output_dir"], manifest["output_dir"], "context output")
    require(data.root != Path(manifest["output_dir"]) and outer.root != Path(receipt["evidence_path"]).parent, "use relocated archives, not live paths")
    same(final["schema"], driver.SCHEMA + "/final", "final schema")
    same(final["cpu_test_complete"], False, "native final cannot be synthetic")
    same(final["report"], report, "final report")
    same(final["outer_release"], receipt, "final release")
    same(receipt["report_sha256"], report["sha256"], "release report")
    same(receipt["gpu_uuid"], report["gpu_uuid"], "release GPU")
    same(receipt["evidence_sha256"], outer.inventory["release_attestation.json"]["sha256"], "attestation byte pin")
    same(outer.read("release_attestation.json"), {key: value for key, value in receipt.items() if key not in ("evidence_path", "evidence_sha256")}, "attestation")
    require(receipt["owned_group_released"] is True and receipt["gpu_vacant"] is True and final["diagnostic_usable"] is True and final["full_v22_release"] is False, "unfinalized evidence")
    for name in ("worker_exit.json", "worker_wait.json"):
        value = outer.read(name)
        same(value["returncode" if name == "worker_exit.json" else "value"], 0, "worker exit")
    require(outer.read("worker_release.json")["owned_group_released"] is True and outer.read("final_gpu.json")["value"]["empty"] is True and outer.read("final_queue.json")["value"]["matched"] is True, "release observations")
    cvd = outer.read("final_cvd_after_gpu.json")["value"]
    require(cvd["clear"] is True and cvd["owners"] == [], "reservation observation")
    prior_cvd = outer.read("final_cvd.json")["value"]
    require(prior_cvd["clear"] is True and prior_cvd["owners"] == [], "pre-GPU reservation observation")
    for key in ("reservation_check_status", "complete_cvd_visibility"):
        same(collection[key], cvd[key], "reservation limitation drift")
    same(collection["approved_unreadable_service_pids"], [entry["pid"] for entry in cvd["approved_unreadable_services"]], "service exceptions")
    same([collection[key] for key in ("fits", "updates", "generation_retries", "full_v22_release")], [0, 0, 0, False], "collection scope")
    elapsed = receipt["elapsed_seconds_from_start"]
    for value in (manifest["wall_seconds"], manifest["device_seconds"]):
        native.number(value, positive=True)
    for value in (elapsed, collection["outer_elapsed_seconds"], context["entry_monotonic"], context["deadline_monotonic"], collection["release_monotonic"], report["started_monotonic"], report["wall_seconds_through_close"]):
        native.number(value)
    cap = min(manifest["wall_seconds"], manifest["device_seconds"])
    require(0 < cap <= 36000 and report["wall_seconds_through_close"] <= elapsed <= collection["outer_elapsed_seconds"] <= cap, "elapsed envelope")
    same(collection["release_monotonic"] - report["started_monotonic"], elapsed, "release clock")
    require(context["entry_monotonic"] <= report["started_monotonic"] and collection["release_monotonic"] <= context["entry_monotonic"] + collection["outer_elapsed_seconds"] <= context["deadline_monotonic"], "outer clock")
    return manifest, report, collection, receipt


class Replay(runtime.Runtime):
    def __init__(self, data, manifest):
        self.data, self.manifest, self.backend = data, manifest, self
        self.calls = self.counts = 0
        self.used = set()
        self.stats = Counter()
        self.measured = {entry["id"]: entry for entry in manifest["measurements"]["measurements"]}
        self.service = {entry["text"]: entry["token_ids"] for key, entry in self.measured.items() if key.startswith(("block/", "service/"))}
        for key, entry in self.measured.items():
            if key.startswith(("block/", "service/")):
                same(entry["token_ids"], self.service[entry["text"]], "inconsistent service token IDs")

    def read(self, name):
        self.used.add(name)
        return self.data.read(name)

    def count_tokens(self, text):
        record = self.read(f"actor/count_{self.counts:04}.json")
        self.counts += 1
        same(record, {"text": text, "sha256": core.byte_hash(text), "token_ids": self.service[text]}, "READ token receipt")
        self.stats.update(service_token_count_operations=1, counted_service_tokens=len(record["token_ids"]))
        return len(record["token_ids"])

    def _generate(self, task, messages, turn, actor_tokens, returned_tokens):
        require(self.calls < 1952 and turn <= (12 if task["projection"] == "ACTIVE_LINKED_TEXT" else 0), "conditional C0 budget")
        name = f"call_{self.calls:04}"
        self.calls += 1
        call, response = self.read(name + "_request.json"), self.read(name + "_response.json")
        request = {"id": f"{core.byte_hash(task['id'])}/actor/{turn}", "messages": messages, "seed": task["seed"], "mount": "C0"}
        same(call["request"], request, "task request/transcript")
        same(call["request_sha256"], digest(request), "request seal")
        same(call["response"], None, "request must precede response")
        limits = call["limits"]
        same([limits[key] for key in ("output_tokens", "returned_tokens", "remaining_reads", "input_tokens")], [2048 - actor_tokens, 4096 - returned_tokens, 12 - turn, len(call["input_token_ids"])], "task budgets")
        actor_request = self.read("actor/" + name + ".request.json")
        same({key: actor_request[key] for key in ("request", "limits", "request_sha256")}, {"request": request, "limits": limits, "request_sha256": digest(request)}, "actor request")
        render, raw = self.read("actor/" + name + ".render.json"), self.read("actor/" + name + ".raw.json")
        for record in (render, raw):
            same([record["mount"], record["lora_request"]], ["C0", None], "C0 only")
        same(render["sampling"], {**native.SAMPLING, "seed": task["seed"], "max_tokens": limits["output_tokens"]}, "sampling")
        same(core.byte_hash(render["rendered_prompt"]), call["render_sha256"], "render seal")
        same(render["prompt_token_ids"], call["input_token_ids"], "prompt IDs")
        if turn == 0:
            measurement = self.measured["initial/" + task["id"]]
            same([render["rendered_prompt"], call["input_token_ids"]], [measurement["text"], measurement["token_ids"]], "initial measured surface")
        same([raw["kind"], raw["request_sha256"]], ["NATIVE", digest(request)], "native raw binding")
        output = raw["raw"]
        native.token_ids(output["output_token_ids"])
        native.token_ids(call["input_token_ids"])
        same(output["prompt_token_ids"], call["input_token_ids"], "raw prompt IDs")
        wrapped = self.read("actor/" + name + ".response.json")
        same(wrapped, {"response": response, "raw_utf8_sha256": core.byte_hash(output["text"]), "raw_hex": output["text"].encode().hex(), "decoded": output["text"]}, "raw/decoded response")
        same(response, {"request_sha256": digest(request), "text": output["text"], "prompt_tokens": len(call["input_token_ids"]), "output_tokens": len(output["output_token_ids"]), "device_seconds": response["device_seconds"]}, "response counts/text")
        require(output["finish_reason"] in ("length", "stop") and (output["stop_reason"] is None or type(output["stop_reason"]) in (int, str)), "termination")
        require(0 < limits["output_tokens"] and len(output["output_token_ids"]) <= limits["output_tokens"] and (output["output_token_ids"] or not output["text"]), "output budget")
        require(0 < response["prompt_tokens"] <= self.manifest["actor"]["max_input_tokens"] and response["prompt_tokens"] + limits["output_tokens"] <= native.ENGINE["max_model_len"], "context budget")
        for value in (raw["operation_started"], raw["generation_started"], raw["generation_ended"], response["device_seconds"], limits["device_seconds"], limits["deadline"]):
            native.number(value)
        same(raw["operation_started"], actor_request["started"], "operation clock")
        require(raw["operation_started"] <= raw["generation_started"] <= raw["generation_ended"] <= limits["deadline"] <= self.manifest["actor"]["deadline"] and raw["generation_ended"] - raw["operation_started"] <= response["device_seconds"] <= limits["device_seconds"], "call elapsed")
        self.stats.update(calls=1, prompt_tokens=response["prompt_tokens"], output_tokens=response["output_tokens"], truncated_calls=int(output["finish_reason"] == "length"), read_requests=int(output["text"].startswith("READ ")))
        self.stats["actor_call_operation_wall_seconds"] += response["device_seconds"]
        self.stats["generation_wall_seconds"] += raw["generation_ended"] - raw["generation_started"]
        return response


def analyze(diagnostic_dir, outer_dir, *, manifest_sha256, collection_sha256):
    """Audit relocated archives against independently supplied byte hashes; no writes."""
    data, outer = Archive(diagnostic_dir), Archive(outer_dir)
    manifest, report, collection, receipt = lineage(data, outer, manifest_sha256, collection_sha256)
    same(manifest["schema"], driver.SCHEMA, "manifest schema")
    same([manifest[key] for key in ("test_only", "fits", "updates", "full_v22_release")], [False, 0, 0, False], "native zero-fit scope")
    same(manifest["plan"], driver.build_tasks(manifest["plan"]["roots"]), "fixed task IDs/prompts/slots")
    pinned = {Path(path).name: checksum for path, checksum in manifest["sources"].items()}
    require(len(pinned) == len(manifest["sources"]), "ambiguous source names")
    same(pinned, {Path(path).name: checksum for path, checksum in driver.source_snapshot().items()}, "local replay source drift")
    driver._check_measurements(manifest["measurements"])
    same(sorted(entry["id"] for entry in manifest["measurements"]["measurements"] if entry["id"].startswith("initial/")), sorted("initial/" + task["id"] for task in manifest["plan"]["tasks"]), "exact measured task coverage")
    same([manifest["measurements"][key] for key in ("schema", "kind", "plan_sha256", "binding")], [driver.SCHEMA + "/tokens", "ACTUAL_OFFLINE", manifest["plan"]["sha256"], driver.tokenizer_binding(manifest["actor"])], "tokenizer lineage")
    same(manifest["panels"], {"delayed": {key: list(value) for key, value in runtime.DELAYED.items()}, "reachout": {key: list(value) for key, value in runtime.REACHOUT.items()}}, "declared thresholds")
    same([report[key] for key in ("schema", "manifest_sha256", "actor_config_sha256", "source_files_sha256", "tokenizer_measurements_sha256", "test_only", "tasks", "scored_tasks", "fits", "updates", "full_v22_release", "diagnostic_usable", "error", "status")], [driver.SCHEMA + "/report", manifest["sha256"], digest(manifest["actor"]), digest(manifest["sources"]), manifest["measurements"]["sha256"], False, 800, 800, 0, 0, False, False, None, "COMPLETE_AWAITING_OUTER_RELEASE"], "report scope/completeness/pins")
    same([report["gpu_uuid"], report["wall_cap"], report["device_cap"]], [manifest["actor"]["gpu_uuid"], manifest["wall_seconds"], manifest["device_seconds"]], "report caps/GPU")
    same(data.read("actor/config.json"), manifest["actor"], "actor config")
    same([manifest["actor"][key] for key in ("engine", "max_calls", "max_output_tokens", "device_seconds_cap")], [native.ENGINE, 1952, 2048, manifest["device_seconds"]], "frozen actor")
    identity = data.read("actor/identity.json")
    same([identity["kind"], identity["config_sha256"]], ["NATIVE", digest(manifest["actor"])], "actor identity")
    identity = identity["identity"]
    same([identity[key] for key in ("repository", "revision", "model_binding_sha256", "source_files", "environment", "gpu_uuid_expected", "mount", "lora_request", "clean_lineage_certified")], [native.MODEL_NAME, native.REVISION, manifest["actor"]["model_binding"]["sha256"], manifest["actor"]["source_files"], manifest["actor"]["environment"], manifest["actor"]["gpu_uuid"], "C0", None, False], "frozen Qwen identity")
    require(len(identity["model_files"]) == 14 and not any("adapter" in name.lower() for name in identity["model_files"]), "base file inventory")
    for name, checksum in manifest["actor"]["tokenizer_files"].items():
        same(identity["model_files"][name], checksum, "tokenizer files")
    same(sorted(manifest["actor"]["tokenizer_files"]), sorted(native.TOKENIZER_FILES), "tokenizer inventory")
    for path, checksum in manifest["sources"].items():
        same(identity["source_files"].get(path), checksum, "identity source")
    replay, rows, groups, render_lengths = Replay(data, manifest), [], defaultdict(Counter), {}
    for index, task in enumerate(manifest["plan"]["tasks"]):
        before = replay.stats.copy()
        row = {**replay._task(task), "execution": "SCORED"}
        same(data.read(f"task_{index:03}.json"), row, "raw scorer/task disagreement")
        rows.append(row)
        render = task["id"].split("/")[-2] if task["panel"] == "reachout" else "TASK"
        length = len(replay.measured["initial/" + task["id"]]["token_ids"])
        render_lengths[task["id"]] = length
        try:
            (core.parse_route if task["panel"] == "delayed" else core.parse_probe)(row["raw"])
            invalid = 0
        except ValueError:
            invalid = 1
        counts = Counter(tasks=1, correct=int(row["success"]), invalid_final_syntax=invalid, invalid_read=int(row["invalid_read"]), usable_false_rows=int(row["usable_false_row"]), served_reads=len(row["reads"]), returned_tokens=row["returned_tokens"], initial_prompt_tokens=length)
        counts.update({key: replay.stats[key] - before[key] for key in replay.stats})
        counts["tasks_with_truncation"] = int(counts["truncated_calls"] > 0)
        for key in ("all", "root/" + row["root"], f"{row['panel']}/{row['projection']}", f"{row['panel']}/{row['projection']}/{render}", f"{row['root']}/{row['panel']}/{row['projection']}/{render}"):
            groups[key].update(counts)
    same(report["results"], rows, "report task ordering/scores")
    panels = driver._panels(rows)
    same(report["panels"], panels, "panel audit")
    same(report["thresholds_passed"], all(panel["passed"] for panel in panels.values()), "threshold audit")
    same([report["actor_attempts"], report["actor_responses"]], [replay.calls, replay.calls], "call totals")
    for identifier, length in render_lengths.items():
        if "/RA/" in identifier:
            same(length - render_lengths[identifier.replace("/RA/", "/RB/")], 1, "declared RA/RB length difference")
    close, load = data.read("actor/close.json"), data.read("actor/load.json")
    same(close, report["backend_close"], "close receipt")
    same([close[key] for key in ("kind", "error_type", "failed", "budget_exceeded", "calls_consumed", "token_count_calls")], ["NATIVE", None, False, False, replay.calls, replay.counts], "close completion")
    same([load[key] for key in ("kind", "mount", "lora_request")], ["NATIVE", "C0", None], "load identity")
    for value in (load["operation_started"], load["model_load_started"], load["ready_at"], close["elapsed_actor_seconds"]):
        native.number(value)
    require(report["started_monotonic"] <= load["operation_started"] <= load["model_load_started"] <= load["ready_at"] <= report["started_monotonic"] + report["wall_seconds_through_close"] and replay.stats["actor_call_operation_wall_seconds"] <= close["elapsed_actor_seconds"] <= report["wall_seconds_through_close"], "load/actor elapsed")
    expected = replay.used | {f"task_{index:03}.json" for index in range(800)} | {"manifest.json", "report.json", "actor/config.json", "actor/identity.json", "actor/load.json", "actor/close.json"}
    same(sorted(data.inventory), sorted(expected), "extra/missing task or actor files")
    for archive in (data, outer):
        same(archive.snapshot(), archive.inventory, "archive changed during audit")
    return {
        "schema": driver.SCHEMA + "/independent_analysis_v1", "evidence_audit": "COMPLETE_MATCH",
        "thresholds_passed": report["thresholds_passed"], "panels": panels, "counts": dict(groups),
        "fixed_scope": {"tasks": 800, "delayed": 640, "reachout": 160, "excluded_roots": 4,
                        "conditional_call_cap": 1952, "fits": 0, "updates": 0, "parents": 0,
                        "base": native.MODEL_NAME, "revision": native.REVISION,
                        "material_origin": manifest["plan"]["material_origin"]},
        "initial_prompt_lengths": render_lengths, "manifest_file_sha256": manifest_sha256,
        "collection_file_sha256": collection_sha256, "report_sha256": report["sha256"],
        "analyzer_sha256": driver._file_hash(__file__), "replay_source_sha256": pinned,
        "elapsed_costs_not_gpu_active": {
            "generation_wall_seconds": replay.stats["generation_wall_seconds"],
            "actor_call_operation_wall_seconds": replay.stats["actor_call_operation_wall_seconds"],
            "actor_operations_wall_seconds": close["elapsed_actor_seconds"],
            "cold_model_load_wall_seconds": load["ready_at"] - load["model_load_started"],
            "diagnostic_wall_seconds_through_close": report["wall_seconds_through_close"],
            "diagnostic_wall_seconds_through_release": receipt["elapsed_seconds_from_start"],
            "outer_entry_through_finalization_wall_seconds": collection["outer_elapsed_seconds"]},
        "reservation_visibility": {key: collection[key] for key in
                                   ("reservation_check_status", "complete_cvd_visibility", "approved_unreadable_service_pids")},
        "scope": LIMITS}


def write_analysis(result, output_dir):
    """Create a fresh directory, never replace evidence or an earlier analysis."""
    output = Path(output_dir)
    output.mkdir(parents=False, exist_ok=False)
    lines = ["# Independent C0 archive audit", "", LIMITS, "", f"Evidence: {result['evidence_audit']}; declared thresholds passed: {result['thresholds_passed']}.", "", "| Panel | Correct/fixed denominator | Declared interval | Passed |", "|---|---:|---:|---|"]
    for name, panel in result["panels"].items():
        lines.append(f"| {name} | {panel['correct']}/{panel['denominator']} | {panel['minimum']}..{panel['maximum']} | {panel['passed']} |")
    lines.extend(["", "## Root / projection / render counts", "", "| Stratum | Tasks | Correct | Invalid syntax / READ | Truncated calls / tasks | Served READs | Prompt / output / returned tokens |", "|---|---:|---:|---:|---:|---:|---:|"])
    for name, counts in sorted(result.get("counts", {}).items()):
        lines.append(f"| {name} | {counts['tasks']} | {counts['correct']} | {counts['invalid_final_syntax']}/{counts['invalid_read']} | {counts['truncated_calls']}/{counts['tasks_with_truncation']} | {counts['served_reads']} | {counts['prompt_tokens']}/{counts['output_tokens']}/{counts['returned_tokens']} |")
    lines.extend(["", "All per-task initial lengths and additional usage counters are preserved in analysis.json.", "", "## Elapsed costs (not GPU-active) and lineage", "", "```json", json.dumps({key: value for key, value in result.items() if key not in ("panels", "counts", "initial_prompt_lengths")}, sort_keys=True, indent=2), "```", ""])
    with (output / "analysis.json").open("xb") as stream:
        stream.write(canonical(result) + b"\n")
    with (output / "analysis.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("diagnostic", "outer", "manifest-sha256", "collection-sha256", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    for archive in (args.diagnostic, args.outer):
        require(Path(archive).resolve() not in Path(args.output).resolve().parents, "analysis must be outside archives")
    result = analyze(args.diagnostic, args.outer, manifest_sha256=args.manifest_sha256, collection_sha256=args.collection_sha256)
    write_analysis(result, args.output)


if __name__ == "__main__":
    main()
