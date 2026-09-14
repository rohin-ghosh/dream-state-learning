"""CPU-only fixtures for the two fixed incremental fits and shared readouts."""

from contextlib import ExitStack
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_goal_pair_train as runner
from tests.test_astra_event_two_hop_memory import setup as memory_setup, material_fixture, write
from tests.test_astra_goal_pair_collection import CollectionEngine, cli as collector_cli, rehash
from tests.test_experienced_event_two_hop import generation
from tests.test_astra_corrective_sleep_train import fake_engine


def cli(root, phase, arm=None, output=None):
    values = collector_cli(root, 'prepare')
    values[values.index('--phase') + 1] = phase
    values[values.index('--output') + 1] = str(output or (root / arm / phase if arm else root / 'fit-prepare'))
    values += ['--collection-root', str(root / 'collection')]
    if arm:
        values += ['--arm', arm]
    if phase == 'after':
        values += ['--training', str(root / arm / 'train')]
    return values


def fixture(root, stack, material, *, bad_baseline=False):
    state = memory_setup(root, stack, material)
    tokenizer = state.token_loader.return_value
    old = tuple(runner.source.encode_row(row['messages'], tokenizer) for row in material['material']['memory_rows'])
    old += tuple(runner.memory.cues.encode_cue_rows(material['material']['cue_rows'], tokenizer))
    old += tuple(runner.memory.audit.encode_rows(material['material']['audit_rows'], tokenizer))
    old += tuple(runner.memory.lesson.lesson.encode_rows(material['material']['trajectory_rows'], tokenizer))
    path = root / 'lesson/train/MASKS.json'
    write(path, [asdict(row) for row in old])
    trained = runner.source.read(root / 'lesson/train/RESULT.json')
    trained['training_files']['MASKS.json'] = runner.source.file_hash(path)
    write(root / 'lesson/train/RESULT.json', trained)
    state.binding['training_result_sha256'] = runner.source.file_hash(root / 'lesson/train/RESULT.json')
    after = runner.source.read(root / 'lesson/after/RESULT.json')
    after['training_result_sha256'] = state.binding['training_result_sha256']
    write(root / 'lesson/after/RESULT.json', after)
    state.binding['after_result_sha256'] = runner.source.file_hash(root / 'lesson/after/RESULT.json')
    collected = runner.source.read(root / 'transfer/collect/RESULT.json')
    collected['binding'] = state.binding
    write(root / 'transfer/collect/RESULT.json', collected)
    for arm in ('TRAINED', 'ORIGINAL'):
        receipt = runner.source.read(root / 'transfer' / arm / 'RESULT.json')
        receipt.update(binding=state.binding, collection_result_sha256=runner.source.file_hash(root / 'transfer/collect/RESULT.json'))
        write(root / 'transfer' / arm / 'RESULT.json', receipt)
    native_factory = state.factory.side_effect

    def collection_factory(arguments, tokenizer, *, check):
        engine = CollectionEngine(arguments, tokenizer, check, {})
        engine.invalid = bad_baseline and (root / 'teach/RESULT.json').exists()
        state.engines.append(engine)
        return engine

    state.factory.side_effect = collection_factory
    for phase in ('expose', 'teach', 'baseline'):
        runner.collector.main(collector_cli(root, phase))
    (root / 'collection').mkdir()
    for phase in ('expose', 'teach', 'baseline'):
        (root / phase).rename(root / 'collection' / phase)

    def factory(*args, **kwargs):
        engine = native_factory(*args, **kwargs)
        original_call = type(engine.model).__call__
        engine.backward_scales = []

        class ScaledLoss:
            requires_grad = True

            def __init__(self, original, scale=1):
                self.original, self.scale = original, scale

            def __mul__(self, scale):
                return ScaledLoss(self.original, self.scale * scale)

            def item(self):
                return self.original.item() * self.scale

            def backward(self):
                engine.backward_scales.append(self.scale)
                self.original.backward()

        type(engine.model).__call__ = lambda model, **options: SimpleNamespace(loss=ScaledLoss(original_call(model, **options).loss))
        return engine

    state.factory.side_effect = factory
    state.factory.reset_mock()
    state.token_loader.reset_mock()
    return state


def encoded_fixture():
    rows = []
    for index in range(270):
        target = (42,) * (index % 7 + 1) + (1,)
        rows.append(runner.source.native.EncodedRow((10,) + target + (11,), (-100,) + target + (-100,), target))
    return tuple(rows)


class GoalFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = material_fixture()

    def test_exact_schedule_common_inputs_and_denominator(self):
        encoded = encoded_fixture()
        original = deepcopy(encoded)
        full = runner.dose(encoded, runner.ARMS[0])
        control = runner.dose(encoded, runner.ARMS[1])
        self.assertEqual(full['reference_supervised_tokens'], control['reference_supervised_tokens'])
        self.assertEqual(full['actual_supervised_tokens'], full['reference_supervised_tokens'])
        self.assertLess(control['actual_supervised_tokens'], control['reference_supervised_tokens'])
        self.assertEqual(full['row_presentations'], control['row_presentations'])
        counts = full['row_presentations']
        self.assertEqual([sum(counts[start:end]) for start, end in ((0,128),(128,148),(148,210),(210,222),(222,270))],
                         [400,100,252,48,800])
        self.assertEqual(set(counts[222:]), {16,17})
        self.assertEqual(runner.controlled_masks(encoded, runner.ARMS[1])[:222], encoded[:222])
        for update in range(1, 401):
            offset = update - 1
            indexes, full_batch, reference, unused, unused_scale = runner.training_batch(encoded, update, runner.ARMS[0])
            controlled_indexes, batch, control_reference, active, scale = runner.training_batch(encoded, update, runner.ARMS[1])
            self.assertEqual(indexes, (offset%128,128+offset%94,222+(2*offset)%48,222+(2*offset+1)%48))
            self.assertEqual(indexes, controlled_indexes)
            self.assertEqual(reference, control_reference)
            self.assertEqual(batch['input_ids'], full_batch['input_ids'])
            self.assertEqual(batch['attention_mask'], full_batch['attention_mask'])
            self.assertEqual(batch['labels'][:2], full_batch['labels'][:2])
            self.assertTrue(all(label == -100 for labels in batch['labels'][2:] for label in labels))
            self.assertAlmostEqual((7 / active) * scale, 7 / reference)
        self.assertEqual(encoded, original)
        for update in (0,401,True,1.5):
            with self.assertRaises(ValueError):
                runner.training_indexes(update)

    def test_prepare_actual_joined_rows_no_model_or_baseline_score_gate(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material, bad_baseline=True)
            snapshot = {str(path): runner.source.file_hash(path) for folder in ('lesson','transfer','collection')
                        for path in (root/folder).rglob('*') if path.is_file()}
            with self.assertRaisesRegex(ValueError, 'reference_output_overlap_forbidden'):
                runner.main(cli(root, 'prepare', output=root / 'collection/forbidden'))
            result = runner.main(cli(root, 'prepare'))
            self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
            self.assertEqual((result['row_count'],result['new_actual_train_targets'],result['probe_training_rows']), (270,48,0))
            state.factory.assert_not_called()
            state.token_loader.assert_not_called()
            rows = runner.source.read(root/'fit-prepare/TRAINING_ROWS.json')
            self.assertEqual(set(rows), set(runner.GROUPS))
            self.assertEqual(rows['trajectory_rows'], self.material['material']['trajectory_rows'])
            self.assertEqual({row['master'] for row in rows['new_trajectory_rows']}, set(runner.goal.TRAIN_MASTERS))
            self.assertNotIn('new_rows', rows)
            for path, digest in snapshot.items():
                self.assertEqual(runner.source.file_hash(path), digest)

    def test_full_native_fixture_lifecycle_both_arms_and_readonly_reload(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)

            def argv(phase, arm=None, output=None):
                values = cli(root, phase, arm, output)
                values[values.index('--collection-root')+1] = str(root/'collection')
                return values

            runner.main(argv('prepare'))
            trained = [runner.main(argv('train', arm)) for arm in runner.ARMS]
            self.assertEqual([result['fits'] for result in trained], [1,1])
            self.assertEqual([result['updates'] for result in trained], [400,400])
            self.assertEqual(trained[0]['reference_supervised_tokens'], trained[1]['reference_supervised_tokens'])
            self.assertGreater(trained[0]['actual_supervised_tokens'], trained[1]['actual_supervised_tokens'])
            for engine in state.engines[-2:]:
                self.assertEqual(engine.steps, 400)
                self.assertEqual(len(engine.optimizers), 1)
                self.assertEqual(engine.seed, 0)
                self.assertEqual(engine.arguments.phase, 'readout')
                self.assertEqual(engine.base.state, 'base')
            self.assertTrue(all(scale == 1 for scale in state.engines[-2].backward_scales))
            self.assertTrue(all(0 < scale < 1 for scale in state.engines[-1].backward_scales))
            self.assertEqual(runner.source.read(root/runner.ARMS[0]/'train/REFERENCE_MASKS.json'),
                             runner.source.read(root/runner.ARMS[1]/'train/REFERENCE_MASKS.json'))
            after = [runner.main(argv('after', arm)) for arm in runner.ARMS]
            for result, training in zip(after, trained):
                self.assertEqual(result['status'], 'COMPLETE')
                self.assertEqual(result['loaded_adapter_state_sha256'], training['adapter_state_after'])
                self.assertEqual(result['adapter_state_after'], training['adapter_state_after'])
                self.assertEqual(result['fits'], 0)
                self.assertLessEqual(result['model_calls'], 240)
                self.assertEqual(result['primary']['correct'], 4)
                self.assertEqual(result['primary']['denominator'], 4)
                self.assertEqual(result['primary']['individual']['denominator'], 8)
                self.assertEqual(len(result['panels']['TRAIN']), 2)
                self.assertEqual(len(result['panels']['PROBE']), 4)
                self.assertTrue(all(reference['summary']['paired']['correct']==0 for reference in result['deterministic_first_port']))
                self.assertTrue(all(reference['summary']['individual']['correct']==2 for reference in result['deterministic_first_port']))
                self.assertFalse(result['engineering_target_met'])
            self.assertEqual(after[0]['panels'], after[1]['panels'])
            state.factory.reset_mock()
            wrong = argv('after', runner.ARMS[0], root/'wrong-arm')
            wrong[wrong.index('--training')+1] = str(root/runner.ARMS[1]/'train')
            with self.assertRaisesRegex(ValueError, 'own_completed_goal_arm_required'):
                runner.main(wrong)
            state.factory.assert_not_called()
            path = root/runner.ARMS[1]/'train/MASKS.json'
            receipt_path = root/runner.ARMS[1]/'train/RESULT.json'
            original_mask, original_receipt = path.read_bytes(), receipt_path.read_bytes()
            masked = runner.source.read(path)
            masked[210]['labels'] = [-100] * len(masked[210]['labels'])
            write(path, masked)
            receipt = runner.source.read(receipt_path)
            receipt['training_files']['MASKS.json'] = runner.source.file_hash(path)
            write(receipt_path, receipt)
            with self.assertRaisesRegex(ValueError, 'saved_control_masks_drift'):
                runner.main(argv('after', runner.ARMS[1], root/'masked-old-trajectory'))
            state.factory.assert_not_called()
            path.write_bytes(original_mask)
            receipt_path.write_bytes(original_receipt)
            native_factory = state.factory.side_effect

            def invalid_factory(*args, **kwargs):
                engine = native_factory(*args, **kwargs)
                engine.invalid = True
                return engine

            state.factory.side_effect = invalid_factory
            invalid = runner.main(argv('after', runner.ARMS[0], root/'invalid-after'))
            self.assertEqual(invalid['status'], 'COMPLETE')
            self.assertEqual(invalid['primary']['correct'], 0)
            self.assertFalse(invalid['engineering_target_met'])

            def over_budget(inputs, generate, output):
                for unused in range(241):
                    generate([dict(role='user',content='fixture')], role='actor')

            with patch.object(runner, 'evaluate', side_effect=over_budget):
                with self.assertRaisesRegex(ValueError, 'goal_fit_native_call_cap'):
                    runner.main(argv('after', runner.ARMS[0], root/'over-cap'))
            failed = runner.source.read(root/'over-cap/FAILED.json')
            self.assertEqual(failed['model_calls'], 240)
            self.assertTrue(failed['cap_hit'])

    def test_native_capture_forgery_rejected_before_model_even_when_rehashed(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            path = root/'collection/teach/CALL_000.json'
            capture = runner.source.read(path)
            capture['response']['raw'] = 'ROUTE fabricated'
            write(path, capture)
            rehash(root/'collection/teach')
            values = cli(root, 'prepare')
            values[values.index('--collection-root')+1] = str(root/'collection')
            with self.assertRaises(ValueError):
                runner.main(values)
            state.factory.assert_not_called()
            state.token_loader.assert_not_called()
            self.assertTrue((root/'fit-prepare/FAILED.json').exists())

    def test_missing_terminal_stage_fails_closed(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            values = cli(root, 'prepare')
            values[values.index('--collection-root')+1] = str(root/'collection')
            write(root/'collection/baseline/FAILED.json', {'retained':True})
            with self.assertRaises(ValueError):
                runner.main(values)
            state.factory.assert_not_called()

    def test_nonfinite_loss_and_gradients_abort_preserving_partial_artifacts(self):
        for failure in ('loss','gradient'):
            with self.subTest(failure=failure), TemporaryDirectory() as temporary, ExitStack() as stack:
                engine = fake_engine()
                if failure == 'loss':
                    engine.mean_loss = float('nan')
                else:
                    engine.gradient = float('nan')
                stack.enter_context(patch.object(runner, 'encode_material', return_value=encoded_fixture()))
                stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', return_value=runner.PARENT_STATE))
                output = Path(temporary)
                with self.assertRaisesRegex(ValueError, 'invalid_goal_' + failure):
                    runner.train(engine, dict(material={'fixture':True}), output, runner.ARMS[0])
                self.assertTrue((output/'DOSE.json').exists())
                self.assertTrue((output/'LOSSES.jsonl').exists())
                engine.optimizer.step.assert_not_called()

    def test_import_without_ml_and_exact_archive_guard_budget(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch','transformers','peft','tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_goal_pair_train
"""
        result = subprocess.run([sys.executable,'-B','-c',script],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        guard = Path(runner.__file__).with_name('astra_goal_pair_train_guard.sh')
        result = subprocess.run(['bash','-n',str(guard)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        text = guard.read_text()
        for fragment in ('test "$#" -eq 6','cat "$root/source_commit.txt"','run_stage 7200 --phase train',
                'run_stage 3600 --phase after','admission_started + 11220','-gt 300','1789980180-21600',
                'CUDA_VISIBLE_DEVICES= python3','"$index" "$uuid"','service_exceptions.json','OMP_NUM_THREADS=1',
                'deadline - $(date +%s) - 60','--kill-after=60','test ! -e "$root/$arm"'):
            self.assertIn(fragment,text)
        self.assertNotIn('git -C',text)


if __name__ == '__main__':
    unittest.main()
