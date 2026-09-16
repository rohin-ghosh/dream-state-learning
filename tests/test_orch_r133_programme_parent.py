import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest

from gpu import orch_r133_programme_parent as parent


class ProgrammeParentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name)/'programme.md'
        self.path.write_text('Talk about an actual draft and its revision.')
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.config = dict(schema='R133_PROGRAMME_PARENT_V1', node='ovx2',
            programme='creative_writing', branch='C1', root='/localhome/local-rohing/orch_test/run1',
            source_root='/localhome/local-rohing/orch_test/source1',
            programme_path=str(self.path), programme_sha256=digest,
            principles_path=str(self.path), principles_sha256=digest,
            cadence_responses=3, hard_end_unix=time.time()+600)

    def test_explicit_pinned_configuration(self):
        self.assertEqual(parent.validate(self.config), self.config)

    def test_changed_programme_rejected(self):
        self.path.write_text('different')
        with self.assertRaisesRegex(ValueError, 'fixed_parent_source'):
            parent.validate(self.config)

    def test_arbitrary_host_or_path_rejected(self):
        for field, value in [('node', 'arbitrary-host'), ('root', '/tmp/held'),
                             ('programme', 'unknown'), ('cadence_responses', 0)]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    parent.validate(dict(self.config, **{field: value}))

    def test_parent_uses_training_snapshot_only(self):
        with self.assertRaisesRegex(ValueError, 'training_snapshot_only'):
            parent.prompt(self.config, {'schema': 'HELD_READOUT'})

    def test_parent_no_unmarked_excerpt_or_thought_format(self):
        state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[dict(actor='child', text='x'*6100)])
        instruction, payload = parent.prompt(self.config, state)
        self.assertIn('Do not prescribe a recurring', instruction)
        self.assertIn('at most90 words', instruction)
        self.assertIn('[Parent-view excerpt truncated]', payload)
        self.assertLess(len(payload), 6500)

    def test_receipts_are_append_only(self):
        destination = self.path.parent/'receipt.json'
        parent.write(destination, {'status': 'original'})
        with self.assertRaises(FileExistsError):
            parent.write(destination, {'status': 'replacement'})

    def test_complete_requires_observed_consumption(self):
        output = self.path.parent/'parent_000000'
        output.mkdir()
        parent.write(output/'RESULT.json', dict(status='PUBLISHED', programme='creative_writing',
                     branch='C1', inbox_publication={'id': 'example'}))
        parent.record_deliveries(self.path.parent, {'consumed_inbox': {}})
        self.assertFalse((output/'DELIVERED.json').exists())
        state = {'consumed_inbox': {'example': {'record_index': 4, 'record_sha256': 'a'*64}}}
        parent.record_deliveries(self.path.parent, state)
        result = json.loads((output/'DELIVERED.json').read_text())
        self.assertEqual(result['status'], 'COMPLETE')
        parent.record_deliveries(self.path.parent, state)


if __name__ == '__main__':
    unittest.main()
