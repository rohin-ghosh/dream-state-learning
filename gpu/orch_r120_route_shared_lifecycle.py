"""Explicitly authorized route successor staging, strict launch and lifecycle rebinding."""

import argparse
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_r118_route_parallel_boundary as boundary
from gpu import orch_r120_route_clock as lease
boundary.TRAIN_END = lease.current()["train_end_unix"]
from gpu import orch_r118_route_parallel_cutoff as owned_cutoff
owned_cutoff.MODULE = 'gpu.orch_r120_route_shared_run'


require, read, sha, ref, bound, write = (boundary.require, boundary.read, boundary.sha,
    boundary.ref, boundary.bound, boundary.write)
MODULE = 'gpu.orch_r120_route_shared_run'
PLAN = 'R118_PARALLEL_PLAN.json'
TERMINAL = 'R118_PARALLEL_TERMINAL.json'


def stage(root, release, readiness, authorization, controls):
    root = Path(root).resolve(strict=True)
    permission, ready = bound(authorization), bound(readiness)
    require(permission.get('authorized') is True and permission.get('all_eight_released') is True
            and permission.get('common_handoff_coordinated') is True
            and permission.get('readiness_sha256') == readiness['sha256']
            and permission.get('release_sha256') == release['sha256'], 'Main_all8_released_before_staging')
    require(permission.get('lifecycle_rebinding_authorized') is True, 'explicit_cutoff_FINAL_broker_rebinding')
    snapshot = boundary.released(root, release)
    require(permission.get('checkpoint_sha256') == snapshot['checkpoint']['path_sha256'],
            'Main_exact_committed_checkpoint')
    original = read(root / 'PLAN.json')
    require(ready['branch'] == original['shared_learner']['branch']
            and ready['status'] == 'CPU_READY_NOT_ACTIVATED', 'own_ready_branch')
    require(time.time() < controls['activation_wait_end_unix'] <= boundary.TRAIN_END
            and controls['train_end_unix'] == boundary.TRAIN_END, 'fixed_common_TRAIN_window')
    require(controls['anchor_root'] == '/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1',
            'unchanged_anchor_inventory')
    require(controls['backend_source']['sha256'] == ready['backend_source']['sha256']
            and controls['backend_source'] == ready['backend_source'], 'exact_Herschel_backend')
    if ready.get('requires_campaign'):
        from gpu import orch_r120_route_shared_client as client
        client.validate_campaign(controls, original['shared_learner']['root'], ready['source_files'])
        controls = dict(controls, requires_campaign=True)
    plan = deepcopy(original)
    plan.update(parallel_control=controls, route_boundary_release=release,
        source_files=ready['source_files'], parallel_source=ready['source_root'],
        parallel_stage=dict(schema='R118_ROUTE_PARALLEL_STAGE_V1', original_plan=ref(root / 'PLAN.json'),
            readiness=readiness, authorization=authorization, boundary=bound(release)['boundary'],
            first_generation=snapshot['state']['generation'], source=ref(Path(__file__).resolve()),
            no_quota_reset=True, prior_metrics={name: snapshot['state'][name] for name in
                ('optimizer_steps', 'child_token_exposures', 'anchor_token_exposures')}))
    require(plan['bounds'] == original['bounds'] and plan['parent_wait_seconds'] == 120,
            'no_bound_or_parent_wait_changes')
    for name, expected in plan['source_files'].items():
        require(sha(name) == expected, 'frozen_successor_source')
    write(root / PLAN, plan)
    write(root / 'R118_PARALLEL_LIFECYCLE_REQUIRED.json', dict(
        new_guard='R118_PARALLEL_SUPERVISOR.json', actual_terminal=TERMINAL,
        old_PLAN_unchanged=ref(root / 'PLAN.json'), old_cutoff_and_FINAL_retirement='Main exact CPU identity receipts',
        successor_cutoff_module='gpu.orch_r118_route_parallel_cutoff',
        FINAL_consumer='gpu.orch_r111_route_final', canonical_selector_unchanged=True,
        broker_binding='R118_PARALLEL_BROKER_BINDING.json',
        no_fake_release=True, own_guard_hard_TRAIN_end=boundary.TRAIN_END))
    return ref(root / PLAN)


def verify_plan(root, *, gpu=False):
    root = Path(root).resolve(strict=True)
    plan = read(root / PLAN)
    physical = plan['physical']
    require(physical in boundary.prior.UUIDS and str(root) == boundary.prior.ROOT_TEMPLATE.format(physical)
            and plan['uuid'] == boundary.prior.UUIDS[physical], 'exact_owned_route')
    stage_document = plan['parallel_stage']
    old = bound(stage_document['original_plan'])
    permission = bound(stage_document['authorization'])
    require(permission['authorized'] is True and permission['all_eight_released'] is True,
            'explicit_coordinated_activation')
    require(lease.same_life(plan, old), 'no_lifetime_or_common_CONFIG_reset')
    for name, expected in plan['source_files'].items():
        require(sha(name) == expected, 'immutable_candidate_source')
    for name in ('orch_r120_route_shared_run.py', 'orch_r120_route_shared_client.py',
                 'orch_r118_route_parallel_boundary.py', 'orch_r120_route_shared_lifecycle.py'):
        require(str(Path(__file__).with_name(name).resolve()) in plan['source_files'], 'route_source_closure')
    require(sha(Path(plan['shared_learner']['root']) / 'CONFIG.json') == plan['shared_learner']['config_sha256'],
            'original_common_CONFIG')
    if gpu:
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['uuid'], 'exact_UUID_CVD')
        require(os.environ.get('PYTHONPATH', '').split(':')[0] == plan['parallel_source'], 'exact_source_root')
        require((root / 'R118_PARALLEL_ADMISSION.json').exists(), 'actual_strict_admission')
    return plan


def identity_exited(expected):
    try:
        return boundary.prior.identity(expected['pid']) != expected or boundary.prior.process_state(expected['pid']) == 'Z'
    except (FileNotFoundError, ProcessLookupError):
        return True


def verify_retirements(permission):
    receipt = bound(permission['old_CPU_lifecycle_retirement'])
    require(receipt['status'] == 'RETIRED_FOR_COORDINATED_SUCCESSOR'
            and set(receipt['identities']) == {'cutoff_monitor', 'cutoff_fuse', 'F1_FINAL', 'A1_FINAL'},
            'exact_old_CPU_lifecycle_roles')
    require(all(identity_exited(identity) for identity in receipt['identities'].values()),
            'old_CPU_waiters_really_retired_no_duplicates')


def validate_broker_binding(root, plan):
    document = read(Path(root) / 'R118_PARALLEL_BROKER_BINDING.json')
    require(document['root'] == str(root) and document['plan'] == ref(Path(root) / PLAN)
            and document['terminal'] == TERMINAL and document['parent_wait_seconds'] == plan['parent_wait_seconds'],
            'actual_successor_broker_root_plan_terminal')
    require(not identity_exited(document['identity']), 'actual_broker_identity')
    source = Path(document['source']['path'])
    require(source.is_absolute() and not source.is_symlink() and ref(source) == document['source'],
            'actual_broker_source_bytes')
    require(document['provider'] == plan['provider'], 'same_parent_provider')


def launch(root, interpreter):
    root = Path(root).resolve(strict=True)
    plan = verify_plan(root)
    require(time.time() < boundary.TRAIN_END - 180, 'launch_before_common_cutoff')
    boundary.released(root, plan['route_boundary_release'])
    verify_retirements(bound(plan['parallel_stage']['authorization']))
    validate_broker_binding(root, plan)
    with (root / 'R118_PARALLEL_LAUNCH.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (root / 'R118_PARALLEL_LAUNCH_ATTEMPT.json').exists(), 'single_launch_no_retry')
        write(root / 'R118_PARALLEL_LAUNCH_ATTEMPT.json', dict(plan=ref(root / PLAN), started_unix=time.time()))
        prefix = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                  'PYTHONPATH=' + plan['parallel_source'], 'python3', '-B', '-m', MODULE]
        subprocess.run(prefix + ['service', '--root', str(root)], capture_output=True, check=True, timeout=90)
        report = subprocess.run(prefix + ['scan', '--root', str(root)], capture_output=True, check=True, timeout=100)
        admission = json.loads(report.stdout)
        require(admission['clear'] is True, 'fresh_privileged_UUID_minor_proc_clear_no_waiver')
        write(root / 'R118_PARALLEL_ADMISSION.json', admission)
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONPATH=plan['parallel_source'],
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
        with (root / 'R118_PARALLEL_SUPERVISOR.log').open('x') as stream:
            process = subprocess.Popen([interpreter, '-B', '-m', MODULE, 'supervise', '--root', str(root)],
                cwd=plan['parallel_source'], env=environment, stdin=subprocess.DEVNULL, stdout=stream,
                stderr=subprocess.STDOUT, start_new_session=True)
        result = dict(supervisor=boundary.prior.identity(process.pid), started_unix=time.time(),
                      plan=ref(root / PLAN), native_loaded=False, no_recovery_loop=True)
        write(root / 'R118_PARALLEL_DISPATCH.json', result)
        return result


def pin_readout_children(expected, spec, handles):
    from gpu import orch_r118_route_parallel_cutoff as cutoff
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            observed = cutoff.identity(int(directory.name))
            if observed['ppid'] != expected['pid']:
                continue
            observed = cutoff.route_process(observed['pid'], spec, 'readout')
            key = (observed['pid'], observed['start_ticks'], observed['boot_id'])
            if key not in handles:
                descriptor = os.pidfd_open(observed['pid'])
                if cutoff.alive(observed):
                    handles[key] = (descriptor, observed)
                else:
                    os.close(descriptor)
        except (FileNotFoundError, ProcessLookupError):
            continue


def stop_guard_children(descriptor, expected, spec, readouts):
    from gpu import orch_r118_route_parallel_cutoff as cutoff
    expected = {key: value for key, value in expected.items() if key != 'cwd'}
    actor_stopped = False
    targets = []
    try:
        if not cutoff.exited(descriptor):
            cutoff.signal_bound(descriptor, expected, signal.SIGSTOP)
            actor_stopped = True
            cutoff.wait_stopped(descriptor, expected)
            pin_readout_children(expected, spec, readouts)
        targets = list(readouts.values()) + [(descriptor, expected)]
        for handle, identity in targets:
            if not cutoff.exited(handle):
                cutoff.signal_bound(handle, identity, signal.SIGTERM)
        if actor_stopped and not cutoff.exited(descriptor):
            cutoff.signal_bound(descriptor, expected, signal.SIGCONT)
            actor_stopped = False
        deadline = time.monotonic() + 20
        for handle, identity in targets:
            if not cutoff.exited(handle, max(0, deadline - time.monotonic())):
                cutoff.signal_bound(handle, identity, signal.SIGKILL)
        require(all(cutoff.exited(handle, 5) for handle, unused in targets), 'all_owned_GPU_children_exited')
        return dict(identities=[identity for unused, identity in targets], reason='ORIGINAL_DEADLINE_OR_ACTOR_EXIT',
                    unrelated_processes_signalled=False, all_exited=True)
    finally:
        if actor_stopped and not cutoff.exited(descriptor) and cutoff.alive(expected):
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)


def supervise(root, interpreter):
    root = Path(root).resolve(strict=True)
    plan = verify_plan(root, gpu=True)
    deadline = min(boundary.TRAIN_END, plan['bounds']['hard_end_unix'], plan['bounds']['lease_end_unix'] - 21600)
    with (root / 'R118_PARALLEL_SUPERVISOR.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (root / 'R118_PARALLEL_SUPERVISOR.json').exists(), 'one_supervisor_one_actor')
        from gpu import orch_r120_route_final_custody as final_custody
        custody_process, final_binding = final_custody.start(root, plan, boundary.prior.identity(os.getpid()), interpreter)
        with (root / 'R118_PARALLEL_ACTOR.log').open('x') as stream:
            process = subprocess.Popen([interpreter, '-B', '-m', MODULE, 'run', '--root', str(root)],
                stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
            expected = boundary.prior.identity(process.pid)
            descriptor = os.pidfd_open(process.pid)
            require(boundary.prior.identity(process.pid) == expected, 'exact_actor_pin')
            readouts = {}
            spec = dict(root=str(root), uid=os.getuid(), uuid=plan['uuid'], source_root=plan['parallel_source'])
            write(root / 'R118_PARALLEL_SUPERVISOR.json', dict(supervisor=boundary.prior.identity(os.getpid()),
                  actor=expected, plan=ref(root / PLAN), train_end_unix=deadline, automatic_retry=False))
            write(root / 'R118_PARALLEL_SUPERVISION_BINDING.json', lease.supervision(root, plan, expected,
                boundary.prior.identity(os.getpid()), ref(root / 'R118_PARALLEL_SUPERVISOR.json'), final_binding))
            try:
                while process.poll() is None and time.time() < deadline - 60:
                    pin_readout_children(expected, spec, readouts)
                    time.sleep(min(1, max(.01, deadline - 60 - time.time())))
                disposition = stop_guard_children(descriptor, expected, spec, readouts)
                process.wait(timeout=30)
                write(root / 'R118_PARALLEL_GUARD_TERMINAL.json', dict(returncode=process.returncode,
                      actor=expected, children=disposition, finished_unix=time.time(), automatic_retry=False,
                      no_STATE_changes=True))
            finally:
                for handle, unused in readouts.values():
                    os.close(handle)
                os.close(descriptor)


def rebind_final(branch, root, output, control_reference, selector_reference, cpu_reference):
    from gpu import orch_r111_route_final as final
    root = Path(root).resolve(strict=True)
    plan = verify_plan(root)
    verify_retirements(bound(plan['parallel_stage']['authorization']))
    control = bound(control_reference)
    require(control['routes'][branch]['plan'] == ref(root / PLAN)
            and control['routes'][branch]['source_root'] == plan['parallel_source'], 'actual_successor_cutoff_binding')
    return final.prepare(branch, root, output, control_reference, selector_reference, cpu_reference)


def rebind_cutoff(common, directory, peer_bindings):
    from gpu import orch_r118_route_parallel_cutoff as cutoff
    return cutoff.prepare(common, directory, peer_bindings)


def export_fresh_owner(root, directory, interpreter):
    root = Path(root).resolve(strict=True)
    return owner_export(root, directory, interpreter, verify_plan(root))


def prepare_fresh_owner(root, directory, interpreter, release, readiness):
    from gpu import orch_r120_route_shared_client as client
    root = Path(root).resolve(strict=True)
    original, ready = read(root / 'PLAN.json'), bound(readiness)
    require(ready['status'] == 'CPU_READY_NOT_ACTIVATED' and ready.get('requires_campaign') is True
            and ready['branch'] == original['shared_learner']['branch']
            and ready['original_plan'] == ref(root / 'PLAN.json')
            and ready['release'] == release, 'exact_prestage_readiness_release_PLAN')
    require(bound(ready['cpu'])['returncode'] == 0, 'tested_prestage_candidate')
    require(ready['backend_source'] == ref(Path(client.backend.__file__).resolve()),
            'actual_invoked_final_backend')
    require(ready['source_root'] == str(Path(__file__).resolve().parents[1]), 'actual_prestage_source_root')
    for name, digest in ready['source_files'].items():
        require(sha(name) == digest, 'immutable_prestage_source')
    for name in ('orch_r120_route_shared_run.py', 'orch_r120_route_shared_client.py',
                 'orch_r120_route_shared_lifecycle.py', 'orch_r118_route_crash_boundary.py'):
        require(str(Path(__file__).with_name(name).resolve()) in ready['source_files'], 'prestage_runtime_closure')
    plan = dict(original, route_boundary_release=release, parallel_source=ready['source_root'],
                source_files=ready['source_files'])
    return owner_export(root, directory, interpreter, plan, prepared=True)


def owner_export(root, directory, interpreter, plan, *, prepared=False):
    from gpu import orch_r120_route_shared_client as client
    root, directory = Path(root).resolve(strict=True), Path(directory).absolute()
    snapshot = boundary.released(root, plan['route_boundary_release'])
    release = bound(plan['route_boundary_release'])
    require(Path(interpreter).is_absolute() and Path(interpreter).is_file(), 'actual_native_interpreter')
    branch = plan['shared_learner']['branch']
    bounds = client.original_bounds(root, plan)
    envelope = dict(root=str(root), bounds=bounds, original_bounds=plan['bounds'],
        release=plan['route_boundary_release'],
        predecessors=[dict(boot_id=identity['boot_id'], pid=identity['pid'], start_ticks=int(identity['start_ticks']))
                      for identity in release.get('predecessors', [release['actor'], release['supervisor']])],
        preserved_files=snapshot['preserved_files'], next_cycle=snapshot['next_cycle'])
    write(directory / 'R118_PARALLEL_HANDOFF_BRANCH.json', envelope)
    cycle = root / f"cycle_{snapshot['completed_cycle']:04d}"
    if snapshot.get('recovery_mode') == 'CRASHED_POSTCOMMIT_MISSING_READOUT':
        proof = dict(kind='CRASHED_POSTCOMMIT', mode=snapshot['recovery_mode'],
            committed_checkpoint_sha256=snapshot['checkpoint']['path_sha256'], mounted_checkpoint_sha256=None,
            disposition=snapshot['readout_disposition'], readout_disposition=snapshot['readout_disposition'],
            postcommit_eval_disposition=snapshot['readout_disposition'], settled_cursor=snapshot['settled_cursor'],
            canonical_reload_required=True,
            restore_required_before_collection=True, fresh_DEV_success_claimed=False,
            mount_wrapper=ref(cycle / 'checkpoint/CHECKPOINT.json'))
    else:
        proof = dict(committed_checkpoint_sha256=snapshot['checkpoint']['path_sha256'],
                     mounted_checkpoint_sha256=snapshot['checkpoint']['path_sha256'],
                     fresh_dev=ref(root / f"readout_{snapshot['sleep']:04d}/COMPLETE.json"),
                     settled_cursor=ref(cycle / 'COMPLETE.json'), mount_wrapper=ref(cycle / 'checkpoint/CHECKPOINT.json'))
    owner = dict(handoff=ref(directory / 'R118_PARALLEL_HANDOFF_BRANCH.json'), inherited_bounds=bounds,
        boundary=proof,
        command=[str(interpreter), '-B', '-m', MODULE, 'launch', '--root', str(root)],
        cwd=plan['parallel_source'], source_files=plan['source_files'],
        env=dict(CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONPATH=plan['parallel_source'],
                 PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'),
        bootstrap_path=str(root / 'R118_PARALLEL_FRESH_BOOTSTRAP.json'),
        device=dict(kind='cuda', physical=plan['physical'], uuid=plan['uuid']))
    if prepared:
        owner.update(runtime_staged=False, requires_coordinated_stage_before_dispatch=True)
    path = directory / ('FRESH_OWNER_PREPARED.json' if prepared else 'FRESH_OWNER.json')
    write(path, owner)
    return dict(branch=branch, owner=ref(path), status='PREPARED_NOT_STAGED' if prepared else 'RELEASED_OWNER_NOT_DISPATCHED',
                no_common_writes=True, no_processes_started=True)


def bind_supervision(root, final_bindings, guard_binding):
    from gpu import orch_r118_parallel_consolidation as backend
    root = Path(root).resolve(strict=True)
    plan = verify_plan(root)
    guard = bound(guard_binding)
    require(guard['plan'] == ref(root / PLAN), 'actual_new_guard_plan')
    def minimal(identity):
        result = {key: identity[key] for key in ('boot_id', 'pid', 'start_ticks')}
        result['start_ticks'] = int(result['start_ticks'])
        backend.live_identity(result)
        return result
    native = minimal(guard['actor'])
    supervisor = minimal(guard['supervisor'])
    require(read(root / 'R118_PARALLEL_ACTOR_READY.json')['pid'] == native['pid'], 'loaded_current_native')
    require(bool(final_bindings), 'fresh_rebound_FINAL_waiter_required')
    for entry in final_bindings:
        backend.live_identity(entry['identity'])
        evidence = bound(entry['evidence'])
        require(evidence['branch'] == plan['shared_learner']['branch']
                and evidence['predecessor_plan'] == ref(root / PLAN), 'actual_rebound_FINAL_config')
    result = dict(guard_identity=supervisor, native_identity=native, guard_binding=guard_binding,
                  final_identity_bindings=final_bindings, owner_verified_safe_for_parallel=True)
    write(root / 'R118_PARALLEL_SUPERVISION_BINDING.json', result)
    return ref(root / 'R118_PARALLEL_SUPERVISION_BINDING.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('stage', 'launch', 'rebind-cutoff', 'rebind-final',
                                        'bind-supervision', 'export-fresh-owner', 'prepare-fresh-owner'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--release', type=Path)
    parser.add_argument('--readiness', type=Path)
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--controls', type=Path)
    parser.add_argument('--common', type=Path)
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--peer-bindings', type=Path)
    parser.add_argument('--branch', choices=('F1', 'A1'))
    parser.add_argument('--cutoff-control', type=Path)
    parser.add_argument('--selector', type=Path)
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--final-bindings', type=Path)
    parser.add_argument('--guard-binding', type=Path)
    parser.add_argument('--interpreter', default=sys.executable)
    arguments = parser.parse_args()
    if arguments.phase == 'stage':
        result = stage(arguments.root, ref(arguments.release), ref(arguments.readiness),
                       ref(arguments.authorization), read(arguments.controls))
    elif arguments.phase == 'launch':
        result = launch(arguments.root, sys.executable)
    elif arguments.phase == 'rebind-cutoff':
        result = rebind_cutoff(arguments.common, arguments.directory, ref(arguments.peer_bindings))
    elif arguments.phase == 'rebind-final':
        result = rebind_final(arguments.branch, arguments.root, arguments.directory,
                              ref(arguments.cutoff_control), ref(arguments.selector), ref(arguments.cpu))
    elif arguments.phase == 'export-fresh-owner':
        result = export_fresh_owner(arguments.root, arguments.directory, arguments.interpreter)
    elif arguments.phase == 'prepare-fresh-owner':
        result = prepare_fresh_owner(arguments.root, arguments.directory, arguments.interpreter,
                                     ref(arguments.release), ref(arguments.readiness))
    else:
        result = bind_supervision(arguments.root, read(arguments.final_bindings), ref(arguments.guard_binding))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
