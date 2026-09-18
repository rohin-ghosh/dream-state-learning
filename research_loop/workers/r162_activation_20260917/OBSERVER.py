"""Single bounded, read-only R162 observation poll; no lifecycle/API actions."""

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

DIRECTORY = Path(__file__).resolve().parent
DEADLINE = 1789629352
BUDGET = 64*1024**2
REMOTE = r'''
import base64,hashlib,json,os,pathlib,re,time
assert os.uname().nodename=='[REDACTED_HOST]'
used=0;artifacts={};cache={};summaries=[]
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path,limit=8*1024**2,retain=False):
 global used
 path=pathlib.Path(path);key=str(path)
 assert time.time()<options['deadline'] and not any(word in key.lower() for word in ['readout','sealed'])
 if key in cache:return cache[key]
 assert path.is_absolute() and path.resolve()==path
 descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  before=os.fstat(descriptor);pseudo=key.startswith('/proc/');allowance=limit if pseudo else before.st_size+1
  assert allowance<=limit and used+allowance<=options['allowance'],'observer_read_bound'
  raw=os.read(descriptor,allowance);used+=len(raw);after=os.fstat(descriptor)
  assert pseudo or (len(raw)==before.st_size and (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns))
 finally:os.close(descriptor)
 reference=dict(path=key,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
 if retain and key not in options['archived']:
  artifacts[key]=dict(reference,raw_base64=base64.b64encode(raw).decode())
 cache[key]=(raw,reference)
 return raw,reference
def document(path,retain=False):
 raw,reference=read(path,retain=retain);return json.loads(raw),reference
def record(root,index,retain=True):
 path=root/'stream/records'/f'{index:020d}.json'
 if str(path) in options['archived']:return dict(path=str(path),already_archived=True)
 value,reference=document(path,retain)
 assert value['sha256']==digest({k:v for k,v in value.items() if k!='sha256'}) and value['index']==index
 assert value['kind'] not in ('READOUT','EVALUATION'),'no_held_record_packet'
 return reference
def evidence(root,value):
 source=pathlib.Path(value['source']['path'])
 refs=[]
 for path in [source,source.parent/'PUBLICATION.json',pathlib.Path(value['publication']['path'])]:
  if str(path) in options['archived']:refs.append(dict(path=str(path),already_archived=True))
  else:refs.append(document(path,True)[1])
 return refs
def ticks(raw):
 fields=raw[raw.rindex(')')+2:].split()
 return dict(state=fields[0],start_ticks=int(fields[19]),utime=int(fields[11]),stime=int(fields[12]))
lock_raw,unused=read('/proc/locks',262144);locks=lock_raw.decode().splitlines()
def owners(path):
 info=path.stat();wanted=(os.major(info.st_dev),os.minor(info.st_dev),info.st_ino);result=[]
 for line in locks:
  fields=line.split()
  if len(fields)<6 or fields[1]!='FLOCK':continue
  device=fields[5].split(':')
  if len(device)==3 and (int(device[0],16),int(device[1],16),int(device[2]))==wanted:result.append(int(fields[4]))
 return result
for arm,prior in options['arms'].items():
 root=pathlib.Path(prior['root']);pid=prior['pid'];summary=dict(arm=arm,events=[],errors=[])
 process=pathlib.Path('/proc',str(pid))
 summary['process_exists']=process.exists()
 if process.exists():
  raw,unused=read(process/'stat',16384);summary['process']=ticks(raw.decode())
  raw,unused=read(process/'cmdline',16384);argv=raw.decode().rstrip('\0').split('\0')
  assert argv==prior['argv'] and summary['process']['start_ticks']==prior['start_ticks'],'service_identity_changed'
 else:summary['errors'].append('R162_OWNER_ABSENT')
 summary['locks']={name:owners(root/name/'OWNER.lock') for name in ('train_service_r159','train_service_r162')}
 if any(value!=[pid] for value in summary['locks'].values()):summary['errors'].append('OWNER_LOCK_MISSING_OR_CHANGED')
 summary['writer_pids']=owners(root/'stream/WRITER.lock')
 for writer in summary['writer_pids']:
  path=pathlib.Path('/proc',str(writer))
  raw,ref=read(path/'stat',16384);summary.setdefault('writers',[]).append(dict(pid=writer,stat=ticks(raw.decode()),stat_reference=ref))
 for unused in range(300):
  path=root/'train_service_r162'/f"{prior['next_index']:08d}.json"
  if not path.exists():break
  event,ref=document(path)
  assert event['schema']=='R162_TRAIN_EPOCH_EVENT_V1' and event['index']==prior['next_index']
  assert event['previous_sha256']==prior['previous'] and event['sha256']==digest({k:v for k,v in event.items() if k!='sha256'})
  state=event['state'];assert state['config_sha256']==prior['config_digest'] and state['floor']==prior['floor']
  assert state['started_unix']==prior['started_unix'] and state['offers']<=24 and state['check_calls']<=48
  if prior.get('last_counters'):
   assert all(state[key]>=prior['last_counters'][key] for key in ('cursor','offers','check_calls','polls','read_bytes','record_reads','output_reserved'))
  prior['last_counters']={key:state[key] for key in ('cursor','offers','check_calls','polls','read_bytes','record_reads','output_reserved')}
  prior['next_index']+=1;prior['previous']=event['sha256'];prior['state']=state
  if state.get('feedback'):prior['feedback']=state['feedback']
  if event['kind'] not in ('POLL','BUDGET_RESERVED','CURSOR_CONSUMED'):
   item=dict(kind=event['kind'],reference=ref,details=event['details'],state=state)
   if event['kind']=='CONTEXT_LOSS_RETIREMENT':
    item['loss_requests']=[record(root,proof['request_index']) for proof in event['details']['losses'].values()]
   if event['kind']=='ACTION_COMPLETE' and event['details']['action']=='offer':item['publication']=evidence(root,state['task'])
   if event['kind']=='OWN_RESPONSE_EXPOSED':
    index=event['details']['response_index'];item['triple']=[record(root,index+offset) for offset in (-1,0,1)]
   if event['kind']=='ACTION_COMPLETE' and event['details']['action']=='check':
    item['result']=evidence(root,state['feedback'])
    result,_=document(pathlib.Path(state['feedback']['source']['path']))
    index=result['origin']['response_index'];item['triple']=[record(root,index+offset) for offset in (-1,0,1)]
   if event['kind']=='FEEDBACK_ACTUALLY_RENDERED':
    item['feedback']=prior['feedback'];item['request']=record(root,state['cursor']-1)
   summary['events'].append(item)
 summary['validated_through']=prior['next_index']-1;summary['ledger_tip']=prior['previous'];summary['state']=prior.get('state')
 summary['caught_up']=not (root/'train_service_r162'/f"{prior['next_index']:08d}.json").exists()
 paths=[path for path in (root/'stream/records').iterdir() if re.fullmatch(r'[0-9]{20}\.json',path.name)]
 assert len(paths)<40000
 head=max(paths,key=lambda path:path.name);summary['journal_head']=dict(index=int(head.stem),bytes=head.stat().st_size,mtime=head.stat().st_mtime)
 if head.stat().st_size<4096:
  value,ref=document(head);summary['journal_head'].update(kind=value['kind'],reference=ref)
  summary['journal_head']['background_metadata']={key:value['document'][key] for key in ('cycle','status','optimizer_steps','step') if key in value['document']}
 summary['old_ledger_entries']=len([path for path in (root/'train_service_r159').iterdir() if re.fullmatch(r'[0-9]{8}\.json',path.name)])
 assert summary['old_ledger_entries']==prior['old_entries'],'old_ledger_length_changed'
 summaries.append(summary)
print(json.dumps(dict(schema='R162_BOUNDED_OBSERVER_POLL_V1',observed_unix=time.time(),read_bytes=used,arms=summaries,artifacts=artifacts,next_arms=options['arms'])))
'''


def exclusive(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), 0o400)


def main():
    assert time.time() < DEADLINE
    receipts = sorted(DIRECTORY.glob('POLL_*.json'))
    initial = json.loads((DIRECTORY/'INITIAL.json').read_bytes())
    consumed = 0
    for path in DIRECTORY.glob('*.json'):
        document = json.loads(path.read_bytes())
        if 'read_bytes' in document:
            consumed += document['read_bytes']+path.stat().st_size
    if receipts:
        previous = json.loads(receipts[-1].read_bytes())
        assert time.time()-previous['observed_unix'] >= 15
        arms = previous['next_arms']
    else:
        arms = {}
        for arm in initial['arms']:
            state = arm['00000000.json']['document']['state']
            raw = arm['proc_stat'];fields = raw[raw.rindex(')')+2:].split()
            arms[arm['arm']] = dict(root=arm['authority']['config']['path'].split('/orch_r159_train_service_candidate5_20260917/')[0]
                +'/orch_r158_matched_node4_20260917_attempt5/'+arm['arm'], pid=arm['pid'], argv=arm['argv'],
                start_ticks=int(fields[19]), previous=arm['authority']['predecessor']['tip'], next_index=0,
                old_entries=arm['authority']['predecessor']['entries'],config_digest=state['config_sha256'],
                floor=state['floor'], started_unix=state['started_unix'])
    archived = {}
    for path in receipts:
        for artifact in json.loads(path.read_bytes()).get('artifacts', {}).values():
            archived[artifact['path']] = artifact['sha256']
    allowance = min(6*1024**2, (BUDGET-consumed)//3)
    assert allowance > 512*1024, 'observer_remaining_budget'
    options = dict(deadline=DEADLINE,allowance=allowance,arms=arms,archived=archived)
    script = 'options=json.loads('+repr(json.dumps(options))+')\n'
    script = 'import json\n'+script+REMOTE
    completed = subprocess.run(['bash','gpu/a40r_ssh.sh','python3 -B -'],input=script.encode(),
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(40,DEADLINE-time.time()))
    path = DIRECTORY/f'POLL_{len(receipts):04d}.json'
    if completed.returncode:
        exclusive(path, json.dumps(dict(schema='R162_OBSERVER_ERROR_V1', observed_unix=time.time(),
            read_bytes=allowance,error=completed.stderr.decode(errors='replace')[-2000:],
            next_arms=arms,artifacts={})).encode())
        raise SystemExit('Observer stopped on error; no service action retried')
    report = json.loads(completed.stdout)
    assert consumed+report['read_bytes']+len(completed.stdout) <= BUDGET
    exclusive(path, completed.stdout)
    for artifact in report['artifacts'].values():
        raw = base64.b64decode(artifact['raw_base64'])
        assert hashlib.sha256(raw).hexdigest() == artifact['sha256']
    print('UTC',time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(report['observed_unix'])),
        'TOTAL_BYTES',consumed+report['read_bytes']+len(completed.stdout),flush=True)
    for arm in report['arms']:
        state = arm['state'] or {}
        print(arm['arm'],'ledger',arm['validated_through'],'caught_up',arm['caught_up'],
            'state',{key:state.get(key) for key in ('cursor','offers','task_index','exposures','check_calls','terminal')},
            'head',arm['journal_head'],'events',[event['kind'] for event in arm['events']],
            'errors',arm['errors'],flush=True)


if __name__ == '__main__':
    main()
