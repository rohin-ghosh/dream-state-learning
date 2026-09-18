"""CPU-only synthetic stage, provenance, state-carry and failure checks."""

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import time
import unittest

from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r184_think_act_learn import (
    SCHEMA, ThinkActLearn, consolidate, ready_to_act, reflection_events, runtime_event,
    stage_prompt, state_delta, validate_config,
)
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest


class Child:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def count_tokens(self, messages):
        return sum(len(message['content'].split()) + 4 for message in messages)

    def generate(self, messages, **limits):
        self.calls.append(messages)
        return dict(raw=next(self.outputs), token_ids=[10, 2], terminal=True, truncated=False)


class ThinkActLearnTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.addCleanup(self.journal.close)
        self.stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Investigate sums.'),
            context_limit=8192, segment_tokens=1024, segments_per_sleep=2,
            deadline_unix=time.time() + 600, model_state_sha256='f' * 64, allow_eviction=True)
        self.config = dict(schema=SCHEMA, trial_id='synthetic_cpu_only', reflection_policy='explicit',
            think_segments=1, cpu_gate_root='/synthetic/not_dispatched/gate', cpu_gate_sha256='e' * 64)
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))

    def driver(self, outputs, executor=None):
        child = Child(outputs)
        return ThinkActLearn(child, self.stream, self.journal, self.config,
            executor=executor or (lambda origin: dict(status='SYNTHETIC_NO_REAL_EXECUTION', executed=False)))

    def records(self, kind):
        return [json.loads(path.read_text())['document']
            for path in sorted((self.root / 'stream/records').glob('*.json'))
            if '.intent.' not in path.name and json.loads(path.read_text())['kind'] == kind]

    def test_think_act_learn_has_bound_origins_masked_notices_and_child_state(self):
        calls = []
        driver = self.driver([
            'Finding [sum]: Three cases agree.\nUncertainty: Generality is unproved.\n'
            'Next intention: Test n=4.\nReady to act.',
            '```python\nprint(sum(range(1, 5)))\n```',
            'Judgment: No real result was obtained.\nNext intention: Obtain actual feedback next.'
        ], lambda origin: calls.append(origin) or dict(status='SYNTHETIC_NO_REAL_EXECUTION', executed=False))
        outcome = driver.wake()
        driver.prepare_sleep(1)
        self.assertFalse(outcome['executed'])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['kind'], 'TRAIN_CHILD_RESPONSE')
        self.assertEqual([entry['stage'] for entry in self.records('R184_STAGE')], ['THINK', 'ACT', 'LEARN'])
        self.assertEqual(self.records('R184_TRANSITION')[0]['cause'], 'child_ready')
        self.assertEqual(len(self.stream.pending_rows()), 3)
        for row in self.stream.rows:
            self.assertFalse(row['prefix_loss'])
            self.assertTrue(row['target_loss'])
            self.assertNotIn('Runtime status:', row['target'])
        self.assertIn('Runtime status: THINK', self.stream.rows[0]['prefix'][-1]['content'])
        self.assertTrue(any('Runtime status: ACT' in message['content']
            for message in self.stream.rows[1]['prefix']))
        self.assertTrue(any('No successful execution is established' in message['content']
            for message in driver.child.calls[-1]))
        latest = self.journal.latest_checkpoint()
        restored = ContinualStream.restore(**latest)
        self.assertEqual(restored.history.working_state, self.stream.history.working_state)
        self.assertEqual(restored.history.working_state['revision'], 2)
        self.assertEqual(self.records('R184_SLEEP_NOTICE')[0]['selected_old_rows'], 0)

    def test_think_code_is_not_executed_and_missing_readiness_is_forced(self):
        calls = []
        driver = self.driver(['```python\nprint("only thinking")\n```', 'I have not made an attempt.'],
            lambda origin: calls.append(origin))
        self.assertEqual(driver.wake()['status'], 'NO_CPU_ATTEMPT')
        self.assertEqual(calls, [])
        transition = self.records('R184_TRANSITION')[0]
        self.assertFalse(transition['child_chosen'])
        self.assertEqual(transition['cause'], 'forced_stage_budget')

    def test_unknown_tool_outcome_is_kept_and_never_retried(self):
        calls = []
        def unknown(origin):
            calls.append(origin)
            raise TimeoutError('synthetic fixture, not a live provider or executor failure')
        driver = self.driver(['Ready to act.', '```python\nprint(1)\n```'], unknown)
        self.assertIsNone(driver.wake()['executed'])
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.records('R184_ACT')[0]['outcome']['status'], 'TOOL_OUTCOME_UNKNOWN_NO_RETRY')

    def test_readiness_does_not_invent_transition_from_negation_or_example(self):
        self.assertTrue(ready_to_act('I am ready to act.'))
        self.assertTrue(ready_to_act('Ｒｅａｄｙ ｔｏ ａｃｔ．'))
        self.assertFalse(ready_to_act('I am not ready to act.'))
        self.assertFalse(ready_to_act('Example: Ready to act.'))
        self.assertFalse(ready_to_act('```text\nReady to act.\n```'))

    def test_optional_state_spans_are_exact_and_code_examples_are_ignored(self):
        source = TrainEvent(event_id='child:example', actor='child', split='TRAIN', phase='experience',
            episode_id='continual_stream', source_id='response:example', source_sha256='d' * 64,
            origin='TRAIN_COLLECTION', text='**Finding [sum]**：  Exact α text.\n'
                '```python\nNote: not state\n```\nNext intention: Check a value.\n')
        self.stream.history.append(source)
        spans, deleted = state_delta(source)
        self.assertEqual(deleted, [])
        self.assertEqual([source.text[span.start:span.end] for span in spans],
                         ['Exact α text.', 'Check a value.'])
        self.assertEqual(consolidate(self.stream.history, source)['status'], 'UPDATED')
        self.assertEqual(consolidate(self.stream.history, source)['status'], 'ALREADY_APPLIED')
        self.assertEqual(consolidate(self.stream.history, replace(source, actor='parent'))['status'],
                         'REJECTED_PRIOR_STATE_RETAINED')

    def test_working_state_is_preserved_through_compaction_and_actual_sleep_checkpoint(self):
        driver = self.driver(['Finding [kept]: Preserve this finding.\nReady to act.',
                              'No code attempted.', 'My next step needs actual evidence.'])
        driver.wake()
        driver.prepare_sleep(1)
        source = self.stream.history.events[-2]
        summary = replace(source, event_id='summary:synthetic', phase='compaction')
        before = self.stream.history.working_state
        self.stream.history.compact(summary, through=self.stream.history.frontier(len(self.stream.history.events)-1))
        self.journal.record('COMPACTION', dict(state=self.stream.checkpoint()))
        receipt = dict(status='COMPLETE', optimizer_steps=48,
            new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
            checkpoint_sha256=dict(adapter='a'*64, optimizer='b'*64, rng='c'*64))
        self.stream.commit_sleep(receipt, self.journal.record)
        self.journal.close()
        with StreamJournal(self.root / 'stream') as reopened:
            restored = ContinualStream.restore(**reopened.latest_checkpoint())
        self.assertEqual(restored.history.working_state, before)
        self.assertEqual(restored.pending_rows(), [])
        visible = restored.history.render(driver.child.count_tokens, 8192)
        self.assertTrue(any('Preserve this finding.' in message['content'] for message in visible.messages))
        self.assertTrue(all(label == -100 for label in visible.labels))

    def test_reflection_archive_excludes_parent_text_and_act(self):
        driver = self.driver(['This is a reflection. Ready to act.', 'This is an action without a tool.'])
        driver.wake()
        self.assertEqual([event.text for event in reflection_events(self.stream.history)],
                         ['This is a reflection. Ready to act.'])

    def test_next_cycle_starts_without_a_new_parent_instruction(self):
        driver = self.driver(['Finding: Keep the observation.\nReady to act.', 'No attempt yet.',
                              'Next intention: Obtain feedback.', 'Ready to act.', 'No code this time.'])
        driver.wake()
        driver.prepare_sleep(1)
        receipt = dict(status='COMPLETE', optimizer_steps=48,
            new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
            checkpoint_sha256=dict(adapter='a'*64, optimizer='b'*64, rng='c'*64))
        self.stream.commit_sleep(receipt, self.journal.record)
        driver.wake()
        self.assertEqual([entry['stage'] for entry in self.records('R184_STAGE')],
                         ['THINK', 'ACT', 'LEARN', 'THINK', 'ACT'])
        self.assertFalse(any(event.actor == 'parent' for event in self.stream.history.events))
        self.assertTrue(any('Obtain feedback.' in message['content'] for message in driver.child.calls[3]))

    def test_state_overflow_is_reported_without_erasing_prior_state(self):
        source = TrainEvent(event_id='child:original', actor='child', split='TRAIN', phase='experience',
            episode_id='continual_stream', source_id='response:original', source_sha256='d'*64,
            origin='TRAIN_COLLECTION', text='Finding: Keep this.')
        self.stream.history.append(source)
        self.assertEqual(consolidate(self.stream.history, source)['status'], 'UPDATED')
        before = self.stream.history.working_state
        oversized = replace(source, event_id='child:oversized', source_id='response:oversized',
            source_sha256='e'*64, text='Finding: ' + 'a' * 4096)
        self.stream.history.append(oversized)
        self.assertEqual(consolidate(self.stream.history, oversized)['status'], 'REJECTED_PRIOR_STATE_RETAINED')
        self.assertEqual(self.stream.history.working_state, before)

    def test_comparison_changes_only_reflection_prompt(self):
        self.assertNotEqual(stage_prompt('THINK', 'brief'), stage_prompt('THINK', 'explicit'))
        self.assertEqual(stage_prompt('ACT', 'brief'), stage_prompt('ACT', 'explicit'))
        self.assertEqual(stage_prompt('LEARN', 'brief'), stage_prompt('LEARN', 'explicit'))
        self.assertEqual(validate_config(self.config), self.config)
        with self.assertRaises(ValueError):
            validate_config(dict(self.config, think_segments=2))

    def test_sleep_notice_reports_actual_copy_presentations(self):
        driver = self.driver(['Ready to act.', 'No tool attempt.', 'Next intention: Test the calculation.'])
        driver.new_presentations = 4
        driver.wake()
        driver.prepare_sleep(1)
        notices = self.records('R184_SLEEP_NOTICE')
        self.assertEqual(notices[-1]['new_presentations'], 4)
        self.assertEqual(notices[-1]['new_rows'], 3)
        self.assertEqual(notices[-1]['selected_old_rows'], 0)


if __name__ == '__main__':
    unittest.main()
