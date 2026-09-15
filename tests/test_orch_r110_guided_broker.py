"""Synthetic local-node transport tests; no provider or SSH calls."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r110_guided_broker as broker
from tests.test_orch_r110_guided import TASKS, PLAN, episode, with_initial


def request(cycle=1, episode_number=1):
    if episode_number == 'presleep':
        payload = broker.policy.presleep_payload(TASKS, with_initial(), 'a' * 64, cycle, [])
        identifier = f'cycle{cycle}_presleep'
    else:
        task = TASKS[episode_number - 1]
        payload = broker.policy.parent_payload(task, episode(task)[0], 'a' * 64, cycle, episode_number)
        identifier = f'cycle{cycle}_episode{episode_number}'
    return dict(id=identifier, payload=payload, payload_sha256=broker.policy.digest(payload), task=payload['task'])


def envelope():
    return dict(model=broker.policy.STRONG, status='completed', error=None,
        output=[dict(type='message', role='assistant', content=[dict(type='output_text',
            text=json.dumps(PLAN))])], usage=dict(input_tokens=2000, output_tokens=40, total_tokens=2040))


TRANSPORT_CALLS = []


def parse_strong(value):
    raise AssertionError('legacy_parser_should_not_be_called')


def synthetic_transport(prompt, directory, deadline, instruction='legacy'):
    TRANSPORT_CALLS.append(dict(prompt=json.loads(prompt), instruction=instruction))
    (directory / 'stdout.json').write_text(json.dumps(envelope()))
    return parse_strong(envelope())


class LocalStore:
    def shell(self, command, check=True):
        return subprocess.run(['bash', '-c', command], check=check, text=True,
            capture_output=True, timeout=5)

    def copy(self, source, destination):
        shutil.copyfile(str(source).removeprefix('NODE:'), str(destination).removeprefix('NODE:'))

    def exists(self, path):
        return path.is_file()


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='orch_r110_broker_test_', dir='/tmp')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.campaign = self.root / 'native'
        self.campaign.mkdir()
        (self.campaign / 'parent_queue').mkdir()
        (self.campaign / 'parent_broker_r110').mkdir()
        self.buffer = self.root / 'buffer'
        self.buffer.mkdir()
        self.now = broker.policy.WALL_END_UNIX - 3600
        clock = patch.object(broker.time, 'time', return_value=self.now)
        clock.start()
        self.addCleanup(clock.stop)
        broker.write(self.campaign / 'READY.json', dict(synthetic=True))
        broker.write(self.campaign / 'PUBLICATION.json', dict(synthetic=True))
        tasks = {}
        for cycle in range(1, broker.policy.CYCLES + 1):
            for episode_number in (1, 2, 'presleep'):
                index = 0 if episode_number == 1 else 1
                identifier = f'cycle{cycle}_presleep' if episode_number == 'presleep' else f'cycle{cycle}_episode{episode_number}'
                tasks[identifier] = {key: TASKS[index][key] for key in ('id', 'question')}
        self.allocation = dict(schema=broker.ALLOCATION_SCHEMA, campaign=str(self.campaign),
            ready_sha256=broker.sha(self.campaign / 'READY.json'), source_files=broker.LOADED_PINS,
            tasks_by_request=tasks, started_unix=self.now - 60, deadline_unix=self.now + 600,
            dispatch_cutoff_unix=self.now + 400, max_parent_calls=broker.policy.PARENT_CAP,
            attempts_per_request=1, max_output_tokens=broker.OUTPUT_CAP)
        broker.write(self.campaign / 'PARENT_BROKER_ALLOCATION.json', self.allocation)
        self.allocation_sha = broker.sha(self.campaign / 'PARENT_BROKER_ALLOCATION.json')
        self.store = LocalStore()
        self.calls = []

    def actor(self, value, directory, deadline):
        self.calls.append(value['id'])
        broker.write(directory / 'DISPATCH.json', dict(attempts=1, synthetic=True))
        broker.write(directory / 'RAW_RESPONSE.json', envelope())
        return PLAN, broker.policy.STRONG, envelope()['usage']

    def put_request(self, cycle=1, episode_number=1, value=None):
        value = request(cycle, episode_number) if value is None else value
        path = self.campaign / 'parent_queue' / (value['id'] + '.request.json')
        broker.write(path, value)
        return value

    def process(self, identifier='cycle1_episode1', actor=None):
        return broker.process(self.store, self.campaign, identifier, self.buffer,
            self.allocation, self.allocation_sha, actor=actor or self.actor)

    def test_allocation_exact_current_caps(self):
        broker.validate_allocation(self.allocation, self.campaign, self.now)
        self.assertEqual(len(broker.IDENTIFIERS), broker.policy.PARENT_CAP)
        self.assertEqual(broker.IDENTIFIERS[-1], f'cycle{broker.policy.CYCLES}_presleep')

    def test_all_registered_identifiers_validate_dynamically(self):
        for cycle in range(1, broker.policy.CYCLES + 1):
            for episode_number in (1, 2, 'presleep'):
                value = request(cycle, episode_number)
                broker.validate_request(value, value['id'], self.allocation)

    def test_old_budgets_and_extra_attempts_rejected(self):
        for key, value in (('max_parent_calls', 4), ('max_parent_calls', 48),
                ('attempts_per_request', 2), ('max_output_tokens', broker.OUTPUT_CAP + 1)):
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, 'fixed_call_bounds'):
                broker.validate_allocation(dict(self.allocation, **{key: value}), self.campaign, self.now)

    def test_original_absolute_deadline_cannot_extend(self):
        allocation = dict(self.allocation, deadline_unix=broker.policy.WALL_END_UNIX + 1)
        with self.assertRaisesRegex(ValueError, 'fixed_eight_hour_window'):
            broker.validate_allocation(allocation, self.campaign, self.now)

    def test_eight_hour_elapsed_cap_cannot_extend(self):
        allocation = dict(self.allocation, started_unix=self.now - broker.policy.WALL_SECONDS)
        with self.assertRaisesRegex(ValueError, 'fixed_eight_hour_window'):
            broker.validate_allocation(allocation, self.campaign, self.now)

    def test_started_unix_required_no_implicit_reset(self):
        allocation = dict(self.allocation)
        del allocation['started_unix']
        with self.assertRaisesRegex(ValueError, 'allocation_schema'):
            broker.validate_allocation(allocation, self.campaign, self.now)

    def test_nan_and_late_cutoff_rejected(self):
        for value in (float('nan'), self.allocation['deadline_unix']):
            with self.subTest(value=value), self.assertRaises(ValueError):
                broker.validate_allocation(dict(self.allocation, dispatch_cutoff_unix=value), self.campaign, self.now)

    def test_principles_file_in_source_pins(self):
        self.assertEqual(broker.LOADED_PINS[broker.policy.PRINCIPLES_RELATIVE], broker.policy.PRINCIPLES_SHA256)

    def test_missing_source_pins_rejected(self):
        with self.assertRaisesRegex(ValueError, 'loaded_source_allocation_binding'):
            broker.validate_allocation(dict(self.allocation, source_files={}), self.campaign, self.now)

    def test_presleep_anchor_must_match_second_task(self):
        allocation = deepcopy(self.allocation)
        allocation['tasks_by_request']['cycle1_presleep'] = allocation['tasks_by_request']['cycle1_episode1']
        with self.assertRaisesRegex(ValueError, 'registered_presleep_last_task_anchor'):
            broker.validate_allocation(allocation, self.campaign, self.now)

    def test_presleep_both_tasks_bind_to_allocation(self):
        value = request(1, 'presleep')
        context = json.loads(value['payload']['child_state']['trace'])
        context['episodes'][0]['task']['id'] = 'other_TRAIN_999'
        value['payload']['child_state']['trace'] = json.dumps(context)
        value['payload_sha256'] = broker.policy.digest(value['payload'])
        with self.assertRaisesRegex(ValueError, 'registered_presleep_episode_context'):
            broker.validate_request(value, value['id'], self.allocation)

    def test_request_id_hash_and_task_mismatch_rejected(self):
        for mutation in (dict(id='cycle1_episode2'), dict(payload_sha256='f' * 64),
                dict(task=dict(id='other_TRAIN_999', question='other'))):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                broker.validate_request(dict(request(), **mutation), 'cycle1_episode1', self.allocation)

    def test_actual_model_completion_tools_and_usage_checked(self):
        for mutation in (dict(model='wrong'), dict(status='incomplete'), dict(error={'message': 'failed'}),
                dict(output=[dict(type='function_call')]), dict(usage={})):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                broker.parse_response(dict(envelope(), **mutation), TASKS[0])

    def test_json_duplicate_keys_and_nonfinite_rejected(self):
        for raw in ('{"key":1,"key":2}', '{"value":NaN}'):
            with self.assertRaises(ValueError):
                broker.loads(raw)

    def test_presleep_provider_uses_presleep_instruction_and_actual_capture(self):
        TRANSPORT_CALLS.clear()
        value = request(1, 'presleep')
        old_parser = broker.provider.parse_strong
        with patch.object(broker.provider, 'strong', synthetic_transport):
            plan, model, usage = broker.evaluate(value, self.buffer, self.allocation['deadline_unix'])
        self.assertEqual(TRANSPORT_CALLS[0]['instruction'], broker.policy.PRESLEEP_PARENT_INSTRUCTION)
        self.assertEqual(TRANSPORT_CALLS[0]['prompt'], value['payload'])
        self.assertEqual(plan, PLAN)
        self.assertEqual(model, broker.policy.STRONG)
        self.assertIs(broker.provider.parse_strong, old_parser)
        self.assertTrue((self.buffer / 'RAW_RESPONSE.json').exists())

    def test_failed_parse_preserves_raw_and_restores_timer(self):
        with patch.object(broker.provider, 'strong', synthetic_transport), patch.object(
                broker, 'parse_response', side_effect=ValueError('synthetic_parse_failure')):
            with self.assertRaisesRegex(ValueError, 'synthetic_parse_failure'):
                broker.evaluate(request(), self.buffer, self.allocation['deadline_unix'])
        self.assertTrue((self.buffer / 'RAW_RESPONSE.json').exists())
        self.assertEqual(broker.signal.getitimer(broker.signal.ITIMER_REAL), (0.0, 0.0))

    def test_three_parent_order_actual_receipts_and_no_repeat(self):
        for episode_number in (1, 2, 'presleep'):
            value = self.put_request(1, episode_number)
            self.assertEqual(self.process(value['id']), 'COMPLETE')
            self.assertEqual(self.process(value['id']), 'EXISTING')
            result = broker.loads((self.campaign / 'parent_queue' / (value['id'] + '.response.json')).read_text())
            receipt = result['transcript_receipt']
            self.assertEqual(receipt['payload_sha256'], value['payload_sha256'])
            self.assertEqual(receipt['plan_sha256'], broker.policy.digest(PLAN))
            self.assertEqual(result['actual_model'], broker.policy.STRONG)
            self.assertTrue(receipt['node_only'] and receipt['all_verified'])
            for name, digest in receipt['files'].items():
                self.assertEqual(broker.sha(Path(receipt['remote_root']) / name), digest)
        self.assertEqual(self.calls, list(broker.IDENTIFIERS[:3]))
        self.assertEqual(list(self.buffer.iterdir()), [])

    def test_next_cycle_waits_for_presleep_receipt(self):
        self.put_request(2, 1)
        self.assertEqual(self.process('cycle2_episode1'), 'WAITING')
        self.assertEqual(self.calls, [])

    def test_claim_survives_restart_without_redispatch(self):
        self.put_request()
        (self.campaign / 'parent_broker_r110/cycle1_episode1.claim').mkdir()
        self.assertEqual(self.process(), 'CLAIMED_NO_RETRY')
        self.assertEqual(self.calls, [])

    def test_failed_attempt_never_retried_or_followed_by_new_parent(self):
        self.put_request()
        def failure(value, directory, deadline):
            self.calls.append(value['id'])
            raise ValueError('synthetic_provider_failure')
        self.assertEqual(self.process(actor=failure), 'FAILED')
        self.assertEqual(self.process(actor=failure), 'EXISTING')
        self.put_request(1, 2)
        with self.assertRaisesRegex(ValueError, 'previous_episode_failed_no_next_parent'):
            self.process('cycle1_episode2')
        self.assertEqual(len(self.calls), 1)

    def test_actual_capture_not_actor_label_controls_acceptance(self):
        self.put_request()
        def wrong(value, directory, deadline):
            self.actor(value, directory, deadline)
            broker.write(directory / 'RAW_RESPONSE.json', dict(envelope(), model='wrong'))
            return PLAN, broker.policy.STRONG, envelope()['usage']
        self.assertEqual(self.process(actor=wrong), 'FAILED')

    def test_archive_failure_preserves_local_raw_and_claim(self):
        self.put_request()
        real_copy = self.store.copy
        def corrupt(source, destination):
            real_copy(source, destination)
            if str(destination).endswith('/RAW_RESPONSE.json'):
                Path(str(destination).removeprefix('NODE:')).write_text('corrupt')
        with patch.object(self.store, 'copy', side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, 'node_archive_hash_mismatch'):
                self.process()
        self.assertTrue((self.buffer / 'cycle1_episode1/RAW_RESPONSE.json').exists())
        self.assertTrue((self.campaign / 'parent_broker_r110/cycle1_episode1.claim').is_dir())
        self.assertFalse((self.campaign / 'parent_queue/cycle1_episode1.response.json').exists())

    def test_response_failure_preserves_local_raw(self):
        self.put_request()
        with patch.object(broker, 'publish_response', side_effect=ValueError('response_transfer_hash')):
            with self.assertRaisesRegex(ValueError, 'response_transfer_hash'):
                self.process()
        self.assertTrue((self.buffer / 'cycle1_episode1/RAW_RESPONSE.json').exists())

    def test_changed_allocation_blocks_dispatch(self):
        self.put_request()
        (self.campaign / 'PARENT_BROKER_ALLOCATION.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'immutable_allocation_hash'):
            self.process()
        self.assertEqual(self.calls, [])

    def test_cutoff_no_new_claim(self):
        self.put_request()
        self.allocation['dispatch_cutoff_unix'] = self.now
        self.assertEqual(self.process(), 'CUTOFF')
        self.assertEqual(self.calls, [])

    def test_worktree_guard_is_fixture_owned_no_transport(self):
        worktree = self.root / 'fake_worktree'
        worktree.mkdir()
        (worktree / '.git').mkdir()
        with patch.object(broker, 'ROOT', worktree), patch.dict(broker.os.environ, {'CUDA_VISIBLE_DEVICES': ''}), patch.object(broker.transport, 'Store') as store:
            with self.assertRaisesRegex(ValueError, 'immutable_runtime_outside_worktree_required'):
                broker.serve(worktree, self.campaign, self.allocation_sha)
            store.assert_not_called()

    def test_empty_queue_poll_checks_only_first_identifier(self):
        with patch.object(broker, 'process', return_value='WAITING') as process:
            position, state = broker.poll_requests(None, None, None, None, None, 0)
        self.assertEqual((position, state), (0, 'WAITING'))
        self.assertEqual(process.call_count, 1)
        self.assertEqual(process.call_args.args[2], broker.IDENTIFIERS[0])

    def test_poll_cursor_does_not_rescan_completed_prefix(self):
        with patch.object(broker, 'process', side_effect=['COMPLETE', 'EXISTING', 'WAITING']) as process:
            position, state = broker.poll_requests(None, None, None, None, None, 0)
        self.assertEqual((position, state), (2, 'WAITING'))
        self.assertEqual(process.call_count, 3)
        with patch.object(broker, 'process', return_value='WAITING') as process:
            next_position, state = broker.poll_requests(None, None, None, None, None, position)
        self.assertEqual(next_position, position)
        self.assertEqual(process.call_count, 1)
        self.assertEqual(process.call_args.args[2], broker.IDENTIFIERS[position])

    def test_claim_failed_cutoff_stop_poll_without_later_calls(self):
        for state in ('CLAIMED_NO_RETRY', 'FAILED', 'CUTOFF'):
            with self.subTest(state=state), patch.object(broker, 'process', return_value=state) as process:
                position, observed = broker.poll_requests(None, None, None, None, None, 4)
                self.assertEqual((position, observed), (4, state))
                self.assertEqual(process.call_count, 1)

    def test_all_completed_ceiling_does_not_start_another_cycle(self):
        with patch.object(broker, 'process', return_value='COMPLETE') as process:
            position, state = broker.poll_requests(None, None, None, None, None, 0)
        self.assertEqual(position, broker.policy.PARENT_CAP)
        self.assertEqual(process.call_count, broker.policy.PARENT_CAP)
        with patch.object(broker, 'process') as process:
            self.assertEqual(broker.poll_requests(None, None, None, None, None, position)[0], position)
            process.assert_not_called()


if __name__ == '__main__':
    unittest.main()
