from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_math_pipeline_l2_parent_node as broker


class ParentNodeTest(unittest.TestCase):
    def test_hash_manifest_changes_with_raw_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'EVENTS.jsonl').write_text('first')
            before = broker.manifest(path)
            (path / 'EVENTS.jsonl').write_text('second')
            self.assertNotEqual(before, broker.manifest(path))

    def test_remote_response_prevents_second_parent_call(self):
        root = Path('/remote/math')
        store = broker.Store(Path('/repo'), root)
        with patch.object(store, 'exists', return_value=True), patch.object(broker.strong, 'evaluate') as evaluate:
            broker.process_request(store, root / 'campaign_test/parent_queue/GUIDED_SLEEP_C1.request.json',
                Path('/tmp/buffer'), Path('/repo/receipts'), {}, broker.time.time() + 60)
            evaluate.assert_not_called()

    def test_existing_claim_never_retries_provider(self):
        root = Path('/remote/math')
        store = broker.Store(Path('/repo'), root)
        with patch.object(store, 'exists', return_value=False), patch.object(store, 'shell') as shell, patch.object(broker.strong, 'evaluate') as evaluate:
            shell.return_value.returncode = 1
            broker.process_request(store, root / 'campaign_test/parent_queue/GUIDED_SLEEP_C1.request.json',
                Path('/tmp/buffer'), Path('/repo/receipts'), {}, broker.time.time() + 60)
            evaluate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
