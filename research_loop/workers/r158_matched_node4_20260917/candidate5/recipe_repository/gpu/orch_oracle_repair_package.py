"""Exact owned source capsule including portable runtime-hashed guard files."""

import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import tarfile

from gpu.orch_math_replication_package import source_closure
from organism_v6.orch_oracle_repair import sha256, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    options.output.mkdir(exist_ok=False)
    initial = {path.relative_to(root).as_posix() for pattern in (
        'gpu/orch_oracle_repair*.py', 'organism_v6/orch_oracle_repair*.py',
        'tests/test_orch_oracle_repair*.py') for path in root.glob(pattern)}
    initial.update(('gpu/astra_goal_breadth_collection_guard.sh',
                    'gpu/astra_goal_pair_collection_guard.sh', 'gpu/astra_event_two_hop_memory_guard.sh'))
    files = source_closure(root, initial)
    inventory = {name: sha256(root / name) for name in files}
    write(options.output / 'SOURCE_SHA256.json', inventory)
    archive_path = options.output / 'source.tar'
    with tarfile.open(archive_path, 'x') as archive:
        for name in files:
            archive.add(root / name, arcname=name, recursive=False)
    with tarfile.open(archive_path) as archive:
        for member in archive:
            if not member.isfile() or hashlib.sha256(archive.extractfile(member).read()).hexdigest() != inventory[member.name]:
                raise ValueError('source_archive_byte_mismatch')
    write(options.output / 'SOURCE_ARCHIVE.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
          files=len(files), archive_sha256=sha256(archive_path),
          source_inventory_sha256=sha256(options.output / 'SOURCE_SHA256.json'), native_calls=0))


if __name__ == '__main__':
    main()
