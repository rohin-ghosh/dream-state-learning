from copy import deepcopy
from pathlib import Path
import unittest
from gpu import orch_r123_base_code_refill as refill


def seed():
    return dict(wrapper='a40r', physical=6, adapter=None, gpu_uuid='GPU-seed',
        ancestry=dict(first_cycle=27, native_used=383, parent_used=128),
        lease_end_unix=100000, hard_end_unix=78400, train_end_unix=78280,
        first_cycle=27, cycle_limit=100, parent_ttl_seconds=600, parent_wait_seconds=0,
        parent_effort='low', parent_cadence='EPISODE', optimizer_updates=0)


class RefillTests(unittest.TestCase):
    def test_narrow_allocation_preserves_seed_and_counters(self):
        previous = refill.fork.ALLOCATIONS
        self.addCleanup(setattr, refill.fork, 'ALLOCATIONS', previous)
        refill.fork.ALLOCATIONS = {'a40r': (4, 5)}
        for physical in (4, 5):
            with self.subTest(physical=physical):
                original = seed()
                before = deepcopy(original)
                result = refill.derive(original, Path('/new'), physical, f'GPU-{physical}', Path('/source'))
                self.assertIs(refill.fork.validate_plan(result, now=1), result)
                self.assertEqual(original, before)
                self.assertEqual(result['ancestry'], original['ancestry'])
                self.assertEqual(result['hard_end_unix'], original['hard_end_unix'])
                self.assertIsNone(result['adapter'])
                self.assertEqual(result['optimizer_updates'], 0)

    def test_rejects_peer_slots(self):
        for physical in (0, 3, 6, 7):
            with self.subTest(physical=physical), self.assertRaisesRegex(ValueError, 'new_owned_physical'):
                refill.derive(seed(), Path('/new'), physical, 'GPU-other', Path('/source'))

    def test_rejects_weight_or_same_device_substitution(self):
        with self.assertRaisesRegex(ValueError, 'existing_BASE'):
            refill.derive(dict(seed(), adapter={'path': '/adapter'}), Path('/new'), 4, 'GPU-4', Path('/source'))
        with self.assertRaisesRegex(ValueError, 'new_owned_physical'):
            refill.derive(seed(), Path('/new'), 4, 'GPU-seed', Path('/source'))


if __name__ == '__main__':
    unittest.main()
