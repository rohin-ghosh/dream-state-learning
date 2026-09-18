import unittest

from deadline_proof import timeout_seconds, wall_adopted


class DeadlineProofTests(unittest.TestCase):
    def test_adoption_requires_current_load_and_actual_wall_not_plan(self):
        row = dict(status='LOADED_ALIVE', actual_native=dict(pid=123), LOADED=dict(index=10),
            resident_deadline_utc='2026-09-24T18:00:00+00:00',
            WALL_EXTENDED=dict(new_deadline_utc='2026-09-24T18:00:00+00:00'))
        self.assertTrue(wall_adopted(row))
        for changed in (dict(status='DISPATCHED_NOT_LOADED'), dict(LOADED=None),
                dict(actual_native=None), dict(WALL_EXTENDED={}), dict(resident_deadline_utc=None)):
            self.assertFalse(wall_adopted(dict(row, **changed)))

    def test_actual_timeout_not_plan_only(self):
        self.assertEqual(timeout_seconds(['timeout', '--signal=TERM', '--kill-after=5s', '100s', 'python']), 100)
        for arguments in (['python', '100s'], ['timeout', '1h', 'python']):
            with self.assertRaises(ValueError):
                timeout_seconds(arguments)


if __name__ == '__main__':
    unittest.main()
