import copy
import unittest

from gpu import orch_route_parent_campaign_queue as queue
from organism_v6 import orch_route_parent_campaign as policy
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


class RouteParentContinuationTests(unittest.TestCase):
    def setUp(self):
        self.original = policy.ROOT, policy.PREFIX, policy.PRESENTATIONS, policy.CELL, policy.CAPS

    def tearDown(self):
        policy.ROOT, policy.PREFIX, policy.PRESENTATIONS, policy.CELL, policy.CAPS = self.original

    def test_prospectively_frozen_segment_namespaces(self):
        original = policy.cohort(set())
        original_masters = {world['master'] for group in original['train'] + original['held'] for world in group}
        seen = set(original_masters)
        for config in queue.configurations():
            policy.activate(config)
            cohort = policy.cohort(set())
            masters = {world['master'] for group in cohort['train'] + cohort['held'] for world in group}
            self.assertFalse(seen & masters)
            seen |= masters
            self.assertEqual(cohort['initial_state'], policy.INITIAL_STATE)
            self.assertEqual(policy.PRESENTATIONS, 16)
            self.assertEqual(GoalReplayLayout(8, policy.PRESENTATIONS).updates, 160)
            self.assertLessEqual(160, policy.CAPS['updates_per_sleep'])
        self.assertEqual(len(seen), 80)

    def test_only_bounded_known_configs(self):
        config = queue.configurations()[0]
        for patch in (dict(segment=5), dict(root='/tmp/other'), dict(presentations=100000),
                      dict(initial_state='score_selected'), dict(extra='undeclared')):
            with self.assertRaises(ValueError):
                policy.activate(dict(config, **patch))

    def test_provider_alias_or_axis_cannot_be_invented(self):
        for axis, value in (('provider', 'gpt-alias'), ('style', 'invented'), ('tone', 'violent')):
            config = copy.deepcopy(queue.configurations()[0])
            config['cell'][axis] = value
            with self.assertRaises(ValueError):
                policy.activate(config)

    def test_all_styles_and_horizons_are_queued_without_scores(self):
        configs = queue.configurations()
        self.assertEqual({config['cell']['style'] for config in configs}, {'training-wheels', 'micromanaging', 'creative'})
        self.assertEqual({config['cell']['horizon'] for config in configs}, {'short', 'long'})
        self.assertEqual({config['cell']['tone'] for config in configs}, {'harsh-critical', 'supportive-positive'})
        self.assertTrue(all(config['initial_state'] == policy.INITIAL_STATE for config in configs))

    def test_strengths_require_primary_train_qualification(self):
        names = ('claude-haiku-4-5-20251001', 'openai/openai/gpt-6-astra')
        receipts = {name: dict(verified=True, actual_primary_model=name,
            scope='TRAIN_ONLY_READINESS_NOT_HELD', usage={'tokens': 20}, envelope_sha256='observed') for name in names}
        configs = queue.configurations(receipts)
        self.assertEqual([config['cell']['provider'] for config in configs], ['existing_claude_cli', *names])
        for config in configs:
            policy.activate(config)
            payload = dict(kind='coach', turn=0, task={}, public_messages=[], prior_parent_messages=[], learner={})
            self.assertEqual(policy.parent_payload(payload)['cell'], config['cell'])
        for field, value in (('verified', False), ('actual_primary_model', 'auxiliary'),
                             ('scope', 'HELD'), ('usage', {}), ('envelope_sha256', '')):
            bad = copy.deepcopy(receipts)
            bad[names[0]][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                queue.configurations(bad)


if __name__ == '__main__':
    unittest.main()
