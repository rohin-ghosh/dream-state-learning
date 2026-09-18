import unittest

from gpu import orch_r119_grid_a40r7_continue as subject


class MigrationTests(unittest.TestCase):
    def test_exact_lease_with_margin(self):
        expiry, end = subject.lease_wall(dict(margin_seconds=21600,
            no_extension_or_new_onboarding=True, conservative_lease_end_utc='2026-09-19T00:00:00+00:00'))
        self.assertEqual(expiry-end, 21600)

    def test_no_margin_waiver(self):
        with self.assertRaises(AssertionError):
            subject.lease_wall(dict(margin_seconds=0, no_extension_or_new_onboarding=True,
                conservative_lease_end_utc='2026-09-19T00:00:00+00:00'))

    def test_no_unbound_lease_extension(self):
        with self.assertRaises(AssertionError):
            subject.lease_wall(dict(margin_seconds=21600, no_extension_or_new_onboarding=True,
                conservative_lease_end_utc='2026-09-20T00:00:00+00:00'))

    def test_exact_frozen_continuation_source(self):
        self.assertTrue(callable(subject.load_base().native))


if __name__ == '__main__':
    unittest.main()
