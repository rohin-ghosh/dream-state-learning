import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from gpu.orch_continual_batch_publish import extract_snapshot_once
from gpu.orch_continual_batch_snapshot import write


class ImmutableSnapshotTests(unittest.TestCase):
    def archive(self, root, entries):
        path = root / 'SOURCE_SNAPSHOT.tar.gz'
        with tarfile.open(path, 'x:gz') as archive:
            for name, data in entries:
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
        return path

    def test_fresh_unique_snapshot_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, [('raw/shard4/call.json', b'original\r\n')])
            destination = root / 'batch_001'
            destination.mkdir()
            extract_snapshot_once(archive, destination)
            self.assertEqual((destination / 'raw/shard4/call.json').read_bytes(), b'original\r\n')

    def test_reextraction_never_overwrites_existing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, [('raw/call.json', b'new')])
            destination = root / 'batch_001'
            (destination / 'raw').mkdir(parents=True)
            (destination / 'raw/call.json').write_bytes(b'preserved')
            with self.assertRaisesRegex(ValueError, 'already_exists'):
                extract_snapshot_once(archive, destination)
            self.assertEqual((destination / 'raw/call.json').read_bytes(), b'preserved')

    def test_duplicate_archive_paths_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, [('raw/call.json', b'first'), ('raw/./call.json', b'second')])
            destination = root / 'batch_001'
            destination.mkdir()
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                extract_snapshot_once(archive, destination)
            self.assertEqual(list(destination.iterdir()), [])

    def test_path_traversal_rejected(self):
        for name in ('../escape', '/absolute'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                archive = self.archive(root, [(name, b'bad')])
                with self.assertRaisesRegex(ValueError, 'unsafe'):
                    extract_snapshot_once(archive, root)

    def test_symlink_parent_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, [('raw/call.json', b'bad')])
            destination = root / 'batch_001'
            destination.mkdir()
            (destination / 'raw').symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'escape'):
                extract_snapshot_once(archive, destination)
            self.assertFalse((root / 'call.json').exists())

    def test_snapshot_json_is_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'CANDIDATES.json'
            write(path, {'original': True})
            initial = path.read_bytes()
            with self.assertRaises(FileExistsError):
                write(path, {'replacement': True})
            self.assertEqual(path.read_bytes(), initial)


if __name__ == '__main__':
    unittest.main()
