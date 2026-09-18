"""Partial synthetic capture fixtures only: never native outcomes or model calls."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_c0_capture_inspect as inspector
import test_astra_pcfl_zero_fit_analyze as synthetic

audit = inspector.audit


def write(root, name, value):
    (root / name).write_bytes(audit.canonical(value) + b"\n")


class PartialCaptureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_UNFINALIZED_C0_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data, self.outer = self.root / "diagnostic", self.root / "outer"
        self.data.mkdir()
        self.outer.mkdir()
        self.manifest = {"schema": audit.driver.SCHEMA, "output_dir": "/SYNTHETIC_ORIGINAL/diagnostic",
                         "wall_seconds": 100, "device_seconds": 100, "plan": {"roots": []},
                         "test_only": False, "fits": 0, "updates": 0, "full_v22_release": False}
        self.report = {"gpu_uuid": "GPU-SYNTHETIC", "started_monotonic": 10, "wall_seconds_through_close": 5}
        write(self.data, "manifest.json", audit.driver._seal(self.manifest))
        write(self.data, "report.json", audit.driver._seal(self.report))
        self.manifest_hash = audit.Archive(self.data).inventory["manifest.json"]["sha256"]
        for name in inspector.CAPTURE_FILES:
            write(self.outer, name, {"synthetic_fixture_only": True})
        self.identity = {"pid": 1234, "pgid": 1234, "sid": 1234, "uid": 123, "boot_id": "synthetic", "starttime": 99}
        write(self.outer, "context.json", {"schema": audit.OUTER, "manifest_file_sha256": self.manifest_hash,
              "output_dir": self.manifest["output_dir"], "entry_monotonic": 8, "deadline_monotonic": 108})
        write(self.outer, "worker_start.json", {"identity": self.identity, "manifest_file_sha256": self.manifest_hash,
              "gpu_uuid": self.report["gpu_uuid"], "spawn_started_monotonic": 9})
        write(self.outer, "worker_exit.json", {"identity": self.identity, "returncode": 0, "ended_monotonic": 16})
        write(self.outer, "worker_wait.json", {"value": 0})
        write(self.outer, "worker_release.json", {"identity": self.identity, "owned_group_released": True, "events": []})
        write(self.outer, "post_worker_gpu.json", {"value": {"empty": True}})
        write(self.outer, "post_worker_cvd.json", {"value": {"device_unreserved": None,
              "reservation_check_status": "PASS_WITH_EXPLICIT_NON_WORKER_SERVICE_EXCEPTIONS", "complete_cvd_visibility": False}})
        self.blocked = {"clear": False, "reservation_check_status": "BLOCKED", "complete_cvd_visibility": False,
                        "unresolved": [{"pid": 5678, "error_type": "PermissionError", "error": "SYNTHETIC unreadable environ"}],
                        "owners": [], "approved_unreadable_services": [{"pid": 9876}]}
        write(self.outer, "finalize_claim.json", {"started_monotonic": 21, "retry": False})
        write(self.outer, "final_queue.json", {"started_monotonic": 22, "ended_monotonic": 23, "value": {"matched": True}})
        write(self.outer, "final_cvd.json", {"started_monotonic": 24, "ended_monotonic": 25, "value": self.blocked})
        write(self.outer, "finalize_failure.json", {"type": inspector.native.ActorError.__name__, "error": "CVD owner remains; release Main holder before finalization"})
        self.recapture()

    def recapture(self):
        inventory = audit.Archive(self.data).inventory
        manifest, report = audit.Archive(self.data).read("manifest.json"), audit.Archive(self.data).read("report.json")
        captured = {"schema": audit.OUTER + "/captured", "status": "CAPTURED_AWAITING_RESERVATION_RELEASE",
                    "manifest_sha256": manifest["sha256"], "report_sha256": report["sha256"],
                    "report_file_sha256": inventory["report.json"]["sha256"], "output_inventory": inventory,
                    "outer_files": {name: audit.driver._file_hash(self.outer / name) for name in inspector.CAPTURE_FILES},
                    "elapsed_seconds": 12, "fits": 0, "updates": 0, "finalized": False,
                    "worker_group_released": True, "gpu_compute_vacant": True, "reservation_released": None,
                    "reservation_check_status": "PASS_WITH_EXPLICIT_NON_WORKER_SERVICE_EXCEPTIONS", "complete_cvd_visibility": False}
        write(self.outer, "capture_complete.json", captured)
        self.capture_hash = audit.driver._file_hash(self.outer / "capture_complete.json")

    def change(self, root, name, update):
        value = json.loads((root / name).read_bytes())
        update(value)
        write(root, name, value)

    def check(self):
        return inspector.capture_lineage(audit.Archive(self.data), audit.Archive(self.outer), self.manifest_hash, self.capture_hash)

    def arguments(self, output):
        return ["--diagnostic", str(self.data), "--outer", str(self.outer), "--manifest-sha256", self.manifest_hash,
                "--capture-sha256", self.capture_hash, "--output", str(output)]

    def test_partial_lineage_keeps_failure_and_visibility_without_release_claim(self):
        before = audit.Archive(self.outer).inventory
        failure = self.check()[2]
        self.assertEqual(failure["observation"], self.blocked)
        self.assertEqual(failure["failed_observation"], "final_cvd.json")
        self.assertIsNone(failure["capture_visibility"]["device_unreserved"])
        self.assertEqual(audit.Archive(self.outer).snapshot(), before)

    def test_failure_type_matches_actual_outer_require_exception(self):
        message = "CVD owner remains; release Main holder before finalization"
        try:
            inspector.native.require(False, message)
        except inspector.native.ActorError as error:
            self.change(self.outer, "finalize_failure.json", lambda value: value.update(type=type(error).__name__, error=str(error)))
        self.check()
        self.change(self.outer, "finalize_failure.json", lambda value: value.update(type="ValueError"))
        with self.assertRaisesRegex(ValueError, "actual CVD finalization failure"):
            self.check()

    def test_second_cvd_failure_requires_prior_clear_and_gpu_vacancy(self):
        self.change(self.outer, "final_cvd.json", lambda value: value.update(value={"clear": True, "owners": []}))
        write(self.outer, "final_gpu.json", {"started_monotonic": 26, "ended_monotonic": 27, "value": {"empty": True}})
        write(self.outer, "final_cvd_after_gpu.json", {"started_monotonic": 28, "ended_monotonic": 29, "value": self.blocked})
        self.change(self.outer, "finalize_failure.json", lambda value: value.update(error="late reservation/group appeared"))
        self.assertEqual(self.check()[2]["failed_observation"], "final_cvd_after_gpu.json")
        self.change(self.outer, "final_gpu.json", lambda value: value.update(value={"empty": False}))
        with self.assertRaisesRegex(ValueError, "prior finalization observation"):
            self.check()

    def test_independent_file_pins_not_internal_seals(self):
        for attribute in ("manifest_hash", "capture_hash"):
            with self.subTest(attribute=attribute):
                original = getattr(self, attribute)
                setattr(self, attribute, "0" * 64)
                with self.assertRaisesRegex(ValueError, "byte pin"):
                    self.check()
                setattr(self, attribute, original)

    def test_capture_bytes_cannot_be_replaced_by_self_seal(self):
        self.change(self.outer, "capture_complete.json", lambda value: value.update(sha256=audit.digest(value)))
        with self.assertRaisesRegex(ValueError, "capture byte pin"):
            self.check()

    def test_added_or_changed_diagnostic_file_rejected(self):
        write(self.data, "task_000.json", {"synthetic": True})
        with self.assertRaisesRegex(ValueError, "captured diagnostic inventory"):
            self.check()

    def test_captured_outer_bytes_cannot_change(self):
        self.change(self.outer, "worker_exit.json", lambda value: value.update(returncode=1))
        with self.assertRaisesRegex(ValueError, "capture receipt byte pin"):
            self.check()

    def test_resealed_capture_still_checks_worker_context_and_clocks(self):
        cases = [("worker_exit.json", "returncode", True), ("worker_wait.json", "value", 1),
                 ("worker_release.json", "owned_group_released", False), ("worker_release.json", "identity", {}),
                 ("worker_start.json", "manifest_file_sha256", "wrong"), ("worker_start.json", "gpu_uuid", "wrong"),
                 ("context.json", "manifest_file_sha256", "wrong"), ("context.json", "output_dir", "/wrong"),
                 ("context.json", "deadline_monotonic", 24), ("context.json", "entry_monotonic", 11),
                 ("worker_exit.json", "ended_monotonic", 14)]
        for name, key, value in cases:
            with self.subTest(name=name, key=key):
                original = (self.outer / name).read_bytes()
                self.change(self.outer, name, lambda record: record.update({key: value}))
                self.recapture()
                with self.assertRaises(ValueError):
                    self.check()
                (self.outer / name).write_bytes(original)
                self.recapture()

    def test_rebound_inventory_cannot_hide_bad_report_seal(self):
        self.change(self.data, "report.json", lambda value: value.update(gpu_uuid="changed"))
        self.recapture()
        with self.assertRaisesRegex(ValueError, "seal drift"):
            self.check()

    def test_no_success_retry_or_unbound_outer_evidence(self):
        for name in ("collection.json", "final.json", "release_attestation.json", "release_receipt.json",
                     "controller_failure.json", "finalize_retry.json", "unbound.json"):
            with self.subTest(name=name):
                write(self.outer, name, {})
                with self.assertRaisesRegex(ValueError, "unfinalized outer inventory"):
                    self.check()
                (self.outer / name).unlink()

    def test_failure_must_match_observed_phase_not_just_filename(self):
        for key, value in (("type", "RuntimeError"), ("error", "invented failure")):
            with self.subTest(key=key):
                original = (self.outer / "finalize_failure.json").read_bytes()
                self.change(self.outer, "finalize_failure.json", lambda record: record.update({key: value}))
                with self.assertRaisesRegex(ValueError, "actual CVD finalization failure"):
                    self.check()
                (self.outer / "finalize_failure.json").write_bytes(original)

    def test_clear_scan_empty_unresolved_and_wrong_pid_types_rejected(self):
        cases = [{**self.blocked, "clear": True}, {**self.blocked, "complete_cvd_visibility": True},
                 {**self.blocked, "unresolved": []}, {**self.blocked, "unresolved": [{"pid": True, "error_type": "PermissionError"}]},
                 {**self.blocked, "unresolved": [{"pid": 5678, "error_type": "FileNotFoundError"}]}]
        for value in cases:
            with self.subTest(value=value):
                self.change(self.outer, "final_cvd.json", lambda record: record.update(value=value))
                with self.assertRaises(ValueError):
                    self.check()

    def test_retry_and_out_of_order_clock_rejected(self):
        for update in ({"retry": True}, {"started_monotonic": 19}, {"started_monotonic": float("inf")}):
            with self.subTest(update=update):
                original = (self.outer / "finalize_claim.json").read_bytes()
                with self.assertRaises(ValueError):
                    self.change(self.outer, "finalize_claim.json", lambda value: value.update(update))
                    self.check()
                (self.outer / "finalize_claim.json").write_bytes(original)

    def test_missing_failure_never_treated_as_success(self):
        (self.outer / "finalize_failure.json").unlink()
        with self.assertRaisesRegex(ValueError, "unfinalized outer inventory"):
            self.check()

    def test_live_path_rejected_even_with_rebound_capture(self):
        self.manifest["output_dir"] = str(self.data)
        write(self.data, "manifest.json", audit.driver._seal(self.manifest))
        self.manifest_hash = audit.driver._file_hash(self.data / "manifest.json")
        self.change(self.outer, "context.json", lambda value: value.update(manifest_file_sha256=self.manifest_hash, output_dir=self.manifest["output_dir"]))
        self.recapture()
        with self.assertRaisesRegex(ValueError, "relocate"):
            self.check()

    def test_relocated_sibling_with_same_parent_is_allowed(self):
        self.manifest["output_dir"] = str(self.root / "original")
        write(self.data, "manifest.json", audit.driver._seal(self.manifest))
        self.manifest_hash = audit.driver._file_hash(self.data / "manifest.json")
        self.change(self.outer, "context.json", lambda value: value.update(manifest_file_sha256=self.manifest_hash, output_dir=self.manifest["output_dir"]))
        self.change(self.outer, "worker_start.json", lambda value: value.update(manifest_file_sha256=self.manifest_hash))
        self.recapture()
        self.check()

    def test_rebound_capture_cannot_overclaim_scope_seals_or_visibility(self):
        cases = {"finalized": True, "fits": 1, "updates": True, "worker_group_released": False,
                 "gpu_compute_vacant": False, "report_file_sha256": "wrong", "report_sha256": "wrong",
                 "manifest_sha256": "wrong", "reservation_released": True, "complete_cvd_visibility": True}
        for key, value in cases.items():
            with self.subTest(key=key):
                self.change(self.outer, "capture_complete.json", lambda record: record.update({key: value}))
                self.capture_hash = audit.driver._file_hash(self.outer / "capture_complete.json")
                with self.assertRaises(ValueError):
                    self.check()
                self.recapture()

    def test_symlink_and_duplicate_json_rejected(self):
        (self.outer / "alias").symlink_to(self.outer / "context.json")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.check()
        (self.outer / "alias").unlink()
        (self.outer / "finalize_claim.json").write_text('{"retry":false,"retry":true}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON"):
            self.check()

    def test_partial_fixture_cannot_pass_800_task_inspection_or_write_output(self):
        output = self.root / "must_not_exist"
        with self.assertRaisesRegex(ValueError, "four excluded roots"):
            inspector.main(self.arguments(output))
        self.assertFalse(output.exists())

    def test_frozen_analyzer_still_requires_collection(self):
        with self.assertRaises(KeyError):
            audit.analyze(self.data, self.outer, manifest_sha256=self.manifest_hash, collection_sha256="0" * 64)

    def test_fresh_only_output_and_no_archive_overlap(self):
        for output in (self.root, self.data / "inspection", self.outer / "inspection"):
            with self.subTest(output=output), patch.object(inspector, "inspect") as inspect:
                with self.assertRaises(ValueError):
                    inspector.main(self.arguments(output))
                inspect.assert_not_called()

    def test_writer_labels_injected_synthetic_result_without_finalization_files(self):
        result = {"schema": "SYNTHETIC_WRITER_TEST_ONLY", "diagnostic_usable": False, "finalization_failed": True,
                  "full_v22_release": False, "counts": {"synthetic": {"correct": 0, "denominator": 2}}, "scope": inspector.SCOPE}
        output = self.root / "inspection"
        before = audit.Archive(self.outer).inventory
        with patch.object(inspector, "inspect", return_value=copy.deepcopy(result)), patch.object(audit, "analyze", side_effect=AssertionError("full analyzer must not be bypassed")):
            inspector.main(self.arguments(output))
        self.assertEqual(json.loads((output / "inspection.json").read_bytes()), result)
        self.assertEqual(sorted(path.name for path in output.iterdir()), ["inspection.json", "inspection.md"])
        self.assertIn("UNFINALIZED", (output / "inspection.md").read_text())
        self.assertEqual(audit.Archive(self.outer).snapshot(), before)
        with self.assertRaises(ValueError):
            inspector.main(self.arguments(output))


class PartialReplayTests(unittest.TestCase):
    def setUp(self):
        self.fixture = synthetic.SyntheticReplayTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def replay(self, outputs):
        replay = self.fixture.fixture(outputs)
        row = {**replay._task(self.fixture.task), "execution": "SCORED"}
        self.fixture.manifest["plan"] = {"tasks": [self.fixture.task]}
        write(self.fixture.root, "task_000.json", row)
        return {"results": [row]}

    def check(self, report):
        return inspector.replay_rows(audit.Archive(self.fixture.root), self.fixture.manifest, report)

    def test_independent_raw_replay_rejects_task_score_tampering(self):
        report = self.replay([self.fixture.answer])
        self.fixture.mutate("task_000.json", lambda value: value.update(success=False))
        with self.assertRaisesRegex(ValueError, "raw scorer/task disagreement"):
            self.check(report)

    def test_independent_raw_replay_rejects_report_score_tampering(self):
        report = self.replay(["SYNTHETIC invalid route"])
        report["results"][0]["success"] = True
        with self.assertRaisesRegex(ValueError, "report task ordering/scores"):
            self.check(report)

    def test_task_plan_and_measurement_drift_rejected(self):
        report = self.replay([self.fixture.answer])
        self.fixture.task["seed"] += 1
        with self.assertRaisesRegex(ValueError, "task request/transcript"):
            self.check(report)
        self.fixture.task["seed"] -= 1
        self.fixture.manifest["measurements"]["measurements"][0]["token_ids"] = [99]
        with self.assertRaises(ValueError):
            self.check(report)

    def test_raw_receipt_tampering_rejected_even_with_new_inventory(self):
        report = self.replay([self.fixture.answer])
        self.fixture.mutate("actor/call_0000.raw.json", lambda value: value["raw"].update(text="changed"))
        with self.assertRaises(ValueError):
            self.check(report)

    def test_partial_replay_cannot_shrink_fixed_denominators(self):
        request = next(iter(self.fixture.task["queries"]))
        report = self.replay([request, self.fixture.answer])
        with self.assertRaisesRegex(ValueError, "fixed denominator changed"):
            self.check(report)

    def test_partial_counter_math_only_with_explicit_test_panel_substitution(self):
        report = self.replay(["SYNTHETIC invalid route"])
        report.update(panels={"SYNTHETIC_PARTIAL_NOT_RELEASE": {"passed": False}}, thresholds_passed=False,
                      actor_attempts=1, actor_responses=1)
        with patch.object(audit.driver, "_panels", return_value=report["panels"]):
            replay, panels, groups, lengths = self.check(report)
        self.assertEqual((groups["all"]["denominator"], groups["all"]["correct"], groups["all"]["invalid_final_syntax"]), (1, 0, 1))
        self.assertEqual((groups["delayed"]["prompt_tokens"], groups["all"]["output_tokens"]), (3, 1))
        self.assertEqual(replay.stats["generation_wall_seconds"], 0.5)
        self.assertEqual(len(lengths), 1)
        self.assertEqual(panels, report["panels"])
        self.assertEqual(len(groups), 6)
        self.assertEqual(json.loads(audit.canonical(groups)), groups)
        self.assertTrue(all(type(counts) is dict for counts in groups.values()))


if __name__ == "__main__":
    unittest.main()
