"""P3 parent transport pinned to the authorized saved-boundary continuation."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time

import p3_endpoint as previous


END_UNIX = 1790359200
TARGET = previous.ROOT / 'r233_lease_continuation'
SOURCE = TARGET / 'source'
BINDING = TARGET / 'control/LIVE_BINDING.json'


def verify_bound(binding, guard, lease, now):
    previous.require(binding['hard_end_unix'] == guard['hard_end_unix'] ==
        lease['hard_end_unix'] == END_UNIX, 'exact_authorized_node4_bound')
    previous.require(now < END_UNIX and lease['lease_end_unix'] >= END_UNIX + 21600,
        'inside_authorized_lease_margin')
    previous.require(binding['journal_id'] == previous.JOURNAL_ID and
        binding['source'] == str(SOURCE) and binding['pid'] != previous.PID,
        'same_journal_new_continuation_incarnation')


def configure():
    sys.path.insert(0, str(previous.BASE / 'MATH_C'))
    import r210_parent_endpoint as transport
    import math_c
    previous.require(hashlib.sha256(socket.gethostname().encode()).hexdigest() ==
        math_c.HOST_SHA and os.getuid() == 2524, 'same_node4_user')
    binding = previous.json.loads(BINDING.read_bytes())
    guard_path = TARGET / 'control/GUARD.json'
    guard = transport.read(guard_path)
    lease = transport.read(guard['lease_path'])
    verify_bound(binding, guard, lease, time.time())
    previous.require(transport.sha(guard_path) == binding['guard_sha256'] and
        transport.sha(guard['lease_path']) == guard['lease_sha256'], 'continuation_guard_and_lease')
    previous.require(transport.sha(guard['plan_path']) == guard['plan_sha256'], 'continuation_plan')
    sys.path.insert(0, str(SOURCE))
    transport.load('gpu.orch_r127_pilot_transcript', transport.HOME / 'read_transcript.py')
    previous.PID = binding['pid']
    previous.START_TICKS = binding['start_ticks']
    previous.LOADED_INDEX = binding['loaded_index']
    previous.LOADED_SHA = binding['loaded_sha256']
    previous.incarnation(SOURCE)
    return transport, binding


def bind_recovery_reducer(snapshot, receipt):
    original = snapshot._reduce

    def reduce(state, record):
        if record['kind'] == 'R233_P3_RECOVERED_BOUNDARY':
            previous.require(record['index'] == receipt['old_head_index'] + 1 and
                record['previous_sha256'] == receipt['old_head_sha256'] and
                record['document']['state']['sha256'] == receipt['saved_state_sha256'],
                'verified_P3_boundary_recovery_for_parent_cursor')
            state['pending'] = state['response'] = None
            return
        return original(state, record)

    snapshot._reduce = reduce


def main():
    request = json.loads(sys.stdin.read())
    previous.check_request(request)
    transport, binding = configure()
    target = previous.ROOT / 'r210'
    if request['op'] == 'poll':
        snapshot = transport.load('r233_p3_continued_snapshot', transport.HOME / 'read_snapshot.py')
        bind_recovery_reducer(snapshot, transport.read(TARGET / 'control/RECOVERY.json'))
        reference = transport.resume_verified_cursor(previous.ROOT, target, request.get('reference'))
        result = snapshot.stored_poll(previous.ROOT / 'life', target / 'parent_cursor', reference)
        opening = transport.read(target / 'PARENT_OPENING.json')['publication']
        result.update(receipts=[], opening_published=True,
            opening_rendered=result['snapshot']['delivered'].get(opening['id']), console_replied=None,
            pinned_loaded_index=binding['loaded_index'], pinned_loaded_sha256=binding['loaded_sha256'])
    else:
        message = request['message']
        previous.require(isinstance(message, str) and len(message.split()) <= 160
            and len(message.encode()) <= 4096, 'bounded_Astra_publication')
        with (target / 'PARENT_PUBLICATION.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            previous.require(not (target / 'R211_ISOLATION.json').exists(), 'no_isolation_publication')
            previous.incarnation(SOURCE)
            from gpu.orch_r127_pilot_console import publish_parent
            result = publish_parent(str(previous.ROOT / 'life'), 'Astra', message)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
