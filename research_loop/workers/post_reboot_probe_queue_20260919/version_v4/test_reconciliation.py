import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import admission as rules
import dispatch_once
import host
import probe_runtime as runtime
import receipts
import shortfall
from test_queue import entry, observation, plan, policy


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def fixture(root, unknown=False):
    row = entry()
    config = dict(root=str(root), condition="R233_FIXTURE", job_id=rules.job_id(row), queue_policy=policy(),
        role_devices=policy()["role_devices"], source_identity=dict(adapter_state_sha256=row["adapter_state_sha256"]))
    output = root / "players/R233_FIXTURE"
    config_path = root / "runtime/JOB_CONFIG.json"
    put(config_path, config)
    bound = dict(plan(row), root=str(root), config_sha256=runtime.sha(config_path), deadline_unix=300, hold_until_unix=330)
    put(root / "runtime/LAUNCH.json", dict(job_id=bound["job_id"], config_sha256=bound["config_sha256"], deadline_unix=300))
    for role, pid in (("judge", 100), ("player", 101)):
        physical = config["role_devices"][role]["physical"]
        proof = {str(index): dict(opened=index == physical) for index in range(8)}
        put(root / (role + "_DEVICE_PROOF.json"), proof)
        put(root / "runtime" / (role + "_START_INTENT.json"), dict(pid=pid, unix=95, role=role, config_sha256=bound["config_sha256"],
            deadline_unix=300, boot_id=policy()["receiving_boot_id"], confinement=proof,
            process_identity=dict(pid=pid, start_ticks="1234", argv_sha256="e" * 64)))
    model = dict(base_sha256=rules.BASE_SHA, adapter_state_sha256=row["adapter_state_sha256"], all_parameters_frozen=True)
    put(output / "LOADED.json", dict(pid=101, unix=100, identity=dict(model, optimizer_created=False), parent_tokens=0,
        snapshot_context_used=False, source_parent_text_loaded=False, actual_visible_device=policy()["role_devices"]["player"]["uuid"]))
    put(root / "JUDGE_LOADED.json", dict(pid=100, unix=98, top_k=50, reference_count=64, existing_games_modified=False))
    put(root / "JUDGE_EXIT.json", dict(pid=100, unix=201))
    scenes = ["scene_" + str(number) for number in range(3)]
    put(root / "GAME_MANIFEST.json", dict(contests=[dict(contest_id=scene) for scene in scenes]))
    cells = []
    for scene in scenes:
        for seed in (23201, 23202):
            events = []
            directory = output / f"{scene}_{seed}"
            for ordinal in range(8):
                prompt = [dict(role="user", content=f"{scene} {seed} {ordinal}")]
                generation = dict(messages=prompt, raw=f"caption {scene} {seed} {ordinal}", token_ids=[5] * 128, prompt_tokens=8)
                origin = dict(request_sha256=rules.digest(prompt), response_sha256=rules.digest(generation),
                    text_sha256=hashlib.sha256(generation["raw"].encode()).hexdigest(), stage="THINK" if ordinal % 2 == 0 else "ACT",
                    generated_tokens_before=ordinal * 128, generated_tokens_after=(ordinal + 1) * 128)
                request = dict(identity=dict(condition=config["condition"], seed=seed, contest_id=scene), raw=generation["raw"],
                    raw_sha256=origin["text_sha256"], origin=origin)
                outcome = dict(ok=True, rank=20, accepted=True, raw_score=0.5)
                if unknown and scene == scenes[0] and seed == 23201 and ordinal == 0:
                    outcome = dict(ok=False, error="provider_error", pause_required=True, status="error")
                result = dict(request_sha256=rules.digest(request), results=[dict(result=outcome)])
                stem = f"{scene}_{seed}_{ordinal:04d}"
                put(root / "queue" / (stem + ".request.json"), request)
                put(root / "queue" / (stem + ".result.json"), result)
                event = dict(origin=origin, actual_generated_tokens=128, requested_max_new_tokens=min(
                    128 if ordinal % 2 == 0 else 256, 1024 - ordinal * 128), score=result)
                put(directory / f"{ordinal:04d}.json", dict(request=prompt, generation=generation, event=event))
                events.append(event)
            cell = dict(contest_id=scene, seed=seed, status="COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET", generated_tokens=1024,
                budget=1024, no_updates=True, parent_tokens=0, learn_or_other_reply_tokens=0, events=events)
            put(directory / "RESULT.json", cell)
            cells.append(cell)
    put(output / "COMPLETE.json", dict(condition=config["condition"], unix=200, unchanged_identity=model, cells=cells, actual_generated_tokens=6144))
    return config, bound


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_exact_budget_uses_actual_token_ids_not_duplicate_nested_events(self):
        config, bound = fixture(self.root)
        result = receipts.completion(config, bound["deadline_unix"])
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["generated_tokens"], 6144)
        self.assertEqual(result["canonical_requests"], 48)

    def test_provider_error_is_unknown_and_pauses_future_jobs_not_zero(self):
        config, bound = fixture(self.root, unknown=True)
        result = receipts.completion(config, bound["deadline_unix"])
        self.assertEqual(result["status"], "COMPLETED_WITH_SCORING_SHORTFALL")
        self.assertEqual(result["unscored_or_pause_required"], 1)
        self.assertFalse(result["unknown_is_zero"])
        self.assertFalse(result["clean_all_scored"])
        self.assertFalse(result["metrics_published_to_parents"])
        self.assertEqual(result["pause_reason"], "UNCLASSIFIED_SCORING_FAULT_REVIEW")

    def test_verified_model_free_too_long_input_does_not_freeze_later_ages(self):
        config, bound = fixture(self.root, unknown=True)
        diagnostic = dict(all_verified=True, model_loaded=False, scoring_called=False)
        result = receipts.completion(config, bound["deadline_unix"], diagnose=lambda *_: diagnostic)
        self.assertEqual(result["status"], "COMPLETED_WITH_SCORING_SHORTFALL")
        self.assertIsNone(result["pause_reason"])
        self.assertTrue(result["later_independent_age_admissible_after_claims_clear"])
        self.assertFalse(result["clean_all_scored"])
        self.assertFalse(result["unknown_is_zero"])

    def test_only_exact_no_judgment_provider_length_guard_is_narrowly_allowed(self):
        outcome = dict(ok=False, error=dict(code="provider_error"), pause_required=True, status="error")
        self.assertTrue(shortfall.guard_classification(outcome, 621, 512))
        for changed, tokens, limit in ((outcome, 511, 512), (outcome, 621, 1024),
                (dict(outcome, accepted=False), 621, 512), (dict(outcome, error=dict(code="rate_limit")), 621, 512),
                (dict(outcome, raw_score=0), 621, 512), (dict(outcome, submission_id="committed"), 621, 512)):
            self.assertFalse(shortfall.guard_classification(changed, tokens, limit))

    def test_shortfall_diagnosis_error_still_pauses(self):
        config, bound = fixture(self.root, unknown=True)
        result = receipts.completion(config, bound["deadline_unix"], diagnose=Mock(side_effect=ValueError("wrong_tokenizer")))
        self.assertEqual(result["pause_reason"], "UNCLASSIFIED_SCORING_FAULT_REVIEW")

    def test_incomplete_actual_token_budget_fails_even_if_total_claims_6144(self):
        config, bound = fixture(self.root)
        path = next((self.root / "players/R233_FIXTURE").glob("*/0000.json"))
        changed = runtime.read(path)
        changed["generation"]["token_ids"].pop()
        put(path, changed)
        with self.assertRaisesRegex(ValueError, "actual_generated_tokens"):
            receipts.completion(config, bound["deadline_unix"])

    def test_duplicate_cells_and_changed_final_adapter_rejected(self):
        config, bound = fixture(self.root)
        path = self.root / "players/R233_FIXTURE/COMPLETE.json"
        original = runtime.read(path)
        for changed in (dict(original, cells=original["cells"][:5] + original["cells"][:1]),
                dict(original, unchanged_identity={})):
            put(path, changed)
            with self.assertRaises(ValueError):
                receipts.completion(config, bound["deadline_unix"])

    def test_canonical_result_is_joined_to_saved_generation_feedback(self):
        config, bound = fixture(self.root)
        path = next((self.root / "queue").glob("*.result.json"))
        changed = runtime.read(path)
        changed["results"][0]["result"]["accepted"] = False
        put(path, changed)
        with self.assertRaisesRegex(ValueError, "canonical_result"):
            receipts.completion(config, bound["deadline_unix"])

    def test_actual_load_and_other_gpu_open_proofs_required(self):
        config, bound = fixture(self.root)
        path = self.root / "player_DEVICE_PROOF.json"
        changed = runtime.read(path)
        changed["4"]["opened"] = True
        put(path, changed)
        with self.assertRaisesRegex(ValueError, "seven_denied"):
            receipts.completion(config, bound["deadline_unix"])

    def test_nonfinite_or_absent_raw_scores_never_become_valid(self):
        for score in (None, float("nan"), float("inf")):
            rows = [dict(outcome=dict(ok=True, accepted=True, rank=1, raw_score=score))]
            self.assertEqual(receipts.scoring_shortfall(rows), rows)


class HostTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.config, self.plan = fixture(self.root)
        self.host = host.LocalHost(policy())
        for target, replacement in (("host.Path.read_text", Mock(return_value=policy()["receiving_boot_id"])),
                ("host.time.time", Mock(return_value=250)), ("host.runtime.verify_protected", Mock()),
                ("host.LocalHost.source_guard", Mock()), ("host.runtime.verify_bundle", Mock()),
                ("host.runtime.gpu_inventory", Mock(return_value=observation()["gpus"])),
                ("host.runtime.process_identity", Mock(side_effect=FileNotFoundError))):
            patched = patch(target, replacement)
            patched.start()
            self.addCleanup(patched.stop)

    def test_completed_matching_job_reconciles_without_launch_or_signals(self):
        with patch.object(host.subprocess, "run") as launcher:
            result = self.host.reconcile(self.plan)
        self.assertEqual(result["status"], "SUCCEEDED")
        launcher.assert_not_called()

    def test_boot_change_is_terminal_no_retry_not_pid_adoption(self):
        with patch.object(host.Path, "read_text", return_value="new-boot"):
            result = self.host.reconcile(self.plan)
        self.assertEqual(result["status"], "INTERRUPTED_NO_RETRY")

    def test_pid_reuse_or_argv_change_is_not_adopted(self):
        with patch.object(runtime, "process_identity", return_value=dict(pid=100, start_ticks="999", argv_sha256="wrong")):
            with self.assertRaisesRegex(ValueError, "pid_reuse"):
                self.host.reconcile(self.plan)

    def test_crash_after_db_intent_before_remote_launch_never_resubmits(self):
        (self.root / "runtime/LAUNCH.json").unlink()
        before = self.host.reconcile(self.plan)
        self.assertEqual(before["status"], "RECONCILING")
        with patch.object(host.time, "time", return_value=331):
            after = self.host.reconcile(self.plan)
        self.assertEqual(after["status"], "UNKNOWN_NO_RETRY")

    def test_protected_adoption_pauses_even_after_budget_complete(self):
        with patch.object(runtime, "verify_protected", side_effect=ValueError("changed")):
            result = self.host.reconcile(self.plan)
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertIn("REVIEW_REBIND", result["pause_reason"])

    def test_active_job_still_alive_after_deadline_never_releases_slot(self):
        def identity(pid):
            return dict(pid=pid, start_ticks="1234", argv_sha256="e" * 64)
        with patch.object(runtime, "process_identity", side_effect=identity), patch.object(host.time, "time", return_value=331):
            result = self.host.reconcile(self.plan)
        self.assertEqual(result["status"], "RECONCILING")
        self.assertEqual(len(result["exact_live_processes"]), 2)


class SourceEpochTests(unittest.TestCase):
    def test_original_multi_condition_battery_is_retained_not_misparsed_as_one_shot(self):
        with tempfile.TemporaryDirectory() as directory:
            bound = dict(policy(), attempt_scan_parent=directory)
            root = Path(directory) / "orch_r232_age_probe_20260918"
            put(root / "sources/CAPTURE.json", dict(sources=[dict(sleep_complete_sha256="a" * 64), dict(sleep_complete_sha256="b" * 64)]))
            for condition in ("base", "young", "old"):
                put(root / "players" / condition / "LOADED.json", {})
                put(root / "players" / condition / "COMPLETE.json", {})
            put(root / "JUDGE_EXIT.json", {})
            with patch.object(host, "attempt_roots", return_value=[root]):
                rows = host.previous_attempts(bound)
            self.assertEqual(rows[0]["state"], "COMPLETE")
            self.assertEqual(len(rows[0]["source_cut_sha256s"]), 2)
            (root / "players/old/COMPLETE.json").unlink()
            with patch.object(host, "attempt_roots", return_value=[root]):
                self.assertEqual(host.previous_attempts(bound)[0]["state"], "UNKNOWN")

    def test_new_loaded_epoch_requires_explicit_rebind_not_self_adaptation(self):
        with tempfile.TemporaryDirectory() as directory:
            bound = policy()
            bound["source_roots"]["FRESH_R231"] = directory
            records = Path(directory) / "stream/records"
            initial = dict(journal_id=bound["supported_journals"]["FRESH_R231"], index=1, kind="LOADED",
                document=dict(base_sha256=rules.BASE_SHA))
            initial["sha256"] = rules.digest(initial)
            anchor = dict(index=1, sha256=initial["sha256"])
            bound["initial_loaded"]["FRESH_R231"] = anchor
            bound["current_loaded"]["FRESH_R231"] = anchor
            put(records / "00000000000000000001.json", initial)
            self.assertEqual(runtime.verify_source_epoch(bound, "FRESH_R231"), anchor)
            changed = dict(journal_id=initial["journal_id"], index=2, kind="LOADED",
                document=dict(base_sha256=rules.BASE_SHA), previous_sha256=initial["sha256"])
            changed["sha256"] = rules.digest(changed)
            put(records / "00000000000000000002.json", changed)
            with self.assertRaisesRegex(ValueError, "explicit_review_rebind"):
                runtime.verify_source_epoch(bound, "FRESH_R231", anchor)

    def test_changed_runtime_or_extra_source_files_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            put(root / "source/item.json", dict(value=1))
            put(root / "SOURCE_MANIFEST.json", {"item.json": runtime.sha(root / "source/item.json")})
            runtime.verify_source_closure(root)
            put(root / "source/extra.json", {})
            with self.assertRaisesRegex(ValueError, "closure"):
                runtime.verify_source_closure(root)


class DispatchFailureTests(unittest.TestCase):
    def test_partial_dispatch_has_durable_no_retry_markers_and_original_uuid_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "runtime").mkdir()
            config = dict(policy(), root=str(root), worker_root=str(root.parent), claims_namespace=str(root / "claims"),
                condition="R233_FIXTURE", job_id=rules.job_id(entry()))
            argv = ["dispatch_once.py", "--config", str(root / "runtime/JOB_CONFIG.json"), "--config-sha256", "a" * 64,
                "--deadline", "2500", "--launch"]
            with patch.object(sys, "argv", argv), patch.object(runtime, "load_config", return_value=config), \
                    patch.object(runtime, "verify_bundle", return_value=root), patch.object(runtime, "verify_live_source"), \
                    patch.object(runtime, "verify_protected"), patch.object(runtime, "gpu_inventory", return_value=observation()["gpus"]), \
                    patch.object(dispatch_once.time, "time", return_value=100), \
                    patch.object(dispatch_once, "submit", side_effect=[None, RuntimeError("denied")]) as submit:
                with self.assertRaisesRegex(RuntimeError, "denied"):
                    dispatch_once.main()
                self.assertEqual(submit.call_count, 2)
                self.assertTrue((root / "runtime/LAUNCH.json").exists())
                failure = runtime.read(root / "runtime/DISPATCH_FAILED.json")
                self.assertEqual(failure["launched"][0]["role"], "judge")
                with self.assertRaisesRegex(ValueError, "never_replayed"):
                    dispatch_once.main()
                self.assertEqual(submit.call_count, 2)
            for assigned in config["role_devices"].values():
                claim = runtime.read(root / "claims" / (assigned["uuid"] + ".json"))
                self.assertEqual(claim["hold_until_unix"], 2530)


if __name__ == "__main__":
    unittest.main()
