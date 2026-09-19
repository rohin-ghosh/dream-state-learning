"""Restore the reviewed COPY on ovx4 and verify bytes and restorable metadata."""

from collections import defaultdict
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


DIRECTORIES = ('r225_siege_retirement_20260918', 'r233_retirement_20260918T1144Z',
    'r224_challenger_retirement_20260918')
ROOT = Path('/localhome/local-rohing/node3_retired_archive_copy_20260919T133405Z_ws6')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def file_sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(4 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def write_once(path, document):
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def dedup_summary(entries):
    groups = defaultdict(list)
    for item in entries.values():
        if item['kind'] == 'file' and item['size'] >= 1024 * 1024:
            groups[item['size'], item['sha256']].append(item)
    potential = 0
    examples = []
    cross_top_level = 0
    for (size, digest), items in groups.items():
        inodes = {(item['device'], item['inode']) for item in items}
        if len(inodes) <= 1:
            continue
        duplicate = (len(inodes) - 1) * size
        potential += duplicate
        cross = len({item['path'].split('/')[0] for item in items}) > 1
        cross_top_level += int(cross)
        metadata = {json.dumps({key: item[key] for key in
            ('mode', 'uid', 'gid', 'mtime_ns', 'atime_ns', 'ctime_ns', 'xattrs')}, sort_keys=True)
            for item in items}
        examples.append(dict(size=size, sha256=digest, path_count=len(items), distinct_inodes=len(inodes),
            logical_duplicate_bytes=duplicate, crosses_retirement_directories=cross,
            identical_all_recorded_metadata=len(metadata) == 1,
            example_paths=[item['path'] for item in items[:8]]))
    return dict(large_threshold_bytes=1024 * 1024, duplicate_groups=len(examples),
        cross_top_level_groups=cross_top_level, logical_duplicate_bytes=potential,
        actual_reclaimed_bytes=0, source_mutations=False,
        independent_metadata_required=True,
        hardlinks_not_lossless_when_metadata_or_independent_mutability_differs=True,
        content_addressed_archive_can_preserve_each_path_and_metadata_in_manifest=True,
        examples=sorted(examples, key=lambda item: item['logical_duplicate_bytes'], reverse=True)[:25])


def main():
    require(os.uname().nodename == 'ipp2-ovx-p3-02', 'original_ovx4_archive_destination_only')
    require(ROOT.is_dir() and not ROOT.is_symlink() and ROOT.stat().st_uid == os.getuid(), 'owned_archive_root')
    verified = json.loads((ROOT / 'COPY_VERIFIED.json').read_bytes())
    require(verified['status'] == 'ALL_ARCHIVE_MEMBERS_STREAM_RESTORED_AND_VERIFIED', 'stream_verification_required')
    manifest = ROOT / 'SOURCE_MANIFEST.jsonl'
    require(file_sha(manifest) == verified['manifest_sha256'].split()[0], 'source_manifest_unchanged')
    entries = {item['path']: item for item in map(json.loads, manifest.read_text().splitlines())}
    require({name.split('/')[0] for name in entries} == set(DIRECTORIES), 'exact_three_retired_directories')
    write_once(ROOT / 'DEDUP_ANALYSIS.json', dedup_summary(entries))
    archive = ROOT / 'retired-node3.tar.zst'
    require(file_sha(archive) == verified['archive_sha256'].split()[0], 'verified_archive_unchanged')
    needed = sum(item.get('size', 0) for item in entries.values()) + 20 * 1024**3
    capacity = os.statvfs(ROOT)
    require(capacity.f_bavail * capacity.f_frsize > needed, 'headroom_preserves_other_ovx4_work')
    restore = ROOT / 'restore_verification'
    restore.mkdir(mode=0o700, exist_ok=False)
    write_once(ROOT / 'RESTORE_STARTED.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        restored_root=str(restore), owner_uid=os.getuid(), original_numeric_ownership='preserved_in_archive_not_applied',
        source_delete_or_remap=False, no_gpu_operations=True))
    with (ROOT / 'RESTORE.stderr').open('xb') as errors:
        decompressor = subprocess.Popen(['zstd', '-dc', str(archive)], stdout=subprocess.PIPE, stderr=errors)
        extractor = subprocess.Popen(['tar', '--no-same-owner', '--same-permissions', '--acls', '--xattrs',
            '--xattrs-include=*', '--delay-directory-restore', '-xpf', '-', '-C', str(restore)],
            stdin=decompressor.stdout, stderr=errors)
        decompressor.stdout.close()
        extractor_status, decompress_status = extractor.wait(), decompressor.wait()
    require(extractor_status == decompress_status == 0, 'extraction_failed_preserve_destination')
    observed = set()
    hardlinks = {}
    verified_bytes = 0
    for directory in DIRECTORIES:
        pending = [restore / directory]
        while pending:
            path = pending.pop()
            name = path.relative_to(restore).as_posix()
            require(name in entries, 'unexpected_restored_path:' + name)
            expected = entries[name]
            observed.add(name)
            metadata = path.lstat()
            require(stat.S_IMODE(metadata.st_mode) == expected['mode']
                and metadata.st_mtime_ns == expected['mtime_ns'], 'restored_mode_mtime_mismatch:' + name)
            require(metadata.st_uid == os.getuid(), 'restored_copy_not_owned_by_destination_owner:' + name)
            attributes = {key: base64.b64encode(os.getxattr(path, key, follow_symlinks=False)).decode()
                for key in os.listxattr(path, follow_symlinks=False)}
            require(attributes == expected['xattrs'], 'restored_xattrs_mismatch:' + name)
            if expected['kind'] == 'file':
                require(stat.S_ISREG(metadata.st_mode) and metadata.st_size == expected['size']
                    and file_sha(path) == expected['sha256'], 'restored_file_bytes_mismatch:' + name)
                identity = (expected['device'], expected['inode'])
                actual = (metadata.st_dev, metadata.st_ino)
                require(hardlinks.setdefault(identity, actual) == actual, 'restored_hardlink_mismatch:' + name)
                verified_bytes += metadata.st_size
            elif expected['kind'] == 'directory':
                require(stat.S_ISDIR(metadata.st_mode), 'restored_directory_mismatch:' + name)
                pending.extend(path.iterdir())
            else:
                require(stat.S_ISLNK(metadata.st_mode) and os.readlink(path) == expected['target'],
                    'restored_symlink_mismatch:' + name)
    require(observed == set(entries), 'missing_restored_paths')
    result = dict(status='FULL_FILESYSTEM_RESTORE_BYTES_LINKS_MODE_MTIME_XATTRS_VERIFIED',
        completed_utc=datetime.now(timezone.utc).isoformat(), members=len(observed),
        logical_file_bytes_verified=verified_bytes, archive_bytes=archive.stat().st_size,
        manifest_bytes=manifest.stat().st_size, source_root_untouched=True,
        owner_available_bytes_reclaimed_on_node3=0, original_owner_uid=2524, restored_owner_uid=os.getuid(),
        original_ownership_atime_ctime='preserved_and_verified_in_archive_and_manifest; not applied as filesystem identity',
        source_delete_or_remap=False, no_gpu_operations=True, root=str(ROOT))
    write_once(ROOT / 'RESTORE_VERIFIED.json', result)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
