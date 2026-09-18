"""Finite parent-withdrawal regression without journal or GPU access."""

import unittest

from clone_parent import due


class ParentWithdrawal(unittest.TestCase):
    def test_followups_only_support_guided_cycles(self):
        self.assertEqual([cycle for cycle in range(51, 59) if due(cycle, set())], [52, 53])

    def test_existing_publication_never_replays(self):
        self.assertFalse(due(52, {52}))
        self.assertFalse(due(53, {52, 53}))
        self.assertTrue(due(53, {52}))


if __name__ == '__main__':
    unittest.main()
