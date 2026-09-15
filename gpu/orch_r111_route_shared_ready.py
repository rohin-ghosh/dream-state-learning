"""Publish node-local client readiness without stopping or modifying a live plan."""

import argparse
from pathlib import Path
import time

from gpu import orch_r111_route_shared as client
from gpu import orch_r116_shared_learner as coordinator


COMMON_ROOT = '/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1'
SOURCE_FILES = ('gpu/orch_r111_route_pair_shared.py', 'gpu/orch_r111_route_shared.py',
                'gpu/orch_r116_shared_learner.py')


def publish(root, successor_source, tests_receipt):
    root = Path(root).resolve(strict=True)
    successor_source = Path(successor_source).resolve(strict=True)
    tests_receipt = Path(tests_receipt).resolve(strict=True)
    plan = coordinator.read(root / 'PLAN.json')
    coordinator.require(plan['root'] == str(root), 'exact_existing_life_root')
    branch = {0: 'F1', 4: 'A1'}.get(plan['physical'])
    coordinator.require(branch is not None, 'route_owned_branch')
    tests = coordinator.read(tests_receipt)
    sources = {name: coordinator.sha(successor_source / name) for name in SOURCE_FILES}
    coordinator.require(tests['source_files'] == sources and tests['passed'] is True
                        and tests['cuda_initialized'] is False, 'bound_native_CPU_tests')
    cohort = coordinator.read(root / 'COHORT.json')
    coordinator.require(coordinator.sha(root / 'COHORT.json') == plan['cohort_sha256'], 'cohort_source_binding')
    coordinator.require(coordinator.sha(root / 'SEALED_FINAL.json') == plan['final_sha256'], 'sealed_source_binding')
    train_ids = [task['id'] for task in cohort['train']]
    excluded_ids = [task['id'] for task in cohort['held']]
    excluded_ids += [task['id'] for task in coordinator.read(root / 'SEALED_FINAL.json')['tasks']]
    coordinator.require(not set(train_ids).intersection(excluded_ids), 'held_never_train')
    boundary = None
    prior = None
    if branch == 'F1' and any(root.glob('cycle_*/COMPLETE.json')):
        adoption = client.adoption_inputs(root)
        checkpoint = adoption['checkpoint']
        destination = root / ('SHARED_HISTORY_CANDIDATE_' + checkpoint['path_sha256'][:16] + '.json')
        if not destination.exists():
            coordinator.write(destination, adoption)
        else:
            coordinator.require(coordinator.read(destination) == adoption, 'immutable_history_candidate')
        boundary = checkpoint
        prior = dict(path=str(destination), sha256=coordinator.sha(destination),
                     prior_metrics=adoption['prior_metrics'], rows=len(adoption['initial_history']['F1']),
                     candidate_only_until_current_cycle_handoff=True)
    receipt = dict(schema='R116_SHARED_CLIENT_READY_V1', branch=branch, root=str(root),
        train_ids=train_ids, excluded_ids=excluded_ids, successor_source=str(successor_source),
        source_files=sources, boundary_checkpoint=boundary, history_candidate=prior,
        common_root=COMMON_ROOT, inherited_bounds=plan['bounds'],
        predecessor_plan_sha256=coordinator.sha(root / 'PLAN.json'),
        tests_receipt=dict(path=str(tests_receipt), sha256=coordinator.sha(tests_receipt)),
        native_capture_fields=['shared_generation', 'shared_checkpoint_sha256'],
        ready_for_initialization=True, active_shared_client=False,
        transition='FINISH_CURRENT_CYCLE_AFTER_ALL_EIGHT_READY_NO_HOTPATCH',
        activation_binding_fields=['branch', 'root', 'config_sha256', 'adoption_path', 'adoption_sha256'],
        optimizer_owner='F1', original_counters_preserved=True,
        observed_unix=time.time())
    coordinator.write(root / 'SHARED_CLIENT_READY.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--successor-source', type=Path, required=True)
    parser.add_argument('--tests-receipt', type=Path, required=True)
    arguments = parser.parse_args()
    result = publish(arguments.root, arguments.successor_source, arguments.tests_receipt)
    print(result['branch'], str(arguments.root / 'SHARED_CLIENT_READY.json'))
