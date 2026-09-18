"""Exercise actual successor confinement without importing a GPU model."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
import uuid


ATTEMPTS = {'pilot': 4, 'run1': 3, 'C1': 2, 'C3': 2, 'C4': 2, 'repo_reader': 2}


def load_operator(root):
    spec = importlib.util.spec_from_file_location('r179_bound_operator', root / 'rollout_operator.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(root, unit):
    operator = load_operator(root)
    config, plan = operator.read(root / 'GUARD.json'), operator.read(root / 'PLAN.json')
    config['device_containment']['unit'] = unit
    sys.path.insert(0, plan['source_root'])
    if plan['physical'] == 7:
        if not operator.namespace_matches(operator.read(root / 'INPUT.json')):
            raise ValueError('reader_private_mount_not_exact')
        capsule = operator.load_auxiliary('reader_capsule.py')
        capsule.DEVICES = {7: plan['gpu_uuid']}
        proof = capsule.verify_device_containment(config, plan)
    else:
        proof = operator.unchanged_containment_check(config, plan)
    if 'torch' in sys.modules:
        raise ValueError('device_only_probe_must_not_import_torch')
    return dict(status='PASS', operator_sha256=operator.sha(root / 'rollout_operator.py'),
        guard_sha256=operator.sha(root / 'GUARD.json'), proof=proof,
        torch_imported=False, model_loaded=False, observed_unix=time.time())


def remote(source):
    rows = []
    for label, attempt in ATTEMPTS.items():
        root = Path('/localhome/local-rohing') / f'orch_r179_context_{label}_20260917_attempt{attempt}'
        row = dict(label=label, output=str(root), returncode=None)
        try:
            operator = load_operator(root)
            config, plan = operator.read(root / 'GUARD.json'), operator.read(root / 'PLAN.json')
            copied = deepcopy(config)
            unit = ('orch-r136-native-' + uuid.uuid4().hex if plan['physical'] == 7 else
                    config['device_containment']['unit'] + '-cpu-proof-' + str(time.time_ns()))
            copied['device_containment']['unit'] = unit
            saved = operator.load_auxiliary('saved_primitives.py') if plan['physical'] not in (2, 6, 7) else None
            command = operator.strict_command(saved, copied, plan, root)
            suffix = [str(operator.PYTHON), '-B', str(root / 'rollout_operator.py'), 'contained', '--output', str(root)]
            if command[-len(suffix):] != suffix:
                raise ValueError('exact_successor_entrypoint_before_CPU_only_replacement')
            command = command[:-len(suffix)] + [str(operator.PYTHON), '-B', '-c', source, '--check', str(root), unit]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=45)
            row['returncode'] = completed.returncode
            if completed.returncode == 0:
                row['result'] = json.loads(completed.stdout)
            else:
                row['error'] = completed.stderr[-2000:]
        except Exception as error:
            row.update(error_type=type(error).__name__, error=str(error))
        rows.append(row)
    return rows


def main():
    if '--capture' in sys.argv:
        position = sys.argv.index('--capture')
        label, attempt = sys.argv[position + 1:position + 3]
        ATTEMPTS.clear()
        ATTEMPTS[label] = int(attempt)
        rows = remote(Path(__file__).read_text())
        row = rows[0]
        if row['returncode'] != 0 or row.get('result', {}).get('status') != 'PASS':
            raise ValueError('receiving_CPU_device_proof_failed_' + str(row))
        operator = load_operator(Path(row['output']))
        path = Path(row['output']) / 'DEVICE_CPU.json'
        operator.write(path, row['result'])
        print(json.dumps(operator.reference(path), sort_keys=True))
        return
    if '--check' in sys.argv:
        position = sys.argv.index('--check')
        print(json.dumps(check(Path(sys.argv[position + 1]), sys.argv[position + 2]), sort_keys=True))
        return
    if '--remote' in sys.argv:
        source = sys.stdin.read()
        print(json.dumps(remote(source), sort_keys=True))
        return
    source = Path(__file__).read_text()
    command = '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(source) + ' --remote'
    completed = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', command], input=source,
                               capture_output=True, text=True, timeout=300)
    if completed.returncode:
        detail = completed.stderr.strip().splitlines()[-1:]
        raise RuntimeError('device_proof_wrapper_failure: ' + ' '.join(detail))
    rows = json.loads(completed.stdout)
    path = Path(__file__).parent / f'RECEIVING_DEVICE_PROOF_{time.time_ns()}.json'
    with path.open('x') as handle:
        json.dump(dict(probe_sha256=hashlib.sha256(source.encode()).hexdigest(), rows=rows), handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(path)
    for row in rows:
        print(row['label'], row['returncode'], row.get('result', {}).get('status'), row.get('error', ''))


if __name__ == '__main__':
    main()
