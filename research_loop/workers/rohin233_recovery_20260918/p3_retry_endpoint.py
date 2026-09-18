"""Retry-only CPU parent endpoint on the original journal and publisher lock."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time

import p3_endpoint as previous
import p3_retry_observe as observer


def verify_bound(binding, guard, lease, now):
    observer.require(binding['hard_end_unix'] == guard['hard_end_unix'] == lease['hard_end_unix'] == observer.END_UNIX
        and now < observer.END_UNIX and lease['lease_end_unix'] >= observer.END_UNIX + 21600,
        'exact_retry_authorized_wall_and_margin')
    observer.require(binding['source'] == str(observer.SOURCE) and binding['journal_id'] == observer.JOURNAL_ID
        and binding['pid'] not in (237705, 598987) and binding['loaded_index'] > 5299,
        'same_journal_only_new_retry_incarnation')


def verify_live(binding):
    observer.require(time.time() < observer.END_UNIX
        and observer.same_process(observer.process(binding['pid']), binding),
        'exact_retry_native_still_alive_inside_wall')


def configure():
    sys.path.insert(0, str(previous.BASE / 'MATH_C'))
    import r210_parent_endpoint as transport
    import math_c
    observer.require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == math_c.HOST_SHA
        and os.getuid() == 2524, 'same_node4_user')
    binding = observer.read(observer.BINDING)
    guard_path = observer.CONTROL / 'GUARD.json'
    guard = observer.read(guard_path)
    lease = observer.read(Path(guard['lease_path']))
    verify_bound(binding, guard, lease, time.time())
    observer.require(observer.digest(guard_path) == binding['guard_sha256']
        and observer.digest(Path(guard['plan_path'])) == binding['plan_sha256'] == guard['plan_sha256']
        and observer.digest(Path(guard['lease_path'])) == guard['lease_sha256']
        and observer.content_digest(guard['source_pins']) == binding['source_manifest_sha256'],
        'retry_guard_plan_lease_manifest_unchanged')
    verify_live(binding)
    sys.path.insert(0, str(observer.SOURCE))
    transport.load('gpu.orch_r127_pilot_transcript', transport.HOME / 'read_transcript.py')
    previous.PID, previous.START_TICKS = binding['pid'], binding['start_ticks']
    previous.LOADED_INDEX, previous.LOADED_SHA = binding['loaded_index'], binding['loaded_sha256']
    previous.incarnation(observer.SOURCE)
    return transport, binding


def bind_recovery_reducer(snapshot, receipts):
    original = snapshot._reduce

    def reduce(state, value):
        if value['kind'] != 'R233_P3_RECOVERED_BOUNDARY':
            return original(state, value)
        document = value['document']
        selected = receipts.get(document['receipt_path'])
        observer.require(selected is not None, 'only_two_immutable_P3_recovery_receipts')
        receipt, checksum = selected
        observer.verify_recovery_record(value, receipt, checksum)
        state['pending'] = state['response'] = None

    snapshot._reduce = reduce


def main():
    request = json.loads(sys.stdin.read())
    previous.check_request(request)
    transport, binding = configure()
    target = previous.ROOT / 'r210'
    if request['op'] == 'poll':
        snapshot = transport.load('r233_p3_retry_snapshot', transport.HOME / 'read_snapshot.py')
        paths = [previous.ROOT / 'r233_lease_continuation/control/RECOVERY.json',
            observer.CONTROL / 'RECOVERY.json']
        receipts = {str(path): (observer.read(path), observer.digest(path)) for path in paths}
        observer.require(receipts[str(paths[1])][1] == binding['recovery_sha256'], 'retry_receipt_unchanged')
        bind_recovery_reducer(snapshot, receipts)
        reference = transport.resume_verified_cursor(previous.ROOT, target, request.get('reference'))
        result = snapshot.stored_poll(previous.ROOT / 'life', target / 'parent_cursor', reference)
        opening = transport.read(target / 'PARENT_OPENING.json')['publication']
        result.update(receipts=[], opening_published=True,
            opening_rendered=result['snapshot']['delivered'].get(opening['id']), console_replied=None,
            pinned_loaded_index=binding['loaded_index'], pinned_loaded_sha256=binding['loaded_sha256'])
    else:
        message = request['message']
        observer.require(isinstance(message, str) and len(message.split()) <= 160
            and len(message.encode()) <= 4096, 'existing_bounded_Astra_publication')
        with (target / 'PARENT_PUBLICATION.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            observer.require(not (target / 'R211_ISOLATION.json').exists(), 'no_isolation_publication')
            verify_live(binding)
            previous.incarnation(observer.SOURCE)
            from gpu.orch_r127_pilot_console import publish_parent
            result = publish_parent(str(previous.ROOT / 'life'), 'Astra', message)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
