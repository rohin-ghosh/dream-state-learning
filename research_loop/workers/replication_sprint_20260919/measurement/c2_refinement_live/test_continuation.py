import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("c2_continuation", Path(__file__).with_name("continuation.py"))
MONITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MONITOR)


class Clock:
    def __init__(self):
        self.value = 10_000.0
        self.sleeps = []

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.value += seconds


class Backend:
    def __init__(self, review, clock, counts=(6,), failure=None):
        self.review = review
        self.clock = clock
        self.counts = iter(counts)
        self.count = 1
        self.calls = []
        self.failure = failure
        self.last = review["cursor"]

    def binding(self):
        return {"attempts": [{"attempt": "parent_000000", "files": {"RESULT.json": {"sha256": "result"}},
                             "result": {"status": "PUBLISHED", "inbox_publication": {"id": "first", "sha256": "publication"},
                                        "response": {"message": "quote source"}}}]}

    def capture(self, after, maximum):
        self.calls.append((after, maximum))
        if self.failure == "capture":
            raise ValueError("source_identity_changed")
        row = {"index": after + 1, "kind": "UPDATE", "journal_id": "journal", "sha256": str(after + 1), "previous_sha256": self.last["sha256"]}
        self.last = row
        self.count = next(self.counts, self.count)
        return {"identity": self.review["identity"], "after": after, "evidence": {
            "journal_id": "journal", "continuity": [row], "records": [], "through": row, "head": row,
            "remote_writes": 0, "signals": 0, "model_calls": 0, "readout_or_private_score_files_read": 0}}

    def merged_evidence(self, paths):
        return {"paths": [str(path) for path in paths]}

    def select(self, evidence, publication, turns):
        if self.failure == "select":
            raise ValueError("unjoined_ACT_receipt_requires_unknown_slot_review_not_silent_exclusion")
        return {"opportunities": [{"opportunity": index + 1} for index in range(self.count)], "status": "PARTIAL" if self.count < 6 else "SIX_AVAILABLE"}


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="continuation_test_", dir=MONITOR.HERE)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "run"
        self.clock = Clock()
        self.review = {"cursor": {"index": 15917, "kind": "UPDATE", "sha256": "cursor", "journal_id": "journal", "previous_sha256": "previous"},
                       "identity": {"pid": 1139778, "start_ticks": "30025875"}, "captures": [], "pins": [], "selection": {"baseline": True}}

    def run_monitor(self, backend, guard=lambda: None):
        return MONITOR.run_loop(self.directory, self.review, "review", backend, self.clock.now, self.clock.now, self.clock.sleep, guard)

    def test_stop_at_six_without_semantic_grades(self):
        backend = Backend(self.review, self.clock)
        result = self.run_monitor(backend)
        self.assertEqual(result["status"], "SIX_HASH_LINKED_ACTS_MANUAL_REVIEW_REQUIRED")
        self.assertEqual(result["eligible_ACT_count"], 6)
        self.assertNotIn("artifact_success", result)
        self.assertEqual(len(backend.calls), 1)
        self.assertLessEqual(result["charged_bytes"], MONITOR.MAX_BYTES)
        pointer = json.loads((self.directory / "LATEST.json").read_text())
        MONITOR.verify_reference(pointer["snapshot"])

    def test_time_ceiling_and_90_second_cadence(self):
        backend = Backend(self.review, self.clock, counts=(1,))
        with patch.object(MONITOR, "MAX_SECONDS", 600):
            result = self.run_monitor(backend)
        self.assertEqual(result["status"], "PARTIAL_TIME_LIMIT")
        self.assertEqual(result["eligible_ACT_count"], 1)
        self.assertLessEqual(self.clock.value - 10_000, 600)
        self.assertTrue(all(0 <= delay <= 90 for delay in self.clock.sleeps))
        self.assertEqual(backend.calls, [(15917, 12), (15918, 12), (15919, 12), (15920, 12)])

    def test_byte_reservation_prevents_remote_read(self):
        backend = Backend(self.review, self.clock)
        with patch.object(MONITOR, "MAX_BYTES", MONITOR.RESERVATION):
            result = self.run_monitor(backend)
        self.assertEqual(result["status"], "PARTIAL_BYTE_LIMIT")
        self.assertEqual(backend.calls, [])

    def test_cumulative_byte_ceiling_stops_before_second_export(self):
        backend = Backend(self.review, self.clock, counts=(1,))
        ceiling = MONITOR.RESERVATION + MONITOR.OVERHEAD + 5000
        with patch.object(MONITOR, "MAX_BYTES", ceiling):
            result = self.run_monitor(backend)
        self.assertEqual(result["status"], "PARTIAL_BYTE_LIMIT")
        self.assertEqual(len(backend.calls), 1)
        self.assertLessEqual(result["charged_bytes"], ceiling)
        self.assertEqual(result["eligible_ACT_count"], 1)

    def test_failed_capture_is_terminal_unknown_slot(self):
        backend = Backend(self.review, self.clock, failure="capture")
        result = self.run_monitor(backend)
        self.assertEqual(result["status"], "PARTIAL_FAILED_SLOT")
        self.assertEqual(result["failed_slot"]["outcome"], "UNKNOWN_NOT_REPLACED")
        self.assertEqual(result["eligible_ACT_count"], 1)
        self.assertTrue((self.directory / "INTENT_0001.json").exists())
        self.assertTrue((self.directory / "BINDING_0001.json").exists())
        self.assertEqual(len(backend.calls), 1)

    def test_failed_selection_preserves_capture_and_no_later_substitute(self):
        backend = Backend(self.review, self.clock, failure="select")
        result = self.run_monitor(backend)
        self.assertEqual(result["status"], "PARTIAL_FAILED_SLOT")
        self.assertTrue((self.directory / "CAPTURE_0001.json").exists())
        self.assertEqual(result["cursor"]["index"], 15917)
        self.assertEqual(result["eligible_ACT_count"], 1)

    def test_cursor_gap_and_identity_change_fail(self):
        backend = Backend(self.review, self.clock)
        capture = backend.capture(15917, 12)
        wrong = copy.deepcopy(capture)
        wrong["identity"]["pid"] = 999
        with self.assertRaisesRegex(ValueError, "source_identity_changed"):
            MONITOR.advance(self.review["cursor"], wrong, self.review["identity"], "journal")
        capture["evidence"]["continuity"][0]["index"] += 1
        with self.assertRaisesRegex(ValueError, "contiguous_cursor"):
            MONITOR.advance(self.review["cursor"], capture, self.review["identity"], "journal")

    def test_empty_poll_does_not_advance_cursor(self):
        capture = {"identity": self.review["identity"], "after": 15917, "evidence": {
            "journal_id": "journal", "continuity": [], "records": [], "through": None, "head": self.review["cursor"],
            "remote_writes": 0, "signals": 0, "model_calls": 0, "readout_or_private_score_files_read": 0}}
        self.assertEqual(MONITOR.advance(self.review["cursor"], capture, self.review["identity"], "journal"), self.review["cursor"])

    def test_no_duplicate_monitor_lock(self):
        lock = Path(self.temporary.name) / "lock"
        with MONITOR.exclusive(lock):
            with self.assertRaises(BlockingIOError):
                with MONITOR.exclusive(lock):
                    self.fail("second monitor entered")

    def test_active_direct_collector_prevents_remote_call(self):
        backend = Backend(self.review, self.clock)
        def reject():
            raise ValueError("direct_collector_already_active")
        result = self.run_monitor(backend, reject)
        self.assertEqual(result["status"], "PARTIAL_FAILED_SLOT")
        self.assertEqual(backend.calls, [])

    def test_snapshots_never_overwrite(self):
        self.directory.mkdir()
        MONITOR.snapshot(self.directory, "receipt.json", {"first": True})
        with self.assertRaises(FileExistsError):
            MONITOR.snapshot(self.directory, "receipt.json", {"first": False})
        self.assertEqual(json.loads((self.directory / "receipt.json").read_text()), {"first": True})

    def test_unfinished_slot_stops_without_recollecting(self):
        self.directory.mkdir()
        state = MONITOR.initial(self.review, "review", self.clock.now(), self.clock.now())
        MONITOR.snapshot(self.directory, "START.json", state)
        MONITOR.snapshot(self.directory, "INTENT_0001.json", {"cursor": state["cursor"]})
        backend = Backend(self.review, self.clock)
        result = self.run_monitor(backend)
        self.assertEqual(result["status"], "PARTIAL_INCOMPLETE_RESUME")
        self.assertEqual(backend.calls, [])
        self.assertTrue((self.directory / "INTENT_0001.json").exists())

    def test_terminal_restart_does_not_reset_caps(self):
        backend = Backend(self.review, self.clock)
        first = self.run_monitor(backend)
        self.clock.value += 10_000
        second = self.run_monitor(backend)
        self.assertEqual(first, second)
        self.assertEqual(len(backend.calls), 1)

    def test_resume_all_captures_and_same_deadlines(self):
        backend = Backend(self.review, self.clock, counts=(1, 6))
        def interrupt(seconds):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            MONITOR.run_loop(self.directory, self.review, "review", backend, self.clock.now, self.clock.now, interrupt, lambda: None)
        state = json.loads((self.directory / "STATE_0001.json").read_text())
        result = self.run_monitor(backend)
        self.assertEqual(backend.calls, [(15917, 12), (15918, 12)])
        self.assertEqual(result["deadline_unix"], state["deadline_unix"])
        self.assertEqual(result["deadline_monotonic"], state["deadline_monotonic"])
        self.assertEqual(len(result["captures"]), 2)
        self.assertEqual(self.clock.sleeps[0], 90)

    def test_durable_state_survives_interrupted_latest_pointer(self):
        backend = Backend(self.review, self.clock, counts=(1, 6))
        with patch.object(MONITOR, "point", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_monitor(backend)
        self.assertTrue((self.directory / "STATE_0001.json").exists())
        self.assertFalse((self.directory / "LATEST.json").exists())
        result = self.run_monitor(backend)
        self.assertEqual(result["eligible_ACT_count"], 6)
        self.assertEqual(backend.calls, [(15917, 12), (15918, 12)])

    def test_modified_receipt_on_resume_fails_closed(self):
        backend = Backend(self.review, self.clock, counts=(1, 6))
        def interrupt(seconds):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            MONITOR.run_loop(self.directory, self.review, "review", backend, self.clock.now, self.clock.now, interrupt, lambda: None)
        with (self.directory / "CAPTURE_0001.json").open("ab") as stream:
            stream.write(b" ")
        result = self.run_monitor(backend)
        self.assertEqual(result["status"], "PARTIAL_INCOMPLETE_RESUME")
        self.assertEqual(len(backend.calls), 1)

    def test_clock_rollback_cannot_extend_monotonic_budget(self):
        backend = Backend(self.review, self.clock, counts=(1,))
        def wall():
            return self.clock.value if not self.clock.sleeps else self.clock.value - 5000
        with patch.object(MONITOR, "MAX_SECONDS", 600):
            result = MONITOR.run_loop(self.directory, self.review, "review", backend, wall, self.clock.now, self.clock.sleep, lambda: None)
        self.assertEqual(result["status"], "PARTIAL_TIME_LIMIT")
        self.assertLessEqual(self.clock.value - 10_000, 600)

    def test_slow_binding_cannot_start_read_near_deadline(self):
        backend = Backend(self.review, self.clock)
        original = backend.binding
        def slow_binding():
            self.clock.value += 400
            return original()
        backend.binding = slow_binding
        with patch.object(MONITOR, "MAX_SECONDS", 600):
            result = self.run_monitor(backend)
        self.assertEqual(result["status"], "PARTIAL_FAILED_SLOT")
        self.assertEqual(result["error"]["message"], "time_budget_before_capture")
        self.assertEqual(backend.calls, [])

    def test_Main_must_approve_exact_review_and_monitor(self):
        path = Path(self.temporary.name) / "approval.json"
        value = {"status": "APPROVED_TO_RUN", "approved_by": "Main", "scope": MONITOR.SCOPE,
                 "review_sha256": "review", "monitor_sha256": "monitor"}
        proof = MONITOR.snapshot(path.parent, path.name, value)
        MONITOR.approve(path, proof["sha256"], "review", "monitor")
        with self.assertRaisesRegex(ValueError, "exact_reviewed_monitor"):
            MONITOR.approve(path, proof["sha256"], "review", "changed-monitor")

    def test_existing_helpers_still_match_frozen_receipt(self):
        frozen = json.loads((MONITOR.HERE / "FIXED_CODE_RECEIPT.json").read_text())
        for name, expected in frozen["sha256"].items():
            self.assertEqual(MONITOR.sha(MONITOR.read(MONITOR.HERE / name)), expected, name)


if __name__ == "__main__":
    unittest.main()
