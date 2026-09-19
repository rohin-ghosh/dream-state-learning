import hashlib
import json
import os
from pathlib import Path
import subprocess

from pidfd_scan import PROGRAM as PRIVILEGED_SCAN


ROOT = Path('/localhome/local-rohing')
FIELDS = ('size', 'sha256', 'uid', 'gid', 'mode', 'mtime_ns', 'xattrs')
LIVES = ('creative_d1', 'math_d1', 'math_transfer_c1', 'repo_c1')
RECORD_ROOTS = tuple(
    'orch_r153_r201_node2_clones_20260917_operator1/' + life + '/raw/stream/records'
    for life in LIVES
) + tuple('orch_rohin233_focus_node2_20260918/preserved/' + life + '/records' for life in LIVES)
BINDINGS_FILE = Path(__file__).with_name('GROUP_BINDINGS.json')
BINDINGS_DIGEST = 'ab1a1ef41e33254c037dfff2d3987ce1099343eb1ece04ed4d12027019d9f237'
BINDINGS_RAW_SHA = 'b73f8e4fb80bbdd9933d26611417d293287dbdf24f5447a1a15cdc85250c9935'
BOUND_SCOPE = None
GROUP_COUNT = 515
SELECTION_SHA = 'ec00b7918d16ac806eb7ebc405b7f150ce83d300946c3a61c44790af8b944e26'
MANIFEST_SHA = 'e9af879062abaeae7018a403a79ed909c0c5dfa334f549d32df5485238139db0'
ARCHIVE_SHA = 'caf4f1733b2ac16493d2f9d46b1e60e1d81a0c953eea1075bb363c1062111874'
RESTORE_SHA = 'fc9a0d2795fd208d2359381720e6683b490add8fc6e7280b78393da920cadda4'
ARCHIVE_DESTINATION = '/localhome/local-rohing/node2_retired_duplicate_preservation_20260919_20260919T151113Z'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def bind_scope_bytes(raw):
    global BOUND_SCOPE
    require(hashlib.sha256(raw).hexdigest() == BINDINGS_RAW_SHA, 'unchanged_exact_bindings_file')
    parsed = json.loads(raw)
    require(digest(parsed) == BINDINGS_DIGEST and len(parsed['group_sha256']) == GROUP_COUNT,
            'unchanged_exact_bindings_file')
    BOUND_SCOPE = parsed


def owned_retired_path(path, root):
    path, root = Path(path), Path(root)
    relative = path.relative_to(root)
    require(str(relative.parent) in RECORD_ROOTS and len(relative.name) == 25
            and relative.name.endswith('.json') and relative.name[:-5].isascii()
            and relative.name[:-5].isdigit(), 'only_exact_retired_record_paths')
    require(path.is_absolute() and path.resolve() == path and not path.is_symlink(),
            'no_symlink_or_redirected_ancestor')
    require(root == ROOT and root.stat().st_uid == os.getuid(), 'owned_exact_node2_source_root')
    return path


def validate_scope(batch, root):
    from retired_writer_guard import LOCKS_SHA256, POLICY
    require(batch.get('writer_protection') == POLICY and batch.get('writer_locks_sha256') == LOCKS_SHA256,
            'explicit_reviewed_lock_held_policy')
    require(Path(root) == ROOT, 'exact_node2_root')
    require(batch.get('bindings_sha256') == BINDINGS_DIGEST, 'exact_group_bindings')
    require(batch.get('selection_sha256') == SELECTION_SHA
            and batch.get('source_manifest_sha256') == MANIFEST_SHA
            and batch.get('archive_sha256') == ARCHIVE_SHA
            and batch.get('archive_full_restore_receipt_sha256') == RESTORE_SHA
            and batch.get('archive_destination') == ARCHIVE_DESTINATION, 'exact_node2_archive_and_selection')
    require(batch.get('ledger_policy') == 'external_durable_hash_chained_ack_before_each_mutation'
            and batch.get('automatic_retry') is False and batch.get('automatic_rollback') is False,
            'explicit_external_ledger_and_no_retry')
    if BOUND_SCOPE is None:
        raw = BINDINGS_FILE.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == BINDINGS_RAW_SHA, 'unchanged_exact_bindings_file')
        bindings = json.loads(raw)
    else:
        bindings = BOUND_SCOPE
    require(digest(bindings) == BINDINGS_DIGEST and len(bindings['group_sha256']) == GROUP_COUNT,
            'unchanged_exact_bindings_file')
    indices = []
    for group in batch['groups']:
        index = group.get('selection_index')
        require(type(index) is int and 0 <= index < GROUP_COUNT and index not in indices,
                'unique_exact_selection_index')
        require(digest(group) == bindings['group_sha256'][index], 'exact_selected_group_bytes')
        indices.append(index)


def validate_writer_scan(scan):
    require(not scan['writers'], 'readable_writer_present')
    require(scan.get('scanner_euid') == 0 and not scan.get('inaccessible_or_exited')
            and scan.get('scope') == 'all_uid_privileged_fds_and_writable_maps'
            and scan.get('lifetime_protocol') == 'pidfd_start_bound_v1',
            'complete_privileged_no_writer_snapshot_required')


def privileged_writer_fds(paths):
    require(0 < len(paths) <= 40, 'bounded_exact_writer_scope')
    for path in paths:
        owned_retired_path(path, ROOT)
    result = subprocess.run(['sudo', '-n', 'python3', '-B', '-c', PRIVILEGED_SCAN],
                            input=json.dumps(paths).encode(), capture_output=True, timeout=45, check=True)
    scan = json.loads(result.stdout)
    validate_writer_scan(scan)
    return scan
