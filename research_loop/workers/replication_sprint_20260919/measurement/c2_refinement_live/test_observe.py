import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location("c2_sidecar", Path(__file__).with_name("observe.py"))
OBSERVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OBSERVE)


def record(index, kind, **values):
    return dict(index=index, kind=kind, sha256=str(index).zfill(64), time_unix=index, **values)


def frame(start, stage="ACT", text="I will do this", visible=True):
    events = [{"actor": "parent", "event_id": "parent:inbox:first", "source_sha256": "publication", "text": "quote and check", "phase": "advice"}] if visible else []
    return [record(start, "REQUEST", request_digest=f"request-{start}", masked=True, external=events, cycle=1),
            record(start + 1, "RESPONSE", request_digest=f"request-{start}", document_sha256=f"response-{start}", text=text),
            record(start + 2, "COMMITTED", source_sha256=f"response-{start}"),
            record(start + 3, "R184_STAGE", source_sha256=f"response-{start}", stage=stage)]


class ObservationTests(unittest.TestCase):
    publication = {"id": "first", "sha256": "publication"}

    def evidence(self, records):
        inbox = record(10, "INBOX", event_id="parent:inbox:first", source_sha256="publication")
        return {"records": [inbox] + records}

    def test_exact_api_text_is_not_json_escaped_text(self):
        text = 'Literal "quote"\nsecond line \\ value'
        self.assertTrue(OBSERVE.contains_exact({"instructions": text}, text))
        self.assertFalse(OBSERVE.contains_exact({"instructions": text[:-1]}, text))

    def test_started_and_publication_are_not_delivery(self):
        result = OBSERVE.select({"records": frame(20)}, self.publication)
        self.assertIsNone(result["first_inbox"])
        self.assertEqual(result["opportunities"], [])

    def test_source_hash_must_match_as_well_as_id(self):
        evidence = self.evidence(frame(20))
        evidence["records"][0]["source_sha256"] = "wrong"
        self.assertIsNone(OBSERVE.select(evidence, self.publication)["first_inbox"])

    def test_duplicate_inbox_is_rejected(self):
        evidence = self.evidence([])
        evidence["records"].append(dict(evidence["records"][0]))
        with self.assertRaisesRegex(ValueError, "unique_first_policy_inbox"):
            OBSERVE.select(evidence, self.publication)

    def test_first_six_kept_including_ignored_and_invisible(self):
        records = []
        for position in range(8):
            records.extend(frame(20 + 10 * position, visible=position != 1))
        result = OBSERVE.select(self.evidence(records), self.publication)
        self.assertEqual([row["request"]["index"] for row in result["opportunities"]], [20, 30, 40, 50, 60, 70])
        self.assertFalse(result["opportunities"][1]["first_policy_exact_visible"])
        self.assertEqual(result["status"], "SIX_AVAILABLE")

    def test_after_request_inbox_is_later_opportunity(self):
        result = OBSERVE.select(self.evidence(frame(9) + frame(20)), self.publication)
        self.assertEqual(len(result["opportunities"]), 1)
        self.assertEqual(result["excluded_pre_INBOX_requests"][0]["request"]["index"], 9)

    def test_think_predating_instruction_is_not_failed_recognition(self):
        result = OBSERVE.select(self.evidence(frame(5, "THINK") + frame(20)), self.publication)
        self.assertTrue(result["opportunities"][0]["previous_think"]["first_policy_arrived_after_think_request"])

    def test_missing_commit_is_not_silently_dropped(self):
        records = frame(20)
        records.pop(2)
        with self.assertRaisesRegex(ValueError, "unknown_slot_review"):
            OBSERVE.select(self.evidence(records), self.publication)

    def test_partial_remains_partial(self):
        result = OBSERVE.select(self.evidence(frame(20)), self.publication)
        self.assertEqual(len(result["opportunities"]), 1)
        self.assertEqual(result["status"], "PARTIAL")

    def test_parent_turns_grouped_without_duplicate_acts(self):
        evidence = self.evidence(frame(20) + frame(30))
        evidence["records"].extend([record(12, "INBOX", event_id="parent:inbox:second", source_sha256="second-sha"),
                                    record(21, "INBOX", event_id="parent:inbox:third", source_sha256="third-sha")])
        turns = [{"publication": self.publication}, {"publication": {"id": "second", "sha256": "second-sha"}},
                 {"publication": {"id": "third", "sha256": "third-sha"}}]
        result = OBSERVE.select(evidence, self.publication, turns)
        self.assertEqual([[turn["publication"]["id"] for turn in row["grouped_parent_turns"]] for row in result["opportunities"]],
                         [["first", "second"], ["third"]])

    def test_published_without_inbox_stays_unknown(self):
        turns = [{"publication": self.publication}, {"publication": {"id": "second", "sha256": "second-sha"}}]
        result = OBSERVE.select(self.evidence(frame(20)), self.publication, turns)
        self.assertEqual(result["publications_without_INBOX_in_capture"][0]["publication"]["id"], "second")
        self.assertEqual(len(result["opportunities"][0]["grouped_parent_turns"]), 1)

    def test_bad_source_order_fails(self):
        records = frame(20)
        records[2]["index"] = 19
        with self.assertRaisesRegex(ValueError, "source_order"):
            OBSERVE.select(self.evidence(records), self.publication)

    def test_output_path_escape_rejected_without_writing(self):
        with self.assertRaisesRegex(ValueError, "sidecar_filename_only"):
            OBSERVE.save("../not-allowed.json", {})


if __name__ == "__main__":
    unittest.main()
