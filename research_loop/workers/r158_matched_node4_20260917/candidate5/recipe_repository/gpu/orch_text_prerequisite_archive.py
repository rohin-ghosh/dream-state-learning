"""Preserve finished native evidence with a verified file inventory."""

import hashlib
import json
from pathlib import Path
import sys
import tarfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(root):
    for index in range(4):
        if (root / f'shard{index}/exit_code.txt').read_text().strip() != '0':
            raise ValueError('all_shards_must_be_terminal_success')
        if not json.loads((root / f'release_{index}.json').read_text())['clear']:
            raise ValueError('resource_release_required')
    paths = sorted(path for path in root.rglob('*') if path.is_file()
        and path.relative_to(root).parts[0] not in ('env', 'source')
        and not path.name.endswith('.tar.gz') and path.name != 'ARCHIVE_RECEIPT.json')
    inventory = {str(path.relative_to(root)): sha(path) for path in paths}
    target = root / 'validated_terminal.tar.gz'
    with tarfile.open(target, 'x:gz') as packed:
        for path in paths:
            packed.add(path, arcname=str(path.relative_to(root)))
    with tarfile.open(target, 'r:gz') as packed:
        recovered = {member.name: hashlib.sha256(packed.extractfile(member).read()).hexdigest()
                     for member in packed.getmembers()}
    if recovered != inventory or any(sha(path) != inventory[str(path.relative_to(root))] for path in paths):
        raise ValueError('archive_or_source_drift')
    receipt = dict(archive_sha256=sha(target), entries=len(inventory), inventory=inventory,
                   bytes=target.stat().st_size, validation='ARCHIVE_BYTES_AND_SOURCE_INVENTORY_EQUAL')
    (root / 'ARCHIVE_RECEIPT.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'inventory'}))


if __name__ == '__main__':
    archive(Path(sys.argv[1]))
