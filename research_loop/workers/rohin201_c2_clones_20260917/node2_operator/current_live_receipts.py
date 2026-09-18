"""Read current node2 ownership and rendered feedback without printing histories."""

import datetime
import json
from pathlib import Path
import shlex
import subprocess


HERE = Path(__file__).resolve().parent
REMOTE = r'''
import datetime,hashlib,json,os,pathlib,subprocess
base=pathlib.Path('/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1')
def read(path):return json.loads(path.read_bytes())
def metadata(path):
 with path.open('rb') as stream:stream.seek(max(0,path.stat().st_size-4096));tail=stream.read()
 return json.loads(b'{'+tail[tail.rfind(b',"index":')+1:])
def reference(path,record):
 return dict(index=record['index'],kind=record['kind'],sha256=record['sha256'],file_mtime_utc=datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat())
result=dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),arms={})
for label,query in [('gpu','index,uuid,memory.used,utilization.gpu'),('compute-apps','pid,gpu_uuid,used_memory')]:
 result['nvml_'+label]=subprocess.check_output(['nvidia-smi','--query-'+label+'='+query,'--format=csv,noheader'],text=True,timeout=12).strip().splitlines()
for arm,gpu in [('math_d1',1),('repo_c1',3),('creative_d1',4),('math_transfer_c1',6),('birth1',2)]:
 root=base/arm if arm!='birth1' else pathlib.Path('/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1')
 attempt=root/'r204_boundary_20260918t0356z'
 control=root/('control_r204_casefix' if gpu in [4,6] else 'control')
 if (attempt/'DISPATCHED.json').exists():control=attempt/'control'
 phase2=root/'r206_phase2_withdrawn_20260918'
 if (root/'r209_dispatch_recovery_20260918/DISPATCHED.json').exists():phase2=root/'r209_dispatch_recovery_20260918'
 if (phase2/'DISPATCHED.json').exists():control=phase2/'control'
 plan=read(control/'PLAN.json');source=pathlib.Path(plan['source_root']);floor=5103 if arm=='birth1' else 5846
 row=dict(gpu=gpu,current_control=str(control),source_root=str(source),record_floor_exclusive=floor,
  loop='R184' if plan.get('think_act_learn',{}).get('schema')=='R184_THINK_ACT_LEARN_V1' else 'LEGACY_NO_R184_PLAN',
  driver=plan.get('think_act_learn'),boundary_attempt={},exits={},loaded=[],stages=[],requests=[],complete=[],rendered_feedback=[])
 row['phase2']={name:read(phase2/name) for name in ['WAITER_STARTED.json','DISPATCHED.json','PHASE2_FAILED.json','WAIT_EXPIRED.json'] if (phase2/name).exists()}
 for name in ['ARMED.json','DISPATCHED.json','HANDOFF_FAILED.json','RETIRED_EXACT.json']:
  if (attempt/name).exists():row['boundary_attempt'][name]=read(attempt/name)
 for name in ['EXIT.json','FAILED.json','OUTER_EXIT.json','OUTER_FAILED.json']:
  if (control/name).exists():row['exits'][name]=read(control/name)
 row['source_sha256']={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ['gpu/orch_r125_continual_native.py','organism_v6/orch_r125_plain_context.py']}
 row['threshold']=min(3*plan['context_limit']//4,plan['context_limit']-plan['segment_tokens'])
 records=root/('life/stream/records' if arm=='birth1' else 'raw/stream/records');inboxes=[]
 for path in sorted(records.glob('[0-9]'*20+'.json')):
  if int(path.stem)<=floor:continue
  meta=metadata(path)
  if meta['kind'] not in ['LOADED','REQUEST','R184_STAGE','SLEEP_COMPLETE','INBOX']:continue
  record=read(path);doc=record['document'];entry=reference(path,record)
  if record['kind']=='LOADED':
   entry.update({key:doc.get(key) for key in ['pid','loaded_unix','optimizer_steps']});row['loaded'].append(entry)
  elif record['kind']=='SLEEP_COMPLETE':entry['cycle']=doc['cycle'];row['complete'].append(entry)
  elif record['kind']=='R184_STAGE':entry.update(stage=doc.get('stage'),segment=doc.get('segment'));row['stages'].append(entry)
  elif record['kind']=='INBOX':
   message=doc['message']
   if message.get('speaker') in ['Astra','Tool']:inboxes.append((entry,message))
  elif record['kind']=='REQUEST':
   entry.update(prompt_tokens=doc.get('prompt_tokens'),all_history_tokens_masked=doc.get('render_receipt',{}).get('all_history_tokens_masked'));row['requests'].append(entry)
   for inbox,message in inboxes:
    if any(item['inbox']['index']==inbox['index'] for item in row['rendered_feedback']):continue
    text=message.get('text','')
    if not text or not any(text in item.get('content','') for item in doc['messages']):continue
    feedback=dict(inbox=inbox,request=entry,id=message['id'],speaker=message['speaker'],text_sha256=hashlib.sha256(text.encode()).hexdigest(),exact_text_rendered=True)
    if message['speaker']=='Tool':
     try:
      tool=json.loads(text)
     except json.JSONDecodeError:
      feedback['text_prefix']=text[:380]
     else:
      feedback['result_summary']={key:tool.get(key) for key in ['schema','status','action','sequence','source_sha256','receipt_sha256','request']}
      feedback['result_keys']=sorted(tool)
      feedback['origin']=tool.get('origin')
      feedback['text_prefix']=text[:380]
    row['rendered_feedback'].append(feedback)
 last_loaded=row['loaded'][-1] if row['loaded'] else None
 pid=last_loaded['pid'] if last_loaded else None;process=pathlib.Path('/proc')/str(pid)
 try:
  fields=(process/'stat').read_text().rsplit(')',1)[1].split();arguments=(process/'cmdline').read_bytes().decode().split('\0')
  row['native']=dict(pid=pid,start_ticks=fields[19],state=fields[0],alive=fields[0] not in ['Z','X'],cwd=os.readlink(process/'cwd'),guard_matches=str(control/'GUARD.json') in arguments)
 except (FileNotFoundError,ProcessLookupError):row['native']=dict(pid=pid,alive=False)
 row['status']='LIVE_VERIFIED_NATIVE' if row['native'].get('alive') and row['native'].get('guard_matches') else 'NO_CURRENT_NATIVE'
 if not row['native']['alive'] and row['complete'] and row['complete'][-1]['cycle']==57:row['status']='SCREEN57_COMPLETED_EXITED_NOT_RESTARTED'
 if (phase2/'DISPATCHED.json').exists() and row['status']!='LIVE_VERIFIED_NATIVE':row['status']='PHASE2_DISPATCHED_AWAITING_CURRENT_LOADED'
 if row['status']!='LIVE_VERIFIED_NATIVE' and any(name in row['exits'] for name in ['FAILED.json','OUTER_FAILED.json']):row['status']='FAILED_DISPATCH_NO_CURRENT_NATIVE'
 parent=root/'r209_parent_reattachment_20260918'
 row['parent_reattachment']=dict(publications=len(list(parent.glob('PUBLICATION_*.json'))),rendered=len(list(parent.glob('RENDERED_*.json'))),phase='R209_PARENT_REATTACHED' if list(parent.glob('PUBLICATION_*.json')) else 'NO_R209_PARENT_PUBLICATION',V_historical_unresolved_preserved=True)
 active_requests=[entry for entry in row['requests'] if row['status']=='LIVE_VERIFIED_NATIVE' and last_loaded and entry['index']>last_loaded['index']]
 row['current_load_budget']=dict(request_count=len(active_requests),at_or_above_threshold=sum(entry.get('prompt_tokens',0)>=row['threshold'] for entry in active_requests),all_recorded_history_masked=all(entry['all_history_tokens_masked'] is True for entry in active_requests))
 row['first_think']=next((entry for entry in row['stages'] if entry['stage']=='THINK'),None)
 row['first_act']=next((entry for entry in row['stages'] if entry['stage']=='ACT'),None)
 row['stage_count']=len(row['stages']);row['stages']=row['stages'][-3:]
 row['request_count']=len(row['requests']);row['requests']=row['requests'][:1]+row['requests'][-2:]
 row['complete']=row['complete'][-2:]
 result['arms'][arm]=row
result['live_C2_clone_count']=sum(row['status']=='LIVE_VERIFIED_NATIVE' for arm,row in result['arms'].items() if arm!='birth1')
print(json.dumps(result))
'''


def save(path, document):
    content = json.dumps(document, indent=2, sort_keys=True) + '\n'
    if path.exists():
        patch = '*** Begin Patch\n*** Update File: ' + str(path) + '\n@@\n'
        patch += ''.join('-' + line + '\n' for line in path.read_text().splitlines())
    else:
        patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    patch += ''.join('+' + line + '\n' for line in content.splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, capture_output=True, check=True)


def main():
    run = subprocess.run(['bash', 'gpu/ovx_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(REMOTE)],
        capture_output=True, text=True, timeout=50, check=True)
    document = json.loads(run.stdout)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    receipt = HERE / 'receipts' / ('CURRENT_LIVE_' + stamp + '.json')
    save(receipt, document)
    status = dict(schema='R206_NODE2_CURRENT_HEALTH_V1', observed_utc=document['observed_utc'],
        live_clone_count=document['live_C2_clone_count'], completed_screen_count=sum(bool(row['complete'] and row['complete'][-1]['cycle']>=57) for arm,row in document['arms'].items() if arm!='birth1'),
        receipt=str(receipt), protected_node2_gpus=[0, 2, 5, 7], original_C2_actions=0,
        peer_exchange_active=False, CJK_exclusion_deployed=False, CJK_shared_filter_owner='Main/Jason notified; frozen repair needed for saved-boundary rollout', arms=[])
    for arm, row in document['arms'].items():
        compact = {key: row[key] for key in ['gpu', 'status', 'loop', 'native', 'current_load_budget', 'parent_reattachment']}
        compact.update(arm=arm, latest_loaded=row['loaded'][-1:] or None, last_complete=row['complete'][-1:] or None,
            continuation_policy=(row['driver'] or {}).get('think_continuation_policy'), rendered_feedback_count=len(row['rendered_feedback']))
        status['arms'].append(compact)
        print(json.dumps(compact))
    save(HERE / 'STATUS.json', status)
    print('SAVED', receipt)


if __name__ == '__main__':
    main()
