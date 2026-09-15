import copy
import unittest

from gpu import orch_route_parent_campaign_queue as queue
from organism_v6 import orch_route_parent_campaign as policy
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


class RouteParentDoseTests(unittest.TestCase):
    def setUp(self):
        self.original = policy.ROOT, policy.PREFIX, policy.PRESENTATIONS, policy.CELL, policy.CAPS

    def tearDown(self):
        policy.ROOT, policy.PREFIX, policy.PRESENTATIONS, policy.CELL, policy.CAPS = self.original

    def test_only_next_segment_changes(self):
        before = queue.configurations()
        after = queue.configurations(dose4to16=True)
        self.assertEqual(before[0], after[0])
        self.assertEqual(before[2], after[2])
        self.assertEqual(after[1]['presentations'], [4, 16])
        self.assertEqual(before[1]['cell'], after[1]['cell'])

    def test_fixed_parent_twins_branching_and_no_child_reset(self):
        config = queue.configurations(dose4to16=True)[1]
        policy.activate(config)
        self.assertEqual([policy.presentations_for_cycle(cycle) for cycle in (1, 2)], [4, 16])
        cohort = policy.cohort(set())
        self.assertEqual(cohort['presentations_by_cycle'], [4, 16])
        for group in cohort['train']:
            for world in group:
                for task in policy.shared.tasks(world):
                    self.assertEqual(len(task['ports']), 2)
        initial = dict(state_sha256='initial', base_sha256='base')
        taught = dict(state_sha256='after_four', base_sha256='base')
        for arm in ('GUIDED', 'UNPARENTED'):
            prior = dict(status='COMPLETE', arm=arm, cycle=1, phase='sleep', output_adapter=taught)
            self.assertEqual(policy.next_identity(initial, arm, 2, prior), taught)
        self.assertEqual(GoalReplayLayout(8, policy.presentations_for_cycle(1)).manifest('FULL_TARGET')['new_target_presentations'], 32)
        self.assertEqual(GoalReplayLayout(8, policy.presentations_for_cycle(2)).manifest('FULL_TARGET')['new_target_presentations'], 128)

    def test_unregistered_dose_or_cycle_rejected(self):
        config = queue.configurations(dose4to16=True)[1]
        for dose in ([16, 4], [4, 16, 64], 4, [4, 32]):
            with self.assertRaises(ValueError):
                policy.activate(dict(config, presentations=dose))
        with self.assertRaises(ValueError):
            policy.activate(dict(queue.configurations()[0], presentations=[4, 16]))
        policy.activate(copy.deepcopy(config))
        for cycle in (0, 3, True):
            with self.assertRaises(ValueError):
                policy.presentations_for_cycle(cycle)


if __name__ == '__main__':
    unittest.main()
