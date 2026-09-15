from copy import deepcopy
import json
from pathlib import Path
import unittest

from organism_v6 import orch_rich_hot_node3_route as route


class RouteContinuationTests(unittest.TestCase):
    def setUp(self):
        root = Path('research_notes/analysis/orch_full_rich_20260914_attempt1/native')
        self.cohort = json.loads((root / 'prepare/COHORT.json').read_text())
        self.source = json.loads((root / 'collection/SOURCE.json').read_text())

    def test_original_child_sources_replay_and_train_only(self):
        self.assertEqual(len(route.validate(self.cohort, self.source)), 32)
        self.assertEqual(sum(len(route.tasks(world)) for world in self.cohort['worlds']), 32)
        changed = deepcopy(self.cohort)
        changed['split'] = 'HELD'
        with self.assertRaises(ValueError):
            route.validate(changed, self.source)

    def test_source_tampering_rejected(self):
        changed = deepcopy(self.source)
        changed['store'][next(iter(changed['store']))] += ' invented'
        with self.assertRaises(ValueError):
            route.validate(self.cohort, changed)

    def test_no_voice_length_or_fabricated_branch_requirement(self):
        self.assertNotIn('first-person', route.GUIDANCE)
        self.assertNotIn('150', route.GUIDANCE)
        self.assertNotIn('400', route.GUIDANCE)
        self.assertIn('genuinely relevant', route.GUIDANCE)
        self.assertIn('Do not fabricate alternatives', route.GUIDANCE)

    def test_cloned_episode_keeps_unchanged_transition_verifier(self):
        world = self.cohort['worlds'][0]
        task = route.tasks(world)[0]
        old_guidance = route.original.GUIDANCE
        record = route.episode(world, task,
            lambda messages: dict(raw='NOT AN ACTION', terminal=True, truncated=False), self.source['store'])
        self.assertEqual(record['terminal_reason'], 'invalid_final_action')
        self.assertFalse(record['correct'])
        self.assertEqual(route.original.GUIDANCE, old_guidance)


if __name__ == '__main__':
    unittest.main()
