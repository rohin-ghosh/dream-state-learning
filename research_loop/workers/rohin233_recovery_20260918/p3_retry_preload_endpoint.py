"""Explicit one-shot PRELOAD_PARENT_QUEUE; no live-LOAD gate is modified."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time

import p3_retry_endpoint as live
import p3_retry_observe as observer


PID = 699464
START_TICKS = '33078516'
MODE = 'PRELOAD_PARENT_QUEUE'


def validate_preload(actual, head, appended, recovery):
    observer.require(actual is not None and actual['pid'] == PID and actual['start_ticks'] == START_TICKS
        and actual['source'] == str(observer.SOURCE) and actual['guard_argument_present']
        and actual['state'] not in ('Z', 'X'), 'exact_authorized_preload_native')
    observer.require(head['journal_id'] == observer.JOURNAL_ID and head['index'] == appended['index']
        and head['sha256'] == appended['sha256'] and head['kind'] == 'R233_P3_RECOVERED_BOUNDARY'
        and head['index'] == recovery['old_head_index'] + 1, 'preserved_head_no_retry_inference_LOAD')


def verified():
    sys.path.insert(0, str(live.previous.BASE / 'MATH_C'))
    import math_c
    import r210_parent_endpoint as transport
    observer.require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == math_c.HOST_SHA
        and os.getuid() == 2524, 'same_node4_user')
    evidence = observer.observe()
    observer.require(evidence['loaded'] is None and evidence['binding'] is None,
        'preload_only_never_fake_LOAD')
    recovery = observer.read(observer.CONTROL / 'RECOVERY.json')
    appended = observer.read(observer.CONTROL / 'RECOVERY_APPENDED.json')
    head_path = max((observer.ROOT / 'life/stream/records').glob('[0-9]' * 20 + '.json'))
    head = observer.record(head_path)
    actual = observer.process(PID)
    validate_preload(actual, head, appended, recovery)
    guard = observer.read(observer.CONTROL / 'GUARD.json')
    manifest = observer.verify_configuration(guard)
    authority = dict(mode=MODE, journal_id=observer.JOURNAL_ID, pid=PID, start_ticks=START_TICKS,
        source=str(observer.SOURCE), command_sha256=actual['command_sha256'],
        guard_sha256=observer.digest(observer.CONTROL / 'GUARD.json'), source_manifest_sha256=manifest,
        recovery_sha256=observer.digest(observer.CONTROL / 'RECOVERY.json'),
        complete_index=5243, complete_sha256=recovery['complete_sha256'],
        preserved_head_index=recovery['old_head_index'], preserved_head_sha256=recovery['old_head_sha256'],
        head_index=head['index'], head_sha256=head['sha256'], hard_end_unix=observer.END_UNIX,
        child_inference_during_replay_claimed=False, loaded=False)
    sys.path.insert(0, str(observer.SOURCE))
    transport.load('gpu.orch_r127_pilot_transcript', transport.HOME / 'read_transcript.py')
    return transport, authority


def main():
    request = json.loads(sys.stdin.read())
    observer.require(request.get('mode') == MODE and request.get('physical') == 3
        and request.get('op') in ('poll', 'publish', 'resolve_publication'), 'explicit_P3_preload_mode_only')
    observer.require(time.time() < request['deadline_unix'] <= time.time() + 600,
        'bounded_600_second_preload_authorization')
    transport, authority = verified()
    target = observer.ROOT / 'r210'
    if request['op'] == 'resolve_publication':
        message_sha = request['message_sha256']
        observer.require(isinstance(message_sha, str) and len(message_sha) == 64
            and all(character in '0123456789abcdef' for character in message_sha), 'exact_message_hash')
        with (target / 'PARENT_PUBLICATION.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            unused, current = verified()
            observer.require(current == authority, 'same_preload_during_readonly_reconciliation')
            paths = sorted((observer.ROOT / 'life/stream/inbox').glob('*.json'))
            observer.require(len(paths) <= 10000, 'bounded_existing_inbox_audit')
            matches, inventory = [], []
            for path in paths:
                observer.require(not path.is_symlink() and path.stat().st_size <= 65536,
                    'bounded_regular_inbox_evidence')
                raw = path.read_bytes()
                document = json.loads(raw)
                checksum = hashlib.sha256(raw).hexdigest()
                inventory.append(dict(name=path.name, sha256=checksum))
                if hashlib.sha256(document['text'].encode()).hexdigest() == message_sha:
                    matches.append(dict(id=document['id'], sha256=checksum, speaker=document['speaker']))
            result = dict(authority=authority, message_sha256=message_sha, matches=matches,
                endpoint_sha256=observer.digest(observer.CPU / 'p3_endpoint.py'),
                inbox_files=len(paths), inventory_sha256=observer.content_digest(inventory),
                observed_unix=time.time(), writes=[])
    elif request['op'] == 'poll':
        snapshot = transport.load('p3_retry_preload_snapshot', transport.HOME / 'read_snapshot.py')
        paths = [observer.ROOT / 'r233_lease_continuation/control/RECOVERY.json', observer.CONTROL / 'RECOVERY.json']
        live.bind_recovery_reducer(snapshot, {str(path): (observer.read(path), observer.digest(path)) for path in paths})
        reference = transport.resume_verified_cursor(observer.ROOT, target, request.get('reference'))
        result = snapshot.stored_poll(observer.ROOT / 'life', target / 'parent_cursor', reference)
        if result['snapshot']['caught_up']:
            observer.require(result['snapshot']['journal_id'] == authority['journal_id']
                and result['snapshot']['head_sha256'] == authority['head_sha256'], 'same_preserved_snapshot_head')
        result['preload_authority'] = authority
    else:
        message = request['message']
        observer.require(isinstance(message, str) and 0 < len(message.split()) <= 160
            and len(message.encode()) <= 4096, 'existing_Astra_limits')
        observer.require(request['authority'] == authority, 'same_authorized_preload_source')
        with (target / 'PARENT_PUBLICATION.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            unused, current = verified()
            observer.require(current == authority and not (target / 'R211_ISOLATION.json').exists(),
                'unchanged_preload_identity_inside_publication_lock')
            receipt = observer.CPU / 'P3_RETRY_PRELOAD_PUBLISHED.json'
            intent = observer.CPU / 'P3_RETRY_PRELOAD_PUBLISH_ATTEMPT.json'
            observer.require(not receipt.exists() and not intent.exists(), 'one_preload_publication_no_automatic_retry')
            observer.immutable(intent, dict(authority=authority, message_sha256=hashlib.sha256(message.encode()).hexdigest(),
                attempted_unix=time.time(), maximum_publications=1))
            from gpu.orch_r127_pilot_console import publish_parent
            result = publish_parent(str(observer.ROOT / 'life'), 'Astra', message)
            observer.immutable(receipt, dict(mode=MODE, publication=result, queued_not_rendered=True,
                authority=authority, observed_unix=time.time(), native_signals=[]))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
