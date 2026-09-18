"""Sole-writer exact-state adoption after measured warm readiness, never replay."""

import re
import shutil
import subprocess
import time
from pathlib import Path

from research_loop.workers.rohin233_ovx4_recovery_20260918.prepare_renewal import read, ref, write, unit_run, MODULE


def activate(root):
    root=Path(root)
    config=read(root/'CONFIG.private.json')
    warm=read(root/'MODEL_WARM.json')
    assert Path('/proc',str(warm['pid'])).exists()
    pid=config['predecessor_pid']
    stat=Path('/proc',str(pid),'stat')
    assert stat.read_text().rsplit(')',1)[1].split()[19]==config['predecessor_start_ticks']
    endpoint=Path(config['endpoint'])
    bridge=root/'bridge'
    bridge.mkdir(mode=0o700)
    bridge_config=dict(root=str(bridge),endpoint=str(endpoint),endpoint_inode=endpoint.stat().st_ino,
        deadline_unix=config['deadline_unix'],lease_boundary_unix=config['lease_boundary_unix'])
    write(root/'BRIDGE_CONFIG.private.json',bridge_config)
    unit_run(root,root/'source',root.name+'-bridge',config['deadline_unix'],MODULE+'.lease_bridge',root/'BRIDGE_CONFIG.private.json')
    end=time.time()+95
    while not (bridge/'ACTIVE.json').exists():
        assert time.time()<end
        time.sleep(.1)
    while True:
        sockets=subprocess.check_output(['ss','-xapnH'],text=True)
        active=[line for line in sockets.splitlines() if 'ESTAB' in line and re.search(r'pid='+str(pid)+r'[,)]',line)]
        if not active and all(read(path)['phase']=='COMPLETE' for path in config['states'].values()):
            break
        assert time.time()<end,'no_stop_of_active_or_incomplete_scorer'
        time.sleep(.1)
    snapshots={}
    for identifier,path in config['states'].items():
        before=ref(path)
        target=root/('PRESERVED_'+identifier+'.private.json')
        shutil.copyfile(path,target)
        assert ref(path)==before and ref(target)['sha256']==before['sha256']
        snapshots[identifier]=ref(target)
    units=re.findall(r'(orch-r233-[^/\n]+\.service)',Path('/proc',str(pid),'cgroup').read_text())
    assert len(units)==1 and stat.read_text().rsplit(')',1)[1].split()[19]==config['predecessor_start_ticks']
    subprocess.run(['sudo','-n','systemctl','stop',units[0]],check=True,capture_output=True,timeout=20)
    assert not stat.exists()
    for identifier,path in config['states'].items():
        assert ref(path)['sha256']==snapshots[identifier]['sha256']
    write(root/'HANDOFF.json',dict(unix=time.time(),sessions=snapshots,predecessor_pid=pid,
        old_scorer_unit=units[0],old_scorer_drained=True,native_signals=[],scoring_replays=0))
    listener=root/'listener/LISTENING.json' if config['kind']=='p3' else root/'sockets/LISTENING.json'
    while not (root/'LOADED.json').exists() or not listener.exists() or read(listener).get('pid')!=warm['pid']:
        assert time.time()<end,'adoption_timeout_preserve_receipts'
        time.sleep(.1)
    loaded=read(root/'LOADED.json')
    assert loaded['pid']==warm['pid'] and Path('/proc',str(loaded['pid'])).exists()
    assert sorted(item['restored_seen_count'] for item in loaded['sessions'])==sorted(len(read(item['path'])['seen']) for item in snapshots.values())
    target=config['socket'] if config['kind']=='p3' else str(root/'sockets'/('base.sock' if config['kind']=='base' else 'native.sock'))
    write(bridge/'TARGET.json',dict(socket=target,loaded_sha256=ref(root/'LOADED.json')['sha256']))
    receipt=dict(unix=time.time(),status='ADOPTED_LISTENER_LIVE_FUTURE_SCORES_PENDING',actual_loaded=loaded,
        bridge_pid=read(bridge/'ACTIVE.json')['pid'],historical_rescoring=False,native_signals=[])
    write(root/'ADOPTED.json',receipt)
    return receipt
