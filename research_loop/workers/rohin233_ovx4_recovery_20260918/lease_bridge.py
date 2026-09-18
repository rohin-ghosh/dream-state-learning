"""Immutable lease-bound CPU route; drain before sole-writer scorer adoption."""

import argparse
import ctypes
import json
import os
from pathlib import Path
import socket
import socketserver
import time

LIMIT = 16777216


def exchange(first, second):
    libc = ctypes.CDLL(None, use_errno=True)
    rename = libc.renameat2
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(first), -100, os.fsencode(second), 2) != 0:
        raise OSError(ctypes.get_errno(), 'atomic_socket_exchange_failed')


def put(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.pending')
    temporary.write_text(json.dumps(value, sort_keys=True))
    os.replace(temporary, path)


def validate(config, now=None):
    now = time.time() if now is None else now
    if not now < config['deadline_unix'] <= config['lease_boundary_unix'] - 21600:
        raise ValueError('lease_bound_six_hour_margin')


def serve(config):
    validate(config)
    root = Path(config['root'])
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    endpoint = Path(config['endpoint'])
    parked = endpoint.with_name(endpoint.name + '.prelease')
    if parked.exists() or endpoint.stat().st_ino != config['endpoint_inode']:
        raise ValueError('exact_current_endpoint')

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(115)
            raw = self.rfile.readline(LIMIT + 1)
            if not raw.endswith(b'\n') or len(raw) > LIMIT:
                raise ValueError('bounded_wire_request')
            stop = min(config['deadline_unix'], time.time() + 108)
            while not (root / 'TARGET.json').exists():
                if time.time() >= stop:
                    raise TimeoutError('handoff_not_ready_no_dispatch')
                time.sleep(.1)
            target = json.loads((root / 'TARGET.json').read_bytes())['socket']
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as upstream:
                upstream.settimeout(max(.1, stop-time.time()))
                upstream.connect(target)
                upstream.sendall(raw)
                with upstream.makefile('rb') as stream:
                    response = stream.readline(262145)
            if not response.endswith(b'\n') or len(response) > 262144:
                raise ValueError('bounded_actual_response')
            self.wfile.write(response)

    class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
        daemon_threads = False

    with Server(str(parked), Handler) as server:
        os.chmod(parked, 0o600)
        exchange(endpoint, parked)
        put(root / 'ACTIVE.json', dict(unix=time.time(), pid=os.getpid(),
            deadline_unix=config['deadline_unix'], endpoint_switched=True,
            scoring_calls=0, native_signals=[], historical_replay=False))
        server.timeout = .5
        while time.time() < config['deadline_unix']:
            server.handle_request()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    serve(json.loads(parser.parse_args().config.read_bytes()))
