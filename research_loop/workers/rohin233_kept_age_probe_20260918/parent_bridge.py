"""Bounded future-only parenting envelope; no scorer or player source mutation."""

import argparse
from copy import deepcopy
import ctypes
import hashlib
import json
import os
from pathlib import Path
import socket
import socketserver
import stat
import time


LIMIT = 262144
EPOCH = 'R233_PARENT_v1'
TOPICS = (
    'Observation: find one concrete visual detail and a plausible expectation to overturn.',
    'Perspective: try the voice of a pictured object or an unexpected participant.',
    'Misdirection: set up one interpretation and finish with a different, scene-grounded interpretation.',
    'Revision: use actual feedback to revise a weak attempt; change the idea, not only its wording.',
    'Transfer: try a grounded analogy to work, science, or everyday relationships without inventing scene facts.',
    'Selection: compare your candidate ideas and prefer a concrete punchline over a description of the scene.',
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    raw = canonical(value) + b'\n'
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('immutable_receipt_collision')
        return
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def guidance(opportunity):
    return (f'[{EPOCH}; Leibniz scripted parent, not scorer judgment] '
        'This begins a separately recorded parented in-life treatment; your weights remain frozen. '
        + TOPICS[(opportunity - 1) % len(TOPICS)] + ' Offer the actual captions, not a promise, diagram, '
        'or description of your plan. Ordinary language is welcome; no mandatory fields or count. '
        'The actual rank, relevance and novelty feedback below remains authoritative game data. '
        'I have no private reference captions and make no claim that an accepted string is a good joke.')


def envelope(request, response, generated, config):
    origin = request['origin']
    identifier = origin['request_id']
    if origin.get('kind') != 'STANDALONE_GENERATION' or len(identifier) != 64:
        raise ValueError('standalone_origin_required')
    if (generated['stage'] != 'ACT' or sha(canonical(generated)) != identifier
            or identifier != origin['request_sha256']):
        raise ValueError('actual_generation_request_binding')
    if (response.get('request_id') != identifier or response.get('condition') != config['condition']
            or response.get('rule_sha256') != config['rule_sha256']):
        raise ValueError('exact_current_scorer_binding')
    receipt = response.get('receipt_sha256', '')
    if len(receipt) != 64 or any(character not in '0123456789abcdef' for character in receipt):
        raise ValueError('original_receipt_required')
    text = guidance(generated['opportunity'])
    parent = dict(epoch=EPOCH, author='Leibniz scripted parent', guidance=text,
        guidance_sha256=sha(text.encode()), opportunity=generated['opportunity'],
        ACT_request_id=identifier, scored_receipt_sha256=receipt,
        raw_response_sha256=sha(canonical(response)), model_weights_changed=False,
        unmatched_guidance=True, parent_tokens=None, parent_token_count_status='not_yet_tokenized')
    result = deepcopy(response)
    instruction = result['report'].get('instruction')
    result['report']['instruction'] = ((str(instruction) + '\n') if instruction else '') + text
    result['R233_parent_envelope'] = parent
    return result, parent


def exchange(first, second):
    libc = ctypes.CDLL(None, use_errno=True)
    rename = libc.renameat2
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(first), -100, os.fsencode(second), 2) != 0:
        raise OSError(ctypes.get_errno(), 'atomic_socket_exchange_failed')


def read_line(stream):
    raw = stream.readline(LIMIT + 1)
    if not raw.endswith(b'\n') or len(raw) > LIMIT:
        raise ValueError('bounded_complete_protocol_line')
    return raw


def forward(raw, target):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(115)
        connection.connect(str(target))
        connection.sendall(raw)
        with connection.makefile('rb') as stream:
            return read_line(stream)


def proc_start(pid):
    return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]


def serve(config, root):
    endpoint = Path(config['endpoint'])
    parked = endpoint.with_name('r233_parked.sock')
    if (not endpoint.is_absolute() or not stat.S_ISSOCK(endpoint.stat().st_mode)
            or endpoint.stat().st_ino != config['endpoint_inode'] or parked.exists()
            or proc_start(config['scorer_pid']) != config['scorer_start_ticks']
            or proc_start(config['player_pid']) != config['player_start_ticks']
            or not 0 < config['deadline_unix'] - time.time() <= 10800):
        raise ValueError('exact_live_endpoint_and_process_ownership')
    generation_root = Path(config['generation_root'])

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(125)
            raw_request = read_line(self.rfile)
            raw_response = forward(raw_request, parked)
            request, response = json.loads(raw_request), json.loads(raw_response)
            identifier = request.get('origin', {}).get('request_id', '')
            try:
                if len(identifier) != 64 or any(value not in '0123456789abcdef' for value in identifier):
                    raise ValueError('bounded_generation_identifier')
                generated = json.loads((generation_root / (identifier + '.json')).read_bytes())['request']
                result, parent = envelope(request, response, generated, config)
                encoded = canonical(result) + b'\n'
                if len(encoded) > LIMIT:
                    raise ValueError('bounded_parent_envelope')
                directory = root / 'private' / identifier
                put(directory / 'SOURCE.json', dict(request=request, original_response=response,
                    raw_request_sha256=sha(raw_request), raw_response_sha256=sha(raw_response)))
                put(directory / 'ENVELOPE.json', result)
                receipt_path = root / 'receipts' / (identifier + '.json')
                if not receipt_path.exists():
                    put(receipt_path, dict(unix=time.time(), **parent,
                        envelope_sha256=sha(encoded), raw_wire_response_sha256=sha(raw_response),
                        first_render_claim=False, historical_rescoring=False))
                self.wfile.write(encoded)
            except Exception as error:
                put(root / 'errors' / f'{time.time_ns()}.json', dict(unix=time.time(),
                    error_type=type(error).__name__, error=str(error)[:160], original_reply_forwarded=True))
                self.wfile.write(raw_response)

    with socketserver.UnixStreamServer(str(parked), Handler) as server:
        os.chmod(parked, 0o600)
        proxy_inode = parked.stat().st_ino
        put(root / 'READY.json', dict(unix=time.time(), pid=os.getpid(), epoch=EPOCH,
            config_sha256=sha(canonical(config)), source_sha256=sha(Path(__file__).read_bytes()),
            original_inode=endpoint.stat().st_ino, proxy_inode=proxy_inode))
        exchange(endpoint, parked)
        put(root / 'ACTIVE.json', dict(unix=time.time(), pid=os.getpid(), epoch=EPOCH,
            deadline_unix=config['deadline_unix'], first_render_claim=False,
            original_scorer_pid=config['scorer_pid'], original_player_pid=config['player_pid'],
            source_process_signals=[], scorer_receipts_unchanged=True))
        server.timeout = .5
        while time.time() < config['deadline_unix']:
            server.handle_request()
        if endpoint.exists() and parked.exists() and endpoint.stat().st_ino == proxy_inode:
            exchange(endpoint, parked)
        put(root / 'EXIT.json', dict(unix=time.time(), pid=os.getpid(), source_process_signals=[]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    serve(json.loads((args.root / 'CONFIG.private.json').read_bytes()), args.root)


if __name__ == '__main__':
    main()
