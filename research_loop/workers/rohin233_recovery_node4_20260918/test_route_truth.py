import json
from pathlib import Path
import unittest

from route_truth import overlay, KEY


class RouteTruthTests(unittest.TestCase):
    def setUp(self):
        self.proof = json.loads(Path(__file__).with_name('RENEWED_RETURN_1748.json').read_bytes())
        self.observation = dict(actual_birth_and_route=dict(standing_overseer_curriculum={KEY:
            dict(current_route_status='EXPIRED', guidance=['Earlier statement'], next_turn_requested_text='unchanged')}))

    def test_observation_only_old_brief_and_instruction_preserved(self):
        result = overlay(self.observation, self.proof)
        self.assertEqual(self.observation['actual_birth_and_route']['standing_overseer_curriculum'][KEY]['current_route_status'], 'EXPIRED')
        route = result['actual_birth_and_route']
        self.assertEqual(route['prior_expired_route_brief_preserved']['current_route_status'], 'EXPIRED')
        self.assertEqual(route['standing_overseer_curriculum'][KEY]['next_turn_requested_text'], 'unchanged')
        self.assertIsNone(route['R233_receiver_recovery']['returned_outputs'][0]['P7_request_render'])

    def test_wrong_current_request_rejected(self):
        self.proof['records'][0]['sha256'] = 'wrong'
        with self.assertRaises(ValueError):
            overlay(self.observation, self.proof)


if __name__ == '__main__':
    unittest.main()
