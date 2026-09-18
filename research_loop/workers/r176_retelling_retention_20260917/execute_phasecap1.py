"""Once-only transport and launch of the two exact Main-authorized opaque cells."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import time

import preparation_io as common


WORKER = Path(__file__).resolve().parent
GO_SHA = 'f4816d4aadde1732d828aba2d01f7ae1c9aedd03a9d9cb2ca3411de7ed3460ca'
REVIEW_SHA = '7cdab75721cb7c472ce756333d345bc78cc0849feddc873fea97e332d755d629'
REMOTE = '''import hashlib,json,os,pathlib,subprocess,sys,time
os.umask(0o077)
base=pathlib.Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1')
root=base/'main_phasecap1_launch1'
root.mkdir(mode=0o700,exist_ok=False)
request=json.loads(sys.stdin.buffer.read(1048576))
used=request['transport_bytes'];sequence=0
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,value):
 raw=value if isinstance(value,bytes) else json.dumps(value,sort_keys=True,separators=(',',':')).encode()
 path.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
 with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 return {'path':str(path),'sha256':sha(raw)}
def read(path,expected=None):
 global used,sequence
 assert path==path.resolve() and path.is_relative_to(base)
 with path.open('rb',buffering=0) as stream:
  size=os.fstat(stream.fileno()).st_size
  assert size<=131072 and used+size<=request['metadata_allowance']['document']['bytes']
  write(root/'READS'/('%06d.json'%sequence),{'path':str(path),'bytes':size,
   'authority':request['metadata_allowance']['reference'],'status':'CHARGED_BEFORE_READ_NO_REFUND'})
  used+=size;sequence+=1
  raw=stream.read(size)
  assert len(raw)==size and (expected is None or sha(raw)==expected)
 return raw
write(root/'REQUEST.json',request)
documents={}
for name in ('review','go'):
 item=request[name];raw=bytes.fromhex(item['bytes_hex'])
 assert sha(raw)==item['sha256']
 target=base/item['remote_name']
 assert not target.exists()
 write(target,raw)
 verified=read(target,item['sha256'])
 documents[name]=json.loads(verified)
go=documents['go'];review=documents['review']
assert go['status']=='MAIN_R176_EXECUTION_GO' and go['no_reset'] is True
assert go['only_these_executions'] is True and go['this_tranche_calls']==6 and len(go['executions'])==2
assert review['status']=='APPROVE' and review['independent'] is True and review['remaining_review_issues']==[]
assert review['scope']['calls']==6 and review['scope']['condition_processes']==2 and not review['scope']['other_cells_approved']
for field in ('executions','source','runner_sha256','cpu_gate','runner_cpu_gate'):assert go[field]==review[field]
assert go['absolute_end_unix']==1789673400 and time.time()+915<go['absolute_end_unix']
assert go['independent_review']=={'path':str(base/'MAIN_PHASECAP1_REVIEW.json'),'sha256':request['review']['sha256']}
runner=base/'runner_candidate1/source/r176_runner.py'
read(runner,go['runner_sha256'])
verified=write(root/'AUTHORIZATION_TRANSFER_VERIFIED.json',{'go_sha256':request['go']['sha256'],
 'review_sha256':request['review']['sha256'],'verified_unix':time.time(),'both_exact_remote_bytes_verified':True,
 'only_fixed_C2_sleep33_pair':True,'this_tranche_calls':6})
started=[]
for execution in go['executions']:
 config=json.loads(read(pathlib.Path(execution['path']),execution['sha256']))
 assert config['life_id']=='C2' and config['sleep']==33 and config['condition'] in ('LORA_ON','LORA_OFF')
 assert config['python']=='/localhome/local-rohing/v2/venv/bin/python'
 key='C2_sleep000033_'+config['condition']
 assert not (base/'attempts'/key).exists() and not (base/'ledger'/(key+'.RESERVED.json')).exists()
 cell=root/execution['sha256'];cell.mkdir(mode=0o700,exist_ok=False)
 command=[config['python'],'-B',str(runner),'start','--config',execution['path'],
  '--go',str(base/'MAIN_EXECUTION_GO_PHASECAP1.json')]
 write(cell/'LAUNCH_INTENT.json',{'execution':execution,'go_sha256':request['go']['sha256'],
  'command':command,'recorded_unix':time.time(),'once_only':True,'max_condition_calls':3})
 environment={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'HOME':os.environ['HOME'],
  'PYTHONPATH':str(base/'receiving_source1/source'),'CUDA_VISIBLE_DEVICES':'',
  'PYTHONDONTWRITEBYTECODE':'1','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1',
  'TOKENIZERS_PARALLELISM':'false','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
 with (cell/'stdout.private.txt').open('xb') as output,(cell/'stderr.private.txt').open('xb') as errors:
  process=subprocess.Popen(command,cwd=base/'receiving_source1/source',env=environment,
   stdin=subprocess.DEVNULL,stdout=output,stderr=errors,start_new_session=True)
 entry={'execution':execution,'controller_pid':process.pid,'launched_unix':time.time(),
  'status':'EXACT_RUNNER_START_INVOKED_ADMISSION_PENDING','calls_completed_not_yet_observed':True}
 write(cell/'CONTROLLER_STARTED.json',entry);started.append(entry)
result={'status':'TWO_EXACT_RUNNER_STARTS_INVOKED','observed_unix':time.time(),'controllers_started':len(started),
 'go_sha256':request['go']['sha256'],'review_sha256':request['review']['sha256'],
 'both_exact_remote_bytes_verified':True,'controllers':started,'tranche_max_calls':6,
 'admission_counts_not_yet_observed':True,'completed_calls_not_yet_observed':True,
 'launch_metadata_charge_bytes':used,'provider_calls':0,'other_cells_started':0,
 'authorization_transfer_receipt':verified,'no_retries':True,'absolute_end_unix':go['absolute_end_unix']}
write(root/'PUBLIC_METADATA.json',result)
print(json.dumps(result,sort_keys=True))
'''


def main():
    os.umask(0o077)
    common.validate_controls(WORKER)
    go_raw = (WORKER / 'MAIN_EXECUTION_GO_PHASECAP1.json').read_bytes()
    review_raw = (WORKER / 'REVIEW_R179_PHASE_CAP1_APPROVAL.json').read_bytes()
    common.require(common.sha(go_raw) == GO_SHA and common.sha(review_raw) == REVIEW_SHA, 'exact_Main_GO_and_Nash_review')
    root = WORKER / 'execution_phasecap1'
    root.mkdir(mode=0o700, exist_ok=False)
    ledger = common.Ledger(WORKER / 'preparation1/global_ledger')
    metadata = ledger.reserve('C2_phasecap1_GO_stage_launch1_metadata', 'C2', 'metadata', common.MIB, discovery=True)
    storage = ledger.reserve('C2_phasecap1_GO_stage_launch1_storage', '_campaign', 'storage', 2 * common.MIB)
    request = dict(go=dict(bytes_hex=go_raw.hex(), sha256=GO_SHA, remote_name='MAIN_EXECUTION_GO_PHASECAP1.json'),
        review=dict(bytes_hex=review_raw.hex(), sha256=REVIEW_SHA, remote_name='MAIN_PHASECAP1_REVIEW.json'),
        metadata_allowance=metadata, storage_allowance=storage, transport_bytes=0, recorded_unix=time.time())
    for iteration in range(4):
        amount = len(common.canonical(request)) + len(REMOTE.encode())
        if amount == request['transport_bytes']:
            break
        request['transport_bytes'] = amount
    common.require(request['transport_bytes'] == len(common.canonical(request)) + len(REMOTE.encode()), 'exact_finite_transport_charge')
    common.write(root / 'REQUEST.json', request)
    common.write(root / 'TRANSPORT_PRECHARGE.json', dict(bytes=request['transport_bytes'], authority=metadata['reference'],
        status='CHARGED_BEFORE_TRANSMISSION_NO_REFUND'))
    try:
        result = subprocess.run(['bash', str(WORKER.parents[2] / 'gpu/ovx_ssh.sh'),
            'python3 -c ' + shlex.quote(REMOTE)], input=common.canonical(request), capture_output=True, timeout=90)
        receipt = json.loads(result.stdout) if result.returncode == 0 else dict(
            status='LAUNCH_OR_TRANSFER_REFUSED_PRESERVED_NO_RETRY', returncode=result.returncode,
            stderr_bytes=len(result.stderr), stderr_sha256=common.sha(result.stderr),
            remote_start_state_requires_readonly_observation=True, no_retries=True)
    except subprocess.TimeoutExpired:
        receipt = dict(status='LAUNCH_ACK_TIMEOUT_PRESERVED_NO_RETRY', remote_start_state_requires_readonly_observation=True)
    common.write(root / 'PUBLIC_METADATA.json', receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
