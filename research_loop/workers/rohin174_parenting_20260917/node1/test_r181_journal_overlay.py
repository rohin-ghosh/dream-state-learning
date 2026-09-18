import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import r181_journal_operator as overlay


class JournalOverlayTests(unittest.TestCase):
    def test_known_R181_native_is_preserved_byte_for_byte(self):
        source = 'already prepared native\n'
        digest = hashlib.sha256(source.encode()).hexdigest()
        with patch.object(overlay, 'READY_NATIVE', {digest}):
            self.assertEqual(overlay.patched_native(source, 'canonical'), source)

    def test_original_handoff_not_overridden(self):
        self.assertEqual(overlay.operator.handoff.__module__, 'r181_operator')
        self.assertEqual(overlay.operator.pause_watchdog.__module__, 'r181_operator')
        self.assertEqual(overlay.operator.original_binding.__module__, 'r181_operator')

    def test_shared_journal_exact_pin(self):
        repository = Path(__file__).resolve().parents[4]
        self.assertEqual(overlay.operator.sha(repository / overlay.JOURNAL), overlay.JOURNAL_SHA)

    def test_unrelated_python_change_rejected(self):
        before = {overlay.JOURNAL: {'sha256': 'old'}, overlay.operator.NATIVE: {'sha256': 'old'},
                  'gpu/guard.py': {'sha256': 'preserve'}}
        after = {overlay.JOURNAL: {'sha256': overlay.JOURNAL_SHA},
                 overlay.operator.NATIVE: {'sha256': next(iter(overlay.READY_NATIVE))},
                 'gpu/guard.py': {'sha256': 'changed'}}
        with self.assertRaisesRegex(ValueError, 'unchanged_other_python'):
            overlay.verify_source_copy(None, None, before, after)


if __name__ == '__main__':
    unittest.main()
