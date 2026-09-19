"""Observe the unmodified reader on a live journal, without acquiring its writer lock."""

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time


def observe(request_path, expected_sha256):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU_only_observer_required')
    content = Path(request_path).read_bytes()
    if hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ValueError('exact_historical_checkpoint_probe_request')
    request = json.loads(content)
    source = Path(request['source'])
    plan = request['plan']
    candidate = request['candidate']
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    from gpu import r232_recovery as recovery
    from gpu.checkpoint_tail_runtime import scan
    recovery.frozen.INITIAL = native.read(recovery.ROOTS[1] / 'raw/checkpoints/initial/COMMIT.json')
    root = Path(plan['root']) / 'stream'
    sidecars = ([dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)]
        if (root / 'correction_ledger.json').exists() else [])
    selection = dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=str(root),
        journal_id=candidate['journal_id'], complete_index=candidate['complete_index'],
        complete_sha256=candidate['complete_sha256'], life_id=plan['think_act_learn']['trial_id'],
        max_tail_records=2048, max_tail_bytes=1024**3, sidecars=sidecars,
        persist_complete_anchors=False)
    base = recovery.FrozenJournal if plan['physical'] == 1 else recovery.LearnerJournal
    journal = object.__new__(base)
    journal.root = root
    journal.inbox = root / 'inbox'
    journal._owner = os.getpid()
    journal._mutex = threading.RLock()
    journal._fds = []
    journal._closed = journal._failed = False
    started = time.monotonic()
    try:
        journal._root_fd = journal._open(root, os.O_RDONLY | os.O_DIRECTORY)
        journal._lock_fd = journal._open('WRITER.lock', os.O_RDONLY, journal._root_fd)
        journal._records_fd = journal._open('records', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._inbox_fd = journal._open('inbox', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._manifest = journal._read_json(journal._root_fd, 'JOURNAL.json')
        state = scan(journal, selection)
        receipt = dict(journal.checkpoint_tail_receipt,
            status='REAL_LIVE_JOURNAL_READER_OBSERVATION_NOT_HANDOFF_PROOF',
            observed_unix=time.time(), elapsed_seconds=time.monotonic() - started,
            pending_request=state['request'] is not None,
            pending_response=state['response'] is not None,
            pending_sleep=state['sleep_request'] is not None,
            read_only=True, writer_lock_acquired=False, native_signals=[],
            source=str(source), root=str(root), live_boundary_reserved=False,
            authorizes_native_handoff=False, journal_writes=0)
        return receipt
    except (ValueError, OSError) as error:
        return dict(status='LIVE_READER_OBSERVATION_REFUSED_NO_NATIVE_ACTION',
            error_type=type(error).__name__, error=str(error),
            observed_unix=time.time(), elapsed_seconds=time.monotonic() - started,
            source=str(source), root=str(root), native_signals=[],
            writer_lock_acquired=False, journal_writes=0, authorizes_native_handoff=False)
    finally:
        journal.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    options = parser.parse_args()
    with contextlib.redirect_stdout(sys.stderr):
        result = observe(options.request, options.request_sha256)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
