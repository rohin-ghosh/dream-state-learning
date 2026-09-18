import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from gpu import orch_r119_grid_continuation as subject


class ContinuationTests(unittest.TestCase):
    def test_filter_never_includes_readouts(self):
        self.assertTrue(subject.training(dict(kind='PARENT')))
        self.assertTrue(subject.training(dict(kind='NATIVE', split='TRAIN')))
        for split, attached in [('DEV', False), ('FINAL', False), ('TRAIN', True)]:
            self.assertFalse(subject.training(dict(kind='NATIVE', split=split, attached_readout=attached)))

    def test_existing_output_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'event.json'
            path.write_text(json.dumps(dict(created_unix=1, resulting_state={'step': 3})))
            before = path.read_bytes()
            grid = SimpleNamespace(read=lambda path: json.loads(path.read_text()),
                                   write=lambda *args, **kwargs: self.fail('unexpected write'))
            writer = subject.existing_writer(grid, root, dry=True)
            writer(path, dict(created_unix=2, resulting_state={'step': 3}))
            self.assertEqual(path.read_bytes(), before)
            with self.assertRaisesRegex(ValueError, 'preserve_existing'):
                writer(path, dict(created_unix=2, resulting_state={'step': 4}))
            with self.assertRaisesRegex(ValueError, 'must_not_write'):
                writer(root / 'new.json', {})

    def life(self, rows, record, dry=False):
        class Original:
            def __init__(self, root, engine, config, cycle):
                self.root, self.engine, self.config, self.cycle = root, engine, config, cycle
                self.events = []

            def event(self, *args):
                self.events.append(args)

            def calls(self, *args, **kwargs):
                raise AssertionError('model called')
        grid = SimpleNamespace(Life=Original, read=lambda path: record,
            sha=lambda path: 'a'*64, ref=lambda path: {'path': str(path), 'sha256': 'a'*64})
        return subject.replay_class(grid)(Path('/tmp/example'), None, {}, 21, cached=rows, dry=dry)

    def test_cached_generation_never_dispatches(self):
        row = dict(kind='NATIVE', number=7, task_id='TRAIN', purpose='episode',
                   split='TRAIN', attached_readout=False)
        messages = [dict(role='user', content='original')]
        record = dict(status='COMPLETE', messages=messages, cap=384,
                      response=dict(raw='saved', token_ids=[1, 2]))
        life = self.life([row], record)
        result = life.calls([dict(id='TRAIN', split='TRAIN')], 'episode', [messages], 384)
        self.assertEqual(result[0]['raw'], 'saved')
        self.assertEqual(life.cursor, 1)
        self.assertNotIn('reference', record['response'])

    def test_wrong_prompt_rejected(self):
        row = dict(kind='NATIVE', number=7, task_id='TRAIN', purpose='episode',
                   split='TRAIN', attached_readout=False)
        life = self.life([row], dict(status='COMPLETE', messages=[], cap=384))
        with self.assertRaisesRegex(ValueError, 'messages_cap'):
            life.calls([dict(id='TRAIN', split='TRAIN')], 'episode', [['changed']], 384)

    def test_incomplete_charged_response_rejected(self):
        row = dict(kind='NATIVE', number=7, task_id='TRAIN', purpose='episode',
                   split='TRAIN', attached_readout=False)
        life = self.life([row], dict(status='STARTED', messages=[], cap=384))
        with self.assertRaisesRegex(ValueError, 'messages_cap'):
            life.calls([dict(id='TRAIN', split='TRAIN')], 'episode', [[]], 384)

    def test_dry_boundary_stops_before_model_or_charge(self):
        life = self.life([], {}, dry=True)
        with self.assertRaises(subject.CachedBoundary):
            life.calls([dict(id='TRAIN', split='TRAIN')], 'episode', [[]], 384)

    def test_held_and_dependent_batch_rejected(self):
        life = self.life([], {})
        with self.assertRaisesRegex(ValueError, 'TRAIN_only'):
            life.calls([dict(id='FINAL', split='FINAL')], 'readout', [[]], 384)
        with self.assertRaisesRegex(ValueError, 'sequential'):
            life.calls([dict(id='TRAIN', split='TRAIN')]*2, 'episode', [[], []], 384)

    def test_exact_charge_order(self):
        life = self.life([dict(kind='PARENT', phase='experience')], {})
        with self.assertRaisesRegex(ValueError, 'causal_charge_order'):
            life.take('NATIVE', {})

    def test_task_cursor_unchanged(self):
        roster = list(range(16))
        self.assertEqual(subject.tasks_for(roster, 21), [4, 12])
        self.assertEqual(subject.tasks_for(roster, 18), [1, 9])


if __name__ == '__main__':
    unittest.main()
