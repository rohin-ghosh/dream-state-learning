import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import admission as rules
import daemon
import dispatch_once
import host
import probe_runtime as runtime
from store import Store, select


WORKER = Path(__file__).resolve().parent


def policy():
    return runtime.read(WORKER / "policy.json")


def entry(number=1, life="FRESH_R231"):
    bound = policy()
    journal = bound["supported_journals"].get(life, "a" * 32)
    checksum = hashlib.sha256(str(number).encode()).hexdigest()
    return dict(key=journal + ":" + checksum, journal_id=journal, life=life, record_index=1000 + number,
        record_sha256=checksum, sleep=number, optimizer_steps=48 * number, adapter_state_sha256="b" * 64,
        runtime_load=dict(index=172, sha256="c" * 64), checkpoint_status="JOINED_NOT_COPIED", evaluated=False)


def capsule(row):
    bound = policy()
    return dict(source_key=row["key"], job_id=rules.job_id(row), root=bound["future_job_root"] + "/" + rules.job_id(row), policy_sha256=rules.digest(bound),
        source_identity=dict(journal_id=row["journal_id"], absolute_sleep=row["sleep"], optimizer_steps=row["optimizer_steps"],
            sleep_complete_sha256=row["record_sha256"], adapter_state_sha256=row["adapter_state_sha256"]),
        battery=copy.deepcopy(rules.BATTERY), base_sha256=rules.BASE_SHA, status="CPU_SOURCE_READY_NOT_LOADED",
        freshness_eligible=True, parent_tokens=0, model_updates=0, source_context_loaded=False, optimizer_rng_loaded=False,
        source_manifest_sha256=rules.SOURCE_MANIFEST_SHA, source_file_count=103, lease_end_unix=rules.HARD_END,
        source_hard_end_unix=rules.HARD_END, config_sha256="d" * 64, freshness_sha256="e" * 64,
        bundle_evidence_sha256="f" * 64, runtime_manifest_sha256="0" * 64, verified_bundle=True,
        runtime_variant="QUEUE_V1_ORIGINAL_PROBE")


def observation(now=None):
    bound = policy()
    devices = [dict(physical=index, uuid="GPU-" + str(index), memory_used_mib=0, compute_pids=[]) for index in range(8)]
    for device in bound["role_devices"].values():
        devices[device["physical"]]["uuid"] = device["uuid"]
    return dict(observed_unix=time.time() if now is None else now, receiving_hostname=bound["receiving_hostname"],
        receiving_boot_id=bound["receiving_boot_id"], observer_boot_id="observer", uid=bound["expected_uid"],
        complete_process_scan=True, complete_attempt_scan=True, complete_claim_scan=True,
        processes=bound["protected_processes"], gpus=devices, claims=[], jobs=[])


def plan(row):
    now = time.time()
    return rules.proposal(row, capsule(row), policy(), observation(now), now)


class AdmissionTests(unittest.TestCase):
    def test_original_job_id_is_identical_and_binds_source(self):
        row = entry()
        identity = dict(journal_id=row["journal_id"], sleep_complete_sha256=row["record_sha256"],
            adapter_state_sha256=row["adapter_state_sha256"], battery=rules.BATTERY)
        self.assertEqual(rules.job_id(row), hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest())
        self.assertNotEqual(rules.job_id(row), rules.job_id(entry(2)))

    def test_known_sleep12_never_gets_new_job_id(self):
        row = dict(journal_id="038f85cbde5c4abfb749ea4d59da6897",
            record_sha256="64927d106eb5069d6a66fc9c61358966cf80a50b77924992d02a72c9221af2cf",
            adapter_state_sha256="c01b385ba9ed28447351b2344efed83fd32513bb3cb0c22012c62d09b7e372f4")
        self.assertEqual(rules.job_id(row), "465dedb4d06300e2a82046af61bd914f915a4ccbe588d5f05fb0616b90440ae7")

    def test_only_uuid_bound_two_seven_and_original_horizon(self):
        rules.validate_policy(policy())
        for change in ({"lease_end_unix": rules.HARD_END + 1}, {"max_runtime_seconds": 2401},
                {"max_concurrent_jobs": 2}, {"automatic_launch": True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                rules.validate_policy(dict(policy(), **change))
        for field in ("physical", "uuid"):
            changed = policy()
            changed["role_devices"]["judge"][field] = changed["role_devices"]["player"][field]
            with self.assertRaises(ValueError):
                rules.validate_policy(changed)

    def test_full_fresh_host_inventory_and_protected_handles_required(self):
        for changed in (dict(observation(100), observed_unix=69), dict(observation(100), observed_unix=101),
                dict(observation(100), receiving_boot_id="new"), dict(observation(100), uid=0),
                dict(observation(100), complete_attempt_scan=False), dict(observation(100), processes=[]),
                dict(observation(100), gpus=[])):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                rules.validate_observation(policy(), changed, 100)
        changed = observation(100)
        changed["processes"][0]["start_ticks"] = "9999"
        with self.assertRaisesRegex(ValueError, "protected"):
            rules.validate_observation(policy(), changed, 100)

    def test_live_or_allocated_gpu_is_never_displaced(self):
        for change in ({"memory_used_mib": 1}, {"compute_pids": [123]}):
            current = observation(100)
            current["gpus"][2].update(change)
            with self.assertRaisesRegex(ValueError, "occupied"):
                rules.lane_free(policy(), current, 100)

    def test_original_claim_and_unknown_external_job_block_lane(self):
        current = observation(100)
        current["claims"] = [dict(namespace=policy()["claims_namespace"], uuid=policy()["role_devices"]["judge"]["uuid"],
            job_id="other", hold_until_unix=130)]
        with self.assertRaisesRegex(ValueError, "claim"):
            rules.lane_free(policy(), current, 100)
        current["claims"] = []
        current["jobs"] = [dict(state="UNKNOWN", job_id="other")]
        with self.assertRaisesRegex(ValueError, "unreconciled"):
            rules.lane_free(policy(), current, 100)

    def test_source_battery_epoch_and_parent_visibility_do_not_change(self):
        row = entry()
        rules.validate_capsule(row, capsule(row), policy())
        for key, value in (("parent_tokens", 1), ("model_updates", 1), ("source_context_loaded", True),
                ("optimizer_rng_loaded", True), ("source_file_count", 102), ("freshness_eligible", False)):
            changed = capsule(row)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                rules.validate_capsule(row, changed, policy())
        for field, value in (("scenes", 4), ("seeds", [1, 2]), ("tokens_per_cell", 512), ("rule_digest", "other")):
            changed = capsule(row)
            changed["battery"][field] = value
            with self.assertRaisesRegex(ValueError, "battery"):
                rules.validate_capsule(row, changed, policy())

    def test_expired_lease_and_stale_free_check_rejected(self):
        with self.assertRaisesRegex(ValueError, "lease"):
            rules.lane_free(policy(), observation(rules.HARD_END), rules.HARD_END)
        with self.assertRaisesRegex(ValueError, "stale"):
            rules.proposal(entry(), capsule(entry()), policy(), observation(100), 131)

    def test_pending_roots_history_and_exposure_are_explicit(self):
        row = entry()
        self.assertEqual(rules.classify(entry(life="C2"), set(), {}, policy()), "PENDING_UNSUPPORTED_ROOT")
        self.assertEqual(rules.classify(dict(row, record_index=921), set(), {}, policy()), "PENDING_HISTORICAL_CAPTURE_NOT_SELECTED")
        self.assertEqual(rules.classify(row, set(), {}, policy()), "PENDING_CAPTURE_EXPOSURE_AND_RUNTIME_BINDING")
        self.assertEqual(rules.classify(dict(row, journal_id="new"), set(), {}, policy()), "PENDING_UNSUPPORTED_JOURNAL_EPOCH")
        self.assertEqual(rules.classify(row, {row["key"]}, {}, policy()), "ATTEMPT_RECORDED_NO_RETRY")

    def test_physical_confinement_rejects_other_gpu_exposure(self):
        proof = {str(index): dict(opened=index == 2) for index in range(8)}
        runtime.validate_confinement(2, proof, "same", "same")
        proof["4"]["opened"] = True
        with self.assertRaisesRegex(ValueError, "seven_denied"):
            runtime.validate_confinement(2, proof, "same", "same")

    def test_one_shot_route_retains_device_policy_and_deadline(self):
        config = dict(policy(), root="/root", job_id="a" * 64)
        for command in dispatch_once.commands(config, Path("/config"), "sha", Path("/launch"), "sha", 2500, 100):
            argv = command["argv"]
            self.assertEqual(argv[:3], ["sudo", "-n", "systemd-run"])
            self.assertIn("--property=DevicePolicy=closed", argv)
            self.assertIn("--property=RuntimeMaxSec=2400", argv)
            assigned = config["role_devices"][command["role"]]
            self.assertIn("--setenv=CUDA_VISIBLE_DEVICES=" + assigned["uuid"], argv)
            opens = [value for value in argv if value.startswith("--property=DeviceAllow=/dev/nvidia")
                and value.removeprefix("--property=DeviceAllow=/dev/nvidia").split()[0].isdigit()]
            self.assertEqual(opens, ["--property=DeviceAllow=/dev/nvidia" + str(assigned["physical"]) + " rw"])

    def test_platform_failure_is_terminal_without_retry(self):
        runner = Mock(return_value=Mock(returncode=1))
        with self.assertRaisesRegex(RuntimeError, "TERMINAL_NO_FALLBACK"):
            dispatch_once.submit(["never-executed"], runner=runner)
        runner.assert_called_once()


class StoreFixture:
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "state.sqlite"
        self.store = Store(self.path, policy())
        self.addCleanup(lambda: self.store.close())


class StoreTests(StoreFixture, unittest.TestCase):
    def test_every_age_dedup_no_latest_only(self):
        rows = [entry(number) for number in range(1, 20)]
        self.store.ingest(rows + [rows[0]], [])
        report = select(self.store, {row["key"]: capsule(row) for row in rows}, policy())
        self.assertEqual(report["retained"], 19)
        self.assertEqual(report["selected"]["sleep"], 1)

    def test_snapshot_shrink_or_epoch_edit_is_not_silently_accepted(self):
        self.store.ingest([entry(), entry(2)], [])
        for rows in ([entry()], [dict(entry(), runtime_load={}), entry(2)]):
            with self.assertRaises(ValueError):
                self.store.ingest(rows, [])
        self.assertEqual(len(self.store.entries()), 2)

    def test_duplicate_conflict_rolls_back_whole_import(self):
        with self.assertRaisesRegex(ValueError, "conflicting"):
            self.store.ingest([entry(), dict(entry(), sleep=99)], [])
        self.assertEqual(self.store.entries(), [])

    def test_intent_is_durable_and_serialized_across_connections(self):
        self.store.ingest([entry(), entry(2)], [])
        self.store.record_intent(plan(entry()))
        another = Store(self.path, policy())
        try:
            self.assertEqual(len(another.active()), 1)
            with self.assertRaisesRegex(ValueError, "serialized"):
                another.record_intent(plan(entry(2)))
        finally:
            another.close()

    def test_terminal_attempt_cannot_retry_or_be_reclassified(self):
        self.store.ingest([entry()], [])
        self.store.record_intent(plan(entry()))
        self.store.update_attempt(rules.job_id(entry()), "FAILED_NO_RETRY", dict(reason="denied"))
        with self.assertRaisesRegex(ValueError, "terminal"):
            self.store.update_attempt(rules.job_id(entry()), "RUNNING", {})
        self.assertIsNone(select(self.store, {entry()["key"]: capsule(entry())}, policy())["selected"])

    def test_fair_oldest_per_life_after_attempt(self):
        rows = [entry(), entry(2), entry(3, "R232_SIBLING_FROZEN")]
        self.store.ingest(rows, [])
        self.store.prior_attempt(rows[0]["key"], dict(reason="already_complete"))
        selected = select(self.store, {row["key"]: capsule(row) for row in rows}, policy())["selected"]
        self.assertEqual(selected["life"], "R232_SIBLING_FROZEN")

    def test_hash_chained_audit_detects_mutation(self):
        self.store.ingest([entry()], [])
        self.store.verify_events()
        self.store.db.execute("UPDATE events SET payload='{}' WHERE seq=1")
        with self.assertRaisesRegex(ValueError, "audit_chain"):
            self.store.verify_events()

    def test_review_rebind_does_not_extend_lease_or_erase_backlog(self):
        self.store.ingest([entry()], [])
        changed = policy()
        changed["protected_processes"][0]["pid"] += 1
        review = dict(old_policy_sha256=rules.digest(policy()), new_policy_sha256=rules.digest(changed),
            reviewed=True, source_freeze_sha256="a" * 64)
        self.store.pause("source_adoption")
        self.store.rebind(changed, review)
        self.assertIsNone(self.store.get_meta("pause"))
        self.assertEqual(len(self.store.entries()), 1)
        changed["lease_end_unix"] += 1
        with self.assertRaises(ValueError):
            self.store.rebind(changed, review)

    def test_active_job_must_reconcile_before_rebind(self):
        self.store.ingest([entry()], [])
        self.store.record_intent(plan(entry()))
        review = dict(old_policy_sha256=rules.digest(policy()), new_policy_sha256=rules.digest(policy()),
            reviewed=True, source_freeze_sha256="a" * 64)
        with self.assertRaisesRegex(ValueError, "reconcile"):
            self.store.rebind(policy(), review)

    def test_flock_rejects_duplicate_foreground(self):
        with daemon.singleton(self.path), self.assertRaises(BlockingIOError):
            with daemon.singleton(self.path):
                self.fail("duplicate singleton")


class EngineTests(StoreFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.host = Mock()
        self.host.observe.side_effect = observation
        self.host.launch.return_value = dict(status="DISPATCHED")
        self.queue = daemon.Queue(self.store, policy(), self.host)
        self.rows = [entry(), entry(2)]
        self.capsules = {row["key"]: capsule(row) for row in self.rows}

    def test_pending_source_observation_cannot_record_intent_or_launch(self):
        self.host.observe.side_effect = runtime.SourceEpochPending({"remaining_records": 2})
        with self.assertRaises(runtime.SourceEpochPending):
            self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.assertEqual(self.store.attempts(), [])
        self.assertIsNone(self.store.get_meta("pause"))
        self.host.launch.assert_not_called()

    def test_pending_capsule_source_cannot_record_intent_or_launch(self):
        self.host.verify_capsule.side_effect = runtime.SourceEpochPending({"remaining_records": 2})
        with patch("daemon.time.time", return_value=100), self.assertRaises(runtime.SourceEpochPending):
            self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.assertEqual(self.store.attempts(), [])
        self.assertIsNone(self.store.get_meta("pause"))
        self.host.launch.assert_not_called()

    def test_offline_check_never_calls_any_host_function(self):
        self.queue.cycle(self.rows, [], self.capsules)
        self.assertEqual(self.host.mock_calls, [])

    def test_executable_integration_persists_intent_before_one_shot(self):
        def launch(bound):
            self.assertEqual(self.store.active()[0]["status"], "INTENT")
            self.assertEqual(self.store.active()[0]["intent"], bound)
            return dict(status="DISPATCHED")
        self.host.launch.side_effect = launch
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.host.launch.assert_called_once()
        self.assertEqual(self.store.active()[0]["status"], "DISPATCHED")

    def test_slow_full_provenance_check_gets_fresh_host_observation_before_intent(self):
        clock = [100]
        self.host.observe.side_effect = lambda: observation(clock[0])
        self.host.verify_capsule.side_effect = lambda *_: clock.__setitem__(0, 240)
        with patch.object(daemon.time, "time", side_effect=lambda: clock[0]):
            self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.host.launch.assert_called_once()
        self.assertEqual(self.host.launch.call_args.args[0]["created_unix"], 240)

    def test_repeat_poll_or_restart_adopts_does_not_launch_again(self):
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.host.reconcile.return_value = dict(status="RUNNING")
        restarted = daemon.Queue(self.store, policy(), self.host)
        restarted.reconcile()
        restarted.cycle(self.rows, [], self.capsules, execute=True)
        self.host.launch.assert_called_once()
        self.assertEqual(self.store.active()[0]["status"], "RUNNING")

    def test_ambiguous_transport_or_platform_denial_is_no_retry(self):
        self.host.launch.side_effect = TimeoutError("unknown")
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.host.launch.assert_called_once()
        self.assertEqual(self.store.active()[0]["status"], "RECONCILING")
        self.assertIsNotNone(self.store.get_meta("pause"))

    def test_pause_required_is_not_clean_success_and_stops_new_admission(self):
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.host.reconcile.return_value = dict(status="COMPLETED_WITH_SCORING_SHORTFALL", pause_reason="unknown_not_zero")
        self.queue.reconcile()
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.host.launch.assert_called_once()
        self.assertEqual(self.store.get_meta("pause"), "unknown_not_zero")

    def test_completed_authenticated_shortfall_tombstones_source_but_allows_next_age(self):
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.host.reconcile.return_value = dict(status="COMPLETED_WITH_SCORING_SHORTFALL", pause_reason=None,
            verified_model_free_shortfall=True, probe_processes_absent=True)
        self.queue.reconcile()
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.assertIsNone(self.store.get_meta("pause"))
        self.assertEqual(self.host.launch.call_count, 2)
        self.assertEqual(self.host.launch.call_args.args[0]["source_key"], entry(2)["key"])

    def test_paused_queue_still_reconciles_existing_job(self):
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.store.pause("protected_changed")
        self.host.reconcile.return_value = dict(status="SUCCEEDED")
        self.queue.reconcile()
        self.assertEqual(self.store.active(), [])
        self.assertEqual(self.store.get_meta("pause"), "protected_changed")

    def test_existing_host_attempt_tombstone_prevents_replay(self):
        current = observation()
        current["jobs"] = [dict(job_id=rules.job_id(entry()), source_key=entry()["key"], state="COMPLETE")]
        self.host.observe.side_effect = None
        self.host.observe.return_value = current
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.assertEqual(self.host.launch.call_args.args[0]["source_key"], entry(2)["key"])

    def test_claim_wait_does_not_consume_or_discard_age(self):
        current = observation()
        current["gpus"][2]["compute_pids"] = [100]
        self.host.observe.side_effect = None
        self.host.observe.return_value = current
        report = self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.assertEqual(report["waiting_for_lane"], "lane_occupied_no_displacement")
        self.assertEqual(self.store.attempts(), [])
        self.host.launch.assert_not_called()

    def test_registered_capsule_cannot_be_replaced_or_deleted(self):
        self.queue.cycle(self.rows, [], self.capsules)
        with self.assertRaisesRegex(ValueError, "capsule_changed"):
            self.queue.cycle(self.rows, [], {})

    def test_reconciled_failed_job_does_not_become_unknown_external_block_forever(self):
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.host.reconcile.return_value = dict(status="FAILED_NO_RETRY", probe_processes_absent=True, deadline_expired=True)
        self.queue.reconcile()
        current = observation()
        current["jobs"] = [dict(job_id=rules.job_id(entry()), source_key=entry()["key"], state="UNKNOWN")]
        self.host.observe.side_effect = None
        self.host.observe.return_value = current
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.assertEqual(self.host.launch.call_count, 2)
        self.assertEqual(self.host.launch.call_args.args[0]["source_key"], entry(2)["key"])

    def test_old_capsules_stay_pending_after_reviewed_policy_rebind(self):
        changed = policy()
        changed["current_loaded"]["FRESH_R231"]["index"] += 1
        self.assertEqual(rules.classify(entry(), set(), self.capsules, changed), "PENDING_POLICY_REBIND_NEW_BUNDLE_REQUIRED")

    def test_legacy_battery_cut_match_is_tombstoned_without_inventing_journal(self):
        current = observation()
        current["jobs"] = [dict(job_id="legacy", source_key="legacy:battery", state="COMPLETE",
            source_cut_sha256s=[entry()["record_sha256"]])]
        self.host.observe.side_effect = None
        self.host.observe.return_value = current
        self.queue.cycle(self.rows, [], self.capsules, execute=True)
        self.assertEqual(self.host.launch.call_args.args[0]["source_key"], entry(2)["key"])


    def test_local_host_launch_invokes_exact_one_shot_once(self):
        with patch.object(host.subprocess, "run", return_value=Mock(returncode=0)) as runner:
            host.LocalHost(policy()).launch(plan(entry()))
        runner.assert_called_once()
        argv = runner.call_args.args[0]
        self.assertIn("--launch", argv)
        self.assertIn("--deadline", argv)
        self.assertTrue(argv[2].endswith("runtime/dispatch_once.py"))

    def test_activation_does_not_treat_template_or_shell_as_boot_ready(self):
        with self.assertRaisesRegex(ValueError, "not_activated"):
            daemon.activation(dict(reviewed=False, runtime_enabled=False), policy(), Path("missing"), 100)
        review = dict(reviewed=True, runtime_enabled=True, policy_sha256=rules.digest(policy()),
            route="ORIGINAL_GPU_HOST_TRANSIENT_CGROUP_ONE_SHOT_ONLY", expires_unix=99)
        with self.assertRaisesRegex(ValueError, "expired"):
            daemon.activation(review, policy(), Path("missing"), 100)


if __name__ == "__main__":
    unittest.main()
