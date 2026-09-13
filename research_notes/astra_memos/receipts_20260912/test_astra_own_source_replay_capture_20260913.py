"""CPU lifecycle and source-join tests. All native/model/GPU boundaries mocked."""
import ast
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
specification = importlib.util.spec_from_file_location("own_replay_capture_test", "/tmp/astra_own_source_replay_capture_20260913.py")
runner = importlib.util.module_from_spec(specification)
specification.loader.exec_module(runner)
memory = runner.lifecycle()


class Tokenizer:
    chat_template = "CPU_FIXTURE_NOT_NATIVE"

    def encode(self, text, add_special_tokens=False):
        return [ord(char) for char in text]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        text = "<|im_start|>system\nCPU fixture only<|im_end|>\n"
        text += "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


class Backend:
    def __init__(self, plan, probe, route):
        self.tokenizer = Tokenizer()
        self.route = route
        self.calls, self.closed = [], False

    def generate(self, request):
        self.calls.append(copy.deepcopy(request))
        raw = '  {"fixture":"not a production record"}\n'
        return dict(request["native"], text=raw, decoded_output=raw, actual_prompt_token_ids=request["native"]["prompt_token_ids"],
                    output_token_ids=[11], finish_reason="stop", stop_reason=None, lora_request=self.route, started=1.0, ended=1.5)

    def close(self):
        self.closed = True


class CaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = memory.load(dict(path="/tmp/astra_own_source_replay_core_20260913.py", sha256=runner.CORE_PIN), "test_replay_core", runner.CORE_PIN)
        cls.native = memory.load(dict(path="/tmp/astra_level1_real_record_run_20260913.py", sha256=runner.NATIVE_PIN), "test_replay_native", runner.NATIVE_PIN)
        cls.public = memory.load(dict(path="/tmp/astra_birth_skill_probe_run_20260913.py", sha256=runner.PUBLIC_PIN), "test_replay_public", runner.PUBLIC_PIN)
        cls.bundles = {str(seed): cls.core.build(seed) for seed in runner.SEEDS}

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="own_replay_capture_cpu_")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / "capture"
        self.root.mkdir()
        self.spec = dict(runner_sha256=memory.digest(runner.SELF),
            core=dict(path=str(Path(self.core.__file__)), sha256=runner.CORE_PIN),
            native=dict(path=str(self.native.SELF), sha256=runner.NATIVE_PIN),
            public=dict(path=self.public.__file__, sha256=runner.PUBLIC_PIN),
            lifecycle=dict(path=str(memory.SELF), sha256=runner.LIFECYCLE_PIN),
            archive=dict(path=self.core.ARCHIVE, sha256=self.core.ARCHIVE_PIN), source_root=self.core.SOURCE_ROOT,
            protocol=dict(path="/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_CAPTURE_2026-09-13.md", sha256=runner.PROTOCOL_PIN),
            gpu_index=6, gpu_uuid="GPU-CPU-FIXTURE-NOT-NATIVE", expected_boot_id="0" * 36, lease_end=time.time() + 100000)
        self.reference = dict(model="CPU_MODEL_NOT_NATIVE", model_files={"base": "pin"}, environment={}, python=sys.executable,
            python_sha256=memory.digest(sys.executable), chat_template=Tokenizer.chat_template, engine=self.native.ENGINE, params=self.public.PARAMS,
            root="/NOT_A_LIVE_ROOT")
        self.runtime = SimpleNamespace(tree=Mock(), validate_response=self.native.validate_response, Native=Backend)
        def tree(path):
            for bundle in self.bundles.values():
                if str(path) == bundle["producer"]["adapter"]:
                    return copy.deepcopy(bundle["producer"]["adapter_files"])
            return {
                str(entry.relative_to(path)): memory.digest(entry) for entry in sorted(Path(path).rglob("*")) if entry.is_file()}
        self.runtime.tree.side_effect = tree
        self.probe = SimpleNamespace(render=self.public.render, native_tokenizer=Mock(return_value=Tokenizer()), gpu_state=Mock(return_value=True))
        self.bound = dict(memory=memory, core=self.core, runtime=self.runtime, probe=self.probe, bundles=self.bundles,
                          parents={str(seed): self.reference for seed in runner.SEEDS}, reference=self.reference)
        memory.write(self.root / "spec.json", self.spec)
        spec_pin = memory.digest(self.root / "spec.json")
        names = []
        for seed in runner.SEEDS:
            for name, value in ((f"bundle_seed{seed}.json", self.bundles[str(seed)]),
                                 (f"calls_seed{seed}.json", runner.make_calls(self.bundles[str(seed)], Tokenizer(), self.probe))):
                memory.write(self.root / name, value)
                names.append(name)
        self.plan = runner.expected_plan(self.root, self.spec, spec_pin, self.bound, {name: memory.digest(self.root / name) for name in names})
        memory.write(self.root / "plan.json", self.plan)
        memory.write(self.root / "prepare_started.json", dict(spec_sha256=spec_pin))
        self.pin = memory.digest(self.root / "plan.json")

    def directory(self, seed):
        path = self.root / "run" / f"seed{seed}"
        path.mkdir(parents=True)
        return path

    def make_complete(self):
        for seed in runner.SEEDS:
            directory = self.directory(seed)
            runner.capture_seed(self.plan, seed, self.bound)
            identity = dict(pid=9000 + seed, pgid=9000 + seed, start_ticks=100 + seed)
            command = [self.plan["python"], "-B", str(runner.SELF), "worker", "--root", self.plan["root"], "--plan-sha256", self.pin,
                       "--seed", str(seed), "--allow-gpu"]
            memory.write(directory / "launch.json", dict(identity=identity, seed=seed, plan_sha256=self.pin, command=command, started=seed * 10 + 1.0))
            memory.write(directory / "started.json", dict(seed=seed, plan_sha256=self.pin, pid=9000 + seed, pgid=9000 + seed, time=seed * 10 + 2.0))
            memory.write(directory / "released.json", dict(identity=identity, seed=seed, ended=seed * 10 + 3.0, elapsed_seconds=2.0))
        inventory = runner.validate_completed(self.plan, self.pin, self.bound)
        memory.write(self.root / "capture_complete.json", dict(scope=runner.SCOPE, plan_sha256=self.pin, stages=inventory,
            calls=72, fits=0, updates=0, teacher_calls=0, admitted=False, elapsed_seconds=30.0))
        return memory.digest(self.root / "capture_complete.json")

    def test_closed_spec_protocol_allocation_and_no_fit_controls(self):
        runner.validate_spec(self.spec, memory)
        for change in (dict(gpu_index=5), dict(gpu_index=True), dict(fit_seed=0), dict(lease_end=float("inf")), dict(runner_sha256="bad")):
            with self.subTest(change=change), self.assertRaises(ValueError):
                runner.validate_spec(dict(self.spec, **change), memory)
        bad = copy.deepcopy(self.spec)
        bad["protocol"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            runner.validate_spec(bad, memory)

    def test_72_train_only_original_settings_no_targets(self):
        self.assertEqual(self.plan["limits"], dict(controller=3000, seed=900, collection=180, calls_per_seed=24,
            calls_total=72, output_tokens=192, fits=0, updates=0, teacher_calls=0))
        for seed in runner.SEEDS:
            calls = memory.read(self.root / f"calls_seed{seed}.json")
            self.assertEqual(len(calls), 24)
            self.assertTrue(all(call["core_request"]["source_split"] == "train" for call in calls))
            self.assertNotIn('"raw_target":', memory.encoded(calls).decode())
        self.assertEqual(self.plan["params"]["temperature"], 0)
        self.assertEqual(self.plan["params"]["max_tokens"], 192)

    def test_prepare_vertical_slice_has_no_admission_or_native_backend(self):
        spec_path = self.home / "spec.json"
        memory.write(spec_path, self.spec)
        target = self.home / "prepared"
        with patch.object(runner, "bind", return_value=self.bound), patch.object(runner, "allocation"), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), patch.object(self.core, "admit", side_effect=AssertionError("admission too early")):
            result = runner.prepare(target, spec_path, memory.digest(spec_path), allow_native=True)
        self.assertEqual(result["calls"], 72)
        self.assertEqual(result["fits"], 0)
        self.assertFalse((target / "run").exists())
        self.assertEqual(memory.read(target / "bundle_seed0.json"), self.bundles["0"])

    def test_verify_rejects_source_row_and_native_settings_drift(self):
        with patch.object(runner, "bind", return_value=self.bound):
            runner.verify(self.root, self.pin)
            bad = copy.deepcopy(self.plan)
            bad["params"]["max_tokens"] = 193
            (self.root / "plan.json").write_bytes(memory.encoded(bad))
            with self.assertRaisesRegex(ValueError, "prepared plan"):
                runner.verify(self.root, memory.digest(self.root / "plan.json"))
            (self.root / "plan.json").write_bytes(memory.encoded(self.plan))
            (self.root / "calls_seed0.json").write_text("[]")
            with self.assertRaisesRegex(ValueError, "prepared input"):
                runner.verify(self.root, self.pin)

    def test_capture_24_raw_outputs_backend_closed_no_admission(self):
        directory = self.directory(0)
        backend = Backend(self.plan, self.probe, runner.route_for(self.plan, 0, self.runtime))
        with patch.object(self.core, "admit", side_effect=AssertionError("no admission in capture")):
            runner.capture_seed(self.plan, 0, self.bound, backend_factory=lambda *args: backend)
        self.assertTrue(backend.closed)
        self.assertEqual(len(backend.calls), 24)
        self.assertEqual(memory.read(directory / "closed.json")["calls"], 24)
        raw = memory.read(directory / "train_00.response.json")["text"]
        self.assertEqual(raw, '  {"fixture":"not a production record"}\n')

    def test_length_capture_preserved_not_retried(self):
        directory = self.directory(0)
        backend = Backend(self.plan, self.probe, runner.route_for(self.plan, 0, self.runtime))
        original = backend.generate
        def truncated(request):
            response = original(request)
            response.update(finish_reason="length", output_token_ids=[11] * 192)
            return response
        backend.generate = truncated
        runner.capture_seed(self.plan, 0, self.bound, backend_factory=lambda *args: backend)
        self.assertEqual(len(backend.calls), 24)
        self.assertEqual(memory.read(directory / "train_00.response.json")["finish_reason"], "length")

    def test_native_token_route_and_decoded_bytes_failure_preserves_raw(self):
        directory = self.directory(0)
        backend = Backend(self.plan, self.probe, runner.route_for(self.plan, 0, self.runtime))
        original = backend.generate
        def mismatched(request):
            response = original(request)
            response["decoded_output"] = "different bytes"
            return response
        backend.generate = mismatched
        with self.assertRaisesRegex(ValueError, "output bytes"):
            runner.capture_seed(self.plan, 0, self.bound, backend_factory=lambda *args: backend)
        self.assertTrue(backend.closed)
        self.assertEqual(len(backend.calls), 1)
        self.assertTrue((directory / "train_00.response.json").exists())
        self.assertTrue((directory / "capture_failure.json").exists())
        self.assertFalse((directory / "closed.json").exists())

    def test_prompt_drift_fails_before_first_generation(self):
        directory = self.directory(0)
        backend = Backend(self.plan, self.probe, runner.route_for(self.plan, 0, self.runtime))
        calls = memory.read(self.root / "calls_seed0.json")
        calls[0]["native"]["prompt_token_ids"][0] += 1
        (self.root / "calls_seed0.json").write_bytes(memory.encoded(calls))
        with self.assertRaisesRegex(ValueError, "prompt/token"):
            runner.capture_seed(self.plan, 0, self.bound, backend_factory=lambda *args: backend)
        self.assertEqual(backend.calls, [])
        self.assertTrue(backend.closed)
        self.assertFalse((directory / "closed.json").exists())

    def test_changed_original_adapter_rejected(self):
        self.runtime.tree.side_effect = None
        self.runtime.tree.return_value = {"changed": "weight"}
        with self.assertRaisesRegex(ValueError, "original parent adapter"):
            runner.route_for(self.plan, 0, self.runtime)

    def test_failed_gpu_precheck_never_spawns(self):
        self.probe.gpu_state.return_value = False
        with patch.object(runner, "allocation"), patch.object(subprocess, "Popen") as spawn, self.assertRaisesRegex(ValueError, "vacancy"):
            runner.run_seed(self.plan, self.pin, 0, time.monotonic() + 3000, self.bound)
        spawn.assert_not_called()

    def test_stage_timeout_cleanup_and_new_worker_binding(self):
        (self.root / "run").mkdir()
        process = Mock(pid=50000)
        process.wait.side_effect = subprocess.TimeoutExpired("worker", 1)
        identity = dict(pid=50000, pgid=50000, start_ticks=100)
        with patch.object(runner, "allocation"), patch.object(subprocess, "Popen", return_value=process) as spawn, patch.object(memory, "identity", return_value=identity), patch.object(memory, "cleanup_owned") as cleanup, self.assertRaises(subprocess.TimeoutExpired):
            runner.run_seed(self.plan, self.pin, 0, time.monotonic() + 3000, self.bound)
        cleanup.assert_called_once_with(process, identity, self.probe)
        self.assertEqual(spawn.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], self.plan["gpu_uuid"])
        self.assertIn(str(runner.SELF), spawn.call_args.args[0])
        self.assertLessEqual(process.wait.call_args.kwargs["timeout"], 860)
        self.assertTrue((self.root / "run/seed0/stage_failure.json").exists())

    def test_cleanup_failure_preserves_both_errors_and_no_release(self):
        (self.root / "run").mkdir()
        process = Mock(pid=50000)
        process.wait.return_value = 1
        identity = dict(pid=50000, pgid=50000, start_ticks=100)
        with patch.object(runner, "allocation"), patch.object(subprocess, "Popen", return_value=process), patch.object(memory, "identity", return_value=identity), patch.object(memory, "cleanup_owned", side_effect=RuntimeError("owned cleanup failed")), self.assertRaisesRegex(RuntimeError, "cleanup"):
            runner.run_seed(self.plan, self.pin, 0, time.monotonic() + 3000, self.bound)
        directory = self.root / "run/seed0"
        self.assertTrue((directory / "stage_failure.json").exists())
        self.assertTrue((directory / "cleanup_failure.json").exists())
        self.assertFalse((directory / "released.json").exists())

    def test_completed_requires_three_distinct_sequential_released_processes(self):
        self.make_complete()
        released_path = self.root / "run/seed0/released.json"
        released = memory.read(released_path)
        released["ended"] = 12.0
        released_path.write_bytes(memory.encoded(released))
        with self.assertRaisesRegex(ValueError, "chronology"):
            runner.validate_completed(self.plan, self.pin, self.bound)

    def test_missing_release_blocks_collection_before_core_admit(self):
        complete_pin = self.make_complete()
        (self.root / "run/seed2/released.json").unlink()
        with patch.object(runner, "verify", return_value=(self.plan, self.bound)), patch.object(self.core, "admit") as admit, self.assertRaises(FileNotFoundError):
            runner.collect(self.root, self.pin, complete_pin, self.home / "collected")
        admit.assert_not_called()
        self.assertFalse(self.root.with_name(self.root.name + ".collection_claim.json").exists())

    def test_collect_once_real_core_raw_rejects_all72_not_an_error(self):
        complete_pin = self.make_complete()
        out = self.home / "collected"
        with patch.object(runner, "verify", return_value=(self.plan, self.bound)), patch.object(self.core, "admit", wraps=self.core.admit) as admit:
            result = runner.collect(self.root, self.pin, complete_pin, out)
            self.assertEqual(admit.call_count, 3)
            for call in admit.call_args_list:
                self.assertEqual(len(call.args[1]), 24)
                self.assertEqual(call.args[1][0]["raw"], '  {"fixture":"not a production record"}\n')
            with self.assertRaises(FileExistsError):
                runner.collect(self.root, self.pin, complete_pin, self.home / "another_collected")
            self.assertEqual(admit.call_count, 3)
        report = memory.read(out / "replay_report.json")
        self.assertEqual(report["costs"]["calls"], 72)
        self.assertEqual(report["costs"]["fits"], 0)
        for seed in runner.SEEDS:
            self.assertEqual(result["counts"][str(seed)]["admitted"], 0)
            self.assertEqual(result["counts"][str(seed)]["rejected"], 24)
            self.assertEqual(result["counts"][str(seed)]["opportunities"], 24)
            self.assertEqual(result["counts"][str(seed)]["source_population"], 96)
            self.assertEqual(len(report["native_source_joins"][str(seed)]), 24)
            self.assertEqual(report["costs_per_seed"][str(seed)]["calls"], 24)

    def test_admission_failure_consumes_claim_no_retry(self):
        complete_pin = self.make_complete()
        out = self.home / "bad_collect"
        with patch.object(runner, "verify", return_value=(self.plan, self.bound)), patch.object(self.core, "admit", side_effect=ValueError("CPU admission mismatch")), self.assertRaisesRegex(ValueError, "admission mismatch"):
            runner.collect(self.root, self.pin, complete_pin, out)
        self.assertTrue((out / "collection_failure.json").exists())
        self.assertTrue(self.root.with_name(self.root.name + ".collection_claim.json").exists())
        self.assertFalse((out / "collection.json").exists())

    def test_controller_fixed_order_no_early_admit(self):
        with patch.object(runner, "verify", return_value=(self.plan, self.bound)), patch.object(runner, "allocation"), patch.object(runner, "run_seed") as run, patch.object(runner, "validate_completed", return_value={}), patch.object(self.core, "admit", side_effect=AssertionError("too early")), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            runner.controller(self.root, self.pin, allow_gpu=True)
        self.assertEqual([call.args[2] for call in run.call_args_list], [0, 1, 2])
        complete = memory.read(self.root / "capture_complete.json")
        self.assertEqual(complete["calls"], 72)
        self.assertFalse(complete["admitted"])
        self.assertEqual(complete["updates"], 0)

    def test_controller_failure_stops_next_seed_preserves_failure(self):
        with patch.object(runner, "verify", return_value=(self.plan, self.bound)), patch.object(runner, "allocation"), patch.object(runner, "run_seed", side_effect=RuntimeError("CPU native failure")) as run, patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), self.assertRaises(RuntimeError):
            runner.controller(self.root, self.pin, allow_gpu=True)
        self.assertEqual(run.call_count, 1)
        self.assertTrue((self.root / "controller_failure.json").exists())
        self.assertFalse((self.root / "capture_complete.json").exists())

    def test_no_model_or_gpu_entry_without_flags_and_empty_controller_cvd(self):
        with self.assertRaises(ValueError):
            runner.prepare(self.root, "missing", "pin")
        with self.assertRaises(ValueError):
            runner.worker(self.root, "pin", 0)
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES="GPU-occupied"), self.assertRaises(ValueError):
            runner.controller(self.root, "pin", allow_gpu=True)

    def test_no_fit_old_collect_or_expected_target_calls(self):
        tree = ast.parse(runner.SELF.read_text())
        attrs = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(attrs & {"fit_arm", "run_training", "expected", "score_row", "collect", "controller", "worker"})
        self.assertEqual(memory.digest(self.core.__file__), runner.CORE_PIN)
        self.assertEqual(memory.digest(self.native.SELF), runner.NATIVE_PIN)


if __name__ == "__main__":
    unittest.main()
