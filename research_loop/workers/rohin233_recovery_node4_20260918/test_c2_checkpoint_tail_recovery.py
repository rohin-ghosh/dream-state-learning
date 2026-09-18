"""Read-only receiving preflight must not compete for ownership or mutate records."""

from copy import deepcopy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

WORKER = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKER))
import checkpoint_tail_tests as fixtures
import c2_checkpoint_tail_recovery as recovery


class ReceivingPreflightTests(fixtures.CheckpointTailTests):
    def test_read_only_receiving_scan_while_exclusive_writer_remains_owner(self):
        selection = self.complete()
        before = {path.name:path.read_bytes() for path in self.journal.root.joinpath('records').iterdir()}
        receipt = recovery.readonly_scan(self.journal.root, selection)
        after = {path.name:path.read_bytes() for path in self.journal.root.joinpath('records').iterdir()}
        self.assertEqual(before, after)
        self.assertEqual(receipt['journal_writes'], 0)
        self.assertFalse(receipt['writer_lock_acquired'])
        self.assertEqual(receipt['complete_sha256'], selection['complete_sha256'])
        self.journal._ensure_open()

    def test_read_only_scan_refuses_different_complete(self):
        selection = self.complete()
        selection['complete_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'checkpoint_tail_exact_complete_pin'):
            recovery.readonly_scan(self.journal.root, selection)

    def test_exact_native_wrong_start_refused(self):
        actor = dict(start_ticks='not_current', uid=2524)
        with patch.object(recovery, 'identity', return_value=actor):
            with self.assertRaisesRegex(ValueError, 'exact_replaying_native_identity'):
                recovery.exact_actor(dict(source_root='/unchanged'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
