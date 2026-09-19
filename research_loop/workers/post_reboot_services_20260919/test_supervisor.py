import copy
import fcntl
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import supervisor


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "daemon.py"
        self.source.write_text("print('test daemon')\n")
        self.lease = self.root / "lease.json"
        self.lease.write_text(json.dumps({"bound": 200}))
        self.entry = dict(name="test-daemon", enabled=True, kind="collector", owner="test owner",
            approval_scope="non-material recovery", local_daemon_only=True, restart_safe=True,
            self_enforces_lease=True, foreground=True, shutdown_leaves_child_natives_running=True,
            child_native=False, argv=["/usr/bin/python3", "-B", str(self.source)],
            cwd=str(self.root), entrypoint=str(self.source),
            entrypoint_sha256=hashlib.sha256(self.source.read_bytes()).hexdigest(), until_unix=150,
            lease_evidence=dict(path=str(self.lease), sha256=hashlib.sha256(self.lease.read_bytes()).hexdigest(),
                                json_pointer="/bound"))
        for attribute, value in (("REPO", self.root), ("HERE", self.root)):
            patcher = patch.object(supervisor, attribute, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(supervisor.time, "time", return_value=100)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tick(self, entry=None, matches=None):
        manager = supervisor.Supervisor()
        with patch.object(supervisor, "matching_processes", return_value=matches or []), patch.object(supervisor.subprocess, "Popen") as spawn:
            spawn.return_value.pid = 456
            result = manager.tick([self.entry if entry is None else entry])
        return manager, result, spawn

    def test_bound_manifest_is_valid(self):
        self.assertEqual(supervisor.validate(self.entry)["until_unix"], 150)

    def test_fleet_horizon_is_distinct_from_collector_margin(self):
        import collector
        self.assertEqual(collector.MAX_UNTIL, 1790791170)
        self.assertEqual(supervisor.MAX_UNTIL, 1790791200)
        self.lease.write_text(json.dumps({"bound": 1790791200}))
        self.entry["lease_evidence"]["sha256"] = supervisor.digest(self.lease)
        self.entry["until_unix"] = 1790791200
        self.assertEqual(supervisor.validate(self.entry)["until_unix"], 1790791200)

    def test_later_fleet_cap_cannot_extend_individual_lease(self):
        self.lease.write_text(json.dumps({"bound": 1790791170}))
        self.entry["lease_evidence"]["sha256"] = supervisor.digest(self.lease)
        self.entry["until_unix"] = 1790791200
        with self.assertRaisesRegex(ValueError, "cannot_extend_source_lease"):
            supervisor.validate(self.entry)

    def test_horizon_beyond_existing_fleet_is_rejected(self):
        self.lease.write_text(json.dumps({"bound": 1790791201}))
        self.entry["lease_evidence"]["sha256"] = supervisor.digest(self.lease)
        self.entry["until_unix"] = 1790791201
        with self.assertRaisesRegex(ValueError, "finite_existing_fleet_horizon_required"):
            supervisor.validate(self.entry)

    def test_sigterm_exit_preserves_owned_workers_before_lease_end(self):
        manager = supervisor.Supervisor()
        worker = MagicMock(pid=456)
        worker.poll.return_value = None
        manager.children["test-daemon"] = (worker, self.entry)
        handlers = {}
        with patch.object(supervisor.sys, "argv", ["supervisor.py"]), \
             patch.object(supervisor, "require_host"), \
             patch.object(supervisor, "identity", return_value={"pid": 123}), \
             patch.object(supervisor, "load_entries", return_value=([self.entry], [])), \
             patch.object(supervisor, "Supervisor", return_value=manager), \
             patch.object(supervisor, "matching_processes", return_value=[{"pid": 456}]), \
             patch.object(supervisor.signal, "signal", side_effect=lambda number, handler: handlers.update({number: handler})), \
             patch.object(supervisor.time, "sleep", side_effect=lambda delay: handlers[supervisor.signal.SIGTERM](15, None)):
            self.assertEqual(supervisor.main(), 0)
        worker.terminate.assert_not_called()
        worker.kill.assert_not_called()

    def test_lease_extension_and_changed_evidence_are_rejected(self):
        entry = copy.deepcopy(self.entry)
        entry["until_unix"] = 201
        with self.assertRaisesRegex(ValueError, "cannot_extend_source_lease"):
            supervisor.validate(entry)
        entry["until_unix"] = 150
        entry["lease_evidence"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "lease_evidence_digest_mismatch"):
            supervisor.validate(entry)

    def test_changed_source_is_rejected(self):
        self.source.write_text("print('changed')\n")
        with self.assertRaisesRegex(ValueError, "source_digest_changed"):
            supervisor.validate(self.entry)

    def test_native_and_shutdown_propagation_are_rejected(self):
        for field, value in (("child_native", True), ("shutdown_leaves_child_natives_running", False), ("foreground", False)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                supervisor.validate(dict(self.entry, **{field: value}))

    def test_secrets_and_inline_commands_are_rejected(self):
        for extra in (["--api-key", "never-store-me"], ["--token=abc-secret"], ["https://user:pass@example.test"]):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                supervisor.validate(dict(self.entry, argv=self.entry["argv"] + extra))
        with self.assertRaises(ValueError):
            supervisor.validate(dict(self.entry, argv=["/usr/bin/python3", "-c", "print(1)"]))
        with self.assertRaises(ValueError):
            supervisor.validate(dict(self.entry, env={"API_KEY": "never-store-me"}))

    def test_approval_watch_requires_watch_only(self):
        with self.assertRaisesRegex(ValueError, "must_not_approve"):
            supervisor.validate(dict(self.entry, kind="approval_watch"))
        self.assertTrue(supervisor.validate(dict(self.entry, kind="approval_watch", watch_only=True)))

    def test_expired_entry_never_starts(self):
        unused, result, spawn = self.tick(dict(self.entry, until_unix=100))
        spawn.assert_not_called()
        self.assertEqual(result[0]["status"], "LEASE_EXPIRED_NO_LAUNCH")

    def test_lease_expiring_during_discovery_never_starts(self):
        with patch.object(supervisor.time, "time", side_effect=[100, 160, 160]):
            unused, result, spawn = self.tick()
        spawn.assert_not_called()
        self.assertEqual(result[0]["status"], "LEASE_EXPIRED_DURING_DISCOVERY_NO_LAUNCH")

    def test_existing_process_is_adopted_without_restart(self):
        unused, result, spawn = self.tick(matches=[dict(pid=123, start_ticks="456")])
        spawn.assert_not_called()
        self.assertEqual(result[0]["status"], "RUNNING_ADOPTED_NO_SIGNALS")

    def test_duplicate_existing_processes_are_not_stopped_or_restarted(self):
        unused, result, spawn = self.tick(matches=[dict(pid=123), dict(pid=124)])
        spawn.assert_not_called()
        self.assertEqual(result[0]["status"], "DUPLICATE_EXISTING_PROCESSES_NO_ACTION")

    def test_busy_legacy_lock_suppresses_start(self):
        lock_path = self.root / "legacy.lock"
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            unused, result, spawn = self.tick(dict(self.entry, singleton_lock=str(lock_path)))
        spawn.assert_not_called()
        self.assertEqual(result[0]["status"], "EXISTING_SINGLETON_LOCK_HELD_NO_LAUNCH")

    def test_start_is_direct_no_shell_and_no_secret_log_capture(self):
        unused, result, spawn = self.tick()
        self.assertEqual(result[0]["status"], "STARTED_LOCAL_DAEMON")
        self.assertEqual(spawn.call_args.args, (self.entry["argv"],))
        self.assertNotIn("shell", spawn.call_args.kwargs)
        self.assertEqual(spawn.call_args.kwargs["stdout"], supervisor.subprocess.DEVNULL)
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])

    def test_disabled_entry_is_not_started(self):
        unused, result, spawn = self.tick(dict(name="test-daemon", enabled=False))
        spawn.assert_not_called()
        self.assertEqual(result[0]["status"], "DISABLED_AWAITING_OWNER_ARGV")

    def test_only_owned_local_pid_is_stopped_at_lease(self):
        manager = supervisor.Supervisor()
        process = MagicMock(pid=123)
        process.poll.return_value = None
        manager.children["test-daemon"] = (process, dict(self.entry, until_unix=100))
        with patch.object(supervisor.os, "killpg") as signal_group:
            manager.tick([])
        process.terminate.assert_called_once()
        signal_group.assert_not_called()

    def test_crash_has_restart_backoff(self):
        manager = supervisor.Supervisor()
        process = MagicMock(returncode=1)
        process.poll.return_value = 1
        manager.children["test-daemon"] = (process, self.entry)
        with patch.object(supervisor, "matching_processes", return_value=[]), patch.object(supervisor.subprocess, "Popen") as spawn:
            result = manager.tick([self.entry])
        spawn.assert_not_called()
        self.assertEqual(result[0]["status"], "RESTART_BACKOFF")

    def test_changed_owned_command_never_launches_duplicate(self):
        manager = supervisor.Supervisor()
        process = MagicMock()
        process.poll.return_value = None
        manager.children["test-daemon"] = (process, self.entry)
        with patch.object(supervisor, "matching_processes", return_value=[]), patch.object(supervisor.subprocess, "Popen") as spawn:
            result = manager.tick([self.entry])
        spawn.assert_not_called()
        self.assertEqual(result[0]["status"], "OWNED_PROCESS_COMMAND_CHANGED_NO_DUPLICATE")

    def test_bad_registry_file_does_not_hide_good_entries(self):
        (self.root / "bad.json").write_text("{")
        (self.root / "test-daemon.json").write_text(json.dumps(self.entry))
        entries, errors = supervisor.load_entries(self.root)
        self.assertEqual([entry["name"] for entry in entries], ["test-daemon"])
        self.assertTrue(any(error["file"] == "bad.json" for error in errors))

    def test_sandbox_pid_namespace_is_rejected(self):
        with patch.object(supervisor.os, "getuid", return_value=supervisor.EXPECTED_UID), patch.object(supervisor.os, "uname") as uname, patch.object(Path, "read_text", return_value="python\n"):
            uname.return_value.nodename = supervisor.EXPECTED_HOST
            with self.assertRaisesRegex(ValueError, "host_pid_namespace"):
                supervisor.require_host()


if __name__ == "__main__":
    unittest.main()
