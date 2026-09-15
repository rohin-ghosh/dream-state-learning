import unittest

from gpu.orch_continual_batch_handoff import wrap_row


class HandoffTests(unittest.TestCase):
    def test_unsampled_wrapper_keeps_unknown_axes(self):
        row = dict(question_sha256='question', provenance=dict(raw_call_path='raw/call', raw_call_sha256='raw'),
                   target_sha256='target', original_semantic_status='UNREVIEWED', generated_tokens=90, review=None)
        wrapped = wrap_row(row, 'manifest')
        self.assertIs(wrapped['row'], row)
        self.assertEqual(wrapped['eligibility']['individual_semantic_status'], 'UNREVIEWED')
        self.assertTrue(all(value is None for value in wrapped['eligibility']['content_axes'].values()))
        self.assertIsNone(wrapped['gold_review'])
        self.assertFalse(wrapped['eligibility']['length_is_quality_gate'])


if __name__ == '__main__':
    unittest.main()
