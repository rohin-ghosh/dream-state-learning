"""Read-only finite R194 receipt inspection without opening the live writer."""

import json
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import hashlib,json,os,time
from pathlib import Path
phase=Path('/localhome/local-rohing/orch_r153_r194_C2_20260917_console1')
life=Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
def sha(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def checkpoint_state(document):
 envelope=document['state'];state=envelope['state']
 assert envelope['sha256']==digest(state)
 return state
def read(path):return json.loads(path.read_bytes())
def record(path):
 value=read(path)
 assert value['sha256']==digest({key:item for key,item in value.items() if key!='sha256'})
 return value
def meta(path):
 with path.open('rb') as stream:
  stream.seek(max(0,path.stat().st_size-4096));raw=stream.read()
 return json.loads(b'{'+raw[raw.rfind(b',"index":')+1:])
def reference(path):return dict(path=str(path),sha256=sha(path))
out=dict(observed_unix=time.time(),signals=0,publications=0,live_changes=0,receipts={},pids={},loaded=None,mode=None,recipe=None,preservation={})
for name in ('WAITER_START.json','ARMED.json','READY_AT_BOUNDARY.json','STATE_CPU.json','FAILED.json','RETIRED.json','STARTED.json','control/OUTER_FAILED.json','control/OUTER_STARTED.json','control/NATIVE_EXIT.json','control/FAILED.json'):
 path=phase/name
 if path.exists():
  document=read(path)
  out['receipts'][name]=dict(**reference(path),document={key:value for key,value in document.items() if key not in ('inbox','checkpoint_files')})
paths=sorted((life/'stream/records').glob('[0-9]'*20+'.json'))
catalog=[meta(path) for path in paths if int(path.stem)>=5753]
out['head']=catalog[-1]
head=record(paths[-1])
out['head_fields']={key:value for key,value in head['document'].items() if key in ('cycle','optimizer_step','finished_unix','stage','segment','started_unix')}
complete_meta=next(item for item in reversed(catalog) if item['kind']=='SLEEP_COMPLETE')
complete_path=life/'stream/records'/f"{complete_meta['index']:020d}.json"
complete=record(complete_path)['document']
out['latest_complete']=dict(index=complete_meta['index'],record_sha256=complete_meta['sha256'],cycle=complete['cycle'],updates=complete['optimizer_steps'],total_optimizer_steps=complete['total_optimizer_steps'],record_mtime_ns=complete_path.stat().st_mtime_ns)
boundary_path=phase/'BOUNDARY.json'
if boundary_path.exists():
 boundary=read(boundary_path);cutoff=int(Path(boundary['head']['path']).stem)
 before=boundary['record']['document']['resume_state']['state']
 checkpoint=boundary['record']['document']['checkpoint']
 proof=dict(cycle=boundary['cycle'],boundary_index=boundary['index'],head_index=cutoff,
  exact_saved_state_digest=digest(before)==boundary['state_sha256']==record(Path(boundary['reference']['path']))['document']['resume_state']['sha256'],
  boundary_record_unchanged=sha(Path(boundary['reference']['path']))==boundary['reference']['sha256'],
  head_record_unchanged=sha(Path(boundary['head']['path']))==boundary['head']['sha256'],
  full_saved_rows=len(before['rows']),full_saved_history_events=len(before['history']['events']),
  saved_rows_sha256=digest(before['rows']),saved_history_sha256=digest(before['history']),
  pending=before['pending'],sleep_frontier=before['sleep_frontier'],checkpoint_optimizer_steps=checkpoint['optimizer_steps'])
 ready_path=phase/'READY_AT_BOUNDARY.json'
 if ready_path.exists():
  ready=read(ready_path)
  proof['checkpoint_original_and_preserved_files_match']=all(sha(life/'checkpoints'/('sleep_%06d'%boundary['cycle'])/name)==value and sha(phase/'preserved_checkpoint'/name)==value for name,value in ready['checkpoint_files'].items())
  proof['inbox_preserved_ids']=[Path(name).stem for name in sorted(ready['inbox'])]
  proof['inbox_all_bound_bytes_preserved']=all((life/'stream/inbox'/name).is_file() and sha(life/'stream/inbox'/name)==value for name,value in ready['inbox'].items())
 proof['adapter_files_match']=all(sha(Path(checkpoint['adapter_path'])/name)==value for name,value in checkpoint['adapter_files'].items())
 proof['optimizer_rng_file_sha256']=sha(Path(checkpoint['optimizer_rng_path']))
 proof['optimizer_rng_bytes_match']=proof['optimizer_rng_file_sha256']==checkpoint['checkpoint_sha256']['optimizer']==checkpoint['checkpoint_sha256']['rng']
 out['preservation']=proof
 out['post_boundary_record_kinds']={}
 for item in catalog:
  if item['index']<=cutoff:continue
  out['post_boundary_record_kinds'][item['kind']]=out['post_boundary_record_kinds'].get(item['kind'],0)+1
  path=life/'stream/records'/f"{item['index']:020d}.json"
  if item['kind'] in ('LOADED','R194_MODE','SLEEP_RECIPE','R194_TURN'):
   body=record(path)['document']
   result=dict(index=item['index'],record_sha256=item['sha256'],file_sha256=sha(path),document=body)
   if item['kind']=='LOADED' and out['loaded'] is None:
    out['loaded']=result
    result['matches_saved_optimizer_steps']=body['optimizer_steps']==checkpoint['optimizer_steps']
    state_cpu=read(phase/'STATE_CPU.json')
    result['matches_saved_adapter']=body['adapter_sha256']==state_cpu['adapter_state_sha256']
   elif item['kind']=='R194_MODE':out['mode']=result
   elif item['kind']=='SLEEP_RECIPE':out['recipe']=result
   elif item['kind']=='R194_TURN':out.setdefault('console_turns',[]).append(result)
  if item['kind'] in ('COMMITTED','CONTEXT_COMMITTED','CONTEXT_INPUT') and 'first_post_boundary_commit_index' not in proof:
   after=checkpoint_state(record(path)['document'])
   proof['first_post_boundary_commit_index']=item['index']
   proof['first_post_boundary_commit_sha256']=item['sha256']
   proof['post_boundary_rows_prefix_exact']=after['rows'][:len(before['rows'])]==before['rows']
   proof['post_boundary_history_events_prefix_exact']=after['history']['events'][:len(before['history']['events'])]==before['history']['events']
   proof['post_boundary_rows_added']=len(after['rows'])-len(before['rows'])
  if item['kind']=='CONTEXT_COMMITTED':
   body=record(path)['document'];state=checkpoint_state(body)
   out.setdefault('context_only_commits',[]).append(dict(index=item['index'],record_sha256=item['sha256'],
    training_eligible=body['training_eligible'],training_rows=len(state['rows']),
    rows_equal_saved_boundary=state['rows']==before['rows'],pending=state['pending']))
  if item['kind']=='INBOX':
   body=record(path)['document'];message=body['message']
   if message.get('speaker')=='Rohin':
    out.setdefault('rohin_inputs',[]).append(dict(index=item['index'],record_sha256=item['sha256'],
     id=message.get('id'),speaker=message['speaker'],schema=message.get('schema'),
     source_id=body['source_id'],source_sha256=body['source_sha256']))
 if out['mode']:
  after_mode=[item for item in catalog if item['index']>out['mode']['index']]
  out['mode']['later_sleep_or_update_records']=[dict(index=item['index'],kind=item['kind']) for item in after_mode if item['kind'] in ('SLEEP_REQUEST','UPDATE','SLEEP_COMPLETE','R184_ACT','R184_LEARN_COMPLETE')]
plan=read(phase/'control/PLAN.json')
out['config']=dict(sleep_loss_impl=plan.get('sleep_loss_impl'),rehearsal_presentations=plan['rehearsal_presentations'],new_presentations=plan['new_presentations'],think_act_learn=plan['think_act_learn'],source_root=plan['source_root'])
dataset=life/'stream/exploration'/(plan['think_act_learn']['trial_id']+'.jsonl')
out['dataset']=dict(path=str(dataset),exists=dataset.exists(),complete_row_count=0)
if dataset.exists():
 raw=dataset.read_bytes();rows=[json.loads(line) for line in raw.splitlines(keepends=True) if line.endswith(b'\n')]
 out['dataset'].update(complete_row_count=len(rows),snapshot_sha256=hashlib.sha256(raw).hexdigest(),partial_last_line=bool(raw) and not raw.endswith(b'\n'))
expected={2930123:('old_native','22768040'),2930061:('old_outer','22767888'),2930020:('old_math_bridge','22767768')}
start=read(phase/'WAITER_START.json')['identity']
expected[start['pid']]=('waiter',start['start_ticks'])
for role,identity in out['receipts'].get('STARTED.json',{}).get('document',{}).get('processes',{}).items():expected[identity['pid']]=('new_'+role,identity['start_ticks'])
if out['loaded']:expected[out['loaded']['document']['pid']]=('new_native',None)
for pid,(role,ticks) in expected.items():
 try:
  process=Path('/proc')/str(pid);fields=(process/'stat').read_text().rsplit(')',1)[1].split()
  out['pids'][role]=dict(pid=pid,state=fields[0],parent=int(fields[1]),start_ticks=fields[19],identity_matches=ticks is None or ticks==fields[19],cwd=os.readlink(process/'cwd'),argv=(process/'cmdline').read_bytes().decode().rstrip('\0').split('\0'))
 except FileNotFoundError:out['pids'][role]=dict(pid=pid,alive=False)
if out['loaded'] and out['pids'].get('new_native',{}).get('cwd'):
 out['pids']['new_native']['expected_source_and_guard']=out['pids']['new_native']['cwd']==str(phase/'source') and out['pids']['new_native']['argv'][-2:]==['--config',str(phase/'control/GUARD.json')]
print(json.dumps(out,sort_keys=True))
'''


def main():
    result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh',
        'PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B -'],
        input=REMOTE, text=True, capture_output=True, timeout=45)
    receipt = dict(returncode=result.returncode, observed_local_unix=time.time(), stderr=result.stderr)
    if result.returncode == 0:
        receipt['result'] = json.loads(result.stdout)
    else:
        receipt['stdout'] = result.stdout
    path = HERE / ('OBSERVE_' + str(time.time_ns()) + '.json')
    with path.open('x') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write('\n')
    detail = receipt.get('result', {})
    preservation = dict(detail.get('preservation', {}))
    if 'inbox_preserved_ids' in preservation:
        preservation['inbox_preserved_count'] = len(preservation.pop('inbox_preserved_ids'))
    print(json.dumps(dict(path=str(path), returncode=result.returncode, stderr=result.stderr,
        latest_complete=detail.get('latest_complete'), head=detail.get('head'),
        receipts=list(detail.get('receipts', {})), loaded=detail.get('loaded'),
        mode=detail.get('mode'), recipe=detail.get('recipe'), pids=detail.get('pids'),
        preservation=preservation, dataset=detail.get('dataset')), indent=2, sort_keys=True))
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
