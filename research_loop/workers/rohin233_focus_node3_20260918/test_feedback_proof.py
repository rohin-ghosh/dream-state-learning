import unittest

from feedback_proof import render_after_inbox


class FeedbackProofTests(unittest.TestCase):
    def inbox(self, index=10, source='bound'):
        return dict(index=index, sha256='inbox-record', kind='INBOX',
            document=dict(message=dict(id='new-message'), source_sha256=source))

    def request(self, index, started=21, masked=True):
        return dict(index=index, sha256='request-record', kind='REQUEST', document=dict(
            started_unix=started, messages=[dict(role='user', content='Tool: No judgment.')],
            render_receipt=dict(all_history_tokens_masked=masked)))

    def test_identical_old_text_cannot_prove_new_publication_render(self):
        item = dict(inbox_id='new-message', inbox_sha256='bound', published_unix=20)
        result = render_after_inbox([self.request(8), self.inbox(), self.request(12)], item, 'No judgment.', 5)
        self.assertEqual(result['REQUEST']['index'], 12)
        self.assertTrue(result['identical_text_unique_attribution_not_claimed'])

    def test_matching_text_without_this_inbox_is_not_delivery(self):
        item = dict(inbox_id='new-message', inbox_sha256='bound', published_unix=20)
        self.assertIsNone(render_after_inbox([self.request(12)], item, 'No judgment.', 5)['REQUEST'])

    def test_publication_time_and_latest_load_both_bound_delivery(self):
        item = dict(inbox_id='new-message', inbox_sha256='bound', published_unix=20)
        self.assertIsNone(render_after_inbox([self.inbox(), self.request(12, started=19)],
            item, 'No judgment.', 5)['REQUEST'])
        self.assertIsNone(render_after_inbox([self.inbox(), self.request(12)],
            item, 'No judgment.', 11)['REQUEST'])

    def test_modified_inbox_and_unmasked_external_input_rejected(self):
        item = dict(inbox_id='new-message', inbox_sha256='bound', published_unix=20)
        with self.assertRaisesRegex(ValueError, 'exact_Tool_inbox_source'):
            render_after_inbox([self.inbox(source='changed')], item, 'No judgment.', 5)
        with self.assertRaisesRegex(ValueError, 'Tool_tokens_must_remain_masked'):
            render_after_inbox([self.inbox(), self.request(12, masked=False)], item, 'No judgment.', 5)


if __name__ == '__main__':
    unittest.main()
