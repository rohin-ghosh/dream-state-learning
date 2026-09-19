"""Uninstalled, CPU-fixture-only empty intent reconciliation candidate.

Full original semantic audit is a CPU test oracle, not a production resume
strategy. The source-bound raw-prefix/COMPLETE-tail receiving seam is unbuilt.
"""

import base64
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import threading
import time


HERE = Path(__file__).resolve().parent
SCHEMA = 'ASTRA7_EMPTY_7808_RECONCILIATION_CANDIDATE_V1'
PARTIAL = '00000000000000007808.intent.json.partial'
NEXT_INDEX = 7808
EMPTY_SHA256 = hashlib.sha256(b'').hexdigest()
JOURNAL_SOURCE_SHA256 = '0b0d309cbb0399be3b9488fab0eb049063e321b927bf5b4b2c43369448bdf06f'
EXECUTION_AUTHORIZED = False


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def identity(value):
    return dict(device=value.st_dev, inode=value.st_ino, mode=value.st_mode,
        size=value.st_size, uid=value.st_uid, gid=value.st_gid, links=value.st_nlink,
        mtime_ns=value.st_mtime_ns, ctime_ns=value.st_ctime_ns)


def object_identity(value):
    return dict(device=value.st_dev, inode=value.st_ino)


def fixture_path(path):
    absolute = Path(path).absolute()
    require(absolute == absolute.resolve(), 'no_symlink_or_relative_path_components')
    containers = [parent for parent in absolute.parents
        if parent.parent == HERE and parent.name.startswith('.cpu-fixture-')]
    require(len(containers) == 1, 'CPU_fixture_scope_only_no_live_entry')
    return absolute, containers[0]


class LockedOriginalAuditor:
    """Own the existing writer lock; use original audit/scan without overrides.

    The original constructor cannot return an object while a partial exists.
    Only its descriptor/ownership setup is factored here; no scan error is
    suppressed inside the original auditor and no historical state is injected.
    """

    def __init__(self, root, original):
        self.root, self.container = fixture_path(root)
        require(hashlib.sha256(Path(original.__file__).read_bytes()).hexdigest()
            == JOURNAL_SOURCE_SHA256, 'pinned_original_journal_source')
        self.original = original
        self.auditor = None

    def __enter__(self):
        journal = self.original.StreamJournal.__new__(self.original.StreamJournal)
        journal.root = self.root
        journal.inbox = self.root / 'inbox'
        journal._owner = os.getpid()
        journal._mutex = threading.RLock()
        journal._fds = []
        journal._closed = False
        journal._failed = False
        self.original._JOURNALS.add(journal)
        self.auditor = journal
        try:
            journal._root_fd = journal._open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            journal._lock_fd = journal._open('WRITER.lock', os.O_RDWR, journal._root_fd)
            require(stat.S_ISREG(os.fstat(journal._lock_fd).st_mode), 'regular_existing_WRITER_lock')
            fcntl.flock(journal._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            journal._records_fd = journal._open('records', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
            journal._inbox_fd = journal._open('inbox', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
            journal._manifest = journal._read_json(journal._root_fd, 'JOURNAL.json')
            require(type(journal._manifest) is dict
                and set(journal._manifest) == {'schema', 'journal_id'}
                and journal._manifest['schema'] == self.original.SCHEMA
                and re.fullmatch(r'[0-9a-f]{32}', journal._manifest['journal_id']) is not None,
                'original_journal_manifest')
            journal._ensure_open()
            return journal
        except BaseException:
            journal.close()
            raise

    def __exit__(self, exception_type, exception, traceback):
        self.auditor.close()


def namespace(journal):
    journal._ensure_open()
    with os.scandir(journal._records_fd) as entries:
        result = {entry.name: identity(entry.stat(follow_symlinks=False)) for entry in entries}
    require(all(stat.S_ISREG(value['mode']) for value in result.values()), 'regular_record_namespace')
    return result


def capture_cut(journal, original):
    before = namespace(journal)
    require(f'{NEXT_INDEX:020d}.json' not in before
        and f'{NEXT_INDEX:020d}.intent.json' not in before, 'no_7808_commit_or_canonical_intent')
    require([name for name in before if name.endswith('.partial')] == [PARTIAL], 'exact_single_7808_partial')
    expected_names = {f'{index:020d}{suffix}' for index in range(NEXT_INDEX)
        for suffix in ('.json', '.intent.json')}
    require(set(before) == expected_names | {PARTIAL}, 'complete_committed_prefix_names_only')
    partial = before[PARTIAL]
    require(partial['size'] == 0, 'empty_partial_only')
    descriptor = journal._open(PARTIAL, os.O_RDONLY, journal._records_fd)
    require(identity(os.fstat(descriptor)) == partial, 'bound_zero_length_partial_descriptor')
    manifest_raw = journal._read_bytes(journal._root_fd, 'JOURNAL.json', limit=65536)
    require(original._decode(manifest_raw) == journal._manifest, 'unchanged_manifest')
    head_raw = journal._read_bytes(journal._records_fd, f'{NEXT_INDEX - 1:020d}.json', limit=1048576)
    intent_raw = journal._read_bytes(journal._records_fd, f'{NEXT_INDEX - 1:020d}.intent.json', limit=65536)
    head = original._decode(head_raw)
    require(set(head) == {'schema', 'journal_id', 'index', 'kind', 'previous_sha256', 'document', 'sha256'}
        and head['schema'] == original.SCHEMA and head['journal_id'] == journal._manifest['journal_id']
        and head['index'] == NEXT_INDEX - 1 and head['kind'] == 'UPDATE'
        and head['sha256'] == original._digest({key: value for key, value in head.items() if key != 'sha256'}),
        'canonical_7807_UPDATE_head')
    require(original._decode(intent_raw) == journal._intent(head), 'canonical_head_intent_binding')
    require(namespace(journal) == before, 'namespace_changed_during_inspection')
    cut = dict(schema=SCHEMA, life='Astra7', next_index=NEXT_INDEX, root=str(journal.root),
        root_identity=object_identity(os.fstat(journal._root_fd)),
        writer_identity=object_identity(os.fstat(journal._lock_fd)),
        records_identity=object_identity(os.fstat(journal._records_fd)),
        inbox_identity=object_identity(os.fstat(journal._inbox_fd)),
        journal_id=journal._manifest['journal_id'], manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
        old_head=dict(record_count=NEXT_INDEX, head_sha256=head['sha256']),
        head_file_sha256=hashlib.sha256(head_raw).hexdigest(),
        head_intent_file_sha256=hashlib.sha256(intent_raw).hexdigest(),
        partial_name=PARTIAL, partial_identity=partial, partial_bytes_sha256=EMPTY_SHA256,
        namespace_sha256=digest(before), original_auditor_sha256=JOURNAL_SOURCE_SHA256,
        execution_authorized=False)
    return cut, before


def observe_fixture(root, original, *, expected_saved_state_sha256):
    """Read-only CPU fixture binding, not a real-node authorization receipt."""
    require(re.fullmatch(r'[0-9a-f]{64}', expected_saved_state_sha256) is not None, 'saved_state_pin_required')
    with LockedOriginalAuditor(root, original) as journal:
        cut, _ = capture_cut(journal, original)
        require(cut['partial_identity']['links'] == 1, 'single_link_partial_required')
        cut['saved_state_sha256'] = expected_saved_state_sha256
        return dict(cut=cut, sha256=digest(cut))


def write_receipt(directory_fd, name, value):
    raw = encoded(value) + b'\n'
    descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600, dir_fd=directory_fd)
    with os.fdopen(descriptor, 'wb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    os.fsync(directory_fd)
    return hashlib.sha256(raw).hexdigest()


def partial_metadata(descriptor):
    value = os.fstat(descriptor)
    names = os.listxattr(descriptor)
    require(len(names) <= 32, 'bounded_partial_xattrs')
    attributes = {name: os.getxattr(descriptor, name) for name in names}
    require(sum(len(raw) for raw in attributes.values()) <= 65536, 'bounded_partial_xattr_bytes')
    return dict(identity(value), atime_ns=value.st_atime_ns,
        blocks=value.st_blocks, block_size=value.st_blksize,
        xattrs_base64={name: base64.b64encode(raw).decode() for name, raw in attributes.items()})


def same_artifact(before, after, links):
    require(after['links'] == links and all(before[name] == after[name]
        for name in before if name not in ('links', 'ctime_ns', 'atime_ns')), 'same_archived_artifact')


def evidence_bound(parent, parent_fd, attempt_name, evidence_fd):
    require(object_identity(os.stat(parent, follow_symlinks=False)) == object_identity(os.fstat(parent_fd))
        and object_identity(os.stat(attempt_name, dir_fd=parent_fd, follow_symlinks=False))
        == object_identity(os.fstat(evidence_fd)), 'evidence_directory_binding_replaced')


def verify_cut(journal, original, expected, before, partial_identity=None):
    expected_cut = {key: value for key, value in expected.items() if key != 'saved_state_sha256'}
    expected_namespace = before
    if partial_identity is not None:
        expected_namespace = dict(before, **{PARTIAL: partial_identity})
        expected_cut = dict(expected_cut, partial_identity=partial_identity,
            namespace_sha256=digest(expected_namespace))
    actual, snapshot = capture_cut(journal, original)
    require(actual == expected_cut and snapshot == expected_namespace, 'exact_unchanged_cut_required')


def reconcile_fixture(root, evidence_parent, envelope, *, expected_sha256, original):
    """Candidate mutation on local CPU fixtures only; never a live entry point."""
    root, container = fixture_path(root)
    evidence_parent, evidence_container = fixture_path(evidence_parent)
    require(container == evidence_container and not evidence_parent.is_relative_to(root)
        and not root.is_relative_to(evidence_parent), 'separate_same_fixture_evidence_directory')
    expected = deepcopy(envelope['cut'])
    require(envelope['sha256'] == expected_sha256 == digest(expected), 'pinned_cut_required')
    require(expected['schema'] == SCHEMA and expected['life'] == 'Astra7'
        and expected['next_index'] == NEXT_INDEX and expected['partial_name'] == PARTIAL
        and expected['execution_authorized'] is False, 'only_Astra7_7808_candidate')
    require(expected['partial_identity']['links'] == 1, 'single_link_partial_required')
    require(re.fullmatch(r'[0-9a-f]{64}', expected['saved_state_sha256']) is not None, 'saved_state_pin_required')
    attempt_name = 'astra7-7808-' + expected_sha256
    stage = 'INSPECT'
    evidence_fd = None
    parent_fd = None
    partial_fd = None
    with LockedOriginalAuditor(root, original) as journal:
        try:
            current, before = capture_cut(journal, original)
            require(current == {key: value for key, value in expected.items() if key != 'saved_state_sha256'},
                'exact_unchanged_cut_required')
            try:
                journal.audit()
            except ValueError as error:
                require(str(error) == 'incomplete_or_unexpected_journal_tail', 'only_expected_partial_audit_failure')
            else:
                raise ValueError('strict_original_auditor_must_refuse_partial')
            verify_cut(journal, original, expected, before)
            parent_fd = os.open(evidence_parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            require(os.fstat(parent_fd).st_dev == expected['partial_identity']['device'], 'same_filesystem_evidence_required')
            require(not os.path.lexists(evidence_parent / attempt_name), 'occupied_evidence_target')
            partial_fd = os.open(PARTIAL, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=journal._records_fd)
            metadata = partial_metadata(partial_fd)
            require(identity(os.fstat(partial_fd)) == before[PARTIAL], 'bound_partial_descriptor')
            os.mkdir(attempt_name, mode=0o700, dir_fd=parent_fd)
            os.fsync(parent_fd)
            evidence_fd = os.open(attempt_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent_fd)
            archive = evidence_parent / attempt_name / PARTIAL
            prepared = dict(schema=SCHEMA, stage='PREPARED', started_unix=time.time(),
                expected_cut=expected, expected_cut_sha256=expected_sha256,
                original_pathname=str(root / 'records' / PARTIAL), archive_pathname=str(archive),
                original_metadata=metadata, artifact_bytes_sha256=EMPTY_SHA256, artifact_bytes=0,
                mutation='DURABLE_HARDLINK_THEN_UNLINK_ONLY_ORIGINAL_TEMPORARY_NAME',
                execution_authorized=False, no_automatic_retry=True, native_restored=False)
            prepared_sha = write_receipt(evidence_fd, 'PREPARED.json', prepared)
            stage = 'PREPARED_DURABLE'
            verify_cut(journal, original, expected, before)
            evidence_bound(evidence_parent, parent_fd, attempt_name, evidence_fd)
            os.link(PARTIAL, PARTIAL, src_dir_fd=journal._records_fd, dst_dir_fd=evidence_fd,
                follow_symlinks=False)
            stage = 'LINK_CREATED'
            linked = partial_metadata(partial_fd)
            same_artifact(metadata, linked, 2)
            link_identity = identity(os.fstat(partial_fd))
            require(identity(os.stat(PARTIAL, dir_fd=evidence_fd, follow_symlinks=False)) == link_identity,
                'archive_is_same_inode')
            verify_cut(journal, original, expected, before, link_identity)
            os.fsync(partial_fd)
            os.fsync(evidence_fd)
            linked_sha = write_receipt(evidence_fd, 'LINKED.json', dict(schema=SCHEMA,
                stage='LINKED_DURABLE', prepared_sha256=prepared_sha,
                original_pathname=prepared['original_pathname'], archive_pathname=str(archive),
                linked_metadata=linked, artifact_bytes_sha256=EMPTY_SHA256))
            stage = 'LINKED_DURABLE'
            verify_cut(journal, original, expected, before, link_identity)
            evidence_bound(evidence_parent, parent_fd, attempt_name, evidence_fd)
            same_artifact(linked, partial_metadata(partial_fd), 2)
            require(identity(os.stat(PARTIAL, dir_fd=evidence_fd, follow_symlinks=False)) == link_identity,
                'archive_is_same_inode')
            os.unlink(PARTIAL, dir_fd=journal._records_fd)
            stage = 'ORIGINAL_TEMPORARY_NAME_UNLINKED'
            os.fsync(journal._records_fd)
            os.fsync(partial_fd)
            os.fsync(evidence_fd)
            evidence_bound(evidence_parent, parent_fd, attempt_name, evidence_fd)
            after_metadata = partial_metadata(partial_fd)
            same_artifact(metadata, after_metadata, 1)
            require(identity(os.stat(PARTIAL, dir_fd=evidence_fd, follow_symlinks=False))
                == identity(os.fstat(partial_fd)), 'archive_is_same_inode')
            require(namespace(journal) == {name: value for name, value in before.items() if name != PARTIAL},
                'committed_prefix_unchanged')
            audit = journal.audit()
            require(audit == expected['old_head'], 'strict_post_audit_same_old_head')
            latest = journal.latest_checkpoint()
            require(latest is not None and latest['expected_sha256'] == expected['saved_state_sha256'],
                'strict_post_audit_same_saved_state')
            require(namespace(journal) == {name: value for name, value in before.items() if name != PARTIAL},
                'committed_prefix_unchanged')
            evidence_bound(evidence_parent, parent_fd, attempt_name, evidence_fd)
            result = dict(schema=SCHEMA, stage='RECONCILED_CPU_FIXTURE_ONLY',
                prepared_sha256=prepared_sha, linked_sha256=linked_sha,
                expected_cut_sha256=expected_sha256, finished_unix=time.time(),
                artifact_pathname=str(archive), original_pathname=prepared['original_pathname'],
                original_metadata=metadata, archived_metadata=after_metadata,
                artifact_bytes_sha256=EMPTY_SHA256, same_inode_preserved=True,
                strict_audit=audit, saved_state_sha256=latest['expected_sha256'],
                new_journal_records=0, original_auditor_modified=False,
                full_history_semantic_audit_CPU_fixture_only=True,
                production_prefix_tail_integration_implemented=False, receiving_ready=False,
                native_restored=False, execution_authorized=False, Main_review_required=True)
            write_receipt(evidence_fd, 'RECONCILED.json', result)
            return result
        except BaseException as error:
            if evidence_fd is not None:
                try:
                    write_receipt(evidence_fd, 'FAILED_OR_UNKNOWN.json', dict(schema=SCHEMA,
                        stage=stage, error_type=type(error).__name__, no_automatic_retry=True,
                        preserve_all_artifacts=True, execution_authorized=False, native_restored=False))
                except BaseException:
                    pass
            raise
        finally:
            for descriptor in (partial_fd, evidence_fd, parent_fd):
                if descriptor is not None:
                    os.close(descriptor)


if __name__ == '__main__':
    raise SystemExit('CPU CANDIDATE ONLY: no live repair, installation or launch entry point')
