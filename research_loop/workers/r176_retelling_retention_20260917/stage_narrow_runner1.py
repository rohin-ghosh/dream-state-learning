"""New CPU-only receiver runner proof and opaque candidate config bindings."""

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
REMOTE = '''import base64,hashlib,io,json,os,pathlib,socket,subprocess,sys,time
os.umask(0o077)
root=pathlib.Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1/runner_candidate1')
root.mkdir(mode=0o700,exist_ok=False)
payload=json.loads(sys.stdin.buffer.read(2*1024*1024))
request=payload['request']
used=0
sequence=0
def write(path,document):
 path.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
 raw=document if isinstance(document,bytes) else json.dumps(document,sort_keys=True,separators=(',',':')).encode()
 with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()}
def read(path,limit=1024*1024):
 global used,sequence
 path=pathlib.Path(path)
 assert path==path.resolve() and path.is_file()
 with path.open('rb',buffering=0) as stream:
  before=os.fstat(stream.fileno())
  assert before.st_size<=limit and used+before.st_size<=request['metadata_allowance']['document']['bytes']
  write(root/'READS'/('%06d.json'%sequence),{'path':str(path),'bytes':before.st_size,'charged_before_read':True,
   'allowance':request['metadata_allowance']})
  used+=before.st_size;sequence+=1
  raw=stream.read(before.st_size)
  assert len(raw)==before.st_size and os.fstat(stream.fileno()).st_mtime_ns==before.st_mtime_ns
 return raw
write(root/'REQUEST.json',request)
source=root/'source'
source.mkdir(mode=0o700)
for name,encoded in payload['files'].items():
 assert pathlib.Path(name).name==name
 raw=base64.b64decode(encoded,validate=True)
 assert hashlib.sha256(raw).hexdigest()==request['source_pins'][name]
 write(source/name,raw)
assert os.stat(source).st_mode&0o077==0
interpreter=pathlib.Path(request['runtime']['python']).resolve()
assert hashlib.sha256(read(interpreter,32*1024*1024)).hexdigest()==request['runtime']['python_sha256']
assert hashlib.sha256(socket.gethostname().encode()).hexdigest()=='0e183169e60b06badac84e0eca6036a53b7ad90c433b8cd69b2a9aaf9159389b'
base=root.parent
references={}
documents={}
for key,relative in [('source','receiving_source1/REQUEST.json'),('cpu_gate','receiving_cpu1/PUBLIC_METADATA.json'),
 ('capture','receiving_transfers/C2_000033/COMPLETE.json')]:
 path=base/relative
 raw=read(path)
 references[key]={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()}
 documents[key]=json.loads(raw)
assert documents['cpu_gate']['status']=='ACTUAL_C2_SLEEP33_RECEIVING_CPU_PASS'
assert documents['cpu_gate']['source_freeze']==documents['source']['source_pins']
assert documents['capture']['status']=='RECEIVING_COPY_COMPLETE'
assert documents['source']['runtime']==request['runtime']
write(root/'EXACT_RECEIVING_BINDINGS.json',references)
bootstrap=r"""import hashlib,json,os,pathlib,sys,time,unittest
root=pathlib.Path.cwd().parent
source=root/'source'
request=json.loads((root/'REQUEST.json').read_bytes())
busy=False
used=0
sequence=0
def audit(event,args):
 global busy,used,sequence
 if busy or event!='open' or not args or not isinstance(args[0],(str,bytes)):return
 path=pathlib.Path(os.fsdecode(args[0])).absolute()
 mode=args[1] if len(args)>1 else None
 if isinstance(mode,str) and any(marker in mode for marker in ('w','a','x','+')):return
 if not path.is_relative_to(source) or not path.is_file():return
 busy=True
 try:
  size=path.stat().st_size
  assert used+size<=request['CPU_allowance']['document']['bytes']
  target=root/'CPU_READS'/('%06d.json'%sequence)
  target.parent.mkdir(mode=0o700,exist_ok=True)
  with target.open('x') as stream:
   json.dump({'path':str(path),'bytes':size,'charged_before_read':True,'allowance':request['CPU_allowance']},stream,sort_keys=True)
   stream.flush();os.fsync(stream.fileno())
  used+=size;sequence+=1
 finally:busy=False
sys.addaudithook(audit)
import r176_runner
assert pathlib.Path(r176_runner.__file__).resolve()==source/'r176_runner.py'
assert hashlib.sha256((source/'r176_runner.py').read_bytes()).hexdigest()==request['source_pins']['r176_runner.py']
suite=unittest.defaultTestLoader.loadTestsFromName('test_r176_runner')
result=unittest.TextTestRunner(verbosity=2).run(suite)
receipt={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
 'metadata_bytes_charged':used,'model_calls':0,'provider_calls':0,'observed_unix':time.time()}
with (root/'CPU_COUNTS.json').open('x') as stream:json.dump(receipt,stream,sort_keys=True)
sys.exit(0 if result.wasSuccessful() else 2)
"""
command=[request['runtime']['python'],'-B','-c',bootstrap]
environment=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',
 TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONPATH=str(source))
completed=subprocess.run(command,cwd=source,env=environment,capture_output=True,timeout=120)
output=write(root/'CPU_TESTS.txt',completed.stdout+completed.stderr)
assert completed.returncode==0,'receiving_narrow_runner_CPU_failure'
counts=json.loads(read(root/'CPU_COUNTS.json'))
gate=dict(counts,status='ACTUAL_R176_NARROW_RUNNER_CPU_PASS',runner_sha256=request['source_pins']['r176_runner.py'],
 source_pins=request['source_pins'],python=request['runtime']['python'],python_sha256=request['runtime']['python_sha256'],
 CUDA_VISIBLE_DEVICES='',command=[request['runtime']['python'],'-B','test_r176_runner'],test_output=output,
 execution_authorized=False,receiving_bindings=references,source_metadata_bytes_charged=used)
gate_ref=write(root/'RUNNER_CPU_GATE.json',gate)
configs=[]
for index,condition in enumerate(('LORA_ON','LORA_OFF')):
 config=dict(schema='R176_C2_SLEEP33_CONDITION_CANDIDATE_V1',life_id='C2',sleep=33,condition=condition,
  physical=index,gpu_uuid=request['devices'][str(index)],**request['runtime'],**references,
  runner_cpu_gate=gate_ref,allowances=request['execution_read_allowances'][condition])
 name=hashlib.sha256(('C2:33:'+condition).encode()).hexdigest()+'.private.json'
 configs.append(write(root/'controls'/name,config))
release=write(root/'OLD_RELEASE.json',base64.b64decode(payload['old_release'],validate=True))
public=dict(status='C2_SLEEP33_RUNNER_CPU_AND_CONFIG_CANDIDATES_READY_FOR_REVIEW',observed_unix=time.time(),
 life_id='C2',sleep=33,condition_config_count=2,future_calls_if_both_admitted=6,
 executions=configs,source=references['source'],cpu_gate=references['cpu_gate'],runner_cpu_gate=gate_ref,
 runner_sha256=request['source_pins']['r176_runner.py'],runner_path=str(source/'r176_runner.py'),old_release=release,
 tests_run=counts['tests_run'],failures=counts['failures'],errors=counts['errors'],model_calls=0,provider_calls=0,
 execution_authorized=False,independent_integration_review_pending=True)
write(root/'PUBLIC_METADATA.json',public)
print(json.dumps(public,sort_keys=True))
'''


def main():
    os.umask(0o077)
    common.validate_controls(HERE)
    operation = HERE/'preparation1/narrow_runner1'
    operation.mkdir(parents=True,mode=0o700,exist_ok=False)
    ledger = common.Ledger(HERE/'preparation1/global_ledger')
    metadata = ledger.reserve('R176_narrow_runner1_source_and_bindings','C2','metadata',16*common.MIB)
    cpu = ledger.reserve('R176_narrow_runner1_CPU_source','C2','metadata',16*common.MIB)
    storage = ledger.reserve('R176_narrow_runner1_storage','_campaign','storage',8*common.MIB)
    execution = {}
    for condition,prefix in (('LORA_ON','ON'),('LORA_OFF','OFF')):
        execution[condition] = {}
        for phase in ('preflight','native'):
            execution[condition][phase] = dict(
                metadata=ledger.reserve('C2_sleep33_'+prefix+'_'+phase+'_metadata','C2','metadata',24*common.MIB),
                adapter=ledger.reserve('C2_sleep33_'+prefix+'_'+phase+'_verification','C2','adapter',128*common.MIB,
                    sleep=33,read_pass=prefix+'_'+phase+'_verification'))
        execution[condition]['model_load'] = ledger.reserve('C2_sleep33_'+prefix+'_model_load','C2','adapter',128*common.MIB,
            sleep=33,read_pass=prefix+'_model_load')
    sibling = HERE.parent/'r172_forward_probes_20260917'
    release = (sibling/'preparation1/RECEIVER_RESOURCE_OBSERVATION_01.json').read_bytes()
    runtime = json.loads(release)['runtime_resource']
    files = {name:(HERE/name).read_bytes() for name in ('r176_runner.py','test_r176_runner.py','preparation_io.py')}
    request = dict(scope_sha256=common.SCOPE_SHA,source_pins={name:common.sha(raw) for name,raw in files.items()},
        metadata_allowance=metadata,CPU_allowance=cpu,storage_allowance=storage,execution_read_allowances=execution,
        runtime=runtime,devices={'0':'GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0','1':'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4'},
        model_calls=0,provider_calls=0,execution_authorized=False)
    common.write(operation/'REQUEST.json',request)
    for name,raw in files.items():
        common.write(operation/'author_source'/name,raw)
    payload = common.canonical(dict(request=request,files={name:base64.b64encode(raw).decode() for name,raw in files.items()},
        old_release=base64.b64encode(release).decode()))
    common.require(len(payload)<2*common.MIB,'bounded_narrow_source_payload')
    result = subprocess.run(['bash',str(REPO/'gpu/ovx_ssh.sh'),'python3 -c '+shlex.quote(REMOTE)],
        input=payload,capture_output=True,timeout=180)
    common.require(len(result.stdout)<common.MIB and len(result.stderr)<common.MIB,'bounded_CPU_status_output')
    receipt = json.loads(result.stdout) if result.returncode==0 else dict(status='NARROW_CPU_PREPARATION_FAILED_PRESERVED',
        returncode=result.returncode,stderr_sha256=common.sha(result.stderr),stderr_bytes=len(result.stderr),
        observed_unix=time.time(),model_calls=0,provider_calls=0)
    common.write(operation/'PUBLIC_METADATA.json',receipt)
    print(json.dumps(receipt,sort_keys=True))


if __name__=='__main__':
    main()
