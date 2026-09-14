"""Bounded CPU contracts for the fresh-cycle driver; no native execution."""

from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_fresh_reader_cycle as runner
from gpu import astra_selected_reader_repair_train as trainer
from organism_v6 import experienced_event_read_route as controller
from tests.test_astra_selected_reader_repair import inputs_fixture, training_fixture, write


ENVIRONMENT = dict(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='fake-gpu')


def generation(raw, messages=None):
    result = dict(raw=raw, terminal=True, truncated=False)
    if messages is not None:
        result['messages'] = deepcopy(messages)
    return result


def fresh_fixture(no_reads=False):
    bank = runner.fresh.build_bank()

    def generate(messages):
        fact = next(fact for fact in bank if fact['port'] in messages[1]['content'])
        raw = ('EXPLORE ' + fact['node'] + ' ' + fact['port'] if len(messages) == 2
               else runner.source.material._event(fact))
        return generation(raw, messages)

    collection = runner.fresh.collect(generate)
    records = []
    by_address = {fact['event']: runner.source.material._event(fact) for fact in bank}
    for fact in bank:
        commands = [] if no_reads else ['READ EVENT ' + address for address in fact['public_events']]
        commands = iter(commands + ['ROUTE ' + fact['port']])
        transitions = {other['port']: other['outcome'] for other in bank if other['node'] == fact['node']}
        episode = controller.run_episode(controller.public_task(fact),
            lambda messages: generation(next(commands), messages),
            lambda address: generation(by_address[address]), transitions.__getitem__)
        records.append(dict(event=fact['event'], episode=episode))
    return collection, records


def prepared_inputs():
    inputs = inputs_fixture()
    old_bank = []
    for master in ('fresh-driver-old-zero', 'fresh-driver-old-one', 'fresh-driver-old-two'):
        old_bank.extend(runner.source.material.build_bank(master))
    inputs.update(fresh_source=dict(parent='bound-repaired-SFT-SELECTED', master=runner.fresh.MASTER),
        initial_state='repaired-parent', adapter_dir='repair/AUDIT_SFT_SELECTED/train/adapter',
        memory_rows=[dict(memory=index) for index in range(96)], old_bank=old_bank,
        old_episodes=[dict(fact=fact, event=generation(runner.source.material._event(fact))) for fact in old_bank])
    return inputs


def arguments(output, phase='prepare', arm='SELECTED', collection='collection', before='before', training='training'):
    result = ['--phase', phase, '--base-after', 'base-after', '--campaign', 'campaign',
              '--audit-root', 'audits', '--repair-root', 'repairs', '--output', str(output),
              '--gpu-uuid', 'fake-gpu']
    if phase in ('before', 'train', 'after'):
        result += ['--collection', str(collection)]
    if phase in ('train', 'after'):
        result += ['--before', str(before), '--arm', arm]
    if phase == 'after':
        result += ['--training', str(training)]
    return result


def stage_fixture(directory, inputs, phase, **changes):
    result = dict(schema=runner.SCHEMA, phase=phase, status='COMPLETE', source=deepcopy(inputs['fresh_source']),
        frozen_base_unchanged=True, parent_present=False, fits=0,
        loaded_adapter_state_sha256=inputs['initial_state'])
    result.update(changes)
    write(directory / 'RESULT.json', result)
    return runner.source.read(directory / 'RESULT.json')


def collection_fixture(directory, inputs):
    collection, records = fresh_fixture()
    write(directory / 'COLLECTION.json', collection)
    result = stage_fixture(directory, inputs, 'collect',
        collection_sha256=runner.source.file_hash(directory / 'COLLECTION.json'))
    return collection, records, result


def before_fixture(directory, inputs, collection, records, collection_sha='collection-receipt', choices=(1, 3, 3)):
    cases = runner.fresh.build_cases(collection, records)
    indexes = iter(list(choices) + [None] * (len(cases['cases']) - len(choices)))

    def generate(messages):
        index = next(indexes)
        return generation('NONE' if index is None else cases['sources'][index]['event'], messages)

    document = runner.fresh.collect_audit(cases, generate)
    write(directory / 'ACTUAL_CASES.json', cases)
    write(directory / 'ACTUAL_READERS.json', document)
    result = stage_fixture(directory, inputs, 'before', collection_result_sha256=collection_sha,
        panels=dict(OWN_PARAMETRIC=dict(episodes=records)))
    return result, cases, document


def fresh_training_fixture(directory, inputs, arm='SELECTED'):
    unused, result = training_fixture(directory)
    result.update(schema=runner.SCHEMA, phase='train', arm=arm, material_arm=arm,
        source=deepcopy(inputs['fresh_source']), parent_present=False, fits=1,
        adapter_state_before=inputs['initial_state'], adapter_state_after='fresh-' + arm,
        collection_result_sha256='collection-receipt', before_result_sha256='before-receipt',
        recipe=trainer.recipe(arm, [1, 3, 3], memory_count=96))
    write(directory / 'RESULT.json', result)
    return runner.source.read(directory / 'RESULT.json')


def parent_fixture(root, stack):
    parent = root / 'AUDIT_SFT_SELECTED'
    inputs, trained = training_fixture(parent / 'train')
    collection, unused = fresh_fixture()
    collection['bank'] = runner.source.material.build_bank('prior-A2')
    collection['episodes'] = [dict(fact=fact, event=generation(runner.source.material._event(fact)))
                              for fact in collection['bank']]
    inputs['collection'] = collection
    inputs['old_bank'] = (runner.source.material.build_bank('prior-original')
                          + runner.source.material.build_bank('prior-A1'))
    inputs['old_episodes'] = [dict(fact=fact, event=generation(runner.source.material._event(fact)))
                             for fact in inputs['old_bank']]
    receipt = dict(schema=runner.repair.SCHEMA, phase='after', status='COMPLETE', fits=0,
        parent_arm='AUDIT_SFT', material_arm='SELECTED', source=deepcopy(inputs['repair_source']),
        loaded_adapter_state_sha256=trained['adapter_state_after'],
        training_result_sha256=runner.source.file_hash(parent / 'train/RESULT.json'), frozen_base_unchanged=True)
    write(parent / 'after/RESULT.json', receipt)
    load = stack.enter_context(patch.object(runner.repair, 'load_inputs', side_effect=lambda *args: deepcopy(inputs)))
    options = SimpleNamespace(base_after='base-after', campaign='campaign', audit_root='audits', repair_root=str(root))
    return inputs, trained, receipt, options, load


class FakeEngine:
    def __init__(self, inputs, collection):
        self.runtime = {'fake': True}
        self.model = MagicMock()
        self.model.named_parameters.return_value = [('layer.lora_A.default.weight', object())]
        self.verify_base = MagicMock()
        self.calls = []
        self.facts = inputs['old_bank'] + collection['bank']
        for index in range(2):
            self.facts += runner.source.material.build_bank(runner.driver.development.HELD_MASTER + '-' + str(index))
        self.audits = iter([collection['bank'][index]['event'] for index in (1, 3, 3)] + ['NONE'] * 5)

    def generate(self, messages, **kwargs):
        self.calls.append(deepcopy(messages))
        if messages[0]['content'] == 'fixture-held':
            return generation('NONE', messages)
        if messages[0]['content'] == controller.PUBLIC_SYSTEM:
            task = messages[1]['content']
            fact = next(fact for fact in self.facts if 'GOAL ' + fact['outcome'] + '\n' in task)
            read_count = sum(message['role'] == 'assistant' for message in messages)
            raw = 'READ EVENT ' + fact['public_events'][read_count] if read_count < 2 else 'ROUTE ' + fact['port']
            return generation(raw, messages)
        address = re.search(r'READ EVENT (E_[A-Z0-9]+)', messages[-1]['content'])
        if address:
            fact = next((fact for fact in self.facts if fact['event'] == address.group(1)), None)
            return generation('MISS\n' if fact is None else runner.source.material._event(fact), messages)
        return generation(next(self.audits), messages)


def held_fixture(cases, generate, *, coached):
    if coached:
        raise AssertionError('live parent guidance is forbidden')
    captures = [generate([dict(role='system', content='fixture-held'),
                          dict(role='user', content=str(index))]) for index in range(16)]
    return dict(captures=captures, model_calls=16, parent_present=False)


def native_mocks(stack, inputs, engine, states=None):
    stack.enter_context(patch.dict('os.environ', ENVIRONMENT))
    stack.enter_context(patch.object(runner, 'load_parent', return_value=deepcopy(inputs)))
    tokenizer = stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', return_value='fake-tokenizer'))
    factory = stack.enter_context(patch.object(runner.source, 'Engine', return_value=engine))
    state = stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash',
        side_effect=states if states is not None else None, return_value=inputs['initial_state']))
    return tokenizer, factory, state


class ParentTests(unittest.TestCase):
    def test_real_parent_loader_preserves_all_twelve_facts_and_selected_receipts(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            inputs, trained, receipt, options, load = parent_fixture(root, stack)
            result = runner.load_parent(options)
            self.assertEqual(result['memory_rows'], inputs['memory_rows'][:64] + inputs['new_rows'])
            self.assertEqual(len(result['memory_rows']), 96)
            self.assertEqual(result['old_bank'], inputs['old_bank'] + inputs['collection']['bank'])
            self.assertEqual(result['old_episodes'], inputs['old_episodes'] + inputs['collection']['episodes'])
            self.assertEqual(len(set(result['fresh_source']['prior_event_ids'])), 12)
            self.assertEqual(result['initial_state'], trained['adapter_state_after'])
            self.assertEqual(result['adapter_dir'], str(root / 'AUDIT_SFT_SELECTED/train/adapter'))
            self.assertEqual(result['fresh_source']['parent_training_result_sha256'], receipt['training_result_sha256'])
            self.assertEqual(result['fresh_source']['memory_rows_sha256'], runner.source.native._digest(result['memory_rows']))
            load.assert_called_once_with('base-after', 'campaign', 'audits', 'AUDIT_SFT')

    def test_parent_after_receipt_mismatches_fail_before_native_loading(self):
        changes = dict(schema='other', phase='train', status='FAILED', fits=1, parent_arm='AUDIT_LOSS_OFF',
            material_arm='UNIFORM', source={}, loaded_adapter_state_sha256='sibling',
            training_result_sha256='different-fit', frozen_base_unchanged=False)
        for field, value in changes.items():
            with self.subTest(field=field), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                unused, unused_train, receipt, options, unused_load = parent_fixture(root, stack)
                receipt[field] = value
                write(root / 'AUDIT_SFT_SELECTED/after/RESULT.json', receipt)
                with self.assertRaisesRegex(ValueError, 'own_terminal_repaired_parent_required'):
                    runner.load_parent(options)

    def test_parent_failed_marker_and_adapter_file_drift_fail_closed(self):
        for target in ('after/FAILED.json', 'train/adapter/adapter_model.safetensors'):
            with self.subTest(target=target), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                unused, unused_train, unused_after, options, unused_load = parent_fixture(root, stack)
                (root / 'AUDIT_SFT_SELECTED' / target).write_bytes(b'drift')
                with self.assertRaises(ValueError):
                    runner.load_parent(options)

    def test_duplicate_prior_event_is_rejected(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            inputs, unused, unused_after, options, unused_load = parent_fixture(Path(temporary), stack)
            inputs['old_bank'][0] = inputs['collection']['bank'][0]
            with self.assertRaisesRegex(ValueError, 'all_twelve_prior_facts_required'):
                runner.load_parent(options)

    def test_fresh_identity_collision_is_rejected_for_every_identity_field(self):
        for field in ('world', 'event', 'node', 'port', 'outcome', 'receipt'):
            with self.subTest(field=field), TemporaryDirectory() as temporary, ExitStack() as stack:
                inputs, unused, unused_after, options, unused_load = parent_fixture(Path(temporary), stack)
                proposed = runner.fresh.build_bank()
                proposed[0][field] = inputs['old_bank'][0][field]
                stack.enter_context(patch.object(runner.fresh, 'build_bank', return_value=proposed))
                stack.enter_context(patch.object(runner.source.world, 'build_bank',
                    side_effect=runner.source.material.build_bank, create=True))
                with self.assertRaisesRegex(ValueError, 'fresh_bank_identity_overlap'):
                    runner.load_parent(options)


class ReceiptTests(unittest.TestCase):
    def test_stage_source_status_phase_and_parent_controls(self):
        changes = dict(schema='other', phase='train', status='FAILED', source={},
                       frozen_base_unchanged=False, parent_present=True)
        for field, value in changes.items():
            with self.subTest(field=field), TemporaryDirectory() as temporary:
                directory = Path(temporary)
                inputs = prepared_inputs()
                receipt = stage_fixture(directory, inputs, 'collect')
                receipt[field] = value
                write(directory / 'RESULT.json', receipt)
                with self.assertRaisesRegex(ValueError, 'own_complete_fresh_stage_required'):
                    runner.read_stage(directory, inputs, 'collect')

    def test_failed_marker_overrides_complete_result(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            inputs = prepared_inputs()
            stage_fixture(directory, inputs, 'collect')
            write(directory / 'FAILED.json', {'error': 'preserved'})
            with self.assertRaisesRegex(ValueError, 'failed_fresh_stage_forbidden'):
                runner.read_stage(directory, inputs, 'collect')

    def test_collection_replays_all_four_events_and_binds_actor_and_file(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            inputs = prepared_inputs()
            collection, unused, receipt = collection_fixture(directory, inputs)
            record, rows, digest = runner.read_collection(directory, inputs)
            self.assertEqual(record, collection)
            self.assertEqual(rows, runner.fresh.replay_collection(collection))
            self.assertEqual(len(rows), 32)
            self.assertEqual(digest, runner.source.file_hash(directory / 'RESULT.json'))
            for field, value in (('loaded_adapter_state_sha256', 'sibling'), ('fits', 1), ('collection_sha256', 'wrong')):
                with self.subTest(field=field):
                    changed = dict(receipt, **{field: value})
                    write(directory / 'RESULT.json', changed)
                    with self.assertRaisesRegex(ValueError, 'own_fresh_collection_actor_required'):
                        runner.read_collection(directory, inputs)

    def test_collection_resealed_document_drift_is_not_accepted(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            inputs = prepared_inputs()
            collection, unused, receipt = collection_fixture(directory, inputs)
            collection['captures'][0]['response']['raw'] = 'invented'
            write(directory / 'COLLECTION.json', collection)
            receipt['collection_sha256'] = runner.source.file_hash(directory / 'COLLECTION.json')
            write(directory / 'RESULT.json', receipt)
            with self.assertRaises(ValueError):
                runner.read_collection(directory, inputs)

    def test_faithfully_captured_failed_collection_cannot_become_fit_material(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            inputs = prepared_inputs()
            collection = runner.fresh.collect(lambda messages: generation('invalid', messages))
            self.assertEqual(runner.fresh.replay_collection(collection), [])
            write(directory / 'COLLECTION.json', collection)
            stage_fixture(directory, inputs, 'collect',
                collection_sha256=runner.source.file_hash(directory / 'COLLECTION.json'))
            with self.assertRaisesRegex(ValueError, 'all_four_fresh_events_required'):
                runner.read_collection(directory, inputs)

    def test_read_before_keeps_wrong_source_valid_choices_and_duplicates(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            inputs = prepared_inputs()
            collection, records = fresh_fixture()
            unused, unused_cases, document = before_fixture(directory, inputs, collection, records)
            self.assertTrue(all(not item['correct'] for item in document['captures'][:3]))
            selected, digest = runner.read_before(directory, inputs, collection, 'collection-receipt')
            self.assertEqual(selected, [1, 3, 3])
            self.assertEqual(digest, runner.source.file_hash(directory / 'RESULT.json'))

    def test_read_before_rejects_actor_collection_and_fit_mismatch(self):
        for field, value in (('loaded_adapter_state_sha256', 'sibling'), ('fits', 1),
                             ('collection_result_sha256', 'other-collection')):
            with self.subTest(field=field), TemporaryDirectory() as temporary:
                directory = Path(temporary)
                inputs = prepared_inputs()
                collection, records = fresh_fixture()
                receipt, unused, unused_doc = before_fixture(directory, inputs, collection, records)
                receipt[field] = value
                write(directory / 'RESULT.json', receipt)
                with self.assertRaisesRegex(ValueError, 'own_fresh_before_required'):
                    runner.read_before(directory, inputs, collection, 'collection-receipt')

    def test_read_before_rejects_case_capture_or_selection_drift(self):
        for target in ('cases', 'prompt', 'response', 'choices', 'extra', 'error'):
            with self.subTest(target=target), TemporaryDirectory() as temporary:
                directory = Path(temporary)
                inputs = prepared_inputs()
                collection, records = fresh_fixture()
                unused, cases, document = before_fixture(directory, inputs, collection, records)
                if target == 'cases':
                    cases['expected_calls'] += 1
                    write(directory / 'ACTUAL_CASES.json', cases)
                else:
                    if target == 'prompt': document['captures'][0]['messages'][0]['content'] = 'changed'
                    if target == 'response': document['captures'][0]['response']['raw'] = 'NONE'
                    if target == 'choices': document['chosen_source_indexes'][0] = 0
                    if target == 'extra': document['captures'].append(deepcopy(document['captures'][-1]))
                    if target == 'error': document['captures'][0]['error'] = {'error': 'callback failed'}
                    write(directory / 'ACTUAL_READERS.json', document)
                with self.assertRaises(ValueError):
                    runner.read_before(directory, inputs, collection, 'collection-receipt')

    def test_empty_pointers_and_no_read_routes_never_fabricate_fit_material(self):
        for no_reads in (False, True):
            with self.subTest(no_reads=no_reads), TemporaryDirectory() as temporary:
                directory = Path(temporary)
                inputs = prepared_inputs()
                collection, records = fresh_fixture(no_reads=no_reads)
                before_fixture(directory, inputs, collection, records, choices=())
                with self.assertRaisesRegex(ValueError, 'no_source_selection_no_matched_fit'):
                    runner.read_before(directory, inputs, collection, 'collection-receipt')

    def test_training_receipt_checks_each_material_fork_and_all_bindings(self):
        for arm in ('SELECTED', 'UNIFORM'):
            with self.subTest(arm=arm), TemporaryDirectory() as temporary:
                directory = Path(temporary)
                inputs = prepared_inputs()
                receipt = fresh_training_fixture(directory, inputs, arm)
                accepted, digest = runner.read_training(directory, inputs, arm, 'collection-receipt', 'before-receipt')
                self.assertEqual(accepted, receipt)
                self.assertEqual(digest, runner.source.file_hash(directory / 'RESULT.json'))
                changes = dict(arm='sibling', material_arm='sibling', fits=0, updates=99,
                    adapter_state_before='sibling', adapter_state_after=inputs['initial_state'],
                    collection_result_sha256='other', before_result_sha256='other')
                for field, value in changes.items():
                    with self.subTest(field=field):
                        write(directory / 'RESULT.json', dict(receipt, **{field: value}))
                        with self.assertRaisesRegex(ValueError, 'own_matched_fresh_training_required'):
                            runner.read_training(directory, inputs, arm, 'collection-receipt', 'before-receipt')

    def test_training_inventories_file_hashes_and_unsafe_names_fail_closed(self):
        for target in ('adapter_files', 'training_artifact_sha256', 'adapter', 'losses', 'unsafe'):
            with self.subTest(target=target), TemporaryDirectory() as temporary:
                directory = Path(temporary)
                inputs = prepared_inputs()
                receipt = fresh_training_fixture(directory, inputs)
                if target in ('adapter_files', 'training_artifact_sha256'):
                    receipt[target] = {}
                elif target == 'unsafe':
                    receipt['adapter_files']['../escape'] = 'digest'
                else:
                    filename = 'adapter/adapter_model.safetensors' if target == 'adapter' else 'LOSSES.jsonl'
                    (directory / filename).write_bytes(b'drift')
                write(directory / 'RESULT.json', receipt)
                with self.assertRaises(ValueError):
                    runner.read_training(directory, inputs, 'SELECTED', 'collection-receipt', 'before-receipt')


class EvaluationTests(unittest.TestCase):
    def test_all_twelve_old_records_are_evaluated_once_per_wrapper_without_duplicate_panels(self):
        with TemporaryDirectory() as temporary:
            output = Path(temporary)
            inputs = prepared_inputs()
            collection, unused = fresh_fixture()
            engine = FakeEngine(inputs, collection)
            with patch.object(runner.driver, 'evaluate', wraps=runner.driver.evaluate) as evaluate:
                result = runner.evaluate(engine, collection, inputs, output)
            evaluate.assert_called_once_with(engine, collection, inputs['old_bank'][:8],
                                             inputs['old_episodes'][:8], output, reader_wrapper=0)
            self.assertEqual(result['model_calls'], len(engine.calls))
            self.assertEqual(result['model_calls'], 100)
            expected_ids = [fact['event'] for fact in inputs['old_bank']]
            for view in (0, 8):
                panel = result['panels']['OLD_RECALL_W%d' % view]
                self.assertEqual((panel['denominator'], panel['correct']), (12, 12))
                self.assertEqual([row['event'] for row in panel['rows']], expected_ids)
                self.assertEqual(len(list(output.glob('OLD_RECALL_W%d_*.json' % view))), 12)
            old_requests = Counter()
            for messages in engine.calls:
                for event in expected_ids:
                    if 'READ EVENT ' + event in messages[-1]['content']:
                        old_requests[event] += 1
            self.assertEqual(old_requests, Counter({event: 2 for event in expected_ids}))
            self.assertEqual(len(list((output / 'new_task').glob('CALL_*.json'))), 76)

    def test_newly_appended_old_record_failures_remain_in_denominator(self):
        with TemporaryDirectory() as temporary:
            inputs = prepared_inputs()
            collection, unused = fresh_fixture()
            engine = FakeEngine(inputs, collection)
            original = engine.generate
            failed_event = inputs['old_bank'][-1]['event']

            def generate(messages, **kwargs):
                response = original(messages, **kwargs)
                if failed_event in messages[-1]['content']:
                    response['raw'] = 'wrong receipt'
                return response

            engine.generate = generate
            result = runner.evaluate(engine, collection, inputs, Path(temporary))
            for view in (0, 8):
                self.assertEqual(result['panels']['OLD_RECALL_W%d' % view]['denominator'], 12)
                self.assertEqual(result['panels']['OLD_RECALL_W%d' % view]['correct'], 11)


class DispatchTests(unittest.TestCase):
    def test_import_and_prepare_never_import_or_load_native_packages(self):
        script = textwrap.dedent('''
            import builtins
            original_import = builtins.__import__
            def blocked(name, *args, **kwargs):
                if name.split('.')[0] in ('torch', 'transformers', 'tokenizers', 'peft', 'safetensors'):
                    raise AssertionError('native import: ' + name)
                return original_import(name, *args, **kwargs)
            builtins.__import__ = blocked
            from pathlib import Path
            from tempfile import TemporaryDirectory
            from unittest.mock import patch
            from tests.test_astra_fresh_reader_cycle import runner, prepared_inputs, arguments
            with TemporaryDirectory() as temporary, \
                 patch.dict('os.environ', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES=''), \
                 patch.object(runner, 'load_parent', return_value=prepared_inputs()), \
                 patch.object(runner.source.native, 'load_local_tokenizer', side_effect=AssertionError('tokenizer load')) as tokenizer, \
                 patch.object(runner.source, 'Engine', side_effect=AssertionError('model load')) as engine:
                output = Path(temporary) / 'prepare'
                runner.main(arguments(output))
                result = runner.source.read(output / 'RESULT.json')
                assert result['status'] == 'PREPARED_NO_MODEL'
                assert result['fits'] == result['model_calls'] == 0
                assert sorted(path.name for path in output.iterdir()) == ['INPUTS.json', 'REQUEST.json', 'RESULT.json']
                tokenizer.assert_not_called()
                engine.assert_not_called()
        ''')
        process = subprocess.run([sys.executable, '-B', '-c', script],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)

    def test_collection_uses_parent_and_preserves_eight_exclusive_captures(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            output = Path(temporary) / 'collect'
            inputs = prepared_inputs()
            collection, unused = fresh_fixture()
            engine = FakeEngine(inputs, collection)
            engine.generate = MagicMock(side_effect=[capture['response'] for capture in collection['captures']])
            unused_tokenizer, factory, unused_state = native_mocks(stack, inputs, engine)
            runner.main(arguments(output, 'collect'))
            result = runner.source.read(output / 'RESULT.json')
            self.assertEqual((result['status'], result['model_calls'], result['fits']), ('COMPLETE', 8, 0))
            self.assertEqual(factory.call_args.args[0].adapter_dir, inputs['adapter_dir'])
            self.assertEqual(factory.call_args.args[0].phase, 'readout')
            self.assertEqual(len(list(output.glob('CALL_*.json'))), 8)
            self.assertEqual(len(runner.fresh.replay_collection(runner.source.read(output / 'COLLECTION.json'))), 32)
            saved = (output / 'RESULT.json').read_bytes()
            with self.assertRaises(FileExistsError):
                runner.main(arguments(output, 'collect'))
            self.assertEqual((output / 'RESULT.json').read_bytes(), saved)
            self.assertEqual(engine.generate.call_count, 8)

    def test_fake_before_and_after_use_exclusive_separate_capture_paths(self):
        for phase in ('before', 'after'):
            with self.subTest(phase=phase), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                output = root / phase
                inputs = prepared_inputs()
                collection, records, unused_receipt = collection_fixture(root / 'collection', inputs)
                collection_sha = runner.source.file_hash(root / 'collection/RESULT.json')
                before_fixture(root / 'prior-before', inputs, collection, records, collection_sha)
                training = fresh_training_fixture(root / 'train', inputs)
                training['collection_result_sha256'] = collection_sha
                training['before_result_sha256'] = runner.source.file_hash(root / 'prior-before/RESULT.json')
                write(root / 'train/RESULT.json', training)
                expected_state = inputs['initial_state'] if phase == 'before' else training['adapter_state_after']
                engine = FakeEngine(inputs, collection)
                unused_tokenizer, factory, unused_state = native_mocks(stack, inputs, engine, [expected_state, expected_state])
                stack.enter_context(patch.object(runner.repair.prior.lesson, 'collect_cases', side_effect=held_fixture))
                runner.main(arguments(output, phase, collection=root / 'collection', before=root / 'prior-before', training=root / 'train'))
                result = runner.source.read(output / 'RESULT.json')
                self.assertEqual((result['status'], result['model_calls'], result['fits']), ('COMPLETE', 124, 0))
                self.assertEqual(len(engine.calls), 124)
                self.assertEqual(len(list(output.glob('CALL_*.json'))), 24)
                self.assertEqual(len(list((output / 'new_task').glob('CALL_*.json'))), 76)
                self.assertTrue((output / 'CALL_000.json').is_file())
                self.assertTrue((output / 'new_task/CALL_001.json').is_file())
                self.assertEqual(len(list(output.glob('OLD_RECALL_*.json'))), 24)
                self.assertEqual(result['loaded_adapter_state_sha256'], expected_state)
                expected_adapter = inputs['adapter_dir'] if phase == 'before' else str(root / 'train/adapter')
                self.assertEqual(factory.call_args.args[0].adapter_dir, expected_adapter)
                engine.verify_base.assert_called_once_with()

    def test_both_training_forks_share_parent_before_choices_and_96_memory_rows(self):
        for arm in ('SELECTED', 'UNIFORM'):
            with self.subTest(arm=arm), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                output = root / arm
                inputs = prepared_inputs()
                collection, records, unused = collection_fixture(root / 'collection', inputs)
                before_fixture(root / 'before', inputs, collection, records,
                    runner.source.file_hash(root / 'collection/RESULT.json'))
                engine = FakeEngine(inputs, collection)
                unused_tokenizer, factory, unused_state = native_mocks(stack, inputs, engine)

                def fit(*args, **kwargs):
                    runner.source.write(args[5] / 'RECIPE.json', {'memory_row_count': kwargs['memory_count']})
                    return dict(schema=trainer.SCHEMA, updates=100, material_arm=arm,
                        adapter_state_before=inputs['initial_state'], adapter_state_after='fresh-' + arm,
                        code_provenance={'fixture': 'preserved'})

                train = stack.enter_context(patch.object(trainer, 'train', side_effect=fit))
                runner.main(arguments(output, 'train', arm=arm, collection=root / 'collection', before=root / 'before'))
                train.assert_called_once_with(engine, inputs['memory_rows'], inputs['cue_rows'], inputs['lesson_rows'],
                    runner.fresh.replay_collection(collection), output, material_arm=arm,
                    selected_source_indexes=[1, 3, 3], memory_count=96)
                self.assertEqual(factory.call_args.args[0].adapter_dir, inputs['adapter_dir'])
                self.assertEqual(engine.calls, [])
                result = runner.source.read(output / 'RESULT.json')
                self.assertEqual((result['schema'], result['arm'], result['fits']), (runner.SCHEMA, arm, 1))
                self.assertEqual(result['code_provenance'], {'fixture': 'preserved'})

    def test_phase_argument_and_environment_gates_precede_load(self):
        invalid = []
        for phase in ('before', 'train', 'after'):
            argv = arguments('unused', phase)
            index = argv.index('--collection')
            invalid.append(argv[:index] + argv[index + 2:])
        invalid += [arguments('unused') + ['--arm', 'UNIFORM'],
                    arguments('unused', 'collect') + ['--before', 'wrong'],
                    arguments('unused', 'train') + ['--training', 'wrong']]
        for argv in invalid:
            with self.subTest(argv=argv), patch.object(runner, 'load_parent') as load:
                with self.assertRaisesRegex(ValueError, 'fresh_phase_inputs_required'):
                    runner.main(argv)
                load.assert_not_called()
        for environment, reason in (({}, 'offline_required'),
            (dict(ENVIRONMENT, CUDA_VISIBLE_DEVICES='other'), 'exact_gpu_required')):
            with patch.dict('os.environ', environment, clear=True), patch.object(runner, 'load_parent') as load:
                with self.assertRaisesRegex(ValueError, reason):
                    runner.main(arguments('unused', 'collect'))
                load.assert_not_called()

    def test_wrong_loaded_actor_aborts_before_generation_and_preserves_failure(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            output = Path(temporary) / 'collect'
            inputs = prepared_inputs()
            collection, unused = fresh_fixture()
            engine = FakeEngine(inputs, collection)
            native_mocks(stack, inputs, engine, ['wrong-sibling'])
            with self.assertRaisesRegex(ValueError, 'own_fresh_actor_required'):
                runner.main(arguments(output, 'collect'))
            self.assertEqual(engine.calls, [])
            self.assertEqual(runner.source.read(output / 'FAILED.json')['status'], 'FAILED')
            self.assertFalse((output / 'RESULT.json').exists())

    def test_collection_callback_failure_keeps_all_attempts_and_no_valid_result(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            output = Path(temporary) / 'collect'
            inputs = prepared_inputs()
            collection, unused = fresh_fixture()
            engine = FakeEngine(inputs, collection)
            engine.generate = MagicMock(side_effect=RuntimeError('fixture failure'))
            native_mocks(stack, inputs, engine)
            with self.assertRaisesRegex(ValueError, 'incomplete_fresh_collection_no_fit'):
                runner.main(arguments(output, 'collect'))
            self.assertEqual(len(list(output.glob('CALL_*.json'))), 4)
            document = runner.source.read(output / 'COLLECTION.json')
            self.assertEqual(document['accepted_events'], 0)
            self.assertEqual(document['infrastructure_failures'], 4)
            self.assertEqual(runner.source.read(output / 'FAILED.json')['captured_calls'], 4)
            self.assertFalse((output / 'RESULT.json').exists())

    def test_readonly_state_change_retains_collection_captures_and_failure(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            output = Path(temporary) / 'collect'
            inputs = prepared_inputs()
            collection, unused = fresh_fixture()
            engine = FakeEngine(inputs, collection)
            engine.generate = MagicMock(side_effect=[capture['response'] for capture in collection['captures']])
            native_mocks(stack, inputs, engine, [inputs['initial_state'], 'changed'])
            with self.assertRaisesRegex(ValueError, 'readonly_fresh_stage_changed_adapter'):
                runner.main(arguments(output, 'collect'))
            self.assertEqual(len(list(output.glob('CALL_*.json'))), 8)
            self.assertTrue((output / 'COLLECTION.json').is_file())
            self.assertTrue((output / 'FAILED.json').is_file())
            self.assertFalse((output / 'RESULT.json').exists())

    def test_failed_base_check_retains_full_before_audit_and_retention_artifacts(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            output = root / 'before'
            inputs = prepared_inputs()
            collection, unused, unused_receipt = collection_fixture(root / 'collection', inputs)
            engine = FakeEngine(inputs, collection)
            engine.verify_base.side_effect = ValueError('fixture_base_changed')
            native_mocks(stack, inputs, engine)
            stack.enter_context(patch.object(runner.repair.prior.lesson, 'collect_cases', side_effect=held_fixture))
            with self.assertRaisesRegex(ValueError, 'fixture_base_changed'):
                runner.main(arguments(output, 'before', collection=root / 'collection'))
            self.assertEqual(len(engine.calls), 124)
            self.assertEqual(len(list(output.glob('CALL_*.json'))), 24)
            self.assertEqual(len(list(output.glob('OLD_RECALL_*.json'))), 24)
            self.assertEqual(len(list((output / 'new_task').glob('CALL_*.json'))), 76)
            self.assertTrue((output / 'ACTUAL_READERS.json').is_file())
            self.assertTrue((output / 'FAILED.json').is_file())
            self.assertFalse((output / 'RESULT.json').exists())

    def test_failed_fit_retains_partial_losses_without_valid_checkpoint_claim(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            output = root / 'train'
            inputs = prepared_inputs()
            collection, records, unused = collection_fixture(root / 'collection', inputs)
            before_fixture(root / 'before', inputs, collection, records,
                runner.source.file_hash(root / 'collection/RESULT.json'))
            engine = FakeEngine(inputs, collection)
            native_mocks(stack, inputs, engine)

            def failed_fit(*args, **kwargs):
                with (args[5] / 'LOSSES.jsonl').open('x') as stream:
                    stream.write('{"update":1,"loss":0.5}\n')
                raise RuntimeError('fixture_partial_fit')

            stack.enter_context(patch.object(trainer, 'train', side_effect=failed_fit))
            with self.assertRaisesRegex(RuntimeError, 'fixture_partial_fit'):
                runner.main(arguments(output, 'train', collection=root / 'collection', before=root / 'before'))
            self.assertEqual((output / 'LOSSES.jsonl').read_text(), '{"update":1,"loss":0.5}\n')
            self.assertTrue((output / 'TRAINING_ROWS.json').is_file())
            self.assertTrue((output / 'FAILED.json').is_file())
            self.assertFalse((output / 'RESULT.json').exists())
            self.assertFalse((output / 'adapter').exists())


if __name__ == '__main__':
    unittest.main()
