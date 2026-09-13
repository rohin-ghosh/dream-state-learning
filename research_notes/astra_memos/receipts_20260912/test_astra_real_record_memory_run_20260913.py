"""CPU vertical slice: pinned projector/encoder and injected native boundaries."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zlib

sys.dont_write_bytecode = True
specification = importlib.util.spec_from_file_location("memory_runner_test", "/tmp/astra_real_record_memory_run_20260913.py")
runner = importlib.util.module_from_spec(specification)
specification.loader.exec_module(runner)


class Tokenizer:
    chat_template = "CPU_FIXTURE_NOT_NATIVE"
    eos_token, eos_token_id, pad_token_id = "<|im_end|>", 1, 0

    def encode(self, text, add_special_tokens=False):
        pieces = re.findall(r"<\|im_start\|>|<\|im_end\|>|[A-Za-z_]+|[0-9]+|[^\w\s]|\s+", text)
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


def scripted_capture(core, dependencies):
    def backend(request):
        if request["kind"] == "wake":
            raw = "PREDICT: T\nACT: TRY 2,5,9"
        else:
            facts = json.loads(re.findall(r"^Observed fields: (.*)$", request["input_messages"][0]["content"], re.MULTILINE)[-1])
            raw = json.dumps({"try": facts["values"], "observed": facts["observed"], "predicted": facts["predicted"],
                              "relation": "matched" if facts["predicted"] == facts["observed"] else "mismatched"})
        return dict(request_id=request["request_id"], state=request["state"], raw=raw, finish_reason="stop")
    return core.run_state("perception_seed0", backend, dependencies=dependencies)


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.memory = runner.load(dict(path="/tmp/astra_real_record_memory_core_20260913.py", sha256=runner.MEMORY_PIN), "test_memory", runner.MEMORY_PIN)
        cls.formation = runner.load(dict(path="/tmp/astra_level1_real_record_run_20260913.py", sha256=runner.FORMATION_PIN), "test_formation", runner.FORMATION_PIN)
        cls.helper = runner.load(dict(path="/tmp/astra_level1_skill_run_20260913.py", sha256=cls.formation.LEVEL1_SHA256), "test_helper")
        cls.probe = runner.load(dict(path="/tmp/astra_birth_skill_probe_run_20260913.py", sha256=cls.formation.PUBLIC_SHA256), "test_probe")
        cls.trainer = runner.load(dict(path="/tmp/astra_level1_real_record_source_20260913_attempt1/organism_v6/train_adapter_v3.py", sha256=runner.TRAINER_PIN), "test_trainer")
        cls.core, cls.dependencies = cls.memory.load_core()
        cls.capture = scripted_capture(cls.core, cls.dependencies)
        cls.dataset = cls.memory.project_capture(cls.capture)
        cls.tokenizer = Tokenizer()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="memory_runner_cpu_")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)

    def prepared(self, rows=None):
        return runner.encode_training(self.dataset["rows"] if rows is None else rows, self.tokenizer, self.trainer,
                                      self.helper, self.probe, 0)

    def manifest(self, prepared, config, parent, arm):
        initial = {"layer.lora_A.weight": dict(sha256="initial", dtype="torch.float32", shape=[1])}
        final = copy.deepcopy(initial)
        if arm == "WRITE":
            final["layer.lora_A.weight"]["sha256"] = "changed"
        return dict(config=config, empty=False, steps=prepared["updates"], micro_batches=prepared["updates"], epochs_run=8,
            nonfinite_batches=0, corpus=dict(n_items=prepared["rows"], n_encoded=prepared["rows"], n_skipped_no_target=0),
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
            packing=dict(mode="one_item_per_sequence", n_sequences=prepared["rows"]),
            tokens=dict(target=prepared["target_tokens"], total=prepared["total_tokens"]), train_tokens_seen=prepared["train_tokens_seen"],
            mean_loss_per_epoch=[.1] * 8, final_loss=.1,
            warm_start=dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", optimizer_initialization="fresh_per_write",
                optimizer_state_restored=False, optimizer_state_saved=False, parent_path=parent["adapter"],
                parent_files=parent["adapter_files"], parent_files_after=parent["adapter_files"], parent_unchanged=True,
                initialized_loaded_state_check=True, base_frozen=True, adapter_count=1, trainer_sha256=runner.TRAINER_PIN,
                phase_seed=config["seed"], phase_steps=prepared["updates"], parent_cumulative_steps=320,
                cumulative_steps=320 + prepared["updates"], initialized_state=initial, source_state=initial, final_state=final,
                trainable_names=["layer.lora_A.default.weight"]))

    def test_exact_raw_target_eos_masks_and_eight_passes(self):
        prepared = self.prepared()
        self.assertEqual(prepared["updates"], 128)
        self.assertEqual(len(prepared["epoch_order"]), 8)
        for row, item, audit in zip(self.dataset["rows"], prepared["items"], prepared["encoding"]):
            self.assertEqual(item["spans"][1][0], row["raw_target"])
            self.assertEqual(audit["supervised_ids"][-1], 1)
            prefix = len(audit["native_prompt"]["prompt_token_ids"])
            self.assertEqual(audit["labels"][:prefix], [-100] * prefix)
            self.assertEqual(audit["labels"][-1], -100)
        self.assertEqual(prepared["actual_padded_tokens"], prepared["train_tokens_seen"])

    def test_actual_count_workloads_no_deduplication(self):
        for count, updates, calls in ((14, 224, 176), (8, 128, 152), (16, 256, 184), (0, 0, 0)):
            prepared = self.prepared(self.dataset["rows"][:count])
            self.assertEqual(2 * prepared["updates"], updates)
            self.assertEqual(2 * (2 * count + 60) if count else 0, calls)
        self.assertLess(len({row["raw_target"] for row in self.dataset["rows"]}), 16)

    def test_paired_configs_only_lr_differs(self):
        configs = [runner.config_for(self.helper, self.trainer, "/fixture", 2, arm) for arm in runner.ARMS]
        self.assertEqual({key for key in configs[0] if configs[0][key] != configs[1][key]}, {"lr"})
        self.assertEqual([config["lr"] for config in configs], [1e-4, 0.0])
        self.assertEqual(configs[0]["batch_size"], 1)

    def test_target_mutation_and_truncation_fail_closed(self):
        rows = copy.deepcopy(self.dataset["rows"][:1])
        rows[0]["raw_target"] += " "
        with self.assertRaisesRegex(ValueError, "target"):
            self.prepared(rows)
        rows = copy.deepcopy(self.dataset["rows"][:1])
        rows[0]["input_messages"][0]["content"] += " long" * 2000
        with self.assertRaisesRegex(ValueError, "truncation"):
            self.prepared(rows)

    def test_fit_manifest_control_and_change_failures(self):
        prepared = self.prepared(self.dataset["rows"][:1])
        parent = dict(adapter="/fixture", adapter_files={"weights": "unchanged"})
        for arm in runner.ARMS:
            config = runner.config_for(self.helper, self.trainer, "/model", 0, arm)
            manifest = self.manifest(prepared, config, parent, arm)
            runner.check_fit(manifest, prepared, config, parent, arm)
            changed = copy.deepcopy(manifest)
            changed["warm_start"]["final_state"] = manifest["warm_start"]["initialized_state"] if arm == "WRITE" else {"wrong": {}}
            with self.assertRaises(ValueError):
                runner.check_fit(changed, prepared, config, parent, arm)
            manifest["nonfinite_batches"] = 1
            with self.assertRaisesRegex(ValueError, "nonfinite"):
                runner.check_fit(manifest, prepared, config, parent, arm)

    def test_source_pins_and_no_native_without_permission(self):
        with self.assertRaisesRegex(ValueError, "pin"):
            runner.load(dict(path="/tmp/astra_real_record_memory_core_20260913.py", sha256="wrong"), "wrong", runner.MEMORY_PIN)
        with self.assertRaisesRegex(ValueError, "allow-native"):
            runner.prepare("missing", "missing", "missing")
        with self.assertRaisesRegex(ValueError, "allow-gpu"):
            runner.controller("missing", "missing")

    def test_original_collector_is_never_called(self):
        import ast
        tree = ast.parse(Path(runner.__file__).read_text())
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "collect" for node in ast.walk(tree)))

    def test_cleanup_refuses_wrong_process_identity(self):
        process = Mock(pid=123)
        process.poll.return_value = None
        probe = Mock()
        with patch.object(runner, "identity", return_value=dict(pid=123, pgid=123, start_ticks=2)):
            with self.assertRaisesRegex(ValueError, "unowned"):
                runner.cleanup_owned(process, dict(pid=123, pgid=123, start_ticks=1), probe)
        probe.cleanup.assert_not_called()

    def test_pair_join_and_denominators(self):
        self.assertEqual(runner.paired_counts({"a": True, "b": False}, {"a": False, "b": True}),
                         dict(total=2, both=0, neither=0, first_only=1, second_only=1))
        with self.assertRaisesRegex(ValueError, "join"):
            runner.paired_counts({"a": True}, {"b": True})

    def test_wrong_record_and_length_do_not_pass_memory(self):
        row = self.dataset["rows"][0]
        changed = json.loads(row["raw_target"])
        changed["observed"] = not changed["observed"]
        for raw, finish in ((json.dumps(changed), "stop"), (row["raw_target"], "length")):
            score = self.memory.score_readback(self.capture, row["row_id"], raw, finish, input_messages=row["input_messages"])
            self.assertFalse(score["score"]["production_eligible"])
            self.assertFalse(score["score"]["content_correct"])
        with self.assertRaisesRegex(ValueError, "cue differs"):
            self.memory.score_readback(self.capture, row["row_id"], row["raw_target"], "stop", input_messages=[dict(role="user", content="other")])

    def test_native_route_and_prefix_drift_rejected(self):
        native = self.probe.render(self.tokenizer, [dict(role="user", content="fixture")])
        route = dict(name="fixture", id=1, path="/adapter")
        request = dict(native=native, params=dict(max_tokens=192))
        response = dict(**native, actual_prompt_token_ids=native["prompt_token_ids"], output_token_ids=[5],
                        text="x", decoded_output="x", finish_reason="stop", stop_reason=1, started=0., ended=1., lora_request=route)
        self.formation.validate_response(request, response, route)
        with self.assertRaisesRegex(ValueError, "route"):
            self.formation.validate_response(request, dict(response, lora_request=None), route)
        with self.assertRaisesRegex(ValueError, "prompt/token"):
            self.formation.validate_response(request, dict(response, actual_prompt_token_ids=[9]), route)

    def test_deadline_failure_prevents_worker_launch(self):
        with patch.object(runner, "check_allocation"), patch.object(runner.time, "monotonic", return_value=100), patch.object(runner.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(ValueError, "budget"):
                runner.run_stage({}, "pin", "WRITE_fit", 110, dict(probe=Mock()))
            launch.assert_not_called()
        self.assertEqual((runner.OUTER_SECONDS, runner.COLLECTION_SECONDS), (3600, 180))

    def test_single_seed_prepare_controller_collect_vertical_slice(self):
        parent_dir = self.home / "parent"
        parent_dir.mkdir()
        (parent_dir / "weights").write_bytes(b"immutable")
        parent = dict(adapter=str(parent_dir), adapter_files=self.formation.tree(parent_dir))
        retention = {"evaluation": {}}
        original_calls = []
        for panel, count in (("held", 48), ("canary", 12)):
            rows = []
            for index in range(count):
                row = dict(row_id=f"{panel}_{index}", input_messages=[dict(role="user", content=f"retention {panel} {index}")], raw_target="ok")
                rows.append(row)
                original_calls.append(dict(call_id=f"{panel}_{index:02d}", panel=panel, row_id=row["row_id"], messages=row["input_messages"],
                                           native=self.probe.render(self.tokenizer, row["input_messages"])))
            retention["evaluation"][panel] = rows
        def material_score(row, raw, finish):
            passed = raw == "ok" and finish == "stop"
            return dict(passed=passed, content_correct=passed, strict=passed, format="exact")
        old_scores = {panel: dict(rows=[dict(row_id=row["row_id"], raw="ok", finish_reason="stop", score=material_score(row, "ok", "stop"))
                                       for row in retention["evaluation"][panel]]) for panel in ("held", "canary")}
        original_collection = self.home / "original_collected"
        original_collection.mkdir()
        runner.write(original_collection / "scores.json", dict(cells=dict(post=old_scores)))
        parent.update(collection=dict(path=str(original_collection / "collection.json")), scores_sha256=runner.digest(original_collection / "scores.json"))
        fake_trainer = SimpleNamespace(**vars(self.trainer))
        fake_trainer._warm_parent = Mock(return_value={})
        config_parent = dict(model="/fixture/model", model_files={"base": "immutable"}, source="/fixture/source", environment={},
                             chat_template=self.tokenizer.chat_template)
        spec = dict(seed=0, fit_seed=0, gpu_index=1, gpu_uuid="GPU-fixture", formation={}, expected_boot_id="fixture", lease_end=10**12)
        bound = dict(formation=self.formation, memory=self.memory, helper=self.helper, trainer=fake_trainer, probe=self.probe,
            reflection=SimpleNamespace(load_native_model=lambda path: (self.tokenizer, SimpleNamespace())),
            material=SimpleNamespace(score_row=material_score), plan=config_parent, parent=parent, capture=self.capture,
            dataset=self.dataset, retention=retention, original_calls=original_calls, kwargs={})
        native_routes = []
        class Backend:
            def __init__(inner, plan, probe, route):
                inner.tokenizer = self.tokenizer
                inner.route = route
                native_routes.append(route["path"])
            def generate(inner, request):
                if request["panel"] in ("exact", "paraphrase"):
                    raw = next(row["raw_target"] for row in self.dataset["rows"] if row["row_id"] == request["row_id"])
                else:
                    raw = "ok"
                return dict(**request["native"], text=raw, decoded_output=raw, output_token_ids=self.tokenizer.encode(raw),
                    actual_prompt_token_ids=request["native"]["prompt_token_ids"], finish_reason="stop", stop_reason=1,
                    lora_request=inner.route, started=1.0, ended=2.0)
        fit_calls = []
        def train(items, tokenizer, base, cfg, out_dir, **kwargs):
            self.assertEqual(kwargs["init_adapter"], parent["adapter"])
            fit_calls.append(kwargs["init_adapter"])
            arm = "WRITE" if cfg.lr else "LR0"
            config = runner.config_for(self.helper, self.trainer, config_parent["model"], 0, arm)
            prepared = runner.read(Path(out_dir).parents[2] / "training.json")
            manifest = self.manifest(prepared, config, parent, arm)
            manifest["corpus"]["sha256"] = kwargs["corpus_sha"]
            Path(out_dir).mkdir()
            runner.write(Path(out_dir) / "train_manifest.json", manifest)
            runner.write(Path(out_dir) / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05,
                         target_modules=config["target_modules"], bias="none"))
            (Path(out_dir) / "DONE").write_bytes(b"ok")
            (Path(out_dir) / "adapter_model.safetensors").write_bytes(arm.encode())
        fake_trainer.run_training = train
        def fake_stage(plan, pin, stage, deadline, bound):
            directory = Path(plan["root"]) / "run" / stage
            directory.mkdir()
            process = dict(pid=100 + runner.STAGES.index(stage), pgid=100 + runner.STAGES.index(stage), start_ticks=1000)
            runner.write(directory / "launch.json", dict(identity=process, stage=stage, plan_sha256=pin))
            runner.write(directory / "started.json", dict(pid=process["pid"], pgid=process["pgid"], stage=stage, plan_sha256=pin))
            arm, operation = stage.split("_")
            if operation == "fit":
                runner.fit_arm(plan, bound, arm)
            else:
                runner.capture_readout(plan, bound, arm, Backend)
            runner.write(directory / "released.json", dict(identity=process, stage=stage))
        spec_path = self.home / "spec.json"
        runner.write(spec_path, spec)
        root = self.home / "run"
        def norms(trainer, parent, adapter, manifest):
            changed = "WRITE_fit" in str(adapter)
            return dict(changed_elements=int(changed), l2=dict(initial=1., final=1., delta=float(changed)))
        with patch.object(runner, "bind_inputs", return_value=bound), patch.object(runner, "protected_inputs", return_value=[parent_dir]), \
             patch.object(runner, "check_allocation"), patch.object(runner, "run_stage", side_effect=fake_stage), \
             patch.object(runner, "tensor_diagnostics", side_effect=norms), patch.object(self.probe, "native_tokenizer", return_value=self.tokenizer), \
             patch.dict(runner.os.environ, CUDA_VISIBLE_DEVICES=""):
            prepared = runner.prepare(str(root), str(spec_path), runner.digest(spec_path), True)
            self.assertEqual((prepared["calls"], prepared["updates"]), (184, 256))
            completed = runner.controller(str(root), prepared["plan_sha256"], True)
            result = runner.collect(str(root), prepared["plan_sha256"], completed["completion_sha256"], str(self.home / "collected"))
            report = runner.read(Path(result["out"]) / "scores.json")
            self.assertEqual(report["summary"]["totals"]["WRITE"]["exact"]["numerators"]["production_eligible"], 16)
            self.assertEqual(report["summary"]["paired_WRITE_LR0"]["held"]["passed"]["both"], 48)
            self.assertEqual(len(report["summary"]["original_retention"]["LR0"]["held"]["retained"]), 48)
            with self.assertRaises(FileExistsError):
                runner.collect(str(root), prepared["plan_sha256"], completed["completion_sha256"], str(self.home / "second_collection"))
        self.assertEqual(fit_calls, [parent["adapter"], parent["adapter"]])
        self.assertEqual(len(set(native_routes)), 2)
        self.assertEqual(self.formation.tree(parent_dir), parent["adapter_files"])


if __name__ == "__main__":
    unittest.main()
