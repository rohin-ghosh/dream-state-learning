"""Finite read-only live, failed-dispatch, and first-action evidence export."""

import datetime
import json
from pathlib import Path
import shlex
import subprocess


REMOTE = r'''
import pathlib,json,datetime,os,subprocess
base=pathlib.Path('/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1')
def read(path):return json.loads(path.read_bytes())
def meta(path):
 with path.open('rb') as stream:
  stream.seek(max(0,path.stat().st_size-4096));tail=stream.read()
 return json.loads(b'{'+tail[tail.rfind(b',"index":')+1:])
result=dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),arms={})
for arm in ['math_d1','repo_c1','creative_d1','math_transfer_c1']:
 root=base/arm; newer=arm in ['creative_d1','math_transfer_c1'];control=root/('control_r204_casefix' if newer else 'control')
 row=dict(control=str(control));result['arms'][arm]=row
 if newer:
  failure=root/'failed_dispatch_r203_pci_case'
  row['preserved_failure']=str(failure)
  row['stderr_tail']=(failure/'supervisor.log').read_text().splitlines()[-24:]
  row['repair']={key:value for key,value in read(root/'R204_CASE_REPAIR.json').items() if key!='source_pins'}
  row['strict_probe']=read(control/'CONFINEMENT_CHILD.json')
 row['driver_options']={key:value for key,value in read(control/'PLAN.json')['think_act_learn'].items() if key in ['think_continuation_policy','think_segments','max_think_segments','context_policy','context_token_budget','context_compact_tokens','new_presentations','trial_id']}
 row['parent_receipts']={path.name:{key:value for key,value in read(path).items() if key not in ['text','message','source_receipt','publication']} for path in (root/'parent_receipts').glob('*.json')}
 stages=[];acts=[];completed=[];requests=[]
 paths={int(path.stem):path for path in (root/'raw/stream/records').glob('*.json') if not path.name.endswith('.intent.json')}
 for index,path in sorted(paths.items()):
  if index<5847:continue
  metadata=meta(path);kind=metadata['kind']
  if kind not in ['LOADED','REQUEST','R184_STAGE','R184_ACT','SLEEP_COMPLETE']:continue
  record=read(path);doc=record['document'];entry=dict(index=index,sha256=record['sha256'],kind=kind,mtime_utc=datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat())
  if kind=='LOADED':entry.update({key:doc.get(key) for key in ['pid','optimizer_steps','loaded_unix','adapter_sha256']});row['loaded']=entry
  elif kind=='REQUEST':
   if not requests:row['first_request']=entry
   requests.append((entry,doc))
  elif kind=='R184_STAGE':
   entry.update(stage=doc.get('stage'),segment=doc.get('segment'));stages.append(entry)
  elif kind=='R184_ACT':
   entry.update(document_keys=list(doc),document={key:doc[key] for key in ['origin','outcome','status','executed','returncode'] if key in doc});acts.append(entry)
  elif kind=='SLEEP_COMPLETE':
   entry.update({key:doc.get(key) for key in ['cycle','optimizer_steps','optimizer_steps_after','updates','status']});completed.append(entry)
 row['first_think']=next((entry for entry in stages if entry['stage']=='THINK'),None)
 row['first_act_stage']=next((entry for entry in stages if entry['stage']=='ACT'),None)
 row['latest_stages']=stages[-4:];row['complete_cycles']=completed;row['acts']=acts[-3:]
 process=pathlib.Path('/proc')/str(row['loaded']['pid'])
 try:
  fields=(process/'stat').read_text().rsplit(')',1)[1].split()
  row['native']=dict(pid=row['loaded']['pid'],state=fields[0],start_ticks=fields[19],cwd=os.readlink(process/'cwd'),uid=process.stat().st_uid,alive=fields[0] not in ['Z','X'])
 except (FileNotFoundError,ProcessLookupError):row['native']=dict(pid=row['loaded']['pid'],alive=False)
 if acts:
  first=acts[0];response_index=first['document'].get('origin',{}).get('record_index')
  if response_index is not None:
   response=read(paths[response_index]);raw=response['document'].get('response',{}).get('raw')
   row['first_act_response']=dict(index=response_index,sha256=response['sha256'],finished_unix=response['document'].get('finished_unix'),raw=raw[:6500] if isinstance(raw,str) else None,raw_truncated=isinstance(raw,str) and len(raw)>6500)
  next_request=next(((entry,doc) for entry,doc in requests if entry['index']>first['index']),None)
  if next_request:
   entry,doc=next_request;row['first_act_following_request']=dict(**entry,document_keys=list(doc),render_receipt=doc.get('render_receipt'))
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader'],capture_output=True,text=True,timeout=12,check=True)
result['nvml_processes']=gpu.stdout.strip().splitlines()
print(json.dumps(result))
'''


def main():
    result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(REMOTE)],
        capture_output=True, text=True, timeout=45, check=True)
    receipt = json.loads(result.stdout)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = Path(__file__).resolve().parent / 'receipts' / ('DISPATCH_REPAIR_AND_ACT_' + stamp + '.json')
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    patch += ''.join('+' + line + '\n' for line in json.dumps(receipt, indent=2).splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, capture_output=True, check=True)
    print('SAVED', path)
    for arm, row in receipt['arms'].items():
        print(json.dumps(dict(arm=arm, native=row['native'], loaded=row['loaded']['index'],
            first_request=row['first_request']['index'], first_ACT=row['first_act_stage'],
            latest_stage=row['latest_stages'][-1], completed=[entry['cycle'] for entry in row['complete_cycles']])))


if __name__ == '__main__':
    main()
