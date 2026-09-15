from contextlib import contextmanager, ExitStack
import io
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from gpu import orch_math_feedback_uptake_r118_broker as broker
from gpu import orch_math_feedback_uptake_r118_migrate as migration


class AstraHttpTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        config = self.root/'.codex/nvidia-astra.config.toml'
        config.parent.mkdir()
        config.write_text('model="'+broker.STRONG+'"\nmodel_provider="test"\nmodel_reasoning_effort="high"\n'
            '[model_providers.test]\nwire_api="responses"\nbase_url="https://inference-api.nvidia.com/v1"\n'
            'env_key="NVIDIA_API_KEY"\n')
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(broker.Path, 'home', return_value=self.root))
        self.stack.enter_context(patch.dict(broker.os.environ, {'NVIDIA_API_KEY': 'TEST_ONLY_NOT_A_CREDENTIAL'}))
        for name in ('validate_config', 'validate_launch'):
            self.stack.enter_context(patch.object(broker.shared, name))
        self.stack.enter_context(patch.object(broker.shared, 'validate_request', return_value={'task_id': 'TRAIN'}))
        self.stack.enter_context(patch.object(broker.shared, 'build_system', return_value=('same system', b'same prompt', {})))
        self.stack.enter_context(patch.object(broker.shared, 'adapt_plan', return_value=({'guidance': 'same guidance'}, {})))
        self.memory = self.stack.enter_context(patch.object(broker.shared.backend, 'available_memory', return_value=2**31))
        self.opener = Mock()
        response = dict(model=broker.STRONG, status='completed', usage={'output_tokens': 3},
            output=[{'type': 'message', 'content': [{'type': 'output_text', 'text': '{}'}]}])
        self.opener.open.return_value = io.BytesIO(json.dumps(response).encode())
        self.stack.enter_context(patch.object(broker.urllib.request, 'build_opener', return_value=self.opener))
        self.acquired, self.released = [], []
        @contextmanager
        def acquire(cutoff):
            self.acquired.append(cutoff)
            try:
                yield dict(slot=2, maximum_http_concurrency=4, waited_seconds=.1,
                    provider_time_reserved_seconds=20, provider_attempts=0, cli_lock_used=False)
            finally:
                self.released.append(True)
        self.slot = self.stack.enter_context(patch.object(broker.slots, 'acquire', side_effect=acquire))
        now = time.time()
        self.request = dict(id='genuine_future_train', payload_sha256='a'*64, lane_deadline_unix=now+120)
        self.deadline = now+1000
        self.config = dict(min_available_bytes=2**30, max_output_tokens=8192, family='math')

    def evaluate(self):
        return broker.astra_evaluate(self.request, self.root/'call', self.deadline,
            config=self.config, launch={}, prompt_root=self.root, principles_path=self.root/'principles')

    def test_uses_common_http_slots_one_attempt_and_same_cutoff(self):
        result = self.evaluate()
        self.assertEqual(result['status'], 'COMPLETE')
        self.slot.assert_called_once_with(self.request['lane_deadline_unix']-30)
        self.opener.open.assert_called_once()
        self.assertEqual(result['http_slot']['provider_attempts'], 1)
        self.assertFalse(result['http_slot']['cli_lock_used'])
        self.assertEqual(result['http_slot']['maximum_http_concurrency'], 4)
        self.assertEqual(self.released, [True])

    def test_low_memory_does_not_dispatch_and_releases_slot(self):
        self.memory.return_value = 1
        result = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(result['error']['stage'], 'memory')
        self.assertFalse(result['provider_dispatched'])
        self.opener.open.assert_not_called()
        self.assertEqual(self.released, [True])

    def test_slot_timeout_preserves_charge_without_provider_attempt(self):
        self.slot.side_effect = TimeoutError('http_slot_deadline_preserves_provider_margin')
        result = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(result['error']['stage'], 'http_slot')
        self.assertFalse(result['provider_dispatched'])
        self.opener.open.assert_not_called()

    def test_http_failure_has_one_attempt_no_retry(self):
        self.opener.open.side_effect = TimeoutError('provider timeout')
        result = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.assertTrue(result['provider_dispatched'])
        self.assertFalse(result['retry'])
        self.assertEqual(result['http_slot']['provider_attempts'], 1)
        self.opener.open.assert_called_once()
        self.assertEqual(self.released, [True])

    def test_actual_model_mismatch_never_complete(self):
        self.opener.open.return_value = io.BytesIO(json.dumps(dict(model='other', status='completed', usage={'tokens': 1})).encode())
        result = self.evaluate()
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(result['error']['stage'], 'verify_response')

    def test_memory_receipt_distinguishes_http_from_cli_lock(self):
        self.evaluate()
        receipt = json.loads((self.root/'call/MEMORY.json').read_text())
        self.assertEqual(receipt['floor_bytes'], 2**30)
        self.assertFalse(receipt['cli_lock_used'])
        self.assertFalse(receipt['serialized_lock'])
        self.assertTrue(receipt['bounded_http_slot'])
        self.assertNotIn('LOCK_PATH', Path(broker.__file__).read_text())


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.claim = self.root/'parent_claude/call.claim'
        self.claim.mkdir(parents=True)
        (self.claim.parent/'CONFIG.json').write_text('{}')
        (self.claim/'RESERVATION.json').write_text('{}')
        self.archive = self.root/'parent_transcripts/call'
        self.archive.mkdir(parents=True)
        (self.archive/'RESULT.json').write_text('{}')
        self.response = self.root/'parent_queue/call.response.json'
        self.response.parent.mkdir()
        self.response.write_text(json.dumps(dict(status='MISSING', transcript_receipt=dict(remote_root=str(self.archive),
            files={'RESULT.json': hashlib.sha256(b'{}').hexdigest()}))))
        (self.claim/'PUBLISHED.json').write_text(json.dumps(dict(response_sha256=hashlib.sha256(self.response.read_bytes()).hexdigest())))

    def test_published_missing_is_safe_boundary_not_quality_selection(self):
        result = migration.snapshot(self.root)
        self.assertTrue(result['safe'])
        self.assertEqual(result['statuses'], {'MISSING': 1})

    def test_inflight_claim_blocks_migration(self):
        (self.claim.parent/'pending.claim').mkdir()
        result = migration.snapshot(self.root)
        self.assertFalse(result['safe'])
        self.assertEqual(result['pending'], ['pending'])

    def test_changed_archive_blocks_migration(self):
        (self.archive/'RESULT.json').write_text('changed')
        self.assertFalse(migration.snapshot(self.root)['safe'])

    def test_partial_response_blocks_migration(self):
        self.response.with_suffix('.json.partial').write_text('pending')
        self.assertFalse(migration.snapshot(self.root)['safe'])

    def test_other_runtime_rejected_before_pid_or_signal(self):
        with patch.object(migration.os, 'pidfd_open') as opened:
            with self.assertRaisesRegex(ValueError, 'only_original_owned_A2_runtime'):
                migration.validate_target(self.root)
        opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()
