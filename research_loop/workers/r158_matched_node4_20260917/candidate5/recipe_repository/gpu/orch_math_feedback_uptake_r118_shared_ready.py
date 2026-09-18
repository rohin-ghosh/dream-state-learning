"""Node-local runnable math readiness, without initializing or stopping a life."""

import argparse
from pathlib import Path
import time

from gpu import orch_math_feedback_uptake_r117_shared as client


shared, math, require = client.shared, client.math, client.require
COMMON_ROOT = '/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1'
ORIGINAL_SOURCE = Path('/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_source_20260915_attempt1')
MODULE = 'gpu.orch_math_feedback_uptake_r118_shared_run'
REQUIRED = ('gpu/orch_math_feedback_uptake_r117_shared.py',
    'gpu/orch_math_feedback_uptake_r118_shared_run.py',
    'gpu/orch_math_feedback_uptake_r118_shared_ready.py',
    'gpu/orch_math_feedback_uptake_r118_shared_boundary.py',
    'gpu/orch_r116_shared_learner.py', 'gpu/orch_r111_route_boundary.py')


def branch_for(root):
    root = Path(root).resolve(strict=True)
    matches = [branch for branch, path in client.BRANCHES.items() if path == root]
    require(len(matches) == 1, 'exact_math_root')
    return matches[0]


def bounds():
    return dict(cycles=math.policy.CYCLES, native_calls=math.policy.NATIVE_CAP,
        parent_calls=math.policy.PARENT_CAP, native_end_unix=math.NATIVE,
        morning_unix=math.policy.previous.MORNING, hard_end_unix=math.HARD)


def reference(path):
    return dict(path=str(path), sha256=shared.sha(path))


def inventory(source):
    source = Path(source)
    return {str(path.relative_to(source)): shared.sha(path)
        for folder in ('gpu', 'organism_v6', 'tests') for path in sorted((source/folder).rglob('*.py'))}


def predecessor(root):
    root = Path(root)
    branch_for(root)
    original = shared.read(root.parent/'READY.json')
    for name, expected in original['source_files'].items():
        require(shared.sha(ORIGINAL_SOURCE/name) == expected, 'original_source_unchanged:'+name)
    for name, expected in original['data_files'].items():
        require(shared.sha(root.parent/name) == expected, 'original_cohort_unchanged:'+name)
    require(shared.digest(shared.read(root.parent/'COMMON_CONTRACT.json')) == original['common_contract_sha256'],
        'original_contract_unchanged')
    activation = shared.read(root/'ACTIVATION.json')
    require(activation['native_deadline_unix'] == math.NATIVE and activation['hard_deadline_unix'] == math.HARD,
        'original_absolute_deadlines')
    return {name: reference(root/name) for name in ('CONFIG.json', 'ACTIVATION.json', 'BROKER_CONFIG.json')} | {
        'READY.json': reference(root.parent/'READY.json'),
        'COMMON_CONTRACT.json': reference(root.parent/'COMMON_CONTRACT.json')}


def publish(root, successor_source, tests_receipt):
    root, source = Path(root).resolve(strict=True), Path(successor_source).resolve(strict=True)
    branch = branch_for(root)
    tests = shared.read(tests_receipt)
    sources = inventory(source)
    require(all(name in sources for name in REQUIRED), 'executable_successor_closure')
    require(tests['source_files'] == sources and tests['passed'] is True
        and tests['cuda_initialized'] is False and tests['native_calls'] == 0, 'bound_native_CPU_tests')
    previous = predecessor(root)
    groups = shared.read(root.parent/'TRAIN.json')[:math.policy.CYCLES]
    train = [task['id'] for group in groups for task in group]
    require(len(groups) == math.policy.CYCLES and all(len(group) == 2 for group in groups)
        and len(set(train)) == len(train), 'original_43_two_episode_cycles')
    roster = shared.read(root.parent/'sealed/READOUT_ROSTER.json')
    excluded = roster['dev_ids'] + roster['final_ids']
    require(not set(train).intersection(excluded), 'DEV_FINAL_never_training')
    receipt = dict(schema='R116_SHARED_CLIENT_READY_V1', branch=branch, root=str(root),
        train_ids=train, excluded_ids=excluded, successor_source=str(source), source_files=sources,
        common_root=COMMON_ROOT, inherited_bounds=bounds(), predecessor_bindings=previous,
        predecessor_plan_sha256=shared.sha(root.parent/'COMMON_CONTRACT.json'),
        tests_receipt=reference(tests_receipt), native_capture_fields=['shared_generation', 'shared_checkpoint_sha256'],
        training_phases=list(client.PHASES), ready_for_initialization=True, active_shared_client=False,
        optimizer_owner='F1', local_optimizer_steps=0, original_counters_preserved=True,
        command_module=MODULE, command=[math.PYTHON, '-B', '-m', MODULE, 'guard', '--root', str(root)],
        boundary_module='gpu.orch_math_feedback_uptake_r118_shared_boundary',
        activation_sidecar='SHARED_ACTIVATION.json',
        activation_binding_fields=['branch', 'root', 'config_sha256', 'adoption_path', 'adoption_sha256'],
        transition='AGREED_ALL_EIGHT_COMPLETED_CYCLE_PINNED_RELEASE_THEN_STRICT_ADMISSION',
        broker_transition_note='Preserve old TERMINAL.json; successor broker follows SHARED_TERMINAL.json, same queues/caps/claims.',
        historical_BASE_captures_never_retagged=True, observed_unix=time.time())
    shared.write(root/'SHARED_CLIENT_READY.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--successor-source', type=Path, required=True)
    parser.add_argument('--tests-receipt', type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.root, args.successor_source, args.tests_receipt)
    print(result['branch'], str(args.root/'SHARED_CLIENT_READY.json'))
