"""R108 tables never invent qualification or expand small discovery quotas."""

import unittest

from gpu.orch_r107_route_parent_triples import evidence_table


class TripleTests(unittest.TestCase):
    def test_small_fixed_run_not_fifty_episodes(self):
        result = evidence_table([{}] * 8, 8)
        self.assertFalse(result['sufficient_episode_count'])
        self.assertEqual(result['status'], 'INSUFFICIENT_EPISODES_NO_QUOTA_EXPANSION')
        self.assertIsNone(result['helpful'])
        self.assertIsNone(result['unhelpful'])

    def test_fifty_episodes_still_needs_author_review(self):
        result = evidence_table([{}] * 50, 50)
        self.assertTrue(result['sufficient_episode_count'])
        self.assertEqual(result['status'], 'AWAIT_AUTHOR_REVIEW')
        self.assertIsNone(result['recurring'])
        self.assertFalse(result['automatic_keyword_or_outcome_qualification'])


if __name__ == '__main__':
    unittest.main()
