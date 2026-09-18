"""Bounded local socket handover while the learner continues running."""

import argparse
import json
import os
from pathlib import Path
import socket
import socketserver
import time


LIMIT = 262144


def read_line(stream):
    raw = stream.readline(LIMIT + 1)
    if not raw.endswith(b'\n') or len(raw) > LIMIT:
        raise ValueError('bounded_complete_protocol_line')
    return raw


def forward(raw, target, *, deadline, ready=None):
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('replacement_scorer_not_ready')
            if ready is not None and not ready.exists():
                time.sleep(min(.1, remaining))
                continue
            connection.settimeout(remaining)
            try:
                connection.connect(str(target))
                break
            except (FileNotFoundError, ConnectionRefusedError):
                time.sleep(min(.1, remaining))
        connection.sendall(raw)
        with connection.makefile('rb') as stream:
            return read_line(stream)
    finally:
        connection.close()


def serve(listen, target, receipt, *, seconds, ready=None):
    if not (listen.is_absolute() and target.is_absolute() and not listen.exists()
            and 0 < seconds <= 21600):
        raise ValueError('new_bounded_absolute_bridge')

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(115)
            raw = read_line(self.rfile)
            try:
                result = forward(raw, target, deadline=time.monotonic() + 110, ready=ready)
            except (OSError, ValueError) as error:
                request = json.loads(raw)
                result = json.dumps(dict(policy='R210_LANGUAGE_NATIVE_CAPTION_BATCH_V1',
                    origin=request.get('origin'), report=dict(ok=False,
                        error='SCORER_HANDOVER_OUTCOME_UNKNOWN_NO_AUTOMATIC_RETRY',
                        error_type=type(error).__name__, feedback=[]))).encode() + b'\n'
            self.wfile.write(result)

    with socketserver.UnixStreamServer(str(listen), Handler) as server:
        os.chmod(listen, 0o600)
        descriptor = os.open(receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(dict(pid=os.getpid(), listen=str(listen), target=str(target),
                unix=time.time(), seconds=seconds), stream, sort_keys=True)
        server.timeout = .5
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            server.handle_request()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listen', required=True, type=Path)
    parser.add_argument('--target', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--seconds', required=True, type=int)
    parser.add_argument('--ready', type=Path)
    args = parser.parse_args()
    serve(args.listen, args.target, args.receipt, seconds=args.seconds, ready=args.ready)


if __name__ == '__main__':
    main()
