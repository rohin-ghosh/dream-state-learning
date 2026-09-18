"""Read-only node1 receipt join; no launch, training, probe, or gating actions."""

import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[4]
REMOTE_CHECK = r'''
import hashlib,json,pathlib,time
arms=json.loads(ARMS_JSON)
expected=json.loads(EXPECTED_JSON)
read=lambda path:json.loads(path.read_bytes())
def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def file_ref(path):
 stat=path.stat()
 with path.open('rb') as incoming: checksum=hashlib.file_digest(incoming,'sha256').hexdigest()
 return dict(path=str(path),sha256=checksum,bytes=stat.st_size,uid=stat.st_uid,gid=stat.st_gid,inode=stat.st_ino)
def ref(path,record):
 return dict(index=int(path.stem),sha256=record['sha256'],mtime_unix=path.stat().st_mtime)
def small(value,keys):
 return {key:value[key] for key in keys if key in value}
report=dict(observed_unix=time.time(),main_ready_archive_sha256='b0f148c92172af9d1525fda79a97bebfb31337e312e26c0f6bc805b3c687f8fc',arms=[],protected=[],hard_end_unix=1790442300,lease_end_unix=1790463900)
for arm in arms:
 root=pathlib.Path(arm['remote_root']);update=root.with_name(root.name+'_r204')
 item=small(arm,('physical','name','task','parent_observer_withdrawn'))
 pins=read(update/'R204_SOURCE.json')['source_pins']
 actual={name:hashlib.sha256((update/'source'/name).read_bytes()).hexdigest() for name in pins}
 assert actual==pins
 for name,sha in expected.items():assert actual[name]==sha,(arm['name'],name)
 item['source_hashes_match']=True;item['source_file_count']=len(actual)
 plan=read(update/'control/PLAN.json');policy=plan['think_act_learn']
 assert plan['hard_end_unix']==1790442300 and plan['lease_end_unix']==1790463900
 assert plan['max_sleeps']==57 and plan['new_presentations']==16 and plan['rehearsal_presentations']==0 and plan['anchor_lambda']==0.25
 assert policy['think_continuation_policy']=='R204_EXPLICIT_THINK_CONTINUATION_V1'
 assert policy['stage_boundary_policy']=='R203_STAGE_BOUNDARIES_V1'
 assert policy['prose_target_filter']=='R203_INTERNAL_COMMON_WORD_CAPITALIZATION_V1'
 if arm['structured']:assert policy['structured_think_policy']=='R202_WIDE_NARROW_WIDE_V1'
 item['policy']=small(policy,('think_continuation_policy','stage_boundary_policy','prose_target_filter','structured_think_policy','cpu_gate_sha256'))
 item['same_physical_life']=str(root/'life');item['same_logical_life']=plan['root']
 item['active_control_redirect']=(root/'ACTIVE_CONTROL.json').exists()
 if item['active_control_redirect']:
  active=read(root/'ACTIVE_CONTROL.json')
  assert active['control_root']==str(update/'control') and active['guard_sha256']==hashlib.sha256((update/'control/GUARD.json').read_bytes()).hexdigest()
 for filename in ('BOUNDARY_STATE.json','RESTORE_CPU.json','BOUNDARY.json','RETIRED.json','DISPATCHED.json','control/LAUNCH.json','control/EXIT.json'):
  path=update/filename
  if not path.exists():continue
  value=read(path)
  item[filename]=small(value,('cycle','state_sha256','record_sha256','terminal_sha256','status','adapter_sha256','optimizer_steps','optimizer_restored_exact','cuda_initialized','exact_state_sha256','observed_unix','preserved_unix','retired_unix','dispatched_unix','pid','started_unix','finished_unix','exit_code','same_logical_life','full_stream_and_checkpoint','old_process_only','no_input_replay'))
  if filename=='BOUNDARY_STATE.json':assert digest(value['state'])==value['state_sha256']
  if filename=='BOUNDARY.json':item['preserved_inbox_file_count']=len(value['inbox_inventory'])
 item.update(initial_load=None,r204_load=None,first_request_after_r204=None,first_think_after_r204=None,latest_complete=51,opening_consumed=None,current_requests=[],current_compactions=[],current_compaction_notices=[],prior_clone_request_max_tokens=0,terminal=None,last_committed_state=None)
 item['compaction_threshold_tokens']=min(plan['context_limit']*3//4,plan['context_limit']-plan['segment_tokens'])
 item['parent_feedback']=[dict(draft=feedback['draft'],publication=feedback['publication'],inbox=None,first_render=None,render_cycle=None) for feedback in arm['feedback']]
 retired=item.get('RETIRED.json',{}).get('retired_unix',float('inf'))
 for path in sorted((root/'life/stream/records').glob('[0-9]'*20+'.json')):
  if int(path.stem)<5847:continue
  record=read(path)
  assert digest({key:value for key,value in record.items() if key!='sha256'})==record['sha256']
  document=record['document'];kind=record['kind'];receipt=ref(path,record)
  item['last_record']=dict(receipt,kind=kind)
  if kind=='SLEEP_COMPLETE' and document['status']=='COMPLETE':
   item['latest_complete']=document['cycle']
   envelope=document['resume_state'];state=envelope['state']
   assert digest(state)==envelope['sha256'] and state['pending'] is None and state['sleep_frontier']==len(state['rows'])
   item['last_complete_state']=dict(receipt,cycle=document['cycle'],state_sha256=envelope['sha256'],pending=None,sleep_frontier=state['sleep_frontier'],rows=len(state['rows']))
  if kind in ('COMMITTED','CONTEXT_COMMITTED'):
   envelope=document['state'];state=envelope['state']
   assert digest(state)==envelope['sha256']
   item['last_committed_state']=dict(receipt,state_sha256=envelope['sha256'],pending=state['pending'],sleep_frontier=state['sleep_frontier'],rows=len(state['rows']))
  if kind=='TERMINAL':item['terminal']=dict(receipt,**small(document,('status','sleeps','completed_sleeps','optimizer_steps','continued_after_sleep','retained_learning_claim','finished_unix')))
  if kind=='LOADED':
   load=dict(receipt,**small(document,('loaded_unix','optimizer_steps','pid','resume','adapter_sha256')))
   if item['initial_load'] is None:item['initial_load']=load
   if document['loaded_unix']>retired:item['r204_load']=load
  if kind=='INBOX':
   for feedback,observed in zip(arm['feedback'],item['parent_feedback']):
    if document['message']['text']==feedback['text'] and observed['inbox'] is None:observed['inbox']=receipt
  if kind=='REQUEST':
   text=chr(10).join(message.get('content','') for message in document.get('messages',[]))
   receipt.update(started_unix=document.get('started_unix'),messages_sha256=digest(document.get('messages',[])),prompt_tokens=document['prompt_tokens'],render_receipt=document['render_receipt'])
   if item['r204_load']:item['current_requests'].append(receipt)
   else:item['prior_clone_request_max_tokens']=max(item['prior_clone_request_max_tokens'],document['prompt_tokens'])
   if item['r204_load'] and item['first_request_after_r204'] is None:item['first_request_after_r204']=receipt
   if arm['opening'] in text and item['opening_consumed'] is None:item['opening_consumed']=receipt
   for feedback,observed in zip(arm['feedback'],item['parent_feedback']):
    if feedback['text'] in text and observed['first_render'] is None:
     observed['first_render']=receipt;observed['render_cycle']=item['latest_complete']+1
  if kind=='R184_STAGE' and document['stage']=='THINK' and item['r204_load'] and item['first_think_after_r204'] is None:
   item['first_think_after_r204']=dict(receipt,source_sha256=document['source_sha256'])
  if item['r204_load'] and kind=='COMPACTION':
   item['current_compactions'].append(dict(receipt,metadata={key:value for key,value in document.items() if key not in ('state','resume_state')}))
  if item['r204_load'] and kind=='CONTEXT_INPUT' and document.get('kind')=='R204_COMPACTION_NOTICE':
   item['current_compaction_notices'].append(dict(receipt,training_eligible=document['training_eligible']))
 if item['r204_load']:
  restore=item['RESTORE_CPU.json'];load=item['r204_load']
  assert restore['status']=='PASS' and restore['optimizer_restored_exact'] and not restore['cuda_initialized']
  assert load['optimizer_steps']==restore['optimizer_steps'] and load['adapter_sha256']==restore['adapter_sha256']
  assert restore['exact_state_sha256']==item['BOUNDARY_STATE.json']['state_sha256']
  item['exact_saved_to_loaded_match']=True
  process=pathlib.Path('/proc',str(load['pid']))
  if process.exists():
   stat=(process/'stat').read_text().rsplit(') ',1)[1].split()
   item['native_identity']=dict(pid=load['pid'],state=stat[0],start_ticks=stat[19],cwd=str((process/'cwd').resolve()),argv=(process/'cmdline').read_bytes().decode().split(chr(0))[:-1])
   assert item['native_identity']['cwd']==str(update/'source')
   assert item['native_identity']['argv'][-1]==str(update/'control/GUARD.json')
 item['current_request_max_tokens']=max((request['prompt_tokens'] for request in item['current_requests']),default=None)
 item['all_current_requests_below_threshold']=all(request['prompt_tokens']<item['compaction_threshold_tokens'] for request in item['current_requests'])
 item['failure_receipts']=[small(read(path),('observed_unix','error_type','reason','retired','no_automatic_retry')) for path in update.glob('CONTINUATION_FAILURE_*.json')]
 item['max_sleeps']=plan['max_sleeps']
 exit_path=update/'control/EXIT.json'
 if exit_path.exists():item['control/EXIT.json']=read(exit_path)
 item['observed_status']='LIVE' if item.get('native_identity') else 'ABSENT_WITHOUT_NORMAL_TERMINAL_PROOF'
 terminal=item['terminal'];exit_receipt=item.get('control/EXIT.json')
 if terminal and terminal['status'] in ('ENGINEERING_SMOKE_COMPLETE','R184_SCREEN_STOP') and terminal.get('sleeps',terminal.get('completed_sleeps'))==plan['max_sleeps']:
  item['observed_status']='TERMINAL_NORMAL' if not item.get('native_identity') and exit_receipt and exit_receipt['exit_code']==0 else 'TERMINAL_EXIT_PENDING'
 elif item.get('native_identity') and item['latest_complete']>=plan['max_sleeps']:item['observed_status']='SCREEN_BOUNDARY_COMPLETE_FINAL_STEP_OR_EXIT_PENDING'
 elif exit_receipt and exit_receipt['exit_code']!=0:item['observed_status']='NONZERO_EXIT_REQUIRES_DIAGNOSIS'
 if item['observed_status']=='TERMINAL_NORMAL':
  checkpoint_path=root/'life/checkpoints'/('sleep_%06d'%item['latest_complete'])/'COMMIT.json'
  checkpoint=read(checkpoint_path)
  item['terminal_checkpoint']=dict(commit=file_ref(checkpoint_path),metadata=small(checkpoint,('schema','created_unix','base_sha256','adapter_files','adapter_state_sha256','optimizer_steps','checkpoint_sha256')),files=[])
  for filename in checkpoint_path.parent.rglob('*'):
   if filename.is_file():item['terminal_checkpoint']['files'].append(file_ref(filename))
  optimizer_path=root/'life'/pathlib.Path(checkpoint['optimizer_rng_path']).relative_to(plan['root'])
  optimizer_ref=file_ref(optimizer_path)
  assert optimizer_ref['sha256']==checkpoint['checkpoint_sha256']['optimizer']==checkpoint['checkpoint_sha256']['rng']
  item['terminal_checkpoint']['optimizer_rng_path']=optimizer_ref
  adapter_path=root/'life'/pathlib.Path(checkpoint['adapter_path']).relative_to(plan['root'])
  adapter_files={path.name:file_ref(path)['sha256'] for path in adapter_path.iterdir() if path.is_file()}
  assert adapter_files==checkpoint['adapter_files'] and digest(adapter_files)==checkpoint['checkpoint_sha256']['adapter']
  item['terminal_checkpoint']['checkpoint_hashes_verified']=True
  item['retained_inbox']=[file_ref(path) for path in (root/'life/stream/inbox').rglob('*') if path.is_file()]
  item['retained_stream_manifest']=file_ref(root/'life/stream/JOURNAL.json')
  latest_state=max((item['last_committed_state'],item['last_complete_state']),key=lambda state:state['index'])
  assert latest_state['pending'] is None
  item['latest_resume_state']=latest_state
  item['post_complete_unslept_rows']=latest_state['rows']-latest_state['sleep_frontier']
  item['phase2_requires_exact_terminal_suffix_restore']=item['post_complete_unslept_rows']>0
  item['retained_root_owner']=dict(uid=(root/'life').stat().st_uid,gid=(root/'life').stat().st_gid,inode=(root/'life').stat().st_ino)
 item['observed_finished_unix']=time.time()
 report['arms'].append(item)
for pid,expected_ticks in ((2258434,'28070412'),(2245391,'28062062'),(183848,'40797822')):
 stat=(pathlib.Path('/proc')/str(pid)/'stat').read_text().rsplit(') ',1)[1].split()
 assert stat[19]==expected_ticks
 report['protected'].append(dict(pid=pid,start_ticks=stat[19],state=stat[0],unchanged=True))
print(json.dumps(report,sort_keys=True,indent=2))
'''


def main():
    ready = REPO / 'research_loop/workers/rohin201_c2_clones_20260917/r204_ready/READY.json'
    assert hashlib.sha256(ready.read_bytes()).hexdigest() == 'cc81c6218fbdb83f218e679250fdec5765e1d3829c1b88b76c166b275242cbb9'
    manifest = json.loads(ready.read_bytes())
    assert manifest['archive_sha256'] == 'b0f148c92172af9d1525fda79a97bebfb31337e312e26c0f6bc805b3c687f8fc'
    expected = dict(manifest['files'])
    expected.update(json.loads((OWN / 'R204_ADAPTER_FILES.json').read_bytes()))
    expected = {name: sha for name, sha in expected.items() if not name.startswith('tests/')}
    arms = json.loads((OWN / 'R203_SELECTED_ARMS.json').read_bytes())['arms']
    arms.append(dict(physical=7, name='CREATIVE-B', structured=True,
        remote_root='/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/creative_b1',
        task='Structured scene/dialogue workshop; attributed draft judgment, not an objective score.'))
    for arm in arms:
        parent = OWN / ('PARENT_B2' if arm['physical'] == 7 else 'PARENT_R203_SLOT' + str(arm['physical']))
        arm['feedback'] = []
        for directory in sorted(parent.glob('DRAFT_*')):
            path = directory / 'RESULT.json'
            if not path.exists():
                continue
            value = json.loads(path.read_bytes())
            if 'publication' in value:
                arm['feedback'].append(dict(draft=int(directory.name[6:]),
                    text=value['publication'].get('payload_text', value['response']['message']),
                    publication=value['publication']))
        arm['opening'] = json.loads((parent / 'OPENING_SOURCE.json').read_bytes())['text']
        arm['parent_observer_withdrawn'] = (parent / 'WITHDRAWN.json').exists()
    code = REMOTE_CHECK.replace('ARMS_JSON', repr(json.dumps(arms))).replace('EXPECTED_JSON', repr(json.dumps(expected)))
    result = subprocess.run(['bash', 'gpu/a100_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(code)],
        cwd=REPO, capture_output=True, text=True, timeout=55)
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    stamp = datetime.datetime.fromtimestamp(value['observed_unix'], datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = OWN / ('R204_LIVE_VERIFIED_' + stamp + '.json')
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)
    print(path.relative_to(REPO))
    for arm in value['arms']:
        print(json.dumps(dict(physical=arm['physical'], name=arm['name'],
            current_pid=arm.get('native_identity', {}).get('pid'),
            loaded_unix=(arm['r204_load'] or {}).get('loaded_unix'),
            request_unix=(arm['first_request_after_r204'] or {}).get('started_unix'),
            first_request_tokens=(arm['first_request_after_r204'] or {}).get('prompt_tokens'),
            current_request_max_tokens=arm['current_request_max_tokens'],
            all_current_requests_below_threshold=arm['all_current_requests_below_threshold'],
            current_compactions=len(arm['current_compactions']),
            latest_complete=arm['latest_complete'],observed_status=arm['observed_status'],
            parent_feedback_published=len(arm['parent_feedback']),
            parent_feedback_consumed=sum(feedback['first_render'] is not None for feedback in arm['parent_feedback']),
            parent_observer_withdrawn=arm['parent_observer_withdrawn'])))
    print('protected', json.dumps(value['protected']))


if __name__ == '__main__':
    main()
