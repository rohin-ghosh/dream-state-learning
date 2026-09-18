"""One same-life node3 filter repair at an exact saved sleep boundary."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time

from r209_node3_audit import metadata, read_record


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
POLICY = 'R209_ENGLISH_PROSE_TARGET_QUARANTINE_V1'
PHASE = 'r209_filter'
ENRICH = False
OVERLAY = 'ab7c3ada0780d8414aba30e59721df1bb8c51fdee747105359682bae3c144f84'
REPAIR_FILES = {
    'gpu/orch_r184_think_act_learn.py': '0575afc35273c2cffc90f45be3635d562ab5d6eef7d7d22e3dcf36c365be9673',
    'organism_v6/orch_r203_prose_target_filter.py': '4bceeff13176f61b8ee32f4ae4f995ce8cce5d2aba7b2286bd13b6e48281d9ed',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)


def files(root):
    return {str(path.relative_to(root)): sha(path) for path in Path(root).rglob('*') if path.is_file()}


def proposed_plan(previous, source, *, enrich=False):
    plan = deepcopy(previous)
    plan['source_root'] = str(source)
    startup = Path(previous['startup_context']['path']).relative_to(previous['source_root'])
    plan['startup_context']['path'] = str(source / startup)
    plan['think_act_learn']['prose_target_filter'] = POLICY
    if enrich:
        plan['max_sleeps'] = None
        plan['think_act_learn']['environment_facts'] = (
            'R210 parented complementary-experience phase after preserved earlier results, not a '
            'parent-withdrawn control. Astra is an operator-authored parent, not Rohin. The frozen base '
            'and this arm\'s plasticity settings are unchanged. No code executor is connected. '
            'Only pinned excerpts and prose reasoning are available; peer assertions in THINK are '
            'masked context, never execution receipts or imported training targets. New English '
            'own targets use R209 quarantine without rewriting raw history.')
    return plan


def boundary_document(record, tail_kinds):
    require(record['kind'] == 'SLEEP_COMPLETE' and all(kind == 'R184_LEARN_COMPLETE' for kind in tail_kinds),
        'exact_COMPLETE_no_subsequent_generation')
    document = record['document']
    state = document['resume_state']['state']
    canonical = json.dumps(state, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    require(document['status'] == 'COMPLETE' and state['pending'] is None
        and state['sleep_frontier'] == len(state['rows'])
        and hashlib.sha256(canonical).hexdigest() == document['resume_state']['sha256'],
        'quiescent_saved_RNG_boundary')
    return document


def environment(source):
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=os.pathsep.join((str(source), str(source / 'tests'))),
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')


def stage(name):
    import r205_prepare as preparation
    arm = ROOT / name
    phase = arm / PHASE
    phase.mkdir(mode=0o700)
    old_guard = read(arm / 'control/GUARD.json')
    previous = read(old_guard['plan_path'])
    ready = read(ROOT / 'r206_ready/READY.json')
    repair = read(ROOT / 'r209_repair/READY.json')
    require(sha(ROOT / 'r206_ready/runtime_overlay.tar.gz') == ready['archive_sha256'] == OVERLAY,
        'frozen_R206_archive')
    require(repair['files'] == REPAIR_FILES and repair['tests']['passed']
        and repair['base_archive_sha256'] == OVERLAY and repair['prose_target_filter'] == POLICY,
        'exact_Descartes_tested_two_file_repair')
    source = phase / 'source'
    shutil.copytree(arm / 'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    preparation.extract(ROOT / 'r206_ready/runtime_overlay.tar.gz', source, ready['files'])
    for relative, expected in REPAIR_FILES.items():
        require(sha(ROOT / 'r209_repair/source' / relative) == expected, 'repair_file_hash')
        shutil.copy2(ROOT / 'r209_repair/source' / relative, source / relative)
    for filename in ('r209_node3_runtime.py', 'r209_node3_audit.py'):
        shutil.copy2(ROOT / filename, source / 'gpu' / filename)
    if ENRICH:
        shutil.copy2(ROOT / 'r210_node3_runtime.py', source / 'gpu/r210_node3_runtime.py')
        shutil.copy2(ROOT / 'r210_node3_runtime.py', source / 'r210_node3_runtime.py')
    for filename in ('r209_filter_resume.py', 'r209_node3_audit.py'):
        shutil.copy2(ROOT / filename, source / filename)
    shutil.copy2(ROOT / 'test_r209_node3.py', source / 'tests/test_r209_node3.py')
    for path in (ROOT / 'r209_repair/tests').glob('test_*.py'):
        shutil.copy2(path, source / 'tests' / path.name)
    plan = proposed_plan(previous, source, enrich=ENRICH)
    control = phase / 'control'
    control.mkdir(mode=0o700)
    write(control / 'PLAN.json', plan)
    tests = ['test_r209_node3', 'test_r205_runtime', 'test_existing_prose',
        'test_orch_r194_code_target_filter', 'test_orch_r195_learn_review_filter', 'test_orch_r184_think_act_learn',
        'test_orch_r125_stream_journal', 'test_console_prose_cadence']
    with (phase / 'CPU.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'unittest', '-q', *tests], cwd=source,
            env=environment(source), stdout=output, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'receiving_CPU_tests_required')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    cpu = dict(passed=True, source_pins=pins, tests=tests, observed_unix=time.time(),
        log_sha256=sha(phase / 'CPU.log'), cuda_visible_devices='', repair_files=REPAIR_FILES,
        plan_delta='source_root,startup_context_path,prose_target_filter' + (',R210_environment_facts,max_sleeps=None' if ENRICH else ''),
        plasticity_and_walls_unchanged=True)
    write(control / 'RECEIVING_CPU.json', cpu)
    allocation = read(old_guard['allocation_path'])
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), declared_unix=time.time(),
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'),
        cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'))
    write(control / 'ALLOCATION.json', allocation)
    config = deepcopy(old_guard)
    config.update(source_pins=pins, resume=True, attempt_dir=str(control),
        plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', config)
    subprocess.run([PYTHON, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; '
        'import sys; validate(sys.argv[1])', str(control / 'GUARD.json')], cwd=source,
        env=environment(source), check=True, timeout=30)
    write(phase / 'STAGED.json', dict(status='CPU_TESTED_NOT_LIVE', observed_unix=time.time(),
        arm=name, old_guard_sha256=sha(arm / 'control/GUARD.json'), policy=POLICY,
        original_source_untouched=True, enrichment=ENRICH, cpu_sha256=sha(control / 'RECEIVING_CPU.json')))
    print(json.dumps(dict(arm=name, status='CPU_TESTED_NOT_LIVE', phase=str(phase))), flush=True)


def actor_identity(pid, guard):
    process = Path('/proc', str(pid))
    command = (process / 'cmdline').read_bytes().split(b'\0')
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    require(str(guard).encode() in command and fields[0] not in ('Z', 'X'), 'exact_owned_actor')
    return dict(pid=pid, start_ticks=fields[19], guard=str(guard))


def preserve_boundary(arm, phase, record, actor):
    document = boundary_document(record, [])
    attempt = str(time.time_ns())
    preserved = phase / ('preserved_' + attempt)
    preserved.mkdir(mode=0o700)
    checkpoint = arm / 'raw/checkpoints' / f'sleep_{document["cycle"]:06d}'
    shutil.copytree(checkpoint, preserved / checkpoint.name)
    require(files(checkpoint) == files(preserved / checkpoint.name), 'checkpoint_bytes_preserved')
    shutil.copytree(arm / 'raw/stream', preserved / 'stream')
    require(files(arm / 'raw/stream/records') == files(preserved / 'stream/records'), 'journal_bytes_preserved')
    with (phase / ('BOUNDARY_CPU_' + attempt + '.log')).open('x') as output:
        validation = subprocess.run([PYTHON, '-B', str(ROOT / 'r210_snapshot_check.py'),
            str(preserved / 'stream'), str(arm / 'control/GUARD.json'),
            read(phase / 'STAGED.json')['old_guard_sha256'], str(record['index'])],
            cwd=phase / 'source', env=environment(phase / 'source'), stdout=output, stderr=subprocess.STDOUT, timeout=120)
    require(validation.returncode == 0, 'actual_preserved_journal_replays_under_R209')
    write(phase / 'PRESERVED_COMPLETE.json', dict(actor=actor, observed_unix=time.time(),
        cycle=document['cycle'], complete_index=record['index'], complete_sha256=record['sha256'],
        state_sha256=document['resume_state']['sha256'], optimizer_steps=document['checkpoint']['optimizer_steps'],
        checkpoint_files=files(preserved / checkpoint.name), preserved_path=str(preserved),
        same_life_root=str(arm / 'raw'),
        plasticity_unchanged=True, raw_history_preserved=True, birth_compaction_not_repeated=True,
        phase='R210_PARENTED_COMPLEMENTARY_EXPERIENCE' if ENRICH else 'R209_FILTER_REPAIR',
        earlier_screen_normally_completed=actor is None))
    return document


def dispatch_phase(arm, phase, document):
    source, control = phase / 'source', phase / 'control'
    module = 'gpu.r210_node3_runtime' if ENRICH else 'gpu.r209_node3_runtime'
    with (phase / 'supervisor.log').open('x') as output:
        process = subprocess.Popen([PYTHON, '-B', '-m', module, 'dispatch', '--config', str(control / 'GUARD.json')],
            cwd=source, env=environment(source), stdin=subprocess.DEVNULL, stdout=output,
            stderr=subprocess.STDOUT, start_new_session=True)
    write(phase / 'DISPATCHED.json', dict(observed_unix=time.time(), supervisor_pid=process.pid,
        status='DISPATCHED_NOT_LOADED', boundary_cycle=document['cycle']))
    write(arm / 'ACTIVE_RUNTIME.json', dict(control=str(control), source=str(source),
        boundary_preservation=str(phase / 'PRESERVED_COMPLETE.json'), policy=POLICY))
    print(json.dumps(dict(arm=arm.name, status='DISPATCHED_NOT_LOADED', phase=str(phase))), flush=True)


def continue_completed(arm, phase, paths):
    records = [read_record(path) for path in paths[-3:]]
    require([record['kind'] for record in records] == ['SLEEP_COMPLETE', 'R184_LEARN_COMPLETE', 'TERMINAL'],
        'normal_screen_terminal_required')
    complete, learned, terminal = records
    require(terminal['document']['status'] == 'R184_SCREEN_STOP'
        and learned['previous_sha256'] == complete['sha256'] and terminal['previous_sha256'] == learned['sha256']
        and read(arm / 'control/EXIT.json')['exit_code'] == 0, 'preserved_normal_screen_not_failed')
    for process in Path('/proc').glob('[0-9]*'):
        try:
            command = (process / 'cmdline').read_bytes().split(b'\0')
        except FileNotFoundError:
            continue
        require(str(arm / 'control/GUARD.json').encode() not in command, 'no_existing_native_or_supervisor')
    document = preserve_boundary(arm, phase, complete, None)
    require(read_record(paths[-1])['sha256'] == terminal['sha256'], 'same_completed_head')
    dispatch_phase(arm, phase, document)


def apply(name):
    arm = ROOT / name
    phase = arm / PHASE
    source = phase / 'source'
    control = phase / 'control'
    staged = read(phase / 'STAGED.json')
    require(staged['status'] == 'CPU_TESTED_NOT_LIVE'
        and staged['old_guard_sha256'] == sha(arm / 'control/GUARD.json'), 'tested_same_old_guard')
    descriptor = os.open(phase / 'WATCHER.lock', os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    paths = sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
    if any(metadata(path) == 'TERMINAL' for path in paths[-4:]):
        if ENRICH:
            continue_completed(arm, phase, paths)
        else:
            write(phase / 'COMPLETE_PRESERVED.json', dict(observed_unix=time.time(),
                status='NORMAL_SCREEN_COMPLETE_NO_RESTART', future_English_LEARN_requires_policy=POLICY))
        os.close(descriptor)
        return
    loaded = next(read_record(path) for path in reversed(paths) if metadata(path) == 'LOADED')
    actor = actor_identity(loaded['document']['pid'], arm / 'control/GUARD.json')
    actor_fd = os.pidfd_open(actor['pid'])
    paused = False
    retired = False
    armed_path = phase / ('ARMED_' + str(time.time_ns()) + '.json')
    write(armed_path, dict(actor=actor, observed_unix=time.time(),
        authority='R209 user-requested next-boundary English LEARN repair; preserve plasticity'))
    next_index = max(0, len(paths) - 2)
    try:
        while time.time() < read(control / 'PLAN.json')['hard_end_unix'] - 120:
            path = arm / 'raw/stream/records' / f'{next_index:020d}.json'
            if not path.exists():
                time.sleep(.01)
                continue
            next_index += 1
            kind = metadata(path)
            if kind == 'TERMINAL':
                if ENRICH:
                    while not (arm / 'control/EXIT.json').exists():
                        time.sleep(.05)
                    continue_completed(arm, phase, sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json')))
                    return
                write(phase / 'COMPLETE_PRESERVED.json', dict(status='NORMAL_SCREEN_COMPLETE_NO_RESTART',
                    observed_unix=time.time(), future_English_LEARN_requires_policy=POLICY))
                return
            if kind != 'SLEEP_COMPLETE':
                continue
            require(actor_identity(actor['pid'], arm / 'control/GUARD.json') == actor, 'same_actor')
            signal.pidfd_send_signal(actor_fd, signal.SIGSTOP)
            paused = True
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                tasks = list(Path('/proc', str(actor['pid']), 'task').iterdir())
                if tasks and all((task / 'stat').read_text().rsplit(')', 1)[1].split()[0] in ('T', 't') for task in tasks):
                    break
                time.sleep(.01)
            else:
                raise TimeoutError('native_threads_not_paused')
            current = sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
            tail = [metadata(item) for item in current[next_index:]]
            if any(item != 'R184_LEARN_COMPLETE' for item in tail):
                signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
                paused = False
                continue
            record = read_record(path)
            document = boundary_document(record, tail)
            plan = read(control / 'PLAN.json')
            if plan['max_sleeps'] is not None and document['cycle'] >= plan['max_sleeps']:
                signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
                paused = False
                write(phase / 'COMPLETE_PRESERVED.json', dict(status='NORMAL_SCREEN_COMPLETE_NO_RESTART',
                    observed_unix=time.time(), cycle=document['cycle'], future_English_LEARN_requires_policy=POLICY))
                return
            document = preserve_boundary(arm, phase, record, actor)
            require(read_record(current[-1])['sha256'] == read_record(sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))[-1])['sha256'],
                'same_paused_head')
            signal.pidfd_send_signal(actor_fd, signal.SIGTERM)
            signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
            paused = False
            retired = True
            poller = select.poll()
            poller.register(actor_fd, select.POLLIN)
            require(bool(poller.poll(30000)), 'old_native_exited_at_preserved_boundary')
            dispatch_phase(arm, phase, document)
            return
        raise TimeoutError('no_exact_boundary_before_existing_wall')
    except BaseException as error:
        if paused and not retired:
            signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
        write(phase / ('FAILURE_' + str(time.time_ns()) + '.json'), dict(observed_unix=time.time(),
            error_type=type(error).__name__, reason=str(error), old_actor_retired=retired,
            old_actor_resumed=paused and not retired))
        raise
    finally:
        os.close(actor_fd)
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('stage', 'apply'))
    parser.add_argument('arm', choices=('conversational', 'p32', 'peer_repo'))
    arguments = parser.parse_args()
    globals()[arguments.mode](arguments.arm)
