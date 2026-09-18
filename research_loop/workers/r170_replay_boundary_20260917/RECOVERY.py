"""Death-only recovery for exact lifecycle pidfds; never discover or restart work."""

import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time


ROLES = ('supervisor', 'timer', 'actor')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def problem(operation, error, role=None):
    return dict(operation=operation, role=role, error_type=type(error).__name__,
                errno=getattr(error, 'errno', None))


def exited(descriptor):
    return bool(select.select([descriptor], [], [], 0)[0])


def not_stopped(descriptor):
    if exited(descriptor):
        return True
    try:
        fields = dict(line.split(':', 1) for line in
                      Path('/proc/self/fdinfo', str(descriptor)).read_text().splitlines())
        identifier = int(fields['Pid'].strip())
        require(identifier > 0, 'live_pidfd_identity')
        tasks = list(Path('/proc', str(identifier), 'task').iterdir())
        states = [path.joinpath('stat').read_text().rsplit(')', 1)[1].split()[0] for path in tasks]
        return exited(descriptor) or bool(states) and all(state not in ('T', 't') for state in states)
    except (OSError, ValueError, KeyError):
        return exited(descriptor)


def continue_all(descriptors):
    errors = []
    for role, descriptor in descriptors.items():
        try:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        except ProcessLookupError:
            pass
        except OSError as error:
            errors.append(problem('SIGCONT', error, role))
    return errors


def watch(operator_fd, descriptors, ready_fd, control_fd):
    require(set(descriptors) == set(ROLES), 'exact_three_lifecycle_roles')
    handles = [operator_fd, *descriptors.values()]
    require(len(set(handles)) == 4 and all(type(handle) is int and handle >= 0 for handle in handles),
            'distinct_inherited_pidfds')
    require(all(os.readlink('/proc/self/fd/' + str(handle)) == 'anon_inode:[pidfd]'
                for handle in handles), 'pidfd_handles_only')
    os.write(ready_fd, b'R')
    os.close(ready_fd)
    control_open = True
    while True:
        readable = select.select([operator_fd, *([control_fd] if control_open else [])], [], [])[0]
        if operator_fd in readable:
            errors = continue_all(descriptors)
            print(json.dumps(dict(status='OPERATOR_DIED_CONT_ATTEMPTED', errors=errors,
                                  observed_unix=time.time(), restart=False)), flush=True)
            return 1 if errors else 0
        if control_open and control_fd in readable:
            command = os.read(control_fd, 1)
            if command == b'D' and all(not_stopped(handle) for handle in descriptors.values()):
                print(json.dumps(dict(status='DISARMED_TARGETS_EXITED_OR_RUNNING',
                                      observed_unix=time.time(), signals_sent=0)), flush=True)
                return 0
            if not command:
                os.close(control_fd)
                control_open = False


class Recovery:
    def __init__(self):
        self.process = None
        self.control = None
        self.errors = []
        self.armed = False
        self.finished = False

    def arm(self, helper, processes, descriptors, output):
        if self.armed:
            return
        require(not self.finished and self.process is None, 'one_watcher_attempt')
        require(set(processes) == set(descriptors) == set(ROLES), 'exact_validated_lifecycle')
        for role in ROLES:
            require(helper.process_record(processes[role]['pid']) == processes[role],
                    'identity_before_watcher_' + role)
        operator_fd = os.pidfd_open(os.getpid())
        ready_reader, ready_writer = os.pipe2(os.O_CLOEXEC)
        control_reader, self.control = os.pipe2(os.O_CLOEXEC)
        try:
            command = [sys.executable, '-B', str(Path(__file__).resolve()), '--watchdog',
                       '--operator-fd', str(operator_fd), '--ready-fd', str(ready_writer),
                       '--control-fd', str(control_reader)]
            for role in ROLES:
                command.extend(['--' + role + '-fd', str(descriptors[role])])
            with (Path(output) / 'DEATH_WATCHER.log').open('x') as log:
                self.process = subprocess.Popen(command,
                    pass_fds=(operator_fd, ready_writer, control_reader, *descriptors.values()),
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True, env=dict(PATH='/usr/bin:/bin',
                    PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''))
            os.close(ready_writer)
            ready_writer = None
            require(bool(select.select([ready_reader], [], [], 5)[0])
                    and os.read(ready_reader, 1) == b'R' and self.process.poll() is None,
                    'watcher_ready_before_any_STOP')
            self.armed = True
            helper.write(Path(output) / 'DEATH_WATCHER_READY.json', dict(
                watcher_pid=self.process.pid, operator_pid=os.getpid(), roles=list(ROLES),
                processes=processes, ready_unix=time.time(), death_only=True,
                timeout_resume=False, automatic_restart=False))
        finally:
            for descriptor in (operator_fd, ready_reader, ready_writer, control_reader):
                if descriptor is not None:
                    try:
                        os.close(descriptor)
                    except OSError as error:
                        self.errors.append(problem('close_setup_fd', error))

    def pause(self, helper, expected, descriptor, processes, descriptors, output):
        self.arm(helper, processes, descriptors, output)
        require(not self.errors and self.process.poll() is None, 'ready_live_watcher_before_STOP')
        helper.pause_exact(expected, descriptor)

    def resume(self, paused, descriptors):
        failures = []
        for role in reversed(list(paused)):
            try:
                signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
            except ProcessLookupError:
                paused.remove(role)
            except OSError as error:
                failures.append(problem('SIGCONT', error, role))
            else:
                paused.remove(role)
        self.errors.extend(failures)
        if failures:
            raise RuntimeError('pause_recovery_CONT_failed_other_handles_attempted')

    def cleanup(self, paused, descriptors, lock, handlers, output):
        try:
            self.resume(paused, descriptors)
        except BaseException as error:
            self.errors.append(problem('resume_during_cleanup', error))
        finally:
            for role, descriptor in descriptors.items():
                try:
                    os.close(descriptor)
                except OSError as error:
                    self.errors.append(problem('close_pidfd', error, role))
            try:
                os.close(lock)
            except OSError as error:
                self.errors.append(problem('close_lock', error))
            for signum, handler in handlers.items():
                try:
                    signal.signal(signum, handler)
                except BaseException as error:
                    self.errors.append(problem('restore_signal_handler', error, str(signum)))
            if self.control is not None:
                try:
                    if not self.errors:
                        os.write(self.control, b'D')
                except OSError as error:
                    self.errors.append(problem('watcher_disarm', error))
                finally:
                    try:
                        os.close(self.control)
                    except OSError as error:
                        self.errors.append(problem('close_watcher_control', error))
                    self.control = None
            if self.process is not None and not self.errors:
                try:
                    require(self.process.wait(timeout=5) == 0, 'watcher_clean_disarm')
                except BaseException as error:
                    self.errors.append(problem('watcher_wait', error))
            self.finished = True
        receipt = dict(status='RECOVERED_AND_CLEANED' if not self.errors else 'RECOVERY_INCOMPLETE',
                       errors=self.errors, observed_unix=time.time(), watcher_armed=self.armed,
                       automatic_restart=False, retry=False)
        with (Path(output) / ('RECOVERY_' + str(time.time_ns()) + '.json')).open('x') as handle:
            json.dump(receipt, handle, sort_keys=True, indent=2)
        if self.errors:
            raise RuntimeError('pause_recovery_incomplete_preserve_failure_no_retry')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watchdog', action='store_true', required=True)
    parser.add_argument('--operator-fd', type=int, required=True)
    parser.add_argument('--ready-fd', type=int, required=True)
    parser.add_argument('--control-fd', type=int, required=True)
    for role in ROLES:
        parser.add_argument('--' + role + '-fd', type=int, required=True)
    args = parser.parse_args()
    return watch(args.operator_fd, {role: getattr(args, role + '_fd') for role in ROLES},
                 args.ready_fd, args.control_fd)


if __name__ == '__main__':
    sys.exit(main())
