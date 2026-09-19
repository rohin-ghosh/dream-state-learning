"""Test-only revision proposal; frozen source and original tests remain untouched.

Controlled metadata tests separate the distinct-ctime contract from the raw-hash
content fence. The residual test records a limitation, not an immutability pass.
"""

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent
BASELINE_PATH = FROZEN.parents[2] / "post_reboot_probe_queue_20260919/version_v4_rebind/epoch_cache.py"
CANDIDATE_PATH = FROZEN / "candidate_epoch_cache.py"
PINS = {
    BASELINE_PATH: "8bd9f79620a42653d9727045e9fab36497345bb586658be649eaf6cc088af0bb",
    CANDIDATE_PATH: "1d11d58676aa9a00cabc989dfcc545de048e612912b3c1d30f56a6b47ee40099",
}


def load_module(name, path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != PINS[path]:
        raise RuntimeError("frozen_source_pin_changed")
    specification = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(specification)
    sys.modules[name] = loaded
    specification.loader.exec_module(loaded)
    return loaded


BASELINE = load_module("audit_timestamp_baseline", BASELINE_PATH)
CANDIDATE = load_module("audit_timestamp_candidate", CANDIDATE_PATH)


def digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()).hexdigest()


class TimestampContract:
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="contract_fixture_", dir=HERE)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.records = self.root / "stream/records"
        self.records.mkdir(parents=True)
        self.anchor = {
            "index": 1, "journal_id": "synthetic-timestamp-journal", "kind": "LOADED",
            "document": {"base_sha256": self.module.BASE_SHA}, "previous_sha256": None,
        }
        self.anchor["sha256"] = digest(self.anchor)
        self.record = {
            "index": 2, "journal_id": "synthetic-timestamp-journal", "kind": "RESPONSE",
            "document": {"text": "retained"}, "previous_sha256": self.anchor["sha256"],
        }
        self.record["sha256"] = digest(self.record)
        for record in (self.anchor, self.record):
            (self.records / f'{record["index"]:020d}.json').write_text(json.dumps(record) + "\n")
        self.path = self.records / "00000000000000000002.json"
        self.source = "FRESH_R231"
        self.policy = {
            "source_roots": {self.source: str(self.root)},
            "supported_journals": {self.source: "synthetic-timestamp-journal"},
            "initial_loaded": {self.source: {"index": 1, "sha256": self.anchor["sha256"]}},
            "current_loaded": {self.source: {"index": 1, "sha256": self.anchor["sha256"]}},
        }
        self.cache = self.module.EpochCache(self.policy, self.source)
        self.fresh_clock_ns = max(path.stat().st_ctime_ns for path in self.records.iterdir())

    def initialize_cache(self, fenced):
        clock = self.fresh_clock_ns if fenced else 10 ** 20
        with patch.object(self.module.time, "time_ns", return_value=clock):
            self.cache.validate()
        self.assertTrue(all(
            row["needs_content_fence"] is fenced for row in self.cache.verified.values()
        ))
        self.original_fingerprint = self.cache.verified[2]["fingerprint"]
        self.original_raw_sha256 = self.cache.verified[2]["raw_sha256"]

    def mutate_same_size_restore_mtime(self):
        before = self.path.stat()
        raw = self.path.read_bytes()
        changed = raw.replace(b"retained", b"tampered")
        self.assertNotEqual(raw, changed)
        self.assertEqual(len(raw), len(changed))
        self.path.write_bytes(changed)
        os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns))
        after = self.path.stat()
        self.assertEqual((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns),
                         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns))
        self.assertNotEqual(self.original_raw_sha256, hashlib.sha256(self.path.read_bytes()).hexdigest())

    def controlled_record_fingerprint(self, reported):
        original = self.module.fingerprint
        identity = self.original_fingerprint[:2]

        def fingerprint(metadata):
            actual = original(metadata)
            if actual[:2] == identity:
                self.assertEqual(actual[:-1], self.original_fingerprint[:-1])
                return reported
            return actual

        return patch.object(self.module, "fingerprint", side_effect=fingerprint)

    def test_distinct_reported_ctime_rejects_same_size_restored_mtime(self):
        self.initialize_cache(fenced=False)
        self.mutate_same_size_restore_mtime()
        reported = (*self.original_fingerprint[:-1], self.original_fingerprint[-1] + 1)
        self.assertNotEqual(reported[-1], self.original_fingerprint[-1])
        self.assertEqual(reported[:-1], self.original_fingerprint[:-1])
        with self.controlled_record_fingerprint(reported):
            with self.assertRaisesRegex(ValueError, "verified_source_record_changed_review_rebind_required"):
                self.cache.validate()

    def test_same_fingerprint_fresh_record_rejected_by_content_fence(self):
        self.initialize_cache(fenced=True)
        self.mutate_same_size_restore_mtime()
        with self.controlled_record_fingerprint(self.original_fingerprint):
            with self.assertRaisesRegex(ValueError, "verified_source_record_changed_within_timestamp_granularity"):
                self.cache.validate()

    def test_final_fence_checks_mutation_before_clearing_fence(self):
        self.initialize_cache(fenced=True)
        self.mutate_same_size_restore_mtime()
        after_window = self.fresh_clock_ns + self.module.TIMESTAMP_FENCE_NS + 1
        with self.controlled_record_fingerprint(self.original_fingerprint), \
                patch.object(self.module.time, "time_ns", return_value=after_window):
            with self.assertRaisesRegex(ValueError, "verified_source_record_changed_within_timestamp_granularity"):
                self.cache.validate()
        self.assertTrue(self.cache.verified[2]["needs_content_fence"])

    def test_unchanged_final_fence_hashes_before_metadata_only_reuse(self):
        self.initialize_cache(fenced=True)
        after_window = self.fresh_clock_ns + self.module.TIMESTAMP_FENCE_NS + 1
        with patch.object(self.module.time, "time_ns", return_value=after_window), \
                patch.object(self.cache, "raw_record", wraps=self.cache.raw_record) as reader:
            self.cache.validate()
        self.assertEqual([call.args[0] for call in reader.call_args_list], [1, 2])
        self.assertEqual(self.cache.total_fence_reads, 2)
        self.assertFalse(self.cache.verified[2]["needs_content_fence"])
        with patch.object(self.cache, "raw_record", side_effect=AssertionError("settled prefix reread")):
            self.cache.validate()

    def test_residual_false_settled_clock_and_identical_metadata_cannot_detect_changed_bytes(self):
        self.initialize_cache(fenced=False)
        self.mutate_same_size_restore_mtime()
        with self.controlled_record_fingerprint(self.original_fingerprint), \
                patch.object(self.cache, "raw_record", side_effect=AssertionError("no raw fence expected")):
            frontier = self.cache.validate()
        self.assertEqual(frontier["sha256"], self.record["sha256"])
        self.assertNotEqual(self.original_raw_sha256, hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(self.cache.total_fence_reads, 0)
        self.assertIsNone(self.cache.failure)

    def test_content_failure_stays_latched(self):
        self.initialize_cache(fenced=True)
        self.mutate_same_size_restore_mtime()
        with self.controlled_record_fingerprint(self.original_fingerprint):
            with self.assertRaisesRegex(ValueError, "timestamp_granularity"):
                self.cache.validate()
        with self.assertRaisesRegex(ValueError, "source_cache_invalid_review_required"):
            self.cache.validate()

    def test_timestamp_guards_are_identical_in_baseline_and_candidate(self):
        def functions(path):
            selected = {}
            for element in ast.parse(path.read_text()).body:
                if isinstance(element, ast.FunctionDef) and element.name == "fingerprint":
                    selected[element.name] = ast.dump(element, include_attributes=False)
                if isinstance(element, ast.ClassDef) and element.name == "EpochCache":
                    for method in element.body:
                        if isinstance(method, ast.FunctionDef) and method.name in ("raw_record", "decode", "validate"):
                            selected[method.name] = ast.dump(method, include_attributes=False)
            return selected

        self.assertEqual(functions(BASELINE_PATH), functions(CANDIDATE_PATH))


class BaselineTimestampTests(TimestampContract, unittest.TestCase):
    module = BASELINE


class CandidateTimestampTests(TimestampContract, unittest.TestCase):
    module = CANDIDATE


if __name__ == "__main__":
    unittest.main()
