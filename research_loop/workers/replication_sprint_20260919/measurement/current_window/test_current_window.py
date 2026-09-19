"""Focused CPU checks: chronology, visibility, selection and pinned review."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import current_window as window


def record(index, kind, **fields):
    return {"index": index, "kind": kind, "sha256": window.sha(f"{index}:{kind}".encode()),
            "time_unix": window.CUTOFF - 100 + index, **fields}


def records(start=10, stage="ACT"):
    digest = window.sha(str(start).encode())
    source = window.sha(str(start + 1).encode())
    return [record(start, "REQUEST", request_digest=digest, masked=True, external=[]),
            record(start + 1, "RESPONSE", request_digest=digest, document_sha256=source, text="synthetic, not research evidence"),
            record(start + 2, "COMMITTED", source_sha256=source),
            record(start + 3, "R184_STAGE", source_sha256=source, stage=stage)]


def parent(index):
    return record(index, "INBOX", actor="parent", event_id=f"parent:inbox:test{index}", source_sha256=window.sha(str(index).encode()))


class SelectionTests(unittest.TestCase):
    def test_late_delivery_goes_to_next_request_not_inflight_response(self):
        frames = window.join_frames(records(10) + records(30))
        groups, unresolved = window.opportunities(frames, [parent(11)], [(0, 40)])
        self.assertEqual(groups[0]["act"]["request"]["index"], 30)
        self.assertEqual(unresolved, [])

    def test_multiple_parent_turns_share_one_opportunity(self):
        groups, unused = window.opportunities(window.join_frames(records(10)), [parent(3), parent(5), parent(7)], [(0, 20)])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["parents"]), 3)

    def test_gap_cannot_be_first_next_act_proof(self):
        groups, unresolved = window.opportunities(window.join_frames(records(30)), [parent(3)], [(0, 10), (20, 40)])
        self.assertEqual(groups, [])
        self.assertEqual(unresolved[0]["reason"], "GAP_CANNOT_ESTABLISH_FIRST_NEXT_ACT")

    def test_pending_delivery_does_not_count_as_failure(self):
        groups, unresolved = window.opportunities(window.join_frames(records(10)), [parent(15)], [(0, 20)])
        self.assertEqual(groups, [])
        self.assertEqual(unresolved[0]["reason"], "NO_NEXT_COMPLETE_ACT_IN_BOUNDED_INPUT")

    def test_last_three_selection_ignores_success_fields(self):
        frames = window.join_frames(records(10) + records(30) + records(50) + records(70))
        groups, unused = window.opportunities(frames, [parent(3), parent(20), parent(40), parent(60)], [(0, 90)])
        target = {"groups": groups}
        decisions = {str(group["act"]["response"]["index"]): {"actionable": True, "target": "synthetic target"} for group in groups}
        groups[0]["success"] = True
        selected = window.select_groups(target, decisions)
        self.assertEqual([group["act"]["response"]["index"] for group in selected], [31, 51, 71])

    def test_all_candidates_require_parent_only_classification(self):
        groups, unused = window.opportunities(window.join_frames(records()), [parent(3)], [(0, 30)])
        with self.assertRaisesRegex(ValueError, "all_candidates"):
            window.select_groups({"groups": groups}, {})

    def test_coverage_intervals_do_not_fill_holes(self):
        self.assertFalse(window.covered(5, 20, [(0, 10), (12, 25)]))
        self.assertTrue(window.covered(5, 20, [(0, 10), (11, 25)]))
        self.assertTrue(window.covered(15, 20, [(0, 10), (12, 25)]))


class BindingTests(unittest.TestCase):
    def test_uncommitted_response_not_an_action(self):
        sample = records()
        self.assertEqual(window.join_frames([sample[0], sample[1], sample[3]]), [])

    def test_stage_source_must_match_response(self):
        sample = records()
        sample[3]["source_sha256"] = "other"
        self.assertEqual(window.join_frames(sample), [])

    def test_masked_actual_stage_order_required(self):
        sample = records()
        sample[0]["masked"] = False
        with self.assertRaisesRegex(ValueError, "masked_stage_order"):
            window.join_frames(sample)

    def test_outcome_and_stage_must_precede_cutoff(self):
        for position in (2, 3):
            sample = records()
            sample[position]["time_unix"] = window.CUTOFF + 1
            self.assertEqual(window.join_frames(sample), [])

    def test_duplicate_source_links_cannot_last_writer_win(self):
        sample = records()
        duplicate = deepcopy(sample[1])
        duplicate["index"] = 19
        with self.assertRaisesRegex(ValueError, "ambiguous_source"):
            window.join_frames(sample + [duplicate])

    def test_same_event_id_different_hash_is_not_visibility(self):
        inbox = parent(3)
        request = {"external": [{"actor": "parent", "event_id": inbox["event_id"], "source_sha256": "wrong"}]}
        self.assertFalse(window.exact_exposure(request, inbox))

    def test_delivery_does_not_imply_visibility(self):
        self.assertFalse(window.exact_exposure({"external": []}, parent(3)))

    def test_source_file_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory(dir=window.HERE, prefix="test_") as directory:
            path = Path(directory) / "fixture.json"
            path.write_text("{}")
            with self.assertRaisesRegex(ValueError, "hash_mismatch"):
                window.Sources().read(path, "wrong")


class AuthenticReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((window.HERE / "EVIDENCE.json").read_text())
        cls.annotations = json.loads((window.HERE / "ANNOTATIONS.json").read_text())
        cls.selection = json.loads((window.HERE / "SELECTION.json").read_text())

    def test_frozen_six_source_bound_annotations_validate(self):
        self.assertEqual(len(self.evidence["rows"]), 6)
        self.assertEqual(self.annotations["evidence_sha256"], window.sha((window.HERE / "EVIDENCE.json").read_bytes()))
        for row, annotation in zip(self.evidence["rows"], self.annotations["rows"]):
            window.verify_annotation(row, annotation)

    def test_c2_target_changed_after_THINK_but_visible_at_ACT(self):
        for row in self.evidence["rows"][:3]:
            self.assertEqual(row["life"], "C2")
            self.assertTrue(row["ACT"]["primary_parent_exactly_visible"])
            self.assertFalse(row["same_target_at_THINK_and_ACT"])
            self.assertTrue(all(thought["request"]["index"] < row["primary_parent"]["inbox"]["index"] for thought in row["THINK"]))

    def test_p3_same_target_visible_in_both_stages(self):
        for row in self.evidence["rows"][3:]:
            self.assertTrue(row["same_target_at_THINK_and_ACT"])
            self.assertTrue(row["ACT"]["primary_parent_exactly_visible"])

    def test_unexposed_recognition_cannot_be_marked_failure(self):
        annotation = deepcopy(self.annotations["rows"][0])
        annotation["specific_recognition_of_primary_in_THINK"] = "NO"
        with self.assertRaisesRegex(ValueError, "must_stay_unknown"):
            window.verify_annotation(self.evidence["rows"][0], annotation)

    def test_truncated_output_prevents_negative_review(self):
        row = deepcopy(self.evidence["rows"][0])
        row["ACT"]["output"]["truncated"] = True
        with self.assertRaisesRegex(ValueError, "full_selected_outputs"):
            window.verify_annotation(row, self.annotations["rows"][0])

    def test_wrong_literal_span_fails(self):
        annotation = deepcopy(self.annotations["rows"][0])
        annotation["ACT_quote"] = "an invented quote"
        with self.assertRaisesRegex(ValueError, "ACT_quote_mismatch"):
            window.verify_annotation(self.evidence["rows"][0], annotation)

    def test_p3_unlinked_newer_act_remains_explicit(self):
        omitted = next(item for item in self.selection["analysis_omissions_NOT_training"] if item["ACT_response"] == 10638)
        self.assertIn("UNKNOWN", omitted["reason"])
        self.assertNotIn(10638, self.selection["selected_ACT_responses"]["GAME1_P3"])

    def test_unknown_metrics_have_zero_assessed_denominator(self):
        counts = window.metric_counts(["UNKNOWN", "UNKNOWN", "UNKNOWN"])
        self.assertEqual(counts["assessed_denominator"], 0)
        self.assertEqual(counts["sampled_denominator"], 3)
        self.assertIsNone(counts["YES_rate_among_assessed"])

    def test_no_historical_five_chain_inputs(self):
        manifest = json.loads((window.HERE / "SOURCE_MANIFEST.json").read_text())
        self.assertTrue(all("post_recovery_correction_review_20260919_0139" not in source["path"] for source in manifest["sources"]))
        self.assertEqual(manifest["remote_reads"], 0)
        self.assertEqual(manifest["parent_API_calls"], 0)
        self.assertEqual(manifest["full_journals_read"], 0)
        self.assertEqual(manifest["sealed_score_files_read"], 0)


if __name__ == "__main__":
    unittest.main()
