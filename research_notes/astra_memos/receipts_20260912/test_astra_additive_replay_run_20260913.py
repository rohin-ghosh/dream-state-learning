"""Mock CPU lifecycle tests; original input files only, no native execution."""
import ast
import copy
import importlib.util
import json
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


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runner = load("/tmp/astra_additive_replay_run_20260913.py", "additive_runner_test")
fixtures = load("/tmp/test_astra_additive_replay_core_20260913.py", "additive_input_fixtures")
core = fixtures.core
memory = runner.runtime()


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.CoreTests.setUpClass()
        if runner.digest("/tmp/astra_additive_replay_train_20260913.py") != runner.TRAINER_PIN or core.digest(core.SELF) != runner.CORE_PIN:
            raise AssertionError("final pinned trainer/core required")
        cls.trainer = load("/tmp/astra_additive_replay_train_20260913.py", "additive_explicit_trainer_test")
        cls.old = load("/tmp/astra_own_replay_repair_run_20260913.py", "additive_old_runtime_test")
        cls.native = memory.load(dict(path="/tmp/astra_level1_real_record_run_20260913.py", sha256=memory.FORMATION_PIN), "additive_native_validator")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="additive_runner_cpu_")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / "new_pair"
        old_plan, source_bound = copy.deepcopy(fixtures.CoreTests.fixtures[0])
        self.material = core.build(old_plan, source_bound)
        self.original = copy.deepcopy(old_plan)
        self.original.update(python=os.path.abspath(sys.executable), python_sha256=runner.digest(sys.executable))
        self.old_root = fixtures.ARCHIVED / "own_replay_repair_seed0_20260913_attempt1"
        self.source = self.home / "source.py"
        self.source.write_text("cpu_fixture_only = True\n")
        self.api = SimpleNamespace(**vars(memory))
        self.api.offline = Mock()
        self.api.cleanup_owned = Mock()
        self.api.identity = Mock(return_value=dict(pid=4321, pgid=4321, start_ticks=99))
        self.parent = copy.deepcopy(old_plan["parent"])
        self.calls = memory.read(self.old_root / "calls.json")
        self.api.build_calls = Mock(return_value=self.calls)
        self.tokenizer = SimpleNamespace(chat_template=old_plan["chat_template"])
        old_mock = SimpleNamespace(snapshots=Mock(return_value={}), protected=Mock(return_value=[]), screen=self.old.screen,
                                   constant_diagnostic=Mock(return_value={"fixture_only": True}))
        self.bound = dict(source_bound, material=self.material, core=core, additive_trainer=self.trainer,
            old=old_mock, old_plan=dict(old_plan, root=str(self.old_root)), old_bound={}, memory_plan=self.original,
            trainer=SimpleNamespace(__file__=str(self.source), TrainConfig=lambda **config: SimpleNamespace(**config), _warm_parent=Mock()),
            dataset={"rows": self.material["mixture"]["memory_rows"]}, retention={}, original_calls=[],
            probe=SimpleNamespace(native_tokenizer=Mock(return_value=self.tokenizer), gpu_state=Mock(return_value=True)),
            helper=SimpleNamespace(check_adapter=Mock(side_effect=lambda path, config: self.tree(path))),
            formation=SimpleNamespace(tree=self.tree, validate_response=self.native.validate_response),
            history={}, historical_manifests={})
        self.cells = {panel: [] for panel in ("exact", "paraphrase", "held", "canary")}
        for call in self.calls:
            score = dict(passed=True, strict=True, content_correct=True, production_eligible=True, format="exact")
            if call["panel"] in ("exact", "paraphrase"):
                score = dict(score=score, exact_target_bytes=True)
            self.cells[call["panel"]].append(dict(row_id=call["row_id"], raw="CPU_ONLY", finish_reason="stop", score=score))
        self.bound["history"] = {name: copy.deepcopy(self.cells) for name in runner.HISTORY}
        self.bound["historical_manifests"] = {"EXTRA_MEMORY": {"warm_start": dict(source_state={"lora_A": "original"},
            initialized_state={"lora_A": "initial"}, optimizer_defaults={"lr": 3e-5})}}
        self.api.score_calls = Mock(return_value=self.cells)
        self.binding = dict(path=str(self.source), sha256=runner.digest(self.source))
        receipt = self.home / "history_receipts" / "collection.json"
        receipt.parent.mkdir()
        memory.write(receipt, {})
        self.spec = dict(runner_sha256=runner.digest(runner.SELF), seed=0, fit_seed=0, gpu_index=0, gpu_uuid="GPU-CPU-FIXTURE",
                         expected_boot_id="0" * 36, lease_end=time.time()+100000,
                         repair_history=dict(root=str(self.old_root), plan_sha256="fixture", completion_sha256="fixture",
                                             collection=dict(path=str(receipt), sha256=runner.digest(receipt)), scores_sha256="fixture"))
        self.spec.update({key: self.binding for key in ("core", "trainer", "protocol", "repair_runtime")})
        spec_path = self.home / "spec.json"
        memory.write(spec_path, self.spec)
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "bind", return_value=self.bound), \
             patch.object(runner, "snapshots", return_value={"sources/fixture.py": self.source}), patch.object(runner, "allocation"), \
             patch.object(runner, "encode", side_effect=lambda bound, arm, tokenizer, seed: core.prepared_from_saved(self.material, arm)), \
             patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            result = runner.prepare(self.root, spec_path, runner.digest(spec_path), allow_native=True)
        self.plan, self.pin = memory.read(self.root / "plan.json"), result["plan_sha256"]
        self.pair = memory.read(self.root / "paired.json")

    def tree(self, path):
        if str(path) == self.parent["adapter"]:
            return self.parent["adapter_files"]
        return {str(item.relative_to(path)): runner.digest(item) for item in sorted(Path(path).rglob("*")) if item.is_file()}

    def manifest(self, arm):
        prepared = memory.read(self.root / f"training_{arm}.json")
        pairs = {pair["memory_row_id"]: pair["replay_row_id"] for pair in prepared["pairs"]}
        order = [dict(epoch=epoch, position=position, memory_row_id=identity, replay_row_id=pairs.get(identity) if arm == "ADDITIVE" else None)
                 for epoch, rows in enumerate(prepared["epoch_order"]) for position, identity in enumerate(rows)]
        return dict(schema=self.trainer.TRAIN_SCHEMA, arm=arm, objective=prepared["objective"], trainer_sha256=runner.TRAINER_PIN,
            frozen_trainer_sha256=memory.TRAINER_PIN, protocol_sha256=runner.PROTOCOL_PIN, paired_sha256=self.pair["paired_sha256"],
            source_pins=self.pair["source_pins"], primary_encoding_sha256=prepared["source_encoding_sha256"],
            primary_training_items_sha256=prepared["training_items_sha256"], primary_epoch_order_sha256=prepared["epoch_order_sha256"],
            pairs_sha256=prepared["pair_sha256"], costs=self.pair["costs"][arm], train_tokens_seen=self.pair["costs"][arm]["total_tokens"],
            memory_forwards=304, replay_forwards=192 if arm == "ADDITIVE" else 0, optimizer_steps=304,
            tokens=dict(target=prepared["target_tokens"], total=prepared["total_tokens"]), packing=dict(mode="one_item_per_sequence", n_sequences=38),
            config=self.plan["configs"][arm], empty=False, steps=304, micro_batches=304, epochs_run=8, nonfinite_batches=0,
            corpus=dict(n_items=38, n_encoded=38, n_skipped_no_target=0, sha256=self.plan["input_hashes"][f"training_{arm}.json"]),
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
            mean_loss_per_epoch=[1.] * 8, final_loss=1., executed_order=order,
            component_losses=[dict(row, memory=1., replay=2. if row["replay_row_id"] else None, total=3. if row["replay_row_id"] else 1.) for row in order],
            warm_start=dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", optimizer_initialization="fresh_per_write", optimizer_state_restored=False,
                optimizer_initial_state_entries=0, optimizer_class="torch.optim.adamw.AdamW", optimizer_defaults={"lr": 3e-5},
                optimizer_state_saved=False, parent_path=self.parent["adapter"], parent_files=self.parent["adapter_files"],
                parent_files_after=self.parent["adapter_files"], parent_unchanged=True, initialized_loaded_state_check=True, base_frozen=True,
                adapter_count=1, phase_seed=0, phase_steps=304, parent_cumulative_steps=320, cumulative_steps=624,
                trainer_sha256=memory.TRAINER_PIN, source_state={"lora_A": "original"}, initialized_state={"lora_A": "initial"},
                final_state={"lora_A": "changed"}, trainable_names=["layers.lora_A", "layers.lora_B"]))

    def check(self, manifest, arm="ADDITIVE"):
        runner.check_fit(manifest, memory.read(self.root / f"training_{arm}.json"), self.plan["configs"][arm], self.parent,
                         arm, self.plan["counts"], self.pair)

    def complete(self):
        entry = time.monotonic()
        memory.write(self.root / "controller_started.json", dict(plan_sha256=self.pin, monotonic=entry, deadline=entry+runner.SECONDS, seconds=runner.SECONDS))
        (self.root / "run").mkdir()
        for index, stage in enumerate(runner.STAGES):
            directory = self.root / "run" / stage
            directory.mkdir()
            identity = dict(pid=1000+index, pgid=1000+index, start_ticks=100+index)
            command = [self.plan["python"], "-B", str(runner.SELF), "worker", "--root", str(self.root), "--plan-sha256", self.pin, "--stage", stage, "--allow-gpu"]
            memory.write(directory / "launch.json", dict(identity=identity, stage=stage, plan_sha256=self.pin, command=command, time=time.time(), monotonic=time.monotonic()))
            memory.write(directory / "started.json", dict(pid=identity["pid"], pgid=identity["pgid"], stage=stage, plan_sha256=self.pin, time=time.time(), monotonic=time.monotonic()))
            arm, kind = stage.rsplit("_", 1)
            if kind == "fit":
                adapter = directory / "adapter"
                adapter.mkdir()
                memory.write(adapter / "train_manifest.json", self.manifest(arm))
                (adapter / "DONE").write_bytes(b"ok\n")
                memory.write(directory / "fit.json", dict(arm=arm, adapter=str(adapter), adapter_files=self.tree(adapter),
                    initialized_from=self.parent, calls=0, updates=304, training_sha256=self.plan["input_hashes"][f"training_{arm}.json"],
                    norms=dict(changed_elements=1, l2={"delta": 1.})))
            else:
                route = memory.route_for(self.plan, self.bound, arm)
                memory.write(directory / "identity.json", dict(arm=arm, route=route, model_files=self.plan["model_files"], parent=self.parent, params=self.plan["params"]))
                for call in self.calls:
                    request = dict(call, params=self.plan["params"], lora_request=route)
                    now = time.monotonic()
                    response = dict(call["native"], text="CPU fixture", decoded_output="CPU fixture", actual_prompt_token_ids=call["native"]["prompt_token_ids"],
                                    output_token_ids=[1], finish_reason="stop", stop_reason=None, started=now, ended=now, lora_request=route)
                    memory.write(directory / (call["call_id"] + ".request.json"), request)
                    memory.write(directory / (call["call_id"] + ".response.json"), response)
                memory.write(directory / "readout.json", dict(arm=arm, calls=88, updates=0))
            memory.write(directory / "worker_done.json", dict(stage=stage, plan_sha256=self.pin, monotonic=time.monotonic()))
            memory.write(directory / "exit.json", dict(identity=identity, returncode=0, monotonic=time.monotonic()))
            memory.write(directory / "released.json", dict(identity=identity, stage=stage, group_absent=True, gpu_vacant=True, time=time.time(), monotonic=time.monotonic()))
        inventory = runner.validate_completed(self.api, self.plan, self.pin, self.bound)
        memory.write(self.root / "capture_complete.json", dict(scope=runner.SCOPE, plan_sha256=self.pin, stages=inventory,
                     scored=False, fits=2, updates=608, calls=176, elapsed_seconds=time.monotonic()-entry))
        return runner.digest(self.root / "capture_complete.json")

    def test_actual_trainer_pair_matches_core_all_three_seeds(self):
        for seed, (plan, bound) in enumerate(fixtures.CoreTests.fixtures):
            material = core.build(plan, bound)
            source = fixtures.ARCHIVED / f"own_replay_repair_seed{seed}_20260913_attempt1"
            context = dict(bound, material=material, core=core, old_plan=dict(plan, root=str(source)), additive_trainer=self.trainer)
            result = runner.paired(context)
            self.assertEqual(result["pairs"], material["pairs"])
            self.assertEqual(result["primary"], bound["saved_training"]["EXTRA_MEMORY"])
            self.assertEqual(result["costs"]["ADDITIVE"]["replay_forwards"], 192)

    def test_preparation_exact_config_calls_and_costs(self):
        self.assertEqual(self.plan["configs"]["ADDITIVE"], self.plan["configs"]["MEMORY_ONLY"])
        self.assertEqual(self.plan["limits"]["global_updates"], 1632)
        self.assertEqual(self.plan["limits"]["global_calls"], 480)
        self.assertEqual(memory.read(self.root / "calls.json"), self.calls)
        self.assertFalse((self.root / "run").exists())

    def test_fit_checks_both_objectives(self):
        for arm in runner.ARMS:
            self.check(self.manifest(arm), arm)

    def test_fit_rejects_averaged_or_missing_replay_and_wrong_order(self):
        baseline = self.manifest("ADDITIVE")
        index = next(index for index, row in enumerate(baseline["component_losses"]) if row["replay"] is not None)
        for key, value in (("total", 1.5), ("replay", None), ("memory_row_id", "OTHER")):
            manifest = copy.deepcopy(baseline)
            manifest["component_losses"][index][key] = value
            with self.assertRaises(ValueError):
                self.check(manifest)

    def test_fit_rejects_nonfinite_dose_warm_and_token_drift(self):
        for key, value in (("steps", 128), ("final_loss", float("nan")), ("train_tokens_seen", 0), ("trainer_sha256", "WRONG")):
            manifest = self.manifest("ADDITIVE")
            manifest[key] = value
            with self.assertRaises(ValueError):
                self.check(manifest)
        manifest = self.manifest("ADDITIVE")
        manifest["warm_start"]["parent_path"] = "/descendant"
        with self.assertRaises(ValueError):
            self.check(manifest)

    def test_fit_invokes_explicit_trainer_with_original_parent(self):
        directory = self.root / "run/ADDITIVE_fit"
        directory.mkdir(parents=True)
        self.bound["reflection"] = SimpleNamespace(load_native_model=Mock(return_value=(self.tokenizer, SimpleNamespace())))
        self.api.tensor_diagnostics = Mock(return_value=dict(changed_elements=1, l2={"delta": 1.}))
        def fake_fit(pair, tokenizer, base, config, out, **kwargs):
            adapter = Path(out)
            adapter.mkdir()
            memory.write(adapter / "train_manifest.json", self.manifest("ADDITIVE"))
            (adapter / "DONE").write_bytes(b"ok\n")
        with patch.object(self.trainer, "run_training", side_effect=fake_fit) as fit, \
             patch.object(runner, "encode", side_effect=lambda bound, arm, tokenizer, seed: core.prepared_from_saved(self.material, arm)):
            runner.fit_arm(self.api, self.plan, self.bound, "ADDITIVE")
        self.assertEqual(fit.call_args.kwargs["arm"], "ADDITIVE")
        self.assertEqual(fit.call_args.kwargs["init_adapter"], self.parent["adapter"])
        self.assertEqual(fit.call_args.kwargs["expected_parent_files"], self.parent["adapter_files"])
        self.assertIs(fit.call_args.kwargs["trainer"], self.bound["trainer"])
        self.assertEqual(fit.call_args.args[0], self.pair)
        self.assertTrue((directory / "fit.json").exists())

    def test_actual_file_pin_not_reserialized_object_substitute(self):
        context = dict(self.bound, old_plan=dict(self.bound["old_plan"], root=str(self.home)))
        for arm in ("EXTRA_MEMORY", "REPLAY"):
            (self.home / f"training_{arm}.json").write_text(json.dumps(self.bound["saved_training"][arm], indent=1))
        with self.assertRaisesRegex(ValueError, "file-byte"):
            runner.paired(context)

    def test_verify_source_and_plan_drift(self):
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "bind", return_value=self.bound), \
             patch.object(runner, "snapshots", return_value={"sources/fixture.py": self.source}):
            runner.verify(self.root, self.pin)
            (self.root / "paired.json").write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "immutable"):
                runner.verify(self.root, self.pin)

    def test_full_cold_four_stage_validation(self):
        self.complete()
        self.assertEqual(len(runner.validate_completed(self.api, self.plan, self.pin, self.bound)), 4)

    def test_missing_release_exit_or_changed_readout_refuses_completion(self):
        self.complete()
        path = self.root / "run/ADDITIVE_readout/exit.json"
        record = memory.read(path)
        record["returncode"] = False
        path.write_bytes(memory.encoded(record))
        with self.assertRaisesRegex(ValueError, "custody"):
            runner.validate_completed(self.api, self.plan, self.pin, self.bound)

    def test_failed_precheck_never_spawns(self):
        self.bound["probe"].gpu_state.return_value = False
        with patch.object(runner, "allocation"), patch.object(runner.subprocess, "Popen") as spawn, self.assertRaisesRegex(ValueError, "vacancy"):
            runner.run_stage(self.api, self.plan, self.pin, runner.STAGES[0], time.monotonic()+500, self.bound)
        spawn.assert_not_called()

    def test_stage_isolated_uuid_and_owned_cleanup(self):
        (self.root / "run").mkdir()
        process = Mock(pid=4321)
        process.wait.return_value = 0
        with patch.object(runner, "allocation"), patch.object(runner.subprocess, "Popen", return_value=process) as spawn:
            runner.run_stage(self.api, self.plan, self.pin, runner.STAGES[0], time.monotonic()+500, self.bound)
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        self.assertEqual(spawn.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], self.plan["gpu_uuid"])
        self.api.cleanup_owned.assert_called_once()
        self.assertTrue((self.root / "run" / runner.STAGES[0] / "exit.json").exists())

    def test_stage_timeout_and_cleanup_failure_both_preserved(self):
        (self.root / "run").mkdir()
        process = Mock(pid=4321)
        process.wait.side_effect = subprocess.TimeoutExpired("fixture", 1)
        self.api.cleanup_owned.side_effect = ValueError("fixture cleanup failure")
        with patch.object(runner, "allocation"), patch.object(runner.subprocess, "Popen", return_value=process), self.assertRaisesRegex(ValueError, "cleanup"):
            runner.run_stage(self.api, self.plan, self.pin, runner.STAGES[0], time.monotonic()+500, self.bound)
        directory = self.root / "run" / runner.STAGES[0]
        self.assertTrue((directory / "stage_failure.json").exists())
        self.assertTrue((directory / "cleanup_failure.json").exists())

    def test_controller_does_not_continue_after_stage_failure(self):
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.api, self.plan, self.bound)), \
             patch.object(runner, "allocation"), patch.object(runner, "run_stage", side_effect=ValueError("fixture stage error")) as stage, \
             patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), self.assertRaisesRegex(ValueError, "stage error"):
            runner.controller(self.root, self.pin, allow_gpu=True)
        self.assertEqual(stage.call_count, 1)
        self.assertTrue((self.root / "controller_failure.json").exists())

    def test_once_collection_imports_history_no_capture_or_fit(self):
        completion = self.complete()
        output = self.home / "collected"
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.api, self.plan, self.bound)):
            runner.collect(self.root, self.pin, completion, output)
            with self.assertRaises(FileExistsError):
                runner.collect(self.root, self.pin, completion, self.home / "second")
        scores = memory.read(output / "scores.json")
        self.assertEqual(set(scores["historical_cells"]), set(runner.HISTORY))
        self.assertEqual(scores["incremental_cost"]["new_source_calls"], 0)
        self.assertEqual(scores["incremental_cost"]["calls"], 176)
        self.assertFalse(scores["automatic_pass"])

    def test_collection_failure_consumes_claim(self):
        completion = self.complete()
        self.api.score_calls.side_effect = ValueError("fixture score failure")
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.api, self.plan, self.bound)), \
             self.assertRaisesRegex(ValueError, "score failure"):
            runner.collect(self.root, self.pin, completion, self.home / "bad_collection")
        self.assertTrue(self.root.with_name(self.root.name + ".collection_claim.json").exists())
        self.assertTrue((self.home / "bad_collection/collection_failure.json").exists())

    def test_entry_budgets_charge_verification_bootstrap(self):
        for function, args, kwargs, seconds in ((runner.prepare, (self.root, "unused", "unused"), {"allow_native": True}, 180),
            (runner.controller, (self.root, self.pin), {"allow_gpu": True}, 7200), (runner.collect, (self.root, self.pin, "unused", "unused"), {}, 180)):
            with patch.object(runner, "runtime", return_value=self.api), patch.object(runner.time, "monotonic", side_effect=[100., 111.]), \
                 patch.object(self.api, "budget", side_effect=ValueError("clock sentinel")) as budget, patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), \
                 self.assertRaisesRegex(ValueError, "clock sentinel"):
                function(*args, **kwargs)
            budget.assert_called_once_with(seconds-11.)

    def test_no_old_lifecycle_mutation_or_capture_collection(self):
        tree = ast.parse(runner.SELF.read_text())
        calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
        self.assertFalse([call for call in calls if isinstance(call, ast.Attribute) and call.attr in ("collect", "controller", "worker", "admit")])
        self.assertNotIn("setattr(", runner.SELF.read_text())
        self.assertEqual(runner.digest("/tmp/astra_own_replay_repair_run_20260913.py"), runner.REPAIR_PIN)


if __name__ == "__main__":
    unittest.main()
