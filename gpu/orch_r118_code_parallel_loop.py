"""Unactivated CODE successor: pooled parallel sleep, then settled fresh DEV."""

import argparse
from copy import deepcopy
import fcntl
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from gpu import orch_r107_base_anchors_inventory as anchor_module
from gpu import orch_r108_code_parent_r116_shared as client
from gpu import orch_r108_code_parent_r116_shared_run as lifecycle
from gpu import orch_r118_code_parallel_handoff as handoff
from gpu import orch_r118_code_parallel_pending as pending
from gpu import orch_r118_parallel_consolidation as consolidation


io, require = client.coordinator, client.require
MODULE = 'gpu.orch_r118_code_parallel_loop'
SOURCE_ROOT = Path(__file__).resolve().parents[1]


def validate_runtime(service, *, clock=time.time):
    service = Path(service)
    runtime = io.read(service / 'RUNTIME.json')
    require(runtime['schema'] == 'R118_CODE_PARALLEL_RUNTIME_V1', 'CODE_runtime_schema')
    root = Path(runtime['root']).resolve(strict=True)
    document, own, plan = handoff.authorize(runtime['authorization'], root, 'LAUNCH', clock)
    released = handoff.checked(runtime['handoff'])
    require(released['schema'] == 'R118_CODE_PARALLEL_RELEASE_V1' and released['root'] == str(root)
        and released['all_original_processes_exited'] is True
        and not handoff.alive(released['native']['identity']) and not handoff.alive(released['guardian']),
        'actual_CODE_predecessor_release')
    require(released['bounds'] == {key: plan[key] for key in client.BOUND_FIELDS}, 'original_lifetime_caps')
    for name, expected in released['native']['boundary']['preserved_files'].items():
        require(io.sha(root / name) == expected, 'handoff_evidence_unchanged')
    charged, unused = handoff.ledger(root)
    require(charged['preserved'] == {name: expected for name, expected in
        released['native']['boundary']['preserved_files'].items() if name.startswith('reservations/')},
        'no_post_handoff_reservation')
    require(runtime['source_root'] == str(SOURCE_ROOT)
        and own['source_manifest_sha256'] == runtime['source_manifest']['sha256'], 'Main_pinned_successor_source')
    manifest = handoff.checked(runtime['source_manifest'])
    require(all(io.sha(SOURCE_ROOT / name) == expected for name, expected in manifest.items()), 'frozen_source_closure')
    cpu = handoff.checked(runtime['cpu_tests'])
    require(cpu['passed'] is True and cpu['cuda_initialized'] is False
        and cpu['source_manifest_sha256'] == runtime['source_manifest']['sha256'],
        'own_frozen_CPU_tests')
    require(runtime['next_cycle'] == released['native']['boundary']['next_cycle'], 'exact_next_cursor')
    require(client.run.policy.digest(client.run.policy.tasks('TRAIN')) ==
        released['native']['boundary']['train_registry_sha256'], 'original_frozen_TRAIN_registry')
    require(runtime['train_end_unix'] == min(handoff.TRAIN_END, plan['hard_deadline_unix'])
        and runtime['hard_end_unix'] == min(handoff.HARD_END, plan['hard_deadline_unix'], plan['lease_end_unix'] - 21600),
        'tighter_parallel_bounds_no_extension')
    common = Path(runtime['common_root']).resolve(strict=True)
    require(own['common_root'] == str(common) and own['checkpoint_sha256'] ==
        released['native']['boundary']['state']['checkpoint']['path_sha256'], 'coordinated_common_checkpoint')
    require(io.read(common / 'STATE.json') == released['native']['boundary']['state'], 'no_stale_launch_checkpoint')
    generation = released['native']['boundary']['state']['generation']
    require(not (common / f'generation_{generation:06d}/sleep/START.json').exists(),
        'no_new_running_or_failed_sleep_before_launch')
    boundary = released['native']['boundary']
    if boundary.get('kind') == pending.MODE:
        require(own.get('boundary_mode') == pending.MODE, 'Main_pending_LAUNCH_mode')
        current = pending.snapshot(root, common)
        require(current['pending'] == boundary['pending'] and current['state'] == boundary['state']
            and current['charges'] == boundary['charges'], 'exact_pending_custody_before_launch')
    require(Path(runtime['activation_directory']).is_absolute(), 'explicit_Main_collective_paths')
    for name in ('activation_directory', 'anchor_root', 'anchor_task_ids', 'campaign'):
        require(runtime[name] == own[name], 'Main_bound_collective_and_anchor_inputs')
    campaign, unused = consolidation.campaign_document(runtime['campaign']['path'], runtime['campaign']['sha256'])
    require(campaign['root'] == str(common) and campaign['mode'] == 'CUDA_INPLACE'
        and campaign['activation_directory'] == runtime['activation_directory']
        and campaign['first_generation'] <= generation
        and clock() < campaign['deadline_unix'] <= runtime['train_end_unix'],
        'same_Main_campaign_root_generation_and_bounds')
    return runtime, released, plan


def prepare_runtime(service, root, authorization, release_reference, *, clock=time.time):
    service, root = Path(service), Path(root).resolve(strict=True)
    require(not service.exists(), 'new_service_no_runtime_overwrite')
    require(service.resolve().is_relative_to(root), 'new_owned_service_sidecar')
    document, own, plan = handoff.authorize(authorization, root, 'LAUNCH', clock)
    released = handoff.checked(release_reference)
    runtime = dict(schema='R118_CODE_PARALLEL_RUNTIME_V1', root=str(root), authorization=authorization,
        handoff=release_reference, source_root=str(SOURCE_ROOT),
        source_manifest=handoff.ref(SOURCE_ROOT.parent / 'SOURCE_SHA256.json'),
        cpu_tests=handoff.ref(SOURCE_ROOT.parent / 'CPU_TESTS.json'),
        next_cycle=released['native']['boundary']['next_cycle'],
        train_end_unix=min(handoff.TRAIN_END, plan['hard_deadline_unix']),
        hard_end_unix=min(handoff.HARD_END, plan['hard_deadline_unix'], plan['lease_end_unix'] - 21600),
        **{key: own[key] for key in ('common_root', 'activation_directory', 'anchor_root', 'anchor_task_ids', 'campaign')})
    service.mkdir(parents=True)
    io.write(service / 'RUNTIME.json', runtime)
    validate_runtime(service, clock=clock)
    io.write(service / 'PREPARED.json', dict(runtime=handoff.ref(service / 'RUNTIME.json'),
        observed_unix=clock(), activated=False, no_new_calls=True))
    return runtime


def owner_request(service, interpreter, *, clock=time.time):
    service = Path(service)
    runtime, released, plan = validate_runtime(service, clock=clock)
    require(Path(interpreter).is_absolute(), 'absolute_native_interpreter')
    envelope_path = Path(runtime['handoff']['path']).with_name('OWNER_RELEASE.json')
    envelope = io.read(envelope_path)
    require(envelope['release'] == runtime['handoff'] and envelope['status'] == 'RELEASED',
        'same_actual_owner_release_envelope')
    manifest = handoff.checked(runtime['source_manifest'])
    boundary = released['native']['boundary']
    result = dict(handoff=handoff.ref(envelope_path), inherited_bounds=envelope['bounds'],
        boundary=dict(committed_checkpoint_sha256=boundary['state']['checkpoint']['path_sha256'],
            mounted_checkpoint_sha256=boundary['state']['checkpoint']['path_sha256'],
            fresh_dev=boundary['dev']['complete'], settled_cursor=runtime['handoff']),
        command=[str(interpreter), '-B', '-m', MODULE, 'guard', '--service', str(service)],
        cwd=str(SOURCE_ROOT), source_files={str(SOURCE_ROOT / name): expected for name, expected in manifest.items()},
        env=dict(CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(SOURCE_ROOT), PYTHONDONTWRITEBYTECODE='1',
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'),
        bootstrap_path=str(service / 'FRESH_BOOTSTRAP.json'),
        device=dict(kind='cuda', physical=plan['physical'], uuid=plan['gpu_uuid']))
    if boundary.get('kind') == pending.MODE:
        result['boundary'] = dict(committed_checkpoint_sha256=boundary['state']['checkpoint']['path_sha256'],
            mounted_checkpoint_sha256=None, canonical_reload_required=True,
            settled_pending_consolidation=boundary['pending_reference'], settled_cursor=boundary['pending_cursor'])
    io.write(service / 'OWNER_REQUEST.json', result)
    return result


def stop_identity(identity, *, grace=2):
    if not handoff.alive(identity):
        return
    descriptor = os.pidfd_open(identity['pid'])
    try:
        require(handoff.alive(identity), 'exact_owned_pidfd_stop')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        try:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        except ProcessLookupError:
            return
        if not select.select([descriptor], [], [], grace)[0]:
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            require(select.select([descriptor], [], [], 2)[0], 'exact_owned_process_exited')
    finally:
        os.close(descriptor)


def owned_readouts(identity, root):
    result = []
    for directory in Path('/proc').iterdir():
        if not directory.name.isdecimal() or int(directory.name) == identity['pid']:
            continue
        try:
            fields = (directory / 'stat').read_text().rsplit(') ', 1)[1].split()
            if int(fields[2]) != identity['pid'] or fields[0] == 'Z':
                continue
            child = handoff.identities.identity(int(directory.name))
            command = (directory / 'cmdline').read_bytes().split(b'\0')
            require(child['uid'] == identity['uid'] and str(root).encode() in command
                and b'readout' in command and b'gpu.orch_r108_code_parent_r116_shared_run' in command,
                'only_exact_owned_readout_in_native_session')
            result.append(child)
        except FileNotFoundError:
            continue
    return result


def cleanup_native(identity, root):
    descriptor = None
    try:
        if handoff.alive(identity):
            descriptor = os.pidfd_open(identity['pid'])
            require(handoff.alive(identity), 'exact_cleanup_actor')
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            for unused in range(100):
                state = (Path('/proc') / str(identity['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()[0]
                if state in ('T', 't'):
                    break
                time.sleep(.01)
            else:
                raise ValueError('cleanup_actor_not_stopped')
        children = owned_readouts(identity, root)
        for child in children:
            stop_identity(child)
        stop_identity(identity)
        require(not owned_readouts(identity, root), 'no_orphaned_readout')
        return dict(native=identity, readouts=children, no_pattern_kill=True)
    finally:
        if descriptor is not None:
            try:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            except ProcessLookupError:
                pass
            os.close(descriptor)


def ordered_anchors(runtime, tokenizer, config):
    inventory, receipt = anchor_module.build_inventory(Path(runtime['anchor_root']), tokenizer, 16384,
        expected_manifest_sha256=config['anchor_sha256'])
    anchors = [row for family in sorted(inventory) for row in inventory[family]]
    require(len(anchors) == 42 and [row['task_id'] for row in anchors] == runtime['anchor_task_ids'],
        'same_original_F1_anchor_order')
    return anchors, receipt


class Session(client.Session):
    def __init__(self, root, plan, *, pending_boundary=None):
        if pending_boundary is None:
            super().__init__(root, plan)
            return
        require(pending_boundary['kind'] == pending.MODE, 'explicit_pending_session_only')
        current = pending.snapshot(root, plan['shared_learner']['root'])
        require(current['pending'] == pending_boundary['pending'] and current['state'] == pending_boundary['state'],
            'pending_session_exact_custody')
        super().__init__(root, plan, readout=True)
        unfinished = [handoff.ref(path) for path in self.root.glob('shared_cycles/*/SHARED_SUBMISSION.json')
            if not (path.parent / 'SHARED_SLEEP.json').exists()]
        require(unfinished == [pending_boundary['pending']['local_submission']], 'only_authorized_unfinished_submission')

    def configure(self, runtime, service, anchors):
        require(self.branch in ('F3', 'A3') and self.owner is False, 'CODE_is_not_optimizer_owner')
        self.runtime, self.service, self.anchors = runtime, Path(service), anchors

    def sleep(self, engine, optimizer, anchors, rows, episode_ids, output, save_callback, check,
              *, consolidate_call=consolidation.launch_at_boundary,
              await_activation=consolidation.await_campaign_activation,
              pause=time.sleep, clock=time.time, **options):
        require(optimizer is None and save_callback is None and not options, 'no_CODE_optimizer_or_serial_fallback')
        output = Path(output)
        generation = self.state['generation']
        require(len(episode_ids) == len(set(episode_ids)) == 2 and rows, 'exact_two_episodes')
        require(not (output / 'SHARED_SUBMISSION.json').exists(), 'no_charged_cycle_resubmission')
        for row in rows:
            source = io.read(row['source_call_path'])
            require(source['shared_learner'] == self.capture_binding()
                and source['shared_generation'] == generation
                and source['shared_checkpoint_sha256'] == self.loaded_reference['path_sha256'],
                'before_dispatch_native_generation_binding')
        check('parallel_submit')
        submitted = io.submit(self.shared_root, self.branch, generation,
            self.loaded_reference['path_sha256'], episode_ids, rows)
        io.write(output / 'SHARED_SUBMISSION.json', submitted)
        return self.consolidate_existing(engine, output, submitted, check,
            consolidate_call=consolidate_call, await_activation=await_activation, pause=pause, clock=clock)

    def consolidate_existing(self, engine, output, submitted, check, *,
            consolidate_call=consolidation.launch_at_boundary,
            await_activation=consolidation.await_campaign_activation, pause=time.sleep, clock=time.time):
        output = Path(output)
        generation = self.state['generation']
        submission = handoff.checked(submitted)
        local = io.read(output / 'SHARED_SUBMISSION.json')
        require(local['path'] == submitted['path'] and local['sha256'] == submitted['sha256']
            and submission['branch'] == self.branch and submission['generation'] == generation
            and submission['checkpoint_sha256'] == self.loaded_reference['path_sha256'],
            'existing_submission_current_child')
        rows, episode_ids = submission['rows'], submission['episode_ids']
        charged, train = handoff.ledger(self.root)
        require(all(row['status'] != 'STARTED' for path, row in train), 'no_inflight_native_or_parent')
        while not handoff.parents_settled(self.root, train):
            check('settle_existing_parent_publication')
            require(clock() < self.runtime['train_end_unix'] - 30, 'fixed_parent_settlement_window')
            pause(1)
        carry = handoff.checked(self.runtime['handoff'])['native']['boundary']['carry']
        io.write(output / 'PARALLEL_CARRY.json', dict(settings=deepcopy(self.driver.settings), inherited=carry))
        preserved = dict(charged['preserved'])
        for path in (self.root / 'PLAN.json', output / 'SHARED_SUBMISSION.json', output / 'PARALLEL_CARRY.json'):
            preserved[str(path.relative_to(self.root))] = io.sha(path)
        certificate = dict(branch=self.branch, root=str(self.root), generation=generation,
            checkpoint_sha256=self.loaded_reference['path_sha256'], identity=consolidation.process_identity(),
            status='SAFE_FOR_PARALLEL', bounds=dict(train_end_unix=self.runtime['train_end_unix'],
                hard_end_unix=self.runtime['hard_end_unix'], native_used=charged['native_used'],
                parent_used=charged['parent_used'], native_cap=self.plan['native_cap'], parent_cap=self.plan['parent_cap']),
            preserved_files=preserved, submission_sha256=submitted['sha256'],
            preceding_cursor_settled=self.cursor_reference, local_optimizer=False)
        certificate.update(launch_device=dict(kind='cuda', physical=self.plan['physical'], uuid=self.plan['gpu_uuid'],
            cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES', '')),
            retained_supervision=io.read(self.service / 'SUPERVISION.json'))
        consolidation.validate_launch_participant(certificate, self.branch, 'CUDA_INPLACE')
        certificate_path = output / 'SAFE_FOR_PARALLEL.json'
        io.write(certificate_path, certificate)
        campaign = self.runtime['campaign']
        activation_reference = await_activation(campaign['path'], campaign['sha256'], self.branch,
            handoff.ref(certificate_path), check=check)
        activation = handoff.checked(activation_reference)
        activation_path = Path(activation_reference['path'])
        require(activation['root'] == str(self.shared_root) and activation['generation'] == generation
            and activation['participants'][self.branch] == handoff.ref(certificate_path), 'Main_exact_live_certificate')
        claim = output / 'PARALLEL_CALL_ONCE'
        claim.mkdir()
        result = consolidate_call(activation_path=activation_path,
            activation_sha256=io.sha(activation_path), branch=self.branch, engine=engine.underlying,
            optimizer=None, anchor_module=anchor_module, anchors=self.anchors,
            anchor_root=Path(self.runtime['anchor_root']), save_checkpoint=None, check=check, clock=clock)
        require(result['status'] == 'COMPLETE_ALL8_INPLACE'
            and result['state']['generation'] == generation + 1, 'one_actual_parallel_commit')
        self.state = result['state']
        self.loaded_reference = deepcopy(self.state['checkpoint'])
        receipt = dict(result, branch=self.branch, optimizer_owner='F1', local_optimizer_steps=0,
            completed_unix=clock(), same_CODE_engine=True, serial_equivalent=False,
            activation=handoff.ref(activation_path))
        io.write(output / 'SHARED_SLEEP.json', receipt)
        return receipt


def settle_readout(root, session, ordinal, check, *, launch=lifecycle.schedule_readout, pause=time.sleep):
    child = launch(root, session, ordinal, 'DEV')
    while child.poll() is None:
        check('settle_existing_fresh_DEV')
        pause(.25)
    require(child.returncode == 0, 'readout_process_failed_no_replay')
    receipt = handoff.readout_settled(root, ordinal)
    require(receipt is not None, 'all_DEV_FOCUS_OPEN_legacy_cells_settled')
    return dict(receipt, observed_process_returncode=child.returncode)


def run_cycles(driver, tasks, start, stop, check, *, run_cycle=lifecycle.cycle,
               settle=settle_readout, clock=time.time):
    session = driver.session
    for ordinal in range(start, stop + 1):
        if clock() >= min(session.runtime['train_end_unix'] - 300, session.runtime['hard_end_unix'] - 120):
            break
        require(not any((driver.root / 'reservations').glob(f'C{ordinal:03d}_*.json')), 'next_cycle_already_charged')
        check('next_fresh_scheduled_cycle')
        result = run_cycle(driver, tasks[(ordinal - 1) * 2:ordinal * 2], ordinal)
        finish_committed_cycle(driver, ordinal, result, check, settle=settle, clock=clock)
    return session.cursor_reference


def finish_committed_cycle(driver, ordinal, result, check, *, settle=settle_readout, clock=time.time):
    session = driver.session
    io.write(driver.root / 'cycles' / f'C{ordinal:03d}_COMPLETE.json', dict(cycle=ordinal,
        completed_unix=clock(), optimizer_owner='F1', local_optimizer_steps=0,
        shared_generation=session.state['generation'], shared_sleep=result,
        sleep_buffer_rows=len(driver.cycle_sources.get(ordinal, []))))
    dev = settle(driver.root, session, ordinal, check)
    cursor = dict(cycle=ordinal, next_cycle=ordinal + 1, dev=dev, state=deepcopy(session.state),
        native_identity=handoff.identities.identity(os.getpid()), all_readouts_settled=True,
        reflection_settings=deepcopy(driver.settings), observed_unix=clock())
    path = session.service / 'cursors' / f'C{ordinal:03d}.json'
    io.write(path, cursor)
    session.cursor_reference = handoff.ref(path)
    return session.cursor_reference


def resume_pending(driver, boundary, check, *, resume=None, finish=finish_committed_cycle):
    session = driver.session
    require(boundary['kind'] == pending.MODE and session.state == boundary['state'], 'pending_resume_current_state')
    resume = resume or getattr(consolidation, 'resume_pending_consolidation', None)
    require(callable(resume), 'Herschel_pending_resume_API_required')
    resumed = resume(root=session.shared_root, branch=session.branch,
        session_path=Path(os.environ['R118_PARALLEL_SESSION']),
        session_sha256=os.environ['R118_PARALLEL_SESSION_SHA256'], check=check)
    expected = boundary['pending']
    require(resumed['status'] == 'PENDING_CONSOLIDATION_READY_NO_NEW_CALLS'
        and resumed['existing_submission_reused'] is True and resumed['new_native_calls'] == 0
        and resumed['optimizer_updates'] == 0 and resumed['cycle'] == boundary['cycle']
        and resumed['next_cycle'] == boundary['next_cycle'] and resumed['generation'] == session.state['generation']
        and resumed['episode_ids'] == expected['episode_ids']
        and resumed['submission']['path'] == expected['submission']['path']
        and resumed['submission']['sha256'] == expected['submission']['sha256']
        and resumed['rows'] == handoff.checked(expected['submission'])['rows'], 'pending_reuse_exact_no_submit')
    ordinal = boundary['cycle']
    driver.cycle_sources[ordinal] = [Path(row['source_call_path']) for row in resumed['rows']]
    result = session.consolidate_existing(driver.engine,
        driver.root / 'shared_cycles' / f'C{ordinal:03d}', resumed['submission'], check)
    require(session.state['generation'] == boundary['state']['generation'] + 1, 'pending_actual_commit_before_collection')
    return finish(driver, ordinal, result, check)


def bootstrap(session, engine, check):
    require(os.environ.get('R118_PARALLEL_BRANCH') == session.branch, 'Main_fresh_session_branch')
    path = Path(os.environ['R118_PARALLEL_SESSION'])
    expected = os.environ['R118_PARALLEL_SESSION_SHA256']
    require(path.is_absolute() and io.sha(path) == expected, 'Main_frozen_fresh_session')
    document = io.read(path)
    require(document['owners'][session.branch]['bootstrap_path'] == str(session.service / 'FRESH_BOOTSTRAP.json'),
        'Main_exact_owned_bootstrap_path')
    setup = getattr(consolidation, 'bootstrap_fresh_actor', None)
    wait = getattr(consolidation, 'wait_fresh_collection_go', None)
    require(callable(setup) and callable(wait), 'Herschel_fresh_session_API_required_no_fallback')
    receipt = setup(root=session.shared_root, branch=session.branch, engine=engine.underlying, optimizer=None,
        session_path=path, session_sha256=expected)
    io.write(session.service / 'BOOTSTRAP.json', dict(receipt=receipt, session=handoff.ref(path)))
    wait(path, expected, session.branch, check=check)
    return receipt


def native(service):
    service = Path(service)
    runtime, released, plan = validate_runtime(service)
    root = Path(runtime['root'])
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'exact_CODE_UUID')
    (service / 'NATIVE_ONCE').mkdir()

    def check(phase):
        require(time.time() < runtime['hard_end_unix'] - 5, 'parallel_hard_wall')
        return client.run.forward_check(root, phase)

    adopted = io.read(root / 'SHARED_ACTIVATION.json')
    boundary = released['native']['boundary']
    pending_boundary = boundary if boundary.get('kind') == pending.MODE else None
    session = Session(root, dict(plan, shared_learner=adopted['shared_learner']), pending_boundary=pending_boundary)
    session.plan = plan
    engine = session.load_engine(plan, check)
    anchors, anchor_receipt = ordered_anchors(runtime, engine.tokenizer, session.config)
    session.configure(runtime, service, anchors)
    driver = client.Driver(root, engine, session)
    driver.settings = deepcopy(released['native']['boundary']['carry']['reflection_settings'])
    session.driver = driver
    session.cursor_reference = runtime['handoff']
    clean = False
    try:
        initialized = bootstrap(session, engine, check)
        io.write(service / 'ACTOR_READY.json', dict(identity=handoff.identities.identity(os.getpid()),
            generation=session.state['generation'], checkpoint=deepcopy(session.loaded_reference),
            next_cycle=runtime['next_cycle'], carry=deepcopy(driver.settings), anchor_receipt=anchor_receipt,
            CODE_optimizer=None, initial_BASE_readout_replayed=False, raw_engine_reused_across_parallel_sleeps=True,
            bootstrap=initialized, initial_process_RNG='MAIN_SESSION_SEED_OR_SAVED_PARALLEL_RANK_RNG'))
        tasks = client.run.policy.tasks('TRAIN')
        if pending_boundary is not None:
            require(initialized['startup_action'] == pending.ACTION
                and initialized['settled_pending_consolidation'] == pending_boundary['pending_reference'],
                'Main_bootstrap_pending_action_binding')
            resume_pending(driver, pending_boundary, check)
        cursor = run_cycles(driver, tasks, runtime['next_cycle'], plan['cycles'], check)
        engine.verify_base()
        io.write(service / 'CLEAN_RELEASE.json', dict(cursor=cursor, identity=handoff.identities.identity(os.getpid()),
            actual_settled_boundary=True, observed_unix=time.time(), charges=handoff.ledger(root)[0]))
        clean = True
    finally:
        io.write(service / 'TERMINAL.json', dict(clean=clean, observed_unix=time.time(), no_replay=True))


def guard(service):
    service = Path(service)
    runtime, unused, plan = validate_runtime(service)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard')
    require(callable(getattr(consolidation, 'bootstrap_fresh_actor', None))
        and callable(getattr(consolidation, 'wait_fresh_collection_go', None))
        and callable(getattr(consolidation, 'await_campaign_activation', None))
        and callable(getattr(consolidation, 'resume_pending_consolidation', None)),
        'complete_pinned_Herschel_API_before_GPU_admission')
    handoff.previous.original.bind(plan['physical'])
    (service / 'GUARD_ONCE').mkdir()
    with (Path('/tmp') / ('orch_r115_f3_' + plan['gpu_uuid'] + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        snapshot = handoff.previous.scan(Path(runtime['root']))
        require(handoff.previous.admitted(snapshot, plan), 'fresh_privileged_full_admission')
        io.write(service / 'ADMISSION.json', snapshot)
        validate_runtime(service)
        with (service / 'NATIVE.log').open('x') as output:
            child = subprocess.Popen([sys.executable, '-B', '-m', MODULE, 'native', '--service', str(service)],
                cwd=SOURCE_ROOT, stdout=output, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid'],
                    PYTHONPATH=str(SOURCE_ROOT), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'))
            identity = handoff.identities.identity(child.pid)
            io.write(service / 'LAUNCH.json', dict(identity=identity,
                guardian=handoff.identities.identity(os.getpid()), runtime=handoff.ref(service / 'RUNTIME.json')))
            while child.poll() is None and time.time() < runtime['hard_end_unix'] - 5:
                time.sleep(1)
            cleanup = cleanup_native(identity, runtime['root'])
            child.wait(timeout=2)
            io.write(service / 'GUARD_TERMINAL.json', dict(returncode=child.returncode,
                identity=identity, observed_unix=time.time(), native_alive=handoff.alive(identity), cleanup=cleanup))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entry', choices=('prepare', 'owner-request', 'native', 'guard'))
    parser.add_argument('--service', required=True, type=Path)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--handoff', type=Path)
    parser.add_argument('--interpreter', type=Path)
    args = parser.parse_args()
    if args.entry == 'prepare':
        require(args.root is not None and args.authorization is not None and args.handoff is not None,
            'explicit_Main_preparation_inputs')
        prepare_runtime(args.service, args.root, handoff.ref(args.authorization), handoff.ref(args.handoff))
    elif args.entry == 'owner-request':
        require(args.interpreter is not None, 'explicit_native_interpreter')
        owner_request(args.service, args.interpreter)
    else:
        (native if args.entry == 'native' else guard)(args.service)
