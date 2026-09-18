"""Read-only single-waiter follow-up; never import or execute the handoff operator."""

import json
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import hashlib,json,os,time
from pathlib import Path
phase=Path('/localhome/local-rohing/orch_r153_r193_C2_masked_ce_20260917_phase1')
life=Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
def sha(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read_record(path):
 value=json.loads(path.read_bytes())
 assert value['sha256']==digest({key:item for key,item in value.items() if key!='sha256'})
 return value
def meta(path):
 with path.open('rb') as stream:
  stream.seek(max(0,path.stat().st_size-4096));raw=stream.read()
 return json.loads(b'{'+raw[raw.rfind(b',"index":')+1:])
out=dict(observed_unix=time.time(),signals=0,publications=0,live_changes=0,receipts={},pids={},loaded=None,recipe=None,dataset={},preservation={})
for name in ('WAITER_START.json','ARMED.json','READY_AT_BOUNDARY.json','STATE_CPU.json','FAILED.json','RETIRED.json','STARTED.json','control/OUTER_FAILED.json','control/OUTER_STARTED.json','control/EXIT.json','control/FAILED.json'):
 path=phase/name
 if path.exists():
  document=json.loads(path.read_bytes())
  out['receipts'][name]=dict(path=str(path),sha256=sha(path),document={key:value for key,value in document.items() if key not in ('inbox','checkpoint_files')})
paths=sorted((life/'stream/records').glob('[0-9]'*20+'.json'))
catalog=[meta(path) for path in paths if int(path.stem)>=5615]
out['head']=catalog[-1]
head=read_record(paths[-1])
out['head_fields']={key:value for key,value in head['document'].items() if key in ('cycle','optimizer_step','finished_unix','stage','segment','started_unix')}
complete_meta=next(item for item in reversed(catalog) if item['kind']=='SLEEP_COMPLETE')
complete_path=life/'stream/records'/f"{complete_meta['index']:020d}.json"
complete=read_record(complete_path)['document']
out['latest_complete']=dict(index=complete_meta['index'],record_sha256=complete_meta['sha256'],cycle=complete['cycle'],updates=complete['optimizer_steps'],total_optimizer_steps=complete['total_optimizer_steps'],record_mtime_ns=complete_path.stat().st_mtime_ns)
cutoff=None
boundary_path=phase/'BOUNDARY.json'
if boundary_path.exists():
 boundary=json.loads(boundary_path.read_bytes());cutoff=int(Path(boundary['head']['path']).stem)
 record=read_record(Path(boundary['reference']['path']))
 before=boundary['record']['document']['resume_state']['state']
 checkpoint=boundary['record']['document']['checkpoint']
 history=before['history']
 proof=dict(cycle=boundary['cycle'],boundary_index=boundary['index'],head_index=cutoff,
  exact_saved_state_digest=digest(before)==boundary['state_sha256']==record['document']['resume_state']['sha256'],
  boundary_record_unchanged=sha(Path(boundary['reference']['path']))==boundary['reference']['sha256'],
  head_record_unchanged=sha(Path(boundary['head']['path']))==boundary['head']['sha256'],
  full_saved_rows=len(before['rows']),full_saved_history_events=len(history['events']),
  saved_rows_sha256=digest(before['rows']),saved_history_sha256=digest(history),
  pending=before['pending'],sleep_frontier=before['sleep_frontier'],checkpoint_optimizer_steps=checkpoint['optimizer_steps'])
 ready_path=phase/'READY_AT_BOUNDARY.json'
 if ready_path.exists():
  ready=json.loads(ready_path.read_bytes())
  proof['checkpoint_original_and_preserved_files_match']=all(sha(life/'checkpoints'/('sleep_%06d'%boundary['cycle'])/name)==value and sha(phase/'preserved_checkpoint'/name)==value for name,value in ready['checkpoint_files'].items())
  proof['inbox_preserved_ids']=[Path(name).stem for name in sorted(ready['inbox'])]
  proof['inbox_all_bound_bytes_preserved']=all((life/'stream/inbox'/name).is_file() and sha(life/'stream/inbox'/name)==value for name,value in ready['inbox'].items())
  proof['preserved_parent_ids']=[Path(name).stem for name in ready['inbox'] if json.loads((life/'stream/inbox'/name).read_bytes()).get('actor')=='parent']
  proof['one_shot_parent_preserved']='311ae25be2484fccbcd8af839c4fa025' in proof['preserved_parent_ids']
 out['preservation']=proof
 for item in catalog:
  if item['index']<=cutoff:continue
  path=life/'stream/records'/f"{item['index']:020d}.json"
  if item['kind']=='LOADED' and out['loaded'] is None:
   body=read_record(path)['document']
   out['loaded']=dict(index=item['index'],record_sha256=item['sha256'],file_sha256=sha(path),restored_cycle=boundary['cycle'],**{key:body[key] for key in ('pid','loaded_unix','optimizer_steps','resume','adapter_sha256') if key in body})
   out['loaded']['optimizer_steps_exact']=body['optimizer_steps']==checkpoint['optimizer_steps']
   out['loaded']['adapter_state_exact']=body['adapter_sha256']==checkpoint['adapter_state_sha256']
  if item['kind']=='COMMITTED' and 'post_boundary_rows_prefix_exact' not in proof:
   body=read_record(path)['document'];after=body['state']['state']
   proof['first_post_boundary_commit_index']=item['index']
   proof['first_post_boundary_commit_sha256']=item['sha256']
   proof['post_boundary_rows_prefix_exact']=after['rows'][:len(before['rows'])]==before['rows']
   proof['post_boundary_history_events_prefix_exact']=after['history']['events'][:len(history['events'])]==history['events']
   proof['post_boundary_saved_context_limit_unchanged']=after['context_limit']==before['context_limit']
   proof['post_boundary_commit_origin']='successor' if out['loaded'] else 'original_runtime_no_successor_load'
  if item['kind']=='SLEEP_RECIPE' and out['recipe'] is None:
   body=read_record(path)['document'];out['recipe']=dict(index=item['index'],record_sha256=item['sha256'],document=body)
 out['dataset_journal_records']=[dict(index=item['index'],kind=item['kind'],record_sha256=item['sha256']) for item in catalog if item['index']>cutoff and item['kind'] in ('R191_DATASET_ROW','R191_EXPORT_ERROR')]
 proof['adapter_files_match']=all(sha(Path(checkpoint['adapter_path'])/name)==value for name,value in checkpoint['adapter_files'].items())
 proof['optimizer_rng_file_sha256']=sha(Path(checkpoint['optimizer_rng_path']))
 proof['optimizer_rng_bytes_match']=proof['optimizer_rng_file_sha256']==checkpoint['checkpoint_sha256']['optimizer']==checkpoint['checkpoint_sha256']['rng']
old=Path('/localhome/local-rohing/orch_r153_r193_C2_20260917_recovery1/parent_intervention_R193_20260917T1759PDT')
intent=json.loads((old/'INTENT.json').read_bytes())
publication=json.loads((old/'PUBLICATION.json').read_bytes())['publication']
expected=intent['prior_parent_inventory']+[publication]
out['preserved_parent_inventory']=[]
for entry in expected:
 path=Path(entry['path']);document=json.loads(path.read_bytes())
 out['preserved_parent_inventory'].append(dict(id=document['id'],speaker=document['speaker'],sha256=sha(path),unchanged=sha(path)==entry['sha256']))
out['all_21_preexisting_parent_bytes_unchanged']=len(expected)==21 and all(item['unchanged'] for item in out['preserved_parent_inventory'])
plan=json.loads((phase/'control/PLAN.json').read_bytes())
dataset=life/'stream/exploration'/(plan['think_act_learn']['trial_id']+'.jsonl')
out['dataset']=dict(path=str(dataset),exists=dataset.exists(),complete_row_count=0,rows=[])
if dataset.exists():
 raw=dataset.read_bytes();rows=[json.loads(line) for line in raw.splitlines(keepends=True) if line.endswith(b'\n')]
 out['dataset'].update(complete_row_count=len(rows),snapshot_sha256=hashlib.sha256(raw).hexdigest(),partial_last_line=bool(raw) and not raw.endswith(b'\n'),rows=[{key:row.get(key) for key in ('row_id','cycle','stage','schema')} for row in rows])
pids={2981108:'waiter',2930123:'original_native',2930061:'original_outer',2930020:'original_math_bridge'}
started=out['receipts'].get('STARTED.json',{}).get('document',{})
for role,identity in started.get('processes',{}).items():pids[identity['pid']]='successor_'+role
if out['loaded']:pids[out['loaded']['pid']]='successor_native'
for pid,role in pids.items():
 try:
  process=Path('/proc')/str(pid);fields=(process/'stat').read_text().rsplit(')',1)[1].split()
  out['pids'][role]=dict(pid=pid,state=fields[0],parent=int(fields[1]),start_ticks=fields[19],cwd=os.readlink(process/'cwd'),argv=(process/'cmdline').read_bytes().decode().rstrip('\0').split('\0'))
 except FileNotFoundError:out['pids'][role]=dict(pid=pid,alive=False)
print(json.dumps(out,sort_keys=True))
'''


def main():
    result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', '/localhome/local-rohing/v2/venv/bin/python -'],
        input=REMOTE, text=True, capture_output=True, timeout=35)
    receipt = dict(returncode=result.returncode, observed_local_unix=time.time(), stderr=result.stderr)
    if result.returncode == 0:
        receipt['result'] = json.loads(result.stdout)
    else:
        receipt['stdout'] = result.stdout
    path = HERE / ('FOLLOWUP_' + str(time.time_ns()) + '.json')
    with path.open('x') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(dict(path=str(path), **receipt), indent=2, sort_keys=True))
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
