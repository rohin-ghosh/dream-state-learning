from copy import deepcopy
import json
import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import retired_coalescer as subject
import test_assess_hardlinks as fixtures


class RetiredCoalescerTests(unittest.TestCase):
    def setUp(self):
        fixtures.HardlinkAssessmentTests.setUp(self)
        result = fixtures.HardlinkAssessmentTests.invoke(self)
        self.batch = dict(execution_status='REQUIRES_SEPARATE_MAIN_REVIEW', archive_verified=True,
            filesystem_restore_verified=True, accepted_metadata_differences=['inode', 'ctime', 'nlink', 'atime'],
            root=str(self.root), source_manifest_sha256=result['manifest_sha256'],
            groups=result['groups'], max_paths=4)
        self.ledger = subject.DurableLedger(self.root / 'ledger.jsonl')
        self.addCleanup(self.ledger.close)
        self.writer_scan = lambda paths: dict(writers=[], inaccessible_or_exited=[], cpu_fixture=True)
        self.approved = True

    def invoke(self):
        return subject.execute_batch(self.batch, expected_sha256=subject.digest(self.batch),
            root=self.root, ledger=self.ledger, writer_scan=self.writer_scan,
            approval=dict(status='MAIN_REVIEWED_EXECUTION', batch_sha256=subject.digest(self.batch))
                if self.approved else None)

    def events(self):
        return [json.loads(line) for line in self.ledger.path.read_text().splitlines()]

    def test_success_preserves_every_path_and_content_and_required_metadata(self):
        before = {path: (path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns)
            for path in (self.first, self.second)}
        self.assertEqual(len(self.invoke()), 1)
        self.assertEqual(self.first.stat().st_ino, self.second.stat().st_ino)
        self.assertEqual(self.first.stat().st_nlink, 2)
        for path, state in before.items():
            self.assertEqual((path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns), state)
        self.assertEqual(self.events()[-1]['kind'], 'BATCH_COMPLETE')
        previous = '0' * 64
        for entry in self.events():
            self.assertEqual(entry['previous_sha256'], previous)
            self.assertEqual(entry['sha256'], subject.digest({key: value for key, value in entry.items()
                if key != 'sha256'}))
            previous = entry['sha256']

    def test_unreviewed_implementation_never_mutates(self):
        self.approved = False
        with self.assertRaisesRegex(ValueError, 'no_execution_approval'):
            self.invoke()
        self.assertNotEqual(self.first.stat().st_ino, self.second.stat().st_ino)
        self.assertEqual(self.events()[-1]['kind'], 'BATCH_REJECTED_NO_MUTATION')

    def test_actual_open_writer_fd_is_detected(self):
        self.writer_scan = subject.readable_writer_fds
        with self.second.open('ab'):
            with self.assertRaisesRegex(ValueError, 'readable_writer_present'):
                self.invoke()

    def test_mode_mismatch_refused(self):
        self.second.chmod(0o400)
        with self.assertRaisesRegex(ValueError, 'required_metadata_changed'):
            self.invoke()

    def test_xattr_mismatch_refused(self):
        os.setxattr(self.second, 'user.ws6_cpu', b'changed')
        with self.assertRaisesRegex(ValueError, 'required_metadata_changed'):
            self.invoke()

    def test_existing_internal_links_preserved_and_counted(self):
        alias = self.second.with_name('also_weights.bin')
        os.link(self.second, alias)
        self.batch['groups'] = fixtures.HardlinkAssessmentTests.invoke(self)['groups']
        self.invoke()
        self.assertEqual({path.stat().st_ino for path in (self.first, self.second, alias)},
            {self.first.stat().st_ino})
        self.assertEqual(self.first.stat().st_nlink, 3)

    def test_outside_link_during_durable_link_intent_refused(self):
        original_record = self.ledger.record
        canonical = Path(self.batch['groups'][0]['canonical']['paths'][0]['path'])

        def add_link(kind, document):
            result = original_record(kind, document)
            if kind == 'TEMP_LINK_INTENT':
                os.link(canonical, self.root / 'late_outside_link')
            return result

        with patch.object(self.ledger, 'record', side_effect=add_link):
            with self.assertRaisesRegex(ValueError, 'fresh_link_counts_changed'):
                self.invoke()
        self.assertNotEqual(self.first.stat().st_ino, self.second.stat().st_ino)
        self.assertEqual(list(self.root.rglob('.ws6-coalesce-*')), [])

    def test_outside_link_during_durable_replace_intent_refused(self):
        original_record = self.ledger.record
        canonical = Path(self.batch['groups'][0]['canonical']['paths'][0]['path'])

        def add_link(kind, document):
            result = original_record(kind, document)
            if kind == 'REPLACE_INTENT':
                os.link(canonical, self.root / 'late_outside_link')
            return result

        with patch.object(self.ledger, 'record', side_effect=add_link):
            with self.assertRaisesRegex(ValueError, 'fresh_link_counts_changed'):
                self.invoke()
        self.assertNotEqual(self.first.stat().st_ino, self.second.stat().st_ino)
        self.assertEqual(len(list(self.root.rglob('.ws6-coalesce-*'))), 1)

    def test_no_restore_verification_never_mutates(self):
        self.batch['filesystem_restore_verified'] = False
        with self.assertRaisesRegex(ValueError, 'verified_archive_restore'):
            self.invoke()

    def test_changed_content_detected_despite_same_size_mtime(self):
        before = self.second.stat()
        self.second.write_bytes(b'x' * before.st_size)
        os.utime(self.second, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, 'content_hash_changed'):
            self.invoke()
        self.assertEqual(self.events()[-1]['kind'], 'HALTED_NO_ROLLBACK')

    def test_new_outside_hardlink_refused(self):
        os.link(self.second, self.root / 'outside')
        with self.assertRaisesRegex(ValueError, 'fresh_no_outside_hardlinks'):
            self.invoke()

    def test_readable_writer_refused(self):
        self.writer_scan = lambda paths: dict(writers=[dict(pid=123, fd=5)])
        with self.assertRaisesRegex(ValueError, 'readable_writer_present'):
            self.invoke()
        self.assertNotEqual(self.first.stat().st_ino, self.second.stat().st_ino)

    def test_symlink_destination_refused(self):
        self.second.rename(self.root / 'preserved_test_file')
        self.second.symlink_to(self.root / 'preserved_test_file')
        with self.assertRaisesRegex(ValueError, 'no_symlink'):
            self.invoke()

    def test_link_enospc_halts_without_path_loss(self):
        with patch.object(subject.os, 'link', side_effect=OSError(28, 'CPU ENOSPC fixture')):
            with self.assertRaises(OSError):
                self.invoke()
        self.assertTrue(self.first.exists() and self.second.exists())
        self.assertEqual(self.events()[-1]['kind'], 'HALTED_NO_ROLLBACK')

    def test_replace_failure_preserves_temporary_and_both_original_paths(self):
        original_inodes = [self.first.stat().st_ino, self.second.stat().st_ino]
        with patch.object(subject.os, 'replace', side_effect=OSError('CPU rename failure')):
            with self.assertRaises(OSError):
                self.invoke()
        self.assertEqual([self.first.stat().st_ino, self.second.stat().st_ino], original_inodes)
        self.assertEqual(len(list(self.root.rglob('.ws6-coalesce-*'))), 1)
        self.assertEqual(self.events()[-1]['kind'], 'HALTED_NO_ROLLBACK')

    def test_durable_ack_failure_before_link_prevents_mutation(self):
        original_record = self.ledger.record

        def fail(kind, document):
            if kind == 'TEMP_LINK_INTENT':
                raise OSError('durability acknowledgement unavailable')
            return original_record(kind, document)

        with patch.object(self.ledger, 'record', side_effect=fail):
            with self.assertRaises(OSError):
                self.invoke()
        self.assertNotEqual(self.first.stat().st_ino, self.second.stat().st_ino)
        self.assertEqual(list(self.root.rglob('.ws6-coalesce-*')), [])

    def test_batch_hash_tamper_refused(self):
        with self.assertRaisesRegex(ValueError, 'exact_reviewed_batch_bytes'):
            subject.execute_batch(self.batch, expected_sha256='0' * 64, root=self.root,
                ledger=self.ledger, writer_scan=self.writer_scan)

    def test_remote_ack_requires_exact_durable_event(self):
        published = io.StringIO()
        ledger = self.ledger

        class Acknowledgements:
            def readline(self):
                entry = json.loads(published.getvalue().splitlines()[-1])
                checksum = ledger.accept_remote(entry)
                return json.dumps(dict(durable=True, sha256=checksum)) + '\n'

        remote = subject.AcknowledgedLedger(Acknowledgements(), published)
        remote.record('INTENT', dict(cpu_fixture=True))
        self.assertEqual(remote.previous, self.events()[0]['sha256'])

    def test_remote_connection_loss_is_not_acknowledgement(self):
        remote = subject.AcknowledgedLedger(io.StringIO(''), io.StringIO())
        with self.assertRaisesRegex(ValueError, 'connection_lost_halt'):
            remote.record('INTENT', dict(cpu_fixture=True))

    def test_wrong_ack_is_not_durability(self):
        remote = subject.AcknowledgedLedger(io.StringIO('{"durable":true,"sha256":"wrong"}\n'), io.StringIO())
        with self.assertRaisesRegex(ValueError, 'exact_event_required'):
            remote.record('INTENT', dict(cpu_fixture=True))

    def test_lost_post_replace_ack_does_not_claim_zero_mutations(self):
        original_record = self.ledger.record

        def fail(kind, document):
            if kind == 'REPLACEMENT_VERIFIED':
                raise OSError('CPU simulated lost post-rename acknowledgement')
            return original_record(kind, document)

        with patch.object(self.ledger, 'record', side_effect=fail), self.assertRaises(OSError):
            self.invoke()
        self.assertEqual(self.first.stat().st_ino, self.second.stat().st_ino)
        halted = self.events()[-1]['document']
        self.assertEqual(halted['durably_confirmed_replacements'], 0)
        self.assertEqual(halted['replacement_syscalls_returned'], 1)
        self.assertEqual(halted['last_phase'], 'REPLACE_RETURNED')


if __name__ == '__main__':
    unittest.main()
