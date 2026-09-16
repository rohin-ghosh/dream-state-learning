import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r131_saved_boundary_handoff as handoff


class SavedBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root/'stream/records').mkdir(parents=True)

    def publish(self, kind='SLEEP_COMPLETE', **changes):
        state = dict(pending=None, sleep_frontier=1, rows=[{'source': 'actual'}],
                     sleep_receipts=[{'status': 'COMPLETE'}], deadline_unix=500)
        state.update(changes)
        envelope = dict(state=state, sha256=handoff.digest(state))
        record = dict(kind=kind, document=dict(status='COMPLETE', cycle=1, resume_state=envelope))
        record['sha256'] = handoff.digest(record)
        path = self.root/'stream/records/00000000000000000000.json'
        path.write_text(json.dumps(record))
        return path, record

    def test_completed_sleep_returns_exact_saved_digest(self):
        unused, record = self.publish()
        result = handoff.sleep_boundary(self.root)
        self.assertEqual(result['state_sha256'], record['document']['resume_state']['sha256'])
        self.assertEqual(result['state'], record['document']['resume_state']['state'])

    def test_nonboundary_never_requests_a_pause(self):
        for kind in ('REQUEST', 'RESPONSE', 'UPDATE', 'COMPACTION', 'SLEEP_REQUEST', 'INBOX'):
            with self.subTest(kind=kind):
                self.publish(kind=kind)
                self.assertIsNone(handoff.sleep_boundary(self.root))

    def test_pending_and_unslept_work_rejected(self):
        for changes in ({'pending': 'request'}, {'sleep_frontier': 0}, {'sleep_receipts': []},
                        {'sleep_receipts': [{'status': 'FAILED'}]}):
            with self.subTest(changes=changes):
                self.publish(**changes)
                with self.assertRaisesRegex(ValueError, 'completed_saved_boundary_only'):
                    handoff.sleep_boundary(self.root)

    def test_tampered_record_rejected(self):
        path, record = self.publish()
        record['document']['cycle'] = 9
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'boundary_record_hash'):
            handoff.sleep_boundary(self.root)

    def test_unpublished_staging_ignored(self):
        self.publish()
        (self.root/'stream/records/99999999999999999999.intent.json').write_text('not a record')
        self.assertEqual(handoff.sleep_boundary(self.root)['cycle'], 1)

    def test_empty_journal_rejected(self):
        with self.assertRaisesRegex(ValueError, 'published_journal_required'):
            handoff.sleep_boundary(self.root)

    def test_process_identity_matches_current_group(self):
        identity = handoff.process_identity(os.getpid())
        self.assertEqual(identity['group'], os.getpgid(os.getpid()))
        self.assertTrue(identity['start_ticks'].isdigit())

    def test_receipts_never_overwrite(self):
        path = self.root/'receipt.json'
        handoff.write(path, {'status': 'original'})
        with self.assertRaises(FileExistsError):
            handoff.write(path, {'status': 'replacement'})
        self.assertEqual(handoff.read(path), {'status': 'original'})

    def test_handoff_does_not_pause_before_readout_spawn(self):
        self.publish()
        self.assertFalse(handoff.readout_started(self.root, 1, 2, 42))

    def test_readout_must_be_in_independent_running_group(self):
        output = self.root/'readouts/sleep_000001_r2'
        output.mkdir(parents=True)
        (output/'REQUEST.json').write_text(json.dumps({'pid': 43}))
        for group, state, expected in ((42, 'R', False), (43, 'T', False),
                                       (43, 'Z', False), (43, 'R', True)):
            with self.subTest(group=group, state=state):
                with patch.object(handoff, 'process_identity', return_value={'group': group, 'state': state}):
                    self.assertEqual(handoff.readout_started(self.root, 1, 2, 42), expected)
        with patch.object(handoff, 'process_identity', side_effect=FileNotFoundError):
            self.assertFalse(handoff.readout_started(self.root, 1, 2, 42))

    def test_completed_readout_does_not_require_live_process(self):
        output = self.root/'readouts/sleep_000001_r2'
        output.mkdir(parents=True)
        (output/'REQUEST.json').write_text(json.dumps({'pid': 43}))
        (output/'COMPLETE.json').write_text('{}')
        self.assertTrue(handoff.readout_started(self.root, 1, 2, 42))


if __name__ == '__main__':
    unittest.main()
