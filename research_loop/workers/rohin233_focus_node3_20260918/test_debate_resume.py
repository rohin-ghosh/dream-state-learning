import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import debate_resume
from retirement import sha


class DebateResumeTests(unittest.TestCase):
    def test_pending_authenticates_exact_existing_parent_no_republish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = SimpleNamespace(MEMBERS=('r213_math_a',), prompt=lambda *arguments: 'Check all cases.')
            pending = root / 'exchange_3'
            parent = pending / 'parents'
            parent.mkdir(parents=True)
            inbox = root / 'r213_math_a/raw/stream/inbox/actual-id.json'
            inbox.parent.mkdir(parents=True)
            inbox.write_text(json.dumps(dict(id='actual-id', speaker='Astra', text='Check all cases.')))
            (parent / 'r213_math_a.intent.json').write_text(json.dumps(dict(life='r213_math_a', text='Check all cases.')))
            publication = dict(id='actual-id', path=str(inbox), sha256=sha(inbox), text='Check all cases.')
            (parent / 'r213_math_a.json').write_text(json.dumps(publication))
            receipts = debate_resume.pending_parents(module, root, pending, 5, 3, 3)
            self.assertEqual(receipts['r213_math_a']['id'], 'actual-id')
            inbox.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'identity_and_source'):
                debate_resume.pending_parents(module, root, pending, 5, 3, 3)

    def test_uncertain_or_later_exchange_artifacts_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'RESULT.json').write_text('{}')
            module = SimpleNamespace(MEMBERS=('r213_math_a',))
            with self.assertRaisesRegex(ValueError, 'complete_previously_published_parent_pairs'):
                debate_resume.pending_parents(module, root, root, 5, 3, 3)


if __name__ == '__main__':
    unittest.main()
