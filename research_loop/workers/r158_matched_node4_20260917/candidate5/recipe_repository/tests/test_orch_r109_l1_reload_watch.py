import unittest

from gpu import orch_r109_l1_reload_watch as watcher


class ReloadWatchTests(unittest.TestCase):
    def test_empty_duration_is_interval_not_exact(self):
        state,closed=watcher.update_window(None,10,True)
        state,closed=watcher.update_window(state,12,False)
        state,closed=watcher.update_window(state,14,False)
        state,closed=watcher.update_window(state,16,True)
        self.assertEqual(closed['lower_bound_seconds'],2)
        self.assertEqual(closed['upper_bound_seconds'],6)

    def test_initial_empty_window_is_left_censored(self):
        state,closed=watcher.update_window(None,10,False)
        state,closed=watcher.update_window(state,12,True)
        self.assertIsNone(closed['upper_bound_seconds'])

    def test_eta_does_not_gate_release_or_extend_lifetime(self):
        value=watcher.startup_estimate(10,86,False)
        self.assertTrue(value['startup_warning'])
        self.assertTrue(value['never_a_scientific_gate'])
        self.assertTrue(value['never_a_release_signal'])
        self.assertFalse(watcher.startup_estimate(10,86,True)['startup_warning'])
        self.assertEqual(watcher.startup_estimate(watcher.END-10,watcher.END,False)['first_progress_eta_upper_unix'],watcher.CUTOFF)


if __name__=='__main__':unittest.main()
