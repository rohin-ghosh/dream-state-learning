from copy import deepcopy
import unittest
from unittest.mock import patch

import movement


def fixture(texts, guidance_at=()):
    frames = []
    records = []
    for ordinal, text in enumerate(texts, 1):
        external = []
        if ordinal in guidance_at:
            identity = f'parent:inbox:{ordinal}'
            records.append(dict(kind='INBOX', event_id=identity, index=ordinal*10-1))
            external = [dict(actor='parent', event_id=identity, source_sha256=str(ordinal))]
        frames.append(dict(stage='ACT', request=dict(kind='REQUEST', index=ordinal*10,
            sha256='a'*64, cycle=ordinal, external=external), response=dict(kind='RESPONSE',
            index=ordinal*10+1, sha256='b'*64, text=text, time_unix=ordinal)))
    evidence = dict(records=records, observed_unix=4, journal_id='fixture', coverage_start=0,
                    through=dict(index=31), caught_up=True)
    return evidence, frames


class MovementTests(unittest.TestCase):
    def summarize(self, texts, guidance_at=()):
        evidence, frames = fixture(texts, guidance_at)
        with patch.object(movement.correction, 'frames', return_value=frames):
            return movement.summarize(evidence, 'test')

    def test_three_unguided_cycles_alert_but_never_claim_correctness(self):
        result = self.summarize(['I will write a caption.']*3)
        self.assertTrue(result['three_cycle_unguided_alert'])
        self.assertIsNone(result['latest_act']['correct_checked_results'])
        self.assertEqual(result['learning_changes'], [])

    def test_actual_new_guidance_breaks_unguided_alert_not_repetition(self):
        result = self.summarize(['I will write a caption.']*3, guidance_at=(3,))
        self.assertFalse(result['three_cycle_unguided_alert'])
        self.assertTrue(result['current_alert'])
        self.assertEqual(result['latest_act']['new_guidance_count'], 1)

    def test_no_act_is_unknown_and_script_count_is_not_language_proof(self):
        self.assertIsNone(self.summarize([])['current_alert'])
        result = self.summarize(['我不知道。'])
        self.assertGreater(result['latest_act']['cjk_fullwidth_character_count'], 0)
        self.assertEqual(result['latest_act']['classification']['classification'], 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
