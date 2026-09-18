"""CPU checks of the metadata-only retention custody verifier."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("r179_retention_observer", HERE / "observe_retained.py")
OBSERVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OBSERVER)


def envelope(history, pending):
    state = dict(history=deepcopy(history), pending=pending, rows=[dict(fixture=True)], sleep_frontier=1)
    return dict(state=state, sha256=OBSERVER.digest(state))


class ObservationTests(unittest.TestCase):
    def setUp(self):
        history = dict(system_prompt="fixture", birth_prompt="fixture", operations=[], events=[dict(fixture=True)])
        history["state_sha256"] = OBSERVER.digest(history)
        self.history = history
        self.records = [
            dict(kind="CONTEXT_RETAINED", document=dict(history_sha256_before=history["state_sha256"],
                history_sha256_after=history["state_sha256"], visible_prompt_tokens=10, threshold_tokens=100,
                action="RETAIN_CONTEXT_ACROSS_SLEEP", cycle=1)),
            dict(kind="SLEEP_REQUEST", document=dict(resume_state=envelope(history, "sleep:fixture"))),
            dict(kind="SLEEP_COMPLETE", document=dict(status="COMPLETE", cycle=1, resume_state=envelope(history, None))),
            dict(kind="REQUEST", document=dict(history_sha256=OBSERVER.digest(history),
                resume_state=envelope(history, "request:fixture"))),
        ]
        for index, record in enumerate(self.records):
            record["index"] = index
            record["sha256"] = OBSERVER.digest(record)

    def test_complete_retention_chain(self):
        result = OBSERVER.retention_chain(self.records)
        self.assertEqual(result, (self.records[0], self.records[2], self.records[3]))

    def test_sleep_without_post_sleep_request_is_not_full_proof(self):
        self.assertIsNone(OBSERVER.retention_chain(self.records[:-1]))

    def test_changed_history_during_sleep_is_rejected(self):
        changed = deepcopy(self.history)
        changed["events"].append(dict(unexpected=True))
        self.records[2]["document"]["resume_state"] = envelope(changed, None)
        with self.assertRaisesRegex(ValueError, "full_raw_history_and_active_view_equal"):
            OBSERVER.retention_chain(self.records)

    def test_lost_history_in_post_sleep_request_is_rejected(self):
        changed = deepcopy(self.history)
        changed["events"] = []
        self.records[3]["document"]["resume_state"] = envelope(changed, "request:fixture")
        with self.assertRaisesRegex(ValueError, "all_prior_history_events"):
            OBSERVER.retention_chain(self.records)

    def test_compaction_between_retention_and_sleep_is_not_retention_proof(self):
        self.records.insert(2, dict(kind="COMPACTION", document={}))
        self.assertIsNone(OBSERVER.retention_chain(self.records))

    def test_retention_without_sleep_is_not_completed_sleep(self):
        result = OBSERVER.progress_metadata(self.records[:1])
        self.assertEqual(result["status"], "CONTEXT_RETAINED_WAITING_SLEEP_REQUEST")
        self.assertNotIn("sleep_complete", result["records"])

    def test_sleep_request_is_not_completed_sleep(self):
        result = OBSERVER.progress_metadata(self.records[:2])
        self.assertEqual(result["status"], "CONTEXT_RETAINED_SLEEP_IN_PROGRESS")
        self.assertNotIn("sleep_complete", result["records"])

    def test_completed_sleep_is_separate_from_prompt_custody(self):
        result = OBSERVER.progress_metadata(self.records[:3])
        self.assertEqual(result["status"], "COMPLETED_RETAINED_SLEEP_WAITING_POST_SLEEP_REQUEST")
        self.assertIn("sleep_complete", result["records"])
        self.assertIsNone(OBSERVER.retention_chain(self.records[:3]))

    def test_no_train_text_in_progress_metadata(self):
        self.records[0]["document"]["messages"] = "never export this"
        result = OBSERVER.progress_metadata(self.records)
        self.assertNotIn("never export this", repr(result))

    def test_spoofed_text_in_hash_field_rejected(self):
        self.records[0]["document"]["retelling_source_sha256"] = "not metadata"
        with self.assertRaisesRegex(ValueError, "metadata_only_retention_fields"):
            OBSERVER.progress_metadata(self.records)

    def test_compaction_invalidates_pending_retention_metadata(self):
        self.records.insert(2, dict(kind="COMPACTION", document={}))
        result = OBSERVER.progress_metadata(self.records)
        self.assertEqual(result["status"], "WAITING_FIRST_CONTEXT_RETAINED")
        self.assertEqual(result["records"], {})


if __name__ == "__main__":
    unittest.main()
