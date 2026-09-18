import base64
import hashlib
import json
from pathlib import Path
import subprocess


DIRECTORY = Path(__file__).resolve().parent
REPOSITORY = DIRECTORY.parents[3]
FILES = ('gpu/orch_r159_matched_evaluation.py', 'tests/test_orch_r159_matched_evaluation.py')


def main():
    payload = dict(files={name: base64.b64encode((REPOSITORY / name).read_bytes()).decode() for name in FILES},
        receiving_cpu=base64.b64encode((DIRECTORY / 'receiving_interval_cpu.py').read_bytes()).decode(),
        cpu_log_sha256=hashlib.sha256((DIRECTORY / 'CPU_TESTS.log').read_bytes()).hexdigest())
    program = '''
import base64, hashlib, json, os, shutil, socket, subprocess, sys, time
from pathlib import Path
payload = PAYLOAD
assert socket.gethostname() == '[REDACTED_HOST]'
base = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1/preparation')
old, new = base/'runtime_generation2', base/'runtime_generation3'
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):
    return dict(path=str(path), sha256=sha(path))
def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\\n')
    path.chmod(0o400)
assert sha(old/'SOURCE_MANIFEST.json') == 'a7f09b623ea9d270f9af70de38b299c2c80f516eae4bbafbab9ba0822f1d0200'
prior = json.loads((old/'SOURCE_MANIFEST.json').read_bytes())
assert all(sha(old/'source'/name) == checksum for name, checksum in prior['sources'].items())
plan_hash = 'c2f32b5390f4d9a06ab30de1cd64eb91858055ca4944c6328edbad52125fed86'
freeze = base/'generation2/sealed/FREEZE.json'
assert sha(old/'PLAN.json') == plan_hash
assert sha(freeze) == '1515341fd0c8d1336cbea6728aa5ba3c27c638752964575affda2400002c81b6'
new.mkdir(mode=0o700, exist_ok=False)
shutil.copytree(old/'source', new/'source', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
for name, encoded in payload['files'].items():
    destination = new/'source'/name
    destination.chmod(0o600)
    destination.write_bytes(base64.b64decode(encoded, validate=True))
    destination.chmod(0o400)
sources = {name: sha(new/'source'/name) for name in prior['sources']}
changes = sorted(name for name in sources if sources[name] != prior['sources'][name])
assert changes == sorted(payload['files'])
assert all(sha(old/'source'/name) == checksum for name, checksum in prior['sources'].items())
write(new/'SOURCE_MANIFEST.json', dict(source_root=str(new/'source'), sources=sources,
    predecessor=ref(old/'SOURCE_MANIFEST.json'), predecessor_unchanged=True, changed_files=changes))
with (new/'PLAN.json').open('xb') as stream:
    stream.write((old/'PLAN.json').read_bytes())
(new/'PLAN.json').chmod(0o400)
with (new/'receiving_interval_cpu.py').open('xb') as stream:
    stream.write(base64.b64decode(payload['receiving_cpu'], validate=True))
(new/'receiving_interval_cpu.py').chmod(0o400)
environment = dict(os.environ, PYTHONPATH=str(new/'source'), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
python = '/localhome/local-rohing/v2/venv/bin/python'
with (new/'RECEIVING_INTERVAL_CPU.stderr').open('x') as errors:
    completed = subprocess.run([python, '-B', str(new/'receiving_interval_cpu.py')], env=environment,
        capture_output=False, stdout=subprocess.PIPE, stderr=errors, check=True, timeout=60)
interval = json.loads(completed.stdout)
assert interval['status'] == 'PASS' and interval['helper_sha256'] == sources['gpu/orch_r159_matched_evaluation.py']
write(new/'RECEIVING_INTERVAL_CPU.json', interval)
with (new/'INSTALLED_GYM_CPU.stderr').open('x') as errors:
    completed = subprocess.run([python, '-B', '-m', 'gpu.orch_r159_matched_evaluation', 'gym-selftest',
        '--freeze', str(freeze), '--output', str(new/'installed_gym_CPU')], env=environment,
        stdout=subprocess.PIPE, stderr=errors, check=True, timeout=120)
gym = json.loads(completed.stdout)
assert gym['status'] == 'PASS' and gym['model_calls'] == 0 and gym['checkpoints_enrolled'] == 0
write(new/'INSTALLED_GYM_CPU.json', gym)
assert sha(old/'PLAN.json') == sha(new/'PLAN.json') == plan_hash
assert sha(freeze) == '1515341fd0c8d1336cbea6728aa5ba3c27c638752964575affda2400002c81b6'
assert all(sha(old/'source'/name) == checksum for name, checksum in prior['sources'].items())
gate = dict(status='PASS', helper_sha256=sources['gpu/orch_r159_matched_evaluation.py'],
    test_sha256=sources['tests/test_orch_r159_matched_evaluation.py'], tests_passed=383, r159_tests_passed=140,
    log_sha256=payload['cpu_log_sha256'], receiving_interval_tests=7,
    receiving_interval_receipt=ref(new/'RECEIVING_INTERVAL_CPU.json'),
    installed_gym_receipt_sha256=sha(new/'INSTALLED_GYM_CPU.json'),
    created_unix=time.time(), GPU_authorization=False, repair='non_material_witnessed_interval_custody')
write(new/'CPU_GATE.json', gate)
metadata = dict(status='INTERVAL_REPAIR_STAGED_NO_ENROLLMENT', source_root=str(new/'source'),
    source_manifest=ref(new/'SOURCE_MANIFEST.json'), cpu_gate=ref(new/'CPU_GATE.json'), plan=ref(new/'PLAN.json'),
    helper_sha256=gate['helper_sha256'], test_sha256=gate['test_sha256'],
    predecessor_unchanged=True, changed_files=changes, freeze=ref(freeze),
    model_calls=0, checkpoints_enrolled=0, created_unix=time.time())
write(new/'REPAIR_METADATA.json', metadata)
print(json.dumps(dict(metadata=metadata, source_manifest=json.loads((new/'SOURCE_MANIFEST.json').read_bytes()),
    cpu_gate=gate, receiving_interval=interval, installed_gym=gym), sort_keys=True))
'''.replace('PAYLOAD', repr(payload), 1)
    with (DIRECTORY / 'STAGING.stderr').open('xb') as errors:
        completed = subprocess.run(['bash', str(REPOSITORY / 'gpu/ovx_ssh.sh'),
            '/localhome/local-rohing/v2/venv/bin/python -B -'], input=program.encode(),
            stdout=subprocess.PIPE, stderr=errors, check=True, timeout=200)
    with (DIRECTORY / 'STAGING_RETURN.json').open('xb') as stream:
        stream.write(completed.stdout)
    result = json.loads(completed.stdout)
    for key, name in (('metadata', 'REPAIR_METADATA.json'), ('source_manifest', 'SOURCE_MANIFEST.json'),
            ('cpu_gate', 'CPU_GATE.json'), ('receiving_interval', 'RECEIVING_INTERVAL_CPU.json'),
            ('installed_gym', 'INSTALLED_GYM_CPU.json')):
        with (DIRECTORY / name).open('x') as stream:
            json.dump(result[key], stream, sort_keys=True, indent=2)
            stream.write('\n')
    print(json.dumps(result['metadata'], sort_keys=True))


if __name__ == '__main__':
    main()
