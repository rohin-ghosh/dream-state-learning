"""Restore an absent, hash-bound read-only dependency without replacing bytes."""

import hashlib
import json
import os
from pathlib import Path


def restore(source, destination, file_sha256, held_sha256):
    data=Path(source).read_bytes()
    assert hashlib.sha256(data).hexdigest()==file_sha256
    document=json.loads(data)
    assert hashlib.sha256(json.dumps(document['held'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==held_sha256
    destination=Path(destination)
    assert not destination.exists() and not destination.is_symlink(), 'absent_dependency_only'
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_suffix('.repair_pending')
    with temporary.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    os.link(temporary,destination)
    temporary.unlink()
    assert destination.read_bytes()==data
    return dict(source=str(source),destination=str(destination),file_sha256=file_sha256,
                held_sha256=held_sha256,identical_bytes=True,missing_dependency_restored=True)
