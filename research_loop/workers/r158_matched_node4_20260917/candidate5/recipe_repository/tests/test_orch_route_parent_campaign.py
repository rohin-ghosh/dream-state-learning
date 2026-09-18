import copy
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import time

from organism_v6 import orch_route_parent_campaign as policy
from gpu import orch_route_parent_campaign_run as run
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


class RouteParentCampaignTests(unittest.TestCase):
    def test_cohort_disjoint_and_matched(self):
        cohort = policy.cohort(set())
        self.assertEqual([len(group) for group in cohort['train']], [4, 4])
        self.assertEqual([len(group) for group in cohort['held']], [4, 4, 4])
        masters = [world['master'] for group in cohort['train'] + cohort['held'] for world in group]
        self.assertEqual(len(set(masters)), 20)
        self.assertEqual(cohort['initial_state'], policy.INITIAL_STATE)
        self.assertEqual(cohort, policy.cohort(set()))

    def test_failures_are_input_not_gold(self):
        record = dict(correct=False, captures=[dict(response={'raw': 'ROUTE wrong'}, error=None)],
                      task={}, messages=[dict(role='assistant', content='ROUTE wrong')],
                      reads=[], routes=[], terminal_reason='dead_end')
        prefix = policy.reflection_prefix(record)
        self.assertIn('FAILURE_NOT_CORRECT_ANSWER', prefix[-1]['content'])
        self.assertIn('ROUTE wrong', prefix[-1]['content'])
        self.assertEqual([item['role'] for item in prefix], ['system', 'user'])
        with self.assertRaisesRegex(ValueError, 'answer_action'):
            policy.target_gate('ROUTE wrong', [])

    def test_all_attempts_preserved(self):
        record = dict(correct=True, captures=[dict(response=None, error={'message': 'failed'})],
                      task={}, messages=[], reads=[], routes=[], terminal_reason='reached_goal')
        prefix = policy.reflection_prefix(record)
        self.assertIn('failed', prefix[-1]['content'])
        self.assertIn('SUCCESS', prefix[-1]['content'])

    def test_teacher_copy_fails_without_scrubbing(self):
        lesson = 'one two three four five six seven eight nine ten'
        for target in (lesson, 'one two three four five six seven eight and my idea'):
            with self.assertRaises(ValueError):
                policy.target_gate(target, [lesson])
        self.assertTrue(policy.target_gate('I observed a dead end and should check evidence.', [lesson]))

    def test_parent_held_paths_extra_keys_denied(self):
        payload = dict(kind='coach', turn=0, task={}, public_messages=[], prior_parent_messages=[], learner={})
        self.assertEqual(policy.parent_payload(payload)['cell'], policy.CELL)
        for field in ('sealed_score', 'HELD', '/tmp/private'):
            forged = copy.deepcopy(payload)
            forged['learner']['data'] = field
            with self.assertRaises(ValueError):
                policy.parent_payload(forged)
        with self.assertRaises(ValueError):
            policy.parent_payload(dict(payload, readout={}))

    def test_only_verified_provider_matrix(self):
        with self.assertRaises(ValueError):
            policy.schedule([dict(verified=False, model='invented')])
        self.assertEqual(len(policy.schedule([dict(verified=True, model='observed')])), 12)

    def test_next_cycle_uses_previous_sleep(self):
        initial = dict(state_sha256='initial', base_sha256='base')
        next_child = dict(state_sha256='next', base_sha256='base')
        prior = dict(status='COMPLETE', arm='GUIDED', cycle=1, phase='sleep', output_adapter=next_child)
        self.assertEqual(policy.next_identity(initial, 'GUIDED', 1), initial)
        self.assertEqual(policy.next_identity(initial, 'GUIDED', 2, prior), next_child)
        for patch in (dict(arm='UNPARENTED'), dict(cycle=0), dict(status='FAILED'), dict(phase='readout')):
            with self.assertRaises(ValueError):
                policy.next_identity(initial, 'GUIDED', 2, dict(prior, **patch))

    def test_frozen_cannot_change(self):
        initial = dict(state_sha256='initial', base_sha256='base')
        prior = dict(status='COMPLETE', arm='FROZEN', cycle=1, phase='sleep', output_adapter=initial, updates=0)
        self.assertEqual(policy.next_identity(initial, 'FROZEN', 2, prior), initial)
        with self.assertRaises(ValueError):
            policy.next_identity(initial, 'FROZEN', 2, dict(prior, updates=1))

    def test_budget_and_allocation(self):
        self.assertEqual([entry[0] for entry in run.DEVICES.values()], [0, 1, 2])
        self.assertEqual(GoalReplayLayout(8, 4).updates, 40)
        self.assertLessEqual(GoalReplayLayout(8, 4).updates, policy.CAPS['updates_per_sleep'])
        self.assertEqual(256 + 3 * policy.CAPS['child_calls_per_lane'], 2656)
        self.assertEqual(run.Engine.generate.__globals__['MAX_CONTEXT'], 8192)
        self.assertEqual(run.native.source.Engine.generate.__globals__['MAX_CONTEXT'], 2048)

    def test_partial_train_source_fails_closed(self):
        cohort = policy.cohort(set())
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                run.training_store(Path(directory), cohort['train'][0])

    def test_private_nested_metadata_excluded_from_neutral_prefix(self):
        record = dict(correct=False, captures=[dict(response=dict(raw='my attempted action',
                      terminal=True, messages=[dict(content='PRIVATE_TEACHER_LESSON')]), error=None)],
                      task={}, messages=[], reads=[], routes=[], terminal_reason='dead_end')
        prefix = policy.reflection_prefix(record)
        self.assertNotIn('PRIVATE_TEACHER_LESSON', str(prefix))
        self.assertIn('my attempted action', str(prefix))

    def test_admission_rechecks_but_never_waives(self):
        observations = iter([dict(clear=False, scanner_euid=0), dict(clear=True, scanner_euid=0)])
        with tempfile.TemporaryDirectory() as directory, patch.object(run.time, 'sleep'):
            root = Path(directory)
            result = run.admit(root, 0, root / 'SCAN.json', time.time() + 1000,
                               scanner=lambda *args: next(observations))
            self.assertTrue(result['clear'])
            self.assertFalse(run.read(root / 'SCAN_ATTEMPT0.json')['clear'])
            with self.assertRaisesRegex(ValueError, 'no_waiver'):
                run.admit(root, 0, root / 'BAD.json', time.time() + 1000,
                          scanner=lambda *args: dict(clear=True, scanner_euid=1000))


if __name__ == '__main__':
    unittest.main()
