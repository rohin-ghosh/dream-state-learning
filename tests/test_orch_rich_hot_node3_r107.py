import unittest
from pathlib import Path
from unittest.mock import patch

from organism_v6 import orch_rich_hot_node3_r107 as policy


class R107RefillTests(unittest.TestCase):
    def test_main_and_foreign_slots_rejected(self):
        for index in (0, 1, 2, 3, 6, 7, True):
            with self.assertRaises(ValueError):
                policy.arm(index)

    def test_driver_rejects_main_slot_before_any_scan(self):
        from gpu import orch_rich_hot_node3_r107_run as runner
        with patch.object(runner, 'bind_host') as bind, patch.object(runner.ownership, 'scan') as scan:
            with self.assertRaises(ValueError):
                runner.watch(Path('/unused'), 3)
        bind.assert_not_called()
        scan.assert_not_called()

    def test_unhinted_persistence_and_labelled_meta(self):
        self.assertEqual(policy.guidance(4), policy.PERSISTENCE)
        self.assertNotIn('check heading', policy.guidance(4))
        self.assertIn('change what you do next', policy.guidance(5))
        self.assertIn('first adequate answer', policy.guidance(4))

    def test_no_forced_branch_or_check_counts(self):
        self.assertIn('no required number', policy.META)
        self.assertNotIn('WORKED_METHOD_COUNT:', policy.guidance(5))
        self.assertNotIn('at least two', policy.guidance(5))
        self.assertIn('stop when further work would only repeat', policy.guidance(4))

    def test_functional_diagnostic_not_self_report(self):
        result = policy.assess(dict(raw='WORKED_APPROACH_COUNT: 2\nI realized something.'))
        self.assertIsNone(result['functional_metarealisation_to_changed_continuation'])
        self.assertIsNone(result['semantic_persistence_beyond_first_adequate'])
        self.assertFalse(result['admission'])

    def test_original_system_scorer_and_r106_bytes_reused_not_mutated(self):
        before = policy.previous.guidance(3)
        self.assertIs(policy.display, policy.previous.display)
        self.assertIs(policy.original.readout.score, policy.previous.original.readout.score)
        self.assertEqual(policy.previous.guidance(3), before)

    def test_only_two_shards_and_explicit_cap(self):
        templates = [dict(kind=kind, node='fixture', goal='goal', events=['a', 'b', 'c', 'd'], ports=['x', 'y'])
                     for kind in ('first', 'middle', 'last')]
        with patch.object(policy.previous.previous.previous.previous, 'tasks', return_value=templates):
            first = policy.tasks({}, 4)
            second = policy.tasks({}, 5)
        self.assertEqual(len(first), 16)
        self.assertEqual(len(second), 16)
        self.assertFalse({policy.original.digest(task) for task in first}.intersection(
            policy.original.digest(task) for task in second))
        self.assertEqual(policy.MAX_CALLS, 2 * policy.MAX_SLOT_CALLS)
        self.assertEqual(5584 + policy.MAX_CALLS, 7120)


if __name__ == '__main__':
    unittest.main()
