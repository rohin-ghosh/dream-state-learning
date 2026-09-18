import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from organism_v6.orch_r124_train_history import TrainEvent
from organism_v6.orch_r125_plain_context import event_message
import seed_notice


class SeedNoticeTests(unittest.TestCase):
    def test_exact_context_survives_renderer_as_supplied_material(self):
        path = Path(__file__).resolve().parents[1] / 'rohin221_continuous_caption_20260918/R230_SEED_CONTEXT_v1.txt'
        text = path.read_text()
        event = TrainEvent(event_id='environment:seeds', actor='environment', text='Tool: ' + text,
            split='TRAIN', phase='feedback', episode_id='continual_stream', source_id='/tmp/seed.json',
            source_sha256='c' * 64, origin='TRAIN_COLLECTION')
        rendered = event_message(event)
        self.assertEqual(rendered['role'], 'user')
        self.assertIn(text, rendered['content'])
        self.assertIn('not your attempts', rendered['content'])

    def test_tampering_is_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = root / 'packet.json'
            context = root / 'context.txt'
            context.write_text('modified')
            packet.write_text(json.dumps(dict(child_context=dict(sha256=hashlib.sha256(b'original').hexdigest()))))
            with patch.object(seed_notice, '_inbox') as publish:
                with self.assertRaisesRegex(ValueError, 'exact_seed_context'):
                    seed_notice.publish(root / 'life', root / 'output', packet, context)
                publish.assert_not_called()
                self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
