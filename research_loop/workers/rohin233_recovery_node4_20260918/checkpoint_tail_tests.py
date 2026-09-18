"""Synthetic receiving regressions; no production journal or native signals."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

arguments, remaining = argparse.ArgumentParser().parse_known_args()
worker = Path(__file__).resolve().parent
source = Path(os.environ.get('CHECKPOINT_TAIL_SOURCE', worker / 'private/port_C2'))
sys.path.insert(0, str(source))
spec = importlib.util.spec_from_file_location('journal_fixture', source / 'tests/test_orch_r125_stream_journal.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
from gpu.orch_r125_stream_journal import StreamJournal
from gpu.checkpoint_tail_runtime import POLICY


class CheckpointTailTests(unittest.TestCase):
    setUp = fixture.StreamJournalTests.setUp
    step = fixture.StreamJournalTests.step
    receipt = fixture.StreamJournalTests.receipt
    parent = fixture.StreamJournalTests.parent
    record_path = fixture.StreamJournalTests.record_path

    def complete(self):
        self.parent()
        self.step(incoming=self.journal.read_inbox())
        self.step()
        self.stream.commit_sleep(self.receipt(), self.journal.record)
        index = self.journal._state['index'] - 1
        return dict(policy=POLICY, root=str(self.root), journal_id=self.journal._manifest['journal_id'],
            complete_index=index, complete_sha256=self.journal._state['previous'], life_id='synthetic',
            max_tail_records=64, max_tail_bytes=16 * 1024 * 1024, sidecars=[], persist_complete_anchors=True)

    def reopen(self, selection):
        self.journal.close()
        self.journal = StreamJournal(self.root, checkpoint_tail=selection)
        self.addCleanup(self.journal.close)
        return self.journal

    def test_anchor_tail_matches_full_replay_and_preserves_all_bytes(self):
        selection = self.complete()
        self.journal.record('R184_LEARN_COMPLETE', dict(cycle=1))
        before = {path.name: path.read_bytes() for path in (self.root / 'records').iterdir()}
        expected = self.journal._state
        self.journal.close()
        with StreamJournal(self.root) as full:
            self.assertEqual(full._state, expected)
        recovered = self.reopen(selection)
        self.assertEqual(recovered._state, expected)
        self.assertEqual(recovered.latest_checkpoint()['document'], self.stream.checkpoint())
        self.assertEqual(len(recovered.read_inbox()), 1)
        self.assertEqual(before, {path.name: path.read_bytes() for path in (self.root / 'records').iterdir()})

    def test_no_historical_request_response_json_decode(self):
        selection = self.complete()
        original = StreamJournal._read_json
        decoded = []
        def observe(directory, name):
            decoded.append(name)
            return original(directory, name)
        with patch.object(StreamJournal, '_read_json', side_effect=observe):
            recovered = self.reopen(selection)
        permitted = set(recovered.checkpoint_tail_receipt['decoded_prefix_indices'])
        for name in decoded:
            if name[:20].isdigit() and not name.endswith('.intent.json'):
                self.assertIn(int(name[:20]), permitted)
        self.assertLess(len(permitted), selection['complete_index'])

    def test_pending_request_is_not_cleared_by_metadata(self):
        selection = self.complete()
        def fail(*args, **kwargs):
            raise RuntimeError('synthetic generation interruption')
        with self.assertRaises(RuntimeError):
            self.step(generate_call=fail)
        self.journal.record('NOTE', dict(pending=False))
        expected = self.journal._state
        recovered = self.reopen(selection)
        self.assertEqual(recovered._state, expected)
        self.assertIsNotNone(recovered._state['request'])
        self.assertIsNotNone(recovered.latest_checkpoint()['document']['state']['pending'])

    def test_pending_response_survives_without_fabricated_commit(self):
        selection = self.complete()
        def record(kind, document):
            if kind == 'COMMITTED':
                raise RuntimeError('synthetic precommit interruption')
            return self.journal.record(kind, document)
        with self.assertRaises(RuntimeError):
            self.step(record=record)
        expected = self.journal._state
        recovered = self.reopen(selection)
        self.assertEqual(recovered._state, expected)
        self.assertIsNotNone(recovered._state['response'])

    def test_pending_sleep_is_preserved(self):
        selection = self.complete()
        self.step()
        self.stream.pending = 'sleep:' + fixture.digest(
            [row['source_sha256'] for row in self.stream.pending_rows()])
        self.journal.record('SLEEP_REQUEST', dict(resume_state=self.stream.checkpoint()))
        expected = self.journal._state
        recovered = self.reopen(selection)
        self.assertEqual(recovered._state, expected)
        self.assertIsNotNone(recovered._state['sleep_request'])

    def test_explicit_audit_replays_every_transition_and_restores_selector(self):
        selection = self.complete()
        self.journal.record('NOTE', dict(tail=True))
        recovered = self.reopen(selection)
        active = recovered._checkpoint_tail
        expected = recovered._state
        with patch('gpu.checkpoint_tail_runtime.scan') as fast_scan, \
                patch.object(recovered, '_advance', wraps=recovered._advance) as advance:
            receipt = recovered.audit()
        fast_scan.assert_not_called()
        self.assertEqual(advance.call_count, expected['index'])
        self.assertTrue(any(call.args[1] == 'REQUEST' for call in advance.call_args_list))
        self.assertEqual(receipt, dict(record_count=expected['index'], head_sha256=expected['previous']))
        self.assertEqual(recovered._state, expected)
        self.assertIs(recovered._checkpoint_tail, active)

    def test_explicit_audit_failure_restores_selector_and_retains_prior_state(self):
        selection = self.complete()
        recovered = self.reopen(selection)
        active = recovered._checkpoint_tail
        expected = recovered._state
        original = recovered._advance
        def reject_historical_request(state, kind, document):
            if kind == 'REQUEST':
                raise ValueError('synthetic_historical_transition_failure')
            return original(state, kind, document)
        with patch('gpu.checkpoint_tail_runtime.scan') as fast_scan, \
                patch.object(recovered, '_advance', side_effect=reject_historical_request), \
                self.assertRaisesRegex(ValueError, 'historical_transition_failure'):
            recovered.audit()
        fast_scan.assert_not_called()
        self.assertIs(recovered._checkpoint_tail, active)
        self.assertIs(recovered._state, expected)

    def test_corrupt_retained_prefix_rejected(self):
        selection = self.complete()
        path = self.record_path(1)
        path.write_bytes(path.read_bytes().replace(b'System.', b'System!', 1))
        with self.assertRaisesRegex(ValueError, 'integrity'):
            self.reopen(selection)

    def test_wrong_anchor_rejected(self):
        selection = self.complete()
        selection['complete_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_complete_pin'):
            self.reopen(selection)

    def test_intent_corruption_rejected(self):
        selection = self.complete()
        path = self.root / 'records' / '00000000000000000000.intent.json'
        intent = json.loads(path.read_text())
        intent['record_sha256'] = '0' * 64
        path.write_text(json.dumps(intent))
        with self.assertRaisesRegex(ValueError, 'intent_binding'):
            self.reopen(selection)

    def test_missing_tail_intent_rejected(self):
        selection = self.complete()
        reference = self.journal.record('NOTE', {})
        (self.root / 'records' / f'{reference["index"]:020d}.intent.json').unlink()
        with self.assertRaisesRegex(ValueError, 'incomplete_journal_tail'):
            self.reopen(selection)

    def test_prefix_symlink_rejected(self):
        selection = self.complete()
        path = self.record_path(0)
        saved = self.root / 'saved.json'
        path.rename(saved)
        path.symlink_to(saved)
        with self.assertRaises(OSError):
            self.reopen(selection)

    def test_tail_bounds_reject_without_modifying_state(self):
        selection = self.complete()
        self.journal.record('NOTE', {})
        self.journal.record('NOTE', {})
        selection['max_tail_records'] = 1
        with self.assertRaisesRegex(ValueError, 'record_bound'):
            self.reopen(selection)
        selection['max_tail_records'] = 4
        selection['max_tail_bytes'] = 1
        with self.assertRaisesRegex(ValueError, 'byte_bound'):
            self.reopen(selection)

    def sidecar(self, selection, cycle=1, life='synthetic'):
        ledger = dict(schema='R197_CORRECTION_LEDGER_V1', life_id=life,
            cycles=[dict(cycle=cycle, completed_sleeps=0, input={})])
        reference = self.journal.record('R197_CORRECTION_CYCLE', dict(ledger=ledger))
        cache = dict(record_index=reference['index'], record_sha256=reference['sha256'])
        (self.root / 'correction_ledger.json').write_text(json.dumps(cache))
        selection['sidecars'] = [dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)]

    def test_sidecar_valid_source_and_cycle(self):
        selection = self.complete()
        self.sidecar(selection)
        recovered = self.reopen(selection)
        self.assertEqual(recovered.checkpoint_tail_receipt['sidecars'][0]['maximum_cycle'], 1)

    def test_sidecar_ahead_cycle_rejected(self):
        selection = self.complete()
        self.sidecar(selection, cycle=2)
        with self.assertRaisesRegex(ValueError, 'cycle_ahead'):
            self.reopen(selection)

    def test_sidecar_other_life_rejected(self):
        selection = self.complete()
        self.sidecar(selection, life='different')
        with self.assertRaisesRegex(ValueError, 'sidecar_life'):
            self.reopen(selection)

    def test_future_anchor_is_durable_but_never_auto_selected(self):
        selection = self.complete()
        self.reopen(selection)
        self.step()
        self.step()
        with patch('os.fsync', wraps=os.fsync) as sync:
            self.stream.commit_sleep(self.receipt(), self.journal.record)
        self.assertGreaterEqual(sync.call_count, 8)
        durable = self.journal.checkpoint_tail_durable_anchor
        self.assertEqual(json.loads(Path(durable['path']).read_text()), durable['document'])
        self.assertGreater(self.journal._checkpoint_tail['complete_index'], selection['complete_index'])
        recovered = self.reopen(selection)
        self.assertEqual(recovered.checkpoint_tail_receipt['complete_index'], selection['complete_index'])

    def test_writer_lock_not_bypassed(self):
        selection = self.complete()
        with self.assertRaises(BlockingIOError):
            StreamJournal(self.root, checkpoint_tail=selection)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]] + remaining, verbosity=2)
