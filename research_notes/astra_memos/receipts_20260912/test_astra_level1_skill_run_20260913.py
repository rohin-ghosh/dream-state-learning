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
PATH = Path("/tmp/astra_level1_skill_run_20260913.py")
spec = importlib.util.spec_from_file_location("level1_runtime_test", PATH)
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
        self.route = None if adapter is None else dict(name="level1_skill", id=1, path=adapter)
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
        temporary = tempfile.TemporaryDirectory(prefix="level1_cpu_", dir="/tmp")
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
        self.original_gpu_state = self.probe.gpu_state
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
             material=record("/tmp/astra_level1_prediction_goal_material_20260913.py"),
             skill="prediction", learner_seed=0, material_seed=0,
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
        return dict(config=self.plan["config"], empty=False, steps=320, micro_batches=320, epochs_run=14, nonfinite_batches=0,
                    corpus=dict(n_items=96, n_encoded=96, n_skipped_no_target=0),
                    truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
                    packing=dict(mode="one_item_per_sequence", n_sequences=96),
                    tokens=dict(target=prepared["target_tokens"], total=prepared["total_tokens"]), train_tokens_seen=prepared["actual_train_tokens"],
                    mean_loss_per_epoch=[.7] * 14, final_loss=.7)

    def fit_fixture(self, stage, write_receipt=True):
        directory = self.root / "run" / stage
        arm = stage.removeprefix("fit_")
        prepared = runtime.read(self.root / "train.json")
        adapter = directory / "adapter"
        adapter.mkdir()
        runtime.write(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05, bias="none",
                                                            target_modules=self.plan["config"]["target_modules"]))
        (adapter / "adapter_model.safetensors").write_text("CPU fake adapter")
        (adapter / "DONE").write_text("CPU fake completion")
        runtime.write(adapter / "train_manifest.json", self.manifest(prepared))
        if write_receipt:
            runtime.write(directory / "fit.json", dict(arm=arm, adapter=str(adapter), adapter_files=runtime.tree(adapter),
                                                      updates=320, presentations=1280, elapsed_seconds=1.0))

    def fake_stage(self, plan, pin, stage, deadline, probe):
        directory = self.root / "run" / stage
        directory.mkdir()
        pid = 90000 + runtime.STAGES.index(stage)
        identity = dict(pid=pid, pgid=pid, stage=stage, plan_sha256=pin)
        runtime.write(directory / "started.json", identity)
        runtime.write(directory / "launch.json", identity)
        if stage == "fit":
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

    def test_prepare_masks_exposure_and_calls(self):
        result = self.prepare()
        self.assertIn("NOT_GPU_APPROVAL", result["status"])
        self.assertEqual(runtime.STAGES, ("OFF", "fit", "post"))
        self.assertEqual(self.plan["config"]["lr"], 3e-4)
        self.assertEqual(self.plan["config"]["max_steps"], 320)
        prepared = runtime.read(self.root / "train.json")
        self.assertEqual(prepared["epochs_run"], 14)
        counts = list(prepared["presentations"].values())
        self.assertEqual((counts.count(13), counts.count(14), sum(counts)), (64, 32, 1280))
        self.assertEqual(len(prepared["actual_batch_order"]), 320)
        for batch in prepared["actual_batch_order"]:
            self.assertEqual(len(set(batch)), 4)
        for row in prepared["encoding"]:
            self.assertEqual([label for label in row["labels"] if label != -100], row["supervised_ids"])
            self.assertEqual(row["supervised_ids"].count(1), 1)
            self.assertEqual(row["labels"][-1], -100)
            self.assertLessEqual(len(row["input_ids"]), 1024)
        self.assertNotEqual(prepared["actual_train_tokens"], 14 * prepared["total_tokens"])
        self.assertGreaterEqual(prepared["actual_padded_tokens"], prepared["actual_train_tokens"])
        calls = runtime.read(self.root / "calls.json")
        self.assertEqual([call["panel"] for call in calls], ["held"] * 48 + ["canary"] * 12)
        self.assertTrue(all("raw_target" not in call and "source_proof" not in call for call in calls))
        self.assertFalse((self.root / "run").exists())

    def test_variable_rows_and_fit_seed_only(self):
        data = runtime.load_material(self.specification).build_dataset("prediction", seed=0)
        orders = []
        for seed in (0, 1, 2):
            for count in (8, 12, 96):
                prepared = runtime.encode_training(data["training"][:count], TokenizerFixture(), self.trainer, self.probe, seed)
                self.assertEqual(sum(prepared["presentations"].values()), 1280)
                self.assertEqual(prepared["epochs_run"], (1280 + count - 1) // count)
            orders.append(prepared["actual_batch_order"])
        self.assertNotEqual(orders[0], orders[1])
        self.assertNotEqual(orders[1], orders[2])
        for invalid in (True, -1, 3, .0):
            with self.assertRaises(ValueError):
                runtime.learner_seed(invalid)

    def test_material_apis_relocation_and_exact_target_scores(self):
        for name in ("prediction_goal", "discrimination"):
            path = f"/tmp/astra_level1_{name}_material_20260913.py"
            specification = dict(self.specification, material=dict(path=path, sha256=runtime.digest(path)))
            with patch.dict(os.environ, ASTRA_LEVEL1_SOURCE_ROOT="/invalid/ambient/source"):
                material = runtime.load_material(specification)
                self.assertEqual(os.environ["ASTRA_LEVEL1_SOURCE_ROOT"], "/invalid/ambient/source")
            for skill in material.SKILLS:
                data = material.build_dataset(skill, seed=0)
                runtime.validate_dataset(data)
                for row in data["training"] + data["evaluation"]["held"] + data["evaluation"]["canary"]:
                    self.assertIs(material.score_row(row, row["raw_target"], "stop")["passed"], True)
                    self.assertIs(material.score_row(row, row["raw_target"], "length")["passed"], False)

    def test_duplicate_source_skin_and_target_drift_rejected(self):
        data = runtime.load_material(self.specification).build_dataset("prediction")
        duplicate = copy.deepcopy(data)
        duplicate["training"][1]["source"] = dict(duplicate["training"][0]["source"], skin_id=99)
        with self.assertRaisesRegex(ValueError, "sources"):
            runtime.validate_dataset(duplicate)
        data["training"][0]["raw_target"] += " "
        with self.assertRaisesRegex(ValueError, "SHA256"):
            runtime.validate_dataset(data)

    def test_truncation_eos_and_padding_fail_closed(self):
        row = runtime.load_material(self.specification).build_dataset("prediction")["training"][0]
        row = copy.deepcopy(row)
        row["input_messages"][-1]["content"] += " many" * 1000
        with self.assertRaisesRegex(ValueError, "truncation"):
            runtime.training_item(row, TokenizerFixture(), self.trainer, self.probe, 0)
        row["input_messages"][-1]["content"] = "short"
        tokenizer = TokenizerFixture()
        tokenizer.trailer = "unexpected tail"
        with self.assertRaises(ValueError):
            runtime.training_item(row, tokenizer, self.trainer, self.probe, 0)
        tokenizer = TokenizerFixture()
        tokenizer.pad_token_id = tokenizer.eos_token_id
        rows = [dict(row, row_id=str(index)) for index in range(4)]
        with self.assertRaisesRegex(ValueError, "PAD/EOS"):
            runtime.encode_training(rows, tokenizer, self.trainer, self.probe)

    def test_complete_one_engine_per_state_collection_once(self):
        self.complete()
        self.assertEqual(len(CaptureFixture.instances), 2)
        self.assertTrue(all(instance.closed and len(instance.seen) == 60 for instance in CaptureFixture.instances))
        self.assertEqual(CaptureFixture.instances[0].seen, CaptureFixture.instances[1].seen)
        self.assertIsNone(CaptureFixture.instances[0].route)
        self.assertEqual(CaptureFixture.instances[1].route["name"], "level1_skill")
        before = runtime.tree(self.root)
        out = self.home / "collection"
        material = runtime.load_material(self.specification)
        def score_fixture(row, raw, finish_reason):
            result = material.score_row(row, raw, finish_reason)
            passed = result["passed"]
            return dict(result, content_correct=passed, strict=passed, format="canonical" if passed else "invalid")
        fixture = SimpleNamespace(build_dataset=material.build_dataset, score_row=score_fixture)
        with patch.object(runtime, "load_material", return_value=fixture):
            runtime.collect(self.root, self.pin, self.completion, out)
        scores = runtime.read(out / "scores.json")
        self.assertEqual(scores["cells"]["OFF"]["held"]["passed"], 48)
        self.assertEqual(scores["cells"]["OFF"]["held"]["content_correct"], 48)
        self.assertEqual(scores["cells"]["OFF"]["held"]["format_counts"], {"canonical": 48})
        self.assertEqual(scores["paired_post_minus_OFF"]["held"], dict(numerator=0, denominator=48))
        self.assertIs(scores["automatic_pass"], False)
        self.assertIsNone(scores["scientific_pass"])
        self.assertEqual(runtime.tree(self.root), before)
        with self.assertRaises(FileExistsError):
            runtime.collect(self.root, self.pin, self.completion, self.home / "second")

    def test_manifest_nonfinite_bool_underfit_and_exposure_rejected(self):
        self.prepare()
        prepared = runtime.read(self.root / "train.json")
        runtime.check_fit_manifest(self.manifest(prepared), prepared, self.plan["config"])
        for key, value in (("steps", True), ("steps", 319), ("final_loss", float("nan")),
                           ("train_tokens_seen", 14 * prepared["total_tokens"]), ("warm_start", {"steps": 80})):
            with self.subTest(key=key):
                manifest = self.manifest(prepared)
                manifest[key] = value
                with self.assertRaises(ValueError):
                    runtime.check_fit_manifest(manifest, prepared, self.plan["config"])

    def test_pin_interpreter_drift_and_fresh_root(self):
        self.prepare()
        with self.assertRaises(ValueError):
            runtime.prepare(**self.kwargs)
        with self.assertRaises(ValueError):
            runtime.verify(self.root, "0" * 64)
        with patch.object(runtime.sys, "executable", "/wrong/interpreter"):
            with self.assertRaises(ValueError):
                runtime.verify(self.root, self.pin)
        protocol = Path(self.specification["protocol"]["path"])
        protocol.write_text("drift")
        with self.assertRaisesRegex(ValueError, "protocol pin"):
            runtime.verify(self.root, self.pin)
        protocol.write_text("CPU protocol fixture; no GPU approval")
        (self.source / "unexpected.py").write_text("drift")
        with self.assertRaisesRegex(ValueError, "snapshot"):
            runtime.verify(self.root, self.pin)

    def test_failure_preserves_partial_captures_never_scores(self):
        self.prepare()
        CaptureFixture.fail_at = 3
        with patch.object(runtime, "run_stage", self.fake_stage):
            with self.assertRaises(RuntimeError):
                runtime.controller(self.root, self.pin, allow_gpu=True)
        self.assertTrue((self.root / "run/OFF/held_02.response.json").exists())
        self.assertTrue(CaptureFixture.instances[0].closed)
        self.assertFalse((self.root / "capture_complete.json").exists())
        with self.assertRaisesRegex(ValueError, "failed controller"):
            runtime.collect(self.root, self.pin, "0" * 64, self.home / "failed_collection")
        self.assertFalse((self.home / "failed_collection/scores.json").exists())
        with self.assertRaises(FileExistsError):
            runtime.controller(self.root, self.pin, allow_gpu=True)

    def test_owned_timeout_cleanup_and_foreign_vacancy(self):
        self.prepare()
        (self.root / "run").mkdir()
        process = Mock(pid=90000)
        process.wait.side_effect = subprocess.TimeoutExpired("CPU fixture", 1)
        with patch.object(self.probe, "gpu_state", return_value=True), patch.object(runtime.subprocess, "Popen", return_value=process), \
             patch.object(self.probe, "cleanup") as cleanup, patch.object(self.probe, "group_alive", return_value=False):
            with self.assertRaises(subprocess.TimeoutExpired):
                runtime.run_stage(self.plan, self.pin, "OFF", time.monotonic() + 1000, self.probe)
            cleanup.assert_called_once_with(process)
        with patch.object(self.probe, "gpu_state", return_value=False), patch.object(self.probe, "cleanup") as cleanup:
            with self.assertRaisesRegex(ValueError, "not vacant"):
                runtime.run_stage(self.plan, self.pin, "fit", time.monotonic() + 1000, self.probe)
            cleanup.assert_not_called()
        self.assertEqual(runtime.GPU_QUERY_SECONDS, 30)

    def test_original_xml_all_process_semantics(self):
        plan = dict(gpu_index=0, gpu_uuid="GPU-CPU-FIXTURE")
        for body, vacant in (("<processes/>", True), ("", False),
                             ("<processes><process_info><type>G</type></process_info></processes>", False),
                             ("<processes><process_info><type>C</type></process_info></processes>", False)):
            response = SimpleNamespace(returncode=0, stdout=f"<nvidia_smi_log><gpu><uuid>GPU-CPU-FIXTURE</uuid>{body}</gpu></nvidia_smi_log>")
            with patch.object(self.probe.subprocess, "run", return_value=response) as query:
                self.assertIs(self.original_gpu_state(plan), vacant)
                self.assertEqual(query.call_args.args[0], ["nvidia-smi", "-i", "0", "-q", "-x"])
                self.assertEqual(query.call_args.kwargs["timeout"], 30)

    def test_cold_fit_uses_unchanged_trainer_with_exact_masks(self):
        self.prepare()
        (self.root / "run/fit").mkdir(parents=True)
        base = SimpleNamespace(named_parameters=lambda: [("layer.lora_A.weight", SimpleNamespace(requires_grad=True))])
        reflection = SimpleNamespace(load_native_model=Mock(return_value=(TokenizerFixture(), base)))
        def train(items, tokenizer, model, config, out, **kwargs):
            self.assertIs(model, base)
            self.assertEqual(len(items), 96)
            self.assertEqual((config.max_steps, config.batch_size, config.seed), (320, 4, 0))
            self.assertNotIn("warm", kwargs)
            self.fit_fixture("fit", write_receipt=False)
        with patch.object(runtime, "load_module", return_value=reflection), patch.object(self.trainer, "run_training", side_effect=train) as training:
            runtime.fit_one(self.plan, "fit", self.probe)
            training.assert_called_once()
        self.assertIn("no parent", runtime.read(self.root / "run/fit/fit.json")["initialized_from"])
        base.peft_config = {}
        with patch.object(runtime, "load_module", return_value=reflection):
            with self.assertRaisesRegex(ValueError, "cold base"):
                runtime.fit_one(self.plan, "fit", self.probe)

    def test_archived_mask_bytes_match_shape_adaptation(self):
        path = SOURCE / "research_notes/astra_memos/receipts_20260912/astra_perception_fit_run_20260913.py"
        archive = runtime.load_module(dict(path=str(path), sha256=runtime.digest(path)), "archive_fixture")
        row = runtime.load_material(self.specification).build_dataset("prediction")["training"][0]
        fixture = dict(row, skill="perception", source_admissible=True,
                       source=dict(source_id="fixture", split="train"))
        _, old = archive.training_item(fixture, TokenizerFixture(), self.trainer, self.probe, 0)
        _, new = runtime.training_item(fixture, TokenizerFixture(), self.trainer, self.probe, 0)
        self.assertEqual(old, new)

    def test_content_primary_format_secondary_without_promotion(self):
        self.complete()
        material = runtime.load_material(self.specification)
        fixture = SimpleNamespace(build_dataset=material.build_dataset,
                     score_row=lambda row, raw, finish_reason: dict(passed=True, content_correct=True, strict=False,
                                                                   format="json_fence", errors=[]))
        out = self.home / "format_collection"
        with patch.object(runtime, "load_material", return_value=fixture):
            runtime.collect(self.root, self.pin, self.completion, out)
        scores = runtime.read(out / "scores.json")
        self.assertEqual(scores["cells"]["post"]["held"]["content_correct"], 48)
        self.assertEqual(scores["cells"]["post"]["held"]["strict"], 0)
        self.assertEqual(scores["cells"]["post"]["held"]["format_counts"], {"json_fence": 48})
        self.assertFalse(scores["automatic_pass"])

    def test_scorer_api_types_and_nonfinite_fail_closed(self):
        valid = dict(passed=True, content_correct=True, strict=False, format="json_fence", errors=[])
        runtime.validate_score(valid, "stop")
        for invalid in (dict(valid, passed=1), dict(valid, content_correct=False), dict(valid, format=None),
                        dict(valid, diagnostic=float("nan")), dict(passed=True, strict=True)):
            with self.assertRaises(ValueError):
                runtime.validate_score(invalid, "stop")
        with self.assertRaises(ValueError):
            runtime.validate_score(valid, "length")


if __name__ == "__main__":
    unittest.main()
