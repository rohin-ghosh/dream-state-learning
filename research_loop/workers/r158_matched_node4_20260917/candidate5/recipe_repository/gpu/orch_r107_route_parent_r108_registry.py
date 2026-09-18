"""Read registered cohort metadata only; emit IDs and hashes, never raw calls."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import time


def collect(roots):
    identifiers, files = set(), {}
    skipped = {'native', 'source', '.git', '.cache', 'venv', '__pycache__',
               'node_modules', 'raw', 'raw_archive', 'gpu_artifacts_local'}
    for root in roots:
        if not root.exists():
            continue
        for directory, children, names in os.walk(root):
            children[:] = [name for name in children if name not in skipped
                           and not name.startswith(('CALL_', 'REQUEST_', 'GUIDED_SLEEP_'))]
            for name in names:
                if not name.endswith('.json') or not any(
                        word in name.upper() for word in ('COHORT', 'ROSTER', 'REGISTRY', 'EXCLUSIONS', 'TASKS')):
                    continue
                path = Path(directory) / name
                if path.is_symlink() or path.stat().st_size > 8_000_000:
                    continue
                content = path.read_bytes()
                text = content.decode('utf-8')
                json.loads(text)
                identifiers.update(re.findall(r'\b[NEPR]_[A-Z0-9]{10}\b', text))
                files[str(path)] = hashlib.sha256(content).hexdigest()
    return dict(identifiers=sorted(identifiers), source_files=files,
                observed_unix=time.time(), raw_embedded=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('roots', nargs='+', type=Path)
    args = parser.parse_args()
    print(json.dumps(collect(args.roots), sort_keys=True))
