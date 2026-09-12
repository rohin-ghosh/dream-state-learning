"""Mock-only readout bridge regression suite; no GPU/native execution."""
from contextlib import nullcontext
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch


sys.path.insert(0, "/tmp")
import test_astra_rulegame_record_write_20260912 as writes

spec = importlib.util.spec_from_file_location("astra_record_readout", "/tmp/astra_rulegame_record_readout_20260912.py")
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
diagnostic = writes.diagnostic


class ReadoutTests(unittest.TestCase):
    def setUp(self):
        self.fixture = writes.BridgeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.prepare()
        self.write_root = self.fixture.output
        plan_path = self.write_root / "plan.json"
        written = diagnostic.read(plan_path)
        written["python"] = os.path.abspath(sys.executable)
        self.fixture.replace_json(plan_path, written)
        self.fixture.prepared["plan_sha256"] = bridge.digest(plan_path)
        self.output = self.fixture.root / "readout"
        self.loads, self.launches = [], []
        self.fail_cell, self.corrupt, self.no_quiz, self.close_ok = None, None, False, True
        self.driver_patch = patch.object(bridge, "load_driver", return_value=writes.bridge)
        self.driver_patch.start()
        self.addCleanup(self.driver_patch.stop)

    def prepare(self, **changes):
        values = dict(write_root=self.write_root, write_plan_sha256=self.fixture.prepared["plan_sha256"],
            write_driver=str(writes.bridge.SELF), out=self.output, deadline=writes.iso(time.time()+3600),
            lease_end=writes.iso(time.time()+8*3600))
        values.update(changes)
        self.prepared = bridge.prepare(**values)
        return self.prepared

    def completed(self):
        self.prepare()
        self.fixture.run_pair()

    def backend(self, model, adapter):
        identity = diagnostic.expected_identity(dict(model=model), adapter)
        native = writes.Backend(tokenizer=writes.Tokenizer())
        native.source_identity = identity
        native.no_quiz = self.no_quiz
        native.backend = SimpleNamespace(tok=native.tokenizer)
        self.loads.append(dict(model=model, adapter=adapter, backend=native))
        cell = "OFF" if adapter is None else Path(adapter).parent.name + "_ON"
        if cell == self.fail_cell:
            raise RuntimeError("mock native load failed: " + cell)
        return native

    def supervise(self, root, plan, stage, command, call_path):
        stage.mkdir()
        self.launches.append((plan, stage, command, call_path))
        self.assertEqual(command[0], os.path.abspath(sys.executable))
        self.assertEqual(call_path, stage / "data" / "calls")
        controller = diagnostic.read(root / "run" / "controller.json")
        self.assertEqual(plan["lease_end"], controller["hard_end"])
        self.assertLessEqual(controller["hard_end"]-controller["started_wall"], 1800)
        self.assertEqual(controller["cleanup_reserve"], 140)
        spec_path = Path(command[command.index("--spec")+1])
        spec_hash = command[command.index("--spec-sha256")+1]
        success = False
        original_open = Path.open
        blocked = (self.fixture.formation, self.write_root / "material", self.fixture.audit_path)
        def guarded_open(path, *args, **kwargs):
            self.assertFalse(any(path == item or item in path.parents for item in blocked), "worker read parent/material data: " + str(path))
            return original_open(path, *args, **kwargs)
        try:
            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES="2"), \
                 patch.object(bridge, "owning_process", return_value=nullcontext()), \
                 patch.object(bridge, "load_driver", side_effect=AssertionError("worker must not import write/material path")), \
                 patch.object(Path, "open", guarded_open):
                bridge.worker(spec_path, spec_hash, allow_gpu=True)
            if self.corrupt:
                self.corrupt(stage)
            success = True
        finally:
            receipt = dict(ok=success, reservation_release_verified=True, owned_group_empty=True,
                gpu_processes_absent=True, reserved_seconds=.01)
            bridge.write_json(stage / "supervision.json", receipt)
        return receipt

    def evaluate(self, allow_gpu=True):
        with patch.object(diagnostic, "NativeBackend", side_effect=self.backend), \
             patch.object(bridge, "close_native", return_value=self.close_ok), \
             patch.object(diagnostic, "supervise", side_effect=self.supervise), \
             patch.object(diagnostic, "native_tokenizer", side_effect=AssertionError("no controller native tokenizer")), \
             patch.object(writes.trainer, "run_training", side_effect=AssertionError("no training in readout")), \
             patch.object(diagnostic, "material", side_effect=AssertionError("no legacy material")), \
             patch.object(diagnostic, "evaluate", side_effect=AssertionError("no legacy entrypoint")):
            return bridge.evaluate(self.output, self.prepared["plan_sha256"], allow_gpu=allow_gpu)

    def test_prepare_prospective_without_fit_or_outcome_reads(self):
        self.assertFalse((self.write_root / "fits").exists())
        with patch.object(bridge, "accepted_writes", side_effect=AssertionError("no fit results before freeze")), \
             patch.object(diagnostic, "NativeBackend", side_effect=AssertionError("no native prepare")):
            self.prepare()
        plan = diagnostic.read(self.output / "plan.json")
        self.assertEqual(plan["write_status"], "NOT_INSPECTED_UNTIL_EVALUATE")
        self.assertEqual(plan["protocol"]["tasks"], diagnostic.schedule()["evaluation"])
        self.assertEqual(plan["protocol"]["limits"], {"wake": 20, "record": 12})
        self.assertEqual(plan["protocol"]["max_calls"], 96)
        self.assertEqual(plan["protocol"]["max_generated_tokens"], 27600)
        self.assertFalse((self.output / "run").exists())

    def test_three_fresh_cells_exact_old_semantics_and_no_parent_context(self):
        self.completed()
        before = diagnostic.tree_hashes(self.write_root)
        result = self.evaluate()
        self.assertEqual(result["status"], "COMPLETE_EXPLORATORY_READOUT")
        self.assertFalse(result["adaptation_test"])
        self.assertEqual([item["adapter"] for item in self.loads], [None,
            str(self.write_root / "fits" / "P" / "adapter"), str(self.write_root / "fits" / "A" / "adapter")])
        self.assertEqual(len({id(item["backend"]) for item in self.loads}), 3)
        for cell, loaded in zip(bridge.CELLS, self.loads):
            requests = loaded["backend"].requests
            self.assertEqual(len(requests), 32)
            self.assertEqual({row["role"] for row in requests}, {"wake", "record"})
            self.assertEqual({row["eid"] for row in requests}, set(diagnostic.schedule()["evaluation"]))
            for request in requests:
                self.assertNotIn(writes.LESSON, request["prompt"])
                self.assertNotIn("Temporary parent restatement:", request["prompt"])
                self.assertEqual(request["temperature"], .7)
                self.assertEqual(request["protocol"], "interaction_v3")
                if request["role"] == "record":
                    self.assertIn(diagnostic.RELATION_DEFINITION, request["prompt"])
                    self.assertIn("Actual emitted output:", request["prompt"])
                else:
                    self.assertNotIn('"relation":', request["prompt"])
                    if request["tick"] == 1:
                        self.assertNotIn("[OUTCOME]", request["prompt"].split("A fresh mystery box.")[0])
                        self.assertNotIn("the box says:", request["prompt"])
            direct_path = self.fixture.root / (cell + "_reference")
            direct_path.mkdir()
            direct = writes.Backend(tokenizer=writes.Tokenizer())
            direct.source_identity = loaded["backend"].identity()
            calls = diagnostic.Calls(direct_path / "calls", direct, "evaluation", direct.identity(), "interaction_v3")
            expected = diagnostic.run_evaluation(calls, diagnostic.Events(), cell)
            self.assertEqual(result["cells"][cell]["result"], expected)
            self.assertEqual(requests, direct.requests)
            worker = diagnostic.read(self.output / "run" / (cell + ".spec.json"))
            self.assertEqual(set(worker), bridge.SPEC_KEYS)
            for forbidden in ("main_audit", "corpora", "formation_root", "parent_text", "write_root"):
                self.assertNotIn(forbidden, worker)
        self.assertEqual(before, diagnostic.tree_hashes(self.write_root))
        self.assertEqual(result["P_minus_A"], 0)
        self.assertEqual(result["P_minus_OFF"], 0)

    def test_no_quiz_keeps_zero_fixed_denominator_and_all_cells(self):
        self.completed()
        self.no_quiz = True
        result = self.evaluate()
        for receipt in result["cells"].values():
            self.assertEqual(receipt["result"]["mean_quiz_accuracy"], 0)
            self.assertEqual(len(receipt["result"]["tasks"]), 4)
            self.assertTrue(all(not task["valid_quiz"] for task in receipt["result"]["tasks"]))

    def test_write_driver_and_root_hash_are_parameterized(self):
        with self.assertRaisesRegex(ValueError, "plan hash mismatch"):
            self.prepare(write_plan_sha256="0"*64)
        self.assertFalse(self.output.exists())
        self.prepare()
        self.assertEqual(diagnostic.read(self.output / "plan.json")["write_plan_sha256"], self.fixture.prepared["plan_sha256"])

    def test_real_v2_driver_api_with_mock_pair_end_to_end(self):
        self.driver_patch.stop()
        v2_path = "/tmp/astra_rulegame_record_write_v2_20260912.py"
        actual = bridge.load_driver(v2_path)
        with patch.object(writes, "bridge", actual):
            self.fixture = writes.BridgeTests()
            self.fixture.setUp()
            self.addCleanup(self.fixture.doCleanups)
            self.fixture.prepare()
            self.write_root = self.fixture.output
            self.output = self.fixture.root / "readout"
            self.completed()
            result = self.evaluate()
        self.assertEqual(result["status"], "COMPLETE_EXPLORATORY_READOUT")
        plan = diagnostic.read(self.output / "plan.json")
        self.assertEqual(plan["write_driver"], v2_path)
        self.assertEqual(plan["write_driver_sha256"], bridge.digest(v2_path))

    def test_native_venv_symlink_interpreter_preserved(self):
        venv_python = self.fixture.root / "venv" / "bin" / "python"
        venv_python.parent.mkdir(parents=True)
        venv_python.symlink_to(sys.executable)
        self.assertNotEqual(str(venv_python), str(venv_python.resolve()))
        self.assertEqual(bridge.absolute_python(venv_python), str(venv_python))
        plan_path = self.write_root / "plan.json"
        written = diagnostic.read(plan_path)
        written["python"] = str(venv_python)
        self.fixture.replace_json(plan_path, written)
        self.fixture.prepared["plan_sha256"] = bridge.digest(plan_path)
        with patch.object(sys, "executable", str(venv_python)):
            self.completed()
            result = self.evaluate()
        self.assertEqual(result["status"], "COMPLETE_EXPLORATORY_READOUT")
        self.assertTrue(all(command[0] == str(venv_python) for _, _, command, _ in self.launches))

    def test_wrong_controller_interpreter_rejected(self):
        alias = self.fixture.root / "python"
        alias.symlink_to(sys.executable)
        with patch.object(sys, "executable", str(alias)), self.assertRaisesRegex(ValueError, "exact write-plan venv"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_fresh_sibling_and_lease_deadline_required(self):
        for changes in (dict(out=self.write_root), dict(out=self.write_root / "nested"),
                        dict(deadline=writes.iso(time.time()+100)), dict(lease_end=writes.iso(time.time()+3600))):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.prepare(**changes)
        self.prepare()
        with self.assertRaises(ValueError):
            self.prepare()

    def test_gpu_opt_in_before_any_work(self):
        with self.assertRaisesRegex(ValueError, "allow-gpu"):
            bridge.evaluate("missing", "missing")
        with self.assertRaisesRegex(ValueError, "allow-gpu"):
            bridge.worker("missing", "missing")
        self.assertFalse(self.loads)

    def test_missing_pair_preserved_failure_and_no_retry(self):
        self.prepare()
        with self.assertRaises(FileNotFoundError):
            self.evaluate()
        self.assertTrue((self.output / "run" / "failure.json").exists())
        with self.assertRaises(FileExistsError):
            self.evaluate()
        self.assertFalse(self.loads)

    def test_failed_partial_write_cannot_launch(self):
        self.completed()
        bridge.write_json(self.write_root / "run" / "failure.json", dict(error="preserved failure"))
        with self.assertRaisesRegex(ValueError, "failed/partial writes"):
            self.evaluate()
        self.assertFalse(self.loads)

    def test_adapter_tamper_before_readout_blocks_all_cells(self):
        self.completed()
        adapter = self.write_root / "fits" / "P" / "adapter" / "adapter_model.safetensors"
        adapter.write_bytes(adapter.read_bytes()+b"tampered")
        with self.assertRaisesRegex(ValueError, "fit seal changed"):
            self.evaluate()
        self.assertFalse(self.loads)

    def test_readout_protocol_tamper_even_rehashed_rejected(self):
        self.prepare()
        path = self.output / "plan.json"
        plan = diagnostic.read(path)
        plan["protocol"]["tasks"].reverse()
        self.fixture.replace_json(path, plan)
        self.prepared["plan_sha256"] = bridge.digest(path)
        with self.assertRaisesRegex(ValueError, "protocol changed"):
            self.evaluate()

    def test_p_failure_preserves_off_no_a_or_retry(self):
        self.completed()
        self.fail_cell = "P_ON"
        with self.assertRaisesRegex(RuntimeError, "mock native load failed"):
            self.evaluate()
        self.assertEqual(len(self.launches), 2)
        failure = diagnostic.read(self.output / "run" / "failure.json")
        self.assertEqual(failure["completed_cells"], ["OFF"])
        self.assertFalse((self.output / "run" / "result.json").exists())
        self.assertTrue((self.output / "run" / "OFF" / "data" / "manifest.json").exists())
        with self.assertRaises(FileExistsError):
            self.evaluate()

    def test_cleanup_failure_blocks_next_cell(self):
        self.completed()
        self.close_ok = False
        with self.assertRaisesRegex(ValueError, "backend cleanup unverified"):
            self.evaluate()
        self.assertEqual(len(self.launches), 1)

    def test_supervisor_release_failure_blocks_next_cell(self):
        self.completed()
        original = self.supervise
        def unreleased(*args):
            receipt = original(*args)
            receipt["reservation_release_verified"] = False
            return receipt
        with patch.object(self, "supervise", side_effect=unreleased), self.assertRaisesRegex(ValueError, "readout cleanup unverified"):
            self.evaluate()
        self.assertEqual(len(self.launches), 1)

    def test_a_failure_preserves_two_cells_without_partial_contrast(self):
        self.completed()
        self.fail_cell = "A_ON"
        with self.assertRaisesRegex(RuntimeError, "mock native load failed"):
            self.evaluate()
        failure = diagnostic.read(self.output / "run" / "failure.json")
        self.assertEqual(failure["completed_cells"], ["OFF", "P_ON"])
        self.assertFalse((self.output / "run" / "result.json").exists())

    def test_changed_write_adapter_during_readout_blocks_next_cell(self):
        self.completed()
        def corrupt(stage):
            target = self.write_root / "fits" / "A" / "adapter" / "DONE"
            target.write_text("changed")
        self.corrupt = corrupt
        with self.assertRaisesRegex(ValueError, "fit seal changed"):
            self.evaluate()
        self.assertEqual(len(self.launches), 1)

    def test_wrong_loaded_adapter_identity_rejected(self):
        self.completed()
        original = self.backend
        def wrong(model, adapter):
            backend = original(model, adapter)
            backend.source_identity = {"forged": "different adapter"}
            return backend
        with patch.object(self, "backend", side_effect=wrong), self.assertRaisesRegex(ValueError, "native backend identity differs"):
            self.evaluate()
        self.assertEqual(len(self.launches), 1)

    def test_native_tokens_wrong_context_and_parent_prefix_rejected(self):
        self.completed()
        original = self.backend
        def wrong(model, adapter):
            backend = original(model, adapter)
            generate = backend.generate
            def output(request):
                response = generate(request)
                response["rendered_prompt"] = "FOREIGN_PARENT_CONTEXT" + response["rendered_prompt"]
                return response
            backend.generate = output
            return backend
        with patch.object(self, "backend", side_effect=wrong), self.assertRaisesRegex(ValueError, "rendered source prompt mismatch"):
            self.evaluate()
        self.assertEqual(len(self.launches), 1)

    def test_prior_capture_change_during_later_cell_fails(self):
        self.completed()
        def corrupt(stage):
            if stage.name == "A_ON":
                raw = self.output / "run" / "OFF" / "data" / "events.jsonl"
                raw.write_text(raw.read_text()+"{}\n")
        self.corrupt = corrupt
        with self.assertRaisesRegex(ValueError, "replay failed"):
            self.evaluate()
        self.assertFalse((self.output / "run" / "result.json").exists())

    def test_worker_spec_extra_context_version_and_adapter_role_fail_closed(self):
        self.completed()
        plan = diagnostic.read(self.output / "plan.json")
        lineage = bridge.accepted_writes(plan)
        (self.output / "run").mkdir()
        spec_path = self.output / "run" / "OFF.spec.json"
        for mutation, message in ((lambda value: value.update(parent_text="not allowed"), "extra context"),
                                  (lambda value: value["protocol"].update(interaction_protocol="interaction_v2"), "protocol changed"),
                                  (lambda value: value.update(adapter="anything"), "adapter mismatch")):
            value = bridge.worker_spec(self.output, plan, lineage, "OFF", time.time()+1800)
            mutation(value)
            self.fixture.replace_json(spec_path, value)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                bridge.worker(spec_path, bridge.digest(spec_path), allow_gpu=True)
        self.assertFalse(self.loads)

    def test_worker_spec_hash_mismatch_precedes_native_or_process_work(self):
        path = self.fixture.root / "spec.json"
        bridge.write_json(path, {"parent_context": "forged"})
        with self.assertRaisesRegex(ValueError, "worker spec changed"):
            bridge.worker(path, "0"*64, allow_gpu=True)
        self.assertFalse(self.loads)

    def test_direct_worker_requires_fresh_supervisor_process(self):
        stage = self.fixture.root / "fake_stage"
        stage.mkdir()
        bridge.write_json(stage / "process.json", dict(pid=-1, pgid=-1))
        with self.assertRaisesRegex(ValueError, "fresh owning supervisor"):
            with bridge.owning_process(stage, time.time()+1800):
                self.fail("unowned worker entered")

    def test_watchdog_cleanup_reserve_and_supervisor_timer_window(self):
        with self.assertRaisesRegex(ValueError, "cleanup reserve"):
            with bridge.work_window(time.time()+130):
                self.fail("expired work window entered")
        with bridge.work_window(time.time()+1800):
            self.assertLessEqual(signal.getitimer(signal.ITIMER_REAL)[0], 1660)
            with bridge.supervised_window(time.time()+1800):
                self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
            self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0], 0)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
