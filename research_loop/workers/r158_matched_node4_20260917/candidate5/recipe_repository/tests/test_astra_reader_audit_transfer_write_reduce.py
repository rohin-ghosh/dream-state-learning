"""Pure transfer-wrapper checks; optional replay of locally retained references."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from organism_v6 import experienced_event_fresh_reader_audit as audit
from tools import astra_reader_audit_transfer_write_reduce as reduce
from tests.test_astra_fresh_reader_cycle_reduce import schedule


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "gpu_artifacts_local/astra_fresh_reader_cycle_terminal_20260914_attempt2"
MATCHED = ROOT / "gpu_artifacts_local/astra_reader_audit_matched_replay_terminal_20260914_attempt1/extracted"


class TransferReducerTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def test_actual_duplicated_OFF_material_100_updates_210_masks(self):
        masks, losses = schedule("SELECTED")
        for loss in losses:
            actual, reference = reduce.fresh.indexes(loss["update"], "SELECTED", [1, 1])
            active = sum(len(masks[index]["target_ids"]) for index in actual)
            original = sum(len(masks[index]["target_ids"]) for index in reference)
            loss.update(row_indexes=actual, reference_row_indexes=reference, actual_label_count=active,
                        active_label_count=active, reference_label_count=original, original_label_count=original,
                        loss_scale=active / original, actual_mean_loss=0.5, loss=0.5 * active / original)
        summary = reduce.fresh.audit_schedule(masks, losses, "SELECTED", [1, 1])
        self.assertEqual(summary["new_fact_presentations"], [0, 200, 0, 0])
        self.assertEqual(summary["old_bank_presentations"], [36, 32, 32])
        self.assertEqual(list(summary["budgets"].values()), [100, 100, 38, 62, 200])
        self.assertEqual(summary["reference_supervised_tokens"], reduce.fresh.audit_schedule(*schedule("UNIFORM"), "UNIFORM", reduce.SFT_CHOICES)["reference_supervised_tokens"])
        changed = deepcopy(losses)
        changed[0]["row_indexes"][2] = 178
        with self.assertRaises(ValueError):
            reduce.fresh.audit_schedule(masks, changed, "SELECTED", [1, 1])

    def test_pending_has_no_invented_scores(self):
        report = reduce.reduce(self.root)
        self.assertEqual(report["status"], "PARTIAL_EVIDENCE")
        self.assertEqual(report["pending"], ["train", "after"])
        self.assertNotIn("reference_outcomes", report)

    def test_CPU_prepare_failure_is_not_classified_as_fit_failure(self):
        path = self.root / "prepare_failure.json"
        receipt = dict(phase="prepare", fits=0, model_calls=0, status="FAILED", error="tuple/list comparison")
        self.write(path, receipt)
        report = reduce.reduce(self.root, prepare_failure=path)
        self.assertEqual(report["failed"], [])
        self.assertEqual(report["engineering_prepare_failure"]["classification"], "PRE_MODEL_CPU_PREPARE_FAILURE_NOT_FIT")
        receipt["fits"] = 1
        self.write(path, receipt)
        with self.assertRaises(ValueError):
            reduce.reduce(self.root, prepare_failure=path)

    def test_FAILED_takes_precedence_and_retains_raw_panels(self):
        self.write(self.root / "after/RESULT.json", dict(status="COMPLETE"))
        self.write(self.root / "after/FAILED.json", dict(status="FAILED", error="inference failure", panels={"raw": "retained"}))
        report = reduce.reduce(self.root)
        self.assertEqual(report["stages"]["after"]["status"], "FAILED")
        self.assertEqual(report["stages"]["after"]["partial_raw_panels"], {"raw": "retained"})

    def test_wrong_reference_receipt_hash_rejected(self):
        path = self.root / "reference.json"
        self.write(path, dict(status="COMPLETE"))
        with self.assertRaisesRegex(ValueError, "verified_SEQ245_receipt_hash"):
            reduce.reference_check(self.root, path)

    def terminal_fixture(self, phase):
        binding = dict(fresh_source={"initial_adapter_state_sha256": reduce.INITIAL_STATE})
        directory = self.root / phase
        request = dict(schema=reduce.SCHEMA, phase=phase, arm=reduce.ARM, arguments={}, started_unix=100,
                       entry_sha256=reduce.digest(ROOT / "gpu/astra_reader_audit_transfer_write.py"), on_policy=False, parent_present=False)
        result = dict(request, status="COMPLETE", finished_unix=200, source=binding, frozen_base_unchanged=True,
                      audit_policy=reduce.fresh.AUDIT_POLICY,
                      audit_helper_sha256=reduce.digest(ROOT / "organism_v6/experienced_event_fresh_reader_audit.py"))
        kernel = {name: reduce.digest(ROOT / path) for name, path in reduce.KERNEL.items()}
        if phase == "train":
            result.update(trainer_sha256=kernel["trainer"], code_provenance={name: dict(sha256=value) for name, value in kernel.items()},
                          adapter_state_after="written")
        else:
            result.update(training_result_sha256=reduce.digest(self.root / "train/RESULT.json"),
                          loaded_adapter_state_sha256="written", adapter_state_after="written")
        for name, value in (("REQUEST.json", request), ("RESULT.json", result), ("INPUTS.json", binding)):
            self.write(directory / name, value)
        return result, kernel

    def test_saved_state_reload_is_checked_before_readout(self):
        unused, kernel = self.terminal_fixture("train")
        after, unused = self.terminal_fixture("after")
        self.write(self.root / "reference/collect/COLLECTION.json", {"captured": True})
        self.write(self.root / "reference_receipt.json", {})
        stage = dict(panels={}, classifier=dict(summary={}), actual_audit=dict(summary={}, chosen_source_indexes=[]))
        uniform = dict(masks_sha256="same", rows_sha256="rows", reference_supervised_tokens=8)
        reference = dict(stages={"SELECTED/after": stage, "UNIFORM/after": stage, "UNIFORM/train": uniform})
        training = dict(uniform, new_fact_presentations=[0, 200, 0, 0])
        with patch.object(reduce, "reference_check", return_value=reference), patch.object(reduce, "binding_check", return_value=dict(kernel_hashes=kernel)), \
                patch.object(reduce.fresh, "training", return_value=training), patch.object(reduce.fresh, "readout", return_value=stage) as readout:
            options = (self.root, SimpleNamespace(root=ROOT), self.root / "reference", self.root / "reference_receipt.json", self.root, {}, {})
            self.assertEqual(reduce.reduce(*options)["status"], "COMPLETE")
            self.assertEqual(readout.call_count, 1)
            after["loaded_adapter_state_sha256"] = "other"
            self.write(self.root / "after/RESULT.json", after)
            result = reduce.reduce(*options)
            self.assertIn("saved_unchanged_after_reload", result["stages"]["after"]["error"])
            self.assertEqual(readout.call_count, 1)

    @unittest.skipUnless((REFERENCE / "SEQ245_independent_reduction_20260914.json").is_file(), "local SEQ245 capsule unavailable")
    def test_actual_SEQ245_reference_hashes_and_parent(self):
        report = reduce.reference_check(REFERENCE / "extracted", REFERENCE / "SEQ245_independent_reduction_20260914.json")
        self.assertEqual(report["pair"]["initial_state"], reduce.INITIAL_STATE)
        self.assertEqual(report["before_pointers"], reduce.SFT_CHOICES)

    @unittest.skipUnless((MATCHED / "AUDIT_SFT/RESULT.json").is_file() and (REFERENCE / "extracted/before/RESULT.json").is_file(), "local SEQ245/246 captures unavailable")
    def test_actual_matched_auditor_prompts_calls_choices_and_drift(self):
        for arm, expected in (("AUDIT_SFT", reduce.SFT_CHOICES), ("AUDIT_LOSS_OFF", reduce.OFF_CHOICES)):
            directory = MATCHED / arm
            result = reduce.read(directory / "RESULT.json")
            names = ["RESULT.json", "INPUTS.json", "CASES.json", "before_AUDIT.json", "SELECTED_after_AUDIT.json"]
            names += ["CALL_%03d.json" % index for index in range(14)]
            binding = dict(files={name: reduce.digest(directory / name) for name in names},
                           evaluated_auditor=result["evaluated_auditor"], stimuli=result["stimuli"])
            summary = reduce.replay_check(directory, binding, arm, REFERENCE / "extracted", SimpleNamespace(audit=audit))
            self.assertEqual(summary["before_choices"], expected)
            binding["files"]["CALL_000.json"] = "incorrect"
            with self.assertRaises(ValueError):
                reduce.replay_check(directory, binding, arm, REFERENCE / "extracted", SimpleNamespace(audit=audit))

    @unittest.skipUnless((MATCHED / "AUDIT_SFT/RESULT.json").is_file() and (REFERENCE / "SEQ245_independent_reduction_20260914.json").is_file(), "local reference capsules unavailable")
    def test_actual_shared_writer_binding_and_changed_parent_rejected(self):
        root = REFERENCE / "extracted"
        reference = reduce.reference_check(root, REFERENCE / "SEQ245_independent_reduction_20260914.json")
        binding = dict(fresh_source=reduce.read(root / "before/RESULT.json")["source"],
                       collection_result_sha256=reference["stages"]["collect"]["result_sha256"],
                       before_result_sha256=reference["stages"]["before"]["result_sha256"],
                       selected_source_indexes=[1, 1], raw_source_choices=dict(AUDIT_SFT=reduce.SFT_CHOICES, AUDIT_LOSS_OFF=reduce.OFF_CHOICES),
                       common_lesson_rehearsal=True, selector_is_writer_on_policy=False,
                       kernel_hashes={name: reduce.digest(ROOT / path) for name, path in reduce.KERNEL.items()},
                       reused_references={}, transfer_sources={})
        for arm in reduce.fresh.ARMS:
            directory = root / arm / "train"
            result = reduce.read(directory / "RESULT.json")
            binding["reused_references"][arm] = dict(training_result_sha256=reduce.digest(directory / "RESULT.json"),
                adapter_state_after=result["adapter_state_after"], masks_sha256=reduce.digest(directory / "MASKS.json"),
                training_rows_sha256=reduce.digest(directory / "TRAINING_ROWS.json"),
                adapter_provenance_sha256=reduce.digest(directory / "ADAPTER_PROVENANCE.json"),
                reference_supervised_tokens=result["reference_supervised_tokens"])
        rows = reduce.read(root / "UNIFORM/train/TRAINING_ROWS.json")
        binding["training_rows_sha256"] = reduce.sha256(reduce.fresh.adult.canonical(rows) + b"\n").hexdigest()
        for arm in ("AUDIT_SFT", "AUDIT_LOSS_OFF"):
            directory = MATCHED / arm
            result = reduce.read(directory / "RESULT.json")
            names = ["RESULT.json", "INPUTS.json", "CASES.json", "before_AUDIT.json", "SELECTED_after_AUDIT.json"]
            names += ["CALL_%03d.json" % index for index in range(14)]
            binding["transfer_sources"][arm] = dict(files={name: reduce.digest(directory / name) for name in names},
                evaluated_auditor=result["evaluated_auditor"], stimuli=result["stimuli"])
        runtime = SimpleNamespace(root=ROOT, audit=audit)
        self.assertEqual(reduce.binding_check(binding, root, MATCHED, reference, runtime)["initial_writer_state"], reduce.INITIAL_STATE)
        binding["fresh_source"]["initial_adapter_state_sha256"] = "changed"
        with self.assertRaises(ValueError):
            reduce.binding_check(binding, root, MATCHED, reference, runtime)


if __name__ == "__main__":
    unittest.main()
