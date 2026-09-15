"""Inactive F4/A4 executable successor; F1 alone owns shared optimization.

Main first collects all eight READY files, retires each predecessor at a complete
cycle boundary, runs ``boundary``, and writes SHARED_ACTIVATION.json. Only then
may Main run ``guard``. This module never initializes the common learner, stops a
predecessor, creates an optimizer, or changes the existing CONFIG/LEDGER/CARRY.
TRAIN alone updates CARRY through the unchanged grid train_cycle implementation.
"""

import argparse
from copy import deepcopy
import fcntl
import gc
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
import time

from gpu import orch_r116_grid_shared_client as client
from gpu import orch_r118_f4_wait600 as wait600
from gpu import orch_r111_route_admission as admission


grid = client.grid
shared = client.shared
require = shared.require
MODULE = 'gpu.orch_r118_grid_shared_run'
SOURCE = Path(__file__).resolve().parents[1]
COMMON_ROOT = '/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1'


def branch_for(config):
    branch = {3: 'F4', 7: 'A4'}.get(config['physical'])
    require(branch is not None and config['life_id'] == {'F4': 'F4_FABLE', 'A4': 'F4_ASTRA'}[branch],
            'exact_grid_pair_only')
    return branch


def inherited_bounds(config):
    require(config['hard_end_unix'] == grid.END and config['train_end_unix'] == grid.TRAIN_END,
            'original_absolute_deadlines')
    return dict(hard_end_unix=grid.END, train_end_unix=grid.TRAIN_END,
                final_unix=grid.policy.FINAL_UNIX, max_native_calls=grid.MAX_NATIVE,
                max_parent_calls=grid.MAX_PARENT, physical=config['physical'],
                parent_wait_seconds=600 if branch_for(config) == 'F4' else 120)


def check_deadline(label):
    require(time.time() < grid.END - 2, 'original_grid_hard_end:' + label)


def read_ledger(root):
    path = root / 'LEDGER.jsonl'
    require(path.is_file(), 'existing_life_ledger_required')
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def capture_boundary(root, complete_path):
    root, complete_path = Path(root).resolve(strict=True), Path(complete_path).resolve(strict=True)
    require(complete_path.parent.parent == root / 'cycles' and complete_path.name == 'CYCLE_COMPLETE.json',
            'exact_completed_grid_cycle')
    complete = shared.read(complete_path)
    cycle = complete['cycle']
    require(type(cycle) is int and cycle >= 1 and complete_path.parent.name == f'{cycle:04d}', 'cycle_identity')
    ledger_ref, carry_ref = grid.ref(root / 'LEDGER.jsonl'), grid.ref(root / 'CARRY.json')
    rows = read_ledger(root)
    require(all(row['cycle'] <= cycle and row['reserved_unix'] <= complete['finished_unix'] for row in rows),
            'no_next_cycle_or_inflight_reservation')
    captures = {}
    for kind in ('NATIVE', 'PARENT'):
        numbers = [row['number'] for row in rows if row['kind'] == kind]
        require(numbers == list(range(1, len(numbers) + 1)), 'preserve_contiguous_charged_cursors')
    for row in rows:
        require(row['kind'] in ('NATIVE', 'PARENT'), 'known_ledger_charge')
        if row['kind'] == 'NATIVE':
            folder = 'sealed_readout_calls' if row['split'] == 'FINAL' else (
                'readout_calls' if row.get('attached_readout') or row['split'] != 'TRAIN' else 'calls')
            path = root / folder / f'N{row["number"]:05d}.json'
            document = shared.read(path)
            require(document['status'] == 'COMPLETE' and all(document[name] == row[name]
                    for name in ('number', 'cycle', 'task_id', 'split', 'purpose')), 'completed_native_capture_binding')
        else:
            path = root / 'parent_received' / f'P{row["number"]:04d}.json'
            document = shared.read(path)
            require(document.get('disposition') is not None, 'completed_parent_disposition_required')
        captures[str(path.relative_to(root))] = shared.sha(path)
    train_path = complete_path.parent / 'TRAIN_COMPLETE.json'
    train = shared.read(train_path)
    require(len(train['outcomes']) == 2 and len({item['task_id'] for item in train['outcomes']}) == 2
            and all(item['split'] == 'TRAIN' for item in train['outcomes']), 'complete_two_episode_boundary')
    require(shared.read(root / 'CARRY.json') == train['carry'], 'same_completed_cycle_carry')
    require(grid.ref(root / 'LEDGER.jsonl') == ledger_ref and grid.ref(root / 'CARRY.json') == carry_ref,
            'boundary_changed_during_snapshot')
    return dict(schema='R118_GRID_SHARED_BOUNDARY_V1', root=str(root), completed_cycle=cycle,
                next_cycle=cycle + 1, complete=grid.ref(complete_path), train_complete=grid.ref(train_path),
                ledger=ledger_ref, carry=carry_ref, captures=captures,
                native_charged=sum(row['kind'] == 'NATIVE' for row in rows),
                parent_charged=sum(row['kind'] == 'PARENT' for row in rows), old_calls_retried=0)


def process_alive(identity):
    try:
        directory = Path('/proc') / str(identity['pid'])
        fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
        return (fields[0] != 'Z' and fields[19] == str(identity['start_ticks'])
                and directory.stat().st_uid == identity['uid']
                and Path('/proc/sys/kernel/random/boot_id').read_text().strip() == identity['boot_id'])
    except FileNotFoundError:
        return False


def validate(root, *, gpu=False, initial_boundary=False):
    from gpu import orch_r118_grid_shared_ready as ready

    root = Path(root).resolve(strict=True)
    config = shared.read(root / 'CONFIG.json')
    branch = branch_for(config)
    require(config['root'] == str(root), 'original_root_binding')
    require(grid.admission.minor.pinned.host_identity() == grid.HOST_SHA, 'exact_node5_hashed_identity')
    require(config['uuid'] == grid.policy.LANES[config['life_id']]['uuid'], 'original_physical_uuid')
    require(config['base_sha256'] == grid.policy.game.BASE_SHA, 'original_frozen_base')
    check_deadline('shared_successor')
    require(grid.END <= grid.LEASE_END - 21600, 'original_lease_margin')
    for name, expected in config['inputs'].items():
        require(shared.sha(root / name) == expected, 'original_input_unchanged:' + name)
    publication = shared.read(root / 'SHARED_CLIENT_READY.json')
    require(publication['schema'] == 'R116_SHARED_CLIENT_READY_V1' and publication['branch'] == branch
            and publication['root'] == str(root) and publication['successor_source'] == str(SOURCE), 'exact_ready_source_root')
    ready.verify_closure(SOURCE, shared.read(publication['tests_receipt']['path']))
    require(shared.sha(publication['tests_receipt']['path']) == publication['tests_receipt']['sha256'], 'tested_receipt_unchanged')
    activation = shared.read(root / 'SHARED_ACTIVATION.json')
    require(activation['schema'] == 'R118_GRID_SHARED_ACTIVATION_V1'
            and activation['all_eight_ready_and_safe'] is True, 'Main_all_eight_safe_activation_required')
    require(activation['ready_sha256'] == shared.sha(root / 'SHARED_CLIENT_READY.json')
            and activation['predecessor_plan_sha256'] == shared.sha(root / 'CONFIG.json')
            and activation['inherited_bounds'] == publication['inherited_bounds'] == inherited_bounds(config),
            'no_original_plan_or_budget_reset')
    link = activation['shared_learner']
    require(link['branch'] == branch and link['root'] == publication['common_root'] == COMMON_ROOT, 'common_branch_binding')
    require(shared.sha(link['adoption_path']) == link['adoption_sha256'], 'Main_adoption_receipt_binding')
    if gpu:
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['uuid'], 'initial_GPU_UUID')
        require(('CUDA_VISIBLE_DEVICES=' + config['uuid']).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'),
                'initial_process_visibility')
    boundary_path = Path(activation['boundary']['path']).resolve(strict=True)
    require(boundary_path.is_relative_to(root / 'shared_boundaries')
            and shared.sha(boundary_path) == activation['boundary']['sha256'], 'owned_exact_boundary_receipt')
    boundary = shared.read(boundary_path)
    if initial_boundary:
        require(len(activation['predecessor_identities']) >= 2 and
                all(not process_alive(identity) for identity in activation['predecessor_identities']),
                'predecessor_native_and_guard_must_exit_no_signals_here')
        require(boundary == capture_boundary(root, boundary['complete']['path']), 'preserve_all_charges_carry_and_cursor')
    return config, activation, boundary


class F4SharedLife(client.SharedLife):
    ask = wait600.WaitLife.ask


class ReadoutLife(client.SharedLife):
    def ask(self, *args, **kwargs):
        raise ValueError('fresh_readout_parent_absent')

    def calls(self, tasks, purpose, messages, cap, *, attached_readout=False):
        require(attached_readout and purpose not in client.TRAIN_PHASES, 'held_and_open_readout_never_train')
        return super().calls(tasks, purpose, messages, cap, attached_readout=True)


def life_class(branch):
    require(branch in ('F4', 'A4'), 'grid_branch_only')
    return F4SharedLife if branch == 'F4' else client.SharedLife


def cycle_tasks(roster, cycle):
    require(len(roster) == 16 and type(cycle) is int and cycle >= 1, 'original_sixteen_task_cursor')
    tasks = [roster[(cycle - 1) % 8], roster[8 + (cycle - 1) % 8]]
    require(len({task['id'] for task in tasks}) == 2 and all(task['split'] == 'TRAIN' for task in tasks),
            'two_sequential_original_train_episodes')
    return tasks


def can_train(root):
    rows = read_ledger(root)
    return (sum(row['kind'] == 'NATIVE' for row in rows) <= grid.MAX_NATIVE - 120
            and sum(row['kind'] == 'PARENT' for row in rows) <= grid.MAX_PARENT - 6)


def spawn_readout(root, cycle, scope, session):
    require(scope in ('dev', 'final_morning'), 'no_repeated_baseline_readout')
    folder = root / 'shared_readout_bindings'
    binding_path = folder / f'{cycle:04d}_{scope}.json'
    shared.write(binding_path, dict(cycle=cycle, scope=scope, session=deepcopy(session),
        predecessor_processes=[list(client.native.process_identity())], parent_calls=0, carry_access=False))
    with (folder / f'{cycle:04d}_{scope}.log').open('x') as stream:
        result = subprocess.run([grid.PYTHON, '-B', '-m', MODULE, 'readout', '--root', str(root),
            '--binding', str(binding_path)], cwd=SOURCE, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT, timeout=max(1, grid.END - time.time() - 3))
    require(result.returncode == 0, 'fresh_shared_readout_failed_no_retry')


def readout(root, binding_path):
    config, activation, boundary = validate(root, gpu=True)
    binding_path = Path(binding_path).resolve(strict=True)
    require(binding_path.is_relative_to(root / 'shared_readout_bindings'), 'own_readout_binding')
    binding = shared.read(binding_path)
    cycle, scope, session = binding['cycle'], binding['scope'], binding['session']
    require(scope in ('dev', 'final_morning'), 'readout_scope')
    require(scope != 'final_morning' or time.time() >= grid.policy.FINAL_UNIX, 'morning_not_early')
    require(session['branch_root'] == str(root) and session['branch'] == branch_for(config)
            and session['shared_root'] == activation['shared_learner']['root']
            and session['config_sha256'] == activation['shared_learner']['config_sha256'], 'pinned_shared_readout')
    directory = root / 'readouts' / f'{cycle:04d}' / scope
    shared.write(directory / 'STARTED.json', dict(pid=os.getpid(), parent=False, carry_access=False,
        shared_child=client.call_binding(session), started_unix=time.time()))
    engine = client.load_shared(session, model_dir=config['model_dir'], gpu_uuid=config['uuid'],
        check=check_deadline, readout=True, predecessor_processes=tuple(tuple(item) for item in binding['predecessor_processes']))
    life = ReadoutLife(root, engine, config, cycle, session)
    tasks = shared.read(root / ('FINAL.json' if scope == 'final_morning' else 'DEV.json'))
    messages = [[dict(role='system', content=grid.policy.HELD_PROMPT), dict(role='user', content=json.dumps(
        grid.policy.public_observation(task, grid.policy.game.initial(task)), sort_keys=True))] for task in tasks]
    responses = life.calls(tasks, scope, messages, 2048, attached_readout=True)
    if scope == 'dev':
        chosen = [tasks[0], tasks[4]]
        focused = [messages[index] + [dict(role='user', content=grid.policy.FOCUSED_PROMPT)] for index in (0, 4)]
        life.calls(chosen, 'focused_DEV', focused, 2048, attached_readout=True)
        from gpu import astra_goal_quality_train as legacy_source
        legacy = shared.read(root / 'LEGACY_READOUT.json')
        require(len(legacy['old_bank']) == 16, 'same_sixteen_old_facts')
        facts = legacy['old_bank']
        cases = [next(case for case in legacy['held']['cases'] if case['kind'] == kind) for kind in ('true', 'fault')]
        legacy_tasks = [dict(id='OLD-' + item['event'], split='LEGACY') for item in facts]
        legacy_messages = [legacy_source.memory.memory_messages(item['event'], 0) for item in facts]
        for start in (0, 8):
            life.calls(legacy_tasks[start:start + 8], 'legacy_facts', legacy_messages[start:start + 8], 512, attached_readout=True)
        life.calls([dict(id='AUDIT-' + case['case_sha256'], split='LEGACY') for case in cases],
            'audit', [legacy_source.memory.audit._messages(case, False) for case in cases], 512, attached_readout=True)
        if cycle:
            history = shared.read(root / 'cycles' / f'{cycle:04d}' / 'TRAIN_COMPLETE.json')
            train = {task['id']: task for task in shared.read(root / 'TRAIN.json')}
            for ordinal, outcome in enumerate(history['outcomes']):
                grid.open_opportunity(life, train[outcome['task_id']], outcome['final_state'], ordinal,
                    parent=False, attached_readout=True)
    engine.verify_base()
    shared.write(directory / 'COMPLETE.json', dict(status='COMPLETE', scope=scope, cycle=cycle,
        response_refs=[item['reference'] for item in responses], parent_calls=0, fresh_process=True,
        carry_access=False, optimizer_steps=0, shared_child=client.call_binding(session),
        readout_open_excluded=True, finished_unix=time.time()))


def resident(root):
    config, activation, boundary = validate(root, gpu=True, initial_boundary=True)
    link = activation['shared_learner']
    session = client.prepare(link['root'], link['branch'], config_sha256=link['config_sha256'])
    engine = client.load_shared(session, model_dir=config['model_dir'], gpu_uuid=config['uuid'], check=check_deadline)
    shared.write(root / 'SHARED_LOADED.json', dict(pid=os.getpid(), process=client.native.process_identity(),
        next_cycle=boundary['next_cycle'], optimizer_owner='F1', local_optimizer_steps=0,
        session=client.call_binding(session), observed_unix=time.time()))
    roster = shared.read(root / 'TRAIN.json')
    cycle = boundary['next_cycle']
    last_completed = boundary['completed_cycle']
    life = None
    while time.time() < grid.TRAIN_END and can_train(root):
        check_deadline('shared_cycle')
        memory = shared.read(root / 'CARRY.json')
        life = life_class(session['branch'])(root, engine, config, cycle, session)
        try:
            submission = client.run_cycle_and_submit(life, cycle_tasks(roster, cycle), memory)
        except grid.TrainWindowClosed as error:
            shared.write(root / 'cycles' / f'{cycle:04d}' / 'CLOCK_BOUNDARY.json', dict(reason=str(error),
                partial_cycle=True, all_completed_calls_preserved=True, submitted=False, optimizer_steps=0))
            break
        shared.write(root / 'shared_cycles' / f'{cycle:04d}' / 'SUBMITTED.json', submission)
        next_session = client.wait_for_next(session, deadline=grid.policy.FINAL_UNIX, check=check_deadline)
        if next_session.get('status') == 'DEADLINE_WAITING_SHARED_CHECKPOINT':
            shared.write(root / 'SHARED_WAIT_DEADLINE.json', next_session)
            break
        reloaded = client.reload_shared(engine, session, next_session)
        session = next_session
        shared.write(root / 'shared_cycles' / f'{cycle:04d}' / 'RELOADED.json', reloaded)
        spawn_readout(root, cycle, 'dev', session)
        shared.write(root / 'cycles' / f'{cycle:04d}' / 'CYCLE_COMPLETE.json', dict(cycle=cycle,
            shared_generation=session['generation'], shared_checkpoint_sha256=session['checkpoint_sha256'],
            optimizer_owner='F1', local_optimizer_steps=0, optimizer_steps=0, finished_unix=time.time()))
        last_completed, cycle = cycle, cycle + 1
    engine.verify_base()
    torch = engine.torch
    del life, engine
    gc.collect()
    torch.cuda.empty_cache()
    while time.time() < grid.policy.FINAL_UNIX:
        time.sleep(min(5, grid.policy.FINAL_UNIX - time.time()))
    spawn_readout(root, last_completed, 'final_morning', session)
    shared.write(root / 'SHARED_COMPLETE.json', dict(completed_cycle=last_completed,
        shared_generation=session['generation'], local_optimizer_steps=0, original_counters_preserved=True,
        finished_unix=time.time()))


def scan(root):
    config, activation, boundary = validate(root)
    if os.geteuid() != 0:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(SOURCE) + ':' + str(SOURCE / 'gpu'), 'python3', '-B', '-m', MODULE, 'scan', '--root', str(root)]
        return json.loads(subprocess.check_output(command, text=True, timeout=100))
    grid.admission.minor.pinned.policy = SimpleNamespace(DEVICES={config['physical']: config['uuid']},
        HOST_SHA=grid.HOST_SHA, require=require,
        allocation=lambda index: require(index == config['physical'], 'only_activated_grid_slot'))
    return admission.scan(config['physical'], root / 'SERVICE_IDENTITY.json')


def guard(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard_only')
    config, activation, boundary = validate(root, initial_boundary=True)
    folder = root / 'shared_guard'
    folder.mkdir(exist_ok=True)
    with (folder / 'LOCK').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (folder / 'ONCE').mkdir()
        shared.write(folder / 'PRE_GPU.json', dict(ready=grid.ref(root / 'SHARED_CLIENT_READY.json'),
            activation=grid.ref(root / 'SHARED_ACTIVATION.json'), boundary=activation['boundary'],
            preserved_bounds=inherited_bounds(config), observed_unix=time.time(), optimizer_owner='F1'))
        try:
            for attempt in range(90):
                report = scan(root)
                shared.write(folder / 'admission' / f'{attempt:03d}.json', report)
                if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
                    break
                check_deadline('admission')
                time.sleep(2)
            else:
                raise ValueError('strict_owned_grid_admission_not_clear')
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=config['uuid'], PYTHONPATH=str(SOURCE) + ':' + str(SOURCE / 'gpu'),
                PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
            command = ['timeout', '--signal=TERM', '--kill-after=2s', str(max(1, int(grid.END - time.time() - 5))) + 's',
                grid.PYTHON, '-B', '-m', MODULE, 'resident', '--root', str(root)]
            with (folder / 'NATIVE.log').open('x') as stream:
                child = subprocess.Popen(command, cwd=SOURCE, env=environment, stdin=subprocess.DEVNULL,
                    stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            shared.write(folder / 'LAUNCH.json', dict(pid=child.pid, command=command, observed_unix=time.time()))
            code = child.wait()
            shared.write(root / 'SHARED_TERMINAL.json', dict(status='COMPLETE' if code == 0 else 'FAILED',
                exit_code=code, local_optimizer_steps=0, finished_unix=time.time()))
        except BaseException as error:
            if not (root / 'SHARED_TERMINAL.json').exists():
                shared.write(root / 'SHARED_TERMINAL.json', dict(status='FAILED', error_type=type(error).__name__,
                    error=str(error), local_optimizer_steps=0, finished_unix=time.time()))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('boundary', 'scan', 'guard', 'resident', 'readout'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--complete', type=Path)
    parser.add_argument('--binding', type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if args.mode == 'boundary':
        require(args.complete is not None, 'complete_cycle_path_required')
        snapshot = capture_boundary(root, args.complete)
        path = root / 'shared_boundaries' / f'C{snapshot["completed_cycle"]:04d}.json'
        shared.write(path, snapshot)
        print(json.dumps(grid.ref(path), sort_keys=True))
    elif args.mode == 'readout':
        require(args.binding is not None, 'pinned_readout_binding_required')
        readout(root, args.binding)
    elif args.mode == 'scan':
        print(json.dumps(scan(root), sort_keys=True))
    else:
        (guard if args.mode == 'guard' else resident)(root)


if __name__ == '__main__':
    main()
