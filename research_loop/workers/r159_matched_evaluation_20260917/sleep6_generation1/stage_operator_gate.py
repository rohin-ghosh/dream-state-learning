import base64
import hashlib
import json
from pathlib import Path
import subprocess


directory = Path(__file__).resolve().parent
worker = directory.parent
repository = worker.parents[2]
files = {name:base64.b64encode((directory/name).read_bytes()).decode() for name in (
    'admission_wrapper.py','test_admission_wrapper.py','copy_sleep6.py','test_copy_sleep6.py','test_window.py')}
program = '''
import base64, hashlib, json, os, subprocess, sys, time
from pathlib import Path
files = FILES
root = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
runtime = root/'preparation/runtime_generation3'
control = root/'control/candidate5_sleep6_runtime3_generation1'
destination = control/'prospective_operator1'
destination.mkdir(mode=0o700,parents=True,exist_ok=False)
sys.path.insert(0,str(runtime/'source'))
from gpu import orch_r159_matched_evaluation as evaluator
for name,encoded in files.items():
    raw = base64.b64decode(encoded,validate=True)
    with (destination/name).open('xb') as stream:
        stream.write(raw)
    (destination/name).chmod(0o400)
environment = dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(runtime/'source'),
    HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
commands = [('/localhome/local-rohing/v2/venv/bin/python','-B','-m','unittest','discover','-s',str(destination),'-p','test*.py'),
    ('/localhome/local-rohing/v2/venv/bin/python','-B',str(runtime/'receiving_interval_cpu.py'))]
for index,command in enumerate(commands):
    result = subprocess.run(command,cwd=destination,env=environment,stdin=subprocess.DEVNULL,
        capture_output=True,timeout=60)
    with (destination/f'CPU_{index}.log').open('xb') as stream:
        stream.write(result.stdout+result.stderr)
    assert result.returncode == 0
receipt = dict(status='PASS_NO_ENROLLMENT_NO_GPU',operator_tests=8,retained_interval_tests=7,model_calls=0,
    wrapper=evaluator.ref(destination/'admission_wrapper.py'),
    source_files={name:evaluator.ref(destination/name) for name in files},
    runtime_helper_sha256=evaluator.sha(evaluator.__file__),runtime_cpu_gate=evaluator.ref(runtime/'CPU_GATE.json'),
    observed_unix=time.time(),hard_end_unix=1789646400,latest_dispatch_strictly_before_unix=1789642785,
    old_wrappers_unchanged_and_expired=True,dispatch_requires_new_Main_GO=True,
    required_outer_launcher_checks=['new exclusive once marker','exact Main GO/config pins',
        'selected key unreserved and attempt-free','own previous slot terminal and exact identities gone',
        'record INITIATOR identity then detach transport','full fresh unchanged admission by wrapper'])
evaluator.write(control/'PROSPECTIVE_OPERATOR_CPU_GATE.json',receipt)
preparation = evaluator.read(control/'PREPARATION_RECEIPT.json')
contents = {}
for key,reference in preparation['configurations'].items():
    raw = Path(reference['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == reference['sha256']
    contents[key+'.EXECUTION.proposed.json'] = base64.b64encode(raw).decode()
for name in ('BUILDER.json','NODE2_AUTHORITY.proposed.json','SCHEDULE.proposed.json','PROSPECTIVE_OPERATOR_CPU_GATE.json'):
    contents[name] = base64.b64encode((control/name).read_bytes()).decode()
assert evaluator.ledger_status(root,evaluator.ORIGINAL_PLAN_SHA256) == preparation['ledger']
print(json.dumps(dict(operator_gate=evaluator.ref(control/'PROSPECTIVE_OPERATOR_CPU_GATE.json'),
    receipt=receipt,configuration_metadata=contents),sort_keys=True))
'''.replace('FILES',repr(files),1)
with (directory/'OPERATOR_STAGE.stderr').open('xb') as errors:
    result = subprocess.run(['bash',str(repository/'gpu/ovx_ssh.sh'),'/localhome/local-rohing/v2/venv/bin/python -B -'],
        input=program.encode(),stdout=subprocess.PIPE,stderr=errors,timeout=180,check=True)
metadata = json.loads(result.stdout)
configs = directory/'configs'
configs.mkdir(mode=0o700,exist_ok=False)
for name,encoded in metadata.pop('configuration_metadata').items():
    assert Path(name).name == name
    with (configs/name).open('xb') as output:
        output.write(base64.b64decode(encoded,validate=True))
with (directory/'OPERATOR_GATE_RECEIPT.json').open('x') as output:
    json.dump(metadata,output,sort_keys=True,indent=2)
    output.write('\n')
print(json.dumps(metadata,sort_keys=True))
