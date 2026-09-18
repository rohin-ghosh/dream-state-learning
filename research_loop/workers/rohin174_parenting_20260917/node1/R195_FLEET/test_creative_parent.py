import unittest

from creative_parent import parent_payload


class ParentPayloadTest(unittest.TestCase):
    def test_journal_adds_one_speaker_label(self):
        for supplied in ('Astra: Check the receipt.', 'Astra: Astra: Check the receipt.'):
            self.assertEqual('Astra: ' + parent_payload(supplied), 'Astra: Check the receipt.')

    def test_preserves_unprefixed_body_and_internal_attribution(self):
        for supplied in ('As Astra, my tentative judgment is unchanged.',
                         'Quote: Astra: keep this exact text.',
                         'I am Astra, your new parent.'):
            self.assertEqual(parent_payload(supplied), supplied)

    def test_prefix_whitespace_only_is_removed(self):
        self.assertEqual(parent_payload('  Astra: \nAstra: Keep the draft.\n'), 'Keep the draft.\n')


if __name__ == '__main__':
    unittest.main()
