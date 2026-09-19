"""Measure a historical COMPLETE prefix without replaying later live cycles."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time


def probe(request_path, request_sha256):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU_only_observer_required')
    raw = Path(request_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != request_sha256:
        raise ValueError('exact_historical_checkpoint_request')
    request = json.loads(raw)
    candidate = request['candidate']
    plan = request['plan']
    sys.path.insert(0, request['source'])
    from gpu import orch_r125_continual_native as native
    from gpu.checkpoint_tail_runtime import hash_record, _decoded_record
    from gpu.orch_r125_stream_journal import _digest
    if plan['think_act_learn']['trial_id'] == 'C2_R216_current_conversation_maintenance':
        native.require(plan['physical'] == 1 and candidate['checkpoint']['optimizer_steps'] > 0,
                       'C2_is_learned_not_frozen_pair')
        from gpu.orch_r125_stream_journal import StreamJournal
        base = StreamJournal
    else:
        from gpu import r232_recovery as recovery
        recovery.frozen.INITIAL = native.read(recovery.ROOTS[1] / 'raw/checkpoints/initial/COMMIT.json')
        base = recovery.FrozenJournal if plan['physical'] == 1 else recovery.LearnerJournal
    journal = object.__new__(base)
    journal.root = Path(plan['root']) / 'stream'
    journal.inbox = journal.root / 'inbox'
    journal._owner = os.getpid()
    journal._mutex = threading.RLock()
    journal._fds = []
    journal._closed = journal._failed = False
    started = time.monotonic()
    try:
        journal._root_fd = journal._open(journal.root, os.O_RDONLY | os.O_DIRECTORY)
        journal._lock_fd = journal._open('WRITER.lock', os.O_RDONLY, journal._root_fd)
        journal._records_fd = journal._open('records', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._inbox_fd = journal._open('inbox', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._manifest = journal._read_json(journal._root_fd, 'JOURNAL.json')
        native.require(journal._manifest['journal_id'] == candidate['journal_id'], 'same_journal')
        previous = _digest(journal._manifest)
        inbox = {}
        headers = {}
        raw_bytes = 0
        for index in range(candidate['learn_index'] + 1):
            header, hashed = hash_record(journal, index)
            native.require(header['previous_sha256'] == previous, 'historical_prefix_integrity')
            previous = header['sha256']
            raw_bytes += hashed['bytes']
            if header['kind'] == 'INBOX' and index <= candidate['complete_index']:
                record = _decoded_record(journal, header)
                journal._advance(dict(inbox=inbox), 'INBOX', record['document'])
            if index >= candidate['complete_index']:
                headers[index] = header
        prefix_seconds = time.monotonic() - started
        anchor = headers[candidate['complete_index']]
        native.require(anchor['kind'] == 'SLEEP_COMPLETE'
                       and anchor['sha256'] == candidate['complete_sha256'], 'exact_complete')
        complete = _decoded_record(journal, anchor)
        checkpoint = journal._checkpoint(complete['document']['resume_state'])
        native.require(checkpoint['expected_sha256'] == candidate['resume_state']['sha256'],
                       'same_saved_working_state')
        state = dict(index=candidate['complete_index'] + 1, previous=anchor['sha256'],
                     latest=checkpoint, request=None, response=None, sleep_request=None, inbox=inbox)
        for index in range(candidate['complete_index'] + 1, candidate['learn_index'] + 1):
            record = _decoded_record(journal, headers[index])
            native.require(record['kind'] in ('INBOX', 'R184_LEARN_COMPLETE'),
                           'only_COMPLETE_boundary_tail')
            journal._advance(state, record['kind'], record['document'])
            state['index'], state['previous'] = index + 1, record['sha256']
        native.require(headers[candidate['learn_index']]['kind'] == 'R184_LEARN_COMPLETE',
                       'matched_LEARN_required')
        native.require(all(state[key] is None for key in ('request', 'response', 'sleep_request')),
                       'resolved_historical_boundary')
        from organism_v6.orch_r124_train_history import TrainHistory
        history_start = time.monotonic()
        saved_history = candidate['resume_state']['state']['history']
        restored_history = TrainHistory.restore(saved_history,
            expected_sha256=saved_history['state_sha256'])
        native.require(restored_history.checkpoint() == saved_history, 'identical_actual_history_checkpoint')
        history_restore_seconds = time.monotonic() - history_start
        return dict(status='HISTORICAL_COMPLETE_COST_NOT_LIVE_HANDOFF_VALIDATION',
                    observed_unix=time.time(), elapsed_seconds=time.monotonic() - started,
                    prefix_hash_seconds=prefix_seconds, raw_bytes_hashed=raw_bytes,
                    complete_index=candidate['complete_index'], learn_index=candidate['learn_index'],
                    tail_records=candidate['learn_index'] - candidate['complete_index'],
                    source=request['source'], checkpoint_state_sha256=checkpoint['expected_sha256'],
                    live_head_ignored=True, current_sidecars_verified=False,
                    full_scan_called=False, writer_lock_acquired=False, native_signals=[],
                    checkpoint_history_byte_equivalent=True, history_restore_seconds=history_restore_seconds,
                    journal_writes=0, no_GPU_calls=True, authorizes_native_handoff=False)
    finally:
        journal.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    parser.add_argument('--request-sha256', required=True)
    options = parser.parse_args()
    print(json.dumps(probe(options.request, options.request_sha256), sort_keys=True))
