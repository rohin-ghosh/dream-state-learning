"""Synthetic NEW outcomes only; frozen pre-additive input/history fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.dont_write_bytecode = True


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


analysis = load("/tmp/astra_additive_replay_analysis_20260913.py", "additive_analysis_test")
runner = load("/tmp/astra_additive_replay_run_20260913.py", "additive_fixture_plan_only")
ARCHIVE = Path("/tmp/astra_own_replay_repair_native_20260913_attempt1")


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((analysis.canonical(value) + "\n").encode())
    return analysis.digest(path)


def inventory(path):
    return {str(item.relative_to(path)): analysis.digest(item) for item in sorted(Path(path).rglob("*")) if item.is_file()}


def fixture(home, seed, apis):
    core, legacy, utilities = apis["additive_core"], apis["legacy"], apis["utilities"]
    old_root = ARCHIVE / f"own_replay_repair_seed{seed}_20260913_attempt1"
    old = analysis.read(old_root / "plan.json")
    old_scores_path = old_root.with_name(old_root.name + "_collected") / "scores.json"
    old_scores = analysis.read(old_scores_path)
    old_collection_path = old_scores_path.parent / "collection.json"
    saved = {arm: analysis.read(old_root / f"training_{arm}.json") for arm in ("EXTRA_MEMORY", "REPLAY")}
    original = analysis.read(old_root / "memory_history/plan.json")
    material = core.build(old, dict(parent=old["parent"], memory_plan=original, mixture=analysis.read(old_root / "mixture.json"), saved_training=saved,
        saved_training_sha256={arm: analysis.digest(old_root / f"training_{arm}.json") for arm in saved}))
    paired = apis["additive_trainer"].prepare_pair(saved["EXTRA_MEMORY"], saved["REPLAY"], seed=seed,
        source_pins=dict(extra_memory_sha256=analysis.digest(old_root / "training_EXTRA_MEMORY.json"), replay_sha256=analysis.digest(old_root / "training_REPLAY.json")))
    root = home / f"mirror{seed}"
    root.mkdir()
    snapshots = {}
    def snapshot(name, source):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(Path(source).read_bytes())
        snapshots[name] = analysis.digest(target)
    for name in old["snapshot_hashes"]:
        if name != "spec.json":
            snapshot("upstream/" + name, old_root / name)
    for name in ("plan.json", "spec.json", "capture_complete.json", "mixture.json", "training_EXTRA_MEMORY.json", "training_REPLAY.json", "calls.json"):
        snapshot("repair/" + name, old_root / name)
    snapshot("repair/scores.json", old_scores_path)
    snapshot("repair/collection.json", old_collection_path)
    specification = dict(runner_sha256=analysis.PINS["runner"][1], seed=seed, fit_seed=seed, gpu_index=seed,
        gpu_uuid="GPU-SYNTHETIC-NOT-A-NATIVE-RESULT", expected_boot_id="0"*36, lease_end=2000000000,
        repair_history=dict(root=old["root"], plan_sha256=analysis.digest(old_root / "plan.json"),
            completion_sha256=analysis.digest(old_root / "capture_complete.json"), scores_sha256=analysis.digest(old_scores_path),
            collection=dict(path=old["root"]+"_collected/collection.json", sha256=analysis.digest(old_collection_path))))
    for name in ("core", "trainer"):
        specification[name] = dict(path="/tmp/"+analysis.PINS[name][0], sha256=analysis.PINS[name][1])
    specification["protocol"] = dict(path=analysis.DEFAULT_PROTOCOL, sha256=analysis.PROTOCOL_PIN)
    specification["repair_runtime"] = dict(path="/tmp/astra_own_replay_repair_run_20260913.py", sha256=runner.REPAIR_PIN)
    for name in ("core", "trainer", "protocol", "repair_runtime"):
        snapshot("sources/" + Path(specification[name]["path"]).name, specification[name]["path"])
    snapshots["spec.json"] = write(root / "spec.json", specification)
    prepared = {arm: core.prepared_from_saved(material, arm) for arm in analysis.ARMS}
    calls = analysis.read(old_root / "calls.json")
    payloads = dict({"material.json": material, "paired.json": paired, "calls.json": calls}, **{f"training_{arm}.json": value for arm, value in prepared.items()})
    inputs = {name: write(root / name, value) for name, value in payloads.items()}
    plan = runner.make_plan(f"/SYNTHETIC_ONLY/additive_seed{seed}", specification, snapshots["spec.json"],
                           dict(memory_plan=original, material=material, old_plan=old), inputs, snapshots)
    plan_hash = write(root / "plan.json", plan)
    write(root / "prepare_started.json", dict(spec_sha256=snapshots["spec.json"], monotonic=1., time=100.))
    write(root / "prepare_done.json", dict(plan_sha256=plan_hash, elapsed_seconds=2.))
    write(root / "controller_started.json", dict(plan_sha256=plan_hash, pid=999, monotonic=1000., deadline=8200., seconds=7200))
    dataset = analysis.read(old_root / "memory/dataset.json")
    capture = analysis.read(old_root / "memory/capture.json")
    retention = analysis.read(old_root / "memory/retention.json")
    scorer = legacy.FrozenScorer(capture, dataset, retention, apis)
    original_rows = {panel: {row["row_id"]: row for row in (dataset["rows"] if panel in ("exact", "paraphrase") else retention["evaluation"][panel])} for panel in analysis.PANELS}
    cells = {arm: {panel: [] for panel in analysis.PANELS} for arm in analysis.ARMS}
    fits, norms = {}, {}
    stage_inventory = {}
    for index, stage in enumerate(analysis.STAGES):
        directory = root / "run" / stage
        directory.mkdir(parents=True)
        start = 1000. + 100*index
        identity = dict(pid=2000+index, pgid=2000+index, start_ticks=1234+index)
        command = [plan["python"], "-B", "/tmp/"+analysis.PINS["runner"][0], "worker", "--root", plan["root"], "--plan-sha256", plan_hash, "--stage", stage, "--allow-gpu"]
        write(directory / "launch.json", dict(identity=identity, stage=stage, plan_sha256=plan_hash, command=command, time=start+1, monotonic=start+1))
        write(directory / "started.json", dict(pid=identity["pid"], pgid=identity["pgid"], stage=stage, plan_sha256=plan_hash, time=start+2, monotonic=start+2))
        arm, kind = stage.rsplit("_", 1)
        if kind == "fit":
            training = prepared[arm]
            manifest = copy.deepcopy(old_scores["fits"]["EXTRA_MEMORY"])
            pair_map = {pair["memory_row_id"]: pair["replay_row_id"] for pair in paired["pairs"]}
            order = [dict(epoch=epoch, position=position, memory_row_id=row_id, replay_row_id=pair_map.get(row_id) if arm == "ADDITIVE" else None)
                     for epoch, rows in enumerate(training["epoch_order"]) for position, row_id in enumerate(rows)]
            losses = [dict(item, memory=1., replay=2. if item["replay_row_id"] else None, total=3. if item["replay_row_id"] else 1.) for item in order]
            manifest.update(schema=apis["additive_trainer"].TRAIN_SCHEMA, arm=arm, objective=training["objective"], trainer_sha256=analysis.PINS["trainer"][1],
                frozen_trainer_sha256=analysis.FROZEN_TRAINER_PIN, protocol_sha256=analysis.PROTOCOL_PIN, paired_sha256=paired["paired_sha256"],
                source_pins=paired["source_pins"], primary_encoding_sha256=training["source_encoding_sha256"], primary_training_items_sha256=training["training_items_sha256"],
                primary_epoch_order_sha256=training["epoch_order_sha256"], pairs_sha256=training["pair_sha256"], costs=paired["costs"][arm],
                train_tokens_seen=paired["costs"][arm]["total_tokens"], memory_forwards=training["updates"], replay_forwards=192 if arm == "ADDITIVE" else 0,
                optimizer_steps=training["updates"], executed_order=order, component_losses=losses, executed_order_sha256=core.value_hash(order),
                mean_loss_per_epoch=[sum(row["total"] for row in losses[:training["rows"]])/training["rows"]]*8, final_loss=losses[-1]["total"],
                train_seconds=1., wall_seconds=1.2, component_seconds=dict(memory_forward_backward=.4, replay_forward_backward=.3 if arm == "ADDITIVE" else 0, optimizer=.1),
                timing_scope="SYNTHETIC fixture intervals", peak_cuda_memory_allocated_bytes=12345, peak_memory_scope="SYNTHETIC fixture only")
            manifest["corpus"]["sha256"] = inputs[f"training_{arm}.json"]
            adapter = directory / "adapter"
            adapter.mkdir()
            write(adapter / "train_manifest.json", manifest)
            write(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05, bias="none", target_modules=plan["configs"][arm]["target_modules"]))
            (adapter / "adapter_model.safetensors").write_bytes(b"SYNTHETIC NONMODEL BYTES")
            (adapter / "DONE").write_bytes(b"ok\n")
            (adapter / "steps.jsonl").write_bytes(b"".join((analysis.canonical(row)+"\n").encode() for row in losses))
            norms[arm] = dict(changed_elements=1, l2=dict(delta=1., source=2., final=3.), comparison="SYNTHETIC")
            write(directory / "fit.json", dict(arm=arm, adapter=plan["root"]+"/run/"+stage+"/adapter", adapter_files=inventory(adapter),
                initialized_from=plan["parent"], training_sha256=inputs[f"training_{arm}.json"], calls=0, updates=training["updates"], norms=norms[arm], elapsed_seconds=2.))
            fits[arm] = manifest
        else:
            route = dict(name="real_record_memory_"+arm.lower(), id=1, path=plan["root"]+"/run/"+arm+"_fit/adapter")
            write(directory / "identity.json", dict(arm=arm, route=route, model_files=plan["model_files"], parent=plan["parent"], params=plan["params"]))
            for position, call in enumerate(calls):
                raw = original_rows[call["panel"]][call["row_id"]]["raw_target"]
                started = start+3+.1*position
                response = dict(call["native"], text=raw, decoded_output=raw, actual_prompt_token_ids=call["native"]["prompt_token_ids"],
                    output_token_ids=[7], finish_reason="stop", stop_reason=None, started=started, ended=started+.01, lora_request=route)
                response_hash = write(directory / (call["call_id"]+".response.json"), response)
                write(directory / (call["call_id"]+".request.json"), dict(call, params=plan["params"], lora_request=route))
                cells[arm][call["panel"]].append(dict(row_id=call["row_id"], raw=raw, finish_reason="stop", response_sha256=response_hash,
                    score=scorer(call["panel"], call["row_id"], raw, "stop", call["messages"]),
                    cost=dict(prompt_tokens=len(response["actual_prompt_token_ids"]), output_tokens=1, generation_seconds=response["ended"]-response["started"])))
            write(directory / "readout.json", dict(arm=arm, calls=len(calls), updates=0))
        write(directory / "worker_done.json", dict(stage=stage, plan_sha256=plan_hash, monotonic=start+25))
        write(directory / "exit.json", dict(identity=identity, returncode=0, monotonic=start+26))
        write(directory / "released.json", dict(identity=identity, stage=stage, group_absent=True, gpu_vacant=True, time=start+27, monotonic=start+27))
        stage_inventory[stage] = inventory(directory)
    complete = dict(scope=analysis.SCOPE, plan_sha256=plan_hash, stages=stage_inventory, scored=False, fits=2,
                    updates=16*(analysis.COUNTS[seed]+24), calls=2*len(calls), elapsed_seconds=330.)
    completion_hash = write(root / "capture_complete.json", complete)
    histories = dict(old_scores["historical_cells"], **old_scores["cells"])
    old_index = {panel: {row["row_id"]: row for row in rows} for panel, rows in histories["LR0"].items()}
    screen = {arm: legacy.screen(seed, {panel: {row["row_id"]: row for row in rows} for panel, rows in cells[arm].items()}, old_index, utilities) for arm in analysis.ARMS}
    report = dict(scope=analysis.SCOPE, seed=seed, parent=plan["parent"], plan_sha256=plan_hash, completion_sha256=completion_hash,
        source_bindings=specification, input_hashes=inputs, counts=plan["counts"], cells=cells, fits=fits, parameter_diagnostics=norms,
        historical_cells=histories, historical_manifests=dict(old_scores["historical_manifests"], **old_scores["fits"]), reused_endpoints=plan["reused_endpoints"],
        training_costs={arm: {key: value for key, value in training.items() if key not in ("items", "encoding", "epoch_order", "replay_items", "replay_encoding")}
                        for arm, training in prepared.items()}, screen=screen, best_constant=legacy.constants(dataset, calls, scorer, cells, utilities),
        incremental_cost=dict(calls=2*len(calls), fits=2, updates=complete["updates"], historical_calls=0, historical_updates=0, historical_fits=0,
            new_source_calls=0, teacher_calls=0, controller_seconds=330.), native_capture_custody_checked=True, automatic_pass=False, scientific_pass=None)
    collected = home / f"collected{seed}"
    scores_hash = write(collected / "scores.json", report)
    collection_hash = write(collected / "collection.json", dict(scores_sha256=scores_hash, completion_sha256=completion_hash, collection_seconds=3.))
    claim_path = home / f"claim{seed}.json"
    claim_hash = write(claim_path, dict(plan_sha256=plan_hash, out=plan["root"]+"_collected", retry=False))
    launcher = home / f"launcher{seed}"
    launcher.mkdir()
    tiny = dict(path="/tmp/SYNTHETIC_ONLY_TINY/receipt.json", sha256=analysis.TINY_PIN,
                trainer_sha256=analysis.PINS["trainer"][1], fixture_only=True, native_scientific_evidence=False)
    holder = dict(pid=888, started_unix=990., plan_sha256=plan_hash, tiny_cpu_receipt=tiny,
                  custodian_sha256=analysis.PINS["launcher"][1], runner_sha256=analysis.PINS["runner"][1])
    launched = dict(holder, status="LAUNCHED_NOT_RESULT", started_unix=991., seed=seed, root=plan["root"], gpu_index=seed,
                    gpu_uuid=plan["gpu_uuid"], automatic_once_collection=True,
                    identity=dict(pid=888, ppid=777, start_ticks=999, uid=1234, comm="python", cmdline_sha256="0"*64),
                    command=[plan["python"], "-B", "/tmp/"+analysis.PINS["launcher"][0], "hold", "--seed", str(seed),
                             "--runner-sha256", analysis.PINS["runner"][1], "--tiny-cpu-receipt", tiny["path"]])
    command = [plan["python"], "-B", "/tmp/"+analysis.PINS["runner"][0]]
    root_args = ["--root", plan["root"], "--plan-sha256", plan_hash]
    launcher_records = {
        "precheck.json": dict(time=989., gpu_index=seed, gpu_uuid=plan["gpu_uuid"], reservations=[], unresolved=[]),
        "launched.json": launched, "holder_started.json": holder,
        "controller.json": dict(pid=999, pgid=999, started_unix=992., command=command+["controller"]+root_args+["--allow-gpu"]),
        "controller_exit.json": dict(returncode=0, completed_unix=1335.),
        "collection_started.json": dict(plan_sha256=plan_hash, completion_sha256=completion_hash, started_unix=1336.),
        "collector.json": dict(pid=1001, pgid=1001, started_unix=1337.,
                               command=command+["collect"]+root_args+["--completion-sha256", completion_hash, "--out", plan["root"]+"_collected"]),
        "collector_exit.json": dict(returncode=0, completed_unix=1341.), "exit.json": dict(returncode=0, completed_unix=1342.)}
    for name, record in launcher_records.items():
        write(launcher / name, record)
    (launcher / "stdout.log").write_bytes(b"SYNTHETIC ONLY\n")
    return dict(seed=seed, root=str(root), plan_sha256=plan_hash, completion_sha256=completion_hash,
                scores=dict(path=str(collected / "scores.json"), sha256=scores_hash), collection=dict(path=str(collected / "collection.json"), sha256=collection_hash),
                collection_claim=dict(path=str(claim_path), sha256=claim_hash), launcher=dict(root=str(launcher), files=inventory(launcher)))


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apis = analysis.load_apis()
        cls.temporary = tempfile.TemporaryDirectory(prefix="additive_reducer_synthetic_")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.home = Path(cls.temporary.name)
        cls.entries = [fixture(cls.home, seed, cls.apis) for seed in range(3)]
        cls.bundles = [analysis.load_bundle(entry) for entry in cls.entries]

    def test_full_three_root_cohort_all_costs_and_denominators(self):
        result = analysis.reduce_cohort(self.bundles, self.apis)
        self.assertEqual([result["costs"][key] for key in ("fits", "updates", "calls")], [6, 1632, 480])
        self.assertFalse(result["automatic_promotion"])
        self.assertIsNone(result["scientific_pass"])
        self.assertAlmostEqual(result["costs"]["prepare_plus_holder_wall_hours"], 3*(352+2)/3600)
        for seed, entry in enumerate(result["seeds"]):
            self.assertEqual(entry["screens"]["ADDITIVE"]["threshold"], (8, 7, 5)[seed])
            self.assertEqual(entry["denominators"]["exact"], (14, 8, 8)[seed])
            self.assertEqual(entry["costs"]["ADDITIVE"]["tokens"]["replay_forwards"], 192)
            self.assertEqual(entry["costs"]["MEMORY_ONLY"]["tokens"]["replay_forwards"], 0)
            self.assertTrue(entry["historical_extra_memory_check"]["noncontemporaneous"])

    def test_missing_duplicate_or_boolean_seed_rejected(self):
        for bundles in (self.bundles[:2], [self.bundles[0]]*3):
            with self.assertRaises(ValueError):
                analysis.reduce_cohort(bundles, self.apis)
        bundle = copy.deepcopy(self.bundles[0])
        bundle["entry"]["seed"] = False
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)

    def test_transport_broken_pipe_preserved_with_successful_native_chain(self):
        bundle = copy.deepcopy(self.bundles[1])
        anomaly = dict(error="BrokenPipeError(32, 'Broken pipe')", holder_may_be_running=True)
        bundle["launcher"]["failure.json"] = anomaly
        bundle["entry"]["launcher"]["files"]["failure.json"] = "e"*64
        result = analysis.reduce_seed(bundle, self.apis)
        self.assertEqual(result["launcher"]["launcher_failure"], anomaly)
        self.assertEqual(result["launcher"]["terminal_controller_rc"], 0)
        self.assertEqual(result["launcher"]["launcher_failure_sha256"], "e"*64)
        self.assertTrue(result["launcher"]["single_launch_receipts_consistent"])
        self.assertIn("BrokenPipeError", analysis.markdown(dict(seeds=[result])))

    def test_launcher_terminal_chain_rejects_bool_rc_and_conflicts(self):
        changes = [(name, "returncode", value) for name in ("controller_exit.json", "collector_exit.json", "exit.json") for value in (False, 1)]
        changes += [("holder_started.json", "pid", 887), ("controller.json", "pid", 998),
                    ("collection_started.json", "completion_sha256", "0"*64),
                    ("precheck.json", "reservations", [123]), ("exit.json", "completed_unix", 0.)]
        for name, key, value in changes:
            with self.subTest(name=name, key=key, value=value):
                bundle = copy.deepcopy(self.bundles[0])
                bundle["launcher"][name][key] = value
                with self.assertRaises(ValueError):
                    analysis.validate_launcher(bundle)
        for name in ("exit.json", "controller_exit.json", "collector_exit.json"):
            bundle = copy.deepcopy(self.bundles[0])
            del bundle["launcher"][name]
            with self.assertRaises(ValueError):
                analysis.validate_launcher(bundle)

    def test_launcher_failure_cannot_excuse_failed_native_controller(self):
        for flag in (False, True):
            bundle = copy.deepcopy(self.bundles[0])
            bundle["launcher"]["failure.json"] = dict(error="BrokenPipeError()", holder_may_be_running=flag)
            bundle["entry"]["launcher"]["files"]["failure.json"] = "e"*64
            if flag:
                bundle["launcher"]["controller_exit.json"]["returncode"] = 1
            with self.assertRaises(ValueError):
                analysis.validate_launcher(bundle)

    def test_loader_preserves_pinned_optional_anomaly_and_rejects_extra_receipts(self):
        with tempfile.TemporaryDirectory(prefix="additive_launcher_synthetic_") as directory:
            entry = copy.deepcopy(self.entries[0])
            root = Path(directory)
            original = Path(entry["launcher"]["root"])
            for name in entry["launcher"]["files"]:
                (root / name).write_bytes((original / name).read_bytes())
            raw = b'{ "holder_may_be_running" : true, "error" : "BrokenPipeError()" }\n'
            (root / "failure.json").write_bytes(raw)
            entry["launcher"] = dict(root=str(root), files=inventory(root))
            loaded = analysis.load_bundle(entry)
            self.assertTrue(analysis.validate_launcher(loaded)["terminal_chain_consistent"])
            self.assertEqual((root / "failure.json").read_bytes(), raw)
            (root / "second_controller.json").write_bytes(b'{}')
            with self.assertRaises(ValueError):
                analysis.load_bundle(entry)
            entry["launcher"]["files"] = inventory(root)
            with self.assertRaises(ValueError):
                analysis.load_bundle(entry)

    def test_bool_returncode_missing_exit_and_release(self):
        for name, key, value in (("exit.json", "returncode", False), ("released.json", "gpu_vacant", False), ("started.json", "pid", True)):
            bundle = copy.deepcopy(self.bundles[0])
            bundle["files"]["run/ADDITIVE_fit/"+name][key] = value
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)

    def test_rejects_raw_source_route_finish_or_cost_changes(self):
        base = self.bundles[0]
        call = base["files"]["calls.json"][0]
        path = "run/ADDITIVE_readout/"+call["call_id"]+".response.json"
        for key, value in (("text", "rewritten"), ("finish_reason", "length"), ("started", 0.)):
            bundle = copy.deepcopy(base)
            bundle["files"][path][key] = value
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)
        bundle = copy.deepcopy(base)
        bundle["report"]["cells"]["ADDITIVE"]["exact"][0]["cost"]["output_tokens"] = 2
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)

    def test_masks_pair_order_and_reported_tokens_not_repairable(self):
        for key in ("epoch_order", "items", "encoding"):
            bundle = copy.deepcopy(self.bundles[0])
            bundle["files"]["training_ADDITIVE.json"][key].reverse()
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)
        bundle = copy.deepcopy(self.bundles[0])
        bundle["report"]["training_costs"]["ADDITIVE"]["token_accounting"]["replay_total_tokens"] = 0
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)

    def test_loss_sum_not_mean_and_nonfinite_norm(self):
        bundle = copy.deepcopy(self.bundles[0])
        manifest = bundle["files"]["run/ADDITIVE_fit/adapter/train_manifest.json"]
        row = next(row for row in manifest["component_losses"] if row["replay"] is not None)
        row["total"] /= 2
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)
        bundle = copy.deepcopy(self.bundles[0])
        bundle["files"]["run/ADDITIVE_fit/fit.json"]["norms"]["l2"]["delta"] = float("nan")
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)

    def test_original_parent_not_repair_descendant(self):
        bundle = copy.deepcopy(self.bundles[0])
        bundle["plan"]["parent"]["adapter"] = "/repair/descendant"
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)

    def test_constant_baseline_and_history_substitution_rejected(self):
        bundle = copy.deepcopy(self.bundles[0])
        bundle["report"]["best_constant"]["variants"]["exact"]["oracle_best_content_correct"] += 1
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)
        bundle = copy.deepcopy(self.bundles[0])
        bundle["report"]["historical_cells"]["EXTRA_MEMORY"]["held"][0]["raw"] = "changed"
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)

    def test_no_gain_offsets_lr0_correct_loss(self):
        utilities, legacy = self.apis["utilities"], self.apis["legacy"]
        bundle = self.bundles[0]
        cells = copy.deepcopy(bundle["report"]["cells"]["ADDITIVE"])
        original = bundle["report"]["historical_cells"]["LR0"]
        baseline = {panel: {row["row_id"]: row for row in rows} for panel, rows in original.items()}
        target = next(row_id for row_id, row in baseline["held"].items() if row["score"]["passed"])
        row = next(row for row in cells["held"] if row["row_id"] == target)
        row["score"]["passed"] = False
        candidate = {panel: {row["row_id"]: row for row in rows} for panel, rows in cells.items()}
        screen = legacy.screen(0, candidate, baseline, utilities)
        self.assertFalse(screen["passed"])
        self.assertIn(target, screen["lr0_correct_regressions"]["held"])
        change = analysis.item_changes(candidate["held"], baseline["held"], "held", "passed", utilities)
        self.assertIn(target, change["row_ids"]["second_only"])

    def test_json_duplicate_nan_pin_and_path_rejected(self):
        for raw in ('{"seed":0,"seed":1}', '{"score":NaN}'):
            with self.assertRaises(ValueError):
                analysis.decode(raw)
        with self.assertRaises(ValueError):
            analysis.local(self.home, "../outside")
        entry = copy.deepcopy(self.entries[0])
        entry["scores"]["sha256"] = "0"*64
        with self.assertRaises(ValueError):
            analysis.load_bundle(entry)

    def test_cli_write_once_without_native_execution(self):
        manifest = self.home / "manifest.json"
        pin = write(manifest, dict(schema=analysis.INPUT_SCHEMA, seeds=self.entries))
        out = self.home / "analysis"
        with patch.object(analysis, "load_apis", return_value=self.apis):
            result = analysis.run(str(manifest), pin, str(out))
            self.assertEqual(result["analysis_sha256"], analysis.digest(out / "analysis.json"))
            with self.assertRaises(ValueError):
                analysis.run(str(manifest), pin, str(out))


if __name__ == "__main__":
    unittest.main()
