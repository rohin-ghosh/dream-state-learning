import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location("controller", "/tmp/astra_l2_access_controller_20260913.py")
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


class ControllerTests(unittest.TestCase):
    def test_no_permission_before_side_effect(self):
        with self.assertRaisesRegex(ValueError, "permission"):
            controller.controller(SimpleNamespace(allow_gpu=False))

    def test_no_controller_cuda_reservation(self):
        with patch.dict(controller.os.environ, CUDA_VISIBLE_DEVICES="3"):
            with self.assertRaisesRegex(ValueError, "reserve"):
                controller.controller(SimpleNamespace(allow_gpu=True))

    def test_write_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            controller.write(path, {"status": "first"})
            with self.assertRaises(FileExistsError):
                controller.write(path, {"status": "replacement"})

    def test_pin_failure_before_precheck(self):
        with patch.object(controller, "digest", return_value="wrong"), patch.object(controller.subprocess, "run") as run:
            with self.assertRaisesRegex(ValueError, "precheck changed"):
                controller.precheck(SimpleNamespace(precheck="fixture"), Path("unused"))
            run.assert_not_called()

    def test_failed_precheck_rejected_and_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "precheck.json"
            with patch.object(controller, "digest", return_value=controller.PRECHECK_PIN), patch.object(
                controller.subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout="occupied", stderr="")):
                with self.assertRaisesRegex(ValueError, "check failed"):
                    controller.precheck(SimpleNamespace(precheck="fixture"), output)
            self.assertTrue(output.exists())

    def test_refuse_kill_wrong_identity(self):
        process = Mock(pid=123)
        process.poll.return_value = None
        with patch.object(controller, "identity", return_value={"pid": 124}), patch.object(controller.os, "killpg") as kill:
            with self.assertRaisesRegex(ValueError, "unbound"):
                controller.stop_owned(process, {"pid": 123, "pgid": 123, "start_ticks": 5})
            kill.assert_not_called()

    def test_finished_process_not_killed(self):
        process = Mock(pid=123)
        process.poll.return_value = 0
        with patch.object(controller.os, "killpg") as kill:
            controller.stop_owned(process, {})
            kill.assert_not_called()

    def test_owned_timeout_cleanup(self):
        process = Mock(pid=123)
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("fixture", 10), 0]
        bound = dict(pid=123, pgid=123, start_ticks=5)
        with patch.object(controller, "identity", return_value=bound), patch.object(controller.os, "killpg") as kill:
            controller.stop_owned(process, bound)
            self.assertEqual(kill.call_count, 2)
            self.assertTrue(all(call.args[0] == 123 for call in kill.call_args_list))

    def test_budget_exhaustion_prevents_launch(self):
        with patch.object(controller.time, "time", return_value=100), patch.object(controller.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(ValueError, "budget"):
                controller.run_worker(None, None, "OFF", 150)
            launch.assert_not_called()

    def test_environment_freezes_network_and_controller_device(self):
        env = controller.environment()
        self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "")
        self.assertEqual(env["HF_HUB_OFFLINE"], "1")
        self.assertEqual(controller.environment(controller.GPU_UUID)["CUDA_VISIBLE_DEVICES"], controller.GPU_UUID)


if __name__ == "__main__":
    unittest.main()
