"""Release verified P3 scoring routes and the sole future-only Tool writer."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    root = Path('/localhome/local-rohing/orch_r233_p3_scorer_recovery_20260918/attempt4')
    loaded = json.loads((root / 'LOADED_VERIFIED.json').read_bytes())
    listening = json.loads((root / 'session/LISTENING.json').read_bytes())
    assert loaded['pid'] == listening['pid'] and Path('/proc', str(loaded['pid'])).exists()
    assert loaded['restored_seen_count'] == 48 and loaded['restored_game_snapshot_sha256'] == 'bce88fc1697e07b77cb1177d755f94a9045bcb8161a815eadbdab637a4378466'
    assert loaded['restored_policy_snapshot_sha256'] == 'c5004cb4090ad136a70a0825e2b2783ac38dff4ee34b5e1b5b2d1698ed367b93'
    assert not (root / 'RESTORED.json').exists()
    relay = Path('/localhome/local-rohing/orch_r228_p3_feedback_20260918')
    dependencies = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3/r212/source')
    environment = dict(os.environ, PYTHONPATH=str(dependencies), PYTHONDONTWRITEBYTECODE='1')
    smoke = "import importlib.util;spec=importlib.util.spec_from_file_location('verified_relay'," + repr(str(relay / 'source_v2/relay.py')) + ");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);assert module.messages(dict(origin=dict(record_index=1,record_sha256='a'*64),report=dict(feedback=[])))"
    subprocess.run(['/usr/bin/python3', '-B', '-c', smoke], env=environment, check=True)
    with (relay / 'relay/WRITER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    unit = 'orch-r233-p3-feedback-recovery-attempt2-20260918'
    command = ['sudo', '-n', 'systemd-run', '--unit='+unit, '--property=User=2524', '--property=Group=2524',
        '--property=WorkingDirectory='+str(dependencies), '--property=RuntimeMaxSec='+str(int(1789754370-time.time())),
        '--property=TimeoutStopSec=15', '--property=KillMode=control-group', '--property=UMask=0077',
        '--property=DevicePolicy=closed', '--property=NoNewPrivileges=yes',
        '--property=StandardOutput=append:'+str(root / 'feedback_attempt2.log'),
        '--property=StandardError=append:'+str(root / 'feedback_attempt2.log'),
        '--setenv=PYTHONDONTWRITEBYTECODE=1', '--setenv=PYTHONPATH='+str(dependencies),
        '/usr/bin/python3', '-B', str(root / 'feedback_recovery.py'), '--config', str(root / 'FEEDBACK_CONFIG.private.json')]
    subprocess.run(command, check=True, capture_output=True)
    end = time.monotonic()+8
    while not (root / 'feedback/STARTED.json').exists():
        assert time.monotonic() < end, 'actual_feedback_writer_start'
        time.sleep(.1)
    listeners = subprocess.check_output(['ss', '-xlnH'], text=True)
    assert listening['socket'] in listeners
    routes = []
    for name in ['/tmp/r224_caption_bridge.sock', '/tmp/r226_caption_bridge.sock']:
        assert name not in listeners, 'no_live_listener_replacement'
        path = Path(name)
        backup = path.with_name(path.name+'.before-r233-recovery')
        assert not backup.exists() and not backup.is_symlink()
        if path.exists() or path.is_symlink():
            path.rename(backup)
        temporary = path.with_name(path.name+'.r233.pending')
        temporary.symlink_to(listening['socket'])
        os.replace(temporary, path)
        routes.append(name)
    proof = dict(unix=time.time(), loaded=loaded, listening=listening,
        feedback_started=json.loads((root / 'feedback/STARTED.json').read_bytes()),
        dependency_hashes={name:hashlib.sha256((dependencies / name).read_bytes()).hexdigest()
            for name in ['gpu/orch_r127_pilot_console.py', 'organism_v6/orch_r125_plain_context.py']},
        legacy_routes_restored=routes, native_signals=[], parent_publications=[], historical_replays=0,
        first_future_score='pending')
    (root / 'RESTORED.json').write_text(json.dumps(proof, indent=2))
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
