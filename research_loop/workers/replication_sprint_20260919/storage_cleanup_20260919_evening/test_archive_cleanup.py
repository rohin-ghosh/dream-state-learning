from copy import deepcopy
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from archive_cleanup import archive_integrity, exact_archive_binding, validate_reference_scan


class ArchiveCleanupTests(unittest.TestCase):
    def scan(self):
        return dict(scanner_euid=0, scope="all_uid_privileged_fds_and_all_maps",
                    lifetime_protocol="pidfd_start_bound_v1", inaccessible_or_exited=[], writers=[])

    def test_unresolved_live_process_cannot_be_waived(self):
        scan = self.scan()
        scan["inaccessible_or_exited"] = [dict(pid=2499, reason="live_or_unresolved_process_unreadable")]
        with self.assertRaisesRegex(ValueError, "no_uncertainty"):
            validate_reference_scan(scan)

    def test_external_reader_is_blocking_too(self):
        scan = self.scan()
        scan["writers"] = [dict(pid=77, start_ticks=12, fd=3, access_mode=0)]
        with self.assertRaisesRegex(ValueError, "external_reader"):
            validate_reference_scan(scan)

    def test_controlled_reader_requires_exact_pid_lifetime_fd_and_read_mode(self):
        scan = self.scan()
        scan["writers"] = [dict(pid=77, start_ticks=12, fd=3, access_mode=0)]
        validate_reference_scan(scan, {(77, 12, 3)})
        for field, value in (("pid", 78), ("start_ticks", 13), ("fd", 4), ("access_mode", 1)):
            changed = deepcopy(scan)
            changed["writers"][0][field] = value
            with self.assertRaises(ValueError):
                validate_reference_scan(changed, {(77, 12, 3)})

    def test_missing_controlled_reader_is_blocking(self):
        with self.assertRaisesRegex(ValueError, "accounted_for"):
            validate_reference_scan(self.scan(), {(77, 12, 3)})

    def test_nonprivileged_snapshot_cannot_authorize(self):
        scan = self.scan()
        scan["scanner_euid"] = 2524
        with self.assertRaises(ValueError):
            validate_reference_scan(scan)

    def test_archive_paths_are_exact_not_merely_under_parent(self):
        with self.assertRaisesRegex(ValueError, "exact_three_original_archive_paths"):
            exact_archive_binding([{"remote_path": "/retired/wrong.tar.gz"}], "/retired", ["right.tar.gz"])

    def test_full_stream_validation_does_not_extract(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.tar.gz"
            with tarfile.open(path, "w:gz") as archive:
                member = tarfile.TarInfo("history/example.json")
                member.size = 8
                archive.addfile(member, io.BytesIO(b"evidence"))
            result = archive_integrity(path, path.stat().st_size)
            self.assertEqual(result["members"], 1)
            self.assertEqual(result["regular_payload_bytes"], 8)
            self.assertFalse((Path(directory) / "history").exists())

    def test_unsafe_member_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.tar.gz"
            with tarfile.open(path, "w:gz") as archive:
                member = tarfile.TarInfo("../outside")
                archive.addfile(member, io.BytesIO(b""))
            with self.assertRaisesRegex(ValueError, "unsafe_or_unbounded"):
                archive_integrity(path, path.stat().st_size)

    def test_corrupt_gzip_is_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.tar.gz"
            path.write_bytes(b"not gzip")
            with self.assertRaises(OSError):
                archive_integrity(path, path.stat().st_size)

    def test_hardlink_to_previous_verified_payload_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.tar.gz"
            with tarfile.open(path, "w:gz") as archive:
                member = tarfile.TarInfo("history/record.json")
                member.size = 8
                archive.addfile(member, io.BytesIO(b"evidence"))
                linked = tarfile.TarInfo("history/record.partial")
                linked.type = tarfile.LNKTYPE
                linked.linkname = "history/record.json"
                archive.addfile(linked)
            result = archive_integrity(path, path.stat().st_size)
            self.assertEqual(result["validated_hardlinks"], 1)
            self.assertEqual(result["regular_payload_bytes"], 8)

    def test_unproven_hardlinks_are_rejected(self):
        for target in ("../outside", "/outside", "history/missing"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "evidence.tar.gz"
                with tarfile.open(path, "w:gz") as archive:
                    linked = tarfile.TarInfo("history/record.partial")
                    linked.type = tarfile.LNKTYPE
                    linked.linkname = target
                    archive.addfile(linked)
                with self.assertRaisesRegex(ValueError, "hardlink_target_not_previously"):
                    archive_integrity(path, path.stat().st_size)


if __name__ == "__main__":
    unittest.main()
