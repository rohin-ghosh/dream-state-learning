import copy
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import queue_launcher as subject


BINDINGS = json.loads((subject.HERE / "SOURCE_BINDINGS.json").read_bytes())
DRIVER = subject.driver_module(BINDINGS)
READER = DRIVER.load_reader(BINDINGS["reader"])


class AdmissionContractTests(unittest.TestCase):
    def test_surviving_and_frozen_sources_are_byte_identical(self):
        self.assertEqual(subject.checked(BINDINGS["driver"]).read_bytes(), subject.checked(BINDINGS["provenance"][0]).read_bytes())
        self.assertEqual(subject.checked(BINDINGS["reader"]).read_bytes(), subject.checked(BINDINGS["provenance"][1]).read_bytes())

    def test_sixteen_unique_journals_and_source_pins(self):
        targets = subject.verify_bindings(BINDINGS)
        self.assertEqual(len({target["journal_id"] for target in targets}), 16)
        self.assertEqual(len(BINDINGS["wrappers_sha256"]), 5)

    def test_all_existing_source_deadlines_and_admission_margins(self):
        for wrapper, (alias, day) in DRIVER.SOURCE_DAYS.items():
            with self.subTest(wrapper=wrapper):
                target = dict(label="synthetic", wrapper=wrapper)
                decision = DRIVER.admission(target, 0)
                expected = datetime.datetime(2026, 9, day, 18, tzinfo=datetime.timezone.utc).timestamp()
                self.assertEqual(decision["source_host_alias"], alias)
                self.assertEqual(decision["effective_cutoff_unix"], min(expected, subject.END))
                for offset in (-35, -1, 0, 1):
                    with patch.object(subprocess, "run") as execute:
                        with self.assertRaises(DRIVER.SourceLeaseClosed):
                            DRIVER.guarded_page(target, {}, "/unused", "unused", {},
                                now=lambda: decision["effective_cutoff_unix"] + offset, runner=execute)
                    execute.assert_not_called()

    def test_read_uses_64_record_pages_and_30_second_timeout(self):
        target = dict(label="synthetic", wrapper="ovx_ssh.sh", root="/unchanged", journal_id="same")
        cursor = dict(last_index=11, last_sha256="bound")
        with patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout='{"entries": []}')) as execute:
            DRIVER.guarded_page(target, cursor, "/repo", "import json\n", {}, now=lambda: 1, runner=execute)
        command = execute.call_args.args[0]
        options = execute.call_args.kwargs
        self.assertEqual(command, ["bash", "/repo/gpu/ovx_ssh.sh", "python3 -B -"])
        self.assertEqual(options["timeout"], 30)
        self.assertIn("limit=64", options["input"])
        self.assertIn("signal.setitimer(signal.ITIMER_REAL, _remaining)", options["input"])
        self.assertIn(repr(cursor), options["input"])

    def test_admission_rechecks_time_at_dispatch(self):
        target = dict(label="synthetic", wrapper="ovx_ssh.sh")
        cutoff = DRIVER.admission(target, 0)["effective_cutoff_unix"]
        moments = iter([cutoff - 36, cutoff - 34])
        with patch.object(subprocess, "run") as execute:
            with self.assertRaises(DRIVER.SourceLeaseClosed):
                DRIVER.guarded_page(target, {}, "/unused", "", {}, now=lambda: next(moments), runner=execute)
        execute.assert_not_called()

    def test_expired_receiver_exits_without_reading(self):
        code = DRIVER.remote_program("raise RuntimeError('reader_must_not_execute')", {}, {}, dict(effective_cutoff_unix=1))
        result = subprocess.run(["/usr/bin/python3", "-B", "-"], input=code, text=True, capture_output=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source_lease_closed_before_read", result.stderr)
        self.assertNotIn("reader_must_not_execute", result.stderr)

    def test_closed_source_does_not_change_queued_ages(self):
        initial = dict(entries={"immutable": dict(life="synthetic", record_index=8, sleep=2)},
                       cursors={"synthetic": dict(last_index=8, last_sha256="original")})
        target = dict(label="synthetic", wrapper="ovx_ssh.sh")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            READER.put(output / "private/STATE.json", initial)
            cutoff = DRIVER.admission(target, 0)["effective_cutoff_unix"]
            with patch.object(subprocess, "run") as execute:
                status = DRIVER.lease_tick(READER, dict(deadline_unix=subject.END, targets=[target]),
                    output, "/unused", "unused", now=lambda: cutoff, runner=execute)
            execute.assert_not_called()
            self.assertEqual(json.loads((output / "private/STATE.json").read_bytes()), initial)
            self.assertEqual(status["rows"][0]["status"], "SOURCE_LEASE_CLOSED_NO_REMOTE_READ")

    def test_unknown_wrapper_fails_closed(self):
        with self.assertRaises(KeyError):
            DRIVER.admission(dict(wrapper="unknown.sh"), 0)


class StartupPreservationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bindings = copy.deepcopy(BINDINGS)
        self.bindings["ledgers"] = []
        self.initial = {}
        for name, count, roots in (("enrollment", 1197, 15), ("extra_enrollment", 45, 1)):
            output = self.root / "canonical" / name
            output.joinpath("private").mkdir(parents=True)
            output.joinpath("ENROLL.lock").touch()
            state = dict(entries={f"{name}-{index}": dict(sleep=index, evaluation="PENDING", captured=False,
                        evaluated=False, dispatched=False) for index in range(count)},
                        cursors={f"{name}-{index}": dict(last_index=100, last_sha256="same") for index in range(roots)})
            payload = json.dumps(state).encode()
            output.joinpath("private/STATE.json").write_bytes(payload)
            registration = output / "registration.json"
            registration.write_text('{"targets": []}')
            self.bindings["ledgers"].append(dict(name=name, output=str(output), initial_state_sha256=hashlib.sha256(payload).hexdigest(),
                registration=dict(path=str(registration), sha256=subject.checksum(registration))))
            self.initial[name] = payload
        patcher = patch.object(subject, "HERE", self.root / "recovery")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(subject, "verify_bindings", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)

    def state_path(self, index=0):
        return Path(self.bindings["ledgers"][index]["output"]) / "private/STATE.json"

    def test_first_prepare_snapshots_1242_without_writing_ledgers(self):
        run = subject.prepare_run(self.bindings)
        config = json.loads((run / "CONFIG.private.json").read_bytes())
        baseline = json.loads((subject.HERE / "BASELINE.json").read_bytes())
        self.assertEqual(baseline["total_references"], 1242)
        self.assertEqual(sum(row["roots"] for row in baseline["counts"]), 16)
        for ledger in config["ledgers"]:
            self.assertEqual(Path(ledger["state_snapshot"]["path"]).read_bytes(), self.initial[ledger["name"]])
            self.assertEqual(Path(ledger["output"]).joinpath("private/STATE.json").read_bytes(), self.initial[ledger["name"]])
        self.assertEqual(config["deadline_unix"], subject.END)

    def test_restart_uses_current_hash_not_obsolete_initial_hash(self):
        first = subject.prepare_run(self.bindings)
        current = json.loads(self.state_path().read_bytes())
        current["entries"]["new-age"] = dict(sleep=1198, evaluation="PENDING", captured=False, evaluated=False, dispatched=False)
        current["cursors"]["enrollment-0"]["last_index"] += 1
        self.state_path().write_text(json.dumps(current))
        second = subject.prepare_run(self.bindings)
        old_config = json.loads((first / "CONFIG.private.json").read_bytes())
        new_config = json.loads((second / "CONFIG.private.json").read_bytes())
        self.assertNotEqual(old_config["ledgers"][0]["state_sha256"], new_config["ledgers"][0]["state_sha256"])
        self.assertEqual(new_config["ledgers"][0]["state_sha256"], subject.checksum(self.state_path()))

    def test_historical_age_or_pending_flags_cannot_be_changed(self):
        subject.prepare_run(self.bindings)
        current = json.loads(self.state_path().read_bytes())
        current["entries"]["enrollment-0"]["evaluated"] = True
        self.state_path().write_text(json.dumps(current))
        with self.assertRaisesRegex(ValueError, "historical_enrollment_changed"):
            subject.prepare_run(self.bindings)

    def test_cursor_cannot_be_reset(self):
        subject.prepare_run(self.bindings)
        current = json.loads(self.state_path().read_bytes())
        current["cursors"]["enrollment-0"]["last_index"] = -1
        self.state_path().write_text(json.dumps(current))
        with self.assertRaisesRegex(ValueError, "enrollment_cursor_regressed"):
            subject.prepare_run(self.bindings)

    def test_either_busy_original_lock_prevents_preparation(self):
        for ledger in self.bindings["ledgers"]:
            with self.subTest(ledger=ledger["name"]), Path(ledger["output"]).joinpath("ENROLL.lock").open("r") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):
                    subject.prepare_run(self.bindings)
            self.assertFalse((subject.HERE / "BASELINE.json").exists())

    def test_driver_rechecks_snapshot_hash_after_lock_handoff(self):
        run = subject.prepare_run(self.bindings)
        current = json.loads(self.state_path().read_bytes())
        current["cursors"]["enrollment-0"]["last_index"] += 1
        self.state_path().write_text(json.dumps(current))
        original_open = Path.open
        descriptors = []

        def track_lock(path, *arguments, **keywords):
            descriptor = original_open(path, *arguments, **keywords)
            if path.name == "ENROLL.lock":
                descriptors.append(descriptor)
            return descriptor

        try:
            with patch("sys.argv", ["driver.py", "--config", str(run / "CONFIG.private.json")]), patch.object(DRIVER, "lease_tick") as tick, patch.object(Path, "open", track_lock):
                with self.assertRaisesRegex(ValueError, "exact_handoff_enrollment_state_required"):
                    DRIVER.main()
        finally:
            for descriptor in descriptors:
                descriptor.close()
        tick.assert_not_called()

    def test_initial_changed_state_requires_review_not_reset(self):
        self.state_path().write_text('{"entries": {}, "cursors": {}}')
        with self.assertRaisesRegex(ValueError, "initial_preserved_state_changed"):
            subject.prepare_run(self.bindings)


if __name__ == "__main__":
    unittest.main()
