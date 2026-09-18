"""Read-only, bounded final node3 inbox transport after old parent retirement."""

import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tarfile
import time


def capture(root, stopped_pid):
    if Path('/proc', str(stopped_pid)).exists():
        raise ValueError('original_native_still_present')
    directory = Path(root) / 'stream/inbox'
    charged = 0
    files = {}
    signatures = {}
    for path in sorted(directory.iterdir()):
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > 2 * 1024**2:
            raise ValueError('regular_bounded_inbox_file_required')
        charged += before.st_size
        if charged > 64 * 1024**2:
            raise ValueError('inbox_read_budget')
        with path.open('rb') as stream:
            raw = stream.read(before.st_size + 1)
        after = path.lstat()
        signature = lambda entry: (entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns)
        if len(raw) != before.st_size or signature(before) != signature(after):
            raise ValueError('inbox_changed_during_capture')
        files[path.name] = raw
        signatures[path.name] = signature(after)
    if {path.name for path in directory.iterdir()} != set(files):
        raise ValueError('inbox_members_changed_during_capture')
    for name, signature in signatures.items():
        current = (directory / name).lstat()
        if (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) != signature:
            raise ValueError('inbox_changed_before_publication')
    manifest = dict(source_root=root, observed_unix=time.time(), original_native_pid_absent=stopped_pid,
        operational_bytes_read=charged, files={name:dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            for name, raw in files.items()}, read_only=True, no_signals=True)
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w|gz') as archive:
        for name, raw in [('INBOX_DELTA.json', json.dumps(manifest, sort_keys=True).encode()),
                          *[('inbox/' + name, raw) for name, raw in files.items()]]:
            member = tarfile.TarInfo(name)
            member.size, member.mode, member.mtime = len(raw), 0o400, int(time.time())
            archive.addfile(member, io.BytesIO(raw))


if __name__ == '__main__':
    capture(sys.argv[1], int(sys.argv[2]))
