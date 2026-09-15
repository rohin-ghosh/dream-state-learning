from types import SimpleNamespace
import unittest

from gpu import orch_r118_claude_recovery_rebind as recovery


class RecoveryRebindTests(unittest.TestCase):
    def test_waits_for_reparent_and_two_equal_actual_reads(self):
        parents = iter([33, 1, 1])
        identities = iter([{'pid': 20, 'ppid': 33}, {'pid': 20, 'ppid': 1},
                           {'pid': 20, 'ppid': 1}, {'pid': 20, 'ppid': 1}])
        actual = recovery.settled_identity(lambda: next(identities),
            parent_pid=lambda: next(parents), sleep=lambda duration: None)
        self.assertEqual(actual, {'pid': 20, 'ppid': 1})

    def test_unsettled_parent_never_publishes_identity(self):
        moments = iter([0, 0, 2])
        with self.assertRaisesRegex(RuntimeError, 'parent_not_settled'):
            recovery.settled_identity(lambda: self.fail('identity read too early'),
                parent_pid=lambda: 33, clock=lambda: next(moments),
                sleep=lambda duration: None, timeout=1)

    def test_only_grid_terminal_and_identity_publication_change(self):
        original = SimpleNamespace(TERMINALS={'F1': 'R118_PARALLEL_TERMINAL.json',
            'F2': 'GUARD_TERMINAL.json', 'F3': 'GUARD_TERMINAL.json', 'F4': 'old'},
            identity=lambda: {'ppid': 1}, serve=object())
        serve = original.serve
        configured = recovery.configure(original)
        self.assertIs(configured.serve, serve)
        self.assertEqual(configured.TERMINALS['F4'], 'R118_GRID_PARALLEL_RECOVERY_V1_TERMINAL.json')
        self.assertEqual(configured.TERMINALS['F1'], 'R118_PARALLEL_TERMINAL.json')


if __name__ == '__main__':
    unittest.main()
