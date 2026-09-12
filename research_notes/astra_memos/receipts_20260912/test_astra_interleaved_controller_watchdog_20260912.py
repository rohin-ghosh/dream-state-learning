"""Fake-clock/proc/signaler tests only. Never opens real pidfds or sends signals."""
from contextlib import ExitStack
import copy
import importlib.util
import json
import os
from pathlib import Path
import signal
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location("interleaved_watchdog_test", "/tmp/astra_interleaved_controller_watchdog_20260912.py")
side = importlib.util.module_from_spec(spec)
spec.loader.exec_module(side)


class Clock:
    def __init__(self, wall=2659.9):
        self.wall, self.mono, self.hook = wall, 10., None

    def time(self): return self.wall
    def monotonic(self): return self.mono
    def sleep(self, seconds):
        assert 0 < seconds <= .2
        self.wall += seconds
        self.mono += seconds
        if self.hook:
            self.hook(self)


def contract():
    return dict(pid=12345, pgid=12345, proc_start_ticks=123456789,
        command=["/venv/bin/python", "-B", "/tmp/owned.py", "run"],
        controller_started_unix=1000., effective_deadline=2800., term_at=2660.,
        launch_path="/fixture/launch.json", launch_sha256="launch", reservation_path="/fixture/reservation.json",
        reservation_sha256="reservation", plan_sha256=side.PLAN_SHA, runner_sha256=side.RUNNER_SHA)


class Proc:
    def __init__(self):
        bound = contract()
        self.value = {key: bound[key] for key in ("pid", "pgid", "proc_start_ticks", "command")}
        self.value.update(state="S", uid=1000)
        self.reads, self.hook = 0, None

    def read(self, pid):
        assert pid == 12345
        self.reads += 1
        if self.hook:
            self.hook(self)
        return copy.deepcopy(self.value)


class Signaler:
    def __init__(self, clock, proc, exit_on=signal.SIGKILL):
        self.clock, self.proc, self.exit_on = clock, proc, exit_on
        self.opened, self.sent, self.closed, self.dead = [], [], False, False
        self.on_open = None

    def open(self, pid):
        self.opened.append(pid)
        if self.on_open: self.on_open()

    def exited(self): return self.dead

    def send(self, number):
        self.sent.append((number, self.clock.wall, self.clock.mono))
        if number == self.exit_on:
            self.proc.value["state"] = "Z"
            self.proc.value["command"] = []

    def close(self): self.closed = True


class WatchTests(unittest.TestCase):
    def run_watch(self, tmp, proc=None, clock=None, signaler=None, immutable=None):
        proc, clock = proc or Proc(), clock or Clock()
        signaler = signaler or Signaler(clock, proc)
        out = Path(tmp) / "watch"
        result = side.monitor(contract(), out, proc, signaler, clock, immutable or (lambda bound: None), uid=1000)
        return result, signaler, out

    def test_term_at_cleanup_boundary_kill_at_exact1800(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, signaler, out = self.run_watch(tmp)
            self.assertEqual([row[0] for row in signaler.sent], [signal.SIGTERM, signal.SIGKILL])
            self.assertAlmostEqual(signaler.sent[0][1], 2660.)
            self.assertAlmostEqual(signaler.sent[1][1], 2800.)
            self.assertTrue(result["success"])
            self.assertEqual(result["observation"], "ZOMBIE")
            self.assertTrue(signaler.closed)
            self.assertEqual(signaler.opened, [12345])
            self.assertEqual(side.decode(side.read_bytes(out / "term-intent.json"))["reason"], "CLEANUP140S_BOUNDARY")
            self.assertEqual(side.decode(side.read_bytes(out / "kill-intent.json"))["reason"], "HARD1800S_DEADLINE")
            self.assertFalse(result["worker_cleanup_verified"])
            self.assertFalse(result["gpu_release_verified"])

    def test_normal_exit_before_term_no_signals(self):
        proc, clock = Proc(), Clock(2600.)
        proc.hook = lambda obj: setattr(obj, "value", None) if clock.wall >= 2601 else None
        with tempfile.TemporaryDirectory() as tmp:
            result, signaler, _ = self.run_watch(tmp, proc, clock)
        self.assertTrue(result["success"])
        self.assertEqual(result["observation"], "ABSENT")
        self.assertEqual(signaler.sent, [])

    def test_initial_zombie_empty_cmdline_no_signals(self):
        proc = Proc()
        proc.value.update(state="Z", command=[])
        with tempfile.TemporaryDirectory() as tmp:
            result, signaler, _ = self.run_watch(tmp, proc)
        self.assertTrue(result["success"])
        self.assertEqual(signaler.opened, [])
        self.assertEqual(signaler.sent, [])

    def test_term_success_means_no_kill(self):
        proc, clock = Proc(), Clock()
        signaler = Signaler(clock, proc, signal.SIGTERM)
        with tempfile.TemporaryDirectory() as tmp:
            result, _, out = self.run_watch(tmp, proc, clock, signaler)
            self.assertFalse((out / "kill-intent.json").exists())
        self.assertTrue(result["success"])
        self.assertEqual(len(signaler.sent), 1)

    def test_late_start_kills_immediately_without_new_grace(self):
        clock = Clock(2801.)
        with tempfile.TemporaryDirectory() as tmp:
            result, signaler, out = self.run_watch(tmp, clock=clock)
            self.assertTrue(side.decode(side.read_bytes(out / "watch.json"))["late_start"])
            self.assertFalse((out / "term-intent.json").exists())
        self.assertTrue(result["success"])
        self.assertEqual(signaler.sent, [(signal.SIGKILL, 2801., 10.)])
        self.assertFalse(result["budget_extended"])

    def test_late_after_term_boundary_no140s_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, signaler, _ = self.run_watch(tmp, clock=Clock(2700.))
        self.assertEqual(signaler.sent[0][1], 2700.)
        self.assertAlmostEqual(signaler.sent[1][1], 2800.)

    def test_identity_mismatches_no_signal(self):
        for key, value in (("pid", 54321), ("pgid", 55555), ("proc_start_ticks", 123456790), ("uid", 999), ("command", ["foreign"])):
            proc = Proc()
            proc.value[key] = value
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                result, signaler, _ = self.run_watch(tmp, proc, Clock(2801.))
            self.assertFalse(result["success"])
            self.assertEqual(signaler.sent, [])

    def test_pid_reuse_after_term_never_signals_replacement(self):
        proc, clock = Proc(), Clock()
        proc.hook = lambda obj: obj.value.update(proc_start_ticks=999) if clock.wall > 2700 else None
        with tempfile.TemporaryDirectory() as tmp:
            result, signaler, _ = self.run_watch(tmp, proc, clock)
        self.assertFalse(result["success"])
        self.assertEqual([row[0] for row in signaler.sent], [signal.SIGTERM])

    def test_recheck_after_pidfd_open_catches_reuse(self):
        proc, clock = Proc(), Clock(2801.)
        signaler = Signaler(clock, proc)
        signaler.on_open = lambda: proc.value.update(proc_start_ticks=9)
        with tempfile.TemporaryDirectory() as tmp:
            result, _, _ = self.run_watch(tmp, proc, clock, signaler)
        self.assertFalse(result["success"])
        self.assertEqual(signaler.sent, [])

    def test_final_cmdline_recheck_before_signal(self):
        proc = Proc()
        proc.hook = lambda obj: obj.value.update(command=["foreign"]) if obj.reads == 3 else None
        with tempfile.TemporaryDirectory() as tmp:
            result, signaler, out = self.run_watch(tmp, proc, Clock(2801.))
            self.assertFalse((out / "kill-intent.json").exists())
        self.assertFalse(result["success"])
        self.assertEqual(signaler.sent, [])

    def test_immutable_receipt_mutation_prevents_signal(self):
        immutable = Mock(side_effect=[None, ValueError("launch changed")])
        with tempfile.TemporaryDirectory() as tmp:
            result, signaler, _ = self.run_watch(tmp, clock=Clock(2801.), immutable=immutable)
        self.assertFalse(result["success"])
        self.assertEqual(signaler.sent, [])

    def test_backward_wall_jump_cannot_extend_monotonic_deadline(self):
        clock = Clock()
        def jump_once(obj):
            if obj.wall >= 2670:
                obj.wall -= 3000
                obj.hook = None
        clock.hook = jump_once
        with tempfile.TemporaryDirectory() as tmp:
            result, signaler, out = self.run_watch(tmp, clock=clock)
            event = side.decode(side.read_bytes(out / "kill-intent.json"))
            self.assertTrue(event["monotonic_deadline_reached"])
            self.assertFalse(event["wall_deadline_reached"])
        self.assertTrue(result["success"])
        self.assertAlmostEqual(signaler.sent[-1][2], 150.1)

    def test_forward_wall_jump_never_extends(self):
        clock = Clock()
        def jump_once(obj): obj.wall += 3000; obj.hook = None
        clock.hook = jump_once
        with tempfile.TemporaryDirectory() as tmp:
            result, signaler, _ = self.run_watch(tmp, clock=clock)
        self.assertTrue(result["success"])
        self.assertEqual([row[0] for row in signaler.sent], [signal.SIGKILL])

    def test_kill_survivor_bounded_observation_no_repeated_signals(self):
        proc, clock = Proc(), Clock(2801.)
        signaler = Signaler(clock, proc, exit_on=None)
        with tempfile.TemporaryDirectory() as tmp:
            result, _, _ = self.run_watch(tmp, proc, clock, signaler)
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "CONTROLLER_STILL_PRESENT_AFTER_KILL")
        self.assertLessEqual(clock.wall, 2806.01)
        self.assertEqual(len(signaler.sent), 1)

    def test_signal_permission_error_is_logged_not_retried(self):
        proc, clock = Proc(), Clock(2801.)
        signaler = Signaler(clock, proc)
        signaler.send = Mock(side_effect=PermissionError("fixture"))
        with tempfile.TemporaryDirectory() as tmp:
            result, _, out = self.run_watch(tmp, proc, clock, signaler)
            event = side.decode(side.read_bytes(out / "kill-result.json"))
            self.assertEqual(event["outcome"], "SIGNAL_FAILED")
        self.assertFalse(result["success"])
        self.assertEqual(result["signals_attempted"], ["kill"])
        signaler.send.assert_called_once_with(signal.SIGKILL)

    def test_open_exit_race_success_without_numeric_pid_fallback(self):
        proc, clock = Proc(), Clock(2801.)
        signaler = Signaler(clock, proc)
        signaler.open = Mock(side_effect=ProcessLookupError())
        with tempfile.TemporaryDirectory() as tmp:
            result, _, _ = self.run_watch(tmp, proc, clock, signaler)
        self.assertTrue(result["success"])
        self.assertEqual(signaler.sent, [])

    def test_fresh_directory_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, out = self.run_watch(tmp)
            before = {path.name: path.read_bytes() for path in out.iterdir()}
            with self.assertRaisesRegex(ValueError, "fresh watch"): self.run_watch(tmp)
            self.assertEqual(before, {path.name: path.read_bytes() for path in out.iterdir()})

    def test_directory_alias_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            alias = Path(tmp) / "alias"
            alias.symlink_to(tmp, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "aliased"): self.run_watch(alias)


class ParsingAndContractTests(unittest.TestCase):
    def test_proc_reader_preserves_extra_empty_argument(self):
        fields = ["S", "1", "12345"] + ["0"]*16 + ["123456789"]
        raw_stat = ("12345 (fixture) " + " ".join(fields)).encode()
        raw_command = b"\0".join(part.encode() for part in contract()["command"]) + b"\0\0"
        with patch.object(side.Path, "read_bytes", side_effect=[raw_stat, raw_command, raw_stat]), \
            patch.object(side.Path, "stat", return_value=SimpleNamespace(st_uid=1000)):
            snapshot = side.Proc().read(12345)
        self.assertEqual(snapshot["command"][-1], "")
        with self.assertRaisesRegex(ValueError, "cmdline mismatch"): side.identity(snapshot, contract(), 1000)

    def test_proc_stat_parses_embedded_parentheses(self):
        fields = ["S", "1", "12345"] + ["0"]*16 + ["123456789"]
        result = side.parse_stat(("12345 (has ) tricky (name) " + " ".join(fields)).encode())
        self.assertEqual(result, dict(pid=12345, state="S", pgid=12345, proc_start_ticks=123456789))
        with self.assertRaises(ValueError): side.parse_stat(b"12345 no parentheses")

    def test_pidfd_only_system_adapter_all_calls_mocked(self):
        with patch.object(side.os, "pidfd_open", return_value=99) as opener, \
            patch.object(side.signal, "pidfd_send_signal") as sender, patch.object(side.os, "close") as close, \
            patch.object(side.select, "select", return_value=([], [], [])), patch.object(side.os, "kill") as numeric:
            signaler = side.PidfdSignaler()
            signaler.open(12345)
            self.assertFalse(signaler.exited())
            signaler.send(signal.SIGTERM)
            signaler.close()
            opener.assert_called_once_with(12345, 0)
            sender.assert_called_once_with(99, signal.SIGTERM, None, 0)
            close.assert_called_once_with(99)
            numeric.assert_not_called()

    def test_no_pidfd_support_fails_closed(self):
        with patch.object(side.os, "pidfd_open", None), self.assertRaisesRegex(ValueError, "pidfd support"):
            side.PidfdSignaler()

    def fixture(self, tmp, stack):
        root = Path(tmp) / "root"
        (root / "launch").mkdir(parents=True)
        (root / "run").mkdir()
        runner = Path(tmp) / "runner.py"
        runner.write_bytes(b"fixture-only")
        plan = dict(root=str(root), source_root=side.SOURCE, seed=0, device="1", pair_seconds=1800, cleanup_seconds=140,
            python="/venv/bin/python", deadline=3000., real_lease_end=10000.)
        side.write_new(root / "plan.json", plan)
        plan_sha, runner_sha = side.sha(side.read_bytes(root / "plan.json")), side.sha(side.read_bytes(runner))
        stack.enter_context(patch.multiple(side, ROOT=root, RUNNER=runner, PLAN_SHA=plan_sha, RUNNER_SHA=runner_sha))
        reservation = dict(controller_pid=12345, started=1000., effective_deadline=2800., plan_sha256=plan_sha, device="1", real_lease_end=10000.)
        side.write_new(root / "run/reservation.json", reservation)
        launch = dict(root=str(root), source=side.SOURCE, device="1", plan_sha256=plan_sha, script_sha256=runner_sha,
            controller_bound_seconds=1800, pid=12345, pgid=12345, proc_start_ticks=123456789,
            command=["/venv/bin/python", "-B", str(runner), "run", "--source-root", side.SOURCE, "--runroot", str(root), "--allow-gpu"],
            controller_started_unix=1000., effective_deadline=2800., reservation_sha256=side.sha(side.read_bytes(root / "run/reservation.json")))
        side.write_new(root / "launch/launch.json", launch)
        return root, launch

    def test_load_bound_launch_reservation_plan(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            root, _ = self.fixture(tmp, stack)
            path = root / "launch/launch.json"
            result = side.load_contract(path, side.sha(side.read_bytes(path)))
            self.assertEqual(result["term_at"], 2660.)
            self.assertEqual(result["command"][0], "/venv/bin/python")
            side.assert_immutable(result)

    def test_rehashed_launch_mutations_fail_fixed_contract(self):
        for key, value in (("pid", True), ("pgid", 1), ("proc_start_ticks", 0), ("controller_bound_seconds", 1801),
            ("effective_deadline", 2801.), ("controller_started_unix", float("nan")), ("device", "2"), ("command", ["foreign"]),
            ("reservation_sha256", "changed")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                root, launch = self.fixture(tmp, stack)
                launch[key] = value
                path = root / "launch/launch.json"
                path.write_text(json.dumps(launch))
                with self.assertRaises(ValueError): side.load_contract(path, side.sha(side.read_bytes(path)))

    def test_missing_startticks_or_launch_hash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            root, launch = self.fixture(tmp, stack)
            path = root / "launch/launch.json"
            with self.assertRaisesRegex(ValueError, "receipt hash"): side.load_contract(path, "0"*64)
            del launch["proc_start_ticks"]
            path.write_text(json.dumps(launch))
            with self.assertRaises(KeyError): side.load_contract(path, side.sha(side.read_bytes(path)))

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError): side.decode(b'{"pid":1,"pid":2}')


if __name__ == "__main__":
    unittest.main()
