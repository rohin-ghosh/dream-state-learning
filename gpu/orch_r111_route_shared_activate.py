"""Bind Main's actual adoption, archive predecessor metadata, then strict launch."""

import argparse
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import time

from gpu import orch_r111_route_boundary as boundary
from gpu import orch_r111_route_shared as client


def bound_read(reference):
    path = Path(reference['path']).resolve(strict=True)
    boundary.require(boundary.sha(path) == reference['sha256'], 'exact_artifact_binding')
    return boundary.read(path)


def stage(root, initialized_reference):
    root = Path(root).resolve(strict=True)
    initialized = bound_read(initialized_reference)
    boundary.require(initialized['schema'] == 'R118_SHARED_INITIALIZED_V1', 'Main_initialization_receipt')
    boundary.require(set(initialized['bindings']) == {'F1', 'F2', 'F3', 'F4', 'A1', 'A2', 'A3', 'A4'},
                     'all_eight_Main_bindings')
    template = boundary.read(root / 'R118_SHARED_SUCCESSOR_PLAN_TEMPLATE.json')
    ready = bound_read(template['ready'])
    branch = ready['branch']
    binding = initialized['bindings'][branch]
    boundary.require(Path(initialized_reference['path']).parent.resolve() == Path(ready['common_root']).resolve(),
                     'Main_exact_common_root')
    boundary.require(binding['branch'] == branch and binding['root'] == ready['common_root'], 'same_shared_branch')
    adoption_reference = dict(path=binding['adoption_path'], sha256=binding['adoption_sha256'])
    adoption = bound_read(adoption_reference)
    boundary.require(adoption['readiness'][branch] == template['ready'], 'Main_selected_exact_v2r1_READY')
    certificate = boundary.read(root / 'R118_SHARED_HANDOFF_BRANCH.json')
    all_released = bound_read(adoption['handoff'])
    boundary.require(all_released['branches'][branch]['release'] == certificate['release'],
                     'Main_adopted_this_actual_release')
    for identity in certificate['predecessors']:
        boundary.require(not (Path('/proc') / str(identity['pid'])).exists(), 'old_process_absent')
    for name, expected in certificate['preserved_files'].items():
        boundary.require(boundary.sha(root / name) == expected, 'preactivation_preserved_boundary')
    boundary.require(boundary.reference(root / 'PLAN.json') == template['original_plan'], 'old_PLAN_still_current')
    plan = deepcopy(template['plan'])
    plan['shared_learner'] = binding
    plan['route_boundary_release'] = certificate['release']
    boundary.require(plan['bounds'] == adoption['branch_bounds'][branch] == ready['inherited_bounds']
                     and plan['parent_wait_seconds'] == 120, 'unchanged_caps_and_wait')
    client.Session(root, plan)
    directory = root / 'R118_SHARED_BOUND_METADATA'
    directory.mkdir(exist_ok=True)
    plan_path = directory / 'PLAN.json'
    boundary.write_new(plan_path, plan)
    publication = boundary.read(root / 'PUBLICATION.json')
    publication.update(plan_sha256=boundary.sha(plan_path), cpu_tests_passed=True,
        cpu_receipt=ready['tests_receipt'], shared_initialization=initialized_reference,
        coordination_reference='R118 Main all8 coordinated release 2026-09-15T12:05Z; actual Main ADOPTION bound')
    boundary.write_new(directory / 'PUBLICATION.json', publication)
    names = ['PLAN.json', 'PUBLICATION.json']
    if branch == 'F1':
        approval = boundary.read(root / 'ROHIN_GO.json')
        boundary.require(approval['authorization'] == 'WATCHER_RELAYED_ROHIN_DONE', 'preserved_original_GO')
        approval.update(plan_sha256=boundary.sha(plan_path), shared_initialization=initialized_reference,
            predecessor_GO=boundary.reference(root / 'ROHIN_GO.json'),
            source_reference='R118 user/Main explicit coordinated shared launch after all8 release and Main ADOPTION')
        boundary.write_new(directory / 'ROHIN_GO.json', approval)
        names.append('ROHIN_GO.json')
    receipt = dict(schema='R118_ROUTE_SHARED_BOUND_METADATA_V1', root=str(root), branch=branch,
        initialized=initialized_reference, ready=template['ready'], successor_source=ready['successor_source'],
        originals={name: boundary.reference(root / name) for name in names},
        replacements={name: boundary.reference(directory / name) for name in names},
        certificate=boundary.reference(root / 'R118_SHARED_HANDOFF_BRANCH.json'),
        prepared_unix=time.time(), launched=False)
    destination = root / 'R118_SHARED_BOUND_METADATA.json'
    boundary.write_new(destination, receipt)
    return boundary.reference(destination)


def replace_preserving(root, staged):
    archive = root / 'R118_SHARED_PREDECESSOR_FILES'
    archive.mkdir(exist_ok=True)
    for name, replacement in staged['replacements'].items():
        original = staged['originals'][name]
        bound_read(replacement)
        path = root / name
        backup = archive / (name + '.' + original['sha256'])
        current = boundary.sha(path)
        boundary.require(current in (original['sha256'], replacement['sha256']), 'no_foreign_metadata_edits')
        if current == original['sha256']:
            if backup.exists():
                boundary.require(boundary.sha(backup) == original['sha256'], 'preserved_original_bytes')
            else:
                os.link(path, backup)
            temporary = archive / (name + '.replacement.' + str(os.getpid()))
            with temporary.open('xb') as stream:
                stream.write(Path(replacement['path']).read_bytes())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        else:
            boundary.require(backup.exists() and boundary.sha(backup) == original['sha256'], 'earlier_replacement_preserved')
    return {name: boundary.reference(archive / (name + '.' + original['sha256']))
            for name, original in staged['originals'].items()}


def launch(root, staged_reference):
    root = Path(root).resolve(strict=True)
    staged = bound_read(staged_reference)
    boundary.require(staged['root'] == str(root), 'exact_staged_root')
    bound_read(staged['initialized'])
    ready = bound_read(staged['ready'])
    certificate = bound_read(staged['certificate'])
    boundary.require(not (root / 'TERMINAL.json').exists(), 'no_terminal_masking')
    for identity in certificate['predecessors']:
        boundary.require(not (Path('/proc') / str(identity['pid'])).exists(), 'no_live_predecessor')
    from gpu import orch_r111_route_pair_shared as successor

    boundary.require(Path(successor.__file__).resolve() == Path(staged['successor_source']) / 'gpu/orch_r111_route_pair_shared.py'
                     and boundary.sha(successor.__file__) == ready['executable']['sha256'], 'exact_frozen_executable')
    with (root / 'R118_SHARED_ACTIVATION_LOCK').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        attempt_path = root / 'R118_SHARED_DISPATCH_ATTEMPT.json'
        boundary.require(not attempt_path.exists(), 'inspect_prior_dispatch_before_any_retry')
        archives = replace_preserving(root, staged)
        boundary.write_new(attempt_path, dict(staged=staged_reference, started_unix=time.time(),
            archived_predecessor_metadata=archives, no_quota_reset=True))
        result = successor.launch(root, recovery=True)
        receipt = dict(result, shared_binding=boundary.read(root / 'PLAN.json')['shared_learner'],
                       staged=staged_reference, archived_predecessor_metadata=archives)
        destination = root / 'R118_SHARED_DISPATCH.json'
        boundary.write_new(destination, receipt)
        return boundary.reference(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('stage', 'launch'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--binding-sha256', required=True)
    arguments = parser.parse_args()
    reference = dict(path=str(arguments.binding), sha256=arguments.binding_sha256)
    result = stage(arguments.root, reference) if arguments.phase == 'stage' else launch(arguments.root, reference)
    print(json.dumps(result, sort_keys=True))
