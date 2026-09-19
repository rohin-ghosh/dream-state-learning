"""Immutable rebind and deadline tests; GPU dispatch and source epoch scans are forbidden."""

from contextlib import ExitStack
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import admission as rules
import daemon
import dispatch_once
import activate_reviewed
import probe_runtime as runtime
import rebind_runtime as rebind
from test_queue import entry, policy


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))


class RebindTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.worker = Path(self.directory.name)
        self.root = self.worker / "jobs" / rules.job_id(entry())
        self.legacy = self.root / "runtime"
        self.legacy.mkdir(parents=True)
        (self.legacy / "admission.py").write_text("legacy = True\n")
        self.claims = self.worker / "claims"
        self.claims.mkdir()
        (self.claims / "DISPATCH.lock").touch()
        self.old = dict(root=str(self.root), runtime_files={"admission.py": runtime.sha(self.legacy / "admission.py")},
            job_id=self.root.name, condition="R233_FIXTURE", queue_policy=policy(), role_devices=policy()["role_devices"],
            claims_namespace=str(self.claims), input_files={"original-science": "a" * 64}, source_runtime_epoch={"index": 74},
            source_identity=dict(journal_id=entry()["journal_id"], sleep_complete_sha256=entry()["record_sha256"]),
            battery=rules.BATTERY, lease_end_unix=rules.HARD_END)
        put(self.legacy / "JOB_CONFIG.json", self.old)
        put(self.legacy / "BUNDLE_EVIDENCE.json", {"legacy": True})
        self.cap = dict(job_id=self.root.name, source_key=entry()["key"], root=str(self.root),
            policy_sha256=rules.digest(policy()),
            config_sha256=runtime.sha(self.legacy / "JOB_CONFIG.json"),
            bundle_evidence_sha256=runtime.sha(self.legacy / "BUNDLE_EVIDENCE.json"),
            runtime_manifest_sha256=rules.digest(self.old["runtime_files"]), battery=rules.BATTERY)
        put(self.legacy / "CAPSULE.json", self.cap)
        self.registry = self.worker / "inputs/capsules.json"
        put(self.registry, {"capsules": [self.cap]})
        put(self.root / "ENROLLMENT_ENTRY.json", entry())
        put(self.root / "SOURCE_MANIFEST.json", {str(index): "a" * 64 for index in range(103)})
        self.original = {str(path.relative_to(self.worker)): path.read_bytes() for path in self.worker.rglob("*") if path.is_file()}

    def replacement(self):
        return rebind.replacement_config(self.old, self.registry, {"probe_runtime.py": "e" * 64})

    def isolated_stage(self):
        with ExitStack() as stack:
            for target in ("daemon.verify_freeze", "runtime.load_config", "runtime.validate_config", "runtime.verify_protected",
                           "runtime.verify_bundle", "rules.validate_capsule"):
                parent, name = target.split(".")
                module = {"daemon": daemon, "runtime": runtime, "rules": rules}[parent]
                stack.enter_context(patch.object(module, name, return_value=self.old if name == "load_config" else None))
            stack.enter_context(patch.object(rebind, "previous_attempts", return_value=[]))
            source = stack.enter_context(patch.object(runtime, "verify_live_source", side_effect=AssertionError("duplicate cold scan")))
            dispatch = stack.enter_context(patch.object(dispatch_once, "submit", side_effect=AssertionError("GPU dispatch forbidden")))
            result = rebind.stage(self.root, self.cap["config_sha256"], runtime.sha(self.registry), self.worker / "seal", "f" * 64)
            source.assert_not_called()
            dispatch.assert_not_called()
            return result

    def test_only_sibling_runtime_changes_not_source_or_job(self):
        new = self.replacement()
        self.assertEqual(new["job_id"], self.old["job_id"])
        self.assertEqual(new["runtime_directory"], str(self.root / "runtime_v4"))
        for field in set(self.old) - {"runtime_files"}:
            self.assertEqual(new[field], self.old[field])

    def test_changed_science_budget_epoch_or_deadline_rejected(self):
        for field in ("input_files", "battery", "source_runtime_epoch", "lease_end_unix", "job_id", "condition"):
            with self.subTest(field=field):
                new = self.replacement()
                new[field] = "changed"
                with self.assertRaisesRegex(ValueError, "preserve_all_science"):
                    runtime.verify_runtime_rebind(new)

    def test_legacy_runtime_bytes_must_remain_exact(self):
        new = self.replacement()
        (self.legacy / "admission.py").write_text("changed = True\n")
        with self.assertRaisesRegex(ValueError, "predecessor_runtime_changed"):
            runtime.verify_runtime_rebind(new)

    def test_predecessor_registry_is_not_mutable(self):
        new = self.replacement()
        put(self.registry, {"capsules": []})
        with self.assertRaisesRegex(ValueError, "immutable_predecessor"):
            runtime.verify_runtime_rebind(new)

    def test_sibling_symlink_or_arbitrary_runtime_rejected(self):
        new = self.replacement()
        new["runtime_directory"] = str(self.worker / "other_runtime")
        with self.assertRaisesRegex(ValueError, "exact_sibling"):
            runtime.runtime_directory(new)
        new["runtime_directory"] = str(self.root / "runtime_v4")
        (self.root / "runtime_v4").symlink_to(self.legacy)
        with self.assertRaisesRegex(ValueError, "symlink"):
            runtime.runtime_directory(new)

    def test_old_or_new_unknown_start_prevents_rebind(self):
        for directory in (self.legacy, self.root / "runtime_v4"):
            directory.mkdir(exist_ok=True)
            path = directory / "player_START_INTENT.json"
            put(path, {"unknown": True})
            with self.assertRaisesRegex(ValueError, "never_replayed"):
                runtime.verify_no_attempt(self.root, self.old)
            path.unlink()

    def test_existing_state_is_never_reset_or_replayed(self):
        state = self.worker / "state/queue.sqlite"
        state.parent.mkdir()
        state.write_bytes(b"unknown-intent")
        with self.assertRaisesRegex(ValueError, "state_reconciliation"):
            rebind.untouched_job(self.root, self.old, state)
        self.assertEqual(state.read_bytes(), b"unknown-intent")

    def test_even_expired_same_job_claim_prevents_rebind(self):
        assigned = self.old["role_devices"]["player"]
        put(self.claims / (assigned["uuid"] + ".json"), dict(job_id=self.old["job_id"], hold_until_unix=1))
        with self.assertRaisesRegex(ValueError, "same_job_no_retry"):
            rebind.untouched_job(self.root, self.old, self.worker / "state/queue.sqlite")

    def test_previous_attempt_any_status_cannot_rebind(self):
        for status in ("UNKNOWN", "COMPLETE", "FAILED_NO_RETRY"):
            with self.subTest(status=status), patch.object(rebind, "previous_attempts", return_value=[
                    dict(job_id=self.old["job_id"], source_key=entry()["key"], state=status)]):
                with self.assertRaisesRegex(ValueError, "prior_source_attempt"):
                    rebind.untouched_job(self.root, self.old, self.worker / "state/queue.sqlite")

    def test_immutable_stage_preserves_all_legacy_bytes_and_skips_live_scan(self):
        result = self.isolated_stage()
        self.assertFalse(result["source_epoch_scan_performed"])
        self.assertFalse(result["gpu_execution_performed"])
        for relative, raw in self.original.items():
            self.assertEqual((self.worker / relative).read_bytes(), raw)
        new_registry = runtime.read(self.worker / "inputs/capsules_v4.json")
        self.assertEqual(len(new_registry["capsules"]), 1)
        self.assertEqual(new_registry["capsules"][0]["job_id"], self.old["job_id"])
        self.assertFalse((self.worker / "state/queue.sqlite").exists())
        self.assertFalse((self.root / "runtime_v4/LAUNCH.json").exists())

    def test_existing_or_partial_rebind_never_overwritten(self):
        self.isolated_stage()
        with self.assertRaisesRegex(ValueError, "never_overwritten_or_retried"):
            self.isolated_stage()

    def test_registry_keeps_other_capsules_and_rejects_science_delta(self):
        other = dict(self.cap, job_id="b" * 64, source_key="other")
        registry = {"capsules": [self.cap, other]}
        new = dict(self.cap, config_sha256="f" * 64)
        rebound = rebind.registry_replacement(registry, self.cap, new, "a" * 64)
        self.assertEqual(rebound["capsules"], [new, other])
        new["battery"] = {"changed": True}
        with self.assertRaisesRegex(ValueError, "only_runtime"):
            rebind.registry_replacement(registry, self.cap, new, "a" * 64)

    def test_role_warmup_cannot_extend_job_deadline(self):
        with patch.object(runtime, "verify_protected"), patch.object(runtime, "verify_live_source") as source, \
                patch.object(runtime.time, "time", return_value=101):
            with self.assertRaisesRegex(ValueError, "job_or_lease"):
                runtime.wait_for_live_source(self.old, deadline=160)
            source.assert_not_called()

    def test_successful_decode_after_deadline_is_not_admitted(self):
        with patch.object(runtime, "verify_protected"), patch.object(runtime, "verify_live_source"), \
                patch.object(runtime.time, "time", side_effect=[100, 100, 450]):
            with self.assertRaisesRegex(ValueError, "job_or_warmup"):
                runtime.wait_for_live_source(self.old, deadline=500)

    def test_bound_commands_use_new_runtime_and_same_absolute_deadline(self):
        config = dict(self.old, runtime_directory=str(self.root / "runtime_v4"), expected_uid=1352)
        commands = dispatch_once.commands(config, self.root / "runtime_v4/JOB_CONFIG.json", "a" * 64,
            self.root / "runtime_v4/LAUNCH.json", "b" * 64, 2000, 100)
        for command in commands:
            self.assertIn(str(self.root / "runtime_v4/probe_runtime.py"), command["argv"])
            self.assertIn("--property=RuntimeMaxSec=1900", command["argv"])
            self.assertIn(str(self.root / "runtime_v4/LAUNCH.json"), command["argv"])
            self.assertIn("--launch-sha256", command["argv"])
            self.assertIn("--property=DevicePolicy=closed", command["argv"])

    def test_activation_must_pin_exact_new_registry(self):
        review = dict(reviewed=True, runtime_enabled=True, policy_sha256=rules.digest(policy()),
            route="ORIGINAL_GPU_HOST_TRANSIENT_CGROUP_ONE_SHOT_ONLY", source_freeze_sha256="a" * 64,
            expires_unix=rules.HARD_END, registry_sha256="b" * 64)
        with patch.object(daemon, "verify_freeze"), self.assertRaisesRegex(ValueError, "registry_changed"):
            daemon.activation(review, policy(), self.worker / "seal", 100, self.registry)

    def activation_fixture(self):
        self.isolated_stage()
        candidate = self.worker / "candidate_v4"
        candidate.mkdir()
        for name in rebind.RUNTIME_FILES:
            (candidate / name).write_bytes((rebind.WORKER / name).read_bytes())
        put(self.worker / "inputs/policy.json", policy())
        return candidate, runtime.sha(self.worker / "inputs/capsules_v4.json")

    def test_review_helper_requires_exact_registry_and_verified_config_before_write(self):
        candidate, checksum = self.activation_fixture()
        with patch.object(daemon, "verify_freeze"), self.assertRaisesRegex(ValueError, "registry_pin"):
            activate_reviewed.prepare_review(candidate, "a" * 64, "b" * 64)
        self.assertFalse((self.worker / "inputs/activation_v4.json").exists())
        path = self.root / "runtime_v4/JOB_CONFIG.json"
        path.write_bytes(path.read_bytes() + b" ")
        with patch.object(daemon, "verify_freeze"), self.assertRaisesRegex(ValueError, "config_and_evidence"):
            activate_reviewed.prepare_review(candidate, "a" * 64, checksum)
        self.assertFalse((self.worker / "inputs/activation_v4.json").exists())

    def test_review_helper_never_resets_queue_state_or_replaces_review(self):
        candidate, checksum = self.activation_fixture()
        state = self.worker / "state/queue.sqlite"
        state.parent.mkdir()
        state.write_bytes(b"durable unknown attempt")
        with patch.object(daemon, "verify_freeze"):
            path = activate_reviewed.prepare_review(candidate, "a" * 64, checksum)
            original = path.read_bytes()
            activate_reviewed.prepare_review(candidate, "a" * 64, checksum)
            self.assertEqual(path.read_bytes(), original)
            with self.assertRaisesRegex(ValueError, "never_overwritten"):
                activate_reviewed.prepare_review(candidate, "b" * 64, checksum)
        self.assertEqual(state.read_bytes(), b"durable unknown attempt")
        self.assertEqual(runtime.read(path)["expires_unix"], rules.HARD_END)

    def test_main_review_record_requires_original_lease(self):
        candidate, checksum = self.activation_fixture()
        with patch.object(daemon, "verify_freeze"), patch.object(activate_reviewed.time, "time", return_value=rules.HARD_END), \
                self.assertRaisesRegex(ValueError, "lease_expired"):
            activate_reviewed.prepare_review(candidate, "a" * 64, checksum)
        self.assertFalse((self.worker / "inputs/activation_v4.json").exists())


if __name__ == "__main__":
    unittest.main()
