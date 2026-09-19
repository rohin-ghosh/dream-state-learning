"""Regression checks for the read-only native filesystem-view observer."""

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import native_view_probe as observer


class NativeViewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.journal = self.root / 'journal'
        self.journal.mkdir()
        for name in ('records', 'inbox'):
            (self.journal / name).mkdir()
        for name in ('JOURNAL.json', 'WRITER.lock'):
            (self.journal / name).write_text('{}')
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'module.py').write_text('value = 1\n')
        self.epoch = self.root / 'epoch.json'
        self.epoch.write_text('{}')
        self.record = self.journal / 'records' / ('0' * 20 + '.json')
        self.record.write_text('{}')
        intent = self.record.with_name('0' * 20 + '.intent.json')
        intent.write_text('{}')
        root_descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
        try:
            descriptor, chain = observer.open_directory(root_descriptor, self.journal)
            os.close(descriptor)
            source_files = []
            for path in (self.epoch, self.source / 'module.py'):
                descriptor, parent_chain = observer.open_directory(root_descriptor, path.parent)
                os.close(descriptor)
                source_files.append(dict(path=str(path), chain=parent_chain,
                    identity=observer.file_identity(path.stat())))
            descriptor, source_chain = observer.open_directory(root_descriptor, self.source)
            os.close(descriptor)
        finally:
            os.close(root_descriptor)
        self.proof = dict(binding=dict(selection=dict(root=str(self.journal), complete_index=0),
            source=dict(root=str(self.source), pins={'module.py': self.sha(self.source / 'module.py')},
                epoch=dict(path=str(self.epoch), sha256=self.sha(self.epoch))),
            environment=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())),
            source_objects=dict(files=source_files, directories=[dict(path=str(self.source),
                chain=source_chain, identity=observer.immutable_directory_identity(self.source.stat()))]),
            locations=dict(root_chain=chain,
                manifest=observer.file_identity((self.journal / 'JOURNAL.json').stat()),
                writer_lock=observer.file_identity((self.journal / 'WRITER.lock').stat()),
                records=observer.directory_identity((self.journal / 'records').stat()),
                inbox=observer.directory_identity((self.journal / 'inbox').stat())),
            records=[dict(header=dict(index=0), identities={'.json': observer.file_identity(self.record.stat()),
                '.intent.json': observer.file_identity(intent.stat())})])
        self.path = self.root / 'proof.json'
        self.path.write_text(json.dumps(self.proof))
        self.pid = os.getpid()
        self.start_ticks = Path('/proc/self/stat').read_text().rsplit(') ', 1)[1].split()[19]

    @staticmethod
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def run_probe(self, **changes):
        arguments = dict(proof_path=self.path, proof_sha256=self.sha(self.path), pid=self.pid,
            start_ticks=self.start_ticks, uid=os.getuid())
        arguments.update(changes)
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=''):
            return observer.probe(**arguments)

    def test_complete_read_only_view_and_identity(self):
        result = self.run_probe()
        self.assertEqual(result['verified_prefix_files'], 2)
        self.assertEqual(result['source_files'], 1)
        self.assertEqual(result['source_epoch_files'], 1)
        self.assertEqual(result['source_directories'], 1)
        self.assertTrue(result['source_identity_attested'])
        self.assertEqual(result['verification_passes'], 2)
        self.assertFalse(result['source_startup_or_admission_proven'])
        self.assertFalse(result['live_adoption'])
        self.assertEqual(result['native_signals'], [])

    def test_pinned_proof_and_exact_native_required(self):
        with self.assertRaisesRegex(ValueError, 'exact_operator_pinned_proof'):
            self.run_probe(proof_sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'exact_live_unstopped_native'):
            self.run_probe(start_ticks=str(int(self.start_ticks) + 1))

    def test_changed_size_detected_even_if_mtime_restored(self):
        before = self.record.stat()
        self.record.write_text('{"changed":true}')
        os.utime(self.record, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, 'same_prefix_file_identity'):
            self.run_probe()

    def test_symlink_prefix_rejected(self):
        original = self.record.with_suffix('.saved')
        self.record.rename(original)
        self.record.symlink_to(original)
        with self.assertRaisesRegex(ValueError, 'regular_file_required'):
            self.run_probe()

    def test_changed_source_and_root_rejected(self):
        (self.source / 'module.py').write_text('value = 2\n')
        with self.assertRaisesRegex(ValueError, 'same_producer_source_or_epoch_identity|same_source_or_epoch_bytes'):
            self.run_probe()
        self.proof['locations']['root_chain'][-1]['ino'] += 1
        self.path.write_text(json.dumps(self.proof))
        with self.assertRaisesRegex(ValueError, 'same_entire_root_chain'):
            self.run_probe()

    def test_boot_and_record_index_rejected(self):
        self.proof['records'][0]['header']['index'] = 1
        self.path.write_text(json.dumps(self.proof))
        with self.assertRaisesRegex(ValueError, 'contiguous_proof_record_indices'):
            self.run_probe()
        self.proof['binding']['environment']['boot_id'] = 'not-this-boot'
        self.path.write_text(json.dumps(self.proof))
        with self.assertRaisesRegex(ValueError, 'same_kernel_boot'):
            self.run_probe()

    def test_byte_identical_source_replacement_rejected(self):
        replacement = self.root / 'replacement.py'
        replacement.write_bytes((self.source / 'module.py').read_bytes())
        replacement.replace(self.source / 'module.py')
        with self.assertRaisesRegex(ValueError, 'same_producer_source_or_epoch_identity'):
            self.run_probe()

    def test_byte_identical_epoch_replacement_rejected(self):
        replacement = self.root / 'replacement.json'
        replacement.write_bytes(self.epoch.read_bytes())
        replacement.replace(self.epoch)
        with self.assertRaisesRegex(ValueError, 'same_producer_source_or_epoch_identity'):
            self.run_probe()

    def test_source_directory_metadata_rejected(self):
        self.source.chmod(0o700 if self.source.stat().st_mode & 0o777 != 0o700 else 0o755)
        with self.assertRaisesRegex(ValueError, 'same_source_file_directory_chain|same_immutable_source_directory_metadata'):
            self.run_probe()

    def test_source_file_parent_chain_rejected(self):
        self.proof['source_objects']['files'][-1]['chain'][-1]['ino'] += 1
        self.path.write_text(json.dumps(self.proof))
        with self.assertRaisesRegex(ValueError, 'same_source_file_directory_chain'):
            self.run_probe()

    def test_source_directory_full_metadata_rejected(self):
        self.proof['source_objects']['directories'][0]['identity']['mtime_ns'] -= 1
        self.path.write_text(json.dumps(self.proof))
        with self.assertRaisesRegex(ValueError, 'same_immutable_source_directory_metadata'):
            self.run_probe()

    def test_incomplete_source_identity_inventory_rejected(self):
        self.proof['source_objects']['files'].pop(0)
        self.path.write_text(json.dumps(self.proof))
        with self.assertRaisesRegex(ValueError, 'every_source_and_epoch_identity_required'):
            self.run_probe()

    def test_incomplete_source_directory_inventory_rejected(self):
        self.proof['source_objects']['directories'].clear()
        self.path.write_text(json.dumps(self.proof))
        with self.assertRaisesRegex(ValueError, 'every_immutable_source_directory_required'):
            self.run_probe()

    def test_pinned_epoch_hash_is_checked(self):
        self.proof['binding']['source']['epoch']['sha256'] = '0' * 64
        self.path.write_text(json.dumps(self.proof))
        with self.assertRaisesRegex(ValueError, 'same_source_or_epoch_bytes'):
            self.run_probe()


if __name__ == '__main__':
    unittest.main()
