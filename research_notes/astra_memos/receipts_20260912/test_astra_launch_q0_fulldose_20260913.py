import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("fulldose_launcher", "/tmp/astra_launch_q0_fulldose_20260913.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / "source"
        (self.source / "gpu").mkdir(parents=True)
        executor = self.source / "gpu/astra_pairwise_q0_fulldose.py"
        executor.write_text("fixture")
        self.root = self.base / "root"
        self.root.mkdir()
        checker = self.base / "checker.py"
        checker.write_text("fixture")
        self.manifest = dict(version="fixture_v2", ready=True, config=dict(
            lease_end_unix=time.time() + 100000, lease_cutoff_unix=time.time() + 70000,
            gpu_uuid="GPU-fixture"))
        self.options = SimpleNamespace(source=str(self.source), root=str(self.root),
            stdout=str(self.base / "controller.log"), executor_sha256=launcher.digest(executor),
            manifest_sha256="", version="fixture_v2", precheck=str(checker),
            precheck_sha256=launcher.digest(checker), gpu_index=0, allow_gpu=True)
        self.seal()

    def seal(self):
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        self.options.manifest_sha256 = launcher.digest(self.root / "manifest.json")
        (self.root / "PREPARED.json").write_text(json.dumps(dict(manifest_sha256=self.options.manifest_sha256)))

    def reject(self, message):
        with patch.object(launcher.subprocess, "run") as check, patch.object(launcher.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(ValueError, message):
                launcher.launch(self.options)
            check.assert_not_called()
            spawn.assert_not_called()

    def test_no_opt_in(self):
        self.options.allow_gpu = False
        self.reject("opt-in")

    def test_changed_source(self):
        self.options.executor_sha256 = "0" * 64
        self.reject("source")

    def test_existing_root(self):
        (self.root / "STARTED.json").write_text("{}")
        self.reject("relaunched")

    def test_existing_stdout(self):
        Path(self.options.stdout).write_text("preserved")
        self.reject("stdout")

    def test_wrong_version(self):
        self.options.version = "v1"
        self.reject("version")

    def test_missing_lease_margin(self):
        self.manifest["config"]["lease_cutoff_unix"] = self.manifest["config"]["lease_end_unix"]
        self.seal()
        self.reject("six-hour")

    def test_short_window(self):
        self.manifest["config"]["lease_cutoff_unix"] = time.time() + 10000
        self.seal()
        self.reject("window")

    def test_precheck_failure_never_spawns(self):
        with patch.object(launcher.subprocess, "run", side_effect=RuntimeError("occupied")), patch.object(launcher.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(RuntimeError, "occupied"):
                launcher.launch(self.options)
            spawn.assert_not_called()
        self.assertFalse(Path(self.options.stdout).exists())

    def test_success_mock_checks_and_detaches(self):
        with patch.object(launcher.subprocess, "run") as check, patch.object(launcher.subprocess, "Popen", return_value=SimpleNamespace(pid=os.getpid())) as spawn:
            result = launcher.launch(self.options)
        self.assertEqual(result["runtime_cap_seconds"], 10800)
        self.assertEqual(result["controller_pid"], os.getpid())
        self.assertEqual(check.call_args.args[0][-2:], ["--gpu-uuid", "GPU-fixture"])
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])
        self.assertEqual(spawn.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], "GPU-fixture")
        self.assertEqual(spawn.call_args.args[0][-4:], ["execute", "--out", str(self.root), "--allow-gpu"])


if __name__ == "__main__":
    unittest.main()
