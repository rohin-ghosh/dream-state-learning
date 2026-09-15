"""Prospective CPU FINAL timer transfer from the failed parallel service era."""

import argparse
import os
from pathlib import Path
import select
import signal
import time
from types import FunctionType

from gpu import orch_r118_code_parallel_stage as stage


final, handoff, io, require = stage.final, stage.handoff, stage.io, stage.require


def validate_timer(root, expected, *, clock=time.time, command=None):
    root = Path(root)
    require(clock() < final.original.CUTOFF - 600, 'before_FINAL_drain_window')
    final.unused_allocation(root)
    dispatch = io.read(root / 'CPU_DISPATCH.json')
    require(expected['pid'] != 1519259 and dispatch['identity'] == expected
        and dispatch['module'] == final.MODULE and handoff.alive(expected), 'exact_parallel_FINAL_timer')
    if command is None:
        command = (Path('/proc') / str(expected['pid']) / 'cmdline').read_bytes().split(b'\0')
    require([b'-m', final.MODULE.encode(), b'schedule', b'--root', str(root).encode()]
        == command[2:7], 'only_exact_parallel_FINAL_schedule_command')
    return dispatch


def cancel_timer(root, expected, *, clock=time.time):
    validate_timer(root, expected, clock=clock)
    descriptor = os.pidfd_open(expected['pid'])
    try:
        require(handoff.alive(expected), 'same_parallel_timer_pidfd')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        require(select.select([descriptor], [], [], 5)[0], 'parallel_CPU_timer_exited')
    finally:
        os.close(descriptor)
    return dict(identity=expected, actual_exit_unix=clock(),
        old_dispatch=handoff.ref(Path(root) / 'CPU_DISPATCH.json'),
        original_allocation=handoff.ref(Path(root) / 'PLAN.json'), cancelled_only_CPU_waiter=True)


def rebind(service, *, clock=time.time, cancel=cancel_timer):
    runtime = io.read(Path(service) / 'RUNTIME.json')
    released = handoff.checked(runtime['handoff'])
    proof = handoff.checked(released['failed_startup_recovery'])
    require(proof['root'] == runtime['root'] and proof['new_calls'] == 0 and proof['optimizer_steps'] == 0,
        'exact_failed_startup_FINAL_custody')
    for name in ('identity', 'guardian'):
        require(not handoff.alive(proof['identities'][name]), 'failed_era_process_stays_exited')
    return stage.rebind(service, clock=clock, cancel=cancel)


def serve(service):
    namespace = dict(vars(stage), rebind=rebind)
    FunctionType(stage.serve.__code__, namespace, 'serve', stage.serve.__defaults__)(service)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service', type=Path, required=True)
    serve(parser.parse_args().service)
