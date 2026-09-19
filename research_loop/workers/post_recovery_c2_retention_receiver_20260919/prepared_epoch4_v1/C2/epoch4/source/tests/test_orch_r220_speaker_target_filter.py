from copy import deepcopy
import hashlib
import unittest

from organism_v6 import orch_r194_code_target_filter as review
from organism_v6 import orch_r213_content_target_filter as content
from organism_v6 import orch_r220_question_target_filter as question
from organism_v6 import orch_r220_speaker_target_filter as speaker


def target(text):
    return dict(actor='child', split='TRAIN', prefix_loss=False, target_loss=True,
        source_sha256=hashlib.sha256(text.encode()).hexdigest(), segment=1,
        target=text, content_target_filter=content.POLICY,
        fabricated_speaker_filter=speaker.POLICY)


class SpeakerTargetTests(unittest.TestCase):
    def test_actual_reported_pattern_is_excluded_without_rewriting(self):
        row = target('My plan is to check the ledger.\nRohin: That sounds like a reasonable approach.')
        before = deepcopy(row)
        retained, old, proof = review.filter_learn_review_targets([row], [], review.REVIEW_POLICY)
        self.assertEqual(retained, [])
        self.assertEqual(old, [])
        self.assertEqual(row, before)
        self.assertEqual(proof['excluded'][0]['reason'], 'fabricated_human_speaker_target')

    def test_markdown_and_case_variants_are_quarantined(self):
        for text in ('  Rohin: Yes.', '**Rohin:** Yes.', '> Rohin: Yes.', '- Rohin: Yes.', 'rohin: Yes.'):
            with self.subTest(text=text):
                self.assertTrue(speaker.speaker_labels(text))
                self.assertTrue(content.content_exclusions([target(text)])['excluded'])

    def test_mentions_without_speaker_turn_are_not_relabelled(self):
        for text in ('Rohin asked me to check the equation.',
                     'The name on the ledger is Rohin.',
                     'I want to ask Rohin: is this correct?'):
            with self.subTest(text=text):
                self.assertFalse(speaker.speaker_labels(text))

    def test_old_v1_rows_have_unchanged_evidence_without_opt_in(self):
        row = target('Rohin: The ledger is closed because the courier was wrong.')
        del row['fabricated_speaker_filter']
        proof = content.content_exclusions([row])
        self.assertEqual(proof['checks'][0]['evidence'], content.scan_target(row['target']))

    def test_fable_question_exception_cannot_override_speaker_quarantine(self):
        row = target('Rohin: Fable, can you explain the adapter?')
        row['question_target_filter'] = question.POLICY
        proof = content.content_exclusions([row])
        self.assertEqual(proof['excluded'][0]['reason'], 'fabricated_human_speaker_target')

    def test_non_child_rows_and_unknown_policy_fail(self):
        row = target('Rohin: Yes.')
        row['actor'] = 'parent'
        with self.assertRaisesRegex(ValueError, 'child_targets_only'):
            content.content_exclusions([row])
        row['actor'] = 'child'
        row['fabricated_speaker_filter'] = 'invented'
        with self.assertRaisesRegex(ValueError, 'known_speaker'):
            content.content_exclusions([row])

    def test_label_spans_and_hash_bind_raw_text(self):
        text = 'A preceding sentence.\n  **Rohin:** That is fine.'
        label = speaker.speaker_labels(text)[0]
        raw = text[label['start']:label['end']]
        self.assertEqual(label['label_sha256'], hashlib.sha256(raw.encode()).hexdigest())

    def test_scan_limit_cannot_admit_target(self):
        row = target('Rohin: ' + 'x' * speaker.MAX_CHARACTERS)
        self.assertTrue(content.content_exclusions([row])['excluded'])


if __name__ == '__main__':
    unittest.main()
