"""Metadata-only immutable config repair after Nash's actual-cap REWORK."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
WORKER = HERE.parents[1]
REPO = WORKER.parents[2]
sys.path.insert(0,str(WORKER))
import preparation_io as common


REMOTE = '''import hashlib,json,os,pathlib,sys,time
os.umask(0o077)
base=pathlib.Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1')
root=base/'runner_candidate2_metadata_repair1'
root.mkdir(mode=0o700,exist_ok=False)
request=json.loads(sys.stdin.buffer.read(1024*1024))
used=0
sequence=0
def canonical(document):return json.dumps(document,sort_keys=True,separators=(',',':')).encode()
def write(path,document):
 path.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
 raw=canonical(document)
 with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()}
def read(reference):
 global used,sequence
 path=pathlib.Path(reference['path'])
 assert path==path.resolve() and path.is_relative_to(base/'runner_candidate1')
 with path.open('rb',buffering=0) as stream:
  size=os.fstat(stream.fileno()).st_size
  assert size<=65536 and used+size<=request['metadata_read_allowance']['document']['bytes']
  write(root/'READS'/('%06d.json'%sequence),{'path':str(path),'bytes':size,'charged_before_read':True,
   'allowance':request['metadata_read_allowance']})
  used+=size;sequence+=1
  raw=stream.read(size)
  assert len(raw)==size and hashlib.sha256(raw).hexdigest()==reference['sha256']
 return json.loads(raw)
write(root/'REQUEST.json',request)
public=read(request['original_public_receipt'])
assert public['runner_sha256']=='4ff1c97b374930b2b6e4c96d2f8d24fbedcdccfaae8c07471edd52720d7a6952'
assert public['future_calls_if_both_admitted']==6 and public['model_calls']==public['provider_calls']==0
assert public['execution_authorized'] is False and len(public['executions'])==2
executions=[]
for previous in public['executions']:
 original=read(previous)
 assert original['life_id']=='C2' and original['sleep']==33
 condition=original['condition']
 assert condition in request['new_metadata_allowances']
 changed=json.loads(json.dumps(original))
 for phase,cap in [('preflight',32*1024*1024),('native',48*1024*1024)]:
  assert original['allowances'][phase]['metadata']['document']['bytes']==24*1024*1024
  entry=request['new_metadata_allowances'][condition][phase]
  document=entry['document']
  assert hashlib.sha256(canonical(document)).hexdigest()==entry['reference']['sha256']
  assert document['status']=='PRECHARGED_NO_REFUND' and document['life_id']=='C2' and document['kind']=='metadata'
  assert document['scope_sha256']==request['scope_sha256'] and document['bytes']==cap
  changed['allowances'][phase]['metadata']=entry
 check=json.loads(json.dumps(changed))
 for phase in ('preflight','native'):check['allowances'][phase]['metadata']=original['allowances'][phase]['metadata']
 assert check==original
 name=hashlib.sha256(('metadata_repair1:'+previous['sha256']).encode()).hexdigest()+'.private.json'
 executions.append(write(root/'controls'/name,changed))
result=dict(public,status='C2_SLEEP33_METADATA_REPAIR_CONFIGS_READY_FOR_ACTUAL_REVIEW',
 executions=executions,superseded_execution_refs=public['executions'],
 superseded_public_receipt=request['original_public_receipt'],observed_unix=time.time(),
 changed_fields_only=['allowances.preflight.metadata','allowances.native.metadata'],
 new_phase_metadata_bytes={'preflight':32*1024*1024,'native':48*1024*1024},
 new_reservations_bytes=160*1024*1024,old_reservations_preserved=True,runner_bytes_changed=False,
 source_capture_or_adapter_reads=0,metadata_read_bytes=used,
 actual_validator_recheck_pending=True,execution_authorized=False,independent_integration_review_pending=True)
write(root/'PUBLIC_METADATA.json',result)
print(json.dumps(result,sort_keys=True))
'''


def main():
    os.umask(0o077)
    common.validate_controls(WORKER)
    once = HERE/'attempt1'
    once.mkdir(mode=0o700,exist_ok=False)
    review_path = WORKER/'REVIEW_R179_PUBLIC_BINDINGS.json'
    review = json.loads(review_path.read_bytes())
    common.require(review['status']=='REWORK' and
        review['first_blocker']=='FIXED_METADATA_PHASE_CAP_BELOW_MANDATORY_PRODUCTION_READS','exact_Nash_rework')
    public_path = WORKER/'preparation1/narrow_runner1/PUBLIC_METADATA.json'
    public = json.loads(public_path.read_bytes())
    ledger = common.Ledger(WORKER/'preparation1/global_ledger')
    new = {}
    for condition,prefix in (('LORA_ON','ON'),('LORA_OFF','OFF')):
        new[condition] = {}
        for phase,amount in (('preflight',32),('native',48)):
            new[condition][phase] = ledger.reserve(f'C2_sleep33_{prefix}_{phase}_metadata_repair1','C2',
                'metadata',amount*common.MIB)
    reads = ledger.reserve('C2_metadata_repair1_config_read_stage','C2','metadata',common.MIB,discovery=True)
    storage = ledger.reserve('C2_metadata_repair1_control_storage','_campaign','storage',common.MIB)
    request = dict(scope_sha256=common.SCOPE_SHA,
        original_public_receipt=dict(path=str(common.REMOTE/'runner_candidate1/PUBLIC_METADATA.json'),
            sha256=common.sha(public_path.read_bytes())),
        Nash_rework=dict(path=str(review_path),sha256=common.sha(review_path.read_bytes())),
        new_metadata_allowances=new,metadata_read_allowance=reads,storage_allowance=storage,
        model_calls=0,provider_calls=0,execution_authorized=False,recorded_unix=time.time())
    common.write(once/'REQUEST.json',request)
    payload = common.canonical(request)
    common.require(len(payload)<common.MIB,'bounded_config_only_payload')
    result = subprocess.run(['bash',str(REPO/'gpu/ovx_ssh.sh'),'python3 -c '+shlex.quote(REMOTE)],
        input=payload,capture_output=True,timeout=90)
    receipt = json.loads(result.stdout) if result.returncode==0 else dict(status='METADATA_REPAIR_FAILED_PRESERVED_NO_RETRY',
        returncode=result.returncode,stderr_bytes=len(result.stderr),stderr_sha256=common.sha(result.stderr),
        observed_unix=time.time(),model_calls=0,provider_calls=0)
    common.write(once/'PUBLIC_METADATA.json',receipt)
    print(json.dumps(receipt,sort_keys=True))


if __name__=='__main__':
    main()
