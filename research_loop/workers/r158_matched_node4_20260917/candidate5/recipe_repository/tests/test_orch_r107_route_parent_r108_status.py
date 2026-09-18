import json
from pathlib import Path
import tempfile
import unittest

from gpu.orch_r107_route_parent_r108_status import collect


class CompactStatusTests(unittest.TestCase):
    def test_no_prompt_or_response_text_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            native = root / 'campaign_route_parent_2/native'
            native.mkdir(parents=True)
            response = dict(raw='PRIVATE_CHILD_TEXT', messages=['PRIVATE_PROMPT'], token_ids=[1, 2],
                            terminal=True, input_truncated=False, full_prompt_prefix_verified=True)
            (native / 'CALL_0001.json').write_text(json.dumps(dict(response=response,
                purpose='train_episode', started_unix=1, finished_unix=2)))
            result = collect(root, [2])
            self.assertNotIn('PRIVATE', json.dumps(result))
            self.assertEqual(result['lanes'][0]['completed_native_calls'], 1)
            self.assertIsNone(result['lanes'][0]['raw_throughput_window']['qualified_rate'])

    def test_pending_intent_not_counted_as_completed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            native = root / 'campaign_route_parent_2/native'
            native.mkdir(parents=True)
            (native / 'CALL_0001.json').write_text('{"started_unix":1}')
            result = collect(root, [2])['lanes'][0]
            self.assertEqual(result['recorded_call_intents'], 1)
            self.assertEqual(result['completed_native_calls'], 0)
            self.assertIsNone(result['first_native'])


if __name__ == '__main__':
    unittest.main()
