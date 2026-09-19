import unittest

import refresh_supervisor


class RefreshIdentityTests(unittest.TestCase):
    def setUp(self):
        self.identity = dict(pid=refresh_supervisor.OLD_PID,
            start_ticks=refresh_supervisor.OLD_START, argv=refresh_supervisor.ARGV)

    def test_only_exact_own_supervisor_is_accepted(self):
        refresh_supervisor.check_identity(self.identity, refresh_supervisor.BOOT_ID)

    def test_reused_pid_other_worker_and_other_boot_are_rejected(self):
        for change in ({"start_ticks": "1"}, {"pid": 378291}, {"argv": ["native"]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                refresh_supervisor.check_identity(dict(self.identity, **change), refresh_supervisor.BOOT_ID)
        with self.assertRaises(ValueError):
            refresh_supervisor.check_identity(self.identity, "another-boot")


if __name__ == "__main__":
    unittest.main()
