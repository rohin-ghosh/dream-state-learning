import sys
import unittest

from gpu import orch_rich_hot_a100_minor_scan
sys.modules['orch_rich_hot_a100_minor_scan'] = orch_rich_hot_a100_minor_scan
from gpu import orch_rich_hot_a100_release_watch as watcher


class ReleaseWatchTests(unittest.TestCase):
    def test_new_floor_ownership(self):
        self.assertEqual(watcher.requested_indices('Laplace', dict(requester='Laplace', launch_ready=True)), (2, 3))
        self.assertEqual(watcher.requested_indices('Anscombe', dict(requester='Anscombe', launch_ready=True)), (4, 5, 7))

    def test_preparation_is_not_readiness(self):
        for request in ({}, dict(requester='Laplace', launch_ready=False), dict(requester='Anscombe', launch_ready=True)):
            with self.assertRaises(ValueError):
                watcher.requested_indices('Laplace', request)

    def test_never_signal_permanent_generation_or_peer_fits(self):
        for index in (0, 1, 6):
            with self.assertRaises(ValueError):
                watcher.signal_owned(index, {})


if __name__ == '__main__':
    unittest.main()
