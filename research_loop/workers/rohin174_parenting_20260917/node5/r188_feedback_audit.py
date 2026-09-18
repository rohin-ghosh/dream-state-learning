"""Read-only first-recipe, elapsed-sleep, and actual C2 feedback inspection."""

import json
from pathlib import Path
import shlex
import subprocess
import time

from activate_parent import read, reference, require, write


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import hashlib,json,time
from pathlib import Path
def ref(path):return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def record(path):
 entry=json.loads(path.read_bytes())
 assert entry['sha256']==digest({key:value for key,value in entry.items() if key!='sha256'})
 return entry
def metadata(path):
 with path.open('rb') as stream:
  stream.seek(max(0,path.stat().st_size-4096));raw=stream.read()
 return json.loads(b'{'+raw[raw.rfind(b',"index":')+1:])
def receipt(path,entry):return dict(index=entry['index'],record_sha256=entry['sha256'],reference=ref(path),mtime_unix=path.stat().st_mtime)
out=dict(observed_unix=time.time(),rows=[],C2_acts=[],signals=0,publications=0,live_source_changes=0)
for item in ITEMS:
 assert not item.get('blocked')
 paths=sorted((Path(item['storage_root'])/'stream/records').glob('[0-9]'*20+'.json'))
 catalog=[(path,metadata(path)) for path in paths]
 row=dict(label=item['label'],first_recipe=None,first_newonly_complete=None,latest_recipe=None,latest_sleep_request=None,latest_complete=None)
 for path,meta in catalog:
  kind=meta['kind']
  if kind not in ('SLEEP_REQUEST','SLEEP_RECIPE','SLEEP_COMPLETE'):continue
  entry=record(path);doc=entry['document'];entry_ref=receipt(path,entry)
  if kind=='SLEEP_REQUEST':
   row['latest_sleep_request']=dict(entry_ref,cycle=doc['cycle'])
  elif kind=='SLEEP_RECIPE':
   recipe=dict(entry_ref,cycle=row['latest_sleep_request']['cycle'],new_rows=doc['new_rows'],new_presentations=doc['new_presentations'],selected_old_rows=doc['selected_old_rows'])
   row['latest_recipe']=recipe
   if row['first_recipe'] is None and recipe['selected_old_rows']==0 and recipe['new_presentations']==16:row['first_recipe']=recipe
  else:
   row['latest_complete']=dict(entry_ref,cycle=doc['cycle'],status=doc['status'],updates=doc.get('optimizer_steps'),total_optimizer_steps=doc['checkpoint']['optimizer_steps'])
   recipe=row['latest_recipe']
   if row['first_newonly_complete'] is None and recipe and recipe['cycle']==doc['cycle'] and recipe['selected_old_rows']==0 and recipe['new_presentations']==16 and doc['status']=='COMPLETE':
    row['first_newonly_complete']=dict(row['latest_complete'],recipe=recipe)
 request=row['latest_sleep_request'];complete=row['latest_complete']
 row['active_sleep']=bool(request and (complete is None or request['index']>complete['index']))
 row['active_sleep_age_seconds']=time.time()-request['mtime_unix'] if row['active_sleep'] else None
 row['long_sleep_over_15min']=row['active_sleep'] and row['active_sleep_age_seconds']>900
 out['rows'].append(row)
 if item['label']!='C2':continue
 c2=Path(item['storage_root']);source=Path(item['plan']['source_root'])
 out['C2_source']={name:ref(source/name) for name in ('gpu/orch_r184_think_act_learn.py','gpu/orch_r125_continual_native.py','gpu/orch_r125_stream_journal.py')}
 for path,meta in catalog:
  if meta['index']<=5128 or meta['kind']!='R184_ACT':continue
  entry=record(path);outcome=entry['document']['outcome']
  observed=dict(receipt(path,entry),segment=entry['document']['segment'],outcome={key:outcome.get(key) for key in ('status','executed','result_status','error_type')},task_correctness='NOT_ESTABLISHED',feedback=None,rendered=None,following_response=None,stage_consolidation=None)
  publication=outcome.get('publication')
  if publication:
   inbox_path=Path(publication['path']);assert inbox_path.parent==c2/'stream/inbox' and ref(inbox_path)['sha256']==publication['sha256']
   message=json.loads(inbox_path.read_bytes());assert message['speaker']=='Tool' and message['split']=='TRAIN'
   result_path=Path(message['source_receipt']['path']);assert result_path.is_relative_to(c2/'community_cpu/spool')
   assert not result_path.is_symlink() and ref(result_path)==message['source_receipt']
   assert message['source_receipt']['sha256']==outcome['result_sha256']
   result=json.loads(result_path.read_bytes())
   observed['feedback']=dict(id=message['id'],inbox=ref(inbox_path),source_receipt=ref(result_path),text=message['text'],result_fields={key:result[key] for key in ('status','returncode','exit_code') if key in result})
   for request_path,request_meta in catalog:
    if request_meta['index']<=entry['index'] or request_meta['kind']!='REQUEST':continue
    request_record=record(request_path);doc=request_record['document'];framed='Tool: '+message['text']
    matches=[position for position,message_row in enumerate(doc['messages']) if message_row['role']=='user' and framed in message_row['content']]
    if not matches:continue
    assert doc['render_receipt']['all_history_tokens_masked'] and message['id'] in json.dumps(doc['resume_state']['state']['history'])
    observed['rendered']=dict(receipt(request_path,request_record),started_unix=doc['started_unix'],positions=matches,all_history_tokens_masked=True)
    response_path=request_path.parent/(str(request_meta['index']+1).zfill(20)+'.json')
    if response_path.exists():
     response=record(response_path)
     if response['kind']=='RESPONSE':observed['following_response']=dict(receipt(response_path,response),raw=response['document']['response']['raw'],truncated=response['document']['response'].get('truncated'))
    break
  for stage_path,stage_meta in catalog:
   if stage_meta['index']<=entry['index'] or stage_meta['kind']!='R184_STAGE':continue
   stage=record(stage_path);doc=stage['document']
   observed['stage_consolidation']=dict(receipt(stage_path,stage),stage=doc['stage'],consolidation=doc.get('consolidation'),runtime_notice_is_target=doc['runtime_notice_is_target'])
   break
  out['C2_acts'].append(observed)
 out['C2_source_unchanged_during_read']=all(ref(source/name)==pin for name,pin in out['C2_source'].items())
print(json.dumps(out))
'''


def main():
    inventory = sorted(HERE.glob('R181_CURRENT_*.json'))[-1]
    result = subprocess.run(['bash', str(HERE.parents[3] / 'gpu/ovx3_ssh.sh'),
        'python3 -B -c ' + shlex.quote(REMOTE.replace('ITEMS', repr(read(inventory)['rows'])))],
        capture_output=True, text=True, timeout=100)
    require(result.returncode == 0, 'read_only_feedback_audit:' + result.stderr[-500:])
    document = json.loads(result.stdout)
    document['inventory'] = reference(inventory)
    path = HERE / ('R188_FEEDBACK_AUDIT_' + str(time.time_ns()) + '.json')
    write(path, document)
    print(json.dumps(dict(receipt=reference(path), rows=[dict(label=row['label'],
        first_cycle=row['first_newonly_complete']['cycle'] if row['first_newonly_complete'] else None,
        first_time=row['first_newonly_complete']['mtime_unix'] if row['first_newonly_complete'] else None,
        latest_cycle=row['latest_complete']['cycle'], active_sleep=row['active_sleep'],
        active_age_seconds=row['active_sleep_age_seconds'], long_sleep=row['long_sleep_over_15min'])
        for row in document['rows']], acts=[dict(index=row['index'],outcome=row['outcome'],
        feedback=row['feedback'],rendered=row['rendered'],stage_consolidation=row['stage_consolidation'])
        for row in document['C2_acts']])))


if __name__ == '__main__':
    main()
