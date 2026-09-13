"""CPU fixtures only: no native/model/remote execution or captured outcome reads."""
import ast
import copy
from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zlib


sys.dont_write_bytecode = True
specification = importlib.util.spec_from_file_location("test_own_replay_repair_runner", "/tmp/astra_own_replay_repair_run_20260913.py")
runner = importlib.util.module_from_spec(specification)
specification.loader.exec_module(runner)
memory = runner.runtime()


@dataclass
class Config:
    model: str = "CPU_MODEL_NOT_NATIVE"
    seed: int = 0
    rank: int = 8
    alpha: int = 16
    dropout: float = .05
    lr: float = 3e-5
    epochs: int = 8
    batch_size: int = 1
    max_steps: int = 0
    note: str = "CPU_FIXTURE"


class Tokenizer:
    chat_template = "CPU_TOKENIZER_NOT_NATIVE"
    eos_token, eos_token_id, pad_token_id = "<|im_end|>", 1, 0

    def encode(self, text, add_special_tokens=False):
        pieces = re.findall(r"<\|im_start\|>|<\|im_end\|>|[A-Za-z_]+|[0-9]+|[^\w\s]|\s", text)
        assert "".join(pieces) == text
        return [1 if piece == self.eos_token else 2 if piece == "<|im_start|>" else zlib.crc32(piece.encode()) + 3 for piece in pieces]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        messages = copy.deepcopy(messages)
        if messages[0]["role"] != "system":
            messages.insert(0, dict(role="system", content="You are a helpful assistant."))
        text = "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


class RunnerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="own_replay_repair_cpu_")
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.root = self.home / "new_pair"
        self.old = self.home / "historical"
        self.old.mkdir()
        self.parent = dict(adapter=str(self.old / "original_adapter"), adapter_files={"original_weights": "pin"})
        self.original = dict(root=str(self.old), parent=self.parent, model="CPU_MODEL_NOT_NATIVE", model_files={"base": "pin"},
                             chat_template="CPU_TEMPLATE", environment={}, source=str(self.home / "frozen_source"), engine={},
                             params={"temperature": 0.0, "max_tokens": 192}, python=os.path.abspath(sys.executable),
                             python_sha256=runner.digest(sys.executable))
        self.rows = [dict(row_id=f"memory_{index:02d}", raw_target=' {"fixture":true} ',
                         target_sha256="raw-pin", input_messages=[{"role": "user", "content": f"cue {index}"}],
                         paraphrase_input_messages=[{"role": "user", "content": f"other cue {index}"}], source={"event": str(index)}) for index in range(14)]
        self.calls = []
        self.cells = {}
        for panel, count in (("exact", 14), ("paraphrase", 14), ("held", 48), ("canary", 12)):
            self.cells[panel] = []
            for index in range(count):
                row_id = self.rows[index]["row_id"] if panel in ("exact", "paraphrase") else f"{panel}_row_{index}"
                self.calls.append(dict(call_id=f"{panel}_{index:02d}", panel=panel, row_id=row_id,
                                       messages=[{"role": "user", "content": f"{panel} {index}"}], native={"prompt_token_ids": [11, index]}))
                base_score = dict(passed=True, strict=True, content_correct=True, production_eligible=True, format="exact")
                score = dict(score=base_score, exact_target_bytes=True) if panel in ("exact", "paraphrase") else base_score
                self.cells[panel].append(dict(row_id=row_id, raw="UNTOUCHED_FIXTURE", finish_reason="stop", response_sha256="fixture",
                                              score=score, cost=dict(prompt_tokens=2, output_tokens=1, generation_seconds=.1)))
        memory.write(self.old / "calls.json", self.calls)
        memory.write(self.old / "dataset.json", dict(rows=self.rows))
        self.source = self.home / "source_pin.py"
        self.source.write_text("fixture_only = True\n")
        (self.old / "collected").mkdir()
        self.collection = self.old / "collected/collection.json"
        memory.write(self.collection, {})
        record = dict(path=str(self.source), sha256=runner.digest(self.source))
        history = dict(root=str(self.old), plan_sha256="p" * 64, completion_sha256="c" * 64,
                       collection=dict(path=str(self.collection), sha256=runner.digest(self.collection)), scores_sha256="s" * 64)
        self.spec = dict(runner_sha256=runner.digest(runner.SELF), runtime=record, lower_runtime=record, capture_runtime=record,
                         core=record, protocol=record, memory_history=history, lower_history=copy.deepcopy(history),
                         capture={**{key: value for key, value in history.items() if key != "scores_sha256"}, "report_sha256": "r" * 64},
                         seed=0, fit_seed=0, gpu_index=6, gpu_uuid="GPU-MOCK-NOT-A-NATIVE-ALLOCATION", expected_boot_id="0" * 36,
                         lease_end=time.time() + 100000)
        self.trainer = SimpleNamespace(TrainConfig=Config, _warm_parent=Mock())
        self.probe = SimpleNamespace(native_tokenizer=Mock(return_value=SimpleNamespace(chat_template="CPU_TEMPLATE")), gpu_state=Mock(return_value=True))
        self.formation = SimpleNamespace(tree=self.tree, validate_response=Mock())
        self.bound = dict(memory_plan=self.original, lower_plan={"configs": {"WRITE": Config().__dict__}}, parent=self.parent,
                          dataset={"rows": self.rows}, retention={}, original_calls=self.calls, admission_report={"admitted_count": 24},
                          mixture={"status": "READY", "seed": 0, "arms": {arm: {"rows": []} for arm in runner.ARMS}},
                          trainer=self.trainer, helper=SimpleNamespace(check_adapter=Mock(side_effect=lambda path, config: self.tree(path))),
                          probe=self.probe, formation=self.formation, repair_core=SimpleNamespace(encode=Mock(side_effect=self.fake_encode)),
                          history={name: copy.deepcopy(self.cells) for name in ("LOWER", "HIGH", "LR0")}, capture={}, kwargs={},
                          memory=SimpleNamespace(score_readback=Mock(return_value={"score": {"content_correct": True, "production_eligible": True}})))
        example = self.manifest(self.prepared_data(), Config().__dict__)
        self.bound["historical_manifests"] = {name: copy.deepcopy(example) for name in ("LOWER", "HIGH", "LR0")}
        self.snapshot_map = {"memory/dataset.json": self.old / "dataset.json", "memory/calls.json": self.old / "calls.json", "sources/core.py": self.source}
        self.api = SimpleNamespace(**vars(memory))
        self.api.offline = Mock()
        self.api.build_calls = Mock(return_value=self.calls)
        self.api.score_calls = Mock(side_effect=lambda plan, bound, arm: copy.deepcopy(self.cells))
        self.api.identity = Mock(return_value=dict(pid=12345, pgid=12345, start_ticks=333))
        self.api.cleanup_owned = Mock()

    def tree(self, path):
        if str(path) == self.parent["adapter"]:
            return self.parent["adapter_files"]
        return {str(item.relative_to(path)): runner.digest(item) for item in sorted(Path(path).rglob("*")) if item.is_file()}

    def prepared_data(self, count=38):
        return dict(items=[{"spans": [["raw", True, "target"]]}] * count, encoding=[{}] * count,
                    epoch_order=[list(range(count)) for _ in range(8)], fit_seed=0, rows=count, updates=8 * count,
                    presentations=8 * count, total_tokens=10 * count, target_tokens=3 * count, context_tokens=7 * count,
                    train_tokens_seen=80 * count, actual_supervised_tokens=24 * count, actual_context_tokens=56 * count,
                    actual_padded_tokens=80 * count, padding_tokens=0)

    def fake_encode(self, mixture, arm, tokenizer, trainer, helper, probe, fit_seed):
        self.assertIn(arm, runner.ARMS)
        result = self.prepared_data(len(self.bound["dataset"]["rows"]) + self.bound["admission_report"]["admitted_count"])
        result["fit_seed"] = fit_seed
        return result

    def manifest(self, prepared, config):
        initial = {"layer.lora_A.weight": {"sha256": "initial", "dtype": "torch.float32", "shape": [1]}}
        final = {"layer.lora_A.weight": {"sha256": "changed", "dtype": "torch.float32", "shape": [1]}}
        return dict(config=config, empty=False, steps=prepared["updates"], micro_batches=prepared["updates"], epochs_run=8,
                    nonfinite_batches=0, corpus=dict(n_items=prepared["rows"], n_encoded=prepared["rows"], n_skipped_no_target=0),
                    truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
                    packing=dict(mode="one_item_per_sequence", n_sequences=prepared["rows"]),
                    tokens=dict(target=prepared["target_tokens"], total=prepared["total_tokens"]), train_tokens_seen=prepared["train_tokens_seen"],
                    mean_loss_per_epoch=[.1] * 8, final_loss=.1,
                    warm_start=dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", optimizer_initialization="fresh_per_write",
                        optimizer_state_restored=False, optimizer_state_saved=False, parent_path=self.parent["adapter"],
                        parent_files=self.parent["adapter_files"], parent_files_after=self.parent["adapter_files"], parent_unchanged=True,
                        initialized_loaded_state_check=True, base_frozen=True, adapter_count=1, trainer_sha256=runner.TRAINER_PIN,
                        phase_seed=config["seed"], phase_steps=prepared["updates"], parent_cumulative_steps=320,
                        cumulative_steps=320 + prepared["updates"], initialized_state=initial, source_state=initial, final_state=final,
                        trainable_names=["layer.lora_A.default.weight"]))

    def prepared(self, replay=24):
        self.bound["admission_report"]["admitted_count"] = replay
        self.bound["mixture"]["status"] = "READY" if replay else "REPLAY_UNAVAILABLE"
        spec_path = self.home / "spec.json"
        memory.write(spec_path, self.spec)
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "bind", return_value=self.bound), \
             patch.object(runner, "allocation"), patch.object(runner, "snapshots", return_value=self.snapshot_map), \
             patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            result = runner.prepare(self.root, spec_path, runner.digest(spec_path), allow_native=True)
        return memory.read(self.root / "plan.json"), result["plan_sha256"]

    def close_stages(self, plan, pin):
        (self.root / "run").mkdir()
        for index, stage in enumerate(plan["stages"]):
            directory = self.root / "run" / stage
            directory.mkdir()
            arm, kind = stage.rsplit("_", 1)
            identity = dict(pid=1000 + index, pgid=1000 + index, start_ticks=100 + index)
            command = [plan["python"], "-B", str(runner.SELF), "worker", "--root", plan["root"], "--plan-sha256", pin,
                       "--stage", stage, "--allow-gpu"]
            memory.write(directory / "launch.json", dict(identity=identity, command=command, stage=stage, plan_sha256=pin, time=10 * index + 1))
            memory.write(directory / "started.json", dict(pid=identity["pid"], pgid=identity["pgid"], stage=stage, plan_sha256=pin, time=10 * index + 2))
            memory.write(directory / "released.json", dict(identity=identity, stage=stage, time=10 * index + 3))
            if kind == "fit":
                adapter = directory / "adapter"
                adapter.mkdir()
                prepared = memory.read(self.root / f"training_{arm}.json")
                manifest = self.manifest(prepared, plan["configs"][arm])
                manifest["corpus"]["sha256"] = plan["input_hashes"][f"training_{arm}.json"]
                memory.write(adapter / "train_manifest.json", manifest)
                (adapter / "weights.bin").write_bytes(b"CPU_MOCK")
                memory.write(directory / "fit.json", dict(arm=arm, adapter=str(adapter), adapter_files=self.tree(adapter),
                             initialized_from=self.parent, updates=prepared["updates"], calls=0,
                             training_sha256=manifest["corpus"]["sha256"], norms=dict(changed_elements=1, l2={"delta": .1})))
            else:
                route = memory.route_for(plan, self.bound, arm)
                memory.write(directory / "identity.json", dict(arm=arm, route=route, model_files=plan["model_files"], parent=plan["parent"], params=plan["params"]))
                memory.write(directory / "readout.json", dict(arm=arm, calls=len(self.calls), updates=0))
                for call in self.calls:
                    memory.write(directory / (call["call_id"] + ".request.json"), dict(call, params=plan["params"], lora_request=route))
                    memory.write(directory / (call["call_id"] + ".response.json"), dict(text="UNCHANGED", finish_reason="stop"))

    def complete(self, plan, pin):
        self.close_stages(plan, pin)
        inventory = runner.validate_completed(self.api, plan, pin, self.bound)
        memory.write(self.root / "capture_complete.json", dict(scope=runner.SCOPE, status=plan["status"], plan_sha256=pin,
                     stages=inventory, fits=plan["limits"]["fits"], calls=plan["limits"]["calls"], updates=plan["limits"]["updates"],
                     scored=False, elapsed_seconds=100))
        return runner.digest(self.root / "capture_complete.json")

    def test_fixed_single_seed_and_global_budgets(self):
        total_updates = total_calls = 0
        for seed, count in enumerate(runner.MEMORY_COUNTS):
            self.bound["dataset"]["rows"] = self.rows[:count]
            self.bound["lower_plan"]["configs"]["WRITE"]["seed"] = seed
            spec = dict(self.spec, seed=seed, fit_seed=seed)
            plan = runner.make_plan(self.root, spec, "pin", self.bound, {}, {})
            self.assertEqual(plan["updates_per_arm"], 8 * (count + 24))
            self.assertEqual(plan["calls_per_arm"], 2 * count + 60)
            self.assertEqual(plan["stages"], list(runner.STAGES))
            self.assertEqual(plan["configs"]["REPLAY"], plan["configs"]["EXTRA_MEMORY"])
            self.assertEqual(plan["configs"]["REPLAY"]["seed"], seed)
            total_updates += plan["limits"]["updates"]
            total_calls += plan["limits"]["calls"]
        self.assertEqual((total_updates, total_calls), (1632, 480))

    def test_prepare_freezes_both_encodings_and_unchanged_calls(self):
        old_bytes = (self.old / "calls.json").read_bytes()
        plan, _ = self.prepared()
        self.assertEqual(set(plan["input_hashes"]), {"mixture.json", "calls.json", "training_REPLAY.json", "training_EXTRA_MEMORY.json"})
        self.assertEqual(self.trainer._warm_parent.call_count, 2)
        self.assertEqual([call.args[1] for call in self.bound["repair_core"].encode.call_args_list], list(runner.ARMS))
        self.assertTrue(all(call.args[0] == self.parent["adapter"] for call in self.trainer._warm_parent.call_args_list))
        self.assertFalse((self.root / "run").exists())
        self.assertEqual(old_bytes, (self.root / "calls.json").read_bytes())
        self.assertEqual(old_bytes, (self.old / "calls.json").read_bytes())

    def test_zero_replay_unavailable_no_fit_no_encoding(self):
        plan, pin = self.prepared(replay=0)
        self.assertEqual(plan["status"], "REPLAY_UNAVAILABLE")
        self.assertEqual(plan["stages"], [])
        self.assertEqual((plan["limits"]["fits"], plan["limits"]["updates"], plan["limits"]["calls"]), (0, 0, 0))
        self.trainer._warm_parent.assert_not_called()
        self.bound["repair_core"].encode.assert_not_called()
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.api, plan, self.bound)), \
             patch.object(runner, "allocation"), patch.object(runner, "run_stage") as run, patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            runner.controller(self.root, pin, allow_gpu=True)
        run.assert_not_called()

    def test_native_flags_required(self):
        with self.assertRaises(ValueError):
            runner.prepare("none", "none", "none")
        with self.assertRaises(ValueError):
            runner.controller("none", "none")
        with self.assertRaises(ValueError):
            runner.worker("none", "none", "LR0_fit", allow_gpu=True)
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES="GPU-UNEXPECTED"), self.assertRaises(ValueError):
            runner.prepare("none", "none", "none", allow_native=True)

    def test_prepare_prompt_drift_failure_preserved(self):
        self.api.build_calls.return_value = self.calls[:-1]
        with self.assertRaisesRegex(ValueError, "prompt/token"):
            self.prepared()
        self.assertTrue((self.root / "prepare_failure.json").exists())
        self.assertFalse((self.root / "plan.json").exists())

    def test_independent_verify_rejects_plan_and_input_drift(self):
        plan, pin = self.prepared()
        with patch.object(runner, "bind", return_value=self.bound), patch.object(runner, "snapshots", return_value=self.snapshot_map):
            runner.verify(self.root, pin)
            bad = copy.deepcopy(plan)
            bad["configs"]["REPLAY"]["lr"] = 1e-4
            (self.root / "plan.json").write_bytes(memory.encoded(bad))
            with self.assertRaisesRegex(ValueError, "independent repair plan"):
                runner.verify(self.root, runner.digest(self.root / "plan.json"))
            (self.root / "plan.json").write_bytes(memory.encoded(plan))
            (self.root / "training_REPLAY.json").write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "immutable input"):
                runner.verify(self.root, pin)

    def test_mixed_fit_bound_allows304_not_old128(self):
        prepared = self.prepared_data()
        manifest = self.manifest(prepared, Config().__dict__)
        for arm in runner.ARMS:
            runner.check_fit(manifest, prepared, Config().__dict__, self.parent, arm, {"memory": 14, "replay": 24})
        with self.assertRaises(ValueError):
            memory.check_fit(manifest, prepared, Config().__dict__, self.parent, "WRITE")
        with self.assertRaises(ValueError):
            runner.check_fit(manifest, prepared, Config().__dict__, self.parent, "REPLAY", {"memory": 14, "replay": 25})

    def test_all_prior_warm_mask_loss_and_step_invariants(self):
        prepared = self.prepared_data()
        baseline = self.manifest(prepared, Config().__dict__)
        changes = [("warm_start", "optimizer_state_restored", True), ("warm_start", "parent_path", "WRITE_DESCENDANT"),
                   ("warm_start", "base_frozen", False), ("warm_start", "adapter_count", 2),
                   ("warm_start", "trainable_names", ["base.weight"]), ("warm_start", "phase_seed", 1),
                   ("warm_start", "parent_cumulative_steps", 432), ("truncation", "target_tokens_dropped", 1),
                   ("corpus", "n_skipped_no_target", 1), ("tokens", "target", 999)]
        for section, key, value in changes:
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                changed = copy.deepcopy(baseline)
                changed[section][key] = value
                runner.check_fit(changed, prepared, Config().__dict__, self.parent, "REPLAY", {"memory": 14, "replay": 24})
        for key, value in (("final_loss", float("nan")), ("steps", 128), ("nonfinite_batches", 1)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.check_fit(dict(baseline, **{key: value}), prepared, Config().__dict__, self.parent, "REPLAY", {"memory": 14, "replay": 24})
        baseline["warm_start"]["final_state"] = baseline["warm_start"]["initialized_state"]
        with self.assertRaisesRegex(ValueError, "parameter change"):
            runner.check_fit(baseline, prepared, Config().__dict__, self.parent, "REPLAY", {"memory": 14, "replay": 24})

    def test_fit_uses_original_parent_and_frozen_new_encoding(self):
        plan, _ = self.prepared()
        directory = self.root / "run/REPLAY_fit"
        directory.mkdir(parents=True)
        self.bound["reflection"] = SimpleNamespace(load_native_model=Mock(return_value=(SimpleNamespace(chat_template="CPU_TEMPLATE"), object())))
        def training(items, tokenizer, base, config, destination, **kwargs):
            self.assertEqual(kwargs["init_adapter"], self.parent["adapter"])
            self.assertEqual(items, self.prepared_data()["items"])
            adapter = Path(destination)
            adapter.mkdir()
            manifest = self.manifest(self.prepared_data(), config.__dict__)
            manifest["corpus"]["sha256"] = kwargs["corpus_sha"]
            memory.write(adapter / "train_manifest.json", manifest)
        self.trainer.run_training = Mock(side_effect=training)
        self.api.tensor_diagnostics = Mock(return_value=dict(changed_elements=1, l2={"delta": .1}))
        runner.fit_arm(self.api, plan, self.bound, "REPLAY")
        self.assertEqual(memory.read(directory / "fit.json")["initialized_from"], self.parent)
        self.trainer.run_training.assert_called_once()
        self.assertIn("REPLAY", self.trainer.run_training.call_args.kwargs["corpus_name"])

    def test_failed_precheck_no_spawn(self):
        plan, pin = self.prepared()
        self.probe.gpu_state.return_value = False
        with patch.object(runner, "allocation"), patch.object(subprocess, "Popen") as spawn, self.assertRaisesRegex(ValueError, "vacancy"):
            runner.run_stage(self.api, plan, pin, "REPLAY_fit", time.monotonic() + 1000, self.bound)
        spawn.assert_not_called()

    def test_launch_uses_reserved_uuid_and_owned_cleanup(self):
        plan, pin = self.prepared()
        (self.root / "run").mkdir()
        process = Mock(pid=12345)
        process.wait.return_value = 0
        with patch.object(runner, "allocation"), patch.object(subprocess, "Popen", return_value=process) as spawn, patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            runner.run_stage(self.api, plan, pin, "REPLAY_fit", time.monotonic() + 1000, self.bound)
        self.assertEqual(spawn.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], plan["gpu_uuid"])
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        self.api.cleanup_owned.assert_called_once()
        self.assertTrue((self.root / "run/REPLAY_fit/released.json").exists())

    def test_failed_worker_and_cleanup_preserve_both(self):
        plan, pin = self.prepared()
        (self.root / "run").mkdir()
        process = Mock(pid=12345)
        process.wait.side_effect = subprocess.TimeoutExpired("fixture", 10)
        self.api.cleanup_owned.side_effect = ValueError("fixture cleanup failure")
        with patch.object(runner, "allocation"), patch.object(subprocess, "Popen", return_value=process), self.assertRaisesRegex(ValueError, "cleanup"):
            runner.run_stage(self.api, plan, pin, "REPLAY_fit", time.monotonic() + 1000, self.bound)
        directory = self.root / "run/REPLAY_fit"
        self.assertTrue((directory / "stage_failure.json").exists())
        self.assertTrue((directory / "cleanup_failure.json").exists())
        self.assertFalse((directory / "released.json").exists())

    def test_four_cold_stages_and_unchanged_evaluation(self):
        plan, pin = self.prepared()
        self.close_stages(plan, pin)
        result = runner.validate_completed(self.api, plan, pin, self.bound)
        self.assertEqual(set(result), set(runner.STAGES))
        self.assertEqual(self.formation.validate_response.call_count, 176)
        for arm in runner.ARMS:
            route = memory.route_for(plan, self.bound, arm)
            self.assertIn(arm + "_fit", route["path"])

    def test_missing_release_or_changed_readout_blocks_completion(self):
        plan, pin = self.prepared()
        self.close_stages(plan, pin)
        release = self.root / "run/REPLAY_fit/released.json"
        before = release.read_bytes()
        release.unlink()
        with self.assertRaises(FileNotFoundError):
            runner.validate_completed(self.api, plan, pin, self.bound)
        release.write_bytes(before)
        request = self.root / "run/REPLAY_readout/exact_00.request.json"
        data = memory.read(request)
        data["messages"][0]["content"] = "WRONG_REPLAY_CONTEXT"
        request.write_bytes(memory.encoded(data))
        with self.assertRaisesRegex(ValueError, "prompt changed"):
            runner.validate_completed(self.api, plan, pin, self.bound)

    def test_controller_runs_declared_order_and_stops_on_failure(self):
        plan, pin = self.prepared()
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.api, plan, self.bound)), \
             patch.object(runner, "allocation"), patch.object(runner, "run_stage", side_effect=ValueError("fixture stop")) as stage, \
             patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), self.assertRaisesRegex(ValueError, "fixture stop"):
            runner.controller(self.root, pin, allow_gpu=True)
        self.assertEqual(stage.call_count, 1)
        self.assertEqual(stage.call_args.args[3], "REPLAY_fit")
        self.assertTrue((self.root / "controller_failure.json").exists())

    def test_collect_once_raw_cells_historical_zero_cost(self):
        plan, pin = self.prepared()
        complete = self.complete(plan, pin)
        output = self.home / "collected"
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.api, plan, self.bound)):
            runner.collect(self.root, pin, complete, output)
            with self.assertRaises(FileExistsError):
                runner.collect(self.root, pin, complete, self.home / "second_collection")
        scores = memory.read(output / "scores.json")
        self.assertEqual(set(scores["cells"]), set(runner.ARMS))
        self.assertEqual(scores["cells"]["REPLAY"]["exact"][0]["raw"], "UNTOUCHED_FIXTURE")
        self.assertEqual(scores["incremental_cost"]["calls"], 176)
        self.assertEqual(scores["incremental_cost"]["updates"], 608)
        self.assertEqual(scores["incremental_cost"]["historical_calls"], 0)
        self.assertEqual(self.api.score_calls.call_count, 2)
        self.assertFalse(scores["automatic_pass"])
        self.assertEqual(scores["best_constant"]["variants"]["exact"]["denominator"], 14)

    def test_unavailable_collection_has_no_fit_or_readout(self):
        plan, pin = self.prepared(replay=0)
        complete = self.complete(plan, pin)
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.api, plan, self.bound)):
            runner.collect(self.root, pin, complete, self.home / "unavailable")
        scores = memory.read(self.home / "unavailable/scores.json")
        self.assertEqual(scores["cells"], {})
        self.assertEqual(scores["fits"], {})
        self.assertEqual(scores["screen"], {})
        self.assertIsNone(scores["best_constant"])
        self.api.score_calls.assert_not_called()

    def test_collection_failure_consumes_claim_no_retry(self):
        plan, pin = self.prepared()
        complete = self.complete(plan, pin)
        self.api.score_calls.side_effect = ValueError("fixture score failure")
        output = self.home / "failed_collection"
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.api, plan, self.bound)), \
             self.assertRaisesRegex(ValueError, "score failure"):
            runner.collect(self.root, pin, complete, output)
        self.assertTrue((output / "collection_failure.json").exists())
        self.assertTrue(self.root.with_name(self.root.name + ".collection_claim.json").exists())

    def test_itemwise_screen_gains_do_not_offset_loss(self):
        cells = copy.deepcopy(self.cells)
        cells["held"][0]["score"]["passed"] = False
        report = runner.screen(0, cells, self.bound["history"]["LR0"])
        self.assertFalse(report["passed"])
        self.assertEqual(report["lr0_correct_regressions"]["held"], ["held_row_0"])
        self.assertEqual(report["threshold"], 8)
        for row in cells["exact"][7:]:
            row["score"]["score"]["production_eligible"] = False
        self.assertFalse(runner.screen(0, cells, self.cells)["passed"])

    def test_frozen_sources_and_no_legacy_fit_calls(self):
        self.assertEqual(runner.digest(memory.SELF), runner.RUNTIME_PIN)
        for filename, checksum in (("astra_memory_lower_lr_run_20260913.py", runner.LOWER_PIN),
                                   ("astra_own_source_replay_capture_20260913.py", runner.CAPTURE_PIN),
                                   ("astra_own_replay_repair_core_20260913.py", runner.CORE_PIN)):
            self.assertEqual(runner.digest(Path("/tmp") / filename), checksum)
        protocol = Path("/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_REPAIR_2026-09-13.md")
        self.assertEqual(runner.digest(protocol), runner.PROTOCOL_PIN)
        tree = ast.parse(runner.SELF.read_text())
        forbidden = {"admit", "collect", "encode_training", "fit_arm", "check_fit", "worker", "controller"}
        calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
        self.assertFalse([func for func in calls if isinstance(func, ast.Attribute) and func.attr in forbidden])
        self.assertNotIn("setattr(", runner.SELF.read_text())

    def test_closed_spec_seed_and_no_extra_recipe_controls(self):
        with patch.object(runner, "pinned"):
            runner.validate_spec(self.spec)
            for change in ({"seed": True}, {"fit_seed": 1}, {"lr": 1e-4}, {"protocol": self.spec["protocol"], "extra": 1}):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    runner.validate_spec(dict(self.spec, **change))
        with self.assertRaises(ValueError):
            runner.pinned(self.spec["protocol"], runner.PROTOCOL_PIN)

    def test_actual_core_encoder_seam_raw_eos_and_duplicate_lineage(self):
        core_path = Path("/tmp/astra_own_replay_repair_core_20260913.py")
        core = memory.load(dict(path=str(core_path), sha256=runner.CORE_PIN), "test_actual_repair_core", runner.CORE_PIN)
        helper = memory.load(dict(path="/tmp/astra_level1_skill_run_20260913.py", sha256=core.HELPER_PIN), "test_actual_repair_helper")
        trainer = memory.load(dict(path="/tmp/astra_level1_real_record_source_20260913_attempt1/organism_v6/train_adapter_v3.py",
                                   sha256=runner.TRAINER_PIN), "test_actual_repair_trainer")
        probe = memory.load(dict(path="/tmp/astra_birth_skill_probe_run_20260913.py", sha256=core.PROBE_PIN), "test_actual_repair_probe")
        memory_rows = copy.deepcopy(self.rows)
        for row in memory_rows:
            row["target_sha256"] = runner.hashlib.sha256(row["raw_target"].encode()).hexdigest()
        replay = []
        for index in range(24):
            row = copy.deepcopy(memory_rows[index % len(memory_rows)])
            row.update(row_id=f"TRAIN_REPLAY_FIXTURE_{index:02d}", source={"source_id": f"TRAIN_ONLY_{index:02d}"},
                       input_messages=[{"role": "user", "content": f"Externally authored TRAIN observation {index}"}])
            replay.append(row)
        parent = dict(self.parent, plan_sha256="CPU_PARENT_PLAN")
        plan = dict(self.original, parent=parent, input_hashes={}, specification={})
        producer = dict(learner_seed=0, adapter=parent["adapter"], adapter_files=parent["adapter_files"], model=plan["model"],
                        model_files=plan["model_files"], parent_plan_sha256=parent["plan_sha256"])
        with patch.object(core, "validate_memory", return_value=memory_rows), \
             patch.object(core, "validated_capture", return_value=(producer, {"admitted": replay, "rejected": []}, {})):
            material = core.build(plan, {}, {}, {}, 0)
        bound = dict(repair_core=core, mixture=material, trainer=trainer, helper=helper, probe=probe)
        for arm in runner.ARMS:
            prepared = runner.encode(bound, arm, Tokenizer(), 0)
            self.assertEqual((prepared["rows"], prepared["updates"]), (38, 304))
            self.assertEqual(prepared["fit_seed"], 0)
            rows = material["arms"][arm]["rows"]
            self.assertEqual(len({row["row_id"] for row in rows}), 38)
            for row, audit, item in zip(rows, prepared["encoding"], prepared["items"], strict=True):
                self.assertEqual(item["spans"][1][0], row["raw_target"])
                self.assertEqual(audit["supervised_ids"][-1], 1)
                self.assertTrue(all(label == -100 for label in audit["labels"][:len(audit["native_prompt"]["prompt_token_ids"])]))
            self.assertEqual(prepared, runner.encode(bound, arm, Tokenizer(), 0))
        self.assertEqual([row["source_row_id"] for row in material["arms"]["EXTRA_MEMORY"]["rows"][14:]],
                         [memory_rows[index % 14]["row_id"] for index in range(24)])
        self.assertEqual(material["arms"]["REPLAY"]["rows"][14]["input_messages"], replay[0]["input_messages"])
        with self.assertRaisesRegex(ValueError, "seed"):
            runner.encode(bound, "REPLAY", Tokenizer(), 1)

    def test_bound_history_capture_raw_join_and_projector_namespace(self):
        memory.write(self.old / "plan.json", self.original)
        lower_root, capture_root = self.home / "lower", self.home / "capture"
        lower_root.mkdir()
        capture_root.mkdir()
        spec = copy.deepcopy(self.spec)
        lower_plan = dict(self.original, root=str(lower_root), specification={"history": spec["memory_history"], "seed": 0},
                          calls_per_arm=88, updates_per_arm=112)
        history = dict(cells={"WRITE": self.cells, "LR0": self.cells},
                       fits={"WRITE": self.bound["historical_manifests"]["HIGH"], "LR0": self.bound["historical_manifests"]["LR0"]})
        lower = SimpleNamespace(SCOPE="MOCK_LOWER", SECONDS=3600, verify=Mock(return_value=(self.api, lower_plan, self.bound, history)),
                                validate_completed=Mock(return_value={"complete": True}), validate_cells=Mock())
        capture_plan = dict(self.original, root=str(capture_root))
        calls, audits, joins = [], [], []
        directory = capture_root / "run/seed0"
        directory.mkdir(parents=True)
        for index in range(24):
            request = dict(request_id=f"request_{index}", input_sha256="input", producer_sha256="parent")
            call = dict(call_id=f"train_{index:02d}", core_request=request)
            calls.append(call)
            response_path = directory / (call["call_id"] + ".response.json")
            request_path = directory / (call["call_id"] + ".request.json")
            memory.write(request_path, request)
            memory.write(response_path, {"text": "  RAW_FIXTURE\n", "finish_reason": "stop"})
            raw = dict(request, raw="  RAW_FIXTURE\n", finish_reason="stop")
            audits.append(dict(response=raw, response_sha256=memory.value_hash(raw)))
            joins.append(dict(request_id=request["request_id"], call_id=call["call_id"], native_request_sha256=runner.digest(request_path),
                              native_response_sha256=runner.digest(response_path), core_response_sha256=memory.value_hash(raw)))
        memory.write(capture_root / "calls_seed0.json", calls)
        admission = {"responses": audits, "admitted_count": 24}
        capture = SimpleNamespace(SCOPE="MOCK_CAPTURE", CONTROLLER_SECONDS=3000,
            verify=Mock(return_value=(capture_plan, {"core": SimpleNamespace(sha=lambda payload: runner.hashlib.sha256(payload).hexdigest(), encoded=memory.encoded)})),
            validate_completed=Mock(return_value={"complete": True}), admission_counts=Mock(return_value={"admitted": 24}))
        for kind, root in (("lower_history", lower_root), ("capture", capture_root)):
            binding = spec[kind]
            binding["root"] = str(root)
            complete = dict(scope=lower.SCOPE if kind == "lower_history" else capture.SCOPE, plan_sha256=binding["plan_sha256"],
                            stages={"complete": True}, elapsed_seconds=100)
            complete.update(dict(scored=False, calls=88, updates=112) if kind == "lower_history" else
                            dict(calls=72, updates=0, fits=0, teacher_calls=0, admitted=False))
            memory.write(root / "capture_complete.json", complete)
            binding["completion_sha256"] = runner.digest(root / "capture_complete.json")
            output = self.home / (kind + "_collected")
            output.mkdir()
            if kind == "lower_history":
                content = dict(seed=0, parent=self.parent, plan_sha256=binding["plan_sha256"], completion_sha256=binding["completion_sha256"],
                    native_capture_custody_checked=True, cells={"WRITE": self.cells}, historical_cells={"HIGH": self.cells, "LR0": self.cells},
                    fits={"WRITE": self.bound["historical_manifests"]["LOWER"]})
                (root / "run/WRITE_fit/adapter").mkdir(parents=True)
                memory.write(root / "run/WRITE_fit/adapter/train_manifest.json", content["fits"]["WRITE"])
                filename, key = "scores.json", "scores_sha256"
            else:
                memory.write(output / "seed0_admission.json", admission)
                content = dict(scope=capture.SCOPE, plan_sha256=binding["plan_sha256"], completion_sha256=binding["completion_sha256"],
                    native_capture_receipts_checked=True, seed_reports={"0": {"path": "seed0_admission.json", "sha256": runner.digest(output / "seed0_admission.json")}},
                    counts={"0": {"admitted": 24}}, native_source_joins={"0": joins})
                filename, key = "replay_report.json", "replay_report_sha256"
            memory.write(output / filename, content)
            checksum = runner.digest(output / filename)
            binding["report_sha256" if kind == "capture" else key] = checksum
            memory.write(output / "collection.json", {key: checksum, "completion_sha256": binding["completion_sha256"]})
            binding["collection"] = {"path": str(output / "collection.json"), "sha256": runner.digest(output / "collection.json")}
            memory.write(root.with_name(root.name + ".collection_claim.json"), dict(plan_sha256=binding["plan_sha256"], out=str(output), retry=False))
        mixture_core = SimpleNamespace(build=Mock(return_value=self.bound["mixture"]))
        self.api.load = Mock(side_effect=lambda record, name, *args: {"own_replay_lower": lower, "own_replay_capture": capture, "own_replay_mixture": mixture_core}[name])
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "validate_spec"):
            bound = runner.bind(spec)
            self.assertIs(bound["memory"], self.bound["memory"])
            self.assertIs(bound["lifecycle"], self.api)
            self.assertEqual(mixture_core.build.call_args.args[3]["scope"], capture.SCOPE)
            changed = directory / "train_00.response.json"
            changed.write_bytes(memory.encoded({"text": "REWRITTEN", "finish_reason": "stop"}))
            with self.assertRaisesRegex(ValueError, "raw child/admission"):
                runner.bind(spec)


if __name__ == "__main__":
    unittest.main()
