"""Read-only compact R109 telemetry; hourly transport contains no raw targets."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time


ROOT=Path('/localhome/local-rohing/orch_r109_l1_20260915')
HOSTS={'node1':'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b',
       'node2':'0e183169e60b06badac84e0eca6036a53b7ad90c433b8cd69b2a9aaf9159389b'}
START=1789462560
END=1789491360


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def alive(expected):
    if not expected:
        return False
    directory=Path('/proc')/str(expected['pid'])
    try:
        fields=(directory/'stat').read_text().rsplit(')',1)[1].split()
        return fields[0]!='Z' and directory.stat().st_uid==expected['uid'] and fields[19]==expected['start_ticks'] and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==expected['boot_id']
    except FileNotFoundError:
        return False


def reduced_calls(rows,now,window=3600):
    recent=[row for row in rows if now-window<=row['finished_unix']<=now]
    return dict(completed_captures=len(rows),window_seconds=window,recent_captures=len(recent),
        raw_captures_per_hour=len(recent)*3600/window,
        completed_output_tokens=sum(len(row.get('response',{}).get('token_ids',[])) for row in recent),
        truncated_recent=sum(bool(row.get('response',{}).get('truncated')) for row in recent),
        machine_correct_recent=sum(row.get('outcome',{}).get('correct') is True for row in recent),
        machine_scored_recent=sum(type(row.get('outcome',{}).get('correct')) is bool for row in recent),
        qualified_rows_per_hour=None,semantic_admissions=0,semantic_status='NOT_INFERRED_FROM_COUNTS_OR_FORM')


def next_hour(now):
    return min(END,START+(int((now-START)//3600)+1)*3600)


def native(node):
    assert hashlib.sha256(socket.gethostname().encode()).hexdigest()==HOSTS[node]
    now=time.time()
    plan=read(ROOT/'PLAN.json')
    gpu=[]
    lines=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu',
        '--format=csv,noheader,nounits'],text=True).splitlines()
    for line in lines:
        index,uuid,memory,utilization=[value.strip() for value in line.split(',')]
        if int(index) in range(7):
            assert uuid==plan['uuid_by_index'][int(index)]
            gpu.append(dict(index=int(index),uuid=uuid,memory_mib=int(memory),utilization_percent=int(utilization)))
    launches=[]
    for path in ROOT.glob('*_LAUNCH.json'):
        row=read(path)
        if 'identity' in row and 'index' in row:
            launches.append(dict(path=str(path),sha256=sha(path),index=row['index'],identity=row['identity'],
                alive=alive(row['identity']),started_unix=row['started_unix'],module=row['module'],arguments=row['arguments']))
    generation=[]
    for index in range(7):
        directory=ROOT/'generation'/f'gpu{index}'
        paths=sorted(directory.glob('CALL_*.json'))
        rows=[read(path) for path in paths]
        loaded=read(directory/'LOADED.json') if (directory/'LOADED.json').exists() else None
        old=(Path('/localhome/local-rohing/orch_rich_hot_node1_20260915_premise_v1') if index==3 else
             Path('/localhome/local-rohing/orch_rich_hot_node1_20260915_exhaustion_v1')) if node=='node1' else Path('/localhome/local-rohing/orch_rich_hot_node2_exhaustion_v3_20260915_attempt1')
        old_identity=read(old/f'LAUNCH_{index}.json')['identity']
        generation.append(dict(index=index,source_label='R109_SELF_GENERATED_FUNCTIONAL',
            condition=loaded['condition'] if loaded else None,source_state_sha256=loaded['adapter']['state_sha256'] if loaded else None,
            old_generator_still_alive=alive(old_identity),old_identity=old_identity if alive(old_identity) else None,
            progress=read(directory/'PROGRESS.json') if (directory/'PROGRESS.json').exists() else None,
            failures=len(list(directory.glob('FAILED_*.json'))),**reduced_calls(rows,now)))
    training=[]
    for path in sorted((ROOT/'fit').glob('*/*/RANK*_LOSSES.jsonl')):
        lines=path.read_text().splitlines()
        complete=[]
        for line in lines:
            try:
                complete.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        recent=[row for row in complete if row['finished_unix']>=now-3600]
        training.append(dict(path=str(path),rank=path.stem,arm=path.parent.parent.name,segment=path.parent.name,
            completed_updates=len(complete),first=complete[0] if complete else None,last=complete[-1] if complete else None,
            recent_updates=len(recent),local_supervised_tokens=sum(row['local_active'] for row in recent),
            original_seed_update=8932,latest_is_not_necessarily_committed=True))
    checkpoints=[]
    for path in sorted((ROOT/'fit').glob('*/checkpoints/*/COMMIT.json')):
        document=read(path)
        metadata=document['metadata']
        checkpoints.append(dict(path=str(path.parent),commit_sha256=sha(path),update=metadata['update'],arm=metadata['arm'],
            state_sha256=metadata['adapter']['state_sha256'],optimizer_sha256=document['files']['optimizer.pt'],
            rng_files={name:digest for name,digest in document['files'].items() if name.startswith('rank')},
            saved_unix=metadata['saved_unix'],source_labels=metadata['source_labels'],r109_exposures=metadata['r109_exposures']))
    readouts=[]
    for path in sorted((ROOT/'fit').glob('*/*/readout/*/COMPLETE.json')):
        readouts.append(dict(path=str(path),receipt=read(path)))
    return dict(schema='R109_COMPACT_OPERATIONAL_REPORT_V1',node=node,observed_unix=now,
        observed_utc=datetime.fromtimestamp(now,timezone.utc).isoformat(),host_sha256=HOSTS[node],
        source_archive_sha256=plan['source_archive_sha256'],plan_sha256=sha(ROOT/'PLAN.json'),
        gpu=gpu,launches=launches,generation=generation,training=training,checkpoints=checkpoints,readouts=readouts,
        lifetime=plan['lifetime'],maximum_lifetime_gpu_hours=112,
        reserved_elapsed_gpu_hours=14*(min(now,END)-START)/3600,
        reserved_elapsed_is_not_measured_compute=True,scope_l1_gpus=14,no_new_nodes_allocated=True,
        ingestion=dict(labels=plan['initial_ingestion_labels'],original_corpus_rows=3635,legacy_encoded_rows=222,
            verified_base_anchors=42,new_functional_or_corrected_l2_rows=0,status='CURATED_L2_DEFERRED_R110_NO_COMPILER'),
        scientific_claim='NO_RETAINED_LEARNING_CLAIM',raw_output=False)


def watch(destination):
    repository=Path(__file__).resolve().parents[1]
    initial_sha=sha(__file__)
    destination.mkdir(parents=True,exist_ok=True)
    while time.time()<END+120:
        assert sha(__file__)==initial_sha,'read_only_watcher_source_changed'
        now=time.time()
        result=dict(observed_unix=now,watcher_sha256=initial_sha,nodes={},errors={})
        for node,wrapper in [('node1','gpu/a40r_ssh.sh'),('node2','gpu/ovx_ssh.sh')]:
            process=subprocess.run(['bash',str(repository/wrapper),f'python3 {ROOT}/report.py native --node {node}'],
                cwd=repository,text=True,capture_output=True,timeout=120)
            if process.returncode:
                result['errors'][node]=dict(returncode=process.returncode,reason='READ_ONLY_NATIVE_REPORT_FAILED_NO_RAW_ERROR_EXPORT')
            else:
                result['nodes'][node]=json.loads(process.stdout)
        filename='HOURLY_'+datetime.fromtimestamp(now,timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json'
        with (destination/filename).open('x') as stream:
            json.dump(result,stream,indent=2)
        if now>=END:
            return
        time.sleep(max(1,next_hour(now)-time.time()))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['native','watch'])
    parser.add_argument('--node',choices=['node1','node2'])
    parser.add_argument('--destination',type=Path)
    options=parser.parse_args()
    if options.action=='native':
        print(json.dumps(native(options.node)))
    else:
        watch(options.destination)
