import copy
import hashlib
import json
import re
import unittest
from collections import Counter

from build_evidence import FOLDER, FINAL_PATTERN, PACKET_SHA256, ROOT, STATUSES, arithmetic, digest


def validate(audit, packet):
    assert audit["packet_sha256"] == PACKET_SHA256
    assert len(packet) == len(audit["rows"]) == 190
    assert [row["packet_index"] for row in audit["rows"]] == list(range(190))
    assert len({row["target_sha256"] for row in audit["rows"]}) == 190
    assert audit["author_labels_consulted"] is False
    assert audit["original_reports_or_reviews_consulted"] is False
    assert audit["model_calls"] == audit["gpu_allocations"] == audit["native_cells"] == 0
    targets = {row["target"] for row in packet}
    axes = ("semantics", "neutral_prefix_support", "mathematical_outcome", "mathematical_narrative", "token_contract", "final_line_format")
    for row, source in zip(audit["rows"], packet):
        assert row["target_sha256"] == source["row_id"] == hashlib.sha256(source["target"].encode()).hexdigest()
        assert row["task_id"] == source["task_id"]
        assert row["full_target_read"] is True
        for axis in axes:
            assert row[axis]["status"] in STATUSES
        for axis in ("semantics", "neutral_prefix_support"):
            assert row[axis]["quote"] and row[axis]["quote"] in source["target"]
            assert row[axis]["reason"]
        assert row["neutral_prefix_support"]["question_quote"] == source["student_prefix"][0]["content"]
        if len(source["student_prefix"]) == 3:
            assert source["student_prefix"][1]["content"] in targets
            assert row["neutral_prefix_support"]["prior_solution_is_already_read_packet_target"] is True
        numeric = row["mathematical_outcome"]
        assert numeric["preserved_gold"] == source["gold"]
        assert numeric["gold_modified_or_rescored"] is False
        assert numeric["answer_quote"] in source["target"]
        assert arithmetic(numeric["independent_expression"]) == arithmetic(numeric["independent_value"])
        count = source["generated_tokens"]
        assert row["token_contract"]["generated_tokens"] == count
        assert row["token_contract"]["status"] == ("PASS" if 150 <= count <= 400 else "FAIL")
        assert row["final_line_format"]["status"] == ("PASS" if re.search(FINAL_PATTERN, source["target"]) else "FAIL")
    for axis in axes:
        assert dict(Counter(row[axis]["status"] for row in audit["rows"])) == audit["summary"]["statuses"][axis]
    assert sum(all(row[axis]["status"] == "PASS" for axis in axes) for row in audit["rows"]) == audit["summary"]["all_separate_contract_axes_pass"]
    assert len({row["task_id"] for row in audit["rows"]}) == audit["summary"]["unique_tasks"] == 64


class EvidenceStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads((FOLDER / "BLIND_PACKET.json").read_text())
        cls.audit = json.loads((FOLDER / "ASSESSMENT.json").read_text())

    def test_packet_digest(self):
        self.assertEqual(digest(FOLDER / "BLIND_PACKET.json"), PACKET_SHA256)

    def test_complete_evidence_structure(self):
        validate(self.audit, self.packet)

    def test_summary_matches_assessment(self):
        self.assertEqual(json.loads((FOLDER / "SUMMARY.json").read_text()), self.audit["summary"])

    def test_missing_target_rejected(self):
        altered = copy.deepcopy(self.audit)
        altered["rows"].pop()
        with self.assertRaises(AssertionError):
            validate(altered, self.packet)

    def test_duplicate_target_rejected(self):
        altered = copy.deepcopy(self.audit)
        altered["rows"][1]["target_sha256"] = altered["rows"][0]["target_sha256"]
        with self.assertRaises(AssertionError):
            validate(altered, self.packet)

    def test_nonverbatim_quote_rejected(self):
        altered = copy.deepcopy(self.audit)
        altered["rows"][0]["semantics"]["quote"] = "NOT PRESENT IN THIS TARGET"
        with self.assertRaises(AssertionError):
            validate(altered, self.packet)

    def test_changed_gold_rejected(self):
        altered = copy.deepcopy(self.audit)
        altered["rows"][120]["mathematical_outcome"]["preserved_gold"] = "12"
        with self.assertRaises(AssertionError):
            validate(altered, self.packet)

    def test_invalid_status_rejected(self):
        altered = copy.deepcopy(self.audit)
        altered["rows"][0]["neutral_prefix_support"]["status"] = "APPROVED"
        with self.assertRaises(AssertionError):
            validate(altered, self.packet)

    def test_token_boundary_is_separate(self):
        self.assertEqual(self.audit["rows"][7]["semantics"]["status"], "PASS")
        self.assertEqual(self.audit["rows"][7]["token_contract"]["status"], "FAIL")

    def test_unseen_checker_event_is_separate(self):
        record = self.audit["rows"][94]
        self.assertEqual(record["semantics"]["status"], "PASS")
        self.assertEqual(record["neutral_prefix_support"]["status"], "FAIL")
        neutral_text = json.dumps(self.packet[94]["student_prefix"])
        self.assertNotIn("checker", neutral_text)
        self.assertIn("checker", self.packet[94]["generation_messages"][-1]["content"])

    def test_mid_sentence_target_preserved(self):
        self.assertTrue(self.packet[137]["target"].endswith("each segment of"))
        self.assertEqual(self.audit["rows"][137]["final_line_format"]["status"], "FAIL")

    def test_restricted_arithmetic_parser(self):
        with self.assertRaises(ValueError):
            arithmetic("__import__('os')")

    def test_freeze_manifest_if_present(self):
        manifest_path = FOLDER / "FREEZE.json"
        if not manifest_path.exists():
            self.skipTest("Pre-freeze run; manifest verified in post-freeze run")
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["state"], "FROZEN_BEFORE_ANY_AUTHOR_LABEL_COMPARISON")
        for relative, expected in manifest["files"].items():
            self.assertEqual(digest(ROOT / relative), expected, relative)


if __name__ == "__main__":
    unittest.main(verbosity=2)
