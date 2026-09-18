"""Read-only original-C2 THINK-to-ACT, target-mask, and failed46 inspection."""

import json
from pathlib import Path
import shlex
import subprocess
import time


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import hashlib,json,re,time
from pathlib import Path
root=Path('/localhome/local-rohing/orch_r153_r193_C2_20260917_recovery1/archived_failed46_life')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(index):
 path=root/'stream/records'/f'{index:020d}.json'
 doc=json.loads(path.read_bytes())
 assert doc['sha256']==digest({key:value for key,value in doc.items() if key!='sha256'})
 return doc
def meta(path):
 with path.open('rb') as stream:
  stream.seek(max(0,path.stat().st_size-4096));raw=stream.read()
 return json.loads(b'{'+raw[raw.rfind(b',"index":')+1:])
def snippets(text):
 pattern=r'(?i)sympy|unavailable|basic algebra|standard library|stdlib|without external|not installed|ModuleNotFound'
 selected=[]
 for match in re.finditer(pattern,text):
  start=max(0,match.start()-100);end=min(len(text),match.end()+240)
  if selected and start<=selected[-1]['end']:
   selected[-1]['end']=end;selected[-1]['text']=text[selected[-1]['start']:end]
  else:selected.append(dict(start=start,end=end,text=text[start:end]))
 return selected[:8]
catalog=[meta(path) for path in sorted((root/'stream/records').glob('[0-9]'*20+'.json'))]
stages=[]
for item in catalog:
 if item['index']>5128 and item['kind']=='R184_STAGE':
  entry=read(item['index']);doc=entry['document']
  stages.append(dict(index=item['index'],stage=doc['stage'],segment=doc['segment'],record_sha256=entry['sha256']))
out=dict(observed_unix=time.time(),archive_root=str(root),signals=0,publications=0,live_changes=0,acts=[])
for position,stage in enumerate(stages):
 if stage['stage']!='ACT':continue
 previous=next(value for value in reversed(stages[:position]) if value['stage']=='THINK')
 request=read(stage['index']-3);response=read(stage['index']-2);commit=read(stage['index']-1)
 thought=read(previous['index']-2)
 assert request['kind']=='REQUEST' and response['kind']=='RESPONSE' and commit['kind']=='COMMITTED' and thought['kind']=='RESPONSE'
 body=request['document'];think_text=thought['document']['response']['raw'];actual_text=response['document']['response']['raw']
 state=commit['document']['state']['state'];rows=state['rows']
 actrow=next(row for row in rows if row['segment']==stage['segment'])
 thinkrow=next(row for row in rows if row['segment']==previous['segment'])
 assert actrow['target']==actual_text and actrow['prefix']==body['messages'] and thinkrow['target']==think_text
 messages=body['messages']
 matches=[dict(position=index,role=message['role'],content_sha256=hashlib.sha256(message['content'].encode()).hexdigest())
          for index,message in enumerate(messages) if think_text in message.get('content','')]
 following=next((item for item in catalog if item['index']>stage['index'] and item['kind']=='SLEEP_REQUEST'),None)
 cycle=read(following['index'])['document']['cycle'] if following else None
 fields=('actor','event_id','segment','prefix_loss','target_loss','source_sha256','terminal','truncated')
 event=next(event for event in state['history']['events'] if event['event_id']==thinkrow['event_id'])
 rendered_corrections=[]
 for excerpt in snippets(think_text):
  rendered_corrections.append(dict(excerpt=excerpt,positions=[index for index,message in enumerate(messages) if excerpt['text'] in message.get('content','')]))
 out['acts'].append(dict(cycle=cycle,stage=stage,request_index=request['index'],request_record_sha256=request['sha256'],
  request_file_sha256=sha(root/'stream/records'/f"{request['index']:020d}.json"),started_unix=body['started_unix'],
  all_history_tokens_masked=body['render_receipt']['all_history_tokens_masked'],
  prior_THINK=dict(response_index=thought['index'],record_sha256=thought['sha256'],raw_sha256=hashlib.sha256(think_text.encode()).hexdigest(),
    full_text_exactly_present_in_ACT_messages=matches,row={key:thinkrow[key] for key in fields},event_actor=event['actor'],excerpts=rendered_corrections),
  ACT=dict(response_index=response['index'],record_sha256=response['sha256'],row={key:actrow[key] for key in fields},excerpts=snippets(actual_text)),
  ACT_prefix_is_actual_request=True))
out['failed46_stages']=[stage for stage in stages if stage['index']>5406]
out['failed46_compaction_reviews']=[]
for stage in out['failed46_stages']:
 request=read(stage['index']-3)['document']
 selected=[dict(position=index,role=message['role'],text=message['content'][:250]) for index,message in enumerate(request['messages']) if 'Compaction review: revisit this exact earlier reflection' in message.get('content','')]
 if selected and stage['stage']=='THINK':out['failed46_compaction_reviews'].append(dict(stage=stage,request_index=stage['index']-3,last_review_message=selected[-1]))
out['latest_parent_registrations']=[]
for item in catalog:
 if item['kind']!='INBOX':continue
 doc=read(item['index'])['document'];message=doc['message']
 if message['actor']=='parent':out['latest_parent_registrations'].append(dict(index=item['index'],record_sha256=item['sha256'],id=message['id'],speaker=message.get('speaker'),text_sha256=hashlib.sha256(message['text'].encode()).hexdigest()))
out['latest_parent_registrations']=out['latest_parent_registrations'][-6:]
print(json.dumps(out))
'''


def main():
    result = subprocess.run(['bash', str(HERE.parents[3] / 'gpu/ovx3_ssh.sh'),
                             'python3 -B -c ' + shlex.quote(REMOTE)], capture_output=True, text=True, timeout=75)
    if result.returncode:
        raise RuntimeError(result.stderr[-1800:])
    document = json.loads(result.stdout)
    path = HERE / ('R193_C2_INPUT_INSPECTION_' + str(time.time_ns()) + '.json')
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
    print(json.dumps(dict(path=str(path),acts=document['acts'],failed46_stages=document['failed46_stages'],
                         latest_parent_registrations=document['latest_parent_registrations']),indent=2))


if __name__ == '__main__':
    main()
