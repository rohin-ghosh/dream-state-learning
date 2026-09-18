"""Read-only exact inbox and rendered-REQUEST reconciliation, without publication."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

from activate_parent import read, reference, require, write


HERE = Path(__file__).resolve().parent
SUFFIX = 'What is the next unresolved question in your work? Choose a step and carry it out.'
REMOTE = '''import hashlib,json,time
from pathlib import Path
rows=[]
for item in ITEMS:
 root=Path(item['root']); messages=[]
 for path in sorted((root/'stream/inbox').glob('*.json')):
  raw=path.read_bytes()
  if len(raw)>65536: continue
  document=json.loads(raw)
  if not document.get('text','').endswith(SUFFIX): continue
  assert document['split']=='TRAIN' and document['actor']=='parent'
  messages.append(dict(id=document['id'],path=str(path),sha256=hashlib.sha256(raw).hexdigest(),speaker=document['speaker'],text_sha256=hashlib.sha256(document['text'].encode()).hexdigest(),mtime_unix=path.stat().st_mtime))
 wanted={entry['id']:entry for entry in messages}
 registered={}; request_times={}
 records=sorted((root/'stream/records').glob('[0-9]'*20+'.json'))
 for path in reversed(records):
  raw=path.read_bytes(); record=json.loads(raw)
  if record['kind']=='INBOX':
   document=record['document']
   identifier=document.get('id')
   if identifier in wanted: registered[identifier]=dict(record_index=record['index'],record_sha256=record['sha256'],mtime_unix=path.stat().st_mtime)
  if record['index'] in item['rendered_indices']:
   assert record['kind']=='REQUEST' and record['document']['split']=='TRAIN'
   request_times[str(record['index'])]=dict(record_sha256=record['sha256'],mtime_unix=path.stat().st_mtime)
  if record['index']<item['minimum_record']: break
 head=json.loads(records[-1].read_bytes())
 rows.append(dict(label=item['label'],messages=messages,registered=registered,request_times=request_times,head={key:head[key] for key in ('index','kind','sha256')},head_mtime_unix=records[-1].stat().st_mtime))
print(json.dumps(dict(rows=rows,observed_unix=time.time(),signals=0,publications=0)))
'''


def main():
    status_path = sorted(HERE.glob('BASELINE_STATUS_*.json'))[-1]
    status = read(status_path)
    items = []
    local = {}
    for row in status['rows']:
        output = Path(row['current_output'])
        manifest = read(row['manifest']['path'])
        config_path = output / 'CONFIG.json'
        config = read(config_path if config_path.exists() else manifest['predecessor']['config']['path'])
        polls = sorted(output.glob('POLL_*.json'))
        snapshot_path = polls[-1] if polls else output / 'BOOTSTRAP.json'
        snapshot = read(snapshot_path)['snapshot']
        indices = [value['record_index'] for value in snapshot['delivered'].values()
                   if value['speaker'] in ('Rohin', 'Fable', 'Astra')]
        items.append(dict(label=row['label'], root=config['root'], rendered_indices=indices,
                          minimum_record=min(indices, default=0)))
        local[row['label']] = dict(status=row, snapshot=snapshot, snapshot_ref=reference(snapshot_path))
    script = REMOTE.replace('ITEMS', repr(items)).replace('SUFFIX', repr(SUFFIX))
    response = subprocess.run(['bash', str(HERE.parents[3] / 'gpu/ovx3_ssh.sh'),
        'python3 -B -c ' + shlex.quote(script)], capture_output=True, text=True, timeout=90)
    require(response.returncode == 0, 'read_only_inbox_reconciliation_failed')
    document = json.loads(response.stdout)
    for remote in document['rows']:
        current = local[remote['label']]
        remote.update(arm=current['status']['arm'], operator_pid=current['status']['operator_pid'],
            operator_live=current['status']['operator_live'], current_status=current['status']['current_status'],
            snapshot=current['snapshot_ref'], own_publications=[], rendered_policy=[])
        for message in remote['messages']:
            delivery = current['snapshot']['delivered'].get(message['id'])
            if delivery:
                require(all(delivery[key] == message[other] for key, other in
                    (('speaker', 'speaker'), ('inbox_sha256', 'sha256'), ('text_sha256', 'text_sha256'))),
                    'exact_Fable_transport_attribution_and_bytes')
                message.update(status='RENDERED_REQUEST_VERIFIED', rendered=delivery,
                    rendered_file=remote['request_times'].get(str(delivery['record_index'])))
            else:
                message['status'] = 'REGISTERED_NOT_RENDERED' if message['id'] in remote['registered'] else 'QUEUED_NOT_REGISTERED'
        for attempt in current['status']['attempts']:
            result = read(attempt['receipt']['path'])
            if result['status'] != 'PUBLISHED':
                continue
            publication = result['publication']
            delivery = current['snapshot']['delivered'].get(publication['id'])
            entry = dict(publication=publication, result=attempt['receipt'], model=result.get('model'),
                         rendered=delivery, status='RENDERED_REQUEST_VERIFIED' if delivery else 'PUBLISHED_NOT_RENDERED')
            remote['own_publications'].append(entry)
            if delivery:
                entry['rendered_file'] = remote['request_times'].get(str(delivery['record_index']))
                remote['rendered_policy'].append(entry)
    document.update(status_source=reference(status_path), C2='EXCLUDED_FIXED_PILOT_MAIN_OWNS',
        no_duplicate_baseline=True, baseline_transport_author='Fable per Main; actual inbox speaker recorded separately')
    receipt = HERE / ('FABLE_RECONCILIATION_' + str(time.time_ns()) + '.json')
    write(receipt, document)
    print(json.dumps(dict(receipt=reference(receipt), rows=[dict(label=row['label'], arm=row['arm'],
        parent_pid=row['operator_pid'], head=row['head'], Fable=[{key:entry[key] for key in ('id','speaker','status','mtime_unix')}
        for entry in row['messages']], own=[dict(id=entry['publication']['id'],status=entry['status'],model=entry['model'])
        for entry in row['own_publications']]) for row in document['rows']])))


if __name__ == '__main__':
    main()
