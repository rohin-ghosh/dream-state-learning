"""Bind runnable readiness and adopt F1 after family-specific boundary release.

The handoff certificate records those releases; this module does not signal actors
or replace the successor families' own reservation and boundary verification.
"""

import argparse
from copy import deepcopy
import json
from pathlib import Path

from gpu import orch_r111_route_shared as route
from gpu import orch_r116_shared_learner as shared


MODULES = {
    'F1': 'gpu.orch_r111_route_pair_shared',
    'A1': 'gpu.orch_r111_route_pair_shared',
    'F2': 'gpu.orch_math_feedback_uptake_r118_shared_run',
    'A2': 'gpu.orch_math_feedback_uptake_r118_shared_run',
    'F3': 'gpu.orch_r108_code_parent_r116_shared_run',
    'A3': 'gpu.orch_r108_code_parent_r116_shared_run',
    'F4': 'gpu.orch_r118_grid_shared_run',
    'A4': 'gpu.orch_r118_grid_shared_run',
}


def reference(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=shared.sha(path))


def bound_read(binding):
    path = Path(binding['path'])
    shared.require(path.is_absolute() and shared.sha(path) == binding['sha256'],
                   'exact_absolute_artifact_binding')
    return shared.read(path)


def readiness(entries, common_root):
    shared.require(set(entries) == set(shared.BRANCHES), 'all_eight_runnable_clients_required')
    common_root = Path(common_root).resolve()
    specs, bounds, exclusions, selected = {}, {}, set(), {}
    coordinator_hashes = set()
    for branch in shared.BRANCHES:
        binding = entries[branch]
        ready = bound_read(binding)
        root = Path(ready['root']).resolve(strict=True)
        source = Path(ready['successor_source']).resolve(strict=True)
        shared.require(ready['branch'] == branch and Path(binding['path']).parent.resolve() == root,
                       'actual_branch_local_readiness_required')
        shared.require(ready['schema'] in ('R116_SHARED_CLIENT_READY_V1', 'R116_SHARED_CLIENT_READY_V2')
                       and ready['ready_for_initialization'] is True
                       and ready['active_shared_client'] is False
                       and ready['optimizer_owner'] == 'F1'
                       and ready['original_counters_preserved'] is True,
                       'runnable_unactivated_single_owner_readiness')
        shared.require(Path(ready['common_root']).resolve() == common_root, 'same_common_root')
        if branch in ('F1', 'A1'):
            shared.require(ready['schema'] == 'R116_SHARED_CLIENT_READY_V2'
                           and ready['empty_successor_cursor_resume'] is True,
                           'route_v2_preserves_empty_next_cycle')
        module = ready.get('command_module', ready.get('executable', {}).get('module'))
        module_path = MODULES[branch].replace('.', '/') + '.py'
        shared.require(module == MODULES[branch] and module_path in ready['source_files'],
                       'runnable_successor_not_client_helper')
        for name, expected in ready['source_files'].items():
            path = source / name
            shared.require(path.resolve() == path and path.is_relative_to(source)
                           and shared.sha(path) == expected, 'successor_source_binding')
        shared.require('gpu/orch_r116_shared_learner.py' in ready['source_files'],
                       'coordinator_in_source_closure')
        coordinator_hashes.add(ready['source_files']['gpu/orch_r116_shared_learner.py'])
        tests = bound_read(ready['tests_receipt'])
        shared.require(tests['passed'] is True and tests['cuda_initialized'] is False,
                       'bound_CPU_test_receipt')
        shared.require(all(tests['source_files'].get(name) == expected
                           for name, expected in ready['source_files'].items()),
                       'tested_source_closure')
        if ready.get('source_closure'):
            closure = bound_read(ready['source_closure'])
            actual = {str(path.relative_to(source)): shared.sha(path)
                      for path in source.rglob('*.py') if path.is_file()}
            shared.require(actual == closure['files'], 'complete_source_closure_unchanged')
        train_ids = ready['train_ids']
        shared.require(train_ids and len(train_ids) == len(set(train_ids)), 'nonempty_unique_train_inventory')
        specs[branch] = dict(root=str(root), train_ids=list(train_ids))
        bounds[branch] = deepcopy(ready['inherited_bounds'])
        exclusions.update(ready['excluded_ids'])
        selected[branch] = deepcopy(binding)
    shared.require(len({spec['root'] for spec in specs.values()}) == 8, 'eight_distinct_branch_roots')
    shared.require(coordinator_hashes == {shared.sha(Path(shared.__file__))},
                   'all_successors_use_this_exact_coordinator')
    shared.require(all(not exclusions.intersection(spec['train_ids']) for spec in specs.values()),
                   'cross_branch_DEV_FINAL_exclusion')
    return dict(schema='R118_EIGHT_RUNNABLE_READY_V1', common_root=str(common_root),
                readiness=selected, branch_specs=specs, branch_bounds=bounds,
                excluded_ids=sorted(exclusions), optimizer_owner='F1', active=False)


def released_handoff(binding, prepared):
    document = bound_read(binding)
    shared.require(document['schema'] == 'R118_SHARED_HANDOFF_V1'
                   and document['readiness'] == prepared['readiness'], 'bound_common_handoff')
    shared.require(set(document['branches']) == set(shared.BRANCHES), 'eight_released_branches')
    for branch, item in document['branches'].items():
        root = Path(prepared['branch_specs'][branch]['root'])
        shared.require(item['root'] == str(root) and item['bounds'] == prepared['branch_bounds'][branch],
                       'no_root_or_lifetime_reset')
        release = bound_read(item['release'])
        code_release = branch in ('F3', 'A3') and (
            Path(item['release']['path']) == root / 'CYCLE_RELEASE_READY.json'
            and type(release.get('cycle')) is int and 'request_sha256' in release)
        shared.require((release.get('status') == 'RELEASED' or code_release)
                       and item['predecessors'] and item['preserved_files'],
                       'release_and_lineage_evidence_required')
        shared.require(type(item['next_cycle']) is int and item['next_cycle'] > 0,
                       'explicit_next_cycle')
        for identity in item['predecessors']:
            shared.require(type(identity['pid']) is int and identity['pid'] > 0,
                           'positive_predecessor_pid')
            shared.require(not (Path('/proc') / str(identity['pid'])).exists(),
                           'predecessor_still_alive')
        for name, expected in item['preserved_files'].items():
            path = root / name
            shared.require(not Path(name).is_absolute() and path.resolve().is_relative_to(root)
                           and shared.sha(path) == expected, 'preserved_boundary_bytes')
    return document


def adopt(entries, common_root, handoff_binding):
    prepared = readiness(entries, common_root)
    handoff = released_handoff(handoff_binding, prepared)
    current = route.adoption_inputs(prepared['branch_specs']['F1']['root'])
    shared.require(current['checkpoint'] == handoff['latest_F1_checkpoint'],
                   'adopt_latest_released_F1_never_historical_candidate')
    shared.require(current['initial_history'].get('F1'), 'preserve_F1_rehearsal_history')
    shared.checked_checkpoint(current['checkpoint'])
    shared.require(set(current['prior_metrics']) == set(shared.METRICS)
                   and all(value is None or type(value) is int and value >= 0
                           for value in current['prior_metrics'].values()), 'explicit_prior_counters')
    for branch, rows in current['initial_history'].items():
        for row in rows:
            shared.validate_row(row, prepared['branch_specs'][branch], prepared['excluded_ids'])
    adoption = dict(current, schema='R118_SHARED_ADOPTION_V1',
                    branch_bounds=prepared['branch_bounds'], readiness=prepared['readiness'],
                    handoff=deepcopy(handoff_binding), no_lifetime_reset=True)
    root = Path(common_root).resolve()
    with shared.locked(root / 'adoption'):
        path = root / 'ADOPTION.json'
        if path.exists():
            shared.require(shared.read(path) == adoption, 'adoption_is_immutable')
        else:
            shared.write(path, adoption)
        state = shared.initialize(root, prepared['branch_specs'], current['checkpoint'],
            excluded_ids=prepared['excluded_ids'], prior_metrics=current['prior_metrics'],
            initial_history=current['initial_history'])
        bindings = {branch: dict(branch=branch, root=str(root),
            config_sha256=shared.sha(root / 'CONFIG.json'), adoption_path=str(path),
            adoption_sha256=shared.sha(path)) for branch in shared.BRANCHES}
        receipt = dict(schema='R118_SHARED_INITIALIZED_V1', state=state, bindings=bindings,
                       optimizer_updates=0, actors_launched=0, handoff=handoff_binding)
        destination = root / 'INITIALIZED.json'
        if destination.exists():
            shared.require(shared.read(destination) == receipt, 'initialization_receipt_is_immutable')
        else:
            shared.write(destination, receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('inspect', 'adopt'))
    parser.add_argument('--roster', type=Path, required=True)
    parser.add_argument('--common-root', type=Path, required=True)
    parser.add_argument('--handoff', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    entries = shared.read(args.roster)
    if args.phase == 'inspect':
        result = readiness(entries, args.common_root)
    else:
        shared.require(args.handoff is not None, 'released_handoff_required')
        result = adopt(entries, args.common_root, reference(args.handoff))
    if args.output:
        shared.write(args.output, result)
    print(json.dumps(dict(phase=args.phase, branches=len(entries),
                         actors_launched=0, optimizer_updates=0), sort_keys=True))


if __name__ == '__main__':
    main()
