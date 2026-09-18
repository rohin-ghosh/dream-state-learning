import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import call, patch

from gpu import astra_memory_mask_diagnostic as diagnostic


class MemoryMaskDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.root = self.directory / "run"
        self.source = self.directory / "original"
        self.root.mkdir()
        self.source.mkdir()
        self.adapter = self.root / "adapters/bank0/F_r16k16/across/sleep4/r8"
        self.tag = "bank0__F_r16k16__across__sleep4__r8"
        self.evaluation_path = self.root / "eval" / (self.tag + "__lam1.json")
        self.corpus = dict(sha="derived-corpus", items_sha="derived-items")
        self.counts = dict(items=12924, changed_masks=6720, changed_label_items=5376,
                           input_tokens_per_epoch=249995,
                           original_supervised_per_epoch=237071,
                           supervised_per_epoch=140975, removed_labels=96096,
                           boundary_straddles=5376, omitted_owner_prefix_tokens=5376,
                           truncated_items=0)
        self.write_json(self.root / diagnostic.CORPUS_PATH, self.corpus)
        self.write_json(self.source / diagnostic.CORPUS_PATH,
                        dict(sha="original-corpus", items_sha="original-items"))
        self.receipt = dict(
            status="PREPARED_NOT_TRAINED", destination=str(self.root),
            source=str(self.source), counts=self.counts,
            inputs={diagnostic.CORPUS_PATH: self.digest(self.root / diagnostic.CORPUS_PATH)},
            source_inputs={diagnostic.CORPUS_PATH: self.digest(self.source / diagnostic.CORPUS_PATH)})
        self.write_json(self.root / diagnostic.RECEIPT, self.receipt)
        self.meta = dict(
            rank=8, alpha=16, dropout=0.05, epochs=3, lr=1e-4, seed=2,
            bsz=4, steps=9693, total_steps=9693, n_items=12924,
            tokens=749985, supervised_tokens=422925, boundary_straddles=5376,
            truncated_items=0, measure_only=False, max_len=512,
            final_loss=1.05,
            corpus_sha=self.corpus["sha"], items_sha=self.corpus["items_sha"],
            model="Qwen/Qwen2.5-7B-Instruct",
            recipe="memory_dose_v1 (mirrors train_adapter.py v1)",
            targets=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            ordering="chronological", writer="occurrences", representation="frames",
            shuffled=False, tokenization="joint context+target (encode_item)",
            throughput=dict(grad_checkpoint=False))
        self.evaluation = dict(n_cues=1313, template_check=True,
                               abstain_check=dict(ok=True))
        self.run_patch = patch.object(diagnostic.subprocess, "run")
        self.run = self.run_patch.start()
        self.addCleanup(self.run_patch.stop)
        self.run.side_effect = self.fake_stage
        self.free_patch = patch.object(diagnostic, "check_free",
                                       side_effect=AssertionError("GPU inspection forbidden"))
        self.free_patch.start()
        self.addCleanup(self.free_patch.stop)
        self.worker_patch = patch.object(diagnostic.supervisor, "run_worker",
                                         side_effect=AssertionError("worker launch forbidden"))
        self.worker_patch.start()
        self.addCleanup(self.worker_patch.stop)

    @staticmethod
    def write_json(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def fake_stage(self, arguments, **kwargs):
        stage = arguments[3]
        if stage == "train":
            self.adapter.mkdir(parents=True)
            (self.adapter / "DONE").write_text("ok\n")
            self.write_json(self.adapter / "train_meta.json", self.meta)
        elif stage == "evaluate":
            self.write_json(self.evaluation_path, self.evaluation)
        elif stage == "report":
            self.write_json(self.root / "report/report.json", dict(fixture_only=True))
        else:
            self.fail("unexpected subprocess stage: " + stage)
        return subprocess.CompletedProcess(arguments, 0)

    def test_validate_fit_accepts_matching_derived_dose_without_mutation(self):
        before = copy.deepcopy((self.meta, self.corpus, self.receipt))
        diagnostic.validate_fit(self.meta, self.corpus, self.receipt)
        self.assertEqual((self.meta, self.corpus, self.receipt), before)

    def test_validate_fit_rejects_dose_mask_hash_and_configuration_drift(self):
        mutations = dict(rank=16, alpha=8, dropout=0.0, epochs=1, lr=3e-5,
                         seed=0, bsz=8, steps=9692, total_steps=100,
                         n_items=12923, tokens=749984, supervised_tokens=711213,
                         boundary_straddles=1, truncated_items=1, measure_only=True,
                         corpus_sha="original-corpus", items_sha="original-items")
        for field, value in mutations.items():
            with self.subTest(field=field):
                metadata = copy.deepcopy(self.meta)
                metadata[field] = value
                with self.assertRaises(ValueError):
                    diagnostic.validate_fit(metadata, self.corpus, self.receipt)

    def test_validate_fit_refuses_missing_identity_or_count_fields(self):
        for field in ("steps", "supervised_tokens", "corpus_sha", "items_sha"):
            with self.subTest(field=field):
                metadata = copy.deepcopy(self.meta)
                del metadata[field]
                with self.assertRaises(ValueError):
                    diagnostic.validate_fit(metadata, self.corpus, self.receipt)

    def test_validate_fit_refuses_checkpointing(self):
        for value in (True, None, 0):
            with self.subTest(value=value):
                metadata = copy.deepcopy(self.meta)
                metadata["throughput"]["grad_checkpoint"] = value
                with self.assertRaises(ValueError):
                    diagnostic.validate_fit(metadata, self.corpus, self.receipt)

    def test_validate_fit_refuses_receipt_boundary_accounting_disagreement(self):
        for field in ("boundary_straddles", "truncated_items"):
            expected = self.counts[field]
            for receipt_count, fit_count in ((expected + 1, expected),
                                              (expected, expected + 1)):
                with self.subTest(field=field, receipt_count=receipt_count,
                                  fit_count=fit_count):
                    receipt = copy.deepcopy(self.receipt)
                    metadata = copy.deepcopy(self.meta)
                    receipt["counts"][field] = receipt_count
                    metadata[field] = fit_count
                    with self.assertRaises(ValueError):
                        diagnostic.validate_fit(metadata, self.corpus, receipt)

    def test_validate_fit_refuses_zero_or_epoch_scaled_straddle_count(self):
        for value in (0, 5375, 5377, 3 * 5376):
            with self.subTest(boundary_straddles=value):
                metadata = copy.deepcopy(self.meta)
                metadata["boundary_straddles"] = value
                with self.assertRaises(ValueError):
                    diagnostic.validate_fit(metadata, self.corpus, self.receipt)

    def test_validate_fit_refuses_nonfinite_final_loss(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(final_loss=value):
                metadata = copy.deepcopy(self.meta)
                metadata["final_loss"] = value
                with self.assertRaisesRegex(ValueError, "nonfinite final loss"):
                    diagnostic.validate_fit(metadata, self.corpus, self.receipt)

    def test_validate_fit_refuses_model_recipe_and_target_module_changes(self):
        mutations = dict(model="other/base", recipe="other-recipe",
                         targets=["q_proj"], max_len=128,
                         ordering="content", writer="dedup", representation="short",
                         shuffled=True, tokenization="separately tokenized")
        for field, value in mutations.items():
            with self.subTest(field=field):
                metadata = copy.deepcopy(self.meta)
                metadata[field] = value
                with self.assertRaises(ValueError):
                    diagnostic.validate_fit(metadata, self.corpus, self.receipt)

    def test_verify_inputs_checks_both_roots_without_mutation(self):
        paths = [self.root / diagnostic.RECEIPT, self.root / diagnostic.CORPUS_PATH,
                 self.source / diagnostic.CORPUS_PATH]
        before = {str(path): path.read_bytes() for path in paths}
        self.assertEqual(diagnostic.verify_inputs(self.root), self.receipt)
        self.assertEqual({str(path): path.read_bytes() for path in paths}, before)
        self.run.assert_not_called()

    def test_verify_inputs_refuses_changed_original_and_derived_bytes(self):
        for directory in (self.source, self.root):
            with self.subTest(directory=directory):
                path = directory / diagnostic.CORPUS_PATH
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                with self.assertRaisesRegex(ValueError, "changed input"):
                    diagnostic.verify_inputs(self.root)
                path.write_bytes(original)
        self.run.assert_not_called()

    def test_verify_inputs_refuses_wrong_receipt_status_or_destination(self):
        for field, value in (("status", "TRAINED"), ("destination", str(self.source))):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt)
                receipt[field] = value
                self.write_json(self.root / diagnostic.RECEIPT, receipt)
                with self.assertRaisesRegex(ValueError, "wrong preparation"):
                    diagnostic.verify_inputs(self.root)

    def test_run_stages_exact_train_evaluate_report_wiring(self):
        with patch.object(diagnostic, "verify_inputs", wraps=diagnostic.verify_inputs) as verify:
            diagnostic.run_stages(self.root)
        prefix = [sys.executable, "-B", str(diagnostic.SOURCE / "organism_v6/memory_dose.py")]
        self.assertEqual(self.run.call_args_list, [
            call(prefix + ["train", "--run-dir", str(self.root), "--corpus",
                           str(self.root / diagnostic.CORPUS_PATH), "--out", str(self.adapter),
                           "--model", "hf", "--rank", "8", "--epochs", "3", "--lr", "1e-4",
                           "--seed", "2", "--no-reuse"], check=True),
            call(prefix + ["evaluate", "--run-dir", str(self.root), "--bank", "0",
                           "--adapter", str(self.adapter), "--tag", self.tag, "--model", "hf",
                           "--lambdas", "1", "--adjacent-subset", "4", "--batch-size", "16",
                           "--seed", "0", "--cell", "F_r16k16", "--arm", "across",
                           "--sleep", "4", "--rank", "8"], check=True),
            call(prefix + ["report", "--run-dir", str(self.root), "--seed", "0"], check=True)])
        self.assertEqual(verify.call_args_list, [call(self.root), call(self.root)])

    def test_run_stages_refuses_existing_adapter_without_subprocess(self):
        self.adapter.mkdir(parents=True)
        sentinel = self.adapter / "sentinel"
        sentinel.write_bytes(b"preserve")
        with self.assertRaisesRegex(ValueError, "adapter already exists"):
            diagnostic.run_stages(self.root)
        self.run.assert_not_called()
        self.assertEqual(sentinel.read_bytes(), b"preserve")

    def test_run_stages_refuses_stale_eval_without_subprocess(self):
        self.evaluation_path.parent.mkdir()
        self.evaluation_path.write_bytes(b"preserve-existing-eval")
        with self.assertRaises(ValueError):
            diagnostic.run_stages(self.root)
        self.run.assert_not_called()
        self.assertEqual(self.evaluation_path.read_bytes(), b"preserve-existing-eval")

    def test_run_stages_refuses_stale_report_without_subprocess(self):
        report = self.root / "report/report.json"
        report.parent.mkdir()
        report.write_bytes(b"preserve-existing-report")
        with self.assertRaises(ValueError):
            diagnostic.run_stages(self.root)
        self.run.assert_not_called()
        self.assertEqual(report.read_bytes(), b"preserve-existing-report")

    def test_run_stages_checks_source_before_training(self):
        (self.source / diagnostic.CORPUS_PATH).write_text("changed")
        with self.assertRaisesRegex(ValueError, "changed input"):
            diagnostic.run_stages(self.root)
        self.run.assert_not_called()

    def test_run_stages_checks_source_again_after_report(self):
        def change_after_report(arguments, **kwargs):
            result = self.fake_stage(arguments, **kwargs)
            if arguments[3] == "report":
                (self.source / diagnostic.CORPUS_PATH).write_text("changed")
            return result

        self.run.side_effect = change_after_report
        with self.assertRaisesRegex(ValueError, "changed input"):
            diagnostic.run_stages(self.root)
        self.assertEqual(self.run.call_count, 3)

    def test_run_stages_stops_after_failed_train(self):
        self.run.side_effect = subprocess.CalledProcessError(1, ["mock-train"])
        with self.assertRaises(subprocess.CalledProcessError):
            diagnostic.run_stages(self.root)
        self.assertEqual(self.run.call_count, 1)

    def test_run_stages_stops_without_fit_done(self):
        self.run.side_effect = None
        with self.assertRaisesRegex(ValueError, "missing fit completion"):
            diagnostic.run_stages(self.root)
        self.assertEqual(self.run.call_count, 1)

    def test_run_stages_stops_before_eval_on_invalid_fit(self):
        self.meta["supervised_tokens"] = 711213
        with self.assertRaises(ValueError):
            diagnostic.run_stages(self.root)
        self.assertEqual(self.run.call_count, 1)

    def test_run_stages_stops_after_failed_evaluate(self):
        def fail_evaluate(arguments, **kwargs):
            if arguments[3] == "evaluate":
                raise subprocess.CalledProcessError(1, arguments)
            return self.fake_stage(arguments, **kwargs)

        self.run.side_effect = fail_evaluate
        with self.assertRaises(subprocess.CalledProcessError):
            diagnostic.run_stages(self.root)
        self.assertEqual(self.run.call_count, 2)

    def test_run_stages_stops_on_incomplete_eval(self):
        self.evaluation["n_cues"] = 1312
        with self.assertRaisesRegex(ValueError, "incomplete native"):
            diagnostic.run_stages(self.root)
        self.assertEqual(self.run.call_count, 2)

    def test_run_stages_stops_on_template_mismatch(self):
        self.evaluation["template_check"] = False
        with self.assertRaisesRegex(ValueError, "incomplete native"):
            diagnostic.run_stages(self.root)
        self.assertEqual(self.run.call_count, 2)

    def test_run_stages_stops_on_abstain_token_failure(self):
        self.evaluation["abstain_check"]["ok"] = False
        with self.assertRaisesRegex(ValueError, "incomplete native"):
            diagnostic.run_stages(self.root)
        self.assertEqual(self.run.call_count, 2)

    def test_write_new_refuses_overwrite(self):
        path = self.root / "result.json"
        diagnostic.write_new(path, dict(original=True))
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            diagnostic.write_new(path, dict(original=False))
        self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
