import unittest

from r227_feedback_render_audit import inspect_messages


class FeedbackRenderAuditTests(unittest.TestCase):
    def test_aggregate_is_not_per_caption_feedback(self):
        content = 'Tool: {"schema":"R189_OUTCOME_ALLOCATION_V1","observation":{"evaluated":3,"quality_accepted":0}}'
        row = inspect_messages([dict(role='user', content=content)], [], [])['findings'][0]
        self.assertEqual(row['aggregate_observations'], [dict(evaluated=3, quality_accepted=0)])
        self.assertEqual(row['rank_fields'], [])
        self.assertEqual(row['accepted_boolean_fields'], [])
        self.assertFalse(row['new_pixel_marker'])

    def test_exact_rendered_result_has_source_binding(self):
        result = dict(submission_id='source1', rank=7, accepted=True,
            status='new_pixel', pixel_id='pixel-1')
        content = 'Tool: {"submission_id":"source1","rank":7,"accepted":true,"status":"new_pixel","pixel_id":"pixel-1"}'
        row = inspect_messages([dict(role='user', content=content)], [], [result])['findings'][0]
        self.assertEqual(row['source_bound_result_objects'], ['source1'])
        self.assertEqual(row['pixel_ids_present'], ['pixel-1'])

    def test_generic_rank_instruction_is_not_a_result(self):
        row = inspect_messages([dict(role='user', content='Aim for a good rank and acceptance.')],
            ['receipt123'], [])['findings'][0]
        self.assertEqual(row['rank_fields'], [])
        self.assertEqual(row['receipt_ids_present'], [])

    def test_wrong_submission_does_not_bind(self):
        result = dict(submission_id='source1', rank=7, accepted=True, status='new_pixel', pixel_id=None)
        row = inspect_messages([dict(role='assistant', content='{"submission_id":"other","rank":7}')],
            [], [result])['findings'][0]
        self.assertEqual(row['source_bound_result_objects'], [])
        self.assertEqual(row['role'], 'assistant')


if __name__ == '__main__':
    unittest.main()
