"""F3-only completed-call recovery after an invalid expression crashed its checker."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace

from gpu import orch_r119_code_independent as previous


io, run, require = previous.custody, previous.run, previous.require
MODULE = 'gpu.orch_r125_code_checker_recovery'
IDENTIFIER = 'C044_E0_ORIGINAL'
ORIGINAL_SHA = '40cfda317b10de661b7572977923aea9b95e0d58513ebc6b421fb2feb2d55ef1'
CYCLE = 44


def checker_environment(original):
    def visible_checker(task, raw):
        try:
            return original.visible_checker(task, raw)
        except SyntaxError:
            return dict(status='INVALID_EXPRESSION', child_received=True, error_type='SyntaxError')

    def inspect_environment(raw):
        try:
            return original.inspect_environment(raw)
        except SyntaxError:
            return dict(status='REJECTED', enacted=False, operation='INSPECT', reason='SyntaxError',
                arbitrary_python_executed=False)

    def score(task, raw):
        value = original.last_json(raw)
        if not isinstance(value, dict) or set(value) != {'expression'} or not isinstance(value['expression'], str):
            return dict(correct=False, format_valid=False, passed=0, total=len(task['tests']))
        passed = 0
        for case in task['tests']:
            try:
                observed = original.policy.previous.gym_policy.gym.evaluate(value['expression'], case['arguments'])
                passed += type(observed) is type(case['expected']) and observed == case['expected']
            except (ValueError, TypeError, ZeroDivisionError, OverflowError, IndexError, SyntaxError):
                pass
        return dict(correct=passed == len(task['tests']), format_valid=True, passed=passed, total=len(task['tests']))

    return SimpleNamespace(**dict(vars(original), visible_checker=visible_checker,
        inspect_environment=inspect_environment, score=score))


def saved_call(root, reference, task, messages, cap):
    row = io.checked(reference)
    require(reference == io.ref(Path(root) / 'reservations' / (IDENTIFIER + '.json')),
        'exact_completed_call_reference')
    require(row['id'] == IDENTIFIER and row['status'] == 'COMPLETE' and row['kind'] == 'NATIVE'
        and row['split'] == task['split'] == 'TRAIN' and row['cycle'] == CYCLE
        and row['phase'] == 'episode' and row['evaluation_origin'] is None
        and row['requested_generation_cap'] == cap == 4096, 'completed_TRAIN_call_only')
    expected = deepcopy(messages)
    guidance = []
    for identifier in row['injected_parent_ids']:
        parent = io.read(Path(root) / 'reservations' / (identifier + '.json'))
        require(parent['kind'] == 'PARENT' and parent['status'] == 'COMPLETE'
            and parent['split'] == 'TRAIN' and parent['guidance'], 'actual_previous_injection')
        guidance.append(parent['guidance'])
    if guidance:
        expected.append(dict(role='user', content='Parent guidance received since your previous turn:\n'
            + '\n\n'.join(guidance)))
    require(row['response']['messages'] == expected, 'same_task_prompt_and_actual_parent_injection')
    return row


def preserved(root, prior_service):
    paths = {path for directory in ('reservations', 'triples', 'parent_queue')
        for path in (root / directory).rglob('*.json')}
    paths.update(path for path in prior_service.rglob('*') if path.is_file())
    paths.update(root / name for name in ('PLAN.json', 'BROKER_CONFIG.json', 'SHARED_ACTIVATION.json'))
    return {str(path.relative_to(root)): io.ref(path)['sha256'] for path in sorted(paths)}


def validate_seam(root, prior_service):
    from gpu import orch_r118_code_parallel_handoff as handoff
    terminal = io.read(prior_service / 'TERMINAL.json')
    require(terminal['status'] == 'FAILED' and terminal['error_type'] == 'SyntaxError', 'exact_checker_failure')
    launch = io.read(prior_service / 'LAUNCH.json')
    require(all(not handoff.alive(launch[key]) for key in ('identity', 'guardian')), 'previous_actors_exited')
    require(io.read(prior_service / 'GUARD_TERMINAL.json')['returncode'] == 1, 'failed_guard_preserved')
    require(io.read(prior_service / 'C043_COMPLETE.json')['cycle'] == 43, 'previous_two_episode_cycle_complete')
    rows = [(path, io.read(path)) for path in (root / 'reservations').glob('*.json')]
    require(all(row['status'] not in ('STARTED', 'PENDING') for path, row in rows), 'all_previous_slots_terminal')
    require(sorted(path.name for path, row in rows if path.name.startswith('C044_'))
        == [IDENTIFIER + '.json'], 'one_completed_call_no_partial_followup')
    require(not (root / 'triples/C044_E0.json').exists()
        and not (root / 'triples/C044_E1.json').exists(), 'no_existing_episode_artifacts')
    require(not any(path.name.startswith('C') and row.get('cycle', 0) > CYCLE for path, row in rows),
        'no_future_cycle_calls')
    reference = io.ref(root / 'reservations' / (IDENTIFIER + '.json'))
    require(reference['sha256'] == ORIGINAL_SHA, 'frozen_actual_completed_response')
    active = [row for path, row in rows if path.name.startswith('C') and row.get('cycle', 0) >= 23]
    used = {identifier for row in active for identifier in row.get('injected_parent_ids', [])}
    require(all(not row.get('guidance') or row['id'] in used for row in active
        if row['kind'] == 'PARENT' and row['status'] == 'COMPLETE'), 'no_unrestored_guidance')
    settings = sorted((row for row in active if row.get('reflection_settings')),
        key=lambda row: row['finished_unix'])[-1]['reflection_settings']
    task = run.policy.tasks('TRAIN')[(CYCLE - 1) * 2]
    messages = run.policy.previous.messages(task)
    messages[-1]['content'] += '\n\n' + run.environment.AFFORDANCE
    saved_call(root, reference, task, messages, 4096)
    return dict(reference=reference, reflection_settings=settings,
        cumulative_counts={kind:sum(row['kind'] == kind for path, row in rows) for kind in ('NATIVE', 'PARENT')},
        predecessors=[launch['identity'], launch['guardian']])


def prepare(prior_service, service):
    prior_service, service = Path(prior_service).resolve(strict=True), Path(service).resolve()
    root = prior_service.parents[1]
    old = io.read(prior_service / 'INDEPENDENT.json')
    require(old['branch'] == 'F3' and old['root'] == str(root) and service.parents[1] == root,
        'F3_only_same_root_new_service')
    proof = validate_seam(root, prior_service)
    require(time.time() < old['train_end_unix'] - 120, 'existing_wall_not_extended')
    require(not service.exists(), 'new_recovery_namespace')
    proof.update(schema='R125_CODE_COMPLETED_CALL_RECOVERY_V1', prior_definition=io.ref(prior_service / 'INDEPENDENT.json'),
        preserved_files=preserved(root, prior_service), observed_unix=time.time(), next_cycle=CYCLE,
        no_model_redispatch=True, prior_cycle_incomplete=True)
    io.write(service / 'RECOVERY.json', proof)
    wrapper = Path(__file__).resolve().parent
    document = dict(old, service=str(service), wrapper_directory=str(wrapper),
        previous_wrapper_directory=old['wrapper_directory'], recovery=io.ref(service / 'RECOVERY.json'))
    document['source_files'] = dict(old['source_files'])
    for path in (Path(__file__).resolve(), wrapper.parent / 'tests/test_orch_r125_code_checker_recovery.py'):
        document['source_files'][str(path)] = io.ref(path)['sha256']
    io.write(service / 'INDEPENDENT.json', document)
    configure(service, initial=True)
    return dict(service=str(service), definition=io.ref(service / 'INDEPENDENT.json'),
        recovery=io.ref(service / 'RECOVERY.json'), terminal=str(service / 'GUARD_TERMINAL.json'),
        next_new_call='C044_E0_REFLECTION', counters=proof['cumulative_counts'])


def configure(service, *, initial=False):
    document, pointers, plan = previous.configure(service, initial=False)
    require(pointers['branch'] == 'F3' and plan['physical'] == 2, 'F3_only_physical2')
    proof = io.checked(document['recovery'])
    old = io.checked(proof['prior_definition'])
    for key in ('pointers', 'native_cap', 'parent_cap', 'cycles', 'hard_end_unix', 'train_end_unix', 'final_unix'):
        require(document[key] == old[key], 'no_historical_bounds_or_lineage_change')
    require(all(document['source_files'].get(path) == pin for path, pin in old['source_files'].items()),
        'all_historical_source_pins_preserved')
    if initial:
        root = Path(pointers['root'])
        prior_service = Path(old['service'])
        require(preserved(root, prior_service) == proof['preserved_files'], 'all_original_artifacts_unchanged')
        fresh = validate_seam(root, prior_service)
        require(all(fresh[key] == proof[key] for key in fresh), 'same_exact_recovery_seam')
    pointers = deepcopy(pointers)
    pointers['next_cycle'] = CYCLE
    pointers['carry']['reflection_settings'] = proof['reflection_settings']
    return document, pointers, plan


class Driver(previous.Driver):
    def __init__(self, root, engine, document, pointers):
        super().__init__(root, engine, document, pointers)
        self.recovery = io.checked(document['recovery'])
        self.restored = False
        self.model_binding.update(runtime_recovery=io.ref(self.service / 'INDEPENDENT.json'))

    def capture(self, identifier, task, phase, cycle, messages, cap, *, evaluation_origin=None):
        if identifier != IDENTIFIER:
            return super().capture(identifier, task, phase, cycle, messages, cap, evaluation_origin=evaluation_origin)
        require(not self.restored and phase == 'episode' and cycle == CYCLE
            and evaluation_origin is None, 'one_logged_response_restore_only')
        row = saved_call(self.root, self.recovery['reference'], task, messages, cap)
        require(row['model_binding']['checkpoint'] == self.model_binding['checkpoint'], 'same_frozen_child')
        io.write(self.service / 'COMPLETED_CALL_RESTORED.json', dict(reference=self.recovery['reference'],
            no_model_dispatch=True, no_reservation_write=True, observed_unix=time.time()))
        self.restored = True
        return row


def native(service):
    service = Path(service)
    document, pointers, plan = configure(service, initial=True)
    root = Path(pointers['root'])
    (service / 'NATIVE_ONCE').mkdir()
    from gpu import orch_r118_code_parallel_handoff as handoff
    identity = handoff.identities.identity(os.getpid())
    io.write(service / 'NATIVE_REQUEST.json', dict(identity=identity, definition=io.ref(service / 'INDEPENDENT.json')))
    run.environment = checker_environment(run.environment)
    driver, error = None, None
    try:
        engine = previous.load_engine(root, pointers, plan)
        driver = Driver(root, engine, document, pointers)
        io.write(service / 'ACTOR_READY.json', dict(identity=identity, loaded_unix=time.time(),
            model_binding=driver.model_binding, original_counters=driver.recovery['cumulative_counts'],
            optimizer_updates=0, shared_barrier=False, reflection_carry=driver.settings))
        tasks = run.policy.tasks('TRAIN')
        for ordinal in range(CYCLE, document['cycles'] + 1):
            if time.time() >= document['train_end_unix'] - 120:
                break
            if ordinal != CYCLE:
                require(not any((root / 'reservations').glob(f'C{ordinal:03d}_*.json')), 'no_charged_cycle_replay')
            selected = tasks[(ordinal - 1) * 2:ordinal * 2]
            require(len(selected) == 2, 'fixed_two_episode_schedule')
            events = []
            for index, task in enumerate(selected):
                events.extend(run.episode(driver, task, ordinal, index))
            messages = [dict(role='assistant' if event['actor'] == 'child' else 'user', content=event['text'])
                for event in events]
            messages.append(dict(role='user', content=run.policy.previous.PROMPTS['presleep']))
            reflected = driver.capture(f'C{ordinal:03d}_META', selected[-1], 'presleep', ordinal,
                messages, driver.settings['effective_max_new_tokens'])
            if reflected['status'] == 'COMPLETE':
                events.append(run.environment.event(selected[-1], 'child', reflected['response']['raw'], completed=True))
                driver.parent(f'C{ordinal:03d}_META_PARENT', selected[-1], events, ordinal, 1, 'presleep_metacognition')
            driver.poll_parent()
            io.write(service / f'C{ordinal:03d}_COMPLETE.json', dict(cycle=ordinal, train_episodes=2,
                optimizer_updates=0, shared_barrier=False, pending_parents=len(driver.pending), finished_unix=time.time()))
            if time.time() >= previous.FINAL_TIME and not (service / 'FINAL_ONCE').exists():
                (service / 'FINAL_ONCE').mkdir()
                previous.diagnostic(driver, ordinal, 'FINAL', 'R119_FINAL_20260916_0600')
            previous.diagnostic(driver, ordinal, 'DEV', 'R119_DEV')
            engine.verify_base()
    except BaseException as failure:
        error = failure
    finally:
        if driver is not None:
            driver.poll_parent()
            io.write(service / 'PENDING_PARENT_CUSTODY.json', dict(ids=list(driver.pending), no_retry=True))
        io.write(service / 'TERMINAL.json', dict(status='FAILED' if error else 'COMPLETE',
            error_type=type(error).__name__ if error else None, observed_unix=time.time(), optimizer_updates=0))
    if error:
        raise error


def command(service, phase, document):
    script = ('import sys,runpy;sys.path.insert(0,' + repr(document['source_root'])
        + ');import gpu;gpu.__path__[:0]='
        + repr([document['wrapper_directory'], document['previous_wrapper_directory']])
        + ';sys.argv=' + repr([MODULE, phase, '--service', str(service)])
        + ';runpy.run_module(' + repr(MODULE) + ',run_name="__main__")')
    return [document['interpreter'], '-B', '-c', script]


def guard(service):
    service = Path(service)
    document, pointers, plan = configure(service, initial=True)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard')
    from gpu import orch_r118_code_parallel_handoff as handoff
    (service / 'GUARD_ONCE').mkdir()
    identity = handoff.identities.identity(os.getpid())
    io.write(service / 'GUARD_IDENTITY.json', dict(identity=identity))
    result = subprocess.run(document['admission_command'], capture_output=True, text=True, timeout=120, check=True)
    report = json.loads(result.stdout)
    io.write(service / 'ADMISSION.json', report)
    require(handoff.previous.admitted(report, plan), 'fresh_privileged_original_full_admission')
    with (service / 'NATIVE.log').open('x') as log:
        child = subprocess.Popen(command(service, 'native', document),
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']), stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    native_identity = handoff.identities.identity(child.pid)
    io.write(service / 'LAUNCH.json', dict(identity=native_identity, guardian=identity,
        admission=io.ref(service / 'ADMISSION.json'), launched_unix=time.time(), independent=True))
    try:
        child.wait(timeout=max(1, document['hard_end_unix'] - time.time() - 5))
    finally:
        if child.poll() is None:
            from gpu import orch_r118_code_parallel_loop as old
            old.cleanup_native(native_identity, Path(pointers['root']))
        io.write(service / 'GUARD_TERMINAL.json', dict(identity=native_identity,
            returncode=child.poll(), observed_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'guard', 'native'))
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--prior-service', type=Path)
    arguments = parser.parse_args()
    if arguments.phase == 'prepare':
        print(json.dumps(prepare(arguments.prior_service, arguments.service), sort_keys=True))
    else:
        globals()[arguments.phase](arguments.service)
