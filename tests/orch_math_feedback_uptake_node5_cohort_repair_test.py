import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_node5_cohort_repair as repair


class CohortRepairTests(unittest.TestCase):
    def test_no_collisions_preserves_original_selection(self):
        with patch.object(repair.policy, 'CYCLES', 1):
            actual, changes = repair.select({'PRIOR'}, {'a' * 64})
            expected = repair.policy.make_cohort(3, {'PRIOR'}, {'a' * 64})
        self.assertEqual(actual, expected)
        self.assertEqual(changes, [])

    def test_exhausted_family_falls_back_without_removing_exclusions(self):
        original = repair.policy.base.history.source.make_task
        def source(split, cycle, position):
            task = original(split, cycle, position)
            if position % 4 == 2:
                task['question_sha256'] = 'blocked'
            return task
        with patch.object(repair.policy, 'CYCLES', 1), patch.object(
                repair.policy.base.history.source, 'make_task', source):
            cohort, changes = repair.select({'PRIOR'}, {'blocked'}, attempts=4)
        self.assertTrue(changes)
        self.assertIn('blocked', cohort['excluded_question_sha256'])
        tasks = [task for group in cohort['train'] + cohort['held'] for task in group]
        self.assertTrue(all(task['question_sha256'] != 'blocked' for task in tasks))
        self.assertEqual(len({task['id'] for task in tasks}), 10)
        self.assertEqual(len({task['question_sha256'] for task in tasks}), 10)

    def test_all_candidates_blocked_fails_closed(self):
        def source(split, cycle, position):
            return dict(id='blocked', question_sha256='blocked', family='blocked')
        with patch.object(repair.policy, 'CYCLES', 1), patch.object(
                repair.policy.base.history.source, 'make_task', source):
            with self.assertRaises(ValueError):
                repair.select({'blocked'}, {'blocked'}, attempts=1)

    def test_not_an_outcome_driven_sampler(self):
        with patch.object(repair.policy, 'CYCLES', 1), patch.object(
                repair.policy.base.history.source, 'judge', side_effect=AssertionError('outcomes forbidden')):
            cohort, _ = repair.select({'PRIOR'}, {'a' * 64})
        self.assertEqual(len(cohort['train'][0]), 2)
        self.assertEqual(len(cohort['held'][0]), 8)


if __name__ == '__main__':
    unittest.main()
