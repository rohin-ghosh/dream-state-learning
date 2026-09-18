import unittest

import p3_lease_parent


class LeaseParentTests(unittest.TestCase):
    def test_only_deadline_changes_and_input_is_preserved(self):
        original = {'hard_end_unix': 1789754400, 'nested': {'budget': 160}}
        renewed = p3_lease_parent.renewed_config(original, p3_lease_parent.END_UNIX)
        self.assertEqual(renewed['nested'], original['nested'])
        self.assertIsNot(renewed['nested'], original['nested'])
        self.assertEqual(original['hard_end_unix'], 1789754400)
        self.assertEqual(renewed['hard_end_unix'], p3_lease_parent.END_UNIX)

    def test_no_shortening_or_outside_reported_lease(self):
        original = {'hard_end_unix': 1789754400}
        for deadline in (1789754400, 1789754399, p3_lease_parent.END_UNIX + 1):
            with self.assertRaises(ValueError):
                p3_lease_parent.renewed_config(original, deadline)


if __name__ == '__main__':
    unittest.main()
