"""Receiver-side read-only source and captured-adapter verification."""

import hashlib
import json
from pathlib import Path
import time


BASE = Path('/localhome/local-rohing')
ROOTS = (
    BASE / 'orch_post_recovery_c2_age_eval_20260918/base',
    BASE / 'orch_post_recovery_c2_age_eval_20260918/c2sleep51',
    BASE / 'orch_post_recovery_c2_age_eval_20260918/c2sleep117',
    BASE / 'orch_post_recovery_age_20260918_attempt3/learner24',
    BASE / 'orch_post_recovery_age_20260918_attempt3/frozen24',
)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(root):
    manifest = read(root / 'SOURCE_MANIFEST.json')
    source = root / 'source'
    failures = []
    for relative, expected in manifest.items():
        path = source / relative
        if path.is_symlink() or not path.resolve().is_relative_to(source) or sha(path) != expected:
            failures.append(relative)
    capture = root / 'sources/CAPTURE.json'
    copy_files = []
    if capture.is_file():
        for entry in read(capture)['sources']:
            directory = root / 'sources' / entry['source_relative']
            for relative, expected in entry['copy_files'].items():
                path = directory / relative
                valid = (not path.is_symlink() and path.resolve().is_relative_to(directory)
                    and sha(path) == expected['sha256'])
                copy_files.append(dict(relative=str(path.relative_to(root)), matched=valid))
    return dict(root=str(root), source_manifest_sha256=sha(root / 'SOURCE_MANIFEST.json'),
        checked_source_files=len(manifest), source_failures=failures,
        capture_files=copy_files, verified=not failures and all(row['matched'] for row in copy_files))


def main():
    result = dict(observed_unix=time.time(), no_writes=True, no_gpu_calls=True, rows=[])
    for root in ROOTS:
        try:
            result['rows'].append(verify(root))
        except (OSError, ValueError, KeyError) as error:
            result['rows'].append(dict(root=str(root), verified=False,
                error_type=type(error).__name__, error=str(error)))
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
