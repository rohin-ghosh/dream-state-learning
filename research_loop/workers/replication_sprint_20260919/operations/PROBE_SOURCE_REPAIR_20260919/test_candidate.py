"""CPU-only fixtures; every write stays under this isolated candidate directory."""

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
BASELINE = HERE.parents[2] / "post_reboot_probe_queue_20260919/version_v4_rebind/epoch_cache.py"
BASELINE_SHA256 = "8bd9f79620a42653d9727045e9fab36497345bb586658be649eaf6cc088af0bb"


def load_module(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


if hashlib.sha256(BASELINE.read_bytes()).hexdigest() != BASELINE_SHA256:
    raise RuntimeError("reviewed_baseline_source_changed")

baseline = load_module("probe_repair_baseline", BASELINE)
candidate = load_module("probe_repair_candidate", HERE / "candidate_epoch_cache.py")


def digest(document):
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


class PublicationRaceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="cpu_fixture_", dir=HERE)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.records = self.root / "stream/records"
        self.records.mkdir(parents=True)
        self.rows = []
        self.source = "R232_SIBLING_FROZEN"
        self.journal = "fixture-frozen-journal"
        anchor = self.append("LOADED", {"base_sha256": candidate.BASE_SHA})
        self.policy = {
            "source_roots": {self.source: str(self.root)},
            "supported_journals": {self.source: self.journal},
            "initial_loaded": {self.source: {"index": 1, "sha256": anchor["sha256"]}},
            "current_loaded": {self.source: {"index": 1, "sha256": anchor["sha256"]}},
        }
        self.cache = candidate.EpochCache(self.policy, self.source)

    def row(self, kind="RESPONSE", document=None):
        record = {
            "index": len(self.rows) + 1,
            "journal_id": self.journal,
            "kind": kind,
            "document": document or {"text": "retained"},
            "previous_sha256": self.rows[-1]["sha256"] if self.rows else None,
        }
        record["sha256"] = digest(record)
        self.rows.append(record)
        return record

    def path(self, record):
        return self.records / f'{record["index"]:020d}.json'

    def append(self, kind="RESPONSE", document=None):
        record = self.row(kind, document)
        self.path(record).write_text(json.dumps(record, sort_keys=True) + "\n")
        return record

    def begin_publication(self, kind="RESPONSE", document=None):
        record = self.row(kind, document)
        final = self.path(record)
        partial = final.with_name(final.name + ".partial")
        with partial.open("xb") as stream:
            stream.write((json.dumps(record, sort_keys=True) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.link(partial, final)
        self.assertEqual(final.stat().st_nlink, 2)
        return record, partial

    def validate(self, cache=None):
        selected = self.cache if cache is None else cache
        with patch.object(candidate.time, "time_ns", return_value=10 ** 20):
            return selected.validate()

    def retire_during_read(self, module, cache, partial):
        original = cache.raw_record

        def concurrent_retirement(index, expected):
            if partial.exists():
                partial.unlink()
            return original(index, expected)

        with patch.object(cache, "raw_record", side_effect=concurrent_retirement):
            with self.assertRaisesRegex(ValueError, "source_record_changed_during_read"):
                self.validate(cache)

    def test_baseline_reproduces_native_link_unlink_race_without_byte_change(self):
        cache = baseline.EpochCache(self.policy, self.source)
        self.validate(cache)
        record, partial = self.begin_publication()
        before = self.path(record).read_bytes()
        self.retire_during_read(baseline, cache, partial)
        self.assertEqual(before, self.path(record).read_bytes())
        self.assertNotIn(record["index"], cache.verified)
        self.assertIn("source_record_changed_during_read", cache.failure)

    def test_demonstrated_open_publication_is_pending_not_cached_or_admitted(self):
        self.validate()
        record, partial = self.begin_publication()
        with patch.object(self.cache, "raw_record", side_effect=AssertionError("unsettled bytes read")):
            with self.assertRaises(candidate.SourceEpochPending) as pending:
                self.validate()
        self.assertEqual(pending.exception.progress["record_index"], record["index"])
        self.assertFalse(pending.exception.progress["ready"])
        self.assertTrue(partial.exists())
        self.assertNotIn(record["index"], self.cache.verified)
        self.assertIsNone(self.cache.failure)

    def test_settled_publication_requires_normal_full_canonical_validation(self):
        self.validate()
        record, partial = self.begin_publication()
        with self.assertRaises(candidate.SourceEpochPending):
            self.validate()
        partial.unlink()
        with patch.object(self.cache, "decode", wraps=self.cache.decode) as decoder:
            frontier = self.validate()
        self.assertEqual(frontier, {"index": record["index"], "sha256": record["sha256"]})
        self.assertEqual([call.args[0] for call in decoder.call_args_list], [record["index"]])

    def test_missing_partial_during_detection_keeps_original_change_error(self):
        self.validate()
        record, partial = self.begin_publication()
        original = Path.lstat

        def cleanup_before_partial_stat(path, *arguments, **keywords):
            if path == partial and partial.exists():
                partial.unlink()
            return original(path, *arguments, **keywords)

        with patch.object(Path, "lstat", cleanup_before_partial_stat):
            with self.assertRaisesRegex(ValueError, "source_record_changed_during_read"):
                self.validate()
        self.assertNotIn(record["index"], self.cache.verified)
        self.assertIsNotNone(self.cache.failure)

    def test_existing_failure_is_not_cleared_by_publication_pending(self):
        self.validate()
        self.begin_publication()
        self.cache.failure = "source_cache_invalid_review_required:source_record_changed_during_read"
        with self.assertRaisesRegex(ValueError, "source_cache_invalid_review_required"):
            self.validate()
        self.assertEqual(len(self.cache.verified), 1)

    def test_cached_mutation_is_checked_before_pending_frontier(self):
        self.validate()
        self.begin_publication()
        self.path(self.rows[0]).write_bytes(self.path(self.rows[0]).read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "verified_source_record_changed"):
            self.validate()

    def test_unrelated_partial_never_suppresses_changed_source_error(self):
        self.validate()
        record, partial = self.begin_publication()
        alias = partial.with_name("unrelated-alias")
        partial.rename(alias)
        partial.write_text("unrelated inode")
        self.retire_during_read(candidate, self.cache, alias)
        self.assertNotIn(record["index"], self.cache.verified)

    def test_partial_symlink_is_not_trusted(self):
        self.validate()
        record, partial = self.begin_publication()
        alias = partial.with_name("unrelated-alias")
        partial.rename(alias)
        partial.symlink_to(alias)
        with self.assertRaisesRegex(ValueError, "bounded_regular_journal_record"):
            self.validate()
        self.assertNotIn(record["index"], self.cache.verified)

    def test_anchor_is_not_reclassified_as_new_publication(self):
        anchor = self.path(self.rows[0])
        partial = anchor.with_name(anchor.name + ".partial")
        os.link(anchor, partial)
        self.retire_during_read(candidate, self.cache, partial)

    def test_verified_record_link_change_still_fails(self):
        self.validate()
        anchor = self.path(self.rows[0])
        os.link(anchor, anchor.with_name(anchor.name + ".partial"))
        with self.assertRaisesRegex(ValueError, "verified_source_record_changed"):
            self.validate()

    def test_tampered_settled_publication_is_not_admitted(self):
        self.validate()
        record, partial = self.begin_publication()
        with self.assertRaises(candidate.SourceEpochPending):
            self.validate()
        partial.write_bytes(partial.read_bytes().replace(b"retained", b"tampered"))
        partial.unlink()
        with self.assertRaisesRegex(ValueError, "source_journal_identity_changed"):
            self.validate()
        self.assertNotIn(record["index"], self.cache.verified)

    def test_settled_new_loaded_epoch_requires_explicit_rebind(self):
        self.validate()
        record, partial = self.begin_publication("LOADED", {"base_sha256": candidate.BASE_SHA})
        with self.assertRaises(candidate.SourceEpochPending):
            self.validate()
        partial.unlink()
        with self.assertRaisesRegex(ValueError, "new_source_epoch_requires_explicit_review_rebind"):
            self.validate()
        self.assertNotIn(record["index"], self.cache.verified)

    def test_broken_previous_hash_still_fails(self):
        self.validate()
        record = self.append()
        record["previous_sha256"] = "0" * 64
        record["sha256"] = digest({key: value for key, value in record.items() if key != "sha256"})
        self.path(record).write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "source_frontier_chain_changed"):
            self.validate()

    def test_same_size_mutation_with_restored_mtime_still_fails(self):
        record = self.append()
        self.validate()
        path = self.path(record)
        before = path.stat()
        path.write_bytes(path.read_bytes().replace(b"retained", b"tampered"))
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, "verified_source_record_changed"):
            self.validate()

    def test_replaced_inode_still_fails(self):
        record = self.append()
        self.validate()
        path = self.path(record)
        replacement = self.root / "replacement"
        replacement.write_bytes(path.read_bytes())
        replacement.replace(path)
        with self.assertRaisesRegex(ValueError, "verified_source_record_changed"):
            self.validate()

    def test_deleted_source_still_fails(self):
        record = self.append()
        self.validate()
        self.path(record).unlink()
        with self.assertRaisesRegex(ValueError, "verified_source_record_changed"):
            self.validate()

    def test_source_symlink_still_fails(self):
        record = self.append()
        path = self.path(record)
        replacement = self.root / "replacement"
        path.rename(replacement)
        path.symlink_to(replacement)
        with self.assertRaisesRegex(ValueError, "bounded_regular_journal_record"):
            self.validate()

    def test_content_mutation_during_decode_still_fails(self):
        self.validate()
        record = self.append()
        original = candidate.json.loads

        def mutate(raw):
            parsed = original(raw)
            path = self.path(record)
            path.write_bytes(path.read_bytes() + b" ")
            return parsed

        with patch.object(candidate.json, "loads", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "source_record_changed_during_read"):
                self.validate()

    def test_unauthenticated_cursor_cannot_skip_prefix(self):
        record = self.append()
        with self.assertRaisesRegex(ValueError, "unverified_cursor_cannot_skip_source_prefix"):
            self.cache.validate({"index": record["index"], "sha256": record["sha256"]})

    def test_fresh_snapshot_publication_is_pending_after_decodes(self):
        self.validate()
        self.append()
        original = self.cache.decode

        def append_during_decode(index, expected):
            record = original(index, expected)
            self.begin_publication()
            return record

        with patch.object(self.cache, "decode", side_effect=append_during_decode):
            with self.assertRaises(candidate.SourceEpochPending) as pending:
                self.validate()
        self.assertFalse(pending.exception.progress["ready"])
        self.assertNotIn("decoded_records", pending.exception.progress)
        self.assertNotIn(3, self.cache.verified)

    def test_prior_epoch_anchors_remain_exact(self):
        self.policy["current_loaded"][self.source]["sha256"] = "0" * 64
        cache = candidate.EpochCache(self.policy, self.source)
        with self.assertRaisesRegex(ValueError, "source_loaded_changed"):
            self.validate(cache)

    def test_candidate_never_edits_binding_policy(self):
        original = json.loads(json.dumps(self.policy))
        self.validate()
        record, partial = self.begin_publication()
        with self.assertRaises(candidate.SourceEpochPending):
            self.validate()
        partial.unlink()
        self.validate()
        self.assertEqual(original, self.policy)


if __name__ == "__main__":
    unittest.main()
