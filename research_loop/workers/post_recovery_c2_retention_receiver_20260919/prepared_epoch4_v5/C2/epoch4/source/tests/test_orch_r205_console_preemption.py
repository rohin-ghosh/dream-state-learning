"""Synthetic CPU-only conversation preemption; never touch a live learner."""

from copy import deepcopy
from types import SimpleNamespace
import time
import unittest
from unittest.mock import Mock, patch

import test_orch_r205_reading_policy as reading_tests
from gpu.orch_r125_continual_native import NativeChild
from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r127_pilot_console import publish_parent
from gpu.orch_r184_think_act_learn import CONSOLE_REPLY_POLICY, run_loop, validate_config
from gpu.orch_r205_console_preemption import ConsoleInterrupt, POLICY, stopping_criteria
from organism_v6.orch_r125_continual_stream import ContinualStream


class ConsolePreemptionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = reading_tests.ReadingPolicyTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.config = dict(self.fixture.config, console_preemption_policy=POLICY)

    def driver(self, outputs):
        return self.fixture.driver(outputs, self.config)

    def records(self, kind):
        return self.fixture.records(kind)

    def interrupt_first_generation(self, driver, *, messages, partial='Unfinished own text.'):
        ordinary = driver.child.generate
        published = []

        def generate(prompt, **limits):
            if not published:
                published.extend(publish_parent(self.fixture.root, speaker, text)['id']
                    for speaker, text in messages)
                interruption = limits['interrupt']()
                result = dict(raw=partial, token_ids=[10], terminal=False, truncated=False)
                if interruption is not None:
                    result['interruption'] = interruption
                return result
            return ordinary(prompt, **limits)

        driver.child.generate = generate
        return published

    def test_ordinary_message_is_very_next_request_and_partial_never_trains(self):
        driver = self.driver(['My direct answer.', 'My resumed artifact.'])
        prior = deepcopy(self.fixture.stream.history.working_state)
        identifiers = self.interrupt_first_generation(driver, messages=[('Rohin', 'What happened?')],
            partial='print("unfinished code must never execute")')
        driver.generate_stage('THINK')
        requests = self.records('REQUEST')
        self.assertEqual(len(requests), 3)
        self.assertEqual(requests[1]['action_policy'], CONSOLE_REPLY_POLICY)
        self.assertNotIn('action_policy', requests[2])
        self.assertEqual(self.records('R205_CONSOLE_REPLY')[0]['source_inbox_events'][0]['event_id'],
            'parent:inbox:' + identifiers[0])
        self.assertEqual(len(self.records('GENERATION_PARTIAL')), 1)
        self.assertEqual(self.records('GENERATION_ABORTED')[0]['status'], 'ABORTED_NOT_TRAINED')
        self.assertEqual([row['target'] for row in self.fixture.stream.rows],
            ['My direct answer.', 'My resumed artifact.'])
        self.assertEqual(self.fixture.stream.history.working_state, prior)
        self.assertEqual(self.fixture.stream.model_state_sha256, 'f' * 64)
        self.assertFalse(self.records('R205_CONSOLE_REPLY')[0]['outcome']['tool_execution_allowed'])

    def test_reading_never_preempts_or_receives_immediate_console_act(self):
        driver = self.driver(['Another own thought.'])
        identifiers = self.interrupt_first_generation(driver, messages=[('Rohin', 'Read this lesson.')])
        driver.generate_stage('THINK')
        driver.generate_stage('THINK')
        self.assertEqual(self.records('GENERATION_PARTIAL'), [])
        self.assertEqual(self.records('R205_CONSOLE_REPLY'), [])
        self.assertIn('parent:inbox:' + identifiers[0], driver.readings.pending_ids())

    def test_ordinary_bypasses_simultaneous_reading_but_cannot_release_it(self):
        driver = self.driver(['Direct answer.', 'Own discussion.'])
        identifiers = self.interrupt_first_generation(driver,
            messages=[('Rohin', 'Please read this.'), ('Rohin', 'Are you available?')])
        driver.generate_stage('THINK')
        sources = self.records('GENERATION_ABORTED')[0]['interruption']['source_inbox_events']
        self.assertEqual([source['event_id'] for source in sources], ['parent:inbox:' + identifiers[1]])
        self.assertEqual(len(self.records('R205_CONSOLE_REPLY')), 1)
        self.assertIn('parent:inbox:' + identifiers[0], driver.readings.pending_ids())

    def test_each_ordinary_turn_is_answered_individually(self):
        driver = self.driver(['First answer.', 'Second answer.', 'Own artifact.'])
        identifiers = self.interrupt_first_generation(driver,
            messages=[('Rohin', 'Question one?'), ('Rohin', 'Question two?')])
        driver.generate_stage('ACT')
        replies = self.records('R205_CONSOLE_REPLY')
        self.assertEqual(len(replies), 2)
        self.assertEqual({reply['source_inbox_events'][0]['event_id'] for reply in replies},
            {'parent:inbox:' + identifier for identifier in identifiers})
        self.assertTrue(all(len(reply['source_inbox_events']) == 1 for reply in replies))

    def test_parent_input_does_not_preempt_child(self):
        driver = self.driver([])
        self.interrupt_first_generation(driver, messages=[('Astra', 'A reading question.')])
        driver.generate_stage('ACT')
        self.assertEqual(self.records('GENERATION_PARTIAL'), [])
        self.assertEqual(self.records('R205_CONSOLE_REPLY'), [])

    def test_learn_is_not_interrupted_and_following_request_is_console(self):
        driver = self.driver(['Direct answer.', 'Own thought.'])
        ordinary = driver.child.generate
        published = []

        def generate(messages, **limits):
            if not published:
                self.assertNotIn('interrupt', limits)
                published.append(publish_parent(self.fixture.root, 'Rohin', 'Tell me what happened.')['id'])
                return dict(raw='My actual review.', token_ids=[10, 2], terminal=True, truncated=False)
            return ordinary(messages, **limits)

        driver.child.generate = generate
        driver.generate_stage('LEARN')
        driver.generate_stage('THINK')
        self.assertEqual(self.records('REQUEST')[1]['action_policy'], CONSOLE_REPLY_POLICY)
        self.assertEqual(self.records('GENERATION_PARTIAL'), [])

    def test_abort_checkpoint_reopens_with_all_prior_rows_and_working_state(self):
        driver = self.driver(['Existing own artifact.'])
        driver.generate_stage('ACT')
        previous = self.fixture.stream.checkpoint()['state']
        interrupt = ConsoleInterrupt(self.fixture.journal, self.fixture.stream, poll_seconds=0)

        def generate(messages, **limits):
            publish_parent(self.fixture.root, 'Rohin', 'A real synthetic question?')
            return dict(raw='Partial', token_ids=[10], terminal=False, truncated=False,
                interruption=limits['interrupt']())

        result = self.fixture.stream.step(generate, driver.child.count_tokens,
            self.fixture.journal.record, interrupt=interrupt)
        self.assertTrue(result['aborted'])
        self.fixture.journal.close()
        with StreamJournal(self.fixture.root / 'stream') as reopened:
            restored = ContinualStream.restore(**reopened.latest_checkpoint())
            self.assertEqual(restored.checkpoint()['state'], previous)

    def test_preemption_without_reading_exception_is_rejected(self):
        config = {key: value for key, value in self.config.items() if key != 'reading_reply_policy'}
        with self.assertRaisesRegex(ValueError, 'preemption_requires_reading_exception'):
            validate_config(config)

    def test_native_can_abort_before_generation_without_sampling_or_optimizer(self):
        native = object.__new__(NativeChild)
        native.check = Mock()
        native.plan = dict(hard_end_unix=1000)
        native.engine = SimpleNamespace(model=SimpleNamespace(parameters=lambda: []))
        interruption = dict(policy=POLICY, source_inbox_events=[dict(event_id='synthetic')])
        result = native.generate([], max_new_tokens=20, deadline_unix=1000, interrupt=lambda: interruption)
        self.assertEqual(result['token_ids'], [])
        self.assertEqual(result['raw'], '')
        self.assertEqual(result['interruption'], interruption)

    def test_native_stopping_criterion_checks_each_generation_boundary(self):
        transformers = SimpleNamespace(StoppingCriteria=object, StoppingCriteriaList=list)
        callback = Mock(side_effect=[None, dict(policy=POLICY)])
        criteria = stopping_criteria(transformers, callback)
        self.assertFalse(criteria[0](None, None))
        self.assertTrue(criteria[0](None, None))
        self.assertEqual(callback.call_count, 2)

    def test_abort_cannot_be_committed_as_a_trainable_child_response(self):
        driver = self.driver([])
        original_record = self.fixture.journal.record
        self.interrupt_first_generation(driver, messages=[('Rohin', 'What happened?')])

        def record(kind, document):
            if kind == 'GENERATION_ABORTED':
                kind = 'COMMITTED'
            return original_record(kind, document)

        self.fixture.journal.record = record
        with self.assertRaisesRegex(ValueError, 'partial_attempt_never_training_target'):
            driver.generate_stage('ACT')
        self.assertEqual(self.fixture.stream.rows, [])

    def test_console_drain_is_after_complete_optimizer_not_after_terminal_budget(self):
        for budget in (1, 2):
            with self.subTest(budget=budget):
                driver = Mock()
                stream = SimpleNamespace(pending_rows=lambda: [dict(source_sha256='a' * 64)],
                    checkpoint=lambda: dict(state=dict(pending=None)),
                    history=SimpleNamespace(working_state=dict(revision=0)))
                plan = dict(rehearsal_presentations=0, new_presentations=16,
                    think_act_learn=self.config, hard_end_unix=time.time() + 60, max_sleeps=budget)
                order = Mock()
                order.attach_mock(driver.drain_console, 'console')
                with patch('gpu.orch_r184_think_act_learn.ThinkActLearn', return_value=driver), \
                        patch('gpu.orch_r125_continual_native.finish_sleep', return_value={}) as finish, \
                        patch('gpu.orch_r125_continual_native.fresh_readout') as readout:
                    order.attach_mock(finish, 'complete')
                    order.attach_mock(readout, 'readout')
                    run_loop(Mock(), stream, Mock(), [], plan, self.fixture.root, '/synthetic/plan', 0)
                self.assertEqual(driver.drain_console.call_count, budget - 1)
                expected = ['complete', 'readout'] if budget == 1 else [
                    'complete', 'console', 'readout', 'complete', 'readout']
                self.assertEqual([call[0] for call in order.mock_calls], expected)
