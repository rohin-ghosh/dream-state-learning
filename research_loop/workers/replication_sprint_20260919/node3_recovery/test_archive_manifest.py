import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import archive_manifest as subject


class ArchiveManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in subject.DIRECTORIES:
            (self.root / name).mkdir()
        self.file = self.root / subject.DIRECTORIES[0] / 'state.bin'
        self.file.write_bytes(bytes(range(256)) * 100)
        os.setxattr(self.file, 'user.recovery_test', b'\x00exact\xffbytes')
        os.link(self.file, self.file.with_name('state_hardlink.bin'))
        self.file.with_name('link').symlink_to('state.bin')
        self.manifest = self.root / 'manifest.jsonl'
        self.entries = list(subject.inventory(self.root))
        self.manifest.write_text(''.join(json.dumps(item) + '\n' for item in self.entries))
        self.archive = subprocess.check_output(['tar', '--format=pax', '--acls', '--xattrs',
            '--xattrs-include=*', '--selinux', '--numeric-owner', '--sort=name',
            '--sparse', '--atime-preserve=system', '-C', str(self.root), '-cf', '-',
            *subject.DIRECTORIES])

    def test_restores_exact_bytes_metadata_and_links(self):
        result = subject.verify_stream(self.manifest, io.BytesIO(self.archive))
        self.assertEqual(result['members'], len(self.entries))
        self.assertEqual(result['owner_available_bytes_reclaimed'], 0)
        self.assertFalse(result['physical_extraction_performed'])
        self.assertEqual(self.entries, list(subject.inventory(self.root)))

    def test_changed_source_hash_fails(self):
        for item in self.entries:
            if item['kind'] == 'file':
                item['sha256'] = '0' * 64
        self.manifest.write_text(''.join(json.dumps(item) + '\n' for item in self.entries))
        with self.assertRaisesRegex(ValueError, 'restored_bytes_mismatch'):
            subject.verify_stream(self.manifest, io.BytesIO(self.archive))

    def test_missing_or_extra_member_fails(self):
        self.entries = [item for item in self.entries if not item['path'].endswith('/state.bin')]
        self.manifest.write_text(''.join(json.dumps(item) + '\n' for item in self.entries))
        with self.assertRaisesRegex(ValueError, 'unexpected_duplicate_member'):
            subject.verify_stream(self.manifest, io.BytesIO(self.archive))

    def test_numeric_ownership_remapping_fails(self):
        self.entries[0]['uid'] += 1
        self.manifest.write_text(''.join(json.dumps(item) + '\n' for item in self.entries))
        with self.assertRaisesRegex(ValueError, 'numeric_metadata_mismatch'):
            subject.verify_stream(self.manifest, io.BytesIO(self.archive))


if __name__ == '__main__':
    unittest.main()
