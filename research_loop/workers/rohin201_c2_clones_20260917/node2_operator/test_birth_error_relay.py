import unittest

from birth_error_relay import eligible, message


class ErrorRelayTests(unittest.TestCase):
    def setUp(self):
        self.receipt = dict(origin=dict(actor='child', split='TRAIN', record_index=5106),
            error_type='ValueError', reason='visible_snapshot_path_only')

    def test_only_new_actual_child_rejections(self):
        self.assertTrue(eligible(self.receipt, set()))
        self.assertFalse(eligible(self.receipt, {5106}))
        self.receipt['origin']['record_index'] = 5104
        self.assertFalse(eligible(self.receipt, set()))

    def test_external_or_nontrain_never_relayed(self):
        self.receipt['origin']['actor'] = 'parent'
        self.assertFalse(eligible(self.receipt, set()))
        self.receipt['origin'].update(actor='child', split='HELD')
        self.assertFalse(eligible(self.receipt, set()))

    def test_visible_error_is_not_success_or_scaffolding(self):
        text = message(self.receipt, 'a' * 64)
        self.assertIn('REPO_ACTION_REJECTED', text)
        self.assertIn('visible_snapshot_path_only', text)
        self.assertNotIn('source_sha256', text)
        self.assertNotIn('receipt_sha256', text)


if __name__ == '__main__':
    unittest.main()
