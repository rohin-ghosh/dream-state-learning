"""Deadline-only retirement of the exact grid repair processes, never F1."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import time


DRAIN = 1789491300
LATEST = 1789491420
REPAIR = '/localhome/local-rohing/orch_r118_grid_shared_repair_20260915_v1/orch_r118_grid_shared_repair.py'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def identity(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, uid=directory.stat().st_uid, start_ticks=fields[19],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), ppid=int(fields[1]), state=fields[0])


def same_process(observed, expected):
    return all(str(observed[key]) == str(expected[key]) for key in ('pid', 'uid', 'start_ticks', 'boot_id'))


def inspect_owned(pid, plan):
    observed = identity(pid)
    require(observed['uid'] == os.getuid(), 'only_same_user_process')
    directory = Path('/proc') / str(pid)
    command = [part.decode() for part in (directory / 'cmdline').read_bytes().split(b'\0') if part]
    require(command.count('--root') == 1 and command[command.index('--root') + 1] == plan['branch_root'],
            'exact_owned_branch_command')
    require(str((directory / 'cwd').resolve(strict=True)) == plan['runtime'], 'exact_frozen_runtime_cwd')
    known = (REPAIR in command and any(phase in command for phase in ('guard', 'resident'))) or (
        'gpu.orch_r118_grid_shared_run' in command and 'readout' in command)
    require(known, 'only_original_repair_or_its_readout')
    environment = (directory / 'environ').read_bytes().split(b'\0')
    cvd = [item.removeprefix(b'CUDA_VISIBLE_DEVICES=').decode()
           for item in environment if item.startswith(b'CUDA_VISIBLE_DEVICES=')]
    require(cvd == ([''] if 'guard' in command else [plan['uuid']]), 'assigned_device_or_CPU_guard_only')
    observed.update(command_sha256=hashlib.sha256((directory / 'cmdline').read_bytes()).hexdigest(),
        cwd=plan['runtime'], cvd=cvd[0])
    return observed


def discover(plan):
    seeds = []
    for expected in plan['predecessor_processes']:
        try:
            observed = identity(expected['pid'])
        except FileNotFoundError:
            continue
        if not same_process(observed, expected) or observed['state'] == 'Z':
            continue
        seeds.append(expected['pid'])
    links = {}
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            observed = identity(int(directory.name))
        except FileNotFoundError:
            continue
        links[observed['pid']] = observed
    selected = set(seeds)
    while True:
        extra = {pid for pid, item in links.items() if item['ppid'] in selected and item['state'] != 'Z'} - selected
        if not extra:
            break
        selected.update(extra)
    require(len(selected) <= 6, 'bounded_own_guard_timeout_actor_readout_tree')
    return [inspect_owned(pid, plan) for pid in sorted(selected)]


def exited(descriptor):
    return bool(select.select([descriptor], [], [], 0)[0])


def send(descriptor, expected, signum):
    if exited(descriptor):
        return False
    observed = identity(expected['pid'])
    require(same_process(observed, expected), 'pidfd_exact_identity')
    actual = hashlib.sha256((Path('/proc') / str(expected['pid']) / 'cmdline').read_bytes()).hexdigest()
    require(actual == expected['command_sha256'], 'no_command_exec_drift_before_signal')
    signal.pidfd_send_signal(descriptor, signum)
    return True


def stop(plan, output, writer, clock=time.time):
    require(DRAIN <= clock() < LATEST, 'original_1655_deadline_only_no_early_stop')
    records = discover(plan)
    writer(output / 'PINNED.json', dict(processes=records, pinned_unix=clock(), no_outcome_selection=True))
    handles = []
    stopped = set()
    signals = []
    try:
        for record in records:
            descriptor = os.pidfd_open(record['pid'])
            try:
                require(same_process(identity(record['pid']), record), 'same_process_after_pidfd_open')
            except BaseException:
                os.close(descriptor)
                raise
            handles.append((descriptor, record))
        for descriptor, record in handles:
            if send(descriptor, record, signal.SIGSTOP):
                stopped.add(descriptor)
                signals.append(dict(pid=record['pid'], signal='SIGSTOP', unix=clock()))
        until = time.monotonic() + 5
        while any(not exited(descriptor) and identity(record['pid'])['state'] not in ('T', 't', 'Z')
                  for descriptor, record in handles):
            require(time.monotonic() < until, 'bounded_process_stop')
            time.sleep(.01)
        after = discover(plan)
        require({item['pid'] for item in after}.issubset({item['pid'] for item in records}),
                'late_child_preserve_no_unbound_signal')
        root = Path(plan['branch_root'])
        preserved = {}
        for name in ('CONFIG.json', 'LEDGER.jsonl', 'CARRY.json', 'shared_repair_v1/LOADED.json'):
            path = root / name
            preserved[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        writer(output / 'BEFORE_SIGNALS.json', dict(processes=records, preserved_files=preserved,
            partial_calls_preserved=True, fake_cycle_complete=False, optimizer_owner='F1_NOT_SIGNALLED',
            observed_unix=clock()))
        for descriptor, record in reversed(handles):
            if send(descriptor, record, signal.SIGTERM):
                signals.append(dict(pid=record['pid'], signal='SIGTERM', unix=clock()))
            if not exited(descriptor):
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            stopped.discard(descriptor)
        grace = time.monotonic() + 20
        while time.monotonic() < grace and any(not exited(descriptor) for descriptor, unused in handles):
            time.sleep(.05)
        for descriptor, record in handles:
            if send(descriptor, record, signal.SIGKILL):
                signals.append(dict(pid=record['pid'], signal='SIGKILL_AFTER_GRACE', unix=clock()))
        until = time.monotonic() + 5
        while time.monotonic() < until and any(not exited(descriptor) for descriptor, unused in handles):
            time.sleep(.05)
        require(all(exited(descriptor) for descriptor, unused in handles) and not discover(plan), 'all_own_processes_exited')
        receipt = dict(status='RELEASED', processes=records, signals=signals, preserved_files=preserved,
            released_unix=clock(), native_raw_preserved=True, no_fake_terminal=True,
            fresh_full_scanner_required=True, old_bounds_unchanged=True)
        writer(output / 'RELEASE.json', receipt)
        return receipt
    finally:
        for descriptor, unused in handles:
            if descriptor in stopped and not exited(descriptor):
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == args.source_sha256, 'immutable_drain_source')
    require(hashlib.sha256(args.plan.read_bytes()).hexdigest() == args.plan_sha256, 'immutable_eval_plan')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_drain_only')
    plan = json.loads(args.plan.read_bytes())
    require(plan['branch'] in ('F4', 'A4') and plan['max_training_calls'] == 0, 'exact_grid_eval_scope')
    evaluator = plan['source']
    require(hashlib.sha256(Path(evaluator['path']).read_bytes()).hexdigest() == evaluator['sha256'], 'frozen_evaluator')
    spec = importlib.util.spec_from_file_location('grid_final', evaluator['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate_plan(plan)
    output = Path(plan['output']) / 'drain'
    output.mkdir(mode=0o700)
    module.write(output / 'ARMED.json', dict(pid=os.getpid(), source=module.ref(__file__),
        plan=module.ref(args.plan), stop_not_before_unix=DRAIN, latest_unix=LATEST, signals_sent=0,
        initial_processes=discover(plan), created_unix=time.time()))
    while time.time() < DRAIN:
        time.sleep(max(0, min(5, DRAIN - time.time())))
    module.validate_plan(plan)
    stop(plan, output, module.write)


if __name__ == '__main__':
    main()
