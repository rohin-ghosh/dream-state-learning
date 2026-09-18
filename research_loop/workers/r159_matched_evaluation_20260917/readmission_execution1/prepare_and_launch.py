import base64
import hashlib
import json
from pathlib import Path
import subprocess


DIRECTORY = Path(__file__).resolve().parent
WORKER = DIRECTORY.parent
REPOSITORY = WORKER.parents[2]


def main():
    go = (WORKER / 'frozen_readmission_proposal1/parented_frozen.MAIN_GO.json').read_bytes()
    expected = 'b78ec5f14448e3518e603940151a3f6cdcd2124ae557291e51551c4ad63c5ebe'
    assert hashlib.sha256(go).hexdigest() == expected
    files = {name: base64.b64encode((DIRECTORY / name).read_bytes()).decode()
             for name in ('admission_wrapper.py', 'test_admission_wrapper.py')}
    payload = dict(go=base64.b64encode(go).decode(), expected=expected, files=files)
    program = '''
import base64, hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path
payload = PAYLOAD
root = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
source = root/'preparation/runtime_generation3/source'
original = root/'control/candidate5_initial3_runtime3'
old_operator = root/'control/initial3_execution_generation1'
destination = root/'control/frozen_readmission_generation2'
operator = destination/'operator1'
assert socket.gethostname() == '[REDACTED_HOST]' and time.time() < 1789628385
sys.path.insert(0, str(source))
from gpu import orch_r159_matched_evaluation as evaluator
from gpu import orch_r130_benchmark_sidecar as sidecar
assert evaluator.sha(evaluator.__file__) == '100e952409e9e76eb143db2d8f5a504ea8120593e52f85b56f19b07fd7d0bafc'
def write(path, value):
    evaluator.write(path, value)
def raw_write(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
    path.chmod(0o400)
old = {}
for arm in ('parented_frozen', 'unparented_learning'):
    assert not (root/'ledger'/f'{arm}_0.RESERVED.json').exists()
    assert not (root/'attempts'/f'{arm}_0').exists()
    assert sidecar.gone(evaluator.read(old_operator/f'{arm}.DISPATCH_LAUNCH.json')['identity'])
    assert evaluator.sha(old_operator/f'{arm}.dispatch.private.log') == 'bd1f76e9d27ed73296518c1b62a0daa2509117bb77f328e7de6ab30021c1737a'
    old[arm] = dict(once=evaluator.ref(old_operator/f'{arm}.DISPATCH_ONCE.json'),
        refusal=evaluator.ref(old_operator/f'{arm}.dispatch.private.log'),
        go=evaluator.ref(original/f'{arm}.MAIN_GO.json'))
proposal_dir = root/'control/unparented_readmission_generation2'
proposal_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
proposed_path = proposal_dir/'unparented_learning.EXECUTION.proposed.json'
raw_write(proposed_path, (original/proposed_path.name).read_bytes())
proposed = evaluator.read(proposed_path)
evaluator.validate_sources(proposed)
evaluator.candidate_check(proposed, evaluator.validate_plan(proposed['campaign']))
proposal = dict(status='PROPOSAL_ONLY_NEW_MAIN_GO_REQUIRED', execution=evaluator.ref(proposed_path),
    physical=0, preserved_original=old['unparented_learning'], observed_unix=time.time(),
    reserved=False, samples_exist=False, old_GO_retry_forbidden=True, full_fresh_admission_required=True,
    serial_release_required=True, hard_end_unix=1789632000, latest_dispatch_strictly_before_unix=1789628385,
    call_cap=672, checkpoint_cap=12, runtime_generation=3, source_changed=False, GPU_started=False)
write(proposal_dir/'PROPOSAL.json', proposal)
operator.mkdir(mode=0o700, parents=True, exist_ok=False)
for name, encoded in payload['files'].items():
    raw_write(operator/name, base64.b64decode(encoded, validate=True))
go_path = destination/'parented_frozen.MAIN_GO.json'
raw = base64.b64decode(payload['go'], validate=True)
assert hashlib.sha256(raw).hexdigest() == payload['expected']
raw_write(go_path, raw)
assert evaluator.sha(go_path) == payload['expected']
config_path = destination/'parented_frozen.EXECUTION.proposed.json'
assert evaluator.sha(config_path) == '9acfb726c120f81102cfd95fb61704aa4b948d11809690d2faa5b73ebaf2d24e'
config = evaluator.read(config_path)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
    PYTHONPATH=str(source), R159_MAIN_GO_SHA256=payload['expected'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
test = subprocess.run([config['python'], '-B', '-m', 'unittest', 'discover', '-s', str(operator), '-p', 'test*.py'],
    cwd=operator, env=environment, stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
assert test.returncode == 0
write(operator/'CPU_GATE.json', dict(status='PASS', tests=3, model_calls=0, source_changed=False,
    wrapper=evaluator.ref(operator/'admission_wrapper.py'), tests_source=evaluator.ref(operator/'test_admission_wrapper.py'),
    observed_unix=time.time()))
with (operator/'VALIDATION.private.log').open('x') as errors:
    result = subprocess.run([config['python'], '-B', '-m', 'gpu.orch_r159_matched_evaluation', 'validate',
        '--config', str(config_path), '--go', str(go_path)], cwd=source, env=environment,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=errors, timeout=120)
metadata = json.loads(result.stdout)
write(operator/'VALIDATION.json', dict(returncode=result.returncode, result=metadata, observed_unix=time.time()))
assert result.returncode == 0 and metadata['status'] == 'PASS_NO_GPU'
for arm, references in old.items():
    for reference in references.values():
        assert evaluator.ref(reference['path']) == reference
    assert not (root/'ledger'/f'{arm}_0.RESERVED.json').exists()
    assert not (root/'attempts'/f'{arm}_0').exists()
assert time.time() < 1789628380
write(operator/'INITIATOR.json', dict(identity=sidecar.identity(os.getpid()), observed_unix=time.time()))
write(operator/'DISPATCH_ONCE.json', dict(execution=evaluator.ref(config_path), main_go=evaluator.ref(go_path),
    preserved_original=old['parented_frozen'], retry_allowed=False, observed_unix=time.time()))
with (operator/'dispatch.private.log').open('x') as log:
    process = subprocess.Popen([config['python'], '-B', str(operator/'admission_wrapper.py'),
        '--source', str(source), '--config', str(config_path), '--go', str(go_path), '--operator', str(operator)],
        cwd=operator, env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
        start_new_session=True, close_fds=True)
launch = dict(status='DETACHED_ONCE_WRAPPER_SPAWNED_NOT_ADMISSION', identity=sidecar.identity(process.pid),
    execution=evaluator.ref(config_path), main_go=evaluator.ref(go_path), cpu_gate=evaluator.ref(operator/'CPU_GATE.json'),
    operator=str(operator), observed_unix=time.time(), delayed_seconds=5, original_preserved=old,
    ledger=evaluator.ledger_status(root, evaluator.ORIGINAL_PLAN_SHA256), unparented_proposal=proposal)
write(operator/'DISPATCH_LAUNCH.json', launch)
print(json.dumps(launch, sort_keys=True))
'''.replace('PAYLOAD', repr(payload), 1)
    with (DIRECTORY / 'LAUNCH.stderr').open('xb') as errors:
        result = subprocess.run(['bash', str(REPOSITORY / 'gpu/ovx_ssh.sh'),
            '/localhome/local-rohing/v2/venv/bin/python -B -'], input=program.encode(),
            stdout=subprocess.PIPE, stderr=errors, timeout=240, check=True)
    with (DIRECTORY / 'LAUNCH.json').open('xb') as stream:
        stream.write(result.stdout)
    print(result.stdout.decode())


if __name__ == '__main__':
    main()
