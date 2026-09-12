"""Fake-clock/proc/signaler tests only. Never opens real pidfds or sends signals."""
from contextlib import ExitStack
import copy
import ast
import io
import importlib.util
import json
import os
from pathlib import Path
import signal
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location("interleaved_watchdog_test", "/tmp/astra_interleaved_replication_watchdog_20260912.py")
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
        reservation_sha256="reservation", plan_sha256="a"*64, runner_sha256=side.RUNNER_SHA,
        protected_roots=["/fixture/root", "/fixture/source", "/fixture/material"], immutable_hashes={})


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
            patch.object(side.select, "select", return_value=([], [], [])), patch.object(side.os, "kill") as numeric, \
            patch.object(side.os, "killpg") as group:
            signaler = side.PidfdSignaler()
            signaler.open(12345)
            self.assertFalse(signaler.exited())
            signaler.send(signal.SIGTERM)
            signaler.close()
            opener.assert_called_once_with(12345, 0)
            sender.assert_called_once_with(99, signal.SIGTERM, None, 0)
            close.assert_called_once_with(99)
            numeric.assert_not_called()
            group.assert_not_called()

    def test_no_pidfd_support_fails_closed(self):
        with patch.object(side.os, "pidfd_open", None), self.assertRaisesRegex(ValueError, "pidfd support"):
            side.PidfdSignaler()

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError): side.decode(b'{"pid":1,"pid":2}')

    def test_original_parent_constants_match_frozen_seed_helpers(self):
        tree = ast.parse(Path('/tmp/astra_memory_only_20260912.py').read_text())
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign) and
            any(isinstance(target, ast.Name) and target.id == 'PINS' for target in node.targets))
        original = ast.literal_eval(assignment.value)
        self.assertEqual(side.PARENT_PINS, {seed: list(original[str(seed)]) for seed in (1, 2)})

    def test_bound_driver_hash_without_import_or_native_execution(self):
        self.assertEqual(side.sha(side.read_bytes(side.RUNNER)), side.RUNNER_SHA)


class Fixture:
    def __init__(self, tmp, stack, seed=1, device="0"):
        self.root = Path(tmp) / f"seed{seed}"
        self.source = Path(tmp) / side.SOURCE_ID
        self.parentroot = Path(tmp) / f"original{seed}"
        self.materialroot = Path(tmp) / "material"
        self.root0 = Path(tmp) / "seed0"
        self.model = Path(tmp) / "model"
        self.runner = Path(tmp) / "runner.py"
        self.runner.write_bytes(b"synthetic-runner-never-executed")
        runner_sha = side.sha(self.runner.read_bytes())
        stack.enter_context(patch.multiple(side, RUNNER=self.runner, RUNNER_SHA=runner_sha))
        for path in (self.root / "launch", self.root / "run", self.source, self.parentroot / "fit_teach",
            self.parentroot / "readouts/teach", self.materialroot, self.root0 / "run", self.model):
            path.mkdir(parents=True, exist_ok=True)
        adapter = str(self.parentroot / "fit_teach/adapter")
        parent_files = {"fixture.weights": "b"*64}
        original = dict(config=dict(seed=seed))
        fit = dict(adapter=adapter, adapter_files=parent_files)
        readout = dict(adapter=adapter, adapter_files=parent_files)
        self.parent_paths = [self.parentroot / "plan.json", self.parentroot / "fit_teach/verified.json",
            self.parentroot / "readouts/teach/plan.json"]
        parent_pins = [self.write(path, value) for path, value in zip(self.parent_paths, (original, fit, readout), strict=True)]
        self.parent_pins = parent_pins
        patched_pins = copy.deepcopy(side.PARENT_PINS)
        patched_pins[seed] = parent_pins
        stack.enter_context(patch.object(side, "PARENT_PINS", patched_pins))
        gate_path = Path(tmp) / "main-gate.json"
        evidence = {}
        gate_record = dict(schema="INTERLEAVED_SEED0_MAIN_GATE_V1", owner="Main", decision="ALLOW_SEEDS_1_2",
            raw_review_verdict="PASS", criteria=side.PROGRESSION, eligible_seeds=[1, 2])
        for key, path in (("seed0_plan", self.root0 / "plan.json"), ("seed0_terminal", self.root0 / "run/terminal.json"),
            ("seed0_validation", Path(tmp) / "validation.json"), ("raw_review", Path(tmp) / "review.md")):
            digest = self.write(path, dict(synthetic_evidence=key))
            gate_record[key] = dict(path=str(path), sha256=digest)
            evidence[str(path)] = digest
        gate_sha = self.write(gate_path, gate_record)
        evidence[str(gate_path)] = gate_sha
        gate = dict(path=str(gate_path), sha256=gate_sha, seed0_root=str(self.root0), evidence_hashes=evidence,
            owner="Main", decision="ALLOW_SEEDS_1_2", raw_review_verdict="PASS", criteria=side.PROGRESSION)
        self.plan = dict(schema=side.SCHEMA, root=str(self.root), source_root=str(self.source),
            source_commit=side.SOURCE_ID, source_hashes=dict(interleaved_replication=runner_sha), seed=seed, device=device,
            config=dict(seed=seed), parentroot=str(self.parentroot), parent_pin=parent_pins,
            parent=dict(parent=adapter, parent_files=parent_files, readout=readout,
                provenance=dict(zip(map(str, self.parent_paths), parent_pins, strict=True))),
            materialroot=str(self.materialroot), material_parentroot=str(self.root0), model=str(self.model), seed0_gate=gate,
            pair_seconds=1800, cleanup_seconds=140, external_custody_seconds=300, lease_margin_seconds=21600,
            arm_order=["SINGLE_VIEW", "FOUR_VIEW"], panels=dict(dev=48, exact=16, lexical=48), total_calls=224,
            calls_per_arm=112, confirmation_calls=0, reduce_only_after_both_captures=True, outcome_selective_skips=False,
            progression=side.PROGRESSION, python="/fixture/native/venv/bin/python", deadline=2800., real_lease_end=24700.)
        self.plan_sha = self.write(self.root / "plan.json", self.plan)
        self.reservation = dict(controller_pid=12345, started=1000., started_monotonic=100., effective_deadline=2800.,
            plan_sha256=self.plan_sha, device=device, seed=seed, real_lease_end=24700., external_custody_deadline=3100.,
            continuous_reservation=True)
        reservation_sha = self.write(self.root / "run/reservation.json", self.reservation)
        self.launch = dict(root=str(self.root), source=str(self.source), device=device, seed=seed,
            plan_sha256=self.plan_sha, script_sha256=runner_sha, parent_plan_sha256=parent_pins[0], seed0_gate_sha256=gate_sha,
            controller_bound_seconds=1800, external_collection_margin_seconds=300, generation_calls=224,
            pid=12345, pgid=12345, proc_start_ticks=123456789,
            command=[self.plan["python"], "-B", str(self.runner), "run", "--source-root", str(self.source),
                "--runroot", str(self.root), "--allow-gpu"], gpu=dict(gpu_uuid="GPU-synthetic-"+device),
            controller_started_unix=1000., effective_deadline=2800., reservation_sha256=reservation_sha)
        (self.root / "launch/gpu.xml").write_text(
            "<nvidia_smi_log><gpu><uuid>GPU-synthetic-"+device+"</uuid></gpu></nvidia_smi_log>")
        self.launch_sha = self.write(self.root / "launch/launch.json", self.launch)

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value, sort_keys=True, allow_nan=True))
        return side.sha(path.read_bytes())

    def repin(self):
        self.plan_sha = self.write(self.root / "plan.json", self.plan)
        self.reservation["plan_sha256"] = self.plan_sha
        self.launch["plan_sha256"] = self.plan_sha
        self.launch["reservation_sha256"] = self.write(self.root / "run/reservation.json", self.reservation)
        self.launch_sha = self.write(self.root / "launch/launch.json", self.launch)

    def load(self):
        return side.load_contract(self.root, self.plan_sha, self.launch_sha)

    def cli(self, out):
        return ["watcher", "--root", str(self.root), "--plan-sha256", self.plan_sha,
            "--launch-sha256", self.launch_sha, "--out", str(out)]


class ReplicationContractTests(unittest.TestCase):
    def reject_cli_without_effects(self, fixture, out):
        with patch("sys.argv", fixture.cli(out)), patch.dict(os.environ, {}, clear=True), \
            patch.object(side, "Proc") as proc, patch.object(side, "PidfdSignaler") as signaler, \
            patch.object(side, "write_new") as writer, patch("sys.stdout", new_callable=io.StringIO) as stdout:
            with self.assertRaises((ValueError, KeyError, TypeError, OSError, side.ET.ParseError)):
                side.main()
            self.assertFalse(out.exists())
            self.assertEqual(stdout.getvalue(), "")
            proc.assert_not_called()
            signaler.assert_not_called()
            writer.assert_not_called()

    def test_seed1_seed2_and_declared_devices(self):
        for seed, device in ((1, "0"), (2, "1"), (1, "7")):
            with self.subTest(seed=seed, device=device), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack, seed, device)
                bound = fixture.load()
                self.assertEqual((bound["seed"], bound["device"]), (seed, device))
                self.assertEqual(bound["gpu_uuid"], "GPU-synthetic-"+device)
                self.assertEqual(bound["term_at"], 2660.)
                self.assertEqual(bound["lease_cutoff"], 3100.)
                self.assertEqual(bound["external_custody_deadline"], 3100.)
                self.assertEqual(bound["parent_pin"], fixture.parent_pins)
                side.assert_immutable(bound)
                proc, clock = Proc(), Clock()
                proc.value["command"] = bound["command"]
                signaler = Signaler(clock, proc)
                out = Path(tmp) / "watch"
                result = side.monitor(bound, out, proc, signaler, clock, uid=1000)
                self.assertTrue(result["success"])
                self.assertEqual([item[0] for item in signaler.sent], [signal.SIGTERM, signal.SIGKILL])
                saved = json.loads((out / "watch.json").read_text())["contract"]
                self.assertEqual(saved, bound)

    def test_rehashed_launch_mutations_fail_without_output_or_signaler(self):
        mutations = [("pid", True), ("pid", 1), ("pgid", 6), ("proc_start_ticks", 0), ("seed", 0), ("seed", True),
            ("device", "3"), ("root", "/wrong"), ("source", "/wrong"), ("plan_sha256", "f"*64),
            ("script_sha256", "f"*64), ("parent_plan_sha256", "f"*64), ("seed0_gate_sha256", "f"*64),
            ("controller_bound_seconds", 1801), ("external_collection_margin_seconds", 299), ("generation_calls", 223),
            ("command", ["foreign"]), ("effective_deadline", 2801.), ("controller_started_unix", float("nan")),
            ("reservation_sha256", "f"*64), ("gpu", dict(gpu_uuid="GPU-foreign"))]
        for key, value in mutations:
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack)
                fixture.launch[key] = value
                fixture.launch_sha = fixture.write(fixture.root / "launch/launch.json", fixture.launch)
                self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_rehashed_plan_mutations_fail_without_output_or_signaler(self):
        mutations = [("seed", 0), ("seed", True), ("seed", 3), ("seed", "1"), ("schema", "ROOT0"),
            ("source_commit", "f"*40), ("source_root", "/tmp"), ("root", "/foreign"), ("device", 0),
            ("device", "0,1"), ("device", "00"), ("pair_seconds", 1801), ("cleanup_seconds", 141),
            ("external_custody_seconds", 0), ("lease_margin_seconds", 10), ("deadline", 2799.),
            ("real_lease_end", 24699.), ("real_lease_end", float("inf")), ("config", dict(seed=0)),
            ("arm_order", ["FOUR_VIEW", "SINGLE_VIEW"]), ("panels", dict(dev=47, exact=16, lexical=48)),
            ("total_calls", 223), ("calls_per_arm", 111), ("confirmation_calls", 1),
            ("reduce_only_after_both_captures", False), ("outcome_selective_skips", True), ("python", "python"),
            ("parent_pin", ["f"*64]*3), ("source_hashes", dict(interleaved_replication="f"*64))]
        for key, value in mutations:
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack)
                fixture.plan[key] = value
                fixture.repin()
                self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_rehashed_reservation_mutations_rejected(self):
        mutations = [("controller_pid", 1), ("seed", 0), ("device", "4"), ("started", 1001.),
            ("effective_deadline", 2801.), ("real_lease_end", 99999.), ("external_custody_deadline", 3099.),
            ("continuous_reservation", False), ("started_monotonic", float("nan")), ("started_monotonic", -1)]
        for key, value in mutations:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack, seed=2)
                fixture.reservation[key] = value
                fixture.repin()
                self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_expiry_is_not_preadjusted_cutoff(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.plan["real_lease_end"] = fixture.reservation["real_lease_end"] = 3100.
            fixture.repin()
            self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_wrong_pins_missing_fields_duplicate_and_missing_root(self):
        for kind in ("launch", "plan", "ticks", "duplicate", "root", "relative", "traversal"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack)
                if kind == "launch": fixture.launch_sha = "0"*64
                if kind == "plan": fixture.plan_sha = "0"*64
                if kind == "ticks":
                    del fixture.launch["proc_start_ticks"]
                    fixture.repin()
                if kind == "duplicate":
                    path = fixture.root / "launch/launch.json"
                    path.write_text('{"pid":12345,"pid":12345}')
                    fixture.launch_sha = side.sha(path.read_bytes())
                if kind == "root": fixture.root = Path(tmp) / "missing"
                if kind == "relative": fixture.root = Path("relative-root")
                if kind == "traversal": fixture.root = fixture.root / ".." / fixture.root.name
                self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_copied_seed0_or_other_seed_parent_and_readout_rejected(self):
        for seed in (1, 2):
            for kind in ("copiedbytes", "wrong_seed", "wrong_readout", "wrong_adapter", "wrong_provenance"):
                with self.subTest(seed=seed, kind=kind), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                    fixture = Fixture(tmp, stack, seed)
                    if kind == "copiedbytes": fixture.parent_paths[0].write_text('{"config":{"seed":0}}')
                    if kind == "wrong_seed": fixture.plan["parent_pin"] = side.PARENT_PINS[3-seed]
                    if kind == "wrong_readout": fixture.plan["parent"]["readout"]["adapter"] = "/seed0/adapter"
                    if kind == "wrong_adapter": fixture.plan["parent"]["parent"] = "/replay/adapter"
                    if kind == "wrong_provenance": fixture.plan["parent"]["provenance"][str(fixture.parent_paths[2])] = "f"*64
                    fixture.repin()
                    self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_invalid_gate_and_swapped_thresholds_rejected(self):
        for kind in ("status", "owner", "decision", "criteria", "hash", "evidence", "gatebytes", "root"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack)
                gate = fixture.plan["seed0_gate"]
                if kind == "status": gate["raw_review_verdict"] = "PENDING"
                if kind == "owner": gate["owner"] = "AUTO"
                if kind == "decision": gate["decision"] = "COMPLETE"
                if kind == "criteria": gate["criteria"] = dict(side.PROGRESSION, dev_habit_min=31, dev_act_min=30)
                if kind == "hash": gate["sha256"] = "f"*64
                if kind == "evidence": gate["evidence_hashes"] = {}
                if kind == "gatebytes": Path(gate["path"]).write_text('{}')
                if kind == "root": gate["seed0_root"] = str(fixture.parentroot)
                fixture.repin()
                self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_input_root_overlap_and_nonsibling_material_rejected(self):
        for key in ("materialroot", "parentroot", "model", "material_parentroot"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack)
                fixture.plan[key] = str(fixture.root)
                fixture.repin()
                self.reject_cli_without_effects(fixture, Path(tmp) / "watch")
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            fixture.plan["materialroot"] = str(Path(tmp))
            fixture.repin()
            self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_exact_native_venv_spelling_not_resolved(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            executable = Path(tmp) / "venv-python"
            executable.symlink_to(fixture.runner)
            fixture.plan["python"] = fixture.launch["command"][0] = str(executable)
            fixture.repin()
            self.assertEqual(fixture.load()["command"][0], str(executable))
            fixture.launch["command"][0] = str(executable.resolve())
            fixture.launch_sha = fixture.write(fixture.root / "launch/launch.json", fixture.launch)
            self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_extra_empty_argument_or_outer_wrapper_rejected(self):
        for kind in ("empty", "wrapper"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack)
                if kind == "empty": fixture.launch["command"].append("")
                else: fixture.launch["command"].insert(0, "timeout")
                fixture.launch_sha = fixture.write(fixture.root / "launch/launch.json", fixture.launch)
                self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_root_alias_and_custody_alias_rejected(self):
        for kind in ("root", "plan"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack)
                if kind == "root":
                    alias = Path(tmp) / "alias"
                    alias.symlink_to(fixture.root)
                    fixture.root = alias
                else:
                    path = fixture.root / "plan.json"
                    moved = Path(tmp) / "plan-copy.json"
                    path.rename(moved)
                    path.symlink_to(moved)
                self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_immutable_each_custody_file_blocks_initial_output(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            bound = fixture.load()
            for path in bound["immutable_hashes"]:
                with self.subTest(path=path):
                    target = Path(path)
                    before = target.read_bytes()
                    target.write_bytes(before + b" ")
                    proc, clock = Proc(), Clock(2801.)
                    signaler = Signaler(clock, proc)
                    out = Path(tmp) / "watch"
                    with self.assertRaisesRegex(ValueError, "immutable custody"):
                        side.monitor(bound, out, proc, signaler, clock, uid=1000)
                    self.assertFalse(out.exists())
                    self.assertEqual(signaler.sent, [])
                    self.assertEqual(signaler.opened, [])
                    target.write_bytes(before)

    def test_immutable_change_after_term_no_kill(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            bound = fixture.load()
            proc, clock = Proc(), Clock()
            proc.value["command"] = bound["command"]
            def mutate_once(obj):
                if obj.wall > 2670:
                    (fixture.root / "launch/gpu.xml").write_text("changed")
                    obj.hook = None
            clock.hook = mutate_once
            signaler = Signaler(clock, proc)
            result = side.monitor(bound, Path(tmp) / "watch", proc, signaler, clock, uid=1000)
            self.assertFalse(result["success"])
            self.assertEqual([item[0] for item in signaler.sent], [signal.SIGTERM])

    def test_output_overlap_precedes_creation_and_signal(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            bound = fixture.load()
            for protected in bound["protected_roots"]:
                with self.subTest(protected=protected):
                    out = Path(protected) / "watch"
                    proc, clock = Proc(), Clock()
                    signaler = Signaler(clock, proc)
                    with self.assertRaisesRegex(ValueError, "external watch"):
                        side.monitor(bound, out, proc, signaler, clock, uid=1000)
                    self.assertFalse(out.exists())
                    self.assertEqual(signaler.opened, [])

    def test_cli_environment_fails_without_output(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            out = Path(tmp) / "watch"
            with patch("sys.argv", fixture.cli(out)), patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}), \
                patch.object(side, "Proc") as proc, patch.object(side, "PidfdSignaler") as signaler:
                with self.assertRaisesRegex(ValueError, "unset CUDA"):
                    side.main()
                proc.assert_not_called()
                signaler.assert_not_called()
                self.assertFalse(out.exists())

    def test_cli_both_seeds_end_to_end_fake_process_and_pidfd(self):
        for seed, device in ((1, "1"), (2, "0")):
            with self.subTest(seed=seed), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack, seed, device)
                bound = fixture.load()
                proc, clock = Proc(), Clock(2801.)
                proc.value["command"] = bound["command"]
                signaler = Signaler(clock, proc)
                out = Path(tmp) / "watch"
                with patch("sys.argv", fixture.cli(out)), patch.dict(os.environ, {}, clear=True), \
                    patch.object(side, "Proc", return_value=proc), patch.object(side, "PidfdSignaler", return_value=signaler), \
                    patch.object(side.os, "getuid", return_value=1000), patch.object(side.time, "time", clock.time), \
                    patch.object(side.time, "monotonic", clock.monotonic), patch.object(side.time, "sleep", clock.sleep), \
                    patch("sys.stdout", new_callable=io.StringIO) as stdout:
                    with self.assertRaises(SystemExit) as ended:
                        side.main()
                    self.assertEqual(ended.exception.code, 0)
                    self.assertTrue(json.loads(stdout.getvalue())["success"])
                saved = json.loads((out / "watch.json").read_text())["contract"]
                self.assertEqual((saved["seed"], saved["device"]), (seed, device))
                self.assertEqual([event[0] for event in signaler.sent], [signal.SIGKILL])

    def test_gpu_xml_must_be_single_matching_device(self):
        for xml in ("<nvidia_smi_log/>", "invalid", "<nvidia_smi_log><gpu><uuid>GPU-synthetic-0</uuid></gpu>"
            "<gpu><uuid>GPU-foreign</uuid></gpu></nvidia_smi_log>"):
            with self.subTest(xml=xml), tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                fixture = Fixture(tmp, stack)
                (fixture.root / "launch/gpu.xml").write_text(xml)
                self.reject_cli_without_effects(fixture, Path(tmp) / "watch")

    def test_pidfd_exit_observed_without_signal(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            bound = fixture.load()
            proc, clock = Proc(), Clock(2801.)
            proc.value["command"] = bound["command"]
            signaler = Signaler(clock, proc)
            signaler.dead = True
            result = side.monitor(bound, Path(tmp) / "watch", proc, signaler, clock, uid=1000)
            self.assertEqual(result["status"], "PINNED_PIDFD_EXIT_OBSERVED")
            self.assertEqual(signaler.sent, [])

    def test_cli_missing_pidfd_fails_without_output(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            fixture = Fixture(tmp, stack)
            out = Path(tmp) / "watch"
            with patch("sys.argv", fixture.cli(out)), patch.dict(os.environ, {}, clear=True), \
                patch.object(side.os, "pidfd_open", None):
                with self.assertRaisesRegex(ValueError, "pidfd support"):
                    side.main()
                self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
