"""CPU fixtures for source joins and memory closure; no ML or device runtime."""

from collections import Counter
from contextlib import ExitStack, nullcontext
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_event_two_hop_memory as runner
from organism_v6 import experienced_event_cue_collection as cue
from organism_v6 import experienced_event_microloop as micro
from tests.test_experienced_event_cue_sleep import ReadingEngine, collector
from tests.test_experienced_event_two_hop import exposed_child, generation
from tests.test_experienced_event_two_hop_lesson import Tokenizer, coached_child
from tests.test_experienced_event_two_hop_transfer import source_actor


ENVIRONMENT = dict(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='fake-gpu')


def write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, allow_nan=False))


def captured(directory, callback):
    calls = []

    def generate(messages, **metadata):
        response = callback(messages)
        call = dict(call_index=len(calls), messages=deepcopy(messages), response=deepcopy(response), error=None,
                    **dict(dict(role='collection', condition=None, task_index=None), **metadata))
        calls.append(call)
        write(directory / f"CALL_{call['call_index']:03d}.json", call)
        return response

    return generate, calls


def actor(messages):
    reads = sum(message['role'] == 'assistant' and message['content'].startswith('READ EVENT ')
                for message in messages)
    if reads < 4:
        events = re.search(r'^EVENTS (.+)$', messages[1]['content'], re.MULTILINE).group(1).split(',')
        return generation('READ EVENT ' + events[reads], messages)
    try:
        return source_actor(messages)
    except (ValueError, StopIteration):
        public = next(message['content'] for message in reversed(messages) if message['content'].startswith('ROUTE TASK\n'))
        port = re.search(r'^PORTS (.+)$', public, re.MULTILINE).group(1).split(',')[0]
        return generation('ROUTE ' + port, messages)


def material_fixture():
    banks = [micro.build_bank('memory-closure-fixture-' + str(index)) for index in range(4)]
    episodes = [[dict(fact=fact, event=generation(micro._event(fact)),
                     exploration=generation('EXPLORE ' + fact['node'] + ' ' + fact['port'])) for fact in bank] for bank in banks]
    memory_rows = sum([micro.compile_rows(bank, records, serialization='FINAL_LF_ONLY')
                       for bank, records in zip(banks, episodes)], [])
    reader = ReadingEngine()
    cue_rows = []
    for bank in collector.training_banks():
        document = cue.run_collection(bank, {fact['event']: micro._event(fact) for fact in bank},
                                      reader.generate, teaching_mode=cue.PUBLIC_FEEDBACK_MODE)
        cue_rows.extend(document['student_rows'])
    events = [dict(event=fact['event'], raw=micro._event(fact)) for bank in banks[:2] for fact in bank]
    cases = runner.audit.build_cases(events, runner.audit.DEV)
    answers = iter(case['expected'] for case in cases['cases'])
    audit_rows = runner.audit.collect_cases(cases, lambda messages: generation(next(answers), messages), coached=True)['rows'][:62]
    original = runner.hop.collect_world(runner.hop.build_world(), exposed_child)
    lessons = runner.lesson.lesson.collect_lessons(original, coached_child)
    held = runner.audit.build_cases(events[:4], runner.audit.HELD)
    return dict(material=dict(memory_rows=memory_rows, cue_rows=cue_rows, audit_rows=audit_rows,
                              trajectory_rows=lessons['rows']), banks=banks, episodes=episodes, lessons=lessons, held=held)


def setup(root, stack, data):
    data = deepcopy(data)
    original = root / 'lesson'
    world = runner.hop.build_world(runner.hop.TRANSFER_MASTER)
    adapter = original / 'train/adapter'
    write(adapter / 'adapter_config.json', dict(r=8, fixture_state=runner.PARENT_STATE))
    (adapter / 'adapter_model.safetensors').write_text('fixture only')
    model = root / 'base'
    write(model / 'config.json', dict(model_type='qwen2', hidden_size=3584, num_hidden_layers=28))
    (model / 'model.safetensors').write_text('not a model')
    material = data['material']
    recorded = {key + '_sha256': runner.source.native._digest(material[key])
                for key in ('memory_rows', 'cue_rows', 'audit_rows')}
    recorded.update(actor_helper_sha256='historical-0b-helper-not-current', lesson_helper_sha256='historical-lesson')
    directory = original / 'collect'
    write(directory / 'LESSONS.json', data['lessons'])
    for capture in data['lessons']['captures']:
        write(directory / f"CALL_{capture['call_index']:03d}.json", capture)
    write(directory / 'RESULT.json', dict(schema=runner.lesson.SCHEMA, phase='collect', status='COMPLETE', binding=recorded,
        fits=0, loaded_adapter_state_sha256=runner.transfer.prior.PARENT_STATE,
        adapter_state_after=runner.transfer.prior.PARENT_STATE, frozen_base_unchanged=True, model_calls=12,
        lessons_sha256=runner.source.file_hash(directory / 'LESSONS.json')))
    write(original / 'train/TRAINING_ROWS.json', material)
    for name in ('MASKS.json', 'RECIPE.json', 'LOSSES.jsonl'):
        write(original / 'train' / name, {'archived_fixture': name})
    files = {path.name: runner.source.file_hash(path) for path in adapter.iterdir()}
    write(original / 'train/RESULT.json', dict(schema=runner.lesson.SCHEMA, phase='train', status='COMPLETE', binding=recorded,
        fits=1, updates=100, loaded_adapter_state_sha256=runner.transfer.prior.PARENT_STATE,
        adapter_state_after=runner.PARENT_STATE, frozen_base_unchanged=True,
        lessons_result_sha256=runner.source.file_hash(directory / 'RESULT.json'), adapter_files=files,
        training_files={name: runner.source.file_hash(original / 'train' / name)
                        for name in ('TRAINING_ROWS.json', 'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl')}))
    transfer_binding = dict(recorded_training_binding=recorded, trained_adapter_dir=str(adapter), trained_adapter_files=files,
        training_result_sha256=runner.source.file_hash(original / 'train/RESULT.json'),
        old_facts_sha256=runner.hop.document_sha256(sum(data['banks'], [])),
        base_files={path.name: runner.source.file_hash(path) for path in model.iterdir()})
    directory = original / 'after'
    generate, calls = captured(directory, actor)
    entries = []
    old_collection = data['lessons']['collection']
    store = runner.hop.exact_text_store(old_collection)
    for index, task in enumerate(runner.hop.build_tasks(old_collection['world'])):
        episode = runner.hop.run_episode(old_collection['world'], task,
            lambda messages: generate(messages, role='actor', condition='ON_OWN_TEXT', task_index=index, adapter_off=False),
            store.__getitem__, protocol='turnbound')
        entry = dict(condition='ON_OWN_TEXT', task_index=index, task=task, episode=episode,
            score=runner.hop.score_episode(old_collection['world'], task, episode), memory_origin='ACTUAL_OWN_EVENT_TEXT')
        write(directory / f'ON_OWN_TEXT_EPISODE_{index:02d}.json', entry)
        entries.append(entry)
    write(directory / 'RESULT.json', dict(schema=runner.lesson.SCHEMA, phase='after', status='COMPLETE', binding=recorded,
        fits=0, parent_present=False, loaded_adapter_state_sha256=runner.PARENT_STATE, adapter_state_after=runner.PARENT_STATE,
        training_result_sha256=transfer_binding['training_result_sha256'], frozen_base_unchanged=True,
        model_calls=len(calls), panels=dict(ON_OWN_TEXT=runner.panel(entries))))
    transfer_binding['after_result_sha256'] = runner.source.file_hash(directory / 'RESULT.json')
    directory = root / 'transfer/collect'
    generate, calls = captured(directory, exposed_child)
    collection = runner.hop.collect_world(world, generate)
    write(directory / 'WORLD.json', world)
    write(directory / 'COLLECTION.json', collection)
    write(directory / 'RESULT.json', dict(schema=runner.transfer.SCHEMA, phase='collect', arm='TRAINED', status='COMPLETE',
        binding=transfer_binding, fits=0, trainingAllowed=False, parent_present=False,
        loaded_adapter_state_sha256=runner.PARENT_STATE, adapter_state_after=runner.PARENT_STATE,
        frozen_base_unchanged=True, model_calls=len(calls), collection_sha256=runner.source.file_hash(directory / 'COLLECTION.json')))
    collection_sha = runner.source.file_hash(directory / 'RESULT.json')
    for arm in ('TRAINED', 'ORIGINAL'):
        directory = root / 'transfer' / arm
        directory.mkdir()
        generate, calls = captured(directory, actor)
        panels = runner.transfer.evaluate(world, collection, generate, directory)
        for name, value in (('WORLD.json', world), ('TASKS.json', runner.hop.build_tasks(world)), ('COLLECTION_SOURCE.json', collection)):
            write(directory / name, value)
        state = runner.PARENT_STATE if arm == 'TRAINED' else runner.transfer.prior.PARENT_STATE
        write(directory / 'RESULT.json', dict(schema=runner.transfer.SCHEMA, phase='readout', arm=arm, status='COMPLETE',
            binding=transfer_binding, fits=0, updates=0, trainingAllowed=False, parent_present=False, protocol='turnbound',
            conditions=list(runner.transfer.CONDITIONS), collection_result_sha256=collection_sha,
            shared_text_sha256=runner.hop.document_sha256(runner.hop.exact_text_store(collection)),
            loaded_adapter_state_sha256=state, adapter_state_after=state, frozen_base_unchanged=True,
            model_calls=len(calls), panels=panels))
    previous = dict(memory_rows=material['memory_rows'][:96], cue_rows=material['cue_rows'], lesson_rows=material['audit_rows'],
        old_bank=sum(data['banks'][:3], []), old_episodes=sum(data['episodes'][:3], []), held=data['held'])
    fresh = dict(bank=data['banks'][3], episodes=data['episodes'][3])
    arguments = dict(model_dir=str(model), expected_base_sha256='fixture-base', adapter_dir=str(adapter))
    stack.enter_context(patch.dict(os.environ, ENVIRONMENT))
    stack.enter_context(patch.object(runner.transfer, 'load_inputs', return_value=(arguments, transfer_binding, world)))
    stack.enter_context(patch.object(runner.transfer.prior.previous, 'load_parent', return_value=previous))
    stack.enter_context(patch.object(runner.transfer.prior.previous, 'read_collection', return_value=(fresh, material['memory_rows'][96:], 'fresh')))
    stack.enter_context(patch.object(runner.lesson, 'load_inputs', side_effect=AssertionError('must not recompute historical binding')))
    stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', side_effect=lambda parameters: next(iter(parameters.values())).state))
    tokenizer = Tokenizer()
    tokenizer.pad_token_id = 151643
    token_loader = stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', return_value=tokenizer))
    engines = []
    events = {fact['event']: micro._event(fact) for bank in data['banks'] for fact in bank}
    events.update(runner.hop.exact_text_store(collection))
    events.update(store)

    def factory(arguments, tokenizer, *, check):
        engine = FakeEngine(arguments, tokenizer, check, events)
        engines.append(engine)
        return engine

    engine_factory = stack.enter_context(patch.object(runner.source, 'Engine', side_effect=factory))
    return SimpleNamespace(engines=engines, factory=engine_factory, token_loader=token_loader, world=world,
                           collection=collection, binding=transfer_binding, previous=previous)


def arguments(root, phase):
    result = ['--phase', phase, '--output', str(root / phase), '--gpu-uuid', 'fake-gpu',
              '--lesson-root', str(root / 'lesson'), '--transfer-root', str(root / 'transfer')]
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root'):
        result += ['--' + name, str(root / name)]
    if phase in ('train', 'after'):
        result += ['--before', str(root / 'before')]
    if phase == 'after':
        result += ['--training', str(root / 'train')]
    return result


class Parameter:
    def __init__(self, state):
        self.state, self.grad, self.dtype, self.requires_grad = state, None, 'float32', False

    def requires_grad_(self, enabled):
        self.requires_grad = enabled


class Finite:
    def __init__(self, value=True):
        self.value = value

    def __bool__(self):
        return self.value

    def all(self):
        return self


class FakeEngine:
    def __init__(self, arguments, tokenizer, check, store):
        self.arguments, self.tokenizer, self.check, self.store = arguments, tokenizer, check, store
        state = json.loads((Path(arguments.adapter_dir) / 'adapter_config.json').read_text())['fixture_state']
        self.parameter, self.base = Parameter(state), Parameter('base')
        self.runtime, self.device = {'fixture': True}, 'no-device'
        self.steps, self.native_calls, self.base_checks = 0, 0, 0
        self.invalid = self.raise_native = self.fail_gradient = self.mutate_state = False
        self.mutate_file = None
        self.optimizers = []
        engine = self

        class Model:
            config = SimpleNamespace(use_cache=True)

            def named_parameters(self):
                return [('model.lora_A.weight', engine.parameter), ('base.weight', engine.base)]

            def gradient_checkpointing_enable(self, **kwargs):
                pass

            def enable_input_require_grads(self):
                pass

            def train(self):
                pass

            def __call__(self, **kwargs):
                return SimpleNamespace(loss=Loss())

            def save_pretrained(self, directory, **kwargs):
                write(directory / 'adapter_config.json', dict(r=8, fixture_state=engine.parameter.state))
                (directory / 'adapter_model.safetensors').write_text('fixture-updated-' + engine.parameter.state)

        class Loss:
            requires_grad = True

            def backward(self):
                engine.parameter.grad = None if engine.fail_gradient else object()

            def item(self):
                return 0.25

        class Optimizer:
            def __init__(self, parameters, **kwargs):
                engine.optimizers.append(dict(parameters=parameters, **kwargs))

            def zero_grad(self, **kwargs):
                engine.parameter.grad = None

            def step(self):
                engine.steps += 1
                engine.parameter.state = sha256(('saved-new-state-' + str(engine.steps)).encode()).hexdigest()

        self.model = Model()
        self.torch = SimpleNamespace(optim=SimpleNamespace(AdamW=Optimizer), float32='float32', long='long', bfloat16='bf16',
            manual_seed=lambda seed: setattr(engine, 'seed', seed), tensor=lambda value, **kwargs: value,
            autocast=lambda **kwargs: nullcontext(), isfinite=lambda value: Finite())

    def verify_base(self):
        self.base_checks += 1
        assert self.base.state == 'base' and self.base.requires_grad is False

    def generate(self, messages, *, max_new_tokens):
        assert max_new_tokens == 160
        self.native_calls += 1
        if self.mutate_state:
            self.parameter.state = 'd' * 64
        if self.mutate_file:
            self.mutate_file.write_text('changed readonly file')
        if self.raise_native:
            raise RuntimeError('captured native failure')
        if self.invalid:
            return dict(generation('not a command', messages), terminal=False)
        if messages[0]['content'] == runner.source.world.MEMORY_SYSTEM:
            address = re.search(r'READ EVENT (E_[A-Z2-7]{10})', messages[1]['content']).group(1)
            return generation(self.store.get(address, 'MISS'), messages)
        if messages[0]['content'] == runner.audit.SYSTEM:
            return generation('NONE', messages)
        return actor(messages)


class MemoryDriverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = material_fixture()

    def test_schedule_exact_groups_presentations_and_no_token_equality_claim(self):
        counts = Counter(index for update in range(1, 101) for index in runner.training_indexes(update))
        self.assertEqual(sum(counts.values()), 400)
        self.assertEqual([sum(counts[index] for index in range(start, end))
                          for start, end in ((0, 128), (128, 148), (148, 210), (210, 222), (222, 254))], [100, 26, 62, 12, 200])
        self.assertEqual([sum(counts[index] for index in range(222, 254) if (index - 222) % 4 == fact)
                          for fact in range(4)], [50] * 4)
        self.assertEqual(runner.training_indexes(1), (0, 128, 222, 223))
        self.assertEqual(runner.training_indexes(100), (99, 133, 228, 229))
        self.assertFalse(runner.recipe()['actual_token_equality_claim'])
        for update in (0, 101, True, 1.5):
            with self.assertRaises(ValueError):
                runner.training_indexes(update)

    def test_prepare_validates_actual_material_with_no_ml_and_no_efficacy_gate(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack, self.data)
            result = runner.main(arguments(root, 'prepare'))
            self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
            self.assertEqual((result['fits'], result['model_calls'], result['max_native_calls']), (0, 0, 0))
            self.assertEqual(result['binding']['baselines']['TRAINED']['panels']['OWN_TEXT']['correct'], 4)
            self.assertEqual(result['binding']['baselines']['ORIGINAL']['panels']['OWN_TEXT']['correct'], 4)
            self.assertEqual(len(runner.source.read(root / 'prepare/NEW_ROWS.json')), 32)
            state.factory.assert_not_called()
            state.token_loader.assert_not_called()
            with self.assertRaises(FileExistsError):
                runner.main(arguments(root, 'prepare'))

    def test_source_readouts_require_both_states_tasks_text_and_native_outputs(self):
        for flaw in ('state', 'task', 'text', 'native', 'failed', 'fit'):
            with self.subTest(flaw=flaw), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = setup(root, stack, self.data)
                directory = root / 'transfer/ORIGINAL'
                if flaw in ('state', 'fit'):
                    document = runner.source.read(directory / 'RESULT.json')
                    document['adapter_state_after' if flaw == 'state' else 'fits'] = runner.PARENT_STATE if flaw == 'state' else 1
                    write(directory / 'RESULT.json', document)
                elif flaw == 'task':
                    tasks = runner.source.read(directory / 'TASKS.json')
                    tasks.reverse()
                    write(directory / 'TASKS.json', tasks)
                elif flaw == 'text':
                    document = runner.source.read(directory / 'COLLECTION_SOURCE.json')
                    document['records'][0]['event']['raw'] += '\n'
                    write(directory / 'COLLECTION_SOURCE.json', document)
                elif flaw == 'native':
                    call = runner.source.read(directory / 'CALL_000.json')
                    call['response']['raw'] += '\n'
                    write(directory / 'CALL_000.json', call)
                else:
                    write(directory / 'FAILED.json', {})
                with self.assertRaises(ValueError):
                    runner.main(arguments(root, 'prepare'))
                state.factory.assert_not_called()

    def test_archived_material_hash_and_current_source_replay_both_required(self):
        for flaw in ('hash', 'current_source', 'native_trajectory'):
            with self.subTest(flaw=flaw), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = setup(root, stack, self.data)
                if flaw == 'hash':
                    material = runner.source.read(root / 'lesson/train/TRAINING_ROWS.json')
                    material['memory_rows'][0]['messages'][-1]['content'] += '\n'
                    write(root / 'lesson/train/TRAINING_ROWS.json', material)
                elif flaw == 'current_source':
                    state.previous['memory_rows'][0]['messages'][-1]['content'] += '\n'
                else:
                    call = runner.source.read(root / 'lesson/collect/CALL_000.json')
                    call['response']['raw'] += '\n'
                    write(root / 'lesson/collect/CALL_000.json', call)
                with self.assertRaises(ValueError):
                    runner.main(arguments(root, 'prepare'))
                state.factory.assert_not_called()

    def test_all_encoders_real_masks_no_parent_bytes_and_source_only_new_rows(self):
        inputs = dict(material=dict(deepcopy(self.data['material'])), collection=runner.hop.collect_world(
            runner.hop.build_world(runner.hop.TRANSFER_MASTER), exposed_child))
        inputs['material']['new_rows'] = runner.memory.compile_rows(inputs['collection'])
        tokenizer = Tokenizer()
        with patch.object(micro, '_check_bank', side_effect=AssertionError('disconnected validator forbidden')):
            encoded = runner.encode_material(inputs, tokenizer)
        self.assertEqual(len(encoded), 254)
        for row in encoded:
            self.assertLessEqual(len(row.input_ids), 2048)
            self.assertEqual(tuple(label for label in row.labels if label != -100), row.target_ids)
            self.assertEqual(row.labels[-1], -100)
            self.assertEqual(row.target_ids[-1], tokenizer.eos_token_id)
            self.assertNotIn('PARENT PROCEDURAL GUIDANCE', tokenizer.decode(row.input_ids))
        inputs['material']['new_rows'][0]['messages'][-1]['content'] += '\n'
        with self.assertRaises(ValueError):
            runner.encode_material(inputs, tokenizer)

    def test_before_train_after_phase_joins_saved_unknown_state_and_exact_caps(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack, self.data)
            before = runner.main(arguments(root, 'before'))
            self.assertEqual(before['panels']['PARAMETRIC']['correct'], 4)
            self.assertEqual(before['model_calls'], 48)
            trained = runner.main(arguments(root, 'train'))
            self.assertEqual((trained['fits'], trained['updates'], trained['model_calls']), (1, 100, 0))
            self.assertNotEqual(trained['adapter_state_after'], runner.PARENT_STATE)
            engine = state.engines[1]
            self.assertEqual((engine.steps, len(engine.optimizers), engine.seed), (100, 1, 0))
            self.assertEqual(engine.optimizers[0]['lr'], 3e-5)
            self.assertEqual(engine.optimizers[0]['parameters'], [engine.parameter])
            self.assertFalse(engine.base.requires_grad)
            self.assertEqual(trained['before_result_sha256'], runner.source.file_hash(root / 'before/RESULT.json'))
            losses = [json.loads(line) for line in (root / 'train/LOSSES.jsonl').read_text().splitlines()]
            self.assertEqual(len(losses), 100)
            self.assertEqual(sum(loss['active_label_count'] for loss in losses), trained['actual_supervised_tokens'])
            after = runner.main(arguments(root, 'after'))
            self.assertEqual(after['loaded_adapter_state_sha256'], trained['adapter_state_after'])
            self.assertEqual(after['adapter_state_after'], trained['adapter_state_after'])
            self.assertEqual(after['training_result_sha256'], runner.source.file_hash(root / 'train/RESULT.json'))
            self.assertEqual(after['model_calls'], 168)
            self.assertEqual(after['max_native_calls'], 168)
            self.assertEqual(after['role_calls'], dict(actor=96, memory=16, new_recall=8, old_recall=32, held_audit=16))
            self.assertEqual(set(after['panels']), set(runner.CONDITIONS))
            self.assertEqual(after['old_recall']['8']['denominator'], 16)
            self.assertEqual(after['held_audit']['overall']['denominator'], 16)
            self.assertEqual(after['taught_graph']['OWN_TEXT']['denominator'], 4)
            self.assertEqual(state.engines[2].optimizers, [])
            self.assertEqual(len(list((root / 'after').glob('*EPISODE*'))), 16)

    def test_before_proof_required_before_loading_training_model(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack, self.data)
            runner.main(arguments(root, 'before'))
            call = runner.source.read(root / 'before/CALL_000.json')
            call['response']['raw'] += '\n'
            write(root / 'before/CALL_000.json', call)
            state.factory.reset_mock()
            with self.assertRaises(ValueError):
                runner.main(arguments(root, 'train'))
            state.factory.assert_not_called()
            self.assertFalse((root / 'train/LOSSES.jsonl').exists())
        with self.assertRaisesRegex(ValueError, 'verified_before_required'):
            runner.train(None, {}, None)

    def test_missing_gradient_failure_preserves_partial_evidence_without_save(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack, self.data)
            runner.main(arguments(root, 'before'))
            factory = state.factory.side_effect

            def failed(*args, **kwargs):
                engine = factory(*args, **kwargs)
                engine.fail_gradient = True
                return engine

            state.factory.side_effect = failed
            with self.assertRaisesRegex(ValueError, 'invalid_memory_gradient'):
                runner.main(arguments(root, 'train'))
            self.assertTrue((root / 'train/FAILED.json').exists())
            self.assertTrue((root / 'train/LOSSES.jsonl').exists())
            self.assertFalse((root / 'train/adapter').exists())
            self.assertEqual(state.engines[-1].steps, 0)

    def test_after_failure_preserves_saved_write_and_never_refits(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack, self.data)
            runner.main(arguments(root, 'before'))
            trained = runner.main(arguments(root, 'train'))
            saved_result = runner.source.file_hash(root / 'train/RESULT.json')
            factory = state.factory.side_effect

            def failure(*args, **kwargs):
                engine = factory(*args, **kwargs)
                engine.raise_native = True
                return engine

            state.factory.side_effect = failure
            with self.assertRaisesRegex(ValueError, 'native_errors_retained'):
                runner.main(arguments(root, 'after'))
            self.assertEqual(state.engines[-1].parameter.state, trained['adapter_state_after'])
            self.assertEqual(state.engines[-1].optimizers, [])
            self.assertEqual(state.engines[1].steps, 100)
            self.assertEqual(runner.source.file_hash(root / 'train/RESULT.json'), saved_result)
            runner.transfer.verify_files(root / 'train/adapter', trained['adapter_files'])
            self.assertEqual(len(list((root / 'after').glob('*EPISODE*'))), 16)
            self.assertTrue((root / 'after/HELD_AUDIT.json').exists())
            with self.assertRaises(FileExistsError):
                runner.main(arguments(root, 'after'))
            self.assertEqual(len(state.engines), 3)

    def test_after_rejects_wrong_before_link_before_model_load(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack, self.data)
            runner.main(arguments(root, 'before'))
            trained = runner.main(arguments(root, 'train'))
            trained['before_result_sha256'] = '0' * 64
            write(root / 'train/RESULT.json', trained)
            state.factory.reset_mock()
            with self.assertRaisesRegex(ValueError, 'own_completed_memory_write_required'):
                runner.main(arguments(root, 'after'))
            state.factory.assert_not_called()

    def test_no_parametric_text_fallback_and_invalid_turns_retained(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack, self.data)
            factory = state.factory.side_effect

            def empty_memory(*args, **kwargs):
                engine = factory(*args, **kwargs)
                engine.store = {}
                return engine

            state.factory.side_effect = empty_memory
            before = runner.main(arguments(root, 'before'))
            for entry in before['panels']['PARAMETRIC']['episodes']:
                reads = [trace for trace in entry['episode']['traces'] if trace['kind'] == 'memory']
                self.assertTrue(reads)
                self.assertTrue(all(trace['response']['raw'] == 'MISS' for trace in reads))
            self.assertEqual(before['new_recall']['0']['correct'], 0)

    def test_call_cap_blocks_native_call_49(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack, self.data)

            def exceed(inputs, generate, output, phase):
                for unused in range(49):
                    generate(runner.memory_messages(inputs['collection']['records'][0]['edge']['event']), role='memory')

            with patch.object(runner, 'evaluate', side_effect=exceed), self.assertRaisesRegex(ValueError, 'memory_native_call_cap'):
                runner.main(arguments(root, 'before'))
            self.assertEqual(state.engines[0].native_calls, 48)
            failure = runner.source.read(root / 'before/FAILED.json')
            self.assertTrue(failure['cap_hit'])
            self.assertEqual(failure['model_calls'], 48)

    def test_readonly_state_file_and_native_failures_do_not_train(self):
        for flaw in ('state', 'file', 'native', 'invalid'):
            with self.subTest(flaw=flaw), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = setup(root, stack, self.data)
                factory = state.factory.side_effect

                def changed(*args, **kwargs):
                    engine = factory(*args, **kwargs)
                    engine.mutate_state = flaw == 'state'
                    engine.raise_native = flaw == 'native'
                    engine.invalid = flaw == 'invalid'
                    if flaw == 'file':
                        engine.mutate_file = root / 'lesson/train/adapter/adapter_model.safetensors'
                    return engine

                state.factory.side_effect = changed
                if flaw == 'invalid':
                    result = runner.main(arguments(root, 'before'))
                    self.assertEqual(result['status'], 'COMPLETE')
                    self.assertEqual(result['panels']['PARAMETRIC']['correct'], 0)
                else:
                    with self.assertRaises(ValueError):
                        runner.main(arguments(root, 'before'))
                    self.assertTrue((root / 'before/FAILED.json').exists())
                self.assertEqual(len(list((root / 'before').glob('*EPISODE*'))), 4)
                self.assertTrue((root / 'before/STATES.json').exists())
                self.assertEqual(state.engines[0].optimizers, [])

    def test_phase_arguments_reject_missing_before_or_training(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            for phase, flag in (('train', '--before'), ('after', '--before'), ('after', '--training')):
                args = arguments(root, phase)
                index = args.index(flag)
                del args[index:index + 2]
                with self.subTest(phase=phase, flag=flag), self.assertRaisesRegex(ValueError, 'memory_phase_arguments'):
                    runner.main(args)
            self.assertFalse((root / 'train').exists())


class GuardTests(unittest.TestCase):
    def test_archived_source_guard_aborts_with_stub_scanner_without_gpu_or_git(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / 'source'
            entry = source_dir / 'gpu/astra_event_two_hop_memory.py'
            entry.parent.mkdir(parents=True)
            entry.write_bytes(Path(runner.__file__).read_bytes())
            write(root / 'prepare/RESULT.json', dict(schema=runner.SCHEMA, phase='prepare',
                status='PREPARED_NO_MODEL', entry_sha256=runner.source.file_hash(entry)))
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
            guard = Path(runner.__file__).with_name('astra_event_two_hop_memory_guard.sh')
            environment = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ['PATH'])
            completed = subprocess.run(['bash', str(guard), str(root), str(source_dir), commit, '0', 'fake-gpu'],
                                       env=environment, capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, 1)
            self.assertTrue((root / 'launch/GUARD_ABORT.txt').exists())
            self.assertFalse((source_dir / '.git').exists())
            self.assertFalse((root / 'before').exists())
            self.assertNotIn('not a git repository', completed.stderr)

    def test_import_no_ml_and_guard_syntax_archive_source_and_bounds(self):
        script = '''
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_event_two_hop_memory
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        guard = Path(runner.__file__).with_name('astra_event_two_hop_memory_guard.sh')
        result = subprocess.run(['bash', '-n', str(guard)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = guard.read_text()
        for fragment in ('test "$#" -eq 5', '"$root/source_commit.txt"', 'CUDA_VISIBLE_DEVICES= python3',
                '"$index" "$uuid"', 'service_exceptions.json', 'time.time()+9300 < 1789980180-21600',
                '--kill-after=60', 'run_stage 1860 --phase before', 'run_stage 3600 --phase train',
                'run_stage 3600 --phase after', '--before "$root/before"', '--training "$root/train"',
                'deadline - $(date +%s) - 60', 'test ! -e "$root/train"', 'HF_HUB_OFFLINE=1'):
            self.assertIn(fragment, text)
        self.assertNotIn('git ', text)
        self.assertNotIn('--phase collect', text)
        self.assertLessEqual(1860 + 60 + 3600 + 60 + 3600 + 60, 9300)


if __name__ == '__main__':
    unittest.main()
