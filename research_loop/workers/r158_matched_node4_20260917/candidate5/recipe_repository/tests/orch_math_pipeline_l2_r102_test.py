import copy
import unittest

from gpu import orch_math_pipeline_l2_r102_broker as broker
from gpu import orch_math_pipeline_l2_r102_native as native
from gpu import orch_math_pipeline_l2_r102_policy as policy
from gpu import orch_math_pipeline_l2_r102_run as runner


class R102Test(unittest.TestCase):
    def episodes(self):
        return [dict(task=task, trace='A recorded unsuccessful attempt. FINAL: -999',
            outcome=dict(status='INCORRECT', correct=False)) for task in policy.original.cohort()['train'][0][:2]]

    def test_eight_sequential_two_episode_cycles_exact_budget(self):
        self.assertEqual(len(runner.sequence()), 16)
        self.assertEqual(runner.sequence()[0], (1, 'experience'))
        self.assertEqual(runner.sequence()[-1], (8, 'readout'))
        self.assertEqual(sum(2 + 2 + 8 + (48 if native.retention_due(cycle) else 0) for cycle in range(1, 9)), 144)

    def test_fresh_roster_excludes_entire_old_pool(self):
        prior = policy.original.cohort(excluded_ids=['SOURCE_TRAIN'], excluded_questions=['source_hash'])
        seed = policy.original.SEED
        cohort = policy.make_cohort(prior)
        self.assertEqual(policy.original.SEED, seed)
        self.assertEqual(cohort, policy.make_cohort(prior))
        self.assertEqual(cohort['held'][0], [])
        tasks = [task for group in cohort['train'] + cohort['held'] for task in group]
        self.assertEqual(len(tasks), 80)
        self.assertEqual(len({task['question_sha256'] for task in tasks}), 80)
        self.assertFalse(set(cohort['excluded_question_hashes']) & {task['question_sha256'] for task in tasks})
        self.assertTrue(all(len(group) == 2 for group in cohort['train']))
        self.assertTrue(all(len(group) == 8 for group in cohort['held'][1:]))

    def test_strong_two_episode_parent_context_not_held(self):
        for variant in policy.VARIANTS:
            policy.configure(variant)
            payload = policy.parent_payload(self.episodes(), 8)
            with broker.parent_context(variant):
                broker.transport.parent.policy.validate_parent_payload(payload)
                bad = copy.deepcopy(payload)
                bad['episodes'][0]['task_id'] = 'LEAK_HELD_TASK'
                with self.assertRaises(AssertionError):
                    broker.transport.parent.policy.validate_parent_payload(bad)
                with self.assertRaises(AssertionError):
                    broker.transport.parent.policy.validate_parent_payload(dict(payload, episodes=payload['episodes'] * 4))

    def test_parent_context_restored_after_failure(self):
        old = broker.transport.parent.policy.validate_parent_payload
        instructions = broker.transport.parent.INSTRUCTIONS
        with self.assertRaises(RuntimeError):
            with broker.parent_context('creative7'):
                raise RuntimeError('fixture')
        self.assertIs(broker.transport.parent.policy.validate_parent_payload, old)
        self.assertEqual(broker.transport.parent.INSTRUCTIONS, instructions)

    def test_failure_coverage_requires_both_actual_reflections(self):
        episodes = self.episodes()
        rows = [dict(episode_id=episode['task']['id'], kind=kind)
            for episode in episodes for kind in ('past_attempt', 'past_reflection')]
        result = policy.validate_coverage(episodes, rows)
        self.assertEqual((result['episodes'], result['failures']), (2, 2))
        with self.assertRaises(AssertionError):
            policy.validate_coverage(episodes, rows[:-1])

    def test_distinct_physical_bindings_no_control_arm(self):
        policy.configure('micro5')
        self.assertEqual(policy.DEVICES['GUIDED_SLEEP'][0], 5)
        policy.configure('creative7')
        self.assertEqual(policy.DEVICES['GUIDED_SLEEP'][0], 7)
        self.assertEqual(set(policy.DEVICES), {'GUIDED_SLEEP'})


if __name__ == '__main__':
    unittest.main()
