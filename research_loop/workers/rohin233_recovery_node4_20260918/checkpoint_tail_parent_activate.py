"""Explicitly authorized, exact CPU-only handoff after the new C2 LOAD."""

import fcntl
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from checkpoint_tail_parent_binding import WALL
from deadline_resume import identity, sha, write
from renew_c2_cpu import stop_drained_parent, remote, PYTHON


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
REMOTE = '/localhome/local-rohing/orch_r233_C2_checkpoint_tail_20260918/parent_operator'


def stop_old_waiter():
    pid = 3590563
    process = Path('/proc') / str(pid)
    expected = ['/usr/bin/python3', '-B', str(OWN / 'renew_c2_cpu.py'), '--hard-end-unix', str(WALL)]
    descriptor = os.pidfd_open(pid)
    try:
        until = time.monotonic() + 90
        while time.monotonic() < until:
            actual = identity(pid)
            if (actual['start_ticks'] != '186658124' or actual['uid'] != os.getuid()
                    or actual['argv'] != expected or actual['cwd'] != str(REPO)):
                raise ValueError('exact_old_CPU_waiter_required_no_signal')
            children = (process / 'task' / str(pid) / 'children').read_text().strip()
            if not children and (process / 'wchan').read_text().strip() == 'hrtimer_nanosleep':
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                poller = select.poll()
                poller.register(descriptor, select.POLLIN)
                if not poller.poll(10000):
                    raise RuntimeError('old_CPU_waiter_exit_unconfirmed')
                return dict(identity=actual, exited_unix=time.time(), signal='EXACT_IDLE_CPU_PIDFD_SIGTERM',
                    native_signals=[])
            time.sleep(.2)
        raise TimeoutError('old_CPU_waiter_not_idle_no_signal')
    finally:
        os.close(descriptor)


def main():
    binding_path = OWN / 'C2_CHECKPOINT_TAIL_LOADED.json'
    binding = json.loads(binding_path.read_bytes())
    if binding['status'] != 'LOADED' or binding['native'] != dict(pid=1139778, start_ticks='30025875'):
        raise ValueError('actual_exact_new_C2_LOAD_required')
    verify = ('import sys;sys.path.insert(0,' + repr(REMOTE) + ');from checkpoint_tail_parent_binding import verify;'
        'verify(' + repr(REMOTE + '/C2_CHECKPOINT_TAIL_LOADED.json') + ',' + repr(sha(binding_path)) + ')')
    remote(PYTHON + ' -B -', verify)
    stopped_waiter = stop_old_waiter()
    write(OWN / 'CHECKPOINT_TAIL_OLD_WAITER_RETIRED.json', stopped_waiter)
    with (OWN / 'private/C2_WAIT_CONTROLLER.lock').open('a') as controller:
        fcntl.flock(controller.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        stopped_parent = stop_drained_parent()
        write(OWN / 'CHECKPOINT_TAIL_OLD_PARENT_DRAINED.json', stopped_parent)
        receipts = OWN / 'private/checkpoint_tail_parent_control'
        output = OWN / 'private/checkpoint_tail_parent'
        subprocess.run([sys.executable, '-B', str(OWN / 'checkpoint_tail_parent_prepare.py'),
            '--binding', str(binding_path), '--remote-binding-path', REMOTE + '/C2_CHECKPOINT_TAIL_LOADED.json',
            '--remote-operator', REMOTE, '--receipt-directory', str(receipts), '--parent-output', str(output)],
            check=True)
        manifest = receipts / 'CHECKPOINT_TAIL_PARENT_MANIFEST.json'
    with (OWN / 'private/CHECKPOINT_TAIL_PARENT_RUN.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', str(OWN / 'checkpoint_tail_parent_continue.py'),
            '--manifest', str(manifest), '--manifest-sha256', sha(manifest)], cwd=REPO,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    spawned = dict(pid=child.pid, spawned_unix=time.time(), manifest_sha256=sha(manifest), native_signals=[])
    write(OWN / 'CHECKPOINT_TAIL_PARENT_SPAWNED.json', spawned)
    until = time.monotonic() + 90
    while not (output / 'STARTED.json').exists():
        if child.poll() is not None or time.monotonic() >= until:
            raise RuntimeError('parent_START_not_confirmed_inspect_preserved_log_no_blind_retry')
        time.sleep(.5)
    started = json.loads((output / 'STARTED.json').read_bytes())
    if started['pid'] != child.pid:
        raise ValueError('actual_CPU_parent_START_identity')
    result = dict(status='CPU_PARENT_STARTED_ACTUAL_C2_LOAD_BOUND_RENDER_PENDING', observed_unix=time.time(),
        parent=identity(child.pid), started=started, hard_end_unix=WALL,
        native=binding['native'], loaded=binding['loaded'], wall_extended=binding['wall_extended'],
        binding_sha256=sha(binding_path), manifest_sha256=sha(manifest),
        predecessor_waiter=stopped_waiter, predecessor_parent=stopped_parent,
        original_parent_source_provider_ledger_preserved=True, actual_REQUEST_render_pending=True, native_signals=[])
    write(OWN / 'CHECKPOINT_TAIL_PARENT_ACTIVATED.json', result)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
