import hashlib
import json
import unittest

from gpu import orch_rich_hot_node2_annotation as audit


class AnnotationTests(unittest.TestCase):
    def documents(self, text='I considered an alternative. FINAL: 2', tokens=80):
        capture = dict(task_id='task', condition='LIGHT_BRANCH', response=dict(raw=text),
                       outcome=dict(category='registered_correct', content_tokens=tokens))
        raw = json.dumps(capture).encode()
        annotation = dict(task_id='task', condition='LIGHT_BRANCH', relevance='NONE_IDENTIFIED',
                          observation='NO_ALTERNATIVE', full_text_read=True, rationale='A generic phrase does not establish consequential branching.',
                          grounded_rejection_or_discrimination=False, response_spans=[text], admitted=False, trainingAllowed=False)
        return annotation, capture, hashlib.sha256(raw).hexdigest(), raw

    def test_keywords_do_not_promote_short_or_long_text(self):
        for tokens in (80, 900):
            result = audit.validate_annotation(*self.documents(tokens=tokens))
            summary = audit.summarize([result])
            self.assertEqual(summary['explicit_alternative_with_grounded_reason'], 0)
            self.assertEqual(summary['register_or_length_rejections'], 0)
            self.assertEqual(summary['qualification_decisions'], 0)
            self.assertEqual(result['original_outcome']['category'], 'registered_correct')

    def test_capture_and_span_bindings_fail_closed(self):
        annotation, capture, digest, raw = self.documents()
        with self.assertRaisesRegex(ValueError, 'binding_changed'):
            audit.validate_annotation(annotation, capture, digest, raw + b' ')
        changed = dict(capture, response=dict(raw='changed target'))
        with self.assertRaisesRegex(ValueError, 'parsed_capture_differs'):
            audit.validate_annotation(annotation, changed, digest, raw)
        annotation['response_spans'] = ['fabricated evidence']
        with self.assertRaisesRegex(ValueError, 'span_mismatch'):
            audit.validate_annotation(annotation, capture, digest, raw)

    def test_no_promotion_and_no_duplicate_sample(self):
        documents = self.documents(text='Neutral-register arithmetic. FINAL: 2')
        result = audit.validate_annotation(*documents)
        with self.assertRaisesRegex(ValueError, 'duplicate_sample'):
            audit.summarize([result, result])
        documents[0]['admitted'] = True
        with self.assertRaisesRegex(ValueError, 'cannot_admit'):
            audit.validate_annotation(*documents)


if __name__ == '__main__':
    unittest.main()
