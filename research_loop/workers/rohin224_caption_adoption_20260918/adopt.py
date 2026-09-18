"""Owner-bound scorer handover; never signals or changes the caption learner."""

import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import sys
import time

from export_session import export_session, require


ROOT = Path('/localhome/local-rohing/orch_r224_caption_scorer_20260918')
OLD = Path('/localhome/local-rohing/orch_r213_caption_service_20260918/session1')
OLD_PID = 224224
OLD_START = '27865890'
ENDPOINT = Path('/tmp/r212_caption_n4.sock')
LEGACY = Path('/tmp/r224_caption_legacy.sock')
BRIDGE = Path('/tmp/r224_caption_bridge.sock')
TARGET = Path('/tmp/r224_caption_new.sock')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
GPU = 'GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d'


def save(name, document):
    path = ROOT / name
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(document, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def read(path):
    return json.loads(Path(path).read_bytes())


def process_sockets():
    sockets = set()
    for descriptor in (Path('/proc') / str(OLD_PID) / 'fd').iterdir():
        try:
            target = os.readlink(descriptor)
        except FileNotFoundError:
            continue
        if target.startswith('socket:'):
            sockets.add(target)
    return sockets


def quiet(baseline):
    lines = subprocess.check_output(['ss', '-xlnpH'], text=True).splitlines()
    listeners = [line.split() for line in lines if f'pid={OLD_PID},' in line
                 and '/tmp/r213_caption_n4.sock' in line]
    return (len(listeners) == 1 and listeners[0][2] == '0'
            and process_sockets() <= baseline)


def main():
    sys.path.insert(0, str(ROOT / 'source'))
    from gpu import ny_caption_data as data
    from gpu.ny_caption_game import DevelopmentManifest
    from gpu.ny_caption_life import child_act

    pid_root = Path('/proc') / str(OLD_PID)
    require(pid_root.joinpath('stat').read_text().rpartition(') ')[2].split()[19] == OLD_START,
            'exact_original_scorer_process')
    require(os.getuid() == 2524, 'same_owner')
    original_args = pid_root.joinpath('cmdline').read_bytes().decode().rstrip('\0').split('\0')
    require('gpu.ny_caption_life_service' in original_args, 'original_native_scorer')
    loaded, listening = read(OLD / 'LOADED.json'), read(OLD / 'LISTENING.json')
    require(loaded['pid'] == OLD_PID and listening['pid'] == OLD_PID, 'same_scorer_receipts')
    require(hashlib.sha256(Path(loaded['source']['path']).read_bytes()).hexdigest()
            == loaded['source']['sha256'], 'unchanged_old_source')
    gpu_line = subprocess.check_output(['nvidia-smi', '--id=0', '--query-gpu=uuid,memory.used,memory.total',
                                       '--format=csv,noheader,nounits'], text=True).strip().split(', ')
    require(gpu_line[0] == GPU and int(gpu_line[2]) - int(gpu_line[1]) >= 20000,
            'same_gpu_and_parallel_loading_headroom')
    seconds = int(listening['deadline_unix'] - time.time())
    require(180 < seconds <= 21600, 'preserve_service_deadline')
    require(stat.S_ISSOCK(ENDPOINT.lstat().st_mode), 'original_endpoint_is_socket')
    for path in (LEGACY, BRIDGE, TARGET, ROOT / 'session2'):
        require(not path.exists() and not path.is_symlink(), 'new_handover_paths')
    bundle = read(ROOT / 'BUNDLE.json')
    for relative, digest in bundle['files'].items():
        require(hashlib.sha256((ROOT / 'source' / relative).read_bytes()).hexdigest() == digest,
                'tested_replacement_source:' + relative)
    manifest = DevelopmentManifest.from_mapping(data.bound(loaded['game_manifest']))
    descriptors = [dict(contest_id=contest.contest_id, canonical_scene=contest.canonical_scene)
                   for contest in manifest.contests]
    export_session(OLD, descriptors, verify_origin=child_act)
    baseline = process_sockets()
    require(quiet(baseline), 'old_listener_idle_before_cut')
    save('PREPARED.json', dict(unix=time.time(), old_pid=OLD_PID, old_start_ticks=OLD_START,
        gpu_uuid=GPU, bundle=bundle, old_deadline=listening['deadline_unix'], learner_signals=[]))
    with (ROOT / 'bridge.log').open('xb') as log:
        bridge = subprocess.Popen([PYTHON, '-B', str(ROOT / 'operator' / 'bridge.py'),
            '--listen', str(BRIDGE), '--target', str(TARGET), '--receipt', str(ROOT / 'BRIDGE_READY.json'),
            '--seconds', str(seconds), '--ready', str(ROOT / 'LOADED_VERIFIED.json')],
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    ready_deadline = time.monotonic() + 10
    while not (ROOT / 'BRIDGE_READY.json').exists():
        require(bridge.poll() is None and time.monotonic() < ready_deadline, 'bridge_ready_before_switch')
        time.sleep(.1)
    original_inode = ENDPOINT.stat().st_ino
    os.link(ENDPOINT, LEGACY)
    require(LEGACY.stat().st_ino == original_inode, 'legacy_listener_alias')
    route = ENDPOINT.with_name('.r224_caption_route.pending')
    require(not route.exists() and not route.is_symlink(), 'new_route_temporary')
    route.symlink_to(BRIDGE)
    os.replace(route, ENDPOINT)
    save('ROUTED.json', dict(unix=time.time(), bridge_pid=bridge.pid, old_inode=original_inode,
        old_listener_alias=str(LEGACY), learner_signals=[]))
    drain_deadline = time.monotonic() + 8
    stable = 0
    previous = None
    while stable < 3:
        require(time.monotonic() < drain_deadline, 'old_dispatch_drains_within_budget')
        state, receipt = export_session(OLD, descriptors, verify_origin=child_act)
        digest = hashlib.sha256(data.canonical(receipt)).hexdigest()
        stable = stable + 1 if quiet(baseline) and digest == previous else 0
        previous = digest
        time.sleep(.25)
    state_path = save('RESUME_STATE.private.json', state)
    state_sha = hashlib.sha256(state_path.read_bytes()).hexdigest()
    save('EXPORTED.json', dict(receipt, unix=time.time(), state_sha256=state_sha))
    args = original_args[:]
    for option, value in {'--output': str(ROOT / 'session2'), '--socket': str(TARGET),
                          '--seconds': str(int(listening['deadline_unix'] - time.time()))}.items():
        args[args.index(option) + 1] = value
    args += ['--resume-state', str(state_path), '--resume-state-sha256', state_sha]
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU, PYTHONPATH=str(ROOT / 'source'),
                       HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
    with (ROOT / 'scorer.log').open('xb') as log:
        scorer = subprocess.Popen(args, cwd=ROOT / 'source', env=environment, stdout=log,
                                  stderr=subprocess.STDOUT, start_new_session=True)
    save('DISPATCHED.json', dict(pid=scorer.pid, unix=time.time(), state_sha256=state_sha,
                               source_files=bundle['files'], learner_signals=[]))
    ready_deadline = time.monotonic() + 80
    while not (ROOT / 'session2' / 'LISTENING.json').exists():
        require(scorer.poll() is None and time.monotonic() < ready_deadline, 'replacement_scorer_ready')
        time.sleep(.2)
    replacement = read(ROOT / 'session2' / 'LOADED.json')
    require(replacement['pid'] == scorer.pid and replacement['life_root'] == loaded['life_root'],
            'same_life_new_scorer_loaded')
    require(replacement['source']['sha256'] == bundle['files']['gpu/ny_caption_life_service.py'],
            'tested_scorer_loaded')
    require(replacement.get('resume_state_input_sha256') == state_sha
            and replacement.get('resumed_complete_state') is True
            and replacement.get('restored_seen_count') == len(state['seen'])
            and replacement.get('restored_game_snapshot_sha256') == data.digest(state['game'])
            and replacement.get('restored_policy_snapshot_sha256') == data.digest(state['policy']),
            'measured_restored_state_before_proxy_release')
    save('LOADED_VERIFIED.json', dict(unix=time.time(), old_pid=OLD_PID, new_pid=scorer.pid,
        loaded=replacement, state_sha256=state_sha, complete_attempts=receipt['complete_attempts'],
        historical_rescoring=False, novelty_reset=False, learner_signals=[]))
    descriptor = os.pidfd_open(OLD_PID)
    try:
        require(pid_root.joinpath('stat').read_text().rpartition(') ')[2].split()[19] == OLD_START,
                'same_original_scorer_before_retirement')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
    finally:
        os.close(descriptor)
    save('OLD_SCORER_RETIREMENT.json', dict(unix=time.time(), pid=OLD_PID,
        signal='SIGTERM', learner_signals=[], new_scorer_loaded=True))


if __name__ == '__main__':
    main()
