"""Synthetic complete archives: no model, native collection or readout outcomes.

Native/COMPLETE labels, tensors, tokens and lifecycle receipts below are explicit
CPU schema fixtures, not genuine qualification. Only the original prefix is real.
"""

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gpu import astra_pcfl_event_only_analyze as analyze
from test_astra_pcfl_event_prefix_import import archived_fixture, reseal
from test_pcfl_event_only_train import SyntheticTokenizer

command, event, prefix = analyze.command, analyze.event, analyze.prefix


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(analyze.canonical(value) + b"\n")


def inventory(root):
    return analyze.Archive(root).inventory


def outer_fixture(archive, manifest, name, pin, index):
    root = Path(pin["outer_path"])
    completed = command.read(archive / name / "completed.json")
    entry = completed["started"] - 1
    worker_deadline = entry + 1740
    identity = {"pid": 1000 + index, "pgid": 1000 + index, "sid": 1000 + index,
                "start_ticks": 5000 + index, "boot_id": "SYNTHETIC_BOOT", "uid": 1000}
    allocation = {"gpu_uuid": manifest["spec"]["gpu_uuid"], "boot_id": "SYNTHETIC_BOOT", "uid": 1000}
    write(root / "allocation.input.json", allocation)
    write(root / "manifest.input.json", manifest)
    write(root / "stage_completed.json", completed)
    stage, arm = ("readout", name[len("readout_"):]) if name.startswith("readout_") else (name, None)
    manifest_hash = command.file_hash(archive / "manifest.json")
    context = {"schema": analyze.outer.SCHEMA, "stage": stage, "arm": arm, "manifest_file_sha256": manifest_hash,
               "allocation_file_sha256": command.file_hash(root / "allocation.input.json"),
               "outer_source_sha256": command.file_hash(analyze.outer.__file__), "entry_monotonic": entry}
    write(root / "context.json", context)
    write(root / "binding.json", {"stage_dir": str(Path(manifest["root"]) / name),
          "helper_sha256": command.file_hash(analyze.outer.lifecycle.__file__),
          "deadline_monotonic": worker_deadline + 60, "worker_deadline_monotonic": worker_deadline})
    write(root / "worker_start.json", {"identity": identity, "spawn_started_monotonic": entry + .5})
    write(root / "worker_exit.json", {"identity": identity, "returncode": 0, "signal": None, "ended_monotonic": completed["ended"] + .5})
    observations = {"worker_wait": 0, "worker_release": {"identity": identity, "owned_group_released": True}}
    for phase in ("pre", "post"):
        observations[phase + "_queue"] = {"matched": True, "mode": "SYNTHETIC"}
        observations[phase + "_gpu"] = {"empty": True, "gpu_uuid": allocation["gpu_uuid"]}
        observations[phase + "_cvd"] = {"clear": True, "owners": [], "unresolved": [],
                                       "complete_cvd_visibility": False, "approved_unreadable_services": ["SYNTHETIC_METADATA_ONLY"]}
    for key, value in observations.items():
        started = entry + .1 if key.startswith("pre_") else completed["ended"] + .1 if key.startswith("worker_") else completed["ended"] + .3
        write(root / (key + ".json"), {"value": value, "started_monotonic": started, "ended_monotonic": started + .1})
    collection = {"schema": analyze.outer.SCHEMA + "/collection", "status": "COMPLETED", "stage": stage, "arm": arm,
        "manifest_file_sha256": manifest_hash, "allocation_file_sha256": context["allocation_file_sha256"],
        "outer_source_sha256": context["outer_source_sha256"], "errors": [], "returncode": 0, "generation_retries": 0,
        "worker_identity": identity, "observations": observations, "stage_completed_file_sha256": pin["completed_sha256"],
        "stage_inventory": inventory(archive / name), "elapsed_seconds": completed["ended"] + 1 - entry,
        "files": {key: value for key, value in inventory(root).items() if key != "collection.json"}}
    write(root / "collection.json", collection)
    pin["collection_sha256"] = command.file_hash(root / "collection.json")


def fixture(root):
    archive = root / "SYNTHETIC_ARCHIVE"
    archive.mkdir()
    original_root = root / "NEVER_CREATED_NATIVE_ROOT"
    evidence, replay, imported = archived_fixture()
    original = prefix._json(evidence["files"]["manifest.json"])["binding"]
    schedule = event.build_schedule(imported, imported["sha256"])
    binding = {key: copy.deepcopy(original[key]) for key in event.BINDING_FIELDS - {"authority_sha256", "sources"}}
    binding.update(authority_sha256=command.file_hash(command.SCOPE), sources=event.source_snapshot())
    fitted = event.build_fit(imported, imported["sha256"], schedule, schedule["sha256"], binding)
    tokenizer = SyntheticTokenizer()
    encoded = event.writer._encode_corpus(fitted["sha256"], schedule["corpus"], schedule["epochs"], imported["queries"],
        event.core.registries()["render_registry"], event.core.byte_hash(tokenizer.chat_template), tokenizer)
    token = prefix.seal({"schema": prefix.SCHEMA + "/tokenizer", "import_sha256": imported["sha256"], "status": "EVENT_PREFIX_TOKENIZER_VERIFIED",
        "calls_checked": 16, "model_calls": 0, "tokenizer_files": binding["tokenizer_receipt"]["files"],
        "chat_template_sha256": binding["tokenizer_receipt"]["chat_template_sha256"], "full_contract_released": False})
    spec = {"source_files": command.source_files(), "authority": {"path": str(command.SCOPE), "sha256": command.file_hash(command.SCOPE)},
            "gpu_uuid": "GPU-SYNTHETIC", "boot_id": "SYNTHETIC_BOOT", "expires_monotonic": 10000,
            "shutdown_binding": {"path": "/SYNTHETIC/shutdown.py", "sha256": "a" * 64}}
    settings = copy.deepcopy(prefix._json(evidence["files"]["formation/actor/config.json"]))
    spec.update(model_path=settings["model_path"], model_binding=settings["model_binding"], environment=binding["environment"]["runtime"],
        archive={"path": "/SYNTHETIC/original.tar", "sha256": prefix.ARCHIVE_SHA256},
        replay_receipt={"path": "/SYNTHETIC/replay.json", "sha256": "7" * 64},
        base_state_receipt={"path": "/SYNTHETIC/base.json", "sha256": "8" * 64})
    actor_sources = dict(spec["source_files"])
    for key in ("archive", "replay_receipt", "base_state_receipt", "authority", "shutdown_binding"):
        actor_sources[spec[key]["path"]] = spec[key]["sha256"]
    settings.update(source_files=actor_sources, gpu_uuid=spec["gpu_uuid"], max_calls=28)
    roster = event.read_roster(imported)
    prepared = {"spec.json": spec, "import.json": imported, "fit.json": fitted, "tokenizer.json": token,
                "encoding.json": encoded, "identity.json": {"repository": analyze.native.MODEL_NAME, "revision": analyze.native.REVISION,
                    "model_files": binding["environment"]["model_files"], "model_binding_sha256": settings["model_binding"]["sha256"],
                    "environment": settings["environment"], "gpu_uuid_expected": settings["gpu_uuid"], "clean_lineage_certified": False,
                    "source_files": settings["source_files"], "mount": "C0", "lora_request": None}}
    measured = []
    for row in roster:
        text = tokenizer.apply_chat_template(analyze.readout.public_messages(row), tokenize=False, add_generation_prompt=True)
        measured.append({"id": row["id"], "prompt_sha256": analyze.native.text_hash(text), "input_tokens": len(tokenizer.encode(text))})
    prepared["read_measurements.json"] = measured
    prepared["service.json"] = {"kind": "DETERMINISTIC_SERVICE_NOT_MODEL", "calls": 0, "denominator": 14, "exact": 14,
        "results": [{"request": request, "response": event.core.read_query(imported["queries"], request)} for request in sorted(imported["queries"])]}
    for name, value in prepared.items():
        write(archive / name, value)
    manifest = prefix.seal({"schema": command.SCHEMA + "/manifest", "kind": "OFFLINE_PREPARATION", "root": str(original_root),
        "spec": spec, "sources": spec["source_files"], "spec_file_sha256": command.file_hash(archive / "spec.json"),
        "input_files": {name: command.file_hash(archive / name) for name in prepared}, "import_sha256": imported["sha256"],
        "fit_sha256": fitted["sha256"], "encoding_sha256": encoded["sha256"], "tokenizer_sha256": token["sha256"],
        "roster": roster, "roster_sha256": analyze.digest(roster), "actor_template": settings,
        "total_seconds": 1800, "cleanup_seconds": 60, "endpoint": event.ENDPOINT, "full_contract_released": False,
        "original_status": "FORMATION_FAILED", "original_returncode": 1})
    write(archive / "manifest.json", manifest)
    initial, final = {"lora": "1" * 64, "optimizer": "2" * 64}, {"lora": "3" * 64, "optimizer": "4" * 64}
    for name, value in (("fit", fitted), ("encoding", encoded), ("initial", initial), ("event_only_scope_report", event.validate_fit(fitted))):
        write(archive / f"fit/write/{name}.json", value)
    updates, lookup = [], {(item["slot"], item["view"]): item for item in encoded["items"]}
    for epoch, batches in enumerate(encoded["epochs"]):
        for batch, items in enumerate(batches):
            updates.append({"update": len(updates) + 1, "epoch": epoch, "batch": batch, "items": items,
                "source_sha256": [lookup[tuple(pair)]["source_sha256"] for pair in items], "loss": 1., "pre_clip_norm": .5,
                "post_clip_norm": .5, "rng_before": "5" * 64, "rng_after": "6" * 64,
                "supervised_tokens": sum(lookup[tuple(pair)]["encoded"]["n_target"] for pair in items)})
    (archive / "fit/write/updates.jsonl").write_bytes(b"".join(analyze.canonical(row) + b"\n" for row in updates))
    write(archive / "fit/write/adapter/adapter_config.json", {"r": 8, "lora_alpha": 16, "lora_dropout": .05, "peft_type": "LORA"})
    (archive / "fit/write/adapter/adapter_model.safetensors").write_bytes(b"SYNTHETIC_NOT_TENSORS")
    receipt = {"status": "COMPLETE", "fit_sha256": fitted["sha256"], "encoding_sha256": encoded["sha256"],
        "updates": 200, "presentations": 800, "training_forwards": 800, "initial": initial, "final": final,
        "objective": event.writer.OBJECTIVE, "layout": event.writer.LAYOUT, "native_custody_verified": False,
        "files": {key: value["sha256"] for key, value in inventory(archive / "fit/write").items()}}
    write(archive / "fit/write/completed.json", receipt)
    adapter = {"name": "pcfl-own-write", "id": 1, "path": str(original_root / "fit/write/adapter"), "files": inventory(archive / "fit/write/adapter")}
    write(archive / "fit/adapter.json", adapter)
    for arm in analyze.ARMS:
        stage_index = analyze.STAGES.index("readout_" + arm)
        started = 100.0 + 300 * stage_index
        directory = archive / ("readout_" + arm)
        mounted = adapter if arm == "AUTH_WRITE" else None
        config = command._readout_config(manifest, arm, mounted, original_root / ("readout_" + arm) / "actor", started - 1 + 1740)
        write(directory / "readout_config.json", config)
        write(directory / "actor/config.json", config)
        route = analyze.readout.route_identity(config)
        base = {"repository": analyze.native.MODEL_NAME, "revision": analyze.native.REVISION,
            "model_files": binding["environment"]["model_files"], "model_binding_sha256": config["model_binding"]["sha256"],
            "environment": config["environment"], "gpu_uuid_expected": config["gpu_uuid"], "clean_lineage_certified": False,
            "source_files": config["source_files"]}
        identity = {"kind": "NATIVE_OWN_WRITE_READOUT", "pid": 1000 + stage_index, "config_sha256": analyze.digest(config),
            "identity": {"route": route, "engine": config["engine"], "adapter": mounted, "roster_sha256": manifest["roster_sha256"],
                         "shutdown_binding": config["shutdown_binding"], "base_identity": base}}
        write(directory / "actor/identity.json", identity)
        write(directory / "actor/load.json", {"kind": "NATIVE_OWN_WRITE_READOUT", "route": route, "model_load_started": started + 1, "ready_at": started + 2})
        close = {"kind": "NATIVE_OWN_WRITE_READOUT", "route": route, "failed": False, "error_type": None, "budget_exceeded": False,
            "calls_consumed": 28, "planned_calls": 28, "elapsed_actor_seconds": 40,
            "shutdown": {"shutdown_returned": True, "source": config["shutdown_binding"]}}
        write(directory / "actor/close.json", close)
        write(directory / "actor_close.json", close)
        write(directory / "custody.json", {"kind": "NATIVE_OWN_WRITE_READOUT", "calls": 28, "route": route,
              "identity_sha256": analyze.digest(identity), "outer_release_required": True})
        results = []
        for index, row in enumerate(roster):
            text = imported["queries"][row["request"]]["target"] if (arm == "AUTH_WRITE" and index != 27) or (arm == "NO_WRITE_C0" and index == 14) else "MISS"
            prompt = tokenizer.apply_chat_template(analyze.readout.public_messages(row), tokenize=False, add_generation_prompt=True)
            prompt_ids, output_ids = tokenizer.encode(prompt), tokenizer.encode(text)
            request = {"request": {"id": row["id"]}, "row": row, "messages": analyze.readout.public_messages(row),
                "route": route, "roster_sha256": manifest["roster_sha256"],
                "started": started + .5 if index == 0 else started + 2.75 + index,
                "limits": {"deadline": config["deadline"], "device_seconds": 1740}}
            raw = {"route": route, "text": text, "prompt_token_ids": prompt_ids, "output_token_ids": output_ids, "finish_reason": "stop", "stop_reason": None}
            response = {"id": row["id"], "request_sha256": analyze.digest({"id": row["id"]}), "roster_sha256": manifest["roster_sha256"],
                "route": route, "text": text, "prompt_tokens": len(prompt_ids), "output_tokens": len(output_ids), "finish_reason": "stop",
                "stop_reason": None, "truncated": False, "device_seconds": 3.1 if index == 0 else .9}
            capture = {"kind": "NATIVE_OWN_WRITE_READOUT", "route": route, "raw": raw,
                       "generation_started": started + 3 + index, "generation_ended": started + 3.5 + index}
            values = {"request": request, "render": {"route": route, "rendered_prompt": prompt, "prompt_token_ids": prompt_ids,
                "sampling": {**analyze.native.SAMPLING, "seed": row["seed"], "max_tokens": row["output_tokens"]}}, "raw": capture,
                "response": {"response": response, "raw_hex": text.encode().hex(), "raw_utf8_sha256": analyze.native.text_hash(text)}}
            for suffix, value in values.items():
                write(directory / f"actor/call_{index:04d}.{suffix}.json", value)
            write(directory / (row["id"].replace("/", "_") + ".json"), response)
            score = event.core.score_memory_response(text, imported["queries"][row["request"]]["target"])
            results.append({"id": row["id"], "request": row["request"], "view": row["view"], "raw": text, "finish_reason": "stop",
                            "score": score, "strict_stop": score["strict"], "semantic_stop": score["semantic"]})
        counts = {str(view): {"denominator": 14, "strict_stop": sum(row["strict_stop"] for row in results if row["view"] == view),
                              "semantic_stop": sum(row["semantic_stop"] for row in results if row["view"] == view)} for view in (0, 8)}
        write(directory / "scores.json", {"arm": arm, "denominator": 28, "results": results, "by_view": counts, "endpoint": event.ENDPOINT,
              "paired_endpoint": "REQUIRES_BOTH_RELEASED_ARMS_NOT_INFERRED_HERE"})
    pins = {}
    for index, name in enumerate(analyze.STAGES):
        started = 100.0 + 300 * index
        write(archive / name / "entry.json", {"manifest_file_sha256": command.file_hash(archive / "manifest.json"), "stage": name, "started": started, "kind": "NATIVE"})
        counts = {"calls": 0, "fits": 1, "updates": 200, "writer_receipt_sha256": analyze.digest(receipt)} if name == "fit" else {
            "calls": 28, "fits": 0, "updates": 0, "arm": name[len("readout_"):], "by_view": command.read(archive / name / "scores.json")["by_view"]}
        completed = prefix.seal({"schema": command.SCHEMA + "/completed", "status": "COMPLETE", "manifest_sha256": manifest["sha256"],
            "stage": name, "kind": "NATIVE", "outer_release_required": True, "gpu_released": False, "full_contract_released": False,
            "original_status": "FORMATION_FAILED", "original_returncode": 1, "started": started, "ended": started + 50,
            "elapsed_seconds": (started + 50) - started, "files": {key: value["sha256"] for key, value in inventory(archive / name).items()}, **counts})
        write(archive / name / "completed.json", completed)
        pins[name] = {"completed_sha256": command.file_hash(archive / name / "completed.json"), "outer_path": str(root / ("SYNTHETIC_OUTER_" + name))}
        outer_fixture(archive, manifest, name, pins[name], index)
    return archive, manifest, pins


class EventOnlyAnalyzeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_EVENT_REDUCER_")
        self.addCleanup(self.temporary.cleanup)
        self.archive, self.manifest, self.pins = fixture(Path(self.temporary.name))
        self.manifest_hash = command.file_hash(self.archive / "manifest.json")

    def analyze(self):
        return analyze.analyze(self.archive, self.manifest_hash, self.pins)

    def repin(self, name):
        path = self.archive / name / "completed.json"
        completed = command.read(path)
        completed["files"] = {key: value["sha256"] for key, value in inventory(path.parent).items() if key != "completed.json"}
        write(path, reseal(completed))
        self.pins[name]["completed_sha256"] = command.file_hash(path)
        outer_fixture(self.archive, self.manifest, name, self.pins[name], analyze.STAGES.index(name))

    def edit_call(self, arm, index, text, finish):
        name = "readout_" + arm
        directory = self.archive / name
        row = self.manifest["roster"][index]
        stem = directory / f"actor/call_{index:04d}"
        raw = command.read(str(stem) + ".raw.json")
        ids = SyntheticTokenizer().encode(text)
        raw["raw"].update(text=text, finish_reason=finish, output_token_ids=ids)
        write(Path(str(stem) + ".raw.json"), raw)
        wrapped = command.read(str(stem) + ".response.json")
        wrapped["response"].update(text=text, finish_reason=finish, output_tokens=len(ids), truncated=finish == "length")
        wrapped.update(raw_hex=text.encode().hex(), raw_utf8_sha256=analyze.native.text_hash(text))
        write(Path(str(stem) + ".response.json"), wrapped)
        write(directory / (row["id"].replace("/", "_") + ".json"), wrapped["response"])
        scores = command.read(directory / "scores.json")
        target = command.read(self.archive / "import.json")["queries"][row["request"]]["target"]
        score = analyze.core.score_memory_response(text, target)
        scores["results"][index].update(raw=text, finish_reason=finish, score=score,
            strict_stop=finish == "stop" and score["strict"], semantic_stop=finish == "stop" and score["semantic"])
        for view in (0, 8):
            for key in ("strict_stop", "semantic_stop"):
                scores["by_view"][str(view)][key] = sum(item[key] for item in scores["results"] if item["view"] == view)
        write(directory / "scores.json", scores)
        completed = command.read(directory / "completed.json")
        completed["by_view"] = scores["by_view"]
        write(directory / "completed.json", reseal(completed))
        self.repin(name)

    def test_full_synthetic_pair_endpoint_vectors_units_and_costs(self):
        with patch.object(command.own, "_model", side_effect=AssertionError("no model")), patch.object(command.own, "_tokenizer", side_effect=AssertionError("no tokenizer")):
            result = self.analyze()
        endpoint = result["endpoint"]
        self.assertEqual(endpoint["label"], "SCOPED_EVENT_PREFIX_ACQUISITION_PASS")
        self.assertEqual((endpoint["AUTH_strict_stop"], endpoint["C0_strict_stop"], endpoint["paired_difference"]), (13, 1, 12))
        self.assertEqual(set(endpoint["ordered_vectors"]), {"W0", "W8"})
        self.assertEqual(len(endpoint["ordered_vectors"]["W8"]["arms"]["AUTH_WRITE"]["raw"]), 14)
        self.assertEqual(len(endpoint["ordered_vectors"]["W8"]["arms"]["AUTH_WRITE"]["semantic"]), 14)
        self.assertEqual(result["experimental_units"]["readout_calls"], 56)
        self.assertFalse(result["experimental_units"]["independent_56_experiences"])
        self.assertEqual(result["historical_prefix"]["original_status"], "FORMATION_FAILED")
        self.assertEqual(result["historical_prefix"]["original_returncode"], 1)
        self.assertEqual(result["historical_prefix"]["original_calls"], 17)
        self.assertEqual(result["costs_not_gpu_active"]["outer_elapsed_seconds_sum"], 156)
        self.assertFalse(result["full_contract_released"])
        self.assertFalse(result["archived_outer_release"]["fit"]["post_cvd"]["complete_cvd_visibility"])

    def test_missing_arm_not_zero(self):
        self.pins.pop("readout_NO_WRITE_C0")
        with self.assertRaisesRegex(ValueError, "all three stage pins"):
            self.analyze()

    def test_endpoint_cutoffs_fail_each_boundary_without_old17(self):
        result = self.analyze()
        for arm, index, value in (("AUTH_WRITE", 14, False), ("NO_WRITE_C0", 15, True)):
            pairs = copy.deepcopy(result["pairs"])
            pairs[index]["arms"][arm]["exact_stop"] = value
            endpoint = analyze.endpoints(pairs, result["deterministic_service"])
            self.assertEqual(endpoint["label"], "SCOPED_EVENT_PREFIX_ACQUISITION_FAIL")
        with self.assertRaises(ValueError):
            analyze.endpoints(result["pairs"][:-1], result["deterministic_service"])

    def test_nonboolean_strict_vector_rejected(self):
        result = self.analyze()
        result["pairs"][0]["arms"]["AUTH_WRITE"]["exact_stop"] = 1
        with self.assertRaisesRegex(ValueError, "boolean"):
            analyze.endpoints(result["pairs"], result["deterministic_service"])

    def test_changed_sampling_target_prose_query_or_route_rejected(self):
        name = "readout_AUTH_WRITE"
        for suffix, mutation in (("render", lambda value: value["sampling"].update(structured_outputs={"regex": ".*"})),
                                 ("request", lambda value: value["messages"].append({"role": "system", "content": "TEACHER"})),
                                 ("raw", lambda value: value["raw"].update(route={"wrong": True})),
                                 ("response", lambda value: value.update(raw_hex="00"))):
            path = self.archive / name / f"actor/call_0000.{suffix}.json"
            original = command.read(path)
            changed = copy.deepcopy(original)
            mutation(changed)
            write(path, changed)
            self.repin(name)
            with self.assertRaises(ValueError):
                self.analyze()
            write(path, original)
            self.repin(name)

    def test_scores_do_not_override_raw(self):
        path = self.archive / "readout_AUTH_WRITE/scores.json"
        scores = command.read(path)
        scores["results"][27]["strict_stop"] = True
        write(path, scores)
        self.repin("readout_AUTH_WRITE")
        with self.assertRaisesRegex(ValueError, "unchanged scorer"):
            self.analyze()

    def test_length_exact_bytes_still_fails_strict_stop(self):
        row = self.manifest["roster"][14]
        target = command.read(self.archive / "import.json")["queries"][row["request"]]["target"]
        self.edit_call("AUTH_WRITE", 14, target, "length")
        result = self.analyze()
        recorded = result["pairs"][14]["arms"]["AUTH_WRITE"]
        self.assertEqual(recorded["raw"], target)
        self.assertTrue(recorded["exact_bytes"])
        self.assertFalse(recorded["exact_stop"])
        self.assertFalse(recorded["semantic_stop"])
        self.assertEqual(recorded["errors"], ["non_stop_finish"])
        self.assertEqual(result["endpoint"]["label"], "SCOPED_EVENT_PREFIX_ACQUISITION_FAIL")

    def test_malformed_fenced_or_missing_lf_raw_never_repaired(self):
        row = self.manifest["roster"][14]
        target = command.read(self.archive / "import.json")["queries"][row["request"]]["target"]
        for raw in ("unparseable prose", target.rstrip("\n"), "```text\n" + target + "```"):
            self.edit_call("AUTH_WRITE", 14, raw, "stop")
            recorded = self.analyze()["pairs"][14]["arms"]["AUTH_WRITE"]
            self.assertEqual(recorded["raw"], raw)
            self.assertFalse(recorded["exact_stop"])
            self.assertIn("strict_raw_mismatch", recorded["errors"])

    def test_extra_retry_capture_rejected(self):
        write(self.archive / "readout_AUTH_WRITE/actor/call_0028.raw.json", {"retry": True})
        self.repin("readout_AUTH_WRITE")
        with self.assertRaisesRegex(ValueError, "exact28 actor call inventory"):
            self.analyze()

    def test_missing_call_close_or_custody_rejected(self):
        for name in ("actor/call_0000.raw.json", "actor_close.json", "custody.json"):
            path = self.archive / "readout_AUTH_WRITE" / name
            original = path.read_bytes()
            path.unlink()
            self.repin("readout_AUTH_WRITE")
            with self.assertRaises((ValueError, KeyError)):
                self.analyze()
            path.write_bytes(original)
            self.repin("readout_AUTH_WRITE")

    def test_nonzero_bool_rc_and_reservation_owner_rejected(self):
        pin = self.pins["fit"]
        root = Path(pin["outer_path"])
        for value in (1, False):
            collection = command.read(root / "collection.json")
            collection["returncode"] = value
            write(root / "collection.json", collection)
            pin["collection_sha256"] = command.file_hash(root / "collection.json")
            with self.assertRaisesRegex(ValueError, "outer completion"):
                self.analyze()
        outer_fixture(self.archive, self.manifest, "fit", pin, 0)
        collection = command.read(root / "collection.json")
        collection["observations"]["post_cvd"]["owners"] = [{"pid": 9999}]
        observation = command.read(root / "post_cvd.json")
        observation["value"] = collection["observations"]["post_cvd"]
        write(root / "post_cvd.json", observation)
        collection["files"] = {key: value for key, value in inventory(root).items() if key != "collection.json"}
        write(root / "collection.json", collection)
        pin["collection_sha256"] = command.file_hash(root / "collection.json")
        with self.assertRaisesRegex(ValueError, "CVD"):
            self.analyze()

    def test_stage_or_close_overrun_rejected(self):
        path = self.archive / "readout_AUTH_WRITE/actor/close.json"
        close = command.read(path)
        close["elapsed_actor_seconds"] = 1801
        write(path, close)
        write(path.parent.parent / "actor_close.json", close)
        self.repin("readout_AUTH_WRITE")
        with self.assertRaisesRegex(ValueError, "cost intervals"):
            self.analyze()

    def test_first_operation_may_start_before_cold_ready(self):
        directory = self.archive / "readout_AUTH_WRITE/actor"
        request = command.read(directory / "call_0000.request.json")
        load = command.read(directory / "load.json")
        self.assertLess(request["started"], load["model_load_started"])
        self.assertLess(request["started"], load["ready_at"])
        result = self.analyze()
        self.assertEqual(result["validator_amendment"], "pre_outcome_request_limits_and_operation_timing_v1")
        self.assertEqual(result["endpoint"]["AUTH_strict_stop"], 13)

    def test_missing_request_start_or_limits_rejected(self):
        path = self.archive / "readout_AUTH_WRITE/actor/call_0000.request.json"
        original = command.read(path)
        for field in ("started", "limits"):
            changed = copy.deepcopy(original)
            changed.pop(field)
            write(path, changed)
            self.repin("readout_AUTH_WRITE")
            with self.assertRaisesRegex(ValueError, "request timing/limits missing"):
                self.analyze()

    def test_production_request_limits_exact_not_repaired(self):
        path = self.archive / "readout_AUTH_WRITE/actor/call_0000.request.json"
        original = command.read(path)
        for limits in ({"deadline": original["limits"]["deadline"] + 1, "device_seconds": 1740},
                       {"deadline": original["limits"]["deadline"], "device_seconds": 1739},
                       {**original["limits"], "extra": 1}, {"device_seconds": 1740}):
            write(path, {**original, "limits": limits})
            self.repin("readout_AUTH_WRITE")
            with self.assertRaisesRegex(ValueError, "production request limits"):
                self.analyze()

    def test_request_start_after_generation_or_overlapping_prior_response_rejected(self):
        directory = self.archive / "readout_AUTH_WRITE/actor"
        path = directory / "call_0001.request.json"
        original = command.read(path)
        generation = command.read(directory / "call_0001.raw.json")["generation_started"]
        prior_start = command.read(directory / "call_0000.request.json")["started"]
        prior_duration = command.read(directory / "call_0000.response.json")["response"]["device_seconds"]
        for started in (generation + .1, prior_start + prior_duration - .1):
            write(path, {**original, "started": started})
            self.repin("readout_AUTH_WRITE")
            with self.assertRaisesRegex(ValueError, "per-call operation chronology/duration"):
                self.analyze()

    def test_individually_impossible_duration_not_hidden_by_unchanged_sum(self):
        directory = self.archive / "readout_AUTH_WRITE"
        before, after = 0., 0.
        for index, delta in ((0, -2.), (27, 2.)):
            path = directory / f"actor/call_{index:04d}.response.json"
            wrapped = command.read(path)
            before += wrapped["response"]["device_seconds"]
            wrapped["response"]["device_seconds"] += delta
            after += wrapped["response"]["device_seconds"]
            write(path, wrapped)
            row = self.manifest["roster"][index]
            write(directory / (row["id"].replace("/", "_") + ".json"), wrapped["response"])
        self.assertAlmostEqual(before, after)
        self.repin("readout_AUTH_WRITE")
        with self.assertRaisesRegex(ValueError, "per-call operation chronology/duration"):
            self.analyze()

    def test_old_threshold_or_prepared_import_drift_rejected(self):
        path = self.archive / "manifest.json"
        manifest = copy.deepcopy(self.manifest)
        manifest["endpoint"]["auth_min"] = 15
        write(path, reseal(manifest))
        with self.assertRaisesRegex(ValueError, "separate scope"):
            analyze.analyze(self.archive, command.file_hash(path), self.pins)

    def test_fit_adapter_and_update_source_drift_rejected(self):
        path = self.archive / "fit/write/adapter/adapter_model.safetensors"
        path.write_bytes(b"OTHER_CHECKPOINT")
        self.repin("fit")
        with self.assertRaisesRegex(ValueError, "writer inventory"):
            self.analyze()

    def test_fresh_process_identity_join_rejected(self):
        path = self.archive / "readout_AUTH_WRITE/actor/identity.json"
        identity = command.read(path)
        identity["pid"] = 1000
        write(path, identity)
        self.repin("readout_AUTH_WRITE")
        with self.assertRaisesRegex(ValueError, "cold worker identity"):
            self.analyze()

    def test_source_relocation_is_exact_relative_byte_mapping_only(self):
        sources = command.source_files()
        root = Path(command.__file__).resolve().parents[1]
        moved = {str(Path("/FIXED_NATIVE_SOURCE") / Path(path).relative_to(root)): checksum for path, checksum in sources.items()}
        result = analyze.source_binding(moved)
        self.assertEqual(result["original_source_root"], "/FIXED_NATIVE_SOURCE")
        moved[next(iter(moved))] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source byte pins"):
            analyze.source_binding(moved)

    def test_artifact_symlink_and_live_root_rejected(self):
        (self.archive / "alias.json").symlink_to(self.archive / "manifest.json")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.analyze()

    def test_cli_fresh_output_only(self):
        out = Path(self.temporary.name) / "analysis"
        pins_path = Path(self.temporary.name) / "pins.json"
        write(pins_path, self.pins)
        argv = ["--archive", str(self.archive), "--manifest-sha256", self.manifest_hash,
                "--stage-pins", str(pins_path), "--output", str(out)]
        analyze.main(argv)
        self.assertTrue((out / "analysis.json").is_file())
        with self.assertRaisesRegex(ValueError, "fresh output"):
            analyze.main(argv)


if __name__ == "__main__":
    unittest.main()
