"""Prospective F4-only longer parent wait at a complete resident-cycle boundary."""

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_r115_grid_native as original
from gpu import orch_r111_grid_release as identity_source
from gpu import orch_r111_route_admission as admission


ROOT = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915/F4')
ERA = ROOT / 'R118_WAIT600_V1'
SOURCE = Path(__file__).resolve().parents[1]
WAIT = 600
require = original.require


def queue_request(identifier, life_id, cycle, episode, phase, task, events, corpus_sha256, now):
    require(life_id == 'F4_FABLE', 'F4_only_no_Astra_wait_change')
    request = original.policy.queue_request(identifier, life_id, cycle, episode, phase,
        task, events, corpus_sha256, now)
    require(request['lane_deadline_unix'] == now + 120, 'exact_original_wait')
    return dict(request, lane_deadline_unix=min(now + WAIT, original.END - 5))


class WaitLife(original.Life):
    ask = FunctionType(original.Life.ask.__code__, dict(original.Life.ask.__globals__,
        policy=SimpleNamespace(**dict(original.policy.__dict__, queue_request=queue_request))),
        'ask', original.Life.ask.__defaults__)


def boundary(root, complete):
    require(root == ROOT and complete.parent.parent == root / 'cycles' and
            complete.name == 'CYCLE_COMPLETE.json', 'exact_F4_cycle_boundary')
    document = original.read(complete)
    cycle = document['cycle']
    rows = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line.strip()]
    if any(row['cycle'] > cycle or row['reserved_unix'] > document['finished_unix'] for row in rows):
        return None
    for row in rows:
        if row['kind'] == 'NATIVE':
            folder = 'sealed_readout_calls' if row['split'] == 'FINAL' else (
                'readout_calls' if row.get('attached_readout') or row['split'] != 'TRAIN' else 'calls')
            path = root / folder / f'N{row["number"]:05d}.json'
            if not path.exists() or original.read(path)['status'] != 'COMPLETE':
                return None
        elif not (root / 'parent_claude' / f'P{row["number"]:04d}.claim' / 'PUBLISHED.json').exists():
            return None
    require((root / 'CARRY.json').is_file(), 'saved_context_carry_required')
    return dict(completed_cycle=cycle, next_cycle=cycle + 1, complete=original.ref(complete),
        ledger=original.ref(root / 'LEDGER.jsonl'), carry=original.ref(root / 'CARRY.json'),
        native_charged=sum(row['kind'] == 'NATIVE' for row in rows),
        parent_charged=sum(row['kind'] == 'PARENT' for row in rows),
        old_calls_retried=0, optimizer_steps=0, observed_unix=time.time())


def resident():
    config = original.validate(ROOT, gpu=True)
    require(config['life_id'] == 'F4_FABLE' and config['physical'] == 3, 'exact_F4_allocation')
    checkpoint = original.read(ERA / 'BOUNDARY.json')
    require(checkpoint['ledger'] == original.ref(ROOT / 'LEDGER.jsonl') and
            checkpoint['carry'] == original.ref(ROOT / 'CARRY.json'), 'same_charge_and_context_boundary')
    source = inspect.getsource(original.resident)
    before = source[source.index('    config = validate'):source.index('    while time.time() < TRAIN_END:')]
    after = ("    config = validate(root, gpu=True)\n"
        "    checkpoint = read(ERA / 'BOUNDARY.json')\n"
        "    cycle = checkpoint['next_cycle']\n"
        "    engine = load_engine(config)\n"
        "    write(ERA / 'LOADED.json', dict(pid=os.getpid(), loaded_unix=time.time(), "
        "base_sha256=engine.loaded_base_sha256, no_adapter=engine.no_adapter, next_cycle=cycle))\n")
    require(before.count('spawn_readout(root, 0,') == 2, 'no_repeated_baseline_readouts')
    namespace = dict(original.resident.__globals__, Life=WaitLife, ERA=ERA)
    exec(compile(source.replace(before, after, 1), __file__ + ':same_resident_successor', 'exec'), namespace)
    namespace['resident'](ROOT)


def scan():
    if os.geteuid() != 0:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(SOURCE), 'python3', '-B', '-m', 'gpu.orch_r118_f4_wait600', 'scan']
        return json.loads(subprocess.check_output(command, text=True, timeout=100))
    config = original.validate(ROOT)
    original.admission.minor.pinned.policy = SimpleNamespace(DEVICES={3: config['uuid']},
        HOST_SHA=original.HOST_SHA, require=require,
        allocation=lambda index: require(index == 3, 'only_owned_F4'))
    return admission.scan(3, ROOT / 'SERVICE_IDENTITY.json')


def guard():
    config = original.validate(ROOT)
    require((ERA / 'BOUNDARY.json').exists(), 'safe_retirement_required')
    (ERA / 'GUARD_ONCE').mkdir()
    try:
        for attempt in range(90):
            report = scan()
            original.write(ERA / f'ADMISSION_{attempt:03d}.json', report)
            if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
                break
            time.sleep(2)
        else:
            raise ValueError('no_admission_no_waiver')
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=config['uuid'], PYTHONPATH=str(SOURCE),
            PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        command = ['timeout', '--signal=TERM', '--kill-after=5s', str(int(original.END-time.time()-5))+'s',
            original.PYTHON, '-B', '-m', 'gpu.orch_r118_f4_wait600', 'resident']
        with (ERA / 'NATIVE.log').open('x') as stream:
            child = subprocess.Popen(command, cwd=SOURCE, env=environment, stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        original.write(ERA / 'LAUNCH.json', dict(pid=child.pid, started_unix=time.time(), command=command))
        code = child.wait()
        original.write(ROOT / 'TERMINAL.json', dict(status='COMPLETE' if code == 0 else 'FAILED',
            exit_code=code, finished_unix=time.time(), era='R118_F4_WAIT600'))
    except BaseException as error:
        original.write(ERA / 'FAILED.json', dict(error_type=type(error).__name__, error=str(error),
            finished_unix=time.time(), no_retry=True))
        raise
    finally:
        original.write(ERA / 'FINAL_RELEASE.json', scan())


def migrate():
    config = original.validate(ROOT)
    require(config['physical'] == 3 and config['life_id'] == 'F4_FABLE', 'only_F4')
    require(original.read(ERA / 'CPU_READY.json')['passed'], 'own_frozen_CPU_provenance')
    native_pid = original.read(ROOT / 'RESIDENT_STARTED.json')['pid']
    require(native_pid == 374237, 'exact_original_F4_native')
    guard_pid = 374023
    processes = {pid: Path('/proc') / str(pid) for pid in (native_pid, guard_pid)}
    identities = {pid: identity_source.identity(path) for pid, path in processes.items()}
    for pid, directory in processes.items():
        expected_cwd = (Path('/localhome/local-rohing/orch_r115_grid_source_20260915_v1')
            if pid == native_pid else Path('/localhome/local-rohing'))
        require(identities[pid]['uid'] == os.getuid() and
                (directory / 'cwd').resolve() == expected_cwd,
                'exact_own_original_source')
        arguments = (directory / 'cmdline').read_bytes().split(b'\0')
        expected = ([b'-m', b'gpu.orch_r115_grid_native', b'resident', b'--root', str(ROOT).encode()]
            if pid == native_pid else
            [b'/localhome/local-rohing/orch_r115_grid_pair_20260915/launch_r116/orch_r116_grid_launch.py',
             b'guard', b'--root', str(ROOT).encode()])
        require(arguments[-len(expected)-1:-1] == expected, 'exact_old_native_and_guard_commands')
    require(('CUDA_VISIBLE_DEVICES=' + config['uuid']).encode() in
            (processes[native_pid] / 'environ').read_bytes().split(b'\0'), 'exact_native_UUID')
    descriptors = {pid: os.pidfd_open(pid) for pid in processes}
    stopped = set()
    seen = set(ROOT.glob('cycles/*/CYCLE_COMPLETE.json'))
    try:
        while time.time() < original.TRAIN_END:
            fresh = set(ROOT.glob('cycles/*/CYCLE_COMPLETE.json')) - seen
            if not fresh:
                time.sleep(.001)
                continue
            seen.update(fresh)
            for pid in (native_pid, guard_pid):
                require(identity_source.identity(processes[pid]) == identities[pid], 'same_process_identity')
                signal.pidfd_send_signal(descriptors[pid], signal.SIGSTOP)
                stopped.add(pid)
            time.sleep(.01)
            checkpoint = boundary(ROOT, max(fresh, key=lambda path: path.parent.name))
            if checkpoint is None:
                for pid in tuple(stopped):
                    signal.pidfd_send_signal(descriptors[pid], signal.SIGCONT)
                    stopped.remove(pid)
                continue
            checkpoint.update(era='R118_F4_WAIT600', wait_seconds=600, provider_cutoff_reserve_seconds=30,
                effort_unchanged='max', head_effort_unchanged='max', original_identities=identities,
                source=original.ref(Path(__file__)), bound_config=original.ref(ROOT / 'CONFIG.json'),
                interpretation='prospective_F4_transport_era_not_matched_A4_wait_control')
            original.write(ERA / 'BOUNDARY.json', checkpoint)
            for pid in (guard_pid, native_pid):
                signal.pidfd_send_signal(descriptors[pid], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[pid], signal.SIGCONT)
                stopped.remove(pid)
                poller = select.poll(); poller.register(descriptors[pid], select.POLLIN)
                require(bool(poller.poll(30000)), 'own_process_exit_before_successor')
            require(not (ROOT / 'TERMINAL.json').exists(), 'no_legacy_terminal_breaking_live_broker')
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1')
            with (ERA / 'GUARD.log').open('x') as log:
                child = subprocess.Popen([original.PYTHON, '-B', '-m', 'gpu.orch_r118_f4_wait600', 'guard'],
                    cwd=SOURCE, env=environment, stdin=subprocess.DEVNULL, stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True)
            original.write(ERA / 'GUARD_PID.json', dict(pid=child.pid, started_unix=time.time()))
            return
        original.write(ERA / 'NO_BOUNDARY.json', dict(native_unchanged=True, observed_unix=time.time()))
    finally:
        for pid in stopped:
            signal.pidfd_send_signal(descriptors[pid], signal.SIGCONT)
        for descriptor in descriptors.values():
            os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('scan', 'migrate', 'guard', 'resident'))
    args = parser.parse_args()
    if args.mode == 'scan':
        print(json.dumps(scan(), sort_keys=True))
    else:
        {'migrate': migrate, 'guard': guard, 'resident': resident}[args.mode]()
