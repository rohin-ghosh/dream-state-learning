"""Bounded retirement-manifest and readable-FD census; no mutations."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
NAMES = ('r225_siege_retirement_20260918', 'r233_retirement_20260918T1144Z',
    'r224_challenger_retirement_20260918')


def main():
    documents = []
    skipped = []
    for name in NAMES:
        origin = ROOT / name
        pending = [(origin, 0)]
        while pending:
            directory, depth = pending.pop()
            for path in directory.iterdir():
                metadata = path.lstat()
                if stat.S_ISDIR(metadata.st_mode) and depth < 2:
                    pending.append((path, depth + 1))
                if not stat.S_ISREG(metadata.st_mode) or not path.name.endswith('.json') \
                        or not any(token in path.name for token in ('MANIFEST', 'RETIR', 'RECEIPT')):
                    continue
                if metadata.st_size > 4 * 1024**2:
                    skipped.append(dict(path=str(path), reason='bounded_4MiB_limit'))
                    continue
                descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME)
                with os.fdopen(descriptor, 'rb') as source:
                    raw = source.read()
                try:
                    value = json.loads(raw)
                except ValueError:
                    skipped.append(dict(path=str(path), reason='not_complete_JSON'))
                    continue
                counts = Counter()
                nodes = [value]
                while nodes:
                    item = nodes.pop()
                    if isinstance(item, dict):
                        counts.update(item.keys())
                        nodes.extend(item.values())
                    elif isinstance(item, list):
                        nodes.extend(item)
                identity = {key: count for key, count in counts.items()
                    if any(term in key.lower() for term in ('inode', 'st_ino', 'st_dev', 'ctime', 'nlink'))}
                hashes = {key: count for key, count in counts.items()
                    if any(term in key.lower() for term in ('sha256', 'sha', 'bytes', 'size'))}
                documents.append(dict(path=str(path), size=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                    top_level_keys=list(value) if isinstance(value, dict) else [],
                    identity_field_counts=identity, hash_size_field_counts=hashes))
    readers = []
    writers = []
    inaccessible = []
    processes = 0
    roots = [str(ROOT / name) + '/' for name in NAMES]
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            processes += 1
            for descriptor in (process / 'fd').iterdir():
                target = os.readlink(descriptor)
                if not any(target.startswith(prefix) for prefix in roots):
                    continue
                fields = dict(line.split(':', 1) for line in
                    (process / 'fdinfo' / descriptor.name).read_text().splitlines() if ':' in line)
                mode = int(fields['flags'].strip(), 8) & os.O_ACCMODE
                item = dict(pid=int(process.name), fd=int(descriptor.name), path=target, access_mode=mode)
                (readers if mode == os.O_RDONLY else writers).append(item)
        except (OSError, ValueError, KeyError) as error:
            inaccessible.append(dict(pid=process.name, error_type=type(error).__name__))
    print(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(), read_only=True,
        scope='only three reviewed retired directories; provenance depth<=3, file<=4MiB; readable owner FDs',
        documents=documents, skipped=skipped, readable_retired_FD_readers=readers,
        readable_retired_FD_writers=writers, owner_processes_examined=processes,
        inaccessible_or_exited_processes=inaccessible,
        universal_nonuse_or_absence_of_inode_dependencies_not_claimed=True), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
