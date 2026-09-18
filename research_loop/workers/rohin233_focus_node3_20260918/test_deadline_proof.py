import unittest

from deadline_proof import timeout_seconds


class DeadlineProofTests(unittest.TestCase):
    def test_actual_timeout_not_plan_only(self):
        self.assertEqual(timeout_seconds(['timeout', '--signal=TERM', '--kill-after=5s', '100s', 'python']), 100)
        for arguments in (['python', '100s'], ['timeout', '1h', 'python']):
            with self.assertRaises(ValueError):
                timeout_seconds(arguments)


if __name__ == '__main__':
    unittest.main()
