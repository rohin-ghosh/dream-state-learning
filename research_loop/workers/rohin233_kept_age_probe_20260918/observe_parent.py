"""Report source-bound parent rendering, not only endpoint setup."""

import json
from pathlib import Path
import subprocess


CODE = '''import hashlib,json,pathlib,time
root=pathlib.Path('/localhome/local-rohing/orch_r233_base_parent_20260918')
player=pathlib.Path('/localhome/local-rohing/orch_r224_continuous_base_20260918/player')
def sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def proc(pid):
 path=pathlib.Path('/proc')/str(pid)/'stat'
 return path.exists() and path.read_text().rsplit(')',1)[1].split()[0]!='Z'
state=json.loads((player/'private/state.json').read_bytes())
active=json.loads((root/'ACTIVE.json').read_bytes())
receipts=[json.loads(path.read_bytes()) for path in (root/'receipts').glob('*.json')]
guides={row['guidance_sha256']:row for row in receipts}
rendered=[]
for entry in state.get('generations',[]):
 if entry['finished_unix']<active['unix']:continue
 path=player/'private/generations'/(entry['request_id']+'.json')
 value=json.loads(path.read_bytes());request=value['request'];generated=value['generated']
 assert sha(request)==entry['request_id'] and generated['messages']==request['messages']
 messages=json.dumps(request['messages'],ensure_ascii=False)
 matched=[key for key,row in guides.items() if row['guidance'] in messages]
 if matched:
  rendered.append(dict(request_id=entry['request_id'],request_sha256=sha(request),response_sha256=sha(generated),
   generation_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),stage=request['stage'],
   opportunity=request['opportunity'],finished_unix=value['finished_unix'],guidance_sha256=matched,
   actual_generated_tokens=len(generated['token_ids']),actual_prompt_tokens=generated['prompt_tokens']))
rendered.sort(key=lambda row:row['finished_unix'])
result=dict(schema='R233_PARENT_RENDER_EVIDENCE_V1',unix=time.time(),epoch='R233_PARENT_v1',
 bridge_pid=active['pid'],bridge_live=proc(active['pid']),player_pid=162813,player_live=proc(162813),
 scorer_pid=162806,scorer_live=proc(162806),source_process_signals=[],guidance_deliveries=len(receipts),
 bridge_errors=len(list((root/'errors').glob('*.json'))),
 first_actual_parented_generation=rendered[0] if rendered else None,rendered_generations=rendered,
 treatment_boundary='first request_id with actual completed generation containing exact guidance; finished_unix is completion not start',
 completed_opportunities=state['completed_opportunities'],cumulative_child_tokens=state['total_generated_tokens'],
 parent_tokens=None,parent_tokens_status='separate_unmeasured_not_zero',model_updates=0,
 no_matched_adapter_scaffold_claim=True,parent_free_age_probes_unchanged=True)
print(json.dumps(result))
'''


def main():
    result = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', 'python3 -B -'], input=CODE,
        text=True, capture_output=True, timeout=40)
    if result.returncode:
        raise RuntimeError(result.stderr[-1000:])
    receipt = json.loads(result.stdout)
    root = Path(__file__).resolve().parent
    (root / 'PARENT_RENDER_LATEST.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'rendered_generations'}))


if __name__ == '__main__':
    main()
