"""Read selected TRAIN records; prove attributed input rendering without publication."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

from activate_parent import reference, require, write


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import hashlib,json,time
from pathlib import Path
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read_record(path):
 record=json.loads(path.read_bytes())
 assert record['sha256']==digest({key:value for key,value in record.items() if key!='sha256'})
 return record
def ref(path):return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
out=dict(observed_unix=time.time(),signals=0,publications=0,rows=[])
targets=[('C2','/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life',5128,['3078c29c7f70428da03ba284e247206c','00bfc710af3542d19b1910d0e45acdcb']),('run1','/localhome/local-rohing/orch_r125_continual_20260916_attempt1/run1',6300,['7b41a74a522b47df9befa9a46a9dea4f'])]
for label,root,start,identifiers in targets:
 root=Path(root);pending={}
 for identifier in identifiers:
  path=root/'stream/inbox'/(identifier+'.json');message=json.loads(path.read_bytes())
  assert message['id']==identifier and message['split']=='TRAIN' and message['actor']=='parent'
  pending[identifier]=dict(id=identifier,speaker=message['speaker'],inbox=ref(path),text_sha256=hashlib.sha256(message['text'].encode()).hexdigest(),text=message['text'],registrations=[],rendered=None)
 for path in sorted((root/'stream/records').glob('[0-9]'*20+'.json')):
  if int(path.stem)<=start:continue
  record=read_record(path);document=record['document']
  if record['kind']=='INBOX' and document['message']['id'] in pending:
   item=pending[document['message']['id']]
   assert document['source_sha256']==item['inbox']['sha256']
   item['registrations'].append(dict(index=record['index'],record_sha256=record['sha256'],reference=ref(path)))
  if record['kind']!='REQUEST':continue
  assert document['split']=='TRAIN'
  for item in pending.values():
   if item['rendered'] is not None:continue
   framed=item['speaker']+': '+item['text']
   matches=[position for position,message in enumerate(document['messages']) if message['role']=='user' and framed in message['content']]
   if not matches:continue
   history=document['resume_state']['state']['history']
   item['rendered']=dict(index=record['index'],record_sha256=record['sha256'],reference=ref(path),started_unix=document['started_unix'],segment=document['segment'],user_message_positions=matches,attributed_text_sha256=hashlib.sha256(framed.encode()).hexdigest(),all_history_tokens_masked=document['render_receipt']['all_history_tokens_masked'],history_reference_present=item['id'] in json.dumps(history),response=None,committed=None)
  for item in pending.values():
   if item['rendered'] is not None:assert item['registrations'] and item['rendered']['all_history_tokens_masked'] and item['rendered']['history_reference_present']
 for item in pending.values():
  rendered=item['rendered']
  if rendered is not None:
   for offset,kind,key in ((1,'RESPONSE','response'),(2,'COMMITTED','committed')):
    path=root/'stream/records'/(str(rendered['index']+offset).zfill(20)+'.json')
    if path.exists():
     record=read_record(path)
     if record['kind']==kind:rendered[key]=dict(index=record['index'],record_sha256=record['sha256'],reference=ref(path))
  del item['text']
  out['rows'].append(dict(label=label,**item))
print(json.dumps(out))
'''


def main():
    result = subprocess.run(['bash', str(HERE.parents[3] / 'gpu/ovx3_ssh.sh'),
        'python3 -B -c ' + shlex.quote(REMOTE)], capture_output=True, text=True, timeout=45)
    require(result.returncode == 0, 'read_only_render_proof:' + result.stderr[-350:])
    document = json.loads(result.stdout)
    run1 = next(row for row in document['rows'] if row['label'] == 'run1')
    require(run1['inbox']['sha256'] == 'b4d3b377ae2ccda7ecde3e6dba27702de9038f6465a0bccf1c9e117b76395110',
            'exact_Main_run1_publication')
    path = HERE / ('R188_RENDERED_INPUTS_' + str(time.time_ns()) + '.json')
    write(path, document)
    print(json.dumps(dict(receipt=reference(path), rows=document['rows'])))


if __name__ == '__main__':
    main()
