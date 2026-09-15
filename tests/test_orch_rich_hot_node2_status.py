import json
from pathlib import Path
import tempfile
import unittest

from gpu.orch_rich_hot_node2_status import lane


class StatusTests(unittest.TestCase):
    def test_rates_count_completed_responses_and_errors_not_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'shard0'
            output.mkdir()
            (output / 'LOADED.json').write_text('{"status":"LOADED"}')
            for index, finished in enumerate((300, 500, 900, 1100)):
                row = dict(task_id=str(index), stage='final_0', family='code', finished_unix=finished,
                           response={}, outcome=dict(category='registered_correct', content_tokens=80))
                (output / f'B{index}.json').write_text(json.dumps(row))
            (output / 'error.json').write_text(json.dumps(dict(task_id='error', stage='final_0', family='code',
                finished_unix=950, error=dict(message='failure'))))
            result = lane(root, 0, now=1000)
            self.assertEqual(result['completed_captures'], 5)
            self.assertEqual(result['recent_completed'], 3)
            self.assertEqual(result['recent_captures_per_hour'], 18)
            self.assertEqual(result['recent_content_tokens'], 160)
            self.assertEqual(result['categories']['execution_error'], 1)
            self.assertFalse(result['identity_alive'])


if __name__ == '__main__':
    unittest.main()
