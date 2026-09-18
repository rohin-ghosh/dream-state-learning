"""Focused checks for exact-output, non-coercive language feedback."""

from copy import deepcopy
import unittest

from r211_language_parent import message


class LanguageParentTests(unittest.TestCase):
    def samples(self, quarantined=True):
        return [dict(index=index, sha256=str(index) * 64,
            raw='  原样\tV＝３\n```python\nunchanged = "The"\n```\n',
            evidence=dict(quarantined=quarantined)) for index in (1, 2)]

    def test_exact_samples_preserved_and_conversation_stays_primary(self):
        samples = self.samples()
        before = deepcopy(samples)
        text = message('conversational', samples)
        self.assertEqual(samples, before)
        for sample in samples:
            self.assertIn('\n' + sample['raw'] + '\nEND EXACT OWN RESPONSE ' + str(sample['index']), text)
        self.assertIn('Conversation remains your priority', text)
        self.assertIn('You choose its cadence', text)
        self.assertIn('this parent message and quoted examples remain masked context', text)

    def test_fragment_fault_is_not_claimed_as_detector_success(self):
        text = message('p32', self.samples(False), fragment_fault=True)
        self.assertIn('filter does not detect it', text)
        self.assertIn('last-line backstop', text)
        self.assertNotIn('same English-output language fault appears in both', text)

    def test_single_match_does_not_claim_repeated_detector_finding(self):
        samples = self.samples()
        samples[1]['evidence']['quarantined'] = False
        text = message('peer_math', samples)
        self.assertIn('not claiming a repeated detector finding', text)


if __name__ == '__main__':
    unittest.main()
