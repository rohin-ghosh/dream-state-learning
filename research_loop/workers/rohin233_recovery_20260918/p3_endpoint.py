"""P3-only incremental verified parent transport, pinned to its live incarnation."""

import fcntl
import hashlib
import json
from pathlib import Path
import sys
import time


BASE = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET')
ROOT = BASE / 'SCALE_physical3'
LOADED_INDEX = 369
LOADED_SHA = 'c33db8f7d8d7c9d4b918d0235ad1127d3dbc959b51e4fd5de163b53ac4b79c20'
JOURNAL_ID = '0727d448bca644bfa64f1a1f65c1f21f'
PID = 237705
START_TICKS = '27878033'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def check_request(request):
    require(request.get('physical') == 3, 'P3_only')
    require(request.get('op') in ('poll', 'publish'), 'existing_parent_only')


def incarnation(source):
    life = ROOT / 'life'
    journal = json.loads((life / 'stream/JOURNAL.json').read_text())
    require(journal['journal_id'] == JOURNAL_ID, 'same_live_journal')
    loaded = json.loads((life / f'stream/records/{LOADED_INDEX:020d}.json').read_text())
    content = {key: value for key, value in loaded.items() if key != 'sha256'}
    from gpu.orch_r125_stream_journal import _digest
    require(loaded['sha256'] == LOADED_SHA and _digest(content) == LOADED_SHA,
            'pinned_actual_LOADED_hash')
    require(loaded['kind'] == 'LOADED' and loaded['document']['pid'] == PID,
            'pinned_actual_LOADED_identity')
    process = Path('/proc') / str(PID)
    require(process.joinpath('cwd').resolve() == source, 'same_live_source')
    require(process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[19]
            == START_TICKS, 'same_live_process_start')
    return loaded


def main():
    request = json.loads(sys.stdin.read())
    check_request(request)
    sys.path.insert(0, str(BASE / 'MATH_C'))
    import r210_parent_endpoint as predecessor
    predecessor.host()
    root, target, source = predecessor.configure(3)
    require(root == ROOT, 'exact_P3_root')
    loaded = incarnation(source)
    if request['op'] == 'poll':
        snapshot = predecessor.load('p3_incremental_snapshot', predecessor.HOME / 'read_snapshot.py')
        reference = predecessor.resume_verified_cursor(root, target, request.get('reference'))
        result = snapshot.stored_poll(root / 'life', target / 'parent_cursor', reference)
        opening = predecessor.read(target / 'PARENT_OPENING.json')['publication']
        delivered = result['snapshot']['delivered'].get(opening['id'])
        result.update(receipts=[], opening_published=True, opening_rendered=delivered,
                      console_replied=None,
                      receipt_scope='VERIFIED_SNAPSHOT_NOT_FULL_HISTORICAL_RECEIPT_REPLAY',
                      pinned_loaded_index=loaded['index'], pinned_loaded_sha256=LOADED_SHA)
    else:
        message = request['message']
        require(time.time() < predecessor.WALL and isinstance(message, str)
                and len(message.split()) <= 160 and len(message.encode()) <= 4096,
                'bounded_Astra_publication')
        with (target / 'PARENT_PUBLICATION.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            require(not (target / 'R211_ISOLATION.json').exists(), 'no_isolation_publication')
            require(loaded['index'] > predecessor.read(target / 'PRESERVED.json')['last_record_index'],
                    'same_current_R210_incarnation')
            incarnation(source)
            from gpu.orch_r127_pilot_console import publish_parent
            result = publish_parent(str(root / 'life'), 'Astra', message)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
