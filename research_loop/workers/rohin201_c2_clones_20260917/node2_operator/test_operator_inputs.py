import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from parent_math_d import FOLLOWUPS, due_messages
from gpu import orch_r127_pilot_console as console


class InputTests(unittest.TestCase):
    def test_only_first_three_guided_cycles(self):
        self.assertEqual(set(FOLLOWUPS), {52, 53})
        self.assertEqual(due_messages(52, {}), [52])
        self.assertEqual(due_messages(53, {}), [53])
        self.assertEqual(due_messages(52, {52: True}), [])
        for cycle in (51, 54, 55, 56, 57, 58):
            self.assertEqual(due_messages(cycle, {}), [])

    def test_exact_attribution_order_and_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'stream/inbox').mkdir(parents=True)
            text = 'exact synthetic first input\n'
            with console._open_stream_directory(root, 'inbox') as (directory, path):
                for identifier, speaker, content in [('r202_000_rohin_part_one', 'Rohin', text),
                                                     ('r202_001_astra_math_d_introduction', 'Astra', 'synthetic introduction')]:
                    document = dict(schema=console.SCHEMA, id=identifier, text=content, split='TRAIN',
                        actor='parent', speaker=speaker, source_receipt=None)
                    receipt = console._publish(directory, path, document)
                    self.assertEqual(hashlib.sha256(Path(receipt['path']).read_bytes()).hexdigest(), receipt['sha256'])
            messages = [json.loads(path.read_bytes()) for path in sorted((root / 'stream/inbox').glob('*.json'))]
            self.assertEqual([message['speaker'] for message in messages], ['Rohin', 'Astra'])
            self.assertEqual(messages[0]['text'], text)
            self.assertTrue(all(message['actor'] == 'parent' and message['source_receipt'] is None for message in messages))


if __name__ == '__main__':
    unittest.main()
