"""Owned pidfd handoff only during an already-saved sleep's readout wait."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from gpu import orch_math_feedback_uptake_r124_readout as run
from gpu import orch_r111_route_boundary as pinned


read, write, sha, ref, require = run.read, run.write, run.sha, run.ref, run.require


def owned_actor(root):
    root = Path(root)
    plan, launch = read(root / 'PLAN.json'), read(root / 'LAUNCH.json')
    recorded = launch['identity']
    actual = pinned.identity(recorded['pid'])
    require(all(str(actual[key]) == str(value) for key, value in recorded.items()), 'actual_predecessor_identity')
    require(actual['uid'] == os.getuid() and actual['cwd'] == plan['source_root'], 'own_UID_frozen_cwd')
    directory = Path('/proc') / str(actual['pid'])
    args = (directory / 'cmdline').read_bytes().split(b'\0')
    module = 'gpu.orch_math_feedback_uptake_r123_f2_recovery' if plan['branch'] == 'F2' else 'gpu.orch_math_feedback_uptake_r121_independent_native'
    require(args[-6:] == [b'-m', module.encode(), b'resident', b'--root', str(root).encode(), b''], 'exact_owned_native_command')
    environment = (directory / 'environ').read_bytes().split(b'\0')
    require(('CUDA_VISIBLE_DEVICES=' + plan['uuid']).encode() in environment
        and ('PYTHONPATH=' + plan['source_root']).encode() in environment, 'exact_CVD_source_binding')
    executable = (directory / 'exe').stat()
    return dict(actual, exe_device=executable.st_dev, exe_inode=executable.st_ino)


def check_actor(request):
    require(owned_actor(request['predecessor_root']) == request['actor'], 'no_PID_reuse_or_exec')


def boundary_contract(committed, sleep, binding, later_cycles):
    require(sleep['checkpoint'] == committed['checkpoint'] == binding['checkpoint'], 'same_saved_readout_checkpoint')
    require(binding['parent_free'] is True and binding['train_rows'] is False and binding['split'] == 'DEV', 'DEV_wait_only')
    require(sleep['cumulative_optimizer_steps'] > 0 and not later_cycles, 'no_unsaved_next_cycle')
    return committed['cycle']


def candidate(request):
    root = Path(request['predecessor_root'])
    if not (root / 'COMMITTED.json').exists():
        return None
    committed = read(root / 'COMMITTED.json')
    cycle = committed['cycle']
    output = root / f'cycle{cycle:06d}'
    readout = root / 'readouts' / f'DEV_C{cycle:06d}'
    if not all(path.exists() for path in (output/'sleep/COMPLETE.json', output/'CARRY.json', readout/'LAUNCH.json', readout/'BINDING.json')):
        return None
    if (readout / 'PROCESS_RESULT.json').exists():
        return None
    later = [path.name for path in root.glob('cycle*') if int(path.name[5:]) > cycle]
    try:
        boundary_contract(committed, read(output/'sleep/COMPLETE.json'), read(readout/'BINDING.json'), later)
    except ValueError:
        return None
    identity = read(readout / 'LAUNCH.json')['identity']
    try:
        actual = pinned.identity(identity['pid'])
        if any(str(actual[key]) != str(value) for key, value in identity.items()) or actual['ppid'] != request['actor']['pid']:
            return None
        if pinned.process_state(actual['pid']) in ('Z', 'X'):
            return None
    except (FileNotFoundError, ProcessLookupError):
        return None
    actor_path = Path('/proc') / str(request['actor']['pid'])
    if (actor_path/'wchan').read_text().strip() not in ('do_wait', 'hrtimer_nanosleep'):
        return None
    return dict(cycle=cycle, checkpoint=committed['checkpoint'], readout_root=str(readout),
        readout_identity=identity, saved_sleep=ref(output/'sleep/COMPLETE.json'))


def settled(request, selected):
    root = Path(request['predecessor_root'])
    committed = read(root / 'COMMITTED.json')
    require(committed['cycle'] == selected['cycle'] and committed['checkpoint'] == selected['checkpoint'], 'same_committed_state_while_paused')
    require(not any(int(path.name[5:]) > selected['cycle'] for path in root.glob('cycle*')), 'no_later_episode_or_input')
    require(sha(selected['saved_sleep']['path']) == selected['saved_sleep']['sha256'], 'unchanged_sleep_save')
    counters = read(root/'COUNTERS.json')
    require(counters['optimizer_steps'] == read(selected['saved_sleep']['path'])['cumulative_optimizer_steps'], 'counters_match_saved_optimizer')
    checkpoint = selected['checkpoint']
    require(sha(checkpoint['path']) == checkpoint['path_sha256'] and
        sha(checkpoint['optimizer_path']) == checkpoint['optimizer_path_sha256'], 'durable_adapter_optimizer')
    return counters


def execute(branch):
    root = run.ROOT / branch
    request = read(root / 'REQUEST.json')
    require(request['branch'] == branch and request['root'] == str(root) and time.time() < request['boundary_expires_unix'], 'bounded_own_request')
    require(sha(request['source_manifest']['path']) == request['source_manifest']['sha256']
        and sha(request['tests']['path']) == request['tests']['sha256'] and read(request['tests']['path'])['passed'], 'CPU_provenance')
    for name, digest in read(request['source_manifest']['path']).items():
        require(sha(run.SOURCE/name) == digest, 'immutable_controller_source:' + name)
    pinned.gpu_mapping(request['index'], request['uuid'])
    check_actor(request)
    with (root/'BOUNDARY.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (root/'RELEASED.json').exists(), 'single_release')
        descriptor = os.pidfd_open(request['actor']['pid'])
        paused = False
        released = False
        try:
            while time.time() < request['boundary_expires_unix']:
                check_actor(request)
                try:
                    selected = candidate(request)
                except (FileNotFoundError, json.JSONDecodeError):
                    selected = None
                if selected is None:
                    time.sleep(.1)
                    continue
                signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
                paused = True
                until = time.monotonic() + 3
                while pinned.process_state(request['actor']['pid']) not in ('T', 't') and time.monotonic() < until:
                    time.sleep(.01)
                require(pinned.process_state(request['actor']['pid']) in ('T', 't'), 'actual_owned_pause')
                check_actor(request)
                try:
                    settled(request, selected)
                except ValueError:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    paused = False
                    continue
                write(root/'PAUSED_AT_SAVED_READOUT.json', dict(selected, actor=request['actor'], observed_unix=time.time()))
                child_fd = os.pidfd_open(selected['readout_identity']['pid'])
                try:
                    actual_child = pinned.identity(selected['readout_identity']['pid'])
                    require(all(str(actual_child[key]) == str(value) for key, value in selected['readout_identity'].items())
                        and actual_child['ppid'] == request['actor']['pid'], 'pidfd_readout_identity_not_reused')
                    poll = select.poll()
                    poll.register(child_fd, select.POLLIN)
                    remaining = min(900, request['bounds']['train_end_unix']-time.time()-600)
                    require(remaining > 0 and poll.poll(int(remaining*1000)), 'existing_readout_finishes_without_signal')
                finally:
                    os.close(child_fd)
                check_actor(request)
                counters = settled(request, selected)
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                paused = False
                poll = select.poll()
                poll.register(descriptor, select.POLLIN)
                require(poll.poll(30000), 'actual_predecessor_exit')
                released = True
                old_root = Path(request['predecessor_root'])
                until = time.monotonic()+30
                while not (old_root/'GUARD_TERMINAL.json').exists() and time.monotonic()<until:
                    time.sleep(.2)
                guard = read(old_root/'GUARD_TERMINAL.json')
                require(guard['identity'] == read(old_root/'LAUNCH.json')['identity'], 'real_predecessor_guard_terminal')
                require(read(old_root/'COUNTERS.json') == counters, 'no_post_boundary_charges')
                paths = [old_root/'PLAN.json', old_root/'COUNTERS.json', old_root/'COMMITTED.json', old_root/'LAUNCH.json',
                    old_root/'GUARD_TERMINAL.json', old_root/f'cycle{selected["cycle"]:06d}/CARRY.json',
                    old_root/f'cycle{selected["cycle"]:06d}/sleep/COMPLETE.json']
                paths.extend((old_root/'reservations').glob('*.json'))
                if (old_root/'TERMINAL.json').exists():
                    paths.append(old_root/'TERMINAL.json')
                release = dict(schema='R124_ACTUAL_OWNED_SAVED_BOUNDARY_RELEASE_V1', **selected,
                    actor=request['actor'], old_guard_terminal=ref(old_root/'GUARD_TERMINAL.json'),
                    counters=counters, next_cycle=selected['cycle']+1, actual_pidfd_exit=True,
                    disposition='INTENTIONAL_SAVED_BOUNDARY_NOT_CRASH_OR_CLEAN_OLD_CYCLE_CLAIM',
                    old_readout_complete=(Path(selected['readout_root'])/'COMPLETE.json').exists(),
                    old_readout_process_result_written=(Path(selected['readout_root'])/'PROCESS_RESULT.json').exists(),
                    preserved={str(path.relative_to(old_root)):sha(path) for path in paths}, released_unix=time.time())
                write(root/'RELEASED.json', release)
                run.build_successor(request, release)
                with (root/'GUARD.log').open('x') as log:
                    guard = subprocess.Popen([sys.executable, '-B', '-m', run.MODULE, 'guard', '--root', str(root)],
                        cwd=run.SOURCE, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(run.SOURCE)),
                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    write(root/'SUCCESSOR_GUARD_DISPATCHED.json', dict(identity=pinned.identity(guard.pid), started_unix=time.time()))
                return
            write(root/'NOT_RUN.json', dict(reason='NO_SAFE_SAVED_READOUT_BOUNDARY_WITHIN_WINDOW', observed_unix=time.time(), no_gpu_calls=True))
        finally:
            if paused and not released:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--branch', choices=('F2','A2'), required=True)
    arguments = parser.parse_args()
    execute(arguments.branch)
