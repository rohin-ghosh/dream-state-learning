"""Move fixed old source archives to /data while retaining logical /tmp paths."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import time


NAMES = (
    'astra_mask_source_98c0459c.tar',
    'astra_mask_source_f96ca508.tar',
    'astra_wake_source_79daf64c.tar',
    'astra_wake_fork_source_a4feb0f7.tar',
    'astra_semantic_source_241dd86e.tar',
    'astra_utility_source_e5c78cc8.tar.gz',
    'astra_rescore_source_02a772f8.tar.gz',
    'astra_exact_train_source_4465e537.tar.gz',
)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    destination = Path(__file__).resolve().parents[1]/'gpu_artifacts_local/vm_archive_preserved_20260914'
    if destination.exists():
        raise ValueError('new_destination_required')
    sources = [Path('/tmp')/name for name in NAMES]
    for process in Path('/proc').iterdir():
        if not process.name.isdecimal() or int(process.name) == os.getpid():
            continue
        try:
            command = (process/'cmdline').read_bytes().decode(errors='replace')
        except (PermissionError,FileNotFoundError,ProcessLookupError):
            continue
        if any(str(source) in command for source in sources):
            raise ValueError('visible_process_reference:'+process.name)
    records = []
    for source in sources:
        before = source.lstat()
        if source.is_symlink() or not source.is_file() or before.st_nlink != 1:
            raise ValueError('ordinary_single_link_archive_required:'+str(source))
        if before.st_mtime >= 1789344000:
            raise ValueError('only_archives_older_than_20260914UTC')
        signature = digest(source)
        after = source.stat()
        if (before.st_size,before.st_mtime_ns,before.st_ctime_ns) != (after.st_size,after.st_mtime_ns,after.st_ctime_ns):
            raise ValueError('source_changed_during_hash:'+str(source))
        records.append(dict(source=str(source),destination=str(destination/source.name),sha256=signature,
                            size=before.st_size,mtime_ns=before.st_mtime_ns))
    destination.mkdir()
    manifest = destination/'MANIFEST.json'
    manifest.write_text(json.dumps(dict(started_unix=time.time(),records=records,status='MOVING'),indent=2)+'\n')
    for record in records:
        source, target = Path(record['source']),Path(record['destination'])
        if target.exists() or source.is_symlink() or digest(source) != record['sha256']:
            raise ValueError('source_or_destination_changed')
        shutil.move(str(source),str(target))
        source.symlink_to(target)
        if digest(source) != record['sha256'] or source.resolve() != target.resolve():
            raise ValueError('relocated_bytes_or_logical_path_mismatch')
        record['verified'] = True
        manifest.write_text(json.dumps(dict(records=records,status='MOVING'),indent=2)+'\n')
    manifest.write_text(json.dumps(dict(finished_unix=time.time(),records=records,status='COMPLETE',
        relocated_bytes=sum(record['size'] for record in records),
        inactivity_scope='Old immutable archives; visible command lines checked, no claim of full proc visibility.'),indent=2)+'\n')
    print(manifest)
    print('relocated_bytes',sum(record['size'] for record in records))
    print('manifest_sha256',digest(manifest))


if __name__ == '__main__':
    main()
