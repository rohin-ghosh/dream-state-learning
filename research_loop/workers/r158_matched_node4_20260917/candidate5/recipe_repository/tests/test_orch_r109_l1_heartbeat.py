import unittest
from gpu import orch_r109_l1_heartbeat as heartbeat


class HeartbeatTests(unittest.TestCase):
    def test_stale_status_not_inferred_running(self):
        self.assertTrue(heartbeat.stale(100,50))
        self.assertFalse(heartbeat.stale(100,90))
        self.assertFalse(heartbeat.stale(100,50,True))

    def test_clock_never_slides(self):
        self.assertEqual(heartbeat.END,1789491360)
        self.assertEqual(heartbeat.END-heartbeat.START,28800)


if __name__=='__main__':unittest.main()
