"""CPU-only foreground ingress: no alias switching, model loading or signals."""

import argparse
import json
import os
from pathlib import Path
import selectors
import socket
import socketserver
import struct
import time

from gpu.ny_caption_life import LIMIT, POLICY
from ..projected_wire.contract import MAX_TRANSFER_BYTES, bounded, canonical, decode, digest, require, validate_binding
from ..projected_wire.custody import OwnerStore, load_binding
from ..projected_wire.relay import prepare
from .ledger import Ledger, origin_key


FORKS = {0: 'observation', 3: 'perspective', 5: 'revision', 6: 'selfderive', 7: 'unparented'}
SESSIONS = {slot: 'r213_r226_caption_' + name + '_fork' for slot, name in FORKS.items()}


def no_judgment(request, reason, *, ambiguous=False):
    return dict(policy=POLICY, origin=request.get('origin'), report=dict(ok=False,
        error='ORIGIN_TRANSPORT_FAILED_AFTER_DISPATCH' if ambiguous else 'ORIGIN_TRANSPORT_NOT_DISPATCHED',
        error_type=reason, no_judgment=True, feedback=[], next_stage='ACT', automatic_replay=False))


def forward_once(path, payload, deadline, ledger, connection):
    require(time.time() < deadline, 'original_transport_deadline')
    encoded = bounded(canonical(payload) + b'\n')
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as upstream:
        upstream.settimeout(min(110, deadline - time.time()))
        ledger.upstream(connection, os.fstat(upstream.fileno()).st_ino)
        try:
            upstream.connect(str(path))
            upstream.sendall(encoded)
            with upstream.makefile('rb') as stream:
                raw = stream.readline(LIMIT + 1)
            require(raw.endswith(b'\n') and len(raw) <= LIMIT, 'original_bounded_response')
            return decode(raw)
        finally:
            upstream.close()
            ledger.upstream(connection)


class Relay:
    def __init__(self, ledger, routes, upstream, preparer=prepare, forwarder=forward_once):
        self.ledger, self.routes, self.upstream = ledger, routes, upstream
        self.preparer, self.forwarder = preparer, forwarder

    def existing(self, key, request):
        item = self.ledger.item(key)
        if item['state'] == 'COMPLETE':
            return item['response']
        return no_judgment(request, item.get('reason', item['state']),
            ambiguous=item['state'] in ('DISPATCH_INTENT', 'UNKNOWN', 'UNKNOWN_SETTLED_NO_REPLAY', 'LEGACY_QUARANTINED'))

    def failure_reply(self, session, request, error):
        ambiguous = False
        try:
            item = self.ledger.item(origin_key(session, request))
            ambiguous = item['state'] in ('DISPATCH_INTENT', 'UNKNOWN', 'UNKNOWN_SETTLED_NO_REPLAY',
                'LEGACY_QUARANTINED', 'COMPLETE')
        except (KeyError, TypeError, ValueError):
            pass
        return no_judgment(request if isinstance(request, dict) else {}, type(error).__name__, ambiguous=ambiguous)

    def handle(self, connection, session, request):
        key, fresh = self.ledger.admit(connection, request)
        if not fresh:
            return self.existing(key, request)
        try:
            route = self.routes[session]
            payload = self.preparer(route['binding'], request, route['node'], route['scorer'])
            require(payload['session_id'] == session and payload['request'] == request
                and payload['transport_epoch'] == self.ledger.epoch, 'exact_prepared_dispatch')
            self.ledger.prepared(key, payload)
            if not self.ledger.dispatch(key):
                return self.existing(key, request)
            response = self.forwarder(self.upstream, payload, self.ledger.deadline, self.ledger, connection)
            require(type(response) is dict and response.get('origin') == request['origin']
                and type(response.get('report')) is dict, 'same_origin_actual_response')
            require(len(canonical(response) + b'\n') <= LIMIT, 'original_feedback_byte_bound')
            self.ledger.complete(key, response)
            return response
        except Exception as error:
            self.ledger.failed(key, type(error).__name__)
            return self.existing(key, request)


class NativeHandler(socketserver.StreamRequestHandler):
    def handle(self):
        identifier = self.server.accepted_ids.pop(self.connection.fileno())
        self.identifier, self.delivery = identifier, 'NOT_ATTEMPTED'
        request = {}
        try:
            self.connection.settimeout(min(115, max(.1, self.server.relay.ledger.deadline - time.time())))
            raw = self.rfile.readline(LIMIT + 1)
            require(raw.endswith(b'\n') and len(raw) <= LIMIT, 'original_native_byte_bound')
            request = decode(raw)
            require(type(request) is dict, 'native_request_object')
            response = self.server.relay.handle(identifier, self.server.session, request)
        except Exception as error:
            response = self.server.relay.failure_reply(self.server.session, request, error)
        try:
            self.wfile.write(canonical(response) + b'\n')
            self.wfile.flush()
            self.delivery = 'WRITE_RETURNED_NOT_TOOL_RECEIPT'
        except OSError:
            self.delivery = 'WRITE_FAILED_NOT_UPTAKE'

    def finish(self):
        try:
            super().finish()
        finally:
            self.connection.close()
            if hasattr(self, 'identifier'):
                self.server.relay.ledger.closed(self.identifier, self.delivery)


class NativeServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = False

    def __init__(self, path, relay, session):
        self.relay, self.session, self.accepted_ids = relay, session, {}
        super().__init__(str(path), NativeHandler)
        os.chmod(path, 0o600)

    def get_request(self):
        connection, address = super().get_request()
        try:
            self.accepted_ids[connection.fileno()] = self.relay.ledger.accepted(
                self.session, os.fstat(connection.fileno()).st_ino)
        except BaseException:
            connection.close()
            raise
        return connection, address


def validate_routes(config):
    require({int(row['slot']): row['binding']['session_id'] for row in config['routes']} == SESSIONS
        and len(config['routes']) == 5, 'all_five_exact_alias_bindings')
    require(config['deadline_unix'] == config['original_transport_deadline_unix'], 'no_transport_deadline_change')
    for row in config['routes']:
        slot, binding = int(row['slot']), row['binding']
        validate_binding(binding)
        require(row['stable_alias'] == f'/tmp/r226-caption-{slot}.sock', 'same_native_alias_name')
        require(binding['transport_epoch'] == config['transport_epoch']
            and binding['deadline_unix'] == config['deadline_unix'], 'same_relay_binding_epoch_deadline')
        require(row['parent_policy'] == 'R233_PARENTED', 'all_five_parented_including_historical_unparented')
    return {row['binding']['session_id']: row for row in config['routes']}


def administration(ledger, command):
    operation = command['operation']
    if operation == 'status':
        return ledger.status()
    if operation == 'close':
        return ledger.close_admission(command.get('reason', 'OWNER_ADMINISTRATIVE_FENCE'))
    if operation == 'open':
        token = command['readiness_sha256']
        readiness = decode(ledger.store.read('readiness-' + token + '.json'))
        require(digest(readiness) == token and readiness['transport_epoch'] == ledger.epoch
            and readiness['deadline_unix'] == ledger.deadline and readiness['projected_receiver_ready'] is True
            and readiness['sole_scorer_proved'] is True and time.time() < readiness['expires_unix'],
            'fresh_owner_installed_receiver_readiness')
        return ledger.open_admission(command['expected_fence'], token)
    if operation == 'resolve-unknown':
        token = command['resolution_sha256']
        resolution = decode(ledger.store.read('resolution-' + token + '.json'))
        require(digest(resolution) == token and resolution['schema'] == 'R233_OWNER_UNKNOWN_RESOLUTION_V1',
            'owner_installed_not_inline_child_resolution')
        return ledger.resolve_unknown(resolution)
    raise ValueError('only_explicit_status_close_open_resolve')


class AdminHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(5)
        peer_pid, peer_uid, peer_gid = struct.unpack('3i', self.connection.getsockopt(
            socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('3i')))
        require(peer_uid == self.server.ledger.store.owner_uid, 'administration_owner_peer_only')
        try:
            raw = self.rfile.readline(LIMIT + 1)
            require(raw.endswith(b'\n') and len(raw) <= LIMIT, 'bounded_owner_command')
            result = administration(self.server.ledger, decode(raw))
            response = dict(ok=True, result=result)
        except Exception as error:
            response = dict(ok=False, error=str(error))
        encoded = canonical(response) + b'\n'
        if len(encoded) > MAX_TRANSFER_BYTES:
            encoded = canonical(dict(ok=False, error='status_too_large_use_owner_journal')) + b'\n'
        self.wfile.write(encoded)


def run(config):
    routes = validate_routes(config)
    root = Path(config['root'])
    require(root.is_dir() and root.resolve() == root and time.time() < config['deadline_unix'],
        'existing_owner_root_and_original_deadline')
    owner_root = OwnerStore(root, os.getuid())
    owner_root.close()
    ledger = Ledger(config.get('journal_root', root / 'ledger'), os.getuid(),
        config['transport_epoch'], config['deadline_unix'])
    relay = Relay(ledger, routes, config['upstream'])
    servers = []
    try:
        with selectors.DefaultSelector() as selector:
            for row in config['routes']:
                server = NativeServer(root / (str(row['slot']) + '.sock'), relay, row['binding']['session_id'])
                servers.append(server)
                selector.register(server, selectors.EVENT_READ)
            admin = socketserver.ThreadingUnixStreamServer(str(root / 'admin.sock'), AdminHandler)
            admin.ledger = ledger
            os.chmod(root / 'admin.sock', 0o600)
            servers.append(admin)
            selector.register(admin, selectors.EVENT_READ)
            ledger.store.put('LISTENING-' + str(os.getpid()) + '.json', canonical(dict(pid=os.getpid(),
                unix=time.time(), native_aliases_changed=False, source_deadline=config['deadline_unix'],
                upstream=config['upstream'], admission='CLOSED', sessions=SESSIONS)))
            while time.time() < config['deadline_unix']:
                for key, unused in selector.select(timeout=.2):
                    key.fileobj._handle_request_noblock()
    finally:
        ledger.close_admission('ORIGINAL_DEADLINE_OR_SERVER_EXIT')
        for server in servers:
            server.server_close()
        ledger.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    serve_parser = commands.add_parser('serve')
    serve_parser.add_argument('--config', required=True)
    serve_parser.add_argument('--sha256', required=True)
    admin_parser = commands.add_parser('admin')
    admin_parser.add_argument('--socket', required=True)
    admin_parser.add_argument('--operation', choices=['status', 'close', 'open', 'resolve-unknown'], required=True)
    admin_parser.add_argument('--expected-fence', type=int)
    admin_parser.add_argument('--readiness-sha256')
    admin_parser.add_argument('--resolution-sha256')
    args = parser.parse_args()
    if args.command == 'serve':
        run(load_binding(args.config, os.getuid(), args.sha256))
    else:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(10)
            connection.connect(args.socket)
            connection.sendall(canonical(dict(operation=args.operation, expected_fence=args.expected_fence,
                readiness_sha256=args.readiness_sha256, resolution_sha256=args.resolution_sha256)) + b'\n')
            with connection.makefile('rb') as stream:
                raw = stream.readline(MAX_TRANSFER_BYTES + 1)
            bounded(raw)
            print(json.dumps(decode(raw), sort_keys=True))


if __name__ == '__main__':
    main()
