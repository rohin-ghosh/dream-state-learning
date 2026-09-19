import hashlib
import unittest
from unittest.mock import patch

import project
import review


class ExposureTests(unittest.TestCase):
    def test_verbatim_body_and_original_publication_are_both_required(self):
        digest = lambda text: hashlib.sha256(text.encode()).hexdigest()
        event = dict(actor='parent', event_id='parent:inbox:correct', source_sha256='source', text='Astra: check A-E')
        publication = dict(id='correct', sha256='source', rendered_sha256=digest(event['text']))
        with patch.object(project, 'text_sha', digest, create=True):
            self.assertTrue(project.publication_exposed([event], publication))
            self.assertFalse(project.publication_exposed([], publication))
            self.assertFalse(project.publication_exposed([dict(event, text='summary of check A-E')], publication))
            self.assertFalse(project.publication_exposed([dict(event, source_sha256='other')], publication))

    def test_truncation_is_explicit_and_span_is_hash_bound(self):
        digest = lambda text: hashlib.sha256(text.encode()).hexdigest()
        with patch.object(project, 'text_sha', digest, create=True):
            clipped = project.excerpt('actual source', 6)
        self.assertTrue(clipped['truncated'])
        self.assertEqual(clipped['text'], 'actual')
        self.assertEqual(clipped['excerpt_sha256'], digest('actual'))
        self.assertNotEqual(clipped['excerpt_sha256'], clipped['text_sha256'])


class GradeTests(unittest.TestCase):
    def flags(self):
        return dict(identifies_actual_correction=True, identification_exposed=True,
            next_ACT_implements=True, next_ACT_exact_exposure=True,
            another_relevant_ACT_implements=True, intervening_context_complete=True,
            no_intervening_reminder=True)

    def test_THINK_recognition_is_not_ACT_exposure(self):
        flags = dict(self.flags(), next_ACT_exact_exposure=False)
        review.validate_grade(1, flags)
        with self.assertRaisesRegex(ValueError, 'exact_parent_exposure'):
            review.validate_grade(2, flags)

    def test_level_three_requires_proved_no_reminder(self):
        for reminder in (False, None):
            with self.assertRaisesRegex(ValueError, 'no_reminder_proof'):
                review.validate_grade(3, dict(self.flags(), no_intervening_reminder=reminder))
        with self.assertRaisesRegex(ValueError, 'no_reminder_proof'):
            review.validate_grade(3, dict(self.flags(), intervening_context_complete=False))
        review.validate_grade(3, self.flags())

    def test_generic_error_word_is_not_automatic_identification(self):
        with self.assertRaisesRegex(ValueError, 'identification_required'):
            review.validate_grade(1, dict(self.flags(), identifies_actual_correction=False))

    def test_tiny_quotes_require_actual_literal_bytes(self):
        with self.assertRaisesRegex(ValueError, 'literal_source'):
            review.bound_quote('actual', 'invented', {})
        quote = review.bound_quote('actual source', 'source', {})
        self.assertEqual((quote['start'], quote['end']), (7, 13))

    def test_arithmetic_and_graph_are_independently_checked(self):
        result = review.numeric_checks()
        self.assertEqual(result['learner_assigned'], 19)
        self.assertEqual(result['learner_changed_expression'], 7)
        self.assertEqual(result['frozen_assigned'], 10)
        self.assertEqual(result['C2_ACE_forbidden_pairs'], [['A', 'E']])
        self.assertEqual(result['C2_largest_independent_size'], 2)


if __name__ == '__main__':
    unittest.main()
