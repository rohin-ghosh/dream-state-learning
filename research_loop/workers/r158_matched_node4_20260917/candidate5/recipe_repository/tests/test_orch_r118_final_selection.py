from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r118_final_selection as selector


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.owner = self.root / 'F1'
        self.owner.mkdir()
        optimizer = self.owner / 'optimizer_rng.pt'
        optimizer.write_bytes(b'preserved-optimizer-and-RNG')
        checkpoint = self.owner / 'CHECKPOINT.json'
        selector.write_new(checkpoint, dict(complete=True, optimizer_rng_sha256=selector.sha(optimizer)))
        self.reference = dict(path=str(checkpoint), path_sha256=selector.sha(checkpoint),
            optimizer_path=str(optimizer), optimizer_path_sha256=selector.sha(optimizer))
        self.metrics = dict(optimizer_steps=1125, child_token_exposures=68231, anchor_token_exposures=20351)
        config = dict(owner='F1', branches={branch: dict(root=str(self.owner)) for branch in selector.BRANCHES},
            initial_checkpoint=self.reference, pretransition_metrics=self.metrics)
        selector.write_new(self.root / 'CONFIG.json', config)
        for name in ('INITIALIZED.json', 'ADOPTION.json'):
            selector.write_new(self.root / name, dict(real=True))
        self.pins = dict(config_sha256=selector.sha(self.root / 'CONFIG.json'),
            initialized_sha256=selector.sha(self.root / 'INITIALIZED.json'),
            adoption_sha256=selector.sha(self.root / 'ADOPTION.json'))
        self.state = dict(generation=0, checkpoint=self.reference, config_sha256=self.pins['config_sha256'],
            **self.metrics, **{'shared_' + metric: 0 for metric in selector.METRICS})
        selector.write_new(self.root / 'STATE.json', self.state)
        selector.write_new(self.root / 'SEALED_FINAL.json', dict(secret='must-never-read'))

    def call(self, now=None):
        return selector.select(self.root, **self.pins,
            clock=lambda: selector.CUT + 1 if now is None else now)

    def test_clock_precedes_any_selection_and_no_sealed_reads(self):
        with self.assertRaisesRegex(ValueError, 'clock_gate'):
            self.call(selector.CUT - 1)
        self.assertFalse((self.root / 'FINAL_SELECTION.json').exists())
        with patch.object(selector, 'read', wraps=selector.read) as reader:
            result = self.call()
        self.assertFalse(result['sealed_tasks_read'])
        self.assertNotIn(self.root / 'SEALED_FINAL.json', [call.args[0] for call in reader.call_args_list])

    def test_initial_checkpoint_is_not_joint_learning_credit(self):
        result = self.call()
        self.assertEqual(result['generation'], 0)
        self.assertEqual(result['lifetime_metrics']['optimizer_steps'], 1125)
        self.assertEqual(result['shared_metrics']['optimizer_steps'], 0)
        self.assertEqual(result['checkpoint'], self.reference)

    def test_idempotent_no_new_checkpoint_or_state_writes(self):
        result = self.call()
        before = (self.root / 'FINAL_SELECTION.json').read_bytes()
        state_before = (self.root / 'STATE.json').read_bytes()
        self.assertEqual(self.call(selector.CUT + 50), result)
        self.assertEqual((self.root / 'FINAL_SELECTION.json').read_bytes(), before)
        self.assertEqual((self.root / 'STATE.json').read_bytes(), state_before)

    def test_partial_sleep_not_selected(self):
        folder = self.root / 'generation_000000/sleep'
        folder.mkdir(parents=True)
        selector.write_new(folder / 'START.json', dict(generation=0))
        (folder / 'UPDATES.jsonl').write_text('{"step":17}\n')
        result = self.call()
        self.assertEqual(result['shared_metrics']['optimizer_steps'], 0)
        self.assertIsNone(result['committed_sleep'])

    def completed_state(self, when):
        import json
        self.state.update(generation=1, shared_optimizer_steps=8, optimizer_steps=1133)
        (self.root / 'STATE.json').write_text(json.dumps(self.state))
        folder = self.root / 'generation_000000/sleep'
        folder.mkdir(parents=True)
        selector.write_new(folder / 'COMPLETE.json', dict(state=self.state,
            same_optimizer=True, completed_unix=when))

    def test_committed_sleep_required_and_recorded(self):
        self.completed_state(selector.CUT - 60)
        result = self.call()
        self.assertEqual(result['generation'], 1)
        self.assertEqual(result['shared_metrics']['optimizer_steps'], 8)
        self.assertIsNotNone(result['committed_sleep'])

    def test_post_cut_completion_rejected_not_silently_selected(self):
        self.completed_state(selector.CUT + 1)
        with self.assertRaisesRegex(ValueError, 'post_cut'):
            self.call(selector.CUT + 2)

    def test_corrupted_optimizer_rejected(self):
        Path(self.reference['optimizer_path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'optimizer_changed'):
            self.call()

    def test_publication_without_complete_rejected(self):
        self.completed_state(selector.CUT - 60)
        (self.root / 'generation_000000/sleep/COMPLETE.json').unlink()
        with self.assertRaises(FileNotFoundError):
            self.call()

    def test_lineage_tampering_rejected(self):
        (self.root / 'ADOPTION.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'lineage_binding'):
            self.call()

    def test_no_overwrite(self):
        path = self.root / 'once.json'
        selector.write_new(path, dict(first=True))
        with self.assertRaises(FileExistsError):
            selector.write_new(path, dict(first=False))
        self.assertEqual(selector.read(path), dict(first=True))

    def test_deadline_requires_explicit_new_scope(self):
        with self.assertRaisesRegex(ValueError, 'clock_gate'):
            self.call(selector.DEADLINE)

    def test_wait_clock_crossing_never_sleeps_negative(self):
        with patch.dict(selector.os.environ, {'CUDA_VISIBLE_DEVICES': ''}), \
                patch.object(selector.time, 'time', side_effect=[selector.CUT - .001, selector.CUT + .001,
                                                                selector.CUT + .002]), \
                patch.object(selector.time, 'sleep') as sleeper, \
                patch.object(selector, 'select', return_value={'selected': True}):
            result = selector.wait_select(self.root, **self.pins)
        sleeper.assert_called_once_with(0)
        self.assertTrue(result['selected'])

    def test_consumer_cannot_create_selection(self):
        with self.assertRaises(FileNotFoundError):
            selector.validate_selection(self.root, **self.pins, clock=lambda: selector.CUT + 1)
        self.assertFalse((self.root / 'FINAL_SELECTION.json').exists())

    def test_consumer_uses_frozen_snapshot_not_later_state(self):
        selected = self.call()
        (self.root / 'STATE.json').write_text('{"generation":999}')
        actual = selector.validate_selection(self.root, **self.pins, clock=lambda: selector.CUT + 2)
        self.assertEqual(actual, selected)

    def test_snapshot_tampering_rejected(self):
        selected = self.call()
        Path(selected['state_reference']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'immutable_state_snapshot'):
            selector.validate_selection(self.root, **self.pins, clock=lambda: selector.CUT + 2)

    def test_consumer_does_not_write_or_read_sealed_contents(self):
        self.call()
        with patch.object(selector, 'write_new') as writer, \
                patch.object(selector, 'read', wraps=selector.read) as reader:
            selector.validate_selection(self.root, **self.pins, clock=lambda: selector.CUT + 2)
        writer.assert_not_called()
        self.assertNotIn(self.root / 'SEALED_FINAL.json', [call.args[0] for call in reader.call_args_list])


if __name__ == '__main__':
    unittest.main()
