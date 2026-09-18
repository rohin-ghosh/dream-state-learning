"""Publication-gated F4 successor custody; no runtime action in preflight."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace


ROOT = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915/F4')
OUTPUT = ROOT / 'r139_timer_custody_v1'
HANDOFF = Path('/tmp/orch_r139_F4_handoff_v1/gpu/orch_r139_grid_astra_handoff.py')
HANDOFF_SHA = 'adc2598e89e3917840129c319a58de122ebda832af7e1acae3dce77562c3c778'
HANDOFF_PLAN = HANDOFF.parent.parent / 'F4_PLAN.json'
HANDOFF_PLAN_SHA = '21cdcf5ce41403176b1a46d12c05fdf5c877f0bd89b82890780444509291a546'
NATIVE_SHA = 'f01356da73124d6be18a39bef168ac0ed16c6156bc9b859ed1d147d7c0aa6963'
MORNING, EVAL_END, TRAIN_END, HARD_END = 1789538400, 1789539600, 1789596120, 1789596240
ERA = 'r139_astra_handoff_v1'
ASTRA = 'openai/openai/gpt-6-astra'
ACTIONS = ['retire_exact_old_timers', 'arm_successor_custody', 'initial_resume_adapter',
           'morning_completed_boundary', 'one_shot_FINAL8', 'resume_same_life', 'enforce_original_wall']
ROLES = ('initial', 'evaluate', 'resume')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    path = Path(path)
    require(path.resolve() == path and path.is_file() and path.stat().st_size <= 16 * 1024 * 1024,
            'bounded_regular_metadata')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_key')
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=sha(path))


def checked(reference):
    path = Path(reference['path'])
    require(path.resolve() == path and sha(path) == reference['sha256'], 'immutable_reference')
    return read(path)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependencies():
    require(sha(HANDOFF) == HANDOFF_SHA and sha(HANDOFF_PLAN) == HANDOFF_PLAN_SHA, 'frozen_handoff')
    handoff = load(HANDOFF, 'r139_timer_frozen_handoff')
    legacy = handoff.custody()
    native_path = Path(legacy.__file__).with_name('orch_r119_grid_final_native.py')
    require(sha(native_path) == NATIVE_SHA, 'frozen_FINAL_native')
    return handoff, legacy, native_path


def preflight():
    handoff, legacy, native_path = dependencies()
    plan = read(HANDOFF_PLAN)
    for reference in plan['references'].values():
        checked(reference)
    old = checked(plan['references']['old_final_plan'])
    legacy.validate(old)
    require(time.time() < MORNING and legacy.no_attempt(Path(old['output'])), 'before_unattempted_FINAL')
    require(not OUTPUT.exists(), 'unused_timer_namespace')
    timers = {name: checked(plan['references'][name])['timer_identity']
              for name in ('old_morning_timer', 'old_wall_timer')}
    require(all(legacy.same_process(identity) for identity in timers.values()), 'both_original_timers_live')
    require(legacy.same_process(plan['predecessor']), 'original_actor_still_live')
    return dict(schema='R139_F4_TIMER_CUSTODY_V1', root=str(ROOT), output=str(OUTPUT),
        controller_source=ref(__file__), handoff_source=ref(HANDOFF), handoff_plan=ref(HANDOFF_PLAN),
        legacy_source=ref(legacy.__file__), native_source=ref(native_path),
        old_final_plan=plan['references']['old_final_plan'], old_timers=timers,
        predecessor=plan['predecessor'], checkpoint=plan['references']['checkpoint'],
        morning_unix=MORNING, evaluation_end_unix=EVAL_END, train_end_unix=TRAIN_END,
        hard_end_unix=HARD_END, existing_FINAL_quota=8, additional_FINAL_calls=0,
        parent_FINAL_calls=0, sealed_inputs_to_parent=False, empty_readout_context=True,
        actions=ACTIONS, approved_intake=plan['approved_intake'], requested_scope=plan['requested_scope'],
        initial_successor_receipt=str(ROOT / ERA / 'RESUMED.json'),
        morning_successor_receipt=str(Path(old['output']) / 'RESUMED.json'),
        status='STAGED_NOT_AUTHORIZED', native_calls=0, signals_sent=0)


def validate(plan):
    handoff, legacy, native_path = dependencies()
    frozen = read(HANDOFF_PLAN)
    require(plan['schema'] == 'R139_F4_TIMER_CUSTODY_V1' and plan['root'] == str(ROOT)
            and plan['output'] == str(OUTPUT), 'exact_F4_timer_scope')
    for key, path in [('controller_source', Path(__file__)), ('handoff_source', HANDOFF),
                      ('handoff_plan', HANDOFF_PLAN), ('legacy_source', Path(legacy.__file__)),
                      ('native_source', native_path)]:
        require(plan[key] == ref(path), 'pinned_timer_dependencies')
    require(plan['old_final_plan'] == frozen['references']['old_final_plan']
            and plan['predecessor'] == frozen['predecessor']
            and plan['checkpoint'] == frozen['references']['checkpoint'], 'same_frozen_life')
    require((plan['morning_unix'], plan['evaluation_end_unix'], plan['train_end_unix'], plan['hard_end_unix'])
            == (MORNING, EVAL_END, TRAIN_END, HARD_END), 'no_clock_extension')
    require(plan['existing_FINAL_quota'] == 8 and plan['additional_FINAL_calls'] == 0
            and plan['parent_FINAL_calls'] == 0 and plan['sealed_inputs_to_parent'] is False
            and plan['empty_readout_context'] is True and plan['actions'] == ACTIONS, 'same_FINAL_visibility_quota')
    require(plan['approved_intake'] == frozen['approved_intake']
            and plan['requested_scope'] == frozen['requested_scope'], 'same_approved_scope')
    old = checked(plan['old_final_plan'])
    require(plan['initial_successor_receipt'] == str(ROOT / ERA / 'RESUMED.json')
            and plan['morning_successor_receipt'] == str(Path(old['output']) / 'RESUMED.json'), 'fixed_actor_receipts')
    for name in ('old_morning_timer', 'old_wall_timer'):
        require(plan['old_timers'][name] == checked(frozen['references'][name])['timer_identity'], 'exact_old_timer')
    return handoff, legacy, old


def authorize(plan, publication, plan_ref, now):
    require(publication.get('authorized') is True and publication.get('published_by') == 'Main'
            and publication.get('timer_plan') == plan_ref
            and publication.get('controller_source') == plan['controller_source']
            and publication.get('actions') == ACTIONS
            and publication.get('approved_intake') == plan['approved_intake']
            and publication.get('requested_scope') == plan['requested_scope']
            and publication.get('not_before_unix', now + 1) <= now < HARD_END
            and publication.get('hard_end_unix') == HARD_END, 'Main_exact_published_handshake')


def bind(function, **globals_patch):
    result = FunctionType(function.__code__, dict(function.__globals__, **globals_patch),
                          function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def custody_receipt(plan, identity, publication_ref):
    return dict(root=str(ROOT), status='ARMED_SUCCESSOR_AWARE', controller_identity=identity,
        controller_source=plan['controller_source'], timer_publication=publication_ref,
        old_final_plan=plan['old_final_plan'], successor_receipt_path=plan['initial_successor_receipt'],
        morning_successor_receipt_path=plan['morning_successor_receipt'],
        resume_preserves_R139_parent_binding=True, morning_unix=MORNING, train_end_unix=TRAIN_END,
        hard_end_unix=HARD_END, existing_FINAL_quota=8, additional_FINAL_calls=0,
        sealed_inputs_to_parent=False, actor_callback='current', initial_resume_entrypoint='initial-resume',
        old_timers_retired=True, observed_unix=time.time())


def live_custody(plan, legacy, publication_ref):
    receipt = read(OUTPUT / 'ARMED.json')
    require(receipt['controller_source'] == plan['controller_source']
            and receipt['timer_publication'] == publication_ref
            and receipt['status'] == 'ARMED_SUCCESSOR_AWARE'
            and legacy.same_process(receipt['controller_identity']), 'live_exact_custody')
    return receipt


def actor_record(plan, legacy, role):
    require(role in ROLES, 'known_native_role')
    return dict(role=role, identity=legacy.process(os.getpid()), controller_source=plan['controller_source'],
        handoff_source=plan['handoff_source'], native_source=plan['native_source'],
        checkpoint=plan['checkpoint'], parent_model=None if role == 'evaluate' else ASTRA,
        parent_absent=role == 'evaluate', source_bound_before_model_load=True, observed_unix=time.time())


def registered(plan, legacy, role):
    document = read(OUTPUT / (role.upper() + '_ACTOR.json'))
    require(document['role'] == role and document['checkpoint'] == plan['checkpoint']
            and document['source_bound_before_model_load'] is True
            and document['parent_absent'] == (role == 'evaluate')
            and document['parent_model'] == (None if role == 'evaluate' else ASTRA), 'actual_registered_role')
    for key in ('controller_source', 'handoff_source', 'native_source'):
        require(document[key] == plan[key] and sha(plan[key]['path']) == plan[key]['sha256'], 'actor_source_identity')
    return document


def current_native(plan, legacy):
    live = []
    for role, key in [('initial', 'initial_successor_receipt'), ('resume', 'morning_successor_receipt')]:
        if not Path(plan[key]).exists():
            continue
        actual = read(plan[key])
        record = registered(plan, legacy, role)
        require(actual['identity'] == record['identity'] and actual['checkpoint'] == plan['checkpoint']
                and actual['parent_model'] == ASTRA and actual['parent_segment'] == ERA
                and actual['counter_reset'] is False, 'actual_restored_consumer_join')
        if legacy.same_process(actual['identity']):
            live.append(dict(record, restored_receipt=ref(plan[key])))
    require(len(live) == 1 and not legacy.same_process(plan['predecessor']), 'exactly_one_current_native')
    return live[0]


def signal_exact(legacy, identity, signum):
    require(identity['uid'] == os.getuid() and legacy.same_process(identity), 'exact_owned_signal_target')
    descriptor = os.pidfd_open(identity['pid'])
    try:
        require(legacy.same_process(identity), 'same_target_after_pidfd_open')
        signal.pidfd_send_signal(descriptor, signum)
        if signum in (signal.SIGTERM, signal.SIGKILL):
            require(bool(select.select([descriptor], [], [], 10)[0]), 'exact_target_exit_observed')
    finally:
        os.close(descriptor)


def register(plan, legacy, role):
    (OUTPUT / (role.upper() + '_ONCE')).mkdir()
    record = actor_record(plan, legacy, role)
    legacy.write(OUTPUT / (role.upper() + '_ACTOR.json'), record)
    return record


def derived_plan(plan, legacy, old):
    current = current_native(plan, legacy)
    return dict(deepcopy(old), predecessor=current['identity']), current


def validate_derived(plan, legacy, old):
    derived = read(OUTPUT / 'MORNING_PLAN.json')
    predecessor = checked(read(OUTPUT / 'MORNING_ACTOR.json')['restored_receipt'])['identity']
    require(derived == dict(old, predecessor=predecessor), 'only_actual_predecessor_changes')
    return derived


def adapted_native(plan, legacy, old, derived):
    handoff = load(HANDOFF, 'r139_timer_resume_binding')
    native = load(plan['native_source']['path'], 'r139_timer_original_FINAL_native')
    initial = read(plan['initial_successor_receipt'])
    initial_actor = registered(plan, legacy, 'initial')
    require(initial['identity'] == initial_actor['identity'] and initial['checkpoint'] == plan['checkpoint']
            and initial['parent_model'] == ASTRA and initial['parent_segment'] == ERA
            and initial['counter_reset'] is False, 'original_Astra_resume_binding')
    initial_boundary = checked(initial['boundary'])

    def validate_phase(candidate):
        require(candidate == derived, 'exact_actual_morning_plan')
        prior, grid, config, checkpoint = legacy.validate(old)
        original_factory = prior.mailbox.life_class
        def life_class(module, era):
            require(era == old['mailbox_era'], 'unchanged_mailbox_era')
            return original_factory(module, era, first_parent=initial_boundary['first_new_parent'])
        prior_view = SimpleNamespace(**vars(prior))
        prior_view.mailbox = SimpleNamespace(life_class=life_class)
        return prior_view, grid, handoff.consumer_config(config, initial_boundary), checkpoint

    def write(path, value):
        if Path(path) == Path(old['output']) / 'RESUMED.json':
            value = dict(value, parent_model=ASTRA, parent_segment=ERA,
                         controller_source=plan['controller_source'],
                         original_parent_boundary=initial['boundary'], live_rng_restored=False)
        return legacy.write(path, value)

    view = SimpleNamespace(**vars(legacy))
    view.validate, view.write = validate_phase, write
    released = bind(native.require_released, custody=view)
    return {mode: bind(getattr(native, mode), custody=view, require_released=released)
            for mode in ('evaluate', 'resume')}


def command(mode, plan_path, publication_path):
    return [str(Path(__file__).resolve()), mode, '--expected-self-sha256', sha(__file__),
            '--plan', str(plan_path), '--plan-sha256', sha(plan_path), '--publication', str(publication_path)]


def launch_phase(plan, legacy, old, mode, admission, plan_path, publication_path):
    require(mode in ('evaluate', 'resume'), 'single_known_phase')
    deadline = EVAL_END if mode == 'evaluate' else HARD_END
    require(time.time() < (EVAL_END if mode == 'evaluate' else TRAIN_END) - 5, 'phase_window')
    prior, grid, config, checkpoint = legacy.validate(old)
    report = checked(admission)
    require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == config['uuid'], 'fresh_same_GPU_admission')
    armed = live_custody(plan, legacy, ref(publication_path))
    output = Path(old['output'])
    authorization = output / (mode.upper() + '_AUTHORIZATION.json')
    legacy.write(authorization, dict(mode=mode, plan=ref(output / 'PLAN.json'),
        actual_plan=ref(OUTPUT / 'MORNING_PLAN.json'), timer_plan=ref(plan_path),
        release=ref(output / 'RELEASED.json'), admission=admission,
        timer_identity=armed['controller_identity'], issued_unix=time.time(), deadline_unix=deadline))
    argv = ['timeout', '--signal=TERM', '--kill-after=3s', f'{int(deadline-time.time()-4)}s',
            grid.PYTHON, '-B', *command(mode, plan_path, publication_path)]
    with (OUTPUT / (mode.upper() + '.log')).open('x') as log:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=config['uuid'], PYTHONPATH=str(prior.OLD),
                PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                ORCH_GRID_FINAL_PHASE_AUTHORIZATION_SHA256=sha(authorization)))
    try:
        legacy.write(OUTPUT / (mode.upper() + '_LAUNCH.json'), dict(timeout_pid=child.pid,
            source=plan['controller_source'], mode=mode, deadline_unix=deadline, no_model_retry=True))
    except BaseException:
        child.wait()
        raise
    return child


def morning(plan, plan_path, publication_path):
    handoff, legacy, old = validate(plan)
    live_custody(plan, legacy, ref(publication_path))
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and MORNING <= time.time() < MORNING + 600,
            'CPU_fixed_morning_boundary_window')
    (OUTPUT / 'MORNING_ONCE').mkdir()
    require(legacy.no_attempt(Path(old['output'])), 'prior_FINAL_never_replayed')
    derived, current = derived_plan(plan, legacy, old)
    legacy.write(OUTPUT / 'MORNING_PLAN.json', derived)
    legacy.write(OUTPUT / 'MORNING_ACTOR.json', current)
    def same_actor(identity):
        return (identity == current['identity'] and
                sha(plan['controller_source']['path']) == plan['controller_source']['sha256'] and
                legacy.same_process(identity))
    release = bind(legacy.release_at_boundary, same_process=same_actor,
                   completed_boundary=lambda root: handoff.boundary_snapshot(root, legacy))
    release(derived)
    try:
        admission = legacy.fresh_scan(old, 'EVAL')
        child = launch_phase(plan, legacy, old, 'evaluate', admission, plan_path, publication_path)
        code = child.wait()
        legacy.write(OUTPUT / 'EVAL_EXIT.json', dict(exit_code=code, no_retry=True))
    except Exception as error:
        legacy.write(OUTPUT / 'EVAL_NOT_RETRIED.json', dict(error_type=type(error).__name__, no_retry=True))
    admission = legacy.fresh_scan(old, 'RESUME')
    child = launch_phase(plan, legacy, old, 'resume', admission, plan_path, publication_path)
    code = child.wait()
    legacy.write(OUTPUT / 'LIFE_TERMINAL.json', dict(exit_code=code, no_retry=True, counter_reset=False))


def native_phase(plan, mode, plan_path, publication_path):
    handoff, legacy, old = validate(plan)
    live_custody(plan, legacy, ref(publication_path))
    derived = validate_derived(plan, legacy, old)
    auth_path = Path(old['output']) / (mode.upper() + '_AUTHORIZATION.json')
    require(sha(auth_path) == os.environ.get('ORCH_GRID_FINAL_PHASE_AUTHORIZATION_SHA256'), 'exact_phase_launch')
    authorization = read(auth_path)
    require(authorization['actual_plan'] == ref(OUTPUT / 'MORNING_PLAN.json')
            and authorization['timer_plan'] == ref(plan_path), 'phase_timer_adapter_join')
    require(time.time() < (EVAL_END if mode == 'evaluate' else TRAIN_END), 'no_late_native_load')
    callbacks = adapted_native(plan, legacy, old, derived)
    register(plan, legacy, mode)
    callbacks[mode](derived)


def initial_resume(plan, publication_path, handoff_publication_path):
    handoff, legacy, old = validate(plan)
    live_custody(plan, legacy, ref(publication_path))
    require(time.time() < MORNING, 'initial_handoff_before_morning_only')
    publication = read(handoff_publication_path)
    require(publication['timer_custody'] == ref(OUTPUT / 'ARMED.json'), 'published_actual_timer_receipt')
    frozen = read(HANDOFF_PLAN)
    handoff.authorize(frozen, publication, HANDOFF_PLAN_SHA, 'resume', time.time())
    register(plan, legacy, 'initial')
    handoff.resume(frozen, publication)


def wall_targets(plan, legacy):
    result = [plan['predecessor']]
    for role in ROLES:
        if (OUTPUT / (role.upper() + '_ACTOR.json')).exists():
            result.append(registered(plan, legacy, role)['identity'])
    return result


def arm(plan, plan_path, publication_path):
    handoff, legacy, old = validate(plan)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and time.time() < MORNING - 30,
            'CPU_arm_before_morning')
    require(legacy.no_attempt(Path(old['output'])), 'unattempted_original_FINAL')
    require(all(legacy.same_process(identity) for identity in plan['old_timers'].values()), 'old_timers_live')
    OUTPUT.mkdir(mode=0o700)
    legacy.write(OUTPUT / 'CONTROLLER.json', dict(identity=legacy.process(os.getpid()),
        source=plan['controller_source'], publication=ref(publication_path), plan=ref(plan_path)))
    armed = False
    try:
        for name, identity in plan['old_timers'].items():
            signal_exact(legacy, identity, signal.SIGTERM)
            legacy.write(OUTPUT / (name.upper() + '_RETIRED.json'), dict(identity=identity, exit_observed=True))
        legacy.write(OUTPUT / 'ARMED.json', custody_receipt(plan, legacy.process(os.getpid()), ref(publication_path)))
        armed = True
    except Exception as error:
        legacy.write(OUTPUT / 'ARM_FAILED.json', dict(error_type=type(error).__name__, wall_custody_retained=True))
    known = {identity['pid']: identity for identity in [plan['predecessor']]}
    morning_started, train_closed = False, False
    while time.time() < HARD_END:
        try:
            for identity in wall_targets(plan, legacy):
                known[identity['pid']] = identity
            if armed and not morning_started and time.time() >= MORNING:
                morning_started = True
                argv = [sys.executable, '-B', *command('morning', plan_path, publication_path)]
                with (OUTPUT / 'MORNING.log').open('x') as log:
                    child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                        env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
                identity = legacy.process(child.pid)
                known[identity['pid']] = identity
                legacy.write(OUTPUT / 'MORNING_LAUNCH.json', dict(identity=identity, source=plan['controller_source']))
            if not train_closed and time.time() >= TRAIN_END:
                train_closed = True
                legacy.write(OUTPUT / 'TRAIN_WINDOW_CLOSED.json', dict(train_end_unix=TRAIN_END, extra_calls=0))
        except Exception as error:
            if not (OUTPUT / 'SUPERVISION_ERROR.json').exists():
                legacy.write(OUTPUT / 'SUPERVISION_ERROR.json', dict(error_type=type(error).__name__, no_retry=True))
        time.sleep(min(1, max(0, HARD_END - time.time())))
    try:
        for identity in wall_targets(plan, legacy):
            known[identity['pid']] = identity
    except Exception:
        pass
    sent, failures = [], []
    for identity in known.values():
        try:
            if legacy.same_process(identity):
                signal_exact(legacy, identity, signal.SIGKILL)
                sent.append(identity)
        except Exception as error:
            failures.append(dict(identity=identity, error_type=type(error).__name__))
    legacy.write(OUTPUT / 'WALL_DISPOSITION.json', dict(hard_end_unix=HARD_END,
        exact_owned_signals=sent, failures=failures, extra_FINAL_calls=0, no_retry=True, observed_unix=time.time()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preflight', 'validate', 'current', 'arm', 'initial-resume',
                                        'morning', 'evaluate', 'resume'))
    parser.add_argument('--expected-self-sha256', required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--plan-sha256')
    parser.add_argument('--publication', type=Path)
    parser.add_argument('--handoff-publication', type=Path)
    args = parser.parse_args()
    require(sha(__file__) == args.expected_self_sha256, 'immutable_timer_command')
    if args.mode == 'preflight':
        print(json.dumps(preflight(), sort_keys=True, indent=2))
        return
    require(args.plan is not None and sha(args.plan) == args.plan_sha256, 'exact_timer_plan')
    plan = read(args.plan)
    handoff, legacy, old = validate(plan)
    if args.mode == 'validate':
        print(json.dumps(dict(status='CPU_VALIDATED_NOT_ARMED', signals_sent=0, native_calls=0)))
        return
    require(args.publication is not None, 'Main_publication_required')
    authorize(plan, read(args.publication), ref(args.plan), time.time())
    if args.mode == 'current':
        live_custody(plan, legacy, ref(args.publication))
        print(json.dumps(current_native(plan, legacy), sort_keys=True))
    elif args.mode == 'arm':
        arm(plan, args.plan, args.publication)
    elif args.mode == 'initial-resume':
        require(args.handoff_publication is not None, 'separate_Main_resume_publication')
        initial_resume(plan, args.publication, args.handoff_publication)
    elif args.mode == 'morning':
        morning(plan, args.plan, args.publication)
    else:
        native_phase(plan, args.mode, args.plan, args.publication)


if __name__ == '__main__':
    main()
