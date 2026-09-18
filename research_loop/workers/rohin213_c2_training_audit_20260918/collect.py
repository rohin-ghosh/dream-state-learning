"""Read only original C2 journal receipts; store raw evidence privately locally."""

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def metadata(path):
    with path.open('rb') as source:
        source.seek(max(0, path.stat().st_size-4096))
        ending = source.read()
    position = ending.rfind(b',"index":')
    if position < 0:
        raise ValueError('journal_metadata_unavailable')
    return json.loads(b'{'+ending[position+1:])


def verified(path):
    payload = path.read_bytes()
    record = json.loads(payload)
    assert digest({key:value for key,value in record.items() if key!='sha256'})==record['sha256']
    return record


def remote_collect(start_cycle=52, end_cycle=63):
    paths = sorted((LIFE/'stream/records').glob('[0-9]'*20+'.json'))
    inventory = [(path, metadata(path)) for path in paths]
    sleeps = []
    selected = []
    for path, meta in inventory:
        if meta['kind'] in ('SLEEP_REQUEST', 'SLEEP_COMPLETE'):
            record = verified(path)
            document = record['document']
            if start_cycle <= document.get('cycle', -1) <= end_cycle:
                state = document.get('resume_state', {}).get('state', {})
                rows = state.get('rows', [])
                sleeps.append(dict(record={**record, 'document':{key:value for key,value in document.items()
                                                             if key!='resume_state'}},
                                   state_sha256=document.get('resume_state', {}).get('sha256'),
                                   sleep_frontier=state.get('sleep_frontier'),
                                   row_count=len(rows), row_keys=list(rows[0]) if rows else [],
                                   file_mtime_unix=path.stat().st_mtime))
                if meta['kind']=='SLEEP_REQUEST':
                    selected.extend(rows[state.get('sleep_frontier', len(rows)):])
                elif document.get('presentations'):
                    known={row['source_sha256'] for row in selected}
                    selected.extend(row for row in rows if row['source_sha256'] in document['presentations']
                                    and row['source_sha256'] not in known)
    indices = [entry['record']['index'] for entry in sleeps]
    lower, upper = min(indices), max(indices)
    if end_cycle == 10000:
        upper = inventory[-1][1]['index']
    relevant = []
    wanted = {'SLEEP_RECIPE','TARGET_ELIGIBILITY','UPDATE','LOADED','R195_LEARN_REVIEW',
              'COMPACTION','R184_LEARN_COMPLETE','R191_DATASET_ROW','R189_OUTCOME_CYCLE'}
    for path, meta in inventory:
        if lower-80 <= meta['index'] <= upper and meta['kind'] in wanted:
            record = verified(path)
            if meta['kind']=='COMPACTION':
                record = {**record, 'document':{key:value for key,value in record['document'].items()
                                              if key not in ('state','resume_state')}}
            relevant.append(dict(record=record, file_mtime_unix=path.stat().st_mtime))
    wanted_hashes = {row['source_sha256'] for row in selected}
    for sleep in sleeps:
        wanted_hashes.update(sleep['record']['document'].get('presentations', {}))
        wanted_hashes.update(sleep['record']['document'].get('new_row_sha256', []))
    responses = {}
    stages = {}
    for path, meta in inventory:
        if meta['index']>upper:
            break
        if meta['kind'] not in ('RESPONSE','R184_STAGE'):
            continue
        record = verified(path)
        source_hash = digest(record['document']) if meta['kind']=='RESPONSE' else record['document']['source_sha256']
        if source_hash in wanted_hashes:
            destination = responses if meta['kind']=='RESPONSE' else stages
            destination[source_hash] = dict(record=record, file_mtime_unix=path.stat().st_mtime)
    report = dict(schema='R213_C2_READ_ONLY_RAW_AUDIT_V1', observed_unix=time.time(),
                  source_label='ORIGINAL_C2', source_path=str(LIFE), journal_head=inventory[-1][1],
                  requested_start_cycle=start_cycle, requested_end_cycle=end_cycle,
                  sleeps=sleeps, relevant_records=relevant, candidate_rows=selected,
                  responses=responses, stages=stages,
                  selected_metadata=[meta for path,meta in inventory if lower<=meta['index']<=upper],
                  remote_writes=False, signals=False, controls_modified=False)
    print(json.dumps(report, ensure_ascii=False))


def collect_local(start_cycle=52, end_cycle=63, suffix=''):
    os.umask(0o077)
    own = Path(__file__).resolve().parent
    repository = own.parents[2]
    private = own/'private'
    private.mkdir(mode=0o700, exist_ok=True)
    result = subprocess.run(['bash', str(repository/'gpu/ovx3_ssh.sh'),
                             'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B - --remote '
                             f'--start-cycle {start_cycle} --end-cycle {end_cycle}'],
                            input=Path(__file__).read_text(), capture_output=True, text=True,
                            cwd=repository, timeout=180)
    if result.returncode:
        with (private/'COLLECT_FAILURE.txt').open('x') as output:
            output.write(result.stderr)
        raise RuntimeError('read_only_collection_failed_private_receipt_retained')
    report = json.loads(result.stdout)
    payload = result.stdout.encode()
    with (private/('RAW_EVIDENCE'+suffix+'.json')).open('xb') as output:
        output.write(payload)
    summary = dict(observed_unix=report['observed_unix'], evidence_sha256=hashlib.sha256(payload).hexdigest(),
                   source_label='ORIGINAL_C2', responses=len(report['responses']),
                   candidate_rows=len(report['candidate_rows']), sleeps=[])
    for item in report['sleeps']:
        record = item['record']
        document = record['document']
        summary['sleeps'].append(dict(cycle=document['cycle'],kind=record['kind'],index=record['index'],
                                     status=document.get('status'),optimizer_steps=document.get('optimizer_steps'),
                                     presentations=document.get('presentations'),row_keys=item['row_keys']))
    with (own/('COLLECTION_RECEIPT'+suffix+'.json')).open('x') as output:
        json.dump(summary,output,sort_keys=True,indent=2)
    print(json.dumps(summary))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote',action='store_true')
    parser.add_argument('--start-cycle',type=int,default=52)
    parser.add_argument('--end-cycle',type=int,default=63)
    parser.add_argument('--suffix',default='')
    arguments=parser.parse_args()
    assert 1<=arguments.start_cycle<=arguments.end_cycle<=10000
    remote_collect(arguments.start_cycle,arguments.end_cycle) if arguments.remote else collect_local(
        arguments.start_cycle,arguments.end_cycle,arguments.suffix)
