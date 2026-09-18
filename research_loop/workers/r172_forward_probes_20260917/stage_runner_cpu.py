"""Fresh node2 CPU-only source snapshot; no transfer, scheduler or model launch."""

import base64
import hashlib
import json
import os
from pathlib import Path

import prep_common as common
import prepare


REMOTE = r'''
import base64,hashlib,json,os,socket,stat,subprocess,time
from pathlib import Path
os.umask(0o077)
root=Path('/localhome/local-rohing/orch_r172_forward_probes_20260917_generation1/receiving_cpu1')
root.mkdir(parents=True,mode=0o700,exist_ok=False)
source=root/'source'
source.mkdir(mode=0o700)
used=0
reads=0
def write(path,raw):
 path.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
 if not isinstance(raw,bytes):raw=json.dumps(raw,sort_keys=True,separators=(',',':')).encode()
 with path.open('xb') as stream:
  stream.write(raw);stream.flush();os.fsync(stream.fileno())
def read(path):
 global used,reads
 path=Path(path)
 assert path==path.resolve() and path.is_file(),'regular_exact_receiving_source'
 with path.open('rb') as stream:
  before=os.fstat(stream.fileno())
  assert used+before.st_size<=REQUEST['metadata_bytes'],'CPU_source_envelope'
  write(root/'reads'/('%05d.json'%reads),dict(path=str(path),bytes=before.st_size,charged_before_read=True))
  reads+=1;used+=before.st_size
  raw=stream.read(before.st_size)
  after=os.fstat(stream.fileno())
  assert len(raw)==before.st_size and all(getattr(before,field)==getattr(after,field) for field in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')),'source_changed'
 return raw
write(root/'REQUEST.json',REQUEST)
try:
 template=Path(REQUEST['template'])
 files={}
 for directory in ('gpu','organism_v6','tests'):
  for path in sorted((template/directory).rglob('*.py')):
   relative=str(path.relative_to(template))
   raw=read(path)
   files[relative]=hashlib.sha256(raw).hexdigest()
   write(source/relative,raw)
 for name,encoded in REQUEST['payload'].items():
  raw=base64.b64decode(encoded)
  assert hashlib.sha256(raw).hexdigest()==REQUEST['payload_sha256'][name],'local_payload_sha'
  write(source/name,raw)
  files[name]=hashlib.sha256(raw).hexdigest()
 for name,checksum in REQUEST['frozen_gpu_pins'].items():
  assert files[name]==checksum,'unchanged_frozen_model_generator_primitives'
 python=Path(REQUEST['python']).resolve()
 assert hashlib.sha256(read(python)).hexdigest()==REQUEST['python_sha256'],'actual_receiver_interpreter'
 host_sha=hashlib.sha256(socket.gethostname().encode()).hexdigest()
 assert host_sha=='0e183169e60b06badac84e0eca6036a53b7ad90c433b8cd69b2a9aaf9159389b','bound_node2_host'
 freeze=dict(status='IMMUTABLE_RECEIVING_RUNNER_CPU_SOURCE',files=files,
  author_files=REQUEST['payload_sha256'],template=REQUEST['template'],scope=REQUEST['scope'],
  proposal=REQUEST['proposal'],frozen_unix=time.time(),model_calls=0,provider_calls=0)
 write(root/'SOURCE_FREEZE.json',freeze)
 test_command=[str(python),'-B','-m','unittest','test_design','test_preparation','test_runner_preparation','-v']
 environment=dict(PATH='/usr/bin:/bin',HOME=os.environ['HOME'],TMPDIR='/tmp',PYTHONPATH=str(source),
  PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
  HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
 bootstrap=r"""import hashlib,json,os,sys,time
from pathlib import Path
source=Path.cwd()
root=source.parent
reservation=json.loads((root/'REQUEST.json').read_bytes())
charged=0
sequence=0
busy=False
def audit(event,args):
 global charged,sequence,busy
 if busy or event!='open' or not args or not isinstance(args[0],(str,bytes)):return
 path=Path(os.fsdecode(args[0])).absolute()
 mode=args[1] if len(args)>1 else None
 if isinstance(mode,str) and any(marker in mode for marker in ('w','a','x','+')):return
 if not path.is_relative_to(source) or not path.exists() or not path.is_file():return
 busy=True
 try:
  size=path.stat().st_size
  if charged+size>reservation['cpu_read_bytes']:raise ValueError('bounded_CPU_source_reads_exhausted')
  entry=dict(path=str(path),bytes=size,charged_before_open=True,observed_unix=time.time())
  target=root/'CPU_READS'/('%05d.json'%sequence)
  target.parent.mkdir(mode=0o700,exist_ok=True)
  with target.open('x') as stream:json.dump(entry,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
  charged+=size;sequence+=1
 finally:busy=False
sys.addaudithook(audit)
import r172_runner,unittest
freeze=json.loads((root/'SOURCE_FREEZE.json').read_bytes())
r172_runner.validate_loaded_sources(source)
r172_runner.verify_source_closure(source,freeze)
suite=unittest.defaultTestLoader.loadTestsFromNames(['test_design','test_preparation','test_runner_preparation'])
result=unittest.TextTestRunner(verbosity=2).run(suite)
with (root/'CPU_RESULT.json').open('x') as stream:
 json.dump(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
  source_bytes_charged=charged,source_read_operations=sequence,model_calls=0,provider_calls=0),stream,sort_keys=True)
sys.exit(0 if result.wasSuccessful() else 1)
"""
 write(root/'BOOTSTRAP.py',bootstrap.encode())
 actual_command=[str(python),'-B',str(root/'BOOTSTRAP.py')]
 completed=subprocess.run(actual_command,cwd=source,env=environment,capture_output=True,timeout=120)
 output=completed.stdout+completed.stderr
 write(root/'TEST_OUTPUT.txt',output)
 test_result=json.loads((root/'CPU_RESULT.json').read_bytes()) if (root/'CPU_RESULT.json').exists() else None
 actual_after={name:hashlib.sha256(read(source/name)).hexdigest() for name in files}
 assert files==actual_after,'frozen_receiving_source_changed_during_CPU'
 result=dict(status='ACTUAL_RECEIVING_RUNNER_CPU_PASS' if completed.returncode==0 else 'ACTUAL_RECEIVING_RUNNER_CPU_FAILED',
  complete_campaign_receiving_gate=False,exit_status=completed.returncode,command=actual_command,logical_test_selection=test_command,
  test_result=test_result,test_output=dict(path=str(root/'TEST_OUTPUT.txt'),sha256=hashlib.sha256(output).hexdigest()),
  source_freeze=dict(path=str(root/'SOURCE_FREEZE.json'),sha256=hashlib.sha256((root/'SOURCE_FREEZE.json').read_bytes()).hexdigest()),
  author_files=REQUEST['payload_sha256'],python=str(python),python_sha256=REQUEST['python_sha256'],host_sha256=host_sha,
  CUDA_VISIBLE_DEVICES='',observed_unix=time.time(),stage_source_bytes_charged=used,
  stage_read_operations=reads,model_calls=0,provider_calls=0,real_custody_or_adapter_reads=0,
  remaining_gates=['AMPERE_B5_B6_TRANSFER_INTEGRATION','REAL_SOURCE_AND_ALLOCATION_BINDINGS',
    'PRIVATE_RUBRIC_FREEZE','FULL_RECEIVING_CPU','FRESH_INDEPENDENT_REVIEW','SEPARATE_MAIN_EXECUTION_GO','FRESH_STRICT_ADMISSION'])
 write(root/'PUBLIC_METADATA.json',result)
 print(json.dumps(dict(result,test_log=output.decode(errors='replace')),sort_keys=True))
except BaseException as error:
 result=dict(status='RECEIVING_RUNNER_CPU_PREPARATION_FAILED_NO_REMOTE_RETRY',error_type=type(error).__name__,
  reason=str(error) if isinstance(error,(AssertionError,ValueError)) else 'RECEIVING_CPU_ERROR',
  source_bytes_charged=used,source_read_operations=reads,observed_unix=time.time(),model_calls=0,provider_calls=0)
 write(root/'FAILED.json',result)
 print(json.dumps(result,sort_keys=True))
'''


def main():
    os.umask(0o077)
    scope,proposal,ledger=prepare.setup()
    reservation=ledger.reserve('receiving_runner_CPU1','_campaign','metadata',128*prepare.MIB)
    names=('r172_runner.py','r172_scheduler.py','design.py','prep_common.py','source_prepare.py',
        'test_runner_preparation.py','test_design.py','test_preparation.py','PROPOSAL.json','PREPARATION_SCOPE.json')
    source_files={name:prepare.HERE/name for name in names}
    roster='research_loop/workers/r171_forward_roster_20260917/CURRENT_LEARNER_ROSTER.json'
    source_files[roster]=prepare.REPO/roster
    payload={}
    checksums={}
    for name,path in source_files.items():
        raw=path.read_bytes()
        checksum=hashlib.sha256(raw).hexdigest()
        common.require(common.ref(path)['sha256']==checksum,'stable_local_CPU_candidate_bytes')
        payload[name]=base64.b64encode(raw).decode()
        checksums[name]=checksum
    resource=common.read(prepare.PREP/'RECEIVER_RESOURCE_OBSERVATION_01.json')
    runtime=resource['runtime_resource']
    request=dict(metadata_bytes=64*prepare.MIB,cpu_read_bytes=64*prepare.MIB,reservation=reservation,
        template=resource['receiving_template_source'],python=runtime['python'],python_sha256=runtime['python_sha256'],
        payload=payload,payload_sha256=checksums,scope=common.ref(prepare.HERE/'PREPARATION_SCOPE.json'),
        proposal=common.ref(prepare.HERE/'PROPOSAL.json'),
        frozen_gpu_pins={name:value['sha256'] for name,value in proposal['existing_source_pins'].items() if name.startswith('gpu/')})
    common.write(prepare.PREP/'receiving_cpu1/REQUEST.json',request)
    result=json.loads(prepare.wrapper('ovx','receiving_runner_CPU1','python3 -B -',
        ('REQUEST='+repr(request)+'\n'+REMOTE).encode(),seconds=180))
    test_log=result.pop('test_log',None)
    if test_log is not None:
        common.write(prepare.PREP/'receiving_cpu1/TEST_OUTPUT.txt',test_log.encode())
    evidence=common.write(prepare.PREP/'receiving_cpu1/PUBLIC_METADATA.json',result)
    print(json.dumps(dict(status=result['status'],test_result=result.get('test_result'),
        observed_unix=result['observed_unix'],complete_campaign_receiving_gate=False,evidence=evidence)))


if __name__=='__main__':
    main()
