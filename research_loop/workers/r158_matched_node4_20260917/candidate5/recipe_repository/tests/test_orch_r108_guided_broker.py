"""Offline broker tests: synthetic transport, local fake node, no API calls."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu import orch_r108_guided_broker as broker


PLAN = dict(intervention_class='perception', guidance='Which observation deserves another look?',
    rationale='Support attention without supplying a solution.')
TASK = dict(id='example_TRAIN_1', question='A box has 2 pens; 3 are added. How many pens?')
TRANSPORT_OBSERVATIONS = []


def payload(cycle=1, episode=1):
    return dict(schema=broker.policy.SCHEMA, cycle=cycle, episode=episode, task=deepcopy(TASK),
        child_state=dict(adapter_sha256='a' * 64, call_sha256='b' * 64,
            trace='I counted the first pens.', outcome='INCORRECT'),
        previous_own_reflections=[], instruction=broker.policy.PARENT_INSTRUCTION,
        parenting=deepcopy(broker.policy.PARENTING))


def request(cycle=1, episode=1):
    value = payload(cycle, episode)
    return dict(id=f'cycle{cycle}_episode{episode}', payload=value,
        payload_sha256=broker.policy.digest(value), task=deepcopy(TASK))


def raw_response():
    return dict(model=broker.policy.STRONG, status='completed', error=None,
        output=[dict(type='message', role='assistant', content=[dict(type='output_text',
            text=json.dumps(PLAN))])], usage=dict(input_tokens=100, output_tokens=40, total_tokens=140))


def parse_strong(envelope):
    raise AssertionError('legacy_parser_must_not_be_called')


def synthetic_transport(prompt, directory, deadline, instruction='old instruction'):
    TRANSPORT_OBSERVATIONS.append(dict(prompt=prompt, instruction=instruction, deadline=deadline))
    (directory / 'stdout.json').write_text(json.dumps(raw_response()))
    return parse_strong(raw_response())


class LocalStore:
    def shell(self, command, check=True):
        return subprocess.run(['bash', '-c', command], check=check, text=True,
            capture_output=True, timeout=5)

    def copy(self, source, destination):
        source = Path(str(source).removeprefix('NODE:'))
        destination = Path(str(destination).removeprefix('NODE:'))
        shutil.copyfile(source, destination)

    def exists(self, path):
        return path.is_file()


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='orch_r108_broker_test_', dir='/tmp')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.campaign = self.root / 'native'
        self.campaign.mkdir()
        (self.campaign / 'parent_queue').mkdir()
        (self.campaign / 'parent_broker_r108').mkdir()
        self.buffer = self.root / 'buffer'
        self.buffer.mkdir()
        broker.write(self.campaign / 'READY.json', dict(synthetic=True))
        broker.write(self.campaign / 'PUBLICATION.json', dict(synthetic=True))
        self.allocation = dict(schema=broker.ALLOCATION_SCHEMA, campaign=str(self.campaign),
            ready_sha256=broker.sha(self.campaign / 'READY.json'), source_files=broker.LOADED_PINS,
            tasks_by_request={identifier: deepcopy(TASK) for identifier in broker.IDENTIFIERS},
            deadline_unix=time.time() + 600, dispatch_cutoff_unix=time.time() + 400,
            max_parent_calls=4, attempts_per_request=1, max_output_tokens=4096)
        broker.write(self.campaign / 'PARENT_BROKER_ALLOCATION.json', self.allocation)
        self.allocation_hash = broker.sha(self.campaign / 'PARENT_BROKER_ALLOCATION.json')
        self.store = LocalStore()
        self.calls = []

    def put_request(self, cycle=1, episode=1, value=None):
        value = value if value is not None else request(cycle, episode)
        path = self.campaign / 'parent_queue' / f'cycle{cycle}_episode{episode}.request.json'
        broker.write(path, value)
        return path

    def actor(self, value, directory, deadline):
        self.calls.append(value['id'])
        broker.write(directory / 'DISPATCH.json', dict(attempts=1, synthetic=True))
        broker.write(directory / 'RAW_RESPONSE.json', raw_response())
        return PLAN, broker.policy.STRONG, raw_response()['usage']

    def process(self, identifier='cycle1_episode1', actor=None):
        return broker.process(self.store, self.campaign, identifier, self.buffer, self.allocation,
            self.allocation_hash, actor=actor or self.actor)

    def test_valid_allocation_and_exact_envelope(self):
        broker.validate_allocation(self.allocation, self.campaign, time.time())
        broker.validate_request(request(), 'cycle1_episode1', self.allocation)

    def test_fixed_call_output_and_attempt_bounds(self):
        for key, value in [('max_parent_calls', 5), ('attempts_per_request', 2),
                ('attempts_per_request', True), ('max_output_tokens', 8192)]:
            with self.subTest(key=key, value=value):
                allocation = dict(self.allocation, **{key: value})
                with self.assertRaisesRegex(ValueError, 'fixed_call_bounds'):
                    broker.validate_allocation(allocation, self.campaign, time.time())

    def test_deadlines_no_reset_or_nan(self):
        for cutoff in (time.time() - 1, self.allocation['deadline_unix'], float('nan')):
            with self.subTest(cutoff=cutoff), self.assertRaises(ValueError):
                broker.validate_allocation(dict(self.allocation, dispatch_cutoff_unix=cutoff),
                    self.campaign, time.time())

    def test_incomplete_source_pins_rejected(self):
        with self.assertRaisesRegex(ValueError, 'loaded_source_allocation_binding'):
            broker.validate_allocation(dict(self.allocation, source_files={}), self.campaign, time.time())

    def test_task_and_id_bindings(self):
        mutations = [dict(id='cycle1_episode2'), dict(task=dict(TASK, question='Different')),
            dict(payload_sha256='c' * 64), dict(extra='forbidden')]
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                broker.validate_request(dict(request(), **mutation), 'cycle1_episode1', self.allocation)

    def test_unregistered_train_task_rejected(self):
        allocation = deepcopy(self.allocation)
        allocation['tasks_by_request']['cycle1_episode1']['id'] = 'different_TRAIN_1'
        with self.assertRaisesRegex(ValueError, 'registered_train_task_join'):
            broker.validate_request(request(), 'cycle1_episode1', allocation)

    def test_forbidden_visibility_and_style(self):
        for text in ('sample_HELD_1', 'sealed_score', 'reference_answer', '/tmp/private', 'api_key'):
            with self.subTest(text=text):
                value = request()
                value['payload']['child_state']['trace'] = text
                value['payload_sha256'] = broker.policy.digest(value['payload'])
                with self.assertRaisesRegex(ValueError, 'parent_visibility_violation'):
                    broker.validate_request(value, 'cycle1_episode1', self.allocation)
        value = request()
        value['payload']['parenting']['tone'] = 'hostile'
        with self.assertRaisesRegex(ValueError, 'parent_instruction_policy_binding'):
            broker.validate_request(value, 'cycle1_episode1', self.allocation)

    def test_bool_cycle_and_extra_payload_key_rejected(self):
        for mutation in (dict(cycle=True), dict(teacher_target='forbidden')):
            value = request()
            value['payload'].update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                broker.validate_request(value, 'cycle1_episode1', self.allocation)

    def test_strict_json_duplicate_and_nonfinite(self):
        for text in ('{"guidance":1,"guidance":2}', '{"value":NaN}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                broker.loads(text)

    def test_actual_model_and_completion(self):
        for mutation in (dict(model='requested-model-is-not-proof'), dict(status='incomplete'),
                dict(error={'message': 'failed'}), dict(incomplete_details={'reason': 'max_tokens'})):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                broker.parse_response(dict(raw_response(), **mutation), TASK)

    def test_tools_and_refusals_are_not_plans(self):
        for output in ([dict(type='function_call')], [dict(type='message', role='assistant',
                content=[dict(type='refusal', refusal='no')])]):
            with self.subTest(output=output), self.assertRaises(ValueError):
                broker.parse_response(dict(raw_response(), output=output), TASK)

    def test_usage_and_output_caps(self):
        for usage in ({}, dict(input_tokens=1, output_tokens=4097, total_tokens=4098),
                dict(input_tokens=1, output_tokens=True, total_tokens=2)):
            with self.subTest(usage=usage), self.assertRaises(ValueError):
                broker.parse_response(dict(raw_response(), usage=usage), TASK)

    def test_exact_plan_enum_no_old_feedback_schema(self):
        for plan in (dict(speak=True, message='hello', rationale='why'),
                dict(PLAN, intervention_class='unknown'), dict(PLAN, guidance=''),
                dict(PLAN, extra='forbidden')):
            value = raw_response()
            value['output'][0]['content'][0]['text'] = json.dumps(plan)
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                broker.parse_response(value, TASK)

    def test_provider_clone_does_not_change_legacy_parser(self):
        TRANSPORT_OBSERVATIONS.clear()
        old_parser = broker.provider.parse_strong
        with patch.object(broker.provider, 'strong', synthetic_transport):
            plan, model, usage = broker.evaluate(request(), self.buffer, time.time() + 600)
        self.assertEqual(plan, PLAN)
        self.assertEqual(model, broker.policy.STRONG)
        self.assertEqual(usage['output_tokens'], 40)
        self.assertIs(broker.provider.parse_strong, old_parser)
        self.assertEqual(len(TRANSPORT_OBSERVATIONS), 1)
        observed = TRANSPORT_OBSERVATIONS[0]
        self.assertEqual(json.loads(observed['prompt']), request()['payload'])
        self.assertEqual(observed['instruction'], broker.policy.PARENT_INSTRUCTION)
        self.assertTrue((self.buffer / 'RAW_RESPONSE.json').exists())
        self.assertFalse((self.buffer / 'stdout.json').exists())

    def test_evaluate_preserves_raw_when_parser_fails(self):
        with patch.object(broker.provider, 'strong', synthetic_transport), patch.object(
                broker, 'parse_response', side_effect=ValueError('synthetic_validation_failure')):
            with self.assertRaisesRegex(ValueError, 'synthetic_validation_failure'):
                broker.evaluate(request(), self.buffer, time.time() + 600)
        self.assertEqual(broker.loads((self.buffer / 'RAW_RESPONSE.json').read_text()), raw_response())
        self.assertEqual(broker.signal.getitimer(broker.signal.ITIMER_REAL), (0.0, 0.0))

    def test_evaluate_never_dispatches_without_margin(self):
        with patch.object(broker.provider, 'strong', synthetic_transport):
            with self.assertRaisesRegex(ValueError, 'provider_dispatch_margin'):
                broker.evaluate(request(), self.buffer, time.time() + 20)
        self.assertEqual(list(self.buffer.iterdir()), [])

    def test_success_receipt_matches_actual_raw_and_callback(self):
        self.put_request()
        self.assertEqual(self.process(), 'COMPLETE')
        result = broker.loads((self.campaign / 'parent_queue/cycle1_episode1.response.json').read_text())
        self.assertEqual(result['actual_model'], broker.policy.STRONG)
        self.assertEqual(result['plan'], PLAN)
        receipt = result['transcript_receipt']
        self.assertIs(receipt['node_only'], True)
        self.assertIs(receipt['all_verified'], True)
        self.assertEqual(receipt['payload_sha256'], broker.policy.digest(request()['payload']))
        self.assertEqual(receipt['plan_sha256'], broker.policy.digest(PLAN))
        self.assertIn('RAW_RESPONSE.json', receipt['files'])
        for name, digest in receipt['files'].items():
            self.assertEqual(broker.sha(Path(receipt['remote_root']) / name), digest)
        self.assertEqual(list(self.buffer.iterdir()), [])

    def test_four_once_only_calls_and_no_fifth_id(self):
        for cycle in (1, 2):
            for episode in (1, 2):
                self.put_request(cycle, episode)
                self.assertEqual(self.process(f'cycle{cycle}_episode{episode}'), 'COMPLETE')
        for identifier in broker.IDENTIFIERS:
            self.assertEqual(self.process(identifier), 'EXISTING')
        self.assertEqual(self.calls, list(broker.IDENTIFIERS))
        with self.assertRaisesRegex(ValueError, 'bounded_request_id'):
            self.process('cycle3_episode1')

    def test_later_episode_waits_for_prior_response(self):
        self.put_request(1, 2)
        self.assertEqual(self.process('cycle1_episode2'), 'WAITING')
        self.assertEqual(self.calls, [])

    def test_existing_claim_prevents_restart_retry(self):
        self.put_request()
        (self.campaign / 'parent_broker_r108/cycle1_episode1.claim').mkdir()
        self.assertEqual(self.process(), 'CLAIMED_NO_RETRY')
        self.assertEqual(self.calls, [])

    def test_invalid_request_fails_without_dispatch_and_remains_charged(self):
        self.put_request(value=dict(request(), payload_sha256='d' * 64))
        self.assertEqual(self.process(), 'FAILED')
        self.assertEqual(self.calls, [])
        self.assertTrue((self.campaign / 'parent_broker_r108/cycle1_episode1.claim').is_dir())
        self.assertEqual(self.process(), 'EXISTING')
        self.put_request(1, 2)
        with self.assertRaisesRegex(ValueError, 'previous_episode_failed_no_next_parent'):
            self.process('cycle1_episode2')

    def test_capture_not_actor_return_controls_success(self):
        self.put_request()
        def dishonest_actor(value, directory, deadline):
            self.actor(value, directory, deadline)
            broker.write(directory / 'RAW_RESPONSE.json', dict(raw_response(), model='wrong'))
            return PLAN, broker.policy.STRONG, raw_response()['usage']
        self.assertEqual(self.process(actor=dishonest_actor), 'FAILED')
        result = broker.loads((self.campaign / 'parent_queue/cycle1_episode1.response.json').read_text())
        self.assertIsNone(result['actual_model'])
        self.assertEqual(result['error']['code'], 'actual_strong_model_identity')
        self.assertTrue((Path(result['transcript_receipt']['remote_root']) / 'RAW_RESPONSE.json').exists())
        self.assertNotIn('plan_sha256', result['transcript_receipt'])

    def test_failed_provider_single_attempt_and_no_raw_in_error(self):
        self.put_request()
        def failure(value, directory, deadline):
            self.calls.append(value['id'])
            raise RuntimeError('sensitive response body must not enter error metadata')
        self.assertEqual(self.process(actor=failure), 'FAILED')
        self.assertEqual(self.process(actor=failure), 'EXISTING')
        result = broker.loads((self.campaign / 'parent_queue/cycle1_episode1.response.json').read_text())
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(result['error']['code'], 'captured_failure_no_retry')

    def test_archive_hash_failure_preserves_buffer_no_success(self):
        self.put_request()
        real_copy = self.store.copy
        def corrupt_copy(source, destination):
            real_copy(source, destination)
            if str(destination).endswith('/RAW_RESPONSE.json'):
                Path(str(destination).removeprefix('NODE:')).write_text('corruption')
        with patch.object(self.store, 'copy', side_effect=corrupt_copy):
            with self.assertRaisesRegex(ValueError, 'node_archive_hash_mismatch'):
                self.process()
        self.assertTrue((self.buffer / 'cycle1_episode1/RAW_RESPONSE.json').exists())
        self.assertFalse((self.campaign / 'parent_queue/cycle1_episode1.response.json').exists())
        self.assertEqual(len(self.calls), 1)

    def test_response_transfer_failure_preserves_raw(self):
        self.put_request()
        with patch.object(broker, 'publish_response', side_effect=ValueError('response_transfer_hash')):
            with self.assertRaisesRegex(ValueError, 'response_transfer_hash'):
                self.process()
        self.assertTrue((self.buffer / 'cycle1_episode1/RAW_RESPONSE.json').exists())
        self.assertTrue((self.buffer / 'result/response.json').exists())

    def test_allocation_change_or_missing_blocks_dispatch(self):
        self.put_request()
        (self.campaign / 'PARENT_BROKER_ALLOCATION.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'immutable_allocation_hash'):
            self.process()
        self.assertEqual(self.calls, [])

    def test_ready_change_blocks_dispatch(self):
        self.put_request()
        (self.campaign / 'READY.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'immutable_ready_hash'):
            self.process()
        self.assertEqual(self.calls, [])

    def test_missing_publication_blocks_dispatch(self):
        self.put_request()
        (self.campaign / 'PUBLICATION.json').unlink()
        with self.assertRaisesRegex(ValueError, 'published_allocation_required'):
            self.process()
        self.assertEqual(self.calls, [])

    def test_oversized_request_is_not_downloaded(self):
        path = self.put_request()
        path.write_text('x' * (1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, 'bounded_request_packet'):
            self.process()
        self.assertFalse((self.buffer / 'cycle1_episode1/REQUEST.json').exists())
        self.assertEqual(self.calls, [])

    def test_native_cycle_accepts_real_broker_response_shape(self):
        from gpu import orch_r108_guided_native as native
        tasks = [dict(TASK, id=f'example_TRAIN_{index}', split='TRAIN', gold='5') for index in (1, 2)]
        for episode, task in enumerate(tasks, 1):
            self.allocation['tasks_by_request'][f'cycle1_episode{episode}'] = {
                key: task[key] for key in ('id', 'question')}
        broker.write(self.campaign / 'PARENT_BROKER_ALLOCATION.json', self.allocation)
        self.allocation_hash = broker.sha(self.campaign / 'PARENT_BROKER_ALLOCATION.json')
        events, saved = [], {}
        def generate(task, purpose, messages):
            events.append((task['id'], purpose))
            return dict(task_id=task['id'], path=f"{task['id']}_{purpose}.json", sha256='f' * 64,
                response=dict(raw='I count the pens.\nFINAL: 5', token_ids=[9, 10],
                    messages=messages, prompt_tokens=10, terminal=True, truncated=False,
                    input_truncated=False))
        def parent(value, task):
            events.append((task['id'], 'parent'))
            identifier = f"cycle{value['cycle']}_episode{value['episode']}"
            self.put_request(value['cycle'], value['episode'], dict(id=identifier, payload=value,
                payload_sha256=broker.policy.digest(value), task=value['task']))
            self.assertEqual(self.process(identifier), 'COMPLETE')
            return broker.loads((self.campaign / 'parent_queue' / (identifier + '.response.json')).read_text())
        result = native.collect_cycle(tasks, 1, 'a' * 64, [], generate, parent, saved.__setitem__)
        self.assertEqual(events, [(task['id'], purpose) for task in tasks
            for purpose in ('experience', 'parent', 'check', 'revision')])
        self.assertEqual(result['parent_calls'], 2)
        self.assertEqual(len(result['rows']), 6)

    def test_source_change_blocks_dispatch(self):
        self.put_request()
        with patch.dict(broker.LOADED_PINS, {'gpu/orch_r108_guided_broker.py': 'e' * 64}):
            with self.assertRaisesRegex(ValueError, 'runtime_source_changed'):
                self.process()
        self.assertEqual(self.calls, [])

    def test_expired_cutoff_never_claims_or_calls(self):
        self.put_request()
        self.allocation['dispatch_cutoff_unix'] = time.time() - 1
        self.assertEqual(self.process(), 'CUTOFF')
        self.assertEqual(self.calls, [])
        self.assertEqual(list((self.campaign / 'parent_broker_r108').iterdir()), [])

    def test_busy_buffer_blocks_new_claim(self):
        self.put_request()
        (self.buffer / 'recover-me').write_text('preserved')
        with self.assertRaisesRegex(ValueError, 'one_bounded_local_buffer'):
            self.process()
        self.assertEqual(self.calls, [])

    def test_native_archive_never_overwrites_conflicting_bytes(self):
        (self.buffer / 'RAW_RESPONSE.json').write_text('first')
        destination = self.campaign / 'archive'
        broker.native_archive(self.store, self.buffer, destination)
        (self.buffer / 'RAW_RESPONSE.json').write_text('second')
        with self.assertRaisesRegex(ValueError, 'node_archive_hash_mismatch'):
            broker.native_archive(self.store, self.buffer, destination)
        self.assertEqual((destination / 'RAW_RESPONSE.json').read_text(), 'first')

    def test_worktree_execution_is_forbidden(self):
        worktree = self.root / 'fake_worktree'
        worktree.mkdir()
        (worktree / '.git').mkdir()
        with patch.object(broker, 'ROOT', worktree), patch.dict(
                broker.os.environ, {'CUDA_VISIBLE_DEVICES': ''}), patch.object(
                broker.transport, 'Store') as store:
            with self.assertRaisesRegex(ValueError, 'immutable_runtime_outside_worktree_required'):
                broker.serve(worktree, self.campaign, self.allocation_hash)
            store.assert_not_called()


if __name__ == '__main__':
    unittest.main()
