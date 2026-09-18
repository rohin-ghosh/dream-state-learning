"""Renew authenticated future-only caption transport within a bound allocation."""

import argparse
import json
import os
from pathlib import Path
import selectors
import socketserver
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_life import LIMIT, POLICY
from research_loop.workers.rohin221_continuous_caption_20260918.native_proxy import (
    authorized_wrapper, export_via_ssh, forward, stage_via_ssh,
)


def validate_deadline(deadline, lease, now):
    if not now < deadline <= lease - 21600:
        raise ValueError('finite_transport_within_recorded_allocation')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = data.bound(data.file_ref(args.config.resolve()))
    validate_deadline(config['deadline_unix'], config['lease_boundary_unix'], time.time())
    root = Path(config['root'])
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    registry = data.bound(config['registry'])

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(115)
            request, dispatched = {}, False
            started = time.time()
            try:
                raw = self.rfile.readline(LIMIT + 1)
                data.require(raw.endswith(b'\n') and len(raw) <= LIMIT, 'bounded_native_request')
                request = json.loads(raw)
                data.require(set(request) == {'origin', 'metrics'}, 'unchanged_native_protocol')
                row = self.server.binding
                envelope = export_via_ssh(row, request, config['native_source'], authorized_wrapper(row))
                records = stage_via_ssh(row, envelope, config['scorer_source'], config['shared_root'])
                dispatched = True
                reply = forward(config['shared_forward'], dict(session_id=row['session_id'], request=request, records=records))
                reply.setdefault('source_transport', {}).update(original_bytes=envelope['original_bytes'],
                    chunks=len(envelope['chunks']), complete_THINK_ancestry=envelope['complete_THINK_ancestry'],
                    mirror_method=envelope['schema'])
            except Exception as error:
                reply = dict(policy=POLICY, origin=request.get('origin'), report=dict(ok=False,
                    error='ORIGIN_TRANSPORT_FAILED_AFTER_DISPATCH' if dispatched else 'ORIGIN_TRANSPORT_NOT_DISPATCHED',
                    error_type=type(error).__name__, feedback=[], next_stage='ACT'))
            report = reply.get('report', {})
            data.private_write(root / ('TRANSPORT_' + str(time.time_ns()) + '.json'), dict(
                unix=time.time(), seconds=time.time()-started, session_id=self.server.binding['session_id'],
                origin=request.get('origin'), dispatched=dispatched, receipt_sha256=reply.get('receipt_sha256'),
                error=report.get('error'), error_type=report.get('error_type'),
                feedback_count=len(report.get('feedback', [])), source_transport=reply.get('source_transport')))
            self.wfile.write(data.canonical(reply) + b'\n')

    class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
        daemon_threads = False

    servers = []
    with selectors.DefaultSelector() as selector:
        try:
            for row in registry['rows']:
                authorized_wrapper(row)
                data.require(type(row['minimum_origin_record_index']) is int, 'explicit_future_frontier')
                path = root / (str(row['physical']) + '.sock')
                server = Server(str(path), Handler)
                server.binding = row
                os.chmod(path, 0o600)
                selector.register(server, selectors.EVENT_READ)
                servers.append(server)
            data.private_write(root / 'READY.json', dict(unix=time.time(), pid=os.getpid(),
                sessions=len(servers), deadline_unix=config['deadline_unix'], no_child_network=True,
                future_frontiers={row['session_id']:row['minimum_origin_record_index'] for row in registry['rows']}))
            while time.time() < config['deadline_unix']:
                for key, _ in selector.select(timeout=1):
                    key.fileobj._handle_request_noblock()
        finally:
            for server in servers:
                server.server_close()


if __name__ == '__main__':
    main()
