import json
import unittest

from gpu import orch_route_parent_campaign_wire_resume as wire


class RouteWireResumeTests(unittest.TestCase):
    def envelope(self):
        return dict(type='result', num_turns=1, stop_reason='end_turn',
            modelUsage={'claude-sonnet-5[1m]': {'outputTokens': 100}},
            result='{"speak": true, "message": "Check the current ports.", "rationale": "Observed process error.}')

    def test_only_framing_inserted_no_words_or_calls(self):
        original = self.envelope()
        response, repair = wire.close_rationale_quote(original)
        self.assertEqual(response['rationale'], 'Observed process error.')
        self.assertEqual(response['message'], 'Check the current ports.')
        self.assertEqual(repair['provider_calls'], 0)
        self.assertEqual(repair['deleted_bytes'], 0)
        self.assertEqual(repair['inserted'], '"')

    def test_incomplete_or_other_corruption_not_repaired(self):
        for patch in (dict(stop_reason='max_tokens'), dict(result='{"speak":true'),
                      dict(result=json.dumps({'speak': True, 'message': 'fine', 'rationale': 'fine'})),
                      dict(result='{"speak":true,"message":"broken.}')):
            with self.assertRaises(ValueError):
                wire.close_rationale_quote(dict(self.envelope(), **patch))

    def test_absent_history_does_not_substitute(self):
        self.assertIsNone(wire.cached(None, 'EPISODE_01.json'))
        self.assertIsNone(wire.advice(None, 1, {}))


if __name__ == '__main__':
    unittest.main()
