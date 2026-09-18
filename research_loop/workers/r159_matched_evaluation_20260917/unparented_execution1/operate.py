import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


DIRECTORY = Path(__file__).resolve().parent
WORKER = DIRECTORY.parent
REPOSITORY = WORKER.parents[2]
GO_SHA = 'cc958ea3109e01be5dd2745c847ab75c6e0a913955e6702317714569ec6d9f6f'
CONFIG_SHA = 'ab43c8725d027826b15e3a1db8b595ef70ea4fd81e032167f352184fabfa80a0'


def main():
    phase = sys.argv[1]
    assert phase in ('stage', 'observe', 'dispatch')
    go = (WORKER / 'unparented_readmission_proposal1/unparented_learning.MAIN_GO.json').read_bytes()
    assert hashlib.sha256(go).hexdigest() == GO_SHA
    files = {name: base64.b64encode((WORKER / 'readmission_execution1' / name).read_bytes()).decode()
             for name in ('admission_wrapper.py', 'test_admission_wrapper.py')}
    assert hashlib.sha256(base64.b64decode(files['admission_wrapper.py'])).hexdigest() == '660cffb87678615732e96dfc7ccaac367b152bcc2435d35a3096eef4efaea96f'
    payload = dict(phase=phase, go=base64.b64encode(go).decode(), go_sha=GO_SHA,
                   config_sha=CONFIG_SHA, files=files)
    program = '''
import base64, hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path
payload = PAYLOAD
root = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
source = root/'preparation/runtime_generation3/source'
destination = root/'control/unparented_readmission_generation2'
operator = destination/'operator1'
frozen_operator = root/'control/frozen_readmission_generation2/operator1'
frozen_config = frozen_operator.parent/'parented_frozen.EXECUTION.proposed.json'
config_path = destination/'unparented_learning.EXECUTION.proposed.json'
go_path = destination/'unparented_learning.MAIN_GO.json'
assert socket.gethostname() == '[REDACTED_HOST]'
sys.path.insert(0, str(source))
from gpu import orch_r159_matched_evaluation as evaluator
from gpu import orch_r130_benchmark_sidecar as sidecar
assert evaluator.sha(evaluator.__file__) == '100e952409e9e76eb143db2d8f5a504ea8120593e52f85b56f19b07fd7d0bafc'
assert evaluator.sha(config_path) == payload['config_sha']
config = evaluator.read(config_path)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
    PYTHONPATH=str(source), R159_MAIN_GO_SHA256=payload['go_sha'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
def write(path, value):
    evaluator.write(path, value)
def raw_write(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
    path.chmod(0o400)
def validate(label):
    with (operator/(label+'.private.log')).open('x') as errors:
        result = subprocess.run([config['python'], '-B', '-m', 'gpu.orch_r159_matched_evaluation', 'validate',
            '--config', str(config_path), '--go', str(go_path)], cwd=source, env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=errors, timeout=120)
    metadata = json.loads(result.stdout)
    write(operator/(label+'.json'), dict(returncode=result.returncode, result=metadata, observed_unix=time.time()))
    assert result.returncode == 0 and metadata['status'] == 'PASS_NO_GPU'
def originals():
    original = root/'control/candidate5_initial3_runtime3/unparented_learning.MAIN_GO.json'
    old_operator = root/'control/initial3_execution_generation1'
    once = old_operator/'unparented_learning.DISPATCH_ONCE.json'
    refusal = old_operator/'unparented_learning.dispatch.private.log'
    assert evaluator.sha(original) == '7a6b063f295d2426ddc10cff5999fc8fb868413a99d2081f3cd6e686fe1c6e6c'
    assert evaluator.sha(once) == 'eb118c66ce09fe0eedbf6d9f980a2c8c029e5b11f27e128b6a2f571f3b620fac'
    assert evaluator.sha(refusal) == 'bd1f76e9d27ed73296518c1b62a0daa2509117bb77f328e7de6ab30021c1737a'
    assert sidecar.gone(evaluator.read(old_operator/'unparented_learning.DISPATCH_LAUNCH.json')['identity'])
    return dict(go=evaluator.ref(original), once=evaluator.ref(once), refusal=evaluator.ref(refusal))
def unreserved():
    assert not any((root/'ledger'/('unparented_learning_0.'+suffix+'.json')).exists()
        for suffix in ('RESERVED','COMPLETE','FAILED'))
    assert not (root/'attempts/unparented_learning_0').exists()
def release_status(identities):
    result = dict(identities_gone={role: sidecar.gone(identity) for role, identity in identities.items()},
        completed=False, failed=(root/'ledger/parented_frozen_0.FAILED.json').exists())
    completion = root/'ledger/parented_frozen_0.COMPLETE.json'
    if completion.is_file():
        terminal = evaluator.read(completion)
        assert terminal['status'] == 'COMPLETE'
        assert terminal['reservation_sha256'] == '4ccc6218a7001e272bead405b7e33b2310838a06f5ce7ced32df77b043825ee2'
        assert evaluator.sha(terminal['completion']['path']) == terminal['completion']['sha256']
        result.update(completed=True, completion=evaluator.ref(completion), completed_unix=terminal['observed_unix'])
    result['released'] = result['completed'] and not result['failed'] and all(result['identities_gone'].values())
    return result
if payload['phase'] == 'stage':
    assert time.time() < 1789628385
    unreserved()
    previous = originals()
    operator.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, encoded in payload['files'].items():
        raw_write(operator/name, base64.b64decode(encoded, validate=True))
    raw = base64.b64decode(payload['go'], validate=True)
    assert hashlib.sha256(raw).hexdigest() == payload['go_sha']
    raw_write(go_path, raw)
    assert evaluator.sha(go_path) == payload['go_sha']
    wrapper = evaluator.read(frozen_operator/'WRAPPER_STARTED.json')['identity']
    timeout = evaluator.read(root/'attempts/parented_frozen_0/LAUNCH.json')['identity']
    native = sidecar.identity(1704196)
    assert native['uid'] == timeout['uid'] == wrapper['uid'] == 2524
    assert native['boot_id'] == timeout['boot_id'] == wrapper['boot_id']
    fields = Path('/proc/1704196/stat').read_text().rsplit(')', 1)[1].split()
    assert int(fields[1]) == timeout['pid']
    arguments = Path('/proc/1704196/cmdline').read_bytes().split(b'\\0')
    assert b'gpu.orch_r159_matched_evaluation' in arguments and b'evaluate' in arguments
    assert arguments[arguments.index(b'--config')+1].decode() == str(frozen_config)
    identities = dict(wrapper=wrapper, timeout=timeout, evaluator=native)
    write(operator/'PREDECESSOR_IDENTITIES.json', dict(identities=identities, observed_unix=time.time(),
        frozen_execution=evaluator.ref(frozen_config)))
    test = subprocess.run([config['python'], '-B', '-m', 'unittest', 'discover', '-s', str(operator), '-p', 'test*.py'],
        cwd=operator, env=environment, stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
    assert test.returncode == 0
    write(operator/'CPU_GATE.json', dict(status='PASS', tests=3, model_calls=0, source_changed=False,
        wrapper=evaluator.ref(operator/'admission_wrapper.py'), tests_source=evaluator.ref(operator/'test_admission_wrapper.py'),
        observed_unix=time.time()))
    validate('STAGE_VALIDATION')
    output = dict(status='STAGED_NO_DISPATCH_WAITING_NATURAL_RELEASE', execution=evaluator.ref(config_path),
        main_go=evaluator.ref(go_path), predecessor_identities=identities, release=release_status(identities),
        original_preserved=previous, cpu_gate=evaluator.ref(operator/'CPU_GATE.json'), observed_unix=time.time())
    write(operator/'STAGED.json', output)
elif payload['phase'] == 'dispatch':
    assert evaluator.sha(go_path) == payload['go_sha']
    gate = evaluator.read(operator/'CPU_GATE.json')
    assert gate['status'] == 'PASS' and gate['tests'] == 3
    for name in ('wrapper', 'tests_source'):
        assert evaluator.ref(gate[name]['path']) == gate[name]
    assert evaluator.sha(operator/'admission_wrapper.py') == '660cffb87678615732e96dfc7ccaac367b152bcc2435d35a3096eef4efaea96f'
    assert time.time() < 1789628380
    unreserved()
    previous = originals()
    predecessor = evaluator.read(operator/'PREDECESSOR_IDENTITIES.json')
    release = release_status(predecessor['identities'])
    assert release['released'], 'natural_frozen_completion_all_exact_identities_gone_required'
    disposition = evaluator.read(frozen_operator/'DISPOSITION.json')
    assert disposition['result']['unresolved'] == 0 and disposition['result']['failed'] == 0
    validate('DISPATCH_VALIDATION')
    release = release_status(predecessor['identities'])
    assert release['released'] and time.time() < 1789628380
    unreserved()
    write(operator/'SERIAL_RELEASE.json', dict(release=release, predecessor=evaluator.ref(operator/'PREDECESSOR_IDENTITIES.json'),
        disposition=evaluator.ref(frozen_operator/'DISPOSITION.json'), observed_unix=time.time()))
    write(operator/'INITIATOR.json', dict(identity=sidecar.identity(os.getpid()), observed_unix=time.time()))
    write(operator/'DISPATCH_ONCE.json', dict(execution=evaluator.ref(config_path), main_go=evaluator.ref(go_path),
        original_preserved=previous, retry_allowed=False, observed_unix=time.time()))
    with (operator/'dispatch.private.log').open('x') as log:
        process = subprocess.Popen([config['python'], '-B', str(operator/'admission_wrapper.py'),
            '--source', str(source), '--config', str(config_path), '--go', str(go_path), '--operator', str(operator)],
            cwd=operator, env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True, close_fds=True)
    output = dict(status='DETACHED_ONCE_WRAPPER_SPAWNED_NOT_ADMISSION', identity=sidecar.identity(process.pid),
        execution=evaluator.ref(config_path), main_go=evaluator.ref(go_path), release=release, observed_unix=time.time())
    write(operator/'DISPATCH_LAUNCH.json', output)
else:
    identities = evaluator.read(operator/'PREDECESSOR_IDENTITIES.json')['identities']
    output = dict(status='METADATA_ONLY', release=release_status(identities), arms={}, held_content_read=False,
        ledger=evaluator.ledger_status(root, evaluator.ORIGINAL_PLAN_SHA256), observed_unix=time.time())
    for arm, current_operator in (('parented_frozen', frozen_operator), ('unparented_learning', operator)):
        metadata = {}
        for name in ('DISPATCH_LAUNCH', 'WRAPPER_STARTED', 'DISPOSITION', 'DISPATCH_ERROR'):
            path = current_operator/(name+'.json')
            if path.is_file():
                metadata[name] = evaluator.read(path)
        if 'WRAPPER_STARTED' in metadata:
            metadata['wrapper_gone'] = sidecar.gone(metadata['WRAPPER_STARTED']['identity'])
        if arm == 'unparented_learning':
            expected_native = dict(pid=1705420, uid=2524, start_ticks='85619609',
                boot_id='8ff7b0dc-fbdf-4945-9044-3dffe94b5407')
            metadata['observed_native_identity'] = expected_native
            metadata['observed_native_gone'] = sidecar.gone(expected_native)
        admission = current_operator/'ACTUAL_ADMISSION.private.json'
        if admission.is_file():
            capture = evaluator.read(admission)
            report = capture['report']
            metadata['admission'] = dict(reference=evaluator.ref(admission), observed_unix=capture['observed_unix'],
                clear=report['clear'], blocking_reasons=report['blocking_reasons'], scanner_euid=report['scanner_euid'], gpu=report['gpu'])
        attempt = root/'attempts'/(arm+'_0')
        if (attempt/'LAUNCH.json').is_file():
            metadata['native_launch'] = evaluator.read(attempt/'LAUNCH.json')
            timeout_identity = metadata['native_launch']['identity']
            metadata['timeout_gone'] = sidecar.gone(timeout_identity)
            metadata['active_native_identities'] = []
            for process_directory in Path('/proc').glob('[0-9]*'):
                try:
                    fields = (process_directory/'stat').read_text().rsplit(')', 1)[1].split()
                    if int(fields[1]) != timeout_identity['pid']:
                        continue
                    arguments = (process_directory/'cmdline').read_bytes().split(b'\\0')
                    if b'gpu.orch_r159_matched_evaluation' not in arguments or b'evaluate' not in arguments:
                        continue
                    if arguments[arguments.index(b'--config')+1].decode() != metadata['native_launch']['execution']['path']:
                        continue
                    metadata['active_native_identities'].append(sidecar.identity(int(process_directory.name)))
                except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, IndexError):
                    continue
        if (attempt/'sealed').is_dir():
            names = [path.name for path in (attempt/'sealed').iterdir()]
            metadata['private_artifact_counts'] = {kind: sum(name.startswith('CALL_') and name.endswith('.'+kind+'.private.json')
                for name in names) for kind in ('RESERVED','RAW','SCORE')}
        for suffix in ('RESERVED','COMPLETE','FAILED'):
            path = root/'ledger'/(arm+'_0.'+suffix+'.json')
            if path.is_file():
                metadata[suffix] = dict(reference=evaluator.ref(path), metadata=evaluator.read(path))
                if suffix == 'COMPLETE':
                    terminal = metadata[suffix]['metadata']
                    assert terminal['reservation_sha256'] == evaluator.sha(root/'ledger'/(arm+'_0.RESERVED.json'))
                    assert evaluator.sha(terminal['completion']['path']) == terminal['completion']['sha256']
        output['arms'][arm] = metadata
    output['gpu_processes'] = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_gpu_memory',
        '--format=csv,noheader,nounits'], text=True, timeout=20).splitlines()
print(json.dumps(output, sort_keys=True))
'''.replace('PAYLOAD', repr(payload), 1)
    label = phase if phase != 'observe' else 'observe_' + str(time.time_ns())
    with (DIRECTORY / (label + '.stderr')).open('xb') as errors:
        result = subprocess.run(['bash', str(REPOSITORY / 'gpu/ovx_ssh.sh'),
            '/localhome/local-rohing/v2/venv/bin/python -B -'], input=program.encode(),
            stdout=subprocess.PIPE, stderr=errors, timeout=200, check=True)
    with (DIRECTORY / (label + '.json')).open('xb') as stream:
        stream.write(result.stdout)
    print(result.stdout.decode())


if __name__ == '__main__':
    main()
