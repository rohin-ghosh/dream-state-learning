"""Read a pinned prefix through an existing native's root; never activate it."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import time


FILE_FIELDS = ('dev', 'ino', 'size', 'mtime_ns', 'ctime_ns', 'mode', 'nlink')
MAX_PROOF_BYTES = 64 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def file_identity(metadata):
    require(stat.S_ISREG(metadata.st_mode), 'regular_file_required')
    return dict(zip(FILE_FIELDS, (metadata.st_dev, metadata.st_ino, metadata.st_size,
        metadata.st_mtime_ns, metadata.st_ctime_ns, metadata.st_mode, metadata.st_nlink)))


def directory_identity(metadata):
    require(stat.S_ISDIR(metadata.st_mode), 'directory_required')
    return dict(dev=metadata.st_dev, ino=metadata.st_ino, mode=metadata.st_mode)


def immutable_directory_identity(metadata):
    require(stat.S_ISDIR(metadata.st_mode), 'immutable_source_directory_required')
    return dict(zip(FILE_FIELDS, (metadata.st_dev, metadata.st_ino, metadata.st_size,
        metadata.st_mtime_ns, metadata.st_ctime_ns, metadata.st_mode, metadata.st_nlink)))


def process_identity(pid, start_ticks, uid):
    require(type(pid) is int and pid > 0, 'explicit_native_pid')
    root = Path('/proc') / str(pid)
    fields = (root / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[19] == str(start_ticks) and root.stat().st_uid == uid
        and fields[0] not in ('Z', 'X', 'T', 't'), 'exact_live_unstopped_native')
    return dict(pid=pid, start_ticks=str(start_ticks), uid=uid,
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        mount_namespace=os.readlink(root / 'ns/mnt'),
        command_sha256=hashlib.sha256((root / 'cmdline').read_bytes()).hexdigest(),
        cwd=os.readlink(root / 'cwd'))


def open_directory(root_descriptor, path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'literal_absolute_path')
    descriptor = os.dup(root_descriptor)
    chain = [directory_identity(os.fstat(descriptor))]
    try:
        for component in path.parts[1:]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
            chain.append(directory_identity(os.fstat(descriptor)))
        return descriptor, chain
    except BaseException:
        os.close(descriptor)
        raise


def verify_source_view(root_descriptor, source, objects):
    source_root = Path(source['root'])
    require(source_root.is_absolute() and '..' not in source_root.parts, 'literal_source_root')
    expected_files = {source['epoch']['path']: source['epoch']['sha256']}
    directories = {source_root}
    for relative, expected in sorted(source['pins'].items()):
        relative_path = Path(relative)
        require(not relative_path.is_absolute() and '..' not in relative_path.parts
            and relative_path.parts and str(relative_path) == relative, 'relative_source_path')
        target = source_root / relative_path
        require(str(target) not in expected_files, 'independent_source_epoch_path')
        expected_files[str(target)] = expected
        parent = target.parent
        while parent != source_root:
            require(source_root in parent.parents, 'source_directory_within_root')
            directories.add(parent)
            parent = parent.parent
    require(set(objects) == {'files', 'directories'}, 'source_objects_schema')
    require([entry['path'] for entry in objects['files']] == list(expected_files),
        'every_source_and_epoch_identity_required')
    require([entry['path'] for entry in objects['directories']]
        == [str(path) for path in sorted(directories, key=str)],
        'every_immutable_source_directory_required')
    for snapshot in objects['files']:
        require(set(snapshot) == {'path', 'chain', 'identity'}, 'source_file_snapshot_schema')
        target = Path(snapshot['path'])
        parent, chain = open_directory(root_descriptor, target.parent)
        try:
            require(chain == snapshot['chain'], 'same_source_file_directory_chain')
            descriptor = os.open(target.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=parent)
            with os.fdopen(descriptor, 'rb') as stream:
                before = file_identity(os.fstat(stream.fileno()))
                require(before == snapshot['identity'], 'same_producer_source_or_epoch_identity')
                require(before['size'] <= MAX_PROOF_BYTES, 'bounded_source_file')
                content = stream.read(MAX_PROOF_BYTES + 1)
                require(file_identity(os.fstat(stream.fileno())) == before
                    == file_identity(os.stat(target.name, dir_fd=parent, follow_symlinks=False)),
                    'unchanged_source_during_read')
            require(len(content) == before['size']
                and hashlib.sha256(content).hexdigest() == expected_files[str(target)],
                'same_source_or_epoch_bytes')
        finally:
            os.close(parent)
    for snapshot in objects['directories']:
        require(set(snapshot) == {'path', 'chain', 'identity'}, 'source_directory_snapshot_schema')
        descriptor, chain = open_directory(root_descriptor, snapshot['path'])
        try:
            require(chain == snapshot['chain'], 'same_source_directory_chain')
            require(immutable_directory_identity(os.fstat(descriptor)) == snapshot['identity'],
                'same_immutable_source_directory_metadata')
        finally:
            os.close(descriptor)
    return len(source['pins'])


def verify_view(root_descriptor, proof):
    selection = proof['binding']['selection']
    descriptor, chain = open_directory(root_descriptor, selection['root'])
    try:
        require(chain == proof['locations']['root_chain'], 'same_entire_root_chain')
        for name, location in (('JOURNAL.json', 'manifest'), ('WRITER.lock', 'writer_lock')):
            require(file_identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False))
                == proof['locations'][location], 'same_' + location)
        for name in ('records', 'inbox'):
            require(directory_identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False))
                == proof['locations'][name], 'same_' + name + '_directory')
        records = os.open('records', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=descriptor)
        try:
            require(len(proof['records']) == selection['complete_index'] + 1, 'complete_prefix_count')
            for index, entry in enumerate(proof['records']):
                require(entry['header']['index'] == index, 'contiguous_proof_record_indices')
                for suffix in ('.json', '.intent.json'):
                    metadata = os.stat(f'{index:020d}' + suffix, dir_fd=records, follow_symlinks=False)
                    require(file_identity(metadata) == entry['identities'][suffix], 'same_prefix_file_identity')
        finally:
            os.close(records)
    finally:
        os.close(descriptor)
    return verify_source_view(root_descriptor, proof['binding']['source'], proof['source_objects'])


def probe(proof_path, proof_sha256, pid, start_ticks, uid):
    started = time.monotonic()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'explicit_CPU_only_observer')
    with Path(proof_path).open('rb') as stream:
        raw = stream.read(MAX_PROOF_BYTES + 1)
    require(len(raw) <= MAX_PROOF_BYTES and hashlib.sha256(raw).hexdigest() == proof_sha256,
        'exact_operator_pinned_proof')
    proof = json.loads(raw)
    before = process_identity(pid, start_ticks, uid)
    require(before['boot_id'] == proof['binding']['environment']['boot_id'], 'same_kernel_boot')
    root_descriptor = os.open(f'/proc/{pid}/root', os.O_RDONLY | os.O_DIRECTORY)
    try:
        source_files = verify_view(root_descriptor, proof)
        verify_view(root_descriptor, proof)
    finally:
        os.close(root_descriptor)
    require(process_identity(pid, start_ticks, uid) == before, 'native_identity_unchanged')
    return dict(status='EXISTING_NATIVE_VIEW_VERIFIED_NOT_NEW_CONSUMER_ADMISSION',
        observed_unix=time.time(), elapsed_seconds=time.monotonic() - started,
        native=before, proof_sha256=proof_sha256, source_files=source_files,
        source_epoch_files=1, source_identity_attested=True,
        source_directories=len(proof['source_objects']['directories']),
        verified_prefix_files=2 * len(proof['records']), verification_passes=2,
        journal_writes=0, GPU_calls=0, native_signals=[], live_adoption=False,
        raw_prefix_bytes_hashed=0, metadata_is_not_cryptographic_immutability=True,
        next_consumer_must_revalidate=True, source_startup_or_admission_proven=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proof', required=True)
    parser.add_argument('--proof-sha256', required=True)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--start-ticks', required=True)
    parser.add_argument('--uid', type=int, required=True)
    arguments = parser.parse_args()
    print(json.dumps(probe(arguments.proof, arguments.proof_sha256,
        arguments.pid, arguments.start_ticks, arguments.uid), sort_keys=True))
