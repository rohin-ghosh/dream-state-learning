import unittest

from p3_receipts import correlate


class ReceiptTests(unittest.TestCase):
    def test_publication_is_not_delivery(self):
        self.assertEqual(correlate({'id': 'actual'}, {'records': []}, [])['status'],
                         'PUBLISHED_RENDER_NOT_YET_IN_AUDIT')

    def test_first_actual_act_after_render_not_prior_response(self):
        request = dict(kind='REQUEST', index=20, sha256='request', time_unix=10,
            masked=True, external=[dict(event_id='parent:inbox:actual')])
        before = dict(stage='ACT', request=dict(index=18), response={})
        after = dict(stage='ACT', request=dict(index=22),
            response=dict(index=23, sha256='response', time_unix=11, text='An actual artifact'))
        result = correlate({'id': 'actual'}, {'records': [request]}, [before, after])
        self.assertEqual(result['act_index'], 23)
        self.assertEqual(result['request_index'], 20)
        self.assertEqual(result['success_claim'], 'NONE_ARTIFACT_REQUIRES_REVIEW')

    def test_wrong_inbox_never_counts_as_render(self):
        request = dict(kind='REQUEST', external=[dict(event_id='parent:inbox:other')])
        self.assertEqual(correlate({'id': 'actual'}, {'records': [request]}, [])['status'],
                         'PUBLISHED_RENDER_NOT_YET_IN_AUDIT')


if __name__ == '__main__':
    unittest.main()
