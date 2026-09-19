"""Detached same-pidfd CONT fail-safe for owner-verified parent-only handoffs."""

import argparse
from contextlib import contextmanager
import os
import select
import signal
import subprocess
import sys
import time

from gpu import orch_r167_parent_takeover as takeover


def watch(parent_fd, operator_fd, cancel_fd, ready_fd, seconds):
    poller = select.poll()
    for descriptor in (parent_fd, operator_fd, cancel_fd):
        poller.register(descriptor, select.POLLIN | select.POLLHUP | select.POLLERR)
    os.write(ready_fd, b'READY')
    os.close(ready_fd)
    events = dict(poller.poll(int(seconds*1000)))
    if parent_fd in events:
        return 'PARENT_EXITED'
    if cancel_fd in events and os.read(cancel_fd, 1) == b'D':
        return 'DISARMED_AFTER_RELEASE'
    try:
        signal.pidfd_send_signal(parent_fd, signal.SIGCONT)
    except ProcessLookupError:
        return 'PARENT_EXITED'
    return 'CONT_OPERATOR_EXIT_OR_TIMEOUT'


class Watchdog:
    def __init__(self, parent_fd, seconds):
        self.deadline = time.monotonic()+seconds
        self.operator_fd = os.pidfd_open(os.getpid())
        cancel_read, self.cancel_write = os.pipe()
        ready_read, ready_write = os.pipe()
        self.process = None
        try:
            command = [sys.executable, '-B', '-m', 'gpu.orch_r167_parent_watchdog',
                '--parent-fd', str(parent_fd), '--operator-fd', str(self.operator_fd),
                '--cancel-fd', str(cancel_read), '--ready-fd', str(ready_write), '--seconds', str(seconds)]
            self.process = subprocess.Popen(command, pass_fds=(parent_fd, self.operator_fd, cancel_read, ready_write),
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True)
            readable, unused_write, unused_errors = select.select([ready_read], [], [], 3)
            takeover.require(readable and os.read(ready_read, 5) == b'READY'
                and self.process.poll() is None, 'watchdog_ready_before_STOP')
        except BaseException:
            self.release()
            raise
        finally:
            for descriptor in (cancel_read, ready_read, ready_write, self.operator_fd):
                os.close(descriptor)

    def release(self):
        try:
            os.write(self.cancel_write, b'D')
        except BrokenPipeError:
            pass
        finally:
            os.close(self.cancel_write)
        if self.process is not None:
            self.process.wait(timeout=3)


class GuardedParent(takeover.QuiescedParent):
    def __init__(self, binding, operations, deadline):
        super().__init__(binding, operations)
        self.deadline = deadline

    def terminate(self):
        takeover.require(time.monotonic()+2 < self.deadline, 'stop_budget_expiring_defer')
        super().terminate()


@contextmanager
def quiesce(binding, *, scope_verifier, operations=None, watchdog_factory=Watchdog, seconds=15):
    """Scope verifier is mandatory: caller binds its Main-approved parent allowlist.

    R133 owner may reuse this with a verifier for its exact module/standalone entry;
    same PID/start/argv and file checks remain mandatory. No killgroup or SIGKILL.
    """
    takeover.require(type(seconds) in (int, float) and 5 <= seconds <= 30, 'bounded_stop_watchdog')
    operations = operations or takeover.PidfdOperations()

    def verify():
        observed = operations.read_identity(binding['pid'])
        takeover.require(observed['pid'] == binding['pid'] and observed['start_ticks'] == binding['start_ticks']
            and observed['argv'] == binding['argv'] and observed['state'] not in ('Z', 'X'), 'same_pidfd_parent_identity')
        scope_verifier(binding, observed)
        operations.check_files(binding)
        return observed

    takeover.require(verify()['state'] not in ('T', 't'), 'preexisting_stop_not_owned')
    descriptor = operations.open(binding['pid'])
    guard = None
    handle = GuardedParent(binding, operations, time.monotonic()+seconds)
    handle.descriptor = descriptor
    try:
        verify()
        guard = watchdog_factory(descriptor, seconds)
        handle.stopped = True
        operations.signal(descriptor, signal.SIGSTOP)
        for attempt in range(100):
            if operations.read_identity(binding['pid'])['state'] in ('T', 't'):
                break
            time.sleep(0.01)
        verify()
        operations.stopped_and_childless(binding['pid'])
        yield handle
    finally:
        try:
            if handle.stopped:
                operations.signal(descriptor, signal.SIGCONT)
                handle.stopped = False
            if guard is not None:
                guard.release()
        finally:
            operations.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent-fd', 'operator-fd', 'cancel-fd', 'ready-fd'):
        parser.add_argument('--'+name, required=True, type=int)
    parser.add_argument('--seconds', required=True, type=float)
    args = parser.parse_args()
    takeover.require(5 <= args.seconds <= 30, 'bounded_watchdog_seconds')
    watch(args.parent_fd, args.operator_fd, args.cancel_fd, args.ready_fd, args.seconds)


if __name__ == '__main__':
    main()
