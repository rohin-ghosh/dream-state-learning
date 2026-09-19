"""Full original-auditor CPU fixtures; no real journals, model or native process."""

from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import reconcile as candidate
from research_loop.workers.replication_sprint_20260919.evidence.node2_recovery.runtime_repair.receiving_fixture import load_receiving_sources


HERE = Path(__file__).resolve().parent


class ReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = load_receiving_sources('Astra7')
        cls.original = cls.sources.journal
        cls.pool = tempfile.TemporaryDirectory(dir=HERE, prefix='.cpu-fixture-astra7-')
        cls.addClassCleanup(cls.pool.cleanup)
        cls.container = Path(cls.pool.name)
        cls.root = cls.container / 'journal'
        stream = cls.sources.stream.ContinualStream(
            cls.sources.history.TrainHistory(system_prompt='CPU fixture.', birth_prompt='No science claims.'),
            context_limit=4096, segment_tokens=16, segments_per_sleep=3,
            deadline_unix=1789927200, model_state_sha256='f' * 64)
        with cls.original.StreamJournal(cls.root, create=True) as journal:
            journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
            for _ in range(3):
                stream.step(lambda messages, **kwargs: dict(raw='Synthetic retained work.',
                    token_ids=[10, 2], terminal=True, truncated=False),
                    lambda messages: sum(len(message['content'].split()) + 4 for message in messages),
                    journal.record, now=lambda: 100)
            saved = stream.checkpoint()
            saved['state']['pending'] = 'sleep:' + cls.original._digest(
                [row['source_sha256'] for row in saved['state']['rows']])
            saved['sha256'] = cls.original._digest(saved['state'])
            journal.record('SLEEP_REQUEST', dict(cycle=147, resume_state=saved))
            initial = journal.audit()
            cls.saved_state = journal.latest_checkpoint()
            manifest = deepcopy(journal._manifest)
        previous = initial['head_sha256']
        for index in range(initial['record_count'], candidate.NEXT_INDEX):
            record = dict(schema=cls.original.SCHEMA, journal_id=manifest['journal_id'], index=index,
                kind='UPDATE', previous_sha256=previous,
                document=dict(synthetic=True, optimizer_step=index, fixture_only=True))
            record['sha256'] = cls.original._digest(record)
            (cls.root / 'records' / f'{index:020d}.json').write_bytes(cls.original._encoded(record) + b'\n')
            (cls.root / 'records' / f'{index:020d}.intent.json').write_bytes(
                cls.original._encoded(cls.original.StreamJournal._intent(record)) + b'\n')
            previous = record['sha256']
        with cls.original.StreamJournal(cls.root) as journal:
            cls.old_head = journal.audit()
            assert cls.old_head == dict(record_count=7808, head_sha256=previous)
            assert journal.latest_checkpoint() == cls.saved_state
        cls.partial = cls.root / 'records' / candidate.PARTIAL
        cls.head_path = cls.root / 'records/00000000000000007807.json'
        cls.intent_path = cls.root / 'records/00000000000000007807.intent.json'

    def setUp(self):
        self.case = tempfile.TemporaryDirectory(dir=self.container, prefix='case-')
        self.addCleanup(self.case.cleanup)
        self.evidence = Path(self.case.name) / 'evidence'
        self.evidence.mkdir(mode=0o700)
        self.partial.write_bytes(b'')
        self.addCleanup(lambda: self.partial.unlink(missing_ok=True))
        self.envelope = candidate.observe_fixture(self.root, self.original,
            expected_saved_state_sha256=self.saved_state['expected_sha256'])

    def run_candidate(self, envelope=None):
        envelope = self.envelope if envelope is None else envelope
        return candidate.reconcile_fixture(self.root, self.evidence, envelope,
            expected_sha256=envelope['sha256'], original=self.original)

    def attempt(self):
        return self.evidence / ('astra7-7808-' + self.envelope['sha256'])

    def archive(self):
        return self.attempt() / candidate.PARTIAL

    def receipt(self, name):
        return json.loads((self.attempt() / name).read_bytes())

    def source_snapshot(self):
        return {path.name: candidate.identity(path.lstat()) for path in (self.root / 'records').iterdir()}

    def preserve(self, path):
        raw = path.read_bytes()
        self.addCleanup(path.write_bytes, raw)
        return raw

    def assert_rejected_without_source_changes(self, reason, operation=None):
        before = self.source_snapshot()
        with self.assertRaisesRegex((ValueError, OSError), reason):
            (self.run_candidate if operation is None else operation)()
        self.assertEqual(self.source_snapshot(), before)
        self.assertFalse((self.attempt() / 'RECONCILED.json').exists())

    def assert_strict_rejects(self):
        with self.assertRaisesRegex(ValueError, 'incomplete_or_unexpected_journal_tail'):
            self.original.StreamJournal(self.root)

    def assert_old_journal_and_pending_state(self):
        with self.original.StreamJournal(self.root) as journal:
            self.assertEqual(journal.audit(), self.old_head)
            self.assertEqual(journal.latest_checkpoint(), self.saved_state)
        self.assertEqual(len(self.saved_state['document']['state']['rows']), 3)
        self.assertTrue(self.saved_state['document']['state']['pending'].startswith('sleep:'))

    def mutate_after_receipt(self, name, mutation):
        write = candidate.write_receipt
        def wrapped(directory, receipt_name, document):
            result = write(directory, receipt_name, document)
            if receipt_name == name:
                mutation()
            return result
        return patch.object(candidate, 'write_receipt', side_effect=wrapped)

    def fail_receipt(self, name):
        write = candidate.write_receipt
        def wrapped(directory, receipt_name, document):
            if receipt_name == name:
                raise OSError('synthetic_ENOSPC_' + name)
            return write(directory, receipt_name, document)
        return patch.object(candidate, 'write_receipt', side_effect=wrapped)

    def test_same_inode_receipts_and_original_full_auditor_accepts_without_state_change(self):
        self.assert_strict_rejects()
        before = self.source_snapshot()
        raw_metadata = candidate.identity(self.partial.stat())
        original_partial_path = str(self.partial)
        result = self.run_candidate()
        self.assertFalse(self.partial.exists())
        self.assertEqual(self.archive().read_bytes(), b'')
        self.assertEqual(self.archive().stat().st_ino, raw_metadata['inode'])
        self.assertEqual(self.archive().stat().st_dev, raw_metadata['device'])
        self.assertEqual(self.source_snapshot(), {name: value for name, value in before.items()
            if name != candidate.PARTIAL})
        prepared = self.receipt('PREPARED.json')
        linked = self.receipt('LINKED.json')
        self.assertEqual(prepared['original_pathname'], original_partial_path)
        for field, value in raw_metadata.items():
            self.assertEqual(prepared['original_metadata'][field], value)
        self.assertEqual(linked['linked_metadata']['links'], 2)
        self.assertEqual(result['archived_metadata']['links'], 1)
        self.assertEqual(result['prepared_sha256'], hashlib.sha256((self.attempt() / 'PREPARED.json').read_bytes()).hexdigest())
        self.assertEqual(result['linked_sha256'], hashlib.sha256((self.attempt() / 'LINKED.json').read_bytes()).hexdigest())
        self.assertEqual(result, self.receipt('RECONCILED.json'))
        self.assertFalse(result['execution_authorized'])
        self.assertFalse(result['native_restored'])
        self.assertFalse(result['receiving_ready'])
        self.assertFalse(result['production_prefix_tail_integration_implemented'])
        self.assertEqual(result['new_journal_records'], 0)
        self.assertFalse((self.root / 'records/00000000000000007808.json').exists())
        self.assert_old_journal_and_pending_state()

    def test_nonempty_partial_rejected(self):
        self.partial.write_bytes(b'not an empty failed publication')
        self.assert_rejected_without_source_changes('empty_partial_only')

    def test_original_mode_timestamps_and_xattrs_preserved_in_evidence(self):
        self.partial.chmod(0o640)
        os.setxattr(self.partial, 'user.synthetic_receipt', b'forensic CPU fixture')
        os.utime(self.partial, ns=(1230000000000000000, 1230000001000000000))
        before = self.partial.stat()
        self.envelope = candidate.observe_fixture(self.root, self.original,
            expected_saved_state_sha256=self.saved_state['expected_sha256'])
        result = self.run_candidate()
        metadata = self.receipt('PREPARED.json')['original_metadata']
        self.assertEqual(metadata['atime_ns'], before.st_atime_ns)
        self.assertEqual(metadata['mtime_ns'], before.st_mtime_ns)
        self.assertEqual(metadata['ctime_ns'], before.st_ctime_ns)
        self.assertEqual(metadata['mode'], before.st_mode)
        self.assertEqual(self.archive().stat().st_atime_ns, before.st_atime_ns)
        self.assertEqual(self.archive().stat().st_mtime_ns, before.st_mtime_ns)
        self.assertEqual(self.archive().stat().st_mode, before.st_mode)
        self.assertEqual(os.getxattr(self.archive(), 'user.synthetic_receipt'), b'forensic CPU fixture')
        self.assertEqual(result['archived_metadata']['xattrs_base64'], metadata['xattrs_base64'])
        self.assert_old_journal_and_pending_state()

    def test_changed_canonical_head_rejected(self):
        self.preserve(self.head_path)
        self.preserve(self.intent_path)
        head = json.loads(self.head_path.read_bytes())
        head['document']['optimizer_step'] += 1
        head['sha256'] = self.original._digest({key: value for key, value in head.items() if key != 'sha256'})
        self.head_path.write_bytes(self.original._encoded(head))
        self.intent_path.write_bytes(self.original._encoded(self.original.StreamJournal._intent(head)))
        self.assert_rejected_without_source_changes('exact_unchanged_cut_required')

    def test_occupied_evidence_target_rejected(self):
        self.attempt().mkdir()
        marker = self.attempt() / 'kept'
        marker.write_bytes(b'do not overwrite')
        self.assert_rejected_without_source_changes('occupied_evidence_target')
        self.assertEqual(marker.read_bytes(), b'do not overwrite')

    def test_missing_WRITER_lock_rejected_without_recreating_it(self):
        lock = self.root / 'WRITER.lock'
        saved = self.root / 'WRITER.saved'
        lock.rename(saved)
        self.addCleanup(saved.rename, lock)
        self.assert_rejected_without_source_changes('No such file')
        self.assertFalse(lock.exists())

    def test_busy_WRITER_lock_rejected(self):
        with (self.root / 'WRITER.lock').open('r+b') as writer:
            fcntl.flock(writer.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assert_rejected_without_source_changes('Resource temporarily unavailable')

    def test_multiple_partials_rejected(self):
        other = self.root / 'records/00000000000000007809.intent.json.partial'
        other.write_bytes(b'')
        self.addCleanup(other.unlink)
        self.assert_rejected_without_source_changes('exact_single_7808_partial')

    def test_existing_7808_commit_rejected(self):
        target = self.root / 'records/00000000000000007808.json'
        target.write_bytes(b'{}')
        self.addCleanup(target.unlink)
        self.assert_rejected_without_source_changes('no_7808_commit_or_canonical_intent')

    def test_existing_7808_canonical_intent_rejected(self):
        target = self.root / 'records/00000000000000007808.intent.json'
        target.write_bytes(b'{}')
        self.addCleanup(target.unlink)
        self.assert_rejected_without_source_changes('no_7808_commit_or_canonical_intent')

    def test_symlink_partial_rejected(self):
        empty = Path(self.case.name) / 'empty'
        empty.write_bytes(b'')
        self.partial.unlink()
        self.partial.symlink_to(empty)
        self.assert_rejected_without_source_changes('regular_record_namespace')

    def test_replaced_empty_partial_inode_rejected(self):
        old = Path(self.case.name) / 'original-partial'
        self.partial.rename(old)
        self.partial.write_bytes(b'')
        self.assert_rejected_without_source_changes('exact_unchanged_cut_required')
        self.assertEqual(old.read_bytes(), b'')

    def test_preexisting_extra_hardlink_rejected(self):
        alias = Path(self.case.name) / 'alias'
        os.link(self.partial, alias)
        self.assert_rejected_without_source_changes('exact_unchanged_cut_required')

    def test_prefix_changes_after_preparation_block_before_link(self):
        older = self.root / 'records/00000000000000000042.json'
        raw = self.preserve(older)
        with self.mutate_after_receipt('PREPARED.json', lambda: older.write_bytes(raw + b' ')):
            with self.assertRaisesRegex(ValueError, 'exact_unchanged_cut_required'):
                self.run_candidate()
        self.assertTrue(self.partial.exists())
        self.assertFalse(self.archive().exists())
        self.assert_strict_rejects()

    def test_partial_changes_after_link_block_source_unlink(self):
        with self.mutate_after_receipt('LINKED.json', lambda: self.partial.write_bytes(b'changed externally')):
            with self.assertRaisesRegex(ValueError, 'empty_partial_only'):
                self.run_candidate()
        self.assertEqual(self.partial.read_bytes(), b'changed externally')
        self.assertEqual(self.archive().read_bytes(), b'changed externally')
        self.assertEqual(self.partial.stat().st_ino, self.archive().stat().st_ino)
        self.assert_strict_rejects()

    def test_target_occupied_after_preparation_never_overwritten(self):
        with self.mutate_after_receipt('PREPARED.json', lambda: self.archive().write_bytes(b'occupied')):
            with self.assertRaises(FileExistsError):
                self.run_candidate()
        self.assertEqual(self.archive().read_bytes(), b'occupied')
        self.assertEqual(self.partial.read_bytes(), b'')
        self.assertEqual(self.partial.stat().st_nlink, 1)
        self.assert_strict_rejects()

    def test_failed_PREPARED_keeps_original_name_and_no_archive(self):
        with self.fail_receipt('PREPARED.json'):
            self.assert_rejected_without_source_changes('synthetic_ENOSPC')
        self.assertFalse(self.archive().exists())
        self.assertTrue(self.partial.exists())
        self.assert_strict_rejects()

    def test_failed_LINKED_keeps_both_links_and_strict_refusal(self):
        with self.fail_receipt('LINKED.json'):
            with self.assertRaisesRegex(OSError, 'synthetic_ENOSPC'):
                self.run_candidate()
        self.assertEqual(self.archive().stat().st_ino, self.partial.stat().st_ino)
        self.assertEqual(self.partial.stat().st_nlink, 2)
        self.assertEqual(self.receipt('FAILED_OR_UNKNOWN.json')['stage'], 'LINK_CREATED')
        self.assert_strict_rejects()

    def test_archive_inode_fsync_failure_never_unlinks_source(self):
        fsync = candidate.os.fsync
        partial_inode = self.partial.stat().st_ino
        def fail_archive_sync(descriptor):
            value = os.fstat(descriptor)
            if value.st_ino == partial_inode and value.st_nlink == 2:
                raise OSError('synthetic_archive_fsync_failure')
            return fsync(descriptor)
        with patch.object(candidate.os, 'fsync', side_effect=fail_archive_sync):
            with self.assertRaisesRegex(OSError, 'synthetic_archive_fsync_failure'):
                self.run_candidate()
        self.assertEqual(self.partial.stat().st_ino, self.archive().stat().st_ino)
        self.assertEqual(self.partial.stat().st_nlink, 2)
        self.assertFalse((self.attempt() / 'LINKED.json').exists())
        self.assertFalse((self.attempt() / 'RECONCILED.json').exists())
        self.assert_strict_rejects()

    def test_unlink_requires_durable_link_and_receipts_and_only_removes_failed_name(self):
        fsync, unlink = candidate.os.fsync, candidate.os.unlink
        partial_inode = self.partial.stat().st_ino
        barriers = set()
        removed = []
        def tracked_fsync(descriptor):
            fsync(descriptor)
            value = os.fstat(descriptor)
            if value.st_ino == partial_inode and value.st_nlink == 2:
                barriers.add('archive_inode_after_link')
            if self.attempt().exists() and value.st_ino == self.attempt().stat().st_ino \
                    and (self.attempt() / 'LINKED.json').exists():
                barriers.add('evidence_directory_with_linked_receipt')
        def checked_unlink(name, *, dir_fd=None):
            self.assertEqual(name, candidate.PARTIAL)
            self.assertEqual(os.fstat(dir_fd).st_ino, (self.root / 'records').stat().st_ino)
            self.assertEqual(barriers, {'archive_inode_after_link', 'evidence_directory_with_linked_receipt'})
            self.assertEqual(self.archive().stat().st_ino, partial_inode)
            self.assertEqual(self.archive().stat().st_nlink, 2)
            linked = self.receipt('LINKED.json')
            self.assertEqual(linked['prepared_sha256'],
                hashlib.sha256((self.attempt() / 'PREPARED.json').read_bytes()).hexdigest())
            removed.append(name)
            return unlink(name, dir_fd=dir_fd)
        with patch.object(candidate.os, 'fsync', side_effect=tracked_fsync), \
                patch.object(candidate.os, 'unlink', side_effect=checked_unlink):
            self.run_candidate()
        self.assertEqual(removed, [candidate.PARTIAL])
        self.assert_old_journal_and_pending_state()

    def test_failed_final_receipt_retains_artifact_no_success_or_automatic_retry(self):
        with self.fail_receipt('RECONCILED.json'):
            with self.assertRaisesRegex(OSError, 'synthetic_ENOSPC'):
                self.run_candidate()
        self.assertFalse(self.partial.exists())
        self.assertEqual(self.archive().read_bytes(), b'')
        self.assertFalse((self.attempt() / 'RECONCILED.json').exists())
        self.assertTrue(self.receipt('FAILED_OR_UNKNOWN.json')['no_automatic_retry'])
        self.assert_old_journal_and_pending_state()
        with self.assertRaisesRegex(ValueError, 'exact_single_7808_partial'):
            self.run_candidate()

    def test_corrupt_older_record_fails_full_original_post_audit_not_success(self):
        older = self.root / 'records/00000000000000000042.json'
        self.preserve(older)
        record = json.loads(older.read_bytes())
        record['document']['synthetic'] = False
        older.write_bytes(self.original._encoded(record))
        self.envelope = candidate.observe_fixture(self.root, self.original,
            expected_saved_state_sha256=self.saved_state['expected_sha256'])
        self.assert_strict_rejects()
        with self.assertRaisesRegex(ValueError, 'journal_chain_integrity'):
            self.run_candidate()
        self.assertEqual(self.archive().read_bytes(), b'')
        self.assertTrue((self.attempt() / 'PREPARED.json').exists())
        self.assertTrue((self.attempt() / 'LINKED.json').exists())
        self.assertFalse((self.attempt() / 'RECONCILED.json').exists())
        with self.assertRaisesRegex(ValueError, 'journal_chain_integrity'):
            self.original.StreamJournal(self.root)

    def test_wrong_saved_state_pin_fails_post_audit_without_restoration_claim(self):
        self.envelope['cut']['saved_state_sha256'] = '0' * 64
        self.envelope['sha256'] = candidate.digest(self.envelope['cut'])
        with self.assertRaisesRegex(ValueError, 'strict_post_audit_same_saved_state'):
            self.run_candidate()
        self.assertFalse(self.receipt('FAILED_OR_UNKNOWN.json')['native_restored'])
        self.assertEqual(self.archive().read_bytes(), b'')
        self.assert_old_journal_and_pending_state()

    def test_wrong_life_or_index_not_permitted_even_after_rehash(self):
        for field, value in (('life', 'MathB'), ('next_index', 7809), ('execution_authorized', True)):
            with self.subTest(field=field):
                envelope = deepcopy(self.envelope)
                envelope['cut'][field] = value
                envelope['sha256'] = candidate.digest(envelope['cut'])
                self.assert_rejected_without_source_changes('only_Astra7_7808_candidate',
                    lambda: self.run_candidate(envelope))

    def test_changed_envelope_hash_rejected(self):
        envelope = deepcopy(self.envelope)
        envelope['cut']['old_head']['head_sha256'] = '0' * 64
        self.assert_rejected_without_source_changes('pinned_cut_required', lambda: self.run_candidate(envelope))

    def test_replaced_WRITER_during_preparation_rejected(self):
        lock = self.root / 'WRITER.lock'
        saved = self.root / 'WRITER.saved'
        def replace():
            lock.rename(saved)
            lock.write_bytes(b'')
        def restore():
            lock.unlink()
            saved.rename(lock)
        self.addCleanup(restore)
        with self.mutate_after_receipt('PREPARED.json', replace):
            with self.assertRaisesRegex(ValueError, 'journal_binding_replaced'):
                self.run_candidate()
        self.assertTrue(self.partial.exists())
        self.assertFalse(self.archive().exists())

    def test_replaced_evidence_directory_blocks_source_unlink(self):
        old = Path(self.case.name) / 'preserved-evidence'
        def replace():
            self.evidence.rename(old)
            self.evidence.mkdir()
        with self.mutate_after_receipt('LINKED.json', replace):
            with self.assertRaisesRegex(ValueError, 'evidence_directory_binding_replaced'):
                self.run_candidate()
        archived = old / self.attempt().name / candidate.PARTIAL
        self.assertEqual(self.partial.stat().st_ino, archived.stat().st_ino)
        self.assertEqual(self.partial.stat().st_nlink, 2)
        self.assert_strict_rejects()

    def test_lock_is_held_across_receipts_and_archival(self):
        checks = []
        def another_writer_cannot_enter():
            with (self.root / 'WRITER.lock').open('r+b') as other:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(other.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            checks.append(True)
        with self.mutate_after_receipt('PREPARED.json', another_writer_cannot_enter), \
                self.mutate_after_receipt('LINKED.json', another_writer_cannot_enter):
            self.run_candidate()
        self.assertEqual(len(checks), 2)
        self.assert_old_journal_and_pending_state()

    def test_bad_head_intent_rejected(self):
        self.preserve(self.intent_path)
        self.intent_path.write_bytes(b'{}')
        self.assert_rejected_without_source_changes('canonical_head_intent_binding')

    def test_missing_historical_record_rejected_without_prefix_drop(self):
        original = self.root / 'records/00000000000000000042.json'
        kept = Path(self.case.name) / 'kept-record'
        original.rename(kept)
        self.addCleanup(kept.rename, original)
        self.assert_rejected_without_source_changes('complete_committed_prefix_names_only')

    def test_preparation_failure_claim_is_not_reused(self):
        with self.fail_receipt('PREPARED.json'):
            with self.assertRaises(OSError):
                self.run_candidate()
        self.assert_rejected_without_source_changes('occupied_evidence_target')

    def test_entry_rejects_nonfixture_paths_before_any_filesystem_write(self):
        self.assert_rejected_without_source_changes('CPU_fixture_scope_only_no_live_entry',
            lambda: candidate.reconcile_fixture('/localhome/not-a-fixture', self.evidence,
                self.envelope, expected_sha256=self.envelope['sha256'], original=self.original))

    def test_original_source_hash_required(self):
        with patch.object(candidate, 'JOURNAL_SOURCE_SHA256', '0' * 64):
            self.assert_rejected_without_source_changes('pinned_original_journal_source')


if __name__ == '__main__':
    unittest.main()
