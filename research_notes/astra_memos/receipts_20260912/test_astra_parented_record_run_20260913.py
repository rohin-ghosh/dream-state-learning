"""CPU integration tests for lifecycle seams; fake native/tokenizer/process boundaries only."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


specification = importlib.util.spec_from_file_location("parented_runner_test", "/tmp/astra_parented_record_run_20260913.py")
runner = importlib.util.module_from_spec(specification)
specification.loader.exec_module(runner)


class ToyTokenizer:
    chat_template = "CPU_FAKE_TEMPLATE"

    def encode(self, text, add_special_tokens=False):
        return list(text.encode())


def render(tokenizer, messages):
    prompt = "SYSTEM\n" + "\n".join(message["content"] for message in messages)
    return dict(rendered_prompt=prompt, prompt_token_ids=tokenizer.encode(prompt),
                actual_system_text="SYSTEM", actual_system_segment="SYSTEM\n")


class FakeNative:
    mode = "valid"

    def __init__(self, plan, probe, route):
        self.tokenizer, self.route, self.closed = ToyTokenizer(), route, False
        self.requests = []

    def generate(self, request):
        self.requests.append(copy.deepcopy(request))
        if self.mode == "failure":
            raise RuntimeError("synthetic infrastructure failure")
        if "core_request" not in request:
            raw = "retention"
        else:
            core_request = request["core_request"]
            if core_request["kind"] == "wake":
                raw = "PREDICT: F\nACT: TRY 2,5,9" if self.mode != "no_write" else "invalid action"
            elif core_request["kind"] == "restate":
                raw = "This is a child's temporary restatement."
            else:
                facts = json.loads(re.findall(r"^Observed fields: (.*)$", core_request["input_messages"][0]["content"], re.MULTILINE)[-1])
                raw = json.dumps(dict(observed=facts["observed"], predicted=facts["predicted"],
                    relation="matched" if facts["predicted"] == facts["observed"] else "mismatched",
                    **{"try": facts["values"]}))
        result = dict(request["native"], actual_prompt_token_ids=request["native"]["prompt_token_ids"],
            text=raw, decoded_output=raw, output_token_ids=[1, 2], finish_reason="stop", stop_reason=None,
            started=1.0, ended=1.25, lora_request=self.route)
        if self.mode == "bad_route":
            result["lora_request"] = dict(self.route, path="/wrong")
        return result

    def close(self):
        self.closed = True


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.memory = runner.runtime()
        cls.formation = cls.memory.load(dict(path="/tmp/astra_level1_real_record_run_20260913.py",
            sha256=cls.memory.FORMATION_PIN), "test_formation", cls.memory.FORMATION_PIN)
        cls.core = runner.load(dict(path="/tmp/astra_parented_record_core_20260913.py", sha256=runner.CORE_PIN), "test_core", runner.CORE_PIN)
        cls.dependencies = cls.core.load_dependencies("/data/home/rohing/dream-state")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="astra_parented_runner_test_")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.root = self.home / "run"
        self.root.mkdir()
        self.parent = self.home / "parent"
        self.parent.mkdir()
        (self.parent / "adapter.bin").write_bytes(b"unchanged-original")
        self.config = dict(lr=3e-5, epochs=8, batch_size=1, seed=0, max_steps=0)
        self.plan = dict(root=str(self.root), seed=0, config=self.config, params=self.formation.PARAMS,
            retention_params=dict(self.formation.PARAMS, max_tokens=192), engine=self.formation.ENGINE,
            model="FAKE_MODEL_NO_LOAD", model_files={}, source=str(self.home), chat_template=ToyTokenizer.chat_template,
            parent=dict(adapter=str(self.parent), adapter_files=self.formation.tree(self.parent), scores_sha256="old-pin"),
            specification=dict(core=dict(path="/tmp/astra_parented_record_core_20260913.py", sha256=runner.CORE_PIN), seed=0),
            historical_retention=dict(path="old-scores", sha256="old-pin", noncontemporaneous=True),
            gpu_uuid="GPU-fake", gpu_index=0, python="FAKE_PYTHON_NEVER_EXECUTED",
            work_started=dict(monotonic=time.monotonic(), unix=time.time()), deadline_monotonic=time.monotonic() + 7000)
        self.retention = dict(evaluation={panel: [dict(row_id=f"{panel}-{index}", input_messages=[dict(role="user", content=f"old {panel} {index}")])
            for index in range(count)] for panel, count in (("held", 48), ("canary", 12))})
        self.original_calls = [dict(call_id=f"{panel}_{index:02d}", row_id=row["row_id"], messages=row["input_messages"], native=render(ToyTokenizer(), row["input_messages"]))
            for panel, rows in self.retention["evaluation"].items() for index, row in enumerate(rows)]
        self.probe = SimpleNamespace(native_tokenizer=Mock(return_value=ToyTokenizer()), render=render,
            gpu_state=Mock(return_value=True), group_alive=Mock(return_value=False))
        self.history = dict(cells=dict(post={panel: dict(rows=[dict(row_id=row["row_id"], raw="retention",
            score=dict(content_correct=True, strict=True)) for row in rows]) for panel, rows in self.retention["evaluation"].items()}))
        self.bound = dict(memory=self.memory, core=self.core, dependencies=self.dependencies, formation=self.formation,
            probe=self.probe, trainer=Mock(), helper=SimpleNamespace(validate_score=Mock()), retention=self.retention,
            original_calls=self.original_calls, history=self.history,
            material=SimpleNamespace(score_row=lambda row, raw, finish: dict(content_correct=raw == "retention", strict=raw == "retention")))
        self.calls = self.memory.build_calls(dict(rows=[]), self.retention, self.original_calls, ToyTokenizer(), self.probe)
        self.memory.write(self.root / "retention_calls.json", self.calls)
        self.pin = "test-plan-pin"
        FakeNative.mode = "valid"

    def seal(self, stage):
        target = runner.directory(self.plan, stage)
        expected = dict(pid=900000 + runner.STAGES.index(stage), pgid=900000 + runner.STAGES.index(stage), start_ticks=100)
        for name, value in {
            "launch.json": dict(identity=expected, stage=stage, plan_sha256=self.pin, command=[]),
            "started.json": dict(identity=expected, stage=stage, plan_sha256=self.pin),
            "worker_done.json": dict(stage=stage, plan_sha256=self.pin),
            "exit.json": dict(identity=expected, returncode=0),
            "released.json": dict(identity=expected, stage=stage, group_absent=True, gpu_vacant=True),
        }.items():
            self.memory.write(target / name, value)
        self.memory.write(self.root / (stage + ".stage.json"), self.formation.tree(target))

    def capture_stage(self, stage):
        runner.directory(self.plan, stage).mkdir(parents=True)
        runner.capture(self.plan, self.bound, stage, backend_factory=FakeNative)
        self.seal(stage)

    def fake_encoding(self, rows, *args):
        return dict(rows=len(rows), updates=8 * len(rows), items=copy.deepcopy(rows), fit_seed=0,
                    target_tokens=1, total_tokens=2, train_tokens_seen=16)

    def fake_fit(self, arm):
        view, _ = runner.arm_plan(self.plan, self.bound, arm)
        target = runner.directory(self.plan, arm + "_fit")
        (target / "adapter").mkdir(parents=True)
        self.memory.write(target / "adapter/train_manifest.json", dict(corpus=dict(sha256=view["input_hashes"]["training.json"]),
            warm_start=dict(source_state={"same": "original"}, initialized_state={"same": "initialized"})))
        prepared = self.memory.read(Path(view["root"]) / "training.json")
        self.memory.write(target / "fit.json", dict(arm="WRITE", adapter=str(target / "adapter"),
            adapter_files=self.formation.tree(target / "adapter"), initialized_from=self.plan["parent"],
            training_sha256=view["input_hashes"]["training.json"], calls=0, updates=prepared["updates"]))
        self.seal(arm + "_fit")

    def all_stages(self, no_write=False):
        FakeNative.mode = "no_write" if no_write else "valid"
        for stage in runner.STAGES:
            if stage.endswith("_fit"):
                with patch.object(self.memory, "encode_training", side_effect=self.fake_encoding):
                    if runner.prepare_arm(self.plan, self.bound, stage[0]):
                        self.fake_fit(stage[0])
            else:
                self.capture_stage(stage)
        with patch.object(self.memory, "check_fit"):
            return runner.validate_completed(self.plan, self.bound, self.pin)

    def test_full_coupling_caps_material_and_cold_stages(self):
        checked = self.all_stages()
        self.assertEqual(sum(cost["calls"] for cost in checked["costs"].values()), 300)
        self.assertEqual(sum(fit["updates"] for fit in checked["fits"].values()), 256)
        self.assertEqual(sum(fit["fits"] for fit in checked["fits"].values()), 2)
        for arm in runner.ARMS:
            dataset = self.memory.read(self.root / "arms" / arm / "dataset.json")
            self.assertEqual(len(dataset["rows"]), 16)
            self.assertTrue(all(row["source"]["state"].endswith("_" + arm) for row in dataset["rows"]))
            for row in dataset["rows"]:
                self.assertNotIn("Temporary session", json.dumps(row["input_messages"]))
                self.assertNotIn("restatement", row["raw_target"])
            result = runner.retention_scores(self.plan, self.bound, arm)
            self.assertEqual(result["versus_original"]["held"]["content_correct"], dict(gains=[], losses=[]))

    def test_no_write_retains_parent_without_fake_fit(self):
        checked = self.all_stages(no_write=True)
        self.assertEqual(sum(cost["calls"] for cost in checked["costs"].values()), 212)
        self.assertEqual(checked["fits"], {arm: dict(status="NO_WRITE", updates=0, fits=0) for arm in runner.ARMS})
        for arm in runner.ARMS:
            self.assertFalse(runner.directory(self.plan, arm + "_fit").exists())
            self.assertFalse((self.root / "arms" / arm / "training.json").exists())
            self.assertEqual(runner.route_for(self.plan, self.bound, arm), runner.route_for(self.plan, self.bound, "ORIGINAL"))

    def test_no_write_does_not_tokenize_or_fit(self):
        FakeNative.mode = "no_write"
        self.capture_stage("P_formation")
        with patch.object(self.memory, "encode_training") as encode, patch.object(self.memory, "fit_arm") as fit:
            self.assertFalse(runner.prepare_arm(self.plan, self.bound, "P"))
        encode.assert_not_called()
        fit.assert_not_called()
        self.probe.native_tokenizer.assert_not_called()

    def test_sampling_caps_and_temporary_context_boundary(self):
        self.capture_stage("P_formation")
        requests = [self.memory.read(path) for path in sorted(runner.directory(self.plan, "P_formation").glob("*.request.json"))]
        self.assertEqual(len(requests), 42)
        for request in requests:
            kind = request["core_request"]["kind"]
            self.assertEqual(request["params"]["max_tokens"], {"wake": 96, "record": 192, "restate": 120}[kind])
            self.assertEqual(request["params"]["temperature"], .5 if kind == "restate" else 0.)
        self.capture_stage("ORIGINAL_held")
        held = runner.directory(self.plan, "ORIGINAL_held")
        self.assertEqual(len(list(held.glob("*.request.json"))), 32)
        self.assertTrue(all("Temporary session" not in path.read_text() and "Session contact:" not in path.read_text() for path in held.glob("*.request.json")))

    def test_infrastructure_failure_not_scored_as_refusal_and_closes(self):
        target = runner.directory(self.plan, "P_formation")
        target.mkdir(parents=True)
        backend = FakeNative(self.plan, self.probe, runner.route_for(self.plan, self.bound, "ORIGINAL"))
        backend.mode = "failure"
        with self.assertRaises(runner.NativeCaptureFailure):
            runner.capture(self.plan, self.bound, "P_formation", backend_factory=lambda *args: backend)
        self.assertTrue(backend.closed)
        self.assertFalse((target / "capture.json").exists())
        self.assertEqual(len(list(target.glob("*.request.json"))), 1)

    def test_wrong_native_route_stops(self):
        FakeNative.mode = "bad_route"
        runner.directory(self.plan, "P_formation").mkdir(parents=True)
        with self.assertRaises(runner.NativeCaptureFailure):
            runner.capture(self.plan, self.bound, "P_formation", backend_factory=FakeNative)

    def test_formation_tampering_stops_before_admission(self):
        self.capture_stage("P_formation")
        (runner.directory(self.plan, "P_formation") / "00.response.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "formation changed"):
            runner.prepare_arm(self.plan, self.bound, "P")
        self.assertFalse((self.root / "arms/P").exists())

    def test_material_tampering_stops_before_fit(self):
        self.capture_stage("P_formation")
        with patch.object(self.memory, "encode_training", side_effect=self.fake_encoding):
            runner.prepare_arm(self.plan, self.bound, "P")
        path = self.root / "arms/P/dataset.json"
        changed = self.memory.read(path)
        changed["rows"][0]["raw_target"] = "teacher answer"
        path.write_bytes(self.memory.encoded(changed))
        with self.assertRaisesRegex(ValueError, "own raw source"):
            runner.arm_plan(self.plan, self.bound, "P")

    def test_training_tampering_stops_before_fit(self):
        self.capture_stage("P_formation")
        with patch.object(self.memory, "encode_training", side_effect=self.fake_encoding):
            runner.prepare_arm(self.plan, self.bound, "P")
        (self.root / "arms/P/training.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "arm preparation"):
            runner.arm_plan(self.plan, self.bound, "P")

    def test_raw_response_tampering_fails_completion(self):
        self.all_stages()
        path = runner.directory(self.plan, "P_held") / "00.response.json"
        response = self.memory.read(path)
        response["text"] = response["decoded_output"] = "changed"
        path.write_bytes(self.memory.encoded(response))
        with patch.object(self.memory, "check_fit"), self.assertRaisesRegex(ValueError, "raw/source replay"):
            runner.validate_completed(self.plan, self.bound, self.pin)

    def test_release_mismatch_fails_completion(self):
        self.all_stages(no_write=True)
        path = runner.directory(self.plan, "P_held") / "released.json"
        release = self.memory.read(path)
        release["group_absent"] = False
        path.write_bytes(self.memory.encoded(release))
        with self.assertRaisesRegex(ValueError, "exit/release"):
            runner.validate_completed(self.plan, self.bound, self.pin)

    def test_stage_precheck_prevents_spawn(self):
        self.probe.gpu_state.return_value = False
        with patch.object(runner, "check_allocation"), patch.object(subprocess, "Popen") as spawn, self.assertRaisesRegex(ValueError, "vacancy"):
            runner.run_stage(self.plan, self.bound, self.pin, "P_formation")
        spawn.assert_not_called()

    def test_stage_failure_cleans_owned_process_without_success(self):
        process = Mock(pid=900001)
        process.wait.return_value = 2
        identity = dict(pid=900001, pgid=900001, start_ticks=100)
        with patch.object(runner, "check_allocation"), patch.object(subprocess, "Popen", return_value=process), patch.object(self.memory, "identity", return_value=identity), patch.object(self.memory, "cleanup_owned") as cleanup, self.assertRaisesRegex(ValueError, "worker failed"):
            runner.run_stage(self.plan, self.bound, self.pin, "P_formation")
        cleanup.assert_called_once_with(process, identity, self.probe)
        self.assertEqual(self.memory.read(runner.directory(self.plan, "P_formation") / "exit.json")["returncode"], 2)
        self.assertFalse((self.root / "P_formation.stage.json").exists())

    def test_worker_timeout_reserves_cleanup_and_collection(self):
        process = Mock(pid=900001)
        process.wait.side_effect = subprocess.TimeoutExpired("fake", 1)
        identity = dict(pid=900001, pgid=900001, start_ticks=100)
        with patch.object(runner, "check_allocation"), patch.object(subprocess, "Popen", return_value=process), patch.object(self.memory, "identity", return_value=identity), patch.object(self.memory, "cleanup_owned") as cleanup, self.assertRaises(subprocess.TimeoutExpired):
            runner.run_stage(self.plan, self.bound, self.pin, "P_formation")
        cleanup.assert_called_once()
        self.assertLess(process.wait.call_args.kwargs["timeout"], 7000 - runner.COLLECTION_SECONDS - runner.CLEANUP_SECONDS)

    def test_low_remaining_budget_never_spawns(self):
        self.plan["deadline_monotonic"] = time.monotonic() + runner.COLLECTION_SECONDS + 20
        with patch.object(runner, "check_allocation"), patch.object(subprocess, "Popen") as spawn, self.assertRaisesRegex(ValueError, "budget"):
            runner.run_stage(self.plan, self.bound, self.pin, "P_formation")
        spawn.assert_not_called()

    def test_failed_release_never_seals_stage(self):
        process = Mock(pid=900001)
        process.wait.return_value = 0
        self.probe.gpu_state.side_effect = [True, False]
        identity = dict(pid=900001, pgid=900001, start_ticks=100)
        with patch.object(runner, "check_allocation"), patch.object(subprocess, "Popen", return_value=process), patch.object(self.memory, "identity", return_value=identity), patch.object(self.memory, "cleanup_owned"), self.assertRaisesRegex(ValueError, "release/vacancy"):
            runner.run_stage(self.plan, self.bound, self.pin, "P_formation")
        self.assertTrue((runner.directory(self.plan, "P_formation") / "cleanup_failure.json").exists())
        self.assertFalse((self.root / "P_formation.stage.json").exists())

    def test_no_authority_flags_reject_before_native(self):
        for callback in (lambda: runner.prepare(self.root, "spec", "pin"), lambda: runner.worker(self.root, "pin", "P_fit"), lambda: runner.controller(self.root, "pin")):
            with self.assertRaises(ValueError):
                callback()

    def test_controller_cannot_reset_consumed_budget(self):
        self.memory.write(self.root / "controller_started.json", {})
        with patch.object(runner, "runtime", return_value=self.memory), patch.object(self.memory, "offline"), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), self.assertRaisesRegex(ValueError, "already claimed"):
            runner.controller(self.root, "pin", allow_gpu=True)
        self.assertFalse((self.root / "controller_failure.json").exists())

    def test_collection_once_claim_and_deadline(self):
        self.memory.write(self.root / "plan.json", self.plan)
        pin = runner.digest(self.root / "plan.json")
        claim = self.root.with_name(self.root.name + ".collection_claim.json")
        self.memory.write(claim, dict(retry=False))
        with patch.object(runner, "runtime", return_value=self.memory), patch.object(self.memory, "offline"), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), self.assertRaises(FileExistsError):
            runner.collect(self.root, pin, "completion", self.home / "out")
        self.assertFalse((self.home / "out").exists())

    def test_frozen_dependencies_unchanged(self):
        self.assertEqual(runner.digest("/tmp/astra_parented_record_core_20260913.py"), runner.CORE_PIN)
        self.assertEqual(runner.digest("/tmp/astra_real_record_memory_run_20260913.py"), runner.MEMORY_PIN)
        self.assertEqual(self.memory.ARMS, ("WRITE", "LR0"))
        self.assertEqual(self.memory.OUTER_SECONDS, 3600)
        self.assertEqual(self.formation.PARAMS["temperature"], 0.0)
        self.assertEqual(self.core.TEMPERATURE["restate"], .5)

    def spec_fixture(self):
        prior = self.home / "prior_ids.json"
        self.memory.write(prior, ["historical-episode"])
        spec = dict(runner_sha256=runner.digest(runner.SELF),
            core=dict(path="/tmp/astra_parented_record_core_20260913.py", sha256=runner.CORE_PIN),
            protocol=dict(path="/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_PARENTED_RECORD_DEV_2026-09-13.md", sha256=runner.PROTOCOL_PIN),
            memory_runtime=dict(path="/tmp/astra_real_record_memory_run_20260913.py", sha256=runner.MEMORY_PIN),
            lower_runtime=dict(path="/tmp/astra_memory_lower_lr_run_20260913.py", sha256=runner.LOWER_PIN),
            memory=dict(root=str(self.home / "historical_memory"), plan_sha256=runner.MEMORY_PLANS[0]),
            prior_episode_ids=dict(path=str(prior), sha256=runner.digest(prior)), seed=0,
            gpu_index=0, gpu_uuid="GPU-fake", expected_boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            lease_end=time.time() + 50000)
        return spec

    def test_closed_spec_rejects_new_control_or_seed_or_source(self):
        spec = self.spec_fixture()
        runner.validate_spec(spec)
        bad_specs = [dict(spec, extra=True), dict(spec, seed=True), dict(spec, seed=3),
                     dict(spec, seed=1), dict(spec, core=dict(spec["core"], sha256="0" * 64)),
                     dict(spec, memory=dict(spec["memory"], plan_sha256="0" * 64))]
        for bad in bad_specs:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                runner.validate_spec(bad)

    def test_wrong_boot_or_short_lease_blocks_allocation(self):
        spec = self.spec_fixture()
        runner.check_allocation(spec)
        with self.assertRaisesRegex(ValueError, "boot"):
            runner.check_allocation(dict(spec, expected_boot_id="0" * 36))
        with self.assertRaisesRegex(ValueError, "six-hour"):
            runner.check_allocation(dict(spec, lease_end=time.time() + runner.SECONDS + runner.LEASE_MARGIN - 1))

    def prepare_fixture(self):
        spec = self.spec_fixture()
        source = self.home / "specification.json"
        self.memory.write(source, spec)
        original = dict(self.plan, environment={})
        bound = dict(self.bound, original=original, parent=self.plan["parent"], config=self.config,
                     manifest=self.core.build_manifest(self.dependencies, prior_episode_ids=["historical-episode"]), history_path="fake-history")
        root = self.home / "prepared"
        with patch.object(runner, "runtime", return_value=self.memory), patch.object(self.memory, "offline"), patch.object(runner, "bind_inputs", return_value=bound), patch.object(runner, "protected", return_value=[self.parent]), patch.object(runner, "check_allocation"), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            result = runner.prepare(root, source, runner.digest(source), allow_native=True)
        return root, result["plan_sha256"], bound

    def test_prepare_verify_and_plan_pin_retention(self):
        root, pin, bound = self.prepare_fixture()
        with patch.object(runner, "runtime", return_value=self.memory), patch.object(runner, "bind_inputs", return_value=bound):
            plan, _ = runner.verify(root, pin)
            self.assertEqual(plan["deadline_monotonic"], plan["work_started"]["monotonic"] + 7200)
            self.assertEqual(plan["limits"], dict(calls=300, updates=256, seconds=7200, collection=180))
            changed = self.memory.read(root / "retention_calls.json")
            changed[0]["messages"] = [dict(role="user", content="wrong")]
            (root / "retention_calls.json").write_bytes(self.memory.encoded(changed))
            (root / "prepared.json").write_bytes(self.memory.encoded(dict(plan_sha256=pin, retention_sha256=runner.digest(root / "retention_calls.json"))))
            with self.assertRaisesRegex(ValueError, "plan-bound retention"):
                runner.verify(root, pin)

    def test_verify_rejects_recipe_change_even_with_new_plan_hash(self):
        root, pin, bound = self.prepare_fixture()
        changed = self.memory.read(root / "plan.json")
        changed["config"]["lr"] = 1e-4
        (root / "plan.json").write_bytes(self.memory.encoded(changed))
        with patch.object(runner, "runtime", return_value=self.memory), patch.object(runner, "bind_inputs", return_value=bound), self.assertRaisesRegex(ValueError, "independent plan"):
            runner.verify(root, runner.digest(root / "plan.json"))

    def test_verify_whole_work_deadline_does_not_reset(self):
        root, pin, bound = self.prepare_fixture()
        plan = self.memory.read(root / "plan.json")
        with patch.object(runner, "runtime", return_value=self.memory), patch.object(runner, "bind_inputs", return_value=bound), patch.object(time, "monotonic", return_value=plan["deadline_monotonic"] + 1), self.assertRaisesRegex(ValueError, "whole-work budget"):
            runner.verify(root, pin)

    def test_worker_forwards_only_own_fit_view_to_frozen_writer(self):
        self.capture_stage("P_formation")
        with patch.object(self.memory, "encode_training", side_effect=self.fake_encoding):
            runner.prepare_arm(self.plan, self.bound, "P")
        self.memory.write(self.root / "plan.json", self.plan)
        pin = runner.digest(self.root / "plan.json")
        target = runner.directory(self.plan, "P_fit")
        target.mkdir(parents=True)
        identity = dict(pid=os.getpid(), pgid=os.getpid(), start_ticks=123)
        self.memory.write(target / "launch.json", dict(identity=identity, stage="P_fit", plan_sha256=pin))
        with patch.object(runner, "runtime", return_value=self.memory), patch.object(self.memory, "offline"), patch.object(runner, "verify", return_value=(self.plan, self.bound)), patch.object(self.memory, "identity", return_value=identity), patch.object(os, "getpgrp", return_value=os.getpid()), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=self.plan["gpu_uuid"]), patch.object(self.memory, "fit_arm") as fit:
            runner.worker(self.root, pin, "P_fit", allow_gpu=True)
        view, arm_bound, arm = fit.call_args.args
        self.assertEqual(arm, "WRITE")
        self.assertEqual(view["root"], str(self.root / "arms/P"))
        self.assertEqual(view["parent"], self.plan["parent"])
        self.assertEqual(view["configs"]["WRITE"]["lr"], 3e-5)
        self.assertEqual(view["specification"]["fit_seed"], 0)
        self.assertTrue(all(row["source"]["state"].endswith("_P") for row in arm_bound["dataset"]["rows"]))

    def test_complete_once_collection_with_no_write_is_a_result(self):
        checked = self.all_stages(no_write=True)
        self.memory.write(self.root / "plan.json", self.plan)
        pin = runner.digest(self.root / "plan.json")
        self.memory.write(self.root / "controller_started.json", dict(identity=dict(pid=900999)))
        complete = dict(plan_sha256=pin, inventory=checked["inventory"], calls=212, fits=0, updates=0, automatic_pass=False)
        self.memory.write(self.root / "capture_complete.json", complete)
        out = self.home / "collected"
        with patch.object(runner, "runtime", return_value=self.memory), patch.object(self.memory, "offline"), patch.object(runner, "verify", return_value=(self.plan, self.bound)), patch.object(runner, "protected", return_value=[self.parent]), patch.object(runner, "check_allocation"), patch.object(runner, "validate_completed", return_value=checked), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""):
            result = runner.collect(self.root, pin, runner.digest(self.root / "capture_complete.json"), out)
        report = self.memory.read(out / "scores.json")
        self.assertEqual(result["status"], "COLLECTED_DEV_ONLY")
        self.assertEqual(report["updates"], 0)
        self.assertEqual(report["held_vs_initial"]["P"]["production_eligible"], 0)
        self.assertFalse(report["automatic_pass"])
        self.assertIsNone(report["scientific_pass"])
        self.assertTrue(report["historical_original"]["noncontemporaneous"])


if __name__ == "__main__":
    unittest.main()
