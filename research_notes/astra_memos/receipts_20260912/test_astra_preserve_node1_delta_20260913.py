"""Synthetic CPU tests; all fixtures live in disposable /tmp directories."""

import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location(
    "astra_delta_custody", Path(__file__).with_name("astra_preserve_node1_delta_20260913.py"))
HELPER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HELPER
SPEC.loader.exec_module(HELPER)


class DeltaCustodyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="astra-delta-tests-", dir="/tmp")
        self.base = Path(self.temporary.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.roster_path = self.base / "roster.json"
        self.archive = self.base / "new.tar"
        self.pack_receipt = self.base / "pack.json"
        self.verify_receipt = self.base / "verify.json"
        self.counts = (2, 2)
        self.payloads = {
            "v6_out/off_noise/tiny.json": b"tiny noise fixture\n",
            "v6_out/pretest_write_ab_AC/life/timings.jsonl": b"tiny changed fixture\n",
            "astra_sources/" + "a" * 40 + "/source.py": b"source alpha\n",
            "astra_sources/" + "b" * 40 + "/source.py": b"source beta\n",
        }
        self.records = {}
        for index, (relative, payload) in enumerate(self.payloads.items()):
            path = self.home / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            path.chmod(0o640)
            os.utime(path, ns=(1_700_000_000_000_000_000 + index,
                              1_700_000_000_000_000_000 + index))
            info = path.stat()
            self.records[relative] = {
                "relative_path": relative, "size_bytes": info.st_size,
                "mtime_ns": info.st_mtime_ns, "mode_octal": "0o640",
                "is_symlink": False, "stable_during_hash": True,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        delta = []
        for relative in list(self.payloads)[:2]:
            record = self.records[relative]
            delta.append({"relative_path": relative.removeprefix("v6_out/"),
                          "source": {key: record[key] for key in
                                     ("size_bytes", "mtime_ns", "mode_octal", "is_symlink")},
                          "source_payload": copy.deepcopy(record)})
        snapshots = []
        for identity in ("a" * 40, "b" * 40):
            record = copy.deepcopy(self.records["astra_sources/" + identity + "/source.py"])
            record["snapshot_relative_path"] = "source.py"
            files = [record]
            snapshots.append({
                "identity": identity, "root": "/unused/original/home/astra_sources/" + identity,
                "files": files, "file_count": 1, "total_bytes": record["size_bytes"],
                "member_manifest_sha256": hashlib.sha256(json.dumps(
                    files, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            })
        self.data = {
            "schema": HELPER.SCHEMA, "status": "READ_ONLY_ROSTER_HASHED_STABLE", "errors": [],
            "missing_files": [delta[0]], "changed_files": [delta[1]],
            "source_snapshots": snapshots,
            "summary": {"all_hash_reads_stable": True, "delta_hashes_bound_to_initial_stat": True,
                        "missing_files": 1, "changed_files": 1, "source_snapshot_files": 2,
                        "source_snapshot_bytes": sum(snapshot["total_bytes"] for snapshot in snapshots)},
        }
        self.save_roster()

    def tearDown(self):
        self.temporary.cleanup()

    def save_roster(self):
        raw = (json.dumps(self.data, indent=2) + "\n").encode()
        self.roster_path.write_bytes(raw)
        self.pin = hashlib.sha256(raw).hexdigest()

    def pack(self):
        return HELPER.pack(self.home, self.roster_path, self.pin, self.archive,
                           self.pack_receipt, expected_counts=self.counts)

    def verify(self, pin):
        return HELPER.verify(self.roster_path, self.pin, self.archive, pin,
                             self.verify_receipt, expected_counts=self.counts)

    def first_source(self):
        return self.home / next(iter(self.payloads))

    def mutate_same_size(self, path):
        info = path.stat()
        original = path.read_bytes()
        path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
        os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))

    def assert_preflight_failure(self):
        with self.assertRaises((HELPER.CustodyError, OSError)):
            self.pack()
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.pack_receipt.exists())

    def rewrite_archive(self, transform):
        with tarfile.open(self.archive, "r:") as archive:
            members = [(member, archive.extractfile(member).read()) for member in archive]
        with tarfile.open(self.archive, "w", format=tarfile.PAX_FORMAT) as archive:
            for info, payload in transform(members):
                archive.addfile(info, io.BytesIO(payload) if info.isreg() else None)
        return hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def test_roundtrip_exact_members_and_receipts(self):
        original_stats = {relative: (self.home / relative).stat() for relative in self.payloads}
        packed = self.pack()
        self.assertEqual(packed["status"], "DELTA_PACKED")
        self.assertEqual(packed["tar_members"], 5)
        self.assertEqual(packed["archive_sha256"], hashlib.sha256(self.archive.read_bytes()).hexdigest())
        with tarfile.open(self.archive, "r:") as archive:
            self.assertEqual(set(archive.getnames()), set(self.payloads) | {HELPER.ROSTER_MEMBER})
            self.assertEqual(archive.extractfile(HELPER.ROSTER_MEMBER).read(), self.roster_path.read_bytes())
        with mock.patch.object(HELPER, "source_file", side_effect=AssertionError("No source access")):
            verified = self.verify(packed["archive_sha256"])
        self.assertEqual(verified["status"], "DELTA_VERIFIED")
        self.assertFalse(verified["extraction_performed"])
        for relative, before in original_stats.items():
            after = (self.home / relative).stat()
            self.assertEqual(HELPER.fingerprint(before), HELPER.fingerprint(after))
        self.assertEqual(json.loads(self.verify_receipt.read_text())["archive_sha256"],
                         packed["archive_sha256"])

    def test_production_counts_are_not_relaxed_by_cli(self):
        with self.assertRaisesRegex(HELPER.CustodyError, "348\\+419"):
            HELPER.load_roster(self.roster_path, self.pin)

    def test_wrong_external_roster_pin(self):
        self.pin = "0" * 64
        self.assert_preflight_failure()

    def test_existing_archive_preserved(self):
        self.archive.write_bytes(b"previous custody")
        with self.assertRaises(HELPER.CustodyError):
            self.pack()
        self.assertEqual(self.archive.read_bytes(), b"previous custody")
        self.assertFalse(self.pack_receipt.exists())

    def test_existing_pack_receipt_preserved(self):
        self.pack_receipt.write_bytes(b"previous receipt")
        with self.assertRaises(HELPER.CustodyError):
            self.pack()
        self.assertEqual(self.pack_receipt.read_bytes(), b"previous receipt")
        self.assertFalse(self.archive.exists())

    def test_existing_verify_receipt_preserved(self):
        packed = self.pack()
        self.verify_receipt.write_bytes(b"previous verify")
        with self.assertRaises(HELPER.CustodyError):
            self.verify(packed["archive_sha256"])
        self.assertEqual(self.verify_receipt.read_bytes(), b"previous verify")

    def test_source_size_change_rejected_before_output(self):
        with self.first_source().open("ab") as stream:
            stream.write(b"changed")
        self.assert_preflight_failure()

    def test_source_mtime_change_rejected_before_output(self):
        path = self.first_source()
        info = path.stat()
        os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 1))
        self.assert_preflight_failure()

    def test_source_same_size_and_mtime_hash_change_rejected(self):
        self.mutate_same_size(self.first_source())
        self.assert_preflight_failure()

    def test_source_mode_change_rejected(self):
        self.first_source().chmod(0o600)
        self.assert_preflight_failure()

    def test_leaf_symlink_rejected(self):
        path = self.first_source()
        other = self.base / "other"
        path.rename(other)
        path.symlink_to(other)
        self.assert_preflight_failure()

    def test_parent_symlink_rejected(self):
        directory = self.home / "v6_out"
        other = self.home / "moved"
        directory.rename(other)
        directory.symlink_to(other, target_is_directory=True)
        self.assert_preflight_failure()

    def test_home_symlink_rejected(self):
        alias = self.base / "alias"
        alias.symlink_to(self.home, target_is_directory=True)
        self.home = alias
        self.assert_preflight_failure()

    def test_roster_leaf_symlink_rejected(self):
        alias = self.base / "alias.json"
        alias.symlink_to(self.roster_path)
        self.roster_path = alias
        self.assert_preflight_failure()

    def test_output_parent_symlink_rejected(self):
        alias = self.base / "alias"
        alias.symlink_to(self.base, target_is_directory=True)
        self.archive = alias / "new.tar"
        self.assert_preflight_failure()

    def test_output_inside_source_tree_rejected(self):
        self.archive = self.home / "v6_out" / "new.tar"
        self.assert_preflight_failure()

    def test_verify_receipt_inside_source_tree_rejected(self):
        packed = self.pack()
        self.verify_receipt = self.home / "astra_sources" / "verify.json"
        with self.assertRaises(HELPER.CustodyError):
            self.verify(packed["archive_sha256"])
        self.assertFalse(self.verify_receipt.exists())

    def test_traversal_absolute_and_noncanonical_paths_rejected(self):
        original = copy.deepcopy(self.data)
        for relative in ("../escape", "/absolute", "noise/../escape", "noise//file", "noise/./file", "noise\\file"):
            with self.subTest(relative=relative):
                self.data = copy.deepcopy(original)
                record = self.data["missing_files"][0]
                record["relative_path"] = relative
                record["source_payload"]["relative_path"] = "v6_out/" + relative
                self.save_roster()
                self.assert_preflight_failure()

    def test_duplicate_manifest_members_rejected(self):
        self.data["missing_files"].append(copy.deepcopy(self.data["missing_files"][0]))
        self.data["summary"]["missing_files"] = 2
        self.counts = (3, 2)
        self.save_roster()
        with self.assertRaisesRegex(HELPER.CustodyError, "Duplicate"):
            self.pack()
        self.assertFalse(self.archive.exists())

    def test_snapshot_manifest_digest_rejected(self):
        self.data["source_snapshots"][0]["member_manifest_sha256"] = "0" * 64
        self.save_roster()
        self.assert_preflight_failure()

    def test_source_stat_binding_rejected(self):
        self.data["missing_files"][0]["source"]["mtime_ns"] += 1
        self.save_roster()
        self.assert_preflight_failure()

    def test_fifo_source_rejected_without_blocking(self):
        path = self.first_source()
        path.unlink()
        os.mkfifo(path)
        self.assert_preflight_failure()

    def test_change_during_pack_preserves_partial_and_error(self):
        original = HELPER.add_source
        called = False

        def changed(archive, home_fd, entry, identity):
            nonlocal called
            if not called:
                called = True
                self.mutate_same_size(self.home / entry.name)
            return original(archive, home_fd, entry, identity)

        with mock.patch.object(HELPER, "add_source", side_effect=changed):
            with self.assertRaises(HELPER.CustodyError):
                self.pack()
        self.assertTrue(self.archive.exists())
        self.assertEqual(json.loads(self.pack_receipt.read_text())["status"],
                         "ERROR_PARTIAL_ARCHIVE_PRESERVED")

    def test_change_after_last_member_fails_postcheck(self):
        original = HELPER.check_sources

        def changed(home_fd, entries, expected_identities=None):
            if expected_identities is not None:
                self.mutate_same_size(self.home / entries[0].name)
            return original(home_fd, entries, expected_identities)

        with mock.patch.object(HELPER, "check_sources", side_effect=changed):
            with self.assertRaises(HELPER.CustodyError):
                self.pack()
        self.assertTrue(self.archive.exists())
        self.assertEqual(json.loads(self.pack_receipt.read_text())["status"],
                         "ERROR_PARTIAL_ARCHIVE_PRESERVED")

    def test_source_replaced_with_identical_bytes_rejected(self):
        original = HELPER.add_source
        called = False

        def replaced(archive, home_fd, entry, identity):
            nonlocal called
            if not called:
                called = True
                path = self.home / entry.name
                info = path.stat()
                replacement = self.base / "replacement"
                replacement.write_bytes(path.read_bytes())
                replacement.chmod(entry.mode)
                os.utime(replacement, ns=(info.st_atime_ns, info.st_mtime_ns))
                replacement.replace(path)
            return original(archive, home_fd, entry, identity)

        with mock.patch.object(HELPER, "add_source", side_effect=replaced):
            with self.assertRaises(HELPER.CustodyError):
                self.pack()
        self.assertTrue(self.archive.exists())

    def test_duplicate_tar_member_rejected(self):
        self.pack()
        pin = self.rewrite_archive(lambda members: members + [members[0]])
        with self.assertRaisesRegex(HELPER.CustodyError, "duplicate"):
            self.verify(pin)
        self.assertTrue(self.archive.exists())

    def test_tar_path_traversal_rejected(self):
        self.pack()

        def transform(members):
            info, payload = members[0]
            info.name = "../escape"
            return [(info, payload)] + members[1:]

        pin = self.rewrite_archive(transform)
        with self.assertRaisesRegex(HELPER.CustodyError, "Unsafe"):
            self.verify(pin)
        self.assertFalse((self.base / "escape").exists())

    def test_tar_symlink_rejected(self):
        self.pack()

        def transform(members):
            info, payload = members[0]
            info.type, info.size, info.linkname = tarfile.SYMTYPE, 0, "../elsewhere"
            return [(info, b"")] + members[1:]

        pin = self.rewrite_archive(transform)
        with self.assertRaisesRegex(HELPER.CustodyError, "Nonregular"):
            self.verify(pin)

    def test_missing_member_rejected(self):
        self.pack()
        pin = self.rewrite_archive(lambda members: members[:-1])
        with self.assertRaisesRegex(HELPER.CustodyError, "missing"):
            self.verify(pin)

    def test_payload_corruption_rejected_even_with_new_archive_pin(self):
        self.pack()

        def transform(members):
            info, payload = members[-1]
            return members[:-1] + [(info, bytes([payload[0] ^ 1]) + payload[1:])]

        pin = self.rewrite_archive(transform)
        with self.assertRaisesRegex(HELPER.CustodyError, "payload hash"):
            self.verify(pin)
        self.assertEqual(json.loads(self.verify_receipt.read_text())["status"], "ERROR_ARCHIVE_PRESERVED")

    def test_embedded_roster_bytes_must_match_exactly(self):
        self.pack()

        def transform(members):
            info, payload = members[0]
            return [(info, b" " + payload[1:])] + members[1:]

        pin = self.rewrite_archive(transform)
        with self.assertRaisesRegex(HELPER.CustodyError, "payload hash"):
            self.verify(pin)

    def test_nonzero_trailing_data_rejected(self):
        self.pack()
        with self.archive.open("ab") as stream:
            stream.write(b"unexpected trailing bytes")
        with self.assertRaisesRegex(HELPER.CustodyError, "trailing"):
            self.verify(hashlib.sha256(self.archive.read_bytes()).hexdigest())

    def test_wrong_archive_pin_rejected(self):
        self.pack()
        with self.assertRaisesRegex(HELPER.CustodyError, "Archive SHA256"):
            self.verify("0" * 64)

    def test_truncated_archive_preserved_on_failure(self):
        packed = self.pack()
        self.archive.write_bytes(self.archive.read_bytes()[:1024])
        with self.assertRaises((HELPER.CustodyError, tarfile.TarError)):
            self.verify(packed["archive_sha256"])
        self.assertEqual(self.archive.stat().st_size, 1024)

    def test_exclusive_create_race_does_not_overwrite(self):
        original = HELPER.open_local

        def raced(path, exclusive=False):
            if exclusive and Path(path) == self.archive and not self.archive.exists():
                self.archive.write_bytes(b"other owner won")
            return original(path, exclusive)

        with mock.patch.object(HELPER, "open_local", side_effect=raced):
            with self.assertRaises(FileExistsError):
                self.pack()
        self.assertEqual(self.archive.read_bytes(), b"other owner won")
        self.assertFalse(self.pack_receipt.exists())

    def test_archive_write_error_preserves_partial_and_error_receipt(self):
        original = HELPER.HashWriter.write
        calls = 0

        def failed(writer, chunk):
            nonlocal calls
            calls += 1
            if calls == 1:
                original(writer, chunk[:512])
                raise OSError("synthetic storage failure")
            return original(writer, chunk)

        with mock.patch.object(HELPER.HashWriter, "write", new=failed):
            with self.assertRaises(OSError):
                self.pack()
        self.assertTrue(self.archive.exists())
        self.assertGreaterEqual(self.archive.stat().st_size, 512)
        self.assertEqual(json.loads(self.pack_receipt.read_text())["status"],
                         "ERROR_PARTIAL_ARCHIVE_PRESERVED")

    def test_tar_hardlink_rejected(self):
        self.pack()

        def transform(members):
            info, payload = members[0]
            info.type, info.size, info.linkname = tarfile.LNKTYPE, 0, members[1][0].name
            return [(info, b"")] + members[1:]

        pin = self.rewrite_archive(transform)
        with self.assertRaisesRegex(HELPER.CustodyError, "Nonregular"):
            self.verify(pin)

    def test_verify_archive_symlink_rejected(self):
        packed = self.pack()
        alias = self.base / "archive-alias.tar"
        alias.symlink_to(self.archive)
        self.archive = alias
        with self.assertRaises(OSError):
            self.verify(packed["archive_sha256"])
        self.assertFalse(self.verify_receipt.exists())


if __name__ == "__main__":
    unittest.main()
