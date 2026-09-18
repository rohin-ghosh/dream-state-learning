"""Pin an existing parent-owned verified cursor; no learner state is written."""

import hashlib
import json
from pathlib import Path
import time


def pin(root):
    target = root / 'r210'
    marker = target / 'R230_BOOTSTRAP_CURSOR.json'
    if marker.exists():
        return json.loads(marker.read_bytes())
    paths = sorted((target / 'parent_cursor').glob('*.json'),
                   key=lambda path: path.stat().st_mtime, reverse=True)[:400]
    candidates = []
    for path in paths:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16 * 1024 * 1024:
            continue
        raw = path.read_bytes()
        state = json.loads(raw)
        if state.get('root') != str((root / 'life').resolve()):
            continue
        if state.get('schema') != 'R166_VERIFIED_TRAIN_CURSOR_V1':
            continue
        candidates.append((state['next_index'], path, hashlib.sha256(raw).hexdigest(), state['journal_id']))
    if not candidates:
        raise ValueError('no_verified_parent_cursor')
    frontier, path, checksum, journal = max(candidates, key=lambda item: item[0])
    document = dict(schema='R230_EXISTING_PARENT_CURSOR_PIN_V1',
        reference=dict(path=str(path), sha256=checksum), next_index=frontier,
        journal_id=journal, pinned_unix=time.time(), learner_signals=[],
        reason='Reuse verified history instead of genesis bootstrap; boundary and chain rechecked by stored_poll.')
    with marker.open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)
    return document


if __name__ == '__main__':
    base = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET')
    results = {}
    for physical in (2, 3, 5, 6):
        root = base / ('MATH_C' if physical == 6 else 'SCALE_physical' + str(physical))
        results[str(physical)] = pin(root)
    print(json.dumps(results, sort_keys=True, indent=2))
