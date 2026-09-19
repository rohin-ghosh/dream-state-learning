from pathlib import Path, PurePosixPath
import hashlib
import io
import json
import tarfile
import tempfile
import sys
import types
import unittest
from unittest.mock import patch

import node_epoch4_probe as probe
import remote_epoch4_stage as stage


class StageSafetyTests(unittest.TestCase):
    def archive(self, name, kind=tarfile.REGTYPE, mode=0o444):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w:gz') as output:
            entry = tarfile.TarInfo(name)
            entry.type, entry.mode = kind, mode
            output.addfile(entry, io.BytesIO())
        return stream.getvalue()

    def test_paths_symlinks_and_privileged_modes_refuse(self):
        for name, kind, mode in (('../escape', tarfile.REGTYPE, 0o444),
                ('curriculum_learner/epoch3', tarfile.REGTYPE, 0o444),
                ('curriculum_learner/epoch4', tarfile.SYMTYPE, 0o444),
                ('curriculum_learner/epoch4', tarfile.REGTYPE, 0o4444)):
            raw = self.archive(name, kind, mode)
            with self.subTest(name=name, kind=kind), self.assertRaises(ValueError):
                stage.validated_members(raw, hashlib.sha256(raw).hexdigest(), [PurePosixPath('curriculum_learner/epoch4')])

    def test_archive_pin_is_mandatory(self):
        raw = self.archive('curriculum_learner/epoch4', tarfile.DIRTYPE)
        with self.assertRaisesRegex(ValueError, 'exact_bounded'):
            stage.validated_members(raw, '0' * 64, [PurePosixPath('curriculum_learner/epoch4')])
        self.assertEqual(len(stage.validated_members(raw, hashlib.sha256(raw).hexdigest(),
            [PurePosixPath('curriculum_learner/epoch4')])), 1)

    def test_existing_mismatch_refuses_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / 'fresh'
            target.mkdir()
            path = target / 'one.py'
            path.write_bytes(b'original')
            path.chmod(0o444)
            with patch.object(stage, 'ROOT', root), self.assertRaisesRegex(ValueError, 'existing_bytes_mismatch'):
                stage.verify_existing(PurePosixPath('fresh'), [(PurePosixPath('fresh/one.py'), 0o444, b'changed')])
            self.assertEqual(path.read_bytes(), b'original')

    def test_frozen_family_initial_explicit_and_never_plain_journal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initial = root / 'raw/checkpoints/initial/COMMIT.json'
            initial.parent.mkdir(parents=True)
            initial.write_text('{"optimizer_steps":0}')
            frozen = type('FrozenJournal', (), {'__module__': 'gpu.r232_recovery'})
            learner = type('LearnerJournal', (), {'__module__': 'gpu.r232_recovery'})
            runtime = types.SimpleNamespace(ROOTS={1: root}, frozen=types.SimpleNamespace(INITIAL=None),
                FrozenJournal=frozen, LearnerJournal=learner)
            native = types.SimpleNamespace(read=lambda path: json.loads(path.read_bytes()))
            with patch.object(probe.importlib, 'import_module', side_effect=[native, runtime]):
                selected, receipt = probe.family(dict(physical=1))
            self.assertIs(selected, frozen)
            self.assertEqual(runtime.frozen.INITIAL, {'optimizer_steps': 0})
            self.assertTrue(receipt['frozen_INITIAL_explicitly_initialized'])
            self.assertEqual(receipt['journal_type'], 'gpu.r232_recovery:FrozenJournal')

    def test_INBOX_snapshot_does_not_register_or_edit_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'inbox').mkdir()
            path = root / 'inbox/arriving.json'
            path.write_bytes(b'{"id":"arriving","text":"kept"}')
            before = path.read_bytes()
            snapshot = probe.inbox_snapshot(root)
            self.assertEqual(snapshot['arriving.json']['sha256'], hashlib.sha256(before).hexdigest())
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(root.iterdir()), [root / 'inbox'])

    def test_suffix_headers_are_read_without_entire_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'record.json'
            path.write_bytes(b'{"document":"' + b'x' * 1024**2 + b'","index":19,"journal_id":"' + b'a' * 32
                + b'","kind":"SLEEP_COMPLETE","previous_sha256":"' + b'b' * 64
                + b'","schema":"R125_STREAM_JOURNAL_V1","sha256":"' + b'c' * 64 + b'"}\n')
            self.assertEqual(probe.header(path)['index'], 19)

    def test_boundary_loading_not_shadowed_by_receiving_research_loop_package(self):
        path = Path(__file__).parent / 'operator_bundle_v4/research_loop/workers/post_recovery_retention_boundary_20260918/boundary.py'
        with patch.dict(sys.modules, {'research_loop': types.ModuleType('research_loop')}):
            boundary = probe.load_boundary(path)
        self.assertEqual(boundary.digest({}), hashlib.sha256(b'{}').hexdigest())


if __name__ == '__main__':
    unittest.main()
