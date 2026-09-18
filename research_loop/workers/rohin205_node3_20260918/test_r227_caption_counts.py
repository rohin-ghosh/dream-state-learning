from copy import deepcopy
import unittest

from r227_caption_counts import aggregate


def attempt(origin='act1', index=1):
    return dict(origin_sha256=origin, record_index=index, scorer_receipt_sha256='receipt-' + origin,
        parser_observed=True, parser_fault=False, no_caption=False, caption_sources=[dict(stage='ACT',
            origin=dict(record_sha256=origin), start=0, end=7, text_sha256='literal-span')],
        results=[dict(ordinal=1, submission_id='submission1', ok=True, accepted=True,
            replayed=False, status='new_pixel', pixel_id='pixel1')])


class CaptionCountTests(unittest.TestCase):
    def test_failed_published_transport_is_not_parser_or_score(self):
        fault = dict(origin_sha256='act1', record_index=1, error='ORIGIN_TRANSPORT_NOT_DISPATCHED',
            parser_observed=False, caption_sources=[], results=[], status='PUBLISHED', executed=True)
        result = aggregate([fault], [dict(attempt_origins=['act1'])])
        self.assertEqual(result['ACT_outcomes'], 1)
        self.assertEqual(result['completed_native_opportunities'], 1)
        self.assertEqual(result['transport_fault_ACTs'], 1)
        self.assertEqual(result['parser_fault_ACTs'], 0)
        self.assertEqual(result['parser_unobserved_ACTs'], 1)
        self.assertEqual(result['newly_scored_captions'], 0)
        self.assertIsNone(result['acceptance_rate']['value'])

    def test_rerouted_origin_and_submission_ids_never_inflate_counts(self):
        first, duplicate, second = attempt(), attempt(index=2), attempt('act2', 3)
        before = deepcopy([first, duplicate, second])
        result = aggregate([first, duplicate, second], [dict(attempt_origins=['act1', 'act2'])])
        self.assertEqual(result['ACT_outcomes'], 2)
        self.assertEqual(result['duplicate_reroute_outcome_records'], 1)
        self.assertEqual(result['newly_scored_captions'], 1)
        self.assertEqual(result['duplicate_submission_results'], 1)
        self.assertEqual(result['new_pixels'], 1)
        self.assertEqual([first, duplicate, second], before)

    def test_cached_replays_excluded_from_rate_denominator(self):
        fresh, cached = attempt(), attempt('act2', 2)
        cached['results'][0]['replayed'] = True
        result = aggregate([fresh, cached], [])
        self.assertEqual(result['newly_scored_captions'], 1)
        self.assertEqual(result['cached_caption_result_ids'], 1)
        self.assertEqual(result['accepted_newly_scored_captions'], 1)
        self.assertEqual(result['acceptance_rate']['denominator'], 1)

    def test_no_caption_and_routing_are_parser_fault_subsets(self):
        empty = attempt()
        empty.update(parser_fault=True, no_caption=True, caption_sources=[], results=[])
        ambiguous = attempt('act2', 2)
        ambiguous.update(parser_fault=True, routing_ambiguity=True, caption_sources=[], results=[])
        result = aggregate([empty, ambiguous], [])
        self.assertEqual((result['parser_fault_ACTs'], result['no_caption_ACTs'],
            result['routing_ambiguity_ACTs'], result['transport_fault_ACTs']), (2, 1, 1, 0))

    def test_opportunities_require_actual_bound_members(self):
        with self.assertRaises(ValueError):
            aggregate([attempt()], [dict(attempt_origins=['unproved'])])
        with self.assertRaises(ValueError):
            aggregate([attempt(), attempt('act2')], [dict(attempt_origins=['act1']),
                dict(attempt_origins=['act1', 'act2'])])

    def test_missing_replayed_status_is_unknown_not_new(self):
        row = attempt()
        del row['results'][0]['replayed']
        result = aggregate([row], [])
        self.assertEqual(result['newly_scored_captions'], 0)
        self.assertEqual(result['unknown_caption_results'], 1)


if __name__ == '__main__':
    unittest.main()
