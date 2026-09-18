from copy import deepcopy
import json
from pathlib import Path
import unittest

from route_truth import continued_receiver, KEY


class ContinuedRouteTests(unittest.TestCase):
    def test_prior_roundtrip_is_not_new_incarnation_proof(self):
        receipt = json.loads(Path(__file__).with_name('CURRENT_ASTRA7_RECEIVER.json').read_bytes())
        original = dict(actual_birth_and_route=dict(R233_receiver_recovery=dict(scope='old'),
            standing_overseer_curriculum={KEY: dict(guidance=[])}))
        before = deepcopy(original)
        result = continued_receiver(original, receipt)
        self.assertEqual(original, before)
        self.assertFalse(result['actual_birth_and_route']['R233_current_receiver']['new_incarnation_roundtrip_claim'])
        self.assertIn('Historical', result['actual_birth_and_route']['R233_receiver_recovery']['scope'])

    def test_stale_native_cannot_be_projected_as_current(self):
        receipt = json.loads(Path(__file__).with_name('CURRENT_ASTRA7_RECEIVER.json').read_bytes())
        receipt['native_pid'] = 762967
        with self.assertRaises(ValueError):
            continued_receiver(dict(actual_birth_and_route={}), receipt)


if __name__ == '__main__':
    unittest.main()
