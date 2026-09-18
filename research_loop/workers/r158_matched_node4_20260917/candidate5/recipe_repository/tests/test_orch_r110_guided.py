"""Offline policy tests for the frozen initial-parent-continuation interface."""

from copy import deepcopy
import hashlib
import json
import unittest

from organism_v6 import orch_r110_guided as policy


TASKS = [dict(id=f'R110_TRAIN_{index:03d}', split='TRAIN', question='What is 2 plus 3?', gold='5')
    for index in (1, 2)]
PLAN = dict(intervention_class='metacognition', guidance='Notice where your attention is going before continuing.',
    rationale='Help allocate effort rather than grade the answer.')


class Tokenizer:
    eos_token_id = 1
    all_special_ids = [1]

    def apply_chat_template(self, messages, **kwargs):
        return ''.join(message['role'] + ': ' + message['content'] + '\n' for message in messages) + 'assistant: '

    def encode(self, text, **kwargs):
        return [ord(character) + 10 for character in text]

    def decode(self, tokens, **kwargs):
        return ''.join(chr(token - 10) for token in tokens)


def response(messages, raw='My own calculation.\nFINAL: 5', terminal=True):
    tokenizer = Tokenizer()
    return dict(raw=raw, messages=deepcopy(messages),
        prompt_tokens=len(tokenizer.encode(tokenizer.apply_chat_template(messages))),
        token_ids=tokenizer.encode(raw) + ([1] if terminal else []), terminal=terminal,
        truncated=not terminal, input_truncated=False)


def episode(task, raw=None):
    records = []
    for purpose in ('experience', 'check', 'revision'):
        messages = policy.messages(task, purpose, records, PLAN if records else None)
        records.append(policy.history.record(task, purpose, response(messages,
            raw if raw is not None else 'My own calculation.\nFINAL: 5')))
    return records


def cycle():
    return {task['id']: episode(task) for task in TASKS}


def with_initial(records=None, raw='I kept returning to the same calculation.'):
    records = cycle() if records is None else records
    messages = policy.presleep_messages(TASKS, records, None, [])
    records['presleep_initial'] = policy.history.record(TASKS[-1], 'revision', response(messages, raw))
    return records


class PolicyTests(unittest.TestCase):
    def test_exact_final_caps(self):
        self.assertEqual((policy.CYCLES, policy.EPISODES, policy.PARENTS_PER_CYCLE), (64, 2, 3))
        self.assertEqual(policy.PARENT_CAP, policy.CYCLES * 3)
        self.assertEqual(policy.COLLECTION_CALLS_PER_CYCLE, 8)
        self.assertEqual(policy.NATIVE_CAP, policy.CYCLES * 80)
        self.assertEqual(policy.WALL_SECONDS, 8 * 3600)

    def test_exact_shared_principles_are_in_both_parent_instructions(self):
        self.assertEqual(hashlib.sha256(policy.PRINCIPLES_PATH.read_bytes()).hexdigest(), policy.PRINCIPLES_SHA256)
        self.assertIn(policy.PRINCIPLES_TEXT, policy.PARENT_INSTRUCTION)
        self.assertIn(policy.PRINCIPLES_TEXT, policy.PRESLEEP_PARENT_INSTRUCTION)

    def test_episode_payload_exact_score_blind_schema(self):
        payload = policy.parent_payload(TASKS[0], episode(TASKS[0])[0], 'a' * 64, 1, 1)
        policy.validate_parent_payload(payload)
        self.assertEqual(set(payload['child_state']), {'adapter_sha256', 'call_sha256', 'trace'})
        self.assertEqual(payload['task'], {key: TASKS[0][key] for key in ('id', 'question')})
        self.assertNotIn('outcome', payload['child_state'])

    def test_last_cycle_and_no_sixty_fifth(self):
        original = episode(TASKS[0])[0]
        policy.parent_payload(TASKS[0], original, 'a' * 64, policy.CYCLES, 2)
        for value in (0, policy.CYCLES + 1, True, 1.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                policy.parent_payload(TASKS[0], original, 'a' * 64, value, 1)

    def test_third_parent_is_named_presleep_not_episode_three(self):
        with self.assertRaisesRegex(ValueError, 'episode_parent_only'):
            policy.parent_payload(TASKS[0], episode(TASKS[0])[0], 'a' * 64, 1, 3)
        payload = policy.presleep_payload(TASKS, with_initial(), 'a' * 64, 1, [])
        self.assertEqual(payload['episode'], 'presleep')

    def test_scores_and_gold_extra_fields_rejected(self):
        base = policy.parent_payload(TASKS[0], episode(TASKS[0])[0], 'a' * 64, 1, 1)
        for field in ('outcome', 'correct', 'score', 'gold'):
            payload = deepcopy(base)
            payload['child_state'][field] = 'forbidden'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'score_blind_child_schema'):
                policy.validate_parent_payload(payload)

    def test_held_task_and_visibility_rejected(self):
        task = dict(TASKS[0], id='R110_HELD_001', split='HELD')
        with self.assertRaises(ValueError):
            policy.messages(task, 'experience')
        payload = policy.parent_payload(TASKS[0], episode(TASKS[0])[0], 'a' * 64, 1, 1)
        payload['child_state']['trace'] += ' sealed_score=100'
        with self.assertRaisesRegex(ValueError, 'parent_visibility_violation'):
            policy.validate_parent_payload(payload)

    def test_outcome_never_enters_child_prompt(self):
        records = episode(TASKS[0], 'I think it is six.\nFINAL: 6')
        for record in records:
            messages = json.dumps(record['response']['messages'])
            self.assertNotIn('Final-answer-only TRAIN outcome', messages)
            self.assertNotIn('INCORRECT', messages)
            self.assertNotIn('"outcome"', messages)

    def test_guidance_scheduled_for_correct_and_incorrect_records(self):
        for text in ('FINAL: 5', 'FINAL: 6'):
            records = episode(TASKS[0], text)
            payload = policy.parent_payload(TASKS[0], records[0], 'a' * 64, 1, 1)
            self.assertEqual(payload['child_state']['trace'], text)
            self.assertEqual(payload['instruction'], policy.PARENT_INSTRUCTION)

    def test_revision_retains_actual_parented_causal_prefix(self):
        records = episode(TASKS[0])
        revision = records[2]['response']['messages']
        check = records[1]['response']
        self.assertEqual(revision[:-2], check['messages'])
        self.assertEqual(revision[-2], dict(role='assistant', content=check['raw']))
        self.assertIn(PLAN['guidance'], json.dumps(revision))

    def test_parent_echo_and_incorrect_outputs_are_retained(self):
        text = PLAN['guidance'] + '\nFINAL: 6'
        records = episode(TASKS[0], text)
        rows = policy.replay_rows(TASKS[0], records, PLAN)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row['target'] == text and row['parent_echo_detected'] for row in rows))
        self.assertTrue(all(row['outcome'] == 'INCORRECT' and row['retain_actual_child_output'] for row in rows))

    def test_truncated_actual_output_retained_without_eos_fabrication(self):
        records = episode(TASKS[0])
        native = response(records[-1]['response']['messages'], 'Still thinking', terminal=False)
        records[-1] = policy.history.record(TASKS[0], 'revision', native)
        row = policy.replay_rows(TASKS[0], records, PLAN)[-1]
        self.assertEqual(row['target'], native['raw'])
        self.assertFalse(row['append_eos'])
        self.assertTrue(row['continuation_only'])

    def test_changed_record_not_accepted_as_native(self):
        records = episode(TASKS[0])
        records[0]['response']['raw'] = 'rewritten'
        with self.assertRaisesRegex(ValueError, 'source_record_mismatch'):
            policy.replay_rows(TASKS[0], records, PLAN)

    def test_presleep_initial_then_parent_then_actual_continuation(self):
        records = cycle()
        initial_messages = policy.presleep_messages(TASKS, records, None, [])
        self.assertNotIn('PRESLEEP PARENT INTERVENTION', json.dumps(initial_messages))
        initial = policy.history.record(TASKS[-1], 'revision', response(initial_messages, 'My initial reflection.'))
        records['presleep_initial'] = initial
        payload = policy.presleep_payload(TASKS, records, 'a' * 64, policy.CYCLES, [])
        self.assertEqual(payload['task'], {key: TASKS[-1][key] for key in ('id', 'question')})
        context = json.loads(payload['child_state']['trace'])
        self.assertEqual(len(context['episodes']), policy.EPISODES)
        self.assertEqual(context['presleep_initial']['trace'], initial['response']['raw'])
        self.assertEqual(context['presleep_initial']['source_record_sha256'], policy.digest(initial))
        continuation = policy.presleep_messages(TASKS, records, PLAN, [])
        self.assertEqual(continuation[:-2], initial_messages)
        self.assertEqual(continuation[-2], dict(role='assistant', content=initial['response']['raw']))
        self.assertIn(PLAN['guidance'], continuation[-1]['content'])

    def test_presleep_requires_actual_initial_before_parent(self):
        records = cycle()
        with self.assertRaisesRegex(ValueError, 'initial_presleep_before_parent_required'):
            policy.presleep_payload(TASKS, records, 'a' * 64, 1, [])
        with self.assertRaisesRegex(ValueError, 'initial_presleep_before_parent_required'):
            policy.presleep_messages(TASKS, records, PLAN, [])

    def test_presleep_initial_must_not_regenerate(self):
        with self.assertRaisesRegex(ValueError, 'initial_reflection_never_regenerated'):
            policy.presleep_messages(TASKS, with_initial(), None, [])

    def test_presleep_public_records_have_no_scores(self):
        payload = policy.presleep_payload(TASKS, with_initial(), 'a' * 64, 1, [])
        context = json.loads(payload['child_state']['trace'])
        for item in context['episodes']:
            self.assertEqual(set(item['task']), {'id', 'question'})
            for record in item['records']:
                self.assertEqual(set(record), {'purpose', 'trace', 'source_record_sha256'})
        self.assertEqual(set(context['presleep_initial']), {'trace', 'source_record_sha256'})

    def test_presleep_tampered_public_score_rejected(self):
        payload = policy.presleep_payload(TASKS, with_initial(), 'a' * 64, 1, [])
        context = json.loads(payload['child_state']['trace'])
        context['episodes'][0]['records'][0]['outcome'] = 'CORRECT'
        payload['child_state']['trace'] = json.dumps(context)
        with self.assertRaisesRegex(ValueError, 'score_blind_presleep_record'):
            policy.validate_parent_payload(payload)

    def test_presleep_last_task_anchor_required(self):
        payload = policy.presleep_payload(TASKS, with_initial(), 'a' * 64, 1, [])
        payload['task'] = {key: TASKS[0][key] for key in ('id', 'question')}
        with self.assertRaisesRegex(ValueError, 'last_train_task_presleep_anchor'):
            policy.validate_parent_payload(payload)

    def test_presleep_initial_and_continuation_rows_preserve_all_raw(self):
        records = with_initial(raw=PLAN['guidance'])
        initial = records['presleep_initial']
        initial_row = policy.encode_presleep_record(TASKS[-1], initial, None)
        continuation = policy.history.record(TASKS[-1], 'revision', response(
            policy.presleep_messages(TASKS, records, PLAN, []), PLAN['guidance']))
        final_row = policy.encode_presleep_record(TASKS[-1], continuation, PLAN)
        self.assertEqual(initial_row['target'], PLAN['guidance'])
        self.assertEqual(final_row['target'], PLAN['guidance'])
        self.assertEqual(initial_row['kind'], 'presleep_initial')
        self.assertEqual(final_row['kind'], 'presleep')
        self.assertFalse(initial_row['teacher_in_prefix'])
        self.assertTrue(final_row['teacher_in_prefix'])
        self.assertTrue(final_row['parent_echo_detected'])

    def test_native_encoder_masks_prefix_not_echoed_child_target(self):
        records = with_initial()
        native = response(policy.presleep_messages(TASKS, records, PLAN, []), PLAN['guidance'])
        record = policy.history.record(TASKS[-1], 'revision', native)
        row = policy.encode_presleep_record(TASKS[-1], record, PLAN)
        policy.replay.verify_source(row, dict(response=native))
        encoded = policy.replay.encode_row(row, Tokenizer(), 20000)
        self.assertEqual(tuple(encoded.labels[:native['prompt_tokens']]), (-100,) * native['prompt_tokens'])
        self.assertEqual(tuple(encoded.labels[native['prompt_tokens']:]), tuple(native['token_ids']))

    def test_encoder_overflow_does_not_crop_source(self):
        records = with_initial()
        record = records['presleep_initial']
        row = policy.encode_presleep_record(TASKS[-1], record, None)
        original = deepcopy(row)
        with self.assertRaisesRegex(ValueError, 'full_source_no_truncation'):
            policy.replay.encode_row(row, Tokenizer(), 1)
        self.assertEqual(row, original)

    def test_triple_never_claims_benefit_from_outcome_or_echo(self):
        triple = policy.intervention_triple(TASKS[0], episode(TASKS[0]), PLAN, 'a' * 64, {})
        self.assertEqual(triple['functional_change'], 'UNASSESSED')
        self.assertEqual(triple['helpfulness'], 'UNASSESSED')
        self.assertEqual(triple['parent_trigger'], 'FIXED_SCHEDULE_NOT_OUTCOME')

    def test_exact_two_train_tasks_and_complete_cycle(self):
        records = cycle()
        with self.assertRaisesRegex(ValueError, 'two_distinct_train_tasks'):
            policy.cycle_records([TASKS[0], TASKS[0]], records)
        records[TASKS[0]['id']].pop()
        with self.assertRaisesRegex(ValueError, 'complete_presleep_episode'):
            policy.cycle_records(TASKS, records)


if __name__ == '__main__':
    unittest.main()
