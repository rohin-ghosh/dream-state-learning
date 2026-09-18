"""A40R7-only CPU staging, proof-bound finalization, and original admission."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from gpu import orch_r145_a40r7_recovery as recovery


OWNED = ('orch_r145_a40r7_recovery.py', 'orch_r145_a40r7_stage.py', 'orch_r145_a40r7_capture.py')
TESTS = ('test_orch_r145_a40r7_recovery.py',)


def reference(path):
    return dict(path=str(Path(path).absolute()), sha256=recovery.sha(path))


def paths(tag):
    recovery.require(tag and tag.replace('_', '').isalnum(), 'unique_safe_tag')
    return (recovery.BASE / ('source_r145_a40r7_' + tag),
            recovery.BASE / ('control_r145_a40r7_' + tag))


def same_plan(source):
    from gpu import orch_r125_continual_native as native
    plan = json.loads(recovery.raw(recovery.BASE / 'control1/PLAN.json'))
    plan['source_root'] = str(source)
    if plan.get('startup_context'):
        relative = Path(plan['startup_context']['path']).relative_to(recovery.SOURCE)
        plan['startup_context']['path'] = str(source / relative)
    native.validate_plan(plan)
    return plan


def environment(source):
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source)+':/localhome/local-rohing/orch_r108_pytest_support_0854')


def prepare(package, tag):
    recovery.pinned_evidence()
    recovery.verify_original_absent()
    recovery.verify_topology()
    source, control = paths(tag)
    recovery.require(not source.exists() and not control.exists(), 'never_overwrite_staging')
    package = Path(package).absolute()
    shutil.copytree(recovery.SOURCE, source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for path in (source, *source.rglob('*')):
        recovery.require(not path.is_symlink(), 'no_source_symlinks')
        path.chmod(path.stat().st_mode | 0o200)
    control.mkdir()
    for name in (*OWNED, *recovery.MEMORY_HELPERS):
        if name in recovery.MEMORY_HELPERS:
            recovery.require(recovery.sha(package / 'gpu' / name) == recovery.MEMORY_HELPERS[name],
                             'exact_Main_helper_bytes')
        shutil.copyfile(package / 'gpu' / name, source / 'gpu' / name)
    for name in TESTS:
        shutil.copyfile(package / 'tests' / name, source / 'tests' / name)
    command = [sys.executable, '-B', '-m', 'gpu.orch_r145_a40r7_stage', 'cpu', '--tag', tag]
    result = subprocess.run(command, cwd=source, env=environment(source), check=False)
    recovery.require(result.returncode == 0, 'original_source_CPU_staging_pass')


def run_tests(source, control, name):
    command = [sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/test_orch_r145_a40r7_recovery.py', 'tests/test_orch_r125_continual_guard.py',
        'tests/test_orch_r125_continual_native.py', 'tests/test_orch_r125_plain_context.py']
    with (control / name).open('x') as log:
        result = subprocess.run(command, cwd=source, env=environment(source), stdout=log,
                                stderr=subprocess.STDOUT, check=False)
    recovery.require(result.returncode == 0, 'own_and_original_CPU_tests_pass')
    text = (control / name).read_text()
    recovery.require('passed' in text and 'skipped' not in text and 'failed' not in text, 'no_skipped_CPU_gate')
    return reference(control / name)


def cpu(tag):
    from gpu import orch_r145_node3_capacity_recovery as capacity
    source, control = paths(tag)
    recovery.require(Path(recovery.__file__).absolute().parent.parent == source, 'actual_staged_module')
    test_log = run_tests(source, control, 'CPU_PREPROOF_TESTS.log')
    plan = same_plan(source)
    provenance = recovery.cpu_provenance(plan)
    original_guard = json.loads(recovery.raw(recovery.BASE / 'control1/GUARD.json'))
    for name, expected in original_guard['source_pins'].items():
        recovery.require(recovery.sha(source / name) == expected, 'copied_original_source_closure')
    runtime = capacity.installed_runtime_pins()
    runtime_path = source / 'gpu' / capacity.RUNTIME_FILENAME
    recovery.save(runtime_path, runtime)
    recovery.save(control / 'CPU_PROVENANCE.json', provenance)
    recovery.save(control / 'PLAN.json', plan)
    result = dict(status='CPU_PREPARED_NO_MEMORY_ACTIVATION_NO_LAUNCH', source_root=str(source),
        control_root=str(control), runtime=reference(runtime_path), test_log=test_log,
        provenance=reference(control / 'CPU_PROVENANCE.json'), module=reference(Path(recovery.__file__).absolute()),
        original_native_unchanged=True, original_minor=4, memory_proof_required=True,
        matched_generations_not_yet_claimed=True, finished_unix=time.time())
    recovery.save(control / 'STAGED_PREPROOF.json', result)
    print(json.dumps(result, indent=2), flush=True)


def finalize(tag, proof_path, proof_sha):
    from gpu import orch_r145_suffix_boundary as boundary
    from gpu import orch_r145_node3_capacity_recovery as capacity
    source, control = paths(tag)
    recovery.require(Path(recovery.__file__).absolute().parent.parent == source, 'actual_staged_module')
    recovery.require(not (control / 'MANIFEST.json').exists(), 'no_repeated_finalization')
    recovery.verify_original_absent()
    recovery.pinned_evidence()
    recovery.verify_topology()
    runtime = reference(source / 'gpu' / capacity.RUNTIME_FILENAME)
    recovery.require(json.loads(recovery.raw(runtime['path'])) == capacity.installed_runtime_pins(), 'actual_runtime_unchanged')
    proof_path = Path(proof_path).absolute()
    proof = boundary.read_bound(proof_path, proof_sha)
    boundary.validate_gpu_proof(proof, runtime['sha256'])
    provenance = recovery.cpu_provenance(json.loads(recovery.raw(control / 'PLAN.json')))
    query = ['nvidia-smi', '--id='+recovery.GPU_UUID, '--query-gpu=memory.total', '--format=csv,noheader,nounits']
    total = int(subprocess.check_output(query, text=True).strip()) * 1024**2
    memory = proof['longest_child_prospective_only']['memory']
    recovery.require(memory['full_input_tokens'] >= provenance['max_input_tokens']
        and memory['logits_tokens'] >= provenance['max_logits_tokens']
        and memory['total_bytes'] <= total, 'actual_node3_proof_must_cover_A40R7_shape_capacity')
    recovery.save_bytes(control / 'MAIN_GPU_PROOF.json', recovery.raw(proof_path))
    coverage = dict(provenance, checkpoint_sha256=recovery.PINS['run1/checkpoints/sleep_000022/COMMIT.json'],
        proof_sha256=proof_sha, runtime_sha256=runtime['sha256'], device_total_bytes=total)
    recovery.save(control / 'MEMORY_COVERAGE.json', coverage)
    binding = dict(proof=reference(control / 'MAIN_GPU_PROOF.json'), runtime=runtime,
                   coverage=reference(control / 'MEMORY_COVERAGE.json'))
    native_path = source / 'gpu/orch_r125_continual_native.py'
    original = recovery.raw(native_path).decode()
    modified = recovery.verified_sleep_source(original, binding)
    native_path.write_text(modified)
    final_tests = run_tests(source, control, 'CPU_FINAL_TESTS.log')
    module_sha = recovery.sha(Path(recovery.__file__).absolute())
    gate = dict(status='PASS', module_sha256=module_sha, tests=final_tests, memory=binding,
        source_pins={str(path.relative_to(source)): recovery.sha(path) for path in source.rglob('*.py')},
        CPU_provenance=reference(control / 'CPU_PROVENANCE.json'), finished_unix=time.time())
    recovery.save(control / 'CPU_GATE.json', gate)
    manifest = dict(schema=recovery.SCHEMA, root=str(recovery.ROOT), recovery_root=str(recovery.RECOVERY),
        semantics=recovery.SEMANTICS, journal_head=recovery.HEAD, module_sha256=module_sha,
        cpu_evidence=reference(control / 'CPU_GATE.json'), allocator=recovery.ALLOCATOR, memory=binding)
    recovery.save(control / 'MANIFEST.json', manifest)
    for path in (source, *source.rglob('*')):
        path.chmod(path.stat().st_mode & ~0o222)
    result = dict(status='PROOF_AND_CPU_PASS_ACK_REQUIRED_NOT_LAUNCHED', manifest=reference(control / 'MANIFEST.json'),
        required_ack=dict(author='Main', approved=True, manifest_sha256=recovery.digest(manifest)),
        required_ack_path=str(control / 'MAIN_ACK.json'), finished_unix=time.time())
    recovery.save(control / 'STAGED_FINAL.json', result)
    print(json.dumps(result, indent=2), flush=True)


def launch(tag):
    from gpu import orch_r125_continual_guard as guard
    source, control = paths(tag)
    recovery.require(Path(recovery.__file__).absolute().parent.parent == source, 'actual_staged_module')
    manifest = json.loads(recovery.raw(control / 'MANIFEST.json'))
    acknowledgment = reference(control / 'MAIN_ACK.json')
    recovery.verify_manifest(manifest, acknowledgment)
    recovery.pinned_evidence()
    recovery.verify_original_absent()
    recovery.verify_topology()
    config = json.loads(recovery.raw(recovery.BASE / 'control1/GUARD.json'))
    policy = config['device_containment']
    recovery.require(policy['minor'] == 4 and policy['uid'] == policy['gid'] == 2524, 'exact_original_containment_identity')
    policy['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    allocation = json.loads(recovery.raw(recovery.BASE / 'control1/ALLOCATION.json'))
    allocation.update(plan_sha256=recovery.sha(control / 'PLAN.json'), declared_unix=time.time(),
        r145_a40r7_cpu_gate_sha256=recovery.sha(control / 'CPU_GATE.json'), r145_same_existing_allocation=True)
    recovery.save(control / 'ALLOCATION.json', allocation)
    config.update(plan_path=str(control / 'PLAN.json'), plan_sha256=recovery.sha(control / 'PLAN.json'),
        attempt_dir=str(control), resume=True, allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=recovery.sha(control / 'ALLOCATION.json'),
        source_pins={str(path.relative_to(source)): recovery.sha(path) for path in source.rglob('*.py')},
        r145_a40r7_manifest=reference(control / 'MANIFEST.json'), r145_a40r7_acknowledgment=acknowledgment)
    gate = json.loads(recovery.raw(control / 'CPU_GATE.json'))
    recovery.require(config['source_pins'] == gate['source_pins'], 'exact_tested_source_closure')
    recovery.save(control / 'GUARD.json', config)
    guard.validate(control / 'GUARD.json')
    command = [sys.executable, '-B', '-m', 'gpu.orch_r145_a40r7_recovery', 'contained-supervise',
               '--config', str(control / 'GUARD.json')]
    with (control / 'SUPERVISOR.log').open('x') as log:
        process = subprocess.Popen(command, cwd=source, env=environment(source), stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='SUPERVISOR_DISPATCHED_NOT_NATIVE_LOADED', pid=process.pid,
        command=command, guard=reference(control / 'GUARD.json'), started_unix=time.time())
    recovery.save(control / 'SUPERVISOR_DISPATCH.json', receipt)
    print(json.dumps(receipt, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'cpu', 'finalize', 'launch'))
    parser.add_argument('--tag', required=True)
    parser.add_argument('--package', type=Path)
    parser.add_argument('--proof', type=Path)
    parser.add_argument('--proof-sha')
    arguments = parser.parse_args()
    if arguments.action == 'prepare':
        recovery.require(arguments.package is not None, 'package_required')
        prepare(arguments.package, arguments.tag)
    elif arguments.action == 'cpu':
        cpu(arguments.tag)
    elif arguments.action == 'finalize':
        recovery.require(arguments.proof is not None and arguments.proof_sha is not None, 'bound_GPU_proof_required')
        finalize(arguments.tag, arguments.proof, arguments.proof_sha)
    else:
        launch(arguments.tag)


if __name__ == '__main__':
    main()
