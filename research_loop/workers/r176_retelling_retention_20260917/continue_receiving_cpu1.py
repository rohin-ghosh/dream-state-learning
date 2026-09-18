"""Read existing transport status, then first CPU phase; never replay transfer."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import time

import preparation_io as common


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
READ = '''import hashlib,json,os,pathlib,sys,time
root=pathlib.Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1')
operation=root/'receiving_status_audit1'
operation.mkdir(mode=0o700,exist_ok=False)
request=json.loads(sys.argv[1])
with (operation/'ALLOWANCE.json').open('x') as stream:json.dump(request,stream,sort_keys=True)
path=root/'receiving_transfers/C2_000033/PUBLIC_METADATA.json'
with path.open('rb',buffering=0) as stream:
 size=os.fstat(stream.fileno()).st_size
 assert size<=65536
 with (operation/'CHARGED_BEFORE_READ.json').open('x') as log:
  json.dump({'path':str(path),'bytes':size,'allowance':request},log,sort_keys=True);log.flush();os.fsync(log.fileno())
 raw=stream.read(size)
 assert len(raw)==size
document=json.loads(raw)
assert document['status']=='FIXED_C2_SLEEP33_RECEIVING_COPY_VERIFIED'
result={'status':'EXISTING_RECEIVER_PROOF_OBSERVED','receipt':document,'receipt_sha256':hashlib.sha256(raw).hexdigest(),
 'metadata_bytes_read':size,'observed_unix':time.time(),'model_calls':0,'provider_calls':0,
 'CPU_once_already_exists':(root/'receiving_cpu1/ONCE.json').exists()}
with (operation/'PUBLIC_METADATA.json').open('x') as stream:json.dump(result,stream,sort_keys=True)
print(json.dumps(result,sort_keys=True))
'''


def main():
    os.umask(0o077)
    common.validate_controls(HERE)
    operation = HERE/'preparation1/receiving_cpu_continuation1'
    operation.mkdir(parents=True,mode=0o700,exist_ok=False)
    ledger = common.Ledger(HERE/'preparation1/global_ledger')
    allowance = ledger.reserve('R176_existing_receiving_status_audit1','C2','metadata',common.MIB,discovery=True)
    common.write(operation/'PRE_IO.json',dict(allowance=allowance,reason='OBSERVE_EXISTING_SUCCESSFUL_RECEIVER_NOT_REPLAY',
        model_calls=0,provider_calls=0,recorded_unix=time.time()))
    command = 'python3 -c '+shlex.quote(READ)+' '+shlex.quote(common.canonical(allowance).decode())
    observed = subprocess.run(['bash',str(REPO/'gpu/ovx_ssh.sh'),command],capture_output=True,timeout=90)
    if observed.returncode != 0:
        common.write(operation/'PUBLIC_METADATA.json',dict(status='STATUS_AUDIT_FAILED_NO_FOLLOWUP',
            stderr_sha256=common.sha(observed.stderr),returncode=observed.returncode))
        return
    receipt = json.loads(observed.stdout)
    common.write(operation/'RECEIVER_STATUS.json',receipt)
    print(json.dumps(receipt,sort_keys=True),flush=True)
    common.require(not receipt['CPU_once_already_exists'],'CPU_attempt_already_consumed')
    prior = HERE/'preparation1/receiving1'
    request = json.loads((prior/'REQUEST.json').read_bytes())
    source = common.REMOTE/'receiving_source1/source'
    common.write(operation/'CPU_FIRST_LAUNCH.json',dict(
        allowance=request['cpu_allowances'],receiving_source_freeze_sha256=common.sha((prior/'SOURCE_FREEZE.json').read_bytes()),
        preserved_export_exit=2,copy_replayed=False,first_CPU_phase=True,started_unix=time.time(),model_calls=0,provider_calls=0))
    command = ('cd '+shlex.quote(str(source))+' && env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 '
        'HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 '
        'PYTHONPATH='+shlex.quote(str(source))+' '+shlex.quote(request['runtime']['python'])+' -B receiving_cpu.py')
    completed = subprocess.run(['bash',str(REPO/'gpu/ovx_ssh.sh'),command],capture_output=True,timeout=180)
    result = json.loads(completed.stdout) if completed.stdout.strip() else dict(status='CPU_WRAPPER_FAILURE',
        stderr_sha256=common.sha(completed.stderr),stderr_bytes=len(completed.stderr))
    result['wrapper_returncode'] = completed.returncode
    common.write(operation/'PUBLIC_METADATA.json',result)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
