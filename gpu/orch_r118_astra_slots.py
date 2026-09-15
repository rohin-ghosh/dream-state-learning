"""Bounded direct-HTTP Astra concurrency, independent of memory-heavy CLI calls."""

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat
import time


ROOT = Path('/tmp/orch_astra_http_slots')
LIMIT = 4


@contextmanager
def acquire(cutoff, *, root=ROOT, clock=time.time, pause=time.sleep):
    root = Path(root)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError('private_owned_http_slot_directory_required')
    started = clock()
    descriptor = None
    try:
        while descriptor is None:
            if clock() >= cutoff - 20:
                raise TimeoutError('http_slot_deadline_preserves_provider_margin')
            for slot in range(LIMIT):
                candidate = os.open(root / str(slot), os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
                try:
                    fcntl.flock(candidate, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    os.close(candidate)
                except BaseException:
                    os.close(candidate)
                    raise
                else:
                    descriptor = candidate
                    break
            if descriptor is None:
                pause(min(.25, max(0, cutoff - 20 - clock())))
        yield dict(slot=slot, maximum_http_concurrency=LIMIT, waited_seconds=clock()-started,
                   provider_time_reserved_seconds=20, provider_attempts=0,
                   cli_lock_used=False)
    finally:
        if descriptor is not None:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
