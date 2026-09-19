"""Exact-origin math transport outside the clone's GPU confinement."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import sys
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def evidence(root, kind, **fields):
    path = root / (kind + '_' + str(time.time_ns()) + '.json')
    with path.open('x') as output:
        json.dump(dict(kind=kind, observed_unix=time.time(), **fields), output, sort_keys=True)


def call(config, origin):
    binding = json.loads((Path(__file__).resolve().parents[2] / 'BRIDGE.json').read_bytes())
    require(config['code_policy'] == binding['code_policy'], 'same_NFKC_policy')
    require(config['cpu_gate_sha256'] == binding['gate_sha256'], 'same_actual_gate')
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
        channel.settimeout(160)
        channel.connect(binding['socket'])
        channel.sendall(json.dumps(origin).encode() + b'\n')
        return json.loads(channel.makefile('rb').readline(262145))


def serve(path):
    config = json.loads(path.read_bytes())
    sys.path.insert(0, config['cpu_source'])
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    from gpu.orch_r153_community_transport import EXISTING_LIFE_CPU_POLICY, cpu_once
    require(digest(verify_gate(config['gate_root'])) == config['gate_sha256'], 'actual_math_gate')
    receipts = path.parent / 'bridge_receipts'
    receipts.mkdir(mode=0o700)
    seen = set()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(config['socket'])
        os.chmod(config['socket'], 0o600)
        server.listen(1)
        server.settimeout(2)
        evidence(receipts, 'READY', pid=os.getpid(), gate_sha256=config['gate_sha256'])
        while time.time() < config['stop_unix']:
            if (path.parent / 'control/EXIT.json').exists():
                break
            try:
                channel, unused_address = server.accept()
            except TimeoutError:
                continue
            with channel:
                channel.settimeout(160)
                origin = None
                try:
                    peer_pid, peer_uid, unused_gid = struct.unpack('3i', channel.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                    process = Path('/proc') / str(peer_pid)
                    arguments = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
                    require(peer_uid == 2524 and os.readlink(process / 'cwd') == config['native_source']
                        and arguments[-3:] == ['native', '--config', config['guard_path']], 'exact_clone_native')
                    require(hashlib.sha256(Path(config['guard_path']).read_bytes()).hexdigest() == config['guard_sha256'], 'guard_binding')
                    origin = json.loads(channel.makefile('rb').readline(4097))
                    require(set(origin) == {'kind', 'record_index', 'record_sha256'}
                        and origin['kind'] == 'TRAIN_CHILD_RESPONSE' and origin['record_index'] > 5846, 'new_clone_responses_only')
                    key = (origin['record_index'], origin['record_sha256'])
                    require(key not in seen, 'no_redispatch')
                    seen.add(key)
                    evidence(receipts, 'ACCEPTED', origin=origin, peer_pid=peer_pid)
                    outcome = cpu_once(config['raw_root'], config['journal_id'], origin,
                        config['gate_sha256'], gate_root=config['gate_root'], start=True,
                        root_policy=EXISTING_LIFE_CPU_POLICY, code_policy=config['code_policy'])
                    outcome = {name: value for name, value in outcome.items() if name != 'result'}
                except Exception as error:
                    outcome = dict(status='TOOL_OUTCOME_UNKNOWN_NO_RETRY', executed=None, error_type=type(error).__name__)
                    evidence(receipts, 'REFUSAL', origin=origin, reason=str(error)[:300])
                evidence(receipts, 'OUTCOME', origin=origin, outcome=outcome)
                try:
                    channel.sendall(json.dumps(outcome).encode() + b'\n')
                except OSError:
                    evidence(receipts, 'REPLY_UNKNOWN_NO_RETRY', origin=origin)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    serve(parser.parse_args().config)
