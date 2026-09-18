"""Drain old scorer only, transfer exact saved state, then release queued RPCs."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from research_loop.workers.rohin233_ovx4_recovery_20260918.prepare_renewal import read, ref, write, unit_run, MODULE


def activate(root):
    root = Path(root)
    config = read(root / 'CONFIG.private.json')
    prior = read(config['prior_config']['path'])
    assert ref(config['prior_config']['path']) == config['prior_config']
    assert (root / 'MODEL_WARM.json').exists(), 'actual_model_warm_required'
    pid = config['predecessor_pid']
    assert Path('/proc', str(pid), 'stat').read_text().rsplit(')',1)[1].split()[19] == config['predecessor_start_ticks']
    if config['kind'] == 'p3':
        endpoint = Path(prior['socket'])
        states = dict(p3=Path(prior['recovery_root']) / 'session/SESSION_STATE.private.json')
        target = config['socket']
    elif config['kind'] == 'shared':
        endpoint = Path(prior['service_root']) / 'native.sock'
        states = {identifier:Path(prior['service_root']) / 'sessions' / identifier / 'SESSION_STATE.private.json'
            for identifier in prior['sessions']}
        target = str(root / 'sockets/native.sock')
    else:
        raise ValueError('base_requires_separate_parent_and_player_boundary')
    bridge = root / 'bridge'
    bridge.mkdir(mode=0o700)
    bridge_config = dict(root=str(bridge), endpoint=str(endpoint), endpoint_inode=endpoint.stat().st_ino,
        deadline_unix=config['deadline_unix'], lease_boundary_unix=config['lease_boundary_unix'])
    write(root / 'BRIDGE_CONFIG.private.json', bridge_config)
    unit_run(root, root / 'source', root.name+'-bridge', config['deadline_unix'], MODULE+'.lease_bridge',
        root / 'BRIDGE_CONFIG.private.json')
    end = time.time()+90
    while not (bridge / 'ACTIVE.json').exists():
        assert time.time() < end, 'bridge_admission_failed'
        time.sleep(.1)
    while True:
        sockets = subprocess.check_output(['ss','-xapnH'], text=True)
        active = [line for line in sockets.splitlines() if 'ESTAB' in line and re.search(r'pid='+str(pid)+r'[,)]', line)]
        if not active and all(read(path)['phase'] == 'COMPLETE' for path in states.values()):
            break
        assert time.time() < end, 'no_forced_stop_of_active_scorer'
        time.sleep(.1)
    snapshots = {}
    for identifier, path in states.items():
        before = ref(path)
        destination = root / ('PRESERVED_'+identifier+'.private.json')
        shutil.copyfile(path, destination)
        assert ref(path) == before and ref(destination)['sha256'] == before['sha256']
        state = read(destination)
        assert state['phase'] == 'COMPLETE' and len(state['seen']) == len(set(state['seen']))
        snapshots[identifier] = ref(destination)
    cgroup = Path('/proc', str(pid), 'cgroup').read_text()
    units = re.findall(r'(orch-r233-[^/\n]+\.service)', cgroup)
    assert len(units) == 1 and Path('/proc', str(pid), 'stat').read_text().rsplit(')',1)[1].split()[19] == config['predecessor_start_ticks']
    subprocess.run(['sudo','-n','systemctl','stop',units[0]], check=True, capture_output=True, timeout=20)
    assert not Path('/proc', str(pid)).exists()
    for identifier,path in states.items():
        assert ref(path)['sha256'] == snapshots[identifier]['sha256'], 'drained_state_unchanged'
    write(root / 'HANDOFF.json', dict(unix=time.time(), sessions=snapshots, predecessor_pid=pid,
        old_scorer_unit=units[0], old_scorer_drained=True, native_signals=[], scoring_replays=0))
    expected_listener = root / ('session/LISTENING.json' if config['kind'] == 'p3' else 'sockets/LISTENING.json')
    while not (root / 'LOADED.json').exists() or not expected_listener.exists():
        assert time.time() < end, 'warm_successor_adoption_timeout'
        time.sleep(.1)
    loaded = read(root / 'LOADED.json')
    assert Path('/proc',str(loaded['pid'])).exists()
    assert sorted(item['restored_seen_count'] for item in loaded['sessions']) == sorted(len(read(item['path'])['seen']) for item in snapshots.values())
    write(bridge / 'TARGET.json', dict(socket=target, loaded_sha256=ref(root / 'LOADED.json')['sha256']))
    receipt = dict(unix=time.time(), kind=config['kind'], role=root.name, physical=config['physical'],
        actual_loaded=loaded, bridge=read(bridge / 'ACTIVE.json'), deadline_unix=config['deadline_unix'],
        predecessor_scorer_stopped_only_after_drain=pid, native_signals=[], historical_rescoring=False)
    write(root / 'RENEWED.json', receipt)
    return receipt
