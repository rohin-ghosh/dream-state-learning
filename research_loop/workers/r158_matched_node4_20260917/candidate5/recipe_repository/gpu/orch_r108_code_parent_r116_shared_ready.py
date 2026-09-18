"""Publish CODE shared-client readiness; never initializes or starts shared training."""

import argparse
from pathlib import Path
import time

from gpu import orch_r108_code_parent_r116_shared as client


coordinator = client.coordinator
COMMON_ROOT = '/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1'
SOURCE_FILES = ('gpu/orch_r108_code_parent_r116_shared.py',
    'gpu/orch_r108_code_parent_r116_shared_run.py',
    'gpu/orch_r108_code_parent_r116_shared_ready.py',
    'gpu/orch_r116_shared_learner.py', 'gpu/orch_r111_route_shared.py')


def publish(root, successor_source, tests_receipt):
    root = Path(root).resolve(strict=True)
    successor_source = Path(successor_source).resolve(strict=True)
    tests_receipt = Path(tests_receipt).resolve(strict=True)
    plan = coordinator.read(root/'PLAN.json')
    branch = {2:'F3',6:'A3'}.get(plan['physical'])
    coordinator.require(branch is not None, 'own_CODE_pair_only')
    tests = coordinator.read(tests_receipt)
    sources = {name:coordinator.sha(successor_source/name) for name in SOURCE_FILES}
    coordinator.require(tests['source_files'] == sources and tests['passed'] is True
        and tests['cuda_initialized'] is False, 'bound_CPU_tests')
    cohort = coordinator.read(root/'COHORT.json')
    coordinator.require(client.run.policy.digest(cohort) == plan['cohort_sha256'], 'same_original_cohort')
    train = [task['task_id'] for task in cohort['TRAIN']]
    excluded = [task['task_id'] for split in ('DEV','FINAL') for task in cohort[split]]
    coordinator.require(not set(train).intersection(excluded), 'all_readouts_excluded')
    receipt = dict(schema='R116_SHARED_CLIENT_READY_V1',branch=branch,root=str(root),train_ids=train,
        excluded_ids=excluded,successor_source=str(successor_source),source_files=sources,
        common_root=COMMON_ROOT,inherited_bounds={key:plan[key] for key in client.BOUND_FIELDS},
        predecessor_plan_sha256=coordinator.sha(root/'PLAN.json'),
        tests_receipt=dict(path=str(tests_receipt),sha256=coordinator.sha(tests_receipt)),
        native_capture_fields=['shared_generation','shared_checkpoint_sha256','task_id'],
        training_phases=sorted(coordinator.PHASES),ready_for_initialization=True,
        active_shared_client=False,optimizer_owner='F1',local_optimizer_steps=0,
        original_counters_preserved=True,transition='COMPLETED_TWO_EPISODE_BOUNDARY_NO_HOTPATCH',
        activation_binding_fields=['branch','root','config_sha256','adoption_path','adoption_sha256'],
        activation_sidecar='SHARED_ACTIVATION.json',
        activation_fields=['predecessor_plan_sha256','inherited_bounds','shared_learner',
            'predecessor_identity','previous_reservations'],
        command_module='gpu.orch_r108_code_parent_r116_shared_run',
        broker_transition_note='Old TERMINAL.json remains immutable; successor broker must follow SHARED_TERMINAL.json after exact activation.',
        observed_unix=time.time())
    coordinator.write(root/'SHARED_CLIENT_READY.json',receipt)
    return receipt


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--successor-source',type=Path,required=True)
    parser.add_argument('--tests-receipt',type=Path,required=True)
    args=parser.parse_args()
    result=publish(args.root,args.successor_source,args.tests_receipt)
    print(result['branch'],str(args.root/'SHARED_CLIENT_READY.json'))
