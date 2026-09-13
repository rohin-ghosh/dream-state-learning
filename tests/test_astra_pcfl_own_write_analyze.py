"""Injected SYNTHETIC archives only: no model, GPU, real fit or native outcomes.

Full roster fixtures contain tiny strings/tokens and fabricated numerical/state
receipts. Literal native labels exercise schema validation, not native origin.
"""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gpu import astra_pcfl_own_write_analyze as analyze
from test_pcfl_own_write_train import synthetic_fixture

command, own, core = analyze.command, analyze.own, analyze.core


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(command.canonical(value) + b"\n")


def seal(value):
    return command.formation_api.seal({key: item for key, item in value.items() if key != "sha256"})


def inventory(root):
    return {str(path.relative_to(root)): {"sha256": command.file_hash(path), "size": path.stat().st_size}
            for path in sorted(root.rglob("*")) if path.is_file()}


def fixture(root):
    args, tokenizer = synthetic_fixture(root)
    formation = command.formation_api
    origin, archive = root / "NEVER_CREATED_LIVE_ROOT", root / "SYNTHETIC_ARCHIVE"
    archive.mkdir()
    settings = {**args["config"]["actor_config"], "source_files": command.source_files(),
                "output_dir": str(origin / "formation/actor")}
    plan = args["config"]["planner"]
    config = formation.build_config(core.from_data(plan["cell"]), plan["actions"], plan["link_choices"],
        actor_config=settings, seed=args["config"]["seed"], limits=args["config"]["limits"])
    identity = copy.deepcopy(args["native_receipts"]["identity"])
    identity["config_sha256"] = command.digest(settings)
    identity["identity"]["source_files"] = settings["source_files"]

    def acquire(index, request, limits):
        attempt = copy.deepcopy(args["report"]["slots"][index]["attempt"])
        if attempt["request"] != request or attempt["limits"] != limits:
            raise AssertionError("SYNTHETIC request drift")
        for name, value in (("config.json", settings), ("identity.json", identity)):
            attempt["capture"]["files"][name] = {"utf8": command.canonical(value).decode(), "sha256": command.digest(value)}
        return attempt

    report = formation._form(config, acquire)
    lifecycle = {**args["native_receipts"], "config": settings, "identity": identity}
    fitted = own.build_fit(config, config["sha256"], report, report["sha256"], args["schedule"],
                          args["schedule_sha256"], args["binding"], lifecycle)
    roster = command._roster(plan)
    measurements = [{"text": "SYNTHETIC unused formation surface", "token_ids": [2]} for _ in range(40)]
    for row in roster:
        text = tokenizer.apply_chat_template(analyze.readout.public_messages(row), tokenize=False, add_generation_prompt=True)
        measurements.append({"text": text, "token_ids": tokenizer.encode(text)})
    write(archive / "measurements.json", seal({"measurements": measurements}))
    spec = {"expires_monotonic": 100000, "gpu_uuid": settings["gpu_uuid"],
            "shutdown_binding": {"path": "/SYNTHETIC/shutdown", "sha256": "e" * 64}}
    write(archive / "spec.json", spec)
    manifest = seal({"schema": command.SCHEMA + "/manifest", "kind": "OFFLINE_PREPARATION", "root": str(origin),
        "spec": spec, "spec_input": {"path": "/SYNTHETIC/spec", "sha256": command.file_hash(archive / "spec.json")},
        "sources": command.source_files(), "formation_template": config, "binding": args["binding"],
        "schedule": args["schedule"], "roster": roster, "roster_sha256": command.digest(roster),
        "stage_seconds": command.STAGE_SECONDS,
        "input_files": {name: command.file_hash(archive / name) for name in ("spec.json", "measurements.json")}})
    write(archive / "manifest.json", manifest)
    write(archive / "formation/formation_config.json", config)
    write(archive / "formation/records/config.json", config)
    write(archive / "formation/records/formation.json", report)
    for index, slot in enumerate(report["slots"]):
        attempt = slot["attempt"]
        write(archive / f"formation/records/call_{index:02}.attempt.json", attempt)
        write(archive / f"formation/records/call_{index:02}.request.json", {key: attempt[key] for key in ("request", "limits")})
        for name, record in attempt["capture"]["files"].items():
            path = archive / "formation/actor" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(record["utf8"].encode())
    for name in ("load", "close"):
        write(archive / f"formation/actor/{name}.json", lifecycle[name])
    write(archive / "formation/actor_close.json", lifecycle["close"])
    write(archive / "formation/shutdown.json", {"shutdown_returned": True})
    queries = report["writer_payload"]["queries"]
    write(archive / "formation/exact_child_service.json", {"kind": "DETERMINISTIC_SERVICE_NOT_MODEL", "calls": 0,
          "items": [core.read_query(queries, request) for request in sorted(queries)]})
    encoded = own.encode_fit(fitted, tokenizer)
    write(archive / "fit/write/fit.json", fitted)
    write(archive / "fit/write/encoding.json", encoded)
    initial, final = {"lora": "1" * 64, "optimizer": "2" * 64}, {"lora": "3" * 64, "optimizer": "4" * 64}
    write(archive / "fit/write/initial.json", initial)
    lookup = {(item["slot"], item["view"]): item for item in encoded["items"]}
    updates = []
    for epoch, batches in enumerate(encoded["epochs"]):
        for batch, items in enumerate(batches):
            updates.append({"update": len(updates) + 1, "epoch": epoch, "batch": batch, "items": items,
                "source_sha256": [lookup[tuple(pair)]["source_sha256"] for pair in items],
                "loss": 1., "pre_clip_norm": .5, "post_clip_norm": .5})
    (archive / "fit/write/updates.jsonl").write_bytes(b"".join(command.canonical(item) + b"\n" for item in updates))
    write(archive / "fit/write/adapter/adapter_config.json", {"r": 8, "lora_alpha": 16, "lora_dropout": .05, "peft_type": "LORA"})
    (archive / "fit/write/adapter/adapter_model.safetensors").write_bytes(b"SYNTHETIC NOT TENSORS")
    writer_receipt = {"status": "COMPLETE", "fit_sha256": fitted["sha256"], "encoding_sha256": encoded["sha256"],
        "updates": 200, "presentations": 800, "training_forwards": 800, "initial": initial, "final": final,
        "objective": own.writer.OBJECTIVE, "layout": own.writer.LAYOUT,
        "files": {name: item["sha256"] for name, item in inventory(archive / "fit/write").items()}}
    write(archive / "fit/write/completed.json", writer_receipt)
    adapter = {"name": "pcfl-own-write", "id": 1, "path": str(origin / "fit/write/adapter"),
               "files": inventory(archive / "fit/write/adapter")}
    write(archive / "fit/adapter.json", adapter)
    for arm in analyze.readout.ARMS:
        start = 210 if arm == "NO_WRITE_C0" else 510
        directory = archive / ("readout_" + arm)
        mounted = adapter if arm == "AUTH_WRITE" else None
        config = command._readout_config(manifest, arm, mounted, origin / ("readout_" + arm) / "actor", start + 1800)
        write(directory / "readout_config.json", config)
        write(directory / "actor/config.json", config)
        route = analyze.readout.route_identity(config)
        base = {key: value for key, value in identity["identity"].items() if key not in ("mount", "lora_request")}
        witness = {"base_identity": base, "route": route, "engine": config["engine"], "adapter": mounted,
                   "roster_sha256": manifest["roster_sha256"], "shutdown_binding": spec["shutdown_binding"]}
        write(directory / "actor/identity.json", {"kind": "NATIVE_OWN_WRITE_READOUT", "pid": 17,
              "config_sha256": command.digest(config), "identity": witness})
        write(directory / "actor/load.json", {"kind": "NATIVE_OWN_WRITE_READOUT", "route": route,
              "engine": config["engine"], "model_load_started": start, "ready_at": start + 1})
        scores = []
        for index, row in enumerate(roster):
            target = queries[row["request"]]["target"]
            text = target if (arm == "AUTH_WRITE" and index // 9 < 15) or (arm == "NO_WRITE_C0" and index // 9 < 2) else "MISS"
            if row["view"] == 1 and text == target:
                text = target[:-1]
            raw = {"text": text, "output_token_ids": tokenizer.encode(text), "prompt_token_ids": measurements[40 + index]["token_ids"],
                   "finish_reason": "stop", "stop_reason": None, "route": route}
            prefix = directory / "actor" / f"call_{index:04}"
            write(Path(str(prefix) + ".request.json"), {"request": {"id": row["id"]}, "row": row,
                  "messages": analyze.readout.public_messages(row), "roster_sha256": manifest["roster_sha256"], "route": route})
            write(Path(str(prefix) + ".render.json"), {"rendered_prompt": measurements[40 + index]["text"], "prompt_token_ids": raw["prompt_token_ids"],
                  "sampling": {**analyze.native.SAMPLING, "seed": row["seed"], "max_tokens": row["output_tokens"]}, "route": route})
            write(Path(str(prefix) + ".raw.json"), {"kind": "NATIVE_OWN_WRITE_READOUT", "route": route, "raw": raw,
                  "generation_started": start + 2 + index, "generation_ended": start + 2.25 + index})
            response = {"id": row["id"], "request_sha256": command.digest({"id": row["id"]}), "roster_sha256": manifest["roster_sha256"],
                        "route": route, "text": text, "prompt_tokens": len(raw["prompt_token_ids"]), "output_tokens": len(raw["output_token_ids"]),
                        "finish_reason": "stop", "stop_reason": None, "truncated": False, "device_seconds": .5}
            write(Path(str(prefix) + ".response.json"), {"response": response, "raw_utf8_sha256": analyze.native.text_hash(text), "raw_hex": text.encode().hex()})
            write(directory / (row["id"].replace("/", "_") + ".json"), response)
            score = core.score_memory_response(text, target)
            scores.append({"id": row["id"], "request": row["request"], "view": row["view"], "raw": text, "finish_reason": "stop",
                           "score": score, "strict_stop": score["strict"], "semantic_stop": score["semantic"]})
        close = {"kind": "NATIVE_OWN_WRITE_READOUT", "route": route, "failed": False, "error_type": None, "budget_exceeded": False,
                 "calls_consumed": 153, "planned_calls": 153, "elapsed_actor_seconds": 80., "shutdown": {"shutdown_returned": True}}
        write(directory / "actor/close.json", close)
        write(directory / "actor_close.json", close)
        write(directory / "scores.json", {"arm": arm, "roster_sha256": manifest["roster_sha256"], "denominator": 153, "results": scores})
    pins = {}
    for name, started, ended in (("formation", 0, 100), ("fit", 100, 200), ("readout_NO_WRITE_C0", 210, 500), ("readout_AUTH_WRITE", 510, 800)):
        directory = archive / name
        write(directory / "entry.json", {"manifest_file_sha256": command.file_hash(archive / "manifest.json"), "stage": name, "started": started, "kind": "NATIVE"})
        calls, fits, count = (20, 0, 0) if name == "formation" else (0, 1, 200) if name == "fit" else (153, 0, 0)
        completed = {"schema": command.SCHEMA + "/completed", "status": "COMPLETE", "manifest_sha256": manifest["sha256"],
            "stage": name, "started": started, "ended": ended, "elapsed_seconds": ended - started, "outer_release_required": True,
            "gpu_released": False, "calls": calls, "fits": fits, "updates": count,
            "files": {filename: value["sha256"] for filename, value in inventory(directory).items()}}
        if name == "formation":
            completed["report_sha256"] = report["sha256"]
        if name == "fit":
            completed["writer_receipt_sha256"] = command.digest(writer_receipt)
        write(directory / "completed.json", seal(completed))
        pins[name] = {"completed_sha256": command.file_hash(directory / "completed.json"),
                      "outer_path": str(root / ("SYNTHETIC_OUTER_" + name))}
        make_outer(archive, manifest, name, pins[name])
    return archive, manifest, pins


def make_outer(archive, manifest, name, pin):
    root = Path(pin["outer_path"])
    write(root / "manifest.input.json", manifest)
    write(root / "stage_completed.json", command.read(archive / name / "completed.json"))
    identity = {"pid": 17, "start_ticks": 123, "kind": "SYNTHETIC_ONLY"}
    observations = {"worker_release": {"identity": identity, "owned_group_released": True}}
    for phase in ("pre", "post"):
        observations.update({phase + "_queue": {"matched": True}, phase + "_gpu": {"empty": True, "gpu_uuid": manifest["spec"]["gpu_uuid"]},
                             phase + "_cvd": {"clear": True, "owners": [], "unresolved": []}})
    for key, value in observations.items():
        write(root / (key + ".json"), {"value": value})
    write(root / "worker_exit.json", {"returncode": 0, "identity": identity})
    write(root / "worker_start.json", {"identity": identity})
    write(root / "allocation.input.json", {"gpu_uuid": manifest["spec"]["gpu_uuid"]})
    stage, arm = ("readout", name[len("readout_"):]) if name.startswith("readout_") else (name, None)
    write(root / "context.json", {"schema": analyze.outer.SCHEMA, "stage": stage, "arm": arm,
        "manifest_file_sha256": command.file_hash(archive / "manifest.json"),
        "allocation_file_sha256": command.file_hash(root / "allocation.input.json"),
        "outer_source_sha256": command.file_hash(analyze.outer.__file__)})
    write(root / "binding.json", {"stage_dir": str(Path(manifest["root"]) / name),
                                 "helper_sha256": command.file_hash(analyze.outer.lifecycle.__file__)})
    collection = {"schema": analyze.outer.SCHEMA + "/collection", "status": "COMPLETED", "stage": "readout" if name.startswith("readout_") else name,
                  "arm": name[len("readout_"):] if name.startswith("readout_") else None, "errors": [], "returncode": 0, "generation_retries": 0,
                  "manifest_file_sha256": command.file_hash(archive / "manifest.json"), "outer_source_sha256": command.file_hash(analyze.outer.__file__),
                  "allocation_file_sha256": command.file_hash(root / "allocation.input.json"),
                  "stage_completed_file_sha256": pin["completed_sha256"], "stage_inventory": inventory(archive / name),
                  "worker_identity": identity, "observations": observations, "elapsed_seconds": 320,
                  "files": {key: value for key, value in inventory(root).items() if key != "collection.json"}}
    write(root / "collection.json", collection)
    pin["collection_sha256"] = command.file_hash(root / "collection.json")


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_REDUCER_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.archive, self.manifest, self.pins = fixture(self.root)
        self.manifest_hash = command.file_hash(self.archive / "manifest.json")

    def run_analysis(self):
        return analyze.analyze(self.archive, self.manifest_hash, self.pins)

    def repin_stage(self, name):
        path = self.archive / name / "completed.json"
        receipt = command.read(path)
        receipt["files"] = {key: value["sha256"] for key, value in inventory(path.parent).items() if key != "completed.json"}
        write(path, seal(receipt))
        self.pins[name]["completed_sha256"] = command.file_hash(path)
        make_outer(self.archive, self.manifest, name, self.pins[name])

    def test_full_synthetic_archive_endpoint_and_costs(self):
        with patch.object(command, "_model", side_effect=AssertionError("no model")), patch.object(command, "_tokenizer", side_effect=AssertionError("no tokenizer")):
            result = self.run_analysis()
        self.assertEqual(result["endpoint"]["label"], "SCOPED_OWN_WRITE_ACQUISITION_PASS")
        self.assertEqual((result["endpoint"]["AUTH_strict_stop"], result["endpoint"]["C0_strict_stop"], result["endpoint"]["paired_difference"]), (15, 2, 13))
        self.assertEqual(result["label"], "FORMAT_SCAFFOLDED_DESCRIPTIVE_ONLY")
        self.assertTrue(result["external_format_assistance"])
        self.assertEqual(result["link_pair_policy"], "requested_preselected_already_admitted_event_handles_v1")
        self.assertIn("Controlled curriculum record task", result["claim_boundary"])
        self.assertIn("no autonomy or discovery", result["limits"])
        self.assertEqual(result["strata"]["W8"]["denominator"], 17)
        self.assertEqual(result["strata"]["W1"]["AUTH_WRITE/exact_stop"], 0)
        self.assertEqual(result["strata"]["W1"]["AUTH_WRITE/semantic_stop"], 15)
        self.assertEqual(result["fit"]["updates"], 200)
        self.assertEqual(result["costs_not_gpu_active"]["AUTH_WRITE"]["generation_wall_seconds_sum"], 38.25)
        self.assertEqual(len(result["authentic_child_rows"]), 12)
        self.assertIn("not compute-matched", analyze.markdown(result))

    def test_missing_arm_and_pin_reject(self):
        del self.pins["readout_AUTH_WRITE"]
        with self.assertRaises(ValueError):
            self.run_analysis()

    def test_raw_bytes_tamper_reject_even_with_resealed_inventory(self):
        path = self.archive / "readout_AUTH_WRITE/actor/call_0000.raw.json"
        raw = command.read(path)
        raw["raw"]["text"] += " "
        write(path, raw)
        self.repin_stage("readout_AUTH_WRITE")
        with self.assertRaisesRegex(ValueError, "response bytes/tokens"):
            self.run_analysis()

    def test_score_tamper_reject(self):
        path = self.archive / "readout_AUTH_WRITE/scores.json"
        scores = command.read(path)
        scores["results"][0]["strict_stop"] = False
        write(path, scores)
        self.repin_stage("readout_AUTH_WRITE")
        with self.assertRaisesRegex(ValueError, "raw scorer"):
            self.run_analysis()

    def test_missing_completion_no_zero_fill(self):
        (self.archive / "readout_NO_WRITE_C0/completed.json").unlink()
        with self.assertRaises(KeyError):
            self.run_analysis()

    def test_failed_outer_reject(self):
        pin = self.pins["readout_AUTH_WRITE"]
        path = Path(pin["outer_path"]) / "collection.json"
        receipt = command.read(path)
        receipt["status"] = "FAILED"
        write(path, receipt)
        pin["collection_sha256"] = command.file_hash(path)
        with self.assertRaisesRegex(ValueError, "outer completion"):
            self.run_analysis()

    def test_checkpoint_tamper_reject(self):
        (self.archive / "fit/write/adapter/adapter_model.safetensors").write_bytes(b"CHANGED")
        with self.assertRaisesRegex(ValueError, "stage inventory"):
            self.run_analysis()

    def test_short_update_log_reject_after_repin(self):
        path = self.archive / "fit/write/updates.jsonl"
        path.write_bytes(b"\n".join(path.read_bytes().splitlines()[:-1]) + b"\n")
        receipt_path = self.archive / "fit/write/completed.json"
        receipt = command.read(receipt_path)
        receipt["files"]["updates.jsonl"] = command.file_hash(path)
        write(receipt_path, receipt)
        stage_path = self.archive / "fit/completed.json"
        stage = command.read(stage_path)
        stage["writer_receipt_sha256"] = command.digest(receipt)
        write(stage_path, seal(stage))
        self.repin_stage("fit")
        with self.assertRaisesRegex(ValueError, "200 recorded updates"):
            self.run_analysis()

    def test_cli_fresh_only(self):
        path, output = self.root / "pins.json", self.root / "analysis"
        write(path, self.pins)
        argv = ["--archive", str(self.archive), "--manifest-sha256", self.manifest_hash,
                "--completion-pins", str(path), "--output", str(output)]
        analyze.main(argv)
        self.assertEqual(command.read(output / "analysis.json")["endpoint"]["denominator"], 17)
        with self.assertRaises(ValueError):
            analyze.main(argv)

    def test_actual_token_count_and_measured_surface_tamper_reject(self):
        path = self.archive / "readout_AUTH_WRITE/actor/call_0000.raw.json"
        raw = command.read(path)
        raw["raw"]["output_token_ids"].append(99)
        write(path, raw)
        self.repin_stage("readout_AUTH_WRITE")
        with self.assertRaisesRegex(ValueError, "response bytes/tokens"):
            self.run_analysis()

    def test_source_pin_drift_reject(self):
        with patch.object(command, "source_files", return_value={}):
            with self.assertRaisesRegex(ValueError, "source snapshot"):
                self.run_analysis()

    def test_utf8_hex_and_normalization_never_repaired(self):
        path = self.archive / "readout_AUTH_WRITE/actor/call_0000.response.json"
        value = command.read(path)
        value["raw_hex"] += "0a"
        write(path, value)
        self.repin_stage("readout_AUTH_WRITE")
        with self.assertRaisesRegex(ValueError, "exact UTF8"):
            self.run_analysis()

    def test_symlink_reject(self):
        (self.archive / "alias").symlink_to(self.archive / "manifest.json")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.run_analysis()

    def test_truncated_exact_string_is_zero_primary_not_missing_evidence(self):
        directory = self.archive / "readout_AUTH_WRITE"
        raw_path, wrapped_path = [directory / f"actor/call_0008.{suffix}.json" for suffix in ("raw", "response")]
        raw, wrapped = command.read(raw_path), command.read(wrapped_path)
        raw["raw"]["finish_reason"] = "length"
        wrapped["response"].update(finish_reason="length", truncated=True)
        write(raw_path, raw)
        write(wrapped_path, wrapped)
        write(directory / "read_00_W8.json", wrapped["response"])
        scores = command.read(directory / "scores.json")
        scores["results"][8].update(finish_reason="length", strict_stop=False, semantic_stop=False)
        write(directory / "scores.json", scores)
        self.repin_stage("readout_AUTH_WRITE")
        result = self.run_analysis()
        self.assertTrue(result["pairs"][8]["arms"]["AUTH_WRITE"]["exact_bytes"])
        self.assertEqual(result["endpoint"]["AUTH_strict_stop"], 14)
        self.assertEqual(result["endpoint"]["label"], "SCOPED_OWN_WRITE_ACQUISITION_FAIL")
        self.assertEqual(result["strata"]["W8"]["AUTH_WRITE/truncated"], 1)

    def test_output_inside_outer_archive_reject(self):
        pins = self.root / "pins.json"
        write(pins, self.pins)
        out = Path(self.pins["formation"]["outer_path"]) / "forbidden"
        with self.assertRaisesRegex(ValueError, "overlaps outer"):
            analyze.main(["--archive", str(self.archive), "--manifest-sha256", self.manifest_hash,
                          "--completion-pins", str(pins), "--output", str(out)])
        self.assertFalse(out.exists())

    def test_failed_stage_reject_after_repin(self):
        write(self.archive / "fit/failure.json", {"error": "SYNTHETIC preserved failure"})
        self.repin_stage("fit")
        with self.assertRaisesRegex(ValueError, "failed stage evidence"):
            self.run_analysis()

    def test_deterministic_service_target_tamper_reject(self):
        path = self.archive / "formation/exact_child_service.json"
        service = command.read(path)
        service["items"][0]["raw"] += " "
        write(path, service)
        self.repin_stage("formation")
        with self.assertRaisesRegex(ValueError, "authentic deterministic service"):
            self.run_analysis()


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.pairs, items = [], []
        kinds = ["EVENT"] * 8 + ["EVENTS_AT"] * 6 + ["LINKS_FROM"] * 3
        for index, kind in enumerate(kinds):
            request = f"SYNTHETIC_ADDRESS_{index}"
            items.append({"request": request, "raw": f"SYNTHETIC_TARGET_{index}\n"})
            for view in range(9):
                self.pairs.append({"id": f"read/{index:02}/W{view}", "request": request, "view": view, "query_kind": kind,
                    "target": items[-1]["raw"], "arms": {arm: {"exact_stop": index < (15 if arm == "AUTH_WRITE" else 2),
                    "semantic_stop": True, "semantic": True} for arm in analyze.readout.ARMS}})
        self.service = {"items": items}

    def result(self):
        return analyze.endpoints(self.pairs, self.service)

    def test_exact_threshold_boundary_and_ordered_kind_vectors(self):
        result = self.result()
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["ordered_vectors"]["W8"]["arms"]["AUTH_WRITE"]["strict_stop"], [1] * 15 + [0] * 2)
        self.assertEqual([len(result["W8_by_query_kind"][kind]["addresses"]) for kind in ("EVENT", "EVENTS_AT", "LINKS_FROM")], [8, 6, 3])

    def test_AUTH14_fails_despite_semantic_and_training_surfaces(self):
        for pair in self.pairs:
            if pair["view"] == 8 and pair["request"] == "SYNTHETIC_ADDRESS_14":
                pair["arms"]["AUTH_WRITE"]["exact_stop"] = False
        self.assertEqual(self.result()["label"], "SCOPED_OWN_WRITE_ACQUISITION_FAIL")
        self.assertFalse(self.result()["checks"]["AUTH_at_least_15"])

    def test_C0_three_fails_and_difference12_fails(self):
        for pair in self.pairs:
            if pair["view"] == 8 and pair["request"] == "SYNTHETIC_ADDRESS_2":
                pair["arms"]["NO_WRITE_C0"]["exact_stop"] = True
        checks = self.result()["checks"]
        self.assertFalse(checks["C0_at_most_2"])
        self.assertFalse(checks["paired_difference_at_least_13"])

    def test_service_mismatch_fails_without_normalization(self):
        self.service["items"][0]["raw"] = self.service["items"][0]["raw"].rstrip()
        self.assertFalse(self.result()["checks"]["service_17_of_17"])

    def test_missing_response_and_wrong_kind_denominator_reject(self):
        self.pairs.pop()
        with self.assertRaises(ValueError):
            self.result()

    def test_wrong_kind_denominator_reject(self):
        self.pairs[8]["query_kind"] = "LINKS_FROM"
        with self.assertRaisesRegex(ValueError, "query-kind denominator"):
            self.result()


if __name__ == "__main__":
    unittest.main()
