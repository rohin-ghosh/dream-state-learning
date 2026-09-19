"""Read-only archive manifests and stream restoration checks."""

import argparse
import base64
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tarfile


DIRECTORIES = (
    'r225_siege_retirement_20260918',
    'r233_retirement_20260918T1144Z',
    'r224_challenger_retirement_20260918',
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checksum(stream):
    digest = hashlib.sha256()
    while block := stream.read(4 * 1024 * 1024):
        digest.update(block)
    return digest.hexdigest()


def inventory(root):
    root = Path(root)
    for directory in DIRECTORIES:
        pending = [root / directory]
        while pending:
            path = pending.pop()
            before = path.lstat()
            attributes = {name: base64.b64encode(os.getxattr(path, name,
                follow_symlinks=False)).decode() for name in sorted(os.listxattr(path,
                follow_symlinks=False))}
            item = dict(path=path.relative_to(root).as_posix(), mode=stat.S_IMODE(before.st_mode),
                uid=before.st_uid, gid=before.st_gid, mtime_ns=before.st_mtime_ns,
                atime_ns=before.st_atime_ns, ctime_ns=before.st_ctime_ns,
                device=before.st_dev, inode=before.st_ino, nlink=before.st_nlink,
                xattrs=attributes)
            if stat.S_ISDIR(before.st_mode):
                item['kind'] = 'directory'
                descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NOATIME)
                try:
                    with os.scandir(descriptor) as entries:
                        pending.extend(sorted((path / entry.name for entry in entries), reverse=True))
                finally:
                    os.close(descriptor)
            elif stat.S_ISREG(before.st_mode):
                descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME)
                with os.fdopen(descriptor, 'rb') as stream:
                    require(os.fstat(stream.fileno()) == before, 'file_changed_before_hash')
                    item.update(kind='file', size=before.st_size, sha256=checksum(stream))
            elif stat.S_ISLNK(before.st_mode):
                item.update(kind='symlink', target=os.readlink(path))
            else:
                raise ValueError('unsupported_archive_special_file:' + str(path))
            after = path.lstat()
            require((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                == (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                'source_changed_during_manifest:' + str(path))
            yield item


def verify_stream(manifest, stream):
    expected = {}
    with open(manifest) as source:
        for line in source:
            item = json.loads(line)
            require(item['path'] not in expected, 'duplicate_source_path')
            expected[item['path']] = item
    require({name.split('/')[0] for name in expected} == set(DIRECTORIES), 'exact_archive_scope')
    seen = {}
    total_bytes = 0
    with tarfile.open(fileobj=stream, mode='r|', encoding='utf-8', errors='surrogateescape') as archive:
        for member in archive:
            name = member.name.rstrip('/')
            require(name in expected and name not in seen, 'unexpected_duplicate_member:' + name)
            item = expected[name]
            require(member.mode == item['mode'] and member.uid == item['uid']
                and member.gid == item['gid'], 'numeric_metadata_mismatch:' + name)
            mtime = member.pax_headers.get('mtime', str(member.mtime))
            require(int(Decimal(mtime) * 10**9) == item['mtime_ns'], 'mtime_mismatch:' + name)
            for field in ('atime', 'ctime'):
                require(field in member.pax_headers, 'missing_pax_' + field + ':' + name)
                require(int(Decimal(member.pax_headers[field]) * 10**9) == item[field + '_ns'],
                    field + '_mismatch:' + name)
            attributes = {key.removeprefix('SCHILY.xattr.'): base64.b64encode(
                value.encode('utf-8', 'surrogateescape')).decode()
                for key, value in member.pax_headers.items() if key.startswith('SCHILY.xattr.')}
            if member.islnk() and not attributes:
                target = seen.get(member.linkname)
                require(target is not None, 'hardlink_target_not_seen:' + name)
                attributes = target['xattrs']
            require(attributes == item['xattrs'], 'xattrs_mismatch:' + name)
            if item['kind'] == 'file':
                if member.islnk():
                    target = seen.get(member.linkname)
                    require(target is not None and target['kind'] == 'file'
                        and (target['device'], target['inode']) == (item['device'], item['inode'])
                        and target['sha256'] == item['sha256'], 'hardlink_mismatch:' + name)
                else:
                    require(member.isfile() and member.size == item['size'], 'file_size_mismatch:' + name)
                    require(checksum(archive.extractfile(member)) == item['sha256'],
                        'restored_bytes_mismatch:' + name)
                    total_bytes += member.size
            elif item['kind'] == 'directory':
                require(member.isdir(), 'directory_mismatch:' + name)
            else:
                require(member.issym() and member.linkname == item['target'], 'symlink_mismatch:' + name)
            seen[name] = item
    require(set(seen) == set(expected), 'missing_archive_members')
    return dict(status='ALL_ARCHIVE_MEMBERS_STREAM_RESTORED_AND_VERIFIED', members=len(seen),
        unique_file_bytes=total_bytes, source_numeric_ownership_preserved=True,
        mode_mtime_atime_ctime_xattrs_verified=True, physical_extraction_performed=False,
        source_deletion_authorized=False, owner_available_bytes_reclaimed=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('inventory', 'verify'))
    parser.add_argument('path')
    args = parser.parse_args()
    if args.operation == 'inventory':
        for item in inventory(args.path):
            print(json.dumps(item, sort_keys=True, separators=(',', ':')), flush=True)
    else:
        print(json.dumps(verify_stream(args.path, sys.stdin.buffer), sort_keys=True))


if __name__ == '__main__':
    main()
