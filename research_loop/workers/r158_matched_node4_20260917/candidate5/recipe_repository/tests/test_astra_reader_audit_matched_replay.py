"""CPU-only matched-stimulus provenance and zero-fit dispatch contracts."""

from contextlib import ExitStack
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_reader_audit_matched_replay as runner
from organism_v6 import experienced_event_read_route as controller
from tests.test_astra_fresh_reader_cycle import fresh_fixture, generation, stage_fixture, fresh_training_fixture
from tests.test_astra_selected_reader_repair import write


ENVIRONMENT = dict(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='fake-gpu')


def fixture(root, stack):
    campaign, stimuli = root / 'campaign', root / 'stimuli'
    inputs = dict(provenance={'original': 'SEQ239'}, after=dict(loaded_adapter_state_sha256='before-lesson',
        arguments=dict(model_dir='no-model', expected_base_sha256='frozen-base')))
    stack.enter_context(patch.object(runner.lesson, 'load_inputs', return_value=inputs))
    stack.enter_context(patch.object(runner.lesson, 'replay_lesson', return_value=([], 'lesson-receipt')))
    for arm in runner.lesson.ARMS:
        directory = campaign / arm / 'train'
        for name in ('adapter_model.safetensors', 'adapter_config.json'):
            path = directory / 'adapter' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(arm + name)
        trained = dict(schema=runner.lesson.SCHEMA, phase='train', status='COMPLETE', arm=arm,
            updates=200, source=inputs['provenance'], lesson_result_sha256='lesson-receipt',
            frozen_base_unchanged=True, adapter_state_before='before-lesson', adapter_state_after='original-' + arm,
            adapter_files={name: runner.source.file_hash(directory / 'adapter' / name)
                           for name in ('adapter_model.safetensors', 'adapter_config.json')})
        write(directory / 'RESULT.json', trained)
    parent = dict(parent_arm='AUDIT_SFT', prior_source=inputs['provenance'], lesson_result_sha256='lesson-receipt',
        initial_training_result_sha256=runner.source.file_hash(campaign / 'AUDIT_SFT/train/RESULT.json'))
    fresh_inputs = dict(fresh_source=dict(initial_adapter_state_sha256='A3-before', parent_source=parent),
                        initial_state='A3-before')
    collection, unused_records = fresh_fixture()
    write(stimuli / 'collect/COLLECTION.json', collection)
    stage_fixture(stimuli / 'collect', fresh_inputs, 'collect',
        collection_sha256=runner.source.file_hash(stimuli / 'collect/COLLECTION.json'))
    collection_sha = runner.source.file_hash(stimuli / 'collect/RESULT.json')
    for relative, phase, unused_count, kind in runner.PACKETS:
        records = []
        bank = collection['bank']
        by_address = {fact['event']: runner.source.material._event(fact) for fact in bank}
        for index, fact in enumerate(bank):
            addresses = [fact['public_events'][index]] if phase == 'after' and index < 2 else fact['public_events']
            commands = iter(['READ EVENT ' + address for address in addresses] + ['ROUTE ' + fact['port']])
            transitions = {other['port']: other['outcome'] for other in bank if other['node'] == fact['node']}
            record = controller.run_episode(controller.public_task(fact),
                lambda messages: generation(next(commands), messages),
                lambda address: generation('MISS\n' if kind == 'fault' else by_address[address]),
                transitions.__getitem__)
            records.append(dict(event=fact['event'], episode=record))
        cases = runner.audit.build_cases(collection, records)
        document = runner.audit.collect_audit(cases, lambda messages: generation(cases['sources'][1]['event']))
        directory = stimuli / relative
        panel = dict(episodes=records, denominator=4)
        for name, value in (('ACTUAL_CASES.json', cases), ('ACTUAL_READERS.json', document),
                            ('new_task/PANELS.json', dict(OWN_PARAMETRIC=panel))):
            write(directory / name, value)
        for index, record in enumerate(records, 1):
            write(directory / ('new_task/OWN_PARAMETRIC_EPISODE_%02d.json' % index), record)
        for index, capture in enumerate(document['captures'], 16):
            write(directory / ('CALL_%03d.json' % index),
                  {key: capture[key] for key in ('messages', 'response', 'error')})
        extra = {}
        if phase == 'after':
            training_dir = stimuli / 'SELECTED/train'
            trained = fresh_training_fixture(training_dir, fresh_inputs)
            trained.update(collection_result_sha256=collection_sha,
                           before_result_sha256=runner.source.file_hash(stimuli / 'before/RESULT.json'))
            write(training_dir / 'RESULT.json', trained)
            extra.update(arm='SELECTED', training_result_sha256=runner.source.file_hash(training_dir / 'RESULT.json'),
                before_result_sha256=trained['before_result_sha256'], loaded_adapter_state_sha256=trained['adapter_state_after'])
        stage_fixture(directory, fresh_inputs, phase, collection_result_sha256=collection_sha,
                      panels=dict(OWN_PARAMETRIC=panel), **extra)
    return campaign, stimuli


def arguments(root, arm='AUDIT_SFT', prepare=True):
    result = ['--after-source', 'original-after', '--campaign', str(root / 'campaign'),
              '--stimulus-root', str(root / 'stimuli'), '--arm', arm, '--gpu-uuid', 'fake-gpu',
              '--output', str(root / ('prepare_' + arm if prepare else 'run_' + arm))]
    return result + ['--prepare-only'] if prepare else result


class MatchedReplayTests(unittest.TestCase):
    def test_import_never_imports_native_dependencies(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError('native import:' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_reader_audit_matched_replay
"""
        completed = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_prepare_both_original_arms_same_stimuli_and_distinct_auditors(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            fixture(root, stack)
            stack.enter_context(patch.dict('os.environ', ENVIRONMENT))
            native = stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', side_effect=AssertionError))
            engine = stack.enter_context(patch.object(runner.source, 'Engine', side_effect=AssertionError))
            results = [runner.main(arguments(root, arm)) for arm in runner.lesson.ARMS]
            self.assertEqual(results[0]['stimuli'], results[1]['stimuli'])
            for result in results:
                self.assertEqual((result['status'], result['fits'], result['model_calls']), ('PREPARED_NO_MODEL', 0, 0))
                self.assertEqual(result['evaluated_auditor']['adapter_state_sha256'], 'original-' + result['arm'])
                self.assertEqual(result['evaluated_auditor']['adapter_dir'], str(root / 'campaign' / result['arm'] / 'train/adapter'))
                self.assertEqual(result['stimuli']['unique_addresses'], 4)
            native.assert_not_called()
            engine.assert_not_called()
            with self.assertRaises(FileExistsError):
                runner.main(arguments(root))

    def test_missing_source_wrong_arm_adapter_and_campaign_join(self):
        for mutation in ('missing', 'arm', 'adapter', 'join'):
            with self.subTest(mutation=mutation), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                campaign, stimuli = fixture(root, stack)
                if mutation == 'missing':
                    (stimuli / 'before/ACTUAL_CASES.json').unlink()
                elif mutation == 'adapter':
                    (campaign / 'AUDIT_SFT/train/adapter/adapter_model.safetensors').write_text('descendant')
                else:
                    path = campaign / 'AUDIT_SFT/train/RESULT.json'
                    document = runner.source.read(path)
                    document['arm' if mutation == 'arm' else 'adapter_state_after'] = 'wrong'
                    write(path, document)
                with self.assertRaises((ValueError, FileNotFoundError)):
                    runner.load_inputs('after', campaign, stimuli, 'AUDIT_SFT')

    def test_prompt_case_and_capture_drift_rejected(self):
        for filename in ('ACTUAL_CASES.json', 'ACTUAL_READERS.json', 'CALL_016.json'):
            with self.subTest(filename=filename), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                unused_campaign, stimuli = fixture(root, stack)
                path = stimuli / 'before' / filename
                document = runner.source.read(path)
                item = document['cases'][0] if filename == 'ACTUAL_CASES.json' else (
                    document['captures'][0] if filename == 'ACTUAL_READERS.json' else document)
                item['messages'][1]['content'] += ' extra metadata'
                write(path, document)
                with self.assertRaisesRegex(ValueError, 'drift'):
                    runner.load_stimuli(stimuli)

    def test_native_fake_fourteen_calls_failure_inclusive_no_fit(self):
        for arm, fail in (('AUDIT_SFT', False), ('AUDIT_LOSS_OFF', False), ('AUDIT_SFT', True)):
            with self.subTest(arm=arm, fail=fail), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                fixture(root, stack)
                packets, unused_binding = runner.load_stimuli(root / 'stimuli')
                expected = [case['messages'] for packet in packets for case in packet['cases']['cases']]
                state = 'original-' + arm
                engine = MagicMock(runtime={'fake': True})
                engine.model.named_parameters.return_value = [('model.lora_A.weight', state), ('base', 'unchanged')]
                responses = [generation('malformed'), generation('NONE')] + [generation(packets[0]['cases']['sources'][1]['event'])] * 12
                if fail:
                    responses[1] = RuntimeError('captured failure')
                engine.generate.side_effect = responses
                stack.enter_context(patch.dict('os.environ', ENVIRONMENT))
                stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', return_value='fake-tokenizer'))
                factory = stack.enter_context(patch.object(runner.source, 'Engine', return_value=engine))
                stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', return_value=state))
                if fail:
                    with self.assertRaisesRegex(ValueError, 'generation_errors'):
                        runner.main(arguments(root, arm, False))
                else:
                    runner.main(arguments(root, arm, False))
                output = root / ('run_' + arm)
                result = runner.source.read(output / ('FAILED.json' if fail else 'RESULT.json'))
                self.assertEqual((result['fits'], result['model_calls']), (0, 14))
                self.assertTrue(result['adapter_unchanged'] and result['frozen_base_unchanged'] and result['adapter_files_unchanged'])
                self.assertEqual([call.args[0] for call in engine.generate.call_args_list], expected)
                self.assertEqual(len(list(output.glob('CALL_*.json'))), 14)
                self.assertEqual([packet['calls'] for packet in result['packets']], [8, 6])
                self.assertEqual([packet['unique_prompts'] for packet in result['packets']], [4, 4])
                self.assertEqual(result['packets'][0]['chosen_source_indexes'][:3], [None, None, 1])
                self.assertEqual(factory.call_args.args[0].phase, 'readout')
                self.assertEqual(factory.call_args.args[0].adapter_dir, str(root / 'campaign' / arm / 'train/adapter'))
                self.assertEqual(factory.call_args.args[0].gpu_uuid, 'fake-gpu')
                self.assertEqual(factory.call_args.args[0].device, 'cuda:0')
                engine.check.assert_called_with('matched_audit_final')
                self.assertFalse((output / 'adapter').exists())
                self.assertFalse((output / 'TRAINING_ROWS.json').exists())

    def test_wrong_loaded_auditor_fails_before_generation(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            fixture(root, stack)
            engine = MagicMock(runtime={'fake': True})
            engine.model.named_parameters.return_value = [('model.lora_B.weight', 'A3-descendant')]
            stack.enter_context(patch.dict('os.environ', ENVIRONMENT))
            stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', return_value='fake'))
            stack.enter_context(patch.object(runner.source, 'Engine', return_value=engine))
            stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', return_value='A3-descendant'))
            with self.assertRaisesRegex(ValueError, 'original_auditor_state'):
                runner.main(arguments(root, prepare=False))
            engine.generate.assert_not_called()
            result = runner.source.read(root / 'run_AUDIT_SFT/FAILED.json')
            self.assertFalse(result['adapter_unchanged'])
            self.assertEqual(result['model_calls'], 0)


if __name__ == '__main__':
    unittest.main()
