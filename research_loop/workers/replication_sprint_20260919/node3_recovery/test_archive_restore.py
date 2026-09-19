from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import archive_restore as subject
import test_archive_manifest as fixtures


class ArchiveRestoreTests(unittest.TestCase):
    def setUp(self):
        fixtures.ArchiveManifestTests.setUp(self)
        self.source_manifest = self.root / 'SOURCE_MANIFEST.jsonl'
        self.source_manifest.write_bytes(self.manifest.read_bytes())
        self.archive_path = self.root / 'retired-node3.tar.zst'
        self.archive_path.write_bytes(subprocess.check_output(['zstd', '-c'], input=self.archive))
        (self.root / 'COPY_VERIFIED.json').write_text(json.dumps(dict(
            status='ALL_ARCHIVE_MEMBERS_STREAM_RESTORED_AND_VERIFIED',
            manifest_sha256=subject.file_sha(self.source_manifest), archive_sha256=subject.file_sha(self.archive_path))))

    def test_complete_filesystem_restore_preserves_source(self):
        with patch.object(subject, 'ROOT', self.root), patch.object(subject.os, 'uname',
                return_value=SimpleNamespace(nodename='ipp2-ovx-p3-02')), \
                patch.object(subject.os, 'statvfs', return_value=SimpleNamespace(f_bavail=100 * 1024**3,
                    f_frsize=1)), redirect_stdout(io.StringIO()):
            subject.main()
        result = json.loads((self.root / 'RESTORE_VERIFIED.json').read_bytes())
        self.assertEqual(result['members'], len(self.entries))
        self.assertEqual(result['owner_available_bytes_reclaimed_on_node3'], 0)
        self.assertTrue(self.file.is_file())

    def test_dedup_counts_independent_inodes_not_existing_hardlinks(self):
        items = [dict(path='r225/data', kind='file', size=1024**2, sha256='1' * 64,
            device=1, inode=1, mode=0o600, uid=1, gid=1, atime_ns=1, mtime_ns=1, ctime_ns=1, xattrs={}),
            dict(path='r233/data', kind='file', size=1024**2, sha256='1' * 64,
            device=1, inode=2, mode=0o600, uid=1, gid=1, atime_ns=1, mtime_ns=2, ctime_ns=2, xattrs={})]
        items.append(dict(items[0], path='r225/existing_hardlink'))
        result = subject.dedup_summary({item['path']: item for item in items})
        self.assertEqual(result['logical_duplicate_bytes'], 1024**2)
        self.assertEqual(result['examples'][0]['path_count'], 3)
        self.assertFalse(result['examples'][0]['identical_all_recorded_metadata'])


if __name__ == '__main__':
    unittest.main()
