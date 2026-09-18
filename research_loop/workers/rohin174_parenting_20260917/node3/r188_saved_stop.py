"""Stop the current native at a verified saved boundary before the existing wall."""

import argparse
import json
import os
from pathlib import Path
import select
import signal
import socket
import time

import r181_boundary as base
from r188_recovery import terminate


NOT_BEFORE = base.HARD_END - 240
QUIET_END = base.HARD_END - 30


def may_capture(now, record):
    return NOT_BEFORE <= now < QUIET_END and record['kind'] == 'SLEEP_COMPLETE'


def present_children(pid):
    children = (Path('/proc') / str(pid) / 'task' / str(pid) / 'children').read_text().split()
    live = []
    for child in children:
        try:
            fields = (Path('/proc') / child / 'stat').read_text().rsplit(') ', 1)[1].split()
            if fields[0] not in ('Z', 'X'):
                live.append(int(child))
        except FileNotFoundError:
            pass
    return live


def run(physical):
    source = base.HERE / ('r188' if physical in (1, 2) else 'r181') / ('physical' + str(physical))
    folder = base.HERE / 'r188' / 'saved_stop' / ('physical' + str(physical))
    folder.mkdir(parents=True, exist_ok=False)
    spec = base.read(source / 'LIVE_HANDOFF.json')
    plan = base.read(source / 'PLAN.json')
    base.require(plan['hard_end_unix'] == base.HARD_END, 'unchanged_operational_wall')
    candidates = []
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            argv = (proc / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
        except FileNotFoundError:
            continue
        if argv[:5] == [base.PYTHON, '-B', '-m', 'gpu.orch_r125_continual_guard', 'native'] \
                and str(source / 'GUARD.json') in argv:
            candidates.append(base.identity(int(proc.name)))
    base.require(len(candidates) == 1, 'one_actual_current_native')
    actor = candidates[0]
    timer = base.identity(actor['parent'])
    supervisor = base.identity(timer['parent'])
    actors = [actor, timer, supervisor]
    base.require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s'] and
        actor['cgroup'] == timer['cgroup'] == supervisor['cgroup'], 'existing_exact_contained_actors')
    descriptors = [os.pidfd_open(item['pid']) for item in actors]
    paused = False
    committed = False
    base.write(folder / 'ARMED.json', dict(actors=actors, root=spec['backing_root'],
        not_before_unix=NOT_BEFORE, quiet_end_unix=QUIET_END, hard_end_unix=base.HARD_END,
        observed_unix=time.time(), original_native_sha256=base.sha(source / 'new_native.py'),
        original_journal_sha256=base.sha(source / 'new_journal.py')))
    print(json.dumps(dict(physical=physical, pid=os.getpid(), native=actor['pid'],
        status='SAVED_BOUNDARY_STOP_ARMED', not_before_unix=NOT_BEFORE)), flush=True)
    try:
        while time.time() < QUIET_END:
            if select.select([descriptors[0]], [], [], 0)[0]:
                base.write(folder / 'ALREADY_EXITED.json', dict(observed_unix=time.time(),
                    exact_native_pid=actor['pid'], no_additional_signals=True,
                    current_head_kind=base.head(spec['backing_root'])['kind']))
                return
            if time.time() < NOT_BEFORE:
                time.sleep(max(0, min(1, NOT_BEFORE - time.time())))
                continue
            record = base.head(spec['backing_root'])
            if not may_capture(time.time(), record):
                time.sleep(.1)
                continue
            state = base.saved_state(record)
            base.exact(actor)
            signal.pidfd_send_signal(descriptors[0], signal.SIGSTOP)
            paused = True
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                tasks = (Path('/proc') / str(actor['pid']) / 'task').iterdir()
                if all((task / 'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't')
                       for task in tasks):
                    break
                time.sleep(.01)
            else:
                raise ValueError('all_native_threads_must_pause')
            if base.head(spec['backing_root'])['sha256'] != record['sha256']:
                signal.pidfd_send_signal(descriptors[0], signal.SIGCONT)
                paused = False
                continue
            while present_children(actor['pid']) and time.time() < QUIET_END:
                time.sleep(.1)
            base.require(not present_children(actor['pid']), 'existing_child_processes_complete_before_stop')
            checkpoint_path = Path(spec['backing_root']) / 'checkpoints' / (
                'sleep_%06d' % record['document']['cycle']) / 'COMMIT.json'
            checkpoint = base.read(checkpoint_path)
            mapped = lambda value: Path(spec['backing_root']) / Path(value).relative_to(plan['root'])
            base.require(base.sha(mapped(checkpoint['optimizer_rng_path'])) ==
                checkpoint['checkpoint_sha256']['optimizer'] == checkpoint['checkpoint_sha256']['rng'],
                'exact_saved_optimizer_RNG')
            adapter = {path.name: base.sha(path) for path in mapped(checkpoint['adapter_path']).iterdir()
                if path.is_file()}
            base.require(adapter == checkpoint['adapter_files'] and base.digest(adapter) ==
                checkpoint['checkpoint_sha256']['adapter'] and base.digest(checkpoint['checkpoint_sha256']) ==
                state['model_state_sha256'], 'exact_saved_adapter_and_stream_state')
            base.require(base.head(spec['backing_root'])['sha256'] == record['sha256'],
                'same_saved_boundary_before_stop')
            base.write(folder / 'SAVED_BOUNDARY.json', dict(record_index=record['index'],
                record_sha256=record['sha256'], cycle=record['document']['cycle'],
                total_optimizer_steps=record['document']['total_optimizer_steps'],
                checkpoint_path=str(checkpoint_path), checkpoint_file_sha256=base.sha(checkpoint_path),
                model_state_sha256=state['model_state_sha256'], root_preserved_in_place=spec['backing_root'],
                inbox_files={path.name: base.sha(path) for path in
                    (Path(spec['backing_root']) / 'stream/inbox').glob('*.json')},
                observed_unix=time.time(), discarded_updates=0, readout_contents_read=False))
            committed = True
            for expected, descriptor in zip(actors, descriptors):
                if not select.select([descriptor], [], [], 0)[0]:
                    terminate(expected)
            base.require(all(select.select([descriptor], [], [], 0)[0] for descriptor in descriptors),
                'all_owned_actors_exited')
            paused = False
            base.write(folder / 'STOPPED.json', dict(status='EXACT_SAVED_BOUNDARY_STOPPED',
                observed_unix=time.time(), cycle=record['document']['cycle'],
                record_index=record['index'], record_sha256=record['sha256'],
                actors=actors, discarded_updates=0, root_preserved_in_place=spec['backing_root'],
                hard_end_unix=base.HARD_END, no_successor_or_restart=True))
            return
        base.write(folder / 'NO_QUIET_BOUNDARY.json', dict(observed_unix=time.time(),
            unchanged_existing_timeout_enforces=base.HARD_END, no_exact_stop_claim=True))
    except BaseException as error:
        base.write(folder / 'FAILED.json', dict(error_type=type(error).__name__, reason=str(error)[:500],
            observed_unix=time.time(), stop_committed=committed))
        raise
    finally:
        if paused and not committed and not select.select([descriptors[0]], [], [], 0)[0]:
            signal.pidfd_send_signal(descriptors[0], signal.SIGCONT)
        for descriptor in descriptors:
            os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(0, 1, 2, 3, 4, 7), required=True)
    args = parser.parse_args()
    base.require(socket.gethostname() == '[REDACTED_HOST]', 'node3_only')
    run(args.physical)
