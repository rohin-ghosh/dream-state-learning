"""Verify this observer and emit only local bounded source-reference receipts."""

import fcntl
import json
import os
import time
from datetime import datetime
from pathlib import Path

import collector


HERE = Path(__file__).resolve().parent


def finish():
    state = json.loads((HERE / 'operator/PROCESS.json').read_text())
    current = collector.process(state['pid'])
    if not state.get('boot_id') or not collector.same_process(current, state):
        raise ValueError('observer_identity_not_alive')
    if state['completed_collections'] < 1 or state['phase'] != 'SCHEDULED':
        raise ValueError('completed_cut_and_future_schedule_required')
    if datetime.fromisoformat(state['next_cut_utc']).timestamp() <= time.time():
        raise ValueError('future_schedule_required')
    config = json.loads((HERE / 'private/CONFIG.json').read_text())
    if state['config_sha256'] != collector.sha(HERE / 'private/CONFIG.json'):
        raise ValueError('exact_observed_config_required')
    command = Path('/proc', str(state['pid']), 'cmdline').read_bytes().split(b'\0')
    if str(HERE / 'collector.py').encode() not in command:
        raise ValueError('exact_collector_command_required')
    lock_proofs = []
    for label, path in (
        ('original', collector.ORIGINAL / 'operator/SINGLE_READER.lock'),
        ('replacement', HERE / 'operator/SINGLE_READER.lock'),
    ):
        with path.open('r') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                information = os.fstat(handle.fileno())
                inode_key = f'{os.major(information.st_dev):02x}:{os.minor(information.st_dev):02x}:{information.st_ino}'
                owned = any(parts[1:4] == ['FLOCK', 'ADVISORY', 'WRITE'] and parts[4] == str(state['pid']) and parts[5] == inode_key
                    for line in Path('/proc/locks').read_text().splitlines() if len(parts := line.split()) >= 6)
                if not owned:
                    raise ValueError('exact_observer_must_own_lock')
                lock_proofs.append(dict(label=label, exclusive_lock_held=True, owner_pid=state['pid'], inode_key=inode_key))
            else:
                raise ValueError('collector_lock_not_held')
    caption = collector.process(config['caption_collector']['pid'])
    cut = json.loads((HERE / 'public/CURRENT.json').read_text())
    if cut['observed_utc'] != state['last_cut_utc'] or not collector.same_process(current, cut['collector_process']):
        raise ValueError('completed_cut_must_belong_to_this_process')
    collector.save(HERE / 'public/VERIFIED_HANDLE.json', dict(verified_utc=collector.utc(time.time()),
        process=current, completed_collections=state['completed_collections'],
        cut_utc=cut['observed_utc'], next_cut_utc=state['next_cut_utc'], locks=lock_proofs,
        original_process_absent=collector.process(config['old_process']['pid']) is None,
        caption_observation=dict(expected=config['caption_collector'], observed=caption, actions=0), read_only=True))
    privacy = collector.load('isolated_original_privacy', HERE / 'contract/publish.py')
    for path in sorted((HERE / 'public').rglob('*')):
        if path.is_file():
            privacy.safe_public(path)
    files = [path for path in HERE.rglob('*') if path.is_file() and
        not set(path.relative_to(HERE).parts) & {'private', 'operator', '__pycache__', '.pytest_cache'} and
        path.name != 'ARTIFACTS_SHA256.json']
    collector.save(HERE / 'public/ARTIFACTS_SHA256.json', dict(created_utc=collector.utc(time.time()),
        hashes={str(path.relative_to(HERE)): collector.sha(path) for path in sorted(files)},
        volatile_files='SERVICE, CURRENT, STATUS_LATEST and REVIEW_QUEUE update at subsequent hourly cuts; immutable dated cut retained.',
        git_publication=False, raw_content_published=False))
    print(json.dumps(dict(actual_bound_sources=cut['actual_current_bound_sources'], process=current,
        cut_utc=cut['observed_utc'], next_cut_utc=state['next_cut_utc'], public_privacy_scan='PASS')))


if __name__ == '__main__':
    finish()
