"""Hash-only inventories for node-backed transcript preservation; never prune."""

import argparse
import hashlib
import json
from pathlib import Path


def fingerprint(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(chunk)
    return dict(bytes=path.stat().st_size, sha256=checksum.hexdigest())


def inventory(root):
    records = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('symlink_forbidden')
        if path.is_file():
            records.append(dict(path=str(path.relative_to(root)), **fingerprint(path)))
    return records


def verify(root, records):
    mismatches = []
    names = set()
    for record in records:
        relative = Path(record['path'])
        if relative.is_absolute() or '..' in relative.parts or str(relative) in names:
            raise ValueError('unsafe_or_duplicate_path')
        names.add(str(relative))
        path = root / relative
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError('symlink_forbidden')
        expected = {key: record[key] for key in ('bytes', 'sha256')}
        if not path.is_file() or fingerprint(path) != expected:
            mismatches.append(str(relative))
    return dict(verified=not mismatches, files=len(records),
                bytes=sum(record['bytes'] for record in records), mismatches=mismatches,
                deletion_performed=False, scope='listed_snapshot_only_not_future_writes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    if args.manifest:
        result = verify(args.root, json.loads(args.manifest.read_text()))
        print(json.dumps(result))
        raise SystemExit(0 if result['verified'] else 1)
    print(json.dumps(inventory(args.root)))
