import copy
import unittest

from prepare_takeovers import ASSIGNMENTS, PEERS, candidate, summarize_ledger


class TakeoverPreparationTests(unittest.TestCase):
    def config(self):
        return dict(root='/localhome/local-rohing/orch_example/run1', node='ovx3',
                    cadence_responses=3, schedule_on='request', start_after_request_count=99,
                    hard_end_unix=1789776000, principles_sha256='old-policy-pin')

    def row(self, label='run1'):
        return dict(label=label, entry_kind='R169_FROZEN_SOURCE_AUTH_REFRESH',
                    output_path='/existing/parent')

    def entry(self):
        return dict(attempt='parent_000001',
            source=dict(schema='R153_COMMITTED_TRAIN_SNAPSHOT_V1', split='TRAIN', response_count=9),
            source_pin=dict(path='SOURCE.json', sha256='source-hash'),
            result=dict(source_sha256='source-hash', status='PUBLISHED', object_id='object',
                publication=dict(id='owned-publication', path='/inbox/id.json', sha256='message-hash')),
            result_pin=dict(path='RESULT.json', sha256='result-hash'))

    def test_exact_assignments(self):
        self.assertEqual(ASSIGNMENTS, dict(run1=('A', 1), pilot=('B', 2),
            repo_reader=('C', 3), C1=('B', 2), C3=('A', 1), C4=('C', 3), C5=('D', 3)))

    def test_exact_peers_exclude_C2(self):
        self.assertEqual(PEERS, (('C1', 'C3'), ('C4', 'C5')))
        self.assertNotIn('C2', ASSIGNMENTS)

    def test_response_clock_does_not_reuse_request_count(self):
        result = candidate(self.row(), self.config(), dict(response_cursor_lower_bound=12))
        self.assertEqual(result['candidate_config']['start_after_response_count'], 12)
        self.assertEqual(result['candidate_config']['schedule_on'], 'response')
        self.assertNotIn('start_after_request_count', result['candidate_config'])

    def test_original_config_and_wall_untouched(self):
        config = self.config()
        original = copy.deepcopy(config)
        result = candidate(self.row(), config, dict(response_cursor_lower_bound=12))
        self.assertEqual(config, original)
        self.assertEqual(result['candidate_config']['hard_end_unix'], config['hard_end_unix'])
        self.assertEqual(result['candidate_config']['principles_sha256'], 'old-policy-pin')

    def test_C2_rejected_before_candidate(self):
        with self.assertRaisesRegex(ValueError, 'C2_excluded'):
            candidate(self.row('C2'), self.config(), {})

    def test_C2_root_rejected_even_with_other_label(self):
        config = self.config()
        config['root'] = '/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life'
        with self.assertRaisesRegex(ValueError, 'C2_excluded'):
            candidate(self.row(), config, {})

    def test_unsettled_dispatch_reserves_cursor_without_replay(self):
        entry = self.entry()
        del entry['result']
        result = summarize_ledger([entry])
        self.assertEqual(result['response_cursor_lower_bound'], 9)
        self.assertEqual(result['blockers'][0]['reason'], 'UNSETTLED_ATTEMPT_NO_REPLAY')

    def test_uncertain_publication_blocks(self):
        entry = self.entry()
        entry['result']['status'] = 'PUBLICATION_UNKNOWN'
        result = summarize_ledger([entry])
        self.assertEqual(result['blockers'][0]['reason'], 'UNCERTAIN_PUBLICATION_NO_REPLAY')

    def test_pending_publication_identity_preserved(self):
        result = summarize_ledger([self.entry()])
        self.assertEqual(result['pending_publications'][0]['id'], 'owned-publication')
        self.assertFalse(result['new_exposure_proven'])

    def test_old_complete_is_not_rendered_REQUEST_proof(self):
        entry = self.entry()
        entry.update(delivery=dict(status='COMPLETE', result_sha256='result-hash'),
                     delivery_pin=dict(path='DELIVERED.json', sha256='delivery-hash'))
        result = summarize_ledger([entry])
        self.assertTrue(result['prior_delivery_metadata'][0][
            'rendered_exposure_requires_independent_REQUEST_binding'])
        self.assertFalse(result['new_exposure_proven'])

    def test_mismatched_source_and_delivery_rejected(self):
        entry = self.entry()
        entry['result']['source_sha256'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'result_source_pin'):
            summarize_ledger([entry])
        entry = self.entry()
        entry['delivery'] = dict(result_sha256='wrong')
        with self.assertRaisesRegex(ValueError, 'delivery_result_binding'):
            summarize_ledger([entry])

    def test_non_TRAIN_rejected(self):
        entry = self.entry()
        entry['source']['split'] = 'FINAL'
        with self.assertRaisesRegex(ValueError, 'TRAIN_only'):
            summarize_ledger([entry])

    def test_staged_not_live_or_three_sleep_claim(self):
        result = candidate(self.row(), self.config(), dict(response_cursor_lower_bound=12))
        self.assertEqual(result['status'], 'PREPARED_NOT_EXECUTABLE')
        self.assertIsNone(result['common_source_bundle'])
        self.assertIsNone(result['first_rendered_REQUEST'])
        self.assertIsNone(result['three_sleep_start'])


if __name__ == '__main__':
    unittest.main()
