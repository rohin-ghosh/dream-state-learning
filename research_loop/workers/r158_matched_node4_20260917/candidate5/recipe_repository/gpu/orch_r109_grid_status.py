"""Read-only grid reductions and hourly compact mirroring; no model/parent calls."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import time

from organism_v6 import orch_r109_grid as policy


ROOT = Path('/localhome/local-rohing/orch_r109_grid_20260915_attempt1')


def read(path):
    return json.loads(path.read_text())


def reference(path):
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def summary(values):
    return dict(count=len(values),minimum=min(values) if values else None,
        median=statistics.median(values) if values else None,maximum=max(values) if values else None,
        total=sum(values),mean=statistics.mean(values) if values else None)


def collect(root, lane, gpu=False):
    ready=read(root/'READY.json')
    policy.require(lane==ready['lane'],'status_lane')
    ledger=[json.loads(line) for line in (root/'LEDGER.jsonl').read_text().splitlines() if line.strip()] if (root/'LEDGER.jsonl').exists() else []
    calls=[(path,read(path)) for path in sorted((root/'calls').glob('*.json'))]
    responses=[(path,read(path)) for path in sorted((root/'parent_queue').glob('*.response.json'))]
    complete=[(path,value) for path,value in calls if value['status']=='COMPLETE']
    parents=[(path,value) for path,value in responses if value['status']=='COMPLETE']
    token_groups={purpose:summary([len(value['response']['token_ids']) for _,value in complete if value['purpose']==purpose])
        for purpose in sorted({value['purpose'] for _,value in complete})}
    episodes=[read(path) for path in sorted(root.glob('*/cycle*/[th]*/episode*/EPISODE.json'))]
    cycle_files=sorted(root.glob('*/cycle*/train/METACOGNITIVE_TRIPLE.json'))
    triples={}
    for path in root.glob('*/cycle*/train/episode*/STEPS/*.json'):
        for triple in read(path)['triples']:
            triples[triple['intervention']['response_ref']['path']]=dict(source=reference(path),
                proposal=triple['proposal'],continuation=triple['continuation'])
    for path in cycle_files:
        triple=read(path);triples[triple['intervention']['response_ref']['path']]=dict(source=reference(path),
            proposal=triple['before'],continuation=triple['continuation'])
    result=dict(schema='R109_GRID_R110_COMPACT_STATUS_V1',lane=lane,observed_unix=time.time(),
        observed_utc=datetime.now(timezone.utc).isoformat(),ready=reference(root/'READY.json'),
        source=reference(root/'SOURCE_SHA256.json'),principles_sha256=policy.PRINCIPLES_SHA,
        native_reserved=sum(value['kind']=='NATIVE' for value in ledger),native_complete=len(complete),
        native_failed=sum(value['status']=='FAILED' for _,value in calls),
        native_incomplete=sum(value['status']=='STARTED' for _,value in calls),
        parent_reserved=sum(value['kind']=='PARENT' for value in ledger),parent_complete=len(parents),
        parent_failed=sum(value['status']=='FAILED' for _,value in responses),
        parent_models=sorted({value['actual_model'] for _,value in parents}),
        tokens_by_purpose=token_groups,
        eos=sum(value['response']['terminal'] for _,value in complete),
        ceilings=sum(value['response']['truncated'] for _,value in complete),
        native_seconds=summary([value['finished_unix']-value['started_unix'] for _,value in complete]),
        parent_seconds=summary([value['finished_unix']-value['started_unix'] for _,value in parents]),
        intervention_classes=dict(Counter(value['plan']['rationale'].split(':',1)[0] for _,value in parents)),
        unique_source_joined_triples=len(triples),metacognitive_conversations=len(cycle_files),
        episodes_by_split=dict(Counter(value['split'] for value in episodes)),
        task_success_secondary=dict(Counter(value['split'] for value in episodes if value['success'])),
        functional_helpfulness='UNASSESSED',effort_allocation_semantics='UNASSESSED',
        no_adapter=True,optimizer_updates=0,weight_learning_claim=False,
        native_deadline_utc='2026-09-15T16:57:00Z',hard_deadline_utc='2026-09-15T17:02:00Z',
        admission_attempts=len(list((root/'admissions').glob('*.json'))),models_mounted=0,
        private_to_research_reporting_not_parent_payload=True)
    if (root/'RESIDENT_LOADED.json').exists():
        loaded=read(root/'RESIDENT_LOADED.json');result['resident']=loaded
        result['models_mounted']=1
        result['resident_pid_present']=Path(f'/proc/{loaded["pid"]}').exists()
    if complete:
        path,value=complete[0]
        result['first_native']=dict(reference(path),started_unix=value['started_unix'],finished_unix=value['finished_unix'])
    if parents:
        path,value=parents[0]
        result['first_parent']=dict(reference(path),started_unix=value['started_unix'],finished_unix=value['finished_unix'])
    if (root/'TERMINAL.json').exists():result['terminal']=read(root/'TERMINAL.json')
    if gpu:
        result['gpu_csv']=subprocess.check_output(['nvidia-smi','-i',str(policy.LANES[lane]['index']),
            '--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=30).strip()
    return result


def write_once(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.flush();os.fsync(stream.fileno())


def mirror(wrappers, output):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU_status_only')
    while time.time() <= policy.HARD_END+300:
        for lane in policy.LANES:
            command=('CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH='+str(ROOT/'source_v1')+
                ' python3 -B '+str(ROOT/'monitor_v1/orch_r109_grid_status.py')+' --lane '+lane)
            completed=subprocess.run(['bash',str(wrappers/'gpu'/f'{lane}_ssh.sh'),command],
                text=True,capture_output=True,timeout=60)
            if completed.returncode:
                value=dict(lane=lane,observed_unix=time.time(),status='READ_FAILED',returncode=completed.returncode)
            else:
                value=json.loads(completed.stdout)
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            write_once(output/f'{lane}_{stamp}.json',value)
        next_hour=policy.START_BOUND+(int((time.time()-policy.START_BOUND)//3600)+1)*3600
        until=min(next_hour,policy.HARD_END+120)
        if until<=time.time():break
        time.sleep(until-time.time())


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--lane',choices=policy.LANES)
    parser.add_argument('--wrappers',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.lane:
        value=collect(ROOT,args.lane,gpu=True)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        path=ROOT/'HOURLY'/f'{stamp}.json';write_once(path,value)
        print(json.dumps(dict(value,node_receipt=reference(path))))
    else:
        mirror(args.wrappers,args.output)
