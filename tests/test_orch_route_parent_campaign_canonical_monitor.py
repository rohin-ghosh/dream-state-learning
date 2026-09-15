import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_route_parent_campaign_canonical_monitor as monitor


class CanonicalMonitorTests(unittest.TestCase):
    def test_raw_held_prompt_and_response_never_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'NO_LORA/cycle0/readout'
            folder.mkdir(parents=True)
            (folder / 'REQUEST.json').write_text(json.dumps(dict(started_unix=10, input_adapter={'kind': 'NO_ADAPTER'})))
            (folder / 'CALL_0000.json').write_text(json.dumps(dict(started_unix=11, finished_unix=12,
                messages=[{'content': 'HELD_PRIVATE_PROMPT'}], response=dict(raw='HELD_PRIVATE_ANSWER',
                prompt_tokens=7, token_ids=[1, 2]))))
            result = monitor.snapshot(root)
            serialized = json.dumps(result)
            self.assertNotIn('HELD_PRIVATE', serialized)
            self.assertEqual(result['phases'][0]['first_call']['output_tokens'], 2)
            self.assertEqual(result['phases'][0]['status'], 'RUNNING_CENSORED')
            self.assertFalse(result['held_text_exported'])

    def test_fresh_parent_free_lineage_verified_before_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'GUIDED/cycle1/readout'
            folder.mkdir(parents=True)
            sleep = root / 'GUIDED/cycle1/sleep'
            sleep.mkdir()
            child = {'state_sha256': 'child'}
            (folder / 'REQUEST.json').write_text(json.dumps(dict(started_unix=10, input_adapter=child)))
            value = dict(finished_unix=12, input_adapter=child, process=['boot', 2, 2], parent_free=True)
            (folder / 'COMPLETE.json').write_text(json.dumps(value))
            (sleep / 'COMPLETE.json').write_text(json.dumps(dict(output_adapter=child, process=['boot', 1, 1])))
            self.assertTrue(monitor.snapshot(root)['phases'][0]['fresh_parent_free_saved_child_verified'])
            (folder / 'COMPLETE.json').write_text(json.dumps(dict(value, parent_free=False)))
            with self.assertRaises(AssertionError):
                monitor.snapshot(root)
