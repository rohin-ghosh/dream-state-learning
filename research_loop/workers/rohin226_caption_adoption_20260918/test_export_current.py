import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

from gpu import ny_caption_data as data


DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY.parent / 'rohin224_caption_adoption_20260918'))
spec = importlib.util.spec_from_file_location('r226_adopt', DIRECTORY / 'adopt_current.py')
adoption = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adoption)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.scenes = [dict(contest_id=1, canonical_scene='A factual scene')]
        self.initial = dict(schema='R223_CAPTION_SESSION_STATE_V1', phase='COMPLETE',
            life_root=str(self.root / 'life'), scene_ids=self.scenes, source_mode='NATIVE_JOURNAL',
            seen=['old-source'], game=dict(count=1), policy=dict(count=1))
        initial_path = self.write('INITIAL.json', self.initial)
        self.write('LOADED.json', dict(life_root=self.initial['life_root'],
            resume_state_input=data.file_ref(initial_path)))
        (self.root / 'attempts' / 'new-source').mkdir(parents=True)
        self.write('attempts/new-source/BEFORE.json', dict(game=dict(count=1), policy=dict(count=1)))
        self.write('attempts/new-source/AFTER.json', dict(game=dict(count=2), policy=dict(count=2)))
        self.write('attempts/new-source/RESULT.json', dict(unix=2, raw_act='A real caption.',
            origin=dict(record_sha256='new-source')))
        self.state = dict(self.initial, seen=['old-source', 'new-source'],
            game=dict(count=2), policy=dict(count=2))
        self.write('SESSION_STATE.private.json', self.state)

    def write(self, name, document):
        path = self.root / name
        path.write_bytes(data.canonical(document))
        return path

    def export(self):
        return adoption.export_current(self.root, self.scenes,
            verify_origin=lambda root, origin: 'A real caption.')

    def test_exact_state_and_seen_preserved(self):
        state, receipt = self.export()
        self.assertEqual(state, self.state)
        self.assertEqual(receipt['complete_attempts'], 2)
        self.assertFalse(receipt['historical_rescoring'])
        self.assertEqual(receipt['state_sha256'], hashlib.sha256(
            (self.root / 'SESSION_STATE.private.json').read_bytes()).hexdigest())

    def test_pending_and_missing_attempt_refuse_export(self):
        self.write('SESSION_STATE.private.json', dict(self.state, phase='PENDING'))
        with self.assertRaisesRegex(ValueError, 'same_complete_native_session'):
            self.export()
        self.write('SESSION_STATE.private.json', self.state)
        (self.root / 'attempts' / 'unfinished').mkdir()
        with self.assertRaisesRegex(ValueError, 'complete_attempt_before_export'):
            self.export()

    def test_state_chain_or_raw_or_seen_tampering_rejected(self):
        for name, document in (
            ('attempts/new-source/BEFORE.json', dict(game={}, policy={})),
            ('attempts/new-source/RESULT.json', dict(unix=2, raw_act='Invented',
                origin=dict(record_sha256='new-source'))),
            ('SESSION_STATE.private.json', dict(self.state, seen=['new-source']))):
            path = self.root / name
            before = path.read_bytes()
            self.write(name, document)
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.export()
            path.write_bytes(before)


if __name__ == '__main__':
    unittest.main()
