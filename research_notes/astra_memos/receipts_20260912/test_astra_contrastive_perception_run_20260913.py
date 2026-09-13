"""CPU fixtures only; actual pinned encoder/scorer, mocked tokenizer/model/processes."""
from collections import UserDict
import copy
from dataclasses import asdict
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
SOURCE = Path("/data/home/rohing/dream-state")
PATH = Path("/tmp/astra_contrastive_perception_run_20260913.py")
spec = importlib.util.spec_from_file_location("contrastive_runtime_test", PATH)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

class TokenizerFixture:
    chat_template = "CPU_QWEN_SHAPED_FULL_ASSISTANT_TEMPLATE"
    eos_token = "<|im_end|>"
    eos_token_id = 1
    pad_token_id = 0
    as_mapping = True
    trailer = "\n"

    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        words = re.findall(r"<\|im_start\|>|<\|im_end\|>|[A-Za-z_]+|[0-9]+|[^\w\s]|\s+", text)
        assert "".join(words) == text
        return [1 if word == self.eos_token else 2 if word == "<|im_start|>" else zlib.crc32(word.encode()) + 3 for word in words]

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        messages = copy.deepcopy(messages)
        if messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": "Fixture generic system."})
        text = "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        elif self.trailer != "\n":
            text = text[:-1] + self.trailer
        if not tokenize:
            return text
        ids = self.encode(text, add_special_tokens=False)
        return UserDict(input_ids=ids) if self.as_mapping else ids

class CaptureFixture:
    instances = []
    answers = {}
    fail_at = None
    corrupt_route = False
    corrupt_input = False
    raw_text = None

    def __init__(self, plan, probe, adapter):
        self.seen = []
        self.closed = False
        self.probe = probe
        self.route = None if adapter is None else dict(name="perception", id=1, path=adapter)
        self.instances.append(self)

    def generate(self, messages):
        if self.fail_at is not None and len(self.seen) == self.fail_at:
            raise RuntimeError("fixture generation failure")
        self.seen.append(copy.deepcopy(messages))
        native = self.probe.render(TokenizerFixture(), messages)
        text = self.raw_text if self.raw_text is not None else self.answers[messages[-1]["content"]]
        ids = TokenizerFixture().encode(text)
        response = dict(**native, text=text, output_token_ids=ids,
                        actual_prompt_token_ids=native["prompt_token_ids"], finish_reason="stop", stop_reason=1,
                        decoded_output=text, started=1.0, ended=2.0,
                        lora_request={"wrong": "adapter"} if self.corrupt_route else self.route)
        if self.corrupt_input:
            response["actual_prompt_token_ids"] = [999]
        return response

    def close(self):
        self.closed = True

class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus, cls.trainer = runtime.source_api(SOURCE)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="contrastive_cpu_", dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / "root"
        self.source = self.home / "source"
        for name in runtime.SOURCE_NAMES:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((SOURCE / name).read_bytes())
        self.model = self.home / "model"
        self.model.mkdir()
        self.probe = runtime.load_probe("/tmp/astra_birth_skill_probe_run_20260913.py",
                                        runtime.digest("/tmp/astra_birth_skill_probe_run_20260913.py"))
        self.patch(runtime, "source_api", return_value=(self.corpus, self.trainer))
        original_probe_loader = runtime.load_probe
        def probe_loader(path, expected):
            runtime.require(runtime.digest(path) == expected, "probe pin differs")
            return self.probe
        self.patch(runtime, "load_probe", side_effect=probe_loader)
        self.model_files = {"fixture.safetensors": "a" * 64}
        self.environment = {"CPU_fixture": True}
        self.patch(self.probe, "model_hashes", return_value=self.model_files)
        self.patch(self.probe, "native_environment", return_value=self.environment)
        self.patch(self.probe, "native_tokenizer", return_value=TokenizerFixture())
        self.patch(runtime, "environment", return_value=self.environment)
        self.patch(self.probe, "gpu_state", side_effect=AssertionError("unexpected actual allocation check"))
        self.patch(runtime.subprocess, "Popen", side_effect=AssertionError("unexpected actual process"))
        envpatch = patch.dict(os.environ)
        envpatch.start()
        self.addCleanup(envpatch.stop)
        binding = dict(schema=1, scope=self.probe.SCOPE, visibility="model-only-public", approved_by="Main",
                       model_name=self.probe.MODEL_NAME, revision=self.probe.REVISION,
                       model_files=self.model_files, native_environment=self.environment,
                       source_files={name: runtime.digest(self.source / name) for name in self.probe.SOURCE_NAMES})
        binding_path = self.home / "binding.json"
        protocol_path = self.home / "protocol.md"
        runtime.write(binding_path, binding)
        protocol_path.write_text("CPU protocol fixture; no GPU approval")
        def record(path):
            return dict(path=str(path), sha256=runtime.digest(path))
        self.specification = dict(source=str(self.source), model=str(self.model),
             source_files=runtime.tree(self.source), runner_sha256=runtime.digest(PATH),
             material=record("/tmp/astra_contrastive_perception_material_20260913.py"),
             encoder=record(SOURCE / "research_notes/astra_memos/receipts_20260912/astra_perception_fit_run_20260913.py"),
             reflection=record("/tmp/astra_reflection_fit_run_20260913.py"),
             public=record("/tmp/astra_birth_skill_probe_run_20260913.py"),
             protocol=record(protocol_path), binding=record(binding_path),
             gpu_index=1, gpu_uuid="GPU-00000000-0000-0000-0000-000000000001", lease_end=time.time() + 40000)
        self.spec_path = self.home / "spec.json"
        runtime.write(self.spec_path, self.specification)
        self.kwargs = dict(root=self.root, spec_path=self.spec_path, spec_sha256=runtime.digest(self.spec_path), allow_native=True)
        CaptureFixture.instances = []
        CaptureFixture.answers = {}
        CaptureFixture.fail_at = None
        CaptureFixture.corrupt_route = False
        CaptureFixture.corrupt_input = False
        CaptureFixture.raw_text = None

    def patch(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def prepare(self):
        result = runtime.prepare(**self.kwargs)
        self.pin = result["plan_sha256"]
        self.plan, _ = runtime.verify(self.root, self.pin)
        self.dataset = runtime.read(self.root / "material.json")
        CaptureFixture.answers = {row["input_messages"][-1]["content"]: row["raw_target"]
                                  for rows in self.dataset["evaluation"].values() for row in rows}
        return result

    def manifest(self, prepared):
        return dict(config=self.plan["config"], empty=False, steps=12, micro_batches=12, epochs_run=4, nonfinite_batches=0,
                    corpus=dict(n_items=12, n_encoded=12, n_skipped_no_target=0),
                    truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
                    packing=dict(mode="one_item_per_sequence", n_sequences=12),
                    tokens=dict(target=prepared["target_tokens"]), train_tokens_seen=4 * prepared["total_tokens"],
                    mean_loss_per_epoch=[1.0, .9, .8, .7], final_loss=.7)

    def fit_fixture(self, stage, write_receipt=True):
        directory = self.root / "run" / stage
        arm = stage.removeprefix("fit_")
        prepared = runtime.read(self.root / f"train_{arm}.json")
        adapter = directory / "adapter"
        adapter.mkdir()
        runtime.write(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05, bias="none",
                                                            target_modules=self.plan["config"]["target_modules"]))
        (adapter / "adapter_model.safetensors").write_text("CPU fake adapter")
        (adapter / "DONE").write_text("CPU fake completion")
        runtime.write(adapter / "train_manifest.json", self.manifest(prepared))
        if write_receipt:
            runtime.write(directory / "fit.json", dict(arm=arm, adapter=str(adapter), adapter_files=runtime.tree(adapter),
                                                      updates=12, presentations=48, elapsed_seconds=1.0))

    def fake_stage(self, plan, pin, stage, deadline, probe):
        directory = self.root / "run" / stage
        directory.mkdir()
        pid = 90000 + runtime.STAGES.index(stage)
        identity = dict(pid=pid, pgid=pid, stage=stage, plan_sha256=pin)
        runtime.write(directory / "started.json", identity)
        runtime.write(directory / "launch.json", identity)
        if stage.startswith("fit_"):
            self.fit_fixture(stage)
        else:
            with patch.object(runtime, "Native", CaptureFixture):
                runtime.capture_cell(plan, stage, probe)
        runtime.write(directory / "released.json", dict(pid=pid, pgid=pid))

    def complete(self):
        self.prepare()
        with patch.object(runtime, "run_stage", self.fake_stage):
            result = runtime.controller(self.root, self.pin, allow_gpu=True)
        self.completion = result["completion_sha256"]
        return result

    def test_native_preflight_exact_archived_encoder_and_unequal_context(self):
        result = self.prepare()
        self.assertIn("NOT_GPU_APPROVAL", result["status"])
        self.assertEqual(runtime.digest(self.root / "material.json"), runtime.MATERIAL_DATA_SHA256)
        self.assertEqual(len(runtime.STAGES), 14)
        self.assertEqual(self.plan["config"], asdict(self.trainer.TrainConfig(**runtime.RECIPE, model=str(self.model))))
        plain = runtime.read(self.root / "train_plain.json")
        contrast = runtime.read(self.root / "train_contrastive.json")
        self.assertEqual(plain["epoch_order"], contrast["epoch_order"])
        self.assertEqual([row["supervised_ids"] for row in plain["encoding"]], [row["supervised_ids"] for row in contrast["encoding"]])
        self.assertNotEqual(plain["total_tokens"], contrast["total_tokens"])
        for train in (plain, contrast):
            for row in train["encoding"]:
                self.assertEqual([label for label in row["labels"] if label != -100], row["supervised_ids"])
                self.assertEqual(row["supervised_ids"].count(1), 1)
                self.assertEqual(row["labels"][-1], -100)
                self.assertLessEqual(len(row["input_ids"]), 1024)
        calls = runtime.read(self.root / "calls.json")
        self.assertEqual(sum(map(len, calls.values())), 48)
        for panel in calls.values():
            for call in panel:
                self.assertEqual(set(call), {"call_id", "row_id", "messages", "native"})
                self.assertNotIn("raw_target", call)
        self.assertFalse((self.root / "run").exists())

    def test_preflight_truncation_fails_without_retry_or_gpu(self):
        self.probe.native_tokenizer.return_value = TokenizerFixture()
        self.probe.native_tokenizer.return_value.encode = lambda text, add_special_tokens=False: list(text.encode())
        with self.assertRaises(ValueError):
            runtime.prepare(**self.kwargs)
        self.assertTrue((self.root / "prepare_failure.json").exists())
        self.assertFalse((self.root / "plan.json").exists())
        with self.assertRaisesRegex(ValueError, "fresh root"):
            runtime.prepare(**self.kwargs)

    def test_explicit_native_and_gpu_opt_in(self):
        self.kwargs["allow_native"] = False
        with self.assertRaises(ValueError):
            runtime.prepare(**self.kwargs)
        self.assertFalse(self.root.exists())
        with self.assertRaises(ValueError):
            runtime.controller(self.root, "0" * 64)

    def test_pins_interpreter_prepared_data_and_protocol(self):
        self.prepare()
        with patch.object(runtime.sys, "executable", "/wrong/python"), self.assertRaises(ValueError):
            runtime.verify(self.root, self.pin)
        protocol = Path(self.specification["protocol"]["path"])
        protocol.write_text("changed")
        with self.assertRaisesRegex(ValueError, "protocol pin"):
            runtime.verify(self.root, self.pin)
        protocol.write_text("CPU protocol fixture; no GPU approval")
        (self.root / "calls.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "prepared input"):
            runtime.verify(self.root, self.pin)

    def test_fourteen_fresh_processes_all_raw_before_scoring_and_collect_once(self):
        self.complete()
        self.assertEqual(len(CaptureFixture.instances), 12)
        self.assertTrue(all(len(backend.seen) == 12 and backend.closed for backend in CaptureFixture.instances))
        self.assertEqual(sum(backend.route is None for backend in CaptureFixture.instances), 4)
        before = runtime.tree(self.root)
        output = self.home / "collection"
        runtime.collect(self.root, self.pin, self.completion, output)
        self.assertEqual(before, runtime.tree(self.root))
        scores = runtime.read(output / "scores.json")
        self.assertEqual(scores["calls"], 144)
        self.assertFalse(scores["automatic_pass"])
        self.assertIsNone(scores["scientific_pass"])
        self.assertEqual(set(scores["material_scores"]["states"]), set(runtime.STATES))
        self.assertTrue(scores["material_scores"]["ceiling_limited"])
        self.assertFalse(scores["material_scores"]["exploratory_screen_pass"])
        with self.assertRaises(FileExistsError):
            runtime.collect(self.root, self.pin, self.completion, self.home / "second_collection")

    def test_native_response_tamper_prevents_scoring(self):
        self.complete()
        response = self.root / "run" / runtime.CELLS[-1] / "00.response.json"
        response.write_text("{}")
        with self.assertRaises(ValueError):
            runtime.collect(self.root, self.pin, self.completion, self.home / "out")

    def test_fit_contract_rejects_nonfinite_loss_truncation_update_drift(self):
        self.prepare()
        prepared = runtime.read(self.root / "train_plain.json")
        for field, value in (("steps", 11), ("final_loss", float("nan")), ("train_tokens_seen", 0)):
            manifest = self.manifest(prepared)
            manifest[field] = value
            with self.assertRaises(ValueError):
                runtime.check_fit_manifest(manifest, prepared, self.plan["config"])
        manifest = self.manifest(prepared)
        manifest["truncation"]["items_truncated"] = 1
        with self.assertRaises(ValueError):
            runtime.check_fit_manifest(manifest, prepared, self.plan["config"])

    def test_timeout_cleanup_owned_only_no_followup_stage(self):
        self.prepare()
        process = Mock(pid=123456)
        process.wait.side_effect = subprocess.TimeoutExpired("CPU worker", 1)
        with patch.object(runtime.subprocess, "Popen", return_value=process), \
             patch.object(self.probe, "gpu_state", return_value=True) as vacancy, \
             patch.object(self.probe, "cleanup", return_value=True) as cleanup, \
             patch.object(self.probe, "group_alive", return_value=False):
            with self.assertRaises(subprocess.TimeoutExpired):
                runtime.controller(self.root, self.pin, allow_gpu=True)
        cleanup.assert_called_once_with(process)
        self.assertEqual(vacancy.call_count, 2)
        self.assertTrue((self.root / "controller_failure.json").exists())
        self.assertFalse((self.root / "capture_complete.json").exists())
        self.assertFalse((self.root / "run" / "fit_contrastive").exists())

    def test_occupied_gpu_never_spawns_or_kills_foreign_process(self):
        self.prepare()
        with patch.object(self.probe, "gpu_state", return_value=False), \
             patch.object(self.probe, "cleanup") as cleanup:
            with self.assertRaisesRegex(ValueError, "not vacant"):
                runtime.controller(self.root, self.pin, allow_gpu=True)
        cleanup.assert_not_called()
        runtime.subprocess.Popen.assert_not_called()

    def test_two_cold_fits_receive_only_their_own_training_items(self):
        self.prepare()
        (self.root / "run").mkdir()
        loaded, trained = [], []
        def loader(model):
            base = SimpleNamespace(named_parameters=lambda: [("layer.lora_A.weight", SimpleNamespace(requires_grad=True))])
            loaded.append(base)
            return TokenizerFixture(), base
        def train(items, tokenizer, base, config, adapter, **kwargs):
            stage = Path(adapter).parent.name
            prepared = runtime.read(self.root / ("train_" + stage.removeprefix("fit_") + ".json"))
            self.assertEqual(items, prepared["items"])
            trained.append(base)
            self.fit_fixture(stage, write_receipt=False)
        reflection = SimpleNamespace(load_native_model=loader)
        with patch.object(runtime, "load_module", return_value=reflection), patch.object(self.trainer, "run_training", side_effect=train):
            for stage in runtime.STAGES[:2]:
                (self.root / "run" / stage).mkdir()
                runtime.fit_one(self.plan, stage, self.probe)
        self.assertEqual(len(loaded), 2)
        self.assertIsNot(loaded[0], loaded[1])
        self.assertEqual(loaded, trained)


if __name__ == "__main__":
    unittest.main()
