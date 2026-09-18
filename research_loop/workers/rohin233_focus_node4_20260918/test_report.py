import unittest

import report


class ReportTests(unittest.TestCase):
    def row(self, response, stage='ACT'):
        return dict(origin=dict(journal_id='same', response_sha256=str(response),
            response_index=response, stage=stage), P7_REQUEST_render={'record_index': 99},
            child_REQUEST_parent_renders=[dict(publication={'id': 'one-publication'},
                exact_parent_text_rendered=True, all_history_tokens_masked=True)],
            interpretation='ACTUAL_REPLY_TO_RENDERED_P7_INPUT')

    def test_deduplication_and_chronological_order(self):
        rows = [self.row(11), self.row(2), self.row(11)]
        self.assertEqual([row['origin']['response_index'] for row in report.unique_origins(rows)], [2, 11])

    def test_stage_outputs_not_independent_conversations(self):
        route = dict(observed_utc='cut', forward_stage_limit='ACT-only',
            forwarded_P7_outputs=[self.row(2)],
            returned_actual_child_outputs=[self.row(3, 'THINK'), self.row(4), self.row(5, 'LEARN')])
        result = report.direction_metrics(route)
        self.assertEqual(result['returned_parent_conditioned_stages_rendered_back_in_P7'], 3)
        self.assertEqual(result['P7_publications_rendered_in_bound_child_requests'], 1)
        self.assertTrue(result['not_independent_conversation_count'])
        self.assertFalse(result['semantic_success_claim'])

    def test_missing_retirement_not_success(self):
        result = report.retirement(None, 2, {'complete_index': 80})
        self.assertEqual(result['status'], 'FINAL_PRESERVATION_RECEIPT_PENDING')
        self.assertEqual(result['fresh_complete_record'], 80)

    def test_unverified_child_render_not_roundtrip_proof(self):
        row = self.row(3)
        row['child_REQUEST_parent_renders'][0]['exact_parent_text_rendered'] = False
        route = dict(observed_utc='cut', forward_stage_limit='ACT-only',
            forwarded_P7_outputs=[], returned_actual_child_outputs=[row])
        self.assertEqual(report.direction_metrics(route)['returned_parent_conditioned_stages_rendered_back_in_P7'], 0)

    def test_safe_output_drops_absolute_private_paths_not_receipt_ids(self):
        value = {'path': '/private/host', 'publication': {'id': 'retained'},
            'source': {'path': 'research_loop/safe.json'}}
        self.assertEqual(report.without_private_paths(value),
            {'publication': {'id': 'retained'}, 'source': {'path': 'research_loop/safe.json'}})


if __name__ == '__main__':
    unittest.main()
