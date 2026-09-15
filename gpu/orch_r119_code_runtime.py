"""Prospective CODE process overlay bound to Main's immutable lease clock."""

import argparse
from copy import deepcopy
import fcntl
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time
from types import FunctionType

from gpu import orch_r119_code_continuation as custody
from gpu import orch_r119_code_final_custodian as final_custodian
from gpu import orch_r119_lease_clock as lease_clock


MODULE = 'gpu.orch_r119_code_runtime'
require = custody.require


def command(service, phase, binding=None):
    service = Path(service)
    runtime = custody.read(service / 'RUNTIME.json')
    return command_from_runtime(service, phase, runtime, binding)


def command_from_runtime(service, phase, runtime, binding=None):
    service = Path(service)
    arguments = [MODULE, phase, '--service', str(service)]
    if binding is not None:
        arguments.extend(['--binding', str(binding)])
    script = ('import sys,runpy;sys.path.insert(0,' + repr(runtime['source_root']) +
        ');import gpu;gpu.__path__.insert(0,' + repr(runtime['wrapper_directory']) +
        ');sys.argv=' + repr(arguments) + ';runpy.run_module(' + repr(MODULE) + ',run_name="__main__")')
    return [runtime['interpreter'], '-B', '-c', script]


def configured(service):
    service = Path(service).resolve(strict=True)
    runtime = custody.read(service / 'RUNTIME.json')
    require(runtime['schema'] == 'R119_CODE_LEASE_RUNTIME_V1' and runtime['service'] == str(service),
        'exact_CODE_continuation_service')
    require(all(custody.ref(path)['sha256'] == sha for path, sha in runtime['source_files'].items()),
        'pinned_existing_closure_and_scoped_wrapper')
    policy = runtime['lease_policy']
    bounds = lease_clock.validate(policy, backend_path=runtime['backend']['path'])
    require(bounds['train_end_unix'] == runtime['train_end_unix']
        and bounds['hard_end_unix'] == runtime['hard_end_unix'], 'same_Main_clock_not_personal_wall')
    require(custody.ref(runtime['backend']['path']) == runtime['backend'], 'exact_prospective_backend')
    os.environ.update(ORCH_R119_LEASE_CLOCK=policy['path'], ORCH_R119_LEASE_CLOCK_SHA256=policy['sha256'])
    spec = importlib.util.spec_from_file_location('gpu.orch_r118_parallel_consolidation', runtime['backend']['path'])
    backend = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = backend
    spec.loader.exec_module(backend)
    require(backend.TRAIN_END == bounds['train_end_unix'] and backend.HARD_END == bounds['hard_end_unix'],
        'actual_backend_consumes_canonical_clock')
    from gpu import orch_r118_code_parallel_loop as core
    require(core.consolidation is backend, 'one_prospective_common_backend')
    pointers = custody.checked(runtime['pointers'])
    root = Path(pointers['root'])
    original = custody.checked(pointers['original_plan'])
    effective = custody.effective_plan(original, bounds)
    require(root == service.parents[1] and runtime['common_root'] == pointers['common_root'],
        'same_branch_root_and_common')
    require(runtime['native_cap'] == original['native_cap'] and runtime['parent_cap'] == original['parent_cap'],
        'cumulative_caps_unchanged')
    tests = custody.checked(runtime['cpu_tests'])
    require(tests['passed'] is True and tests['cuda_initialized'] is False
        and tests['wrapper_sha256'] == custody.ref(__file__)['sha256'], 'tested_wrapper_source')

    def check(checked_root, phase):
        require(Path(checked_root) == root and custody.ref(root / 'PLAN.json') == pointers['original_plan'],
            'original_PLAN_never_rewritten')
        require(time.time() < bounds['hard_end_unix'] - 10, 'lease_native_hard_wall')
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == original['gpu_uuid'], 'exact_CODE_CVD')
        return effective

    core.client.run.check = check
    return core, runtime, pointers, original, effective


def preflight(service):
    core, runtime, pointers, original, effective = configured(service)
    fresh = custody.branch_snapshot(pointers['root'])
    for key in ('original_plan', 'generation', 'checkpoint', 'existing_submission', 'pending_reference',
        'pending_cursor', 'cumulative_counts', 'preserved_files', 'final_completed', 'final_terminal'):
        require(fresh[key] == pointers[key], 'same_released_continuation:' + key)
    require(runtime['next_cycle'] == pointers['next_cycle'], 'cursor_never_reset')
    require(runtime['activation_directory'] == custody.checked(runtime['campaign'])['activation_directory'],
        'actual_Main_campaign_binding')
    for identity in custody.checked(custody.checked(pointers['prepared'])['proof'])['predecessors']:
        require(not core.handoff.alive(identity), 'failed_predecessors_exited')
    return core, runtime, pointers, original, effective


def schedule_dev(root, session, ordinal, scope):
    require(scope == 'DEV', 'completed_FINAL_never_rescheduled')
    reference = Path(root) / 'shared_readout_bindings' / f'C{ordinal:03d}_DEV.json'
    custody.write(reference, dict(state=deepcopy(session.state), checkpoint=deepcopy(session.loaded_reference),
        scope='DEV', cycle=ordinal, config_sha256=custody.ref(session.shared_root / 'CONFIG.json')['sha256']))
    with reference.with_suffix('.log').open('x') as log:
        return subprocess.Popen(command(session.service, 'readout', reference), stdout=log,
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)


def lifecycle_functions(core):
    namespace = dict(vars(core))
    for name in ('settle_readout', 'finish_committed_cycle', 'resume_pending', 'run_cycles'):
        original = getattr(core, name)
        replacement = FunctionType(original.__code__, namespace, name, original.__defaults__, original.__closure__)
        replacement.__kwdefaults__ = dict(original.__kwdefaults__ or {})
        namespace[name] = replacement
    namespace['settle_readout'].__kwdefaults__['launch'] = schedule_dev
    namespace['finish_committed_cycle'].__kwdefaults__['settle'] = namespace['settle_readout']
    namespace['resume_pending'].__kwdefaults__['finish'] = namespace['finish_committed_cycle']
    namespace['run_cycles'].__kwdefaults__['settle'] = namespace['settle_readout']
    return namespace


def native(service):
    core, runtime, pointers, original, effective = preflight(service)
    root, service = Path(pointers['root']), Path(service)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == original['gpu_uuid'], 'exact_CODE_native_UUID')
    (service / 'NATIVE_ONCE').mkdir()
    check = lambda phase: core.client.run.forward_check(root, phase)
    released = custody.checked(pointers['release'])
    boundary = released['native']['boundary']
    adopted = custody.checked(pointers['original_activation'])
    session = core.Session(root, dict(original, shared_learner=adopted['shared_learner']), pending_boundary=boundary)
    session.plan = effective
    engine = session.load_engine(effective, check)
    anchors, receipt = core.ordered_anchors(runtime, engine.tokenizer, session.config)
    session.configure(runtime, service, anchors)
    driver = core.client.Driver(root, engine, session)
    driver.plan = effective
    driver.settings = deepcopy(pointers['carry']['reflection_settings'])
    session.driver, session.cursor_reference = driver, pointers['release']
    lifecycle = lifecycle_functions(core)
    try:
        boot = core.bootstrap(session, engine, check)
        custody.write(service / 'ACTOR_READY.json', dict(identity=core.handoff.identities.identity(os.getpid()),
            generation=session.state['generation'], checkpoint=session.loaded_reference,
            pending_cycle=pointers['pending_cycle'], next_cycle=pointers['next_cycle'],
            carry=driver.settings, lease_policy=runtime['lease_policy'], bootstrap=boot,
            anchor_receipt=receipt, local_optimizer=None, final_replay=False))
        lifecycle['resume_pending'](driver, boundary, check)
        cursor = lifecycle['run_cycles'](driver, core.client.run.policy.tasks('TRAIN'),
            pointers['next_cycle'], original['cycles'], check)
        engine.verify_base()
        custody.write(service / 'CLEAN_RELEASE.json', dict(identity=core.handoff.identities.identity(os.getpid()),
            cursor=cursor, actual_settled_boundary=True, charges=core.handoff.ledger(root)[0]))
    finally:
        custody.write(service / 'TERMINAL.json', dict(observed_unix=time.time(), no_replay=True,
            clean=(service / 'CLEAN_RELEASE.json').exists()))


def readout(service, binding):
    core, runtime, pointers, original, effective = configured(service)
    root = Path(pointers['root'])
    document = custody.read(binding)
    require(document['scope'] == 'DEV' and Path(binding).resolve().is_relative_to(root / 'shared_readout_bindings'),
        'DEV_only_not_completed_FINAL')
    adopted = custody.checked(pointers['original_activation'])
    session = core.client.Session(root, dict(original, shared_learner=adopted['shared_learner']), readout=True)
    require(document['state']['config_sha256'] == document['config_sha256']
        == custody.ref(session.shared_root / 'CONFIG.json')['sha256']
        and document['state']['checkpoint'] == document['checkpoint']
        and document['state']['generation'] <= session.state['generation'], 'actual_committed_DEV_binding')
    session.state = document['state']
    session.loaded_reference = core.io.checked_checkpoint(document['checkpoint'])
    engine = session.load_engine(effective, lambda phase: core.client.run.forward_check(root, phase), readout=True)
    driver = core.lifecycle.ReadoutDriver(root, engine, session)
    driver.plan = effective
    core.client.run.readouts(driver, document['cycle'], 'DEV')
    engine.verify_base()


def completed_final_custody(service):
    core, runtime, pointers, original, effective = configured(service)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_completed_FINAL_custodian')
    service = Path(service)
    launch = custody.read(service / 'LAUNCH.json')
    require(core.handoff.alive(launch['identity']), 'actual_continuation_actor_present')
    identity = core.handoff.identities.identity(os.getpid())
    document = final_custodian.evidence(pointers,
        core.handoff.collective_identity(launch['identity']),
        core.handoff.collective_identity(identity), custody.ref(service / 'RUNTIME.json'))
    custody.write(service / 'COMPLETED_FINAL_CUSTODY.json', document)
    while time.time() < runtime['hard_end_unix'] and not (service / 'GUARD_TERMINAL.json').exists():
        if not core.handoff.alive(launch['identity']):
            break
        time.sleep(2)
    custody.write(service / 'CUSTODY_TERMINAL.json', dict(identity=identity,
        role=final_custodian.ROLE, evaluator_calls=0, observed_unix=time.time()))


def guard(service):
    core, runtime, pointers, original, effective = preflight(service)
    service, root = Path(service), Path(pointers['root'])
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard')
    session_path = Path(os.environ['R118_PARALLEL_SESSION'])
    session_sha = os.environ['R118_PARALLEL_SESSION_SHA256']
    session, control = core.consolidation.fresh_session(session_path, session_sha)
    require(not (control / 'FAILED.json').exists(), 'no_failed_session_restart')
    (service / 'GUARD_ONCE').mkdir()
    identity = core.handoff.identities.identity(os.getpid())
    custody.write(service / 'GUARD_IDENTITY.json', dict(identity=identity, lease_policy=runtime['lease_policy']))
    child = None
    try:
        with (Path('/tmp') / ('orch_r115_f3_' + original['gpu_uuid'] + '.lock')).open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            scan = subprocess.run(runtime['admission_command'], capture_output=True, text=True,
                timeout=120, check=True)
            report = __import__('json').loads(scan.stdout)
            custody.write(service / 'ADMISSION.json', report)
            accepted = core.handoff.previous.admitted(report, original)
            custody.write(service / 'ADMISSION_DECISION.json', dict(accepted=accepted,
                snapshot=custody.ref(service / 'ADMISSION.json'), observed_unix=time.time()))
            require(accepted and time.time() < session['startup_deadline_unix'], 'fresh_bound_admission_before_startup')
            preflight(service)
            with (service / 'NATIVE.log').open('x') as log:
                child = subprocess.Popen(command(service, 'native'), stdout=log, stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL, start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=original['gpu_uuid']))
            native_identity = core.handoff.identities.identity(child.pid)
            custody.write(service / 'LAUNCH.json', dict(identity=native_identity, guardian=identity,
                runtime=custody.ref(service / 'RUNTIME.json')))
            with (service / 'CUSTODY.log').open('x') as log:
                custodian = subprocess.Popen(command(service, 'completed_final_custody'),
                    stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                    start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
            custody_deadline = min(time.time() + 60, session['startup_deadline_unix'])
            while not (service / 'COMPLETED_FINAL_CUSTODY.json').exists():
                require(custodian.poll() is None and time.time() < custody_deadline,
                    'actual_completed_FINAL_custodian_ready')
                time.sleep(0.2)
            final_binding = final_custodian.binding(custody.ref(service / 'COMPLETED_FINAL_CUSTODY.json'),
                core.handoff.collective_identity(native_identity), core.consolidation.live_identity)
            custody.write(service / 'SUPERVISION.json', dict(native_identity=core.handoff.collective_identity(native_identity),
                guard_identity=core.handoff.collective_identity(identity), guard_binding=custody.ref(service / 'LAUNCH.json'),
                final_identity_bindings=[final_binding], completed_final_bindings=[dict(complete=pointers['final_completed'],
                    terminal=pointers['final_terminal'], identity=pointers['final_identity'])],
                owner_verified_safe_for_parallel=True, lease_policy=runtime['lease_policy']))
            while child.poll() is None and time.time() < runtime['hard_end_unix'] - 5:
                time.sleep(1)
            core.cleanup_native(native_identity, root)
            child.wait(timeout=2)
            custody.write(service / 'GUARD_TERMINAL.json', dict(identity=native_identity,
                native_alive=False, returncode=child.returncode, observed_unix=time.time()))
    except BaseException as error:
        if child is None:
            custody.write(service / 'GUARD_TERMINAL.json', dict(guardian=identity, native_started=False,
                native_alive=False, error_type=type(error).__name__, observed_unix=time.time()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('preflight', 'guard', 'native', 'readout', 'completed_final_custody'))
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--binding', type=Path)
    args = parser.parse_args()
    if args.phase == 'readout':
        require(args.binding is not None, 'explicit_DEV_binding')
        readout(args.service, args.binding)
    else:
        globals()[args.phase](args.service)
