import json
import unittest

from gpu import orch_math_pipeline_l2_parent_strong as strong


class StrongParentTest(unittest.TestCase):
    def envelope(self):
        plan = dict(guidance='Check independently.', order=['TRAIN1'], episode_guidance=dict(TRAIN1='Replay your actual history.'), rationale='All experience.')
        return dict(model=strong.STRONG, status='completed', usage=dict(output_tokens=10),
            output=[dict(type='message', content=[dict(type='output_text', text=json.dumps(plan))])])

    def test_actual_model_not_requested_label(self):
        strong.parse(self.envelope(), ['TRAIN1'])
        for model in ('gpt-5.6-sol', 'claude-haiku-4-5-20251001', None):
            with self.assertRaises(AssertionError):
                strong.parse(dict(self.envelope(), model=model), ['TRAIN1'])

    def test_no_incomplete_or_tool_response(self):
        for changes in (dict(status='incomplete'), dict(output=[dict(type='tool_call')]), dict(usage=None)):
            with self.assertRaises(AssertionError):
                strong.parse(dict(self.envelope(), **changes), ['TRAIN1'])


if __name__ == '__main__':
    unittest.main()
