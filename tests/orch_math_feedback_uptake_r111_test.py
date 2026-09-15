import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r111_prepare as preparation
from gpu import orch_r110_claude_broker as broker
from organism_v6 import orch_math_feedback_uptake_r111 as policy


class R111F2Tests(unittest.TestCase):
    def setUp(self):
        self.repository = Path(__file__).resolve().parents[1]
        self.task = policy.source.make_task('R111_F2_TRAIN', 1, 0)
        self.task['split'] = 'TRAIN'
        self.events = [dict(actor='child', text='My own recorded attempt.', source_sha256='a' * 64, split='TRAIN')]
        self.request = policy.request('C001_T001', 'R111_F2', 1, 0, 'experience',
            self.task, 'b' * 64, self.events, 1000, 5000)

    def reply(self, silent=False):
        plan, metadata = broker.adapt_plan('[SILENT]' if silent else dict(guidance='Keep that thought alive.',
            tag='ADD', intervention_class='persistence', rationale='Parent-only note.'), 'math', self.task['id'])
        return dict(status='SILENT' if silent else 'COMPLETE', plan=plan, parent_metadata=metadata,
            request_sha256=policy.digest(self.request), actual_model=policy.MEMBERS['FABLE']['model'])

    def test_exact_v2_principles(self):
        self.assertEqual(policy.sha(self.repository / policy.AREA / 'PRINCIPLES_V2.md'), policy.PRINCIPLES_SHA)
        self.assertIn((self.repository / policy.AREA / 'PRINCIPLES_V2.md').read_text(), policy.parent_prompt(self.repository))

    def test_shared_parent_prompt_only_replaces_declared_fields(self):
        template = (self.repository / policy.AREA / 'PARENT_TEMPLATE_V2.txt').read_text()
        rendered = policy.parent_template(self.repository)
        for field in ('GAME', 'STYLE', 'NUDGING', 'FOCUS'):
            self.assertNotIn('[' + field + ']', rendered)
        self.assertIn('[SILENT]', rendered)
        self.assertIn('never let it decide when you speak', rendered)
        self.assertEqual(template.count('[GAME]'), 1)

    def test_exact_three_child_prompts_no_presleep_checklist(self):
        common = policy.contract(self.repository)
        self.assertEqual(set(common['exact_child_prompts']), {'episode', 'presleep', 'reflection'})
        self.assertEqual(policy.PRESLEEP, 'We are about to leave this context; take the space to reflect in your own way.')
        for text in (policy.PRESLEEP, policy.REFLECTION):
            self.assertNotIn('?', text)
            self.assertNotIn('\n', text)
            self.assertNotIn('#', text)
        self.assertNotIn('two', policy.REFLECTION)

    def test_matched_settings_and_truthful_no_sleep(self):
        common = policy.contract(self.repository)
        self.assertEqual(common['episodes_per_cycle'], 2)
        self.assertEqual(common['cadence'], 'after_every_completed_child_segment')
        self.assertEqual(common['weight_updates'], 0)
        self.assertIsNone(common['optimizer'])
        self.assertIsNone(common['adapter'])
        self.assertEqual(set(policy.MEMBERS), {'FABLE', 'ASTRA'})
        self.assertEqual(common['core_native_cap'], 1160)
        self.assertEqual(common['parent_slot_cap'], 384)

    def test_child_decoder_and_guard_scopes(self):
        self.assertEqual(policy.decoder('episode')['max_new_tokens'], 4096)
        self.assertEqual(policy.decoder('held')['max_new_tokens'], 2048)
        for purpose in ('episode', 'held'):
            self.assertEqual(policy.decoder(purpose)['no_repeat_ngram_size'], 0)
        for purpose in ('presleep', 'reflection'):
            self.assertEqual(policy.decoder(purpose)['no_repeat_ngram_size'], 8)
            self.assertFalse(policy.decoder(purpose)['delete_generated_text'])

    def test_fixed_eight_held_and_train_disjoint(self):
        with patch.object(policy, 'CYCLES', 3):
            cohort = policy.cohort({'PRIOR'}, {'a' * 64})
        tasks = cohort['held'] + [task for group in cohort['train'] for task in group]
        self.assertEqual(len(cohort['held']), 8)
        self.assertEqual(len({task['id'] for task in tasks}), 14)
        self.assertEqual(len({task['question_sha256'] for task in tasks}), 14)
        baseline = preparation.sleep0(cohort)
        self.assertEqual(baseline['batch_size'], 8)
        self.assertFalse(baseline['completed'])
        self.assertEqual(baseline['native_calls'], 0)
        self.assertTrue(baseline['fresh_process'] and baseline['context_free'] and baseline['parent_free'])

    def test_cohort_selection_never_reads_outcomes(self):
        with patch.object(policy, 'CYCLES', 1), patch.object(policy.source, 'judge', side_effect=AssertionError):
            self.assertEqual(len(policy.cohort({'PRIOR'}, {'a' * 64})['held']), 8)

    def test_request_matches_actual_hubble_wire(self):
        config = dict(life_id='R111_F2', family='math', train_tasks={self.task['id']:self.task['question_sha256']},
            excluded_task_ids=[], cohort_sha256='b' * 64)
        public = broker.validate_request(self.request, config)
        self.assertEqual(public, self.request['payload'])
        self.assertEqual(self.request['lane_deadline_unix'] - policy.PROVIDER_MARGIN, 1090)
        self.assertEqual(policy.TRANSPORT_CLASSES, broker.CLASSES)

    def test_parent_event_outcome_and_held_rejected(self):
        for addition in ({'outcome': 'INCORRECT'}, {'split': 'HELD'}, {'actor': 'oracle'}):
            events = [dict(self.events[0], **addition)]
            with self.assertRaises(ValueError):
                policy.request('C001_T001', 'R111_F2', 1, 0, 'experience', self.task, 'b' * 64, events, 1000, 5000)

    def test_parent_visibility_contains_no_gold_or_outcome(self):
        serialized = json.dumps(self.request)
        for forbidden in ('"gold"', '"outcome"', '"correct"', '"score"'):
            self.assertNotIn(forbidden, serialized)

    def test_actual_guidance_only_reaches_child(self):
        result = policy.resolve_parent(self.request, self.reply(), 1050, broker.MODEL, archive_verified=True)
        self.assertEqual(result['status'], 'INTERVENTION')
        self.assertEqual(result['guidance'], 'Keep that thought alive.')
        self.assertNotIn('Parent-only', result['guidance'])

    def test_silent_valid_does_not_stop_or_emit_sentinel(self):
        result = policy.resolve_parent(self.request, self.reply(True), 1050, broker.MODEL, archive_verified=True)
        self.assertEqual(result['status'], 'SILENT')
        self.assertEqual(result['guidance'], '')
        self.assertTrue(result['continue_child'])

    def test_missing_failed_late_or_malformed_always_continues(self):
        variants = [(None, 1120), ({'status': 'MISSING'}, 1050), (self.reply(), 1120),
            (dict(self.reply(), plan='bad'), 1050)]
        for reply, now in variants:
            result = policy.resolve_parent(self.request, reply, now, broker.MODEL, archive_verified=True)
            self.assertEqual(result['status'], 'MISSING')
            self.assertTrue(result['continue_child'])
            self.assertFalse(result['apply_to_later_turn'])

    def test_source_model_archive_mismatch_never_applied(self):
        for reply, verified in [(dict(self.reply(), actual_model='other'), True),
                (dict(self.reply(), request_sha256='wrong'), True), (self.reply(), False)]:
            self.assertEqual(policy.resolve_parent(self.request, reply, 1050, broker.MODEL, verified)['status'], 'MISSING')

    def test_r112_silence_window_and_fable_self_approval_not_go(self):
        release = dict(released=True, uuid=policy.MEMBERS['FABLE']['uuid'])
        for grace in ({}, dict(review_grace_confirmed=True, confirmed_by='Fable'),
                dict(approved_by='Fable', relayed_by='Fable', decision='GO',
                    common_contract_sha256='same', source_reference='self')):
            with self.assertRaises(ValueError):
                policy.require_launch_permission('FABLE', release, grace, 'same')

    def test_exact_rohin_go_and_release_both_required(self):
        gate = dict(approved_by='Rohin', relayed_by='Fable', decision='GO',
            common_contract_sha256='same', source_reference='exact relay')
        with self.assertRaises(ValueError):
            policy.require_launch_permission('FABLE', {}, gate, 'same')
        policy.require_launch_permission('FABLE', dict(released=True,
            uuid=policy.MEMBERS['FABLE']['uuid']), gate, 'same')

    def test_astra_not_waiting_for_fable_but_needs_cicero_release(self):
        with self.assertRaises(ValueError):
            policy.require_launch_permission('ASTRA', {}, {}, 'same')
        policy.require_launch_permission('ASTRA', dict(released=True,
            uuid=policy.MEMBERS['ASTRA']['uuid']), {}, 'same')


if __name__ == '__main__':
    unittest.main()
