"""Operator CPU relay: private Unix requests, authenticated SSH journal reads."""

import argparse
import json
import os
from pathlib import Path
import selectors
import shlex
import socket
import socketserver
import subprocess
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_life import POLICY, LIMIT
from research_loop.workers.rohin221_continuous_caption_20260918.journal_transport import (
    MAX_ENVELOPE_BYTES, SCHEMA,
)


def forward(path, payload):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(110)
        connection.connect(str(path))
        connection.sendall(data.canonical(payload) + b'\n')
        with connection.makefile('rb') as stream:
            raw = stream.readline(LIMIT + 1)
    data.require(raw.endswith(b'\n') and len(raw) <= LIMIT, 'bounded_scorer_response')
    return json.loads(raw)


def authorized_wrapper(config):
    wrappers = {'ovx': 'gpu/ovx_ssh.sh', 'ovx2': 'gpu/ovx2_ssh.sh'}
    data.require(config.get('host_alias') in wrappers, 'fixed_authorized_native_host')
    return wrappers[config['host_alias']]


def require_future_origin(config, request):
    minimum = config.get('minimum_origin_record_index')
    if minimum is not None:
        data.require(type(minimum) is int and type(request['origin'].get('record_index')) is int
            and request['origin']['record_index'] >= minimum, 'future_only_no_historical_replay')


def export_via_ssh(config, request, source, wrapper):
    require_future_origin(config, request)
    origin = request['origin']
    data.require(set(origin) == {'kind','record_index','record_sha256'} and
        origin['kind'] == 'TRAIN_CHILD_RESPONSE' and type(origin['record_index']) is int and
        origin['record_index'] >= 0 and len(origin['record_sha256']) == 64 and
        all(character in '0123456789abcdef' for character in origin['record_sha256']), 'actual_native_origin')
    command = ['env', 'PYTHONPATH='+source, '/usr/bin/python3', '-B', '-m',
        'research_loop.workers.rohin221_continuous_caption_20260918.journal_transport',
        '--root',config['life_root'],'--journal-id',config['journal']['journal_id'],
        '--index',str(origin['record_index']),'--sha256',origin['record_sha256']]
    result = subprocess.run(['bash',wrapper,shlex.join(command)],text=True,capture_output=True,
                            timeout=20,check=True)
    data.require(len(result.stdout) <= MAX_ENVELOPE_BYTES, 'bounded_export_response')
    envelope = json.loads(result.stdout)
    data.require(envelope['schema'] == SCHEMA and envelope['origin'] == origin
        and envelope['journal_id'] == config['journal']['journal_id'], 'same_exported_source_binding')
    return envelope


def stage_via_ssh(config, envelope, source, shared_root):
    mirror = str(Path(shared_root) / 'mirrors' / config['session_id'])
    command = ['env', 'PYTHONPATH='+source, '/usr/bin/python3', '-B', '-m',
        'research_loop.workers.rohin221_continuous_caption_20260918.journal_transport',
        '--root', mirror, '--journal-id', config['journal']['journal_id'], '--import-chunk']
    for records in envelope['chunks']:
        result = subprocess.run(['bash','gpu/ovx4_ssh.sh',shlex.join(command)],
            input=data.canonical(records), capture_output=True, timeout=25, check=True)
        receipt = json.loads(result.stdout)
        data.require(receipt == dict(imported=len(records), first=records[0]['index'], last=records[-1]['index']),
                     'same_imported_chunk')
    return [envelope['chunks'][-1][-1]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--source-on-node3', required=True)
    parser.add_argument('--source-on-scorer', required=True)
    parser.add_argument('--shared-root', required=True)
    parser.add_argument('--shared-forward', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=21600)
    args = parser.parse_args()
    data.require(0 < args.seconds <= 21600, 'bounded_operator_proxy')
    registry = data.bound(data.file_ref(Path(args.registry).resolve()))
    args.root.mkdir(mode=0o700, parents=True, exist_ok=False)

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(115)
            request, dispatched = {}, False
            try:
                raw = self.rfile.readline(LIMIT + 1)
                data.require(raw.endswith(b'\n') and len(raw) <= LIMIT, 'bounded_native_request')
                request = json.loads(raw)
                data.require(set(request) == {'origin','metrics'}, 'unchanged_native_protocol')
                config = self.server.config
                envelope = export_via_ssh(config, request, args.source_on_node3, authorized_wrapper(config))
                records = stage_via_ssh(config, envelope, args.source_on_scorer, args.shared_root)
                dispatched = True
                reply = forward(args.shared_forward, dict(session_id=config['session_id'],
                    request=request, records=records))
                reply.setdefault('source_transport', {}).update(original_bytes=envelope['original_bytes'],
                    chunks=len(envelope['chunks']), complete_THINK_ancestry=envelope['complete_THINK_ancestry'],
                    mirror_method=SCHEMA)
            except Exception as error:
                reply = dict(policy=POLICY, origin=request.get('origin'), report=dict(ok=False,
                    error='SCORER_OUTCOME_UNKNOWN_NO_RETRY' if dispatched else 'ORIGIN_TRANSPORT_NOT_DISPATCHED',
                    error_type=type(error).__name__, feedback=[]))
            report = reply.get('report', {})
            stamp = str(time.time_ns())
            data.private_write(args.root / ('TRANSPORT_'+stamp+'.json'), dict(unix=time.time(),
                session_id=self.server.config['session_id'], origin=request.get('origin'),
                scoring_dispatched=dispatched, ok=report.get('ok'), error=report.get('error'),
                error_type=report.get('error_type'), receipt_sha256=reply.get('receipt_sha256'),
                source_transport=reply.get('source_transport'), feedback_count=len(report.get('feedback', []))))
            self.wfile.write(data.canonical(reply) + b'\n')

    class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
        daemon_threads = True

    servers = []
    with selectors.DefaultSelector() as selector:
        try:
            for config in registry['rows']:
                authorized_wrapper(config)
                path = args.root / (str(config['physical'])+'.sock')
                server = Server(str(path), Handler)
                server.config = config
                os.chmod(path, 0o600)
                selector.register(server, selectors.EVENT_READ)
                servers.append(server)
            data.private_write(args.root / 'READY.json', dict(pid=os.getpid(), unix=time.time(),
                registry=data.file_ref(Path(args.registry).resolve()), sessions=len(servers),
                source_on_node3=args.source_on_node3, no_child_network=True))
            deadline = time.time() + args.seconds
            while time.time() < deadline:
                for key, unused in selector.select(timeout=1):
                    key.fileobj.handle_request()
        finally:
            for server in servers:
                server.server_close()


if __name__ == '__main__':
    main()
