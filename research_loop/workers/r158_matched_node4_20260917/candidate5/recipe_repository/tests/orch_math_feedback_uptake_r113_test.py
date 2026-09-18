import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r110_claude_broker as broker
from organism_v6 import orch_math_feedback_uptake_r113 as policy


class R113Tests(unittest.TestCase):
    def event(self, actor='child', text='actual child text', visibility='CHILD_VISIBLE', split='TRAIN'):
        return dict(actor=actor, text=text, visibility=visibility, split=split,
            source_sha256='a' * 64, exposure_sha256='b' * 64)

    def test_child_visible_failed_feedback_kept_exactly(self):
        feedback = '{"correct": false, "score": 0, "message": "checker rejected this attempt"}'
        public = policy.visible_events([self.event(), self.event('environment', feedback)])
        self.assertEqual(public[1]['text'], feedback)

    def test_child_visible_oracle_actor_normalized_not_dropped(self):
        public = policy.visible_events([self.event(), self.event('oracle', 'shown to child: failed')])
        self.assertEqual(public[1]['actor'], 'environment')
        self.assertEqual(public[1]['text'], 'shown to child: failed')

    def test_only_hidden_evaluator_and_held_feedback_removed(self):
        events = [self.event(), self.event('oracle', 'SECRET_GOLD', 'HIDDEN_EVALUATOR'),
            self.event('environment', 'SECRET_FINAL', 'FINAL_READOUT', 'FINAL'),
            self.event('environment', 'DEV_SCORE', 'DEV_READOUT', 'DEV'),
            self.event('environment', 'child saw discrepancy')]
        public = policy.visible_events(events)
        self.assertEqual([event['sequence'] for event in public], [0, 1])
        self.assertEqual(public[1]['text'], 'child saw discrepancy')
        self.assertNotIn('SECRET', json.dumps(public))
        self.assertNotIn('DEV_SCORE', json.dumps(public))

    def test_unknown_visibility_fails_closed(self):
        with self.assertRaises(ValueError):
            policy.visible_events([self.event(visibility='MAYBE_PUBLIC')])

    def test_actual_hubble_wire_keeps_visible_feedback(self):
        task = policy.previous.source.make_task('R113_TRAIN', 1, 0)
        task['split'] = 'TRAIN'
        request = policy.request('C1_T1', 'F2', 1, 0, 'experience', task, 'c' * 64,
            [self.event(), self.event('environment', 'wrong, as the child was told')], 1000, 5000)
        config = dict(life_id='F2', family='math', train_tasks={task['id']:task['question_sha256']},
            excluded_task_ids=[], cohort_sha256='c' * 64)
        visible = broker.validate_request(request, config)
        self.assertEqual(visible['events'][1]['text'], 'wrong, as the child was told')

    def test_final_never_parent_head_exchange_any_phase(self):
        for surface in ('PARENT', 'HEAD', 'EXCHANGE'):
            for phase in ('sleep0', 'cycle', 'morning'):
                self.assertFalse(policy.readout_access('FINAL', surface, phase))

    def test_dev_only_head_exchange_not_parent(self):
        self.assertFalse(policy.readout_access('DEV', 'PARENT', 'cycle'))
        self.assertTrue(policy.readout_access('DEV', 'HEAD', 'cycle'))
        self.assertTrue(policy.readout_access('DEV', 'EXCHANGE', 'cycle'))

    def test_export_does_not_accept_final_or_extra_fields(self):
        good = dict(split='DEV', phase='cycle', cycle=1, taskset_sha256='devhash', metrics={})
        self.assertEqual(policy.export_dev(good, 'HEAD', 'devhash'), good)
        for bad in (dict(good, split='FINAL'), dict(good, final_results=[]), dict(good, taskset_sha256='finalhash')):
            with self.assertRaises(ValueError):
                policy.export_dev(bad, 'HEAD', 'devhash')

    def test_final_fresh_and_disjoint_without_outcome_queries(self):
        with patch.object(policy.previous.source, 'judge', side_effect=AssertionError):
            tasks = policy.final_cohort({'PRIOR'}, {'a' * 64})
        self.assertEqual(len(tasks), 8)
        self.assertEqual(len({task['id'] for task in tasks}), 8)
        self.assertTrue(all(task['split'] == 'FINAL' for task in tasks))

    def test_final_sleep0_once_before_experience(self):
        with tempfile.TemporaryDirectory() as temporary:
            policy.reserve_final(temporary, 'sleep0', 1000, 5000, 'a' * 64)
            with self.assertRaises(FileExistsError):
                policy.reserve_final(temporary, 'sleep0', 1001, 5000, 'a' * 64)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                policy.reserve_final(temporary, 'sleep0', 1000, 5000, 'a' * 64, episodes_started=1)

    def test_final_morning_not_early_or_outside_budget(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                policy.reserve_final(temporary, 'morning', policy.MORNING - 1, policy.MORNING + 60, 'a' * 64)
            with self.assertRaises(ValueError):
                policy.reserve_final(temporary, 'morning', policy.MORNING, policy.previous.NATIVE_END, 'a' * 64)
            policy.reserve_final(temporary, 'morning', policy.MORNING, policy.MORNING + 60, 'a' * 64)
            with self.assertRaises(FileExistsError):
                policy.reserve_final(temporary, 'morning', policy.MORNING, policy.MORNING + 60, 'a' * 64)

    def test_no_cycle_final_reservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                policy.reserve_final(temporary, 'cycle', 1000, 5000, 'a' * 64)

    def test_anchor_plan_inactive_and_exposures_explicit(self):
        contract = policy.contract(Path(__file__).resolve().parents[1])
        sleep = contract['future_sleep']
        self.assertFalse(sleep['active'])
        self.assertEqual(sleep['anchor_manifest_sha256'], policy.ANCHOR_SHA)
        self.assertEqual(sleep['anchor_rows'], 42)
        self.assertEqual(sleep['anchor_lambda'], 0.25)
        self.assertEqual([policy.expected_presentations(1, count) for count in (1, 2, 10)], [16, 17, 25])
        self.assertEqual(contract['weight_updates'], 0)

    def test_systems_elicitation_and_morning_bound_disclosed(self):
        contract = policy.contract(Path(__file__).resolve().parents[1])
        self.assertIn('SYSTEMS', contract['label'])
        self.assertIn('ELICITATION_ONLY', contract['label'])
        self.assertTrue(contract['morning_exceeds_existing_native_wall'])
        self.assertFalse(contract['morning_dispatch_authorized'])

    def test_r112_done_not_review_grace_or_silence(self):
        release = dict(released=True, uuid=policy.previous.MEMBERS['FABLE']['uuid'])
        relay = dict(approved_by='Rohin', relayed_by='Fable', decision='DONE',
            common_contract_sha256='hash', source_reference='verbatim relay')
        policy.require_done('FABLE', release, relay, 'hash')
        policy.require_done('FABLE', release, dict(relay, decision='GO'), 'hash')
        for bad in ({}, dict(relay, decision='GRACE_EXPIRED'), dict(relay, approved_by='Fable')):
            with self.assertRaises(ValueError):
                policy.require_done('FABLE', release, bad, 'hash')


if __name__ == '__main__':
    unittest.main()
