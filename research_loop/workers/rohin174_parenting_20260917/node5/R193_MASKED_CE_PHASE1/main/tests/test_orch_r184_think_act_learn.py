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
from gpu.orch_r189_outcome_allocation import SCHEMA as OUTCOME_SCHEMA, counts
from gpu.orch_r193_continuity import SCHEMA as CONTINUITY_SCHEMA


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
            validate_config(dict(self.config, think_segments=4))

    def test_larger_think_budget_allows_child_to_act_early(self):
        driver = self.driver(['Ready to act.', 'No executable attempt.'])
        driver.config = dict(driver.config, think_segments=3)
        driver.wake()
        self.assertEqual([entry['stage'] for entry in self.records('R184_STAGE')], ['THINK', 'ACT'])
        transition = self.records('R184_TRANSITION')[0]
        self.assertTrue(transition['child_chosen'])
        self.assertEqual(transition['think_segments_used'], 1)
        self.assertEqual(transition['think_segments_budget'], 3)

    def test_thinking_can_continue_then_choose_action_without_parent(self):
        driver = self.driver(['More thought may resolve this.', 'Ready to act.', 'No executable attempt.'])
        driver.config = dict(driver.config, think_segments=3)
        driver.wake()
        self.assertEqual([entry['stage'] for entry in self.records('R184_STAGE')], ['THINK', 'THINK', 'ACT'])
        self.assertEqual(self.records('R184_TRANSITION')[0]['think_segments_used'], 2)
        self.assertTrue(self.records('R184_TRANSITION')[0]['child_chosen'])
        self.assertTrue(any('at most 2 responses left' in message['content'] for message in driver.child.calls[1]))

    def test_exhausted_think_budget_logs_forced_action_once(self):
        driver = self.driver(['More thinking.', 'Still thinking.', 'No executable attempt.'])
        driver.config = dict(driver.config, think_segments=2)
        driver.wake()
        transition = self.records('R184_TRANSITION')[0]
        self.assertFalse(transition['child_chosen'])
        self.assertEqual(transition['cause'], 'forced_stage_budget')
        self.assertEqual(transition['think_segments_used'], 2)
        self.assertEqual(len(self.records('R184_ACT')), 1)

    def test_sleep_notice_reports_actual_copy_presentations(self):
        driver = self.driver(['Ready to act.', 'No tool attempt.', 'Next intention: Test the calculation.'])
        driver.new_presentations = 4
        driver.wake()
        driver.prepare_sleep(1)
        notices = self.records('R184_SLEEP_NOTICE')
        self.assertEqual(notices[-1]['new_presentations'], 4)
        self.assertEqual(notices[-1]['new_rows'], 3)
        self.assertEqual(notices[-1]['selected_old_rows'], 0)

    def test_outcome_policy_is_explicit_and_requires_declared_ceiling(self):
        with self.assertRaises(ValueError):
            validate_config(dict(self.config, outcome_policy=OUTCOME_SCHEMA))
        with self.assertRaises(ValueError):
            validate_config(dict(self.config, think_segments=3, outcome_policy='unregistered'))
        accepted = dict(self.config, think_segments=3, outcome_policy=OUTCOME_SCHEMA)
        self.assertEqual(validate_config(accepted), accepted)

    def test_exit_zero_without_task_evaluator_never_becomes_success(self):
        self.config.update(think_segments=3, outcome_policy=OUTCOME_SCHEMA)
        driver = self.driver(['Ready to act.', '```python\nprint(1)\n```',
                              'Next intention: Obtain a test result.'],
                             lambda origin: dict(status='PUBLISHED', returncode=0, executed=True))
        driver.wake()
        driver.prepare_sleep(1)
        report = self.records('R189_OUTCOME_CYCLE')[0]['report']
        self.assertEqual(report['observation']['unknown'], 1)
        self.assertEqual(report['observation']['successes'], 0)
        self.assertIsNone(report['running_success_rate'])
        self.assertEqual(report['think_token_share'], 0.5)
        learn = self.records('R189_LEARN_ALLOCATION')[0]
        self.assertEqual(learn['stage_tokens'], dict(THINK=2, ACT=2, LEARN=2))
        self.assertAlmostEqual(learn['think_share_including_learn'], 1 / 3)
        self.assertTrue(all(not row['prefix_loss'] and row['target_loss'] for row in self.stream.rows))
        self.assertTrue(all('Outcome-driven allocation:' not in row['target'] for row in self.stream.rows))

    def test_evaluated_success_survives_compaction_sleep_restore_and_reduces_think_ceiling(self):
        self.config.update(think_segments=3, outcome_policy=OUTCOME_SCHEMA)
        responses = ['Ready to act.', '```python\nprint(1)\n```',
                     'Finding: Retain the observed method.'] * 2
        driver = self.driver(responses, lambda origin: dict(status='PUBLISHED'))
        driver.outcome_reader = lambda origin, outcome: dict(
            observation=counts(requested=1, evaluated=1, successes=1), receipt='synthetic:test_receipt')
        for cycle in range(2):
            driver.wake()
            driver.prepare_sleep(cycle + 1)
            source = next(event for event in reversed(self.stream.history.events) if event.actor == 'child')
            self.stream.history.compact(replace(source, event_id=f'synthetic:summary:{cycle}', phase='compaction'),
                through=self.stream.history.frontier())
            self.journal.record('COMPACTION', dict(state=self.stream.checkpoint()))
            receipt = dict(status='COMPLETE', optimizer_steps=48,
                new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
                checkpoint_sha256=dict(adapter='a'*64, optimizer='b'*64, rng='c'*64))
            self.stream.commit_sleep(receipt, self.journal.record)
        checkpoint = self.stream.checkpoint()
        restored = ContinualStream.restore(checkpoint, expected_sha256=checkpoint['sha256'])
        resumed = ThinkActLearn(Child(['Continue thinking.', 'No attempt.']), restored,
            self.journal, self.config)
        self.assertEqual(resumed.allocation.snapshot(), driver.allocation.snapshot())
        resumed.wake()
        transition = self.records('R184_TRANSITION')[-1]
        self.assertEqual(transition['think_segments_budget'], 1)
        self.assertFalse(transition['child_chosen'])
        self.assertTrue(any('small changes' in message['content'] for message in resumed.child.calls[0]))

    def test_failed_evaluator_is_unknown_and_not_retried(self):
        self.config.update(think_segments=3, outcome_policy=OUTCOME_SCHEMA)
        driver = self.driver(['Ready to act.', '```python\nprint(1)\n```'],
                             lambda origin: dict(status='PUBLISHED'))
        calls = []
        def failed(origin, outcome):
            calls.append(origin)
            raise RuntimeError('synthetic evaluator failure')
        driver.outcome_reader = failed
        driver.wake()
        self.assertEqual(len(calls), 1)
        self.assertEqual(driver.last_allocation['evaluation']['status'], 'TASK_EVALUATION_UNKNOWN')
        self.assertEqual(driver.last_allocation['observation']['unknown'], 1)

    def test_continuity_prompt_incorporates_last_think_without_fixed_field_block(self):
        self.config.update(continuity_policy=CONTINUITY_SCHEMA,
            environment_facts='Python standard library and the installed SymPy math package are available.')
        driver = self.driver(['POSSIBILITY [method]: Use a direct numerical check.\nReady to act.',
            'My change is a direct calculation.\n```python\nprint(98 * 30)\n```',
            'EXPERIMENT [method]: No verified result yet; retain the question.'])
        driver.wake()
        driver.prepare_sleep(1)
        act_input = '\n'.join(message['content'] for message in driver.child.calls[1])
        self.assertIn('Use a direct numerical check.', act_input)
        self.assertIn('check in one line', act_input)
        self.assertIn('installed SymPy', act_input)
        self.assertIn('Nothing changed is an acceptable answer',
                      '\n'.join(message['content'] for message in driver.child.calls[0]))
        self.assertNotIn('Investigation: ..., Judgment [name]', act_input)
        state = self.stream.history.working_state
        self.assertTrue(any(entry['text'].startswith('EXPERIMENT [method]:') for entry in state['entries']))
        self.assertIn('POSSIBILITY [method]:', self.stream.rows[0]['target'])
        self.assertIn('EXPERIMENT [method]:', self.stream.rows[-1]['target'])
        self.assertTrue(all(not row['prefix_loss'] and row['target_loss'] for row in self.stream.rows))

    def test_continuity_sleep_never_cuts_think_and_review_has_no_extra_generation_pass(self):
        self.config.update(continuity_policy=CONTINUITY_SCHEMA)
        driver = self.driver(['Ready to act.', 'No attempted code.', 'Nothing changed.'])
        driver.cycle_phase = 'THINK'
        with self.assertRaisesRegex(ValueError, 'sleep_waits_for_complete'):
            driver.prepare_sleep(1)
        driver.wake()
        from unittest.mock import patch
        with patch.object(self.stream.history, 'render', wraps=self.stream.history.render) as render:
            original = self.stream.history.render(driver.child.count_tokens, self.stream.context_limit)
            render.return_value = replace(original, token_count=self.stream.context_limit)
            render.side_effect = [render.return_value, original]
            driver.prepare_sleep(1)
        self.assertEqual([entry['stage'] for entry in self.records('R184_STAGE')], ['THINK', 'ACT', 'LEARN'])
        self.assertEqual(len(driver.child.calls), 3)
        self.assertTrue(self.records('R184_SLEEP_NOTICE')[-1]['compaction'])
        self.assertEqual(self.records('R184_SLEEP_NOTICE')[-1]['reviewed_reflection_ids'], [])

    def test_first_class_dataset_keeps_state_context_and_real_failed_outcome(self):
        from unittest.mock import patch
        self.config.update(continuity_policy=CONTINUITY_SCHEMA)
        parent = TrainEvent(event_id='parent:synthetic:1', actor='parent', split='TRAIN',
            phase='experience', episode_id='continual_stream', source_id='parent:synthetic:receipt',
            source_sha256='a' * 64, origin='TRAIN_COLLECTION', text='Do the chosen check.\n')
        driver = self.driver(['POSSIBILITY [claim]: Test this.\nReady to act.',
            '```python\nprint(1)\n```', 'EXPERIMENT [claim]: The attempt failed; no answer established.'],
            lambda origin: dict(status='PUBLISHED', executed=True,
                                result=dict(returncode=1, stdout='', stderr='synthetic failure')))
        with patch.object(self.journal, 'read_inbox', side_effect=[[parent], [], []]):
            driver.wake()
            driver.prepare_sleep(1)
        rows = list(driver.dataset.iter_rows())
        self.assertEqual([row['stage'] for row in rows], ['THINK', 'ACT', 'LEARN'])
        self.assertEqual(rows[0]['parent_turns'][0]['text'], parent.text)
        self.assertFalse(rows[0]['parent_turns'][0]['target_loss'])
        self.assertEqual(rows[1]['parent_turns'], [])
        self.assertEqual(rows[1]['outcome']['result']['returncode'], 1)
        self.assertEqual(rows[1]['state_before'], rows[0]['state_after'])
        self.assertTrue(rows[1]['transition']['think_to_act']['child_chosen'])
        self.assertEqual(rows[1]['context'], self.stream.rows[1]['prefix'])
        self.assertEqual(rows[2]['target'], self.stream.rows[2]['target'])
        self.assertTrue(all(row['retained_in_weights'] is None for row in rows))

    def test_export_failure_does_not_kill_life_or_replace_the_journal(self):
        from unittest.mock import patch
        self.config.update(continuity_policy=CONTINUITY_SCHEMA)
        driver = self.driver(['Ready to act.', 'No attempted code.', 'Nothing changed.'])
        with patch.object(driver.dataset, 'append', side_effect=OSError('synthetic disk quota')):
            driver.wake()
            driver.prepare_sleep(1)
        self.assertEqual(len(self.records('R191_EXPORT_ERROR')), 3)
        self.assertEqual(len(self.records('RESPONSE')), 3)
        self.assertEqual(len(self.stream.pending_rows()), 3)


if __name__ == '__main__':
    unittest.main()
