"""Bounded current processes, per-request budget, and math source provenance."""

import datetime
import json
from pathlib import Path
import shlex
import subprocess


REMOTE = r'''
import ast,datetime,hashlib,importlib.util,json,os,pathlib,subprocess
base=pathlib.Path('/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1')
def read(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def metadata(path):
 with path.open('rb') as stream:stream.seek(max(0,path.stat().st_size-4096));tail=stream.read()
 return json.loads(b'{'+tail[tail.rfind(b',"index":')+1:])
result=dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),arms={})
ready=read(base/'r204_ready/READY.json')
for arm,pid,gpu in [('math_d1',2128807,1),('repo_c1',2170067,3),('creative_d1',2204408,4),('math_transfer_c1',2204538,6)]:
 root=base/arm;current=root/('control_r204_casefix' if gpu in [4,6] else 'control')
 updated=root/'r204_boundary_20260918t0353z/control'
 if (updated/'LAUNCH.json').exists():current=updated
 guard=read(current/'GUARD.json');plan=read(current/'PLAN.json');source=pathlib.Path(plan['source_root'])
 paths=sorted((root/'raw/stream/records').glob('[0-9]'*20+'.json'))
 entries=[];responses=[];inboxes=[];latest_request=None;stage_requests=[];loaded=[];complete=[]
 for path in paths:
  if int(path.stem)<5847:continue
  meta=metadata(path);kind=meta['kind']
  if kind not in ['LOADED','REQUEST','RESPONSE','R184_STAGE','SLEEP_COMPLETE','TERMINAL','INBOX']:continue
  record=read(path);doc=record['document'];entry=dict(index=record['index'],kind=kind,sha256=record['sha256'])
  if kind=='LOADED':entry.update({key:doc.get(key) for key in ['loaded_unix','pid','optimizer_steps','adapter_sha256']});loaded.append(entry)
  elif kind=='REQUEST':
   entry.update(prompt_tokens=doc.get('prompt_tokens'),render_receipt=doc.get('render_receipt'),segment=doc.get('segment'),started_unix=doc.get('started_unix'))
   entries.append(entry);latest_request=entry
  elif kind=='R184_STAGE':
   if latest_request:stage_requests.append(dict(**latest_request,stage=doc.get('stage')))
  elif kind=='RESPONSE':responses.append(record)
  elif kind=='INBOX':inboxes.append(dict(index=record['index'],speaker=doc['message'].get('speaker'),id=doc['message']['id']))
  elif kind=='SLEEP_COMPLETE':complete.append(dict(index=record['index'],cycle=doc['cycle'],mtime_utc=datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat()))
 if loaded:pid=loaded[-1]['pid']
 process=pathlib.Path('/proc')/str(pid)
 try:
  fields=(process/'stat').read_text().rsplit(')',1)[1].split()
  identity=dict(pid=pid,start_ticks=fields[19],state=fields[0],alive=fields[0] not in ['Z','X'],cwd=os.readlink(process/'cwd'),guard_in_argv=str(current/'GUARD.json') in (process/'cmdline').read_bytes().decode().split('\0'))
 except (FileNotFoundError,ProcessLookupError):identity=dict(pid=pid,alive=False)
 threshold=min(3*plan['context_limit']//4,plan['context_limit']-plan['segment_tokens'])
 row=dict(gpu=gpu,native=identity,current_control=str(current),loaded=loaded,complete_cycles=complete,record_floor=5847,inherited_records_excluded='0..5846',policy=plan.get('think_act_learn',{}).get('think_continuation_policy'),threshold=threshold,request_count=len(entries),first_request=entries[0] if entries else None,last_request=entries[-1] if entries else None,requests_at_or_above_threshold=[entry for entry in entries if entry.get('prompt_tokens',0)>=threshold],stage_requests=stage_requests,all_recorded_history_masked=all(entry.get('render_receipt',{}).get('all_history_tokens_masked') is True for entry in entries),source_pins_match={name:sha(source/name)==ready['files'][name] for name in ['gpu/orch_r125_continual_native.py','organism_v6/orch_r125_continual_stream.py','organism_v6/orch_r125_plain_context.py']},current_exits={name:read(current/name) for name in ['EXIT.json','FAILED.json','OUTER_EXIT.json','OUTER_FAILED.json'] if (current/name).exists()},new_parent_inboxes=[entry for entry in inboxes if entry['speaker']=='Astra'])
 if gpu in [1,6]:
  spec=importlib.util.spec_from_file_location('actual_code_blocks',source/'gpu/orch_r153_code_blocks.py');blocks=importlib.util.module_from_spec(spec);spec.loader.exec_module(blocks)
  attempts=[]
  for record in responses:
   raw=record['document']['response'].get('raw')
   if not isinstance(raw,str):continue
   report=blocks.extract(raw,policy=plan['think_act_learn']['code_policy'])
   if not report['attempted']:continue
   attempt=dict(response_index=record['index'],response_sha256=record['sha256'],reason=report['reason'],raw_source=report.get('raw_source'),normalized_source=report.get('source'),raw_source_sha256=report.get('raw_source_sha256'),normalized_source_sha256=report.get('source_sha256'),transformations=report.get('transformations'),executed_result=[])
   if report.get('source') is not None:
    try:ast.parse(report['source']);attempt['normalized_python_syntax']='PARSES_NOT_EXECUTION_PROOF'
    except SyntaxError as error:attempt['syntax_fault']=dict(type='SyntaxError',message=error.msg,lineno=error.lineno,offset=error.offset,text=error.text)
   attempts.append(attempt)
  by_index={entry['response_index']:entry for entry in attempts}
  for intent_path in (root/'raw/community_cpu').glob('*/INTENT.json'):
   intent=read(intent_path);request=intent['request'];origin=request.get('origin',{});index=origin.get('record_index')
   if index not in by_index:continue
   attempt=by_index[index];attempt['actual_request_id']=request.get('request_id');attempt['actual_request_source_sha256']=request.get('source_sha256');attempt['request_source_matches_normalized']=request.get('source')==attempt['normalized_source']
   result_path=root/'raw/community_cpu/spool'/request['request_id']/'RESULT.json'
   if result_path.exists():
    outcome=read(result_path)
    attempt['executed_result']=dict(path=str(result_path),sha256=sha(result_path),keys=list(outcome),outcome={key:value for key,value in outcome.items() if key in ['status','returncode','stdout','stderr','error','execution','result']})
  row['math_attempt_count']=len(attempts);row['math_attempts']=attempts[-4:]
 result['arms'][arm]=row
for label,query in [('gpu','index,uuid,memory.used,utilization.gpu'),('compute-apps','pid,gpu_uuid,used_memory')]:
 result['nvml_'+label]=subprocess.check_output(['nvidia-smi','--query-'+label+'='+query,'--format=csv,noheader'],text=True,timeout=12).strip().splitlines()
print(json.dumps(result))
'''


def main():
    result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', '/usr/bin/python3 -B -c ' + shlex.quote(REMOTE)],
        capture_output=True, text=True, timeout=45, check=True)
    receipt = json.loads(result.stdout)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = Path(__file__).resolve().parent / 'receipts' / ('CURRENT_R204_' + stamp + '.json')
    patch = '*** Begin Patch\n*** Add File: ' + str(path) + '\n'
    patch += ''.join('+' + line + '\n' for line in json.dumps(receipt, indent=2).splitlines()) + '*** End Patch\n'
    subprocess.run(['apply_patch'], input=patch, text=True, capture_output=True, check=True)
    print('SAVED', path)
    for arm, row in receipt['arms'].items():
        print(json.dumps(dict(arm=arm, native=row['native'], policy=row['policy'],
            requests=row['request_count'], over_threshold=len(row['requests_at_or_above_threshold']),
            completed=row['complete_cycles'][-1:] if row['complete_cycles'] else [],
            exit=row['current_exits'], math_attempts=row.get('math_attempt_count'))))


if __name__ == '__main__':
    main()
