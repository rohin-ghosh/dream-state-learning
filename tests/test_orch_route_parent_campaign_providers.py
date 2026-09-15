import json
import unittest

from gpu import orch_route_parent_campaign_providers as providers


class ParentProviderTests(unittest.TestCase):
    def reply(self):
        return json.dumps(dict(speak=True, message='Read the available event before choosing.', rationale='Grounding'))

    def test_smaller_must_be_primary(self):
        envelope = dict(type='result', num_turns=1, result=self.reply(),
            modelUsage={providers.SMALLER: dict(outputTokens=50), 'claude-sonnet-5': dict(outputTokens=50)})
        with self.assertRaises(ValueError):
            providers.parse_smaller(envelope)
        del envelope['modelUsage']['claude-sonnet-5']
        self.assertEqual(providers.parse_smaller(envelope)[1], providers.SMALLER)

    def test_strong_requires_actual_identity_completed_usage_no_tools(self):
        envelope = dict(model=providers.STRONG, status='completed', usage=dict(output_tokens=80),
            output=[dict(type='message', content=[dict(type='output_text', text=self.reply())])])
        self.assertEqual(providers.parse_strong(envelope)[1], providers.STRONG)
        for key, value in (('model', 'guessed-alias'), ('status', 'incomplete'), ('usage', {}),
                           ('output', [dict(type='function_call')])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                providers.parse_strong(dict(envelope, **{key: value}))

    def test_message_bound_and_silence(self):
        for response in (dict(speak=False, message='nonempty', rationale='test'),
                         dict(speak=True, message='word ' * 91, rationale='test')):
            with self.assertRaises(ValueError):
                providers.response_schema(json.dumps(response))


if __name__ == '__main__':
    unittest.main()
