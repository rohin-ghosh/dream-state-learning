"""Original-C2-only prospective CPU environment cutover; never restart native."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import socket
import stat
import struct
import subprocess
import sys
import time


PHASE = 'R188_C2_MATH_ENV_V1'
LIFE = '/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life'
CONTROL = '/localhome/local-rohing/orch_r153_r188_C2_20260917_recovery1'
CANDIDATE = '/localhome/local-rohing/orch_r153_cpu_smoke_20260917t2350z'
JOURNAL = '260be8b8710a42559b291797c6e14983'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    path = Path(path)
    require(path.resolve() == path.absolute() and path.is_file(), 'regular_unaliased_pin')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(root, name, **fields):
    document = dict(phase=PHASE, time=time.time(), event=name, **fields)
    path = Path(root) / f'{name}_{time.time_ns()}.json'
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return document


def identity(pid):
    root = Path('/proc') / str(pid)
    fields = (root / 'stat').read_text().split(') ', 1)[1].split()
    status = dict(line.split(':', 1) for line in (root / 'status').read_text().splitlines())
    return dict(pid=pid, start=int(fields[19]), uid=status['Uid'].split(),
                argv=(root / 'cmdline').read_bytes().decode().strip('\0').split('\0'),
                cwd=os.readlink(root / 'cwd'), sigcgt=status['SigCgt'].strip(),
                sigign=status['SigIgn'].strip())


def verify_identity(expected):
    require(identity(expected['pid']) == expected, 'exact_process_identity_changed')


def listener_state(owner, socket_inode):
    verify_identity(owner)
    root = Path('/proc') / str(owner['pid'])
    links = []
    for path in (root / 'fd').iterdir():
        try:
            links.append(os.readlink(path))
        except FileNotFoundError:
            return False
    if [link for link in links if link.startswith('socket:')] != [f'socket:[{socket_inode}]']:
        return False
    if (root / 'task' / str(owner['pid']) / 'children').read_text().strip():
        return False
    output = subprocess.run(['ss', '-xlpnH'], capture_output=True, text=True, check=True).stdout
    matches = [line.split() for line in output.splitlines()
               if f'pid={owner["pid"]},' in line and str(socket_inode) in line.split()]
    return len(matches) == 1 and matches[0][1] == 'LISTEN' and matches[0][2] == '0'


def replace_listener(server, temporary, destination, expected_stat):
    current = os.lstat(destination)
    require(stat.S_ISSOCK(current.st_mode) and current.st_uid == os.getuid()
            and (current.st_dev, current.st_ino) == tuple(expected_stat), 'original_socket_changed')
    server.bind(str(temporary))
    os.chmod(temporary, 0o600)
    server.listen(8)
    os.replace(temporary, destination)


def drain_and_retire(owner, socket_inode, lock_path, receipt_root, timeout=90):
    deadline = time.monotonic() + timeout
    stable = 0
    while time.monotonic() < deadline:
        stable = stable + 1 if listener_state(owner, socket_inode) else 0
        if stable >= 3:
            break
        time.sleep(0.15)
    require(stable >= 3, 'old_bridge_drain_timeout_no_signal')
    descriptor = os.open(lock_path, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                and before.st_nlink == 1, 'existing_CPU_lock_required')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(listener_state(owner, socket_inode), 'old_bridge_not_idle_no_signal')
        pidfd = os.pidfd_open(owner['pid'])
        try:
            verify_identity(owner)
            record(receipt_root, 'OLD_BRIDGE_DRAINED_STOP_INTENT', owner=owner,
                   lock_inode=before.st_ino, socket_inode=socket_inode,
                   native_signals=0, group_signals=0)
            signal.pidfd_send_signal(pidfd, signal.SIGTERM)
            require(bool(select.select([pidfd], [], [], 10)[0]), 'old_bridge_exit_unconfirmed_no_retry')
            record(receipt_root, 'OLD_BRIDGE_EXITED', owner=owner)
        finally:
            os.close(pidfd)
        require(os.stat(lock_path).st_ino == before.st_ino, 'CPU_lock_inode_changed')
    finally:
        os.close(descriptor)


def head(root):
    path = max((Path(root) / 'stream/records').glob('*.json'))
    document = json.loads(path.read_bytes())
    return dict(index=document['index'], kind=document['kind'], sha256=document['sha256'],
                file_sha256=sha(path))


def requests(root):
    result = []
    for path in sorted((Path(root) / 'community_cpu').glob('*/INTENT.json')):
        value = json.loads(path.read_bytes())
        result_path = path.parent.parent / 'spool' / path.parent.name / 'RESULT.json'
        published = path.parent / 'PUBLISHED.json'
        result.append(dict(request_id=path.parent.name, origin=value['request']['origin'],
                           intent_sha256=sha(path), published_sha256=sha(published) if published.exists() else None,
                           result_sha256=sha(result_path) if result_path.exists() else None))
    return result


def preflight(config):
    require(config['phase'] == PHASE and config['raw_root'] == LIFE
            and config['journal_id'] == JOURNAL and config['source'] == CANDIDATE + '/source',
            'original_C2_only')
    require(config['socket'] == '/tmp/r188_node5_c2_recovery1.sock'
            and config['old_config'] == CONTROL + '/BRIDGE.json'
            and config['gate_root'] == CANDIDATE + '/gate', 'fixed_original_bindings')
    require(config['stop_unix'] == 1789776000 and time.time() < config['stop_unix'], 'unchanged_wall')
    for path, expected in config['pins'].items():
        require(sha(path) == expected, 'source_or_evidence_pin_changed:' + path)
    original = json.loads(Path(config['old_config']).read_bytes())
    require(all(original[key] == config[key] for key in ('raw_root', 'journal_id', 'socket', 'stop_unix')),
            'original_routing_and_wall')
    candidate = json.loads(Path(CANDIDATE, 'CANDIDATE.json').read_bytes())
    for name, expected in candidate['source_files'].items():
        require(sha(Path(config['source']) / name) == expected, 'candidate_source_changed:' + name)
    complete44 = json.loads(Path(LIFE, 'stream/records/00000000000000005337.json').read_bytes())
    require(complete44['kind'] == 'SLEEP_COMPLETE' and complete44['sha256'] ==
            '30002558e2a5f620f642d5e7843e3f9eb7c41f7a174bf2d4a0f54345e077b078', 'complete44_required')
    verify_identity(config['native'])
    verify_identity(config['supervisor'])
    verify_identity(config['old_bridge'])
    sys.path.insert(0, config['source'])
    from gpu import orch_r125_cpu_experiment as cpu
    require(cpu.digest(cpu.verify_gate(config['gate_root'])) == config['gate_sha256'], 'actual_new_gate')
    require(Path(cpu.profile.__file__).resolve() == Path(config['source']) / 'gpu/orch_r125_cpu_confinement_probe.py',
            'actual_profile_import')
    return cpu


def dispatch(config, origin, seen, cpu_once):
    require(type(origin) is dict and set(origin) == {'kind', 'record_index', 'record_sha256'}
            and origin['kind'] == 'TRAIN_CHILD_RESPONSE' and type(origin['record_index']) is int
            and origin['record_index'] > 5337, 'prospective_complete44_origin_only')
    key = (origin['record_index'], origin['record_sha256'])
    require(key not in seen, 'previous_attempt_never_redispatched')
    seen.add(key)
    outcome = cpu_once(config['raw_root'], config['journal_id'], origin, config['gate_sha256'],
                       gate_root=config['gate_root'], start=True)
    return {key: value for key, value in outcome.items() if key != 'result'}


def serve(config_path):
    config = json.loads(Path(config_path).read_bytes())
    receipts = Path(config_path).parent / 'receipts'
    receipts.mkdir(mode=0o700)
    record(receipts, 'STARTED', helper_sha256=sha(__file__), config_sha256=sha(config_path), owner=identity(os.getpid()))
    cpu = preflight(config)
    from gpu.orch_r153_community_transport import cpu_once
    old_requests = requests(LIFE)
    seen = {(item['origin']['record_index'], item['origin']['record_sha256']) for item in old_requests}
    before = head(LIFE)
    record(receipts, 'PREFLIGHT', head=before, old_requests=old_requests,
           profile_sha256=sha(cpu.profile.__file__), gate_sha256=config['gate_sha256'],
           pure_matched_arm_result=False, preserved_cycles=[42, 43, 44], native=config['native'])
    deadline = time.monotonic() + 90
    while not listener_state(config['old_bridge'], config['old_socket_inode']):
        require(time.monotonic() < deadline, 'inflight_old_bridge_not_settled_no_changes')
        time.sleep(0.25)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        record(receipts, 'SOCKET_ROUTE_INTENT', head=head(LIFE), no_native_reset=True)
        replace_listener(server, config['temporary_socket'], config['socket'], config['socket_stat'])
        record(receipts, 'SOCKET_ROUTE_EFFECTIVE', head=head(LIFE), new_socket_inode=os.lstat(config['socket']).st_ino)
        drain_and_retire(config['old_bridge'], config['old_socket_inode'],
                         Path(LIFE) / 'community_cpu/OWNER.lock', receipts)
        verify_identity(config['native'])
        verify_identity(config['supervisor'])
        for path, expected in config['preserved_pins'].items():
            require(sha(path) == expected, 'preserved_original_changed:' + path)
        for item in requests(LIFE):
            seen.add((item['origin']['record_index'], item['origin']['record_sha256']))
        record(receipts, 'EFFECTIVE', head=head(LIFE), native=config['native'], supervisor=config['supervisor'],
               gate_sha256=config['gate_sha256'], original_bridge_config_sha256=sha(config['old_config']),
               native_signals=0, native_resets=0, historical_redispatches=0, pure_matched_arm_result=False)
        server.settimeout(5)
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
                    require(peer_pid == config['native']['pid'] and peer_uid == os.getuid(), 'original_native_peer_only')
                    verify_identity(config['native'])
                    origin = json.loads(channel.makefile('rb').readline(4097))
                    record(receipts, 'TOOL_ACCEPTED', origin=origin)
                    outcome = dispatch(config, origin, seen, cpu_once)
                except Exception as error:
                    outcome = dict(status='TOOL_OUTCOME_UNKNOWN_NO_RETRY', executed=None, error_type=type(error).__name__)
                record(receipts, 'TOOL_OUTCOME', origin=origin, outcome=outcome)
                try:
                    channel.sendall(json.dumps(outcome).encode() + b'\n')
                except OSError as error:
                    record(receipts, 'REPLY_UNCONFIRMED_NO_RETRY', origin=origin, error_type=type(error).__name__)
        record(receipts, 'WALL_EXIT')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    arguments = parser.parse_args()
    try:
        serve(arguments.config)
    except BaseException as error:
        destination = Path(arguments.config).parent / 'receipts'
        if destination.is_dir():
            record(destination, 'FAILED_NO_RETRY', error_type=type(error).__name__, reason=str(error))
        raise
