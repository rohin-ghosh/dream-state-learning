"""Synthetic standard-library custody fixtures; no live/native evidence is read."""
import contextlib
import gzip
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import astra_q0_archive_check_20260913 as check


class ArchiveCustodyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest = b'{"fixture_only":true}\n'
        self.manifest_hash = check.sha256(self.manifest)

    def members(self, *, failed=False, finalized=True, abort=False, large=False):
        files = {"manifest.json": self.manifest, "prepared.json": b"opaque preparation bytes",
                 "RESOURCE.json": b"not parsed as science", "reduction.json": b"not parsed as science",
                 "stages/opaque.bin": b"\x00\xffNOT A TENSOR FORMAT" * (130000 if large else 1)}
        if failed:
            files["FAILED.json"] = b"opaque failure record; custody does not reinterpret it"
        files["SEAL.json"] = check.canonical(dict(version=check.VERSION, evidence_kind=check.EVIDENCE_KIND,
            classification="PENDING_DURABLE_FINALIZATION", files={name: check.sha256(data) for name, data in files.items()}))
        if finalized:
            files["FINALIZED.json"] = check.canonical(dict(seal_sha256=check.sha256(files["SEAL.json"]),
                                                         evidence_durable_unix=123., elapsed_seconds=10.))
        if abort:
            files["FINALIZATION_ABORT.json"] = check.canonical(dict(seal_sha256=check.sha256(files["SEAL.json"]),
                finalized_sha256=check.sha256(files.get("FINALIZED.json", b"")), observed_unix=9999., elapsed_seconds=2701.))
        return [("./", None, tarfile.DIRTYPE), ("./stages/", None, tarfile.DIRTYPE)] + [
            ("./" + name, data, tarfile.REGTYPE) for name, data in files.items()]

    def archive(self, members, *, compressed=True):
        path = self.root / ("fixture.tgz" if compressed else "fixture.tar")
        with tarfile.open(path, "w:gz" if compressed else "w", format=tarfile.PAX_FORMAT) as archive:
            for name, data, kind in members:
                member = tarfile.TarInfo(name)
                member.type = kind
                member.size = len(data) if data is not None else 0
                if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                    member.linkname = "manifest.json"
                archive.addfile(member, io.BytesIO(data) if data is not None else None)
        return path

    def validate(self, path, **kwargs):
        return check.validate_archive(path, archive_sha256=kwargs.get("archive_sha256", check.sha256(path.read_bytes())),
                                      manifest_sha256=kwargs.get("manifest_sha256", self.manifest_hash))

    def reject(self, members, message):
        with self.assertRaisesRegex(check.CustodyError, message):
            self.validate(self.archive(members))

    def change_json(self, members, name, change):
        result = []
        for filename, data, kind in members:
            if filename == "./" + name:
                value = json.loads(data)
                change(value)
                data = check.canonical(value)
            result.append((filename, data, kind))
        return result

    def test_normal_tar_and_tgz_counts_and_manifest_binding(self):
        for compressed in (False, True):
            with self.subTest(compressed=compressed):
                members = self.members()
                path = self.archive(members, compressed=compressed)
                result = self.validate(path)
                self.assertTrue(result["custody_valid"])
                self.assertEqual(result["file_count"], 7)
                self.assertEqual(result["sealed_file_count"], 5)
                self.assertEqual(result["directory_count"], 2)
                self.assertEqual(result["regular_file_bytes"], sum(len(data) for _, data, _ in members if data is not None))
                self.assertEqual(result["archive_bytes"], path.stat().st_size)
                self.assertEqual(result["prepared_manifest_sha256"], self.manifest_hash)
                self.assertEqual(result["final_witness_status"], "PRESENT_HASH_BOUND")
                self.assertFalse(result["scientific_replay"])
                self.assertFalse(result["scientific_ready"])

    def test_failed_and_finalization_abort_roots_are_valid_custody(self):
        result = self.validate(self.archive(self.members(failed=True, abort=True)))
        self.assertTrue(result["custody_valid"])
        self.assertTrue(result["failure_record_present"])
        self.assertTrue(result["finalization_abort_present"])
        self.assertFalse(result["scientific_replay"])

    def test_missing_final_witness_is_explicit_not_ready(self):
        result = self.validate(self.archive(self.members(finalized=False)))
        self.assertTrue(result["custody_valid"])
        self.assertIsNone(result["finalized_sha256"])
        self.assertEqual(result["scientific_readiness"], "NOT_SCIENTIFIC_READY_MISSING_FINAL_WITNESS")
        self.assertFalse(result["scientific_ready"])

    def test_abort_without_completion_cannot_invent_hash_binding(self):
        self.reject(self.members(finalized=False, abort=True), "requires FINALIZED")

    def test_extra_file_is_rejected(self):
        self.reject(self.members() + [("./extra", b"unexpected", tarfile.REGTYPE)], "exact inventory")

    def test_missing_file_and_missing_seal_rejected(self):
        for name, message in (("./prepared.json", "exact inventory"), ("./SEAL.json", "missing SEAL"),
                              ("./manifest.json", "missing manifest")):
            with self.subTest(name=name):
                self.reject([item for item in self.members() if item[0] != name], message)

    def test_duplicate_and_normalized_alias_members_rejected(self):
        for name, data, kind in (("./manifest.json", self.manifest, tarfile.REGTYPE),
                                 ("manifest.json", self.manifest, tarfile.REGTYPE),
                                 ("././manifest.json", self.manifest, tarfile.REGTYPE),
                                 (".", None, tarfile.DIRTYPE), ("stages", None, tarfile.DIRTYPE)):
            with self.subTest(name=name):
                self.reject(self.members() + [(name, data, kind)], "duplicate archive member")

    def test_traversal_absolute_windows_and_control_paths_rejected(self):
        for name in ("../evil", "./../evil", "/absolute", "./nested/../../evil", "a/../b", "a/./b",
                     "a//b", "C:/evil", "./C:/evil", "a\\b", "./bad\nname"):
            with self.subTest(name=name):
                self.reject(self.members() + [(name, b"bad", tarfile.REGTYPE)], "unsafe archive member")

    def test_regular_file_cannot_claim_root(self):
        self.reject(self.members() + [("./", b"bad", tarfile.REGTYPE)], "unsafe archive member")

    def test_links_and_special_files_rejected(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE, tarfile.CHRTYPE, tarfile.BLKTYPE):
            with self.subTest(kind=kind):
                self.reject(self.members() + [("./special", None, kind)], "links and special")

    def test_file_directory_collisions_both_orders_rejected(self):
        for tail in ([('a', b'data', tarfile.REGTYPE), ('a/b', b'data', tarfile.REGTYPE)],
                     [('a/b', b'data', tarfile.REGTYPE), ('a', b'data', tarfile.REGTYPE)]):
            with self.subTest(tail=tail):
                self.reject(self.members() + tail, "file/directory path collision")

    def test_caller_archive_hash_and_manifest_hash_drift_rejected(self):
        path = self.archive(self.members())
        for kwargs, message in ((dict(archive_sha256="0" * 64), "archive SHA256 mismatch"),
                                (dict(manifest_sha256="0" * 64), "manifest SHA256 mismatch"),
                                (dict(archive_sha256="bad"), "64-hex")):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(check.CustodyError, message):
                self.validate(path, **kwargs)

    def test_member_data_drift_rejected_even_with_new_archive_hash(self):
        members = [(name, b"drift" if name == "./prepared.json" else data, kind)
                   for name, data, kind in self.members()]
        self.reject(members, "exact inventory")

    def test_seal_hash_drift_detected_by_completion(self):
        members = self.change_json(self.members(), "SEAL.json", lambda value: value.update(extra="changed bytes"))
        self.reject(members, "FINALIZED seal hash")

    def test_final_and_abort_witness_hash_drifts_rejected(self):
        for name, field in (("FINALIZED.json", "seal_sha256"), ("FINALIZATION_ABORT.json", "seal_sha256"),
                            ("FINALIZATION_ABORT.json", "finalized_sha256")):
            with self.subTest(name=name, field=field):
                members = self.change_json(self.members(abort=True), name, lambda value: value.update({field: "0" * 64}))
                self.reject(members, "hash binding mismatch")

    def test_noncanonical_seal_path_and_invalid_pin_rejected(self):
        for name, value in (("../evil", "0" * 64), ("./alias", "0" * 64),
                            ("SEAL.json", "0" * 64), ("extra", "bad")):
            with self.subTest(name=name):
                members = self.change_json(self.members(), "SEAL.json", lambda seal: seal["files"].update({name: value}))
                self.reject(members, "unsafe|noncanonical|invalid SEAL")

    def test_wrong_seal_identity_rejected(self):
        for field in ("version", "evidence_kind", "classification"):
            with self.subTest(field=field):
                self.reject(self.change_json(self.members(), "SEAL.json", lambda seal: seal.update({field: "bad"})),
                            "seal identity")

    def test_duplicate_and_malformed_json_rejected(self):
        for data in (b'{"files":{},"files":{}}', b'not JSON', b'[]', b'{"bad":NaN}'):
            with self.subTest(data=data):
                members = [(name, data if name == "./SEAL.json" else content, kind)
                           for name, content, kind in self.members()]
                self.reject(members, "duplicate JSON|malformed|JSON object|nonfinite")

    def test_metadata_size_is_bounded(self):
        with patch.object(check, "MAX_METADATA_BYTES", 8):
            self.reject(self.members(), "bounded metadata")

    def test_opaque_large_payload_is_streamed_without_extraction_or_deserialization(self):
        path = self.archive(self.members(large=True))
        before = set(self.root.iterdir())
        with patch.object(tarfile.TarFile, "extract", side_effect=AssertionError("no extraction")), \
                patch.object(tarfile.TarFile, "extractall", side_effect=AssertionError("no extraction")):
            result = self.validate(path)
        self.assertGreater(result["regular_file_bytes"], 2 * check.CHUNK_BYTES)
        self.assertEqual(set(self.root.iterdir()), before)
        self.assertFalse(result["extracted"])
        self.assertFalse(result["tensors_deserialized"])

    def test_truncated_gzip_and_corrupt_gzip_crc_rejected(self):
        for corrupt_crc in (False, True):
            with self.subTest(corrupt_crc=corrupt_crc):
                path = self.archive(self.members())
                data = path.read_bytes()
                path.write_bytes(data[:-8] + bytes([data[-8] ^ 1]) + data[-7:] if corrupt_crc else data[:-6])
                with self.assertRaises(check.CustodyError):
                    self.validate(path)

    def test_truncated_tar_payload_rejected(self):
        path = self.archive(self.members(large=True), compressed=False)
        with tarfile.open(path, "r:") as archive:
            member = archive.getmember("./stages/opaque.bin")
            truncate_at = member.offset_data + member.size - 1
        with path.open("r+b") as stream:
            stream.truncate(truncate_at)
        with self.assertRaises(check.CustodyError):
            self.validate(path)

    def test_malformed_compressed_stream_is_a_custody_error(self):
        path = self.archive(self.members())
        data = bytearray(path.read_bytes())
        data[32:48] = b"\xff" * 16
        path.write_bytes(data)
        with self.assertRaises(check.CustodyError):
            self.validate(path)

    def test_concatenated_tar_or_gzip_cannot_hide_extra_members(self):
        for compressed in (False, True):
            with self.subTest(compressed=compressed):
                path = self.archive(self.members(), compressed=compressed)
                original = path.read_bytes()
                extra = io.BytesIO()
                with tarfile.open(fileobj=extra, mode="w") as archive:
                    member = tarfile.TarInfo("extra")
                    member.size = 1
                    archive.addfile(member, io.BytesIO(b"x"))
                path.write_bytes(original + (gzip.compress(extra.getvalue()) if compressed else extra.getvalue()))
                with self.assertRaisesRegex(check.CustodyError, "exact inventory"):
                    self.validate(path)

    def test_cli_reports_custody_only_and_nonzero_on_hash_error(self):
        path = self.archive(self.members())
        stdout, stderr = io.StringIO(), io.StringIO()
        args = [str(path), "--archive-sha256", check.sha256(path.read_bytes()), "--manifest-sha256", self.manifest_hash]
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(check.main(args), 0)
        self.assertFalse(json.loads(stdout.getvalue())["scientific_replay"])
        args[2] = "0" * 64
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(check.main(args), 2)
        self.assertFalse(json.loads(stderr.getvalue())["custody_valid"])


if __name__ == "__main__":
    unittest.main()
