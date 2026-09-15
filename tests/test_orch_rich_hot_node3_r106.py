import unittest
from unittest.mock import patch

from organism_v6 import orch_rich_hot_node3_r106 as policy
from gpu.orch_rich_hot_node3_exhaustion_boundary import episode_complete


class R106RefillTests(unittest.TestCase):
    def test_only_own_three_slots(self):
        for index in (0, 1, 2, 6, 7, True):
            with self.assertRaises(ValueError):
                policy.arm(index)

    def test_preserved_unhinted_and_labelled_meta(self):
        self.assertEqual(policy.guidance(3), policy.previous.guidance(3))
        self.assertEqual(policy.arm(3), 'EXHAUSTION_ONLY')
        self.assertEqual(policy.arm(4), 'R106_META_DEPARTURE_RETURN')
        self.assertEqual(policy.guidance(4), policy.guidance(5))

    def test_departure_return_not_two_method_requirement(self):
        self.assertIn('then return', policy.META)
        self.assertIn('not a requirement for two methods', policy.META)
        self.assertIn('terminal check is distinct', policy.META)
        self.assertIn('Do not force a departure', policy.META)
        self.assertIn('only after the actual result', policy.META)

    def test_unseen_display_selection(self):
        templates = [dict(kind=kind, node='fixture', events=['a', 'b', 'c', 'd'], ports=['x', 'y'])
                     for kind in ('first', 'middle', 'last')]
        with patch.object(policy.previous.previous.previous, 'tasks', return_value=templates):
            prior = {policy.original.digest(task) for provider in
                     (policy.batch02, policy.batch03, policy.previous.previous, policy.previous)
                     for index in (3, 4, 5) for task in provider.tasks({}, index)}
            selected = [policy.original.digest(task) for index in (3, 4, 5)
                        for task in policy.tasks({}, index)]
        self.assertEqual(len(selected), 48)
        self.assertEqual(len(set(selected)), 48)
        self.assertFalse(prior.intersection(selected))

    def test_separate_unverified_measurements(self):
        result = policy.assess(dict(raw='WORKED_APPROACH_COUNT: 2'))
        self.assertEqual(result['self_reported_worked_approach_count'], 2)
        for key in ('semantic_departure_return_count', 'semantic_mid_solution_excursion_count',
                    'semantic_terminal_check_count', 'semantic_method_count'):
            self.assertIsNone(result[key])
        self.assertFalse(result['admission'])

    def test_layout_has_exact_same_public_facts_no_padding(self):
        task = dict(node='start', goal='goal', ports=['one', 'two'], events=['event'],
                    display_variant='GOAL_FIRST_PUBLIC_FIELDS_V1')
        old = policy.original.readout.display(task['node'], task, task['ports'])
        new = policy.display(task['node'], task, task['ports'])
        self.assertEqual(sorted(old.splitlines()), sorted(new.splitlines()))
        self.assertNotEqual(old, new)
        self.assertEqual(new.splitlines()[1], 'GOAL goal')

    def test_scorer_is_unchanged(self):
        self.assertIs(policy.original.readout.score, policy.previous.original.readout.score)

    def test_prospective_cap_and_complete_episode(self):
        self.assertEqual(policy.MAX_CALLS, 3 * policy.MAX_SLOT_CALLS)
        self.assertEqual(5584 + policy.MAX_CALLS, 7888)
        self.assertFalse(episode_complete([dict(global_call=1, task_id='fixture')], [],
                                         [dict(global_call=1)]))


if __name__ == '__main__':
    unittest.main()
