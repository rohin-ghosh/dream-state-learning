"""Stage the existing target-exclusion repair for the failed a40r7 life only."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from gpu.orch_r144_target_patch import patch_source


BASE = Path('/localhome/local-rohing/orch_r136_raw_unparented_none_a40r7_20260916_attempt1')
OLD_SOURCE = BASE/'source_r145_a40r7_20260916t1630z'
OLD_CONTROL = BASE/'control_r145_a40r7_20260916t1630z_readmit1'
OLD_GUARD_SHA256 = '7cc737f65d5e10b62eb11dcd106cfa13d0895025e2d13460840d588303b3f180'
OLD_NATIVE_SHA256 = '3eb3d1ae2e302f4d77c75ede5f7ca667fe2eb18d71878f2232572686355b3082'
PATCHED_NATIVE_SHA256 = 'bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6'
GPU_UUID = 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98'
MODULE = 'gpu.orch_r152_a40r7_recovery'
OWNED = ('gpu/orch_r152_a40r7_recovery.py', 'gpu/orch_r152_a40r7_stage.py',
    'gpu/orch_r144_sleep_targets.py', 'tests/test_orch_r152_a40r7_recovery.py',
    'tests/test_orch_r152_a40r7_stage.py', 'tests/test_orch_r144_sleep_targets.py',
    'tests/test_orch_r145_suffix_boundary.py')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    path = Path(path)
    require(not any(item.is_symlink() for item in (path, *path.parents)), 'no_source_symlinks')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2, allow_nan=False)
        output.flush()
        os.fsync(output.fileno())


def reference(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def inventory(source):
    return {str(path.relative_to(source)): sha(path) for path in sorted(Path(source).rglob('*.py'))}


def paths(tag):
    require(tag and tag.replace('_', '').isalnum(), 'safe_unique_tag')
    return BASE/('source_r152_a40r7_'+tag), BASE/('control_r152_a40r7_'+tag)


def environment(source):
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source)+':/localhome/local-rohing/orch_r108_pytest_support_0854',
        PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True')


def repair_native(original):
    require(hashlib.sha256(original.encode()).hexdigest() == OLD_NATIVE_SHA256, 'exact_failed_native_source')
    patched = patch_source(original)
    require(hashlib.sha256(patched.encode()).hexdigest() == PATCHED_NATIVE_SHA256,
        'exact_existing_target_exclusion_patch')
    return patched


def relocated_plan(old_plan, source):
    require(old_plan['root'] == str(BASE/'run1') and old_plan['physical'] == 7
        and old_plan['gpu_uuid'] == GPU_UUID and old_plan['source_root'] == str(OLD_SOURCE),
        'same_failed_life_only')
    plan = deepcopy(old_plan)
    plan['source_root'] = str(source)
    if plan.get('startup_context'):
        relative = Path(old_plan['startup_context']['path']).relative_to(OLD_SOURCE)
        plan['startup_context']['path'] = str(source/relative)
        require(sha(source/relative) == old_plan['startup_context']['sha256'], 'same_startup_bytes')
    return plan


def prepare(package, tag):
    require(sha(OLD_CONTROL/'GUARD.json') == OLD_GUARD_SHA256, 'actual_failed_guard')
    old_config = read(OLD_CONTROL/'GUARD.json')
    require(sha(old_config['plan_path']) == old_config['plan_sha256'], 'actual_failed_plan')
    require(inventory(OLD_SOURCE) == old_config['source_pins'], 'entire_original_source_closure')
    require(read(OLD_CONTROL/'EXIT.json')['exit_code'] == 1, 'original_failed_exit')
    source, control = paths(tag)
    require(not source.exists() and not control.exists(), 'never_overwrite_source_or_attempt')
    shutil.copytree(OLD_SOURCE, source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for path in (source, *source.rglob('*')):
        require(not path.is_symlink(), 'source_copy_without_symlinks')
        path.chmod(path.stat().st_mode | 0o200)
    control.mkdir()
    for relative in OWNED:
        target = source/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(package)/relative, target)
    native_path = source/'gpu/orch_r125_continual_native.py'
    native_path.write_text(repair_native(native_path.read_text()))
    expected = dict(old_config['source_pins'])
    expected['gpu/orch_r125_continual_native.py'] = PATCHED_NATIVE_SHA256
    for relative in OWNED:
        expected[relative] = sha(Path(package)/relative)
    require(inventory(source) == expected, 'only_explicit_recovery_source_changes')
    write(control/'PLAN.json', relocated_plan(read(old_config['plan_path']), source))
    write(control/'SOURCE_PROVENANCE.json', dict(original_guard=reference(OLD_CONTROL/'GUARD.json'),
        original_source=str(OLD_SOURCE), original_pins=old_config['source_pins'], source_pins=expected,
        original_native_unchanged=True, existing_suffix_memory_policy_preserved=True,
        new_runtime_policy='R144_SPECIAL_TOKEN_TARGET_EXCLUSION_V1', prepared_unix=time.time()))
    command = [sys.executable, '-B', '-m', 'gpu.orch_r152_a40r7_stage', 'cpu', '--tag', tag]
    subprocess.run(command, cwd=source, env=environment(source), check=True)


def cpu(tag):
    from gpu import orch_r152_a40r7_recovery as recovery
    source, control = paths(tag)
    require(Path(__file__).resolve().parents[1] == source, 'CPU_runs_from_actual_staged_source')
    tests = ['tests/test_orch_r152_a40r7_recovery.py', 'tests/test_orch_r152_a40r7_stage.py',
        'tests/test_orch_r144_sleep_targets.py', 'tests/test_orch_r145_suffix_boundary.py',
        'tests/test_orch_r125_continual_guard.py']
    command = [sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *tests]
    with (control/'CPU_TESTS.log').open('x') as log:
        result = subprocess.run(command, cwd=source, env=environment(source), stdout=log,
            stderr=subprocess.STDOUT, check=False)
    require(result.returncode == 0, 'scoped_CPU_tests_must_pass')
    plan = read(control/'PLAN.json')
    provenance = recovery.cpu_provenance(plan, OLD_CONTROL/'GUARD.json')
    write(control/'CPU_PROVENANCE.json', provenance)
    gate = dict(status='PASS', exit_code=result.returncode, tests=reference(control/'CPU_TESTS.log'),
        provenance=reference(control/'CPU_PROVENANCE.json'), source_pins=inventory(source),
        module_sha256=sha(source/'gpu/orch_r152_a40r7_recovery.py'), finished_unix=time.time())
    write(control/'CPU_GATE.json', gate)
    manifest = recovery.make_manifest(plan, provenance, reference(control/'CPU_GATE.json'))
    write(control/'MANIFEST.json', manifest)
    for path in (source, *source.rglob('*')):
        path.chmod(path.stat().st_mode & ~0o222)
    status = dict(status='CPU_PREPARED_MAIN_ACK_REQUIRED_NO_GPU', manifest=reference(control/'MANIFEST.json'),
        source_pins=gate['source_pins'], required_ack=dict(author='Main', approved=True,
            manifest_sha256=recovery.digest(manifest)), prepared_unix=time.time())
    write(control/'STAGED.json', status)
    print(json.dumps({key:status[key] for key in ('status', 'manifest', 'required_ack')}, sort_keys=True))


def launch(tag):
    from gpu import orch_r125_continual_guard as guard
    from gpu import orch_r152_a40r7_recovery as recovery
    source, control = paths(tag)
    require(Path(__file__).resolve().parents[1] == source, 'launch_from_immutable_staged_source')
    manifest = read(control/'MANIFEST.json')
    acknowledgment = reference(control/'MAIN_ACK.json')
    recovery.verify_manifest(manifest, acknowledgment)
    require(sha(OLD_CONTROL/'GUARD.json') == OLD_GUARD_SHA256, 'preserved_original_guard')
    config = read(OLD_CONTROL/'GUARD.json')
    allocation = read(config['allocation_path'])
    require(sha(config['allocation_path']) == config['allocation_sha256'], 'original_allocation_bytes')
    allocation.update(plan_sha256=sha(control/'PLAN.json'), declared_unix=time.time(),
        r152_recovery_cpu_gate=reference(control/'CPU_GATE.json'), no_new_allocation=True)
    write(control/'ALLOCATION.json', allocation)
    config.update(plan_path=str(control/'PLAN.json'), plan_sha256=sha(control/'PLAN.json'),
        attempt_dir=str(control), resume=True, allocation_path=str(control/'ALLOCATION.json'),
        allocation_sha256=sha(control/'ALLOCATION.json'), source_pins=inventory(source),
        r152_manifest=reference(control/'MANIFEST.json'), r152_acknowledgment=acknowledgment)
    config['device_containment'] = dict(config['device_containment'], unit='orch-r136-native-'+uuid.uuid4().hex)
    require(config['source_pins'] == read(control/'CPU_GATE.json')['source_pins'], 'tested_source_bytes')
    write(control/'GUARD.json', config)
    guard.validate(control/'GUARD.json')
    command = [sys.executable, '-B', '-m', MODULE, 'contained-supervise', '--config', str(control/'GUARD.json')]
    with (control/'SUPERVISOR.log').open('x') as log:
        process = subprocess.Popen(command, cwd=source, env=environment(source), stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='SUPERVISOR_DISPATCHED_NOT_NATIVE_LOADED', pid=process.pid, command=command,
        guard=reference(control/'GUARD.json'), started_unix=time.time())
    write(control/'SUPERVISOR_DISPATCH.json', receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'cpu', 'launch'))
    parser.add_argument('--tag', required=True)
    parser.add_argument('--package', type=Path)
    arguments = parser.parse_args()
    if arguments.action == 'prepare':
        require(arguments.package is not None, 'explicit_source_package_required')
        prepare(arguments.package, arguments.tag)
    else:
        globals()[arguments.action](arguments.tag)
