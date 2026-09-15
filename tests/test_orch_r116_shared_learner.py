from collections import Counter
from contextlib import nullcontext
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gpu import orch_r116_shared_learner as shared


class SharedLearnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.shared = self.root / 'shared'
        self.specs = {branch: dict(root=str(self.root / branch),
            train_ids=[branch + '_one', branch + '_two']) for branch in shared.BRANCHES}
        self.checkpoint = self.make_checkpoint(self.root / 'initial', 'initial')
        self.prior = dict.fromkeys(shared.METRICS, 0)
        shared.initialize(self.shared, self.specs, self.checkpoint, excluded_ids=['sealed'],
                          prior_metrics=self.prior, initial_history={})

    def make_checkpoint(self, folder, text):
        folder.mkdir(parents=True)
        result = {}
        for field in ('path', 'optimizer_path'):
            path = folder / (field + '.json')
            shared.write(path, dict(identity=text, kind=field))
            result[field] = str(path)
            result[field + '_sha256'] = shared.sha(path)
        return result

    def row(self, branch, ordinal, *, phase='experience', split='TRAIN', attached=False):
        task = self.specs[branch]['train_ids'][ordinal]
        messages = [dict(role='user', content='Visible observation; parent advice in prefix.')]
        response = dict(messages=messages, prompt_tokens=12, raw='Child thought.',
                        token_ids=[3, 4], terminal=True, truncated=False)
        call = dict(task_id=task, phase=phase, split=split, attached_readout=attached, response=response,
                    shared_generation=0, shared_checkpoint_sha256=self.checkpoint['path_sha256'])
        path = self.root / branch / ('call_' + str(ordinal) + '.json')
        shared.write(path, call)
        return dict(replay_mode=shared.replay.MODE, student_prefix=messages,
                    source_prompt_sha256=shared.replay.history_policy.digest(messages),
                    source_prompt_tokens=12, target=response['raw'],
                    target_sha256=shared.replay.history_policy.text_sha(response['raw']),
                    source_generated_token_ids=[3, 4], append_eos=True, continuation_only=False,
                    source_call_path=str(path), source_call_sha256=shared.sha(path), episode_id=task)

    def submit(self, branch, rows=None):
        rows = rows if rows is not None else [self.row(branch, 0), self.row(branch, 1)]
        return shared.submit(self.shared, branch, 0, self.checkpoint['path_sha256'],
                             self.specs[branch]['train_ids'], rows)

    def all_arrive(self):
        for branch in shared.BRANCHES:
            self.submit(branch)

    def test_exact_eight_not_subset(self):
        specs = dict(self.specs)
        specs.pop('A4')
        with self.assertRaisesRegex(ValueError, 'exact_eight'):
            shared.initialize(self.shared, specs, self.checkpoint, prior_metrics=self.prior, initial_history={})

    def test_initialize_idempotent(self):
        before = shared.read(self.shared / 'STATE.json')
        after = shared.initialize(self.shared, self.specs, self.checkpoint, excluded_ids=['sealed'],
                                  prior_metrics=self.prior, initial_history={})
        self.assertEqual(before, after)

    def test_sealed_overlap_rejected(self):
        specs = deepcopy(self.specs)
        specs['F1']['train_ids'].append('sealed')
        with self.assertRaisesRegex(ValueError, 'held_train_overlap'):
            shared.initialize(self.root / 'bad', specs, self.checkpoint, excluded_ids=['sealed'],
                              prior_metrics=self.prior, initial_history={})

    def test_submit_is_idempotent_not_double_counted(self):
        rows = [self.row('F1', 0), self.row('F1', 1)]
        self.assertEqual(self.submit('F1', rows), self.submit('F1', rows))
        self.assertEqual(shared.barrier_status(self.shared)['present'], ['F1'])

    def test_duplicate_capture_rejected(self):
        row = self.row('F1', 0)
        with self.assertRaisesRegex(ValueError, 'duplicate_source'):
            self.submit('F1', [row, row])

    def test_two_episodes_required(self):
        with self.assertRaisesRegex(ValueError, 'two_episodes'):
            shared.submit(self.shared, 'F1', 0, self.checkpoint['path_sha256'], ['F1_one'], [])

    def test_stale_child_rejected(self):
        with self.assertRaisesRegex(ValueError, 'common_child'):
            shared.submit(self.shared, 'F1', 0, 'different', self.specs['F1']['train_ids'],
                          [self.row('F1', 0)])

    def test_future_generation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'stale_or_future'):
            shared.submit(self.shared, 'F1', 1, self.checkpoint['path_sha256'],
                          self.specs['F1']['train_ids'], [self.row('F1', 0)])

    def test_dev_and_final_rejected(self):
        for branch, split in [('F1', 'DEV'), ('F2', 'FINAL')]:
            with self.assertRaisesRegex(ValueError, 'held_split'):
                self.submit(branch, [self.row(branch, 0, split=split)])

    def test_readout_open_turn_rejected_even_train_task(self):
        with self.assertRaisesRegex(ValueError, 'readout_open_turn'):
            self.submit('F1', [self.row('F1', 0, phase='open_turn', attached=True)])

    def test_readout_phase_rejected(self):
        with self.assertRaisesRegex(ValueError, 'readout_phase'):
            self.submit('F1', [self.row('F1', 0, phase='dev')])

    def test_train_open_turn_accepted(self):
        self.submit('F1', [self.row('F1', 0, phase='open_turn'), self.row('F1', 1)])
        self.assertEqual(shared.barrier_status(self.shared)['present'], ['F1'])

    def test_parent_text_cannot_become_target(self):
        row = self.row('F1', 0)
        row['target'] = 'Parent intervention substituted for child'
        with self.assertRaisesRegex(ValueError, 'actual_target_binding'):
            self.submit('F1', [row])

    def test_source_tamper_detected(self):
        row = self.row('F1', 0)
        Path(row['source_call_path']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'source_capture_hash'):
            self.submit('F1', [row])

    def test_wrong_branch_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source_outside_branch'):
            self.submit('F2', [self.row('F1', 0)])

    def test_anchor_weight_in_every_step_at_small_and_large_dose(self):
        for new_count in (1, 2, 3, 16, 100):
            for allocation in shared.schedule(new_count, 3):
                self.assertTrue(allocation['anchors'])
                self.assertAlmostEqual(len(allocation['anchors']) * allocation['anchor_weight'], .25)
                self.assertEqual(allocation['child_weight'], .75)

    def test_exact_presentation_accounting(self):
        allocations = list(shared.schedule(5, 3))
        counts = Counter((item['kind'], item['index']) for item in allocations)
        self.assertEqual([counts['NEW', index] for index in range(5)], [16] * 5)
        self.assertEqual([counts['REHEARSAL', index] for index in range(3)], [1] * 3)
        self.assertEqual(set(index for item in allocations for index in item['anchors']), set(range(42)))

    def test_optimizer_never_runs_before_all_arrive(self):
        self.submit('F1')
        def unexpected(*args):
            self.fail('optimizer ran before barrier')
        result = shared.consolidate(self.shared, 'F1', self.checkpoint['path_sha256'],
                                    None, None, [], unexpected, unexpected, train_call=unexpected)
        self.assertEqual(result['status'], 'WAITING')
        self.assertEqual(len(result['missing']), 7)

    def test_only_owner_may_train(self):
        with self.assertRaisesRegex(ValueError, 'only_F1'):
            shared.consolidate(self.shared, 'A1', '', None, None, [], None, None)

    def test_joint_sleep_uses_one_optimizer_and_all_branches(self):
        self.all_arrive()
        optimizer = object()
        def train(engine, actual_optimizer, rows, history, anchors, output, check):
            self.assertIs(actual_optimizer, optimizer)
            self.assertEqual(len(rows), 16)
            self.assertEqual(history, [])
            return dict(optimizer_steps=256, child_token_exposures=512, anchor_token_exposures=256)
        def save(folder, generation, metrics):
            self.assertEqual(generation, 1)
            return self.make_checkpoint(folder, 'pooled')
        result = shared.consolidate(self.shared, 'F1', self.checkpoint['path_sha256'], None,
                                    optimizer, [], save, lambda label: None, train_call=train)
        self.assertEqual(result['state']['generation'], 1)
        self.assertEqual(result['state']['optimizer_steps'], 256)
        self.assertEqual(len(shared.barrier_status(self.shared)['missing']), 8)

    def test_failed_sleep_is_not_silently_replayed(self):
        self.all_arrive()
        def crash(*args):
            raise RuntimeError('native crash after optimizer started')
        with self.assertRaises(RuntimeError):
            shared.consolidate(self.shared, 'F1', self.checkpoint['path_sha256'],
                               None, None, [], None, None, train_call=crash)
        with self.assertRaisesRegex(ValueError, 'partial_sleep'):
            shared.consolidate(self.shared, 'F1', self.checkpoint['path_sha256'],
                               None, None, [], None, None, train_call=crash)
        self.assertEqual(shared.read(self.shared / 'STATE.json')['generation'], 0)

    def test_adoption_preserves_counters_unknown_exposures_and_rehearsal(self):
        previous_row = self.row('F1', 0)
        previous_metrics = dict(optimizer_steps=113, child_token_exposures=None, anchor_token_exposures=700)
        root = self.root / 'adopted'
        state = shared.initialize(root, self.specs, self.checkpoint, prior_metrics=previous_metrics,
                                  initial_history={'F1': [previous_row]})
        self.assertEqual(state['optimizer_steps'], 113)
        self.assertIsNone(state['child_token_exposures'])
        self.assertEqual(state['shared_optimizer_steps'], 0)
        self.assertEqual(shared.read(root / 'CONFIG.json')['initial_history']['F1'], [previous_row])

    def test_continuation_is_training_not_readout(self):
        self.submit('F1', [self.row('F1', 0, phase='continuation'), self.row('F1', 1)])
        self.assertEqual(shared.barrier_status(self.shared)['present'], ['F1'])

    def test_old_base_capture_cannot_be_relabeled_shared(self):
        row = self.row('F1', 0)
        source = Path(row['source_call_path'])
        call = shared.read(source)
        call.pop('shared_checkpoint_sha256')
        shared.write(source, call, replace=True)
        row['source_call_sha256'] = shared.sha(source)
        with self.assertRaisesRegex(ValueError, 'capture_must_bind_actual_shared_child'):
            self.submit('F1', [row])

    def test_actual_training_loop_has_anchor_gradient_every_update(self):
        from gpu import orch_guided_native as native
        weights = []
        class Loss:
            def __mul__(self, weight):
                weights.append(weight)
                return self

            def backward(self):
                pass

        item = SimpleNamespace(input_ids=(1, 2, 3), labels=(-100, 2, 3), target_ids=(2, 3))
        torch = SimpleNamespace(tensor=lambda values, **kwargs: values, long='long', bfloat16='bf16',
            ones_like=lambda values: values, autocast=lambda **kwargs: nullcontext(), isfinite=lambda loss: True)
        model = Mock(return_value=SimpleNamespace(loss=Loss()))
        model.config = SimpleNamespace(use_cache=True)
        engine = SimpleNamespace(torch=torch, tokenizer=None, model=model, device='cpu', verify_base=Mock())
        optimizer = Mock()
        output = self.root / 'train'
        output.mkdir()
        with patch.object(shared.replay, 'encode_row', return_value=item), \
                patch.object(native.development, 'enable_existing_adapter'):
            result = shared.train(engine, optimizer, [{}, {}, {}], [{}],
                                  [dict(encoded=item)] * 42, output, lambda label: None)
        self.assertEqual(optimizer.step.call_count, 49)
        self.assertEqual(weights, [.75, .25] * 49)
        self.assertEqual(result['child_token_exposures'], 98)
        self.assertEqual(result['anchor_token_exposures'], 98)
        engine.verify_base.assert_called_once()
        model.requires_grad_.assert_called_once_with(False)

    def test_changed_configuration_rejected_before_barrier(self):
        config = shared.read(self.shared / 'CONFIG.json')
        config['anchor_loss_weight'] = 0
        shared.write(self.shared / 'CONFIG.json', config, replace=True)
        with self.assertRaisesRegex(ValueError, 'configuration_hash'):
            shared.barrier_status(self.shared)

    def test_saved_checkpoint_publication_recovers_without_optimizer_replay(self):
        self.all_arrive()
        metrics = dict(optimizer_steps=256, child_token_exposures=512, anchor_token_exposures=256)
        def save(folder, generation, result):
            return self.make_checkpoint(folder, 'pooled')
        original = shared.write
        def crash_state_publication(path, value, replace=False):
            if Path(path) == self.shared / 'STATE.json' and replace:
                raise RuntimeError('crash after saved complete checkpoint')
            return original(path, value, replace)
        with patch.object(shared, 'write', side_effect=crash_state_publication):
            with self.assertRaisesRegex(RuntimeError, 'saved complete'):
                shared.consolidate(self.shared, 'F1', self.checkpoint['path_sha256'], None,
                    None, [], save, None, train_call=lambda *args: metrics)
        self.assertEqual(shared.read(self.shared / 'STATE.json')['generation'], 0)
        result = shared.recover_published_checkpoint(self.shared)
        self.assertEqual(result['optimizer_updates_replayed'], 0)
        self.assertEqual(result['state']['optimizer_steps'], 256)
        self.assertEqual(result['state']['generation'], 1)


if __name__ == '__main__':
    unittest.main()
