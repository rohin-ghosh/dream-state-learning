"""Pure CPU alignment runner fixtures; no model, GPU or native result access."""
import ast
import copy
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
spec = importlib.util.spec_from_file_location("alignment_runner_test", "/tmp/astra_parenting_alignment_run_20260913.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
memory = runner.runtime()


class Tokenizer:
    chat_template = "CPU_TOKENIZER_NOT_NATIVE"

    def encode(self, text, add_special_tokens=False):
        pieces = re.findall(r"<\|im_start\|>|<\|im_end\|>|[A-Za-z_]+|[0-9]+|[^\w\s]|\s", text)
        assert "".join(pieces) == text
        return [zlib.crc32(piece.encode()) + 1 for piece in pieces]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        messages = copy.deepcopy(messages)
        if messages[0]["role"] != "system":
            messages.insert(0, dict(role="system", content="You are a helpful assistant."))
        text = "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text


class Backend:
    def __init__(self, plan, probe, route, *, valid_action=True, finish="stop", malformed_decode=False, close_error=False):
        self.tokenizer = Tokenizer()
        self.route = route
        self.valid_action, self.finish = valid_action, finish
        self.malformed_decode, self.close_error = malformed_decode, close_error
        self.closed, self.requests = False, []

    def generate(self, request):
        self.requests.append(copy.deepcopy(request))
        started = time.monotonic()
        kind = request["core_request"]["kind"]
        if kind == "wake" and self.valid_action:
            raw = ' {"action":{"kind":"TRY","values":[2,5,9]},"note":{},"prediction":true} '
        else:
            raw = "  CPU fixture malformed child output\n"
        tokens = [7] * (request["params"]["max_tokens"] if self.finish == "length" else 1)
        return dict(request["native"], text=raw, decoded_output="BROKEN_DECODE" if self.malformed_decode else raw,
                    actual_prompt_token_ids=request["native"]["prompt_token_ids"], output_token_ids=tokens,
                    finish_reason=self.finish, stop_reason=None, started=started, ended=time.monotonic(), lora_request=self.route)

    def close(self):
        self.closed = True
        if self.close_error:
            raise ValueError("fixture backend closure failure")


class AlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        core_path = Path("/tmp/astra_parenting_alignment_core_20260913.py")
        cls.core = runner.load(dict(path=str(core_path), sha256=runner.CORE_PIN), "core_fixture", runner.CORE_PIN)
        cls.native = memory.load(dict(path="/tmp/astra_level1_real_record_run_20260913.py", sha256=runner.NATIVE_PIN), "alignment_native_fixture")
        cls.public = memory.load(dict(path="/tmp/astra_birth_skill_probe_run_20260913.py", sha256=runner.PUBLIC_PIN), "alignment_public_fixture")
        cls.parented = memory.load(dict(path="/tmp/astra_parented_record_run_20260913.py", sha256=runner.PARENTED_PIN), "alignment_parented_fixture")
        cls.capture_runtime = memory.load(dict(path="/tmp/astra_own_source_replay_capture_20260913.py", sha256=runner.CAPTURE_PIN), "alignment_capture_fixture")
        cls.dependencies = cls.core.load_dependencies("/tmp/astra_level1_real_record_source_20260913_attempt1",
            protocol_path="/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_PARENTING_ALIGNMENT_DEV_2026-09-13.md")
        cls.manifest = cls.core.build_manifest(cls.dependencies, prior_ids=["fixture_previous_namespace"])

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="alignment_runner_cpu_")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / "new_alignment"
        original_root = self.core.root_binding(0)
        self.producer = {key: original_root[key] for key in ("learner_seed", "parent_plan_sha256", "adapter")}
        self.producer["adapter_files"] = {"adapter_model.safetensors": original_root["adapter_model_sha256"]}
        self.producer.update(model="CPU_MODEL", model_files={"base": "pin"})
        self.original = dict(root=str(self.home / "original"), learner_seed=0, model="CPU_MODEL", model_files={"base": "pin"},
            environment={}, python=os.path.abspath(sys.executable), python_sha256=runner.digest(sys.executable),
            chat_template=Tokenizer.chat_template, engine=self.native.ENGINE, params=self.public.PARAMS)
        self.api = SimpleNamespace(**vars(memory))
        self.api.offline = Mock()
        self.api.cleanup_owned = Mock()
        self.api.identity = Mock(return_value=dict(pid=1234, pgid=1234, start_ticks=222))
        self.probe = SimpleNamespace(render=self.public.render, native_tokenizer=Mock(return_value=Tokenizer()), gpu_state=Mock(return_value=True))
        self.formation = SimpleNamespace(tree=self.tree, validate_response=self.native.validate_response)
        self.bound = dict(memory=self.api, core=self.core, probe=self.probe, formation=self.formation, dependencies=self.dependencies,
            manifest=self.manifest, producer=self.producer, original=self.original, original_bytes=memory.encoded(self.original),
            provenance={"fixture": "original-source"}, capture_runtime=self.capture_runtime, parented=self.parented)
        self.fixture_source = self.home / "fixture_source.py"
        self.fixture_source.write_text("fixture_only = True\n")
        binding = dict(path=str(self.fixture_source), sha256=runner.digest(self.fixture_source))
        self.spec = dict(runner_sha256=runner.digest(runner.SELF), seed=0, source_root=str(self.home / "source"),
                         gpu_index=0, gpu_uuid="GPU-CPU-FIXTURE", expected_boot_id="0" * 36, lease_end=time.time() + 100000)
        self.spec.update({key: copy.deepcopy(binding) for key in
            ("core", "protocol", "capture_runtime", "parented_runtime", "parent_source", "native", "public", "archive", "prior_task_ids")})
        self.sources = {"sources/fixture.py": self.fixture_source}
        spec_path = self.home / "spec.json"
        memory.write(spec_path, self.spec)
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "bind", return_value=self.bound), \
             patch.object(runner, "source_files", return_value=self.sources), patch.object(runner, "allocation"), \
             patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            result = runner.prepare(self.root, spec_path, runner.digest(spec_path), allow_native=True)
        self.plan, self.pin = memory.read(self.root / "plan.json"), result["plan_sha256"]

    def tree(self, path):
        if str(path) == self.producer["adapter"]:
            return self.producer["adapter_files"]
        return {str(item.relative_to(path)): runner.digest(item) for item in sorted(Path(path).rglob("*")) if item.is_file()}

    def stage(self, arm, *, valid_action=True, finish="stop"):
        if not (self.root / "controller_started.json").exists():
            entry = time.monotonic()
            memory.write(self.root / "controller_started.json", dict(plan_sha256=self.pin, pid=os.getpid(), monotonic=entry,
                         deadline=entry + runner.SECONDS, seconds=runner.SECONDS))
        (self.root / "run").mkdir(exist_ok=True)
        directory = self.root / "run" / arm
        directory.mkdir()
        index = runner.ARMS.index(arm)
        identity = dict(pid=1000 + index, pgid=1000 + index, start_ticks=100 + index)
        command = [self.plan["python"], "-B", str(runner.SELF), "worker", "--root", str(self.root), "--plan-sha256", self.pin,
                   "--arm", arm, "--allow-gpu"]
        memory.write(directory / "launch.json", dict(identity=identity, arm=arm, plan_sha256=self.pin, command=command, time=time.time(), monotonic=time.monotonic()))
        memory.write(directory / "started.json", dict(pid=identity["pid"], pgid=identity["pgid"], arm=arm, plan_sha256=self.pin, time=time.time(), monotonic=time.monotonic()))
        backend = Backend(self.plan, self.probe, runner.route_for(self.plan, self.bound), valid_action=valid_action, finish=finish)
        runner.capture_arm(self.plan, self.bound, arm, backend_factory=lambda *args: backend)
        memory.write(directory / "worker_done.json", dict(arm=arm, plan_sha256=self.pin, monotonic=time.monotonic()))
        memory.write(directory / "exit.json", dict(identity=identity, returncode=0, monotonic=time.monotonic()))
        memory.write(directory / "released.json", dict(identity=identity, arm=arm, group_absent=True, gpu_vacant=True, time=time.time(), monotonic=time.monotonic()))
        return directory, backend

    def complete(self, valid_action=True):
        for arm in runner.ARMS:
            self.stage(arm, valid_action=valid_action)
        checked = runner.validate_completed(self.plan, self.bound, self.pin, Tokenizer())
        memory.write(self.root / "capture_complete.json", dict(scope=runner.SCOPE, plan_sha256=self.pin, stages=checked["inventory"],
                     calls=sum(cost["calls"] for cost in checked["costs"].values()), fits=0, updates=0, parent_model_calls=0,
                     collected=False, elapsed_seconds=100))
        return runner.digest(self.root / "capture_complete.json")

    def test_prepared_static_prompts_original_parent_and_no_fits(self):
        self.assertEqual(self.plan["states"], [runner.state_for(0, arm) for arm in runner.ARMS])
        self.assertEqual(self.plan["limits"]["calls_per_seed"], 104)
        self.assertEqual(self.plan["limits"]["campaign_calls"], 312)
        self.assertEqual(self.plan["limits"]["fits"], 0)
        self.assertEqual(len(memory.read(self.root / "preflight.json")["static_prompts"]), 18)
        self.assertEqual((self.root / "original_plan.json").read_bytes(), self.bound["original_bytes"])
        self.assertFalse((self.root / "run").exists())

    def test_prepare_and_verify_pin_drift(self):
        with patch.object(runner, "bind", return_value=self.bound), patch.object(runner, "source_files", return_value=self.sources):
            runner.verify(self.root, self.pin)
            changed = copy.deepcopy(self.plan)
            changed["producers"]["0"]["adapter"] = "/REPAIR_DESCENDANT"
            (self.root / "plan.json").write_bytes(memory.encoded(changed))
            with self.assertRaisesRegex(ValueError, "prepared plan"):
                runner.verify(self.root, runner.digest(self.root / "plan.json"))
            (self.root / "plan.json").write_bytes(memory.encoded(self.plan))
            (self.root / "manifest.json").write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "input changed"):
                runner.verify(self.root, self.pin)

    def test_raw_malformed_restatements_and_records_do_not_abort(self):
        directory, backend = self.stage("ALIGNED")
        capture, audit, cost = runner.replay_arm(self.plan, self.bound, "ALIGNED", Tokenizer())
        self.assertEqual(cost["calls"], 36)
        self.assertEqual(capture["readout"]["EXECUTED"], 16)
        self.assertEqual(capture["readout"]["RECORD_FAITHFUL"], 0)
        self.assertEqual(capture["readout"]["RESTATE"], 0)
        self.assertEqual(len(capture["records"]), 16)
        self.assertTrue(audit["consistent"])
        self.assertTrue(backend.closed)
        calls = memory.read(directory / "core_calls.json")
        self.assertEqual(calls[0]["response"]["raw"], "  CPU fixture malformed child output\n")
        wake = next(call for call in calls if call["request"]["kind"] == "wake")
        self.assertIn(calls[0]["response"]["raw"], wake["request"]["input_messages"][0]["content"])

    def test_invalid_actions_keep_all16_uncalled_record_slots(self):
        self.stage("NO_PARENT", valid_action=False)
        capture, audit, cost = runner.replay_arm(self.plan, self.bound, "NO_PARENT", Tokenizer())
        self.assertEqual(cost["calls"], 16)
        self.assertEqual(capture["readout"]["record_not_called"], 16)
        self.assertEqual(capture["readout"]["EXECUTED"], 0)
        self.assertEqual(len(capture["records"]), 16)
        self.assertEqual(len(capture["contacts"]), 0)
        self.assertTrue(audit["consistent"])

    def test_length_finish_kept_no_retry_no_execution(self):
        _, backend = self.stage("SWAPPED", finish="length")
        capture, _, costs = runner.replay_arm(self.plan, self.bound, "SWAPPED", Tokenizer())
        self.assertEqual(costs["calls"], 20)
        self.assertEqual(len(backend.requests), 20)
        self.assertEqual(capture["readout"]["finishes"], {"length": 20})
        self.assertEqual(capture["readout"]["record_not_called"], 16)

    def test_native_decode_fault_not_ordinary_refusal_and_raw_preserved(self):
        directory = self.root / "run/ALIGNED"
        directory.mkdir(parents=True)
        backend = Backend(self.plan, self.probe, runner.route_for(self.plan, self.bound), malformed_decode=True)
        with self.assertRaises(self.parented.NativeCaptureFailure):
            runner.capture_arm(self.plan, self.bound, "ALIGNED", backend_factory=lambda *args: backend)
        self.assertTrue(backend.closed)
        self.assertEqual(len(backend.requests), 1)
        self.assertTrue((directory / "00.response.json").exists())
        self.assertTrue((directory / "capture_failure.json").exists())
        self.assertFalse((directory / "closed.json").exists())

    def test_backend_close_failure_preserved(self):
        directory = self.root / "run/ALIGNED"
        directory.mkdir(parents=True)
        backend = Backend(self.plan, self.probe, runner.route_for(self.plan, self.bound), malformed_decode=True, close_error=True)
        with self.assertRaisesRegex(ValueError, "closure"):
            runner.capture_arm(self.plan, self.bound, "ALIGNED", backend_factory=lambda *args: backend)
        self.assertTrue((directory / "capture_failure.json").exists())
        self.assertTrue((directory / "backend_close_failure.json").exists())

    def test_three_actual_core_states104calls_and_partial_vector(self):
        self.complete()
        checked = runner.validate_completed(self.plan, self.bound, self.pin, Tokenizer())
        self.assertEqual([cost["calls"] for cost in checked["costs"].values()], [36, 36, 32])
        self.assertEqual(sum(cost["calls"] for cost in checked["costs"].values()), 104)
        summary = self.core.summarize(checked["captures"], self.dependencies)
        self.assertFalse(summary["gate"]["complete"])
        self.assertFalse(summary["fit_authorized"])

    def test_all_failure_states56calls_still_complete(self):
        self.complete(valid_action=False)
        checked = runner.validate_completed(self.plan, self.bound, self.pin, Tokenizer())
        self.assertEqual([cost["calls"] for cost in checked["costs"].values()], [20, 20, 16])
        self.assertTrue(all(capture["readout"]["record_not_called"] == 16 for capture in checked["captures"]))

    def test_missing_exit_or_release_blocks_collection(self):
        self.complete()
        path = self.root / "run/SWAPPED/exit.json"
        old = path.read_bytes()
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            runner.validate_completed(self.plan, self.bound, self.pin, Tokenizer())
        path.write_bytes(old)
        release = self.root / "run/NO_PARENT/released.json"
        value = memory.read(release)
        value["gpu_vacant"] = False
        release.write_bytes(memory.encoded(value))
        with self.assertRaisesRegex(ValueError, "custody"):
            runner.validate_completed(self.plan, self.bound, self.pin, Tokenizer())

    def test_closed_raw_or_uncalled_slot_tampering_detected(self):
        directory, _ = self.stage("ALIGNED", valid_action=False)
        capture_path = directory / "capture.json"
        capture = memory.read(capture_path)
        capture["records"].pop()
        capture["capture_sha256"] = self.core.digest({key: value for key, value in capture.items() if key != "capture_sha256"})
        capture_path.write_bytes(memory.encoded(capture))
        closed_path = directory / "closed.json"
        closed = memory.read(closed_path)
        closed["files"]["capture.json"] = runner.digest(capture_path)
        closed_path.write_bytes(memory.encoded(closed))
        with self.assertRaises(ValueError):
            runner.replay_arm(self.plan, self.bound, "ALIGNED", Tokenizer())

    def test_failed_gpu_precheck_never_spawns(self):
        self.probe.gpu_state.return_value = False
        with patch.object(runner, "allocation"), patch.object(subprocess, "Popen") as spawn, self.assertRaisesRegex(ValueError, "precheck"):
            runner.run_arm(self.plan, self.bound, self.pin, "ALIGNED", time.monotonic() + 1000)
        spawn.assert_not_called()

    def test_worker_uuid_and_owned_cleanup_custody(self):
        (self.root / "run").mkdir()
        process = Mock(pid=1234)
        process.wait.return_value = 0
        with patch.object(runner, "allocation"), patch.object(subprocess, "Popen", return_value=process) as spawn, patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            runner.run_arm(self.plan, self.bound, self.pin, "ALIGNED", time.monotonic() + 1000)
        self.assertEqual(spawn.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], self.plan["gpu_uuid"])
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        self.api.cleanup_owned.assert_called_once()
        self.assertEqual(memory.read(self.root / "run/ALIGNED/exit.json")["returncode"], 0)

    def test_worker_failure_and_release_failure_both_preserved(self):
        (self.root / "run").mkdir()
        process = Mock(pid=1234)
        process.wait.side_effect = subprocess.TimeoutExpired("fixture", 10)
        self.api.cleanup_owned.side_effect = ValueError("fixture release failed")
        with patch.object(runner, "allocation"), patch.object(subprocess, "Popen", return_value=process), self.assertRaisesRegex(ValueError, "release"):
            runner.run_arm(self.plan, self.bound, self.pin, "ALIGNED", time.monotonic() + 1000)
        self.assertTrue((self.root / "run/ALIGNED/stage_failure.json").exists())
        self.assertTrue((self.root / "run/ALIGNED/cleanup_failure.json").exists())
        self.assertFalse((self.root / "run/ALIGNED/released.json").exists())

    def test_collect_once_no_generation_and_raw_outcomes_preserved(self):
        completion = self.complete(valid_action=False)
        output = self.home / "collected"
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.plan, self.bound)), \
             patch.object(self.formation, "Native", create=True, side_effect=AssertionError("no native in collection")):
            runner.collect(self.root, self.pin, completion, output)
            with self.assertRaises(FileExistsError):
                runner.collect(self.root, self.pin, completion, self.home / "second_collection")
        report = memory.read(output / "alignment_report.json")
        self.assertEqual(report["costs"]["calls"], 56)
        self.assertEqual(report["costs"]["fits"], 0)
        self.assertEqual(len(report["captures"]), 3)
        self.assertFalse(report["fit_authorized"])
        self.assertTrue(all(len(capture["records"]) == 16 for capture in report["captures"]))

    def test_collection_fault_consumes_claim(self):
        completion = self.complete(valid_action=False)
        output = self.home / "bad_collection"
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.plan, self.bound)), \
             patch.object(self.core, "summarize", side_effect=ValueError("fixture summary fault")), self.assertRaisesRegex(ValueError, "summary"):
            runner.collect(self.root, self.pin, completion, output)
        self.assertTrue((output / "collection_failure.json").exists())
        self.assertTrue(self.root.with_name(self.root.name + ".collection_claim.json").exists())

    def test_controller_stops_infrastructure_failure_not_next_arm(self):
        with patch.object(runner, "runtime", return_value=self.api), patch.object(runner, "verify", return_value=(self.plan, self.bound)), \
             patch.object(runner, "allocation"), patch.object(runner, "run_arm", side_effect=ValueError("fixture infrastructure fault")) as run, \
             patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), self.assertRaisesRegex(ValueError, "infrastructure"):
            runner.controller(self.root, self.pin, allow_gpu=True)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[3], "ALIGNED")
        self.assertTrue((self.root / "controller_failure.json").exists())

    def test_flags_unknown_seed_arm_and_protocol_pins(self):
        with self.assertRaises(ValueError):
            runner.controller("missing", "missing")
        with self.assertRaises(ValueError):
            runner.prepare("missing", "missing", "missing")
        with self.assertRaises(ValueError):
            runner.worker("missing", "missing", "REPAIR", allow_gpu=True)
        with self.assertRaises(ValueError):
            runner.state_for(True, "ALIGNED")
        path = "/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_PARENTING_ALIGNMENT_DEV_2026-09-13.md"
        self.assertEqual(runner.digest(path), runner.PROTOCOL_PIN)
        self.assertEqual(runner.digest(self.parented.SELF), runner.PARENTED_PIN)
        self.assertEqual(runner.digest(self.capture_runtime.SELF), runner.CAPTURE_PIN)
        self.assertEqual(runner.digest("/tmp/astra_parenting_alignment_core_20260913.py"), runner.CORE_PIN)

    def test_entry_clocks_charge_runtime_bootstrap(self):
        cases = [(runner.prepare, (self.root, "unused", "unused"), {"allow_native": True}, 180),
                 (runner.controller, (self.root, self.pin), {"allow_gpu": True}, 3600),
                 (runner.collect, (self.root, self.pin, "unused", self.home / "out"), {}, 180)]
        for function, args, kwargs, cap in cases:
            with self.subTest(function=function.__name__), patch.object(runner, "runtime", return_value=self.api), \
                 patch.object(runner.time, "monotonic", side_effect=[100.0, 107.0]), \
                 patch.object(self.api, "budget", side_effect=ValueError("entry clock sentinel")) as budget, \
                 patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), self.assertRaisesRegex(ValueError, "clock sentinel"):
                function(*args, **kwargs)
            budget.assert_called_once_with(cap - 7.0)

    def test_transitive_source_snapshot_uses_actual_frozen_pins(self):
        source = runner.load(dict(path="/tmp/astra_own_source_replay_core_20260913.py", sha256=runner.PARENT_SOURCE_PIN),
                             "snapshot_parent_source", runner.PARENT_SOURCE_PIN)
        material, _ = source.dependencies("/tmp/astra_level1_real_record_source_20260913_attempt1")
        bound = dict(self.bound, parent_source=source, parent_material=material)
        spec = dict(self.spec, source_root="/tmp/astra_level1_real_record_source_20260913_attempt1")
        paths = runner.source_files(spec, bound)
        self.assertEqual(paths["sources/astra_real_record_memory_run_20260913.py"], memory.SELF)
        for relative, checksum in material.PINS.items():
            self.assertEqual(runner.digest(paths["source_snapshot/" + relative]), checksum)
        for relative, checksum in self.dependencies.manifest["full_source_sha256"].items():
            self.assertEqual(runner.digest(paths["source_snapshot/" + relative]), checksum)

    def test_dynamic_native_prompt_and_timing_tamper_rejected(self):
        directory, _ = self.stage("NO_PARENT", valid_action=False)
        for filename, field, replacement in (("00.request.json", "messages", []),
                                              ("00.response.json", "started", -1.0)):
            with self.subTest(field=field):
                path = directory / filename
                original = path.read_bytes()
                closed_raw = (directory / "closed.json").read_bytes()
                record = memory.read(path)
                record[field] = replacement
                path.write_bytes(memory.encoded(record))
                closed = memory.read(directory / "closed.json")
                closed["files"][filename] = runner.digest(path)
                (directory / "closed.json").write_bytes(memory.encoded(closed))
                with self.assertRaises(ValueError):
                    runner.replay_arm(self.plan, self.bound, "NO_PARENT", Tokenizer())
                path.write_bytes(original)
                (directory / "closed.json").write_bytes(closed_raw)

    def test_boolean_exit_is_not_zero_exit(self):
        for arm in runner.ARMS:
            self.stage(arm, valid_action=False)
        path = self.root / "run" / "ALIGNED" / "exit.json"
        record = memory.read(path)
        record["returncode"] = False
        path.write_bytes(memory.encoded(record))
        with self.assertRaisesRegex(ValueError, "custody"):
            runner.validate_completed(self.plan, self.bound, self.pin, Tokenizer())

    def test_released_stages_must_fit_controller_entry_window(self):
        for arm in runner.ARMS:
            self.stage(arm, valid_action=False)
        path = self.root / "controller_started.json"
        started = memory.read(path)
        started["monotonic"] += runner.SECONDS + 1
        started["deadline"] = started["monotonic"] + runner.SECONDS
        path.write_bytes(memory.encoded(started))
        with self.assertRaisesRegex(ValueError, "chronology"):
            runner.validate_completed(self.plan, self.bound, self.pin, Tokenizer())

    def test_no_training_or_old_controller_calls(self):
        tree = ast.parse(runner.SELF.read_text())
        calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
        forbidden = {"run_training", "fit_arm", "TrainConfig", "collect", "controller", "run_state", "audit_capture", "admit"}
        self.assertFalse([call for call in calls if isinstance(call, ast.Attribute) and call.attr in forbidden])
        self.assertNotIn("setattr(", runner.SELF.read_text())


if __name__ == "__main__":
    unittest.main()
