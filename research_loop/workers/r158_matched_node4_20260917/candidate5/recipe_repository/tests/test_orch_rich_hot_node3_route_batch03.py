import json
from pathlib import Path
import unittest

from organism_v6 import orch_rich_hot_node3_route_batch03 as route
from organism_v6 import orch_rich_hot_node3_route_next as previous


class RouteBatch03Tests(unittest.TestCase):
    def setUp(self):
        root = Path('research_notes/analysis/orch_full_rich_20260914_attempt1/native')
        self.cohort = json.loads((root / 'prepare/COHORT.json').read_text())
        self.source = json.loads((root / 'collection/SOURCE.json').read_text())

    def test_new_displays_exclude_both_prior_batches(self):
        roster = route.roster(self.cohort)
        old_ids = {row['task_id'] for row in previous.roster(self.cohort)['tasks']}
        self.assertEqual(len(roster['tasks']), 48)
        self.assertEqual(roster['maximum_calls'], 288)
        self.assertFalse(old_ids.intersection(row['task_id'] for row in roster['tasks']))
        for row in roster['tasks']:
            self.assertNotIn(row['task'], route.previous.tasks(self.cohort['worlds'][row['world_index']]))

    def test_unchanged_train_sources_and_prompt(self):
        self.assertEqual(len(route.validate(self.cohort, self.source)), 32)
        self.assertEqual(route.GUIDANCE, previous.GUIDANCE)
