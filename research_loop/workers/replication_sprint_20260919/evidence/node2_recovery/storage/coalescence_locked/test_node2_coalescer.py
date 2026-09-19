from copy import deepcopy
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

import node2_scope as scope
import retired_coalescer as subject
import retired_writer_guard as writer_guard


HERE = Path(__file__).resolve().parent


def clean_scan(paths):
    return dict(writers=[], inaccessible_or_exited=[], scanner_euid=0,
                scope='all_uid_privileged_fds_and_writable_maps',
                lifetime_protocol='pidfd_start_bound_v1', verified_exits=[], cpu_fixture=True)


class Node2MutationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.root = self.work / 'source'
        self.root.mkdir()
        self.paths = []
        self.inodes = []
        for index, life in enumerate(scope.LIVES):
            first = self.root / scope.RECORD_ROOTS[index] / '00000000000000005844.json'
            alias = self.root / scope.RECORD_ROOTS[index + 4] / first.name
            first.parent.mkdir(parents=True)
            alias.parent.mkdir(parents=True)
            first.write_bytes(b'retired-record\n' * 400)
            first.chmod(0o600)
            os.utime(first, ns=(1000000000, 1000000000))
            os.link(first, alias)
            info = first.stat()
            entries = [dict(path=str(path), allocated_bytes=info.st_blocks * 512,
                            nlink=info.st_nlink, current_atime_ns=info.st_atime_ns,
                            source_ctime_ns=info.st_ctime_ns) for path in (first, alias)]
            self.paths.extend([first, alias])
            self.inodes.append(dict(device=info.st_dev, inode=info.st_ino, paths=entries,
                                    links_outside_eligible_set=0, allocated_bytes=info.st_blocks * 512))
        descriptor = os.open(self.paths[0], os.O_RDONLY | os.O_NOATIME)
        try:
            metadata = subject.metadata(descriptor)
            metadata['sha256'] = subject.read_hash(descriptor)
        finally:
            os.close(descriptor)
        self.group = dict(selection_index=0, filename=self.paths[0].name, metadata=metadata,
                          canonical=self.inodes[0], replacement_inodes=self.inodes[1:],
                          potential_allocated_bytes_freed=sum(item['allocated_bytes'] for item in self.inodes[1:]))
        self.bindings = {'group_sha256': [subject.digest(self.group)]}
        self.binding_path = self.work / 'GROUP_BINDINGS.json'
        self.binding_path.write_text(json.dumps(self.bindings))
        for name, value in [('ROOT', self.root), ('GROUP_COUNT', 1),
                            ('BINDINGS_FILE', self.binding_path), ('BINDINGS_DIGEST', subject.digest(self.bindings)),
                            ('BINDINGS_RAW_SHA', hashlib.sha256(self.binding_path.read_bytes()).hexdigest()),
                            ('BOUND_SCOPE', None)]:
            patcher = patch.object(scope, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.batch = json.loads((HERE / 'CANARY.json').read_bytes())
        self.batch.update(root=str(self.root), bindings_sha256=scope.BINDINGS_DIGEST, groups=[self.group])
        locks = []
        for relative in scope.RECORD_ROOTS[:4]:
            path = self.root / Path(relative).parent / 'WRITER.lock'
            path.write_bytes(b'')
            locks.append(writer_guard.lock_metadata(path, path.stat()))
        lock_file = self.work / 'WRITER_LOCKS.json'
        lock_file.write_text(json.dumps(dict(locks=locks)))
        lock_hash = hashlib.sha256(lock_file.read_bytes()).hexdigest()
        for name, value in [('LOCKS_FILE', lock_file), ('LOCKS_SHA256', lock_hash), ('BOUND_LOCKS', None)]:
            patcher = patch.object(writer_guard, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.batch['writer_locks_sha256'] = lock_hash
        self.locks = locks
        self.ledger = subject.DurableLedger(self.work / 'external.jsonl')
        self.addCleanup(self.ledger.close)
        self.writer_scan = clean_scan
        self.before = [path.stat().st_ino for path in self.paths]

    def invoke(self, approval=True, ledger=None):
        checksum = subject.digest(self.batch)
        return subject.execute_batch(self.batch, expected_sha256=checksum, root=self.root,
                                     ledger=ledger or self.ledger, writer_scan=self.writer_scan,
                                     approval=dict(status='MAIN_REVIEWED_EXECUTION', batch_sha256=checksum) if approval else None)

    def events(self):
        return [json.loads(line) for line in self.ledger.path.read_text().splitlines()]

    def assert_original_inodes(self):
        self.assertEqual([path.stat().st_ino for path in self.paths], self.before)

    def test_real_copied_mutator_preserves_all_eight_paths_and_metadata(self):
        self.assertEqual(len(self.invoke()), 6)
        for path in self.paths:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOATIME)
            try:
                self.assertEqual(subject.metadata(descriptor), {key:value for key,value in self.group['metadata'].items() if key != 'sha256'})
                self.assertEqual(subject.read_hash(descriptor), self.group['metadata']['sha256'])
                self.assertEqual(os.fstat(descriptor).st_ino, self.before[0])
                self.assertEqual(os.fstat(descriptor).st_nlink, 8)
            finally:
                os.close(descriptor)
        self.assertEqual(self.events()[-1]['kind'], 'BATCH_COMPLETE')
        self.assertEqual(list(self.root.rglob('.node2-coalesce-*')), [])

    def test_no_execution_authorization_has_no_mutation(self):
        with self.assertRaisesRegex(ValueError, 'no_execution_approval'):
            self.invoke(approval=False)
        self.assert_original_inodes()

    def test_wrong_approval_digest_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no_execution_approval'):
            subject.execute_batch(self.batch, expected_sha256=subject.digest(self.batch), root=self.root,
                                  ledger=self.ledger, approval=dict(status='MAIN_REVIEWED_EXECUTION', batch_sha256='0'*64))
        self.assert_original_inodes()

    def test_source_local_ledger_rejected(self):
        local = subject.DurableLedger(self.root / 'ledger.jsonl')
        self.addCleanup(local.close)
        with self.assertRaisesRegex(ValueError, 'external_durable_ledger_required'):
            self.invoke(ledger=local)
        self.assert_original_inodes()

    def test_acknowledged_remote_events_fsync_before_mutation(self):
        published = io.StringIO()
        durable = self.ledger
        class Receive:
            def readline(inner):
                entry = json.loads(published.getvalue().splitlines()[-1])
                return json.dumps(dict(durable=True, sha256=durable.accept_remote(entry))) + '\n'
        remote = subject.AcknowledgedLedger(Receive(), published)
        original_link, original_replace = os.link, os.replace
        def link(*args, **kwargs):
            self.assertEqual(self.events()[-1]['kind'], 'TEMP_LINK_INTENT')
            return original_link(*args, **kwargs)
        def replace(*args, **kwargs):
            self.assertEqual(self.events()[-1]['kind'], 'REPLACE_INTENT')
            return original_replace(*args, **kwargs)
        with patch.object(subject.os, 'link', side_effect=link), patch.object(subject.os, 'replace', side_effect=replace):
            self.assertEqual(len(self.invoke(ledger=remote)), 6)

    def test_lost_ack_halts_before_link(self):
        original = self.ledger.record
        def record(kind, document):
            if kind == 'TEMP_LINK_INTENT':
                raise OSError('CPU durable acknowledgement lost')
            return original(kind, document)
        with patch.object(self.ledger, 'record', side_effect=record):
            with self.assertRaises(OSError):
                self.invoke()
        self.assert_original_inodes()
        self.assertEqual(list(self.root.rglob('.node2-coalesce-*')), [])

    def test_exact_group_mutation_rejected_even_with_new_batch_approval(self):
        self.group['metadata']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_selected_group_bytes'):
            self.invoke()
        self.assert_original_inodes()

    def test_unknown_selection_index_rejected(self):
        self.group['selection_index'] = 1
        with self.assertRaisesRegex(ValueError, 'unique_exact_selection_index'):
            self.invoke()

    def test_bindings_file_change_rejected(self):
        self.binding_path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'unchanged_exact_bindings_file'):
            self.invoke()

    def test_exact_in_memory_binding_avoids_source_staging_files(self):
        scope.bind_scope_bytes(self.binding_path.read_bytes())
        with patch.object(scope, 'BINDINGS_FILE', self.work / 'absent.json'):
            self.assertEqual(len(self.invoke()), 6)

    def test_mutated_in_memory_binding_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unchanged_exact_bindings_file'):
            scope.bind_scope_bytes(self.binding_path.read_bytes() + b'\n')
        self.assert_original_inodes()

    def test_bound_in_memory_membership_cannot_be_changed_after_installation(self):
        scope.bind_scope_bytes(self.binding_path.read_bytes())
        scope.BOUND_SCOPE['group_sha256'][0] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'unchanged_exact_bindings_file'):
            self.invoke()
        self.assert_original_inodes()

    def test_old_judge_or_other_archive_proof_rejected(self):
        self.batch['archive_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_node2_archive_and_selection'):
            self.invoke()

    def test_missing_restore_proof_rejected(self):
        self.batch['filesystem_restore_verified'] = False
        with self.assertRaisesRegex(ValueError, 'verified_archive_restore'):
            self.invoke()

    def test_unaccepted_parent_directory_deltas_rejected(self):
        self.batch['accepted_metadata_differences'] = ['inode', 'ctime', 'nlink', 'atime']
        with self.assertRaisesRegex(ValueError, 'metadata_exception'):
            self.invoke()

    def test_scope_rejects_protected_and_unselected_paths(self):
        for relative in ['C0/raw/stream/records/00000000000000005844.json',
                         'Astra7/raw/stream/records/00000000000000005844.json',
                         'orch_r229_unparented_caption_20260918/raw/stream/records/00000000000000005844.json',
                         'models/00000000000000005844.json', 'checkpoints/00000000000000005844.json',
                         scope.RECORD_ROOTS[0] + '/PLAN.json']:
            with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, 'only_exact_retired'):
                scope.owned_retired_path(self.root / relative, self.root)

    def test_content_change_detected_with_same_size_mtime(self):
        path = self.paths[-1]
        info = path.stat()
        path.write_bytes(b'x' * info.st_size)
        os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, 'content_hash_changed'):
            self.invoke()
        self.assert_original_inodes()

    def test_mode_change_detected(self):
        self.paths[-1].chmod(0o400)
        with self.assertRaisesRegex(ValueError, 'required_metadata_changed'):
            self.invoke()

    def test_xattr_change_detected(self):
        os.setxattr(self.paths[-1], 'user.node2_cpu', b'different')
        with self.assertRaisesRegex(ValueError, 'required_metadata_changed'):
            self.invoke()

    def test_ctime_change_without_content_change_rejected(self):
        self.paths[-1].chmod(0o600)
        with self.assertRaisesRegex(ValueError, 'changed_since_reviewed_manifest'):
            self.invoke()

    def test_preexisting_outside_hardlink_rejected(self):
        os.link(self.paths[-1], self.work / 'outside_link')
        with self.assertRaisesRegex(ValueError, 'fresh_no_outside_hardlinks'):
            self.invoke()

    def test_linkcount_race_after_ack_rejected(self):
        original = self.ledger.record
        def record(kind, document):
            result = original(kind, document)
            if kind == 'TEMP_LINK_INTENT':
                os.link(self.paths[0], self.work / 'late_link')
            return result
        with patch.object(self.ledger, 'record', side_effect=record):
            with self.assertRaisesRegex(ValueError, 'fresh_link_counts_changed'):
                self.invoke()
        self.assert_original_inodes()

    def test_actual_open_writer_is_detected(self):
        self.writer_scan = subject.readable_writer_fds
        with self.paths[-1].open('ab'):
            with self.assertRaisesRegex(ValueError, 'readable_writer_present'):
                self.invoke()

    def test_inaccessible_process_blocks_mutation(self):
        self.writer_scan = lambda paths: dict(clean_scan(paths), inaccessible_or_exited=[{'error_type':'PermissionError'}])
        with self.assertRaisesRegex(ValueError, 'complete_privileged'):
            self.invoke()
        self.assert_original_inodes()

    def test_unprivileged_incomplete_scan_blocks_mutation(self):
        self.writer_scan = lambda paths: dict(clean_scan(paths), scanner_euid=os.getuid()+1)
        with self.assertRaisesRegex(ValueError, 'complete_privileged'):
            self.invoke()

    def test_symlink_destination_rejected(self):
        path = self.paths[-1]
        moved = self.work / 'preserved'
        path.rename(moved)
        path.symlink_to(moved)
        with self.assertRaisesRegex(ValueError, 'no_symlink'):
            self.invoke()

    def test_existing_temporary_artifact_preserved(self):
        name = '.node2-coalesce-' + subject.digest(self.batch)[:16] + '-0-2'
        path = self.paths[2].parent / name
        path.write_bytes(b'failed-previous-attempt')
        with self.assertRaisesRegex(ValueError, 'preserve_prior_temporary_artifact'):
            self.invoke()
        self.assertEqual(path.read_bytes(), b'failed-previous-attempt')
        self.assert_original_inodes()

    def test_enospc_preserves_every_original(self):
        with patch.object(subject.os, 'link', side_effect=OSError(28, 'CPU ENOSPC')):
            with self.assertRaises(OSError):
                self.invoke()
        self.assert_original_inodes()
        self.assertEqual(self.events()[-1]['kind'], 'HALTED_NO_ROLLBACK')

    def test_replace_failure_preserves_originals_and_temporary(self):
        with patch.object(subject.os, 'replace', side_effect=OSError('CPU replacement failure')):
            with self.assertRaises(OSError):
                self.invoke()
        self.assert_original_inodes()
        self.assertEqual(len(list(self.root.rglob('.node2-coalesce-*'))), 1)
        self.assertEqual(self.events()[-1]['kind'], 'HALTED_NO_ROLLBACK')

    def test_existing_lock_refused(self):
        with self.paths[0].open('rb') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):
                self.invoke()
        self.assert_original_inodes()


class ProductionBindingTests(unittest.TestCase):
    def test_all_515_groups_partition_exact_4120_paths(self):
        catalog = json.loads((HERE / 'GROUPS.json').read_bytes())
        template = json.loads((HERE / 'CANARY.json').read_bytes())
        paths = []
        for start in range(0, 515, 5):
            batch = dict(template, groups=catalog['groups'][start:start+5], max_paths=40)
            scope.validate_scope(batch, scope.ROOT)
            for group in batch['groups']:
                for inode in [group['canonical'], *group['replacement_inodes']]:
                    paths.extend(entry['path'] for entry in inode['paths'])
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 4120)
        self.assertEqual(sum(group['potential_allocated_bytes_freed'] for group in catalog['groups']), 1841565696)

    def test_canary_is_first_exact_group_only(self):
        catalog = json.loads((HERE / 'GROUPS.json').read_bytes())
        canary = json.loads((HERE / 'CANARY.json').read_bytes())
        self.assertEqual(canary['groups'], catalog['groups'][:1])
        self.assertEqual(canary['groups'][0]['filename'], '00000000000000005844.json')
        self.assertEqual(canary['groups'][0]['potential_allocated_bytes_freed'], 10444800)
        self.assertEqual(canary['max_paths'], 8)

    def test_minimum_size_lowering_is_exact_membership_not_general_scope(self):
        catalog = json.loads((HERE / 'GROUPS.json').read_bytes())
        template = json.loads((HERE / 'CANARY.json').read_bytes())
        small = next(group for group in catalog['groups'] if group['metadata']['size'] < 1024**2)
        scope.validate_scope(dict(template, groups=[small]), scope.ROOT)
        changed = deepcopy(small)
        changed['metadata']['size'] += 1
        with self.assertRaisesRegex(ValueError, 'exact_selected_group_bytes'):
            scope.validate_scope(dict(template, groups=[changed]), scope.ROOT)


if __name__ == '__main__':
    unittest.main(verbosity=2)
