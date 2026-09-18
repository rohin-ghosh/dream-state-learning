"""CPU-only paired-fork authentication and driver dispatch tests."""

from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_corrective_sleep_train as trainer
from gpu import astra_experienced_event_adult_cycle as runner
from tests.test_astra_corrective_selection_driver import ACTOR_SHA, fixture, write


def selection_fixture(root, responses=None):
    before, collection, current = fixture(root)
    cases, provenance = runner.load_correction_before(before, collection, current,
        expected_adapter_state_sha256=ACTOR_SHA)
    directory = root / 'select_corrective'
    directory.mkdir()
    engine = MagicMock()
    raws = responses if responses is not None else [cases['sources'][0]['canonical']] * 2
    engine.generate.side_effect = [dict(raw=raw, terminal=True, truncated=False) for raw in raws]
    captured = runner.select_corrective(engine, cases, directory, provenance)
    arguments = dict(current['arguments'], phase='select_corrective', state='BEFORE', cycle=2,
                     development_arm='CUE_REPLAY', correction_before=str(before))
    result = dict(deepcopy(current), **captured, arguments=arguments, schema=runner.SCHEMA,
        phase='select_corrective', state='BEFORE', status='SELECTION_CAPTURED_NO_FIT',
        frozen_base_unchanged=True, loaded_adapter_state_sha256=ACTOR_SHA,
        runner_sha256='runner', material_sha256='material')
    write(directory / 'RESULT.json', result)
    write(directory / 'REQUEST.json', result)
    return directory, before, collection, current


def load_selection(values):
    directory, before, collection, current = values
    return runner.load_corrective_selection(directory, before, collection, current,
        expected_adapter_state_sha256=ACTOR_SHA)


def training_fixture(root, arm='CHILD_CORRECTIVE'):
    values = selection_fixture(root)
    selected, provenance = load_selection(values)
    current = dict(values[3], corrective_selection_source=provenance)
    directory = root / 'train'
    adapter = directory / 'adapter'
    adapter.mkdir(parents=True)
    (adapter / 'adapter_model.safetensors').write_bytes(b'fake-native-adapter')
    (adapter / 'adapter_config.json').write_text('{}')
    masks = [dict(labels=[-100] + [index + 1] * (index % 3 + 1)) for index in range(116)]
    write(directory / 'MASKS.json', masks)
    write(directory / 'SELECTION_LAYOUT.json', trainer.selection_layout(arm, selected))
    losses = []
    for update in range(1, 101):
        indexes, reference_indexes = trainer.training_indexes(update, arm, selected)
        actual = sum(len(masks[index]['labels']) - 1 for index in indexes)
        reference = sum(len(masks[index]['labels']) - 1 for index in reference_indexes)
        losses.append(dict(update=update, row_indexes=list(indexes), reference_row_indexes=list(reference_indexes),
            actual_label_count=actual, active_label_count=actual, reference_label_count=reference,
            original_label_count=reference, loss_scale=actual / reference))
    (directory / 'LOSSES.jsonl').write_text(''.join(runner.source.json.dumps(row) + '\n' for row in losses))
    budgets = dict(old_memory_presentations=100, old_cue_presentations=100, new_memory_presentations=200,
                   original_bank_presentations=64, first_adult_presentations=36)
    actual_total = sum(row['actual_label_count'] for row in losses)
    reference_total = sum(row['reference_label_count'] for row in losses)
    arguments = dict(current['arguments'], phase='train_corrective', replay_arm=arm)
    provenance = dict(adapter_state_before=ACTOR_SHA, adapter_state_after='new-state', runner_sha256='helper',
        adapter_files={path.name: runner.source.file_hash(path) for path in adapter.iterdir()},
        training_artifact_sha256={name: runner.source.file_hash(directory / name)
            for name in ('MASKS.json', 'SELECTION_LAYOUT.json', 'LOSSES.jsonl')})
    result = dict(deepcopy(current), **provenance, schema=runner.SCHEMA, phase='train_corrective', state='BEFORE',
        status='COMPLETE', arguments=arguments, updates=100, fits=1, train_seed=0, replay_arm=arm,
        selected_source_indexes=selected, frozen_base_unchanged=True, loaded_adapter_state_sha256=ACTOR_SHA,
        loss_normalization=trainer.LOSS_NORMALIZATION, optimizer='FRESH_ADAMW', learning_rate=3e-5,
        old_fact_count=8, budgets=budgets, **budgets, supervised_tokens=actual_total,
        actual_supervised_tokens=actual_total, original_supervised_tokens=reference_total,
        reference_supervised_tokens=reference_total)
    write(directory / 'RESULT.json', result)
    write(directory / 'REQUEST.json', dict(arguments=arguments))
    write(directory / 'ADAPTER_PROVENANCE.json', provenance)
    return adapter, current, selected


def check_training(values, arm='CHILD_CORRECTIVE'):
    adapter, current, selected = values
    return runner.check_corrective_training(adapter, current, replay_arm=arm,
        selected_source_indexes=selected, expected_adapter_state_sha256=ACTOR_SHA)


class SelectionTests(unittest.TestCase):
    def test_wrong_but_sourced_duplicate_choices_are_eligible(self):
        with TemporaryDirectory() as temporary:
            values = selection_fixture(Path(temporary))
            selected, provenance = load_selection(values)
            self.assertEqual(selected, [0, 0])
            self.assertEqual(len(provenance['source_files']), 7)
            self.assertEqual(provenance['before_source']['reader_wrapper'], 0)

    def test_invalid_choice_never_substituted(self):
        for raw in ('NONE', 'garbage'):
            with self.subTest(raw=raw), TemporaryDirectory() as temporary:
                values = selection_fixture(Path(temporary), [raw, raw])
                with self.assertRaisesRegex(ValueError, 'all_nonempty_cases'):
                    load_selection(values)

    def test_receipt_actor_source_before_and_calls_drift_fail_closed(self):
        faults = [('RESULT.json', 'loaded_adapter_state_sha256', 'other'),
                  ('RESULT.json', 'adult_source', {}), ('RESULT.json', 'selection_sha256', 'other'),
                  ('RESULT.json', 'initial_training_result_sha256', 'other'),
                  ('REQUEST.json', 'arguments', {}), ('CALL_000.json', 'response', {}),
                  ('CORRECTION_CASES.json', 'preparation_sha256', 'other'),
                  ('CORRECTION_SOURCE.json', 'result_sha256', 'other')]
        for name, key, value in faults:
            with self.subTest(name=name, key=key), TemporaryDirectory() as temporary:
                values = selection_fixture(Path(temporary))
                path = values[0] / name
                document = runner.source.read(path)
                document[key] = value
                write(path, document)
                with self.assertRaises(ValueError):
                    load_selection(values)

    def test_uniform_multiplicity_and_empty_selection_rejected(self):
        for selected in ([], [0, 1, 2, 3]):
            with self.subTest(selected=selected), TemporaryDirectory() as temporary:
                values = selection_fixture(Path(temporary))
                directory = values[0]
                result = runner.source.read(directory / 'RESULT.json')
                selection = runner.source.read(directory / 'SELECTION.json')
                cases = runner.source.read(directory / 'CORRECTION_CASES.json')
                count = len(selected)
                cases['expected_calls'] = count
                selection.update(model_calls=count, admitted_selections=count, chosen_source_indexes=selected,
                                 captures=[selection['captures'][0]] * count)
                for index, capture in enumerate(selection['captures']):
                    write(directory / ('CALL_%03d.json' % index), {key: capture[key] for key in
                        ('call_index', 'messages', 'response', 'error')})
                if not count:
                    for path in directory.glob('CALL_*.json'):
                        path.unlink()
                write(directory / 'SELECTION.json', selection)
                write(directory / 'CORRECTION_CASES.json', cases)
                result.update(model_calls=count, admitted_selections=count, actual_wrong_goal_cases=count,
                              selection_sha256=runner.source.file_hash(directory / 'SELECTION.json'))
                write(directory / 'RESULT.json', result)
                with patch.object(runner, 'load_correction_before', return_value=(cases, result['selection_source'])), \
                     patch('organism_v6.experienced_event_corrective_replay.collect_selection', return_value=selection):
                    with self.assertRaisesRegex(ValueError, 'all_nonempty_cases|no_sampling_contrast'):
                        load_selection(values)


class TrainingTests(unittest.TestCase):
    def test_both_arms_validate_actual_reference_counts_and_files(self):
        for arm in trainer.REPLAY_ARMS:
            with self.subTest(arm=arm), TemporaryDirectory() as temporary:
                values = training_fixture(Path(temporary), arm)
                self.assertEqual(check_training(values, arm), runner.source.file_hash(values[0].parent / 'RESULT.json'))

    def test_arm_count_actor_recipe_source_and_token_drift_rejected(self):
        faults = dict(replay_arm='UNIFORM_REPLAY', updates=400, phase='train', fits=0, train_seed=1,
            adapter_state_before='other', actual_supervised_tokens=0, reference_supervised_tokens=1,
            corrective_selection_source={}, selected_source_indexes=[1, 1], old_memory_presentations=400,
            loss_normalization='HF_MEAN', prior_adult_source={})
        for key, value in faults.items():
            with self.subTest(key=key), TemporaryDirectory() as temporary:
                values = training_fixture(Path(temporary))
                path = values[0].parent / 'RESULT.json'
                document = runner.source.read(path)
                document[key] = value
                write(path, document)
                with self.assertRaises(ValueError):
                    check_training(values)

    def test_adapter_artifact_and_logged_budget_drift_rejected(self):
        for name in ('adapter/adapter_model.safetensors', 'MASKS.json', 'LOSSES.jsonl', 'ADAPTER_PROVENANCE.json'):
            with self.subTest(name=name), TemporaryDirectory() as temporary:
                values = training_fixture(Path(temporary))
                (values[0].parent / name).write_text('{}')
                with self.assertRaises(ValueError):
                    check_training(values)

    def test_corrective_fit_never_qualifies_as_legacy_adult_fit(self):
        with TemporaryDirectory() as temporary:
            adapter, current, selected = training_fixture(Path(temporary))
            with self.assertRaisesRegex(ValueError, 'completed_same_adult_training_required'):
                runner.check_adult_training(adapter, cycle=2, arm='CUE_REPLAY',
                    expected_base_sha256=current['arguments']['expected_base_sha256'],
                    memory_source=current['memory_source'], cue_source=current['cue_source'],
                    adult_source=current['adult_source'])


class DispatchTests(unittest.TestCase):
    def test_native_dispatch_same_initial_adapter_and_cold_w0_without_legacy_fit(self):
        for phase in ('train_corrective', 'readout_corrective', 'bad_selection'):
            with self.subTest(phase=phase), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                initial = root / 'initial' / 'adapter'
                fitted = root / 'fitted' / 'adapter'
                before, collection, current = fixture(root)
                arguments = []
                bindings = dict(model_dir='unused', expected_base_sha256=current['arguments']['expected_base_sha256'],
                    initial_adapter_dir=str(initial), expected_initial_adapter_sha256='d' * 64,
                    collection='memory', cue_collection='cue', adult_collection='adult', output=str(root / 'output'),
                    gpu_uuid='fake', development_arm='CUE_REPLAY', cycle='2', prior_adult_collection='prior',
                    correction_before=str(before), corrective_selection='selection', replay_arm='CHILD_CORRECTIVE',
                    phase='train_corrective' if phase == 'bad_selection' else phase)
                if phase == 'readout_corrective':
                    bindings.update(state='AFTER', reader_wrapper='0', adapter_dir=str(fitted))
                for key, value in bindings.items():
                    arguments += ['--' + key.replace('_', '-'), value]
                stack.enter_context(patch.dict(runner.os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                                               CUDA_VISIBLE_DEVICES='fake'))
                real_hash = runner.source.file_hash
                stack.enter_context(patch.object(runner.source, 'file_hash', side_effect=lambda path:
                    'c' * 64 if Path(path) == initial.parent / 'RESULT.json' else
                    'd' * 64 if Path(path) == initial / 'adapter_model.safetensors' else real_hash(path)))
                real_read = runner.source.read

                def read(path):
                    if Path(path) == initial.parent / 'RESULT.json':
                        return dict(adapter_state_after=ACTOR_SHA, arguments=current['arguments'])
                    if Path(path) == fitted.parent / 'RESULT.json':
                        return dict(adapter_state_after='fitted-state')
                    if str(path) in ('memory/RESULT.json', 'cue/RESULT.json', 'adult/RESULT.json'):
                        return dict(arguments=current['arguments'])
                    return real_read(path)

                stack.enter_context(patch.object(runner.source, 'read', side_effect=read))
                stack.enter_context(patch.object(runner.source, 'load_collection', return_value=(
                    list(range(4)), list(range(4)), ['old'] * 32, current['memory_source'])))
                stack.enter_context(patch.object(runner.cue_material, 'load_cue_rows', return_value=(
                    ['cue'] * 20, current['cue_source'])))
                stack.enter_context(patch.object(runner, 'load_cycle2_initial', return_value=(
                    'c' * 64, dict(bank=list(range(4)), episodes=list(range(4))), ['prior'] * 32, current['prior_adult_source'])))
                stack.enter_context(patch.object(runner, 'read_adult_collection', return_value=(
                    collection, ['new'] * 32, current['adult_source'])))
                loader = stack.enter_context(patch.object(runner, 'load_corrective_selection', return_value=([0, 2], {})))
                if phase == 'bad_selection':
                    loader.side_effect = ValueError('selection_invalid')
                checker = stack.enter_context(patch.object(runner, 'check_corrective_training', return_value='trained-receipt'))
                tokenizer = stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer'))
                stack.enter_context(patch.object(runner.source.native, 'tokenizer_signature', return_value={}))
                engine = MagicMock()
                engine.runtime = {}
                engine.model.named_parameters.return_value = [('layer.lora_A.weight', object())]
                constructor = stack.enter_context(patch.object(runner.source, 'Engine', return_value=engine))
                stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash',
                    return_value='fitted-state' if phase == 'readout_corrective' else ACTOR_SHA))
                train = stack.enter_context(patch.object(trainer, 'train', return_value=dict(updates=100)))
                legacy = stack.enter_context(patch.object(runner, 'train'))
                evaluate = stack.enter_context(patch.object(runner, 'evaluate', return_value=dict(fits=0)))
                if phase == 'bad_selection':
                    with self.assertRaisesRegex(ValueError, 'selection_invalid'):
                        runner.main(arguments)
                    constructor.assert_not_called()
                    tokenizer.assert_not_called()
                else:
                    runner.main(arguments)
                    options = constructor.call_args.args[0]
                    self.assertEqual(options.phase, 'readout')
                    self.assertEqual(options.adapter_dir, str(fitted if phase == 'readout_corrective' else initial))
                    if phase == 'train_corrective':
                        train.assert_called_once_with(engine, ['old'] * 32 + ['prior'] * 32, ['cue'] * 20,
                            ['new'] * 32, root / 'output', replay_arm='CHILD_CORRECTIVE', selected_source_indexes=[0, 2])
                        evaluate.assert_not_called()
                        checker.assert_not_called()
                    else:
                        train.assert_not_called()
                        checker.assert_called_once()
                        evaluate.assert_called_once()
                        self.assertEqual(len(evaluate.call_args.args[2]), 8)
                        self.assertEqual(evaluate.call_args.kwargs, dict(reader_wrapper=0))
                legacy.assert_not_called()

    def test_explicit_arm_selection_cycle_and_w0_after_required_before_native(self):
        common = []
        for name in ('model-dir', 'expected-base-sha256', 'initial-adapter-dir', 'expected-initial-adapter-sha256',
                     'collection', 'cue-collection', 'output', 'gpu-uuid'):
            common += ['--' + name, 'unused']
        valid = common + ['--phase', 'train_corrective', '--development-arm', 'CUE_REPLAY', '--cycle', '2',
            '--prior-adult-collection', 'prior', '--adult-collection', 'adult', '--correction-before', 'before',
            '--corrective-selection', 'selection', '--replay-arm', 'CHILD_CORRECTIVE']
        for field, value in (('--cycle', '1'), ('--development-arm', 'CUE_LOSS_OFF'),
                             ('--phase', 'train'), ('--phase', 'readout_corrective'), ('--state', 'AFTER')):
            arguments = valid[:]
            if field in arguments:
                arguments[arguments.index(field) + 1] = value
            else:
                arguments += [field, value]
            with self.subTest(field=field, value=value), patch.object(runner.source, 'Engine') as engine:
                with self.assertRaises(ValueError):
                    runner.main(arguments)
                engine.assert_not_called()
        for field in ('--replay-arm', '--corrective-selection', '--correction-before'):
            arguments = valid[:]
            del arguments[arguments.index(field):arguments.index(field) + 2]
            with self.subTest(field=field), patch.object(runner.source, 'Engine') as engine:
                with self.assertRaises(ValueError):
                    runner.main(arguments)
                engine.assert_not_called()

    def test_guard_dispatch_is_after_environment_and_does_not_rerun_before(self):
        script = Path(runner.__file__).with_name('astra_adult_stage_guard.sh').read_text()
        self.assertLess(script.index('common=('), script.index('--phase train_corrective'))
        start = script.index('    correction=(')
        end = script.index('elif test "$stage" = select_corrective;', start)
        commands = script[start:end]
        self.assertEqual(commands.count('timeout --signal'), 2)
        self.assertIn('--phase readout_corrective --state AFTER --reader-wrapper 0', commands)
        self.assertNotIn('--state BEFORE', commands)
        self.assertIn('test ! -e "$corrective_root"', script)


if __name__ == '__main__':
    unittest.main()
