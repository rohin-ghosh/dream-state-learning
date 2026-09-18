import unittest
from unittest.mock import patch, Mock

from gpu import orch_r109_l1_async as scheduler


class AsyncTests(unittest.TestCase):
    def test_full_exact32_and_held_once_per_condition(self):
        partitions = [scheduler.partition('FULL', index) for index in range(3)]
        self.assertEqual(sorted(position for positions, held in partitions for position in positions), list(range(32)))
        self.assertEqual(sum(held for positions, held in partitions), 1)
        self.assertEqual(partitions[2], ([], True))

    def test_control_identical_coverage(self):
        self.assertEqual(scheduler.partition('CONTROL', 3), (list(range(32)), True))

    def test_no_gpu7_or_cross_arm(self):
        for arm, index in [('FULL', 3), ('FULL', 7), ('CONTROL', 0), ('CONTROL', 7)]:
            with self.assertRaises(ValueError):
                scheduler.partition(arm, index)

    def test_continuation_beyond_old16_without_clock_reset(self):
        self.assertTrue(scheduler.may_start_fit(1789465000, 16))
        self.assertFalse(scheduler.may_start_fit(scheduler.CUTOFF - 600, 16))
        self.assertFalse(scheduler.may_start_fit(1789465000, 512))
        self.assertEqual(scheduler.END, 1789491360)

    def test_full_does_not_wait_for_control_gpu3(self):
        self.assertTrue(scheduler.ready('FULL', [], {3}))
        self.assertFalse(scheduler.ready('FULL', [], {2, 3}))
        self.assertTrue(scheduler.ready('CONTROL', [], {0, 1, 2}))

    def test_live_owned_job_blocks_next_stage(self):
        with patch.object(scheduler, 'alive', return_value=True):
            self.assertFalse(scheduler.ready('FULL', [{'identity': {}}], set()))

    def test_cpu_launcher_home_cwd_requires_exact_source_environment(self):
        self.assertTrue(scheduler.cpu_binding(scheduler.ROOT.parent, str(scheduler.ROOT / 'source'), ''))
        self.assertTrue(scheduler.cpu_binding(scheduler.ROOT / 'source', str(scheduler.ROOT / 'source'), ''))
        self.assertFalse(scheduler.cpu_binding('/tmp', str(scheduler.ROOT / 'source'), ''))
        self.assertFalse(scheduler.cpu_binding(scheduler.ROOT.parent, '/tmp/other', ''))
        self.assertFalse(scheduler.cpu_binding(scheduler.ROOT.parent, str(scheduler.ROOT / 'source'), '0'))

    def test_exiting_proc_is_not_failed_until_waitpid_settles(self):
        child = Mock()
        child.poll.return_value = None
        self.assertIsNone(scheduler.exit_codes([{'child':child}]))
        child.poll.return_value = 0
        self.assertEqual(scheduler.exit_codes([{'child':child}]), [0])
        child.poll.return_value = -9
        self.assertEqual(scheduler.exit_codes([{'child':child}]), [-9])
        self.assertEqual(scheduler.exit_codes([{'child':None}]), [None])


if __name__ == '__main__':
    unittest.main()
