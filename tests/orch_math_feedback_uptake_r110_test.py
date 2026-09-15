import ast
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r110_broker as broker
from gpu import orch_math_feedback_uptake_r110_native as native
from gpu import orch_math_feedback_uptake_r110_run as runner
from organism_v6 import orch_math_feedback_uptake_r110 as policy
import orch_math_feedback_uptake_base_test as fixture


class R110Tests(unittest.TestCase):
    def setUp(self):
        data = ("Shared principles fixture: behavior addition, stopping and shifting; pure metacognition, no outcome trigger. " * 2).encode()
        import hashlib
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'principles.md'
            path.write_bytes(data)
            policy.bind_principles(path, hashlib.sha256(data).hexdigest())

    def test_exact_observable_cadences_and_caps(self):
        for index, expected in ((0, 768), (1, 288), (2, 103)):
            self.assertEqual(sum(policy.due(index, count) for count in range(1, 769)), expected)
            self.assertEqual(policy.PARENT_CAPS[index], expected)
        self.assertEqual([count for count in range(1, 769) if policy.due(2, count) and count % 8 != 7], [100, 200, 300, 400, 500, 600, 700])
        self.assertFalse(policy.due(1, 1))
        self.assertTrue(policy.due(1, 3))

    def test_no_unallocated_or_hidden_counter(self):
        for index, count in ((3, 1), (6, 1), (0, 0), (0, 769), (0, True)):
            with self.assertRaises(ValueError):
                policy.due(index, count)
        self.assertFalse(policy.budget(0)['hidden_cot_count'])

    def test_prospective_budgets_no_new_controls(self):
        self.assertEqual(sum(policy.budget(index)['native_calls'] for index in policy.DEVICES), 4608)
        self.assertEqual(sum(policy.budget(index)['parent_calls'] for index in policy.DEVICES), 1159)
        self.assertEqual(sum(policy.budget(index)['max_gpu_hours'] for index in policy.DEVICES), 24)
        self.assertEqual(policy.budget(0)['new_control_arms'], 0)
        self.assertEqual(runner.HARD - runner.NATIVE, 180)

    def test_fresh_96_cycle_cohorts_whole_pool_and_lane_disjointness(self):
        ids, questions = {'PRIOR'}, {'a' * 64}
        for index in policy.DEVICES:
            cohort = policy.make_cohort(index, ids, questions)
            self.assertEqual(len(cohort['train']), 96)
            self.assertEqual(len(cohort['held']), 96)
            for group in cohort['train'] + cohort['held']:
                for task in group:
                    self.assertNotIn(task['id'], ids)
                    self.assertNotIn(task['question_sha256'], questions)
                    ids.add(task['id'])
                    questions.add(task['question_sha256'])
        self.assertEqual(len(ids), 2881)

    def payload(self):
        task = fixture.tasks()[0]
        record = policy.base.history.record(task, 'experience', dict(fixture.response(), raw='FINAL: 999999'))
        return policy.parent_payload(0, 1, 1, task, [record])

    def test_actual_negative_outcome_not_relabelled(self):
        payload = self.payload()
        self.assertFalse(payload['episodes'][0]['records'][0]['outcome']['correct'])
        self.assertEqual(payload['episodes'][0]['records'][0]['outcome']['status'], 'INCORRECT')
        self.assertIn('Outcomes are background', payload['instruction'])
        policy.validate_parent_payload(payload)

    def test_parent_blind_unknown_keys_or_oracle(self):
        original = self.payload()
        for mutation in ('held', 'gold', 'extra', 'outcome', 'cadence'):
            payload = copy.deepcopy(original)
            if mutation == 'held':
                payload['episodes'][0]['task_id'] = 'SECRET_HELD_1'
            elif mutation == 'gold':
                payload['episodes'][0]['records'][0]['outcome']['reference_answer'] = '7'
            elif mutation == 'extra':
                payload['sealed_scores'] = [1]
            elif mutation == 'outcome':
                payload['episodes'][0]['records'][0]['outcome']['correct'] = True
            else:
                payload['cadence'] = 'hidden_thoughts'
            with self.assertRaises(ValueError):
                policy.validate_parent_payload(payload)

    def test_reflection_guard_scope_and_parent_free_tests(self):
        held = fixture.tasks('HELD')[0]
        self.assertEqual(policy.messages(held, purpose='held'), policy.base.messages(held, purpose='held'))
        with self.assertRaises(ValueError):
            policy.messages(held, purpose='held', teacher='secret')
        original = policy.messages(fixture.tasks()[0], teacher='check your perception')
        self.assertIn('PRIVATE PARENT GUIDANCE', original[0]['content'])
        self.assertIn(policy.previous.REFLECTION, policy.messages(fixture.tasks()[0], purpose='revision')[0]['content'])

    def test_plan_not_clipped_or_task_substituted(self):
        plan = dict(guidance='Notice conflict.', rationale='Perception.', order=['X_TRAIN_0'], episode_guidance={'X_TRAIN_0': 'Check it.'})
        self.assertIn('Check it.', policy.validate_plan(plan, 'X_TRAIN_0'))
        with self.assertRaises(ValueError):
            policy.validate_plan(plan, 'OTHER_TRAIN_0')
        plan['guidance'] = 'word ' * 201
        with self.assertRaises(ValueError):
            policy.validate_plan(plan, 'X_TRAIN_0')

    def test_no_fixed_check_template_and_mandatory_dialogue_on_sparse_lane(self):
        messages = policy.messages(fixture.tasks()[0], purpose='check')
        self.assertNotIn('Investigate the live uncertainty', json.dumps(messages))
        self.assertIn('Do not add a check', messages[-1]['content'])
        self.assertTrue(all(policy.due(2, 8 * cycle + 7) for cycle in range(96)))
        self.assertEqual(policy.DISTILLATION_CAPS, {0: 2048, 1: 4096, 2: 4096})

    def test_shared_principles_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'wrong.md'
            path.write_text('wrong principles')
            with self.assertRaises(ValueError):
                policy.bind_principles(path, 'a' * 64)

    def test_resident_actual_loop_one_load_no_readmission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lane = root / 'campaign_node3_style0'
            lane.mkdir()
            runner.common.write(lane / 'ACTIVATION.json', dict(native_deadline_unix=9999999999))
            loaded = []
            class Engine:
                def __init__(self, *args, **kwargs):
                    loaded.append(self)
            def phase(lane, index, cycle, name, factory, validate):
                self.assertIs(factory('/fixture', None, 'fixture', lambda label: None), loaded[0])
                output = lane / f'cycle{cycle}' / name
                runner.common.write(output / 'COMPLETE.json', dict(status='COMPLETE', process=['boot', 1, 1]))
                runner.common.write(output / 'AFTER.json', dict(actual_mounted_base_verified=True, process=['boot', 1, 1]))
                for position in range(8):
                    runner.common.write(output / f'CALL_{position}.json', {})
            with patch.object(runner, 'validate'), patch.object(policy, 'CYCLES', 3), \
                patch.object(runner.machinery.previous.direct, 'Engine', Engine), \
                patch.object(runner.machinery.previous.response_contract, 'engine_class', side_effect=lambda engine: engine), \
                patch.object(runner.driver.reflection, 'engine_class', side_effect=lambda engine: engine), \
                patch.object(runner.driver, 'run', side_effect=phase) as run, \
                patch.object(runner.driver.reuse.driver.seam.native, 'process_identity', return_value=('boot', 1, 1)), \
                patch.object(runner, 'statistics'), patch.object(runner, 'scan', side_effect=AssertionError('no_between_cycle_scan')):
                runner.resident(root, 0)
                self.assertEqual(run.call_count, 6)
                self.assertEqual(len(loaded), 1)
                self.assertEqual(runner.common.read(lane / 'RESIDENT_TERMINAL.json')['loads'], 1)

    def test_only_strong_actual_model(self):
        envelope = fixture.envelope()
        envelope['model'] = 'unverified-smaller'
        with self.assertRaises(AssertionError):
            native.provider.parse(envelope, [task['id'] for task in fixture.tasks()])

    def test_no_training_or_new_model_mechanism(self):
        tree = ast.parse(Path(native.__file__).read_text())
        attributes = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(attributes & {'backward', 'step', 'save_pretrained', 'load_state_dict', 'from_pretrained', 'get_peft_model'})
        self.assertIsNone(policy.budget(0)['adapter'])

    def test_broker_node_only_transport(self):
        store = broker.previous.Store(Path('/repo'), Path('/node'))
        with patch.object(broker.previous.subprocess, 'run', return_value=SimpleNamespace(stdout='', returncode=0)) as call:
            store.shell('read metadata')
            self.assertIn('ovx2_ssh.sh', str(call.call_args))

    def test_native_three_cycles_sequential_no_held_to_parent_and_carry(self):
        for index in policy.DEVICES:
            with self.subTest(index=index), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                lane = root / f'campaign_node3_style{index}'
                lane.mkdir()
                (lane / 'r110_parent_queue').mkdir()
                write, read = native.common.write, native.common.read
                write(lane / 'COHORT.json', dict(train=[fixture.tasks()] * 3, held=[fixture.tasks('HELD') * 4] * 3))
                write(lane / 'READY.json', dict(cohort_sha256=native.common.sha(lane / 'COHORT.json')))
                write(lane / 'ACTIVATION.json', dict(native_deadline_unix=9999999999))
                process = ['boot', 1, 1]
                class Fake(fixture.FakeEngine):
                    def __init__(self, model_dir, tokenizer, device, check):
                        super().__init__(SimpleNamespace(adapter_dir=None, phase='readout'), tokenizer, check)
                def deliver(unused):
                    for path in (lane / 'r110_parent_queue').glob('*.request.json'):
                        destination = path.with_name(path.name.replace('.request.', '.response.'))
                        if destination.exists():
                            continue
                        request = read(path)
                        policy.validate_parent_payload(request['payload'])
                        task_id = request['payload']['episodes'][0]['task_id']
                        plan = dict(guidance='Check sourced evidence.', order=[task_id], episode_guidance={task_id: 'Notice a conflict.'}, rationale='Perception.')
                        envelope = fixture.envelope()
                        envelope['output'][0]['content'][0]['text'] = json.dumps(plan)
                        directory = root / 'parent_transcripts' / lane.name / request['id']
                        directory.mkdir(parents=True)
                        write(directory / 'RAW_RESPONSE.json', envelope)
                        write(directory / 'PLAN.json', plan)
                        write(destination, dict(status='COMPLETE', plan=plan, request_sha256=native.common.sha(path),
                            archive=dict(remote_root=str(directory), files={name: native.common.sha(directory / name) for name in ('RAW_RESPONSE.json', 'PLAN.json')})))
                original_read = Path.read_bytes
                with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=policy.DEVICES[index]), \
                    patch.object(Path, 'read_bytes', autospec=True, side_effect=lambda path: ('CUDA_VISIBLE_DEVICES=' + policy.DEVICES[index]).encode() if str(path) == '/proc/self/environ' else original_read(path)), \
                    patch.object(native.reuse.driver.seam.portable, 'verify_base_files', return_value=dict(expected_base_sha256=policy.base.BASE_SHA)), \
                    patch.object(native.reuse.driver.seam.native.source.native, 'load_local_tokenizer', return_value=fixture.Tokenizer()), \
                    patch.object(native.reuse.driver.seam.native, 'process_identity', side_effect=lambda: tuple(process)), \
                    patch.object(native.reflection, 'engine_class', side_effect=lambda engine: engine), \
                    patch.object(native.time, 'sleep', side_effect=deliver):
                    for cycle in range(1, 4):
                        for phase in ('experience', 'readout'):
                            self.assertEqual(process[1], 1)
                            native.run(lane, index, cycle, phase, Fake, lambda root: dict(bundle='/fixture', model_dir='/fixture'))
                            self.assertEqual(read(lane / f'cycle{cycle}' / phase / 'COMPLETE.json')['status'], 'COMPLETE')
                        calls = [read(path) for path in sorted((lane / f'cycle{cycle}' / 'experience').glob('CALL_*.json'))]
                        self.assertEqual([call['purpose'] for call in calls], ['experience', 'check', 'revision'] * 2 + ['revision', 'revision'])
                        for path in (lane / f'cycle{cycle}' / 'readout').glob('CALL_*.json'):
                            self.assertFalse(read(path)['parent_present'])
                            self.assertNotIn('PRIVATE PARENT GUIDANCE', json.dumps(read(path)['messages']))
                    self.assertEqual(len(list(lane.glob('cycle*/*/CALL_*.json'))), 48)
                    self.assertEqual(read(lane / 'cycle3/experience/STATE.json')['completed_train_segments'], 24)
                    self.assertEqual(len(list((lane / 'r110_parent_queue').glob('*.request.json'))), {0: 24, 1: 9, 2: 3}[index])
                    self.assertFalse(list(lane.rglob('optimizer*')))
                    self.assertTrue(read(lane / 'cycle2/experience/CONTEXT_CONDITION.json')['own_train_memory'])


if __name__ == '__main__':
    unittest.main()
