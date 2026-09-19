"""Source-cache regressions use only temporary CPU fixtures and mocked host identities."""

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import daemon
import epoch_cache
import host
import probe_runtime as runtime
from test_queue import policy


class EpochTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.records = self.root / "stream/records"
        self.records.mkdir(parents=True)
        self.policy = policy()
        self.source = "FRESH_R231"
        self.policy["source_roots"][self.source] = str(self.root)
        self.rows = []
        anchor = self.append("LOADED", dict(base_sha256=epoch_cache.BASE_SHA))
        for field in ("initial_loaded", "current_loaded"):
            self.policy[field][self.source] = dict(index=1, sha256=anchor["sha256"])
        self.cache = epoch_cache.EpochCache(self.policy, self.source)

    def append(self, kind="REQUEST", document=None):
        row = dict(index=len(self.rows) + 1, journal_id=self.policy["supported_journals"][self.source],
            kind=kind, document=document or {"text": "retained"},
            previous_sha256=self.rows[-1]["sha256"] if self.rows else None)
        row["sha256"] = hashlib.sha256(json.dumps(row, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        (self.records / f'{row["index"]:020d}.json').write_text(json.dumps(row))
        self.rows.append(row)
        return row

    def test_warm_calls_never_decode_whole_prefix(self):
        for unused in range(32):
            self.append()
        initial = self.cache.validate()
        with patch.object(self.cache, "decode", side_effect=AssertionError("prefix reparsed")):
            self.assertEqual(self.cache.validate(initial), initial)
        self.assertEqual(self.cache.last["decoded_records"], 0)
        self.assertEqual(self.cache.last["decoded_bytes"], 0)

    def test_append_decodes_only_new_record(self):
        self.cache.validate()
        self.append()
        with patch.object(self.cache, "decode", wraps=self.cache.decode) as decode:
            self.assertEqual(self.cache.validate()["index"], 2)
        self.assertEqual([call.args[0] for call in decode.call_args_list], [2])

    def test_multiple_bounded_calls_make_forward_progress_once(self):
        for unused in range(12):
            self.append()
        pending = 0
        with patch.object(epoch_cache.time, "time_ns", return_value=10 ** 20):
            while True:
                try:
                    result = self.cache.validate(budget=epoch_cache.Budget(records=2))
                    break
                except epoch_cache.SourceEpochPending as error:
                    self.assertLessEqual(error.progress["decoded_records"], 2)
                    pending += 1
        self.assertEqual(result["index"], 13)
        self.assertEqual(self.cache.total_decoded, 13)
        self.assertEqual(pending, 6)

    def test_byte_budget_bounded_with_one_atomic_record_allowance(self):
        self.append(document={"text": "x" * 4096})
        with self.assertRaises(epoch_cache.SourceEpochPending):
            self.cache.validate(budget=epoch_cache.Budget(bytes=100))
        self.assertEqual(self.cache.last["decoded_records"], 1)
        with patch.object(epoch_cache.time, "time_ns", return_value=10 ** 20):
            with self.assertRaises(epoch_cache.SourceEpochPending):
                self.cache.validate(budget=epoch_cache.Budget(bytes=100))
            self.assertEqual(self.cache.validate(budget=epoch_cache.Budget(bytes=100))["index"], 2)

    def test_elapsed_budget_does_not_admit_unvalidated_tail(self):
        self.append()
        with patch.object(epoch_cache.time, "monotonic", side_effect=[0, 3, 3]):
            with self.assertRaises(epoch_cache.SourceEpochPending):
                self.cache.validate()
        self.assertEqual(self.cache.last["decoded_records"], 1)

    def test_in_place_same_size_mutation_restored_mtime_rejected(self):
        self.append()
        self.cache.validate()
        path = self.records / "00000000000000000002.json"
        before = path.stat()
        path.write_bytes(path.read_bytes().replace(b"retained", b"mutated!"))
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, "record_changed"):
            self.cache.validate()

    def test_identical_byte_replacement_rejected(self):
        self.cache.validate()
        target = self.records / "00000000000000000001.json"
        other = self.records / "replacement"
        other.write_bytes(target.read_bytes())
        other.replace(target)
        with self.assertRaisesRegex(ValueError, "record_changed"):
            self.cache.validate()

    def test_cached_interior_deletion_rejected(self):
        self.append()
        self.append()
        self.cache.validate()
        (self.records / "00000000000000000002.json").unlink()
        with self.assertRaisesRegex(ValueError, "frontier_chain_changed"):
            self.cache.validate()

    def test_cached_tail_deletion_rejected(self):
        self.append()
        self.cache.validate()
        (self.records / "00000000000000000002.json").unlink()
        with self.assertRaisesRegex(ValueError, "record_changed"):
            self.cache.validate()

    def test_symlink_record_rejected(self):
        original = self.records / "00000000000000000001.json"
        other = self.root / "retained.json"
        original.rename(other)
        original.symlink_to(other)
        with self.assertRaisesRegex(ValueError, "regular_journal"):
            self.cache.validate()

    def test_replaced_directory_is_not_adopted(self):
        self.cache.validate()
        self.records.rename(self.root / "old_records")
        self.records.mkdir()
        with self.assertRaisesRegex(ValueError, "directory_replaced"):
            self.cache.validate()

    def test_new_loaded_epoch_never_adopted(self):
        self.cache.validate()
        self.append("LOADED", dict(base_sha256=epoch_cache.BASE_SHA))
        with self.assertRaisesRegex(ValueError, "explicit_review_rebind"):
            self.cache.validate()

    def test_unverified_cursor_cannot_skip_loaded(self):
        row = self.append("LOADED", dict(base_sha256=epoch_cache.BASE_SHA))
        with self.assertRaisesRegex(ValueError, "unverified_cursor"):
            self.cache.validate(dict(index=row["index"], sha256=row["sha256"]))

    def test_changed_append_checksum_rejected(self):
        self.cache.validate()
        self.append()
        path = self.records / "00000000000000000002.json"
        path.write_bytes(path.read_bytes().replace(b"retained", b"tampered"))
        with self.assertRaisesRegex(ValueError, "journal_identity_changed"):
            self.cache.validate()

    def test_append_during_validation_is_pending_not_early_success(self):
        original = self.cache.decode
        def extending(index, expected):
            record = original(index, expected)
            self.append()
            return record
        with patch.object(self.cache, "decode", side_effect=extending):
            with self.assertRaises(epoch_cache.SourceEpochPending):
                self.cache.validate()
        self.assertEqual(self.cache.validate()["index"], 2)

    def test_mutation_during_decode_not_cached(self):
        original = epoch_cache.json.loads
        def mutate(raw):
            record = original(raw)
            path = self.records / "00000000000000000001.json"
            path.write_bytes(path.read_bytes() + b" ")
            return record
        with patch.object(epoch_cache.json, "loads", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "changed_during_read"):
                self.cache.validate()
        self.assertFalse(self.cache.verified)

    def test_failure_stays_latched(self):
        self.cache.validate()
        path = self.records / "00000000000000000001.json"
        raw = path.read_bytes()
        path.write_bytes(raw + b" ")
        with self.assertRaises(ValueError):
            self.cache.validate()
        path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "cache_invalid_review_required"):
            self.cache.validate()

    def test_runtime_entrypoints_share_one_process_proof(self):
        self.append()
        cursor = runtime.verify_source_epoch(self.policy, self.source)
        cached = epoch_cache.cache_for(self.policy, self.source)
        with patch.object(cached, "decode", side_effect=AssertionError("duplicate decode")):
            runtime.verify_source_epoch(self.policy, self.source, cursor)
            runtime.verify_source_epoch(self.policy, self.source)

    def test_warm_source_does_not_cache_protected_identity_or_lease(self):
        local = host.LocalHost(self.policy)
        with patch.object(runtime, "verify_source_epoch", return_value=dict(index=1, sha256="a" * 64)), \
                patch.object(runtime, "verify_protected") as protected, patch.object(host.time, "time", return_value=100):
            local.source_guard()
            local.source_guard()
            self.assertEqual(protected.call_count, 2)
            protected.side_effect = ValueError("protected_changed")
            with self.assertRaisesRegex(ValueError, "protected_changed"):
                local.source_guard()
        with patch.object(runtime, "verify_source_epoch"), patch.object(runtime, "verify_protected"), \
                patch.object(host.time, "time", return_value=self.policy["lease_end_unix"]):
            with self.assertRaisesRegex(ValueError, "unexpired"):
                local.source_guard()

    def test_pending_checks_other_source_and_protected_identity(self):
        local = host.LocalHost(self.policy)
        with patch.object(runtime, "verify_source_epoch", side_effect=epoch_cache.SourceEpochPending({})) as guard, \
                patch.object(runtime, "verify_protected") as protected, patch.object(host.time, "time", return_value=100):
            with self.assertRaises(epoch_cache.SourceEpochPending):
                local.source_guard()
            self.assertEqual(guard.call_count, 2)
            self.assertEqual(protected.call_count, 1)

    def test_changed_policy_does_not_reuse_old_cache(self):
        first = epoch_cache.cache_for(self.policy, self.source)
        changed = json.loads(json.dumps(self.policy))
        changed["receiving_boot_id"] = "different"
        self.assertIsNot(first, epoch_cache.cache_for(changed, self.source))

    def test_settled_prefix_has_no_content_reads(self):
        for unused in range(10):
            self.append()
        with patch.object(epoch_cache.time, "time_ns", return_value=10 ** 20):
            self.cache.validate()
        with patch.object(self.cache, "raw_record", side_effect=AssertionError("stable prefix reread")):
            self.cache.validate()
        self.assertEqual(self.cache.last["decoded_bytes"], 0)
        self.assertEqual(self.cache.last["timestamp_fence_bytes"], 0)

    def test_same_timestamp_fingerprint_mutation_still_fails_content_fence(self):
        self.cache.validate()
        path = self.records / "00000000000000000001.json"
        prior = self.cache.verified[1]["fingerprint"]
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b"LOADED", b"LOADEx"))
        with patch.object(epoch_cache, "fingerprint", return_value=prior):
            with self.assertRaisesRegex(ValueError, "timestamp_granularity"):
                self.cache.validate()

    def test_final_content_fence_before_metadata_only_reuse(self):
        self.cache.validate()
        with patch.object(epoch_cache.time, "time_ns", return_value=10 ** 20):
            self.cache.validate()
        self.assertEqual(self.cache.last["timestamp_fence_reads"], 1)
        with patch.object(self.cache, "raw_record", side_effect=AssertionError("settled prefix reread")):
            self.cache.validate()

    def test_different_process_never_inherits_proof_authority(self):
        initial = epoch_cache.cache_for(self.policy, self.source)
        with patch.object(epoch_cache.os, "getpid", return_value=os.getpid() + 100000):
            self.assertIsNot(initial, epoch_cache.cache_for(self.policy, self.source))

    def test_waiter_rechecks_protection_and_lease_while_pending(self):
        config = dict(lease_end_unix=10000)
        with patch.object(runtime, "verify_protected") as protected, \
                patch.object(runtime, "verify_live_source", side_effect=[epoch_cache.SourceEpochPending({}), None]) as source, \
                patch.object(runtime.time, "time", return_value=100):
            runtime.wait_for_live_source(config)
        self.assertEqual(source.call_count, 2)
        self.assertEqual(protected.call_count, 4)

    def test_waiter_does_not_turn_timeout_into_success(self):
        config = dict(lease_end_unix=10000)
        with patch.object(runtime, "verify_protected"), \
                patch.object(runtime, "verify_live_source", side_effect=epoch_cache.SourceEpochPending({})), \
                patch.object(runtime.time, "time", return_value=100), \
                patch.object(runtime.time, "monotonic", side_effect=[0, 0, 301]):
            with self.assertRaises(epoch_cache.SourceEpochPending):
                runtime.wait_for_live_source(config)

    def test_pending_active_reconciliation_does_not_pause_or_launch(self):
        from unittest.mock import Mock
        store = Mock()
        store.active.return_value = [dict(intent={}, job_id="existing")]
        receiving = Mock()
        receiving.reconcile.side_effect = epoch_cache.SourceEpochPending({})
        queue = daemon.Queue(store, self.policy, receiving)
        queue.reconcile()
        store.pause.assert_not_called()
        store.update_attempt.assert_not_called()
        receiving.launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
