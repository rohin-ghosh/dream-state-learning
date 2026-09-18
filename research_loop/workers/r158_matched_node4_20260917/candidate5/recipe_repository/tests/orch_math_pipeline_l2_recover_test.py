import unittest

from gpu import orch_math_pipeline_l2_recover as recovery


class RecoveryTest(unittest.TestCase):
    def test_recovery_loads_bound_sibling_not_frozen_archive_module(self):
        module = recovery.admission_module()
        self.assertEqual(module.Path(module.__file__), recovery.Path(recovery.__file__).with_name('orch_math_pipeline_l2_lane.py'))
        self.assertTrue(callable(module.admit))

    def test_exact_loss_required_no_quality_or_tolerance_substitute(self):
        recovery.require_identical_loss(0.25, 0.25)
        with self.assertRaises(AssertionError):
            recovery.require_identical_loss(0.25 + 1e-12, 0.25)

    def test_full_contiguous_log_required(self):
        row = dict(update=1, matched_learning_rate=3e-5, supervised_tokens=10, source=dict(kind='past_attempt'))
        recovery.validate_steps([row])
        for records in ([], [dict(row, update=2)], [row, dict(row, update=3)], [dict(row, source=dict(kind='teacher'))]):
            with self.assertRaises(AssertionError):
                recovery.validate_steps(records)


if __name__ == '__main__':
    unittest.main()
