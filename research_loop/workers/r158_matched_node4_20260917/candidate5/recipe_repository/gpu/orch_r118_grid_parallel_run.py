"""Fresh-exec GRID CLI and strict guard; inert without Main's all-eight session."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


TERMINAL = 'R118_GRID_PARALLEL_TERMINAL.json'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def verify_file(reference):
    path = Path(reference['path'])
    require(path.is_absolute() and not path.is_symlink() and
            hashlib.sha256(path.read_bytes()).hexdigest() == reference['sha256'], 'exact_pinned_file')
    return path


def read(reference):
    return json.loads(verify_file(reference).read_bytes())


def modules(plan):
    source = Path(__file__).resolve().parents[1]
    runtime = Path(plan['runtime']).resolve(strict=True)
    require(source != runtime and not (source / '.git').exists(), 'new_immutable_overlay_not_live_repo')
    candidate = read(plan['candidate'])
    for name, expected in candidate['source_files'].items():
        require(hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, 'candidate_source_changed')
    require(str(Path(__file__).resolve()) in candidate['source_files'], 'CLI_in_frozen_closure')
    sys.path.insert(0, str(runtime))
    import gpu
    gpu.__path__.insert(0, str(source / 'gpu'))
    from gpu import orch_r118_grid_parallel_handoff as handoff
    from gpu import orch_r118_grid_parallel_loop as loop
    require(Path(handoff.run.__file__).resolve().parents[1] == runtime, 'original_readout_runtime')
    ready = handoff.repaired_source(plan['root'], plan['repair_ready'])
    repair_path = Path(ready['bundle']) / 'orch_r118_grid_shared_repair.py'
    spec = importlib.util.spec_from_file_location('grid_parallel_original_repair', repair_path)
    repair = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(repair)
    repair.bind_references(Path(ready['bundle']))
    return handoff, loop


def validate(plan, handoff, *, released=True):
    require(plan['schema'] == 'R118_GRID_PARALLEL_EXEC_V1' and plan['branch'] in ('F4', 'A4'),
            'grid_fresh_exec_plan')
    root = Path(plan['root']).resolve(strict=True)
    require(Path(plan['directory']).resolve().is_relative_to(root) and
            not (root / TERMINAL).exists(), 'new_own_single_use_era')
    require(os.environ.get('R118_PARALLEL_BRANCH') == plan['branch'] and
            os.environ.get('R118_PARALLEL_SESSION') and os.environ.get('R118_PARALLEL_SESSION_SHA256'),
            'Main_dispatcher_injected_fresh_session_required')
    boundary = read(plan['boundary'])
    handoff.validate_snapshot(boundary)
    require(boundary['branch'] == plan['branch'] and boundary['root'] == str(root), 'same_released_grid_branch')
    startup, unused = handoff.parallel.fresh_session(Path(os.environ['R118_PARALLEL_SESSION']),
                                                    os.environ['R118_PARALLEL_SESSION_SHA256'])
    require(startup['root'] == boundary['session']['shared_root'] and
            startup['state']['generation'] == boundary['session']['generation'] and
            startup['state']['checkpoint'] == boundary['session']['checkpoint'], 'Main_fresh_session_exact_child')
    handoff.parallel.fresh_releases(startup)
    config = handoff.shared.read(root / 'CONFIG.json')
    require(plan['bounds'] == boundary['bounds'] == handoff.run.inherited_bounds(config), 'original_boundaries_caps')
    require(time.time() < plan['bounds']['train_end_unix'], 'original_TRAIN_deadline')
    if released:
        release = read(plan['release'])
        require(release['status'] == 'RELEASED' and release['boundary'] == plan['boundary'] and
                release['root'] == str(root) and release['next_cycle'] == boundary['next_cycle'],
                'actual_own_release_not_planned')
        require(read(release['release'])['status'] in ('FAILED', 'COMPLETE'), 'authentic_repair_terminal')
        from gpu import orch_r118_grid_final_drain as process
        for identity in (release['predecessor_identity'], release['guard_identity']):
            try:
                actual = process.identity(identity['pid'])
            except FileNotFoundError:
                continue
            require(not process.same_process(actual, identity) or actual['state'] == 'Z',
                    'predecessor_native_and_guard_must_exit')
    return root, config, boundary


def wait_file(path, deadline, check, *, pause=time.sleep, clock=time.time):
    while not Path(path).exists():
        check('grid_parallel_file_wait')
        require(clock() < deadline, 'bounded_wait_no_extension')
        pause(.25)
    return path


def final_module(plan):
    previous = read(plan['previous_final_plan'])
    verify_file(previous['source'])
    spec = importlib.util.spec_from_file_location('grid_parallel_frozen_final', previous['source']['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, previous


def retire_old_timers(plan, handoff):
    from gpu import orch_r118_grid_final_drain as process

    final, previous = final_module(plan)
    require(previous['branch_root'] == plan['root'] and len(plan['old_final_identities']) == 2,
            'own_original_drain_and_evaluator_only')
    require(not (Path(previous['output']) / 'DISPATCH.json').exists(), 'never_retire_dispatched_FINAL')
    retired = []
    for expected in plan['old_final_identities']:
        try:
            actual = process.identity(expected['pid'])
        except FileNotFoundError:
            retired.append(dict(identity=expected, already_exited=True))
            continue
        if not process.same_process(actual, expected) or actual['state'] == 'Z':
            retired.append(dict(identity=expected, already_exited=True))
            continue
        require(actual['uid'] == os.getuid(), 'same_user_timer')
        directory = Path('/proc') / str(expected['pid'])
        command_bytes = (directory / 'cmdline').read_bytes()
        command = [part.decode() for part in command_bytes.split(b'\0') if part]
        require(hashlib.sha256(command_bytes).hexdigest() == expected['command_sha256'] and
                command.count('--plan') == 1 and command[command.index('--plan') + 1] ==
                plan['previous_final_plan']['path'] and
                any(Path(part).name in ('orch_r118_grid_final.py', 'orch_r118_grid_final_drain.py')
                    for part in command) and 'readout' not in command, 'exact_own_CPU_final_timer_command')
        environment = (directory / 'environ').read_bytes().split(b'\0')
        require(b'CUDA_VISIBLE_DEVICES=' in environment, 'CPU_timer_only')
        descriptor = os.pidfd_open(expected['pid'])
        try:
            require(process.same_process(process.identity(expected['pid']), expected), 'timer_PID_not_reused')
            process.send(descriptor, expected, signal.SIGTERM)
            for unused in range(100):
                if process.exited(descriptor):
                    break
                time.sleep(.02)
            require(process.exited(descriptor), 'old_timer_did_not_retire')
        finally:
            os.close(descriptor)
        retired.append(dict(identity=expected, already_exited=False))
    return retired


def certificate(plan, handoff, session, cycle, submitted):
    root = Path(plan['root'])
    directory = Path(plan['directory'])
    common = Path(session['shared_root'])
    path = common / f"generation_{session['generation']:06d}" / f"{session['branch']}.json"
    require(submitted['submission']['path'] == str(path) and
            submitted['submission']['sha256'] == handoff.shared.sha(path), 'actual_generation_submission')
    rows = handoff.run.read_ledger(root)
    paths = [root / 'LEDGER.jsonl', root / 'CARRY.json', root / 'CONFIG.json',
             root / 'cycles' / f'{cycle:04d}' / 'TRAIN_COMPLETE.json', Path(submitted['packet']['path'])]
    for folder in ('calls', 'parent_queue', 'parent_received', 'triples'):
        paths.extend(sorted((root / folder).rglob('*.json')))
    support = handoff.shared.read(directory / 'SUPERVISION.json')
    config = handoff.shared.read(root / 'CONFIG.json')
    result = dict(branch=session['branch'], root=str(root), generation=session['generation'],
        checkpoint_sha256=session['checkpoint_sha256'], identity=handoff.parallel.process_identity(),
        status='SAFE_FOR_PARALLEL', submission_sha256=handoff.shared.sha(path),
        preserved_files={str(item.relative_to(root)):handoff.shared.sha(item) for item in paths},
        bounds=dict(train_end_unix=plan['bounds']['train_end_unix'], hard_end_unix=plan['bounds']['hard_end_unix'],
            native_used=sum(item['kind'] == 'NATIVE' for item in rows), native_cap=handoff.run.grid.MAX_NATIVE,
            parent_used=sum(item['kind'] == 'PARENT' for item in rows), parent_cap=handoff.run.grid.MAX_PARENT),
        launch_device=dict(kind='cuda', physical=config['physical'], uuid=config['uuid'],
                           cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES']),
        retained_supervision=support['retained_supervision'])
    handoff.supervision(result)
    output = directory / f'PARTICIPANT_{session["generation"]:06d}.json'
    handoff.shared.write(output, result)
    return handoff.reference(output)


def native(plan, handoff, loop):
    root, config, boundary = validate(plan, handoff)
    handoff.run.validate(root, gpu=True)
    directory = Path(plan['directory'])
    identity = handoff.parallel.process_identity()
    handoff.shared.write(directory / 'NATIVE_IDENTITY.json', dict(identity=identity,
        process=[identity['boot_id'], identity['pid'], identity['start_ticks']]))
    check = handoff.run.check_deadline
    wait_file(directory / 'SUPERVISION.json', min(time.time() + 300, handoff.run.grid.TRAIN_END), check)
    session = boundary['session']
    decoder = handoff.run.client.load_shared(session, model_dir=config['model_dir'], gpu_uuid=config['uuid'],
        check=check, predecessor_processes=(tuple(boundary['identity'][name] for name in ('boot_id','pid','start_ticks')),))
    bootstrap_before_collection(handoff, decoder, session, directory, check)
    session_path = Path(os.environ['R118_PARALLEL_SESSION'])
    session_sha = os.environ['R118_PARALLEL_SESSION_SHA256']
    support = handoff.shared.read(directory / 'SUPERVISION.json')
    entry = dict(schema='R118_GRID_PARALLEL_ENTRY_V1', status='MAIN_ALL8_COORDINATED_GO',
        authority='HERSCHEL_VERIFIED_FRESH_SESSION_AND_ALL8_COLLECTION_GO',
        startup_session=dict(path=str(session_path), sha256=session_sha),
        issued_unix=time.time(), expires_unix=handoff.run.grid.TRAIN_END,
        branches={branch:{} for branch in handoff.shared.BRANCHES})
    entry['branches'][session['branch']] = dict(root=str(root), generation=session['generation'],
        checkpoint_sha256=session['checkpoint_sha256'], native_identity=identity,
        rng_provenance='EXPLICIT_NEW_PROCESS_STARTUP_NOT_INHERITED', candidate=plan['candidate'],
        boundary=plan['boundary'], supervision_certificate=handoff.reference(directory / 'SUPERVISION.json'))
    handoff.shared.write(directory / 'ENTRY.json', entry)
    from gpu import orch_r107_base_anchors_inventory as anchors

    def activation(reference, check):
        return campaign_activation(plan, handoff, reference, check)

    result = loop.run_loop(root=root, decoder=decoder, session=session, boundary=boundary,
        entry_reference=handoff.reference(directory / 'ENTRY.json'), config=config, anchor_module=anchors,
        anchor_root=plan['anchor_root'], certificate_for_submission=lambda *args:certificate(plan, handoff, *args),
        activation_for_certificate=activation, check=check)
    handoff.shared.write(directory / 'COMPLETE.json', result)


def campaign_activation(plan, handoff, certificate, check):
    campaign = plan['campaign']
    document, unused = handoff.parallel.campaign_document(campaign['path'], campaign['sha256'])
    require(document['root'] == plan['common_root'] and
            document['deadline_unix'] <= plan['bounds']['train_end_unix'],
            'same_COMMON_original_campaign_deadline')
    require(callable(getattr(handoff.parallel, 'await_campaign_activation', None)),
            'pinned_central_autoarm_API_required')
    return handoff.parallel.await_campaign_activation(campaign['path'], campaign['sha256'],
        plan['branch'], certificate, check=check)


def bootstrap_before_collection(handoff, decoder, session, directory, check):
    session_path = Path(os.environ['R118_PARALLEL_SESSION'])
    session_sha = os.environ['R118_PARALLEL_SESSION_SHA256']
    require(decoder.loaded.optimizer is None, 'grid_peer_optimizer_None')
    require(callable(getattr(handoff.parallel, 'bootstrap_fresh_actor', None)) and
            callable(getattr(handoff.parallel, 'wait_fresh_collection_go', None)), 'pinned_Herschel_fresh_API_required')
    bootstrap = handoff.parallel.bootstrap_fresh_actor(root=session['shared_root'], branch=session['branch'],
        engine=decoder.loaded.engine, optimizer=None, session_path=session_path, session_sha256=session_sha)
    handoff.shared.write(directory / 'FRESH_BOOTSTRAP_RETURN.json', bootstrap)
    handoff.parallel.wait_fresh_collection_go(session_path, session_sha, session['branch'], check=check)
    decoder.verify_base()
    return bootstrap


def rebound_final_plan(previous, output, guard_reference, native_reference, handoff):
    root = Path(previous['branch_root'])
    output = Path(output)
    require(output.is_absolute() and not output.exists() and not output.is_relative_to(root),
            'new_separate_eval_only_output')
    guard = handoff.checked(guard_reference)
    native = handoff.checked(native_reference)
    require(guard['terminal_filename'] == TERMINAL, 'actual_successor_terminal')
    identity = guard['identity']
    result = deepcopy(previous)
    result.update(output=str(output), predecessor_refs=[guard_reference, native_reference],
        predecessor_processes=[identity, dict(native['identity'], uid=identity['uid'],
            start_ticks=str(native['identity']['start_ticks']))])
    require(all(result[name] == value for name, value in previous.items()
                if name not in ('output', 'predecessor_refs', 'predecessor_processes')),
            'only_FINAL_identity_output_rebind')
    return result


def timer(plan, handoff):
    directory = Path(plan['directory'])
    handoff.shared.write(directory / 'TIMER_IDENTITY.json', handoff.parallel.process_identity())
    wait_file(directory / 'FINAL_PLAN.ref.json', handoff.run.grid.TRAIN_END, handoff.run.check_deadline)
    final, previous = final_module(plan)
    current = handoff.checked(handoff.shared.read(directory / 'FINAL_PLAN.ref.json'))
    final.validate_plan(current)
    final.guard(current, final.COMMON / 'FINAL_SELECTION.json')


def guard(plan, handoff, loop, plan_reference):
    from gpu import orch_r118_grid_final_drain as process

    root, config, boundary = validate(plan, handoff)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_guard')
    directory = Path(plan['directory'])
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'GUARD_ONCE').mkdir()
    identity = process.identity(os.getpid())
    handoff.shared.write(directory / 'CPU_LAUNCH.json', dict(identity=identity, terminal_filename=TERMINAL,
        source=handoff.reference(__file__), plan=plan_reference))
    child = None
    child_descriptor = None
    try:
        for attempt in range(120):
            report = handoff.run.scan(root)
            handoff.shared.write(directory / 'admission' / f'{attempt:03d}.json', report)
            require(report['gpu']['uuid'] == config['uuid'], 'only_assigned_grid_GPU')
            if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
                break
            require(time.time() < handoff.run.grid.TRAIN_END, 'original_admission_deadline')
            time.sleep(2)
        else:
            raise ValueError('strict_GPU_admission_failed_no_waiver')
        validate(plan, handoff)
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'native', '--plan',
                   plan_reference['path'], '--sha256', plan_reference['sha256']]
        duration = max(1, int(handoff.run.grid.TRAIN_END - time.time()))
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=config['uuid'], HF_HUB_OFFLINE='1',
            TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
        with (directory / 'NATIVE.log').open('x') as log:
            child = subprocess.Popen(['timeout', '--signal=TERM', '--kill-after=5s', f'{duration}s', *command],
                cwd=plan['runtime'], env=environment, stdin=subprocess.DEVNULL, stdout=log,
                stderr=subprocess.STDOUT, start_new_session=True)
        child_descriptor = os.pidfd_open(child.pid)
        handoff.shared.write(directory / 'DISPATCH.json', dict(pid=child.pid, command=command,
            deadline=handoff.run.grid.TRAIN_END, plan=plan_reference))
        wait_file(directory / 'NATIVE_IDENTITY.json', time.time() + 120, handoff.run.check_deadline)
        native_doc = handoff.shared.read(directory / 'NATIVE_IDENTITY.json')
        require(process.identity(native_doc['identity']['pid'])['ppid'] == child.pid,
                'actual_owned_timeout_native_child')
        guard_identity = {key:identity[key] for key in ('boot_id', 'pid', 'start_ticks')}
        guard_identity['start_ticks'] = int(guard_identity['start_ticks'])
        guard_binding = dict(root=str(root), native_identity=native_doc['identity'], guard_identity=guard_identity,
                             terminal_filename=TERMINAL)
        handoff.shared.write(directory / 'GUARD_BINDING.json', guard_binding)
        timer_command = [sys.executable, '-B', str(Path(__file__).resolve()), 'timer', '--plan',
                         plan_reference['path'], '--sha256', plan_reference['sha256']]
        with (directory / 'TIMER.log').open('x') as log:
            timer_process = subprocess.Popen(timer_command, cwd=plan['runtime'], env=dict(environment,
                CUDA_VISIBLE_DEVICES=''), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True)
        wait_file(directory / 'TIMER_IDENTITY.json', time.time() + 60, handoff.run.check_deadline)
        timer_identity = handoff.shared.read(directory / 'TIMER_IDENTITY.json')
        require(timer_identity['pid'] == timer_process.pid, 'actual_new_timer_identity')
        retired = retire_old_timers(plan, handoff)
        final, old_plan = final_module(plan)
        final_output = Path(plan['final_output'])
        final_plan = rebound_final_plan(old_plan, final_output, handoff.reference(directory / 'CPU_LAUNCH.json'),
                                       handoff.reference(directory / 'NATIVE_IDENTITY.json'), handoff)
        final.validate_plan(final_plan)
        handoff.shared.write(final_output / 'PLAN.json', final_plan)
        handoff.shared.write(directory / 'FINAL_PLAN.ref.json', handoff.reference(final_output / 'PLAN.json'))
        final_binding = dict(root=str(root), native_identity=native_doc['identity'], timer_identity=timer_identity,
            old_timer_retired=True, retired=retired, canonical_selection_schema='R118_FINAL_SELECTION_V1',
            evaluation_only=True, plan=handoff.reference(final_output / 'PLAN.json'))
        handoff.shared.write(directory / 'FINAL_BINDING.json', final_binding)
        support = dict(branch=plan['branch'], root=str(root), identity=native_doc['identity'],
            retained_supervision=dict(native_identity=native_doc['identity'], guard_identity=guard_identity,
                guard_binding=handoff.reference(directory / 'GUARD_BINDING.json'), owner_verified_safe_for_parallel=True,
                final_identity_bindings=[dict(identity=timer_identity,
                    evidence=handoff.reference(directory / 'FINAL_BINDING.json'))]))
        handoff.supervision(support)
        handoff.shared.write(directory / 'SUPERVISION.json', support)
        code = child.wait()
        handoff.shared.write(root / TERMINAL, dict(status='COMPLETE' if code == 0 else 'FAILED', exit_code=code,
            finished_unix=time.time(), no_retry=True, final_timer_pid=timer_process.pid))
    except BaseException as error:
        if child_descriptor is not None and not process.exited(child_descriptor):
            signal.pidfd_send_signal(child_descriptor, signal.SIGTERM)
            child.wait(timeout=10)
        if not (root / TERMINAL).exists():
            handoff.shared.write(root / TERMINAL, dict(status='FAILED', error=type(error).__name__ + ': ' + str(error),
                finished_unix=time.time(), no_retry=True))
        raise
    finally:
        if child_descriptor is not None:
            os.close(child_descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('validate', 'guard', 'native', 'timer', 'snapshot', 'drain',
                                         'crash-snapshot', 'crash-release', 'pending-snapshot'))
    parser.add_argument('--plan', required=True)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    plan_reference = dict(path=args.plan, sha256=args.sha256)
    plan = read(plan_reference)
    handoff, loop = modules(plan)
    if args.mode in ('snapshot', 'crash-snapshot', 'pending-snapshot'):
        session = handoff.run.client.prepare(plan['common_root'], plan['branch'],
                                            config_sha256=plan['common_config_sha256'])
        kwargs = dict(session=session, cycle=plan['cycle'], ready_reference=plan['repair_ready'],
                      native_identity=plan['native_identity'])
        if args.mode == 'crash-snapshot':
            result = handoff.recovery_snapshot(plan['root'], **kwargs, guard_identity=plan['guard_identity'],
                output=Path(plan['output']).parent / 'disposition')
        elif args.mode == 'pending-snapshot':
            result = handoff.pending_snapshot(plan['root'], **kwargs,
                output=Path(plan['output']).parent / 'PENDING_CURSOR.json')
        else:
            result = handoff.snapshot(plan['root'], **kwargs)
        handoff.shared.write(plan['output'], result)
        print(json.dumps(handoff.reference(plan['output'])))
    elif args.mode in ('drain', 'crash-release'):
        if args.mode == 'crash-release':
            result = handoff.release_crashed(authorization=plan['drain_authorization'],
                boundary_reference=plan['boundary'], output=plan['output'])
        else:
            session = handoff.run.client.prepare(plan['common_root'], plan['branch'],
                                                config_sha256=plan['common_config_sha256'])
            result = handoff.drain_at_settled_boundary(authorization=plan['drain_authorization'], root=plan['root'],
                session=session, cycle=plan['cycle'], ready_reference=plan['repair_ready'], output=plan['output'],
                pending=plan.get('pending_consolidation', False))
        if result['status'] == 'RELEASED':
            envelope = {name:result[name] for name in ('root', 'bounds', 'predecessors', 'preserved_files', 'next_cycle')}
            envelope.update(status='RELEASED', release=handoff.reference(Path(plan['output']) / 'RELEASE.json'))
            handoff.shared.write(Path(plan['output']) / 'HANDOFF.json', envelope)
            result['handoff'] = handoff.reference(Path(plan['output']) / 'HANDOFF.json')
        print(json.dumps(result))
    elif args.mode == 'validate':
        validate(plan, handoff)
        print(json.dumps(dict(status='VALIDATED_NOT_LAUNCHED', plan=plan_reference)))
    elif args.mode == 'guard':
        guard(plan, handoff, loop, plan_reference)
    elif args.mode == 'native':
        native(plan, handoff, loop)
    else:
        timer(plan, handoff)


if __name__ == '__main__':
    main()
