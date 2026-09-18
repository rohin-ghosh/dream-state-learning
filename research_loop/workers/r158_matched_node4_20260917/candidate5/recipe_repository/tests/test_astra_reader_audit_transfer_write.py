"""CPU contracts for one counterfactual material fit and reused A3 references."""

from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_reader_audit_transfer_write as runner
from tests.test_astra_reader_audit_matched_replay import fixture as stimulus_fixture
from tests.test_astra_fresh_reader_cycle import generation
from tests.test_astra_selected_reader_repair import write


ENVIRONMENT = dict(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='fake-gpu')


def writer_fixture(directory, inputs, selected, material_arm='SELECTED', schema=None):
    rows = inputs['rows']
    config = runner.expected_recipe(material_arm, selected, rows)
    for name, value in (('TRAINING_ROWS.json', rows), ('RECIPE.json', config),
                        ('MASKS.json', ['same-210-encoded-rows']), ('LOSSES.jsonl', {'reference_tokens': 3210})):
        write(directory / name, value)
    for name in ('adapter_model.safetensors', 'adapter_config.json'):
        path = directory / 'adapter' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(material_arm + str(selected) + name)
    result = dict(schema=schema or runner.fresh.SCHEMA, phase='train', status='COMPLETE', arm=runner.ARM,
        material_arm=material_arm, source=inputs.get('transfer_source', {}), updates=100, fits=1,
        adapter_state_before=runner.INITIAL_STATE, adapter_state_after='trained-' + str(selected),
        selected_source_indexes=selected, budgets=runner.BUDGETS, recipe=config, frozen_base_unchanged=True,
        reference_supervised_tokens=3210, trainer_sha256=runner.source.file_hash(runner.trainer.__file__),
        code_provenance={name: dict(sha256=digest, path='fixture', role=name) for name, digest in runner.kernel_hashes().items()},
        adapter_files={name: runner.source.file_hash(directory / 'adapter' / name)
                       for name in ('adapter_model.safetensors', 'adapter_config.json')},
        training_artifact_sha256={name: runner.source.file_hash(directory / name)
                                 for name in ('MASKS.json', 'RECIPE.json', 'LOSSES.jsonl')})
    write(directory / 'ADAPTER_PROVENANCE.json', dict(result, schema=runner.trainer.SCHEMA))
    write(directory / 'RESULT.json', result)
    return result


def replay_fixture(directory, expected, arm):
    responses = []
    for packet in expected['packets']:
        choices = (runner.SFT_CHOICES if arm == 'AUDIT_SFT' else runner.OFF_CHOICES) if packet['packet'] == 'before' else [None] * 6
        responses.extend(generation('E_UNSOURCED' if index is None else packet['cases']['sources'][index]['event']) for index in choices)
    remaining = iter(responses)
    engine = SimpleNamespace(generate=lambda messages, **kwargs: next(remaining))
    directory.mkdir(parents=True)
    summaries = runner.replay.dispatch(engine, expected['packets'], directory, [], lambda label: None)
    auditor = expected['auditor']
    result = dict(schema=runner.replay.SCHEMA, status='COMPLETE', arm=arm, fits=0, model_calls=14,
        evaluated_auditor=auditor, stimuli=expected['stimuli'], packets=summaries,
        adapter_state_before=auditor['adapter_state_sha256'], adapter_state_after=auditor['adapter_state_sha256'],
        adapter_files_after=auditor['adapter_files'], adapter_unchanged=True, adapter_files_unchanged=True,
        frozen_base_unchanged=True, code_provenance={name: runner.source.file_hash(module.__file__) for name, module in
            (('entry', runner.replay), ('lesson_driver', runner.replay.lesson), ('fresh_driver', runner.fresh),
             ('audit_evaluator', runner.replay.audit), ('native_engine', runner.source))})
    write(directory / 'RESULT.json', result)
    write(directory / 'INPUTS.json', dict(evaluated_auditor=auditor, stimuli=expected['stimuli']))
    write(directory / 'CASES.json', dict(packets=expected['packets']))


def fixture(root, stack):
    campaign, cycle = stimulus_fixture(root, stack)
    packets, stimuli = runner.replay.load_stimuli(cycle)
    collection = packets[0]['cases']['collection']
    packets[0]['source_actor_state_sha256'] = runner.INITIAL_STATE
    inputs = dict(initial_state=runner.INITIAL_STATE, fresh_source=stimuli['source'],
        adapter_dir='same-A3-initial/adapter', after=dict(arguments=dict(model_dir='no-model', expected_base_sha256='base')),
        memory_rows=[dict(memory=index) for index in range(96)], cue_rows=[dict(cue=index) for index in range(20)],
        lesson_rows=[dict(student_lesson=index) for index in range(62)], old_bank=[dict(fact=index) for index in range(12)],
        old_episodes=[dict(episode=index) for index in range(12)], held={'held': True})
    new_rows = runner.fresh.fresh.replay_collection(collection)
    inputs['rows'] = dict(memory_rows=inputs['memory_rows'], cue_rows=inputs['cue_rows'],
                          lesson_rows=inputs['lesson_rows'], new_rows=new_rows)
    choices = iter(runner.SFT_CHOICES)
    document = runner.fresh.audit.collect_audit(packets[0]['cases'],
        lambda messages: generation(packets[0]['cases']['sources'][next(choices)]['event']))
    write(cycle / 'before/ACTUAL_READERS.json', document)
    for material_arm in ('SELECTED', 'UNIFORM'):
        writer_fixture(cycle / material_arm / 'train', inputs, runner.SFT_CHOICES, material_arm)
    expected = {}
    for arm in runner.replay.lesson.ARMS:
        expected[arm] = dict(auditor=dict(arm=arm, adapter_state_sha256='original-' + arm,
            adapter_files={'adapter_model.safetensors': 'original-' + arm}), packets=deepcopy(packets), stimuli=deepcopy(stimuli))
        replay_fixture(root / 'replays' / arm, expected[arm], arm)
    stack.enter_context(patch.object(runner.fresh, 'load_parent', side_effect=lambda options: deepcopy(inputs)))
    stack.enter_context(patch.object(runner.fresh, 'read_collection', return_value=(collection, new_rows, 'collection-sha')))
    stack.enter_context(patch.object(runner.fresh, 'read_before', return_value=(runner.SFT_CHOICES, 'before-sha')))
    stack.enter_context(patch.object(runner.fresh, 'read_training', side_effect=lambda directory, *args:
        (runner.source.read(Path(directory) / 'RESULT.json'), runner.source.file_hash(Path(directory) / 'RESULT.json'))))
    stack.enter_context(patch.object(runner.replay, 'load_inputs', side_effect=lambda after, campaign, cycle, arm: deepcopy(expected[arm])))
    options = SimpleNamespace(base_after='base-after', campaign=str(campaign), cycle_root=str(cycle),
        audit_root='audit-root', repair_root='repair-root', replay_root=str(root / 'replays'))
    return options, inputs, expected


def arguments(root, options, phase, training=None):
    result = ['--phase', phase, '--gpu-uuid', 'fake-gpu', '--output', str(root / phase)]
    for name, value in vars(options).items():
        result += ['--' + name.replace('_', '-'), str(value)]
    if training:
        result += ['--training', str(training)]
    return result


class TransferWriteTests(unittest.TestCase):
    def test_native_tuple_cues_match_saved_json_but_changed_content_rejects(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            rows = dict(memory_rows=[], cue_rows=({'cue': 'unchanged'},), lesson_rows=[],
                        new_rows=[{'event': 'E_%d' % index} for index in range(4)])
            result = writer_fixture(directory, {'rows': rows}, [1, 1])
            runner.check_writer(directory, result, rows, [1, 1], 'SELECTED', runner.INITIAL_STATE)
            altered = deepcopy(rows)
            altered['cue_rows'][0]['cue'] = 'changed'
            with self.assertRaisesRegex(ValueError, 'shared_writer_rows_or_recipe_drift'):
                runner.check_writer(directory, result, altered, [1, 1], 'SELECTED', runner.INITIAL_STATE)

    def test_import_is_cpu_only(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_reader_audit_transfer_write
astra_reader_audit_transfer_write.kernel_hashes()
"""
        completed = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_prepare_binds_raw_choices_shared_writer_and_references_without_fit(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            options, unused_inputs, unused_expected = fixture(root, stack)
            stack.enter_context(patch.dict('os.environ', ENVIRONMENT))
            native = stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', side_effect=AssertionError))
            train = stack.enter_context(patch.object(runner.trainer, 'train', side_effect=AssertionError))
            result = runner.main(arguments(root, options, 'prepare'))
            binding = result['source']
            self.assertEqual(binding['selected_source_indexes'], [1, 1])
            self.assertEqual(binding['raw_source_choices']['AUDIT_LOSS_OFF'], runner.OFF_CHOICES)
            self.assertEqual(binding['raw_source_choices']['AUDIT_SFT'], runner.SFT_CHOICES)
            self.assertEqual(set(binding['reused_references']), {'SELECTED', 'UNIFORM'})
            self.assertFalse(binding['selector_is_writer_on_policy'])
            self.assertEqual((result['status'], result['fits']), ('PREPARED_NO_MODEL', 0))
            self.assertEqual(runner.trainer.recipe('SELECTED', [1, 1], memory_count=96)['encoded_row_count'], 210)
            native.assert_not_called()
            train.assert_not_called()
            with self.assertRaises(FileExistsError):
                runner.main(arguments(root, options, 'prepare'))

    def test_source_call_auditor_and_roster_drift_rejected(self):
        for mutation in ('missing', 'raw', 'auditor', 'roster'):
            with self.subTest(mutation=mutation), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                options, unused_inputs, expected = fixture(root, stack)
                directory = root / 'replays/AUDIT_LOSS_OFF'
                if mutation == 'missing':
                    (directory / 'RESULT.json').unlink()
                elif mutation == 'raw':
                    document = runner.source.read(directory / 'CALL_000.json')
                    document['response'] = generation('NONE')
                    write(directory / 'CALL_000.json', document)
                elif mutation == 'auditor':
                    document = runner.source.read(directory / 'RESULT.json')
                    document['adapter_state_after'] = 'descendant'
                    write(directory / 'RESULT.json', document)
                else:
                    expected['AUDIT_SFT']['packets'][0]['cases']['cases'][0]['messages'][1]['content'] += ' drift'
                with self.assertRaises((ValueError, FileNotFoundError)):
                    runner.load_inputs(options)

    def test_reference_kernel_recipe_rows_or_initial_drift_rejected(self):
        for mutation in ('kernel', 'recipe', 'rows', 'initial'):
            with self.subTest(mutation=mutation), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                options, inputs, unused_expected = fixture(root, stack)
                directory = Path(options.cycle_root) / 'UNIFORM/train'
                document = runner.source.read(directory / 'RESULT.json')
                if mutation == 'kernel':
                    document['code_provenance']['trainer']['sha256'] = 'new-kernel'
                elif mutation == 'recipe':
                    document['recipe']['learning_rate'] = 9e-5
                elif mutation == 'rows':
                    rows = deepcopy(inputs['rows'])
                    rows['lesson_rows'][0]['label_from_transfer'] = 'forbidden'
                    write(directory / 'TRAINING_ROWS.json', rows)
                else:
                    document['adapter_state_before'] = 'original-OFF-auditor-not-writer'
                write(directory / 'RESULT.json', document)
                with self.assertRaisesRegex(ValueError, 'shared_writer'):
                    runner.load_inputs(options)

    def test_one_fake_fit_then_full_after_no_reference_refits(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            options, unused_inputs, expected = fixture(root, stack)
            loaded = runner.load_inputs(options)
            stack.enter_context(patch.dict('os.environ', ENVIRONMENT))
            stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', return_value='fake-tokenizer'))
            engine = MagicMock(runtime={'fake': True})
            engine.model.named_parameters.return_value = [('model.lora_A.weight', object())]
            engine.generate.return_value = generation('E_UNSOURCED')
            factory = stack.enter_context(patch.object(runner.source, 'Engine', return_value=engine))
            state_hash = stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', return_value=runner.INITIAL_STATE))

            def train(engine, **kwargs):
                self.assertEqual(kwargs['memory_count'], 96)
                self.assertEqual(kwargs['material_arm'], 'SELECTED')
                self.assertEqual(kwargs['selected_source_indexes'], [1, 1])
                self.assertEqual({key: kwargs[key] for key in loaded['rows']}, loaded['rows'])
                result = writer_fixture(kwargs['output'], loaded, [1, 1], schema=runner.SCHEMA)
                (kwargs['output'] / 'RESULT.json').unlink()
                return result

            train_mock = stack.enter_context(patch.object(runner.trainer, 'train', side_effect=train))
            trained = runner.main(arguments(root, options, 'train'))
            self.assertEqual(factory.call_args.args[0].adapter_dir, loaded['adapter_dir'])
            self.assertEqual((trained['fits'], trained['updates'], trained['arm']), (1, 100, runner.ARM))
            state_hash.return_value = trained['adapter_state_after']

            def held(cases, generate, **kwargs):
                return [generate([dict(role='user', content='held')]) for index in range(16)]

            def evaluate(engine, collection, inputs, output):
                self.assertEqual(len(inputs['old_bank']), 12)
                return dict(model_calls=96, panels=dict(OWN_PARAMETRIC=dict(
                    episodes=expected['AUDIT_SFT']['packets'][0]['cases']['route_records'])))

            stack.enter_context(patch.object(runner.fresh.repair.prior.lesson, 'collect_cases', side_effect=held))
            evaluation = stack.enter_context(patch.object(runner.fresh, 'evaluate', side_effect=evaluate))
            after = runner.main(arguments(root, options, 'after', root / 'train'))
            train_mock.assert_called_once()
            evaluation.assert_called_once()
            self.assertEqual(factory.call_args.args[0].adapter_dir, str(root / 'train/adapter'))
            self.assertEqual(factory.call_args.args[0].phase, 'readout')
            self.assertEqual(factory.call_args.args[0].gpu_uuid, 'fake-gpu')
            self.assertEqual((after['fits'], after['model_calls']), (0, 120))
            self.assertEqual(after['adapter_state_after'], trained['adapter_state_after'])
            self.assertTrue((root / 'after/ACTUAL_READERS.json').exists())
            self.assertEqual(len(list((root / 'after').glob('CALL_*.json'))), 24)
            engine.check.assert_called_with('transfer_write_final')
            all_indexes = [runner.trainer.training_indexes(update, 'SELECTED', [1, 1], memory_count=96)
                           for update in range(1, 101)]
            self.assertEqual([actual[0] for actual, reference in all_indexes], list(range(96)) + list(range(4)))
            self.assertTrue(all((index - 178) % 4 == 1 for actual, reference in all_indexes for index in actual[2:]))
            self.assertEqual(sum(actual[1] < 116 for actual, reference in all_indexes), 38)
            self.assertEqual(runner.trainer.selected_new_indexes('SELECTED', [1, 1], memory_count=96),
                             tuple(range(179, 210, 4)) * 2)


if __name__ == '__main__':
    unittest.main()
