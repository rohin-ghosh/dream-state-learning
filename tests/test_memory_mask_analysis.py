"""CPU-only synthetic fixtures; patched fixture hashes are NOT native fit evidence."""
import contextlib
import copy
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest import mock

from organism_v6 import memory_dose as native
from organism_v6 import memory_mask_analysis as analysis


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


class MemoryMaskAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        taken = set()
        identities = native.make_owner_ids(random.Random(71), 64, taken)
        cls.bank = native.generate_bank(0, 71, identities, {}, {}, taken)
        cues = native.build_cues(cls.bank, "Mock distractor.", adjacent_subset=4)
        scores = native.score_cues(native.MockScorer(seed=71), cues, [1.0])
        cls.rows = []
        for cue, off, on in zip(cues, scores["off"], scores["on"][1.0]):
            row = {key: value for key, value in cue.items() if key not in ("prompt", "candidates")}
            for side, score in (("OFF", off), ("ON", on)):
                row[side] = dict(p_raw={key: round(value, 7) for key, value in score["p_raw"].items()},
                                 logp={key: round(value, 5) for key, value in score["logp"].items()},
                                 mass=round(score["mass"], 7))
                if "p_abstain" in score:
                    row[side]["p_abstain"] = round(score["p_abstain"], 7)
            cls.rows.append(row)
        cls.gates = native.evaluate_gates(native.summarize_eval(dict(cues=cls.rows), cls.bank), seed=0)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.baseline = self.directory / "relocated_baseline"
        self.mask = self.directory / "relocated_mask"
        self.counts = dict(analysis.COUNTS, items=4, changed_masks=2, changed_label_items=1,
                           input_tokens_per_epoch=50, original_supervised_per_epoch=46,
                           supervised_per_epoch=30, removed_labels=16, boundary_straddles=1,
                           omitted_owner_prefix_tokens=1)
        self.patch("COUNTS", self.counts)
        self.patch("KINDS", dict(fact=1, lesson=1, filler=1, filler_colour=1))
        self.patch("FIT", dict(analysis.FIT, n_items=4, tokens=150))
        items = [dict(kind=kind, context=context, target=target, chat=False, weight=1.0,
                      mask_context=False, event_ids=[kind]) for kind, context, target in (
                          ("fact", "Mock observation. ", "Owner K7M4 has a red car."),
                          ("lesson", "", "Press ARM."), ("filler", "", "Six screws."),
                          ("filler_colour", "", "Door blue."))]
        self.original = dict(corpus=items, stats=dict(supervised_tokens=46),
                             sha=native.sha_of([(native.render_item(item), item["weight"], False) for item in items]),
                             items_sha=native.items_sha(items), synthetic=True, fixture_only=True)
        self.derived = analysis.expected_mask_corpus(self.original)
        for root, corpus in ((self.baseline, self.original), (self.mask, self.derived)):
            write_json(root / analysis.CORPUS, corpus)
            write_json(root / "manifest.json", dict(seed=1, fixture_only=True))
            write_json(root / "distractor.json", dict(text="Mock distractor.", fixture_only=True))
            for index in range(3):
                write_json(root / f"banks/bank{index}.json", self.bank)
        self.source_hashes = {relative: analysis.digest(self.baseline / relative) for relative in analysis.INPUT_HASHES}
        self.patch("INPUT_HASHES", self.source_hashes)
        self.patch("MASK_CORPUS_HASH", analysis.digest(self.mask / analysis.CORPUS))
        corpus_metadata = dict(sha=self.original["sha"], items_sha=self.original["items_sha"],
                               ordering="chronological", token_budget=250000)
        self.seed_receipt = dict(destination_run="/remote/original", corpora={"0": corpus_metadata},
                                 inputs={relative: dict(sha256=checksum, bytes=(self.baseline / relative).stat().st_size)
                                         for relative, checksum in self.source_hashes.items()})
        self.receipt = dict(status="PREPARED_NOT_TRAINED", training_seed=2, source_bank_seed=1,
                            rank=8, epochs=3, lr=1e-4, expected_steps=9693,
                            treatment="fact_and_lesson_context_mask_only", clean_lineage_eligible=False,
                            source_corpus_sha256=self.source_hashes[analysis.CORPUS],
                            model_authentication="UNRESOLVED_LOCAL_HASHES_ONLY", counts=self.counts,
                            source_inputs=self.source_hashes,
                            inputs=dict(self.source_hashes, **{analysis.CORPUS: analysis.MASK_CORPUS_HASH}),
                            source_corpora={"0": corpus_metadata}, source="/remote/original_inputs",
                            destination="/remote/mask_attempt2")
        write_json(self.baseline / "seed_run_receipt.json", self.seed_receipt)
        write_json(self.mask / "mask_run_receipt.json", self.receipt)
        for root, corpus, remote, masked in (
                (self.baseline, self.original, "/remote/original", False),
                (self.mask, self.derived, "/remote/mask_attempt2", True)):
            fit = dict(analysis.FIT, corpus_sha=corpus["sha"], items_sha=corpus["items_sha"],
                       supervised_tokens=90 if masked else 138, boundary_straddles=1 if masked else 0,
                       throughput=dict(grad_checkpoint=False), final_loss=1.0, wall_seconds=1.0)
            write_json(root / analysis.ADAPTER / "train_meta.json", fit)
            (root / analysis.ADAPTER / "DONE").write_text("ok\n")
            evaluation = dict(analysis.EVAL_META, adapter=remote + "/" + analysis.ADAPTER,
                              adapter_arg=remote + "/" + analysis.ADAPTER,
                              adapter_meta={field: fit[field] for field in analysis.ADAPTER_FIELDS},
                              abstain_check=dict(ok=True, fixture_only=True), seconds=0.0,
                              cues=copy.deepcopy(self.rows))
            write_json(root / analysis.EVAL, evaluation)
            write_json(root / "report/report.json", self.report())
        self.patch("BASE_HASHES", {relative: analysis.digest(self.baseline / relative) for relative in analysis.BASE_HASHES})

    def patch(self, name, value):
        patcher = mock.patch.object(analysis, name, value)
        patcher.start()
        self.addCleanup(patcher.stop)

    def report(self, banks=None):
        return dict(
            results={analysis.KEY: dict(banks=banks or [0], sleeps=[4], ref_sleep=4,
                                       per_bank={"0": dict(gates=self.gates)},
                                       frame=self.gates, gates=self.gates)}, n_evals=len(banks or [0]),
            evals_used={"F_r16k16__across__8__1.0__4__0": analysis.TAG},
            gates_thresholds=json.loads(json.dumps(native.GATES)))

    def change(self, root, relative, transform):
        value = analysis.load(root / relative)
        transform(value)
        write_json(root / relative, value)

    def compare(self):
        return analysis.compare_runs(self.baseline, self.mask)

    def assert_invalid(self, result, phrase=None):
        self.assertFalse(result["valid"], result)
        self.assertEqual(result["metrics_status"], "unavailable_as_matched_evidence")
        self.assertNotIn("delta_mask_minus_baseline", result)
        if phrase:
            self.assertIn(phrase, json.dumps(result))

    def test_native_reduction_relocated_paths_and_negative_gate_are_valid_artifacts(self):
        result = self.compare()
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["mask"]["metrics"]["G9"]["passed"])
        self.assertEqual(result["mask"]["metrics"]["G9"], self.gates["G9_frame_binding"])
        self.assertEqual(result["mask"]["metrics"]["G11"], self.gates["G11_abstention"])
        self.assertTrue(result["comparison"]["off_exact_at_serialized_precision"])
        self.assertIn("exploratory", result["classification"])
        self.assertFalse(result["clean_lineage_eligible"])

    def test_missing_adapter_weights_explicit(self):
        result = self.compare()
        for label in ("baseline", "mask"):
            self.assertFalse(result[label]["adapter_weights_present"])
            self.assertIn("Adapter weights absent", " ".join(result[label]["warnings"]))

    def test_present_weights_not_claimed_authenticated(self):
        (self.mask / analysis.ADAPTER / "adapter_model.safetensors").write_bytes(b"mock not real weights")
        result = self.compare()
        self.assertTrue(result["mask"]["adapter_weights_present"])
        self.assertIn("do not authenticate", " ".join(result["limitations"]))

    def test_baseline_three_bank_report_selects_bank_zero_not_pooled(self):
        report = self.report([0, 1, 2])
        report["results"][analysis.KEY]["frame"] = dict(unused="pooled, deliberately different")
        report["results"][analysis.KEY]["gates"] = dict(unused="pooled")
        write_json(self.baseline / "report/report.json", report)
        result = self.compare()
        self.assertTrue(result["valid"], result)
        self.assertTrue(result["baseline"]["report"]["pooled_ignored"])

    def test_absent_baseline_report_is_explicitly_unavailable(self):
        (self.baseline / "report/report.json").unlink()
        result = self.compare()
        self.assertTrue(result["valid"], result)
        self.assertIsNone(result["baseline"]["report"]["agreement"])

    def test_missing_mask_report_is_incomplete_not_scientific_failure(self):
        (self.mask / "report/report.json").unlink()
        self.assert_invalid(self.compare(), "mask native report missing")

    def test_report_rejects_either_gate_disagreement(self):
        for name in analysis.GATE_NAMES:
            with self.subTest(gate=name):
                report = copy.deepcopy(self.report())
                report["results"][analysis.KEY]["per_bank"]["0"]["gates"][name]["passed"] = True
                write_json(self.mask / "report/report.json", report)
                self.assert_invalid(self.compare(), name)

    def test_report_rejects_threshold_tag_extra_eval_and_wrong_sleep(self):
        changes = [lambda report: report["gates_thresholds"].update(frame_spill=0.9),
                   lambda report: report["gates_thresholds"].update(abstain_min=0.0),
                   lambda report: report.update(evals_used={}),
                   lambda report: report.update(n_evals=2),
                   lambda report: report["results"][analysis.KEY].update(ref_sleep=3)]
        for change in changes:
            with self.subTest(change=change):
                report = copy.deepcopy(self.report())
                change(report)
                write_json(self.mask / "report/report.json", report)
                self.assert_invalid(self.compare(), "report")

    def test_source_and_derived_hashes_refuse_corruption(self):
        for root, relative in ((self.baseline, "banks/bank0.json"), (self.mask, analysis.CORPUS)):
            with self.subTest(root=root):
                path = root / relative
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                self.assert_invalid(self.compare(), "input hash")
                path.write_bytes(original)

    def test_receipt_counts_require_exact_measured_values(self):
        for field in self.counts:
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt)
                receipt["counts"][field] += 1
                write_json(self.mask / "mask_run_receipt.json", receipt)
                self.assert_invalid(self.compare(), "receipt counts")

    def test_receipt_rejects_manifest_changes_and_traversal(self):
        for field in ("source_inputs", "inputs"):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt)
                receipt[field]["../../unapproved.json"] = "0" * 64
                write_json(self.mask / "mask_run_receipt.json", receipt)
                self.assert_invalid(self.compare(), "input manifest")

    def test_rebound_bad_transformation_still_rejected(self):
        changes = [lambda corpus: corpus["corpus"][0].update(context="Different input. "),
                   lambda corpus: corpus["corpus"][0].update(target="Owner WRONG has a car."),
                   lambda corpus: corpus["corpus"][0].update(mask_context=False),
                   lambda corpus: corpus["corpus"][1].update(mask_context=False),
                   lambda corpus: corpus["corpus"][2].update(mask_context=True),
                   lambda corpus: corpus["corpus"][3].update(weight=2.0),
                   lambda corpus: corpus["corpus"].reverse(),
                   lambda corpus: corpus.update(extra="not permitted")]
        for change in changes:
            with self.subTest(change=change):
                corpus = copy.deepcopy(self.derived)
                change(corpus)
                write_json(self.mask / analysis.CORPUS, corpus)
                checksum = analysis.digest(self.mask / analysis.CORPUS)
                receipt = copy.deepcopy(self.receipt)
                receipt["inputs"][analysis.CORPUS] = checksum
                write_json(self.mask / "mask_run_receipt.json", receipt)
                with mock.patch.object(analysis, "MASK_CORPUS_HASH", checksum):
                    self.assert_invalid(self.compare(), "derived transformation")

    def test_fit_refuses_recipe_dose_mask_identity_and_completion_changes(self):
        path = self.mask / analysis.ADAPTER / "train_meta.json"
        original = analysis.load(path)
        changes = dict(steps=9692, total_steps=9692, lr=3e-5, seed=1, rank=16, epochs=2,
                       supervised_tokens=138, boundary_straddles=0, truncated_items=1,
                       max_len=256, model="other", targets=["q_proj"], corpus_sha="bad", items_sha="bad",
                       ordering="reverse", measure_only=True, synthetic=False,
                       tokenization="separate", recipe="other", tokens=149)
        for field, value in changes.items():
            with self.subTest(field=field):
                write_json(path, dict(original, **{field: value}))
                self.assert_invalid(self.compare(), "fit." + field)

    def test_fit_refuses_nonfinite_loss_and_checkpointing(self):
        fit = analysis.load(self.mask / analysis.ADAPTER / "train_meta.json")
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                analysis.validate_fit(dict(fit, final_loss=value), self.derived, True)
        fit["throughput"]["grad_checkpoint"] = True
        with self.assertRaisesRegex(ValueError, "checkpointing"):
            analysis.validate_fit(fit, self.derived, True)

    def test_missing_and_wrong_done(self):
        path = self.mask / analysis.ADAPTER / "DONE"
        path.write_text("measure_only\n")
        self.assert_invalid(self.compare(), "fit DONE")
        path.unlink()
        self.assert_invalid(self.compare(), "FileNotFoundError")

    def test_frozen_source_or_baseline_hash_mismatch(self):
        with mock.patch.object(analysis, "SOURCE_HASH", "0" * 64):
            self.assert_invalid(self.compare(), "native scorer")
        self.change(self.baseline, analysis.EVAL, lambda value: value.update(seconds=99.0))
        self.assert_invalid(self.compare(), "frozen baseline hash")

    def test_relocated_remote_adapter_binding_cannot_be_rewritten(self):
        self.change(self.mask, analysis.EVAL, lambda value: value.update(
            adapter=str(self.mask / analysis.ADAPTER), adapter_arg=str(self.mask / analysis.ADAPTER)))
        self.assert_invalid(self.compare(), "remote adapter binding")

    def test_fit_eval_corpus_identity_cannot_be_copied_from_baseline(self):
        baseline_eval = analysis.load(self.baseline / analysis.EVAL)
        self.change(self.mask, analysis.EVAL, lambda value: value.update(adapter_meta=baseline_eval["adapter_meta"]))
        self.assert_invalid(self.compare(), "eval adapter_meta")

    def test_eval_adapter_metadata_cannot_hide_extra_treatment(self):
        self.change(self.mask, analysis.EVAL, lambda value: value["adapter_meta"].update(other_treatment=True))
        self.assert_invalid(self.compare(), "eval adapter_meta field set")

    def test_report_single_bank_pooled_gate_must_also_agree(self):
        report = copy.deepcopy(self.report())
        report["results"][analysis.KEY]["frame"] = copy.deepcopy(self.gates)
        report["results"][analysis.KEY]["frame"]["G11_abstention"]["passed"] = True
        write_json(self.mask / "report/report.json", report)
        self.assert_invalid(self.compare(), "report single-bank")

    def test_native_normalization_uses_candidate_sum_not_rounded_mass(self):
        evaluation = analysis.load(self.mask / analysis.EVAL)
        before = native.summarize_eval(evaluation, self.bank)
        for row in evaluation["cues"]:
            if row["kind"] in analysis.FRAME_KINDS:
                row["ON"]["mass"] *= 0.5
        after = native.summarize_eval(evaluation, self.bank)
        self.assertEqual(native.evaluate_gates(before, seed=0)["G9_frame_binding"],
                         native.evaluate_gates(after, seed=0)["G9_frame_binding"])
        self.assertEqual(after["per_dose"][16]["frame_mass_on"], before["per_dose"][16]["frame_mass_on"] * 0.5)

    def test_missing_duplicate_cue_and_eval_straddle_mismatch(self):
        path = self.mask / analysis.EVAL
        original = analysis.load(path)
        for change in (lambda value: value["cues"].pop(),
                       lambda value: value["cues"].__setitem__(1, value["cues"][0]),
                       lambda value: value.update(boundary_straddles=5376)):
            with self.subTest(change=change):
                value = copy.deepcopy(original)
                change(value)
                write_json(path, value)
                self.assert_invalid(self.compare())

    def test_cue_metadata_and_order_drift_are_not_matched(self):
        before = analysis.load(self.baseline / analysis.EVAL)
        changes = [lambda value: value["cues"].reverse(),
                   lambda value: value["cues"][0].update(context="heldout changed"),
                   lambda value: value["cues"][0].update(cand_tokens=dict(reversed(list(value["cues"][0]["cand_tokens"].items())))),
                   lambda value: value["abstain_check"].update(mode="changed")]
        for change in changes:
            with self.subTest(change=change):
                after = copy.deepcopy(before)
                change(after)
                self.assertFalse(analysis.compare_evals(before, after)["cue_metadata_match"])

    def test_off_drift_exact_no_tolerance_and_no_delta(self):
        self.change(self.mask, analysis.EVAL, lambda value: value["cues"][0]["OFF"].update(mass=value["cues"][0]["OFF"]["mass"] + 0.0000001))
        result = self.compare()
        self.assert_invalid(result)
        self.assertEqual(result["comparison"]["off_changed_count"], 1)
        self.assertAlmostEqual(result["comparison"]["off_max_abs"]["mass"], 0.0000001)

    def test_scores_reject_nonfinite_negative_and_frame_zero(self):
        evaluation = analysis.load(self.mask / analysis.EVAL)
        frame_index = next(index for index, row in enumerate(evaluation["cues"]) if row["kind"] == "frame")
        cases = [(0, "mass", -1.0), (0, "mass", float("inf")), (frame_index, "mass", 0.0),
                 (frame_index, "p_abstain", -0.1)]
        for index, field, value in cases:
            with self.subTest(field=field, value=value):
                altered = copy.deepcopy(evaluation)
                altered["cues"][index]["OFF"][field] = value
                with self.assertRaises(ValueError):
                    analysis.validate_cues(altered, self.bank)

    def test_rounded_zero_nonframe_remains_native_compatible(self):
        evaluation = analysis.load(self.mask / analysis.EVAL)
        score = evaluation["cues"][0]["OFF"]
        score["mass"] = 0.0
        score["p_raw"] = {colour: 0.0 for colour in score["p_raw"]}
        zeros = analysis.validate_cues(evaluation, self.bank)
        self.assertIn(evaluation["cues"][0]["cue_id"], zeros["OFF"])
        gates = native.evaluate_gates(native.summarize_eval(evaluation, self.bank), seed=0)
        self.assertEqual(gates["G9_frame_binding"], self.gates["G9_frame_binding"])

    def test_frame_source_join_and_missing_control_refused(self):
        evaluation = analysis.load(self.mask / analysis.EVAL)
        similar = next(row for row in evaluation["cues"] if row["kind"] == "frame_similar")
        similar["cue_id_used"] = "wrong"
        with self.assertRaisesRegex(ValueError, "similar ID"):
            analysis.validate_cues(evaluation, self.bank)
        similar["kind"] = "other"
        with self.assertRaisesRegex(ValueError, "frame control inventory"):
            analysis.validate_cues(evaluation, self.bank)

    def test_cli_exclusive_output_and_no_input_mutation(self):
        before = {str(path): path.read_bytes() for root in (self.baseline, self.mask) for path in root.rglob("*") if path.is_file()}
        output = self.directory / "result.json"
        args = [str(self.baseline), str(self.mask), "--output-new", str(output)]
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(analysis.main(args), 0)
        self.assertEqual(json.loads(stdout.getvalue()), analysis.load(output))
        saved = output.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            analysis.main(args)
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(output.read_bytes(), saved)
        after = {str(path): path.read_bytes() for root in (self.baseline, self.mask) for path in root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_cli_output_inside_capsule_refused(self):
        output = self.mask / "new.json"
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            analysis.main([str(self.baseline), str(self.mask), "--output-new", str(output)])
        self.assertFalse(output.exists())

    def test_cli_incomplete_returns_json_and_nonzero(self):
        (self.mask / analysis.EVAL).unlink()
        output = self.directory / "incomplete.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(analysis.main([str(self.baseline), str(self.mask), "--output-new", str(output)]), 1)
        self.assert_invalid(analysis.load(output))


if __name__ == "__main__":
    unittest.main()
