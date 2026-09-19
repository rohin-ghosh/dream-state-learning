import hashlib
from pathlib import Path
import tempfile
import unittest

from audit import compare, hash_file


class ReadOnlyAuditTests(unittest.TestCase):
    def test_identical_independent_files_and_no_atime_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            survivor = Path(directory) / "survivor"
            source.write_bytes(b"preserved evidence")
            survivor.write_bytes(b"preserved evidence")
            first = hash_file(source, 100)
            second = hash_file(survivor, 100)
            self.assertTrue(compare(first, second))
            self.assertNotEqual(first["before"]["inode"], second["before"]["inode"])
            self.assertEqual(first["sha256"], hashlib.sha256(b"preserved evidence").hexdigest())
            self.assertEqual(first["before"], first["after_path"])

    def test_same_size_different_contents_are_not_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            survivor = Path(directory) / "survivor"
            source.write_bytes(b"first")
            survivor.write_bytes(b"other")
            self.assertFalse(compare(hash_file(source, 100), hash_file(survivor, 100)))

    def test_missing_survivor_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            result = hash_file(Path(directory) / "absent", 100)
            self.assertEqual(result["status"], "blocked")
            self.assertFalse(compare(result, result))

    def test_symlink_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.write_bytes(b"evidence")
            link = Path(directory) / "link"
            link.symlink_to(source)
            result = hash_file(link, 100)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["error"]["message"], "redirected_path")

    def test_size_bound_is_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.write_bytes(b"evidence")
            self.assertEqual(hash_file(source, 2)["status"], "blocked")

    def test_metadata_or_historical_presence_is_not_equality(self):
        self.assertFalse(compare({"before": {"size": 10}}, {"before": {"size": 10}}))


if __name__ == "__main__":
    unittest.main()
