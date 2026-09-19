"""CPU-only synthetic stage, provenance, state-carry and failure checks."""

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

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
        self.directory = tempfile.TemporaryDirectory(dir='/tmp')
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

    def test_explicit_nfkc_policy_reaches_cpu_dispatch_without_changing_default(self):
        from gpu.orch_r153_code_blocks import NFKC_POLICY
        self.config['code_policy'] = NFKC_POLICY
        driver = self.driver([])
        with patch('gpu.orch_r153_community_transport.cpu_once', return_value={'status': 'SYNTHETIC'}) as cpu:
            driver._cpu({'kind': 'TRAIN_CHILD_RESPONSE', 'record_index': 1, 'record_sha256': 'a' * 64})
        self.assertEqual(cpu.call_args.kwargs['code_policy'], NFKC_POLICY)
        self.assertTrue(cpu.call_args.kwargs['start'])
        with self.assertRaisesRegex(ValueError, 'known_code_policy'):
            validate_config(dict(self.config, code_policy='implicit_repair'))

    def test_judgment_first_is_explicit_and_keeps_continuation_prompts(self):
        from gpu.orch_r184_think_act_learn import JUDGMENT_POLICY
        self.config.update(continuity_policy=CONTINUITY_SCHEMA, judgment_policy=JUDGMENT_POLICY)
        driver = self.driver(['Ready to act.', 'No attempt made.'])
        driver.wake()
        prompt = driver.child.calls[0][-1]['content']
        self.assertIn('Runtime status: THINK. First, judge your last attempt:', prompt)
        self.assertLess(prompt.index('First, judge your last attempt:'), prompt.index('Before continuing'))
        self.assertIn('what actual receipt supports that judgment?', prompt)
        self.assertIn('Nothing changed is an acceptable answer.', prompt)
        self.assertIn('actually incorporates', driver.child.calls[-1][-1]['content'])
        original = stage_prompt('THINK', 'explicit', continuity_policy=CONTINUITY_SCHEMA)
        self.assertNotIn('First, judge your last attempt:', original)
        self.assertIn('worked hand calculation', driver.child.calls[-1][-1]['content'])
        self.assertEqual(self.records('R184_ACT')[0]['outcome']['status'], 'LANGUAGE_RESPONSE_UNVERIFIED')
        for stage in ('LEARN',):
            self.assertEqual(stage_prompt(stage, 'explicit', continuity_policy=CONTINUITY_SCHEMA),
                stage_prompt(stage, 'explicit', continuity_policy=CONTINUITY_SCHEMA,
                    judgment_policy=JUDGMENT_POLICY))
        with self.assertRaisesRegex(ValueError, 'known_judgment_policy'):
            validate_config(dict(self.config, judgment_policy='unversioned'))

    def test_structured_think_is_opt_in_masked_and_keeps_act_and_learn_unchanged(self):
        from gpu.orch_r184_think_act_learn import JUDGMENT_POLICY, STRUCTURED_THINK_POLICY
        self.config.update(continuity_policy=CONTINUITY_SCHEMA, judgment_policy=JUDGMENT_POLICY,
            structured_think_policy=STRUCTURED_THINK_POLICY)
        driver = self.driver(['Ready to act.', 'An actual three-paragraph draft remains unfinished.'])
        driver.wake()
        prompt = driver.child.calls[0][-1]['content']
        self.assertIn('Runtime status: THINK. First, judge your last attempt:', prompt)
        self.assertLess(prompt.index('First, judge your last attempt:'),
            prompt.index('Structured THINK experiment:'))
        self.assertIn('move from wide to narrow and back to wide', prompt)
        self.assertIn('one sentence per top-level question', prompt)
        self.assertIn('free flow inside relevant narrow notes', prompt)
        self.assertIn('what small change will I make now?', prompt)
        self.assertIn('Parent conversation is THINK', prompt)
        self.assertNotIn('Structured THINK experiment:', driver.child.calls[-1][-1]['content'])
        self.assertNotIn('Structured THINK experiment:', stage_prompt('THINK', 'explicit',
            continuity_policy=CONTINUITY_SCHEMA, judgment_policy=JUDGMENT_POLICY))
        for stage in ('ACT', 'LEARN'):
            self.assertEqual(stage_prompt(stage, 'explicit', continuity_policy=CONTINUITY_SCHEMA,
                judgment_policy=JUDGMENT_POLICY), stage_prompt(stage, 'explicit',
                continuity_policy=CONTINUITY_SCHEMA, judgment_policy=JUDGMENT_POLICY,
                structured_think_policy=STRUCTURED_THINK_POLICY))
        for row in self.stream.rows:
            self.assertFalse(row['prefix_loss'])
            self.assertTrue(row['target_loss'])
            self.assertNotIn('Structured THINK experiment:', row['target'])
        self.assertEqual(self.records('R184_TRANSITION')[0]['cause'], 'child_ready')

    def test_structured_think_rejects_unknown_or_missing_judgment_policy(self):
        from gpu.orch_r184_think_act_learn import JUDGMENT_POLICY, STRUCTURED_THINK_POLICY
        for structured, judgment in ((STRUCTURED_THINK_POLICY, None), ('unversioned', JUDGMENT_POLICY)):
            with self.subTest(structured=structured, judgment=judgment):
                with self.assertRaisesRegex(ValueError, 'versioned_structured_think_requires_judgment_first'):
                    validate_config(dict(self.config, structured_think_policy=structured,
                        **({'judgment_policy': judgment} if judgment else {})))
                with self.assertRaisesRegex(ValueError, 'versioned_structured_think_requires_judgment_first'):
                    stage_prompt('THINK', 'explicit', judgment_policy=judgment,
                        structured_think_policy=structured)

    def test_r203_limits_autonomous_think_and_explains_state_capacity(self):
        from gpu.orch_r184_think_act_learn import STAGE_BOUNDARY_POLICY
        self.config.update(think_segments=3, stage_boundary_policy=STAGE_BOUNDARY_POLICY)
        driver = self.driver(['Consider the uncertainty.', 'Choose a small attempt.', 'A language attempt.'])
        driver.wake()
        self.assertEqual([item['stage'] for item in self.records('R184_STAGE')], ['THINK', 'THINK', 'ACT'])
        self.assertEqual(self.records('R184_TRANSITION')[0]['think_segments_budget'], 2)
        self.assertEqual(self.records('R184_TRANSITION')[0]['cause'], 'forced_stage_budget')
        self.assertIn('2048 UTF-8 bytes including source metadata', driver.child.calls[0][-1]['content'])
        self.assertIn('No fixed field block is required', driver.child.calls[0][-1]['content'])

    def test_r203_defers_actual_rohin_question_out_of_learn_until_think(self):
        from gpu.orch_r127_pilot_console import publish_parent
        from gpu.orch_r184_think_act_learn import STAGE_BOUNDARY_POLICY
        self.config['stage_boundary_policy'] = STAGE_BOUNDARY_POLICY
        driver = self.driver(['Ready to act.', 'My actual attempt.', 'Review only the attempt.',
            'These are my own conclusions.'])
        driver.wake()
        question = 'Who do you want to be, and what are your own conclusions?'
        publish_parent(self.root, 'Rohin', question)
        driver.prepare_sleep(1)
        self.assertNotIn(question, str(driver.child.calls[-1]))
        self.assertEqual(self.records('R203_CONSOLE_DEFERRED')[0]['destination'], 'NEXT_THINK')
        driver.generate_stage('THINK')
        self.assertIn(question, str(driver.child.calls[-1]))
        self.assertIn('Answer Rohin\'s actual latest questions', driver.child.calls[-1][-1]['content'])
        self.assertNotIn(question, driver.stream.rows[-1]['target'])
        self.assertFalse(driver.stream.rows[-1]['prefix_loss'])

    def test_r204_one_think_default_without_explicit_extension(self):
        from gpu.orch_r184_think_act_learn import STAGE_BOUNDARY_POLICY, THINK_CONTINUATION_POLICY
        self.config.update(think_segments=3, stage_boundary_policy=STAGE_BOUNDARY_POLICY,
            think_continuation_policy=THINK_CONTINUATION_POLICY)
        driver = self.driver(['I should attempt the small calculation.', 'The actual attempt.'])
        driver.wake()
        self.assertEqual([item['stage'] for item in self.records('R184_STAGE')], ['THINK', 'ACT'])
        self.assertEqual(self.records('R184_TRANSITION')[0]['cause'], 'default_action_boundary')

    def test_r205_console_reply_precedes_each_stage_and_never_executes_its_code(self):
        from gpu.orch_r127_pilot_console import publish_parent
        from gpu.orch_r184_think_act_learn import CONSOLE_REPLY_POLICY, STAGE_BOUNDARY_POLICY
        self.config.update(stage_boundary_policy=STAGE_BOUNDARY_POLICY,
            console_reply_policy=CONSOLE_REPLY_POLICY, continuity_policy=CONTINUITY_SCHEMA)
        calls = []
        driver = self.driver(['```python\nprint("message only")\n```', 'Ready to act.',
            'My answer before the attempt.', '```python\nprint("real attempt")\n```',
            'My answer before review.', 'Review of the actual result.'],
            lambda origin: calls.append(origin) or dict(status='SYNTHETIC', executed=False))
        for stage in ('THINK', 'ACT', 'LEARN'):
            question = f'Rohin question arriving before {stage}: what do you conclude?'
            publish_parent(self.root, 'Rohin', question)
            before = len(driver.child.calls)
            if stage == 'ACT':
                driver.act()
            elif stage == 'LEARN':
                driver.prepare_sleep(1)
            else:
                driver.generate_stage(stage)
            prompt = driver.child.calls[before][-1]['content']
            self.assertIn('Runtime status: ACT — reply to Rohin.', prompt)
            self.assertIn(question, prompt)
            self.assertNotIn('Protect this sleep:', prompt)
            self.assertNotIn('Structured THINK experiment:', prompt)
            reply = self.records('R205_CONSOLE_REPLY')[-1]
            self.assertEqual(reply['interrupted_stage'], stage)
            self.assertFalse(reply['outcome']['human_read_confirmed'])
            self.assertFalse(reply['outcome']['tool_execution_allowed'])
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(self.records('R205_CONSOLE_REPLY')), 3)
        self.assertEqual([item['stage'] for item in self.records('R184_STAGE')],
            ['ACT', 'THINK', 'ACT', 'ACT', 'ACT', 'LEARN'])
        reply_indices = {item['response_origin']['record_index'] for item in self.records('R205_CONSOLE_REPLY')}
        self.assertNotIn(calls[0]['record_index'], reply_indices)
        self.assertTrue(all(not row['prefix_loss'] and row['target_loss'] for row in self.stream.rows))
        self.assertEqual(sum(item.get('action_policy') == CONSOLE_REPLY_POLICY
            for item in self.records('REQUEST')), 3)
        driver.child.outputs = iter(['Ordinary later thought.'])
        driver.generate_stage('THINK')
        self.assertEqual(len(self.records('R205_CONSOLE_REPLY')), 3)

    def test_r205_astra_is_not_rohin_and_ordinary_tool_origin_still_works(self):
        from gpu.orch_r127_pilot_console import publish_parent
        from gpu.orch_r184_think_act_learn import CONSOLE_REPLY_POLICY, STAGE_BOUNDARY_POLICY
        self.config.update(stage_boundary_policy=STAGE_BOUNDARY_POLICY, console_reply_policy=CONSOLE_REPLY_POLICY)
        publish_parent(self.root, 'Astra', 'Rohin: this is quoted text, not a Rohin turn.')
        driver = self.driver(['Ready to act.', '```python\nprint(42)\n```'])
        driver.wake()
        self.assertEqual(self.records('R205_CONSOLE_REPLY'), [])
        self.assertEqual([item['stage'] for item in self.records('R184_STAGE')], ['THINK', 'ACT'])
        from gpu.orch_r125_cpu_experiment import verify_origin
        from gpu.orch_r153_code_blocks import NFKC_POLICY
        proof = verify_origin(dict(origin=driver.last_response, source='print(42)\n'),
            self.root, code_policy=NFKC_POLICY)
        self.assertTrue(proof['child_generated'])

    def test_r205_console_reply_origin_is_refused_by_cpu_and_community(self):
        from gpu.orch_r127_pilot_console import publish_parent
        from gpu.orch_r184_think_act_learn import CONSOLE_REPLY_POLICY, STAGE_BOUNDARY_POLICY
        from gpu.orch_r125_cpu_experiment import verify_origin
        from gpu.orch_r153_community_exchange import verify_snapshot
        from gpu.orch_r153_code_blocks import NFKC_POLICY
        self.config.update(stage_boundary_policy=STAGE_BOUNDARY_POLICY, console_reply_policy=CONSOLE_REPLY_POLICY)
        publish_parent(self.root, 'Rohin', 'Tell me what you would do, without doing it.')
        driver = self.driver(['```python\nprint(42)\n```', 'Ready to act.'])
        driver.generate_stage('THINK')
        origin = self.records('R205_CONSOLE_REPLY')[0]['response_origin']
        with self.assertRaisesRegex(ValueError, 'console_reply_is_not_a_tool_action'):
            verify_origin(dict(origin=origin, source='print(42)\n'), self.root, code_policy=NFKC_POLICY)
        snapshot = dict(manifest=json.loads((self.root / 'stream/JOURNAL.json').read_text()),
            records=[json.loads((self.root / 'stream/records' / f'{index:020d}.json').read_text())
                for index in range(origin['record_index'] - 1, origin['record_index'] + 2)])
        with self.assertRaisesRegex(ValueError, 'console_reply_is_not_a_tool_action'):
            verify_snapshot('C2', snapshot['manifest']['journal_id'], origin, snapshot, {}, lambda raw: {})

    def test_r205_console_policy_cannot_disable_boundary_compaction(self):
        from gpu.orch_r184_think_act_learn import CONSOLE_REPLY_POLICY
        with self.assertRaisesRegex(ValueError, 'console_reply_requires_stage_boundaries'):
            validate_config(dict(self.config, console_reply_policy=CONSOLE_REPLY_POLICY))

    def test_r206_pins_old_and_new_genuine_rohin_messages_without_reanswering_old_ones(self):
        from gpu.orch_r127_pilot_console import publish_parent
        from gpu.orch_r184_think_act_learn import CONSOLE_REPLY_POLICY, STAGE_BOUNDARY_POLICY
        from gpu.orch_r206_pinned_messages import POLICY as PINNED_POLICY
        from organism_v6.orch_r125_plain_context import VERSION, replay_prefix
        self.config.update(stage_boundary_policy=STAGE_BOUNDARY_POLICY, console_reply_policy=CONSOLE_REPLY_POLICY)
        old = 'Keep my exact source_sha256\nwording and spacing. '
        publish_parent(self.root, 'Rohin', old)
        driver = self.driver(['My reply.', 'Ready to act.'])
        driver.generate_stage('THINK')
        source = next(event for event in reversed(self.stream.history.events) if event.actor == 'child')
        self.stream.history.compact(replace(source, event_id='summary:before_pin', phase='compaction'),
            through=self.stream.history.frontier())
        self.journal.record('COMPACTION', dict(kind='SYNTHETIC_PRIOR_COMPACTION', state=self.stream.checkpoint()))
        self.config['pinned_messages_policy'] = PINNED_POLICY
        driver = self.driver(['Ordinary later thought.'])
        driver.generate_stage('THINK')
        self.assertEqual(len(self.records('R205_CONSOLE_REPLY')), 1)
        rendered = self.stream.history.render(driver.child.count_tokens, 8192,
            presentation=dict(version=VERSION, system_prompt='System.', birth_prompt='Birth.'))
        pinned_text = 'Rohin: ' + old
        self.assertEqual(sum(message['content'] == pinned_text for message in rendered.messages), 1)
        replayed = replay_prefix(rendered.messages,
            dict(version=VERSION, system_prompt='System.', birth_prompt='Birth.'))
        self.assertIn(pinned_text, [message['content'] for message in replayed])
        restored = ContinualStream.restore(self.stream.checkpoint(), expected_sha256=self.stream.checkpoint()['sha256'])
        self.assertEqual(restored.history.checkpoint()['pinned_parent_event_ids'],
            self.stream.history.checkpoint()['pinned_parent_event_ids'])
        publish_parent(self.root, 'Astra', 'Rohin: I am not actually Rohin.')
        publish_parent(self.root, 'Rohin', 'A new real question.')
        driver.child.outputs = iter(['My new direct answer.', 'Ready to act.'])
        driver.generate_stage('THINK')
        self.assertEqual(len(self.records('R205_CONSOLE_REPLY')), 2)
        self.assertEqual(len(self.stream.history.checkpoint()['pinned_parent_event_ids']), 2)

    def test_r204_explicit_uncertainty_allows_one_bounded_think_extension(self):
        from gpu.orch_r184_think_act_learn import STAGE_BOUNDARY_POLICY, THINK_CONTINUATION_POLICY
        self.config.update(think_segments=3, stage_boundary_policy=STAGE_BOUNDARY_POLICY,
            think_continuation_policy=THINK_CONTINUATION_POLICY)
        driver = self.driver(['Continue thinking: Which observation would distinguish the cases?',
            'Continue thinking: I still have another alternative.', 'The actual attempt.'])
        driver.wake()
        self.assertEqual([item['stage'] for item in self.records('R184_STAGE')], ['THINK', 'THINK', 'ACT'])
        transition = self.records('R184_TRANSITION')[0]
        self.assertEqual(transition['cause'], 'forced_stage_budget')
        self.assertEqual(len(transition['continuation_requests']), 2)
        self.assertEqual(transition['think_segments_used'], 2)

    def test_r203_outcome_guidance_reports_the_enforced_think_limit(self):
        from gpu.orch_r184_think_act_learn import EFFORT_POLICY, STAGE_BOUNDARY_POLICY
        self.config.update(think_segments=3, outcome_policy=OUTCOME_SCHEMA,
            effort_policy=EFFORT_POLICY, stage_boundary_policy=STAGE_BOUNDARY_POLICY)
        driver = self.driver([])
        for unused in range(3):
            driver.allocation.record(self.config['trial_id'], counts(requested=1, evaluated=1))
        guidance = driver.effort_guidance()
        self.assertEqual(guidance['mode'], 'SUSTAINED_FAILURE')
        self.assertEqual(guidance['think_segments_budget'], 2)
        self.assertIn('at most two consecutive autonomous THINK', guidance['instruction'])

    def test_learn_review_veto_binds_raw_pending_rows_before_commit(self):
        from organism_v6.orch_r194_code_target_filter import REVIEW_POLICY, filter_learn_review_targets
        self.config['learn_review_filter'] = REVIEW_POLICY
        driver = self.driver(['Ready to act.', 'No attempt made.',
            'Do not train: row 1 — I claimed no concrete action.\n'
            'Do not train: self — This review is administrative.\n'
            'Do not train: row 999 — This row does not exist.'])
        driver.wake()
        before = [dict(row) for row in self.stream.pending_rows()]
        driver.prepare_sleep(1)
        rows = self.stream.pending_rows()
        self.assertEqual(rows[:2], before)
        self.assertEqual(rows[-1]['learn_review']['candidate_source_sha256'],
            [row['source_sha256'] for row in rows])
        self.assertIn('Protect this sleep:', driver.child.calls[-1][-1]['content'])
        self.assertIn('Do not train: self', driver.child.calls[-1][-1]['content'])
        kept, old, proof = filter_learn_review_targets(rows, [], REVIEW_POLICY)
        self.assertEqual([row['segment'] for row in kept], [0])
        self.assertEqual(old, [])
        self.assertEqual(proof['excluded_counts']['NEW'], 2)
        self.assertEqual(proof['reviews'][0]['rejected'][0]['reason'], 'unknown_or_out_of_batch_segment')
        self.assertEqual(self.records('R195_LEARN_REVIEW')[0]['proof'], proof)
        self.journal.close()
        with StreamJournal(self.root / 'stream') as reopened:
            restored = ContinualStream.restore(**reopened.latest_checkpoint())
        self.assertEqual(restored.rows, self.stream.rows)
        self.assertEqual(restored.rows[-1]['target'], rows[-1]['target'])

    def test_learn_review_remains_opt_in(self):
        driver = self.driver(['Ready to act.', 'No attempt.', 'Do not train: self — Not enabled.'])
        driver.wake()
        driver.prepare_sleep(1)
        self.assertNotIn('learn_review', self.stream.rows[-1])
        self.assertEqual(self.records('R195_LEARN_REVIEW'), [])
        with self.assertRaisesRegex(ValueError, 'known_learn_review_filter_policy'):
            validate_config(dict(self.config, learn_review_filter='unknown'))

    def test_correction_ledger_preserves_raw_fault_and_restores_without_claiming_intentions(self):
        from gpu.orch_r197_correction_ledger import SCHEMA as CORRECTION_SCHEMA
        self.config['correction_ledger'] = CORRECTION_SCHEMA
        driver = self.driver(['Ready to act.', '```python\nprint(９８)\n```', 'No result obtained.'])
        driver.wake()
        ledger = self.records('R197_CORRECTION_CYCLE')[0]['ledger']
        self.assertEqual(ledger['cycles'][0]['raw_check']['fault_present'], 'YES')
        self.assertFalse(ledger['causality_claimed'])
        self.assertEqual(ledger['retained_in_weights'], 'UNKNOWN')
        self.assertTrue((self.journal.root / 'correction_ledger.json').exists())
        driver.prepare_sleep(1)
        restored = self.driver([])
        self.assertEqual(restored.corrections, ledger)
        self.assertEqual(restored.correction_parents, [])
        self.assertIn('９８', self.stream.rows[1]['target'])
        self.assertNotIn('R197_CORRECTION_LEDGER', self.stream.rows[1]['target'])
        with self.assertRaisesRegex(ValueError, 'known_correction_ledger'):
            validate_config(dict(self.config, correction_ledger='unversioned'))

    def test_correction_cache_failure_does_not_invent_a_clean_history(self):
        from gpu.orch_r197_correction_ledger import SCHEMA as CORRECTION_SCHEMA
        self.config['correction_ledger'] = CORRECTION_SCHEMA
        (self.journal.root / 'correction_ledger.json').write_text('{broken')
        driver = self.driver([])
        self.assertIsNone(driver.corrections)
        self.assertTrue(self.records('R197_STATE_CACHE_ERROR')[0]['correction_history_unknown'])

    def test_outcome_effort_is_parameterized_and_does_not_change_sleep_dose(self):
        from gpu.orch_r184_think_act_learn import EFFORT_POLICY
        self.config.update(outcome_policy=OUTCOME_SCHEMA, think_segments=3, effort_policy=EFFORT_POLICY)
        driver = self.driver([])
        self.assertEqual(driver.effort_guidance()['think_segments_budget'], 3)
        for unused in range(3):
            driver.allocation.record(self.config['trial_id'], counts(requested=1, evaluated=1, successes=1))
        self.assertEqual(driver.effort_guidance()['mode'], 'CONSOLIDATE_SUCCESS')
        self.assertEqual(driver.effort_guidance()['think_segments_budget'], 2)
        self.assertEqual(driver.new_presentations, 16)
        for unused in range(3):
            driver.allocation.record(self.config['trial_id'], counts(requested=1, evaluated=1))
        self.assertEqual(driver.effort_guidance()['mode'], 'SUSTAINED_FAILURE')
        self.assertEqual(driver.effort_guidance()['think_segments_budget'], 3)
        self.assertIn('alternative approaches', driver.effort_guidance()['instruction'])
        invalid = dict(self.config)
        invalid.pop('outcome_policy')
        with self.assertRaisesRegex(ValueError, 'versioned_effort_policy'):
            validate_config(invalid)

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
