"""CPU-only provenance and matched-stimulus contracts; never native calls."""

from contextlib import ExitStack
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_event_two_hop_transfer as runner
from tests.test_astra_event_two_hop import arguments as prior_arguments, fixture
from tests.test_astra_selected_reader_repair import write
from tests.test_experienced_event_two_hop import generation


def arguments(root, phase, arm='TRAINED', output=None):
    return prior_arguments(root, phase, output or root / (arm if phase == 'readout' else phase)) + [
        '--arm', arm, '--lesson-root', str(root / 'lesson')]


def setup(root, stack):
    state = fixture(root, stack)
    model = root / 'base'
    write(model / 'config.json', dict(model_type='qwen2', hidden_size=3584, num_hidden_layers=28))
    (model / 'model.safetensors').write_text('fake immutable base')
    state.original['model_dir'] = str(model)
    adapter = Path(state.parent['adapter_dir'])
    write(adapter / 'adapter_config.json', {'r': 8})
    state.parent['parent_adapter_files']['adapter_config.json'] = runner.source.file_hash(adapter / 'adapter_config.json')
    lesson = root / 'lesson'
    (lesson / 'launch').mkdir(parents=True)
    (lesson / 'launch/source_commit.txt').write_text(runner.SOURCE_COMMIT + '\n')
    recorded = dict(parent=state.parent)
    for field, name in (('lesson_helper_sha256', 'experienced_event_two_hop_lesson.py'),
                        ('actor_helper_sha256', 'experienced_event_two_hop.py')):
        path = lesson / 'source/organism_v6' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('captured historical helper, deliberately not current ' + name)
        recorded[field] = runner.source.file_hash(path)
    common = dict(schema=runner.lesson_driver.SCHEMA, status='COMPLETE', binding=recorded,
        fits=0, loaded_adapter_state_sha256=runner.prior.PARENT_STATE,
        adapter_state_after=runner.prior.PARENT_STATE, frozen_base_unchanged=True, parent_present=False)
    write(lesson / 'collect/RESULT.json', dict(common, phase='collect'))
    trained = lesson / 'train'
    write(trained / 'adapter/adapter_config.json', {'r': 8})
    (trained / 'adapter/adapter_model.safetensors').write_text('fake trained adapter')
    training_files = {}
    for name in ('TRAINING_ROWS.json', 'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl'):
        write(trained / name, {'fixture': name})
        training_files[name] = runner.source.file_hash(trained / name)
    training = dict(common, phase='train', fits=1, updates=100, adapter_state_after=runner.TRAINED_STATE,
        lessons_result_sha256=runner.source.file_hash(lesson / 'collect/RESULT.json'),
        training_files=training_files, adapter_files={path.name: runner.source.file_hash(path)
            for path in (trained / 'adapter').iterdir()})
    write(trained / 'RESULT.json', training)
    write(lesson / 'after/RESULT.json', dict(common, phase='after',
        loaded_adapter_state_sha256=runner.TRAINED_STATE, adapter_state_after=runner.TRAINED_STATE,
        lessons_result_sha256=training['lessons_result_sha256'],
        training_result_sha256=runner.source.file_hash(trained / 'RESULT.json')))
    banks = [runner.source.material.build_bank('transfer-fixture-' + str(index)) for index in range(4)]
    state.previous = dict(old_bank=sum(banks[:3], []))
    state.current = dict(bank=banks[3])
    stack.enter_context(patch.object(runner.prior.previous, 'load_parent', return_value=state.previous))
    stack.enter_context(patch.object(runner.prior.previous, 'read_collection', return_value=(state.current, [], 'actual-a3')))
    stack.enter_context(patch.object(runner.lesson_driver, 'load_inputs', side_effect=AssertionError('must use recorded binding')))
    original_factory = state.factory.side_effect

    def factory(*args, **kwargs):
        engine = original_factory(*args, **kwargs)
        if Path(engine.arguments.adapter_dir) == trained / 'adapter':
            engine.state = runner.TRAINED_STATE
        return engine

    state.factory.side_effect = factory
    return state


class TransferTests(unittest.TestCase):
    def test_import_without_ml(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_event_two_hop_transfer
"""
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_prepare_uses_historical_binding_no_model(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            result = runner.main(arguments(root, 'prepare'))
            self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
            self.assertEqual(result['max_native_calls'], 0)
            self.assertFalse(result['trainingAllowed'])
            self.assertNotEqual(result['binding']['recorded_training_binding']['actor_helper_sha256'],
                                runner.source.file_hash(runner.hop.__file__))
            state.factory.assert_not_called()
            state.tokenizer.assert_not_called()
            with self.assertRaises(FileExistsError):
                runner.main(arguments(root, 'prepare'))

    def test_matched_arms_exact_text_readonly_caps(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            collection = runner.main(arguments(root, 'collect'))
            self.assertEqual(collection['model_calls'], 8)
            self.assertEqual(collection['accepted_events'], 4)
            results = [runner.main(arguments(root, 'readout', arm)) for arm in ('TRAINED', 'ORIGINAL')]
            self.assertEqual(results[0]['shared_text_sha256'], results[1]['shared_text_sha256'])
            self.assertEqual(results[0]['collection_result_sha256'], results[1]['collection_result_sha256'])
            store = runner.hop.exact_text_store(runner.source.read(root / 'collect/COLLECTION.json'))
            for result, engine in zip(results, state.engines[1:]):
                self.assertLessEqual(result['model_calls'], 48)
                self.assertEqual(result['fits'], 0)
                self.assertEqual(result['adapter_state_after'], result['loaded_adapter_state_sha256'])
                self.assertEqual(engine.arguments.phase, 'readout')
                self.assertEqual(engine.disable_entries, 0)
                self.assertEqual(set(result['panels']), {'OWN_TEXT', 'UNAVAILABLE'})
                for condition, panel in result['panels'].items():
                    self.assertEqual(panel['denominator'], 4)
                    for record in panel['tasks']:
                        self.assertLessEqual(record['score']['actor_calls'], 6)
                        self.assertLessEqual(len(record['reads']), 4)
                        self.assertLessEqual(len(record['routes']), 2)
                        for trace in record['reads']:
                            self.assertEqual(trace['response'], store[trace['address']] if condition == 'OWN_TEXT' else 'MEMORY UNAVAILABLE')
            self.assertEqual(results[0]['panels'], results[1]['panels'])

    def test_training_joins_and_file_tampering_block_before_model(self):
        mutations = [('train', 'adapter_state_after', 'bad'), ('train', 'loaded_adapter_state_sha256', 'bad'),
            ('train', 'updates', 99), ('train', 'fits', 0), ('train', 'frozen_base_unchanged', False),
            ('after', 'adapter_state_after', 'bad'), ('after', 'loaded_adapter_state_sha256', 'bad'),
            ('after', 'training_result_sha256', 'bad'), ('after', 'parent_present', True),
            ('after', 'fits', 1), ('after', 'status', 'FAILED')]
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            for index, (phase, field, value) in enumerate(mutations):
                with self.subTest(phase=phase, field=field):
                    path = root / 'lesson' / phase / 'RESULT.json'
                    original = runner.source.read(path)
                    write(path, dict(original, **{field: value}))
                    output = root / ('rejected-' + str(index))
                    with self.assertRaises(ValueError):
                        runner.main(arguments(root, 'prepare', output=output))
                    self.assertTrue((output / 'FAILED.json').exists())
                    write(path, original)
            for index, relative in enumerate(('train/adapter/adapter_model.safetensors', 'train/MASKS.json',
                    'source/organism_v6/experienced_event_two_hop.py', 'launch/source_commit.txt')):
                path = root / 'lesson' / relative
                original = path.read_bytes()
                path.write_text('drift')
                with self.assertRaises(ValueError):
                    runner.main(arguments(root, 'prepare', output=root / ('file-' + str(index))))
                path.write_bytes(original)
            state.factory.assert_not_called()
            state.tokenizer.assert_not_called()

    def test_collision_in_actual_old_facts_rejected(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            state.current['bank'][0]['receipt'] = runner.hop.build_world(runner.hop.TRANSFER_MASTER)['edges'][0]['receipt']
            with self.assertRaisesRegex(ValueError, 'fresh_namespace_collision'):
                runner.main(arguments(root, 'prepare'))
            state.factory.assert_not_called()

    def test_incomplete_collection_retained_without_substitution(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            factory = state.factory.side_effect

            def invalid(*args, **kwargs):
                engine = factory(*args, **kwargs)
                engine.generate = lambda messages, **unused: generation('INVALID', messages)
                return engine

            state.factory.side_effect = invalid
            with self.assertRaisesRegex(ValueError, 'incomplete_transfer_collection'):
                runner.main(arguments(root, 'collect'))
            document = runner.source.read(root / 'collect/COLLECTION.json')
            self.assertEqual(document['accepted_events'], 0)
            self.assertEqual(len(document['records']), 4)
            self.assertTrue((root / 'collect/FAILED.json').exists())
            self.assertFalse((root / 'collect/RESULT.json').exists())
            with self.assertRaisesRegex(ValueError, 'failed_transfer_collection'):
                runner.main(arguments(root, 'readout'))

    def test_collection_capture_and_binding_tampering_rejected(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            runner.main(arguments(root, 'collect'))
            state.factory.reset_mock()
            for index, (filename, field, value) in enumerate((('CALL_000.json', 'messages', []),
                    ('RESULT.json', 'binding', {}), ('RESULT.json', 'arm', 'ORIGINAL'),
                    ('RESULT.json', 'trainingAllowed', True))):
                path = root / 'collect' / filename
                original = runner.source.read(path)
                write(path, dict(original, **{field: value}))
                with self.assertRaises(ValueError):
                    runner.main(arguments(root, 'readout', output=root / ('bad-collection-' + str(index))))
                write(path, original)
            state.factory.assert_not_called()

    def test_readonly_state_file_and_base_drift_retained(self):
        for mutation in ('mounted', 'state', 'adapter', 'base'):
            with self.subTest(mutation=mutation), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = setup(root, stack)
                runner.main(arguments(root, 'collect'))
                factory = state.factory.side_effect

                def changed(*args, **kwargs):
                    engine = factory(*args, **kwargs)
                    if mutation == 'mounted':
                        engine.state = 'wrong'
                    elif mutation == 'state':
                        engine.mutate_state = True
                    else:
                        engine.mutate_file = root / ('base/model.safetensors' if mutation == 'base'
                            else 'lesson/train/adapter/adapter_model.safetensors')
                    return engine

                state.factory.side_effect = changed
                with self.assertRaises(ValueError):
                    runner.main(arguments(root, 'readout'))
                self.assertTrue((root / 'TRAINED/FAILED.json').exists())
                self.assertFalse((root / 'TRAINED/RESULT.json').exists())

    def test_guard_is_single_stage_bounded_and_scanned(self):
        path = Path(runner.__file__).with_name('astra_event_two_hop_transfer_guard.sh')
        result = subprocess.run(['bash', '-n', str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = path.read_text()
        for fragment in ('test "$#" -eq 7', 'CUDA_VISIBLE_DEVICES= python3', '"$index" "$uuid"',
                'service_exceptions.json', 'time.time()+1920 < 1789980180-21600',
                '--kill-after=60 1860', 'launch_collect', 'launch_$arm', 'OMP_NUM_THREADS=1',
                '"$root/collect/FAILED.json"', '"$root/prepare/FAILED.json"'):
            self.assertIn(fragment, text)
        self.assertEqual(text.count('-m gpu.astra_event_two_hop_transfer'), 1)
        self.assertNotIn('--phase train', text)

    def test_actor_errors_and_invalid_terminals_preserve_all_episodes(self):
        for native_error in (True, False):
            with self.subTest(native_error=native_error), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = setup(root, stack)
                runner.main(arguments(root, 'collect'))
                factory = state.factory.side_effect

                def changed(*args, **kwargs):
                    engine = factory(*args, **kwargs)

                    def invalid(messages, **unused):
                        if native_error:
                            raise RuntimeError('fixture native error')
                        return dict(generation('ROUTE invalid', messages), terminal=False)

                    engine.generate = invalid
                    return engine

                state.factory.side_effect = changed
                if native_error:
                    with self.assertRaisesRegex(ValueError, 'native_errors_retained'):
                        runner.main(arguments(root, 'readout'))
                else:
                    result = runner.main(arguments(root, 'readout'))
                    self.assertEqual(result['status'], 'COMPLETE')
                    self.assertTrue(all(panel['correct'] == 0 for panel in result['panels'].values()))
                self.assertEqual(len(list((root / 'TRAINED').glob('EPISODE_*.json'))), 8)
                self.assertEqual(len(list((root / 'TRAINED').glob('CALL_*.json'))), 8)
                self.assertTrue((root / 'TRAINED/STATES.json').exists())

    def test_hard_native_budget_fails_before_call_49(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            setup(root, stack)
            runner.main(arguments(root, 'collect'))

            def over_budget(world, collection, generate, output):
                for unused in range(49):
                    generate([dict(role='system', content='fixture'), dict(role='user', content='fixture')], role='actor')

            with patch.object(runner, 'evaluate', side_effect=over_budget), patch.object(
                    runner.source, 'Engine') as factory:
                engine = factory.return_value
                engine.state = runner.TRAINED_STATE
                engine.model.named_parameters.return_value = [('model.lora_A.weight', engine)]
                engine.runtime = {'fake': True}
                engine.generate.return_value = generation('INVALID')
                with self.assertRaisesRegex(ValueError, 'transfer_native_call_cap'):
                    runner.main(arguments(root, 'readout'))
                self.assertEqual(engine.generate.call_count, 48)
                failure = runner.source.read(root / 'TRAINED/FAILED.json')
                self.assertEqual(failure['model_calls'], 48)


if __name__ == '__main__':
    unittest.main()
