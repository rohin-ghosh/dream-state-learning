"""Read-only, inventory-bound parent admission. Never stops, starts, or calls a parent."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import stat


IDENTITY_FIELDS = ('pid', 'ticks', 'argv', 'cwd', 'uid')
MODULE = 'gpu.orch_r133_programme_parent'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical_path(value):
    require(type(value) is str and bool(value), 'path_string_required')
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts and str(path) == value,
            'canonical_absolute_path_required')
    require(path == path.resolve(strict=True), 'path_alias_refused')
    return path


def reference_fields(reference):
    require(type(reference) is dict and set(reference) == {'path', 'sha256'}, 'exact_file_reference')
    checksum = reference['sha256']
    require(type(checksum) is str and re.fullmatch('[0-9a-f]{64}', checksum) is not None,
            'sha256_required')
    return canonical_path(reference['path'])


def read_pinned(reference, *, limit=1024 * 1024):
    path = reference_fields(reference)
    parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parent.parts[1:]:
            nested = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                             dir_fd=parent)
            os.close(parent)
            parent = nested
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                             dir_fd=parent)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'bounded_regular_file')
            raw = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
            require(len(raw) == before.st_size and all(getattr(before, key) == getattr(after, key)
                for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')),
                'file_changed_during_read')
    finally:
        os.close(parent)
    require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'file_hash_mismatch')
    return raw


def read_inventory(reference):
    def unique_pairs(pairs):
        document = {}
        for key, value in pairs:
            require(key not in document, 'duplicate_inventory_key')
            document[key] = value
        return document

    def refuse_constant(value):
        raise ValueError('nonfinite_inventory_value')

    document = json.loads(read_pinned(reference, limit=4 * 1024 * 1024),
                          object_pairs_hook=unique_pairs, parse_constant=refuse_constant)
    require(type(document) is dict and type(document.get('processes')) is list
            and 0 < len(document['processes']) <= 1000, 'bounded_approved_inventory')
    processes = document['processes']
    require(all(type(process) is dict and all(key in process for key in IDENTITY_FIELDS)
                and type(process['pid']) is int and process['pid'] > 0 for process in processes),
            'inventory_process_identity')
    require(len({process['pid'] for process in processes}) == len(processes), 'unique_inventory_pid')
    return processes


def admit_parent(process, *, inventory_ref, repository, python_executable, expected_uid,
                 source_ref, config_ref):
    require(type(expected_uid) is int and expected_uid >= 0, 'explicit_owner_uid')
    require(type(process) is dict and all(key in process for key in IDENTITY_FIELDS),
            'complete_process_identity')
    require(type(process['pid']) is int and process['pid'] > 0
            and type(process['uid']) is int and process['uid'] == expected_uid,
            'owned_process_identity')
    require(type(process['ticks']) is str and re.fullmatch('[0-9]+', process['ticks']) is not None,
            'explicit_start_ticks')
    require(process.get('state') in ('R', 'S', 'D', 'I'), 'running_unstopped_parent_only')
    approved = [entry for entry in read_inventory(inventory_ref) if entry['pid'] == process['pid']]
    require(len(approved) == 1 and all(process[key] == approved[0][key] for key in IDENTITY_FIELDS),
            'exact_approved_inventory_identity')
    repository_path = canonical_path(repository)
    require(repository_path.is_dir(), 'repository_directory')
    legacy_scope = canonical_path(str(repository_path / 'research_loop/workers/r167_legacy_parent_rollout'))
    executable = canonical_path(python_executable)
    require(executable.is_file() and os.access(executable, os.X_OK), 'approved_python_executable')
    cwd = canonical_path(process['cwd'])
    require(cwd.is_dir(), 'process_cwd_directory')
    argv = process['argv']
    require(type(argv) is list and all(type(value) is str for value in argv)
            and argv[:2] == [str(executable), '-B'], 'exact_python_B_entry')
    if len(argv) == 10 and argv[2:4] == ['-m', MODULE]:
        mode, offset = 'module', 4
        source = canonical_path(str(cwd / 'gpu/orch_r133_programme_parent.py'))
    else:
        require(len(argv) == 9 and not argv[2].startswith('-'), 'exact_standalone_parent_entry')
        mode, offset = 'standalone', 3
        source = canonical_path(argv[2])
    arguments = argv[offset:]
    require(arguments[::2] == ['--config', '--repository', '--output'], 'exact_parent_options')
    config, invocation_repository, output = map(canonical_path, arguments[1::2])
    require(invocation_repository == repository_path, 'exact_repository_argument')
    require(config.name == 'CONFIG.json' and output.name == 'parent'
            and config.parent == output.parent and config.parent.parent == legacy_scope,
            'same_direct_legacy_branch_config_output')
    require(output.is_dir(), 'existing_predecessor_output')
    if mode == 'standalone':
        require(source == config.parent / 'PARENT.py', 'same_scoped_standalone_parent')
    require(reference_fields(source_ref) == source and reference_fields(config_ref) == config,
            'exact_source_config_reference_paths')
    read_pinned(source_ref)
    read_pinned(config_ref)
    return dict(schema='R169_PARENT_ADMISSION_V2',
        status='READ_ONLY_ADMISSION_NOT_TERMINATION_OR_SERVING', mode=mode,
        identity={key: deepcopy(process[key]) for key in IDENTITY_FIELDS},
        inventory_ref=deepcopy(inventory_ref), source_ref=deepcopy(source_ref),
        config_ref=deepcopy(config_ref), repository=str(repository_path),
        predecessor_output=str(output))
