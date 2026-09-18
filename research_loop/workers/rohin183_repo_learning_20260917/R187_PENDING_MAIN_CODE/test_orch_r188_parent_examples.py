import unittest

from gpu.orch_r188_parent_examples import MARKER, append_parent_examples, parent_policy_suffix


class ParentExampleTests(unittest.TestCase):
    def test_append_preserves_existing_policy_and_attributes_examples(self):
        original = b'Original parent instructions and masking rules.\n'
        result = append_parent_examples(original)
        self.assertTrue(result.startswith(original))
        for expected in (MARKER, 'Rohin message188', 'C2 separating case',
                         'Pilot receipt discipline', 'Raw Next-Steps handshake',
                         'OWN current object', 'reported example', 'masked training',
                         'parent-withdrawal', 'redundant'):
            self.assertIn(expected.encode(), result)

    def test_duplicate_or_nontext_policy_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'already_present'):
            append_parent_examples(append_parent_examples(b'Original'))
        with self.assertRaisesRegex(ValueError, 'utf8_bytes'):
            append_parent_examples('not bytes')
        with self.assertRaises(UnicodeDecodeError):
            append_parent_examples(b'\xff')

    def test_examples_supply_no_invented_numerical_result(self):
        suffix = parent_policy_suffix()
        self.assertIn('not a new result or a numerical answer', suffix)
        self.assertIn('Do not invent its transcript', suffix)
        self.assertIn('successful process exit alone does not verify its answer', suffix)


if __name__ == '__main__':
    unittest.main()
