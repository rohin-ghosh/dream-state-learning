import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from gpu.orch_r118_checked_dispatch import launch


class CheckedDispatchTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.request = dict(output=str(self.root / "attempt"), cwd=str(self.root),
                            env={"CUDA_VISIBLE_DEVICES": ""}, preflight_timeout_seconds=30,
                            preflight_commands=[["/usr/bin/true"], ["/usr/bin/true"]],
                            command=["/usr/bin/true"])

    def assert_failure_stops_spawn(self, error):
        run, spawn = Mock(side_effect=error), Mock()
        with self.assertRaises(type(error)):
            launch(self.request, run=run, spawn=spawn)
        spawn.assert_not_called()
        receipt = json.loads((self.root / "attempt/PREFLIGHT_FAILED.json").read_text())
        self.assertFalse(receipt["dispatcher_started"])
        self.assertFalse((self.root / "attempt/DISPATCH_LAUNCH.json").exists())

    def test_nonzero_preflight_never_spawns(self):
        self.assert_failure_stops_spawn(subprocess.CalledProcessError(1, ["preflight"]))

    def test_timeout_preflight_never_spawns(self):
        self.assert_failure_stops_spawn(subprocess.TimeoutExpired(["preflight"], 30))

    def test_missing_preflight_never_spawns(self):
        self.assert_failure_stops_spawn(FileNotFoundError("preflight"))

    def test_second_failure_does_not_fall_through(self):
        run = Mock(side_effect=[SimpleNamespace(returncode=0, stdout="ok", stderr=""),
                                subprocess.CalledProcessError(1, ["second"])])
        spawn = Mock()
        with self.assertRaises(subprocess.CalledProcessError):
            launch(self.request, run=run, spawn=spawn)
        spawn.assert_not_called()
        self.assertTrue((self.root / "attempt/PREFLIGHT_00.json").exists())

    def test_success_checks_before_single_detached_spawn(self):
        events = []

        def run(command, **kwargs):
            self.assertTrue(kwargs["check"])
            self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")
            events.append("check")
            return SimpleNamespace(returncode=0, stdout="ok", stderr="")

        def spawn(command, **kwargs):
            events.append("spawn")
            self.assertEqual(events, ["check", "check", "spawn"])
            self.assertTrue(kwargs["start_new_session"])
            return SimpleNamespace(pid=123)

        result = launch(self.request, run=run, spawn=spawn)
        self.assertEqual(result["status"], "STARTED_NOT_BOOTSTRAP_PROOF")
        self.assertEqual(result["pid"], 123)

    def test_existing_attempt_never_replayed(self):
        (self.root / "attempt").mkdir()
        run, spawn = Mock(), Mock()
        with self.assertRaises(FileExistsError):
            launch(self.request, run=run, spawn=spawn)
        run.assert_not_called()
        spawn.assert_not_called()

    def test_no_preflight_rejected(self):
        self.request["preflight_commands"] = []
        spawn = Mock()
        with self.assertRaisesRegex(ValueError, "explicit_preflight"):
            launch(self.request, spawn=spawn)
        spawn.assert_not_called()
        self.assertFalse(Path(self.request["output"]).exists())
