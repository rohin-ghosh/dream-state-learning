import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu.orch_rich_hot_node2_status import lane, observe


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

    def test_derived_slot_and_current_controller_not_obsolete_queue(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, successor, derived, control = [Path(temporary) / name for name in
                ('original', 'successor', 'derived', 'control')]
            for root in (original, successor, derived, control):
                root.mkdir()
            (successor / 'WATCH_STATUS.json').write_text('{"obsolete":true}')
            (successor / 'GUARD_FAILED.json').write_text('{"superseded":true}')
            (control / 'STATUS.json').write_text('{"launched_shards":[0,1]}')
            (derived / 'LAUNCH_0.json').write_text('{"identity":{"pid":123}}')
            with patch('gpu.orch_rich_hot_node2_status.identity_alive', return_value=True), patch(
                    'gpu.orch_rich_hot_node2_status.subprocess.check_output', return_value='inventory'):
                result = observe(original, successor, derived, control)
                self.assertEqual(result['slots']['0']['status'], 'ACTIVE')
                self.assertEqual(result['slots']['0']['processes'][0]['generation'], 'checkpoint_derived')
                self.assertEqual(result['queue'], {'launched_shards': [0, 1]})
                self.assertIsNone(result['successor_guard_failure'])
                self.assertEqual(result['reservations']['checkpoint_derived'], 0)
                (original / 'LAUNCH_0.json').write_text('{"identity":{"pid":124}}')
                self.assertEqual(observe(original, successor, derived, control)['slots']['0']['status'], 'OWNERSHIP_OVERLAP')
                (control / 'FAILED.json').write_text('{"message":"current failure"}')
                result = observe(original, successor, derived, control)
                self.assertEqual(result['successor_guard_failure']['summary'], {})
                self.assertEqual(result['successor_guard_failure']['native_path'], str(control / 'FAILED.json'))
                self.assertNotIn('current failure', json.dumps(result))

    def test_compact_status_excludes_embedded_raw_and_preserves_native_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            original, successor, control = [Path(temporary) / name for name in ('original', 'successor', 'control')]
            output = original / 'shard0'
            (output / 'evidence').mkdir(parents=True)
            successor.mkdir()
            control.mkdir()
            raw = 'RAW_SENTINEL_' * 10000
            capture = dict(task_id='task', source_task_id='source', family='code', stage='final_0', finished_unix=900,
                messages=[raw], response=dict(raw=raw, token_ids=[raw], terminal=True, truncated=False),
                outcome=dict(category='bounded_oracle_failed', correct=False, content_tokens=35,
                             expression=raw, verifier=dict(input=raw, error=raw)), error=dict(message=raw))
            path = output / 'task_final_0.json'
            path.write_text(json.dumps(capture))
            (output / 'TERMINAL.json').write_text(json.dumps(dict(status='COMPLETE', raw=raw)))
            (output / 'FAILED.json').write_text(json.dumps(dict(message=raw)))
            (output / 'evidence/B000-P05.json').write_text(json.dumps(dict(task=dict(family='route', payload=raw),
                evidence=dict(complete_routes=1, route_denominator=2, episodes=[raw]))))
            (control / 'STATUS.json').write_text(json.dumps(dict(launched_shards=[0], messages=raw)))
            (control / 'FAILED.json').write_text(json.dumps(dict(message=raw)))
            (control / 'TERMINAL.json').write_text(json.dumps(dict(status='FAILED', error=raw)))
            with patch('gpu.orch_rich_hot_node2_status.subprocess.check_output', return_value='inventory'):
                result = observe(original, successor, control=control)
            encoded = json.dumps(result)
            self.assertNotIn('RAW_SENTINEL', encoded)
            self.assertLess(len(encoded), 30000)
            first = result['roots']['original']['0']['first_by_family']['code']
            self.assertEqual(first['artifact'], dict(native_path=str(path), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            self.assertEqual(first['content_tokens'], 35)
            self.assertEqual(result['roots']['original']['0']['route_goals_correct'], 1)
            self.assertEqual(result['roots']['original']['0']['route_goals_denominator'], 2)


if __name__ == '__main__':
    unittest.main()
