"""Fsynced, hash-chained owner journal. Dispatch ambiguity is never a retry."""

from copy import deepcopy
import fcntl
import os
from pathlib import Path
import stat
import threading
import time
import uuid

from ..projected_wire.contract import canonical, decode, digest, is_sha, require
from ..projected_wire.custody import OwnerStore


def origin_key(session, request):
    require(type(request) is dict and set(request) == {'origin', 'metrics'}, 'unchanged_native_request')
    origin = request['origin']
    require(type(origin) is dict and is_sha(origin.get('record_sha256')), 'source_origin_required')
    return digest(dict(session_id=session, origin_sha256=origin['record_sha256']))


class Ledger:
    def __init__(self, root, owner_uid, transport_epoch, deadline):
        require(is_sha(transport_epoch), 'explicit_transport_epoch')
        self.store = OwnerStore(root, owner_uid)
        self.lock = threading.RLock()
        self.descriptor = os.open('LOCK', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600,
            dir_fd=self.store.directory)
        metadata = os.fstat(self.descriptor)
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == owner_uid
            and stat.S_IMODE(metadata.st_mode) == 0o600 and metadata.st_nlink == 1, 'owner_singleton_lock')
        try:
            fcntl.flock(self.descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            os.close(self.descriptor)
            self.store.close()
            raise
        self.epoch, self.deadline = transport_epoch, deadline
        self.sequence, self.head = 0, '0' * 64
        self.connections, self.origins = {}, {}
        self.opened, self.fence_sequence, self.poisoned = False, 0, False
        try:
            names = sorted(path.name for path in Path(root).glob('event-*.json'))
            for name in names:
                event = decode(self.store.read(name))
                require(name == f'event-{self.sequence + 1:020d}.json'
                    and event['sequence'] == self.sequence + 1 and event['previous'] == self.head,
                    'complete_hash_chained_journal')
                self._apply(event)
                self.sequence, self.head = event['sequence'], digest(event)
            if self.sequence:
                require(self.metadata == dict(transport_epoch=transport_epoch, deadline_unix=deadline),
                    'no_transport_epoch_or_deadline_reinterpretation')
            else:
                self._event('BIND', dict(transport_epoch=transport_epoch, deadline_unix=deadline))
            self._event('CLOSE', dict(reason='START_OR_RESTART_FAIL_CLOSED'))
            for key, item in list(self.origins.items()):
                if item['state'] == 'DISPATCH_INTENT':
                    self._event('UNKNOWN', dict(key=key, reason='RESTART_AFTER_DURABLE_DISPATCH_INTENT'))
                elif item['state'] in ('ADMITTED', 'PREPARED'):
                    self._event('NO_DISPATCH', dict(key=key, reason='RESTART_NEVER_DISPATCHED'))
            for identifier, item in list(self.connections.items()):
                if item['closed'] is None:
                    self._event('SOCKET_CLOSED', dict(connection=identifier, disposition='PROCESS_LOST',
                        delivery='UNKNOWN', upstream_lifetime='UNKNOWN_IF_DISPATCHED'))
        except BaseException:
            self.release()
            raise

    def _event(self, kind, payload):
        require(not self.poisoned, 'journal_io_failure_requires_offline_reconciliation')
        event = dict(sequence=self.sequence + 1, previous=self.head, kind=kind, payload=deepcopy(payload),
            unix=time.time())
        try:
            self.store.put(f'event-{event["sequence"]:020d}.json', canonical(event))
        except BaseException:
            self.poisoned = True
            self.opened = False
            raise
        self._apply(event)
        self.sequence, self.head = event['sequence'], digest(event)
        return event

    def _apply(self, event):
        kind, payload = event['kind'], event['payload']
        if kind == 'BIND':
            self.metadata = payload
        elif kind == 'OPEN':
            self.opened = True
        elif kind == 'CLOSE':
            self.opened, self.fence_sequence = False, event['sequence']
        elif kind == 'SOCKET_ACCEPTED':
            self.connections[payload['connection']] = dict(payload, accepted=event['sequence'], closed=None,
                delivery='NOT_ATTEMPTED', upstream=None)
        elif kind == 'SOCKET_CLOSED':
            self.connections[payload['connection']].update(payload, closed=event['sequence'])
        elif kind in ('UPSTREAM_OPEN', 'UPSTREAM_CLOSED'):
            self.connections[payload['connection']]['upstream'] = dict(payload, state=kind)
        elif kind == 'ADMIT':
            self.origins[payload['key']] = dict(payload, state='ADMITTED', admitted=event['sequence'])
        elif kind in ('PREPARED', 'DISPATCH_INTENT', 'COMPLETE', 'UNKNOWN', 'NO_DISPATCH', 'UNKNOWN_SETTLED_NO_REPLAY'):
            self.origins[payload['key']].update(payload, state=kind)
        elif kind == 'IMPORT':
            self.origins[payload['key']] = dict(payload, state='LEGACY_QUARANTINED')
        else:
            require(kind == 'DUPLICATE', 'recognized_ledger_event')

    def close_admission(self, reason):
        with self.lock:
            self._event('CLOSE', dict(reason=reason))
            return self.status()

    def open_admission(self, expected_fence, readiness_sha256):
        with self.lock:
            require(not self.opened and expected_fence == self.fence_sequence, 'compare_and_open_same_fence')
            require(is_sha(readiness_sha256), 'owner_bound_receiver_readiness')
            require(time.time() < self.deadline and self.status()['drained'], 'closed_drained_unexpired_before_open')
            self._event('OPEN', dict(readiness_sha256=readiness_sha256, fence_sequence=expected_fence))
            return self.status()

    def accepted(self, session, descriptor_inode):
        with self.lock:
            identifier = uuid.uuid4().hex
            self._event('SOCKET_ACCEPTED', dict(connection=identifier, session=session,
                socket_inode=descriptor_inode, gate_open_at_accept=self.opened))
            return identifier

    def closed(self, connection, delivery):
        with self.lock:
            self._event('SOCKET_CLOSED', dict(connection=connection, disposition='HANDLER_FINISHED', delivery=delivery))

    def admit(self, connection, request):
        with self.lock:
            live = self.connections[connection]
            key = origin_key(live['session'], request)
            if key in self.origins:
                require(self.origins[key]['request'] == request, 'same_origin_cannot_change_request_or_metrics')
                self._event('DUPLICATE', dict(key=key, connection=connection))
                return key, False
            self._event('ADMIT', dict(key=key, connection=connection, session=live['session'], request=request))
            if not self.opened or not live['gate_open_at_accept'] or time.time() >= self.deadline:
                self._event('NO_DISPATCH', dict(key=key, reason='ADMISSION_FENCED_OR_EXPIRED'))
                return key, False
            return key, True

    def prepared(self, key, envelope):
        with self.lock:
            require(self.origins[key]['state'] == 'ADMITTED', 'prepare_only_admitted')
            self._event('PREPARED', dict(key=key, envelope_sha256=digest(envelope)))

    def dispatch(self, key):
        with self.lock:
            item = self.origins[key]
            require(item['state'] == 'PREPARED', 'single_dispatch_after_preparation')
            if not self.opened or item['admitted'] <= self.fence_sequence or time.time() >= self.deadline:
                self._event('NO_DISPATCH', dict(key=key, reason='FENCED_OR_EXPIRED_BEFORE_DISPATCH'))
                return False
            self._event('DISPATCH_INTENT', dict(key=key, no_automatic_replay=True))
            return True

    def upstream(self, connection, inode=None):
        with self.lock:
            self._event('UPSTREAM_OPEN' if inode is not None else 'UPSTREAM_CLOSED',
                dict(connection=connection, socket_inode=inode))

    def complete(self, key, response):
        with self.lock:
            require(self.origins[key]['state'] == 'DISPATCH_INTENT', 'completion_only_after_intent')
            self._event('COMPLETE', dict(key=key, response=response, response_sha256=digest(response),
                client_delivery_proved=False))

    def failed(self, key, reason):
        with self.lock:
            state = self.origins[key]['state']
            require(state in ('ADMITTED', 'PREPARED', 'DISPATCH_INTENT'), 'failure_before_completion_only')
            self._event('UNKNOWN' if state == 'DISPATCH_INTENT' else 'NO_DISPATCH', dict(key=key, reason=reason))

    def resolve_unknown(self, resolution):
        with self.lock:
            key = resolution['key']
            item = self.origins[key]
            require(not self.opened and item['state'] == 'UNKNOWN', 'closed_unknown_resolution_only')
            require(resolution['transport_epoch'] == self.epoch and resolution['request_sha256'] == digest(item['request'])
                and resolution['no_replay'] is True and resolution['upstream_callback_quiesced'] is True
                and is_sha(resolution['owner_evidence_sha256']), 'owner_resolution_exact_request_lifetime')
            if resolution['disposition'] == 'COMPLETE':
                require(resolution['response']['origin'] == item['request']['origin']
                    and digest(resolution['response']) == resolution['response_sha256'], 'exact_retained_owner_result')
                self._event('COMPLETE', dict(key=key, response=resolution['response'],
                    response_sha256=resolution['response_sha256'], resolution_sha256=digest(resolution),
                    client_delivery_proved=False))
            else:
                require(resolution['disposition'] == 'UNKNOWN_NO_REPLAY', 'no_retry_resolution')
                self._event('UNKNOWN_SETTLED_NO_REPLAY', dict(key=key, resolution_sha256=digest(resolution)))
            return self.status()

    def import_quarantine(self, rows, proof_sha256):
        with self.lock:
            require(not self.opened and not self.origins and is_sha(proof_sha256), 'initial_closed_legacy_import_only')
            require(len({origin_key(row['session'], row['request']) for row in rows}) == len(rows),
                'one_disposition_per_legacy_origin')
            for row in rows:
                require(row['disposition'] in ('COMPLETE', 'UNKNOWN_NO_REPLAY', 'PREPARED_NEVER_DISPATCHED',
                    'NO_JUDGMENT_EXPIRED'), 'explicit_legacy_disposition')
            for row in rows:
                self._event('IMPORT', dict(row, key=origin_key(row['session'], row['request']),
                    proof_sha256=proof_sha256, no_automatic_replay=True))

    def item(self, key):
        with self.lock:
            return deepcopy(self.origins[key])

    def status(self):
        with self.lock:
            pending = {key: value['state'] for key, value in self.origins.items()
                if value['state'] in ('ADMITTED', 'PREPARED', 'DISPATCH_INTENT', 'UNKNOWN')}
            active = {key: deepcopy(value) for key, value in self.connections.items() if value['closed'] is None}
            before_fence = {key: value for key, value in active.items() if value['accepted'] <= self.fence_sequence}
            return dict(transport_epoch=self.epoch, deadline_unix=self.deadline, open=self.opened,
                fence_sequence=self.fence_sequence, head=self.head, sequence=self.sequence,
                pending=pending, active_sockets=active, prefence_sockets=before_fence,
                drained=not self.opened and not pending and not before_fence and not self.poisoned,
                kernel_backlog_count=None, queued_connections_cannot_dispatch_while_closed=True,
                legacy_drain_proved=False)

    def release(self):
        os.close(self.descriptor)
        self.store.close()
