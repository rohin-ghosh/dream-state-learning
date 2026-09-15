"""Export actual route releases and stage an unbound shared successor plan."""

import argparse
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import time

from gpu import orch_r111_route_boundary as boundary
from gpu import orch_r111_route_shared as client


def check_preserved(root, references):
    result = {}
    for reference in references:
        path = Path(reference['path']).resolve(strict=True)
        boundary.require(path.is_relative_to(root), 'preserved_file_inside_life')
        boundary.require(boundary.sha(path) == reference['sha256'], 'preserved_file_hash')
        result[str(path.relative_to(root))] = reference['sha256']
    return result


def preserve_uncharged_teardown(root, saved):
    empty = saved.get('empty_successor_start')
    if empty is None:
        return None
    start = Path(empty['path'])
    directory = start.parent
    extras = {path.name for path in directory.iterdir()} - {'START.json'}
    if not extras:
        return None
    boundary.require(extras == {'EPISODE_0.json'} and boundary.sha(start) == empty['sha256'],
                     'only_original_empty_cycle_teardown_diagnostic')
    boundary.require(boundary.sha(root / 'RESERVATIONS.jsonl') == saved['ledger']['sha256'],
                     'zero_new_native_or_parent_reservations')
    diagnostic = directory / 'EPISODE_0.json'
    episode = boundary.read(diagnostic)
    captures = episode.get('captures', [])
    boundary.require(episode.get('terminal_reason') == 'generation_failure'
                     and episode.get('actor_calls') == 1 and episode.get('reads') == []
                     and episode.get('routes') == [] and len(captures) == 1
                     and captures[0].get('response') is None
                     and captures[0].get('error') == dict(type='TimeoutError', message='owned_lifetime_signal'),
                     'exact_administrative_signal_not_a_generated_episode')
    archive = root / 'R118_SHARED_TEARDOWN_ARCHIVE' / directory.name
    archive.mkdir(parents=True, exist_ok=True)
    original_reference = boundary.reference(diagnostic)
    destination = archive / ('EPISODE_0_' + original_reference['sha256'] + '.json')
    if destination.exists():
        boundary.require(boundary.sha(destination) == original_reference['sha256'], 'unchanged_archive_bytes')
    else:
        os.link(diagnostic, destination)
    receipt = dict(original_path=str(diagnostic), original_sha256=original_reference['sha256'],
        archived=boundary.reference(destination), original_start=empty, original_ledger=saved['ledger'],
        native_calls_added=0, parent_calls_added=0, administrative_actor_attempts=1,
        reason='SIGTERM_before_first_reservation_preserve_diagnostic_resume_same_task',
        no_response_replay=True)
    receipt_path = archive / 'ARCHIVE.json'
    if receipt_path.exists():
        boundary.require(boundary.read(receipt_path) == receipt, 'same_archive_receipt')
    else:
        boundary.write_new(receipt_path, receipt)
    diagnostic.unlink()
    return boundary.reference(receipt_path)


def reconcile_exit(request_path):
    request_path = Path(request_path).resolve(strict=True)
    directory = request_path.parent
    request = boundary.read(request_path)
    root = Path(request['root']).resolve(strict=True)
    error = boundary.read(directory / 'ERROR.json')
    boundary.require(error['after_supervisor_termination'] is True
                     and error['error_type'] == 'ValueError', 'only_saved_post_signal_exit_timeout')
    boundary.require('actor_exit_no_SIGKILL' in (directory / 'CONTROLLER.log').read_text(),
                     'explicit_actor_teardown_timeout')
    authorization = boundary.read(directory / 'AUTH.json')
    boundary.require(authorization['request_sha256'] == boundary.sha(request_path)
                     and authorization['all_eight_ready'] is True
                     and authorization['common_handoff_coordinated'] is True, 'original_coordinated_authorization')
    saved_path = directory / 'BOUNDARY.json'
    saved = boundary.read(saved_path)
    boundary.require(saved['request'] == boundary.reference(request_path), 'same_saved_boundary_request')
    for role in ('actor', 'supervisor'):
        boundary.require(not (Path('/proc') / str(request[role]['pid'])).exists(), 'owned_process_still_present')
    with (root / 'LIFE_LOCK').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with (root / 'RESERVATIONS.jsonl').open('r') as ledger_lock:
            fcntl.flock(ledger_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            archive = preserve_uncharged_teardown(root, saved)
            current = boundary.completed_boundary(root, Path(saved['complete']['path']).parent)
            boundary.require(current is not None and all(saved[key] == value for key, value in current.items()),
                             'late_exit_boundary_and_all_charges_unchanged')
            boundary.require(boundary.reference(root / 'PLAN.json') == request['plan'], 'original_plan_unchanged')
            result = dict(status='RELEASED', released_unix=time.time(),
                boundary=boundary.reference(saved_path), actor=request['actor'], supervisor=request['supervisor'],
                no_restart=True, no_quota_reset=True, raw_node_only=True,
                original_plan=boundary.reference(root / 'PLAN.json'),
                release_detection='POST_TIMEOUT_IDENTITY_ABSENCE_RECONCILIATION', exact_exit_unix=None,
                preserved_controller_error=boundary.reference(directory / 'ERROR.json'),
                additional_signals=0, uncharged_teardown_archive=archive,
                source=boundary.reference(Path(__file__).resolve()))
            boundary.write_new(directory / 'RELEASED.json', result)
            return boundary.reference(directory / 'RELEASED.json')


def export(root, release_path):
    root, release_path = Path(root).resolve(strict=True), Path(release_path).resolve(strict=True)
    release_reference = boundary.reference(release_path)
    released = boundary.read(release_path)
    saved = boundary.released_boundary(root, release_reference)
    request = boundary.read(saved['request']['path'])
    boundary.require(boundary.sha(saved['request']['path']) == saved['request']['sha256'], 'bound_original_request')
    boundary.require(request['root'] == str(root) and request['purpose'] == 'SHARED_ADOPTION', 'shared_route_release')
    predecessors = [released['actor'], released['supervisor']]
    boundary.require(predecessors == [request['actor'], request['supervisor']], 'exact_released_predecessors')
    for identity in predecessors:
        boundary.require(not (Path('/proc') / str(identity['pid'])).exists(), 'released_predecessor_not_reaped_yet')
    plan = boundary.read(root / 'PLAN.json')
    boundary.require(boundary.reference(root / 'PLAN.json') == released['original_plan'], 'current_original_PLAN')
    boundary.require(plan['bounds'] == saved['bounds'] == request['bounds'], 'no_bounds_reset')
    branch = {0: 'F1', 4: 'A1'}.get(plan['physical'])
    boundary.require(branch is not None and plan['uuid'] == boundary.UUIDS[plan['physical']], 'owned_route_slot')
    with (root / 'LIFE_LOCK').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        references = [saved[name] for name in ('complete', 'checkpoint', 'optimizer', 'carry', 'ledger')]
        references.append(released['original_plan'])
        if released.get('uncharged_teardown_archive'):
            references.append(released['uncharged_teardown_archive'])
            references.append(boundary.read(released['uncharged_teardown_archive']['path'])['archived'])
        for name in ('pending_triple', 'empty_successor_start'):
            if saved.get(name):
                references.append(saved[name])
        cycle = Path(saved['complete']['path']).parent
        for name in ('START.json', 'ROWS.json', 'SLEEP.json', 'ENCODING.json', 'UPDATES.jsonl'):
            if (cycle / name).exists():
                references.append(boundary.reference(cycle / name))
        checkpoint = boundary.read(saved['checkpoint']['path'])
        references.extend(dict(path=str(Path(checkpoint['adapter']['path']) / name), sha256=expected)
                          for name, expected in checkpoint['adapter']['files'])
        preserved = check_preserved(root, references)
        next_cycle = boundary.successor_cycle(root, release_reference)
        checkpoint_reference = client.checkpoint_reference(saved['checkpoint']['path'])
        adoption_reference = None
        metrics = None
        if branch == 'F1':
            adoption = client.adoption_inputs(root)
            boundary.require(adoption['checkpoint'] == checkpoint_reference, 'latest_released_F1_not_older_candidate')
            adoption_path = root / 'R118_SHARED_RELEASED_ADOPTION_INPUTS.json'
            if adoption_path.exists():
                boundary.require(boundary.read(adoption_path) == adoption, 'same_released_adoption_inputs')
            else:
                boundary.write_new(adoption_path, adoption)
            adoption_reference = boundary.reference(adoption_path)
            metrics = adoption['prior_metrics']
        certificate = dict(schema='R118_SHARED_HANDOFF_BRANCH_V1', branch=branch, root=str(root),
            bounds=plan['bounds'], release=release_reference, predecessors=predecessors,
            preserved_files=preserved, next_cycle=next_cycle, checkpoint=checkpoint_reference,
            charged=saved['charged'], carry=saved['carry'], adoption_inputs=adoption_reference,
            prior_metrics=metrics, nonowner_optimizer_preserved_not_merged=branch != 'F1',
            source=boundary.reference(Path(__file__).resolve()), created_unix=time.time(),
            original_caps_preserved=True, parent_wait_seconds=plan['parent_wait_seconds'])
        destination = root / 'R118_SHARED_HANDOFF_BRANCH.json'
        if destination.exists():
            previous = boundary.read(destination)
            boundary.require(previous['release'] == release_reference and previous['preserved_files'] == preserved
                            and previous['next_cycle'] == next_cycle, 'existing_certificate_immutable')
            return boundary.reference(destination)
        boundary.write_new(destination, certificate)
        return boundary.reference(destination)


def prepare_successor(root, ready_reference):
    root = Path(root).resolve(strict=True)
    ready_path = Path(ready_reference['path']).resolve(strict=True)
    boundary.require(boundary.sha(ready_path) == ready_reference['sha256'], 'exact_selected_READY')
    ready = boundary.read(ready_path)
    boundary.require(ready_path.parent == root and ready['root'] == str(root)
                     and ready['schema'] == 'R116_SHARED_CLIENT_READY_V2', 'selected_route_v2')
    original_path = root / 'PLAN.json'
    boundary.require(boundary.sha(original_path) == ready['predecessor_plan_sha256'], 'original_PLAN_until_Main_adoption')
    plan = boundary.read(original_path)
    boundary.require(plan['bounds'] == ready['inherited_bounds'] and plan['parent_wait_seconds'] == 120,
                     'same_bounds_and_wait120')
    source = Path(ready['successor_source']).resolve(strict=True)
    closure = ready['source_closure']
    boundary.require(boundary.sha(closure['path']) == closure['sha256'], 'complete_closure_binding')
    files = boundary.read(closure['path'])['files']
    for name, expected in files.items():
        boundary.require(boundary.sha(source / name) == expected, 'complete_successor_sources_unchanged')
    template = deepcopy(plan)
    template['source_files'] = dict(plan['source_files'])
    template['source_files'].update({str(source / name): expected for name, expected in files.items()})
    template['shared_learner'] = None
    template['route_boundary_release'] = None
    result = dict(schema='R118_ROUTE_SHARED_PLAN_TEMPLATE_V1', branch=ready['branch'], root=str(root),
        ready=ready_reference, original_plan=boundary.reference(original_path), successor_source=str(source),
        plan=template, bound_and_launchable=False, missing_bindings=['Main CONFIG', 'Main ADOPTION', 'actual RELEASED'],
        command_module='gpu.orch_r111_route_pair_shared', command_phase='recover',
        no_live_PLAN_replacement=True, no_shared_initialization=True,
        required_prelaunch=['all_eight_released', 'Main ADOPTION/config hashes',
                            'preserve_original_PLAN_PUBLICATION_ROHIN_GO',
                            'bind_complete_source_and_release', 'fresh_privileged_admission'],
        broker_contract=dict(root_unchanged=True, queue='parent_queue', ledger='RESERVATIONS.jsonl',
            terminal='TERMINAL.json', wait_seconds=120, claims_no_reset=True, request_schema_unchanged=True))
    destination = root / 'R118_SHARED_SUCCESSOR_PLAN_TEMPLATE.json'
    if destination.exists():
        boundary.require(boundary.read(destination) == result, 'immutable_successor_template')
    else:
        boundary.write_new(destination, result)
    return boundary.reference(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('export', 'prepare', 'reconcile-exit'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--release', type=Path)
    parser.add_argument('--ready', type=Path)
    parser.add_argument('--ready-sha256')
    parser.add_argument('--request', type=Path)
    arguments = parser.parse_args()
    if arguments.phase == 'export':
        result = export(arguments.root, arguments.release)
    elif arguments.phase == 'reconcile-exit':
        result = reconcile_exit(arguments.request)
    else:
        result = prepare_successor(arguments.root, dict(path=str(arguments.ready), sha256=arguments.ready_sha256))
    print(json.dumps(result, sort_keys=True))
