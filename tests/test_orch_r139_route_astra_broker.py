from copy import deepcopy
import unittest

from gpu import orch_r139_route_astra_broker as broker


class ConsumerTests(unittest.TestCase):
    def setUp(self):
        self.report = dict(provider=broker.prior.astra.MODEL, substitution=None,
            mode='R139_SAME_LOGICAL_LIFE_ASTRA_SEGMENT', actual_checkpoint={'sha': 'a'},
            expected_checkpoint={'sha': 'a'}, next_cycle=55, expected_cycle=55,
            source_verified=True, actor_command_verified=True, logical_life_reset=False)

    def test_exact_live_consumer(self):
        broker.validate_consumer(self.report)

    def test_wrong_identity_or_state_rejected(self):
        changes = [('provider', 'claude-fable-5-1'), ('substitution', {}),
            ('mode', 'old'), ('actual_checkpoint', {'sha': 'b'}), ('next_cycle', 54),
            ('source_verified', False), ('actor_command_verified', False), ('logical_life_reset', True)]
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(ValueError):
                changed = deepcopy(self.report)
                changed[key] = value
                broker.validate_consumer(changed)

    def test_subsecond_post_boundary_request_eligible(self):
        boundary = dict(highest_request=117, highest_cycle=54, observed_unix=100.25)
        self.assertTrue(broker.prior.eligible('000118_F1_C0055.request.json', boundary, 100.75))
        self.assertFalse(broker.prior.eligible('000117_F1_C0054.request.json', boundary, 100.75))
        self.assertFalse(broker.prior.eligible('000118_F1_C0055.request.json', boundary, 100.1))


if __name__ == '__main__':
    unittest.main()
