"""Synthetic byte-custody tests, not validation of a live sealed scientific bundle."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_candidate as fixtures


class FrozenWitnessTests(unittest.TestCase):
    def setUp(self):
        checkpoint = json.loads((fixtures.HERE / "CHECKPOINT.json").read_bytes())
        self.assertEqual(
            hashlib.sha256((fixtures.HERE / "candidate_epoch_cache.py").read_bytes()).hexdigest(),
            checkpoint["candidate_sha256"],
        )
        self.fixture = fixtures.PublicationRaceTests(
            methodName="test_candidate_never_edits_binding_policy"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.validate()
        self.cache = self.fixture.cache
        protected = self.fixture.root / "synthetic_sealed_bundle"
        protected.mkdir()
        self.protected = protected
        (protected / "CONTEXT.json").write_bytes(
            b'{"fixture_only":true,"sealed_context":"must remain byte identical"}\n'
        )
        (protected / "SOURCE.bin").write_bytes(b"synthetic-adapter-source-not-model-weights\x00\xff")
        (protected / "CAPSULE.json").write_text(json.dumps({
            "fixture_only": True,
            "source_sha256": hashlib.sha256((protected / "SOURCE.bin").read_bytes()).hexdigest(),
            "context_sha256": hashlib.sha256((protected / "CONTEXT.json").read_bytes()).hexdigest(),
            "source_context_loaded": False,
            "parent_tokens": 0,
            "model_updates": 0,
        }, sort_keys=True))
        (protected / "NO_REDISPATCH_LEDGER.json").write_text(json.dumps({
            "fixture_only": True,
            "job_id": "synthetic-consumed-capsule",
            "status": "PRIOR_ATTEMPT_NO_RETRY",
            "retry_permitted": False,
        }, sort_keys=True))
        self.protected_bytes = self.file_bytes(protected)
        self.policy_before = deepcopy(self.fixture.policy)
        self.prefix_before = deepcopy(self.cache.verified)
        self.source_prefix_bytes = self.file_bytes(self.fixture.records)

    def file_bytes(self, directory):
        return {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()}

    def assert_custody(self):
        current = self.file_bytes(self.protected)
        self.assertEqual(self.protected_bytes, current)
        self.assertEqual(
            {name: hashlib.sha256(raw).hexdigest() for name, raw in self.protected_bytes.items()},
            {name: hashlib.sha256(raw).hexdigest() for name, raw in current.items()},
        )
        self.assertEqual(self.policy_before, self.fixture.policy)
        for name, raw in self.source_prefix_bytes.items():
            self.assertEqual(raw, (self.fixture.records / name).read_bytes())
        for index, evidence in self.prefix_before.items():
            self.assertEqual(evidence, self.cache.verified[index])

    def test_pending_preserves_sealed_source_context_policy_ledger_and_prefix_witness(self):
        record, partial = self.fixture.begin_publication()
        raw = self.fixture.path(record).read_bytes()
        with self.assertRaises(fixtures.candidate.SourceEpochPending):
            self.fixture.validate()
        self.assert_custody()
        self.assertEqual(raw, self.fixture.path(record).read_bytes())
        self.assertEqual(self.prefix_before, self.cache.verified)
        self.assertTrue(partial.exists())

    def test_cleanup_changes_metadata_not_context_source_or_canonical_record_bytes(self):
        record, partial = self.fixture.begin_publication()
        record_path = self.fixture.path(record)
        before_bytes = record_path.read_bytes()
        before_fingerprint = fixtures.candidate.fingerprint(record_path.stat())
        with self.assertRaises(fixtures.candidate.SourceEpochPending):
            self.fixture.validate()
        partial.unlink()
        after_fingerprint = fixtures.candidate.fingerprint(record_path.stat())
        self.assertEqual(before_fingerprint[5], 2)
        self.assertEqual(after_fingerprint[5], 1)
        self.assertEqual(before_fingerprint[:5], after_fingerprint[:5])
        self.assertEqual(before_bytes, record_path.read_bytes())
        frontier = self.fixture.validate()
        self.assertEqual(frontier["sha256"], record["sha256"])
        self.assertEqual(before_bytes, record_path.read_bytes())
        self.assert_custody()

    def test_concurrent_append_keeps_earlier_witness_and_sealed_bundle_byte_identical(self):
        record = self.fixture.append()
        earlier_bytes = self.fixture.path(record).read_bytes()
        original = self.cache.decode
        publication = []

        def concurrent_append(index, expected):
            decoded = original(index, expected)
            publication.append(self.fixture.begin_publication())
            return decoded

        with patch.object(self.cache, "decode", side_effect=concurrent_append):
            with self.assertRaises(fixtures.candidate.SourceEpochPending):
                self.fixture.validate()
        newest, partial = publication[0]
        self.assertNotIn(newest["index"], self.cache.verified)
        self.assertEqual(earlier_bytes, self.fixture.path(record).read_bytes())
        self.assert_custody()
        partial.unlink()
        self.fixture.validate()
        self.assertEqual(earlier_bytes, self.fixture.path(record).read_bytes())
        self.assert_custody()

    def test_consumed_capsule_ledger_remains_exact_after_pending_and_full_validation(self):
        record, partial = self.fixture.begin_publication()
        ledger = self.protected / "NO_REDISPATCH_LEDGER.json"
        consumed = ledger.read_bytes()
        with self.assertRaises(fixtures.candidate.SourceEpochPending):
            self.fixture.validate()
        partial.unlink()
        self.fixture.validate()
        self.assertEqual(consumed, ledger.read_bytes())
        self.assertFalse(json.loads(ledger.read_bytes())["retry_permitted"])
        self.assert_custody()

    def test_changed_cached_source_still_blocks_without_mutating_capsule_or_ledger(self):
        self.fixture.begin_publication()
        anchor = self.fixture.path(self.fixture.rows[0])
        anchor.write_bytes(anchor.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "verified_source_record_changed"):
            self.fixture.validate()
        self.assertEqual(self.protected_bytes, self.file_bytes(self.protected))
        self.assertEqual(self.policy_before, self.fixture.policy)
        self.assertEqual(self.prefix_before, self.cache.verified)
        self.assertIsNotNone(self.cache.failure)

    def test_test_harness_rejects_sealed_context_drift_instead_of_claiming_equivalence(self):
        context = self.protected / "CONTEXT.json"
        context.write_bytes(context.read_bytes() + b" ")
        with self.assertRaises(AssertionError):
            self.assert_custody()
        self.assertEqual(self.prefix_before, self.cache.verified)


if __name__ == "__main__":
    unittest.main()
