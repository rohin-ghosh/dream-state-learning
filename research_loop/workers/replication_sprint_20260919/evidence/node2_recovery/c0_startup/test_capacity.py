import unittest

from prepare_receiving import space_budget


class CapacityTests(unittest.TestCase):
    def test_owner_available_bytes_do_not_fit_the_observed_conservative_budget(self):
        budget = space_budget(source_bytes=30051006, checkpoint_bytes=242659584,
            complete_bytes=21453804, pending_bytes=21625820, addition_bytes=52946)
        self.assertEqual(budget['required_bytes'], 2981136864)
        self.assertGreater(budget['required_bytes'], 947650560)
        self.assertEqual(budget['required_bytes'] - 947650560, 2033486304)

    def test_includes_new_checkpoint_temp_and_first_ACT_without_deleting_failed_artifacts(self):
        budget = space_budget(source_bytes=30, checkpoint_bytes=200,
            complete_bytes=100, pending_bytes=120, addition_bytes=10)
        self.assertEqual(budget['components']['new_checkpoint_and_temporary_payloads'], 400)
        self.assertEqual(budget['components']['first_THINK_ACT_atomic_record_headroom'], 8 * (120 + 4 * 1024**2))
        self.assertEqual(budget['components']['shared_filesystem_unallocated_safety_reserve'], 2 * 1024**3)


if __name__ == '__main__':
    unittest.main()
