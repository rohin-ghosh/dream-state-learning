import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat

import node2_scope as scope


LOCKS_FILE = Path(__file__).with_name('WRITER_LOCKS.json')
LOCKS_SHA256 = '7e71274cbd4745a38c717423c10472572df2b5c5155aac8f5828e2010a4570f7'
BOUND_LOCKS = None
POLICY = 'exact_four_original_WRITER_locks_one_pidfd_bound_scan_per_batch'


def bind_lock_bytes(raw):
    global BOUND_LOCKS
    scope.require(hashlib.sha256(raw).hexdigest() == LOCKS_SHA256, 'exact_original_WRITER_binding_bytes')
    BOUND_LOCKS = raw


def lock_metadata(path, info):
    return dict(path=str(path), device=info.st_dev, inode=info.st_ino,
                uid=info.st_uid, gid=info.st_gid, mode=stat.S_IMODE(info.st_mode),
                size=info.st_size, nlink=info.st_nlink, mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)


class RetiredWriterGuard:
    def __init__(self, batch, paths, scanner):
        scope.require(batch.get('writer_protection') == POLICY
                      and batch.get('writer_locks_sha256') == LOCKS_SHA256,
                      'explicit_reviewed_lock_held_policy')
        raw = BOUND_LOCKS if BOUND_LOCKS is not None else LOCKS_FILE.read_bytes()
        scope.require(hashlib.sha256(raw).hexdigest() == LOCKS_SHA256, 'exact_original_WRITER_binding_bytes')
        self.locks = json.loads(raw)['locks']
        expected = [str(scope.ROOT / Path(relative).parent / 'WRITER.lock') for relative in scope.RECORD_ROOTS[:4]]
        scope.require([item['path'] for item in self.locks] == expected, 'exact_four_original_stream_WRITER_paths')
        self.paths = frozenset(paths)
        self.scanner = scanner
        self.opened = []
        self.snapshot = None

    def __enter__(self):
        try:
            for binding in self.locks:
                path = Path(binding['path'])
                scope.require(path.resolve() == path and not path.is_symlink(), 'WRITER_path_not_redirected')
                descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_CLOEXEC)
                info = os.fstat(descriptor)
                self.opened.append((path, descriptor, binding, info.st_atime_ns))
                scope.require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                              and lock_metadata(path, info) == binding
                              and lock_metadata(path, path.lstat()) == binding, 'exact_original_WRITER_identity_metadata')
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.verify_held()
            self.snapshot = self.scanner(sorted(self.paths))
            scope.validate_writer_scan(self.snapshot)
            self.verify_held()
            return self
        except BaseException:
            self.close()
            raise

    def verify_held(self):
        scope.require(len(self.opened) == 4, 'all_four_original_WRITER_locks_held')
        for path, descriptor, binding, atime in self.opened:
            current = path.lstat()
            bound = os.fstat(descriptor)
            scope.require(path.resolve() == path and not path.is_symlink()
                          and lock_metadata(path, current) == binding
                          and lock_metadata(path, bound) == binding
                          and current.st_atime_ns == bound.st_atime_ns == atime,
                          'WRITER_identity_or_metadata_changed_while_held')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def check(self, paths):
        scope.require(self.snapshot is not None and set(paths).issubset(self.paths), 'exact_batch_under_writer_guard')
        self.verify_held()
        return dict(self.snapshot, reused_under_held_original_WRITER_locks=True,
                    writer_guard_policy=POLICY, writer_locks_sha256=LOCKS_SHA256)

    def close(self):
        while self.opened:
            unused_path, descriptor, unused_binding, unused_atime = self.opened.pop()
            os.close(descriptor)

    def __exit__(self, kind, value, traceback):
        try:
            self.verify_held()
        finally:
            self.close()
