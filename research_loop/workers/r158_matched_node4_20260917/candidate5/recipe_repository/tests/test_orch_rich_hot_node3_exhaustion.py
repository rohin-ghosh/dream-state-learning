import json
from pathlib import Path
import unittest

from gpu.orch_rich_hot_node3_exhaustion_boundary import episode_complete
from organism_v6 import orch_rich_hot_node3_exhaustion as route
from organism_v6 import orch_rich_hot_node3_route_next as batch02
from organism_v6 import orch_rich_hot_node3_route_batch03 as batch03


class RouteExhaustionTests(unittest.TestCase):
    def test_arms_and_no_route_hints_in_only(self):
        self.assertEqual(route.arm(3), 'EXHAUSTION_ONLY')
        self.assertNotIn(route.previous.GUIDANCE, route.guidance(3))
        for index in (4, 5):
            self.assertEqual(route.arm(index), 'EXHAUSTION_PLUS_STEERING')
            self.assertIn(route.previous.GUIDANCE, route.guidance(index))
        with self.assertRaises(ValueError):
            route.arm(6)

    def test_unseen_train_displays_and_sources(self):
        root = Path('research_notes/analysis/orch_full_rich_20260914_attempt1/native')
        cohort = json.loads((root / 'prepare/COHORT.json').read_text())
        source = json.loads((root / 'collection/SOURCE.json').read_text())
        self.assertEqual(len(route.validate(cohort, source)), 32)
        old = {row['task_id'] for policy in (batch02, batch03) for row in policy.roster(cohort)['tasks']}
        rows = route.roster(cohort)['tasks']
        self.assertEqual(len(rows), 120)
        self.assertFalse(old.intersection(row['task_id'] for row in rows))

    def test_waits_for_full_episode_and_pending_calls(self):
        calls = [dict(global_call=1, task_id='task')]
        reservations = [dict(global_call=1)]
        self.assertFalse(episode_complete(calls, [], reservations))
        self.assertTrue(episode_complete(calls, [dict(task_id='task')], reservations))
        self.assertFalse(episode_complete(calls, [dict(task_id='task')], reservations + [dict(global_call=2)]))

    def test_later_route_turn_uses_remaining_context(self):
        self.assertEqual(route.exhaustion.token_budget(556), 16384)
        self.assertEqual(route.exhaustion.token_budget(32000), 768)
        with self.assertRaises(ValueError):
            route.exhaustion.token_budget(32768)
