import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch


WORKERS = Path(__file__).resolve().parents[2]
OWNER = WORKERS / "post_reboot_c2_p7_20260919"
PREVIOUS = WORKERS / "rohin233_recovery_node4_20260918"
sys.path.insert(0, str(OWNER))
SPECIFICATION = importlib.util.spec_from_file_location("approved_c2_service", OWNER / "c2_service.py")
SERVICE = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(SERVICE)


class C2OwnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.owner = self.root / "owner"
        self.previous = self.root / "previous"
        self.owner.mkdir()
        self.previous.joinpath("private").mkdir(parents=True)
        for name, value in (("OWN", self.owner), ("PREVIOUS", self.previous)):
            patcher = patch.object(SERVICE, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_live_original_publisher_is_not_started_or_signalled(self):
        lock_path = self.previous / "private/C2_WAIT_CONTROLLER.lock"
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch.object(SERVICE.subprocess, "Popen") as spawn, patch.object(SERVICE.time, "sleep", side_effect=InterruptedError):
                with self.assertRaises(InterruptedError):
                    SERVICE.main()
        spawn.assert_not_called()
        self.assertFalse(list(self.owner.glob("c2_session*")))

    def test_duplicate_owner_fails_on_its_unique_lock(self):
        with (self.owner / "C2_SERVICE.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch.object(SERVICE.subprocess, "Popen") as spawn:
                with self.assertRaises(BlockingIOError):
                    SERVICE.main()
        spawn.assert_not_called()

    def test_missing_started_ledger_never_starts_publisher(self):
        with patch.object(SERVICE.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(ValueError, "preserved_started_parent_ledger_required"):
                SERVICE.main()
        spawn.assert_not_called()

    def test_lease_end_never_starts_publisher(self):
        with patch.object(SERVICE.time, "time", return_value=1789927200), patch.object(SERVICE.subprocess, "Popen") as spawn:
            SERVICE.main()
        spawn.assert_not_called()

    def test_latest_started_ledger_preserves_reserved_response_frontier(self):
        source = self.root / "pinned.py"
        source.write_text("bound source\n")
        for number, response_count, started in ((1, 5, True), (2, 12, True), (3, 100, False)):
            session = self.owner / ("c2_session" + str(number))
            output = session / "parent"
            output.mkdir(parents=True)
            config_path = session / "CONFIG.json"
            config_path.write_text(json.dumps(dict(start_after_response_count=response_count - 2, hard_end_unix=1789927200)))
            if started:
                (output / "STARTED.json").write_text('{"started": true}')
                attempt = output / "parent_1"
                attempt.mkdir()
                (attempt / "SOURCE.json").write_text(json.dumps(dict(response_count=response_count)))
            manifest = dict(config_path=str(config_path), output=str(output), local_source_sha256={str(source): SERVICE.sha(source)})
            path = session / "MANIFEST.json"
            path.write_text(json.dumps(manifest))
            os.utime(path, ns=(number * 1000000, number * 1000000))
        child = MagicMock(pid=123)
        child.wait.return_value = 0
        with patch.object(SERVICE.subprocess, "Popen", return_value=child) as spawn, patch.object(SERVICE, "validate_manifest") as validate, patch.object(SERVICE.time, "sleep", side_effect=InterruptedError):
            with self.assertRaises(InterruptedError):
                SERVICE.main()
        spawn.assert_called_once()
        validate.assert_called_once()
        created = validate.call_args.args[0]
        config = json.loads(Path(created["config_path"]).read_bytes())
        self.assertEqual(config["start_after_response_count"], 12)
        self.assertEqual(config["predecessor_output"], str(self.owner / "c2_session2/parent"))
        self.assertEqual(config["predecessor_started_sha256"], SERVICE.sha(self.owner / "c2_session2/parent/STARTED.json"))
        self.assertEqual(spawn.call_args.args[0][2], str(self.previous / "checkpoint_tail_parent_strong.py"))


class ParentAuthorityTests(unittest.TestCase):
    def test_pinned_c2_restore_remains_exactly_unchanged(self):
        path = OWNER / "c2_restore.py"
        manifest = json.loads((OWNER / "c2_session1/MANIFEST.json").read_bytes())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), manifest["local_source_sha256"][str(path)])

    def test_bridge_uses_earlier_astra7_bound_not_p7_cpu_lease(self):
        authority = json.loads((PREVIOUS / "LEASE_AUTHORITY.json").read_bytes())
        binding = json.loads((PREVIOUS / "private/bridge/BINDING.json").read_bytes())
        self.assertEqual(authority["node4_cpu_hard_end_unix"], 1790359200)
        self.assertEqual(min(authority["node4_cpu_hard_end_unix"], binding["astra7"]["hard_end_unix"]), 1789927200)


if __name__ == "__main__":
    unittest.main()
