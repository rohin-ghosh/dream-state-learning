import signal
import unittest

import pair_cutoff


class CutoffTests(unittest.TestCase):
    def test_rejects_other_lives_and_short_lease_margin(self):
        plan = dict(physical=0, root=str(pair_cutoff.ROOT / 'raw'),
                    lease_end_unix=pair_cutoff.SAFE_END + 21600)
        pair_cutoff.validate_policy(plan, pair_cutoff.TERM_AT - 1)
        for change in ({'physical': 1}, {'root': '/other'},
                       {'lease_end_unix': pair_cutoff.SAFE_END + 21599}):
            with self.assertRaises(ValueError):
                pair_cutoff.validate_policy(dict(plan, **change), pair_cutoff.TERM_AT - 1)

    def test_no_signal_before_deadline_and_no_pause_signal(self):
        now, sent, events = [0], [], []
        def sleeper(seconds):
            now[0] += seconds
        def sender(descriptor, operation):
            sent.append((now[0], operation))
        pair_cutoff.wait_and_finish(10, 4, events.append, clock=lambda: now[0],
            sleeper=sleeper, sender=sender, waiter=lambda *arguments: ([], [], []))
        self.assertEqual(sent, [(4, signal.SIGTERM), (4, signal.SIGKILL)])
        self.assertNotIn(signal.SIGSTOP, [operation for stamp, operation in sent])

    def test_earlier_exit_is_not_signalled(self):
        sent = []
        pair_cutoff.wait_and_finish(10, 4, lambda event: None, clock=lambda: 0,
            sender=lambda *arguments: sent.append(arguments),
            waiter=lambda *arguments: ([10], [], []))
        self.assertEqual(sent, [])


if __name__ == '__main__':
    unittest.main()
