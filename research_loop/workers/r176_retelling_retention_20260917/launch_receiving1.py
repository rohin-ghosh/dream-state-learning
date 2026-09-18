"""One finite C2 source-export/receiver/CPU path with distinct advance charges."""

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
REVIEWED_PINS = dict(transfer='e8b3aed5abe19cfc195ac4fde318e8316834c582d883e9dcfce892b02f19bb2e',
    common='f6751d157bb283627a185ecf14321d571673512b61f17aedac3b056ef5410aee')
STAGE = '''import base64,hashlib,json,os,pathlib,shutil,sys,time
os.umask(0o077)
root=pathlib.Path(sys.argv[1])
assert str(root) in ('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1/source_export1',
 '/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1/receiving_source1')
root.mkdir(parents=True,mode=0o700,exist_ok=False)
raw=sys.stdin.buffer.read(32*1024*1024+1)
assert len(raw)<=32*1024*1024
payload=json.loads(raw)
assert shutil.disk_usage(root).free>=64*1024*1024
def write(path,raw):
 path.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
 with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
write(root/'REQUEST.json',json.dumps(payload['request'],sort_keys=True,separators=(',',':')).encode())
for name,encoded in payload['files'].items():
 assert not pathlib.Path(name).is_absolute() and '..' not in pathlib.Path(name).parts
 raw=base64.b64decode(encoded,validate=True)
 assert hashlib.sha256(raw).hexdigest()==payload['request']['source_pins'][name]
 write(root/'source'/name,raw)
if root.name=='receiving_source1':
 interpreter=pathlib.Path(payload['request']['runtime']['python']).resolve()
 with interpreter.open('rb',buffering=0) as stream:
  size=os.fstat(stream.fileno()).st_size
  assert size<=32*1024*1024
  write(root/'INTERPRETER_READ.json',json.dumps({'path':str(interpreter),'bytes':size,
   'stage_precharge':payload['request']['stage_allowance'],'charged_before_read':True},sort_keys=True).encode())
  raw=stream.read(size)
  assert len(raw)==size and hashlib.sha256(raw).hexdigest()==payload['request']['runtime']['python_sha256']
result={'status':'SOURCE_STAGE_COMPLETE_CPU_ONLY','root':str(root),'files':len(payload['files']),
 'model_calls':0,'provider_calls':0,'observed_unix':time.time()}
write(root/'PUBLIC_METADATA.json',json.dumps(result,sort_keys=True).encode())
print(json.dumps(result,sort_keys=True))
'''


def stage(wrapper, remote, files, request, local):
    payload = common.canonical(dict(request=request,files={name:base64.b64encode(raw).decode() for name,raw in files.items()}))
    common.require(len(payload)<=32*common.MIB,'bounded_code_staging')
    result = subprocess.run(['bash',str(REPO/wrapper),'python3 -c '+shlex.quote(STAGE)+' '+shlex.quote(str(remote))],
        input=payload,capture_output=True,timeout=180)
    common.require(len(result.stdout)<=common.MIB and len(result.stderr)<=common.MIB,'bounded_staging_result')
    receipt = json.loads(result.stdout) if result.returncode==0 else dict(status='STAGING_FAILED_PRESERVED',
        returncode=result.returncode,stderr_sha256=common.sha(result.stderr),stderr_bytes=len(result.stderr))
    common.write(local,receipt)
    common.require(result.returncode==0,'staging_failed_no_retry')


def main():
    os.umask(0o077)
    common.validate_controls(HERE)
    operation = HERE/'preparation1/receiving1'
    operation.mkdir(parents=True,mode=0o700,exist_ok=False)
    prior = json.loads((HERE/'preparation1/source_capture2/PUBLIC_METADATA.json').read_bytes())
    common.require(prior['status']=='FIXED_C2_SLEEP33_SOURCE_CAPTURE_VERIFIED','source_capture_required')
    ledger = common.Ledger(HERE/'preparation1/global_ledger')
    allowances = {}
    for label,read_pass,metadata in [('export','source_export',32),('receive','receiver_stream',32),
            ('cpu','receiving_CPU_verification',128)]:
        allowances[label] = dict(
            metadata=ledger.reserve('C2_receiving1_'+label+'_metadata','C2','metadata',metadata*common.MIB),
            adapter=ledger.reserve('C2_sleep33_'+read_pass,'C2','adapter',128*common.MIB,sleep=33,read_pass=read_pass))
    stage_allowance = ledger.reserve('R176_receiving1_code_and_interpreter','_campaign','metadata',64*common.MIB)
    control_allowance = ledger.reserve('R176_receiving1_transport_control','_campaign','metadata',4*common.MIB,discovery=True)
    storage = ledger.reserve('C2_receiving1_payload_storage','C2','storage',160*common.MIB)
    source_storage = ledger.reserve('R176_receiving1_source_storage','_campaign','storage',64*common.MIB)
    sibling = HERE.parent/'r172_forward_probes_20260917'
    reviewed = (sibling/'prep_common.py').read_bytes()
    common.require(common.sha(reviewed)==REVIEWED_PINS['common'] and
        common.sha((sibling/'transfer.py').read_bytes())==REVIEWED_PINS['transfer'],'V3_exact_components')
    minimal = {name:(HERE/name).read_bytes() for name in ('r176_transfer.py','preparation_io.py','c2_capture.py')}
    minimal['reviewed_prep_common.py'] = reviewed
    files = dict(minimal)
    for directory in ('gpu','organism_v6'):
        for path in sorted((REPO/directory).rglob('*.py')):
            common.require(path.is_file() and not path.is_symlink(),'regular_local_CPU_source')
            files[str(path.relative_to(REPO))] = path.read_bytes()
    for name in ('receiving_cpu.py','candidate.py','test_candidate.py','test_preparation_io.py','test_r176_transfer.py'):
        files[name] = (HERE/name).read_bytes()
    for name in common.PINS:
        files[name] = (HERE/name).read_bytes()
    files['tests/__init__.py'] = b''
    files['tests/test_orch_r167_fleet_eval.py'] = (REPO/'tests/test_orch_r167_fleet_eval.py').read_bytes()
    common.require(common.sha(files['gpu/orch_r167_fleet_eval.py'])==
        '383415b6b37f8ff237c95b053439f6919f7ee47c452b3ffd015e606ff1962011','unchanged_actual_generator')
    runtime = json.loads((sibling/'preparation1/RECEIVER_RESOURCE_OBSERVATION_01.json').read_bytes())['runtime_resource']
    request = dict(scope_sha256=common.SCOPE_SHA,source_capture=prior['capture_complete'],
        export_allowances=allowances['export'],receive_allowances=allowances['receive'],cpu_allowances=allowances['cpu'],
        stage_allowance=stage_allowance,control_allowance=control_allowance,storage_allowance=storage,
        source_storage_allowance=source_storage,runtime=runtime,reviewed_pins=REVIEWED_PINS,model_calls=0,provider_calls=0)
    common.write(operation/'REQUEST.json',request)
    for name in ('r176_transfer.py','receiving_cpu.py','preparation_io.py','c2_capture.py'):
        common.write(operation/'author_source'/name,files[name])
    source_request = dict(request,source_pins={name:common.sha(raw) for name,raw in minimal.items()})
    receiver_request = dict(request,source_pins={name:common.sha(raw) for name,raw in files.items()})
    common.write(operation/'SOURCE_FREEZE.json',receiver_request['source_pins'])
    try:
        stage('gpu/ovx3_ssh.sh',common.REMOTE/'source_export1',minimal,source_request,operation/'SOURCE_STAGE.json')
        stage('gpu/ovx_ssh.sh',common.REMOTE/'receiving_source1',files,receiver_request,operation/'RECEIVER_STAGE.json')
        source_command = 'python3 -B '+str(common.REMOTE/'source_export1/source/r176_transfer.py')+' export --request '+str(common.REMOTE/'source_export1/REQUEST.json')
        receiver_command = 'python3 -B '+str(common.REMOTE/'receiving_source1/source/r176_transfer.py')+' receive --request '+str(common.REMOTE/'receiving_source1/REQUEST.json')
        exporter = subprocess.Popen(['bash',str(REPO/'gpu/ovx3_ssh.sh'),source_command],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        receiver = subprocess.Popen(['bash',str(REPO/'gpu/ovx_ssh.sh'),receiver_command],stdin=exporter.stdout,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        exporter.stdout.close()
        output,receiver_error = receiver.communicate(timeout=240)
        exporter.wait(timeout=30)
        source_error = exporter.stderr.read(common.MIB)
        common.write(operation/'TRANSPORT_EXIT.json',dict(source_returncode=exporter.returncode,
            receiver_returncode=receiver.returncode,source_stderr_sha256=common.sha(source_error),
            receiver_stderr_sha256=common.sha(receiver_error),source_stderr_bytes=len(source_error),
            receiver_stderr_bytes=len(receiver_error),observed_unix=time.time(),model_calls=0,provider_calls=0))
        common.require(exporter.returncode==receiver.returncode==0,'transport_failed_no_retry')
        received = json.loads(output)
        common.write(operation/'RECEIVING_COPY.json',received)
        print(json.dumps(received,sort_keys=True),flush=True)
        source = common.REMOTE/'receiving_source1/source'
        command = ('cd '+shlex.quote(str(source))+' && env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 '
            'HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 '
            'PYTHONPATH='+shlex.quote(str(source))+' '+shlex.quote(runtime['python'])+' -B receiving_cpu.py')
        cpu = subprocess.run(['bash',str(REPO/'gpu/ovx_ssh.sh'),command],capture_output=True,timeout=180)
        common.require(len(cpu.stdout)<common.MIB and len(cpu.stderr)<common.MIB,'bounded_CPU_result')
        result = json.loads(cpu.stdout) if cpu.stdout.strip() else dict(status='CPU_WRAPPER_FAILURE',
            returncode=cpu.returncode,stderr_sha256=common.sha(cpu.stderr),stderr_bytes=len(cpu.stderr))
        result['wrapper_returncode'] = cpu.returncode
    except Exception as error:
        result = dict(status='RECEIVING_PATH_FAILED_OR_UNCERTAIN_NO_RETRY',error_type=type(error).__name__,
            reason=str(error) if isinstance(error,ValueError) else 'RECEIVING_PREPARATION_FAILURE',
            observed_unix=time.time(),model_calls=0,provider_calls=0)
    common.write(operation/'PUBLIC_METADATA.json',result)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
