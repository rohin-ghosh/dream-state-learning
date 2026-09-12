"""Synthetic CPU-only pair fixtures; no production inputs or outcomes."""
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from dataclasses import replace
import io
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from organism_v6 import parent_material_analysis as analysis
from organism_v6 import parent_material_diagnostic as formation
from organism_v6 import parent_material_write as extraction
from organism_v6 import preschool_reasoning as policy
import test_parent_material_diagnostic as fixtures


class OneTickDriver(formation.DiagnosticDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.st.budget_ticks = 1


class SyntheticModel(fixtures.FixtureModel):
    def __init__(self, path, *, repeated=False, response="faithful"):
        super().__init__(path)
        self.counter = 0
        self.repeated = repeated
        self.response = response

    def batch(self, prompts, max_tokens=400, seeds=None, temperature=.7):
        outputs = []
        for prompt in prompts:
            if max_tokens == 100:
                action = json.loads(re.findall(r"^ACT submitted: (.+)$", prompt, re.M)[-1])
                text = f'I submitted "{action}"; the score was 0.50.'
                if self.response == "empty":
                    text = ""
                elif self.response == "wrong-score":
                    text = f'I submitted "{action}"; the score was 1.00.'
                elif self.response == "no-first-person":
                    text = "The score was 0.50."
                elif self.response == "literal-verdict":
                    text += " It was not accepted; partial credit."
                outputs.append(text)
            else:
                action = "north" if self.repeated else f"child-{self.counter:03d}"
                self.counter += 1
                outputs.append("NOTE: synthetic café\nACT: " + action)
        return outputs


class PairedSummaryTests(unittest.TestCase):
    def test_constant_effect_and_discordance(self):
        result = analysis.paired_summary([1] * 64, [0] * 64, replicates=100)
        self.assertEqual(result["mean_count_difference"], 1)
        self.assertEqual(result["mean_count_difference_interval_95"], [1, 1])
        self.assertEqual(result["any_formation_rate_difference_interval_95"], [1, 1])
        self.assertEqual(result["discordant_any_formation"],
                         dict(lesson_only=64, sham_only=0, both=0, neither=0))

    def test_seeded_paired_not_individual_record_resampling(self):
        lesson, sham = [2, 0, 1, 0] * 16, [0, 3, 1, 0] * 16
        first = analysis.paired_summary(lesson, sham, seed=7, replicates=500)
        self.assertEqual(first, analysis.paired_summary(lesson, sham, seed=7, replicates=500))
        self.assertEqual(first["mean_count_difference"], -.25)
        self.assertEqual(first["discordant_any_formation"],
                         dict(lesson_only=16, sham_only=16, both=16, neither=16))
        identical = analysis.paired_summary(lesson, lesson, replicates=100)
        self.assertEqual(identical["mean_count_difference_interval_95"], [0, 0])
        self.assertEqual(sum(first["count_comparison"].values()), 64)

    def test_bounds_and_invalid_counts(self):
        for values in ([1] * 63, [True] * 64, [-1] * 64):
            with self.assertRaises(ValueError):
                analysis.paired_summary(values, [0] * 64)
        for options in (dict(seed=-1), dict(seed=True), dict(replicates=99),
                        dict(replicates=20001), dict(replicates=True)):
            with self.assertRaises(ValueError):
                analysis.paired_summary([0] * 64, [0] * 64, **options)


class ParentMaterialAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.DiagnosticTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.lesson = self.make_arm("lesson")
        self.sham = self.make_arm("sham")
        self.output = self.root / "analysis"

    def make_arm(self, mode, *, name=None, **kwargs):
        model = SyntheticModel(str(self.fixture.model_dir), **kwargs)
        @contextmanager
        def backend(model_path):
            self.assertEqual(model_path, str(self.fixture.model_dir))
            yield model
        config = replace(self.fixture.config, mode=mode, out=str(self.root / (name or mode)))
        with patch.object(formation, "DiagnosticDriver", OneTickDriver):
            formation.run(config, gym=fixtures.FixtureGym(), backend_factory=backend)
        return Path(config.out)

    @staticmethod
    def read(path):
        return json.loads(path.read_bytes())

    @staticmethod
    def rewrite(path, value):
        path.chmod(0o644)
        path.write_bytes(policy._encoded(value))

    def rewrite_lines(self, path, rows):
        path.chmod(0o644)
        path.write_bytes(b"".join(policy._encoded(row) for row in rows))

    def reseal(self, root, *, recompute=True):
        if recompute:
            self.rewrite(root / "results.json", dict(status="COMPLETE",
                         mode=self.read(root / "config.json")["mode"], **formation.summarize(root)))
        manifest = self.read(root / "artifact_hashes.json")
        manifest["files"] = {name: formation._hash(root / name) for name in manifest["files"]}
        self.rewrite(root / "artifact_hashes.json", manifest)

    def run_analysis(self, **kwargs):
        with patch.object(extraction, "_load_tokenizer", return_value=fixtures.FixtureTokenizer()) as load:
            with patch.object(formation, "local_backend", side_effect=AssertionError("no GPU")):
                with patch.object(extraction.trainer, "main", side_effect=AssertionError("no training")):
                    report = analysis.analyze_pair(kwargs.pop("lesson_root", self.lesson),
                        kwargs.pop("sham_root", self.sham), kwargs.pop("output_dir", self.output),
                        replicates=100, **kwargs)
        load.assert_called_once_with(str(self.fixture.model_dir))
        return report

    def result_rows(self):
        return [json.loads(line) for line in (self.output / "per_schedule.jsonl").read_bytes().splitlines()]

    def test_complete_pair_exact_accounting_tokens_and_input_immutability(self):
        before = {str(path): (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)
                  for root in (self.lesson, self.sham) for path in root.iterdir()}
        report = self.run_analysis()
        rows = self.result_rows()
        self.assertEqual(len(rows), 64)
        self.assertTrue(all(row["lesson"]["any_strict_faithful_note_after"] for row in rows))
        self.assertEqual([row["any_grounded_difference"] for row in rows], [0] * 64)
        self.assertEqual([row["episode_id"] for row in rows], self.read(self.lesson / "schedule.json"))
        for mode in ("lesson", "sham"):
            arm = report["arms"][mode]
            totals = arm["totals"]
            self.assertEqual(totals["strict_faithful_note_after"], 64)
            self.assertEqual(totals["unique_grounded_note_after"], 64)
            self.assertEqual(totals["valid_acts"], 64)
            self.assertEqual(totals["generation_requests"], 128)
            self.assertEqual(totals["slot_requests"], 64)
            self.assertEqual(totals["slot_nonempty_responses"], 64)
            self.assertEqual(arm["missing_occurrence_schedules"], [])
            teacher = policy.lesson_block(mode, 0).encode()
            self.assertEqual((self.output / f"{mode}_teacher.txt").read_bytes(), teacher)
            self.assertEqual(arm["teacher"]["tokenizer_tokens"], len(teacher))
            self.assertEqual(totals["teacher_presented_tokens"], len(teacher) * 128)
            self.assertGreater(totals["child_output_bytes"], totals["child_output_chars"])
            self.assertEqual(totals["child_output_tokens"], totals["child_output_bytes"])
            for key, value in totals.items():
                if type(value) is int:
                    self.assertEqual(value, sum(row[mode][key] for row in rows) + arm["unassigned"][key])
            detail = rows[0][mode]["records"][0]
            self.assertTrue(detail["first_person_attempt_form"])
            self.assertFalse(detail["literal_observed_verdict_present"])
            self.assertEqual(detail["source_observed"]["displayed_score"], "0.50")
            self.assertEqual(detail["source_observed"]["verdict"], "not accepted; partial credit")
            self.assertEqual(detail["content_judgment"], "faithful-single-event-record")
        for name, evidence in before.items():
            path = Path(name)
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode), evidence)
        self.assertEqual(report["paired"]["mean_count_difference_interval_95"], [0, 0])
        self.assertIn("not independent learner replication", report["inference"])
        self.assertIn("203 versus sham 158", report["attribution"])
        self.assertFalse(report["training"] or report["eligibility_claim"] or report["H1_claim"])
        self.assertEqual(set(path.name for path in self.output.iterdir()),
                         {"report.json", "per_schedule.jsonl", "lesson_teacher.txt", "sham_teacher.txt",
                          "artifact_hashes.json"})

    def test_duplicate_grounded_counts_remain_faithful_but_not_unique(self):
        repeated = self.make_arm("lesson", name="repeated", repeated=True)
        report = self.run_analysis(lesson_root=repeated)
        totals = report["arms"]["lesson"]["totals"]
        self.assertEqual(totals["strict_faithful_note_after"], 64)
        self.assertEqual(totals["unique_grounded_note_after"], 1)
        self.assertEqual(totals["rejected_note_after"], 63)
        self.assertEqual(totals["rejection_reasons"]["duplicate-grounded-record"], 63)
        self.assertEqual(report["paired"]["discordant_any_formation"]["both"], 64)

    def test_rejected_records_not_dropped_and_diagnostics_not_inferred(self):
        wrong = self.make_arm("sham", name="wrong", response="wrong-score")
        report = self.run_analysis(sham_root=wrong)
        totals = report["arms"]["sham"]["totals"]
        self.assertEqual(totals["note_after_records"], 64)
        self.assertEqual(totals["rejection_reasons"]["score-mismatch"], 64)
        self.assertEqual(report["paired"]["discordant_any_formation"]["lesson_only"], 64)
        detail = self.result_rows()[0]["sham"]["records"][0]
        self.assertTrue(detail["first_person_attempt_form"])
        self.assertEqual(detail["content_judgment"], "score-mismatch")
        self.assertEqual(detail["source_observed"]["displayed_score"], "0.50")

    def test_empty_slot_output_is_not_nonempty_response(self):
        empty = self.make_arm("sham", name="empty", response="empty")
        report = self.run_analysis(sham_root=empty)
        totals = report["arms"]["sham"]["totals"]
        self.assertEqual(totals["slot_outputs"], 64)
        self.assertEqual(totals["slot_nonempty_responses"], 0)
        self.assertEqual(totals["rejection_reasons"]["empty-record"], 64)
        self.assertFalse(self.result_rows()[0]["sham"]["records"][0]["first_person_attempt_form"])

    def test_literal_verdict_only_when_present(self):
        literal = self.make_arm("lesson", name="literal", response="literal-verdict")
        self.run_analysis(lesson_root=literal)
        self.assertTrue(self.result_rows()[0]["lesson"]["records"][0]["literal_observed_verdict_present"])

    def test_missing_note_ledger_row_keeps_unassigned_slot_generation(self):
        _, ledger = policy._lines((self.lesson / "ledger.jsonl").read_bytes())
        removed = next(row for row in ledger if row["kind"] == "note_after")
        self.rewrite_lines(self.lesson / "ledger.jsonl", [row for row in ledger if row is not removed])
        self.reseal(self.lesson)
        report = self.run_analysis()
        arm = report["arms"]["lesson"]
        self.assertEqual(arm["totals"]["note_after_records"], 63)
        self.assertEqual(arm["totals"]["missing_note_after"], 1)
        self.assertEqual(arm["unassigned"]["slot_outputs"], 1)
        self.assertEqual(arm["totals"]["slot_outputs"], 64)
        self.assertEqual(self.result_rows()[0]["lesson"]["missing_note_after"], 1)

    def test_missing_schedule_records_retained_as_zero_observed(self):
        episode = self.read(self.lesson / "schedule.json")[-1]
        _, ledger = policy._lines((self.lesson / "ledger.jsonl").read_bytes())
        self.rewrite_lines(self.lesson / "ledger.jsonl", [row for row in ledger if row.get("episode_id") != episode])
        self.reseal(self.lesson)
        report = self.run_analysis()
        self.assertEqual(report["arms"]["lesson"]["missing_occurrence_schedules"], [episode])
        self.assertEqual(report["arms"]["lesson"]["unassigned"]["generation_requests"], 2)
        self.assertEqual(len(self.result_rows()), 64)
        self.assertEqual(self.result_rows()[-1]["lesson"]["strict_faithful_note_after"], 0)
        self.assertFalse(self.result_rows()[-1]["lesson"]["any_strict_faithful_note_after"])

    def test_orphan_has_no_invented_source_and_unknown_episode_is_accounted(self):
        _, ledger = policy._lines((self.lesson / "ledger.jsonl").read_bytes())
        record = next(row for row in ledger if row["kind"] == "note_after")
        record["execution_id"] = "orphan"
        record["episode_id"] = "unknown"
        self.rewrite_lines(self.lesson / "ledger.jsonl", ledger)
        self.reseal(self.lesson)
        report = self.run_analysis()
        unknown = report["arms"]["lesson"]["unassigned"]
        self.assertEqual(unknown["note_after_records"], 1)
        self.assertEqual(unknown["records"][0]["reason"], "provenance-orphan")
        self.assertIsNone(unknown["records"][0]["source_observed"])
        self.assertIsNone(unknown["records"][0]["content_judgment"])
        self.assertEqual(report["arms"]["lesson"]["totals"]["note_after_records"], 64)

    def test_missing_actual_output_diagnostics_unavailable_not_false(self):
        _, events = policy._lines((self.lesson / "generations.jsonl").read_bytes())
        slot = next(row["request_index"] for row in events if row["kind"] == "request" and row["max_tokens"] == 100)
        self.rewrite_lines(self.lesson / "generations.jsonl", [row for row in events
                           if not (row["kind"] == "output" and row["request_index"] == slot)])
        self.reseal(self.lesson)
        report = self.run_analysis()
        detail = self.result_rows()[0]["lesson"]["records"][0]
        self.assertFalse(detail["actual_slot_output"])
        self.assertIsNone(detail["first_person_attempt_form"])
        self.assertIsNone(detail["literal_observed_verdict_present"])
        self.assertIsNone(detail["content_judgment"])
        self.assertEqual(report["arms"]["lesson"]["totals"]["missing_generation_outputs"], 1)

    def test_invalid_feedback_preserved_without_inventing_valid_act(self):
        _, ledger = policy._lines((self.lesson / "ledger.jsonl").read_bytes())
        action = next(row for row in ledger if row["kind"] == "act")
        action["score"] = None
        self.rewrite_lines(self.lesson / "ledger.jsonl", ledger)
        self.reseal(self.lesson)
        report = self.run_analysis()
        totals = report["arms"]["lesson"]["totals"]
        self.assertEqual(totals["actions"], 64)
        self.assertEqual(totals["measured_actions"], 63)
        self.assertEqual(totals["invalid_feedback_actions"], 1)
        self.assertEqual(totals["valid_acts"], 63)
        detail = self.result_rows()[0]["lesson"]["records"][0]
        self.assertIsNone(detail["source_observed"])
        self.assertIsNone(detail["content_judgment"])

    def test_source_absent_from_actual_wake_not_a_valid_act(self):
        _, ledger = policy._lines((self.lesson / "ledger.jsonl").read_bytes())
        action = next(row for row in ledger if row["kind"] == "act")
        action["action"] = "invented"
        self.rewrite_lines(self.lesson / "ledger.jsonl", ledger)
        self.reseal(self.lesson)
        report = self.run_analysis()
        self.assertEqual(report["arms"]["lesson"]["totals"]["measured_actions"], 64)
        self.assertEqual(report["arms"]["lesson"]["totals"]["valid_acts"], 63)
        self.assertFalse(self.result_rows()[0]["lesson"]["action_diagnostics"][0]["in_actual_wake"])

    def test_first_person_form_not_inferred_from_slot_response(self):
        no_first_person = self.make_arm("sham", name="no-first", response="no-first-person")
        report = self.run_analysis(sham_root=no_first_person)
        totals = report["arms"]["sham"]["totals"]
        self.assertEqual(totals["slot_nonempty_responses"], 64)
        self.assertEqual(totals["first_person_attempt_forms"], 0)
        self.assertEqual(totals["first_person_diagnostic_unavailable"], 0)
        self.assertEqual(totals["rejection_reasons"]["missing-first-person-action"], 64)

    def test_completion_and_config_validation_before_output(self):
        self.rewrite(self.lesson / "results.json", dict(self.read(self.lesson / "results.json"), status="INCOMPLETE"))
        self.reseal(self.lesson, recompute=False)
        with self.assertRaisesRegex(ValueError, "source recomputation"):
            self.run_analysis()
        self.assertFalse(self.output.exists())

    def test_schedule_configuration_tampering_rejected(self):
        self.rewrite(self.lesson / "schedule.json", list(reversed(self.read(self.lesson / "schedule.json"))))
        self.reseal(self.lesson)
        with self.assertRaisesRegex(ValueError, "schedule mismatch"):
            self.run_analysis()
        self.assertFalse(self.output.exists())

    def test_changed_protocol_rejected(self):
        config = self.read(self.lesson / "config.json")
        config["protocol"]["generation_seed"] = 99
        self.rewrite(self.lesson / "config.json", config)
        self.reseal(self.lesson)
        with self.assertRaisesRegex(ValueError, "protocol changed"):
            self.run_analysis()

    def test_dose_mismatch_rejected(self):
        dose = self.read(self.lesson / "teaching_dose.json")
        dose["actual_token_counts"]["lesson"] += 1
        self.rewrite(self.lesson / "teaching_dose.json", dose)
        self.reseal(self.lesson)
        with self.assertRaisesRegex(ValueError, "dose/tokenizer mismatch"):
            self.run_analysis()
        self.assertFalse(self.output.exists())

    def test_rendered_token_count_mismatch_rejected(self):
        _, events = policy._lines((self.lesson / "generations.jsonl").read_bytes())
        next(row for row in events if row["kind"] == "request")["prompt_tokens"] += 1
        self.rewrite_lines(self.lesson / "generations.jsonl", events)
        self.reseal(self.lesson)
        with self.assertRaisesRegex(ValueError, "prompt/tokenizer mismatch"):
            self.run_analysis()

    def test_arm_order_and_failed_formation_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected lesson then sham"):
            self.run_analysis(lesson_root=self.sham, sham_root=self.lesson)
        self.lesson.chmod(0o755)
        (self.lesson / "failure.json").write_bytes(policy._encoded(dict(error="synthetic failure")))
        manifest = self.read(self.lesson / "artifact_hashes.json")
        manifest["files"]["failure.json"] = formation._hash(self.lesson / "failure.json")
        self.rewrite(self.lesson / "artifact_hashes.json", manifest)
        with self.assertRaisesRegex(ValueError, "failed formation"):
            self.run_analysis()

    def test_duplicate_generation_ids_rejected_even_when_resealed(self):
        _, events = policy._lines((self.lesson / "generations.jsonl").read_bytes())
        events.append(dict(events[0]))
        self.rewrite_lines(self.lesson / "generations.jsonl", events)
        self.reseal(self.lesson)
        with self.assertRaisesRegex(ValueError, "duplicate generation"):
            self.run_analysis()

    def test_fresh_disjoint_nonsymlink_output(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_analysis()
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.run_analysis(output_dir=self.lesson / "nested")
        link = self.root / "linked"
        link.symlink_to(self.lesson, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.run_analysis(lesson_root=link)

    def test_input_change_during_analysis_refused_before_writing(self):
        original = analysis._arm
        def change_after_read(root, snapshot, tokenizer):
            result = original(root, snapshot, tokenizer)
            if root == self.sham:
                self.rewrite(self.lesson / "teaching_dose.json", {"changed": True})
            return result
        with patch.object(analysis, "_arm", side_effect=change_after_read):
            with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
                self.run_analysis()
        self.assertFalse(self.output.exists())

    def test_byte_bound_before_snapshot(self):
        with patch.object(analysis, "MAX_ARTIFACT_BYTES", 1):
            with patch.object(extraction, "_formation_snapshot") as snapshot:
                with self.assertRaisesRegex(ValueError, "CPU byte bound"):
                    self.run_analysis()
                snapshot.assert_not_called()

    def test_cli_synthetic_success_and_help_without_inputs(self):
        with patch.object(extraction, "_load_tokenizer", return_value=fixtures.FixtureTokenizer()):
            with redirect_stdout(io.StringIO()) as output:
                analysis.main(["--lesson-root", str(self.lesson), "--sham-root", str(self.sham),
                               "--out", str(self.output), "--bootstrap-replicates", "100"])
        self.assertEqual(json.loads(output.getvalue())["status"], "COMPLETE")
        with patch.object(analysis, "analyze_pair") as analyze:
            with redirect_stdout(io.StringIO()) as help_text:
                with self.assertRaises(SystemExit) as exit_code:
                    analysis.main(["--help"])
            self.assertEqual(exit_code.exception.code, 0)
            self.assertIn("--bootstrap-seed", help_text.getvalue())
            analyze.assert_not_called()

    def test_cli_validation_failure_has_no_traceback(self):
        with redirect_stderr(io.StringIO()) as errors:
            with self.assertRaises(SystemExit) as exit_code:
                analysis.main(["--lesson-root", str(self.lesson), "--sham-root", str(self.sham),
                               "--out", str(self.output), "--bootstrap-replicates", "2"])
        self.assertEqual(exit_code.exception.code, 2)
        self.assertIn("analysis refused", errors.getvalue())
        self.assertNotIn("Traceback", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
