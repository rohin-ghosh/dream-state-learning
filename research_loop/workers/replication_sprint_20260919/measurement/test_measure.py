"""CPU-only tests; synthetic positive examples are never research observations."""

from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import measure


def reference(record_index, kind):
    return {"index": record_index, "kind": kind, "sha256": measure.digest([record_index, kind])}


def frame(record_index=20):
    return {"stage": "ACT", "request": reference(record_index, "REQUEST"),
            "response": reference(record_index + 1, "RESPONSE"),
            "committed": reference(record_index + 2, "COMMITTED"),
            "stage_receipt": reference(record_index + 3, "R184_STAGE")}


def sample_case(namespace="test-journal", epoch="test-epoch"):
    return measure.new_case("test_only", "synthetic", epoch, namespace, frame(),
                            {"test_fixture": True})


class MeasurementTests(unittest.TestCase):
    def test_missing_is_unknown_not_no(self):
        report = measure.aggregate([sample_case()])
        result = report["cohorts"]["test_only"]["metrics"]["next_act_correct"]
        self.assertEqual((result["yes"], result["no"], result["unknown"]), (0, 0, 1))
        self.assertEqual(result["assessed_denominator"], 0)
        self.assertIsNone(result["yes_rate_among_assessed"])

    def test_delivery_and_visibility_never_imply_uptake(self):
        case = sample_case()
        for metric in ("feedback_delivered", "exact_visibility_at_act", "next_act_observed"):
            measure.annotate(case, metric, True, "Synthetic explicit receipt", [{"fixture": True}])
        report = measure.aggregate([case])["cohorts"]["test_only"]
        self.assertEqual(report["metrics"]["specific_recognition"]["unknown"], 1)
        self.assertEqual(report["conditional"]["next_act_correct_given_exact_visibility"]["assessed_denominator"], 0)

    def test_intention_text_does_not_establish_artifacts(self):
        case = sample_case()
        case["unreviewed_text"] = 'I will write six captions. print("The answer is correct")'
        metrics = measure.aggregate([case])["cohorts"]["test_only"]["metrics"]
        for metric in ("artifact_plan_established", "planned_artifact_emitted", "specific_recognition", "next_act_correct"):
            self.assertEqual(metrics[metric]["unknown"], 1)

    def test_known_decisions_need_evidence(self):
        with self.assertRaisesRegex(ValueError, "evidence"):
            measure.annotate(sample_case(), "next_act_correct", True, "unsupported", [])

    def test_non_boolean_truthiness_rejected(self):
        with self.assertRaisesRegex(ValueError, "tristate"):
            measure.annotate(sample_case(), "next_act_correct", "false", "bad type", [{}])

    def test_same_record_repeated_is_not_a_replication(self):
        case = sample_case()
        report = measure.aggregate([case, deepcopy(case), deepcopy(case)])
        self.assertEqual(report["unique_case_count"], 1)
        self.assertEqual(report["analysis_exclusions_NOT_training"][0]["input_rows"], 2)
        self.assertEqual(report["training_rows_excluded"], 0)

    def test_conflicting_hash_excludes_all_not_first_wins(self):
        first, second = sample_case(), sample_case()
        second["anchor"]["sha256"] = "a" * 64
        report = measure.aggregate([first, second])
        self.assertEqual(report["unique_case_count"], 0)
        self.assertIn("conflicting_record", report["analysis_exclusions_NOT_training"][0]["reason"])

    def test_conflicting_annotation_excludes_all(self):
        first, second = sample_case(), sample_case()
        measure.annotate(second, "specific_recognition", True, "conflict", [{}])
        self.assertEqual(measure.aggregate([first, second])["unique_case_count"], 0)

    def test_conflicting_non_anchor_receipt_is_detected(self):
        first, second = sample_case(), sample_case()
        second["frame"]["request"]["sha256"] = "c" * 64
        self.assertEqual(measure.aggregate([first, second])["unique_case_count"], 0)

    def test_same_record_new_epoch_does_not_double_count(self):
        self.assertEqual(measure.aggregate([sample_case(), sample_case(epoch="other")])["unique_case_count"], 0)

    def test_different_journals_same_index_are_distinct(self):
        report = measure.aggregate([sample_case(), sample_case(namespace="other-journal")])
        self.assertEqual(report["unique_case_count"], 2)

    def test_assistance_visibility_epoch_stratification(self):
        first, second = sample_case(), sample_case(namespace="other-journal", epoch="other")
        second["assistance"] = "PARENT_TEXT_VISIBLE"
        measure.annotate(second, "exact_visibility_at_act", True, "explicit", [{}])
        self.assertEqual(len(measure.aggregate([first, second])["strata"]), 2)

    def test_conditional_denominators_keep_unknown(self):
        cases = [sample_case(namespace=str(position)) for position in range(3)]
        for case in cases:
            measure.annotate(case, "specific_recognition", True, "explicit", [{}])
        measure.annotate(cases[0], "next_act_correct", True, "explicit", [{}])
        measure.annotate(cases[1], "next_act_correct", False, "explicit", [{}])
        result = measure.aggregate(cases)["cohorts"]["test_only"]["conditional"]["next_act_correct_given_specific_recognition"]
        self.assertEqual((result["sampled_denominator"], result["assessed_denominator"], result["unknown"]), (3, 2, 1))
        self.assertEqual(result["yes_rate_among_assessed"], 0.5)

    def test_record_order_and_kind_are_checked(self):
        bad = frame()
        bad["committed"]["index"] = 0
        with self.assertRaisesRegex(ValueError, "order"):
            measure.validate_frame(bad)
        bad = frame()
        bad["response"]["kind"] = "INBOX"
        with self.assertRaisesRegex(ValueError, "receipt"):
            measure.validate_frame(bad)


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="test_", dir=measure.HERE)
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "fixture.json"
        self.path.write_text('{"key": {"a/b": true}}')

    def test_hash_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "sha256_mismatch"):
            measure.Artifacts().load(self.path, "a" * 64)

    def test_file_size_bound(self):
        with patch.object(measure, "MAX_FILE_BYTES", 8):
            with self.assertRaisesRegex(ValueError, "artifact_size_limit"):
                measure.Artifacts().load(self.path)

    def test_total_size_bound(self):
        with patch.object(measure, "MAX_TOTAL_BYTES", 8):
            with self.assertRaisesRegex(ValueError, "total_artifact_size_limit"):
                measure.Artifacts().load(self.path)

    def test_pointer_escape_and_missing_target(self):
        store = measure.Artifacts()
        self.assertIs(store.verify_ref(store.ref(self.path, "/key/a~1b")), True)
        with self.assertRaises(KeyError):
            store.ref(self.path, "/absent")

    def test_cached_reads_not_counted_twice(self):
        store = measure.Artifacts()
        store.load(self.path)
        count = store.bytes_read
        store.load(self.path)
        self.assertEqual(store.bytes_read, count)

    def test_duplicate_json_keys_rejected(self):
        self.path.write_text('{"state": "NO", "state": "YES"}')
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            measure.Artifacts().load(self.path)


class AnnotationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="test_", dir=measure.HERE)
        self.addCleanup(self.directory.cleanup)
        self.directory = Path(self.directory.name)
        self.source = self.directory / "evidence.json"
        self.annotation = self.directory / "annotation.json"
        self.payload = {
            "frame": frame(), "identity": {"journal_id": "synthetic", "epoch": "synthetic-epoch"},
            "assistance": "NO_PARENT_HELP_VERIFIED", "review": "Explicit synthetic reviewer decision",
            "later_relevant_action": frame(80), "post_sleep_action": frame(120),
            "sleep_boundary": reference(110, "SLEEP_COMPLETE"), "intervening_context_complete": True,
            "no_reminder": True, "no_reteaching": True, "fresh_context": True,
            "novel_instance": True, "no_parent_help": True,
            "plan_response": reference(12, "RESPONSE"), "next_action_response": frame()["response"],
            "artifact_specification": "One worked calculation with an independent check",
            "external_result": {"record": reference(24, "TOOL_RESULT"), "result": {"correct": True}},
        }

    def prepare(self, states):
        self.source.write_text(json.dumps(self.payload))
        self.store = measure.Artifacts()
        self.store.load(self.source)
        entry = {"label": "test-only", "epoch": "synthetic-epoch", "journal_id": "synthetic",
                 "frame_evidence": self.store.ref(self.source, "/frame"),
                 "identity_evidence": self.store.ref(self.source, "/identity"),
                 "assistance": "NO_PARENT_HELP_VERIFIED", "assistance_evidence": self.store.ref(self.source, "/assistance"),
                 "metrics": {}}
        for name, state in states.items():
            entry["metrics"][name] = {"state": state, "basis": "Synthetic reviewed test fixture only.",
                "evidence": [self.store.ref(self.source, "/review")],
                "criteria": {criterion: self.store.ref(self.source, "/" + criterion)
                             for criterion in measure.REQUIRED_CRITERIA.get(name, ())}}
        document = {"schema": "think_act_annotations_v1", "reviewer": "CPU test, not a scientific reviewer", "cases": [entry]}
        self.annotation.write_text(json.dumps(document))
        return self.store.load(self.annotation)

    def import_cases(self, document):
        return measure.import_annotations(self.store, self.annotation, document)[0]

    def test_explicit_complete_chain_is_counted(self):
        document = self.prepare({name: "YES" for name in measure.METRICS})
        cases = self.import_cases(document)
        self.assertTrue(all(value["state"] == "YES" for value in cases[0]["metrics"].values()))
        self.assertEqual(measure.aggregate(cases)["cohorts"]["annotated_correction_chain"]["metrics"]["no_reminder_reuse"]["yes"], 1)

    def test_missing_no_reminder_evidence_rejected(self):
        document = self.prepare({"specific_recognition": "YES", "next_act_correct": "YES", "no_reminder_reuse": "YES"})
        del document["cases"][0]["metrics"]["no_reminder_reuse"]["criteria"]["no_reminder"]
        with self.assertRaisesRegex(ValueError, "missing_criterion"):
            self.import_cases(document)

    def test_false_no_reminder_evidence_rejected(self):
        self.payload["no_reminder"] = False
        document = self.prepare({"specific_recognition": "YES", "next_act_correct": "YES", "no_reminder_reuse": "YES"})
        with self.assertRaisesRegex(ValueError, "unestablished_criterion"):
            self.import_cases(document)

    def test_sleep_alone_does_not_establish_retention(self):
        document = self.prepare({"post_sleep_retention": "YES"})
        with self.assertRaisesRegex(ValueError, "prerequisite"):
            self.import_cases(document)

    def test_retention_requires_post_sleep_order(self):
        self.payload["sleep_boundary"]["index"] = 130
        document = self.prepare({"specific_recognition": "YES", "next_act_correct": "YES", "post_sleep_retention": "YES"})
        with self.assertRaisesRegex(ValueError, "post_sleep_order"):
            self.import_cases(document)

    def test_prior_help_prevents_clean_transfer_claim(self):
        self.payload["no_parent_help"] = False
        document = self.prepare({"specific_recognition": "YES", "next_act_correct": "YES", "fresh_context_transfer": "YES"})
        with self.assertRaisesRegex(ValueError, "unestablished_criterion"):
            self.import_cases(document)

    def test_artifact_requires_established_plan(self):
        document = self.prepare({"next_act_observed": "YES", "planned_artifact_emitted": "NO"})
        with self.assertRaisesRegex(ValueError, "prerequisite"):
            self.import_cases(document)

    def test_plan_and_emission_are_separate(self):
        document = self.prepare({"artifact_plan_established": "YES", "next_act_observed": "YES", "planned_artifact_emitted": "NO"})
        result = measure.aggregate(self.import_cases(document))["cohorts"]["annotated_correction_chain"]
        self.assertEqual(result["conditional"]["emitted_given_established_plan"]["no"], 1)
        self.assertEqual(result["metrics"]["next_act_correct"]["unknown"], 1)

    def test_external_callback_is_not_check(self):
        self.payload["external_result"] = {"record": reference(24, "INBOX"), "result": "delivered"}
        document = self.prepare({"external_check_performed": "YES"})
        with self.assertRaisesRegex(ValueError, "external_result_not_child_or_delivery"):
            self.import_cases(document)

    def test_external_check_pass_requires_performed(self):
        document = self.prepare({"external_check_passed": "YES"})
        with self.assertRaisesRegex(ValueError, "prerequisite"):
            self.import_cases(document)

    def test_explicit_complete_check_absence_is_not_unknown(self):
        self.payload["complete_check_window"] = True
        self.payload["no_external_check_observed"] = True
        document = self.prepare({"external_check_performed": "NO"})
        decision = document["cases"][0]["metrics"]["external_check_performed"]
        decision["criteria"] = {name: self.store.ref(self.source, "/" + name)
                                for name in ("complete_check_window", "no_external_check_observed")}
        self.assertEqual(self.import_cases(document)[0]["metrics"]["external_check_performed"]["state"], "NO")

    def test_committed_frame_contradiction_rejected(self):
        document = self.prepare({"next_act_committed": "NO"})
        with self.assertRaisesRegex(ValueError, "contradicts_committed_frame"):
            self.import_cases(document)

    def test_identity_binding_cannot_be_relabelled(self):
        document = self.prepare({})
        document["cases"][0]["journal_id"] = "wrong"
        with self.assertRaisesRegex(ValueError, "identity"):
            self.import_cases(document)


class AuthenticInputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = measure.run(measure.HERE / "inputs.json")

    def test_review_counts_and_denominators(self):
        cohort = self.report["cohorts"]["reviewed_correction_chain"]
        self.assertEqual(cohort["sampled_units"], 5)
        self.assertEqual(cohort["metrics"]["specific_recognition"]["yes"], 1)
        self.assertEqual(cohort["metrics"]["next_act_correct"]["no"], 5)
        self.assertEqual(cohort["metrics"]["exact_visibility_at_act"]["yes"], 4)
        self.assertEqual(cohort["source_reported_levels_not_inferred"], {"0": 4, "1": 1})

    def test_higher_level_missing_trials_are_unknown(self):
        cohort = self.report["cohorts"]["reviewed_correction_chain"]
        for metric in ("no_reminder_reuse", "post_sleep_retention", "fresh_context_transfer", "external_check_performed"):
            self.assertEqual(cohort["metrics"][metric]["unknown"], 5)
            self.assertEqual(cohort["metrics"][metric]["assessed_denominator"], 0)

    def test_hourly_exposure_never_promotes_semantics(self):
        cohort = self.report["cohorts"]["unreviewed_ACT"]
        self.assertEqual(cohort["sampled_units"], 11)
        self.assertEqual(cohort["metrics"]["exact_visibility_at_act"]["yes"], 4)
        self.assertEqual(cohort["metrics"]["specific_recognition"]["unknown"], 11)
        self.assertEqual(cohort["metrics"]["next_act_correct"]["unknown"], 11)

    def test_withdrawal_is_not_clean_independence(self):
        case = next(case for case in self.report["cases"] if case["unit"] == "reviewed_withdrawal_cycle")
        self.assertIn("PRIOR_CONTEXT_VISIBLE", case["assistance"])
        self.assertEqual(case["metrics"]["specific_recognition"]["state"], "NO")
        self.assertEqual(case["metrics"]["fresh_context_transfer"]["state"], "UNKNOWN")
        self.assertEqual(case["metrics"]["planned_artifact_emitted"]["state"], "UNKNOWN")

    def test_inputs_bounded_and_no_live_actions(self):
        self.assertLess(self.report["input_bytes_read"], 2 * 1024 * 1024)
        self.assertEqual(self.report["live_actions"], 0)
        self.assertEqual(self.report["training_rows_excluded"], 0)

    def test_markdown_denominators_and_limits(self):
        text = measure.markdown(self.report)
        self.assertIn("Assessed denominator", text)
        self.assertIn("not independent training replications", text)
        self.assertIn("No authentic training rows", text)

    def test_duplicate_import_has_same_scientific_counts(self):
        report = measure.aggregate(self.report["cases"] + deepcopy(self.report["cases"]))
        self.assertEqual(report["unique_case_count"], self.report["unique_case_count"])
        self.assertEqual(report["cohorts"], self.report["cohorts"])

    def test_quote_tampering_is_rejected(self):
        manifest = json.loads((measure.HERE / "inputs.json").read_text())
        path = measure.ROOT / manifest["inputs"][0]["path"]
        document = json.loads(path.read_text())
        row = document["rows"][0]
        evidence = json.loads((path.parent / row["evidence_path"]).read_text())
        row["quotes"][0]["text"] += " changed"
        with self.assertRaisesRegex(ValueError, "quote_hash"):
            measure.verify_review_row(row, evidence)

    def test_review_proof_must_match_projection(self):
        manifest = json.loads((measure.HERE / "inputs.json").read_text())
        path = measure.ROOT / manifest["inputs"][0]["path"]
        row = json.loads(path.read_text())["rows"][0]
        evidence = json.loads((path.parent / row["evidence_path"]).read_text())
        row["proofs"][0]["response"]["sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "proof_projection"):
            measure.verify_review_row(row, evidence)

    def test_cli_rejects_output_outside_workstream(self):
        with patch("sys.argv", ["measure.py", "--output-dir", str(measure.HERE.parent)]):
            with self.assertRaisesRegex(ValueError, "output_must_stay"):
                measure.main()

    def test_cli_stdout_only_preserves_input_hashes(self):
        captured = io.StringIO()
        with patch("sys.argv", ["measure.py"]), contextlib.redirect_stdout(captured):
            measure.main()
        self.assertEqual(json.loads(captured.getvalue())["unique_cases"], 17)
        for source in self.report["source_artifacts"]:
            self.assertEqual(measure.digest_bytes((measure.ROOT / source["path"]).read_bytes()), source["sha256"])

    def test_cli_scope_local_reports_are_deterministic(self):
        with tempfile.TemporaryDirectory(prefix="test_", dir=measure.HERE) as output:
            for attempt in range(2):
                with patch("sys.argv", ["measure.py", "--output-dir", output]), contextlib.redirect_stdout(io.StringIO()):
                    measure.main()
                report = json.loads((Path(output) / "SUMMARY.json").read_text())
                self.assertEqual(report, self.report)
                self.assertEqual((Path(output) / "SUMMARY.md").read_text(), measure.markdown(self.report))


if __name__ == "__main__":
    unittest.main()
