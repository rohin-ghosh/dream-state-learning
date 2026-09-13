"""Finite CPU regression tests; native identity/model/GPU boundaries are mocked."""
import copy
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


sys.dont_write_bytecode = True
specification = importlib.util.spec_from_file_location("lower_lr_candidate_test", "/tmp/astra_memory_lower_lr_run_20260913.py")
runner = importlib.util.module_from_spec(specification)
specification.loader.exec_module(runner)
frozen = runner.runtime()


class CandidateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="lower_lr_cpu_")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.old = self.home / "old"
        self.old.mkdir()
        self.collected = self.home / "old_collected"
        self.collected.mkdir()
        self.root = self.home / "candidate"
        self.protocol = self.home / "protocol.md"
        self.protocol.write_text("CPU fixture protocol; not native launch authorization.\n")
        self.spec = dict(runner_sha256=runner.digest(runner.SELF),
            runtime=dict(path=str(frozen.SELF), sha256=runner.RUNTIME_PIN),
            design=dict(path="/tmp/astra_memory_retention_repair_design_20260913.md", sha256=runner.DESIGN_PIN),
            protocol=dict(path="/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_ACTUAL_MEMORY_RETENTION_REPAIR_2026-09-13.md",
                          sha256=runner.PROTOCOL_PIN), seed=0, fit_seed=0,
            gpu_index=4, gpu_uuid="GPU-CPU-NOT-NATIVE", expected_boot_id="0" * 36, lease_end=time.time() + 100000,
            history=dict(root=str(self.old), plan_sha256=runner.HISTORY_PINS[0][0], completion_sha256=runner.HISTORY_PINS[0][1],
                         collection=dict(path=str(self.collected / "collection.json"), sha256=runner.HISTORY_PINS[0][2]),
                         scores_sha256=runner.HISTORY_PINS[0][3]))
        self.calls = [dict(panel=panel, row_id=panel + "_row", call_id=panel + "_call", messages=[dict(role="user", content=panel)],
                           prompt_token_ids=[11, 12]) for panel in runner.PANELS]
        self.cells = {panel: [dict(row_id=panel + "_row", raw="untouched\n", finish_reason="stop", score={}, response_sha256="CPU")]
                      for panel in runner.PANELS}
        self.historical = dict(cells=dict(WRITE=copy.deepcopy(self.cells), LR0=copy.deepcopy(self.cells)), fits={})
        config = dict(lr=1e-4, seed=0, rank=8, alpha=16, dropout=.05, epochs=8, batch_size=1, note="unchanged original note")
        self.original = dict(root=str(self.old), specification=dict(seed=0, fit_seed=0), model="CPU_MODEL", model_files={"config": "pin"},
            chat_template="CPU_TEMPLATE", environment={}, source="CPU_SOURCE", parent=dict(adapter="ORIGINAL_PERCEPTION_PARENT", adapter_files={"weight": "pin"}),
            engine={}, params=dict(max_tokens=192), status="WRITE", python=os.path.abspath(sys.executable), python_sha256=runner.digest(sys.executable),
            configs=dict(WRITE=config, LR0=dict(config, lr=0.0)), calls_per_arm=88, updates_per_arm=112)
        self.files = {"dataset.json": dict(rows=[dict(raw_target="unmodified raw")]), "capture.json": dict(actual="CPU fixture"),
                      "retention.json": {}, "training.json": dict(rows=14, updates=112, encoding=[dict(labels=[-100, 23, 1])]), "calls.json": self.calls}
        for name, value in self.files.items():
            frozen.write(self.old / name, value)
        self.original["input_hashes"] = {name: runner.digest(self.old / name) for name in runner.INPUTS}
        frozen.write(self.old / "plan.json", self.original)
        frozen.write(self.old / "capture_complete.json", dict(fixture=True))
        frozen.write(self.collected / "collection.json", dict(fixture=True))
        frozen.write(self.collected / "scores.json", self.historical)
        self.bound = dict(dataset=self.files["dataset.json"], retention={}, original_calls=[], parent=self.original["parent"])

    def api(self):
        return SimpleNamespace(**{name: getattr(frozen, name) for name in
            ("read", "write", "failure", "budget", "new_external", "offline", "encoded")},
            check_allocation=Mock(), protected_inputs=Mock(return_value=[]),
            GPU_QUERY_SECONDS=30, CLEANUP_SECONDS=40, identity=Mock(return_value=dict(pid=70001, pgid=70001, start_ticks=99)),
            cleanup_owned=Mock(), summarize=Mock(return_value=self.summary()), fit_arm=Mock(), capture_readout=Mock(), score_calls=Mock(return_value=self.cells))

    def summary(self):
        return dict(totals=dict(WRITE=dict(exact=dict(numerators=dict(production_eligible=8)))),
                    paired_WRITE_LR0={panel: dict(passed=dict(second_only=0)) for panel in ("held", "canary")})

    def prepared(self):
        self.root.mkdir()
        (self.root / "history").mkdir()
        frozen.write(self.root / "spec.json", self.spec)
        spec_pin = runner.digest(self.root / "spec.json")
        plan = runner.make_plan(self.root, self.spec, spec_pin, self.original)
        for name, source in runner.snapshot_paths(self.spec, self.original).items():
            (self.root / name).write_bytes(source.read_bytes())
        frozen.write(self.root / "prepare_started.json", dict(spec_sha256=spec_pin))
        frozen.write(self.root / "plan.json", plan)
        return plan, runner.digest(self.root / "plan.json")

    def test_closed_spec_pins_seed_and_separate_protocol(self):
        runner.validate_spec(self.spec)
        for update in (dict(seed=True), dict(fit_seed=1), dict(extra="field"), dict(lease_end=float("inf"))):
            with self.subTest(update=update), self.assertRaises(ValueError):
                runner.validate_spec(dict(self.spec, **update))
        bad = copy.deepcopy(self.spec)
        bad["history"]["scores_sha256"] = runner.HISTORY_PINS[1][3]
        with self.assertRaisesRegex(ValueError, "history pins"):
            runner.validate_spec(bad)
        bad = dict(self.spec, protocol=self.spec["design"])
        with self.assertRaisesRegex(ValueError, "source pin"):
            runner.validate_spec(bad)

    def test_all_seeds_lr_only_original_parent_and_costs(self):
        old_bytes = (self.old / "plan.json").read_bytes()
        for seed, rows in enumerate((14, 8, 8)):
            original = copy.deepcopy(self.original)
            original.update(calls_per_arm=2 * rows + 60, updates_per_arm=8 * rows)
            original["configs"]["WRITE"]["seed"] = seed
            original["configs"]["LR0"]["seed"] = seed
            plan = runner.make_plan(self.root, dict(self.spec, seed=seed, fit_seed=seed), "specpin", original)
            differences = {key for key in plan["configs"]["WRITE"] if plan["configs"]["WRITE"][key] != original["configs"]["WRITE"][key]}
            self.assertEqual(differences, {"lr"})
            self.assertEqual(plan["configs"]["WRITE"]["lr"], 3e-5)
            self.assertEqual(plan["configs"]["WRITE"]["seed"], seed)
            self.assertEqual(plan["parent"], self.original["parent"])
            self.assertEqual(plan["stages"], ["WRITE_fit", "WRITE_readout"])
            self.assertEqual(plan["limits"]["updates"], 8 * rows)
            self.assertEqual(plan["limits"]["calls"], 2 * rows + 60)
            self.assertEqual(plan["limits"]["controller"], 3600)
            self.assertEqual(plan["limits"]["collection"], 180)
            self.assertEqual(plan["input_hashes"], original["input_hashes"])
        self.assertEqual(old_bytes, (self.old / "plan.json").read_bytes())

    def test_input_count_drift_rejected(self):
        with self.assertRaisesRegex(ValueError, "workload"):
            runner.make_plan(self.root, self.spec, "pin", dict(self.original, calls_per_arm=89))

    def test_prepare_copies_bytes_replays_encoder_and_warm_parent(self):
        memory = self.api()
        memory.encode_training = Mock(return_value=self.files["training.json"])
        memory.build_calls = Mock(return_value=self.calls)
        trainer = SimpleNamespace(_warm_parent=Mock(), TrainConfig=lambda **config: config)
        bound = dict(self.bound, trainer=trainer, helper=object(),
                     probe=SimpleNamespace(native_tokenizer=Mock(return_value=SimpleNamespace(chat_template="CPU_TEMPLATE"))))
        source = self.home / "spec.json"
        frozen.write(source, self.spec)
        snapshots = {name: path.read_bytes() for name, path in runner.snapshot_paths(self.spec, self.original).items()}
        with patch.object(runner, "runtime", return_value=memory), patch.object(runner, "bind_history", return_value=(self.original, bound, self.historical)), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            result = runner.prepare(self.root, source, runner.digest(source), allow_native=True)
        self.assertEqual(result["calls"], 88)
        for name, before in snapshots.items():
            self.assertEqual((self.root / name).read_bytes(), before)
        self.assertEqual(memory.encode_training.call_args.args[-1], 0)
        self.assertEqual(trainer._warm_parent.call_args.args[0], "ORIGINAL_PERCEPTION_PARENT")
        self.assertEqual(trainer._warm_parent.call_args.args[-1]["lr"], 3e-5)
        self.assertFalse((self.root / "run").exists())

    def test_prepare_rejects_changed_prompt_tokens(self):
        memory = self.api()
        memory.encode_training = Mock(return_value=self.files["training.json"])
        memory.build_calls = Mock(return_value=[dict(self.calls[0], prompt_token_ids=[99])])
        bound = dict(self.bound, trainer=Mock(), helper=Mock(),
                     probe=SimpleNamespace(native_tokenizer=Mock(return_value=SimpleNamespace(chat_template="CPU_TEMPLATE"))))
        source = self.home / "spec.json"
        frozen.write(source, self.spec)
        with patch.object(runner, "runtime", return_value=memory), patch.object(runner, "bind_history", return_value=(self.original, bound, self.historical)), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), self.assertRaisesRegex(ValueError, "token/mask/order"):
            runner.prepare(self.root, source, runner.digest(source), allow_native=True)
        self.assertTrue((self.root / "prepare_failure.json").exists())
        self.assertFalse((self.root / "plan.json").exists())

    def test_independent_verify_rejects_descendant_or_lr_and_input_mutation(self):
        plan, pin = self.prepared()
        with patch.object(runner, "bind_history", return_value=(self.original, self.bound, self.historical)):
            runner.verify(self.root, pin)
            for changed in (dict(plan, parent=dict(adapter="WRITE_DESCENDANT")), dict(plan, configs=self.original["configs"])):
                (self.root / "plan.json").write_bytes(frozen.encoded(changed))
                with self.assertRaisesRegex(ValueError, "independent candidate plan"):
                    runner.verify(self.root, runner.digest(self.root / "plan.json"))
            (self.root / "plan.json").write_bytes(frozen.encoded(plan))
            (self.root / "training.json").write_text("{}\n")
            with self.assertRaisesRegex(ValueError, "immutable input"):
                runner.verify(self.root, pin)

    def test_source_and_history_pins_not_relaxed(self):
        self.assertEqual(runner.digest(frozen.SELF), runner.RUNTIME_PIN)
        bad = dict(path=str(self.protocol), sha256=runner.RUNTIME_PIN)
        with self.assertRaisesRegex(ValueError, "source pin"):
            runner.runtime(bad)
        with self.assertRaises(ValueError):
            runner.bind_history(self.api(), dict(self.spec, seed=2, fit_seed=2))

    def test_duplicate_missing_foreign_rows_and_panels_rejected(self):
        runner.validate_cells(self.cells, self.calls)
        for row_ids in (["exact_row", "exact_row"], [], ["foreign"]):
            cells = copy.deepcopy(self.cells)
            cells["exact"] = [dict(self.cells["exact"][0], row_id=row_id) for row_id in row_ids]
            with self.assertRaisesRegex(ValueError, "source row"):
                runner.validate_cells(cells, self.calls)
        with self.assertRaisesRegex(ValueError, "panel"):
            runner.validate_cells(dict(self.cells, extra=[]), self.calls)
        with self.assertRaisesRegex(ValueError, "duplicate call"):
            runner.validate_cells(self.cells, self.calls + [self.calls[0]])

    def test_worker_forwarding_only_candidate_and_original_seed(self):
        plan, pin = self.prepared()
        memory = self.api()
        (self.root / "run").mkdir()
        for stage in runner.STAGES:
            (self.root / "run" / stage).mkdir()
            with patch.object(runner, "runtime", return_value=memory), patch.object(runner, "verify", return_value=(memory, plan, self.bound, self.historical)), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"]), patch.object(os, "getpgrp", return_value=os.getpid()):
                runner.worker(self.root, pin, stage, allow_gpu=True)
        memory.fit_arm.assert_called_once_with(plan, self.bound, "WRITE")
        memory.capture_readout.assert_called_once_with(plan, self.bound, "WRITE")
        with self.assertRaisesRegex(ValueError, "WRITE worker"):
            runner.worker(self.root, pin, "LR0_fit", allow_gpu=True)

    def stage_fixture(self):
        plan, pin = self.prepared()
        (self.root / "run").mkdir()
        memory = self.api()
        bound = dict(self.bound, probe=SimpleNamespace(gpu_state=Mock(return_value=True)))
        process = Mock(pid=70001)
        process.wait.return_value = 0
        return memory, plan, pin, bound, process

    def test_failed_precheck_never_spawns(self):
        memory, plan, pin, bound, process = self.stage_fixture()
        bound["probe"].gpu_state.return_value = False
        with patch.object(subprocess, "Popen", return_value=process) as spawn, self.assertRaisesRegex(ValueError, "vacancy"):
            runner.run_stage(memory, plan, pin, "WRITE_fit", time.monotonic() + 200, bound)
        spawn.assert_not_called()
        memory.cleanup_owned.assert_not_called()

    def test_stage_uses_new_worker_and_owned_cleanup(self):
        memory, plan, pin, bound, process = self.stage_fixture()
        with patch.object(subprocess, "Popen", return_value=process) as spawn:
            runner.run_stage(memory, plan, pin, "WRITE_fit", time.monotonic() + 200, bound)
        self.assertIn(str(runner.SELF), spawn.call_args.args[0])
        self.assertNotIn(str(frozen.SELF), spawn.call_args.args[0])
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        self.assertEqual(spawn.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], plan["gpu_uuid"])
        memory.cleanup_owned.assert_called_once_with(process, memory.identity.return_value, bound["probe"])
        self.assertTrue((self.root / "run/WRITE_fit/released.json").exists())

    def test_timeout_and_cleanup_failure_both_preserved(self):
        memory, plan, pin, bound, process = self.stage_fixture()
        process.wait.side_effect = subprocess.TimeoutExpired("worker", 1)
        memory.cleanup_owned.side_effect = RuntimeError("CPU cleanup failure")
        with patch.object(subprocess, "Popen", return_value=process), self.assertRaisesRegex(RuntimeError, "cleanup"):
            runner.run_stage(memory, plan, pin, "WRITE_fit", time.monotonic() + 200, bound)
        directory = self.root / "run/WRITE_fit"
        self.assertTrue((directory / "stage_failure.json").exists())
        self.assertTrue((directory / "cleanup_failure.json").exists())
        self.assertFalse((directory / "released.json").exists())
        self.assertEqual(frozen.read(directory / "stage_failure.json")["error_type"], "TimeoutExpired")

    def test_controller_only_two_stages_actual_cost_no_control_receipt(self):
        plan, pin = self.prepared()
        memory = self.api()
        with patch.object(runner, "runtime", return_value=memory), patch.object(runner, "verify", return_value=(memory, plan, self.bound, self.historical)), patch.object(runner, "run_stage") as stages, patch.object(runner, "validate_completed", return_value={"CPU": "inventory"}), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            runner.controller(self.root, pin, allow_gpu=True)
        self.assertEqual([call.args[3] for call in stages.call_args_list], list(runner.STAGES))
        receipt = frozen.read(self.root / "capture_complete.json")
        self.assertEqual((receipt["calls"], receipt["updates"]), (88, 112))
        self.assertFalse(receipt["scored"])
        self.assertFalse((self.root / "run/LR0_fit").exists())

    def test_controller_failure_no_completion(self):
        plan, pin = self.prepared()
        memory = self.api()
        with patch.object(runner, "runtime", return_value=memory), patch.object(runner, "verify", return_value=(memory, plan, self.bound, self.historical)), patch.object(runner, "run_stage", side_effect=RuntimeError("CPU failure")), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), self.assertRaises(RuntimeError):
            runner.controller(self.root, pin, allow_gpu=True)
        self.assertTrue((self.root / "controller_failure.json").exists())
        self.assertFalse((self.root / "capture_complete.json").exists())

    def test_comparisons_reuse_unchanged_cells_and_explicit_noncontemporaneous_costs(self):
        plan, _ = self.prepared()
        memory = self.api()
        before = copy.deepcopy(self.historical)
        report = runner.comparison(memory, plan, self.bound, self.historical, self.cells)
        self.assertEqual(self.historical, before)
        self.assertEqual(set(report["cells"]), {"WRITE"})
        self.assertEqual(report["historical_cells"]["HIGH"], before["cells"]["WRITE"])
        self.assertEqual(report["incremental_cost"], dict(calls=88, updates=112, historical_calls=0, historical_updates=0))
        for endpoint in report["reused_endpoints"].values():
            self.assertTrue(endpoint["noncontemporaneous"])
            self.assertEqual(endpoint["incremental_calls"], 0)
        self.assertEqual(memory.summarize.call_count, 2)
        self.assertEqual(memory.summarize.call_args_list[1].args[0]["LR0"], before["cells"]["WRITE"])
        self.assertFalse(report["automatic_pass"])
        self.assertIsNone(report["scientific_pass"])

    def test_once_only_collector_never_calls_old_collect(self):
        plan, pin = self.prepared()
        memory = self.api()
        complete = dict(scope=runner.SCOPE, plan_sha256=pin, stages={}, calls=88, updates=112, scored=False, elapsed_seconds=2)
        frozen.write(self.root / "capture_complete.json", complete)
        completion_pin = runner.digest(self.root / "capture_complete.json")
        (self.root / "run/WRITE_fit/adapter").mkdir(parents=True)
        frozen.write(self.root / "run/WRITE_fit/adapter/train_manifest.json", {})
        frozen.write(self.root / "run/WRITE_fit/fit.json", dict(norms={}))
        before = {path: path.read_bytes() for path in self.old.iterdir()}
        with patch.object(runner, "runtime", return_value=memory), patch.object(runner, "verify", return_value=(memory, plan, self.bound, self.historical)), patch.object(runner, "validate_completed", return_value={}):
            runner.collect(self.root, pin, completion_pin, self.home / "new_collected")
            with self.assertRaises(FileExistsError):
                runner.collect(self.root, pin, completion_pin, self.home / "another_collected")
        memory.score_calls.assert_called_once_with(plan, self.bound, "WRITE")
        self.assertFalse((self.home / "another_collected").exists())
        self.assertEqual(before, {path: path.read_bytes() for path in self.old.iterdir()})
        self.assertFalse(hasattr(memory, "collect"))

    def test_bad_collection_raw_join_preserves_failure_and_consumes_claim(self):
        plan, pin = self.prepared()
        memory = self.api()
        memory.score_calls.side_effect = ValueError("CPU wrong source")
        frozen.write(self.root / "capture_complete.json", dict(scope=runner.SCOPE, plan_sha256=pin, stages={}, calls=88,
            updates=112, scored=False, elapsed_seconds=2))
        with patch.object(runner, "runtime", return_value=memory), patch.object(runner, "verify", return_value=(memory, plan, self.bound, self.historical)), patch.object(runner, "validate_completed", return_value={}), self.assertRaisesRegex(ValueError, "wrong source"):
            runner.collect(self.root, pin, runner.digest(self.root / "capture_complete.json"), self.home / "bad_collect")
        self.assertTrue(self.root.with_name(self.root.name + ".collection_claim.json").exists())
        self.assertTrue((self.home / "bad_collect/collection_failure.json").exists())
        self.assertFalse((self.home / "bad_collect/collection.json").exists())

    def test_no_native_entry_without_explicit_permission(self):
        with self.assertRaises(ValueError):
            runner.prepare(self.root, "missing", "pin")
        with self.assertRaises(ValueError):
            runner.controller(self.root, "pin")
        with self.assertRaises(ValueError):
            runner.worker(self.root, "pin", "WRITE_fit")

    def test_strict_screen_requires_itemwise_canary_held_restoration_and_exact_floor(self):
        summary = self.summary()
        for seed, minimum in enumerate((8, 7, 5)):
            summary["totals"]["WRITE"]["exact"]["numerators"]["production_eligible"] = minimum
            self.assertTrue(runner.repair_screen(seed, summary)["met"])
            summary["totals"]["WRITE"]["exact"]["numerators"]["production_eligible"] = minimum - 1
            self.assertFalse(runner.repair_screen(seed, summary)["met"])
        for panel in ("held", "canary"):
            summary = self.summary()
            summary["paired_WRITE_LR0"][panel]["passed"].update(second_only=1, first_only=10)
            self.assertFalse(runner.repair_screen(0, summary)["met"])

    def test_bind_history_uses_original_verify_and_checks_raw_source_join(self):
        memory = self.api()
        memory.OUTER_SECONDS = 3600
        memory.verify = Mock(return_value=(self.original, self.bound))
        memory.validate_completed = Mock(return_value={"old": "inventory"})
        complete = dict(plan_sha256="OLDPLAN", scored=False, elapsed_seconds=1, stages={"old": "inventory"}, calls=176, updates=224)
        (self.old / "capture_complete.json").write_bytes(frozen.encoded(complete))
        historical = copy.deepcopy(self.historical)
        historical.update(seed=0, plan_sha256="OLDPLAN", completion_sha256=runner.digest(self.old / "capture_complete.json"),
                          parent=self.original["parent"], native_capture_custody_checked=True)
        for arm in ("WRITE", "LR0"):
            adapter = self.old / "run" / (arm + "_fit") / "adapter"
            adapter.mkdir(parents=True)
            manifest = dict(arm=arm, fixture=True)
            frozen.write(adapter / "train_manifest.json", manifest)
            historical["fits"][arm] = manifest
            readout = self.old / "run" / (arm + "_readout")
            readout.mkdir()
            for call in self.calls:
                path = readout / (call["call_id"] + ".response.json")
                frozen.write(path, dict(text="untouched\n", finish_reason="stop"))
                historical["cells"][arm][call["panel"]][0]["response_sha256"] = runner.digest(path)
        (self.collected / "scores.json").write_bytes(frozen.encoded(historical))
        collection = dict(scores_sha256=runner.digest(self.collected / "scores.json"), completion_sha256=historical["completion_sha256"])
        (self.collected / "collection.json").write_bytes(frozen.encoded(collection))
        frozen.write(self.old.with_name("old.collection_claim.json"), dict(plan_sha256="OLDPLAN", out=str(self.collected), retry=False))
        spec = copy.deepcopy(self.spec)
        spec["history"] = dict(root=str(self.old), plan_sha256="OLDPLAN", completion_sha256=collection["completion_sha256"],
            collection=dict(path=str(self.collected / "collection.json"), sha256=runner.digest(self.collected / "collection.json")), scores_sha256=collection["scores_sha256"])
        with patch.object(runner, "validate_spec"):
            runner.bind_history(memory, spec, native=False)
            memory.verify.assert_called_once_with(self.old, "OLDPLAN", native=False)
            response = self.old / "run/LR0_readout/exact_call.response.json"
            response.write_bytes(frozen.encoded(dict(text="wrong source", finish_reason="stop")))
            with self.assertRaisesRegex(ValueError, "raw source join"):
                runner.bind_history(memory, spec, native=False)

    def completed_fixture(self):
        plan, pin = self.prepared()
        plan["calls_per_arm"] = len(self.calls)
        memory = self.api()
        memory.check_fit = Mock()
        route = dict(path="CANDIDATE_ADAPTER", id=1)
        memory.route_for = Mock(return_value=route)
        bound = dict(self.bound, helper=SimpleNamespace(check_adapter=Mock()),
                     formation=SimpleNamespace(tree=Mock(return_value={"CPU": "pin"}), validate_response=Mock()))
        manifest = dict(corpus=dict(sha256=plan["input_hashes"]["training.json"]),
                        warm_start=dict(initialized_state={"tensor": "original"}, source_state={"tensor": "original"}))
        historical = dict(fits={arm: copy.deepcopy(manifest) for arm in ("WRITE", "LR0")})
        for offset, stage in enumerate(runner.STAGES):
            directory = self.root / "run" / stage
            directory.mkdir(parents=True)
            identity = dict(pid=100 + offset, pgid=100 + offset, start_ticks=123 + offset)
            command = [plan["python"], "-B", str(runner.SELF), "worker", "--root", plan["root"], "--plan-sha256", pin, "--stage", stage, "--allow-gpu"]
            frozen.write(directory / "launch.json", dict(identity=identity, stage=stage, plan_sha256=pin, command=command))
            frozen.write(directory / "started.json", dict(pid=identity["pid"], pgid=identity["pgid"], stage=stage, plan_sha256=pin))
            frozen.write(directory / "released.json", dict(identity=identity, stage=stage))
            if stage == "WRITE_fit":
                (directory / "adapter").mkdir()
                frozen.write(directory / "adapter/train_manifest.json", manifest)
                frozen.write(directory / "fit.json", dict(updates=112, calls=0, training_sha256=plan["input_hashes"]["training.json"]))
            else:
                frozen.write(directory / "identity.json", dict(arm="WRITE", route=route, model_files=plan["model_files"], parent=plan["parent"], params=plan["params"]))
                frozen.write(directory / "readout.json", dict(arm="WRITE", calls=len(self.calls), updates=0))
                for call in self.calls:
                    frozen.write(directory / (call["call_id"] + ".request.json"), dict(call, params=plan["params"], lora_request=route))
                    frozen.write(directory / (call["call_id"] + ".response.json"), dict(fixture=True))
        return memory, plan, pin, bound, historical

    def test_completed_warm_inventory_mismatch_rejected(self):
        memory, plan, pin, bound, historical = self.completed_fixture()
        self.assertEqual(set(runner.validate_completed(memory, plan, pin, bound, historical)), set(runner.STAGES))
        memory.check_fit.assert_called_once()
        historical["fits"]["LR0"]["warm_start"]["initialized_state"] = {"tensor": "wrong seed"}
        with self.assertRaisesRegex(ValueError, "warm tensors"):
            runner.validate_completed(memory, plan, pin, bound, historical)

    def test_completed_rejects_forged_lr0_and_missing_release(self):
        memory, plan, pin, bound, historical = self.completed_fixture()
        (self.root / "run/LR0_fit").mkdir()
        with self.assertRaisesRegex(ValueError, "candidate-only stage"):
            runner.validate_completed(memory, plan, pin, bound, historical)
        (self.root / "run/LR0_fit").rmdir()
        (self.root / "run/WRITE_fit/released.json").unlink()
        with self.assertRaises(FileNotFoundError):
            runner.validate_completed(memory, plan, pin, bound, historical)


if __name__ == "__main__":
    unittest.main()
