import unittest

from p3_renewed_receipts import proof


class RenewedReceiptTests(unittest.TestCase):
    def setUp(self):
        self.loaded = dict(original_journal_id='original', loaded=dict(index=10))
        self.publication = dict(id='message', sha256='source')
        self.request = dict(kind='REQUEST', index=11, sha256='request', time_unix=1789760000,
            masked=True, external=[dict(event_id='environment:inbox:message', source_sha256='source')])
        self.evidence = dict(journal_id='original', records=[self.request])

    def test_exact_source_and_actual_render_required(self):
        self.request['external'][0]['source_sha256'] = 'different'
        result = proof(self.publication, 'environment', self.evidence, [], self.loaded)
        self.assertEqual(result['status'], 'PUBLISHED_NOT_YET_RENDERED_IN_WINDOW')
        self.request['external'][0]['source_sha256'] = 'source'
        result = proof(self.publication, 'environment', self.evidence, [], self.loaded)
        self.assertEqual(result['status'], 'RENDERED_ACT_PENDING')

    def test_pre_load_or_unmasked_evidence_is_not_delivery(self):
        self.request['index'] = 9
        with self.assertRaises(ValueError):
            proof(self.publication, 'environment', self.evidence, [], self.loaded)
        self.request['index'] = 11
        self.request['masked'] = False
        with self.assertRaises(ValueError):
            proof(self.publication, 'environment', self.evidence, [], self.loaded)

    def test_requires_committed_act_not_only_a_think_response(self):
        frame = dict(stage='THINK', request=self.request, response=dict(index=12, sha256='response',
            time_unix=1789760001, text='Actual output'), commit=dict(index=13), stage_receipt=dict(index=14))
        result = proof(self.publication, 'environment', self.evidence, [frame], self.loaded)
        self.assertEqual(result['status'], 'RENDERED_ACT_PENDING')
        frame['stage'] = 'ACT'
        result = proof(self.publication, 'environment', self.evidence, [frame], self.loaded)
        self.assertEqual(result['status'], 'REQUEST_TO_COMMITTED_ACT_OBSERVED')
        self.assertEqual(result['committed_index'], 13)
        self.assertFalse(result['uptake_or_quality_claim'])


if __name__ == '__main__':
    unittest.main()
