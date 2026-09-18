"""Create-only actual-source R179 candidates. No learner or device actions."""

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
POLICY_SHA = 'b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b'
NATIVE = 'gpu/orch_r125_continual_native.py'
POLICY = 'gpu/orch_r179_context_survival.py'
SCOPE_SHA = '85441db890036947f6bc242e66ef15db750a683d73fe02d06778ebe996d4fb54'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path == path.resolve()
            and not any(part.is_symlink() for part in (path, *path.parents)), 'canonical_no_symlinks')
    return path


def sha(path):
    return hashlib.sha256(canonical(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


def read_ref(reference):
    require(set(reference) == {'path', 'sha256'} and sha(reference['path']) == reference['sha256'], 'bound_reference')
    return json.loads(Path(reference['path']).read_text())


def pins(source):
    return {str(path.relative_to(source)): sha(path) for path in sorted(source.rglob('*.py'))}


def stage(physical):
    require(socket.gethostname() == '[REDACTED_HOST]', 'node3_only')
    require(sha(HERE / 'BUILDER_SCOPE.json') == SCOPE_SHA and sha(HERE / 'POLICY.py') == POLICY_SHA,
            'Main_bound_policy_scope')
    seed = json.loads((HERE / 'SEED.json').read_text())
    lane = next(row for row in seed['lanes'] if row['physical'] == physical)
    config = read_ref(lane['guard_ref'])
    plan = read_ref(lane['plan_ref'])
    require(config['plan_path'] == lane['plan_ref']['path'] and config['plan_sha256'] == lane['plan_ref']['sha256'],
            'actual_plan_binding')
    require(plan['source_root'] == lane['source_root'] and plan['root'] == lane['life_root']
            and plan['physical'] == physical and plan['gpu_uuid'] == lane['gpu_uuid'], 'exact_actual_lane')
    require(plan['hard_end_unix'] > time.time() and not plan.get('authorized_wall_extension')
            and not plan.get('preupdate_recovery'), 'unchanged_live_wall')
    original = canonical(plan['source_root'])
    original_pins = pins(original)
    require(original_pins == config['source_pins'] and POLICY not in original_pins, 'complete_original_census')
    require(original_pins[NATIVE] == lane['source_census']['native']['sha256'], 'actual_native_cohort')
    target = ROOT / ('physical' + str(physical))
    target.mkdir()
    destination = target / 'source'
    destination.mkdir()
    for relative, checksum in original_pins.items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'relative_source_pin')
        raw = (original / relative).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == checksum, 'stable_original_copy')
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
    sys.path.insert(0, str(original))
    spec = importlib.util.spec_from_file_location('r179_bound_policy', HERE / 'POLICY.py')
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    before = (original / NATIVE).read_text()
    after = policy.patch_native(before)
    (destination / NATIVE).write_text(after)
    with (destination / POLICY).open('xb') as stream:
        stream.write((HERE / 'POLICY.py').read_bytes())
    expected = dict(original_pins, **{NATIVE: sha(destination / NATIVE), POLICY: POLICY_SHA})
    require(pins(destination) == expected and pins(original) == original_pins, 'only_exact_native_policy_delta')
    new_plan = deepcopy(plan)
    new_plan['source_root'] = str(destination)
    if plan.get('startup_context'):
        startup = canonical(plan['startup_context']['path'])
        relative = startup.relative_to(original)
        require(sha(startup) == plan['startup_context']['sha256'], 'startup_source_hash')
        copied = destination / relative
        copied.parent.mkdir(parents=True, exist_ok=True)
        with copied.open('xb') as stream:
            stream.write(startup.read_bytes())
        new_plan['startup_context']['path'] = str(copied)
    write(target / 'PLAN.json', new_plan)
    allocation = json.loads(canonical(config['allocation_path']).read_text())
    require(sha(config['allocation_path']) == config['allocation_sha256'], 'original_allocation')
    write(target / 'ALLOCATION.json', dict(allocation, plan_sha256=sha(target / 'PLAN.json')))
    proposed = deepcopy(config)
    proposed.update(plan_path=str(target / 'PLAN.json'), plan_sha256=sha(target / 'PLAN.json'),
                    source_pins=expected, allocation_path=str(target / 'ALLOCATION.json'),
                    allocation_sha256=sha(target / 'ALLOCATION.json'))
    write(target / 'PROPOSED_GUARD.json', proposed)
    for path in destination.rglob('*'):
        if path.is_file():
            path.chmod(0o444)
    receipt = dict(status='SOURCE_STAGED_CPU_PENDING', physical=physical, source=str(destination),
        old_guard_ref=lane['guard_ref'], old_plan_ref=lane['plan_ref'], policy_sha256=POLICY_SHA,
        old_python_count=len(original_pins), new_python_count=len(expected),
        changed=[NATIVE], added=[POLICY], startup_unchanged=True, original_source_unchanged=True,
        plan_sha256=sha(target / 'PLAN.json'), guard_sha256=sha(target / 'PROPOSED_GUARD.json'),
        source_manifest_sha256=hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest(),
        native_ast_compiles=bool(ast.parse(after)), observed_unix=time.time(), signals_sent=0,
        model_calls=0, no_readout_output=True)
    write(target / 'STAGED_SOURCE.json', receipt)
    command = [sys.executable, '-I', '-B', str(HERE / 'receiving_policy.py'), str(destination)]
    with (target / 'CPU_POLICY.log').open('x') as log:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            timeout=90, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', TMPDIR='/tmp'))
    cpu = dict(status='PASS' if result.returncode == 0 else 'FAILED_NO_RETRY', returncode=result.returncode,
        source_manifest_sha256=receipt['source_manifest_sha256'], policy_sha256=POLICY_SHA,
        test_sha256=sha(HERE / 'receiving_policy.py'), log_sha256=sha(target / 'CPU_POLICY.log'),
        immutable_after_cpu=pins(destination) == expected, signals_sent=0, model_calls=0, observed_unix=time.time())
    write(target / 'CPU_POLICY.json', cpu)
    require(cpu['status'] == 'PASS' and cpu['immutable_after_cpu'], 'actual_source_receiving_CPU')
    return dict(source=receipt, cpu=cpu)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(0, 1, 2, 3, 4, 7), required=True)
    arguments = parser.parse_args()
    print(json.dumps(stage(arguments.physical), sort_keys=True))
