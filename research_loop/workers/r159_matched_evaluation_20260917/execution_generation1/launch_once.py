import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys


DIRECTORY = Path(__file__).resolve().parent
WORKER = DIRECTORY.parent
REPOSITORY = WORKER.parents[2]
EXPECTED = dict(parented_learning='e5b7527d19f5194566238baa3c9f395980336f0f8b020d78877ab06161055194',
    parented_frozen='c258de3c57418ac986f11d469ec3aecb5aa9e237294e959f8ea9f5cc343d27f7',
    unparented_learning='7a6b063f295d2426ddc10cff5999fc8fb868413a99d2081f3cd6e686fe1c6e6c')


def main():
    phase = sys.argv[1]
    assert phase in ('first', 'third')
    payload = dict(phase=phase, expected=EXPECTED, go={})
    for arm, checksum in EXPECTED.items():
        raw = (WORKER / f'initial3_generation1/{arm}.MAIN_GO.json').read_bytes()
        assert hashlib.sha256(raw).hexdigest() == checksum
        payload['go'][arm] = base64.b64encode(raw).decode()
    program = '''
import base64, hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path
payload = PAYLOAD
root = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
source = root/'preparation/runtime_generation3/source'
control = root/'control/candidate5_initial3_runtime3'
execution = root/'control/initial3_execution_generation1'
assert socket.gethostname() == '[REDACTED_HOST]'
assert time.time() < 1789628385
sys.path.insert(0, str(source))
from gpu import orch_r159_matched_evaluation as evaluator
from gpu import orch_r130_benchmark_sidecar as sidecar
assert evaluator.sha(evaluator.__file__) == '100e952409e9e76eb143db2d8f5a504ea8120593e52f85b56f19b07fd7d0bafc'
if payload['phase'] == 'first':
    execution.mkdir(mode=0o700, parents=True, exist_ok=False)
else:
    assert execution.is_dir()
def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\\n')
    path.chmod(0o400)
configs = {}
for arm, encoded in payload['go'].items():
    path = control/f'{arm}.MAIN_GO.json'
    raw = base64.b64decode(encoded, validate=True)
    assert hashlib.sha256(raw).hexdigest() == payload['expected'][arm]
    if path.exists():
        assert path.read_bytes() == raw
    else:
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o400)
    go = json.loads(raw)
    config_path = Path(go['execution']['path'])
    assert evaluator.ref(config_path) == go['execution']
    config = evaluator.read(config_path)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source), R159_MAIN_GO_SHA256=payload['expected'][arm],
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    configs[arm] = (config_path, config, path, environment)
arms = ('parented_learning','parented_frozen') if payload['phase'] == 'first' else ('unparented_learning',)
if payload['phase'] == 'third':
    claim = root/'ledger/parented_learning_0.RESERVED.json'
    terminal = evaluator.read(root/'ledger/parented_learning_0.COMPLETE.json')
    assert terminal['reservation_sha256'] == evaluator.sha(claim)
    predecessor = evaluator.read(execution/'parented_learning.DISPATCH_LAUNCH.json')
    assert sidecar.gone(predecessor['identity'])
    timeout_launch = evaluator.read(root/'attempts/parented_learning_0/LAUNCH.json')
    assert sidecar.gone(timeout_launch['identity'])
    assert time.time() < 1789628385
    config = configs['unparented_learning'][1]
    report = sidecar.scan(config)
    assert report['clear'] and not report['blocking_reasons']
    write(execution/'THIRD_RELEASE_CHECK.json', dict(status='PREDECESSOR_COMPLETE_IDENTITIES_GONE_FRESH_SCAN_CLEAR',
        predecessor_completion=evaluator.ref(root/'ledger/parented_learning_0.COMPLETE.json'),
        observed_unix=time.time(), scanner_euid=report['scanner_euid'], gpu_uuid=report['gpu']['uuid']))
validations = {}
for arm in arms:
    config_path, config, go_path, environment = configs[arm]
    with (execution/f'{arm}.VALIDATION.private.log').open('x') as errors:
        result = subprocess.run([config['python'], '-B', '-m', 'gpu.orch_r159_matched_evaluation',
            'validate', '--config', str(config_path), '--go', str(go_path)], cwd=source, env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=errors, timeout=120)
    metadata = json.loads(result.stdout)
    write(execution/f'{arm}.VALIDATION.json', dict(returncode=result.returncode, result=metadata,
        execution=evaluator.ref(config_path), main_go=evaluator.ref(go_path), observed_unix=time.time()))
    assert result.returncode == 0 and metadata['status'] == 'PASS_NO_GPU'
    validations[arm] = metadata['status']
launched = {}
for arm in arms:
    config_path, config, go_path, environment = configs[arm]
    assert time.time() < 1789628385
    write(execution/f'{arm}.DISPATCH_ONCE.json', dict(schema='R159_OPERATOR_DISPATCH_ONCE_V1',
        execution=evaluator.ref(config_path), main_go=evaluator.ref(go_path), observed_unix=time.time(), retry_allowed=False))
    with (execution/f'{arm}.dispatch.private.log').open('x') as log:
        process = subprocess.Popen([config['python'], '-B', '-m', 'gpu.orch_r159_matched_evaluation',
            'dispatch', '--config', str(config_path), '--go', str(go_path)], cwd=source, env=environment,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    identity = sidecar.identity(process.pid)
    receipt = dict(identity=identity, execution=evaluator.ref(config_path), main_go=evaluator.ref(go_path),
        observed_unix=time.time(), physical=config['physical'], gpu_uuid=config['gpu_uuid'])
    write(execution/f'{arm}.DISPATCH_LAUNCH.json', receipt)
    launched[arm] = receipt
print(json.dumps(dict(status='ONCE_DISPATCH_PROCESSES_SPAWNED_NOT_COMPLETION', validations=validations,
    launches=launched, phase=payload['phase'], observed_unix=time.time()), sort_keys=True))
'''.replace('PAYLOAD', repr(payload), 1)
    with (DIRECTORY / f'{phase}.LAUNCH.stderr').open('xb') as errors:
        result = subprocess.run(['bash', str(REPOSITORY / 'gpu/ovx_ssh.sh'),
            '/localhome/local-rohing/v2/venv/bin/python -B -'], input=program.encode(),
            stdout=subprocess.PIPE, stderr=errors, check=True, timeout=200)
    with (DIRECTORY / f'{phase}.LAUNCH.json').open('xb') as stream:
        stream.write(result.stdout)
    print(result.stdout.decode())


if __name__ == '__main__':
    main()
