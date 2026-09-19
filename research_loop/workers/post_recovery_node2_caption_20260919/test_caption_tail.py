"""CPU synthetic tests against the exact caption receiving-source closure."""

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SOURCE = Path(os.environ.get('CAPTION_TEST_SOURCE', HERE / 'prepared_v2/source'))
sys.path.insert(0, str(SOURCE))
from gpu.caption_tail_runtime import bind_journal, journal_class
from gpu.checkpoint_tail_runtime import scan
from gpu.orch_r125_stream_journal import StreamJournal, _digest
from gpu.r213_recovery_runtime import RecoveryJournal, saved_state

spec = importlib.util.spec_from_file_location('caption_fixture', SOURCE / 'tests/test_orch_r125_stream_journal.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class CaptionTailTests(unittest.TestCase):
    setUp = fixture.StreamJournalTests.setUp
    step = fixture.StreamJournalTests.step
    receipt = fixture.StreamJournalTests.receipt
    parent = fixture.StreamJournalTests.parent
    record_path = fixture.StreamJournalTests.record_path

    def complete(self):
        self.parent()
        self.step(incoming=self.journal.read_inbox())
        self.step()
        receipt = self.receipt()
        receipt.update(cycle=1, checkpoint=dict(checkpoint_sha256=receipt['checkpoint_sha256']))
        self.stream.commit_sleep(receipt, self.journal.record)
        selection = dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=str(self.root),
            journal_id=self.journal._manifest['journal_id'], complete_index=self.journal._state['index'] - 1,
            complete_sha256=self.journal._state['previous'], life_id='synthetic', max_tail_records=64,
            max_tail_bytes=16 * 1024 * 1024, sidecars=[], persist_complete_anchors=False)
        working = self.stream.history.working_state
        self.journal.record('R184_LEARN_COMPLETE', dict(cycle=1, checkpoint=receipt['checkpoint'],
            state_revision=working['revision'], working_state=working, parent_required_for_next_cycle=False))
        return selection

    def reopen(self, selection, deadline=1000):
        self.journal.close()
        self.journal = journal_class(RecoveryJournal, selection, deadline)(self.root)
        self.addCleanup(self.journal.close)
        return self.journal

    def test_full_replay_equals_tail_exact_saved_bytes(self):
        selection = self.complete()
        expected = deepcopy(self.journal._state)
        files = {path.name: path.read_bytes() for path in (self.root / 'records').iterdir()}
        self.journal.close()
        with RecoveryJournal(self.root) as original:
            self.assertEqual(original._state, expected)
        received = self.reopen(selection)
        self.assertEqual(received._state, expected)
        self.assertEqual(received.latest_checkpoint()['document'], self.stream.checkpoint())
        self.assertEqual(files, {path.name: path.read_bytes() for path in (self.root / 'records').iterdir()})
        self.assertIs(type(received)._advance, RecoveryJournal._advance)

    def test_unregistered_arriving_inbox_is_not_deleted_or_silently_consumed(self):
        selection = self.complete()
        path = self.parent('new.json', 'new-parent', 'Arrived after COMPLETE.')
        pending = path.read_bytes()
        received = self.reopen(selection)
        self.assertEqual(len(received._state['inbox']), 1)
        self.assertEqual(path.read_bytes(), pending)
        self.assertEqual(len(received.read_inbox()), 2)
        self.assertEqual(path.read_bytes(), pending)

    def test_registered_inbox_tail_is_preserved(self):
        selection = self.complete()
        self.parent('new.json', 'new-parent')
        self.journal.read_inbox()
        expected = deepcopy(self.journal._state)
        self.assertEqual(self.reopen(selection)._state, expected)

    def test_pending_request_scans_exactly_but_startup_refuses(self):
        selection = self.complete()
        def interrupted(*arguments, **keywords):
            raise RuntimeError('interrupted')
        with self.assertRaises(RuntimeError):
            self.step(generate_call=interrupted)
        expected = deepcopy(self.journal._state)
        self.assertEqual(scan(self.journal, selection), expected)
        with self.assertRaisesRegex(ValueError, 'resolved_state'):
            self.reopen(selection)

    def test_pending_response_scans_exactly_but_startup_refuses(self):
        selection = self.complete()
        def interrupted(kind, document):
            if kind == 'COMMITTED':
                raise RuntimeError('interrupted')
            return self.journal.record(kind, document)
        with self.assertRaises(RuntimeError):
            self.step(record=interrupted)
        self.assertEqual(scan(self.journal, selection), self.journal._state)
        with self.assertRaisesRegex(ValueError, 'resolved_state'):
            self.reopen(selection)

    def test_original_recovery_transition_is_applied_not_ignored(self):
        selection = self.complete()
        self.journal.close()
        with RecoveryJournal(self.root) as original:
            anchor = json.loads(self.record_path(selection['complete_index']).read_bytes())
            receipt = dict(old_native_absent=True, old_outer_exit_status=1,
                exact_resident_continuity_claimed=False, old_head_index=original._state['index'] - 1,
                old_head_sha256=original._state['previous'], complete_path=str(self.record_path(selection['complete_index'])),
                complete_sha256=anchor['sha256'], new_deadline_unix=1000)
            path = self.root.parent / 'recovery.json'
            path.write_text(json.dumps(receipt))
            original.record('R213_SAVED_BOUNDARY_RECOVERY', dict(receipt_path=str(path),
                receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), state=saved_state(anchor, 1000)))
            self.assertEqual(scan(original, selection), original._state)
            path.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'recovery_receipt_binding'):
                scan(original, selection)

    def test_no_historical_request_response_decoding(self):
        selection = self.complete()
        decoded = []
        original = StreamJournal._read_json
        def observe(directory, name):
            decoded.append(name)
            return original(directory, name)
        with patch.object(StreamJournal, '_read_json', side_effect=observe):
            received = self.reopen(selection)
        allowed = set(received.checkpoint_tail_receipt['decoded_prefix_indices'])
        for name in decoded:
            if name[:20].isdigit() and not name.endswith('.intent.json') and int(name[:20]) <= selection['complete_index']:
                self.assertIn(int(name[:20]), allowed)
        self.assertLess(len(allowed), selection['complete_index'])

    def test_full_audit_still_uses_original_transitions(self):
        received = self.reopen(self.complete())
        with patch.object(RecoveryJournal, '_advance', wraps=received._advance) as advance:
            received.audit()
        self.assertTrue(any(call.args[1] == 'REQUEST' for call in advance.call_args_list))
        self.assertFalse(received._caption_full_audit)

    def test_wrong_complete_pin_refused(self):
        selection = self.complete()
        selection['complete_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_complete_pin'):
            self.reopen(selection)

    def test_deadline_change_refused(self):
        with self.assertRaisesRegex(ValueError, 'same_deadline'):
            self.reopen(self.complete(), deadline=1001)
        with RecoveryJournal(self.root):
            pass

    def test_writer_lock_still_precedes_scan(self):
        selection = self.complete()
        with patch('gpu.checkpoint_tail_runtime.scan') as scanner, self.assertRaises(BlockingIOError):
            journal_class(RecoveryJournal, selection, 1000)(self.root)
        scanner.assert_not_called()

    def test_cold_create_forbidden(self):
        selection = self.complete()
        with self.assertRaisesRegex(ValueError, 'resume_only'):
            journal_class(RecoveryJournal, selection, 1000)(self.root, create=True)

    def test_prefix_corruption_refused(self):
        selection = self.complete()
        path = self.record_path(1)
        path.write_bytes(path.read_bytes().replace(b'System.', b'System!', 1))
        with self.assertRaisesRegex(ValueError, 'integrity'):
            self.reopen(selection)

    def test_intent_corruption_refused(self):
        selection = self.complete()
        path = self.root / 'records/00000000000000000000.intent.json'
        value = json.loads(path.read_bytes())
        value['record_sha256'] = '0' * 64
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'intent_binding'):
            self.reopen(selection)

    def test_missing_sidecar_refused(self):
        selection = self.complete()
        selection['sidecars'] = [dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)]
        with self.assertRaisesRegex(ValueError, 'required_sidecar_missing'):
            self.reopen(selection)

    def test_duplicate_learn_refused(self):
        selection = self.complete()
        self.journal.record('R184_LEARN_COMPLETE', dict(cycle=1))
        with self.assertRaisesRegex(ValueError, 'one_durable_LEARN'):
            self.reopen(selection)

    def test_moving_record_set_refused(self):
        selection = self.complete()
        from gpu import checkpoint_tail_runtime as reader
        original = reader.hash_record
        def changed(journal, index):
            result = original(journal, index)
            if index == selection['complete_index']:
                (self.root / 'records/extra.partial').write_bytes(b'')
            return result
        with patch.object(reader, 'hash_record', side_effect=changed), self.assertRaisesRegex(ValueError, 'changed_during_scan'):
            self.reopen(selection)

    def test_unknown_metadata_does_not_clear_pending_or_authorize_startup(self):
        selection = self.complete()
        self.journal.record('NOTE', dict(pending=None, authorized=True))
        with self.assertRaisesRegex(ValueError, 'no_intervening_work'):
            self.reopen(selection)


class SourceTests(unittest.TestCase):
    def test_default_returns_original_family(self):
        self.assertIs(bind_journal(RecoveryJournal, {}), RecoveryJournal)

    def test_other_cohorts_cannot_enroll(self):
        from gpu.checkpoint_tail_runtime import POLICY
        plan = dict(checkpoint_tail_recovery=dict(policy=POLICY), physical=1)
        with self.assertRaisesRegex(ValueError, 'caption_only'):
            bind_journal(RecoveryJournal, plan)

    def test_exact_overlay_and_original_dispatch_confinement(self):
        manifest = json.loads((HERE / 'prepared_v2/MANIFEST.json').read_bytes())
        for name, expected in manifest['all_files'].items():
            self.assertEqual(hashlib.sha256((SOURCE / name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(set(manifest['delta']), {'gpu/caption_tail_runtime.py',
            'gpu/checkpoint_tail_runtime.py', 'gpu/r233_node2_recovery.py'})
        source = (SOURCE / 'gpu/r233_node2_recovery.py').read_bytes()
        addition = (b'        from gpu.caption_tail_runtime import bind_journal\n'
            b'        runtime.ControlJournal = bind_journal(runtime.ControlJournal, plan)\n')
        self.assertEqual(source.count(addition), 1)
        self.assertEqual(hashlib.sha256(source.replace(addition, b'')).hexdigest(),
            manifest['delta']['gpu/r233_node2_recovery.py']['before'])

    def test_plan_delta_strictly_metadata_only(self):
        original = json.loads((HERE / 'original/PLAN.json').read_bytes())
        proposed = json.loads((HERE / 'prepared_v2/PLAN_CANDIDATE.json').read_bytes())
        self.assertEqual(proposed['hard_end_unix'], 1789927200)
        proposed.pop('checkpoint_tail_recovery')
        proposed['source_root'] = original['source_root']
        proposed['startup_context'] = original['startup_context']
        proposed['authorized_wall_extension'] = original['authorized_wall_extension']
        self.assertEqual(proposed, original)

    def test_original_caption_hooks_remain_wired(self):
        from gpu import r233_node2_recovery as route, r205_runtime as runtime
        from gpu import ny_caption_life, r227_caption_runtime
        plan = json.loads((HERE / 'prepared_v2/PLAN_CANDIDATE.json').read_bytes())
        with patch.object(runtime, 'main', side_effect=lambda: runtime.install_runtime(plan)), \
                patch.object(runtime, 'install_runtime') as original_install, \
                patch.object(ny_caption_life, 'activate') as activate, \
                patch.object(r227_caption_runtime, 'make_sleep_hook', side_effect=lambda function: function) as sleep_hook:
            route.main()
            original_install.assert_called_once_with(plan)
            activate.assert_called_once_with('/tmp/r226-caption-2.sock', max_act_attempts=3)
            sleep_hook.assert_called_once()
            self.assertTrue(issubclass(runtime.ControlJournal, RecoveryJournal))
        runtime.ControlJournal = RecoveryJournal


if __name__ == '__main__':
    unittest.main(verbosity=2)
