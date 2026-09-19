from copy import deepcopy
import hashlib
import unittest

from organism_v6 import orch_r194_code_target_filter as review
from organism_v6 import orch_r203_prose_target_filter as prose
from organism_v6 import orch_r213_content_target_filter as content
from organism_v6 import orch_r220_question_target_filter as question


def target(text):
    return dict(actor='child', split='TRAIN', prefix_loss=False, target_loss=True,
        source_sha256=hashlib.sha256(text.encode()).hexdigest(), segment=1,
        target=text, content_target_filter=content.POLICY,
        question_target_filter=question.POLICY)


class QuestionTargetTests(unittest.TestCase):
    def test_actual_questions_are_eligible_and_keep_exact_source_bytes(self):
        for text in ('Fable, what survives my next sleep?',
                     'Question for Fable: why does an adapter forget?',
                     'Could you explain this, Fable?', 'Fable, why?'):
            with self.subTest(text=text):
                row = target(text)
                before = deepcopy(row)
                retained, old, proof = review.filter_learn_review_targets([row], [], review.REVIEW_POLICY)
                self.assertEqual(retained, [row])
                self.assertEqual(row, before)
                self.assertEqual(old, [])
                evidence = proof['content_target_filter']['checks'][0]['evidence']
                self.assertTrue(evidence['eligible'])
                self.assertFalse(evidence['question_target_filter']['delivery_claimed'])

    def test_no_implicit_exception_for_historical_v1_rows(self):
        row = target('Fable, what survives my next sleep?')
        del row['question_target_filter']
        proof = content.content_exclusions([row])
        self.assertFalse(proof['checks'][0]['evidence']['eligible'])
        self.assertNotIn('question_target_filter', proof['checks'][0]['evidence'])

    def test_intention_without_actual_question_stays_excluded(self):
        row = target('I will ask Fable about the format of the data.')
        self.assertEqual(question.question_lines(row['target']), [])
        self.assertEqual(content.content_exclusions([row])['excluded'][0]['reason'], 'meta_only_target')

    def test_code_fence_is_not_an_outgoing_question(self):
        text = '```python\nprint("Fable, what is your answer?")\n```'
        self.assertEqual(question.question_lines(text), [])
        self.assertEqual(question.question_lines('~~~\nFable, why?\n~~~\nFable, what now?')[0]['text'], 'Fable, what now?')

    def test_spans_bind_exact_lines_with_unicode_and_crlf(self):
        text = 'An earlier line.\r\nFable, can I use naïve counting?\r\nA last line.'
        matches = question.question_lines(text)
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(text[match['start']:match['end']], match['text'])
        self.assertEqual(hashlib.sha256(match['text'].encode()).hexdigest(), match['text_sha256'])

    def test_repetition_and_wrapped_prose_still_excluded(self):
        cases = ('Fable, why why why why why?',
                 'Story:\n```python\nprint("Byte opened the door and found a folded map inside.")\n```\nFable, why?')
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(content.content_exclusions([target(text)])['excluded'])
        row = target('Fable, what survives my next sleep?')
        row['token_ids'] = [42] * 5
        self.assertEqual(content.content_exclusions([row])['excluded'][0]['reason'], 'repetition_collapse_target')

    def test_language_backstop_still_applies(self):
        row = target('Fable, what happens when 我的回答完全变成中文呢?')
        row['prose_target_filter'] = prose.POLICY
        retained, unused, proof = review.filter_learn_review_targets([row], [], review.REVIEW_POLICY)
        self.assertEqual(retained, [])
        self.assertTrue(proof['prose_target_filter']['excluded'])

    def test_unknown_policies_and_non_child_rows_fail(self):
        row = target('Fable, why?')
        row['question_target_filter'] = 'invented'
        with self.assertRaisesRegex(ValueError, 'known_question'):
            content.content_exclusions([row])
        row['question_target_filter'] = question.POLICY
        row['actor'] = 'parent'
        with self.assertRaisesRegex(ValueError, 'child_targets_only'):
            content.content_exclusions([row])
        row = target('Fable, why?')
        del row['content_target_filter']
        with self.assertRaisesRegex(ValueError, 'require_content_filter'):
            content.content_exclusions([row])

    def test_bounded_scan_does_not_grant_exception(self):
        row = target('Fable, why?\n' + 'x' * question.MAX_CHARACTERS)
        self.assertTrue(content.content_exclusions([row])['excluded'])


if __name__ == '__main__':
    unittest.main()
