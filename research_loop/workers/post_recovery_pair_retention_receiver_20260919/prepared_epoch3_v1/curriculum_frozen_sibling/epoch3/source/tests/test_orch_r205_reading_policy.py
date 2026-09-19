"""Synthetic CPU-only reading routing; no live inbox or learner controls."""

import json
from pathlib import Path
import tempfile
import time
import unittest

from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r127_pilot_console import publish_parent
from gpu.orch_r184_think_act_learn import (
    ARTIFACT_ELICITATION_POLICY, CONSOLE_REPLY_POLICY, SCHEMA, STAGE_BOUNDARY_POLICY,
    ThinkActLearn, validate_config,
)
from gpu.orch_r205_reading_policy import POLICY, is_reading
from gpu.orch_r206_pinned_messages import POLICY as PINNED_POLICY
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream


class SyntheticChild:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def count_tokens(self, messages):
        return sum(len(message['content'].split()) + 4 for message in messages)

    def generate(self, messages, **limits):
        self.calls.append(messages)
        return dict(raw=next(self.outputs), token_ids=[10, 2], terminal=True, truncated=False)


class ReadingPolicyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir='/tmp')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.addCleanup(self.journal.close)
        self.stream = ContinualStream(TrainHistory(system_prompt='Synthetic system.', birth_prompt='Investigate.'),
            context_limit=8192, segment_tokens=1024, segments_per_sleep=2,
            deadline_unix=time.time() + 600, model_state_sha256='f' * 64, allow_eviction=True)
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))
        self.config = dict(schema=SCHEMA, trial_id='synthetic_reading_cpu_only', reflection_policy='explicit',
            think_segments=1, cpu_gate_root='/synthetic/not_dispatched/gate', cpu_gate_sha256='e' * 64,
            stage_boundary_policy=STAGE_BOUNDARY_POLICY, console_reply_policy=CONSOLE_REPLY_POLICY,
            pinned_messages_policy=PINNED_POLICY, reading_reply_policy=POLICY)
        self.first = 'The base stays fixed while my adapter learns. I will write a specific example before judging a revision.'
        self.second = 'Context messages are not my training targets. I will compare my prediction with the next observed result.'

    def records(self, kind):
        result = []
        for path in sorted((self.root / 'stream/records').glob('[0-9]' * 20 + '.json')):
            record = json.loads(path.read_bytes())
            if record['kind'] == kind:
                result.append(record['document'])
        return result

    def driver(self, outputs, config=None):
        return ThinkActLearn(SyntheticChild(outputs), self.stream, self.journal, config or self.config,
            executor=lambda origin: dict(status='SYNTHETIC_NO_EXECUTION', executed=False))

    def reading(self, text='Please read this synthetic lesson.'):
        return publish_parent(self.root, 'Rohin', text)['id']

    def prompt(self, identifier, section):
        return publish_parent(self.root, 'Astra', f'Reading: {identifier}\nSection: {section}\n'
            'Restate the lesson in your words and choose a concrete behavior change.')

    def review(self, identifier, turn, restatement, change, *, release=False, speaker='Astra'):
        text = (f'Reading: {identifier}\nSection: {turn["section"]}\n'
            f'Child response: {turn["response"]["record_index"]}\nJudgment: substantive\n'
            f'Restatement: {restatement}\nBehavior change: {change}')
        if release:
            text += f'\nRelease reading: {identifier}'
        return publish_parent(self.root, speaker, text)

    def turns(self, driver, identifier):
        return driver.readings.entries['parent:inbox:' + identifier]['turns']

    def test_exact_classification_boundary_and_phrase(self):
        self.assertFalse(is_reading(' '.join(['word'] * 600)))
        self.assertTrue(is_reading(' '.join(['word'] * 601)))
        self.assertTrue(is_reading('Please READ\nTHIS carefully.'))
        self.assertFalse(is_reading('A bread thisway example.'))
        self.assertTrue(is_reading('Do not read this.'))

    def test_reading_runs_normal_stages_without_console_act_or_parent_wait(self):
        identifier = self.reading()
        driver = self.driver(['Own thinking.', 'Own ordinary action.', 'Own review.'])
        driver.wake()
        driver.prepare_sleep(1)
        self.assertEqual([item['stage'] for item in self.records('R184_STAGE')], ['THINK', 'ACT', 'LEARN'])
        self.assertEqual(self.records('R205_CONSOLE_REPLY'), [])
        self.assertEqual(self.turns(driver, identifier), [])
        self.assertEqual(len(self.stream.pending_rows()), 3)
        self.assertTrue(all(not row['prefix_loss'] for row in self.stream.rows))

    def test_ordinary_message_bypasses_pending_reading_individually(self):
        reading = self.reading(' '.join(['word'] * 601))
        ordinary = publish_parent(self.root, 'Rohin', 'What is your current uncertainty?')['id']
        driver = self.driver(['My ordinary reply.', 'My reading discussion.'])
        driver.generate_stage('THINK')
        replies = self.records('R205_CONSOLE_REPLY')
        self.assertEqual(len(replies), 1)
        self.assertEqual(replies[0]['source_inbox_events'][0]['event_id'], 'parent:inbox:' + ordinary)
        self.assertIn('parent:inbox:' + reading, driver.readings.pending_ids())
        self.assertFalse(replies[0]['outcome']['tool_execution_allowed'])

    def test_unreleased_reading_before_learn_does_not_spin_or_answer_inside_learn(self):
        identifier = self.reading()
        driver = self.driver(['Own bounded review.'])
        driver.prepare_sleep(1)
        self.assertEqual(len(driver.child.calls), 1)
        self.assertEqual(self.records('R205_CONSOLE_REPLY'), [])
        self.assertNotIn('parent:inbox:' + identifier, {event.event_id for event in self.stream.history.events})
        self.assertEqual(self.records('R184_STAGE')[0]['stage'], 'LEARN')

    def test_two_source_bound_exchanges_then_explicit_release(self):
        identifier = self.reading()
        self.prompt(identifier, 1)
        driver = self.driver([self.first, self.second, 'My final reading reply.', 'My ordinary action.'])
        driver.generate_stage('THINK')
        first = self.turns(driver, identifier)[0]
        self.review(identifier, first, 'The base stays fixed while my adapter learns.',
            'I will write a specific example before judging a revision.')
        self.prompt(identifier, 2)
        driver.generate_stage('THINK')
        second = self.turns(driver, identifier)[1]
        self.assertEqual(self.records('R205_CONSOLE_REPLY'), [])
        self.review(identifier, second, 'Context messages are not my training targets.',
            'I will compare my prediction with the next observed result.', release=True)
        driver.generate_stage('ACT')
        replies = self.records('R205_CONSOLE_REPLY')
        self.assertEqual(len(replies), 1)
        self.assertEqual(replies[0]['source_inbox_events'][0]['event_id'], 'parent:inbox:' + identifier)
        self.assertEqual(driver.readings.entries['parent:inbox:' + identifier]['status'], 'REPLIED')
        self.assertTrue(self.records('R205_READING_PARENT_RECEIPT')[-1]['release_accepted'])
        self.assertEqual(self.records('R205_READING_PARENT_RECEIPT')[-1]['accepted_exchange_count'], 2)
        self.assertFalse(replies[0]['outcome']['tool_execution_allowed'])

    def test_premature_release_and_repeated_prompt_do_not_count_two_exchanges(self):
        identifier = self.reading()
        self.prompt(identifier, 1)
        driver = self.driver([self.first, self.second, 'An ordinary action.'])
        driver.generate_stage('THINK')
        driver.generate_stage('THINK')
        self.assertEqual(len(self.turns(driver, identifier)), 1)
        self.review(identifier, self.turns(driver, identifier)[0],
            'The base stays fixed while my adapter learns.',
            'I will write a specific example before judging a revision.', release=True)
        driver.generate_stage('ACT')
        self.assertEqual(self.records('R205_CONSOLE_REPLY'), [])
        self.assertFalse(self.records('R205_READING_PARENT_RECEIPT')[-1]['release_accepted'])

    def test_fabricated_child_excerpts_cannot_release(self):
        identifier = self.reading()
        self.prompt(identifier, 1)
        driver = self.driver([self.first, 'An ordinary action.'])
        driver.generate_stage('THINK')
        self.review(identifier, self.turns(driver, identifier)[0],
            'Invented restatement never written by the child.', 'An invented change.', release=True)
        driver.generate_stage('ACT')
        receipt = self.records('R205_READING_PARENT_RECEIPT')[-1]
        self.assertFalse(receipt['judgment']['substantive'])
        self.assertFalse(receipt['release_accepted'])

    def test_other_speaker_cannot_supply_parent_release(self):
        identifier = self.reading()
        self.prompt(identifier, 1)
        driver = self.driver([self.first, 'Own action.'])
        driver.generate_stage('THINK')
        self.review(identifier, self.turns(driver, identifier)[0],
            'The base stays fixed while my adapter learns.',
            'I will write a specific example before judging a revision.', release=True, speaker='Fable')
        driver.generate_stage('ACT')
        self.assertEqual(self.records('R205_READING_PARENT_RECEIPT'), [])
        self.assertEqual(self.records('R205_CONSOLE_REPLY'), [])

    def test_act_and_learn_are_not_reading_think_exchanges(self):
        identifier = self.reading()
        self.prompt(identifier, 1)
        driver = self.driver([self.first, self.second])
        driver.generate_stage('ACT')
        driver.generate_stage('LEARN')
        self.assertEqual(self.turns(driver, identifier), [])

    def test_policy_restores_pending_discussion_without_replaying_human(self):
        identifier = self.reading()
        self.prompt(identifier, 1)
        driver = self.driver([self.first])
        driver.generate_stage('THINK')
        restored = self.driver(['Another thought.'])
        self.assertEqual(len(self.turns(restored, identifier)), 1)
        restored.generate_stage('THINK')
        self.assertEqual(len(self.turns(restored, identifier)), 1)
        self.assertEqual(self.records('R205_CONSOLE_REPLY'), [])

    def test_already_answered_reading_is_not_reclassified_or_replayed(self):
        identifier = self.reading()
        old_config = {key: value for key, value in self.config.items() if key != 'reading_reply_policy'}
        original = self.driver(['Old-policy answer.', 'Own thought.'], old_config)
        original.generate_stage('THINK')
        upgraded = self.driver(['Another own thought.'])
        upgraded.generate_stage('THINK')
        self.assertNotIn('parent:inbox:' + identifier, upgraded.readings.entries)
        self.assertEqual(len(self.records('R205_CONSOLE_REPLY')), 1)

    def test_reading_policy_requires_pins_and_nonhuman_parent(self):
        config = {key: value for key, value in self.config.items() if key != 'pinned_messages_policy'}
        with self.assertRaisesRegex(ValueError, 'reading_discussion_requires_pinned_console_policy'):
            validate_config(config)
        with self.assertRaisesRegex(ValueError, 'bound_reading_parent_not_human'):
            validate_config(dict(self.config, reading_parent_speaker='Rohin'))

    def test_content_annotations_include_console_rows_and_leave_raw_targets_unchanged(self):
        from organism_v6.orch_r194_code_target_filter import REVIEW_POLICY
        from organism_v6.orch_r213_content_target_filter import POLICY as CONTENT_POLICY
        config = dict(self.config, content_target_filter=CONTENT_POLICY, learn_review_filter=REVIEW_POLICY,
            artifact_elicitation_policy=ARTIFACT_ELICITATION_POLICY)
        publish_parent(self.root, 'Rohin', 'What do you intend to write?')
        outputs = ['I have checked all tasks.', self.first, 'Byte opened the door and found a folded map inside.',
            'I have completed everything.']
        driver = self.driver(outputs, config)
        driver.generate_stage('THINK')
        driver.generate_stage('ACT')
        driver.prepare_sleep(1)
        self.assertEqual([row['target'] for row in self.stream.rows], outputs)
        self.assertTrue(all(row['content_target_filter'] == CONTENT_POLICY for row in self.stream.rows))
        self.assertNotIn('judgment in ONE', driver.child.calls[0][-1]['content'])
        self.assertIn('judgment in ONE', driver.child.calls[1][-1]['content'])
        self.assertIn('Produce the artifact itself', driver.child.calls[2][-1]['content'])
        excluded = self.records('R195_LEARN_REVIEW')[-1]['proof']['excluded']
        self.assertIn(self.stream.rows[0]['source_sha256'], [item['source_sha256'] for item in excluded])
        self.assertNotIn(self.stream.rows[2]['source_sha256'], [item['source_sha256'] for item in excluded])

    def test_content_annotation_requires_existing_zero_dose_review_path(self):
        from organism_v6.orch_r213_content_target_filter import POLICY as CONTENT_POLICY
        with self.assertRaisesRegex(ValueError, 'content_targets_require_review_filter'):
            validate_config(dict(self.config, content_target_filter=CONTENT_POLICY))

    def test_unrendered_parent_guidance_cannot_count_as_an_exchange(self):
        identifier = self.reading()
        publication = self.prompt(identifier, 1)
        driver = self.driver([self.first])
        original_capture = driver.readings.capture_think

        def capture(request, request_origin, response, response_origin):
            request['messages'] = [message for message in request['messages']
                if publication['id'] not in message['content']]
            return original_capture(request, request_origin, response, response_origin)

        driver.readings.capture_think = capture
        driver.generate_stage('THINK')
        self.assertEqual(self.turns(driver, identifier), [])

    def test_released_reading_reply_binds_two_actual_thinks_and_parent_release(self):
        self.test_two_source_bound_exchanges_then_explicit_release()
        evidence = self.records('R205_CONSOLE_REPLY')[0]['reading_evidence']
        self.assertEqual(len(evidence['substantive_exchanges']), 2)
        self.assertTrue(evidence['parent_release']['source_sha256'])
        self.assertEqual(len({turn['parent_guidance']['event_id']
            for turn in evidence['substantive_exchanges']}), 2)
