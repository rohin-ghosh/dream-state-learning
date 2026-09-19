"""Bounded file and process evidence for the separate C2 owner adapter."""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OWNER = REPO / 'research_loop/workers/post_reboot_c2_p7_20260919'
PREVIOUS = REPO / 'research_loop/workers/rohin233_recovery_node4_20260918'
REGISTRY = REPO / 'research_loop/workers/post_reboot_services_20260919/services.d/c2-parent.json'
ROOT = '/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life'
JOURNAL = '260be8b8710a42559b291797c6e14983'
DEADLINE = 1789927200
IDENTITY = ('pid', 'uid', 'start_ticks', 'boot_id', 'argv', 'cwd')


def require(condition, reason):
    if not condition:
        raise ValueError('C2_owner_' + reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def literal(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path, 'literal_original_path')
    return path


def identity(entry):
    return (entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns, entry.st_ctime_ns, entry.st_mode)


def file_bytes(path, limit=256 * 1024**2):
    path = literal(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as handle:
        before = os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'bounded_regular_file')
        raw = handle.read(limit + 1)
        after = os.fstat(handle.fileno())
    require(len(raw) == before.st_size and identity(before) == identity(after) == identity(path.lstat()),
        'file_changed_during_read')
    return raw


def sha(path):
    return hashlib.sha256(file_bytes(path)).hexdigest()


def read(path):
    return json.loads(file_bytes(path))


def reference(path):
    return dict(path=str(literal(path)), sha256=sha(path))


def pinned(value):
    require(type(value) is dict and set(value) == {'path', 'sha256'}, 'exact_reference')
    raw = file_bytes(value['path'])
    require(hashlib.sha256(raw).hexdigest() == value['sha256'], 'exact_pinned_bytes')
    return json.loads(raw)


def pins_match(pins):
    require(pins and all(sha(path) == expected for path, expected in pins.items()), 'source_or_ledger_changed')


def sync(path):
    descriptor = os.open(literal(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_once(path, value):
    path = literal(path)
    raw = encoded(value) + b'\n'
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    sync(path.parent)
    return reference(path)


@contextmanager
def locked(path, *, create=False):
    flags = os.O_RDONLY | os.O_NOFOLLOW | (os.O_CREAT if create else 0)
    descriptor = os.open(literal(path), flags, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield descriptor
    finally:
        os.close(descriptor)


def process_identity(process_id):
    process = Path('/proc', str(process_id))
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=process_id, uid=process.stat().st_uid, start_ticks=fields[19], state=fields[0],
        ppid=int(fields[1]), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        argv=[os.fsdecode(part) for part in (process / 'cmdline').read_bytes().split(b'\0') if part],
        cwd=str((process / 'cwd').resolve()))


def lock_owners(path):
    entry = literal(path).stat()
    target = (os.major(entry.st_dev), os.minor(entry.st_dev), entry.st_ino)
    owners = []
    for line in Path('/proc/locks').read_text().splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[1:4] == ['FLOCK', 'ADVISORY', 'WRITE']:
            device = fields[5].split(':')
            if len(device) == 3 and (int(device[0], 16), int(device[1], 16), int(device[2])) == target:
                owners.append(int(fields[4]))
    return owners
