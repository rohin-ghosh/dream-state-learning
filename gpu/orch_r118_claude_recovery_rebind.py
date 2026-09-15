"""Terminal-only recovery using the pinned original custody implementation."""

import hashlib
import importlib.util
import os
from pathlib import Path
import time


CUSTODY_SHA256 = '985111d9e1c49ecdcf18deb82b6b19bdcdb6e5a05695b3372b79b5615a066635'


def settled_identity(read_identity, *, parent_pid=os.getppid, clock=time.monotonic,
                     sleep=time.sleep, timeout=60):
    deadline = clock() + timeout
    while clock() < deadline:
        if parent_pid() == 1:
            first = read_identity()
            sleep(.1)
            second = read_identity()
            if first == second and second['ppid'] == 1:
                return second
        sleep(.1)
    raise RuntimeError('broker_parent_not_settled_no_ready_publication')


def load_custody(path):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != CUSTODY_SHA256:
        raise ValueError('exact_original_custody_dependency')
    specification = importlib.util.spec_from_file_location('frozen_terminal_custody', path)
    custody = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(custody)
    return custody


def configure(custody):
    custody.TERMINALS = dict(custody.TERMINALS, F4='R118_GRID_PARALLEL_RECOVERY_V1_TERMINAL.json')
    original_identity = custody.identity
    custody.identity = lambda: settled_identity(original_identity)
    custody.__file__ = str(Path(__file__).resolve())
    return custody


if __name__ == '__main__':
    configure(load_custody(Path(__file__).with_name('orch_r118_claude_terminal_rebind.py'))).main()
