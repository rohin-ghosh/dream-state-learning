import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_rich_hot_node1_observe as observer


class MetadataOnlyObserverTests(unittest.TestCase):
    def test_native_reduction_never_returns_capture_contents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shard = root / 'shard3'
            shard.mkdir()
            secret = 'RAW_CAPTURE_MUST_STAY_ON_GENERATION_NODE'
            call = dict(started_unix=1, finished_unix=2, phase_version='TEST',
                        response=dict(raw=secret, token_ids=[1, 2], terminal=True),
                        messages=[dict(content=secret)], episode_receipt='EPISODE_0_0.json')
            capture = shard / 'CALL_0001.json'
            capture.write_text(json.dumps(call))
            (shard / 'EPISODE_0_0.json').write_text(json.dumps(dict(correct=True, captures=[call])))
            (shard / 'PROGRESS.json').write_text(json.dumps(dict(calls=1, raw=secret, messages=[secret])))
            (root / 'CALL_RESERVATIONS.jsonl').write_text(json.dumps(dict(global_call=1, messages=[secret])) + '\n')
            (root / 'PROVENANCE.json').write_text(json.dumps(dict(content=secret)))
            original_bytes = capture.read_bytes()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(observer.COLLECT, dict(ROOT=str(root), INDICES=[3], ORIGINAL=None, LEDGER=str(root)))
            payload = output.getvalue()
            result = json.loads(payload)
            observer.require_metadata_only(result)
            self.assertNotIn(secret, payload)
            self.assertEqual(result['summary'][0]['calls'], 1)
            self.assertEqual(result['summary'][0]['progress'], {'calls': 1})
            self.assertEqual(result['remote_files']['shard3/CALL_0001.json']['sha256'],
                             hashlib.sha256(original_bytes).hexdigest())
            self.assertEqual(capture.read_bytes(), original_bytes)

    def test_vm_snapshot_writes_only_one_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'status'
            result = dict(summary=[], remote_files={'shard0/CALL_00001.json': dict(sha256='abc', bytes=12)})
            with patch.object(observer, 'floor', return_value=dict(active_generators=16)):
                with patch.object(observer, 'remote', return_value=json.dumps(result)):
                    with contextlib.redirect_stdout(io.StringIO()):
                        observer.snapshot(output)
            self.assertEqual([path.name for path in output.iterdir()], ['MANIFEST.json'])
            self.assertLess((output / 'MANIFEST.json').stat().st_size, observer.MAX_MANIFEST_BYTES)

    def test_old_or_nested_raw_payloads_are_rejected(self):
        for value in ({'files': {'CALL.json': 'raw'}}, {'summary': [{'response': {'raw': 'raw'}}]}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'raw_payload_forbidden'):
                observer.require_metadata_only(value)

    def test_oversized_manifest_is_not_written(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'status'
            with patch.object(observer, 'floor', return_value={}):
                with patch.object(observer, 'remote', return_value='{}'):
                    with patch.object(observer, 'MAX_MANIFEST_BYTES', 1):
                        with self.assertRaisesRegex(ValueError, 'size_limit'):
                            observer.snapshot(output)
            self.assertEqual(list(output.iterdir()), [])
