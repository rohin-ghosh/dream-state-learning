"""Replace only a quiescent CPU boundary waiter with a ready immutable successor."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import time


EFFECTS = ('ACTUAL_BOUNDARY_READY.json', 'CONTROLLER_STOP_INTENT.json',
           'CONTROLLER_EXITED.json', 'CONTROLLER_LOCK_ACQUIRED.json',
           'TERMINATION_INTENT.json', 'OWNER_RETIRED.json', 'attempt', 'EXECUTION_FAILED.json')


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_bytes())


def reference(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def before_handoff(output):
    require(not any((output / name).exists() for name in EFFECTS), 'waiter_already_advanced_no_replacement')


def exact_started(saved, output):
    expected = read(output / 'OPERATOR_STARTED.json')['identity']
    current = saved.identity(expected['pid'])
    for key in ('pid', 'start_ticks', 'uid', 'argv', 'cwd', 'boot_id'):
        require(current[key] == expected[key], 'exact_waiter_' + key)
    require(current['uid'] == 2524 and current['argv'][2:6] ==
        [str(output / 'rollout_operator.py'), 'execute', '--output', str(output)], 'only_owned_execute_waiter')
    require(reference(output / 'rollout_operator.py') == read(output / 'READY.json')['operator'], 'bound_waiter_source')
    return current


def terminate_once(descriptor):
    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
    try:
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
    except ProcessLookupError:
        pass
    poller = select.poll()
    poller.register(descriptor, select.POLLIN)
    require(bool(poller.poll(10000)), 'CPU_waiter_not_exited_no_repeat_stop')


def execute(old, successor, seconds):
    require(socket.gethostname() == '[REDACTED_HOST]' and os.getuid() == 2524, 'node5_owner_only')
    for output in (old, successor):
        require(output.parent == Path('/localhome/local-rohing') and
                output.name.startswith('orch_r181_node5_') and not output.is_symlink(), 'owned_root')
    before_handoff(old)
    require(not (successor / 'OPERATOR_STARTED.json').exists(), 'successor_not_started')
    spec = importlib.util.spec_from_file_location('successor_operator', successor / 'rollout_operator.py')
    operator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operator)
    saved, config, plan = operator.validate_successor(successor)
    old_ready, new_ready = read(old / 'READY.json'), read(successor / 'READY.json')
    require(old_ready['pair'] == new_ready['pair'], 'same_unmodified_native_pair')
    current = exact_started(saved, old)
    descriptor = os.pidfd_open(current['pid'])
    stopped = False
    try:
        with saved.pause_watchdog(descriptor, 60):
            saved.pause_exact(current, descriptor)
            before_handoff(old)
            require(not saved.live_children(current['pid']), 'CPU_waiter_has_no_active_child')
            for native in new_ready['pair'].values():
                saved.same(native)
                state = (Path('/proc') / str(native['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()[0]
                require(state not in ('T', 't', 'Z', 'X'), 'native_unpaused_and_alive')
            write(successor / 'WAITER_REPLACEMENT_INTENT.json', dict(old_waiter=current,
                old_ready=reference(old / 'READY.json'), new_ready=reference(successor / 'READY.json'),
                native_signals=0, old_attempt_preserved=True, lock_operations=0, observed_unix=time.time()))
            stopped = True
            terminate_once(descriptor)
            write(successor / 'WAITER_REPLACED.json', dict(old_pid=current['pid'],
                old_start_ticks=current['start_ticks'], native_signals=0, lock_operations=0,
                exited=True, observed_unix=time.time()))
        authorization = successor / 'R181_AUTHORITY.json'
        result = subprocess.run([str(operator.PYTHON), '-B', str(successor / 'rollout_operator.py'),
            'start', '--output', str(successor), '--seconds', str(seconds),
            '--controller-go', str(authorization), '--controller-go-sha256', reference(authorization)['sha256']],
            env=operator.environment(successor / 'source'), cwd=successor / 'source',
            capture_output=True, text=True, timeout=60)
        write(successor / 'REPLACEMENT_START.json', dict(returncode=result.returncode,
            stdout=result.stdout, stderr=result.stderr, native_signals=0, observed_unix=time.time()))
        require(result.returncode == 0, 'replacement_start_failed_no_replay')
        print(result.stdout.strip())
    except BaseException as error:
        write(successor / 'WAITER_REPLACEMENT_FAILED.json', dict(reason=str(error),
            stop_attempted=stopped, automatic_retry=False, native_signals=0, observed_unix=time.time()))
        raise
    finally:
        os.close(descriptor)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old', required=True, type=Path)
    parser.add_argument('--successor', required=True, type=Path)
    parser.add_argument('--seconds', type=int, default=14400)
    arguments = parser.parse_args()
    execute(arguments.old, arguments.successor, arguments.seconds)
