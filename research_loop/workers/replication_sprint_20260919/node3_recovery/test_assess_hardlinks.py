import json
import os
from pathlib import Path
import tempfile
import unittest

import archive_manifest
import assess_hardlinks as subject


class HardlinkAssessmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in archive_manifest.DIRECTORIES:
            (self.root / name).mkdir()
        self.first = self.root / archive_manifest.DIRECTORIES[0] / 'weights.bin'
        self.second = self.root / archive_manifest.DIRECTORIES[1] / 'weights.bin'
        for path in (self.first, self.second):
            path.write_bytes(b'restored' * (1024**2 // 8))
            os.utime(path, ns=(1000000000, 1000000000))

    def invoke(self):
        lines = [json.dumps(item).encode() + b'\n' for item in archive_manifest.inventory(self.root)]
        return subject.analyze(lines, root=self.root)

    def test_exact_metadata_and_allocated_blocks(self):
        result = self.invoke()
        self.assertEqual(result['eligible_groups'], 1)
        self.assertEqual(result['eligible_allocated_bytes_potential'], self.second.stat().st_blocks * 512)
        self.assertEqual(result['bytes_actually_reclaimed'], 0)
        self.assertNotEqual(self.first.stat().st_ino, self.second.stat().st_ino)

    def test_different_mtime_not_eligible(self):
        os.utime(self.second, ns=(1000000000, 2000000000))
        self.assertEqual(self.invoke()['eligible_groups'], 0)

    def test_external_hardlinks_prevent_counting_unfreed_blocks(self):
        os.link(self.first, self.root / 'outside_first')
        os.link(self.second, self.root / 'outside_second')
        result = self.invoke()
        self.assertEqual(result['eligible_groups'], 1)
        self.assertEqual(result['eligible_allocated_bytes_potential'], 0)
        self.assertEqual(result['inodes_with_external_links'], 2)

    def test_existing_hardlink_paths_count_original_inode_once(self):
        os.link(self.second, self.second.with_name('also_weights.bin'))
        result = self.invoke()
        self.assertEqual(result['existing_hardlinked_extra_paths'], 1)
        self.assertEqual(result['eligible_allocated_bytes_potential'], self.second.stat().st_blocks * 512)


if __name__ == '__main__':
    unittest.main()
