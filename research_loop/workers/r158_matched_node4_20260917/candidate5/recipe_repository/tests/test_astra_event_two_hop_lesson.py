"""CPU-only native trajectory-driver contracts; no model or GPU runtime."""

from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_event_two_hop_lesson as runner
from organism_v6 import experienced_event_reader_audit_lesson as audit
from tests.test_astra_event_two_hop import arguments as prior_arguments, fixture
from tests.test_astra_selected_reader_repair import write
from tests.test_experienced_event_two_hop import generation


def arguments(root, phase, output=None):
    result = prior_arguments(root, phase, output or root / ('lesson-' + phase))
    result += ['--event-collection', str(root / 'collect'), '--baseline', str(root / 'readout')]
    if phase in ('train', 'after'):
        result += ['--lessons', str(root / 'lesson-collect')]
    if phase == 'after':
        result += ['--training', str(root / 'lesson-train')]
    return result


def setup(root, stack):
    state = fixture(root, stack)
    runner.prior.main(prior_arguments(root, 'collect'))
    runner.prior.main(prior_arguments(root, 'readout') + ['--protocol', 'turnbound'])
    banks = [runner.source.material.build_bank(seed + '-a') + runner.source.material.build_bank(seed + '-b')
             for seed in ('lesson-old', 'lesson-fresh')]
    episodes = [[dict(event=dict(raw=runner.source.material._event(fact))) for fact in bank]
                for bank in banks]
    events = [dict(event=fact['event'], raw=runner.source.material._event(fact))
              for bank in banks for fact in bank]
    state.held = audit.build_cases(events[:4], audit.HELD)
    previous = dict(memory_rows=[{'old': index} for index in range(64)],
                    cue_rows=[{'cue': index} for index in range(20)],
                    lesson_rows=[{'audit': index} for index in range(62)],
                    old_bank=banks[0], old_episodes=episodes[0], held=state.held)
    stack.enter_context(patch.object(runner.prior.previous, 'load_parent', return_value=previous))
    stack.enter_context(patch.object(runner.prior.previous, 'read_collection', return_value=(
        dict(bank=banks[1], episodes=episodes[1]), [{'fresh': index} for index in range(64)], 'fresh')))
    factory = state.factory.side_effect

    def lesson_engine(*args, **kwargs):
        engine = factory(*args, **kwargs)
        engine.store.update({event['event']: event['raw'] for event in events})
        if Path(engine.arguments.adapter_dir) == root / 'lesson-train/adapter':
            engine.state = 'trained-state'
        original = engine.generate

        def generate(messages, *, max_new_tokens):
            if max_new_tokens != 160:
                raise AssertionError('token bound drift')
            guidance = 'Execute only this next command, then wait for actual feedback:\n'
            if guidance in messages[-1]['content']:
                engine.calls.append(dict(messages=deepcopy(messages), adapter_off=engine.off))
                return generation(messages[-1]['content'].split(guidance)[1] + '\n\n', messages)
            if messages[0]['content'] == audit.SYSTEM:
                engine.calls.append(dict(messages=deepcopy(messages), adapter_off=engine.off))
                return generation('NONE', messages)
            return original(messages, max_new_tokens=max_new_tokens)

        engine.generate = generate
        return engine

    state.factory.side_effect = lesson_engine
    state.factory.reset_mock()
    state.tokenizer.reset_mock()
    return state


def fake_train(engine, inputs, rows, output):
    engine.state = 'trained-state'
    (output / 'adapter').mkdir()
    (output / 'adapter/adapter_model.safetensors').write_text('fake trained adapter')
    runner.source.write(output / 'RECIPE.json', {'updates': 100})
    return dict(fits=1, updates=100, adapter_state_after=engine.state,
                adapter_files={'adapter_model.safetensors': runner.source.file_hash(
                    output / 'adapter/adapter_model.safetensors')},
                training_files={'RECIPE.json': runner.source.file_hash(output / 'RECIPE.json')})


class TwoHopLessonDriverTests(unittest.TestCase):
    def test_import_without_native_dependencies(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_event_two_hop_lesson
"""
        completed = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_schedule_exact_layout_and_200_trajectory_presentations(self):
        self.assertEqual(runner.UPDATES, 100)
        schedule = [runner.training_indexes(update) for update in range(1, 101)]
        self.assertEqual(schedule, [(offset % 128, 128 + offset % 82,
                                    210 + 2 * offset % 12, 210 + (2 * offset + 1) % 12)
                                   for offset in range(100)])
        counts = Counter(index for batch in schedule for index in batch[2:])
        self.assertEqual(set(counts), set(range(210, 222)))
        self.assertEqual(sum(counts.values()), 200)
        self.assertEqual([counts[index] for index in range(210, 222)], [17] * 8 + [16] * 4)
        for invalid in (0, 101, -1, True, 1.0, '1'):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'fixed_100_updates_required'):
                runner.training_indexes(invalid)

    def test_prepare_no_model_exclusive_output_and_source_binding(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            result = runner.main(arguments(root, 'prepare'))
            self.assertEqual((result['status'], result['fits'], result['model_calls']), ('PREPARED_NO_MODEL', 0, 0))
            self.assertEqual(result['binding']['parent'], state.parent)
            for field, path in (('baseline_result_sha256', 'readout/RESULT.json'),
                                ('collection_result_sha256', 'collect/RESULT.json')):
                self.assertEqual(result['binding'][field], runner.source.file_hash(root / path))
            state.factory.assert_not_called()
            state.tokenizer.assert_not_called()
            with self.assertRaises(FileExistsError):
                runner.main(arguments(root, 'prepare'))

    def test_wrong_parent_and_baseline_joins_block_before_loading(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            path = root / 'readout/RESULT.json'
            baseline = runner.source.read(path)
            mutations = dict(source={}, collection_result_sha256='wrong',
                             adapter_state_after='wrong', loaded_adapter_state_sha256='wrong',
                             arguments={'protocol': 'original'}, frozen_base_unchanged=False)
            for field, value in mutations.items():
                with self.subTest(field=field):
                    write(path, dict(baseline, **{field: value}))
                    output = root / ('bad-' + field)
                    with self.assertRaisesRegex(ValueError, 'same_parent_turnbound_baseline_required'):
                        runner.main(arguments(root, 'prepare', output))
                    self.assertTrue((output / 'FAILED.json').exists())
            write(path, baseline)
            runner.source.write(root / 'readout/FAILED.json', {'error': 'captured baseline failure'})
            with self.assertRaisesRegex(ValueError, 'failed_two_hop_baseline'):
                runner.main(arguments(root, 'prepare', root / 'failed-baseline'))
            state.factory.assert_not_called()
            state.tokenizer.assert_not_called()

    def test_fake_collect_train_after_lifecycle_is_parent_free_readonly(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            collected = runner.main(arguments(root, 'collect'))
            self.assertTrue(collected['parent_present'])
            self.assertEqual(collected['model_calls'], 12)
            rows, digest = runner.read_lessons(root / 'lesson-collect', collected['binding'])
            self.assertEqual(len(rows), 12)
            self.assertEqual(digest, runner.source.file_hash(root / 'lesson-collect/RESULT.json'))
            with patch.object(runner, 'train', side_effect=fake_train) as train:
                trained = runner.main(arguments(root, 'train'))
            train.assert_called_once()
            self.assertEqual(trained['lessons_result_sha256'], digest)
            self.assertEqual(trained['model_calls'], 0)
            before = runner.source.file_hash(root / 'lesson-train/adapter/adapter_model.safetensors')
            after = runner.main(arguments(root, 'after'))
            self.assertFalse(after['parent_present'])
            self.assertEqual((after['fits'], after['status']), (0, 'COMPLETE'))
            self.assertEqual(after['loaded_adapter_state_sha256'], 'trained-state')
            self.assertEqual(after['adapter_state_after'], 'trained-state')
            self.assertEqual(set(after['panels']), set(runner.prior.CONDITIONS))
            self.assertEqual(len(after['panels']), 4)
            self.assertEqual(after['max_native_calls'], 160)
            self.assertEqual(after['model_calls'], 160)
            self.assertEqual(after['max_new_tokens'], 160)
            captures = [runner.source.read(path) for path in sorted((root / 'lesson-after').glob('CALL_*.json'))]
            self.assertEqual(Counter(capture['role'] for capture in captures),
                             {'actor': 96, 'memory': 16, 'retention': 32, 'held_audit': 16})
            self.assertNotIn('PARENT', str([capture['messages'] for capture in captures]))
            self.assertEqual(after['retention'], {'0': {'correct': 16, 'denominator': 16},
                                                  '8': {'correct': 16, 'denominator': 16}})
            self.assertEqual(state.engines[-1].state, 'trained-state')
            self.assertEqual(state.engines[-1].base_checks, 1)
            self.assertEqual(before, runner.source.file_hash(root / 'lesson-train/adapter/adapter_model.safetensors'))
            self.assertFalse((root / 'lesson-after/adapter').exists())

    def test_failed_incomplete_or_changed_actual_lessons_block_training(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            runner.main(arguments(root, 'collect'))
            directory = root / 'lesson-collect'
            original = runner.source.read(directory / 'RESULT.json')
            document = runner.source.read(directory / 'LESSONS.json')
            capture = runner.source.read(directory / 'CALL_000.json')
            for mutation in ('failed', 'incomplete', 'actual_target', 'missing_call', 'hash', 'native_capture'):
                with self.subTest(mutation=mutation):
                    write(directory / 'RESULT.json', original)
                    write(directory / 'LESSONS.json', document)
                    write(directory / 'CALL_000.json', capture)
                    if mutation == 'failed':
                        runner.source.write(directory / 'FAILED.json', {'error': 'retained'})
                    elif mutation == 'incomplete':
                        write(directory / 'RESULT.json', dict(original, model_calls=11))
                    elif mutation in ('actual_target', 'hash'):
                        changed = deepcopy(document)
                        changed['rows'][0]['assistant'] = 'ROUTE invented'
                        write(directory / 'LESSONS.json', changed)
                        if mutation == 'actual_target':
                            write(directory / 'RESULT.json', dict(original,
                                lessons_sha256=runner.source.file_hash(directory / 'LESSONS.json')))
                    elif mutation == 'native_capture':
                        changed = deepcopy(capture)
                        changed['response']['raw'] = 'ROUTE invented'
                        write(directory / 'CALL_000.json', changed)
                    else:
                        (directory / 'CALL_000.json').rename(directory / 'saved-call.json')
                    state.factory.reset_mock()
                    with patch.object(runner, 'train') as train, self.assertRaises(ValueError):
                        runner.main(arguments(root, 'train', root / ('blocked-' + mutation)))
                    train.assert_not_called()
                    state.factory.assert_not_called()
                    if mutation == 'failed':
                        (directory / 'FAILED.json').unlink()
                    if mutation == 'missing_call':
                        (directory / 'saved-call.json').rename(directory / 'CALL_000.json')

    def test_read_training_state_hash_and_lesson_join(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            setup(root, stack)
            collected = runner.main(arguments(root, 'collect'))
            with patch.object(runner, 'train', side_effect=fake_train):
                original = runner.main(arguments(root, 'train'))
            directory = root / 'lesson-train'
            binding, digest = collected['binding'], original['lessons_result_sha256']
            result, result_hash = runner.read_training(directory, binding, digest)
            self.assertEqual(result, original)
            self.assertEqual(result_hash, runner.source.file_hash(directory / 'RESULT.json'))
            for field, value in (('adapter_state_after', runner.prior.PARENT_STATE),
                                 ('loaded_adapter_state_sha256', 'wrong'), ('updates', 99),
                                 ('lessons_result_sha256', 'wrong'), ('binding', {})):
                with self.subTest(field=field):
                    write(directory / 'RESULT.json', dict(original, **{field: value}))
                    with self.assertRaisesRegex(ValueError, 'own_completed_trajectory_sleep_required'):
                        runner.read_training(directory, binding, digest)
            write(directory / 'RESULT.json', original)
            for path in (directory / 'RECIPE.json', directory / 'adapter/adapter_model.safetensors'):
                contents = path.read_text()
                path.write_text('changed')
                with self.assertRaisesRegex(ValueError, 'saved_training_file_drift'):
                    runner.read_training(directory, binding, digest)
                path.write_text(contents)
            runner.source.write(directory / 'FAILED.json', {'error': 'retained training failure'})
            with self.assertRaisesRegex(ValueError, 'failed_trajectory_training'):
                runner.read_training(directory, binding, digest)

    def test_after_checks_actual_mounted_state_readonly_state_and_base(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            runner.main(arguments(root, 'collect'))
            with patch.object(runner, 'train', side_effect=fake_train):
                runner.main(arguments(root, 'train'))
            factory = state.factory.side_effect
            for mutation, error in (('mounted', 'mounted_trajectory_state_required'),
                                    ('readonly', 'readonly_trajectory_phase_changed_adapter'),
                                    ('files', 'readonly_trajectory_adapter_files_changed'),
                                    ('base', 'captured changed base')):
                with self.subTest(mutation=mutation):
                    def changed_engine(*args, **kwargs):
                        engine = factory(*args, **kwargs)
                        if mutation == 'mounted':
                            engine.state = runner.prior.PARENT_STATE
                        elif mutation == 'readonly':
                            engine.mutate_state = True
                        elif mutation == 'files':
                            engine.mutate_file = root / 'lesson-train/adapter/adapter_model.safetensors'
                        else:
                            engine.verify_base = lambda: runner.require(False, 'captured changed base')
                        return engine

                    state.factory.side_effect = changed_engine
                    output = root / ('after-' + mutation)
                    with self.assertRaisesRegex(ValueError, error):
                        runner.main(arguments(root, 'after', output))
                    failure = runner.source.read(output / 'FAILED.json')
                    self.assertIn(error, failure['error'])
                    self.assertEqual(failure['model_calls'], 0 if mutation == 'mounted' else 160)
                    self.assertFalse((output / 'RESULT.json').exists())
                    if mutation == 'files':
                        (root / 'lesson-train/adapter/adapter_model.safetensors').write_text('fake trained adapter')


if __name__ == '__main__':
    unittest.main()
