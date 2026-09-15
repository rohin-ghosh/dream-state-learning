"""Hourly read-only node reductions; no raw VM copies and no GPU actions."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from gpu.orch_r109_route_ops import REPOSITORY,ANALYSIS,ROOTS
from gpu.orch_r109_route_run import END,write
from organism_v6.orch_r109_route import LANES,HOSTS


def bindings():
    result={lane:dict(root=str(ROOTS[lane]),wrapper=HOSTS[LANES[lane]['host']]['wrapper']) for lane in LANES}
    for lane in ('node5_0','node5_1'):
        result[lane]=dict(root='/localhome/local-rohing/orch_r109_route_node5_20260915_'+lane+'_attempt1',wrapper='gpu/ovx3_ssh.sh')
    return result


def snapshot(source,selected):
    def collect(item):
        lane,binding=item
        result=subprocess.run(['bash',str(REPOSITORY/binding['wrapper']),
            'python3 - --root '+binding['root']+' --lane '+lane],input=source,capture_output=True,text=True,timeout=90)
        if result.returncode:
            return dict(lane=lane,observer_error='REMOTE_REDUCTION_FAILED',returncode=result.returncode,raw_stderr_withheld=True)
        return json.loads(result.stdout)
    with ThreadPoolExecutor(max_workers=len(selected)) as pool:
        return list(pool.map(collect,selected.items()))


def watch():
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    path=REPOSITORY/'gpu/orch_r109_route_observe.py'
    source=path.read_text()
    digest=hashlib.sha256(source.encode()).hexdigest()
    next_run=datetime(2026,9,15,10,2,tzinfo=timezone.utc).timestamp()
    destination=ANALYSIS/'HOURLY'
    destination.mkdir(parents=True,exist_ok=True)
    write(destination/'WATCHER.json',dict(pid=os.getpid(),started_unix=time.time(),first_due_unix=next_run,
        hard_deadline_unix=END,observer_source_sha256=digest,no_gpu_actions=True,raw_embedded=False))
    while next_run<=END:
        while time.time()<next_run:
            time.sleep(min(30,next_run-time.time()))
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,'observer_source_changed'
        values=snapshot(source,bindings())
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        output=destination/(stamp+'.json')
        write(output,dict(observed_utc=stamp,observer_source_sha256=digest,lanes=values,raw_embedded=False))
        with (REPOSITORY/'research_loop/workers/R109_ROUTE.md').open('a') as stream:
            stream.write('\n[Builder / Poincare] '+stamp+' hourly native-only reduction: '+str(output.relative_to(REPOSITORY))+
                '; semantics UNKNOWN unless separately audited; raw throughput is not qualified behavior. No GPU actions.\n')
        next_run+=3600


if __name__=='__main__':
    watch()
