"""CPU fixtures only; no corpus import/freeze, native tokenizer, model, GPU or network.

Exercises the real pinned-runner mechanics and existing trainer's pure encoding
functions against synthetic source/export records and a fake chat tokenizer.
"""
from collections import UserDict
import contextlib
import copy
from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zlib

sys.dont_write_bytecode = True
PATH = Path(os.environ.get("REFLECTION_DRIVER", "/tmp/astra_reflection_fit_run_20260913.py"))
PROBE_PATH = Path(os.environ.get("REFLECTION_PUBLIC_HELPER", "/tmp/astra_birth_skill_probe_run_20260913.py"))
TRAINER_PATH = Path(os.environ.get("REFLECTION_TRAINER", "/data/home/rohing/dream-state/organism_v6/train_adapter_v3.py"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runtime = load("reflection_runtime_cpu", PATH)


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
        self.route = None if adapter is None else dict(name="reflection", id=1, path=adapter)
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


class CorpusFixture:
    def build_panel(self, panel, *, split, parent_condition):
        assert panel in runtime.PANELS
        assert split in ("train", "dev") and not (panel == "application" and split == "train")
        rows = []
        for index in range(12):
            source_id = f"{panel}-{split}-{index}"
            correction = "\nPUBLIC_CORRECTION\n" if parent_condition == "present" else "\n"
            user = f"Public event {source_id}." + correction + "Describe the supported procedure."
            target = ("A" if index % 2 == 0 else "B") if panel == "application" else f"Authored {split} response {index}. Keep observations separate."
            messages = [dict(role="system", content=runtime.GENERIC_SYSTEM), dict(role="user", content=user)]
            source = dict(source_id=source_id, split=split, template_id=panel + "-" + split,
                          events=[dict(raw_response="ACT " + source_id, raw_outcome="Outcome " + source_id)])
            rows.append(dict(row_id=source_id, panel=panel, split=split, parent_condition=parent_condition,
                             source=source, source_proof={"fixture": True}, input_messages=messages,
                             response_target=target, input_sha256=runtime.value_hash(messages),
                             target_sha256=hashlib.sha256(target.encode()).hexdigest()))
        return dict(schema="birth_reflection_probe_v1", rows=rows, manifest=dict(panel=panel, split=split))

    def export_training(self, built):
        return dict(records=[dict(input_messages=row["input_messages"], response_target=row["response_target"])
                             for row in built["rows"]], report=dict(application_rows=0, dev_rows=0))

    def export_development(self, built):
        return dict(requests=[dict(input_messages=row["input_messages"]) for row in built["rows"]],
                    scoring_rows=built["rows"], report=dict(training_allowed=False))

    def score_response(self, row, raw_response):
        if row["panel"] == "application":
            return dict(score_kind="strict_application_choice", syntax_valid=raw_response in ("A", "B"),
                        passed=raw_response == row["response_target"], raw_response=raw_response)
        return dict(score_kind="exact_authored_restatement_only", passed=raw_response == row["response_target"],
                    raw_response=raw_response, semantic_prose_score=None)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="reflection_cpu_", dir="/tmp")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.root = self.home / "run"
        self.model = self.home / "model"
        self.model.mkdir()
        self.source = self.home / "final-source-fixture"
        for name in runtime.SOURCE_NAMES:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('"""CPU synthetic source placeholder; not the authored corpus."""\n')
        self.pins = runtime.tree(self.source)
        self.pins_path = self.home / "final-pins.json"
        runtime.write(self.pins_path, self.pins)
        self.probe_hash = runtime.digest(PROBE_PATH)
        self.probe = runtime.load_probe(PROBE_PATH, self.probe_hash)
        self.corpus = CorpusFixture()
        self.trainer = load("reflection_fixture_trainer", TRAINER_PATH)
        self.model_files = {"config.json": "a" * 64, "fixture.safetensors": "b" * 64}
        self.fixture_environment = {"cpu_fixture": True}
        self.binding = dict(schema=1, scope=self.probe.SCOPE, visibility="model-only-public", approved_by="Main",
                            model_name=self.probe.MODEL_NAME, revision=self.probe.REVISION,
                            model_files=self.model_files, native_environment=self.fixture_environment,
                            source_files={name: self.pins[name] for name in self.probe.SOURCE_NAMES})
        self.binding_path = self.home / "binding.json"
        runtime.write(self.binding_path, self.binding)
        def pinned_probe(path, expected):
            runtime.require(runtime.digest(path) == expected, "public helper final driver hash differs")
            return self.probe
        self.patch(runtime, "load_probe", pinned_probe)
        self.patch(runtime, "source_api", lambda source: (self.corpus, self.trainer))
        self.patch(runtime, "environment", lambda probe: self.fixture_environment)
        self.patch(self.probe, "native_environment", lambda: self.fixture_environment)
        self.patch(self.probe, "model_hashes", lambda model: self.model_files)
        self.patch(self.probe, "native_tokenizer", lambda model: TokenizerFixture())
        self.kwargs = dict(root=self.root, source=self.source, model=self.model, probe_driver=PROBE_PATH,
                           probe_sha256=self.probe_hash, binding_path=self.binding_path,
                           binding_sha256=runtime.digest(self.binding_path),
                           corpus_sha256=self.pins["organism_v6/birth_skill_corpus.py"],
                           reflection_sha256=self.pins["organism_v6/birth_reflection_probe.py"],
                           source_pins_path=self.pins_path, source_pins_sha256=runtime.digest(self.pins_path),
                           log_dir=self.home / "fresh-logs", gpu_uuid="GPU-00000000-0000-0000-0000-000000000001",
                           gpu_index=0, lease_end=time.time() + 7200)
        CaptureFixture.instances = []
        CaptureFixture.answers = {}
        CaptureFixture.fail_at = None
        CaptureFixture.corrupt_route = False
        CaptureFixture.corrupt_input = False
        CaptureFixture.raw_text = None

    def prepare(self):
        result = runtime.prepare(**self.kwargs)
        self.pin = result["plan_sha256"]
        self.plan, _ = runtime.verify(self.root, self.pin)
        dev = runtime.read(self.root / "dev.json")
        CaptureFixture.answers = {row["input_messages"][-1]["content"]: row["response_target"]
                                  for arm in runtime.ARMS for row in dev[arm]}
        return result

    def row(self, panel="restatement", split="train"):
        return self.corpus.build_panel(panel, split=split, parent_condition="withdrawn")["rows"][0]


    def patch(self, target, name, replacement):
        patcher = patch.object(target, name, replacement)
        patcher.start()
        self.addCleanup(patcher.stop)


    def manifest(self, prepared):
        return dict(config=self.plan["config"], empty=False, steps=12, micro_batches=12, epochs_run=4, nonfinite_batches=0,
                    corpus=dict(n_items=12, n_encoded=12, n_skipped_no_target=0),
                    truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
                    packing=dict(mode="one_item_per_sequence", n_sequences=12),
                    tokens=dict(target=prepared["target_tokens"], total=prepared["total_tokens"],
                                context=prepared["total_tokens"] - prepared["target_tokens"],
                                target_by_category={"authored_restatement": prepared["authored_target_tokens"], "assistant_end": 12},
                                target_by_view={"restatement": prepared["target_tokens"]}),
                    train_tokens_seen=4 * prepared["total_tokens"],
                    mean_loss_per_epoch=[1.0, .9, .8, .7], final_loss=.7)


    def fit_fixture(self, stage):
        directory = self.root / "run" / stage
        arm = stage.removeprefix("fit_")
        prepared = runtime.read(self.root / f"train_{arm}.json")
        adapter = directory / "adapter"
        adapter.mkdir()
        runtime.write(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05, bias="none",
                                                            target_modules=self.plan["config"]["target_modules"]))
        (adapter / "adapter_model.safetensors").write_text("CPU fixture only: not a model or actual weights")
        (adapter / "DONE").write_text("ok\n")
        runtime.write(adapter / "train_manifest.json", self.manifest(prepared))
        runtime.write(directory / "fit.json", dict(arm=arm, adapter=str(adapter), adapter_files=runtime.tree(adapter),
                                                   updates=12, presentations=48))


    def fake_stage(self, plan, pin, stage, deadline, probe):
        directory = self.root / "run" / stage
        directory.mkdir()
        logs = Path(plan["log_dir"]) / stage
        logs.mkdir()
        (logs / "stdout.log").write_text("CPU stdout fixture\n")
        (logs / "stderr.log").write_text("")
        pid = 80000 + runtime.STAGES.index(stage)
        identity = dict(pid=pid, pgid=pid, stage=stage, plan_sha256=pin)
        runtime.write(directory / "started.json", dict(identity, time=time.time()))
        runtime.write(directory / "launch.json", identity)
        if stage.startswith("fit_"):
            self.fit_fixture(stage)
        else:
            with patch.object(runtime, "Native", CaptureFixture):
                runtime.capture_cell(plan, stage, probe)
        runtime.write(directory / "released.json", dict(pid=pid, pgid=pid, time=time.time()))


    def complete(self):
        self.prepare()
        with patch.object(runtime, "run_stage", self.fake_stage):
            result = runtime.controller(self.root, self.pin, allow_gpu=True)
        self.completion = result["completion_sha256"]
        return result


    def test_token_vector_accepts_mapping_and_rejects_nested_bool_empty(self):
        self.assertEqual(runtime.token_ids(UserDict(input_ids=[1, 2])), [1, 2])
        for value in ([True], [], [[1, 2]], {"wrong": [1]}, {"input_ids": []}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                runtime.token_ids(value)
        tokenizer = TokenizerFixture()
        tokenizer.as_mapping = False
        row = self.row()
        runtime.training_item(row, tokenizer, self.trainer, self.probe, 0)


    def test_native_bad_tail_and_template_token_mismatch_rejected(self):
        row = self.row()
        tokenizer = TokenizerFixture()
        tokenizer.trailer = "UNSUPPORTED_TEMPLATE_CONTENT"
        with self.assertRaisesRegex(ValueError, "trailer"):
            runtime.training_item(row, tokenizer, self.trainer, self.probe, 0)
        tokenizer = TokenizerFixture()
        original = tokenizer.apply_chat_template
        def inconsistent(messages, tokenize, add_generation_prompt):
            result = original(messages, tokenize, add_generation_prompt)
            if tokenize and not add_generation_prompt:
                result["input_ids"][0] += 1
            return result
        tokenizer.apply_chat_template = inconsistent
        with self.assertRaisesRegex(ValueError, "template/token mismatch"):
            runtime.training_item(row, tokenizer, self.trainer, self.probe, 0)


    def test_worker_interpreter_preserves_venv_symlink_spelling(self):
        venv = self.home / "venv" / "bin"
        venv.mkdir(parents=True)
        interpreter = venv / "python"
        interpreter.symlink_to(sys.executable)
        with patch.object(runtime.sys, "executable", str(interpreter)):
            self.prepare()
        self.assertEqual(self.plan["python"], str(interpreter))
        self.assertNotEqual(self.plan["python"], str(interpreter.resolve()))


    def test_adapter_mutation_after_fit_is_not_accepted_for_readout(self):
        self.prepare()
        directory = self.root / "run" / "fit_withdrawn"
        directory.mkdir(parents=True)
        self.fit_fixture("fit_withdrawn")
        (directory / "adapter" / "adapter_model.safetensors").write_text("changed CPU fixture")
        with self.assertRaisesRegex(ValueError, "custody differs"):
            runtime.adapter_for(self.plan, "fitWithdrawn__withdrawn")


    def test_input_scope_recipe_model_and_environment_drift(self):
        self.prepare()
        with patch.object(self.probe, "model_hashes", return_value={"wrong": "hash"}), self.assertRaisesRegex(ValueError, "base differs"):
            runtime.verify(self.root, self.pin, native=True)
        with patch.object(runtime, "environment", return_value={"wrong": "version"}), self.assertRaisesRegex(ValueError, "environment"):
            runtime.verify(self.root, self.pin, native=True)
        (self.root / "calls.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "prepared input differs"):
            runtime.verify(self.root, self.pin)


    def test_two_cold_fit_calls_actual_trainer_api_and_no_dev_items(self):
        self.prepare()
        (self.root / "run").mkdir()
        loaded = []
        def loader(model):
            base = SimpleNamespace(named_parameters=lambda: [("layer.lora_A.default.weight", SimpleNamespace(requires_grad=True)),
                                                              ("base.weight", SimpleNamespace(requires_grad=False))])
            loaded.append(base)
            return TokenizerFixture(), base
        seen = []
        def train(items, tokenizer, base, config, out_dir, **kwargs):
            self.assertNotIn("init_adapter", kwargs)
            self.assertEqual(len(items), 12)
            arm = "withdrawn" if kwargs["corpus_name"] == "train_withdrawn.json" else "present"
            prepared = runtime.read(self.root / f"train_{arm}.json")
            self.assertEqual(items, prepared["items"])
            self.assertEqual(kwargs["corpus_sha"], self.plan["input_hashes"][f"train_{arm}.json"])
            seen.append((base, asdict(config)))
            adapter = Path(out_dir)
            adapter.mkdir()
            runtime.write(adapter / "train_manifest.json", self.manifest(prepared))
            runtime.write(adapter / "adapter_config.json", dict(r=8, lora_alpha=16, lora_dropout=.05, bias="none", target_modules=config.target_modules))
            (adapter / "adapter_model.safetensors").write_text("CPU fixture; not model weights")
            (adapter / "DONE").write_text("ok")
        with patch.object(runtime, "load_native_model", loader), patch.object(self.trainer, "run_training", train):
            for stage in ("fit_withdrawn", "fit_present"):
                (self.root / "run" / stage).mkdir()
                runtime.fit_one(self.plan, stage, self.probe)
                self.assertTrue((self.root / "run" / stage / "fit.json").exists())
        self.assertEqual(len(loaded), 2)
        self.assertIsNot(loaded[0], loaded[1])
        self.assertEqual(seen[0][1], seen[1][1])


    def test_fit_manifest_rejects_skips_nonfinite_drops_exposure(self):
        self.prepare()
        prepared = runtime.read(self.root / "train_withdrawn.json")
        valid = self.manifest(prepared)
        runtime.check_fit_manifest(valid, prepared, self.plan["config"])
        changes = [("steps", 11), ("nonfinite_batches", 1), ("epochs_run", 3), ("final_loss", float("nan")),
                   ("train_tokens_seen", 1), ("mean_loss_per_epoch", [1.0])]
        for key, value in changes:
            wrong = copy.deepcopy(valid)
            wrong[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                runtime.check_fit_manifest(wrong, prepared, self.plan["config"])
        for section, key in (("corpus", "n_skipped_no_target"), ("truncation", "items_truncated")):
            wrong = copy.deepcopy(valid)
            wrong[section][key] = 1
            with self.assertRaises(ValueError):
                runtime.check_fit_manifest(wrong, prepared, self.plan["config"])


    def test_capture_error_preserves_raw_and_never_closes_or_scores(self):
        self.prepare()
        directory = self.root / "run" / "OFF__withdrawn"
        directory.mkdir(parents=True)
        CaptureFixture.corrupt_input = True
        with patch.object(runtime, "Native", CaptureFixture), self.assertRaisesRegex(ValueError, "prompt tokens drift"):
            runtime.capture_cell(self.plan, "OFF__withdrawn", self.probe)
        self.assertTrue((directory / "00.response.json").exists())
        self.assertFalse((directory / "closed.json").exists())
        self.assertTrue(CaptureFixture.instances[0].closed)


    def test_off_never_routes_adapter_and_adapters_are_hash_bound(self):
        self.prepare()
        directory = self.root / "run" / "OFF__withdrawn"
        directory.mkdir(parents=True)
        CaptureFixture.corrupt_route = True
        with patch.object(runtime, "Native", CaptureFixture), self.assertRaisesRegex(ValueError, "LoRA route"):
            runtime.capture_cell(self.plan, "OFF__withdrawn", self.probe)
        self.assertFalse((directory / "closed.json").exists())


    def test_missing_capture_never_scores_even_after_completion(self):
        self.complete()
        (self.root / "run" / runtime.CELLS[-1] / "11.response.json").unlink()
        out = self.home / "scores"
        with patch.object(self.corpus, "score_response", side_effect=AssertionError("must not score")) as score:
            with self.assertRaises((ValueError, FileNotFoundError)):
                runtime.collect(self.root, self.pin, self.completion, out)
            score.assert_not_called()
        self.assertFalse((out / "scores.json").exists())
        self.assertTrue((out / "collection_failure.json").exists())


    def test_capture_tamper_duplicate_process_and_recollection_rejected(self):
        self.complete()
        last = self.root / "run" / runtime.CELLS[-1]
        original = (last / "started.json").read_bytes()
        changed = runtime.read(last / "started.json")
        changed["pid"] = 80000
        (last / "started.json").write_bytes(runtime.encoded(changed))
        with self.assertRaisesRegex(ValueError, "process receipt"):
            runtime.validate_completed(self.plan, self.pin, self.probe)
        (last / "started.json").write_bytes(original)
        out = self.home / "scores"
        runtime.collect(self.root, self.pin, self.completion, out)
        with self.assertRaisesRegex(ValueError, "fresh external"):
            runtime.collect(self.root, self.pin, self.completion, out)


    def test_controller_stops_on_failure_preserves_evidence_and_no_retry(self):
        self.prepare()
        seen = []
        def fail_second(plan, pin, stage, deadline, probe):
            seen.append(stage)
            if stage == "fit_present":
                raise TimeoutError("fixture worker timeout")
            self.fake_stage(plan, pin, stage, deadline, probe)
        with patch.object(runtime, "run_stage", fail_second), self.assertRaises(TimeoutError):
            runtime.controller(self.root, self.pin, allow_gpu=True)
        self.assertEqual(seen, ["fit_withdrawn", "fit_present"])
        self.assertTrue((self.root / "controller_failure.json").exists())
        self.assertTrue((self.root / "run" / "fit_withdrawn" / "fit.json").exists())
        self.assertFalse((self.root / "capture_complete.json").exists())
        with self.assertRaises(FileExistsError):
            runtime.controller(self.root, self.pin, allow_gpu=True)


    def test_readout_300s_ceiling_still_clamps_to_global_release_reserve(self):
        self.prepare()
        (self.root / "run").mkdir()
        process = Mock(pid=87654)
        process.wait.return_value = 0
        with patch.object(self.probe, "gpu_state", return_value=True), patch.object(self.probe, "group_alive", return_value=False), \
                patch.object(self.probe, "cleanup"), patch.object(runtime.subprocess, "Popen", return_value=process), \
                patch.object(runtime.time, "monotonic", return_value=100):
            runtime.run_stage(self.plan, self.pin, "OFF__withdrawn", 1000, self.probe)
            process.wait.assert_called_with(timeout=300)
            runtime.run_stage(self.plan, self.pin, "OFF__present", 300, self.probe)
            process.wait.assert_called_with(timeout=160)


    def test_stage_owns_only_spawned_group_and_cleanup_runs_on_timeout(self):
        self.prepare()
        (self.root / "run").mkdir()
        process = Mock(pid=87654)
        process.wait.side_effect = subprocess.TimeoutExpired("fixture", 1)
        cleanup = Mock()
        with patch.object(self.probe, "gpu_state", return_value=True), patch.object(self.probe, "group_alive", return_value=False), \
                patch.object(self.probe, "cleanup", cleanup), patch.object(runtime.subprocess, "Popen", return_value=process) as popen:
            with self.assertRaises(subprocess.TimeoutExpired):
                runtime.run_stage(self.plan, self.pin, "fit_withdrawn", time.monotonic() + 100, self.probe)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertEqual(popen.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], self.plan["gpu_uuid"])
        cleanup.assert_called_once_with(process)
        self.assertTrue((self.root / "run" / "fit_withdrawn" / "released.json").exists())


    def test_busy_gpu_is_never_killed_or_started(self):
        self.prepare()
        with patch.object(self.probe, "gpu_state", return_value=False), patch.object(self.probe, "cleanup") as cleanup, \
                patch.object(runtime.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "not vacant"):
                runtime.run_stage(self.plan, self.pin, "fit_withdrawn", time.monotonic() + 100, self.probe)
        popen.assert_not_called()
        cleanup.assert_not_called()


    def test_nvml_30s_budget_preserves_exact_uuid_and_release_checks(self):
        self.prepare()
        xml = f"<nvidia_smi_log><gpu><uuid>{self.plan['gpu_uuid']}</uuid><processes/></gpu></nvidia_smi_log>"
        response = SimpleNamespace(returncode=0, stdout=xml)
        with patch.object(self.probe.subprocess, "run", return_value=response) as query:
            self.assertTrue(self.probe.gpu_state(self.plan))
            self.assertEqual(query.call_args.kwargs["timeout"], 30)
            self.assertEqual(query.call_args.args[0], ["nvidia-smi", "-i", "0", "-q", "-x"])
        response.stdout = xml.replace("<processes/>", "<processes><process_info><pid>123</pid></process_info></processes>")
        with patch.object(self.probe.subprocess, "run", return_value=response):
            self.assertFalse(self.probe.gpu_state(self.plan))
        response.stdout = xml.replace(self.plan["gpu_uuid"], "GPU-wrong-device")
        with patch.object(self.probe.subprocess, "run", return_value=response), self.assertRaises(ValueError):
            self.probe.gpu_state(self.plan)
        with patch.object(self.probe.subprocess, "run", side_effect=subprocess.TimeoutExpired("nvidia-smi", 30)), self.assertRaises(subprocess.TimeoutExpired):
            self.probe.gpu_state(self.plan)


    def test_insufficient_query_release_budget_starts_nothing(self):
        self.prepare()
        with patch.object(self.probe, "gpu_state") as query, patch.object(runtime.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "vacancy and release"):
                runtime.run_stage(self.plan, self.pin, "fit_withdrawn", time.monotonic() + 60, self.probe)
        query.assert_not_called()
        popen.assert_not_called()


    def test_native_backend_calls_matched_engine_and_actual_lora_argument(self):
        self.prepare()
        engines, requests = [], []
        class FakeLLM:
            def __init__(self, **kwargs):
                engines.append(kwargs)
                self.tokenizer = TokenizerFixture()
                self.tokenizer.decode = lambda ids, skip_special_tokens: "{}"

            def get_tokenizer(self):
                return self.tokenizer

            def generate(self, prompts, params, lora_request, use_tqdm):
                requests.append(lora_request)
                output = SimpleNamespace(text="{}", token_ids=self.tokenizer.encode("{}"), finish_reason="stop", stop_reason=1)
                return [SimpleNamespace(outputs=[output], prompt_token_ids=self.tokenizer.encode(prompts[0]))]

            def shutdown(self):
                pass
        modules = {"vllm": SimpleNamespace(LLM=FakeLLM, SamplingParams=lambda **kwargs: kwargs),
                   "vllm.lora": SimpleNamespace(),
                   "vllm.lora.request": SimpleNamespace(LoRARequest=lambda name, number, path: (name, number, path)),
                   "torch": SimpleNamespace(inference_mode=contextlib.nullcontext)}
        calls = runtime.read(self.root / "calls.json")["withdrawn"]
        with patch.dict(sys.modules, modules):
            for adapter in (None, "/cpu-fixture-withdrawn", "/cpu-fixture-present"):
                backend = runtime.Native(self.plan, self.probe, adapter)
                response = backend.generate(calls[0]["messages"])
                self.probe.validate_response(calls[0], response)
                backend.close()
        self.assertEqual(requests, [None, ("reflection", 1, "/cpu-fixture-withdrawn"), ("reflection", 1, "/cpu-fixture-present")])
        self.assertTrue(all(engine["enable_lora"] and engine["max_lora_rank"] == 32 for engine in engines))
        self.assertEqual(engines[0], engines[1])
        self.assertEqual(engines[1], engines[2])


    def test_cleanup_failure_cannot_claim_release(self):
        self.prepare()
        (self.root / "run").mkdir()
        process = Mock(pid=87654)
        process.wait.return_value = 0
        with patch.object(self.probe, "gpu_state", return_value=True), patch.object(self.probe, "group_alive", return_value=True), \
                patch.object(self.probe, "cleanup"), patch.object(runtime.subprocess, "Popen", return_value=process):
            with self.assertRaisesRegex(ValueError, "survived cleanup"):
                runtime.run_stage(self.plan, self.pin, "fit_withdrawn", time.monotonic() + 100, self.probe)
        directory = self.root / "run" / "fit_withdrawn"
        self.assertTrue((directory / "cleanup_failure.json").exists())
        self.assertFalse((directory / "released.json").exists())


    def test_budget_expires_and_restores_alarm(self):
        previous = signal.getsignal(signal.SIGALRM)
        with self.assertRaises(TimeoutError):
            with runtime.budget(.01):
                time.sleep(.05)
        self.assertEqual(signal.getsignal(signal.SIGALRM), previous)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0], 0)


    def test_import_does_not_load_native_libraries(self):
        script = ("import importlib.util,sys; "
                  f"spec=importlib.util.spec_from_file_location('p', {str(PATH)!r}); "
                  "module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
                  "assert not any(name in sys.modules for name in ('torch','vllm','transformers','peft'))")
        result = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


    def test_prepare_inventory_recipe_and_public_scope_not_ancestry(self):
        with patch.object(self.corpus, "score_response", side_effect=AssertionError("premature score")), \
                patch.object(runtime, "load_native_model", side_effect=AssertionError("native model")), \
                patch.object(runtime, "Native", side_effect=AssertionError("native engine")), \
                patch.object(self.probe, "gpu_state", side_effect=AssertionError("GPU query")):
            result = self.prepare()
        self.assertEqual(result["status"], "PREPARED_NOT_LAUNCHED")
        self.assertEqual(self.plan["stages"], list(runtime.STAGES))
        self.assertEqual(self.plan["config"], asdict(self.trainer.TrainConfig(**runtime.RECIPE, model=str(self.model))))
        self.assertEqual(self.plan["generic_system"], "You are a helpful assistant.")
        self.assertEqual(self.plan["binding"]["scope"], runtime.BINDING_SCOPE)
        self.assertIn("NO_FIT", self.plan["binding"]["upstream_receipt_scope"])
        self.assertIn("not this runtime", self.plan["binding"]["scope_explanation"])
        self.assertFalse(self.plan["binding"]["clean_ancestry_certified"])
        self.assertFalse((self.root / "run").exists())
        self.assertEqual(list(Path(self.plan["log_dir"]).iterdir()), [])
        for arm in runtime.ARMS:
            train = runtime.read(self.root / f"train_{arm}.json")
            dev = runtime.read(self.root / "dev.json")[arm]
            calls = runtime.read(self.root / "calls.json")[arm]
            self.assertEqual(len(train["items"]), 12)
            self.assertEqual([row["panel"] for row in dev], ["restatement"] * 12 + ["application"] * 12)
            self.assertEqual(len(calls), 24)
            self.assertTrue(all(set(call) == {"call_id", "row_id", "messages", "native"} for call in calls))
            self.assertTrue(all(item["view"] == "restatement" for item in train["items"]))
            for call in calls:
                runtime.validate_messages(call["messages"])
                self.assertNotIn("response_target", str(call))
                self.assertNotIn("source_proof", str(call))

    def test_full_assistant_masks_counts_bytes_padding_and_matched_orders(self):
        self.prepare()
        arms = [runtime.read(self.root / f"train_{arm}.json") for arm in runtime.ARMS]
        self.assertEqual(arms[0]["epoch_order"], arms[1]["epoch_order"])
        self.assertEqual(arms[0]["target_tokens"], arms[1]["target_tokens"])
        self.assertEqual(arms[0]["target_utf8_bytes"], arms[1]["target_utf8_bytes"])
        self.assertLess(arms[0]["prompt_tokens"], arms[1]["prompt_tokens"])
        for arm in arms:
            self.assertEqual(len(arm["batch_exposure"]), 12)
            self.assertEqual(sum(batch["input_tokens"] for batch in arm["batch_exposure"]), 4 * arm["total_tokens"])
            self.assertEqual(sum(batch["supervised_tokens"] for batch in arm["batch_exposure"]), 4 * arm["target_tokens"])
            for audit in arm["encoding"]:
                self.assertEqual([label for label in audit["labels"] if label != -100], audit["supervised_ids"])
                self.assertEqual(audit["supervised_ids"].count(1), 1)
                self.assertEqual(audit["labels"][-2:], [1, -100])
                self.assertTrue(all(label == -100 for label in audit["labels"][:audit["prompt_tokens"]]))
                self.assertEqual(audit["supervised_ids"], TokenizerFixture().encode(audit["response_target"]) + [1])
                self.assertEqual(audit["input_ids"], TokenizerFixture().encode(audit["full_assistant_text"]))
                self.assertEqual(audit["input_tokens"], len(audit["input_ids"]))
                self.assertEqual(audit["target_utf8_bytes"], len(audit["response_target"].encode()))
                self.assertEqual(audit["full_assistant_utf8_bytes"], len(audit["full_assistant_text"].encode()))
                self.assertEqual(audit["native_prompt"]["actual_system_text"], runtime.GENERIC_SYSTEM)

    def test_oversize_rejected_before_native_encoder_and_nontrain_loss_forbidden(self):
        row = self.row()
        row["input_messages"][1]["content"] += " extra" * 1200
        with patch.object(self.trainer, "encode_item_segments", side_effect=AssertionError("encoder must not truncate")):
            with self.assertRaisesRegex(ValueError, "before native encoder"):
                runtime.training_item(row, TokenizerFixture(), self.trainer, self.probe, 0)
        for panel in runtime.PANELS:
            with self.assertRaisesRegex(ValueError, "TRAIN"):
                runtime.training_item(self.row(panel, "dev"), TokenizerFixture(), self.trainer, self.probe, 0)

    def test_target_eos_bad_mask_and_padding_loss_rejected(self):
        row = self.row()
        row["response_target"] += TokenizerFixture.eos_token
        with self.assertRaisesRegex(ValueError, "target contains"):
            runtime.training_item(row, TokenizerFixture(), self.trainer, self.probe, 0)
        original = self.trainer.encode_item_segments
        def bad_mask(*args, **kwargs):
            segments = original(*args, **kwargs)
            segments[0].labels[0] = segments[0].ids[0]
            return segments
        with patch.object(self.trainer, "encode_item_segments", bad_mask), self.assertRaisesRegex(ValueError, "mask differs"):
            runtime.training_item(self.row(), TokenizerFixture(), self.trainer, self.probe, 0)
        original_collate = self.trainer.collate
        def bad_padding(packs, pad_id):
            batch = original_collate(packs, pad_id)
            if len(packs) > 1:
                batch["input_ids"][0].append(pad_id)
                batch["labels"][0].append(pad_id)
            return batch
        rows = self.corpus.build_panel("restatement", split="train", parent_condition="present")["rows"]
        with patch.object(self.trainer, "collate", bad_padding), self.assertRaisesRegex(ValueError, "padding receives loss"):
            runtime.encode_training(rows, TokenizerFixture(), self.trainer, self.probe)

    def test_all_144_raw_captures_close_before_two_separate_metrics(self):
        with patch.object(self.corpus, "score_response", side_effect=AssertionError("premature scoring")):
            result = self.complete()
        self.assertEqual(result["status"], "ALL_CAPTURES_CLOSED_UNSCORED")
        self.assertEqual(len(CaptureFixture.instances), 6)
        self.assertTrue(all(backend.closed and len(backend.seen) == 24 for backend in CaptureFixture.instances))
        self.assertEqual([backend.route is None for backend in CaptureFixture.instances], [True, True, False, False, False, False])
        self.assertEqual(len(runtime.validate_completed(self.plan, self.pin, self.probe)), 8)
        out = self.home / "collected"
        runtime.collect(self.root, self.pin, self.completion, out)
        report = runtime.read(out / "scores.json")
        self.assertEqual(report["calls"], 144)
        self.assertEqual(report["fresh_workers"], 8)
        self.assertIsNone(report["composite_metric"])
        self.assertFalse(report["automatic_pass"])
        self.assertFalse(report["clean_ancestry_certified"])
        for cell in report["cells"].values():
            self.assertEqual(set(cell), set(runtime.PANELS))
            for panel in runtime.PANELS:
                self.assertEqual(cell[panel]["count"], 12)
                self.assertEqual(cell[panel]["total"], 12)
            self.assertEqual(cell["restatement"]["metric"], "exact_authored_fixture_matches")
            self.assertEqual(cell["application"]["metric"], "strict_application_correct")

    def test_raw_whitespace_choice_not_normalized_and_prose_not_semantic_failure(self):
        CaptureFixture.raw_text = "A\n"
        self.complete()
        out = self.home / "scores"
        with patch.object(self.corpus, "score_response", wraps=self.corpus.score_response) as scorer:
            runtime.collect(self.root, self.pin, self.completion, out)
        self.assertEqual(scorer.call_count, 144)
        self.assertTrue(all(call.args[1] == "A\n" for call in scorer.call_args_list))
        report = runtime.read(out / "scores.json")
        self.assertIn("NOT semantic prose failure", report["restatement_limitation"])
        for cell in report["cells"].values():
            self.assertIsNone(cell["restatement"]["semantic_prose_score"])
            self.assertEqual(cell["restatement"]["count"], 0)
            self.assertEqual(cell["application"]["count"], 0)
            self.assertTrue(all(not row["score"]["syntax_valid"] for row in cell["application"]["rows"]))

    def test_final_source_pins_supplied_by_main_not_frozen_during_development(self):
        self.kwargs["reflection_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Main final corpus/probe"):
            runtime.prepare(**self.kwargs)
        self.assertFalse(self.root.exists())
        self.kwargs["reflection_sha256"] = self.pins["organism_v6/birth_reflection_probe.py"]
        self.prepare()
        (self.source / "organism_v6/birth_reflection_probe.py").write_text("fixture source drift")
        with self.assertRaisesRegex(ValueError, "snapshot differs"):
            runtime.verify(self.root, self.pin)

    def test_final_helper_hash_binding_and_environment_rejections(self):
        self.kwargs["probe_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "final driver hash"):
            runtime.prepare(**self.kwargs)
        self.kwargs["probe_sha256"] = self.probe_hash
        self.kwargs["binding_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "base receipt"):
            runtime.prepare(**self.kwargs)
        self.assertTrue((self.root / "prepare_failure.json").exists())
        self.assertFalse((self.root / "plan.json").exists())
        with self.assertRaisesRegex(ValueError, "new disjoint"):
            runtime.prepare(**self.kwargs)

    def test_extra_source_and_checkout_symlink_rejected(self):
        extra = self.source / "extra.py"
        extra.write_text("unexpected fixture")
        with self.assertRaisesRegex(ValueError, "snapshot differs"):
            runtime.source_snapshot(self.source, self.pins)
        extra.unlink()
        extra.symlink_to(self.binding_path)
        with self.assertRaisesRegex(ValueError, "symlink"):
            runtime.source_snapshot(self.source, self.pins)
        extra.unlink()
        (self.source / ".git").mkdir()
        with self.assertRaisesRegex(ValueError, "non-checkout"):
            runtime.source_snapshot(self.source, self.pins)

    def test_same_source_template_and_event_leakage_are_rejected(self):
        original = self.corpus.build_panel
        for field in ("source_id", "template_id", "events"):
            def leaky(panel, *, split, parent_condition):
                built = original(panel, split=split, parent_condition=parent_condition)
                if split == "dev":
                    train = original("restatement", split="train", parent_condition=parent_condition)
                    built["rows"][0]["source"][field] = train["rows"][0]["source"][field]
                return built
            with self.subTest(field=field), patch.object(self.corpus, "build_panel", leaky):
                with self.assertRaisesRegex(ValueError, "leakage"):
                    runtime.panel_inputs(self.corpus)

    def test_export_metadata_leakage_and_application_loss_rejected(self):
        original = self.corpus.export_development
        def leaky(built):
            result = original(built)
            result["requests"][0]["response_target"] = built["rows"][0]["response_target"]
            return result
        with patch.object(self.corpus, "export_development", leaky), self.assertRaisesRegex(ValueError, "target/metadata"):
            runtime.panel_inputs(self.corpus)
        original_train = self.corpus.export_training
        def app_loss(built):
            result = original_train(built)
            result["report"]["application_rows"] = 1
            return result
        with patch.object(self.corpus, "export_training", app_loss), self.assertRaisesRegex(ValueError, "rows in loss"):
            runtime.panel_inputs(self.corpus)

    def test_pair_target_order_and_generic_system_drift_rejected(self):
        original = self.corpus.build_panel
        def target_drift(panel, *, split, parent_condition):
            built = original(panel, split=split, parent_condition=parent_condition)
            if parent_condition == "present":
                built["rows"].reverse()
            return built
        with patch.object(self.corpus, "build_panel", target_drift), self.assertRaisesRegex(ValueError, "paired"):
            runtime.panel_inputs(self.corpus)
        row = self.row()
        row["input_messages"][0]["content"] = "Task specific anchor"
        with self.assertRaisesRegex(ValueError, "generic system"):
            runtime.training_item(row, TokenizerFixture(), self.trainer, self.probe, 0)

    def test_explicit_gpu_flags_deadlines_and_lease_reserve(self):
        with self.assertRaisesRegex(ValueError, "Main-only controller"):
            runtime.controller(self.root, "none")
        with self.assertRaisesRegex(ValueError, "Main-only worker"):
            runtime.worker(self.root, "none", runtime.STAGES[0])
        self.assertEqual((runtime.OUTER_SECONDS, runtime.FIT_SECONDS, runtime.READOUT_SECONDS,
                          runtime.GPU_QUERY_SECONDS, runtime.COLLECTION_SECONDS), (3600, 600, 300, 30, 180))
        self.assertEqual(2 * runtime.FIT_SECONDS + 6 * runtime.READOUT_SECONDS +
                         8 * (runtime.GPU_QUERY_SECONDS + runtime.CLEANUP_SECONDS), 3560)
        self.kwargs["lease_end"] = time.time() + 3600
        with self.assertRaisesRegex(ValueError, "insufficient lease"):
            runtime.prepare(**self.kwargs)

    def test_missing_fit_or_log_never_allows_scores(self):
        self.complete()
        (self.root / "run/fit_present/adapter/DONE").unlink()
        out = self.home / "scores"
        with patch.object(self.corpus, "score_response", side_effect=AssertionError("premature score")):
            with self.assertRaisesRegex(ValueError, "incomplete adapter"):
                runtime.collect(self.root, self.pin, self.completion, out)
        self.assertFalse((out / "scores.json").exists())

    def test_log_mutation_after_capture_closure_is_rejected(self):
        self.complete()
        (Path(self.plan["log_dir"]) / "OFF__present/stdout.log").write_text("changed fixture log")
        out = self.home / "scores"
        with patch.object(self.corpus, "score_response", side_effect=AssertionError("premature score")):
            with self.assertRaisesRegex(ValueError, "completion inventory changed"):
                runtime.collect(self.root, self.pin, self.completion, out)

    def test_collection_never_writes_into_sources_models_logs_or_capture_root(self):
        self.complete()
        for parent in (self.source, self.model, self.root, Path(self.plan["log_dir"])):
            out = parent / "illegal-collection"
            with self.subTest(parent=parent), self.assertRaisesRegex(ValueError, "fresh external collection"):
                runtime.collect(self.root, self.pin, self.completion, out)
            self.assertFalse(out.exists())

    def test_immutable_json_no_overwrite_duplicate_keys_or_nonfinite(self):
        target = self.home / "immutable.json"
        runtime.write(target, {"fixture": True})
        initial = target.read_bytes()
        with self.assertRaises(FileExistsError):
            runtime.write(target, {"fixture": False})
        self.assertEqual(target.read_bytes(), initial)
        for index, invalid in enumerate(('{"same":1,"same":2}', '{"not_finite":NaN}')):
            candidate = self.home / f"invalid{index}.json"
            candidate.write_text(invalid)
            with self.assertRaises(ValueError):
                runtime.read(candidate)

    def test_nested_release_timer_restores_outer_and_signal_handlers(self):
        alarm = signal.getsignal(signal.SIGALRM)
        terminate = signal.getsignal(signal.SIGTERM)
        interrupt = signal.getsignal(signal.SIGINT)
        with runtime.budget(2):
            before = signal.getitimer(signal.ITIMER_REAL)[0]
            with runtime.release_budget(time.monotonic() + 1):
                self.assertEqual(signal.getsignal(signal.SIGTERM), signal.SIG_IGN)
                self.assertEqual(signal.getsignal(signal.SIGINT), signal.SIG_IGN)
            self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0], 0)
            self.assertLessEqual(signal.getitimer(signal.ITIMER_REAL)[0], before)
        self.assertEqual(signal.getsignal(signal.SIGALRM), alarm)
        self.assertEqual(signal.getsignal(signal.SIGTERM), terminate)
        self.assertEqual(signal.getsignal(signal.SIGINT), interrupt)

    def test_controller_sigterm_unwinds_owned_group_cleanup(self):
        self.prepare()
        (self.root / "run").mkdir()
        process = Mock(pid=87654)
        process.wait.side_effect = lambda **kwargs: signal.raise_signal(signal.SIGTERM)
        original = signal.getsignal(signal.SIGTERM)
        with patch.object(self.probe, "gpu_state", return_value=True), \
                patch.object(self.probe, "group_alive", return_value=False), \
                patch.object(self.probe, "cleanup") as cleanup, \
                patch.object(runtime.subprocess, "Popen", return_value=process):
            with self.assertRaises(InterruptedError), runtime.controller_budget():
                runtime.run_stage(self.plan, self.pin, "fit_withdrawn", time.monotonic() + 100, self.probe)
        cleanup.assert_called_once_with(process)
        self.assertTrue((self.root / "run/fit_withdrawn/released.json").exists())
        self.assertEqual(signal.getsignal(signal.SIGTERM), original)


if __name__ == "__main__":
    unittest.main()
