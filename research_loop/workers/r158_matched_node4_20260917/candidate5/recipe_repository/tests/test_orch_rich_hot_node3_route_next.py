import json
from pathlib import Path
import unittest

from organism_v6 import orch_rich_hot_node3_route_next as route


class RouteNextTests(unittest.TestCase):
    def setUp(self):
        root = Path('research_notes/analysis/orch_full_rich_20260914_attempt1/native')
        self.cohort = json.loads((root / 'prepare/COHORT.json').read_text())
        self.source = json.loads((root / 'collection/SOURCE.json').read_text())

    def test_distinct_unseen_displays_and_unchanged_sources(self):
        self.assertEqual(len(route.validate(self.cohort, self.source)), 32)
        roster = route.roster(self.cohort)
        self.assertEqual(len(roster['tasks']), 120)
        for row in roster['tasks']:
            world = self.cohort['worlds'][row['world_index']]
            self.assertNotIn(row['task'], route.previous.tasks(world))
            self.assertEqual(set(row['task']['events']), set(route.previous.tasks(world)[0]['events']))
        self.assertEqual(roster['maximum_calls'], 720)

    def test_ownership_is_only_three_four_five(self):
        for index in (0, 1, 2, 6, 7):
            with self.assertRaises(ValueError):
                route.tasks(self.cohort['worlds'][0], index)

    def test_unchanged_verifier_accepts_actual_route(self):
        world = self.cohort['worlds'][0]
        task = route.tasks(world, 3)[0]
        final = next(edge for edge in world['edges'] if edge['outcome'] == task['goal'])
        first = next(edge for edge in world['edges'] if edge['outcome'] == final['node'])
        actions = iter([first['port'], final['port']])
        record = route.episode(world, task, lambda messages: dict(
            raw='ROUTE ' + next(actions), terminal=True, truncated=False), self.source['store'])
        self.assertTrue(record['correct'])

    def test_prompt_still_version_two_no_length_floor(self):
        self.assertEqual(route.GUIDANCE, route.previous.GUIDANCE)
        self.assertNotIn('150', route.GUIDANCE)
        self.assertIn('Do not fabricate alternatives', route.GUIDANCE)
