import unittest

from fleet_deadlines import verified


class DeadlineEvidenceTests(unittest.TestCase):
    def test_dispatch_or_pid_alone_does_not_prove_renewal(self):
        self.assertFalse(verified(dict(alive_now=True, identity_matches=True)))

    def test_requires_both_journal_events_and_current_identity(self):
        row = dict(loaded_index=10, wall_index=9, resident_deadline_utc='2026-09-25T18:00:00Z',
            target_deadline_utc='2026-09-25T18:00:00Z',
            alive_now=True, identity_matches=True)
        self.assertTrue(verified(row))
        for key in row:
            changed = dict(row)
            changed[key] = None
            self.assertFalse(verified(changed))
        self.assertFalse(verified(dict(row, resident_deadline_utc='2026-09-18T18:00:00Z')))
        self.assertFalse(verified(dict(row, resident_deadline_utc='2026-09-26T18:00:00Z')))


if __name__ == '__main__':
    unittest.main()
