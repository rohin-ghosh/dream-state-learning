import ast
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_base_broker as broker
from gpu import orch_math_feedback_uptake_base_native as native
from gpu import orch_math_feedback_uptake_base_run as runner
from organism_v6 import orch_math_feedback_uptake_base as policy


def tasks(split='TRAIN'):
    return [dict(id=f'FIXTURE_{split}_{index}', split=split, question=f'Find {index} plus 8.', gold=str(index + 8)) for index in range(2)]


def response():
    return dict(raw='I should use the supplied observation, not invent one. FINAL: 8',
        token_ids=[11, 12, 1], terminal=True, truncated=False, input_truncated=False)


def plan():
    return dict(guidance='Stay with the relevant uncertainty.', order=[task['id'] for task in tasks()],
        episode_guidance={task['id']: 'Consider what the environment supports.' for task in tasks()}, rationale='Help the child allocate effort.')


def envelope():
    return dict(model=policy.STRONG, status='completed', usage=dict(output_tokens=25), output=[
        dict(type='message', content=[dict(type='output_text', text=json.dumps(plan()))])])


class Tokenizer:
    def encode(self, text, **unused):
        return list(text.encode())

    def apply_chat_template(self, messages, **unused):
        return list(json.dumps(messages).encode())


class FakeEngine:
    def __init__(self, options, tokenizer, check):
        if options.adapter_dir is not None or options.phase != 'readout':
            raise AssertionError('not_base')
        self.model = SimpleNamespace(named_parameters=lambda: [('base.weight', SimpleNamespace(requires_grad=False))])
        self.runtime = dict(fixture=True)
        self.tokenizer = tokenizer

    def generate(self, messages, max_new_tokens):
        return dict(response(), messages=messages)

    def verify_base(self):
        return None


class BaseParentingTest(unittest.TestCase):
    def test_genuine_base_not_disabled_or_frozen_learned_adapter(self):
        options = policy.options('/fixture/model')
        self.assertIsNone(options.adapter_dir)
        self.assertEqual(options.phase, 'readout')
        self.assertEqual(options.expected_base_sha256, policy.BASE_SHA)
        model = SimpleNamespace(named_parameters=lambda: [('base.weight', SimpleNamespace(requires_grad=False))])
        self.assertEqual(policy.verify_no_adapter(model), 1)
        for bad in (SimpleNamespace(peft_config={}, named_parameters=model.named_parameters),
            SimpleNamespace(named_parameters=lambda: [('lora_A.weight', SimpleNamespace(requires_grad=False))]),
            SimpleNamespace(named_parameters=lambda: [('base.weight', SimpleNamespace(requires_grad=True))])):
            with self.assertRaises(ValueError):
                policy.verify_no_adapter(bad)

    def test_no_optimizer_or_weight_write_calls(self):
        tree = ast.parse(Path(native.__file__).read_text())
        forbidden = {'backward', 'step', 'save_pretrained', 'load_training', 'get_peft_model', 'load_state_dict', 'encode_row'}
        calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & forbidden)
        self.assertEqual(policy.budget()['training_updates'], 0)
        self.assertIsNone(policy.budget()['optimizer'])
        self.assertIsNone(policy.budget()['adapter'])

    def test_bounded_two_episode_interactive_cycles_not_controls(self):
        self.assertEqual((policy.NATIVE_CAP, policy.PARENT_CAP), (28, 4))
        self.assertEqual(2 * (2 * 3 + 8), policy.NATIVE_CAP)
        self.assertEqual(policy.budget()['aggregate_native_cap'], 2064 + 28)
        self.assertEqual(policy.budget()['aggregate_parent_cap'], 36 + 4)
        self.assertEqual(policy.budget()['gpus'], 1)
        self.assertEqual(policy.CAPS, dict(experience=4096, check=4096, revision=2048, held=8192))

    def test_parent_original_and_readout_visibility(self):
        with self.assertRaises(ValueError):
            policy.messages(tasks()[0], teacher='parent')
        with self.assertRaises(ValueError):
            policy.messages(tasks('HELD')[0], purpose='held', teacher='parent')
        with self.assertRaises(ValueError):
            policy.messages(tasks('HELD')[0], purpose='experience')
        self.assertNotIn('PRIVATE PARENT', json.dumps(policy.messages(tasks('HELD')[0], purpose='held')))

    def test_two_round_parent_payload_and_no_hidden_score(self):
        records = {task['id']: [policy.history.record(task, 'experience', response())] for task in tasks()}
        first = policy.parent_payload(tasks(), records, 1, 1)
        self.assertEqual(first['turn_generation_budget'], 4096)
        self.assertNotIn('gold', json.dumps(first))
        for task in tasks():
            records[task['id']].append(policy.history.record(task, 'check', response()))
        second = policy.parent_payload(tasks(), records, 1, 2)
        self.assertEqual(second['turn_generation_budget'], 2048)
        self.assertEqual(len(second['episodes'][0]['records']), 2)
        bad = copy.deepcopy(second)
        bad['episodes'][0]['sealed_score'] = 0
        with self.assertRaises(ValueError):
            policy.validate_parent_payload(bad)

    def test_no_branch_quota_or_surprise_sft(self):
        self.assertNotIn('be surprised', policy.WAKE.lower())
        self.assertIn('Do not demand a branch count', policy.PARENT_INSTRUCTION)
        self.assertIn('Avoid prescribing a specific solution strategy', policy.PARENT_INSTRUCTION)

    def test_actual_strong_envelope_and_exact_plan(self):
        self.assertEqual(policy.verified_plan(envelope(), tasks()), plan())
        for field, value in (('model', 'weak'), ('status', 'incomplete'), ('usage', {})):
            with self.assertRaises(ValueError):
                policy.verified_plan(dict(envelope(), **{field: value}), tasks())

    def test_broker_context_isolated_and_restored(self):
        previous = broker.transport.parent.policy.validate_parent_payload
        instructions = broker.transport.parent.INSTRUCTIONS
        with broker.parent_context():
            self.assertIs(broker.transport.parent.policy.validate_parent_payload, policy.validate_parent_payload)
        self.assertIs(broker.transport.parent.policy.validate_parent_payload, previous)
        self.assertEqual(broker.transport.parent.INSTRUCTIONS, instructions)
        self.assertNotEqual(broker.QUEUE, 'parent_queue')

    def test_no_silent_truncation_and_teacher_budget(self):
        self.assertEqual(policy.generation_cap('held', 100), 8192)
        self.assertEqual(policy.generation_cap('check', 14000, 100), 2384)
        for purpose, prompt, teacher in (('check', 16384, 0), ('check', 100, 1025)):
            with self.assertRaises(ValueError):
                policy.generation_cap(purpose, prompt, teacher)

    def test_complete_native_control_flow_cpu_double_no_model_or_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            original = Path(temporary).resolve()
            root = original / runner.CAMPAIGN
            root.mkdir()
            (root / broker.QUEUE).mkdir()
            write, read = native.common.write, native.common.read
            write(root / 'READY.json', dict(source_files={}, files={}))
            write(root / 'ACTIVATION.json', dict(native_deadline_unix=9999999999))
            write(root / 'COHORT.json', dict(train=[tasks(), tasks()], held=[tasks('HELD') * 4, tasks('HELD') * 4]))
            process = ['fixture_boot', 1, 10]
            def deliver(unused):
                for path in (root / broker.QUEUE).glob('*.request.json'):
                    destination = path.with_name(path.name.replace('.request.', '.response.'))
                    if destination.exists():
                        continue
                    directory = original / 'parent_transcripts' / root.name / path.stem
                    directory.mkdir(parents=True)
                    write(directory / 'RAW_RESPONSE.json', envelope())
                    write(directory / 'PLAN.json', plan())
                    files = {item.name: native.common.sha(item) for item in directory.iterdir()}
                    write(destination, dict(status='COMPLETE', plan=plan(), request_sha256=native.common.sha(path),
                        archive=dict(remote_root=str(directory), files=files)))
            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=policy.UUID), \
                patch.object(Path, 'read_bytes', autospec=True, side_effect=lambda path: ('CUDA_VISIBLE_DEVICES=' + policy.UUID).encode() if str(path) == '/proc/self/environ' else original_read_bytes(path)), \
                patch.object(native.common, 'validate', return_value=dict(bundle='/fixture', model_dir='/fixture')), \
                patch.object(native.seam.portable, 'verify_base_files', return_value=dict(expected_base_sha256=policy.BASE_SHA)), \
                patch.object(native.seam.native.source.native, 'load_local_tokenizer', return_value=Tokenizer()), \
                patch.object(native.seam, 'Engine', FakeEngine), \
                patch.object(native.seam.native, 'process_identity', side_effect=lambda: tuple(process)), \
                patch.object(native.time, 'sleep', side_effect=deliver):
                for cycle in (1, 2):
                    for phase in ('experience', 'readout'):
                        process[1] += 1
                        native.run(root, cycle, phase)
                        output = root / f'cycle{cycle}' / phase
                        self.assertEqual(read(output / 'COMPLETE.json')['status'], 'COMPLETE')
                        self.assertIsNone(read(output / 'AFTER.json')['adapter'])
                        self.assertFalse(list(output.glob('optimizer*')))
                        self.assertFalse((output / 'ROWS.json').exists())
                self.assertEqual(len(list(root.glob('cycle*/*/CALL_*.json'))), 28)
                self.assertEqual(len(list((root / broker.QUEUE).glob('*.request.json'))), 4)
                carry = read(root / 'cycle1/experience/CARRY.json')
                next_call = read(sorted((root / 'cycle2/experience').glob('CALL_*.json'))[0])
                self.assertIn(carry['trace'], json.dumps(next_call['messages']))


original_read_bytes = Path.read_bytes


if __name__ == '__main__':
    unittest.main()
