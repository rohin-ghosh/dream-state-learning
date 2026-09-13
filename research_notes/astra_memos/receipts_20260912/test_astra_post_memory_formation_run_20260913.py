"""Mocked native boundaries with the frozen original renderer, validator, and new core."""
import ast
import copy
import importlib.util
import json
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

import astra_post_memory_formation_run_20260913 as runner


class Tokenizer:
    chat_template = "CPU_ONLY_TOY_TEMPLATE"

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        prefix = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
        text = prefix + "".join(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n" for message in messages)
        if add_generation_prompt:
            text += "<|im_start|>assistant\n"
        return self.encode(text) if tokenize else text

    def encode(self, text, add_special_tokens=False):
        return [ord(character) for character in text]


class Backend:
    instances = []
    mode = "valid"

    def __init__(self, plan, probe, route):
        self.tokenizer, self.route, self.calls, self.closed = Tokenizer(), route, [], False
        self.instances.append(self)

    def generate(self, request):
        self.calls.append(copy.deepcopy(request))
        core_request = request["core_request"]
        if self.mode == "raise":
            raise RuntimeError("mock native infrastructure failure")
        if core_request["kind"] == "wake":
            raw = "PREDICT: F\nACT: TRY 1,4,-2" if core_request["tick"] == 1 else "PREDICT: T\nACT: TRY 2,5,-2"
            if self.mode == "invalid":
                raw = "unexecutable"
        else:
            facts = json.loads(re.findall(r"^Observed fields: (.*)$", core_request["input_messages"][0]["content"], re.MULTILINE)[-1])
            relation = "unavailable" if facts["predicted"] is None else "matched" if facts["predicted"] == facts["observed"] else "mismatched"
            raw = json.dumps(dict(try_value=facts["values"])) if self.mode == "wrong" else json.dumps(
                {"try": facts["values"], "observed": facts["observed"], "predicted": facts["predicted"], "relation": relation})
            if self.mode == "fenced":
                raw = "```json\n" + raw + "\n```"
        response = dict(**request["native"], actual_prompt_token_ids=request["native"]["prompt_token_ids"],
                        text=raw, decoded_output=raw, output_token_ids=[3, 4], finish_reason="stop", stop_reason=None,
                        started=1.0, ended=1.01, lora_request=self.route)
        if self.mode == "route":
            response["lora_request"] = dict(self.route, path="/wrong")
        if self.mode == "length":
            response.update(finish_reason="length", output_token_ids=[3] * request["params"]["max_tokens"])
        return response

    def close(self):
        self.closed = True


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real_load = staticmethod(runner.load)
        cls.core = runner.load(dict(path="/tmp/astra_post_memory_formation_core_20260913.py", sha256=runner.CORE_PIN), "test_core", runner.CORE_PIN)
        cls.formation = runner.load(dict(path="/tmp/astra_level1_real_record_run_20260913.py", sha256=runner.FORMATION_PIN), "test_formation", runner.FORMATION_PIN)
        cls.original_memory = runner.load(dict(path="/tmp/astra_real_record_memory_run_20260913.py", sha256=runner.MEMORY_PIN), "test_memory", runner.MEMORY_PIN)
        cls.original_probe = runner.load(dict(path="/tmp/astra_birth_skill_probe_run_20260913.py", sha256=cls.formation.PUBLIC_SHA256), "test_probe")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="post_memory_runner_cpu_")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root, self.upstream = self.home / "new", self.home / "memory"
        self.upstream.mkdir()
        self.collection = self.home / "memory_collected"
        self.collection.mkdir()
        self.routes = {}
        self.stages = list(self.original_memory.STAGES)
        for index, stage in enumerate(self.stages):
            directory = self.upstream / "run" / stage
            directory.mkdir(parents=True)
            runner.write(directory / "launch.json", dict(identity=dict(pid=80000000 + index, pgid=80000000 + index, start_ticks=1)))
            if stage.endswith("_fit"):
                arm = stage.split("_")[0]
                adapter = directory / "adapter"
                adapter.mkdir()
                (adapter / "adapter_model.safetensors").write_bytes(b"TOY_NOT_NATIVE_" + arm.encode())
                self.routes[arm] = dict(name="real_record_memory_" + arm.lower(), id=1, path=str(adapter))
        runner.write(self.upstream / "controller_started.json", dict(pid=81000000))
        self.memory_plan = dict(root=str(self.upstream), specification=dict(seed=0, fit_seed=0), status="WRITE_AVAILABLE",
                                stages=self.stages, calls_per_arm=76, updates_per_arm=64, model=str(self.home / "model"),
                                model_files={"model": "bound"}, source="/data/home/rohing/dream-state", environment={"mock": True},
                                chat_template=Tokenizer.chat_template)
        runner.write(self.upstream / "plan.json", self.memory_plan)
        self.upstream_plan_sha = runner.digest(self.upstream / "plan.json")
        complete = dict(plan_sha256=self.upstream_plan_sha, stages={}, scored=False, status="WRITE_AVAILABLE",
                        elapsed_seconds=12.0, calls=152, updates=128)
        runner.write(self.upstream / "capture_complete.json", complete)
        self.upstream_complete_sha = runner.digest(self.upstream / "capture_complete.json")
        self.scores = dict(plan_sha256=self.upstream_plan_sha, completion_sha256=self.upstream_complete_sha,
                           seed=0, status="WRITE_AVAILABLE", native_capture_custody_checked=True, automatic_pass=False,
                           calls=152, updates=128, summary={"WRITE_minus_LR0": -10, "canary_regressions": 12})
        runner.write(self.collection / "scores.json", self.scores)
        runner.write(self.collection / "collection.json", dict(scores_sha256=runner.digest(self.collection / "scores.json"),
                                                              completion_sha256=self.upstream_complete_sha))
        runner.write(self.upstream.with_name(self.upstream.name + ".collection_claim.json"),
                     dict(plan_sha256=self.upstream_plan_sha, out=str(self.collection), retry=False))
        self.probe = SimpleNamespace(render=self.original_probe.render, native_tokenizer=Mock(return_value=Tokenizer()),
                                     gpu_state=Mock(return_value=True), group_alive=Mock(return_value=False), cleanup=Mock(return_value=True))
        self.memory_bound = dict(formation=self.formation, probe=self.probe,
                                 capture={"episodes": [{"episode_id": value} for value in self.core.load_v2().episode_ids()]})
        self.memory = SimpleNamespace(STAGES=self.stages, OUTER_SECONDS=3600,
                                      verify=Mock(return_value=(self.memory_plan, self.memory_bound)),
                                      validate_completed=Mock(return_value={}), route_for=Mock(side_effect=lambda plan, bound, arm: self.routes[arm]),
                                      protected_inputs=Mock(return_value=[self.upstream]), cleanup_owned=self.original_memory.cleanup_owned)
        self.spec = dict(runner_sha256=runner.digest(runner.SELF),
                         core=dict(path="/tmp/astra_post_memory_formation_core_20260913.py", sha256=runner.CORE_PIN),
                         memory_runtime=dict(path="/tmp/astra_real_record_memory_run_20260913.py", sha256=runner.MEMORY_PIN),
                         memory=dict(root=str(self.upstream), plan_sha256=self.upstream_plan_sha, completion_sha256=self.upstream_complete_sha,
                                     collection=dict(path=str(self.collection / "collection.json"), sha256=runner.digest(self.collection / "collection.json")),
                                     scores=dict(path=str(self.collection / "scores.json"), sha256=runner.digest(self.collection / "scores.json"))),
                         seed=0, node="node2", gpu_index=3, gpu_uuid="GPU-CPU-FIXTURE", expected_boot_id="0" * 36, lease_end=time.time() + 86400)
        self.loader_patch = patch.object(runner, "load", side_effect=lambda record, name, expected=None:
                                  self.memory if name == "memory" else self.real_load(record, name, expected))
        self.loader_patch.start()
        self.addCleanup(self.loader_patch.stop)
        self.environment_patch = patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""})
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)
        Backend.instances, Backend.mode = [], "valid"

    def prepare(self, pretty=False):
        spec_path = self.home / "spec.json"
        spec_path.write_text(json.dumps(self.spec, indent=2) if pretty else runner.encoded(self.spec).decode())
        with patch.object(runner, "check_allocation"):
            result = runner.prepare(str(self.root), str(spec_path), runner.digest(spec_path), allow_native=True)
        plan, bound = runner.verify(str(self.root), result["plan_sha256"])
        return plan, bound, result["plan_sha256"]

    def simulate_state(self, plan, plan_sha, state, deadline, bound):
        directory = self.root / "run" / state
        directory.mkdir()
        now = time.time()
        process = dict(pid=82000000 + list(runner.STATES).index(state), pgid=82000000 + list(runner.STATES).index(state), start_ticks=1)
        deadline_wall = now + 100
        runner.write(directory / "launch.json", dict(identity=process, state=state, plan_sha256=plan_sha,
                     command=runner.worker_command(plan, plan_sha, state, deadline_wall), deadline_wall=deadline_wall, started=now))
        runner.write(directory / "started.json", dict(identity=process, state=state, plan_sha256=plan_sha, deadline_wall=deadline_wall, started=now))
        (directory / "stdout.log").write_bytes(b"")
        (directory / "stderr.log").write_bytes(b"")
        runner.capture_state(plan, state, bound, backend_factory=Backend)
        runner.write(directory / "released.json", dict(identity=process, state=state, ended=time.time()))

    def completed(self):
        plan, bound, plan_sha = self.prepare()
        actual_identity = runner.identity
        def identities(pid):
            return dict(pid=83000000, pgid=83000000, start_ticks=1) if pid == os.getpid() else actual_identity(pid)
        with patch.object(runner, "run_state", side_effect=self.simulate_state), patch.object(runner, "check_allocation"), \
                patch.object(runner, "identity", side_effect=identities):
            terminal = runner.controller(str(self.root), plan_sha, allow_gpu=True)
        return plan, bound, plan_sha, terminal["completion_sha256"]

    def test_vertical_prepare_cold_pair_replay_collect_once(self):
        plan, bound, plan_sha, complete_sha = self.completed()
        self.assertEqual(len(Backend.instances), 2)
        self.assertTrue(all(backend.closed and len(backend.calls) == 32 for backend in Backend.instances))
        with patch.object(runner, "check_allocation"):
            result = runner.collect(str(self.root), plan_sha, complete_sha, str(self.home / "collected"))
        scores = runner.read(self.home / "collected/scores.json")
        self.assertEqual((scores["calls"], scores["fits"], scores["updates"]), (64, 0, 0))
        self.assertFalse(scores["automatic_pass"])
        self.assertIsNone(scores["outcome_gate"])
        self.assertTrue(scores["comparison"]["paired_by_seed"]["0"]["available"])
        self.assertEqual(result["scores_sha256"], runner.digest(self.home / "collected/scores.json"))
        with self.assertRaisesRegex(ValueError, "claimed"):
            runner.collect(str(self.root), plan_sha, complete_sha, str(self.home / "second_collection"))

    def test_original_upstream_checks_and_negative_scores_do_not_gate(self):
        bound = runner.bind_inputs(self.spec)
        self.memory.verify.assert_called_once_with(self.upstream, self.upstream_plan_sha, native=False)
        self.memory.validate_completed.assert_called_once()
        self.assertEqual(set(bound["routes"]), {"WRITE", "LR0"})
        self.assertEqual(bound["contract"]["outcome_gate"], None)

    def test_explicit_sources_and_strict_spec_validation(self):
        for key, value in (("seed", True), ("seed", 3), ("seed", "1"), ("lease_end", True),
                           ("lease_end", float("nan")), ("gpu_index", False), ("node", "node1"),
                           ("runner_sha256", "0" * 64)):
            changed = copy.deepcopy(self.spec)
            changed[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                runner.validate_spec(changed)
        changed = copy.deepcopy(self.spec)
        changed["core"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "pin"):
            runner.validate_spec(changed)

    def test_different_seed_completion_or_score_hash_refused(self):
        for change in (lambda value: value.update(seed=1),
                       lambda value: value["memory"].update(completion_sha256="0" * 64),
                       lambda value: value["memory"]["scores"].update(sha256="0" * 64)):
            changed = copy.deepcopy(self.spec)
            change(changed)
            with self.assertRaises(ValueError):
                runner.bind_inputs(changed)

    def test_upstream_original_claim_tamper_refused(self):
        claim = self.upstream.with_name(self.upstream.name + ".collection_claim.json")
        claim.write_bytes(runner.encoded(dict(plan_sha256=self.upstream_plan_sha, out="/wrong", retry=False)))
        with self.assertRaisesRegex(ValueError, "claim"):
            runner.bind_inputs(self.spec)

    def test_fresh_paths_no_resume_symlink_or_protected_overlap(self):
        with self.assertRaises(ValueError):
            runner.fresh(str(self.upstream / "new"), [self.upstream])
        link = self.home / "link"
        link.symlink_to(self.upstream, target_is_directory=True)
        with self.assertRaises(ValueError):
            runner.fresh(str(link / "new"), [])
        self.prepare()
        with self.assertRaises(ValueError):
            runner.fresh(str(self.root), [])

    def test_pretty_spec_preserved_and_plan_drift_rejected(self):
        plan, bound, plan_sha = self.prepare(pretty=True)
        self.assertEqual((self.root / "specification.json").read_bytes(), (self.home / "spec.json").read_bytes())
        plan["params"]["seed"] = 2
        (self.root / "plan.json").write_bytes(runner.encoded(plan))
        with self.assertRaisesRegex(ValueError, "agreement"):
            runner.verify(str(self.root), runner.digest(self.root / "plan.json"))

    def test_seed1_and_seed2_qualified_routes(self):
        for seed in (1, 2):
            self.assertEqual(runner.core_state(seed, "WRITE"), f"perception_seed{seed}_WRITE")
            self.assertIn(runner.core_state(seed, "LR0"), self.core.STATES)

    def test_invalid_actions_remain_sixteen_calls_zero_records(self):
        plan, bound, plan_sha = self.prepare()
        (self.root / "run/WRITE").mkdir(parents=True)
        Backend.mode = "invalid"
        runner.capture_state(plan, "WRITE", bound, backend_factory=Backend)
        closed = runner.read(self.root / "run/WRITE/closed.json")
        self.assertEqual((closed["calls"], closed["record_calls"]), (16, 0))
        capture = runner.read(self.root / "run/WRITE/formation.json")
        self.assertEqual(capture["summary"]["production_eligible"], 0)

    def test_truncated_native_outputs_not_success_or_repaired(self):
        plan, bound, plan_sha = self.prepare()
        (self.root / "run/WRITE").mkdir(parents=True)
        Backend.mode = "length"
        runner.capture_state(plan, "WRITE", bound, backend_factory=Backend)
        capture = runner.read(self.root / "run/WRITE/formation.json")
        self.assertEqual(capture["summary"]["production_eligible"], 0)
        self.assertEqual(len(Backend.instances[0].calls), 16)

    def test_fenced_content_is_diagnostic_not_production(self):
        plan, bound, plan_sha = self.prepare()
        (self.root / "run/WRITE").mkdir(parents=True)
        Backend.mode = "fenced"
        runner.capture_state(plan, "WRITE", bound, backend_factory=Backend)
        summary = runner.read(self.root / "run/WRITE/formation.json")["summary"]
        self.assertEqual((summary["content_correct"], summary["production_eligible"]), (16, 0))

    def test_native_failure_escapes_core_and_closes_backend(self):
        plan, bound, plan_sha = self.prepare()
        (self.root / "run/WRITE").mkdir(parents=True)
        Backend.mode = "raise"
        with self.assertRaises(runner.NativeCaptureFailure):
            runner.capture_state(plan, "WRITE", bound, backend_factory=Backend)
        self.assertTrue(Backend.instances[0].closed)
        self.assertFalse((self.root / "run/WRITE/closed.json").exists())

    def test_native_wrong_route_is_infrastructure_failure(self):
        plan, bound, plan_sha = self.prepare()
        (self.root / "run/WRITE").mkdir(parents=True)
        Backend.mode = "route"
        with self.assertRaises(runner.NativeCaptureFailure):
            runner.capture_state(plan, "WRITE", bound, backend_factory=Backend)

    def test_adapter_bytes_changed_after_prepare_are_refused(self):
        plan, bound, plan_sha = self.prepare()
        adapter = Path(self.routes["WRITE"]["path"]) / "adapter_model.safetensors"
        adapter.write_bytes(b"CHANGED")
        with self.assertRaisesRegex(ValueError, "inventory"):
            runner.current_route(plan, bound, "WRITE")

    def test_initial_prompts_only_core_messages_no_upstream_records(self):
        plan, bound, plan_sha = self.prepare()
        initial = runner.read(self.root / "initial_prompts.json")
        self.assertEqual(len(initial), 8)
        for index, item in enumerate(initial):
            self.assertEqual(item["case"]["cue_stratum"], "example_present" if index % 2 == 0 else "example_absent")
            self.assertEqual("ACT: TRY 2,5,9" in item["messages"][0]["content"], index % 2 == 0)
            self.assertNotIn(str(self.upstream), item["native"]["rendered_prompt"])
        self.assertEqual(plan["engine"]["seed"], 0)
        self.assertEqual(plan["params"]["seed"], 0)

    def test_duplicate_core_request_refused_before_second_native_call(self):
        plan, bound, plan_sha = self.prepare()
        (self.root / "run/WRITE").mkdir(parents=True)
        original_run = bound["core"].run_state
        def repeated(state, callback, **kwargs):
            def duplicate(request):
                callback(request)
                return callback(request)
            return original_run(state, duplicate, **kwargs)
        with patch.object(bound["core"], "run_state", side_effect=repeated), self.assertRaises(runner.NativeCaptureFailure):
            runner.capture_state(plan, "WRITE", bound, backend_factory=Backend)
        self.assertEqual(len(Backend.instances[0].calls), 1)

    def test_extra_raw_file_and_reused_process_identity_refused(self):
        plan, bound, plan_sha, complete_sha = self.completed()
        extra = self.root / "run/WRITE/32.response.json"
        extra.write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "inventory"):
            runner.validate_completed(plan, plan_sha, bound)
        extra.unlink()
        first_identity = runner.read(self.root / "run/WRITE/launch.json")["identity"]
        for name in ("launch.json", "started.json", "released.json"):
            path = self.root / "run/LR0" / name
            value = runner.read(path)
            value["identity"] = first_identity
            path.write_bytes(runner.encoded(value))
        with self.assertRaisesRegex(ValueError, "two cold"):
            runner.validate_completed(plan, plan_sha, bound)

    def test_native_bool_tokens_and_nonfinite_times_rejected(self):
        request = dict(native=dict(prompt_token_ids=[1]), params=dict(max_tokens=96))
        response = dict(prompt_token_ids=[1], actual_prompt_token_ids=[1], output_token_ids=[True],
                        text="x", decoded_output="x", finish_reason="stop", stop_reason=None,
                        lora_request=self.routes["WRITE"], started=1, ended=2)
        with self.assertRaisesRegex(ValueError, "token"):
            self.formation.validate_response(request, response, self.routes["WRITE"])
        response.update(output_token_ids=[3], ended=float("nan"))
        with self.assertRaisesRegex(ValueError, "timing"):
            self.formation.validate_response(request, response, self.routes["WRITE"])

    def test_dynamic_context_overflow_refused_before_native_call(self):
        plan, bound, plan_sha = self.prepare()
        (self.root / "run/WRITE").mkdir(parents=True)
        original_render = self.probe.render
        calls = 0
        def render(tokenizer, messages):
            nonlocal calls
            calls += 1
            native = original_render(tokenizer, messages)
            if calls > 8:
                native["prompt_token_ids"] = [3] * plan["engine"]["max_model_len"]
            return native
        with patch.object(self.probe, "render", side_effect=render), self.assertRaises(runner.NativeCaptureFailure):
            runner.capture_state(plan, "WRITE", bound, backend_factory=Backend)
        self.assertEqual(len(Backend.instances[0].calls), 0)

    def test_raw_file_and_extra_call_tampering_fail_replay(self):
        plan, bound, plan_sha, complete_sha = self.completed()
        response = self.root / "run/WRITE/00.response.json"
        response.write_bytes(response.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            runner.validate_completed(plan, plan_sha, bound)

    def test_same_pid_and_deadline_drift_refused(self):
        plan, bound, plan_sha, complete_sha = self.completed()
        launch_path = self.root / "run/LR0/launch.json"
        launch = runner.read(launch_path)
        launch["deadline_wall"] = float("inf")
        launch_path.write_text(json.dumps(launch))
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            runner.validate_completed(plan, plan_sha, bound)

    def test_controller_failure_never_scores_and_no_retry(self):
        plan, bound, plan_sha = self.prepare()
        with patch.object(runner, "check_allocation"), patch.object(runner, "run_state", side_effect=RuntimeError("mock failed")):
            with self.assertRaises(RuntimeError):
                runner.controller(str(self.root), plan_sha, allow_gpu=True)
        self.assertTrue((self.root / "controller_failure.json").exists())
        with self.assertRaisesRegex(ValueError, "claimed"):
            runner.controller(str(self.root), plan_sha, allow_gpu=True)
        with self.assertRaises(ValueError):
            runner.collect(str(self.root), plan_sha, "0" * 64, str(self.home / "collected"))
        self.assertFalse((self.home / "collected/scores.json").exists())

    def test_collection_requires_absent_controller_and_failure_consumes_claim(self):
        plan, bound, plan_sha, complete_sha = self.completed()
        receipt = self.root / "controller_started.json"
        value = runner.read(receipt)
        value["identity"] = runner.identity(os.getpid())
        receipt.write_bytes(runner.encoded(value))
        with self.assertRaisesRegex(ValueError, "still exists"):
            runner.collect(str(self.root), plan_sha, complete_sha, str(self.home / "collected"))
        self.assertTrue((self.home / "collected/collection_failure.json").exists())
        self.assertFalse((self.home / "collected/scores.json").exists())
        with self.assertRaisesRegex(ValueError, "claimed"):
            runner.collect(str(self.root), plan_sha, complete_sha, str(self.home / "again"))

    def test_all_process_vacancy_failure_prevents_spawn(self):
        plan, bound, plan_sha = self.prepare()
        self.probe.gpu_state.return_value = False
        with patch.object(runner, "check_allocation"), patch.object(runner.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(ValueError, "vacancy"):
                runner.run_state(plan, plan_sha, "WRITE", time.monotonic() + 100, bound)
            spawn.assert_not_called()

    def test_failed_collection_vacancy_never_writes_scores(self):
        plan, bound, plan_sha, complete_sha = self.completed()
        self.probe.gpu_state.return_value = False
        with patch.object(runner, "check_allocation"), self.assertRaisesRegex(ValueError, "vacancy"):
            runner.collect(str(self.root), plan_sha, complete_sha, str(self.home / "collected"))
        self.assertFalse((self.home / "collected/scores.json").exists())
        self.assertTrue((self.home / "collected/collection_failure.json").exists())

    def test_timeout_cleans_only_owned_group_and_rechecks_release(self):
        plan, bound, plan_sha = self.prepare()
        (self.root / "run").mkdir()
        process = Mock(pid=84000000)
        process.wait.side_effect = subprocess.TimeoutExpired("mock worker", 1)
        expected = dict(pid=process.pid, pgid=process.pid, start_ticks=123)
        self.memory.cleanup_owned = Mock()
        with patch.object(runner, "check_allocation"), patch.object(runner, "identity", return_value=expected), \
                patch.object(runner.subprocess, "Popen", return_value=process) as spawn:
            with self.assertRaises(subprocess.TimeoutExpired):
                runner.run_state(plan, plan_sha, "WRITE", time.monotonic() + 100, bound)
        self.memory.cleanup_owned.assert_called_once_with(process, expected, self.probe)
        self.assertEqual(self.probe.gpu_state.call_count, 2)
        self.assertEqual(spawn.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], self.spec["gpu_uuid"])
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        self.assertLessEqual(process.wait.call_args.kwargs["timeout"], 900)

    def test_cleanup_identity_mismatch_is_refused(self):
        process = Mock(pid=84000000)
        process.poll.return_value = None
        with patch.object(self.original_memory, "identity", return_value=dict(pid=process.pid, pgid=process.pid, start_ticks=2)):
            with self.assertRaisesRegex(ValueError, "unowned"):
                self.original_memory.cleanup_owned(process, dict(pid=process.pid, pgid=process.pid, start_ticks=1), self.probe)
        self.probe.cleanup.assert_not_called()

    def test_permissions_deadlines_boot_and_lease(self):
        with self.assertRaisesRegex(ValueError, "allow-native"):
            runner.prepare("missing", "missing", "missing")
        with self.assertRaisesRegex(ValueError, "allow-gpu"):
            runner.controller("missing", "missing")
        for deadline in (True, float("nan"), time.time() - 1, time.time() + 10000):
            with self.assertRaises(ValueError):
                runner.worker("missing", "missing", "WRITE", deadline, allow_gpu=True)
        with self.assertRaisesRegex(ValueError, "boot"):
            runner.check_allocation(dict(specification=self.spec))
        spec = copy.deepcopy(self.spec)
        spec["expected_boot_id"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        spec["lease_end"] = time.time()
        with self.assertRaisesRegex(ValueError, "lease"):
            runner.check_allocation(dict(specification=spec))

    def test_no_original_collectors_fits_or_scientific_core_reimplementation(self):
        tree = ast.parse(Path(runner.__file__).read_text())
        forbidden = {"collect", "run_training", "fit_arm", "score_record", "evaluate"}
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                             node.func.attr in forbidden for node in ast.walk(tree)))
        definitions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertFalse({"score_record", "episode_ids", "compare_states"} & definitions)


if __name__ == "__main__":
    unittest.main()
