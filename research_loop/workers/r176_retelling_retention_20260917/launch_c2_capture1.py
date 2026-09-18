"""One-shot wrapper launcher; persistent reservations precede remote I/O."""

import base64
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

import preparation_io as common


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BOOTSTRAP = '''import base64,json,os,pathlib,subprocess,sys
os.umask(0o077)
root=pathlib.Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1/source_capture1')
root.mkdir(parents=True,mode=0o700,exist_ok=False)
raw=sys.stdin.buffer.read(2*1024*1024+1)
assert len(raw)<=2*1024*1024
payload=json.loads(raw)
for name,encoded in payload['files'].items():
    path=root/name
    assert not pathlib.Path(name).is_absolute() and '..' not in pathlib.Path(name).parts
    path.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
    with path.open('xb') as stream:
        stream.write(base64.b64decode(encoded,validate=True))
with (root/'STAGING_BYTES.json').open('x') as stream:
    json.dump({'received_bytes':len(raw),'global_precharge':payload['stage_allowance']},stream)
sys.exit(subprocess.call(['python3',str(root/'source/c2_capture.py')],cwd=root/'source'))
'''


def main():
    os.umask(0o077)
    controls = common.validate_controls(HERE)
    operation = HERE/'preparation1/source_capture1'
    operation.mkdir(parents=True,mode=0o700,exist_ok=False)
    ledger = common.Ledger(HERE/'preparation1/global_ledger')
    stage = ledger.reserve('C2_capture1_control_transport','_campaign','metadata',4*common.MIB,discovery=True)
    allowances = dict(
        metadata=ledger.reserve('C2_capture1_metadata','C2','metadata',32*common.MIB),
        discovery=ledger.reserve('C2_capture1_native_discovery','C2','metadata',2*common.MIB,discovery=True),
        adapter=ledger.reserve('C2_sleep33_original_capture','C2','adapter',128*common.MIB,
            sleep=33,read_pass='original_capture'))
    inventory = json.loads((HERE.parent/'r172_forward_probes_20260917/preparation1/discovery/ovx3.json').read_bytes())
    native = next(row['native_identity'] for row in inventory['rows'] if row['life_id']=='C2')
    sources = {name:(HERE/name).read_bytes() for name in ('preparation_io.py','c2_capture.py')}
    request = dict(scope=controls['PREPARATION_SCOPE.json'],allowances=allowances,native_identity=native,
        life_id='C2',sleep=33,model_calls=0,provider_calls=0,source_pins={name:common.sha(raw) for name,raw in sources.items()})
    common.write(operation/'REQUEST.json',request)
    files = {'source/'+name:raw for name,raw in sources.items()}
    files.update({'control/'+name:(HERE/name).read_bytes() for name in controls})
    files['REQUEST.json'] = common.canonical(request)
    payload = common.canonical(dict(stage_allowance=stage,
        files={name:base64.b64encode(raw).decode() for name,raw in files.items()}))
    common.require(len(payload)<2*common.MIB,'bounded_staging_payload')
    common.write(operation/'LAUNCH.json',dict(started_unix=time.time(),payload_bytes=len(payload),
        stage_allowance=stage,wrapper='gpu/ovx3_ssh.sh',model_calls=0,provider_calls=0))
    try:
        completed = subprocess.run(['bash',str(REPO/'gpu/ovx3_ssh.sh'),
            'python3 -c '+shlex.quote(BOOTSTRAP)],input=payload,capture_output=True,timeout=180)
        common.require(len(completed.stdout)<common.MIB and len(completed.stderr)<common.MIB,'bounded_operation_output')
        if completed.stdout.strip():
            result = json.loads(completed.stdout)
        else:
            result = dict(status='WRAPPER_OR_SOURCE_FAILURE_PRESERVED_NO_RETRY',returncode=completed.returncode,
                stderr_bytes=len(completed.stderr),stderr_sha256=common.sha(completed.stderr),
                observed_unix=time.time(),model_calls=0,provider_calls=0)
        result['wrapper_returncode'] = completed.returncode
    except Exception as error:
        result = dict(status='LAUNCH_FAILED_OR_UNCERTAIN_NO_RETRY',error_type=type(error).__name__,
            observed_unix=time.time(),model_calls=0,provider_calls=0)
    common.write(operation/'PUBLIC_METADATA.json',result)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
