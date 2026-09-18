"""Refresh only P3's operator-owned bootstrap reference; preserve its old pin."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time


BASE = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET')
ROOT = BASE / 'SCALE_physical3'
TARGET = ROOT / 'r210'


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_cursor(store, life, journal_id, minimum):
    candidates = []
    paths = sorted(store.glob('*.json'), key=lambda path: path.stat().st_mtime, reverse=True)[:600]
    for path in paths:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16*1024*1024:
            continue
        raw = path.read_bytes()
        state = json.loads(raw)
        if state.get('schema') != 'R166_VERIFIED_TRAIN_CURSOR_V1' or state.get('root') != str(life.resolve()):
            continue
        if state.get('journal_id') != journal_id or type(state.get('next_index')) is not int:
            continue
        if state['next_index'] >= minimum:
            candidates.append((state['next_index'], path, hashlib.sha256(raw).hexdigest()))
    if not candidates:
        raise ValueError('existing_parent_owned_forward_cursor_required')
    return max(candidates, key=lambda item: item[0])


def main():
    sys.path.insert(0, str(BASE / 'MATH_C'))
    import r210_parent_endpoint as endpoint
    configured_root, configured_target, unused_source = endpoint.configure(3)
    if configured_root != ROOT or configured_target != TARGET:
        raise ValueError('exact_P3_binding_required')
    snapshot = endpoint.load('r233_existing_p3_snapshot', endpoint.HOME / 'read_snapshot.py')
    marker = TARGET / 'R230_BOOTSTRAP_CURSOR.json'
    old_bytes = marker.read_bytes()
    old = json.loads(old_bytes)
    life = ROOT / 'life'
    journal = json.loads((life / 'stream/JOURNAL.json').read_text())['journal_id']
    if old['journal_id'] != journal:
        raise ValueError('same_live_journal_required')
    frontier, selected_path, selected_sha = select_cursor(TARGET / 'parent_cursor', life, journal, old['next_index'])
    result = snapshot.stored_poll(life, TARGET / 'parent_cursor', dict(path=str(selected_path), sha256=selected_sha))
    new_state = json.loads(Path(result['reference']['path']).read_text())
    if new_state['next_index'] < frontier or new_state['journal_id'] != journal:
        raise ValueError('verified_forward_only')
    receipt_directory = TARGET / 'r233_cursor_refresh'
    receipt_directory.mkdir(exist_ok=True)
    preservation = receipt_directory / (hashlib.sha256(old_bytes).hexdigest() + '.json')
    if not preservation.exists():
        with preservation.open('xb') as stream:
            stream.write(old_bytes)
            stream.flush()
            os.fsync(stream.fileno())
    replacement = dict(old, reference=result['reference'], next_index=new_state['next_index'],
        pinned_unix=time.time(), policy='R233_P3_FORWARD_VERIFIED_CURSOR_REFRESH_V1',
        prior_marker_sha256=hashlib.sha256(old_bytes).hexdigest(), learner_signals=[])
    if marker.read_bytes() != old_bytes:
        raise ValueError('marker_changed_no_overwrite')
    temporary = receipt_directory / 'marker.next'
    with temporary.open('w') as stream:
        json.dump(replacement, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, marker)
    print(json.dumps(dict(policy=replacement['policy'], observed_unix=time.time(),
        prior_frontier=old['next_index'], selected_existing_frontier=frontier,
        new_frontier=new_state['next_index'], caught_up=result['snapshot']['caught_up'],
        journal_id=journal, preserved_marker_sha256=hashlib.sha256(old_bytes).hexdigest(),
        selected_cursor_sha256=selected_sha, verified_cursor_sha256=result['reference']['sha256'],
        new_marker_sha256=checksum(marker), learner_signals=[], parent_signals=[]), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
