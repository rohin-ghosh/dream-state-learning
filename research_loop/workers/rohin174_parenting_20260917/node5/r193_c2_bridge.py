"""Original C2 recovery-only CPU bridge, using the separately tested math profile."""

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
    document = dict(kind=kind, phase='R193_C2_RECOVERY45_MATH_ENV', time=time.time(), **fields)
    with (root / (kind + '_' + str(time.time_ns()) + '.json')).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def serve(path):
    config = json.loads(path.read_bytes())
    require(config['raw_root'] == '/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life', 'original_C2_only')
    require(config['socket'] == '/tmp/r193_node5_c2_recovery1.sock', 'new_original_C2_socket')
    require(config['cpu_source'] == '/localhome/local-rohing/orch_r153_cpu_smoke_20260917t2350z/source', 'tested_math_source')
    sys.path.insert(0, config['cpu_source'])
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    from gpu.orch_r153_community_transport import cpu_once
    require(digest(verify_gate(config['gate_root'])) == config['gate_sha256'], 'actual_math_gate')
    receipts = path.parent / 'bridge_receipts'
    receipts.mkdir(mode=0o700)
    seen = set()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(config['socket'])
        os.chmod(config['socket'], 0o600)
        server.listen(1)
        server.settimeout(5)
        evidence(receipts, 'READY', pid=os.getpid(), config_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), gate_sha256=config['gate_sha256'])
        while time.time() < config['stop_unix']:
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
                    argv = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
                    require(peer_uid == 2524 and os.readlink(process / 'cwd') == config['native_source']
                            and argv[-3:] == ['native', '--config', config['guard_path']], 'exact_successor_native_only')
                    require(hashlib.sha256(Path(config['guard_path']).read_bytes()).hexdigest() == config['guard_sha256'], 'successor_guard_bytes')
                    origin = json.loads(channel.makefile('rb').readline(4097))
                    require(set(origin) == {'kind', 'record_index', 'record_sha256'}
                            and origin['kind'] == 'TRAIN_CHILD_RESPONSE' and origin['record_index'] > 5406, 'new_recovered_history_only')
                    key = (origin['record_index'], origin['record_sha256'])
                    require(key not in seen, 'no_redispatch')
                    seen.add(key)
                    evidence(receipts, 'ACCEPTED', origin=origin, peer_pid=peer_pid)
                    outcome = cpu_once(config['raw_root'], config['journal_id'], origin, config['gate_sha256'],
                                       gate_root=config['gate_root'], start=True)
                    outcome = {name: value for name, value in outcome.items() if name != 'result'}
                except Exception as error:
                    outcome = dict(status='TOOL_OUTCOME_UNKNOWN_NO_RETRY', executed=None, error_type=type(error).__name__)
                    evidence(receipts, 'REFUSAL', origin=origin, error_type=type(error).__name__, reason=str(error)[:300])
                evidence(receipts, 'OUTCOME', origin=origin, outcome=outcome)
                try:
                    channel.sendall(json.dumps(outcome).encode() + b'\n')
                except OSError:
                    evidence(receipts, 'REPLY_UNKNOWN_NO_RETRY', origin=origin)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    serve(parser.parse_args().config)
