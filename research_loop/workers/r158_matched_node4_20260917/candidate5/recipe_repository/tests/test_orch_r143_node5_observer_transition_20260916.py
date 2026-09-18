import importlib.util
import inspect
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'research_loop/workers/r143_node5_allocator_20260916t1427z'
SPEC = importlib.util.spec_from_file_location('node5_transition_test', ROOT / 'node5_observer_transition_20260916t1630z.py')
transition = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transition)


class ObserverTransitionTests(unittest.TestCase):
    def setUp(self):
        self.actor = dict(pid=2070925, argv=['python', '-B', 'owned', '--action', 'handoff'])
        self.dispatch = dict(pid=2070925, command=self.actor['argv'],
            script_sha256='3054bac4f1a2674e21eda1ab62183eb01d13024b359c1f2ebb308eba92536ad7')

    def test_waiting_only_observer_accepted(self):
        transition.waiting_only(self.actor, self.dispatch, {})

    def test_each_boundary_action_marker_blocks_stop(self):
        for marker in transition.ACTION_MARKERS:
            with self.subTest(marker=marker), self.assertRaisesRegex(ValueError, 'action_started'):
                transition.waiting_only(self.actor, self.dispatch, {marker: True})

    def test_other_pid_command_or_source_rejected(self):
        for changed in (dict(self.actor, pid=123), dict(self.actor, argv=['other'])):
            with self.assertRaises(ValueError):
                transition.waiting_only(changed, self.dispatch, {})
        with self.assertRaises(ValueError):
            transition.waiting_only(self.actor, dict(self.dispatch, script_sha256='wrong'), {})

    def test_lock_and_proofs_precede_only_observer_signal(self):
        source = inspect.getsource(transition.transition)
        self.assertLess(source.index('both_new_exact_real_strict_probes'), source.index('signal.pidfd_send_signal'))
        self.assertLess(source.index('fcntl.flock'), source.index('waiting_only'))
        self.assertLess(source.index('os.pidfd_open(OBSERVER_PID)'), source.index('signal.pidfd_send_signal'))
        self.assertEqual(source.count('signal.pidfd_send_signal'), 1)
        self.assertIn('no_child_or_supervisor_signaled', source)
        self.assertNotIn('SIGKILL', source)


if __name__ == '__main__':
    unittest.main()
