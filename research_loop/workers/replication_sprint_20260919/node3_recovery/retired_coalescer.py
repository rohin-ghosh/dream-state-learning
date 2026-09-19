"""Explicitly approved immutable-retirement coalescing; no automatic execution."""

from datetime import datetime, timezone
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat

from assess_hardlinks import DIRECTORIES, FIELDS, require


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class DurableLedger:
    def __init__(self, path):
        self.path = Path(path)
        self.stream = self.path.open('x')
        self.previous = '0' * 64
        self.sequence = 0
        descriptor = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def record(self, kind, document):
        entry = dict(sequence=self.sequence, previous_sha256=self.previous, kind=kind,
            utc=datetime.now(timezone.utc).isoformat(), document=document)
        entry['sha256'] = digest(entry)
        return self.accept_remote(entry)

    def accept_remote(self, entry):
        require(entry['sequence'] == self.sequence and entry['previous_sha256'] == self.previous
            and entry['sha256'] == digest({key: value for key, value in entry.items() if key != 'sha256'}),
            'durable_ledger_exact_sequence_and_content')
        self.stream.write(json.dumps(entry, sort_keys=True) + '\n')
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.previous = entry['sha256']
        self.sequence += 1
        return entry['sha256']

    def close(self):
        self.stream.close()


class AcknowledgedLedger:
    """Remote mutator blocks until a VM/destination fsync acknowledgement."""

    def __init__(self, receive, publish):
        self.receive, self.publish = receive, publish
        self.previous, self.sequence = '0' * 64, 0

    def record(self, kind, document):
        entry = dict(sequence=self.sequence, previous_sha256=self.previous, kind=kind,
            utc=datetime.now(timezone.utc).isoformat(), document=document)
        entry['sha256'] = digest(entry)
        self.publish.write(json.dumps(entry, sort_keys=True) + '\n')
        self.publish.flush()
        raw = self.receive.readline()
        require(bool(raw), 'durable_ack_connection_lost_halt')
        acknowledgement = json.loads(raw)
        require(acknowledgement == dict(durable=True, sha256=entry['sha256']),
            'durable_ack_exact_event_required')
        self.previous, self.sequence = entry['sha256'], self.sequence + 1
        return entry['sha256']


def read_hash(descriptor):
    before = os.fstat(descriptor)
    os.lseek(descriptor, 0, os.SEEK_SET)
    value = hashlib.sha256()
    while block := os.read(descriptor, 4 * 1024 * 1024):
        value.update(block)
    after = os.fstat(descriptor)
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
        'file_changed_during_rehash')
    return value.hexdigest()


def owned_retired_path(path, root):
    path, root = Path(path), Path(root)
    relative = path.relative_to(root)
    require(relative.parts and relative.parts[0] in DIRECTORIES and '..' not in relative.parts,
        'only_reviewed_retired_paths')
    require(path.is_absolute() and path.resolve() == path and not path.is_symlink(),
        'no_symlink_or_redirected_ancestor')
    require(root.stat().st_uid == os.getuid(), 'owned_source_root')
    return path


def metadata(descriptor):
    value = os.fstat(descriptor)
    require(stat.S_ISREG(value.st_mode), 'regular_file_only')
    attributes = {name: base64.b64encode(os.getxattr(descriptor, name)).decode()
        for name in os.listxattr(descriptor)}
    return dict(size=value.st_size, uid=value.st_uid, gid=value.st_gid,
        mode=stat.S_IMODE(value.st_mode), mtime_ns=value.st_mtime_ns, xattrs=attributes)


def verify_path_fd(path, descriptor, expected, identity):
    bound = os.fstat(descriptor)
    current = path.lstat()
    require((bound.st_dev, bound.st_ino) == (identity['device'], identity['inode'])
        == (current.st_dev, current.st_ino), 'original_path_inode_binding_changed')
    require(metadata(descriptor) == {field: expected[field] for field in FIELDS if field != 'sha256'},
        'required_metadata_changed')
    require(read_hash(descriptor) == expected['sha256'], 'content_hash_changed')
    require(path.lstat() == current, 'path_changed_during_verification')


def readable_writer_fds(paths):
    identities = {(Path(path).stat().st_dev, Path(path).stat().st_ino) for path in paths}
    writers, inaccessible = [], []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            for descriptor in (process / 'fd').iterdir():
                observed = descriptor.stat()
                if (observed.st_dev, observed.st_ino) not in identities:
                    continue
                fields = dict(line.split(':', 1) for line in
                    (process / 'fdinfo' / descriptor.name).read_text().splitlines() if ':' in line)
                mode = int(fields['flags'].strip(), 8) & os.O_ACCMODE
                if mode != os.O_RDONLY:
                    writers.append(dict(pid=int(process.name), fd=int(descriptor.name), access_mode=mode))
        except (OSError, ValueError, KeyError) as error:
            inaccessible.append(dict(pid=process.name, error_type=type(error).__name__))
    return dict(writers=writers, inaccessible_or_exited=inaccessible, scope='readable_owner_FDs')


def verify_directory(path, descriptor):
    current = path.lstat()
    bound = os.fstat(descriptor)
    require(stat.S_ISDIR(current.st_mode)
        and (bound.st_dev, bound.st_ino) == (current.st_dev, current.st_ino),
        'parent_directory_replaced')


def validate_batch(batch, expected_sha256, root, approval):
    require(digest(batch) == expected_sha256, 'exact_reviewed_batch_bytes')
    require(approval is not None and approval['status'] == 'MAIN_REVIEWED_EXECUTION'
        and approval['batch_sha256'] == expected_sha256, 'implementation_only_no_execution_approval')
    require(batch['archive_verified'] is True and batch['filesystem_restore_verified'] is True
        and batch['accepted_metadata_differences'] == ['inode', 'ctime', 'nlink', 'atime'],
        'verified_archive_restore_and_explicit_metadata_exception')
    require(batch['root'] == str(root), 'exact_source_root')
    all_paths = []
    for group in batch['groups']:
        require(group['metadata']['size'] >= 1024**2, 'reviewed_large_files_only')
        for inode in [group['canonical'], *group['replacement_inodes']]:
            require(inode['links_outside_eligible_set'] == 0, 'no_outside_hardlinks')
            all_paths.extend(path['path'] for path in inode['paths'])
    require(all_paths and len(all_paths) == len(set(all_paths)) and len(all_paths) <= batch['max_paths'] <= 40,
        'unique_explicit_bounded_canary_paths')
    for path in all_paths:
        owned_retired_path(path, root)
    return all_paths


def verify_link_counts(descriptor, canonical_fd, original, canonical, changed, temporary_links=0):
    require(os.fstat(descriptor).st_nlink == len(original['paths']) - changed[original['inode']]
        and os.fstat(canonical_fd).st_nlink
            == len(canonical['paths']) + changed[canonical['inode']] + temporary_links,
        'fresh_link_counts_changed')


def execute_batch(batch, *, expected_sha256, root, ledger, approval=None, writer_scan=readable_writer_fds):
    try:
        all_paths = validate_batch(batch, expected_sha256, root, approval)
        ledger.record('BATCH_INTENT', dict(batch_sha256=expected_sha256,
            source_manifest_sha256=batch['source_manifest_sha256'], exact_paths=all_paths,
            archived_original_metadata_preserved=True, no_path_removal=True))
    except BaseException as error:
        ledger.record('BATCH_REJECTED_NO_MUTATION', dict(error_type=type(error).__name__,
            error=str(error), batch_sha256=expected_sha256, no_automatic_retry=True))
        raise
    completed = []
    replacements_returned = []
    last_operation, last_phase = None, 'BEFORE_MUTATION'
    try:
        for group_number, group in enumerate(batch['groups']):
            expected = group['metadata']
            inodes = [group['canonical'], *group['replacement_inodes']]
            opened = []
            directories = []
            try:
                for inode in inodes:
                    for entry in inode['paths']:
                        path = owned_retired_path(entry['path'], root)
                        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME)
                        opened.append((path, descriptor, inode))
                        verify_path_fd(path, descriptor, expected, inode)
                        require(os.fstat(descriptor).st_nlink == len(inode['paths']),
                            'fresh_no_outside_hardlinks')
                        require(os.fstat(descriptor).st_ctime_ns == entry['source_ctime_ns'],
                            'changed_since_reviewed_manifest')
                identities = {(item[2]['device'], item[2]['inode']) for item in opened}
                require(len({item[0] for item in identities}) == 1, 'same_device_only')
                for identity in identities:
                    descriptor = next(item[1] for item in opened
                        if (item[2]['device'], item[2]['inode']) == identity)
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                scan = writer_scan([str(item[0]) for item in opened])
                require(not scan['writers'], 'readable_writer_present')
                ledger.record('GROUP_REHASHED', dict(group=group_number, metadata=expected,
                    writer_scan=scan, potential_allocated_bytes=group['potential_allocated_bytes_freed']))
                canonical_path, canonical_fd, canonical = opened[0]
                canonical_directory = os.open(canonical_path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                directories.append(canonical_directory)
                changed = {inode['inode']: 0 for inode in inodes}
                for path_number, (path, descriptor, original) in enumerate(opened):
                    if original is canonical:
                        continue
                    verify_path_fd(path, descriptor, expected, original)
                    verify_path_fd(canonical_path, canonical_fd, expected, canonical)
                    verify_link_counts(descriptor, canonical_fd, original, canonical, changed)
                    require(not writer_scan([str(path), str(canonical_path)])['writers'], 'readable_writer_present')
                    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                    directories.append(directory)
                    temporary = f'.ws6-coalesce-{expected_sha256[:16]}-{group_number}-{path_number}'
                    require(not os.path.lexists(path.parent / temporary), 'preserve_prior_temporary_artifact')
                    operation = dict(group=group_number, source=str(canonical_path), destination=str(path),
                        temporary=str(path.parent / temporary), original_inode=original['inode'],
                        canonical_inode=canonical['inode'], expected_sha256=expected['sha256'])
                    last_operation, last_phase = operation, 'TEMP_LINK_INTENT'
                    ledger.record('TEMP_LINK_INTENT', operation)
                    verify_directory(canonical_path.parent, canonical_directory)
                    verify_directory(path.parent, directory)
                    verify_path_fd(path, descriptor, expected, original)
                    verify_path_fd(canonical_path, canonical_fd, expected, canonical)
                    require(not writer_scan([str(path), str(canonical_path)])['writers'], 'readable_writer_present')
                    verify_link_counts(descriptor, canonical_fd, original, canonical, changed)
                    os.link(canonical_path.name, temporary, src_dir_fd=canonical_directory,
                        dst_dir_fd=directory, follow_symlinks=False)
                    last_phase = 'TEMP_LINK_RETURNED'
                    os.fsync(directory)
                    temporary_stat = os.stat(temporary, dir_fd=directory, follow_symlinks=False)
                    require((temporary_stat.st_dev, temporary_stat.st_ino)
                        == (canonical['device'], canonical['inode']), 'temporary_is_original_canonical_inode')
                    verify_path_fd(path, descriptor, expected, original)
                    verify_path_fd(canonical_path, canonical_fd, expected, canonical)
                    ledger.record('REPLACE_INTENT', operation)
                    verify_directory(canonical_path.parent, canonical_directory)
                    verify_directory(path.parent, directory)
                    verify_path_fd(path, descriptor, expected, original)
                    verify_path_fd(canonical_path, canonical_fd, expected, canonical)
                    require(not writer_scan([str(path), str(canonical_path)])['writers'], 'readable_writer_present')
                    verify_link_counts(descriptor, canonical_fd, original, canonical, changed, temporary_links=1)
                    temporary_stat = os.stat(temporary, dir_fd=directory, follow_symlinks=False)
                    require((temporary_stat.st_dev, temporary_stat.st_ino)
                        == (canonical['device'], canonical['inode']), 'temporary_binding_changed_before_replace')
                    last_phase = 'REPLACE_INTENT_ACKNOWLEDGED'
                    os.replace(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory)
                    replacements_returned.append(operation)
                    last_phase = 'REPLACE_RETURNED'
                    os.fsync(directory)
                    verify_path_fd(path, canonical_fd, expected, canonical)
                    verify_directory(path.parent, directory)
                    changed[original['inode']] += 1
                    changed[canonical['inode']] += 1
                    require(os.fstat(descriptor).st_nlink == len(original['paths']) - changed[original['inode']]
                        and os.fstat(canonical_fd).st_nlink == len(canonical['paths']) + changed[canonical['inode']],
                        'replacement_link_counts_changed')
                    ledger.record('REPLACEMENT_VERIFIED', operation)
                    completed.append(operation)
                    last_phase = 'REPLACEMENT_VERIFIED_ACKNOWLEDGED'
            finally:
                for descriptor in reversed(directories):
                    os.close(descriptor)
                for unused_path, descriptor, unused_identity in opened:
                    os.close(descriptor)
        ledger.record('BATCH_COMPLETE', dict(replacements=len(completed), batch_sha256=expected_sha256,
            actual_owner_available_bytes=os.statvfs(root).f_bavail * os.statvfs(root).f_frsize))
        return completed
    except BaseException as error:
        ledger.record('HALTED_NO_ROLLBACK', dict(error_type=type(error).__name__, error=str(error),
            durably_confirmed_replacements=len(completed), replacement_syscalls_returned=len(replacements_returned),
            last_operation=last_operation, last_phase=last_phase, batch_sha256=expected_sha256,
            preserve_temporary_artifacts=True, no_automatic_retry=True))
        raise
