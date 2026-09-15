"""Natural-C100, lease-bound old CODE successors. No fitting or actor interruption."""

import argparse
from collections import Counter
from copy import deepcopy
import fcntl
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_r119_code_old_fork as fork
from gpu import orch_r119_code_old_admission as admission
from gpu import orch_r124_code_capacity as capacity


io, require = fork.io, fork.require
MODULE = 'gpu.orch_r126_code_capacity'
LANE = 'campaign_code_parent'


def identity(pid):
    from gpu import orch_r108_code_parent_r109_run as original
    return original.common.process_identity(Path('/proc') / str(pid))


def exited(expected):
    path = Path('/proc') / str(expected['pid'])
    if not path.exists():
        return True
    try:
        current = identity(expected['pid'])
        return any(current[key] != expected[key] for key in ('pid', 'uid', 'start_ticks', 'boot_id'))
    except (FileNotFoundError, ProcessLookupError):
        return True


def schedules(rows):
    result = []
    for task in rows:
        phases = ('segment1', 'segment2', 'parent2', 'reflection2', 'continuation') if task['split'] == 'TRAIN' else ('held',)
        for phase in phases:
            result.append(dict(cell_id=task['task_id'] + '_' + phase, task_id=task['task_id'],
                cycle=task['cycle'], slot=task['slot'], phase=phase, kind='PARENT' if phase == 'parent2' else 'NATIVE'))
    for cycle in sorted({row['cycle'] for row in rows}):
        for round_number in (1, 2, 3):
            task_id = f'R110_META_node3_episode_C{cycle:03d}'
            phase = 'meta_child' + str(round_number)
            result.append(dict(cell_id=task_id + '_' + phase, task_id=task_id,
                cycle=cycle, slot=0, phase=phase, kind='NATIVE'))
    require(len({row['cell_id'] for row in result}) == len(result), 'unique_reserved_calls')
    return result


def freeze_cohorts(output, old_cohort, exclusions):
    output = Path(output)
    old_rows, denied = io.checked(old_cohort), io.checked(exclusions)
    sets = {field:set(denied[key]) | {row[field] for row in old_rows}
        for field, key in (('task_id', 'task_ids'), ('prompt_sha256', 'prompt_hashes'), ('question_sha256', 'question_hashes'))}
    manifests, training, held = [], {}, []
    for chunk in range(capacity.MAX_CHUNKS):
        rows = capacity.chunk_registry(chunk, sets['task_id'], sets['prompt_sha256'], sets['question_sha256'])
        calls = schedules(rows)
        counts = Counter(row['kind'] for row in calls)
        require(counts == dict(NATIVE=960, PARENT=128), 'exact_chunk_call_capacity')
        for field in sets:
            sets[field].update(row[field] for row in rows)
        folder = output / f'chunk_{chunk:03d}'
        io.write(folder / 'COHORT_PRIVATE.json', rows)
        io.write(folder / 'RESERVATIONS.json', calls)
        manifests.append(dict(capacity.chunk_manifest(chunk, rows), cohort=io.ref(folder / 'COHORT_PRIVATE.json'),
            reservations=io.ref(folder / 'RESERVATIONS.json')))
        training.update({row['task_id']:row['content_sha256'] for row in rows if row['split'] == 'TRAIN'})
        held.extend(row['task_id'] for row in rows if row['split'] == 'HELD')
    value = dict(schema='R126_CODE_FROZEN_CAPACITY_COHORTS_V1', chunks=manifests,
        old_cohort=old_cohort, exclusions=exclusions, train_tasks=training, held_task_ids=held,
        cohort_sha256=capacity.digest(manifests), no_benchmark_independence_claim=True)
    io.write(output / 'COHORTS.json', value)
    return io.ref(output / 'COHORTS.json')


def arm(root, predecessor, cohort_reference, tests_reference):
    root, predecessor = Path(root).resolve(), Path(predecessor).resolve(strict=True)
    old_reference = io.ref(predecessor / 'PLAN.json')
    old = io.checked(old_reference)
    contract = capacity.capacity(old, old_reference)
    require(io.checked(tests_reference)['passed'] is True, 'own_native_CPU_passed')
    cohort = io.checked(cohort_reference)
    require(len(cohort['chunks']) == capacity.MAX_CHUNKS, 'full_lease_capacity_frozen')
    require(io.ref(predecessor / 'COHORT_PRIVATE.json')['sha256'] == cohort['old_cohort']['sha256'],
        'same_excluded_original_cohort')
    pins = dict(old['source_files'])
    for path, pin in pins.items():
        require(io.ref(path)['sha256'] == pin, 'frozen_predecessor_sources')
    dependency_root = Path(fork.__file__).resolve().parents[1]
    for path in dependency_root.rglob('*.py'):
        pins[str(path)] = io.ref(path)['sha256']
    overlay = Path(__file__).resolve().parents[1]
    for name in ('gpu/orch_r126_code_capacity.py', 'gpu/orch_r124_code_capacity.py', 'tests/test_orch_r126_code_capacity.py'):
        path = overlay / name
        pins[str(path)] = io.ref(path)['sha256']
    launch = io.read(predecessor / 'LAUNCH.json')
    require(not root.exists() and time.time() < contract['train_end_unix'], 'new_namespace_inside_actual_lease')
    value = dict(schema='R126_CODE_NATURAL_C100_ARM_V1', root=str(root), predecessor=old_reference,
        predecessor_launch=io.ref(predecessor / 'LAUNCH.json'), original_identities=[launch['identity'], launch['guardian']],
        contract=contract, cohorts=cohort_reference, tests=tests_reference, source_files=pins,
        source_root=str(overlay), dependency_root=str(dependency_root),
        interpreter=old['interpreter'], poll_seconds=20, GPU_launch_only_after_natural_C100=True,
        no_signals=True, parent_broker_owned_separately=True, observed_unix=time.time())
    io.write(root / 'ARM.json', value)
    io.write(root / 'PUBLICATION.json', dict(own_CPU_and_provenance_passed=True,
        authorization='Main R126 natural-C100 seven old CODE capacity continuation',
        journal='research_loop/workers/R118_CODE_PARALLEL_STAGE.md', elicitation_only=True, optimizer_updates=0,
        prospective_native_increment=contract['prospective_native_increment'],
        prospective_parent_increment=contract['prospective_parent_increment']))
    return io.ref(root / 'ARM.json')


def checked_arm(root):
    value = io.read(Path(root) / 'ARM.json')
    require(value['root'] == str(Path(root).resolve()), 'exact_successor_root')
    old = io.checked(value['predecessor'])
    require(value['contract'] == capacity.capacity(old, value['predecessor']), 'unchanged_prospective_contract')
    for path, pin in value['source_files'].items():
        require(io.ref(path)['sha256'] == pin, 'frozen_successor_source')
    require(io.checked(value['tests'])['passed'] is True, 'native_CPU_proof')
    return value, old


def release_snapshot(armed, old):
    root = Path(old['root'])
    require(all(exited(item) for item in armed['original_identities']), 'both_original_actors_exited')
    terminal = io.read(root / 'TERMINAL.json')
    require(io.read(root / 'GUARD_TERMINAL.json')['returncode'] == 0, 'original_guard_natural_success')
    complete = io.read(root / LANE / 'CYCLE_100_COMPLETE.json')
    after = io.read(root / 'AFTER.json')
    actor = io.read(root / 'ACTOR_READY.json')
    require(after['unchanged'] is True and after['model'] == actor['model'], 'exact_readonly_model_after')
    paths = sorted((root / LANE / 'cells').glob('*.json'))
    rows = [io.read(path) for path in paths]
    require(all(row['status'] in ('COMPLETE', 'FAILED') for row in rows if row['kind'] == 'NATIVE'),
        'all_native_slots_terminal')
    require(sum(row['kind'] == 'NATIVE' for row in rows) == 74 * 15
        and sum(row['kind'] == 'PARENT' for row in rows) == 74 * 2, 'all_74_predecessor_cycles_charged')
    context_path = root / LANE / 'CONTEXT_DISTILLATION_C100.json'
    context = io.read(context_path)
    require(context['status'] == 'COMPLETE' and context['weight_updates'] == 0
        and context['after_context_sha256'] == capacity.original.digest(context['own_context']), 'actual_final_TRAIN_context')
    lessons = list(io.checked(old['inputs']['context']).get('lessons', []))
    for cycle in range(27, 101):
        parents = sorted((row for row in rows if row['cycle'] == cycle and row['kind'] == 'PARENT'), key=lambda row:row['slot'])
        require([row['slot'] for row in parents] == [1, 2] and all(row['lesson'] == '' for row in parents),
            'exact_async_old_lesson_state')
        lessons.extend([''] * 5)
    pending = [dict(record=io.ref(path), request=io.ref(root / 'parent_queue' / (row['cell_id'] + '.request.json')))
        for path, row in zip(paths, rows) if row['kind'] == 'PARENT' and row['status'] == 'PENDING']
    files = {str(path.relative_to(root)):io.ref(path)['sha256'] for path in root.rglob('*')
        if path.is_file() and (path.suffix == '.json' or path.name in ('NATIVE.log', 'GUARD.log'))}
    counts = Counter(row['kind'] for row in rows)
    boundary = dict(terminal_status=terminal['status'], completed_cycle=complete['cycle'],
        latest_charged_cycle=max(row['cycle'] for row in rows), native_inflight=0,
        actor_exited=True, guard_exited=True, readonly_verified=True,
        terminal=io.ref(root / 'TERMINAL.json'), cycle_complete=io.ref(root / LANE / 'CYCLE_100_COMPLETE.json'),
        context=io.ref(context_path), after=io.ref(root / 'AFTER.json'), context_cycle=100,
        all_charges_preserved=True, native_used=old['ancestry']['native_used'] + counts['NATIVE'],
        parent_used=old['ancestry']['parent_used'] + counts['PARENT'], pending_parent_references=[entry['record'] for entry in pending])
    return dict(boundary=boundary, files=files, context=dict(context, lessons=lessons), pending_parents=pending)


def activate(root):
    root = Path(root)
    armed, old = checked_arm(root)
    snapshot = release_snapshot(armed, old)
    io.write(root / 'PREDECESSOR_FILES.json', snapshot['files'])
    snapshot['boundary']['ledger_manifest'] = io.ref(root / 'PREDECESSOR_FILES.json')
    carried = capacity.settled_handoff(armed['contract'], snapshot['boundary'])
    io.write(root / 'CARRY_PRIVATE.json', snapshot['context'])
    io.write(root / 'RELEASE.json', dict(boundary=snapshot['boundary'], carried=carried,
        pending_parents=snapshot['pending_parents'], observed_unix=time.time()))
    cohort = io.checked(armed['cohorts'])
    plan = deepcopy(old)
    plan.update(schema='R126_CODE_LEASE_SUCCESSOR_V1', root=str(root), source_root=armed['source_root'],
        source_files=armed['source_files'], first_cycle=101, cycle_limit=armed['contract']['last_new_cycle'],
        predecessor=armed['predecessor'], release=io.ref(root / 'RELEASE.json'), cohorts=armed['cohorts'],
        train_tasks=cohort['train_tasks'], cohort_sha256=cohort['cohort_sha256'],
        life_id=old['life_id'] + '_R126_CAPACITY', continuation_not_new_learning=True)
    plan['ancestry'] = dict(old['ancestry'], native_used=carried['carried_native_used'],
        parent_used=carried['carried_parent_used'], native_cap=carried['new_absolute_native_cap'],
        parent_cap=carried['new_absolute_parent_cap'], first_cycle=101,
        prospective_increment=armed['contract'], historical_ancestry=deepcopy(old['ancestry']))
    plan['inputs'] = dict(context=io.ref(root / 'CARRY_PRIVATE.json'), lease=old['inputs']['lease'],
        cohorts=armed['cohorts'], release=io.ref(root / 'RELEASE.json'))
    io.write(root / 'PLAN.json', plan)
    io.write(root / 'ACTIVATED.json', dict(plan=io.ref(root / 'PLAN.json'), arm=io.ref(root / 'ARM.json'),
        release=io.ref(root / 'RELEASE.json'), observed_unix=time.time()))
    shutil.copyfile(Path(old['root']) / 'SERVICE_IDENTITY.json', root / 'SERVICE_IDENTITY.json')
    for name in (LANE + '/cells', 'parent_queue', 'delayed_interventions', 'carried_parents'):
        (root / name).mkdir(parents=True, exist_ok=True)
    io.write(root / 'PARENT_HANDOFF.json', dict(schema='R126_CODE_PARENT_CAPACITY_HANDOFF_V1',
        previous_root=old['root'], root=str(root), plan=io.ref(root / 'PLAN.json'),
        original_queue=str(Path(old['root']) / 'parent_queue'), new_queue=str(root / 'parent_queue'),
        pending_references=snapshot['pending_parents'], parent_requests_reissued=0,
        cumulative_parent_used=carried['carried_parent_used'], prospective_parent_increment=8192,
        terminal=str(root / 'TERMINAL.json'), deadline_unix=plan['train_end_unix'],
        broker_process_started=False, cadence='EPISODE', ttl_seconds=600, wait_seconds=0))
    return plan


def plan_for(root):
    armed, old = checked_arm(root)
    plan = io.read(Path(root) / 'PLAN.json')
    require(io.read(Path(root) / 'ACTIVATED.json')['plan'] == io.ref(Path(root) / 'PLAN.json'),
        'exact_activated_plan')
    released = io.checked(plan['release'])
    carried = capacity.settled_handoff(armed['contract'], released['boundary'])
    require(plan['root'] == str(Path(root).resolve()) and plan['first_cycle'] == 101
        and plan['cycle_limit'] == 4196 and plan['optimizer_updates'] == 0, 'lease_successor_no_optimizer')
    require(plan['ancestry']['native_cap'] == carried['new_absolute_native_cap']
        and plan['ancestry']['parent_cap'] == carried['new_absolute_parent_cap']
        and plan['ancestry']['native_used'] == carried['carried_native_used']
        and plan['ancestry']['parent_used'] == carried['carried_parent_used'], 'explicit_new_caps_only')
    cohort = io.checked(armed['cohorts'])
    require(plan['cohorts'] == armed['cohorts'] and plan['train_tasks'] == cohort['train_tasks']
        and plan['cohort_sha256'] == cohort['cohort_sha256'], 'frozen_new_TRAIN_registry')
    for key in ('adapter', 'model_dir', 'gpu_uuid', 'physical', 'wrapper', 'arm', 'host_sha256', 'lease_end_unix',
            'train_end_unix', 'hard_end_unix', 'parent_wait_seconds', 'parent_ttl_seconds', 'parent_cadence'):
        require(plan[key] == old[key], 'same_model_allocation_loop_and_lease')
    for entry in plan['inputs'].values():
        io.checked(entry)
    if plan['adapter'] is not None:
        for name, pin in plan['adapter']['files']:
            require(io.ref(Path(plan['adapter']['path']) / name)['sha256'] == pin, 'frozen_actual_adapter')
    return plan


def bind_policy(original, rows):
    namespace = dict(vars(original), CYCLES=4196, frozen_tasks=lambda arm:rows)
    for name in ('meta_task', 'meta_payload', 'validate_meta_payload'):
        function = getattr(original, name)
        namespace[name] = FunctionType(function.__code__, namespace, name, function.__defaults__)
    return SimpleNamespace(**namespace)


def cycle_function(run, context, rows):
    source = inspect.getsource(run.cycles)
    replacements = {"memory,lessons='',[]": 'memory,lessons=restored_memory,list(restored_lessons)',
        "tasks=read(root/'COHORT_PRIVATE.json')": 'tasks=chunk_tasks',
        'range(1,policy.CYCLES+1)': 'range(first_cycle,last_cycle+1)',
        'prior.assert_no_adapter(engine.model)': 'engine.identity()'}
    for before, after in replacements.items():
        require(source.count(before) == 1, 'exact_existing_cycle_source')
        source = source.replace(before, after)
    source += '\n    return memory,lessons\n'
    namespace = dict(vars(run), policy=bind_policy(run.policy, rows), chunk_tasks=rows,
        restored_memory=context['own_context'], restored_lessons=context.get('lessons', []),
        first_cycle=min(row['cycle'] for row in rows), last_cycle=max(row['cycle'] for row in rows), parent=fork.parent_call)
    exec(compile(source, __file__ + ':existing_cycles', 'exec'), namespace)
    return namespace['cycles']


def native(root):
    root = Path(root)
    fork.plan_for = plan_for
    run, plan = fork.configured(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'exact_owned_CVD')
    (root / 'NATIVE_ONCE').mkdir()
    io.write(root / 'NATIVE_REQUEST.json', dict(identity=identity(os.getpid()), plan=io.ref(root / 'PLAN.json')))
    cohort = io.checked(plan['cohorts'])
    released = io.checked(plan['release'])
    old_root = Path(io.checked(plan['predecessor'])['root'])
    for entry in released['pending_parents']:
        record, request = io.checked(entry['record']), io.checked(entry['request'])
        target = root / 'carried_parents' / (record['cell_id'] + '.json')
        io.write(target, record)
        fork.PENDING.setdefault(str(old_root), {})[record['cell_id']] = dict(path=target, record=record, request=request)
    original_poll = fork.poll_parents
    def combined_poll(checked_root, actual_plan, now=None):
        require(Path(checked_root) == root, 'same_successor_parent_root')
        return original_poll(old_root, actual_plan, now) + original_poll(root, actual_plan, now)
    fork.poll_parents = combined_poll
    counters = Counter(NATIVE=plan['ancestry']['native_used'], PARENT=plan['ancestry']['parent_used'])
    schedule = {}
    def begin(checked_root, task, phase):
        require(Path(checked_root) == root, 'same_call_root')
        selected = schedule.get((task['task_id'], phase))
        require(selected is not None, 'frozen_reservation_required')
        kind = selected['kind']
        require(counters[kind] < plan['ancestry'][kind.lower() + '_cap'], 'prospective_cumulative_call_cap')
        path = root / LANE / 'cells' / (selected['cell_id'] + '.json')
        row = dict(selected, status='STARTED', started_unix=time.time())
        io.write(path, row)
        counters[kind] += 1
        return path, row
    run.begin = begin
    def check(label):
        deadline = plan['hard_end_unix'] - 1 if label == 'readonly_hash' else plan['train_end_unix']
        require(time.time() < deadline, 'actual_existing_lease_end:' + label)
    engine, failure = None, None
    try:
        engine = fork.load_engine(run, plan, check)
        require(engine.identity() == io.checked(released['boundary']['after'])['model'],
            'exact_loaded_predecessor_model_identity')
        io.write(root / 'ACTOR_READY.json', dict(identity=identity(os.getpid()), model=engine.identity(),
            loaded_unix=time.time(), ancestry=plan['ancestry'], optimizer_updates=0, independent_elicitation=True))
        context = io.checked(plan['inputs']['context'])
        original_policy = run.policy
        for chunk in cohort['chunks']:
            if time.time() >= plan['train_end_unix'] - 120:
                break
            rows = io.checked(chunk['cohort'])
            calls = io.checked(chunk['reservations'])
            require(capacity.digest(rows) == chunk['registry_sha256'] and calls == schedules(rows), 'frozen_chunk_before_dispatch')
            schedule = {(row['task_id'], row['phase']):row for row in calls}
            run.policy = bind_policy(original_policy, rows)
            memory, lessons = cycle_function(run, context, rows)(root, plan['arm'], engine, check, parent_call=fork.parent_call)
            context = dict(own_context=memory, lessons=lessons)
            io.write(root / f'CHUNK_{chunk["chunk"]:03d}_CARRY_PRIVATE.json', context)
            io.write(root / f'CHUNK_{chunk["chunk"]:03d}_COMPLETE.json', dict(chunk=chunk['chunk'],
                cumulative_counts=dict(counters), finished_unix=time.time(), optimizer_updates=0))
    except BaseException as error:
        failure = error
    finally:
        if engine is not None:
            try:
                engine.verify_base()
                io.write(root / 'AFTER.json', dict(model=engine.identity(), unchanged=True))
            except BaseException as verification_error:
                io.write(root / 'AFTER_FAILED.json', dict(error_type=type(verification_error).__name__,
                    observed_unix=time.time(), unchanged_not_verified=True))
                failure = failure or verification_error
        io.write(root / 'TERMINAL.json', dict(status='FAILED' if failure else 'COMPLETE',
            error_type=type(failure).__name__ if failure else None, observed_unix=time.time(),
            cumulative_counts=dict(counters), optimizer_updates=0, no_retry=True))
    if failure:
        raise failure


def command(root, phase, armed):
    code = ('import sys,runpy;sys.path.insert(0,' + repr(armed['dependency_root'])
        + ');import gpu;gpu.__path__.insert(0,' + repr(str(Path(armed['source_root']) / 'gpu'))
        + ');sys.argv=' + repr([MODULE, phase, '--root', str(root)])
        + ';runpy.run_module(' + repr(MODULE) + ',run_name="__main__")')
    return [armed['interpreter'], '-B', '-c', code]


def guard(root):
    root = Path(root)
    armed, old = checked_arm(root)
    plan = plan_for(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard')
    (root / 'GUARD_ONCE').mkdir()
    for attempt in range(20):
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1']
            + command(root, 'scan', armed), capture_output=True, text=True, timeout=120, check=True)
        report = json.loads(result.stdout)
        io.write(root / f'ADMISSION_{attempt:02d}.json', report)
        if report['clear'] is True:
            break
        require(fork.fresh_scan_retryable(report), 'unknown_or_occupied_GPU_not_waived')
        time.sleep(5)
    require(report['clear'] is True and report['scanner_euid'] == 0 and report['gpu']['uuid'] == plan['gpu_uuid']
        and report['gpu']['index'] == plan['physical'], 'full_privileged_fresh_clear')
    with (root / 'NATIVE.log').open('x') as log:
        child = subprocess.Popen(command(root, 'native', armed), cwd=armed['dependency_root'],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']), stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    native_identity = identity(child.pid)
    io.write(root / 'LAUNCH.json', dict(identity=native_identity, guardian=identity(os.getpid()),
        admission=io.ref(root / f'ADMISSION_{attempt:02d}.json'), plan=io.ref(root / 'PLAN.json'), started_unix=time.time()))
    try:
        child.wait(timeout=max(1, plan['hard_end_unix'] - time.time() - 10))
    finally:
        from gpu import orch_r108_code_parent_r109_run as original
        original.common.stop_owned(child, native_identity)
        io.write(root / 'GUARD_TERMINAL.json', dict(returncode=child.poll(), observed_unix=time.time()))


def watch(root):
    root = Path(root)
    armed, old = checked_arm(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_custodian_only')
    with (root / 'CUSTODIAN.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        io.write(root / 'ARMED.json', dict(identity=identity(os.getpid()), arm=io.ref(root / 'ARM.json'),
            observed_unix=time.time(), CPU_only=True, waiting_for='NATURAL_C100_BOTH_ACTORS_EXITED'))
        try:
            while time.time() < armed['contract']['train_end_unix'] - 120:
                if all(exited(item) for item in armed['original_identities']):
                    activate(root)
                    guard(root)
                    return
                time.sleep(armed['poll_seconds'])
            io.write(root / 'CUSTODIAN_EXPIRED.json', dict(no_GPU_dispatch=True, observed_unix=time.time()))
        except BaseException as error:
            io.write(root / 'CUSTODIAN_FAILED.json', dict(error_type=type(error).__name__, reason=str(error),
                observed_unix=time.time(), no_retry=True))
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('watch', 'scan', 'native'))
    parser.add_argument('--root', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.phase == 'scan':
        fork.plan_for = plan_for
        print(json.dumps(admission.scan(arguments.root)))
    else:
        globals()[arguments.phase](arguments.root)
