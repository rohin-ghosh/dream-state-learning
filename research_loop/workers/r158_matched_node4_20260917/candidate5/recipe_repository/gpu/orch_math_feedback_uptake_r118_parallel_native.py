"""Executable fresh-exec F2/A2 guard/resident; no optimizer on math workers."""

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

from gpu import orch_math_feedback_uptake_r118_parallel_lifecycle as life
from gpu import orch_math_feedback_uptake_r118_parallel_run as loop
from gpu import orch_math_feedback_uptake_r118_parallel_recipe as recipe


shared, client, previous, require = life.shared, life.client, life.previous, life.require
MODULE, SOURCE = life.MODULE, life.SOURCE
FINALIZED_HOOK_SHA256 = 'c56bb57b69405877a65124b623316f9b8bd769aa8f51db6f2481ff65325c5cdb'


def verified_hook():
    require(loop.hook is life.hook and shared.sha(life.hook.__file__) == FINALIZED_HOOK_SHA256,
        'finalized_Herschel_v4_invoked_hook_required')
    return dict(path=str(Path(life.hook.__file__).resolve()), sha256=FINALIZED_HOOK_SHA256)


def runtime(service, *, initial=False):
    service = Path(service)
    plan = life.plan_for(service)
    document = shared.read(service/'RUNTIME.json')
    require(document['schema'] == 'R118_MATH_FRESH_EXEC_RUNTIME_V1'
            and document['plan'] == life.ref(service/'PLAN.json')
            and document['inherited_bounds'] == plan['inherited_bounds']
            and document['train_end_unix'] == life.TRAIN_END, 'exact_staged_runtime_bounds')
    life.checked(document['authorization'])
    life.released(service, require_unchanged=initial)
    return plan, document


def bootstrap(engine, document, check):
    verified_hook()
    session_path = Path(os.environ['R118_PARALLEL_SESSION'])
    session_sha = os.environ['R118_PARALLEL_SESSION_SHA256']
    require(os.environ['R118_PARALLEL_BRANCH'] == engine.session['branch'], 'central_fresh_branch_binding')
    published = life.checked(dict(path=str(session_path), sha256=session_sha))
    require(published['owners'][engine.session['branch']]['bootstrap_path'] == document['bootstrap_path'],
            'central_owner_bootstrap_path')
    result = life.hook.bootstrap_fresh_actor(root=engine.session['shared_root'], branch=engine.session['branch'],
        engine=engine.loaded.engine, optimizer=None, session_path=session_path, session_sha256=session_sha)
    require(result.get('startup_action') == 'COLLECT_NEW_TWO_EPISODES'
        and result.get('canonical_adapter_actually_verified') is True,
        'math_crash_disposition_requires_canonical_new_cycle_startup_action')
    engine.verify_base()
    life.hook.wait_fresh_collection_go(session_path, session_sha, engine.session['branch'], check=check)
    return result


def protected(service, plan):
    final = Path(plan['final_root'])
    return dict(native_launch=life.ref(service/'LAUNCH.json'), guard_receipt=life.ref(service/'GUARD_STARTED.json'),
        final_drain_plan=life.ref(service/'CUTOFF_PLAN.json'), final_evaluation_plan=life.ref(final/'PLAN.json'),
        final_timer=life.ref(final/'SCHEDULED.json'), final_drain_timer=life.ref(service/'CUTOFF_ARMED.json'),
        broker_config=life.ref(Path(plan['root'])/'BROKER_CONFIG.json'))


def supervision(service, plan, references):
    documents = life.boundary.fences(references)
    guard = life.boundary.minimal_identity(documents['guard_receipt']['identity'])
    native = life.hook.process_identity()
    require(life.boundary.minimal_identity(documents['native_launch']['identity']) == native,
            'actual_fresh_exec_native_not_previous_PID')
    life.hook.live_identity(guard)
    final_identities = [dict(identity=life.boundary.minimal_identity(documents[name]['identity']), evidence=references[name])
        for name in ('final_timer', 'final_drain_timer')]
    for item in final_identities:
        life.hook.live_identity(item['identity'])
    require(documents['final_drain_timer']['parallel_safe_snapshot_source_sha256'] == shared.sha(life.boundary.__file__),
            'actual_parallel_safe_cutoff_timer')
    return dict(native_identity=native, guard_identity=guard, guard_binding=references['guard_receipt'],
        final_identity_bindings=final_identities, owner_verified_safe_for_parallel=True,
        parallel_safe_snapshot_source_sha256=shared.sha(life.boundary.__file__))


def wait_activation(service, document, certificate, deadline, *, clock=time.time, pause=time.sleep):
    verified_hook()
    receipt = life.checked(certificate)
    if document.get('campaign') is not None:
        campaign = document['campaign']
        def bounded_check(label):
            require(clock() < min(deadline, document['train_end_unix'])
                and not (Path(service)/'STOP_REQUEST.json').exists(), 'bounded_autoarm_wait:'+label)
        return life.hook.await_campaign_activation(campaign['path'], campaign['sha256'],
            receipt['branch'], certificate, check=bounded_check)
    inbox = Path(document['activation_directory'])/f"generation_{receipt['generation']:06d}.ref.json"
    previous.math.atomic(Path(service)/'WAITING_ACTIVATION.json', dict(participant=certificate,
        expected_reference_path=str(inbox), generation=receipt['generation'], observed_unix=clock()))
    end = min(deadline, document['train_end_unix'])
    while clock() < end:
        if (Path(service)/'STOP_REQUEST.json').exists():
            raise TimeoutError('common_TRAIN_retirement_no_collective_launch')
        if inbox.exists():
            activation = shared.read(inbox)
            value = life.checked(activation)
            require(value['generation'] == receipt['generation']
                    and value['participants'][receipt['branch']] == certificate, 'exact_Main_parallel_activation')
            return activation
        pause(min(.2, max(0, end-clock())))
    raise TimeoutError('bounded_Main_activation_wait_no_retry')


def clean_boundary(service, plan):
    launch = shared.read(service/'LAUNCH.json')
    candidate = life.boundary.parallel_safe_snapshot(dict(root=plan['root'], branch=plan['branch'],
        native=launch['identity']))
    if candidate is None:
        return None
    root = Path(plan['root'])
    if candidate['kind'] == 'COMPLETE_SHARED_CHECKPOINT_AND_FRESH_DEV_CYCLE':
        progress = shared.read(root/'PROGRESS.json')
        require(progress['cycle'] == candidate['cycle'] and progress['phase'] == 'CYCLE_COMPLETE'
                and progress['counters'] == candidate['counters'], 'settled_parallel_cursor')
    return candidate


def resident(service):
    service = Path(service)
    plan, document = runtime(service, initial=True)
    def interrupted(signum, frame):
        raise SystemExit(128+signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    root = Path(plan['root'])
    rank = life.hook.BRANCHES.index(plan['branch'])
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == previous.math.policy.DEVICES[rank], 'same_original_math_GPU')
    until = min(time.time()+90, life.TRAIN_END)
    needed = [service/'LAUNCH.json', service/'CUTOFF_ARMED.json', Path(plan['final_root'])/'SCHEDULED.json',
              service/'BROKER_READY.json']
    while not all(path.exists() for path in needed):
        require(time.time() < until, 'bounded_actual_guard_FINAL_broker_binding_wait')
        time.sleep(.1)
    launch, guard = shared.read(service/'LAUNCH.json'), shared.read(service/'GUARD_STARTED.json')
    require(life.boundary.minimal_identity(launch['identity']) == life.hook.process_identity(), 'actual_new_native_identity')
    broker = shared.read(service/'BROKER_READY.json')
    require(broker['runtime'] == life.ref(service/'RUNTIME.json') and broker['terminal_path'] == str(service/'GUARD_TERMINAL.json')
            and broker['actual_single_lane_lock_acquired'] is True,
            'new_broker_tracks_actual_new_guard_terminal')
    shared.write(service/'CUTOFF_PLAN.json', dict(root=str(root), branch=plan['branch'], native=launch['identity'],
        guard=guard['identity'], runtime=life.ref(service/'RUNTIME.json'), module=MODULE,
        uuid=previous.math.policy.DEVICES[rank], native_source=str(SOURCE)))
    references = protected(service, plan)
    retained = supervision(service, plan, references)
    def check(label):
        require(time.time() < life.TRAIN_END, 'unchanged_common_TRAIN_deadline:'+label)
    engine, status = None, 'FAILED'
    try:
        shared.write(service/'FINALIZED_HOOK_BINDING.json', verified_hook())
        session = deepcopy(document['session'])
        client.current(session)
        initial = shared.read(Path(session['shared_root'])/'INITIALIZED.json')['state']['checkpoint']
        shared.checked_checkpoint(initial)
        original_adapter = shared.read(initial['path'])['adapter']
        comparison = recipe.require_same_recipe(
            shared.read(Path(original_adapter['path'])/'adapter_config.json'),
            shared.read(Path(session['adapter']['path'])/'adapter_config.json'))
        shared.write(service/'RECIPE_COMPATIBILITY.json', dict(comparison,
            initial_checkpoint=initial, mounted_checkpoint=session['checkpoint'],
            tensor_verification='REQUIRED_AT_NATIVE_LOAD_NOT_YET_RUN', observed_unix=time.time()))
        engine = client.load(session, model_dir=previous.math.MODEL,
            gpu_uuid=previous.math.policy.DEVICES[rank], check=check)
        shared.write(service/'MODEL_LOADED.json', previous.loaded_receipt(root, engine, 'fresh_parallel_worker_before'))
        shared.write(service/'NEW_GRADIENT_RNG.json', bootstrap(engine, document, check))
        carry = life.checked(document['carry'])['own_reflection']
        tasks = shared.read(root.parent/'TRAIN.json')
        from gpu import orch_r107_base_anchors_inventory as anchor_module
        for cycle in range(document['next_cycle'], previous.math.policy.CYCLES+1):
            if time.time() >= life.TRAIN_END-120 or (service/'STOP_REQUEST.json').exists():
                break
            carry = loop.run_cycle(root, engine, cycle, tasks[cycle-1], carry, anchor_module=anchor_module,
                anchors=None, anchor_root='/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1',
                protected_refs=references, supervision=retained,
                await_activation=lambda certificate, deadline: wait_activation(service, document, certificate, deadline), check=check)
        status = 'COMPLETE_BOUNDED'
    except BaseException as error:
        shared.write(service/'FAILED.json', dict(status='FAILED_NO_RETRY', error=type(error).__name__+': '+str(error),
            counters=shared.read(root/'COUNTERS.json'), no_replay=True, observed_unix=time.time()))
        raise
    finally:
        candidate = clean_boundary(service, plan)
        if candidate is not None:
            shared.write(service/'CLEAN_RELEASE.json', dict(status='CLEAN_BOUNDARY', boundary=candidate,
                identity=launch['identity'], runtime=life.ref(service/'RUNTIME.json'),
                counter_sha256=shared.sha(root/'COUNTERS.json'), observed_unix=time.time()))
        if engine is not None and not engine.poisoned:
            shared.write(service/'MOUNTED_AFTER.json', previous.loaded_receipt(root, engine, 'fresh_parallel_worker_after'))
        shared.write(service/'NATIVE_TERMINAL.json', dict(status=status, counters=shared.read(root/'COUNTERS.json'),
            local_optimizer_steps=0, observed_unix=time.time()))


def scan(service):
    plan = life.plan_for(service)
    rank = life.hook.BRANCHES.index(plan['branch'])
    return previous.math.scan(Path(plan['root']).parent, rank)


def guard(service):
    service = Path(service)
    plan, document = runtime(service, initial=True)
    released = shared.read(service/'RELEASED.json')
    require(not released.get('final_custody_pending') or (service/'FINAL_TIMERS_RETIRED.json').exists(),
        'actual_old_FINAL_timers_retired_before_new_guard')
    life.authorization(document['authorization'], dict(plan, plan_sha256=shared.sha(service/'PLAN.json')), 'LAUNCH')
    with (service/'GUARD.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (service/'GUARD_STARTED.json').exists(), 'one_guard_no_native_retry')
        shared.write(service/'GUARD_STARTED.json', dict(identity=life.identity(os.getpid()), runtime=life.ref(service/'RUNTIME.json')))
        child = expected = None
        status = 'FAILED'
        def interrupted(signum, frame):
            raise SystemExit(128+signum)
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        try:
            from gpu import orch_math_feedback_uptake_r118_parallel_final as final
            if not (Path(plan['final_root'])/'PLAN.json').exists():
                final.prepare(service)
            timers = []
            for module, phase, flag, target in ((MODULE,'cutoff','--service',service),
                    (final.MODULE,'schedule','--root',Path(plan['final_root']))):
                with (service/(phase+'.log')).open('x') as log:
                    timer = subprocess.Popen([previous.math.PYTHON,'-B','-m',module,phase,flag,str(target)],
                        cwd=SOURCE, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                        env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1'))
                    timers.append(dict(pid=timer.pid, module=module, phase=phase))
            shared.write(service/'TIMERS_DISPATCHED.json', dict(timers=timers, runtime=life.ref(service/'RUNTIME.json')))
            report = subprocess.run(['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH='+str(SOURCE),'python3','-B','-m',MODULE,'scan','--service',str(service)],
                capture_output=True, text=True, check=True, timeout=90)
            admission = json.loads(report.stdout)
            shared.write(service/'ADMISSION.json', admission)
            require(admission['clear'] and admission['scanner_euid'] == 0 and not admission['blocking_reasons'],
                    'strict_full_proc_UUID_CVD_FD_admission_no_waiver')
            life.released(service)
            rank = life.hook.BRANCHES.index(plan['branch'])
            with (service/'NATIVE.log').open('x') as log:
                child = subprocess.Popen([previous.math.PYTHON,'-B','-m',MODULE,'resident','--service',str(service)],
                    cwd=SOURCE, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=previous.math.policy.DEVICES[rank], PYTHONPATH=str(SOURCE),
                        PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                        MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'))
                for attempt in range(100):
                    expected = life.identity(child.pid)
                    if MODULE.encode() in (Path('/proc')/str(child.pid)/'cmdline').read_bytes().split(b'\0'):
                        break
                    time.sleep(.01)
                else:
                    raise ValueError('actual_new_exec_not_observed')
                shared.write(service/'LAUNCH.json', dict(identity=expected, guardian=life.identity(os.getpid()),
                    uuid=previous.math.policy.DEVICES[rank], runtime=life.ref(service/'RUNTIME.json'), observed_unix=time.time()))
                require(child.wait(timeout=max(.01, previous.math.HARD-time.time())) == 0, 'parallel_native_failed_no_retry')
                status = 'COMPLETE'
        finally:
            if child is not None and child.poll() is None:
                life.terminate_owned(expected, force=True)
            for expected_readout in life.drain.live_readout_identities(Path(plan['root'])):
                actual = life.identity(expected_readout['pid'])
                require(previous.math.common.process_identity(Path('/proc')/str(expected_readout['pid'])) == expected_readout,
                        'actual_owned_readout_identity')
                life.terminate_owned(actual)
            shared.write(service/'GUARD_TERMINAL.json', dict(status=status, identity=expected,
                native_alive=child is not None and child.poll() is None, observed_unix=time.time(), no_retry=True))


def cutoff(service):
    service = Path(service)
    plan, document = runtime(service)
    with (service/'CUTOFF.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        shared.write(service/'CUTOFF_ARMED.json', dict(identity=life.identity(os.getpid()), runtime=life.ref(service/'RUNTIME.json'),
            parallel_safe_snapshot_source_sha256=shared.sha(life.boundary.__file__), not_before_unix=life.TRAIN_END))
        while time.time() < life.TRAIN_END:
            time.sleep(min(10, life.TRAIN_END-time.time()))
        shared.write(service/'STOP_REQUEST.json', dict(reason='PREDECLARED_COMMON_TRAIN_DEADLINE', observed_unix=time.time()))
        end = min(previous.math.NATIVE, life.drain.io.START-20)
        while time.time() < end:
            if (service/'GUARD_TERMINAL.json').exists():
                return
            candidate = clean_boundary(service, plan)
            if candidate is not None:
                actors = shared.read(service/'LAUNCH.json')
                with (Path(plan['root'])/'COUNTERS.lock').open('a') as counters:
                    fcntl.flock(counters, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    candidate = clean_boundary(service, plan)
                    if candidate is not None:
                        life.terminate_owned(actors['identity'])
                        require((service/'NATIVE_TERMINAL.json').exists(), 'authentic_native_finally_required')
                        return
            time.sleep(.2)
        shared.write(service/'CUTOFF_NOT_CLEAN.json', dict(status='NOT_RUN_FINAL_UNLESS_GENUINE_CLEAN_RELEASE',
            observed_unix=time.time(), no_parallel_inflight_signals=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('guard','resident','scan','cutoff'))
    parser.add_argument('--service', type=Path, required=True)
    args = parser.parse_args()
    if args.phase == 'scan':
        print(json.dumps(scan(args.service)))
    else:
        globals()[args.phase](args.service)


if __name__ == '__main__':
    main()
