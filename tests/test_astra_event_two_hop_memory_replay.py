"""CPU-only replay-repair schedule, reference proofs, masks and lifecycle tests."""

from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_event_two_hop_memory_replay as runner
from tests.test_astra_event_two_hop_memory import arguments as memory_arguments
from tests.test_astra_event_two_hop_memory import material_fixture, setup, write


def arguments(root, phase):
    values = ['--phase', phase, '--output', str(root / ('replay-' + phase)), '--gpu-uuid', 'fake-gpu',
        '--reference-root', str(root), '--lesson-root', str(root / 'lesson'), '--transfer-root', str(root / 'transfer')]
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root'):
        values += ['--' + name, str(root / name)]
    if phase == 'after':
        values += ['--training', str(root / 'replay-train')]
    return values


def reference(root, stack, material):
    state = setup(root, stack, material)
    for phase in ('before', 'train', 'after'):
        runner.memory.main(memory_arguments(root, phase))
    state.factory.reset_mock()
    state.token_loader.reset_mock()
    return state


def rehash_readout(directory):
    result = runner.source.read(directory / 'RESULT.json')
    result['output_files'] = {path.name: runner.source.file_hash(path) for path in directory.glob('*.json')
                              if path.name != 'RESULT.json'}
    write(directory / 'RESULT.json', result)


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = material_fixture()

    def test_single_fixed_batch_six_recipe_preserves_base_schedule(self):
        doses = Counter()
        for update in range(1, 101):
            indexes = runner.training_indexes(update)
            self.assertEqual(indexes[:4], runner.memory.training_indexes(update))
            self.assertEqual(indexes[4:], (210 + (2 * (update - 1)) % 12, 210 + (2 * (update - 1) + 1) % 12))
            self.assertEqual(len(indexes), 6)
            self.assertTrue(all(0 <= index < 254 for index in indexes))
            doses.update(indexes)
        self.assertEqual(sum(doses.values()), 600)
        self.assertEqual([sum(doses[index] for index in range(start, end)) for start, end in
                          ((0, 128), (128, 148), (148, 210), (210, 222), (222, 254))], [100, 26, 62, 212, 200])
        self.assertEqual([sum(doses[index] for index in range(222, 254) if (index - 222) % 4 == fact)
                          for fact in range(4)], [50] * 4)
        self.assertEqual([doses[index] for index in range(210, 222)], [18] * 8 + [17] * 4)
        recipe = runner.recipe()
        self.assertEqual((recipe['batch_size'], recipe['seed'], recipe['updates'], recipe['learning_rate']), (6, 0, 100, 3e-5))
        self.assertEqual(recipe['extra_actual_trajectory_presentations'], 200)
        self.assertTrue(recipe['increased_budget'])
        self.assertFalse(recipe['actual_token_equality_claim'])
        for update in (0, 101, True, 1.5):
            with self.assertRaises(ValueError):
                runner.training_indexes(update)

    def test_six_row_collator_preserves_targets_and_masks_padding(self):
        rows = [runner.source.native.EncodedRow(tuple(range(10, 10 + length)),
                (-100,) * (length - 2) + (length + 8, -100), (length + 8,)) for length in range(3, 9)]
        batch = runner.collate_six(rows, pad_id=151643)
        self.assertEqual(len(batch['input_ids']), 6)
        for index, row in enumerate(rows):
            width = len(row.input_ids)
            self.assertEqual(batch['input_ids'][index], list(row.input_ids) + [151643] * (8 - width))
            self.assertEqual(batch['labels'][index], list(row.labels) + [-100] * (8 - width))
            self.assertEqual(batch['attention_mask'][index], [1] * width + [0] * (8 - width))
            self.assertEqual([value for value in batch['labels'][index] if value != -100], list(row.target_ids))
        with self.assertRaisesRegex(ValueError, 'batch_six_required'):
            runner.collate_six(rows[:4], pad_id=151643)

    def test_prepare_reuses_exact_old_binding_and_saved_rows_without_models_or_efficiency_gate(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = reference(root, stack, self.material)
            before = runner.source.read(root / 'before/RESULT.json')
            reference_train = runner.source.read(root / 'train/RESULT.json')
            result = runner.main(arguments(root, 'prepare'))
            self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
            self.assertEqual((result['model_calls'], result['fits'], result['max_native_calls']), (0, 0, 0))
            self.assertEqual(result['binding']['memory_binding'], before['binding'])
            self.assertEqual(result['binding']['starting_parent_state'], runner.PARENT_STATE)
            self.assertEqual(result['binding']['reference_adapter_state'], reference_train['adapter_state_after'])
            self.assertNotEqual(reference_train['adapter_state_after'], runner.PARENT_STATE)
            self.assertEqual(result['reference_summary']['before_parametric'], 4)
            self.assertEqual(result['reference_summary']['after_panels']['PARAMETRIC']['correct'], 4)
            state.factory.assert_not_called()
            state.token_loader.assert_not_called()
            self.assertEqual(len(state.engines), 3)
            self.assertFalse((root / 'replay-before').exists())
            self.assertFalse((root / 'replay-collect').exists())
            self.assertEqual(result['binding']['saved_rows_sha256'], runner.source.file_hash(root / 'train/TRAINING_ROWS.json'))

    def test_reference_full_after_rejects_resealed_native_recall_audit_and_taught_drift(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = reference(root, stack, self.material)
            inputs = runner.memory.load_inputs(SimpleNamespace(lesson_root=str(root / 'lesson'), transfer_root=str(root / 'transfer'),
                cycle_root=str(root / 'cycle-root')))
            before_sha = runner.source.file_hash(root / 'before/RESULT.json')
            training = runner.source.read(root / 'train/RESULT.json')
            training_sha = runner.source.file_hash(root / 'train/RESULT.json')
            after = root / 'after'
            original_result = runner.source.read(after / 'RESULT.json')
            for name, mutate in (
                ('CALL_000.json', lambda doc: doc['response'].update(raw=doc['response']['raw'] + '\n')),
                ('NEW_RECALL_W8_00.json', lambda doc: doc.update(expected='fabricated')),
                ('OLD_RECALL_W0_15.json', lambda doc: doc.update(correct=not doc['correct'])),
                ('HELD_AUDIT.json', lambda doc: doc['captures'][0]['response'].update(raw='forged')),
                ('TAUGHT_OWN_TEXT_EPISODE_03.json', lambda doc: doc['score'].update(correct=not doc['score']['correct'])),
                ('FRESH_PARAMETRIC_EPISODE_00.json', lambda doc: doc['episode']['traces'][1]['response'].update(raw='MISS')),
                ('STATES.json', lambda doc: doc.update(after=runner.PARENT_STATE)),
            ):
                with self.subTest(name=name):
                    original = runner.source.read(after / name)
                    forged = deepcopy(original)
                    mutate(forged)
                    write(after / name, forged)
                    rehash_readout(after)
                    with self.assertRaises(ValueError):
                        runner.read_reference_after(after, inputs, training, training_sha, before_sha)
                    write(after / name, original)
                    write(after / 'RESULT.json', original_result)
            state.factory.assert_not_called()

    def test_reference_after_result_joins_are_required_before_any_new_model(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = reference(root, stack, self.material)
            original = runner.source.read(root / 'after/RESULT.json')
            for field, value in (('status', 'FAILED'), ('fits', 1), ('before_result_sha256', 'forged'),
                                  ('training_result_sha256', 'forged'), ('adapter_state_after', runner.PARENT_STATE),
                                  ('protocol', 'original')):
                with self.subTest(field=field):
                    write(root / 'after/RESULT.json', dict(original, **{field: value}))
                    output = root / ('rejected-' + field)
                    args = arguments(root, 'prepare')
                    args[args.index('--output') + 1] = str(output)
                    with self.assertRaises(ValueError):
                        runner.main(args)
                    state.factory.assert_not_called()
                    state.token_loader.assert_not_called()
            write(root / 'after/RESULT.json', original)

    def test_fit_from_37ec_same254_rows_masks_and_exact212_trajectory_presentations(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = reference(root, stack, self.material)
            reference_after_sha = runner.source.file_hash(root / 'after/RESULT.json')
            result = runner.main(arguments(root, 'train'))
            engine = state.engines[-1]
            self.assertEqual(result['loaded_adapter_state_sha256'], runner.PARENT_STATE)
            self.assertEqual(Path(engine.arguments.adapter_dir), root / 'lesson/train/adapter')
            self.assertNotEqual(Path(engine.arguments.adapter_dir), root / 'train/adapter')
            self.assertEqual((engine.steps, len(engine.optimizers), engine.seed), (100, 1, 0))
            self.assertEqual(engine.optimizers[0]['parameters'], [engine.parameter])
            self.assertEqual(engine.optimizers[0]['lr'], 3e-5)
            self.assertFalse(engine.base.requires_grad)
            self.assertEqual((result['fits'], result['updates'], result['model_calls']), (1, 100, 0))
            self.assertEqual(result['before_result_sha256'], runner.source.file_hash(root / 'before/RESULT.json'))
            self.assertEqual(result['reference_after_result_sha256'], reference_after_sha)
            self.assertEqual(runner.source.file_hash(root / 'replay-train/TRAINING_ROWS.json'),
                             runner.source.file_hash(root / 'train/TRAINING_ROWS.json'))
            self.assertEqual(runner.source.read(root / 'replay-train/MASKS.json'), runner.source.read(root / 'train/MASKS.json'))
            losses = [json.loads(line) for line in (root / 'replay-train/LOSSES.jsonl').read_text().splitlines()]
            self.assertEqual(len(losses), 100)
            self.assertTrue(all(len(record['row_indexes']) == 6 for record in losses))
            self.assertEqual(result['actual_supervised_tokens'], sum(record['active_label_count'] for record in losses))
            self.assertEqual(sum(result['row_presentations']), 600)
            self.assertEqual(sum(result['row_presentations'][210:222]), 212)
            for encoded in runner.source.read(root / 'replay-train/MASKS.json'):
                self.assertEqual([label for label in encoded['labels'] if label != -100], encoded['target_ids'])
                self.assertNotIn('PARENT PROCEDURAL GUIDANCE', engine.tokenizer.decode(encoded['input_ids']))
            after = runner.main(arguments(root, 'after'))
            self.assertEqual(after['loaded_adapter_state_sha256'], result['adapter_state_after'])
            self.assertEqual(after['adapter_state_after'], result['adapter_state_after'])
            self.assertEqual(after['model_calls'], 168)
            self.assertEqual(after['role_calls'], dict(actor=96, memory=16, new_recall=8, old_recall=32, held_audit=16))
            self.assertEqual(set(after['panels']), set(runner.memory.CONDITIONS))
            self.assertEqual(after['old_recall']['0']['denominator'], 16)
            self.assertEqual(after['held_audit']['overall']['denominator'], 16)
            self.assertEqual(after['taught_graph']['OWN_TEXT']['denominator'], 4)
            self.assertEqual(state.engines[-1].optimizers, [])
            self.assertEqual(runner.source.file_hash(root / 'after/RESULT.json'), reference_after_sha)

    def test_wrong_mounted_reference_writer_and_incomplete_reference_fail_before_gradients(self):
        with self.assertRaisesRegex(ValueError, 'complete_reference_before_and_after_required'):
            runner.train(None, {}, None)
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = reference(root, stack, self.material)
            factory = state.factory.side_effect
            reference_state = runner.source.read(root / 'train/RESULT.json')['adapter_state_after']

            def wrong_parent(*args, **kwargs):
                engine = factory(*args, **kwargs)
                engine.parameter.state = reference_state
                return engine

            state.factory.side_effect = wrong_parent
            with self.assertRaisesRegex(ValueError, 'mounted_replay_state_required'):
                runner.main(arguments(root, 'train'))
            self.assertEqual(state.engines[-1].steps, 0)
            self.assertEqual(state.engines[-1].optimizers, [])

    def test_saved_new_training_joins_reject_forged_recipe_and_reference(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = reference(root, stack, self.material)
            result = runner.main(arguments(root, 'train'))
            state.factory.reset_mock()
            forged = dict(result, reference_after_result_sha256='forged')
            write(root / 'replay-train/RESULT.json', forged)
            with self.assertRaisesRegex(ValueError, 'own_completed_replay_write_required'):
                runner.main(arguments(root, 'after'))
            state.factory.assert_not_called()

    def test_after_call_cap_blocks169_and_does_not_refit(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = reference(root, stack, self.material)
            trained = runner.main(arguments(root, 'train'))
            saved_sha = runner.source.file_hash(root / 'replay-train/RESULT.json')

            def exceed(inputs, generate, output, phase):
                for unused in range(169):
                    generate(runner.memory.memory_messages(inputs['collection']['records'][0]['edge']['event']), role='memory')

            with patch.object(runner.memory, 'evaluate', side_effect=exceed), self.assertRaisesRegex(ValueError, 'replay_native_call_cap'):
                runner.main(arguments(root, 'after'))
            self.assertEqual(state.engines[-1].native_calls, 168)
            self.assertEqual(state.engines[-1].optimizers, [])
            self.assertEqual(runner.source.file_hash(root / 'replay-train/RESULT.json'), saved_sha)
            runner.memory.transfer.verify_files(root / 'replay-train/adapter', trained['adapter_files'])
            self.assertTrue(runner.source.read(root / 'replay-after/FAILED.json')['cap_hit'])
            with self.assertRaises(FileExistsError):
                runner.main(arguments(root, 'after'))

    def test_prepare_has_no_ml_import_and_only_three_phases(self):
        script = '''
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_event_two_hop_memory_replay
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(runner.CAPS, dict(prepare=0, train=0, after=168))
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            values = arguments(root, 'after')
            index = values.index('--training')
            del values[index:index + 2]
            with self.assertRaisesRegex(ValueError, 'replay_phase_arguments'):
                runner.main(values)
            self.assertFalse((root / 'replay-after').exists())


class GuardTests(unittest.TestCase):
    def test_only_train_after_3660_each_offline_physical_cvd_and_archive_source(self):
        guard = Path(runner.__file__).with_name('astra_event_two_hop_memory_replay_guard.sh')
        result = subprocess.run(['bash', '-n', str(guard)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = guard.read_text()
        for fragment in ('test "$#" -eq 5', '"$root/source_commit.txt"', 'CUDA_VISIBLE_DEVICES= python3',
                '"$index" "$uuid"', 'service_exceptions.json', '1789980180-21600', 'seconds=3600', '--kill-after=60',
                'run_stage --phase train', 'run_stage --phase after --training "$root/train"',
                '--reference-root /tmp/astra_event_two_hop_memory_20260914_attempt1', 'HF_HUB_OFFLINE=1'):
            self.assertIn(fragment, text)
        for forbidden in ('git ', '--phase before', '--phase collect', '--before ', '--learning-rate', '--updates'):
            self.assertNotIn(forbidden, text)
        self.assertEqual(text.count('run_stage --phase train'), 1)
        self.assertEqual(text.count('run_stage --phase after'), 1)

    def test_stubbed_scanner_abort_does_not_launch_or_require_git(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = root / 'source/gpu/astra_event_two_hop_memory_replay.py'
            entry.parent.mkdir(parents=True)
            entry.write_bytes(Path(runner.__file__).read_bytes())
            write(root / 'prepare/RESULT.json', dict(schema=runner.SCHEMA, phase='prepare', status='PREPARED_NO_MODEL',
                entry_sha256=runner.source.file_hash(entry)))
            commit = 'a' * 40
            (root / 'source_commit.txt').write_text(commit + '\n')
            binaries = root / 'bin'
            binaries.mkdir()
            scripts = dict(timeout='#!/bin/bash\nexit 1\n', sleep='#!/bin/bash\nexit 0\n',
                python3='#!/bin/bash\nif [[ "$2" == "import time;"* ]]; then exit 0; fi\nexec '
                        + sys.executable + ' "$@"\n')
            for name, text in scripts.items():
                path = binaries / name
                path.write_text(text)
                path.chmod(0o700)
            guard = Path(runner.__file__).with_name('astra_event_two_hop_memory_replay_guard.sh')
            environment = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ['PATH'])
            result = subprocess.run(['bash', str(guard), str(root), str(root / 'source'), commit, '1', 'fake-gpu'],
                                    env=environment, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 1)
            self.assertTrue((root / 'launch/GUARD_ABORT.txt').exists())
            self.assertFalse((root / 'train').exists())
            self.assertFalse((root / 'source/.git').exists())


if __name__ == '__main__':
    unittest.main()
