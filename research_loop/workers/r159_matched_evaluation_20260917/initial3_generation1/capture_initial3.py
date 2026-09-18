import hashlib
import io
import json
import os
from pathlib import Path
import socket
import stat
import sys
import tarfile
import time


ROOT = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5')
COMMITS = dict(parented_learning='1aa2785d58eb0ac98f7af799360f2334226977a8a3648ed61a6ccfffe6ccfc55',
    parented_frozen='68580b9e6f4db25d0bc8b5a2107eec7507863d617065ff8b3f6d7c352a97417c',
    unparented_learning='101dcf3bfdc327d664ee394374733d18f748800966b32e67925bf587e2d5628a')
ADAPTERS = {'README.md': '1b1a685a0798f66ef71e870c1b87713d92814d912c47297127c119e751d3ea33',
    'adapter_config.json': 'defb66b9d5bfdeff0a65f5624c661420b59219091a525401e23fa491824fe997',
    'adapter_model.safetensors': '2beaa09d4930b1eafa6a1a07a67f3d062b35336d5e5ac58778a00ad518cf9dfe'}


def checked_bytes(path, checksum, remaining, end):
    if time.time() >= end:
        raise ValueError('copy_authority_expired')
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('source_symlink')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > remaining:
            raise ValueError('copy_bound_or_regular_file')
        raw = stream.read(before.st_size)
        after = os.fstat(stream.fileno())
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError('source_changed_during_capture')
    if len(raw) != before.st_size or hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError('source_hash_changed')
    return raw


def capture(root, commits, adapters, output, limit=536870912, end=1789632000):
    captured = {}
    used = 0
    for arm, checksum in commits.items():
        prefix = Path(arm) / 'checkpoints/initial'
        inventory = {'COMMIT.json': checksum, **{f'adapter/{name}': value for name, value in adapters.items()}}
        for name, expected in inventory.items():
            relative = prefix / name
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('exact_relative_member')
            raw = checked_bytes(root / relative, expected, limit-used, end)
            used += len(raw)
            captured[str(relative)] = raw
    for arm, checksum in commits.items():
        checked_bytes(root / arm / 'checkpoints/initial/COMMIT.json', checksum, 16777216, end)
    if time.time() >= end:
        raise ValueError('copy_authority_expired')
    with tarfile.open(fileobj=output, mode='w|') as archive:
        for name, raw in captured.items():
            metadata = tarfile.TarInfo(name)
            metadata.size, metadata.mode = len(raw), 0o600
            archive.addfile(metadata, io.BytesIO(raw))
    return dict(bytes=used, files=len(captured))


if __name__ == '__main__':
    assert socket.gethostname() == '[REDACTED_HOST]'
    assert hashlib.sha256((ROOT / 'COHORT.json').read_bytes()).hexdigest() == 'da04b4cd814f6f695ca49a1ace66f9378039f6166d04e26bbd27ed7692ad0b4b'
    capture(ROOT, COMMITS, ADAPTERS, sys.stdout.buffer)
