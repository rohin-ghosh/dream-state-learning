"""Same MATH-C journal/state, new R204 source at a freshly preserved COMPLETE."""

import argparse
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import time
import uuid

from math_c import HOME, PYTHON, host, read, require, sha, write
from apply_r204 import layer


TARGET = HOME / 'reload_r204'


def prepare():
    host()
    TARGET.mkdir()
    shutil.copytree(HOME/'source', TARGET/'source')
    control = TARGET/'control'
    control.mkdir()
    plan = read(HOME/'control/PLAN.json')
    old_source = Path(plan['source_root'])
    plan['source_root'] = str(TARGET/'source')
    if plan.get('startup_context'):
        plan['startup_context']['path'] = str(TARGET/'source'/Path(plan['startup_context']['path']).relative_to(old_source))
    write(control/'PLAN.json', plan)
    allocation, guard = read(HOME/'control/ALLOCATION.json'), read(HOME/'control/GUARD.json')
    allocation.update(plan_sha256=sha(control/'PLAN.json'), declared_unix=time.time())
    write(control/'ALLOCATION.json', allocation)
    guard.update(plan_path=str(control/'PLAN.json'), plan_sha256=sha(control/'PLAN.json'),
        allocation_path=str(control/'ALLOCATION.json'), allocation_sha256=sha(control/'ALLOCATION.json'),attempt_dir=str(control))
    guard['device_containment']['unit']='orch-r136-native-'+uuid.uuid4().hex
    write(control/'GUARD.json', guard)
    bridge = read(HOME/'BRIDGE.json')
    bridge.update(socket=str(HOME/'r204.sock'), native_source=str(TARGET/'source'),
        guard_path=str(control/'GUARD.json'),guard_sha256=sha(control/'GUARD.json'))
    write(TARGET/'BRIDGE.json',bridge)
    write(TARGET/'RECEIVING_READY.json',dict(status='CPU_TESTED_NOT_LIVE',guard_sha256=sha(control/'GUARD.json'),same_life=True))
    layer(TARGET,TARGET/'source',control)
    original_guard=read(HOME/'control/GUARD.json')
    original_plan=read(original_guard['plan_path'])
    loaded=read(HOME/'FIRST_LOADED.json')
    process=Path('/proc')/str(loaded['pid'])
    require(process.exists() and os.readlink(process/'cwd')==str(old_source), 'same_live_MATH_C_native')
    fields=(process/'stat').read_text().rsplit(')',1)[1].split()
    write(HOME/'RELOAD6_CENSUS.json',dict(learners=[dict(plan=original_plan,guard_path=str(HOME/'control/GUARD.json'),
        guard_sha256=sha(HOME/'control/GUARD.json'),backing_root=str(Path(original_plan['root']).resolve()),
        native=dict(pid=loaded['pid'],start_ticks=fields[19]))]))
    withdrawal=(HOME/'withdraw_math_c.py').read_text().replace('from math_c import','from reload_support import')
    withdrawal=withdrawal.replace("HOME / 'control", "HOME / 'reload_r204/control")
    withdrawal=withdrawal.replace("HOME / 'BRIDGE.json'", "HOME / 'reload_r204/BRIDGE.json'")
    withdrawal=withdrawal.replace('WITHDRAWAL_WAITER.json','WITHDRAWAL_WAITER_R204.json')
    (HOME/'withdraw_r204.py').write_text(withdrawal)
    support=(HOME/'arm_support.py').read_text().replace("SOURCE = HOME / 'source'", "SOURCE = HOME / 'reload_r204/source'")
    (HOME/'reload_support.py').write_text(support)
    print(json.dumps(dict(status='R204_SAME_LIFE_RECEIVING_READY',root=plan['root'],source=plan['source_root'])))


def exact_stop(pid, expected_tail):
    process=Path('/proc')/str(pid)
    if not process.exists():
        return
    identity=lambda: ((process/'stat').read_text().rsplit(')',1)[1].split()[19],(process/'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'))
    before=identity()
    require(before[1][-len(expected_tail):]==expected_tail and process.stat().st_uid==2524,'exact_owned_sidecar')
    descriptor=os.pidfd_open(pid)
    try:
        require(identity()==before,'unchanged_sidecar_identity')
        signal.pidfd_send_signal(descriptor,signal.SIGTERM)
        require(bool(select.select([descriptor],[],[],20)[0]),'sidecar_exited_without_KILL')
    finally:
        os.close(descriptor)


def launch():
    host()
    retired=read(HOME/'reload_r204_boundary/RETIRED.json')
    require(retired['status']=='EXACT_COMPLETE_PRESERVED_RETIRED','same_life_fresh_COMPLETE_preserved')
    withdrawn = read(TARGET/'control/PLAN.json')['max_sleeps'] == 57
    original=read(HOME/('WITHDRAWN_DISPATCHED.json' if withdrawn else 'DISPATCHED.json'))
    old_bridge = HOME/'withdrawn/BRIDGE.json' if withdrawn else HOME/'BRIDGE.json'
    exact_stop(original['bridge_pid'],['--config',str(old_bridge)])
    bridge=read(TARGET/'BRIDGE.json')
    bridge['first_new_record']=int(Path(retired['saved']['record_path']).stem)+1
    (TARGET/'BRIDGE.json').rename(TARGET/'BRIDGE_PREBOUNDARY.json')
    write(TARGET/'BRIDGE.json',bridge)
    with (TARGET/'BRIDGE.log').open('x') as log:
        server=subprocess.Popen([str(PYTHON),'-B',str(HOME/'math_c_bridge.py'),'--config',str(TARGET/'BRIDGE.json')],
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    deadline=time.monotonic()+15
    while not list((TARGET/'bridge_receipts').glob('READY_*.json')):
        require(time.monotonic()<deadline and server.poll() is None,'reloaded_bridge_ready')
        time.sleep(.1)
    endpoint=(HOME/'parent_endpoint.py').read_text()
    endpoint=endpoint.replace('from math_c import','from reload_support import')
    endpoint=endpoint.replace("next(record['document'] for record in records if record['kind'] == 'LOADED')",
        "next(record['document'] for record in reversed(records) if record['kind'] == 'LOADED')")
    (HOME/'parent_endpoint_R202.py').write_text((HOME/'parent_endpoint.py').read_text())
    (HOME/'parent_endpoint.py').write_text(endpoint)
    source=TARGET/'source'
    command=[str(PYTHON),'-B','-m','gpu.orch_r188_node4_rehome_containment','contained-supervise','--config',str(TARGET/'control/GUARD.json')]
    with (TARGET/'control/SUPERVISOR.log').open('x') as log:
        native=subprocess.Popen(command,cwd=source,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(source),PYTHONDONTWRITEBYTECODE='1'),
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    with (HOME/'WITHDRAWAL_R204.log').open('x') as log:
        watcher = HOME/'finish_r204_screen.py' if withdrawn else HOME/'withdraw_r204.py'
        withdrawal=subprocess.Popen([str(PYTHON),'-B',str(watcher)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    write(TARGET/'DISPATCHED.json',dict(supervisor_pid=native.pid,bridge_pid=server.pid,withdrawal_pid=withdrawal.pid,
        started_unix=time.time(),same_root=str(HOME/'life'),saved_cycle=retired['cycle'],no_inbox_or_history_reset=True))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('prepare','launch'))
    {'prepare':prepare,'launch':launch}[parser.parse_args().action]()
