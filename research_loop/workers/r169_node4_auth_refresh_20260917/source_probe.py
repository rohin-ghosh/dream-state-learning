"""Bounded read-only exact source search; never imports or extracts candidates."""

import hashlib
import json
import os
from pathlib import Path
import socket
import tarfile
import time


TARGETS = {
    '26f2ce2ec6d6a986e9133acdbfa0ca80122f23181cb82186913050d78b1d4105',
    '9255cadf1355a5eb6e7b69cd086eaca28a69baad480160458aa9bd4adf22e2f9',
}


def relevant(name):
    return name.endswith('.py') and any(part in Path(name).name.lower()
        for part in ('programme_parent', 'node4_parent', 'parent.py'))


def observe(roots, archive_budget=2 * 1024**3, file_limit=250000):
    sources, archives, errors, matches = [], [], [], []
    files_seen = 0
    deadline = time.monotonic() + 100
    candidates = []
    exhausted = False
    for root in roots:
        for directory, subdirectories, names in os.walk(root, followlinks=False):
            subdirectories[:] = [name for name in subdirectories if name not in
                ('.git', '.cache', 'node_modules', 'site-packages', '__pycache__', '.venv')]
            for name in names:
                files_seen += 1
                if files_seen > file_limit or time.monotonic() > deadline:
                    exhausted = True
                    break
                path = Path(directory) / name
                try:
                    if path.is_symlink():
                        continue
                    if relevant(name) and path.stat().st_size <= 1024**2:
                        row = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                        sources.append(row)
                        if row['sha256'] in TARGETS:
                            matches.append(row)
                    elif name.endswith(('.tar', '.tar.gz', '.tgz')) and path.stat().st_size <= 256 * 1024**2:
                        candidates.append(path)
                except OSError as error:
                    errors.append(dict(path=str(path), type=type(error).__name__))
            if exhausted:
                break
        if exhausted:
            break
    candidates.sort(key=lambda path: (not any(part in str(path) for part in
        ('node4', 'r136', 'r137', 'r138', 'r133')), path.stat().st_size))
    bytes_scanned = 0
    for path in candidates:
        size = path.stat().st_size
        if bytes_scanned + size > archive_budget or time.monotonic() > deadline:
            exhausted = True
            break
        bytes_scanned += size
        row = dict(path=str(path), bytes=size, members=0, source_members=[])
        try:
            with tarfile.open(path, mode='r|*') as archive:
                for member in archive:
                    row['members'] += 1
                    if row['members'] > 50000 or time.monotonic() > deadline:
                        row['truncated'] = True
                        break
                    if member.isfile() and relevant(member.name) and member.size <= 1024**2:
                        content = archive.extractfile(member).read()
                        source = dict(archive=str(path), member=member.name,
                                      sha256=hashlib.sha256(content).hexdigest())
                        row['source_members'].append(source)
                        if source['sha256'] in TARGETS:
                            matches.append(source)
            archives.append(row)
        except (OSError, tarfile.TarError) as error:
            errors.append(dict(path=str(path), type=type(error).__name__))
    return dict(hostname=socket.gethostname(), observed_unix=time.time(), roots=roots,
                files_seen=files_seen, sources=sources, archives=archives, matches=matches,
                errors=errors, bounded_search_not_exhaustive=exhausted,
                archive_candidates=len(candidates), compressed_bytes_scanned=bytes_scanned,
                no_source_mutation=True, no_import_or_extraction=True, no_signals=True)


if __name__ == '__main__':
    roots = ['/localhome/local-rohing', '/tmp'] if Path('/localhome/local-rohing').is_dir() else [
        '/tmp', '/data/home/rohing/.tmp', '/data/home/rohing/dream-state-orch/research_notes/analysis']
    print(json.dumps(observe(roots), sort_keys=True))
