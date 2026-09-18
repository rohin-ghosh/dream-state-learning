"""One wrapper-only read of fixed metadata pointers; no old controller changes."""

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
root=pathlib.Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1/subsequent_slots1/discovery1')
root.mkdir(parents=True,mode=0o700,exist_ok=False)
payload=json.loads(sys.stdin.buffer.read(1024*1024))
with (root/'REQUEST.json').open('x') as stream:json.dump(payload['request'],stream,sort_keys=True)
source=root/'source';source.mkdir(mode=0o700)
for name,encoded in payload['files'].items():
 assert pathlib.Path(name).name==name
 with (source/name).open('xb') as stream:stream.write(base64.b64decode(encoded,validate=True))
sys.exit(subprocess.call(['python3','-B',str(source/'discover.py')]))
'''


def main():
    os.umask(0o077)
    common.validate_controls(WORKER)
    operation = HERE/'discovery1'
    operation.mkdir(mode=0o700,exist_ok=False)
    ledger = common.Ledger(WORKER/'preparation1/global_ledger')
    allowance = ledger.reserve('C2_followup_discovery1_metadata','C2','metadata',2*common.MIB,discovery=True)
    stage = ledger.reserve('C2_followup_discovery1_staging','_campaign','metadata',common.MIB,discovery=True)
    files = {'discover.py':(HERE/'discover.py').read_bytes(),'preparation_io.py':(WORKER/'preparation_io.py').read_bytes()}
    request = dict(allowance=allowance,stage_allowance=stage,scope_sha256=common.SCOPE_SHA,
        fixed_sleeps=list(range(34,39)),model_calls=0,provider_calls=0,
        source_pins={name:common.sha(raw) for name,raw in files.items()},created_unix=time.time())
    common.write(operation/'REQUEST.json',request)
    payload = common.canonical(dict(request=request,files={name:base64.b64encode(raw).decode() for name,raw in files.items()}))
    common.require(len(payload)<common.MIB,'bounded_fixed_discovery_staging')
    result = subprocess.run(['bash',str(REPO/'gpu/ovx3_ssh.sh'),'python3 -c '+shlex.quote(REMOTE)],
        input=payload,capture_output=True,timeout=90)
    receipt = json.loads(result.stdout) if result.returncode==0 else dict(status='FIXED_DISCOVERY_FAILED_PRESERVED_NO_RETRY',
        returncode=result.returncode,stderr_bytes=len(result.stderr),stderr_sha256=common.sha(result.stderr),
        observed_unix=time.time(),model_calls=0,provider_calls=0)
    common.write(operation/'PUBLIC_METADATA.json',receipt)
    print(json.dumps(receipt,sort_keys=True))


if __name__=='__main__':
    main()
