"""Native-driver CPU contracts using captured fixtures and no ML runtime."""

from contextlib import ExitStack, contextmanager
from copy import deepcopy
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_event_two_hop as runner
from tests.test_experienced_event_two_hop import exposed_child, generation
from tests.test_astra_selected_reader_repair import write


ENVIRONMENT = dict(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='fake-gpu')


class FakeModel:
    def __init__(self, engine):
        self.engine = engine

    def named_parameters(self):
        return [('model.lora_A.weight', self.engine), ('base.weight', object())]

    @contextmanager
    def disable_adapter(self):
        if self.engine.off:
            raise AssertionError('nested adapter disable')
        self.engine.off = True
        self.engine.disable_entries += 1
        try:
            yield
        finally:
            self.engine.off = False


class FakeEngine:
    def __init__(self, arguments, tokenizer, *, check):
        self.arguments, self.tokenizer, self.check = arguments, tokenizer, check
        self.state = runner.PARENT_STATE
        self.runtime = {'fake': True}
        self.off = False
        self.disable_entries = 0
        self.calls = []
        self.base_checks = 0
        self.fail_off_once = False
        self.mutate_state = False
        self.mutate_file = None
        self.model = FakeModel(self)
        self.store = runner.task.exact_text_store(runner.task.collect_world(runner.task.build_world(),
            lambda messages: exposed_child(messages, '\n\n')))

    def verify_base(self):
        self.base_checks += 1

    def generate(self, messages, *, max_new_tokens):
        if max_new_tokens != 160:
            raise AssertionError('token bound drift')
        self.calls.append(dict(messages=deepcopy(messages), adapter_off=self.off))
        if self.off and self.fail_off_once:
            self.fail_off_once = False
            raise RuntimeError('captured adapter-off actor error')
        if self.mutate_state:
            self.state = 'changed-state'
        if self.mutate_file is not None:
            self.mutate_file.write_text('changed adapter file')
        if messages[0]['content'] == runner.task.COLLECTION_SYSTEM:
            return exposed_child(messages, '\n\n')
        if messages[0]['content'] == runner.source.world.MEMORY_SYSTEM:
            address = re.search(r'READ EVENT (E_[A-Z2-7]{10})', messages[1]['content']).group(1)
            return generation(self.store[address], messages)
        initial = messages[1]['content']
        events = re.search(r'^EVENTS (.+)$', initial, re.MULTILINE).group(1).split(',')
        reads = sum(message['role'] == 'assistant' and message['content'].startswith('READ EVENT ')
                    for message in messages)
        if reads < 4:
            return generation('READ EVENT ' + events[reads], messages)
        public = next(message['content'] for message in reversed(messages) if message['content'].startswith('ROUTE TASK\n'))
        current = re.search(r'^CURRENT (\S+)$', public, re.MULTILINE).group(1)
        goal = re.search(r'^GOAL (\S+)$', public, re.MULTILINE).group(1)
        ports = re.search(r'^PORTS (.+)$', public, re.MULTILINE).group(1).split(',')
        records = []
        for message in messages:
            if message['content'].startswith('MEMORY RESULT\n'):
                try:
                    raw = runner.task.micro.canonical_event(message['content'][len('MEMORY RESULT\n'):])
                    records.append(runner.task.micro.parse_event_line(raw))
                except ValueError:
                    pass
        selected = [record['port'] for record in records if record['source'] == current and
            (record['destination'] == goal or any(other['source'] == record['destination']
                                                 and other['destination'] == goal for other in records))]
        return generation('ROUTE ' + (selected[0] if selected else ports[0]), messages)


def fixture(root, stack):
    adapter = root / 'cycle/SELECTED/train/adapter'
    adapter.mkdir(parents=True)
    for name in ('adapter_model.safetensors', 'adapter_config.json'):
        (adapter / name).write_text('original-' + name)
    parent = dict(parent_adapter_state_sha256=runner.PARENT_STATE, adapter_dir=str(adapter),
        parent_adapter_files={path.name: runner.source.file_hash(path) for path in adapter.iterdir()},
        expected_base_sha256='base', parent_training_result_sha256='selected-train', parent_after_result_sha256='selected-after')
    original = dict(model_dir='no-model', expected_base_sha256='base')
    stack.enter_context(patch.dict('os.environ', ENVIRONMENT))
    stack.enter_context(patch.object(runner, 'load_parent', return_value=(original, parent)))
    tokenizer = stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', return_value='fake-tokenizer'))
    engines = []

    def factory(arguments, tokenizer, *, check):
        engine = FakeEngine(arguments, tokenizer, check=check)
        engines.append(engine)
        return engine

    factory_mock = stack.enter_context(patch.object(runner.source, 'Engine', side_effect=factory))
    stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash',
                             side_effect=lambda parameters: parameters['model.lora_A.weight'].state))
    return SimpleNamespace(parent=parent, original=original, tokenizer=tokenizer, factory=factory_mock, engines=engines)


def arguments(root, phase, output=None):
    result = ['--phase', phase, '--base-after', 'base-after', '--campaign', 'campaign', '--audit-root', 'audit-root',
              '--repair-root', 'repair-root', '--cycle-root', str(root / 'cycle'), '--gpu-uuid', 'fake-gpu',
              '--output', str(output or root / phase)]
    if phase == 'readout':
        result += ['--collection', str(root / 'collect')]
    return result


class TwoHopDriverTests(unittest.TestCase):
    def test_module_import_does_not_import_native_dependencies(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_event_two_hop
"""
        completed = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_prepare_has_no_engine_and_output_is_exclusive(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            result = runner.main(arguments(root, 'prepare'))
            self.assertEqual((result['status'], result['model_calls'], result['fits']), ('PREPARED_NO_MODEL', 0, 0))
            self.assertEqual(runner.source.read(root / 'prepare/TASKS.json'), runner.task.build_tasks(runner.task.build_world()))
            state.factory.assert_not_called()
            state.tokenizer.assert_not_called()
            with self.assertRaises(FileExistsError):
                runner.main(arguments(root, 'prepare'))

    def test_parent_pin_and_selected_after_join_reject_wrong_sources(self):
        for mutation in (None, 'train_state', 'after_state', 'after_join', 'arm'):
            with self.subTest(mutation=mutation), ExitStack() as stack:
                bank = runner.source.material.build_bank('two-hop-driver-prior')
                inputs = dict(old_bank=bank, fresh_source={'source': 'prior'},
                              after=dict(arguments={'expected_base_sha256': 'base'}))
                trained = dict(adapter_state_after=runner.PARENT_STATE, adapter_files={'adapter_model.safetensors': 'file'})
                after = dict(loaded_adapter_state_sha256=runner.PARENT_STATE, training_result_sha256='selected-train', fits=0, arm='SELECTED')
                if mutation == 'train_state':
                    trained['adapter_state_after'] = 'wrong-parent'
                elif mutation == 'after_state':
                    after['loaded_adapter_state_sha256'] = 'wrong-after-parent'
                elif mutation == 'after_join':
                    after['training_result_sha256'] = 'unrelated-fit'
                elif mutation == 'arm':
                    after['arm'] = 'UNIFORM'
                stack.enter_context(patch.object(runner.previous, 'load_parent', return_value=inputs))
                stack.enter_context(patch.object(runner.previous, 'read_collection', return_value=({'bank': bank}, [], 'collection')))
                stack.enter_context(patch.object(runner.previous, 'read_before', return_value=([1], 'before')))
                training = stack.enter_context(patch.object(runner.previous, 'read_training', return_value=(trained, 'selected-train')))
                stack.enter_context(patch.object(runner.previous, 'read_stage', return_value=(after, 'selected-after')))
                if mutation:
                    with self.assertRaisesRegex(ValueError, 'complete_selected_A3_parent'):
                        runner.load_parent(SimpleNamespace(cycle_root='cycle'))
                else:
                    unused_arguments, parent = runner.load_parent(SimpleNamespace(cycle_root='cycle'))
                    self.assertEqual(parent['parent_adapter_state_sha256'], runner.PARENT_STATE)
                    self.assertEqual(parent['parent_after_result_sha256'], 'selected-after')
                    self.assertEqual(training.call_args.args[0], Path('cycle/SELECTED/train'))

    def test_collect_eight_actual_captures_replay_and_drift_rejection(self):
        for mutation in (None, 'call', 'record', 'parent'):
            with self.subTest(mutation=mutation), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = fixture(root, stack)
                result = runner.main(arguments(root, 'collect'))
                self.assertEqual((result['fits'], result['model_calls'], result['accepted_events']), (0, 8, 4))
                self.assertEqual(state.engines[0].disable_entries, 0)
                self.assertEqual(state.engines[0].base_checks, 1)
                verified, digest = runner.read_collection(root / 'collect', state.parent)
                self.assertEqual(verified, runner.task.replay_collection(verified))
                self.assertEqual(digest, runner.source.file_hash(root / 'collect/RESULT.json'))
                self.assertTrue(all(raw.endswith('\n\n') for raw in runner.task.exact_text_store(verified).values()))
                if mutation == 'call':
                    saved = runner.source.read(root / 'collect/CALL_001.json')
                    saved['response']['raw'] += 'fake EVENT repair'
                    write(root / 'collect/CALL_001.json', saved)
                elif mutation == 'record':
                    saved = runner.source.read(root / 'collect/COLLECTION.json')
                    saved['records'][0]['event']['raw'] += 'repaired'
                    write(root / 'collect/COLLECTION.json', saved)
                    result['collection_sha256'] = runner.source.file_hash(root / 'collect/COLLECTION.json')
                    write(root / 'collect/RESULT.json', result)
                elif mutation == 'parent':
                    result['adapter_state_after'] = 'wrong-parent'
                    write(root / 'collect/RESULT.json', result)
                if mutation:
                    with self.assertRaises(ValueError):
                        runner.read_collection(root / 'collect', state.parent)

    def test_all_conditions_share_tasks_with_exact_actor_off_scope_and_112_calls(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            runner.main(arguments(root, 'collect'))
            result = runner.main(arguments(root, 'readout'))
            engine = state.engines[-1]
            self.assertEqual((result['fits'], result['model_calls']), (0, 112))
            self.assertEqual(result['native_calls_by_role'], {'actor': 96, 'memory': 16})
            self.assertEqual((engine.disable_entries, engine.off, engine.base_checks), (24, False, 1))
            self.assertEqual(engine.arguments.phase, 'readout')
            self.assertEqual(engine.arguments.adapter_dir, state.parent['adapter_dir'])
            self.assertEqual((engine.arguments.gpu_uuid, engine.arguments.device), ('fake-gpu', 'cuda:0'))
            tasks = runner.task.build_tasks(runner.task.build_world())
            for condition in runner.CONDITIONS:
                panel = result['panels'][condition]
                self.assertEqual([entry['task'] for entry in panel['episodes']], tasks)
                self.assertEqual((panel['actor_calls'], panel['memory_calls']), (24, 16))
                for index, entry in enumerate(panel['episodes']):
                    episode = entry['episode']
                    self.assertEqual(len(episode['traces'][0]['messages']), 2)
                    self.assertEqual(episode['traces'][0]['messages'],
                        result['panels']['ON_PARAMETRIC']['episodes'][index]['episode']['traces'][0]['messages'])
                    for trace in episode['traces']:
                        if trace['kind'] == 'memory':
                            if condition == 'ON_UNAVAILABLE':
                                self.assertEqual(trace['response'], 'MEMORY UNAVAILABLE')
                            elif condition != 'ON_PARAMETRIC':
                                self.assertEqual(trace['response'], engine.store[trace['address']])
                self.assertEqual(panel['correct'], 2 if condition == 'ON_UNAVAILABLE' else 4)
            for index, observed in enumerate(engine.calls):
                capture = runner.source.read(root / 'readout' / ('CALL_%03d.json' % index))
                self.assertEqual(observed['adapter_off'], capture['condition'] == 'OFF_OWN_TEXT' and capture['role'] == 'actor')
                if capture['role'] == 'memory':
                    self.assertEqual(capture['condition'], 'ON_PARAMETRIC')
                    self.assertNotIn('GOAL ', str(capture['messages']))
                    self.assertNotIn('CURRENT ', str(capture['messages']))
            self.assertEqual(result['adapter_state_after'], runner.PARENT_STATE)
            self.assertTrue(result['frozen_base_unchanged'])
            self.assertFalse((root / 'readout/adapter').exists())

    def test_readout_rejects_wrong_loaded_state_or_mutation_and_saves_failure(self):
        for mutation in ('mounted', 'state', 'files'):
            with self.subTest(mutation=mutation), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = fixture(root, stack)
                runner.main(arguments(root, 'collect'))
                original_factory = state.factory.side_effect

                def factory(*args, **kwargs):
                    engine = original_factory(*args, **kwargs)
                    if mutation == 'mounted':
                        engine.state = 'wrong-parent'
                    elif mutation == 'state':
                        engine.mutate_state = True
                    else:
                        engine.mutate_file = Path(state.parent['adapter_dir']) / 'adapter_model.safetensors'
                    return engine

                state.factory.side_effect = factory
                with self.assertRaises(ValueError):
                    runner.main(arguments(root, 'readout'))
                failure = runner.source.read(root / 'readout/FAILED.json')
                self.assertEqual(failure['fits'], 0)
                self.assertEqual(failure['model_calls'], 0 if mutation == 'mounted' else 112)
                self.assertFalse((root / 'readout/RESULT.json').exists())

    def test_adapter_off_error_restores_scope_and_preserves_failed_readout(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            runner.main(arguments(root, 'collect'))
            original_factory = state.factory.side_effect

            def factory(*args, **kwargs):
                engine = original_factory(*args, **kwargs)
                engine.fail_off_once = True
                return engine

            state.factory.side_effect = factory
            with self.assertRaisesRegex(ValueError, 'native_errors_retained'):
                runner.main(arguments(root, 'readout'))
            self.assertFalse(state.engines[-1].off)
            failure = runner.source.read(root / 'readout/FAILED.json')
            self.assertEqual(failure['fits'], 0)
            self.assertLessEqual(failure['model_calls'], 112)
            captures = [runner.source.read(path) for path in (root / 'readout').glob('CALL_*.json')]
            errors = [capture for capture in captures if capture['error'] is not None]
            self.assertEqual(len(errors), 1)
            self.assertEqual((errors[0]['role'], errors[0]['condition']), ('actor', 'OFF_OWN_TEXT'))
            self.assertTrue((root / 'readout/PANELS.json').exists())


if __name__ == '__main__':
    unittest.main()
