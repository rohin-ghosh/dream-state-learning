"""Publish node-local client readiness without stopping or modifying a live plan."""

import argparse
from pathlib import Path
import time

from gpu import orch_r111_route_shared as client
from gpu import orch_r116_shared_learner as coordinator


COMMON_ROOT = '/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1'
SOURCE_FILES = ('gpu/orch_r111_route_pair_shared.py', 'gpu/orch_r111_route_shared.py',
                'gpu/orch_r116_shared_learner.py', 'gpu/orch_r111_route_boundary.py')
V2_SOURCE_FILES = SOURCE_FILES + ('gpu/orch_r111_route_shared_ready.py',)


def verify_closure(successor_source, tests):
    reference = tests['closure_manifest']
    path = Path(reference['path']).resolve(strict=True)
    coordinator.require(path.parent == successor_source and coordinator.sha(path) == reference['sha256'],
                        'source_closure_manifest_binding')
    manifest = coordinator.read(path)
    coordinator.require(manifest['schema'] == 'R118_ROUTE_SOURCE_CLOSURE_V2'
                        and manifest['root'] == str(successor_source), 'exact_source_closure_root')
    actual = {str(path.relative_to(successor_source)): coordinator.sha(path)
              for path in successor_source.rglob('*.py') if path.is_file()}
    coordinator.require(actual == manifest['files'], 'complete_python_closure_unchanged')
    for name in actual:
        source_file = successor_source / name
        coordinator.require(source_file.resolve() == source_file and source_file.resolve().is_relative_to(successor_source),
                            'no_source_symlink_escape')
    entrypoint = tests['entrypoint']
    coordinator.require(entrypoint['module'] == 'gpu.orch_r111_route_pair_shared'
                        and entrypoint['sha256'] == actual['gpu/orch_r111_route_pair_shared.py']
                        and entrypoint['help_exit_code'] == 0 and tests['native_cpu'] is True
                        and tests['tests_failed'] == 0 and tests['tests_skipped'] == 0,
                        'native_complete_closure_executable_tested')
    return dict(path=str(path), sha256=reference['sha256'], files=len(actual))


def publish(root, successor_source, tests_receipt, version=1, revision=0):
    root = Path(root).resolve(strict=True)
    successor_source = Path(successor_source).resolve(strict=True)
    tests_receipt = Path(tests_receipt).resolve(strict=True)
    plan = coordinator.read(root / 'PLAN.json')
    coordinator.require(plan['root'] == str(root), 'exact_existing_life_root')
    branch = {0: 'F1', 4: 'A1'}.get(plan['physical'])
    coordinator.require(branch is not None, 'route_owned_branch')
    coordinator.require(version in (1, 2), 'supported_ready_version')
    coordinator.require(type(revision) is int and revision >= 0 and (version == 2 or revision == 0),
                        'v2_revision_only')
    destination_name = 'SHARED_CLIENT_READY_V2.json' if version == 2 else 'SHARED_CLIENT_READY.json'
    if revision:
        destination_name = f'SHARED_CLIENT_READY_V2_R{revision}.json'
    if (root / destination_name).exists():
        raise FileExistsError(root / destination_name)
    tests = coordinator.read(tests_receipt)
    files = V2_SOURCE_FILES if version == 2 else SOURCE_FILES
    sources = {name: coordinator.sha(successor_source / name) for name in files}
    coordinator.require(tests['source_files'] == sources and tests['passed'] is True
                        and tests['cuda_initialized'] is False, 'bound_native_CPU_tests')
    closure = verify_closure(successor_source, tests) if version == 2 else None
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
    receipt = dict(schema='R116_SHARED_CLIENT_READY_V' + str(version), branch=branch, root=str(root),
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
    if version == 2:
        previous = root / 'SHARED_CLIENT_READY.json'
        receipt.update(source_closure=closure,
            executable=dict(module='gpu.orch_r111_route_pair_shared',
                source=str(successor_source / 'gpu/orch_r111_route_pair_shared.py'),
                sha256=sources['gpu/orch_r111_route_pair_shared.py']),
            predecessor_ready=dict(path=str(previous), sha256=coordinator.sha(previous)) if previous.exists() else None,
            predecessor_ready_preserved=True, empty_successor_cursor_resume=True,
            boundary_release_plan_field='route_boundary_release',
            all_eight_ready_required_before_arming=True, boundary_controller_armed=False,
            parent_wait_seconds_unchanged=plan['parent_wait_seconds'],
            replaces_v1_only_after_Main_explicit_binding=True)
        if revision:
            previous_v2 = root / ('SHARED_CLIENT_READY_V2.json' if revision == 1
                                   else f'SHARED_CLIENT_READY_V2_R{revision-1}.json')
            coordinator.require(previous_v2.is_file(), 'preserved_previous_v2_revision')
            receipt.update(revision=revision,
                predecessor_v2_revision=dict(path=str(previous_v2), sha256=coordinator.sha(previous_v2)),
                requires_Main_explicit_revision_binding=True)
    coordinator.write(root / destination_name, receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--successor-source', type=Path, required=True)
    parser.add_argument('--tests-receipt', type=Path, required=True)
    parser.add_argument('--version', type=int, choices=(1, 2), default=1)
    parser.add_argument('--revision', type=int, default=0)
    arguments = parser.parse_args()
    result = publish(arguments.root, arguments.successor_source, arguments.tests_receipt,
                     arguments.version, arguments.revision)
    destination = 'SHARED_CLIENT_READY_V2.json' if arguments.version == 2 else 'SHARED_CLIENT_READY.json'
    if arguments.revision:
        destination = f'SHARED_CLIENT_READY_V2_R{arguments.revision}.json'
    print(result['branch'], str(arguments.root / destination))
