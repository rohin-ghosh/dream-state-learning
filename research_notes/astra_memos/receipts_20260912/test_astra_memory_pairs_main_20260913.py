"""Outer-wrapper custody only; all native/loading/process boundaries mocked."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


SOURCE = Path("/tmp/astra_memory_pairs_main_20260913.py")
SOURCE_SHA256 = "5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe"
PRECHECKS = "/tmp/astra_level1_roster_20260913_attempt1/prechecks.json"
PRECHECKS_SHA256 = "71e8eaa0c326ddef4414539684d20315e3752c48ce425a280438100e32815929"
sys.dont_write_bytecode = True
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
    raise RuntimeError("outer wrapper source differs from reviewed pin")
specification = importlib.util.spec_from_file_location("memory_pairs_main_under_test", SOURCE)
wrapper = importlib.util.module_from_spec(specification)
specification.loader.exec_module(wrapper)


class OuterCustodyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="memory_pairs_wrapper_cpu_")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.base = self.home / "specs"
        self.base.mkdir()
        self.prechecks = self.home / "prechecks.json"
        self.prechecks.write_text(json.dumps({"node2": {"fixture": "reservation-config"}}))
        self.roots = {seed: self.home / f"seed{seed}" for seed in wrapper.GPUS}
        self.plans = {}
        for seed, root in self.roots.items():
            root.mkdir()
            (self.base / f"seed{seed}_prepared.json").write_text(json.dumps({"plan_sha256": f"fixture-plan-{seed}"}))
            index, uuid = wrapper.GPUS[seed]
            self.plans[seed] = dict(gpu_index=index, gpu_uuid=uuid)
        self.runtime = Mock()
        self.probe = Mock()
        self.probe.gpu_state.return_value = True
        self.runtime.verify.side_effect = lambda root, pin, native: (self.plans[next(seed for seed, path in self.roots.items() if path == root)], {"probe": self.probe})
        self.batch = Mock()
        self.batch.reservations.return_value = {"fresh_mock_reservation_check": True}
        self.batch.identity.side_effect = lambda path: dict(pid=int(path.name), start_ticks=123456, pgid=int(path.name))
        self.process = Mock(pid=765432)
        self.process.wait.return_value = 0
        self.popen = Mock(return_value=self.process)
        original_digest = wrapper.digest
        def mapped_path(value):
            return self.prechecks if str(value) == PRECHECKS else Path(value)
        def digest(path):
            return PRECHECKS_SHA256 if Path(path) == self.prechecks else original_digest(path)
        def load(name, path, expected):
            if name == "memory_main_runtime":
                self.assertEqual(Path(path), wrapper.RUNNER)
                self.assertEqual(expected, wrapper.RUNNER_SHA)
                return self.runtime
            self.assertEqual(name, "memory_main_reservations")
            self.assertEqual(path, "/tmp/astra_level1_next_batch_20260913.py")
            self.assertEqual(expected, "03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2")
            return self.batch
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for mocked in (patch.object(wrapper, "BASE", self.base), patch.object(wrapper, "root_for", side_effect=self.roots.__getitem__),
                       patch.object(wrapper, "Path", side_effect=mapped_path), patch.object(wrapper, "digest", side_effect=digest),
                       patch.object(wrapper, "load", side_effect=load), patch.object(wrapper.subprocess, "Popen", self.popen),
                       patch.dict(os.environ, CUDA_VISIBLE_DEVICES=""), contextlib.redirect_stdout(io.StringIO())):
            self.stack.enter_context(mocked)

    def claim(self, seed=0):
        return Path(str(self.roots[seed]) + ".launcher")

    def read(self, name, seed=0):
        return json.loads((self.claim(seed) / name).read_text())

    def test_launch_all_three_reservation_holders_not_controllers(self):
        for seed, (index, uuid) in wrapper.GPUS.items():
            with self.subTest(seed=seed):
                wrapper.launch(seed)
                arguments, options = self.popen.call_args
                self.assertEqual(arguments[0], [sys.executable, "-B", str(SOURCE), "hold", "--seed", str(seed)])
                self.assertEqual(options["env"]["CUDA_VISIBLE_DEVICES"], uuid)
                self.assertTrue(options["start_new_session"])
                self.assertEqual(options["stdin"], subprocess.DEVNULL)
                self.assertEqual(options["stderr"], subprocess.STDOUT)
                self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], "")
                self.batch.reservations.assert_called_with({"fixture": "reservation-config"}, index, uuid)
                self.runtime.verify.assert_called_with(self.roots[seed], f"fixture-plan-{seed}", native=False)
                self.runtime.check_allocation.assert_called_with(self.plans[seed])
                receipt = self.read("launched.json", seed)
                self.assertEqual(receipt["status"], "LAUNCHED_NOT_RESULT")
                self.assertEqual(receipt["plan_sha256"], f"fixture-plan-{seed}")
                self.assertEqual(receipt["pid"], receipt["identity"]["pid"])
                self.assertEqual(receipt["gpu_uuid"], uuid)
                self.assertEqual(receipt["custodian_sha256"], SOURCE_SHA256)
                self.assertEqual(receipt["controller_seconds"], 3600)
                self.assertTrue((self.claim(seed) / "stdout.log").exists())
        self.process.wait.assert_not_called()

    def test_holder_retains_cvd_while_controller_cvd_is_empty(self):
        for seed, (_, uuid) in wrapper.GPUS.items():
            with self.subTest(seed=seed), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=uuid):
                self.claim(seed).mkdir()
                def waiting():
                    self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], uuid)
                    self.assertEqual(self.popen.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")
                    self.assertTrue((self.claim(seed) / "controller.json").is_file())
                    self.assertFalse((self.claim(seed) / "exit.json").exists())
                    return 0
                self.process.wait.side_effect = waiting
                with self.assertRaises(SystemExit) as stopped:
                    wrapper.hold(seed)
                self.assertEqual(stopped.exception.code, 0)
                self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], uuid)
                command = self.popen.call_args.args[0]
                self.assertEqual(command, [sys.executable, "-B", str(wrapper.RUNNER), "controller", "--root", str(self.roots[seed]),
                                           "--plan-sha256", f"fixture-plan-{seed}", "--allow-gpu"])
                self.assertNotIn("start_new_session", self.popen.call_args.kwargs)
                self.assertEqual(self.read("controller.json", seed)["pid"], self.process.pid)
                self.assertEqual(self.read("exit.json", seed)["returncode"], 0)

    def test_holder_preserves_nonzero_controller_exit(self):
        self.claim().mkdir()
        self.process.wait.return_value = 7
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=wrapper.GPUS[0][1]):
            with self.assertRaises(SystemExit) as stopped:
                wrapper.hold(0)
        self.assertEqual(stopped.exception.code, 7)
        self.assertEqual(self.read("exit.json")["returncode"], 7)
        self.assertTrue((self.claim() / "controller.json").exists())

    def test_bad_holder_cvd_or_runner_pin_never_spawns(self):
        with self.assertRaises(AssertionError):
            wrapper.hold(0)
        self.popen.assert_not_called()
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=wrapper.GPUS[0][1]), patch.object(wrapper, "digest", return_value="wrong"):
            with self.assertRaises(AssertionError):
                wrapper.hold(0)
        self.popen.assert_not_called()

    def test_failed_environment_precheck_preserves_claim_and_no_spawn(self):
        self.batch.reservations.side_effect = RuntimeError("reserved by another holder")
        with self.assertRaisesRegex(RuntimeError, "reserved"):
            wrapper.launch(0)
        self.popen.assert_not_called()
        self.probe.gpu_state.assert_not_called()
        failure = self.read("failure.json")
        self.assertFalse(failure["controller_may_be_running"])
        self.assertIn("reserved", failure["error"])
        before = (self.claim() / "failure.json").read_bytes()
        with self.assertRaises(FileExistsError):
            wrapper.launch(0)
        self.assertEqual((self.claim() / "failure.json").read_bytes(), before)
        self.popen.assert_not_called()

    def test_occupied_gpu_preserves_precheck_and_no_spawn(self):
        self.probe.gpu_state.return_value = False
        with self.assertRaises(AssertionError):
            wrapper.launch(0)
        self.popen.assert_not_called()
        self.runtime.check_allocation.assert_not_called()
        self.assertEqual(self.read("precheck.json"), {"fresh_mock_reservation_check": True})
        self.assertFalse(self.read("failure.json")["controller_may_be_running"])

    def test_failed_allocation_preserves_precheck_and_no_spawn(self):
        self.runtime.check_allocation.side_effect = ValueError("boot or lease mismatch")
        with self.assertRaisesRegex(ValueError, "lease"):
            wrapper.launch(0)
        self.popen.assert_not_called()
        self.assertTrue((self.claim() / "precheck.json").exists())
        self.assertFalse(self.read("failure.json")["controller_may_be_running"])

    def test_popen_failure_preserves_precheck_log_and_failure(self):
        self.popen.side_effect = OSError("cannot spawn holder")
        with self.assertRaisesRegex(OSError, "spawn"):
            wrapper.launch(0)
        self.assertTrue((self.claim() / "precheck.json").exists())
        self.assertTrue((self.claim() / "stdout.log").exists())
        self.assertFalse(self.read("failure.json")["controller_may_be_running"])
        self.assertFalse((self.claim() / "launched.json").exists())

    def test_postspawn_identity_failure_marks_process_may_be_running(self):
        self.batch.identity.side_effect = OSError("identity read failed")
        with self.assertRaisesRegex(OSError, "identity"):
            wrapper.launch(0)
        self.assertTrue(self.read("failure.json")["controller_may_be_running"])
        self.process.terminate.assert_not_called()
        self.process.kill.assert_not_called()
        self.assertFalse((self.claim() / "launched.json").exists())

    def test_postspawn_receipt_failure_preserves_running_uncertainty(self):
        original_write = wrapper.write
        def write(path, value):
            if Path(path).name == "launched.json":
                raise OSError("launch receipt failed")
            original_write(path, value)
        with patch.object(wrapper, "write", side_effect=write):
            with self.assertRaisesRegex(OSError, "receipt"):
                wrapper.launch(0)
        self.assertTrue(self.read("failure.json")["controller_may_be_running"])
        self.assertTrue((self.claim() / "stdout.log").exists())

    def test_started_controller_and_existing_claim_prevent_duplicate_spawn(self):
        (self.roots[0] / "controller_started.json").write_text("{}")
        with self.assertRaises(AssertionError):
            wrapper.launch(0)
        self.assertFalse(self.claim().exists())
        self.claim(1).mkdir()
        sentinel = self.claim(1) / "keep"
        sentinel.write_bytes(b"existing-attempt")
        with self.assertRaises(FileExistsError):
            wrapper.launch(1)
        self.assertEqual(sentinel.read_bytes(), b"existing-attempt")
        self.popen.assert_not_called()

    def test_roster_pin_and_verify_fail_before_claim_or_spawn(self):
        with patch.object(wrapper, "digest", return_value="wrong"):
            with self.assertRaises(AssertionError):
                wrapper.launch(0)
        self.runtime.verify.assert_not_called()
        self.runtime.verify.side_effect = ValueError("prepared plan changed")
        with self.assertRaisesRegex(ValueError, "plan"):
            wrapper.launch(0)
        self.assertFalse(self.claim().exists())
        self.popen.assert_not_called()

    def test_holder_wait_exception_preserves_controller_but_has_no_exit_receipt(self):
        self.claim().mkdir()
        self.process.wait.side_effect = OSError("wait interrupted")
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=wrapper.GPUS[0][1]):
            with self.assertRaisesRegex(OSError, "wait"):
                wrapper.hold(0)
        self.assertTrue((self.claim() / "controller.json").exists())
        self.assertFalse((self.claim() / "exit.json").exists())
        self.assertFalse((self.claim() / "failure.json").exists())
        self.process.kill.assert_not_called()


if __name__ == "__main__":
    unittest.main()
