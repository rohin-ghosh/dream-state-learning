import unittest

from gpu import orch_math_pipeline_l2_replicate as replicate


class ReplicateTest(unittest.TestCase):
    def test_new_life_has_baseline_and_each_cycle_test(self):
        self.assertEqual(replicate.sequence(), [(0, 'readout'), (1, 'experience'), (1, 'readout'),
            (2, 'experience'), (2, 'readout'), (3, 'experience'), (3, 'readout')])

    def test_no_acceptance_of_approximate_recovery(self):
        valid = dict(no_state_accepted=True, native_generation_calls=0,
            message='reconstruction_loss_mismatch_no_tolerance_waiver:actual:expected')
        replicate.require_failed_recovery(valid)
        for changed in [dict(no_state_accepted=False), dict(native_generation_calls=1), dict(message='quality_low')]:
            with self.assertRaises(AssertionError):
                replicate.require_failed_recovery(dict(valid, **changed))

    def test_distinct_campaign_and_learning_only_lanes(self):
        self.assertEqual(replicate.NAME, 'campaign_02_recovery_paired')
        self.assertEqual(replicate.ARMS, ('GUIDED_SLEEP', 'UNPARENTED_SLEEP'))
        self.assertTrue(callable(replicate.lane_module().admit))


if __name__ == '__main__':
    unittest.main()
