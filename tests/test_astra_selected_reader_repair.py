"""CPU-only driver contracts, receipt validation, and isolated fake dispatch."""

from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_selected_reader_repair as runner
from gpu import astra_selected_reader_repair_train as trainer
from organism_v6 import experienced_event_read_route as controller
from tests.test_experienced_event_actual_reader_audit import actual_fixture


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(runner.source.native._json_bytes(value))


def inputs_fixture(parent_arm='AUDIT_SFT'):
    return dict(repair_source=dict(parent_arm=parent_arm, initial_training_result_sha256='prior-fit',
                    selected_source_indexes=[1, 3, 3] if parent_arm == 'AUDIT_SFT' else [1]),
        initial_state='actor-' + parent_arm, adapter_dir='campaign/' + parent_arm + '/train/adapter',
        after=dict(arguments=dict(model_dir='unused-model', expected_base_sha256='base-digest')),
        memory_rows=[dict(memory=index) for index in range(80)],
        cue_rows=[dict(cue=index) for index in range(20)], lesson_rows=[dict(lesson=index) for index in range(62)],
        new_rows=[dict(new=index) for index in range(32)], selected=[1, 3, 3] if parent_arm == 'AUDIT_SFT' else [1],
        collection={'collection': 'own'}, old_bank=['own-old-bank'], old_episodes=['own-old-episodes'], held={'held': 'own'})


def arguments(output, phase='prepare', parent_arm='AUDIT_SFT', material_arm='SELECTED', training=None):
    result = ['--phase', phase, '--base-after', 'base-after', '--campaign', 'campaign',
              '--audit-root', 'audits', '--output', str(output), '--gpu-uuid', 'fake-gpu',
              '--parent-arm', parent_arm, '--material-arm', material_arm]
    if training is not None:
        result += ['--training', str(training)]
    return result


def training_fixture(directory, parent_arm='AUDIT_SFT', material_arm='SELECTED'):
    inputs = inputs_fixture(parent_arm)
    for name in ('adapter_model.safetensors', 'adapter_config.json'):
        path = directory / 'adapter' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(('fake-' + name).encode())
    for name in ('MASKS.json', 'RECIPE.json', 'LOSSES.jsonl', 'ADAPTER_PROVENANCE.json'):
        write(directory / name, dict(fixture=name))
    result = dict(schema=runner.SCHEMA, phase='train', status='COMPLETE', updates=100,
        parent_arm=parent_arm, material_arm=material_arm, source=deepcopy(inputs['repair_source']),
        adapter_state_before=inputs['initial_state'], adapter_state_after='repaired-' + parent_arm + '-' + material_arm,
        frozen_base_unchanged=True, fits=1,
        adapter_files={name: runner.source.file_hash(directory / 'adapter' / name)
                       for name in ('adapter_model.safetensors', 'adapter_config.json')},
        training_artifact_sha256={name: runner.source.file_hash(directory / name)
                                 for name in ('MASKS.json', 'RECIPE.json', 'LOSSES.jsonl', 'ADAPTER_PROVENANCE.json')})
    write(directory / 'RESULT.json', result)
    return inputs, result


def audit_fixture(root, stack, parent_arm='AUDIT_SFT', selected=(1, 3, 3)):
    collection, records = actual_fixture()
    cases = runner.actual.build_cases(collection, records)
    choices = iter(list(selected) + [None] * (len(cases['cases']) - len(selected)))

    def generate(messages):
        choice = next(choices)
        raw = 'NONE' if choice is None else cases['sources'][choice]['event']
        return dict(raw=raw, terminal=True, truncated=False)

    record = runner.actual.collect_cases(cases, generate)
    inputs = dict(provenance={'own': 'base-source'}, collection=collection)
    lessons = [dict(lesson=index) for index in range(62)]
    trained = dict(adapter_state_after='actor-' + parent_arm, adapter_files={'adapter_model.safetensors': 'parent-file'})
    actual_source = dict(parent_arm=parent_arm, route_receipt='own-after')
    directory = root / 'audits' / parent_arm
    result = dict(schema=runner.prior.SCHEMA, phase='actual', status='COMPLETE', arm=parent_arm,
        source=inputs['provenance'], fits=0, actual_source=actual_source, training_result_sha256='prior-fit',
        loaded_adapter_state_sha256=trained['adapter_state_after'], frozen_base_unchanged=True)
    for name, value in (('RESULT.json', result), ('ACTUAL_CASES.json', cases), ('ACTUAL_READERS.json', record)):
        write(directory / name, value)
    load = stack.enter_context(patch.object(runner.prior, 'load_inputs', return_value=deepcopy(inputs)))
    lesson_replay = stack.enter_context(patch.object(runner.prior, 'replay_lesson', return_value=(lessons, 'lesson-receipt')))
    training_check = stack.enter_context(patch.object(runner.prior, 'checked_training', return_value=(trained, 'prior-fit')))
    actual_cases = stack.enter_context(patch.object(runner.prior, 'actual_cases', return_value=(cases, actual_source)))
    return SimpleNamespace(directory=directory, result=result, record=record, cases=cases, lessons=lessons,
        load=load, lesson_replay=lesson_replay, training_check=training_check, actual_cases=actual_cases)


class InputTests(unittest.TestCase):
    def test_both_actual_actors_replay_sources_and_keep_duplicate_pointers(self):
        for parent_arm, selected in (('AUDIT_SFT', (1, 3, 3)), ('AUDIT_LOSS_OFF', (1,))):
            with self.subTest(parent_arm=parent_arm), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                fixture = audit_fixture(root, stack, parent_arm, selected)
                loaded = runner.load_inputs('base-after', root / 'campaign', root / 'audits', parent_arm)
                self.assertEqual(loaded['selected'], list(selected))
                self.assertEqual(loaded['initial_state'], 'actor-' + parent_arm)
                self.assertEqual(len(loaded['lesson_rows']), 62)
                self.assertEqual(len(loaded['new_rows']), 32)
                self.assertEqual(loaded['adapter_dir'], str(root / 'campaign' / parent_arm / 'train/adapter'))
                fixture.training_check.assert_called_once_with(root / 'campaign' / parent_arm / 'train',
                    fixture.load.return_value, parent_arm, 'lesson-receipt')
                fixture.actual_cases.assert_called_once_with(root / 'campaign' / parent_arm / 'after',
                    fixture.load.return_value, parent_arm, 'prior-fit', 'actor-' + parent_arm)
                for name, digest in loaded['repair_source']['audit_files'].items():
                    self.assertEqual(digest, runner.source.file_hash(fixture.directory / name))
                self.assertEqual(loaded['repair_source']['selected_source_indexes'], list(selected))

    def test_actual_receipt_actor_source_and_cell_mismatches_are_rejected(self):
        faults = dict(schema='other', phase='after', status='FAILED', arm='AUDIT_LOSS_OFF', source={}, fits=1,
            actual_source={}, training_result_sha256='other', loaded_adapter_state_sha256='other', frozen_base_unchanged=False)
        for field, value in faults.items():
            with self.subTest(field=field), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                fixture = audit_fixture(root, stack)
                fixture.result[field] = value
                write(fixture.directory / 'RESULT.json', fixture.result)
                with self.assertRaisesRegex(ValueError, 'own_terminal_actual_audit'):
                    runner.load_inputs('base-after', root / 'campaign', root / 'audits', 'AUDIT_SFT')

    def test_audit_files_capture_replay_failed_marker_and_lesson_count(self):
        for fault in ('failed', 'cases', 'capture', 'selection', 'extra_capture', 'lessons'):
            with self.subTest(fault=fault), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                fixture = audit_fixture(root, stack)
                if fault == 'failed':
                    write(fixture.directory / 'FAILED.json', {})
                elif fault == 'cases':
                    write(fixture.directory / 'ACTUAL_CASES.json', {})
                elif fault == 'lessons':
                    fixture.lessons.pop()
                else:
                    record = deepcopy(fixture.record)
                    if fault == 'capture':
                        record['captures'][0]['messages'][0]['content'] += 'drift'
                    elif fault == 'selection':
                        record['chosen_source_indexes'][0] = 0
                    else:
                        record['captures'].append(deepcopy(record['captures'][0]))
                    write(fixture.directory / 'ACTUAL_READERS.json', record)
                with self.assertRaises(ValueError):
                    runner.load_inputs('base-after', root / 'campaign', root / 'audits', 'AUDIT_SFT')

    def test_empty_selections_never_fabricate_material(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            audit_fixture(root, stack, selected=())
            with self.assertRaisesRegex(ValueError, 'nonempty_actual_source_choices'):
                runner.load_inputs('base-after', root / 'campaign', root / 'audits', 'AUDIT_SFT')


class TrainingReceiptTests(unittest.TestCase):
    def test_each_cell_accepts_only_its_own_fit_and_actor(self):
        for parent_arm in runner.prior.ARMS:
            for material_arm in ('SELECTED', 'UNIFORM'):
                with self.subTest(parent_arm=parent_arm, material_arm=material_arm), TemporaryDirectory() as temporary:
                    directory = Path(temporary)
                    inputs, receipt = training_fixture(directory, parent_arm, material_arm)
                    result, digest = runner.checked_training(directory, inputs, parent_arm, material_arm)
                    self.assertEqual(result, receipt)
                    self.assertEqual(digest, runner.source.file_hash(directory / 'RESULT.json'))
                    for wrong_parent in runner.prior.ARMS:
                        for wrong_material in ('SELECTED', 'UNIFORM'):
                            if (wrong_parent, wrong_material) == (parent_arm, material_arm):
                                continue
                            with self.assertRaisesRegex(ValueError, 'matched_repair_fit'):
                                runner.checked_training(directory, inputs, wrong_parent, wrong_material)
                    for field, value in (('initial_state', 'foreign-actor'), ('repair_source', {'foreign': 'source'})):
                        changed = dict(inputs, **{field: value})
                        with self.assertRaisesRegex(ValueError, 'matched_repair_fit'):
                            runner.checked_training(directory, changed, parent_arm, material_arm)

    def test_training_receipt_and_file_drift_fail_closed(self):
        faults = dict(schema=trainer.SCHEMA, phase='after', status='FAILED', updates=200,
                      source={}, adapter_state_before='foreign', frozen_base_unchanged=False)
        for field, value in faults.items():
            with self.subTest(field=field), TemporaryDirectory() as temporary:
                directory = Path(temporary)
                inputs, receipt = training_fixture(directory)
                receipt[field] = value
                write(directory / 'RESULT.json', receipt)
                with self.assertRaisesRegex(ValueError, 'matched_repair_fit'):
                    runner.checked_training(directory, inputs, 'AUDIT_SFT', 'SELECTED')
        for filename in ('adapter/adapter_model.safetensors', 'adapter/adapter_config.json', 'MASKS.json',
                         'RECIPE.json', 'LOSSES.jsonl', 'ADAPTER_PROVENANCE.json', 'FAILED.json'):
            with self.subTest(filename=filename), TemporaryDirectory() as temporary:
                directory = Path(temporary)
                inputs, receipt = training_fixture(directory)
                (directory / filename).write_text('changed')
                with self.assertRaisesRegex(ValueError, 'drift|failed_repair'):
                    runner.checked_training(directory, inputs, 'AUDIT_SFT', 'SELECTED')

    def test_adapter_inventory_and_unsafe_paths_are_rejected(self):
        for fault in ('missing_weights', 'missing_config', 'adapter_path', 'artifact_path'):
            with self.subTest(fault=fault), TemporaryDirectory() as temporary:
                directory = Path(temporary)
                inputs, receipt = training_fixture(directory)
                if fault.startswith('missing'):
                    receipt['adapter_files'].pop('adapter_model.safetensors' if fault == 'missing_weights' else 'adapter_config.json')
                else:
                    receipt['adapter_files' if fault == 'adapter_path' else 'training_artifact_sha256']['../foreign'] = 'digest'
                write(directory / 'RESULT.json', receipt)
                with self.assertRaisesRegex(ValueError, 'inventory|drift'):
                    runner.checked_training(directory, inputs, 'AUDIT_SFT', 'SELECTED')

    def test_missing_training_artifact_inventory_must_be_rejected(self):
        """Omitting the hash inventory cannot bypass required evidence checks."""
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            inputs, receipt = training_fixture(directory)
            receipt.pop('training_artifact_sha256')
            write(directory / 'RESULT.json', receipt)
            with self.assertRaises(ValueError):
                runner.checked_training(directory, inputs, 'AUDIT_SFT', 'SELECTED')

    def test_missing_final_adapter_state_must_be_rejected(self):
        """A fit must bind the final adapter state consumed by AFTER dispatch."""
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            inputs, receipt = training_fixture(directory)
            receipt.pop('adapter_state_after')
            write(directory / 'RESULT.json', receipt)
            with self.assertRaises(ValueError):
                runner.checked_training(directory, inputs, 'AUDIT_SFT', 'SELECTED')


class DispatchTests(unittest.TestCase):
    def test_unknown_address_is_policy_failure_before_reader_and_audit_rejects_uncommitted_route(self):
        collection, records = actual_fixture()
        fact = collection['bank'][0]
        unknown = runner.source.material.build_bank('repair-test-unknown-address')[0]['event']
        reader = MagicMock()
        transition = MagicMock()
        episode = controller.run_episode(controller.public_task(fact),
            lambda messages: dict(raw='READ EVENT ' + unknown, terminal=True, truncated=False), reader, transition)
        self.assertEqual(episode['terminal_reason'], 'unsupported_address')
        self.assertFalse(episode['reached_goal'])
        self.assertEqual(episode['memory_calls'], 0)
        reader.assert_not_called()
        transition.assert_not_called()
        records[0] = dict(event=fact['event'], episode=episode)
        with self.assertRaisesRegex(ValueError, 'actual_committed_outcome_required'):
            runner.actual.build_cases(collection, records)

    def test_import_and_prepare_in_fresh_process_without_native_imports(self):
        script = textwrap.dedent('''
            import builtins
            original_import = builtins.__import__
            def blocked(name, *args, **kwargs):
                if name.split('.')[0] in ('torch', 'transformers', 'peft'):
                    raise AssertionError('native import: ' + name)
                return original_import(name, *args, **kwargs)
            builtins.__import__ = blocked
            from pathlib import Path
            from tempfile import TemporaryDirectory
            from unittest.mock import patch
            from tests.test_astra_selected_reader_repair import runner, inputs_fixture, arguments
            with TemporaryDirectory() as temporary, \\
                 patch.dict('os.environ', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='not-the-requested-gpu'), \\
                 patch.object(runner, 'load_inputs', return_value=inputs_fixture()), \\
                 patch.object(runner.source.native, 'load_local_tokenizer', side_effect=AssertionError('tokenizer load')) as tokenizer, \\
                 patch.object(runner.source, 'Engine', side_effect=AssertionError('model load')) as engine:
                output = Path(temporary) / 'prepare'
                runner.main(arguments(output))
                result = runner.source.read(output / 'RESULT.json')
                assert result['status'] == 'PREPARED_NO_MODEL'
                assert result['fits'] == result['model_calls'] == 0
                assert result['source'] == inputs_fixture()['repair_source']
                assert sorted(path.name for path in output.iterdir()) == ['INPUTS.json', 'REQUEST.json', 'RESULT.json']
                tokenizer.assert_not_called()
                engine.assert_not_called()
        ''')
        process = subprocess.run([sys.executable, '-c', script], cwd=Path(__file__).resolve().parents[1],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)

    def test_all_four_train_cells_dispatch_own_actor_and_preserve_helper_provenance(self):
        for parent_arm in runner.prior.ARMS:
            for material_arm in ('SELECTED', 'UNIFORM'):
                with self.subTest(parent_arm=parent_arm, material_arm=material_arm), TemporaryDirectory() as temporary, ExitStack() as stack:
                    output = Path(temporary) / 'train'
                    inputs = inputs_fixture(parent_arm)
                    engine = MagicMock(runtime={'fake': True})
                    engine.model.named_parameters.return_value = [('layer.lora_A.weight', object())]
                    helper_result = dict(schema=trainer.SCHEMA, updates=100, adapter_state_before=inputs['initial_state'],
                        adapter_state_after='repaired', code_provenance={'lesson_encoder': {'role': 'parent-safe fixture'}})

                    def fit(*args, **kwargs):
                        runner.source.write(args[5] / 'RECIPE.json', {'fixture': 'exclusive artifact'})
                        return deepcopy(helper_result)

                    stack.enter_context(patch.dict('os.environ', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='fake-gpu'))
                    load = stack.enter_context(patch.object(runner, 'load_inputs', return_value=inputs))
                    stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', return_value='fake-tokenizer'))
                    make_engine = stack.enter_context(patch.object(runner.source, 'Engine', return_value=engine))
                    stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', return_value=inputs['initial_state']))
                    train = stack.enter_context(patch.object(trainer, 'train', side_effect=fit))
                    runner.main(arguments(output, 'train', parent_arm, material_arm))
                    train.assert_called_once_with(engine, inputs['memory_rows'], inputs['cue_rows'], inputs['lesson_rows'],
                        inputs['new_rows'], output, material_arm=material_arm, selected_source_indexes=inputs['selected'])
                    self.assertEqual(make_engine.call_args.args[0].adapter_dir, inputs['adapter_dir'])
                    result = runner.source.read(output / 'RESULT.json')
                    self.assertEqual((result['schema'], result['status'], result['fits']), (runner.SCHEMA, 'COMPLETE', 1))
                    self.assertEqual((result['parent_arm'], result['material_arm']), (parent_arm, material_arm))
                    self.assertEqual(result['code_provenance'], helper_result['code_provenance'])
                    self.assertEqual(result['source'], inputs['repair_source'])
                    self.assertEqual(result['loaded_adapter_state_sha256'], inputs['initial_state'])
                    engine.verify_base.assert_called_once_with()
                    engine.generate.assert_not_called()
                    before = (output / 'RESULT.json').read_bytes()
                    with self.assertRaises(FileExistsError):
                        runner.main(arguments(output, 'train', parent_arm, material_arm))
                    self.assertEqual((output / 'RESULT.json').read_bytes(), before)
                    self.assertEqual(load.call_count, 1)

    def test_after_uses_checked_adapter_w0_readouts_and_separate_audit_captures(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            output = Path(temporary) / 'after'
            training = Path(temporary) / 'own-cell-training'
            inputs = inputs_fixture()
            engine = MagicMock(runtime={'fake': True})
            engine.model.named_parameters.return_value = [('layer.lora_B.weight', object())]
            engine.generate.return_value = dict(raw='NONE', terminal=True, truncated=False)
            stack.enter_context(patch.dict('os.environ', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='fake-gpu'))
            stack.enter_context(patch.object(runner, 'load_inputs', return_value=inputs))
            checked = stack.enter_context(patch.object(runner, 'checked_training', return_value=({'adapter_state_after': 'own-repaired'}, 'fit-receipt')))
            stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', return_value='fake-tokenizer'))
            make_engine = stack.enter_context(patch.object(runner.source, 'Engine', return_value=engine))
            state = stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', return_value='own-repaired'))

            def collect(cases, generate, **kwargs):
                return dict(response=generate([dict(role='user', content='fake public audit')]))

            held = stack.enter_context(patch.object(runner.prior.lesson, 'collect_cases', side_effect=collect))
            evaluate = stack.enter_context(patch.object(runner.driver, 'evaluate', return_value=dict(
                panels={'OWN_PARAMETRIC': {'episodes': ['own-fresh-episode']}}, model_calls=5)))
            build = stack.enter_context(patch.object(runner.actual, 'build_cases', return_value={'fresh': 'cases'}))
            actual = stack.enter_context(patch.object(runner.actual, 'collect_cases', side_effect=collect))
            runner.main(arguments(output, 'after', training=training))
            checked.assert_called_once_with(str(training), inputs, 'AUDIT_SFT', 'SELECTED')
            self.assertEqual(make_engine.call_args.args[0].adapter_dir, str(training / 'adapter'))
            evaluate.assert_called_once_with(engine, inputs['collection'], inputs['old_bank'], inputs['old_episodes'], output, reader_wrapper=0)
            self.assertFalse(held.call_args.kwargs['coached'])
            build.assert_called_once_with(inputs['collection'], ['own-fresh-episode'])
            self.assertEqual(actual.call_args.args[0], {'fresh': 'cases'})
            result = runner.source.read(output / 'RESULT.json')
            self.assertEqual((result['status'], result['fits'], result['model_calls']), ('COMPLETE', 0, 7))
            self.assertEqual(result['training_result_sha256'], 'fit-receipt')
            self.assertEqual(state.call_count, 2)
            self.assertEqual(len(list(output.glob('CALL_*.json'))), 2)
            engine.verify_base.assert_called_once_with()

    def test_bad_actor_and_source_fail_before_fit_with_failure_receipt(self):
        for fault in ('actor', 'source'):
            with self.subTest(fault=fault), TemporaryDirectory() as temporary, ExitStack() as stack:
                output = Path(temporary) / 'train'
                inputs = inputs_fixture()
                engine = MagicMock(runtime={})
                engine.model.named_parameters.return_value = [('layer.lora_A.weight', object())]
                stack.enter_context(patch.dict('os.environ', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='fake-gpu'))
                stack.enter_context(patch.object(runner, 'load_inputs', return_value=inputs,
                    side_effect=ValueError('foreign_source') if fault == 'source' else None))
                tokenizer = stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer'))
                stack.enter_context(patch.object(runner.source, 'Engine', return_value=engine))
                stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', return_value='foreign-actor'))
                train = stack.enter_context(patch.object(trainer, 'train'))
                with self.assertRaisesRegex(ValueError, 'foreign_source|own_repair_actor'):
                    runner.main(arguments(output, 'train'))
                train.assert_not_called()
                if fault == 'source':
                    tokenizer.assert_not_called()
                self.assertEqual(runner.source.read(output / 'FAILED.json')['status'], 'FAILED')
                self.assertFalse((output / 'RESULT.json').exists())

    def test_training_argument_and_environment_gates_precede_loading(self):
        for phase, training in (('after', None), ('prepare', 'unexpected'), ('train', 'unexpected')):
            with self.subTest(phase=phase), patch.object(runner, 'load_inputs') as load:
                with self.assertRaisesRegex(ValueError, 'own_repair_training_required'):
                    runner.main(arguments('unused', phase, training=training))
                load.assert_not_called()
        for environment, message in (({}, 'offline_required'),
            ({'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'CUDA_VISIBLE_DEVICES': 'other'}, 'exact_gpu_required')):
            with patch.dict('os.environ', environment, clear=True), patch.object(runner, 'load_inputs') as load:
                with self.assertRaisesRegex(ValueError, message):
                    runner.main(arguments('unused', 'train'))
                load.assert_not_called()


if __name__ == '__main__':
    unittest.main()
