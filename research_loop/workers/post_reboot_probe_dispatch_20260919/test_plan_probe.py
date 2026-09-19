import copy
import unittest

import plan_probe


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.source = dict(source_name="FRESH", journal_id="journal", sleep_complete_sha256="complete",
            adapter_state_sha256="adapter", sleep_complete_index=20, absolute_sleep=2,
            captured_unix=100, copy_hashes_verified=True, canonical_complete_verified=True,
            eligibility="PENDING_SOURCE_AND_INHERITED_EXPOSURE_AUDIT", queued="/queue/source", life_root="/life")
        self.entry = dict(journal_id="journal", record_sha256="complete", record_index=20, sleep=2)
        self.policy = dict(optional_historical_enabled=False,
            sources=[dict(life="FRESH", journal_id="journal", source_frontier=10)])
        self.inventory = dict(read_only=True, unix=100, captures=[self.source], prior_jobs=[],
            battery=copy.deepcopy(plan_probe.BATTERY), lease_end_unix=plan_probe.LEASE_END,
            lease_boundary_unix=plan_probe.LEASE_BOUNDARY, gpus=[dict(physical=4, memory_used_mib=14000,
            compute_pids=[499900])], prepare_script="/frozen/prepare.py", source_root="/frozen",
            original_root="/original", lease_runner_present_in_frozen_source=False)

    def result(self, now=101):
        return plan_probe.plan(self.inventory, [self.entry], self.policy, now)

    def test_coherent_enrollment_never_becomes_gpu_eligibility(self):
        result = self.result()
        self.assertIsNotNone(result["source_preparation_candidate"])
        self.assertEqual(result["admitted_gpu_jobs"], [])
        self.assertIsNone(result["launch_command"])
        self.assertFalse(result["gpu_execution_performed"])

    def test_busy_scorer_devices_are_never_replaced(self):
        self.assertIn("EXISTING_LEASE_RUNNER_GPU_4_5_OCCUPIED_DO_NOT_DISPLACE", self.result()["blockers"])

    def test_empty_other_gpu_is_not_an_authorized_replacement(self):
        self.inventory["gpus"].append(dict(physical=2, memory_used_mib=0, compute_pids=[]))
        self.assertIsNone(self.result()["launch_command"])

    def test_complete_source_is_excluded_despite_queue_pending_label(self):
        self.inventory["prior_jobs"] = [self.source]
        self.assertIsNone(self.result()["source_preparation_candidate"])

    def test_failed_or_partial_attempt_is_not_automatically_retried(self):
        self.inventory["prior_jobs"] = [dict(self.source, status="FAILED_OR_PARTIAL")]
        self.assertIsNone(self.result()["source_preparation_candidate"])

    def test_historical_captures_not_added_to_backlog_execution(self):
        self.policy["sources"][0]["source_frontier"] = 20
        self.assertIsNone(self.result()["source_preparation_candidate"])

    def test_source_tampering_and_unjoined_records_block_selection(self):
        for field in ("copy_hashes_verified", "canonical_complete_verified"):
            with self.subTest(field=field):
                self.source[field] = False
                self.assertIsNone(self.result()["source_preparation_candidate"])
                self.source[field] = True

    def test_changed_scientific_contract_or_lease_is_rejected(self):
        self.inventory["battery"]["total_generated_tokens"] = 7000
        with self.assertRaises(ValueError):
            self.result()
        self.inventory["battery"] = copy.deepcopy(plan_probe.BATTERY)
        self.inventory["lease_end_unix"] += 1
        with self.assertRaises(ValueError):
            self.result()

    def test_stale_inventory_and_expired_lease_block_readiness(self):
        self.assertIn("INVENTORY_STALE_RECHECK_HOST_AND_GPU_OCCUPANCY", self.result(500)["blockers"])
        self.assertIn("SOURCE_LEASE_EXPIRED_OR_INSUFFICIENT_MARGIN", self.result(plan_probe.LEASE_END)["blockers"])

    def test_job_identity_is_stable_and_retains_distinct_native_ages(self):
        self.assertEqual(plan_probe.job_id(self.source), plan_probe.job_id(dict(self.source)))
        self.assertNotEqual(plan_probe.job_id(self.source), plan_probe.job_id(dict(self.source, sleep_complete_sha256="other")))

    def test_duplicate_capture_and_wrong_enrollment_age_fail_closed(self):
        self.inventory["captures"].append(dict(self.source))
        with self.assertRaises(ValueError):
            self.result()
        self.inventory["captures"].pop()
        self.entry["sleep"] = 3
        self.assertIsNone(self.result()["source_preparation_candidate"])


if __name__ == "__main__":
    unittest.main()
