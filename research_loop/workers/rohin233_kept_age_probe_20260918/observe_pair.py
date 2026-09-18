"""Read-only actual parent INBOX-to-REQUEST proof for Cicero's kept pair."""

import json
from pathlib import Path
import subprocess


CODE = '''import hashlib,json,pathlib,time
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def utc(value):
 import datetime
 return datetime.datetime.fromtimestamp(value,datetime.timezone.utc).isoformat()
targets=[('learner','/localhome/local-rohing/orch_r231_curriculum_birth_20260918/raw','038f85cbde5c4abfb749ea4d59da6897'),
 ('frozen_sibling','/localhome/local-rohing/orch_r232_curriculum_frozen_20260918/raw','30fa18c869b34fd496a2758a4a28e197')]
rows=[]
for label,name,journal in targets:
 life=pathlib.Path(name);stream=life/'stream';header=json.loads((stream/'JOURNAL.json').read_bytes())
 assert header['journal_id']==journal
 previous=digest(header);inboxes={};rendered={};loaded=None;latest_sleep=None;tail=None
 paths=sorted(path for path in (stream/'records').glob('*.json') if path.stem.isdigit())
 assert len(paths)<=4000,'bounded_pair_scan'
 for index,path in enumerate(paths):
  row=json.loads(path.read_bytes());document=row['document']
  assert row['index']==index and row['journal_id']==journal and row['previous_sha256']==previous
  assert row['sha256']==digest({key:value for key,value in row.items() if key!='sha256'})
  previous=row['sha256'];tail=index
  if row['kind']=='LOADED':
   loaded=dict(record_index=index,record_sha256=previous,pid=document['pid'],loaded_unix=document['loaded_unix'],optimizer_steps=document['optimizer_steps'])
  elif row['kind']=='INBOX':
   message=document['message']
   if message.get('speaker')=='Astra':
    inboxes[message['id']]=dict(record_index=index,record_sha256=previous,text=message['text'],
     text_sha256=hashlib.sha256(message['text'].encode()).hexdigest(),source_sha256=document['source_sha256'])
  elif row['kind']=='REQUEST':
   messages=document['messages']
   for identifier,message in inboxes.items():
    if identifier not in rendered and any(message['text'] in item['content'] for item in messages):
     rendered[identifier]=dict(parent_inbox_id=identifier,inbox_record_index=message['record_index'],
      inbox_record_sha256=message['record_sha256'],parent_text_sha256=message['text_sha256'],
      source_sha256=message['source_sha256'],request_record_index=index,request_record_sha256=previous,
      request_started_unix=document['started_unix'],request_utc=utc(document['started_unix']),
      prompt_tokens=document['prompt_tokens'],exact_parent_text_rendered=True)
  elif row['kind']=='SLEEP_COMPLETE' and document.get('status')=='COMPLETE':
   latest_sleep=dict(record_index=index,record_sha256=previous,sleep=document['cycle'],optimizer_steps=document['total_optimizer_steps'])
 alive=False
 if loaded:
  stat=pathlib.Path('/proc')/str(loaded['pid'])/'stat'
  alive=stat.exists() and stat.read_text().rsplit(')',1)[1].split()[0]!='Z'
 values=sorted(rendered.values(),key=lambda value:value['request_started_unix'])
 rows.append(dict(arm=label,journal_id=journal,observed_head=tail,verified_head_sha256=previous,
  native_alive=alive,latest_loaded=loaded,latest_complete_sleep=latest_sleep,parent_speaker='Astra',
  consumed_parent_inboxes=len(inboxes),rendered_parent_turns=len(rendered),pending_consumed_parent_ids=sorted(set(inboxes)-set(rendered)),
  latest_three_actual_rendered=values[-3:],exact_text_substring_not_just_process_state=True,
  parent_policy_owner='Cicero',life_controls_performed=[]))
print(json.dumps(dict(schema='R233_PAIR_PARENT_RENDER_CHECK_V1',unix=time.time(),rows=rows,
 existing_birth_and_recovery_gaps_preserved=True,causal_matched_claim=False,read_only=True)))
'''


def main():
    result = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', 'python3 -B -'], input=CODE,
        text=True, capture_output=True, timeout=40)
    if result.returncode:
        raise RuntimeError(result.stderr[-1600:])
    receipt = json.loads(result.stdout)
    (Path(__file__).resolve().parent / 'PAIR_PARENT_LATEST.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
