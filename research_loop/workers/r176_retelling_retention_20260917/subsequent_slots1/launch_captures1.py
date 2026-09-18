"""Separate once/read authorities for each eligible already fixed C2 checkpoint."""

import base64
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
WORKER = HERE.parent
REPO = WORKER.parents[2]
sys.path.insert(0,str(WORKER))
import preparation_io as common


REMOTE = '''import base64,json,os,pathlib,subprocess,sys
os.umask(0o077)
root=pathlib.Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1/subsequent_slots1/capture_batch1')
root.mkdir(parents=True,mode=0o700,exist_ok=False)
payload=json.loads(sys.stdin.buffer.read(1024*1024))
with (root/'REQUEST.json').open('x') as stream:json.dump(payload['request'],stream,sort_keys=True)
source=root/'source';source.mkdir(mode=0o700)
for name,encoded in payload['files'].items():
 assert pathlib.Path(name).name==name
 with (source/name).open('xb') as stream:stream.write(base64.b64decode(encoded,validate=True))
sys.exit(subprocess.call(['python3','-B',str(source/'capture_fixed.py')]))
'''


def main():
    os.umask(0o077)
    common.validate_controls(WORKER)
    operation = HERE/'capture_batch1'
    operation.mkdir(mode=0o700,exist_ok=False)
    discovery_path = HERE/'discovery1/PUBLIC_METADATA.json'
    discovery = json.loads(discovery_path.read_bytes())
    common.require(discovery['status']=='FIXED_C2_FOLLOWUP_POINTER_DISCOVERY_COMPLETE','completed_fixed_discovery')
    ledger = common.Ledger(WORKER/'preparation1/global_ledger')
    stage = ledger.reserve('C2_followup_capture_batch1_staging','_campaign','metadata',common.MIB,discovery=True)
    slots = []
    for row in discovery['rows']:
        if row['status']!='BOUND_OPERATIONAL_POINTER_NOT_NEW_CAPTURE':
            continue
        sleep = row['sleep']
        slots.append(dict(sleep=sleep,pointer=row['pointer'],allowances=dict(
            metadata=ledger.reserve(f'C2_sleep{sleep}_capture1_metadata','C2','metadata',8*common.MIB),
            adapter=ledger.reserve(f'C2_sleep{sleep}_original_capture','C2','adapter',128*common.MIB,
                sleep=sleep,read_pass='original_capture'))))
    files = {name:(HERE/name).read_bytes() for name in ('capture_fixed.py','discover.py')}
    files.update({name:(WORKER/name).read_bytes() for name in ('preparation_io.py','c2_capture.py')})
    request = dict(scope_sha256=common.SCOPE_SHA,stage_allowance=stage,slots=slots,
        discovery=dict(path=str(discovery_path),sha256=common.sha(discovery_path.read_bytes())),
        source_pins={name:common.sha(raw) for name,raw in files.items()},model_calls=0,provider_calls=0,
        current_reviewed_C2_sleep33_unchanged=True,created_unix=time.time())
    common.write(operation/'REQUEST.json',request)
    for name,raw in files.items():
        common.write(operation/'author_source'/name,raw)
    payload = common.canonical(dict(request=request,files={name:base64.b64encode(raw).decode() for name,raw in files.items()}))
    common.require(len(payload)<common.MIB,'bounded_capture_batch_staging')
    result = subprocess.run(['bash',str(REPO/'gpu/ovx3_ssh.sh'),'python3 -c '+shlex.quote(REMOTE)],
        input=payload,capture_output=True,timeout=180)
    receipt = json.loads(result.stdout) if result.returncode==0 else dict(status='FIXED_CAPTURE_BATCH_FAILED_PRESERVED_NO_RETRY',
        returncode=result.returncode,stderr_bytes=len(result.stderr),stderr_sha256=common.sha(result.stderr),
        observed_unix=time.time(),model_calls=0,provider_calls=0)
    common.write(operation/'PUBLIC_METADATA.json',receipt)
    print(json.dumps(receipt,sort_keys=True))


if __name__=='__main__':
    main()
