from copy import deepcopy
import unittest

from audit_saved_counts import summarize


def row(identifier='one'):
    return dict(origin_sha256=identifier, receipt_sha256=identifier, parsed=3,
        scored=2, accepted=1, new_pixels=1, cached=1, format_fault=True,
        unix=1789720000, top_k_values=[50], scored_sources=[
            dict(accepted=True, stage='ACT', text_sha256='accepted', exact_source_span_verified=True),
            dict(accepted=False, stage='ACT', text_sha256='rejected', exact_source_span_verified=True)])


class SavedCountAuditTests(unittest.TestCase):
    def test_rate_excludes_cached_and_parser_only_entries(self):
        original = row()
        before = deepcopy(original)
        result = summarize([original])
        self.assertEqual(result['accept_rate'], 0.5)
        self.assertEqual(result['ACT_attempts'], 1)
        self.assertEqual(result['parsed'], 3)
        self.assertEqual(result['scored'], 2)
        self.assertEqual(original, before)

    def test_missing_legacy_hash_is_not_a_distinct_caption(self):
        original = row()
        original['scored_sources'][0].update(text_sha256=None, exact_source_span_verified=False)
        result = summarize([original])
        self.assertEqual(result['accepted_distinct_known_text_hashes'], 0)
        self.assertEqual(result['accepted_missing_source_spans'], 1)

    def test_duplicate_attempts_across_scorer_migrations_fail(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_ACT'):
            summarize([row(), row()])

    def test_score_denominator_mismatch_fails(self):
        original = row()
        original['accepted'] = 2
        with self.assertRaisesRegex(ValueError, 'denominators'):
            summarize([original])

    def test_empty_is_unknown_rate_not_zero_percent(self):
        self.assertIsNone(summarize([])['accept_rate'])


if __name__ == '__main__':
    unittest.main()
