"""Minute-level compact custody alerts and original-clock hourly receipts."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


ROOT = Path('/localhome/local-rohing/orch_r109_l1_20260915')
START = 1789462560
END = START + 28800


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def alive(identity):
    try:
        directory = Path('/proc') / str(identity['pid'])
        fields = (directory / 'stat').read_text().rsplit(')',1)[1].split()
        return fields[0] != 'Z' and fields[19] == identity['start_ticks'] and directory.stat().st_uid == identity['uid']
    except FileNotFoundError:
        return False


def stale(now, observed, terminal=False):
    return not terminal and now - observed > 30


def native():
    now = time.time()
    result = dict(observed_unix=now, observed_utc=datetime.fromtimestamp(now,timezone.utc).isoformat(),
        hard_end_unix=END, raw_output=False, alerts=[], rehearsal={}, experience={}, gpu=[])
    for line in subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).splitlines():
        index,memory,utilization=[int(value.strip()) for value in line.split(',')]
        if index < 7:
            result['gpu'].append(dict(index=index,memory_mib=memory,utilization_percent=utilization))
    for name in ('HEARTBEAT.json','FAILURE.json','CPU_LAUNCH.json'):
        path=ROOT/'async_v3'/name
        if path.exists():result['rehearsal'][name]=read(path)
    heartbeat=result['rehearsal'].get('HEARTBEAT.json')
    if heartbeat and stale(now,heartbeat['observed_unix'],all(arm['terminal'] for arm in heartbeat['arms'].values())):
        result['alerts'].append('REHEARSAL_HEARTBEAT_STALE_NOT_RUNNING_PROOF')
    if 'FAILURE.json' in result['rehearsal']:result['alerts'].append('REHEARSAL_CONTROLLER_FAILED')
    cohort=ROOT/'experience_c1'
    if (cohort/'PREPARED.json').exists():
        prepared=read(cohort/'PREPARED.json')
        result['experience']['admission']=dict(rows=prepared['counts']['eligible'],unique_tasks=prepared['eligible_unique_tasks'],
            eligible_sha256=prepared['eligible_sha256'],source_label='R109_SELF_GENERATED_FUNCTIONAL',teacher_l2=False)
    for arm in ('FULL','CONTROL'):
        state={}
        launch=cohort/(arm+'_CPU_LAUNCH.json')
        if launch.exists():state['supervisor']=dict(identity=read(launch)['identity'],alive=alive(read(launch)['identity']))
        path=cohort/('HEARTBEAT_'+arm+'.json')
        if path.exists():
            state['heartbeat']=read(path)
            state['model_alive']=alive(state['heartbeat']['identity'])
            if stale(now,state['heartbeat']['observed_unix']):result['alerts'].append(arm+'_EXPERIENCE_HEARTBEAT_STALE')
        losses=sorted((cohort/'fit'/arm).glob('segment*/RANK0_LOSSES.jsonl'))
        if losses:
            rows=[readline for readline in losses[-1].read_text().splitlines() if readline]
            state['latest_segment_updates']=len(rows)
            if rows:state['last_update']=json.loads(rows[-1])
            state['latest_segment_eligible_supervised_tokens']=sum(json.loads(row)['eligible_supervised_tokens'] for row in rows)
        checkpoints=sorted((cohort/'fit'/arm/'checkpoints').glob('*/COMMIT.json'))
        if checkpoints:
            path=checkpoints[-1];document=read(path)
            state['checkpoint']=dict(path=str(path.parent),commit_sha256=sha(path),update=document['metadata']['update'],
                state_sha256=document['metadata']['adapter']['state_sha256'],optimizer_sha256=document['files']['optimizer.pt'],
                eligible_supervised_tokens=document['metadata']['eligible_supervised_tokens'])
        result['experience'][arm]=state
    print(json.dumps(result,indent=2))


def watch(destination):
    repository=Path(__file__).resolve().parents[1]
    source_sha=sha(Path(__file__))
    next_hour=START+(int((time.time()-START)//3600)+1)*3600
    while time.time()<END+60:
        assert sha(Path(__file__))==source_sha
        now=time.time()
        process=subprocess.run(['bash','gpu/ovx_ssh.sh',f'python3 {ROOT}/heartbeat.py native'],cwd=repository,
            capture_output=True,text=True,timeout=90)
        result=json.loads(process.stdout) if process.returncode==0 else dict(observed_unix=now,alerts=['READ_ONLY_REPORT_FAILED'])
        label=datetime.fromtimestamp(now,timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        path=destination/f'HEARTBEAT_{label}.json'
        with path.open('x') as stream:json.dump(result,stream,indent=2)
        if now>=next_hour:
            manifest=dict(observed_unix=now,original_hard_end_unix=END,alerts=result['alerts'],files={str(path.relative_to(repository)):sha(path)})
            with (destination/f'HOURLY_OPERATIONAL_{label}_STAGE_READY.json').open('x') as stream:json.dump(manifest,stream,indent=2)
            next_hour+=3600
        if now>=END:return
        time.sleep(min(60,max(1,END-time.time())))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['native','watch'])
    parser.add_argument('--destination',type=Path)
    options=parser.parse_args()
    native() if options.action=='native' else watch(options.destination)
