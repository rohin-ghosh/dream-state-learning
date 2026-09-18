"""Synchronous, actual-origin repository tools; never execute child code."""

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


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def call(config, origin):
    binding = json.loads((Path(__file__).resolve().parents[2] / 'BRIDGE.json').read_bytes())
    require(config['trial_id'] == 'R202_REPO_C_node2_clone1', 'repo_clone_only')
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
        channel.settimeout(160)
        channel.connect(binding['socket'])
        channel.sendall(json.dumps(origin).encode() + b'\n')
        return json.loads(channel.makefile('rb').readline(262145))


def serve(path):
    config = json.loads(path.read_bytes())
    sys.path.insert(0, config['native_source'])
    from research_loop.workers.rohin183_repo_learning_20260917 import tools
    settings = json.loads(Path(config['repo_config']).read_bytes())
    require(hashlib.sha256(Path(config['repo_config']).read_bytes()).hexdigest() == config['repo_config_sha256'], 'exact_repo_config')
    tools.manifest(settings)
    receipts = path.parent / 'bridge_receipts'
    receipts.mkdir(mode=0o700)
    seen = set()
    sequence = 0
    def evidence(kind, **fields):
        target = receipts / (kind + '_' + str(time.time_ns()) + '.json')
        with target.open('x') as output:
            json.dump(dict(kind=kind, observed_unix=time.time(), **fields), output, sort_keys=True)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(config['socket'])
        os.chmod(config['socket'], 0o600)
        server.listen(1)
        server.settimeout(2)
        evidence('READY', pid=os.getpid(), repo_config_sha256=config['repo_config_sha256'], code_execution=False)
        while time.time() < config['stop_unix'] and sequence < tools.ACTION_LIMIT:
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
                        and arguments[-3:] == ['native', '--config', config['guard_path']], 'exact_repo_native')
                    require(hashlib.sha256(Path(config['guard_path']).read_bytes()).hexdigest() == config['guard_sha256'], 'guard_binding')
                    origin = json.loads(channel.makefile('rb').readline(4097))
                    require(set(origin) == {'kind', 'record_index', 'record_sha256'}
                        and origin['kind'] == 'TRAIN_CHILD_RESPONSE' and origin['record_index'] > 5846, 'new_repo_response_only')
                    key = (origin['record_index'], origin['record_sha256'])
                    require(key not in seen, 'no_redispatch')
                    seen.add(key)
                    record_path = Path(config['raw_root']) / 'stream/records' / f"{origin['record_index']:020d}.json"
                    require(record_path.stat().st_size < 32 * 1024**2 and not record_path.is_symlink(), 'bounded_actual_response')
                    record = json.loads(record_path.read_bytes())
                    require(record['kind'] == 'RESPONSE' and record['journal_id'] == config['journal_id']
                        and record['sha256'] == origin['record_sha256']
                        and digest({name: value for name, value in record.items() if name != 'sha256'}) == record['sha256'], 'actual_response_hash_binding')
                    action = tools.request(record['document']['response']['raw'])
                    require(action is not None, 'explicit_repo_request_required_no_CPU_fallback')
                    source = dict(actor='child', split='TRAIN', record_index=origin['record_index'], record_sha256=origin['record_sha256'])
                    evidence('INTENT', origin=origin, action=action, sequence=sequence)
                    reference = tools.execute(settings, action, source, sequence)
                    outcome = dict(status='PUBLISHED', executed=False, code_executed=False, tool='REPOSITORY',
                        action=action['action'], actual_tool_receipt=reference, origin=origin,
                        semantics='Actual repository operation, not a CPU/test execution or successful scientific result')
                    sequence += 1
                except Exception as error:
                    outcome = dict(status='TOOL_OUTCOME_UNKNOWN_NO_RETRY', executed=None, tool='REPOSITORY', error_type=type(error).__name__)
                    evidence('REFUSAL', origin=origin, reason=str(error)[:300])
                    sequence += 1
                evidence('OUTCOME', origin=origin, outcome=outcome)
                try:
                    channel.sendall(json.dumps(outcome).encode() + b'\n')
                except OSError:
                    evidence('REPLY_UNKNOWN_NO_RETRY', origin=origin)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    serve(parser.parse_args().config)
