import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_math_feedback_uptake as driver
from gpu import orch_math_feedback_uptake_prepare as prepare
from gpu import orch_math_pipeline_l2_r104_native as native_seam
from organism_v6 import orch_math_feedback_uptake as policy


def tasks():
    return [dict(id='FIXTURE_TRAIN_0', split='TRAIN', question='Calculate 31 times 21.', gold='651'),
        dict(id='FIXTURE_TRAIN_1', split='TRAIN', question='Calculate 2 times 4.', gold='8')]


def response(raw='I kept my initial conclusion. FINAL: 684'):
    return dict(raw=raw, token_ids=[11, 12], terminal=True, truncated=False, input_truncated=False)


class Tokenizer:
    eos_token = '\x01'
    eos_token_id = 1
    all_special_ids = [1]

    def encode(self, text, add_special_tokens=False, truncation=False):
        return [ord(character) for character in text]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False, return_dict=False):
        text = ''.join(message['role'] + ':' + message['content'] + self.eos_token + '\n' for message in messages)
        if add_generation_prompt:
            text += 'assistant:'
        return self.encode(text) if tokenize else text


def plan():
    return dict(guidance='Examine the recorded history.', order=[task['id'] for task in tasks()],
        episode_guidance={task['id']: 'Recompute the multiplication and let a conflicting check stop the conclusion.' for task in tasks()},
        rationale='Test actual use of feedback without certifying reasoning.')


def parent_finish(cycle):
    action = cycle.reserve()
    result = plan()
    receipt = dict(node_only=True, all_verified=True, request_sha256=policy.digest(action), plan_sha256=policy.digest(result))
    cycle.finish_parent(result, policy.STRONG, receipt)
    return action


def drive_to_sleep(cycle):
    for purpose in policy.PURPOSES:
        for unused in range(2):
            action = cycle.reserve()
            if action['purpose'] != purpose:
                raise AssertionError('fixture_order')
            cycle.finish_child(response())
        if purpose != 'revision':
            parent_finish(cycle)
    return cycle.rows()


class FeedbackUptakeTest(unittest.TestCase):
    def test_two_rounds_are_actual_sequential_requests(self):
        cycle = driver.Cycle(tasks(), 1)
        self.assertEqual(cycle.next_action()['purpose'], 'experience')
        cycle.reserve()
        with self.assertRaises(ValueError):
            cycle.reserve()
        cycle.finish_child(response())
        self.assertEqual(cycle.next_action()['purpose'], 'experience')
        cycle.reserve()
        cycle.finish_child(response())
        first = parent_finish(cycle)
        self.assertEqual(first['payload']['round'], 1)
        for unused in range(2):
            action = cycle.reserve()
            self.assertEqual(action['purpose'], 'check')
            self.assertIn(plan()['episode_guidance'][action['task_id']], json.dumps(action['messages']))
            cycle.finish_child(response())
        second = parent_finish(cycle)
        self.assertEqual(second['payload']['round'], 2)
        self.assertEqual([item['purpose'] for item in second['payload']['episodes'][0]['records']], ['experience', 'check'])
        self.assertIn('684', second['payload']['episodes'][0]['records'][1]['trace'])
        self.assertEqual(cycle.next_action()['purpose'], 'revision')

    def test_all_wrong_originals_checks_reflections_retained_and_trained(self):
        cycle = driver.Cycle(tasks(), 1)
        rows = drive_to_sleep(cycle)
        self.assertEqual(len(rows), 6)
        self.assertEqual(sum(row['own_reflection'] for row in rows), 2)
        self.assertTrue(all(row['outcome'] == 'INCORRECT' for row in rows))
        self.assertTrue(all('NEGATIVE EXAMPLES' in row['student_prefix'][0]['content'] for row in rows))
        self.assertTrue(all(row['target'] == response()['raw'] for row in rows))
        self.assertTrue(all(row['semantic_admission'] == 'NOT_USED' for row in rows))
        cycle.sleep_complete({row['source_record_sha256']: 55 for row in rows}, True, True)
        self.assertEqual(cycle.next_action(), dict(kind='FRESH_PARENT_FREE_READOUT', cycle=1, held=8, retention=0))

    def test_correct_revision_does_not_relabel_failed_history(self):
        task = tasks()[0]
        history = [policy.record(task, purpose, response('FINAL: 651' if purpose == 'revision' else 'FINAL: 684')) for purpose in policy.PURPOSES]
        rows = policy.sleep_rows(task, history, [[], []])
        self.assertEqual([row['outcome'] for row in rows], ['INCORRECT', 'INCORRECT', 'CORRECT'])
        self.assertTrue(all(row['original_outcome'] == 'INCORRECT' for row in rows))
        self.assertIn('reasoning and reflection remain unverified', rows[-1]['student_prefix'][0]['content'])

    def test_outcome_cannot_be_relabelled(self):
        task = tasks()[0]
        history = [policy.record(task, purpose, response()) for purpose in policy.PURPOSES]
        history[0]['outcome'] = dict(status='CORRECT', correct=True)
        with self.assertRaisesRegex(ValueError, 'source_record_mismatch'):
            policy.sleep_rows(task, history, [[], []])

    def test_wrong_task_source_rejected(self):
        history = [policy.record(tasks()[0], purpose, response()) for purpose in policy.PURPOSES]
        with self.assertRaisesRegex(ValueError, 'source_task_mismatch'):
            policy.sleep_rows(tasks()[1], history, [[], []])

    def test_missing_original_preserved_no_invented_target(self):
        cycle = driver.Cycle(tasks(), 1)
        cycle.reserve()
        cycle.finish_child(error=dict(type='NativeFailure'))
        cycle.reserve()
        cycle.finish_child(response())
        for unused in range(2):
            parent_finish(cycle)
            for position in range(2):
                cycle.reserve()
                cycle.finish_child(response())
        self.assertEqual(len(cycle.rows()), 5)
        self.assertEqual(cycle.snapshot()['records']['FIXTURE_TRAIN_0'][0]['outcome']['status'], 'NO_RESPONSE')

    def test_missing_check_blocks_write_not_record_retention(self):
        task = tasks()[0]
        history = [policy.record(task, 'experience', response()),
            policy.record(task, 'check', error=dict(type='Timeout')),
            policy.record(task, 'revision', response())]
        with self.assertRaisesRegex(ValueError, 'actual_check_and_reflection_required'):
            policy.sleep_rows(task, history, [[], []])
        self.assertEqual(len(history), 3)

    def test_teacher_copy_stops_write_not_quality_drops(self):
        task = tasks()[0]
        teacher = plan()['episode_guidance'][task['id']]
        history = [policy.record(task, purpose, response(('' if purpose == 'experience' else teacher) + ' FINAL: 684')) for purpose in policy.PURPOSES]
        with self.assertRaisesRegex(ValueError, 'teacher_text_in_target'):
            policy.sleep_rows(task, history, [[teacher], []])

    def test_parent_quoting_earlier_child_does_not_erase_child_provenance(self):
        task = tasks()[0]
        utterance = 'My earlier computation was performed this way and I obtained 684. FINAL: 684'
        history = [policy.record(task, purpose, response(utterance)) for purpose in policy.PURPOSES]
        rows = policy.sleep_rows(task, history, [[utterance], [utterance]])
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row['target'] == utterance for row in rows))

    def test_second_parent_cannot_retroactively_taint_prior_check(self):
        task = tasks()[0]
        history = [policy.record(task, purpose, response('A real child check before round two. FINAL: 684' if purpose != 'experience' else 'FINAL: 684')) for purpose in policy.PURPOSES]
        rows = policy.sleep_rows(task, history, [[], [history[1]['response']['raw']]])
        self.assertEqual(len(rows), 3)

    def test_prefix_has_no_parent_lesson_or_supervised_teacher(self):
        cycle = driver.Cycle(tasks(), 1)
        for row in drive_to_sleep(cycle):
            self.assertFalse(row['teacher_in_prefix'])
            self.assertNotIn(plan()['guidance'], json.dumps(row['student_prefix']))
            self.assertEqual(row['objective'], 'outcome_conditioned_historical_SFT_not_unlikelihood')

    def test_existing_native_encoder_masks_context_and_only_supervises_child(self):
        cycle = driver.Cycle(tasks(), 1)
        tokenizer = Tokenizer()
        for row in drive_to_sleep(cycle):
            encoded = native_seam.encode_row(row, tokenizer)
            expected = tuple(tokenizer.encode(row['target'])) + (tokenizer.eos_token_id,)
            self.assertEqual(encoded.target_ids, expected)
            self.assertEqual(tuple(value for value in encoded.labels if value != -100), expected)
            self.assertTrue(all(value == -100 for value in encoded.labels[:20]))
            self.assertEqual(encoded.labels[-1], -100)
            self.assertEqual(len(encoded.labels), len(encoded.input_ids))
        with self.assertRaises(AssertionError):
            native_seam.encode_row(dict(row, target='a' * policy.CONTEXT), tokenizer)

    def test_sleep_requires_all_rows_equal_dose_prior_and_old_mix(self):
        cycle = driver.Cycle(tasks(), 1)
        rows = drive_to_sleep(cycle)
        presentations = {row['source_record_sha256']: 5 for row in rows}
        for bad in ({}, dict(presentations, **{rows[0]['source_record_sha256']: 0}), dict(presentations, **{rows[0]['source_record_sha256']: 6})):
            with self.assertRaises(ValueError):
                cycle.sleep_complete(bad, True, True)
        for prior, old in ((False, True), (True, False)):
            with self.assertRaises(ValueError):
                cycle.sleep_complete(presentations, prior, old)

    def test_sleep_cannot_precede_actual_child_rounds(self):
        with self.assertRaises(ValueError):
            driver.Cycle(tasks(), 1).rows()

    def test_parent_failure_has_no_fallback_or_retry(self):
        cycle = driver.Cycle(tasks(), 1)
        for unused in range(2):
            cycle.reserve()
            cycle.finish_child(response())
        action = cycle.reserve()
        with self.assertRaisesRegex(ValueError, 'verified_strong_parent_required'):
            cycle.finish_parent(plan(), 'unverified-model', {})
        with self.assertRaisesRegex(ValueError, 'terminal_failure_no_retry'):
            cycle.reserve()
        self.assertEqual(cycle.snapshot()['outstanding'], action)

    def test_parent_transcript_must_bind_request_and_plan(self):
        for field in ('request_sha256', 'plan_sha256'):
            cycle = driver.Cycle(tasks(), 1)
            for unused in range(2):
                cycle.reserve()
                cycle.finish_child(response())
            action = cycle.reserve()
            receipt = dict(node_only=True, all_verified=True, request_sha256=policy.digest(action), plan_sha256=policy.digest(plan()))
            receipt[field] = '0' * 64
            with self.assertRaises(ValueError):
                cycle.finish_parent(plan(), policy.STRONG, receipt)

    def test_parent_visibility_allowlist_and_no_oracle(self):
        cycle = driver.Cycle(tasks(), 1)
        for unused in range(2):
            cycle.reserve()
            cycle.finish_child(response())
        payload = cycle.next_action()['payload']
        self.assertNotIn('651', json.dumps(payload))
        for level in ('top', 'episode', 'outcome'):
            bad = copy.deepcopy(payload)
            destination = bad if level == 'top' else bad['episodes'][0] if level == 'episode' else bad['episodes'][0]['records'][0]['outcome']
            destination['gold'] = '651'
            with self.assertRaises(ValueError):
                policy.validate_parent_payload(bad)
        bad = copy.deepcopy(payload)
        bad['previous_own_reflections'] = [dict(task_id='X_HELD_Y', trace='data', source_record_sha256='a' * 64)]
        with self.assertRaises(ValueError):
            policy.validate_parent_payload(bad)

    def test_generation_reserves_full_revision_context_without_cropping(self):
        self.assertEqual(policy.generation_budget('experience', 100)['effective_generation_cap'], 8192)
        bound = policy.generation_budget('check', 8500, 500)
        self.assertEqual(bound['effective_generation_cap'], 1740)
        self.assertFalse(bound['input_truncated'])
        self.assertEqual(bound['reserved_for_revision'], 6144)
        self.assertEqual(policy.generation_budget('revision', 12000, 1000)['effective_generation_cap'], 4384)
        for purpose, prompt, teacher in (('check', 11000, 1000), ('revision', 16384, 10), ('check', 100, 1025)):
            with self.assertRaises(ValueError):
                policy.generation_budget(purpose, prompt, teacher)

    def test_native_input_truncation_rejected(self):
        cycle = driver.Cycle(tasks(), 1)
        cycle.reserve()
        with self.assertRaises(ValueError):
            cycle.finish_child(dict(response(), input_truncated=True))
        self.assertIsNotNone(cycle.snapshot()['failed'])

    def test_budget_no_c0_no_new_control_triple(self):
        self.assertEqual(policy.NATIVE_CAP, 76)
        self.assertEqual(policy.PARENT_CAP, 4)
        self.assertEqual(policy.budget()['gpus'], 1)
        cycle = driver.Cycle(tasks(), 2)
        rows = drive_to_sleep(cycle)
        cycle.sleep_complete({row['source_record_sha256']: 1 for row in rows}, True, True)
        self.assertEqual(cycle.next_action()['retention'], 48)
        self.assertEqual(len([event for event in cycle.events if event['event'] == 'RESERVED_NO_RETRY']), 8)

    def test_snapshot_not_mutable_alias(self):
        cycle = driver.Cycle(tasks(), 1)
        action = cycle.reserve()
        action['purpose'] = 'other'
        self.assertEqual(cycle.snapshot()['outstanding']['purpose'], 'experience')
        snapshot = cycle.snapshot()
        snapshot['records'].clear()
        self.assertEqual(len(cycle.records), 2)

    def test_whole_source_registry_and_deterministic_fresh_cohort(self):
        scopes = ('L1_ALL_SOURCE', 'L1_READOUT', 'L2_ALL_SOURCE', 'L2_READOUT', 'RETENTION')
        manifests = [dict(scope=scope, complete_pool=True, ids=[scope], question_sha256=['0' * 64]) for scope in scopes]
        seed_before = policy.source.SEED
        cohort = policy.make_cohort(manifests)
        self.assertEqual(cohort, policy.make_cohort(manifests))
        self.assertEqual(policy.source.SEED, seed_before)
        roster = [task for group in cohort['train'] + cohort['held'] for task in group]
        self.assertEqual(len(roster), 20)
        self.assertEqual(len({task['question_sha256'] for task in roster}), 20)
        manifests[0]['ids'].append(roster[0]['id'])
        manifests[0]['question_sha256'].append(roster[0]['question_sha256'])
        fresh = policy.make_cohort(manifests)
        self.assertNotIn(roster[0]['id'], [task['id'] for group in fresh['train'] for task in group])
        with self.assertRaises(ValueError):
            policy.make_cohort(manifests[:-1])
        manifests[0]['complete_pool'] = False
        with self.assertRaises(ValueError):
            policy.make_cohort(manifests)

    def test_cpu_preparation_cannot_claim_native_readiness(self):
        ready = prepare.readiness()
        self.assertFalse(ready['launch_authorized'])
        self.assertFalse(ready['native_driver_connected'])
        self.assertEqual((ready['native_calls'], ready['parent_calls']), (0, 0))
        self.assertNotEqual(prepare.QUEUE_DIRECTORY, 'parent_queue')
        with self.assertRaises(KeyError):
            prepare.validate_allocation({}, 'a' * 64, 0)

    def test_bound_artifacts_require_hash_and_exact_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / 'fixture.json'
            path.write_text('{"status":"COMPLETE"}')
            reference = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(prepare.read_bound(reference)['status'], 'COMPLETE')
            with self.assertRaises(ValueError):
                prepare.read_bound(dict(reference, sha256='0' * 64))

    def allocation(self):
        physical, uuid = next(iter(policy.source.DEVICES.values()))
        return dict(schema='ORCH_MATH_FEEDBACK_UPTAKE_ALLOCATION_V1', ready_sha256='a' * 64,
            publication=dict(commit='fixture-only', path='COORDINATION.md'), owner='MATH_FEEDBACK_UPTAKE',
            devices=[dict(physical=physical, uuid=uuid)], host_sha256=policy.source.HOST_SHA,
            additional_budget=policy.budget(), seed_campaign=prepare.SEED_CAMPAIGN, seed_rule=prepare.SEED_RULE,
            aggregate_native_cap=2140, aggregate_parent_cap=40, aggregate_gpu_hours_cap=24,
            native_deadline_unix=1789472355.2727501, hard_deadline_unix=1789472535.2727501)

    def test_allocation_budget_uuid_host_deadline_and_seed_binding(self):
        allocation = self.allocation()
        prepare.validate_allocation(allocation, 'a' * 64, 0)
        changes = dict(ready_sha256='b' * 64, owner='OTHER', aggregate_native_cap=2064,
            aggregate_parent_cap=36, aggregate_gpu_hours_cap=25, seed_campaign='a_better_scoring_seed',
            native_deadline_unix=1789472356, hard_deadline_unix=1789472536, host_sha256='0' * 64)
        for key, value in changes.items():
            with self.subTest(key=key), self.assertRaises(ValueError):
                prepare.validate_allocation(dict(allocation, **{key: value}), 'a' * 64, 0)
        bad = copy.deepcopy(allocation)
        bad['devices'][0]['uuid'] = 'GPU-not-allocated'
        with self.assertRaises(ValueError):
            prepare.validate_allocation(bad, 'a' * 64, 0)
        with self.assertRaises(ValueError):
            prepare.validate_allocation(allocation, 'a' * 64, 1789472356)

    def test_saved_seed_requires_optimizer_continuity_and_native_after(self):
        adapter = dict(base_sha256=policy.source.BASE_SHA, state_sha256='b' * 64)
        process = ['fixture_boot', 9, 100]
        seed = dict(campaign_name=prepare.SEED_CAMPAIGN, selection_rule=prepare.SEED_RULE,
            output_adapter=adapter, optimizer_sha256='c' * 64, reset_optimizer=False, l2_into_l1=False)
        complete = dict(status='COMPLETE', cycle=8, phase='experience', arm='GUIDED_SLEEP', updates=10,
            process=process, output_adapter=adapter, optimizer_sha256='c' * 64)
        after = dict(output_adapter=adapter, process=process, actual_mounted_identity_verified=True, frozen_base_verified=True)
        terminal = dict(status='COMPLETE')
        prepare.validate_seed(seed, complete, after, terminal)
        for field, value in (('reset_optimizer', True), ('l2_into_l1', True), ('optimizer_sha256', 'd' * 64)):
            with self.assertRaises(ValueError):
                prepare.validate_seed(dict(seed, **{field: value}), complete, after, terminal)
        with self.assertRaises(ValueError):
            prepare.validate_seed(seed, complete, dict(after, actual_mounted_identity_verified=False), terminal)
        with self.assertRaises(ValueError):
            prepare.validate_seed(seed, complete, after, dict(status='FAILED'))
        with self.assertRaises(ValueError):
            prepare.validate_seed(seed, dict(complete, cycle=7), after, terminal)

    def test_empty_gpu_is_not_release_and_proc_failures_block(self):
        device = self.allocation()['devices'][0]
        release = dict(owner='CREATIVE_OWNER', next_owner='MATH_FEEDBACK_UPTAKE', natural_completion=True,
            uuid=device['uuid'], physical=device['physical'], terminal_receipt={'fixture': True},
            after_receipt={'fixture': True}, released_unix=50,
            previous_processes=[dict(boot_id='fixture_boot', pid=9, uid=1, start_ticks=100, command_sha256='e' * 64)])
        scan = dict(observed_unix=60, report=dict(clear=True, scanner_euid=0, blocking_reasons=[],
            gpu=dict(index=device['physical'], uuid=device['uuid']), host_sha256=policy.source.HOST_SHA, device_minor=4))
        prepare.validate_release(release, scan, device, 65)
        for field, value in (('scanner_euid', 1000), ('blocking_reasons', ['unknown_proc']), ('clear', False)):
            bad = copy.deepcopy(scan)
            bad['report'][field] = value
            with self.assertRaises(ValueError):
                prepare.validate_release(release, bad, device, 65)
        with self.assertRaises(ValueError):
            prepare.validate_release(release, scan, device, 100)
        with self.assertRaises(ValueError):
            prepare.validate_release(dict(release, natural_completion=False), scan, device, 65)
        with self.assertRaises(ValueError):
            prepare.validate_release(dict(release, previous_processes=[]), scan, device, 65)
        with self.assertRaises(KeyError):
            prepare.validate_release(dict(memory_mib=0), scan, device, 65)


if __name__ == '__main__':
    unittest.main()
