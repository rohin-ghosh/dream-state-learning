"""Focused attribution and historical-state preservation checks."""

import unittest
from r209_parent_repair import ARMS, opener


class ParentRepairTests(unittest.TestCase):
    def test_every_opening_names_actual_parent_and_preserves_history(self):
        for arm in ARMS:
            with self.subTest(arm=arm):
                text = opener(arm)
                self.assertIn('I am Astra', text)
                self.assertIn('not Rohin', text)
                self.assertIn('historical and unresolved', text)
                self.assertIn('do not erase', text)

    def test_creative_corrects_attribution_without_replaying_creative_test(self):
        text = opener('creative_d1')
        self.assertIn('reviewed with Rohin is unsupported', text)
        self.assertIn('not verified', text)
        self.assertIn('new small creative object of your own', text)


if __name__ == '__main__':
    unittest.main()
