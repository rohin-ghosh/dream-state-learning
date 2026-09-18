"""One-shot independent GRID morning FINAL custody and same-life resumption."""

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import struct
import subprocess
import sys
import time


MORNING = 1789538400
EVAL_END = MORNING + 1200
BOUNDARY_END = MORNING + 600
TRAIN_END = 1789596120
HARD_END = 1789596240
ROOT = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915')
SOURCE = Path('/localhome/local-rohing/orch_r119_grid_independent_source_20260915_v1')
ORIGINAL_SHA = 'a4129eca891e0cd9dc2f49f607e5d53d292c662b56a501d4a1611779feb8be7c'
EVENT = 'final_20260916T060000Z_r119_v1'
BRANCHES = {
    'F4': ('independent_r119_v1', 'R119_GRID_INDEPENDENT_TERMINAL.json', 3324550),
    'A4': ('independent_r119_recovery_v2', 'R119_GRID_INDEPENDENT_RECOVERY_V2_TERMINAL.json', 3407701),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return {'path': str(Path(path).resolve(strict=True)), 'sha256': sha(path)}


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def module(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(loaded)
    return loaded


def original():
    path = SOURCE / 'gpu/orch_r119_grid_independent.py'
    require(sha(path) == ORIGINAL_SHA, 'unchanged_working_native')
    return module(path, 'r119_independent_final_dependency')


def process(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rpartition(') ')[2].split()
    require(fields[0] != 'Z', 'process_not_zombie')
    return dict(pid=pid, start_ticks=fields[19], uid=directory.stat().st_uid,
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                command_sha256=hashlib.sha256((directory / 'cmdline').read_bytes()).hexdigest())


def same_process(expected):
    try:
        return process(expected['pid']) == expected
    except (FileNotFoundError, ProcessLookupError, ValueError):
        return False


def event_paths(branch):
    root = ROOT / branch
    return root, root / EVENT


def validate_scope(plan):
    require(plan['schema'] == 'R119_GRID_INDEPENDENT_FINAL_LIFECYCLE_V1', 'new_independent_event')
    require(plan['branch'] in BRANCHES and plan['event'] == EVENT, 'exact_grid_event')
    root, output = event_paths(plan['branch'])
    require(plan['root'] == str(root) and plan['output'] == str(output), 'own_output_only')
    require(plan['morning_unix'] == MORNING and plan['boundary_end_unix'] == BOUNDARY_END
            and plan['evaluation_end_unix'] == EVAL_END and plan['train_end_unix'] == TRAIN_END
            and plan['hard_end_unix'] == HARD_END, 'distinct_fixed_clocks')
    require(plan['native_call_cap'] == 8 and plan['parent_call_cap'] == 0
            and plan['optimizer_steps'] == 0 and plan['training_call_cap'] == 0
            and plan['lease_wall_extra_calls'] == 0, 'only_eight_new_eval_calls')
    require(plan['parent_absent'] and not plan['readout_carry_access']
            and not plan['shared_coordinator'] and not plan['old_final_retry'], 'sealed_independent_scope')
    require(plan['mailbox_era'] == BRANCHES[plan['branch']][0], 'preserve_applied_parent_cursor')
    require(plan['predecessor']['pid'] == BRANCHES[plan['branch']][2], 'actual_owned_predecessor')


def validate(plan):
    validate_scope(plan)
    for path, expected in plan['source_files'].items():
        require(sha(path) == expected, 'frozen_source_changed:' + path)
    require(plan['source_files'].get(str(Path(__file__).resolve())) == sha(__file__), 'own_source_bound')
    for key in ('config', 'clock', 'checkpoint', 'ready', 'budget', 'final_file'):
        reference = plan[key]
        require(sha(reference['path']) == reference['sha256'], 'frozen_' + key)
    prior = original()
    grid, admission, root, config, checkpoint = prior.configure(plan['branch'])
    require(grid.END == HARD_END and grid.TRAIN_END == TRAIN_END, 'original_lease_margin')
    held = module(Path(__file__).with_name('orch_r118_grid_final.py'), 'old_final_constants_only')
    held.config_for(plan['branch'])
    require(plan['final_ids'] == list(held.IDS) and plan['decoder'] == held.DECODER
            and plan['held_prompt'] == held.HELD_PROMPT and plan['final_file']['sha256'] == held.FINAL_SHA,
            'original_sealed_panel_prompt_decoder')
    return prior, grid, config, checkpoint


def prepare(branch):
    require(time.time() < MORNING, 'prepare_before_new_morning')
    prior = original()
    grid, admission, root, config, checkpoint = prior.configure(branch)
    era, terminal, pid = BRANCHES[branch]
    held = module(Path(__file__).with_name('orch_r118_grid_final.py'), 'old_grid_final_constants')
    held.config_for(branch)
    expected = process(pid)
    require(expected['uid'] == os.getuid() and grid.read(root / era / 'LOADED.json')['pid'] == pid,
            'actual_loaded_owned_actor')
    require(not (root / terminal).exists(), 'current_actor_not_terminal')
    output = root / EVENT
    require(not output.exists(), 'one_new_morning_namespace')
    sources = dict(grid.read(root / era / 'READY.json')['source_files'])
    for name in ('orch_r119_grid_final_lifecycle.py', 'orch_r119_grid_final_native.py', 'orch_r118_grid_final.py'):
        path = Path(__file__).with_name(name)
        sources[str(path.resolve())] = sha(path)
    for name in ('orch_r119_grid_independent.py', 'orch_r119_grid_async_parent.py', 'orch_r119_grid_lease_budget.py'):
        path = SOURCE / 'gpu' / name
        sources[str(path)] = sha(path)
    prompt_path = prior.OLD / 'research_notes/PARENTING_BATTLE_PLAN_v4_2026-09-15.md'
    sources[str(prompt_path)] = sha(prompt_path)
    plan = dict(schema='R119_GRID_INDEPENDENT_FINAL_LIFECYCLE_V1', branch=branch, event=EVENT,
        root=str(root), output=str(output), morning_unix=MORNING, boundary_end_unix=BOUNDARY_END,
        evaluation_end_unix=EVAL_END, train_end_unix=TRAIN_END, hard_end_unix=HARD_END,
        native_call_cap=8, parent_call_cap=0, training_call_cap=0, optimizer_steps=0,
        lease_wall_extra_calls=0, parent_absent=True, readout_carry_access=False,
        shared_coordinator=False, old_final_retry=False, mailbox_era=era, predecessor=expected,
        old_terminal=str(root / terminal), new_terminal=str(output / 'LIFE_TERMINAL.json'),
        config=ref(root / 'CONFIG.json'), clock=ref(prior.CLOCK), checkpoint=ref(prior.CHECKPOINT),
        ready=ref(root / era / 'READY.json'), budget=ref(root / era / 'LEASE_BUDGET.json'),
        final_file=ref(root / 'FINAL.json'), final_ids=list(held.IDS), decoder=held.DECODER,
        held_prompt=held.HELD_PROMPT, source_files=sources, prepared_unix=time.time(),
        final_window_label='2026-09-16T06:00:00Z_NEW_EVENT_NOT_OLD_FINAL_RETRY',
        lease_wall_disposition='CUSTODY_CLOSE_NO_ADDITIONAL_CAPTURE',
        parent_custody='BROKER_REBIND_AFTER_ACTUAL_RELEASE_PENDING_CLAIMS_PRESERVED')
    validate(plan)
    write(output / 'PLAN.json', plan)
    return ref(output / 'PLAN.json')


def completed_boundary(root):
    rows = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line]
    cycle = max(row.get('cycle', 0) for row in rows)
    path = root / 'cycles' / f'{cycle:04d}' / 'TRAIN_COMPLETE.json'
    require(path.exists(), 'not_completed_cycle')
    document = read(path)
    require(len(document['outcomes']) == 2 and document['optimizer_steps'] == 0
            and document['carry'] == read(root / 'CARRY.json'), 'two_episodes_durable_carry')
    for row in rows:
        if row.get('cycle') == cycle and row['kind'] == 'NATIVE':
            require(row['split'] == 'TRAIN' and not row.get('attached_readout'), 'no_eval_in_train_cursor')
            require(read(root / 'calls' / f'N{row["number"]:05d}.json')['status'] == 'COMPLETE',
                    'no_unfinished_model_input')
    return dict(cycle=cycle, next_cycle=cycle + 1, ledger=ref(root / 'LEDGER.jsonl'),
                carry=ref(root / 'CARRY.json'), train_complete=ref(path),
                counts={kind: sum(row['kind'] == kind for row in rows) for kind in ('NATIVE', 'PARENT')},
                pending_parent_claims_preserved=True, optimizer_used=False, no_replay=True)


def carry_events(payload):
    offset = 0
    names = []
    while offset < len(payload):
        watch, mask, cookie, size = struct.unpack_from('iIII', payload, offset)
        name = payload[offset + 16:offset + 16 + size].split(b'\0')[0]
        if mask & 0x80 and name == b'CARRY.json':
            names.append(name)
        offset += 16 + size
    return names


def release_at_boundary(plan):
    require(MORNING <= time.time() < BOUNDARY_END, 'no_early_signal')
    expected = plan['predecessor']
    require(same_process(expected), 'custody_changed_no_signals')
    root, output = event_paths(plan['branch'])
    library = ctypes.CDLL(None, use_errno=True)
    watcher = library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    require(watcher >= 0, 'inotify_available')
    descriptor = os.pidfd_open(expected['pid'])
    stopped = False
    released = False
    try:
        require(library.inotify_add_watch(watcher, os.fsencode(root), 0x80) >= 0, 'carry_watch')
        while time.time() < BOUNDARY_END:
            require(same_process(expected), 'custody_changed_no_signals')
            if not select.select([watcher], [], [], min(1, max(0, BOUNDARY_END-time.time())))[0]:
                continue
            if not carry_events(os.read(watcher, 65536)):
                continue
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            try:
                for unused in range(100):
                    state = (Path('/proc') / str(expected['pid']) / 'stat').read_text().rpartition(') ')[2].split()[0]
                    if state in ('T', 't'):
                        break
                    time.sleep(.001)
                require(state in ('T', 't'), 'actor_stopped_before_snapshot')
                require(same_process(expected), 'same_identity_while_stopped')
                try:
                    snapshot = completed_boundary(root)
                except ValueError:
                    continue
                snapshot.update(status='RELEASE_AUTHORIZED_AT_DURABLE_CYCLE', identity=expected,
                                observed_unix=time.time(), event=EVENT)
                write(output / 'BOUNDARY.json', snapshot)
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                stopped = False
                require(bool(select.select([descriptor], [], [], 30)[0]), 'owned_actor_exit_observed')
                released = True
                write(output / 'RELEASED.json', dict(status='RELEASED', predecessor=expected,
                    boundary=ref(output / 'BOUNDARY.json'), observed_unix=time.time(), foreign_signals=0))
                return snapshot
            finally:
                if stopped:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    stopped = False
        raise ValueError('NO_COMPLETED_CYCLE_BY_BOUNDARY_DEADLINE_NO_CAPTURE')
    finally:
        if stopped and not released:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)
        os.close(watcher)


def no_attempt(output):
    return not any((output / name).exists() for name in ('EVAL_CLAIM.json', 'EVAL_LEDGER.json', 'EVAL_COMPLETE.json'))


def fresh_scan(plan, prefix):
    prior, grid, config, checkpoint = validate(plan)
    folder = Path(plan['output'])
    for ordinal in range(8):
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                   'python3', '-B', __file__, 'scan', '--plan', str(folder / 'PLAN.json'),
                   '--plan-sha256', sha(folder / 'PLAN.json')]
        report = json.loads(subprocess.check_output(command, text=True, timeout=100))
        write(folder / f'{prefix}_ADMISSION_{ordinal}.json', report)
        if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
            return ref(folder / f'{prefix}_ADMISSION_{ordinal}.json')
        time.sleep(.25)
    raise ValueError('fresh_full_privileged_admission_not_clear')


def launch(plan, mode, deadline, admission):
    prior, grid, config, checkpoint = validate(plan)
    require(time.time() < deadline - 5, 'native_deadline')
    output = Path(plan['output'])
    report = read(admission['path'])
    require(sha(admission['path']) == admission['sha256'] and report['clear']
            and report['scanner_euid'] == 0 and not report['blocking_reasons'], 'phase_fresh_admission')
    authorization = output / (mode.upper() + '_AUTHORIZATION.json')
    write(authorization, dict(mode=mode, plan=ref(output / 'PLAN.json'),
        release=ref(output / 'RELEASED.json'), admission=admission,
        timer_identity=process(os.getpid()), issued_unix=time.time(), deadline_unix=deadline))
    command = ['timeout', '--signal=TERM', '--kill-after=3s', str(max(1, int(deadline-time.time()-4)))+'s',
        grid.PYTHON, '-B', str(Path(__file__).with_name('orch_r119_grid_final_native.py')),
        mode, '--plan', str(output / 'PLAN.json'), '--plan-sha256', sha(output / 'PLAN.json')]
    with (output / (mode.upper() + '.log')).open('x') as log:
        child = subprocess.Popen(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=config['uuid'],
            PYTHONPATH=str(prior.OLD), PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
            TRANSFORMERS_OFFLINE='1', ORCH_GRID_FINAL_PHASE_AUTHORIZATION_SHA256=sha(authorization)), stdin=subprocess.DEVNULL, stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True)
    write(output / (mode.upper() + '_LAUNCH.json'), dict(pid=child.pid, command=command,
                                                       started_unix=time.time()))
    return child


def timer(plan):
    validate(plan)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_timer_only')
    require(time.time() < MORNING and same_process(plan['predecessor']), 'live_custody_before_arming')
    output = Path(plan['output'])
    (output / 'TIMER_ONCE').mkdir()
    write(output / 'ARMED.json', dict(timer_identity=process(os.getpid()), plan=ref(output / 'PLAN.json'),
        trigger_unix=MORNING, boundary_end_unix=BOUNDARY_END, evaluation_end_unix=EVAL_END,
        train_end_unix=TRAIN_END, lease_wall_unix=HARD_END, native_calls=0, signals_sent=0,
        capture_armed_condition='ACTUAL_COMPLETED_CYCLE_RELEASE_AND_FRESH_ADMISSION',
        timer_not_capture=True, observed_unix=time.time()))
    while time.time() < MORNING:
        time.sleep(min(5, MORNING - time.time()))
    write(output / 'TRIGGERED.json', dict(trigger_unix=time.time(), native_calls=0))
    try:
        validate(plan)
        require(no_attempt(output), 'new_event_already_attempted_no_retry')
        release_at_boundary(plan)
    except BaseException as error:
        write(output / 'EVAL_DISPOSITION.json', dict(status='NOT_RUN', reason=str(error), native_calls=0,
                                                  observed_unix=time.time(), no_retry=True))
        return
    try:
        admission = fresh_scan(plan, 'EVAL')
        child = launch(plan, 'evaluate', EVAL_END, admission)
        code = child.wait()
        write(output / 'EVAL_EXIT.json', dict(exit_code=code, observed_unix=time.time(), no_retry=True))
    except BaseException as error:
        write(output / 'EVAL_ERROR.json', dict(error=str(error), no_retry=True, observed_unix=time.time()))
    try:
        admission = fresh_scan(plan, 'RESUME')
        child = launch(plan, 'resume', HARD_END, admission)
        code = child.wait()
        write(output / 'LIFE_TERMINAL.json', dict(status='COMPLETE' if code == 0 else 'FAILED',
            exit_code=code, observed_unix=time.time(), no_reset=True, no_auto_retry=True))
    except BaseException as error:
        write(output / 'LIFE_TERMINAL.json', dict(status='FAILED', reason=str(error),
                                               observed_unix=time.time(), no_auto_retry=True))
    write(output / 'LEASE_CUSTODY.json', dict(observed_unix=time.time(), train_end_unix=TRAIN_END,
        lease_wall_unix=HARD_END, extra_final_calls=0, sealed_capture_never_retried=True))


def wall(plan):
    validate(plan)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and time.time() < MORNING,
            'CPU_wall_timer_armed_before_morning')
    output = Path(plan['output'])
    (output / 'WALL_ONCE').mkdir()
    write(output / 'WALL_ARMED.json', dict(timer_identity=process(os.getpid()),
        plan=ref(output / 'PLAN.json'), train_end_unix=TRAIN_END, hard_end_unix=HARD_END,
        native_calls=0, lease_wall_capture_quota=0, observed_unix=time.time()))
    while time.time() < TRAIN_END:
        time.sleep(min(5, TRAIN_END-time.time()))
    write(output / 'TRAIN_WINDOW_CLOSED.json', dict(observed_unix=time.time(), extra_final_calls=0))
    while time.time() < HARD_END:
        time.sleep(min(1, HARD_END-time.time()))
    identities = [plan['predecessor']]
    if (output / 'RESUMED.json').exists():
        identities.append(read(output / 'RESUMED.json')['identity'])
    signals = []
    for expected in identities:
        if same_process(expected):
            descriptor = os.pidfd_open(expected['pid'])
            try:
                require(same_process(expected), 'exact_actor_at_lease_wall')
                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
                signals.append(expected)
            finally:
                os.close(descriptor)
    write(output / 'WALL_DISPOSITION.json', dict(observed_unix=time.time(), hard_end_unix=HARD_END,
        exact_owned_wall_signals=signals, extra_final_calls=0, no_retry=True,
        capture_disposition='NO_ADDITIONAL_CAPTURE_AT_LEASE_WALL'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'validate', 'timer', 'wall', 'scan'))
    parser.add_argument('--branch', choices=tuple(BRANCHES))
    parser.add_argument('--plan')
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    if args.mode == 'prepare':
        print(json.dumps(prepare(args.branch)))
        return
    require(sha(args.plan) == args.plan_sha256, 'exact_plan')
    plan = read(args.plan)
    if args.mode == 'timer':
        timer(plan)
    elif args.mode == 'wall':
        wall(plan)
    elif args.mode == 'scan':
        require(os.geteuid() == 0, 'privileged_scanner')
        validate(plan)
        print(json.dumps(original().scan(plan['branch'])))
    else:
        validate(plan)
        print(json.dumps(dict(status='CPU_VALIDATED', native_calls=0)))


if __name__ == '__main__':
    main()
