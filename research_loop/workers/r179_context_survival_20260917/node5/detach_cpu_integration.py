"""Receiving CPU-only systemd wait/pipe detach proof in an isolated new root."""

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
import uuid

import controller_transfer as transfer


def wait_for(predicate, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise TimeoutError('bounded_CPU_detach_probe_wait')


def service(root):
    transfer.require(os.getuid() == 2524 and 'torch' not in sys.modules, 'CPU_only_service_identity')
    identity = transfer.process_identity(os.getpid())
    transfer.write(root / 'SERVICE_STARTED.json', identity)
    deadline = time.monotonic() + 14
    counter = 0
    while time.monotonic() < deadline:
        counter += 1
        temporary = root / 'HEARTBEAT.partial'
        temporary.write_text(json.dumps(dict(counter=counter, pid=os.getpid(), observed_unix=time.time())))
        os.replace(temporary, root / 'HEARTBEAT.json')
        print('CPU_ONLY_HEARTBEAT', flush=True)
        time.sleep(0.1)
    transfer.write(root / 'SERVICE_COMPLETE.json', dict(status='PASS', identity=identity,
        counters=counter, natural_exit=True, model_loaded=False))


def outer(root):
    descriptor = os.open(root / 'PROBE_HANDOFF.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        transfer.require(not os.get_inheritable(descriptor), 'lock_not_inherited_by_wait_child')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        transfer.write(root / 'OUTER_STARTED.json', transfer.process_identity(os.getpid()))
        result = subprocess.run(transfer.read(root / 'COMMAND.json')['command'], check=False)
        transfer.write(root / 'OUTER_TERMINAL.json', dict(returncode=result.returncode, no_retry=True))
    finally:
        os.close(descriptor)


def run(output):
    transfer.require(os.getuid() == 2524 and output.parent == transfer.BASE, 'receiving_NODE5_CPU_probe')
    transfer.require(not (output / 'DETACH_CPU_INTEGRATION.json').exists(), 'new_CPU_probe_receipt_only')
    root = output / ('CPU_DETACH_PROBE_' + uuid.uuid4().hex)
    root.mkdir(mode=0o700)
    unit = 'orch-r179-controller-cpu-' + uuid.uuid4().hex
    script = str(Path(__file__).resolve())
    properties = dict(User='2524', Group='2524', NoNewPrivileges='yes', DevicePolicy='strict',
        CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes',
        RuntimeMaxSec='25', TimeoutStopSec='5', KillMode='control-group', WorkingDirectory=str(root))
    command = ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + unit,
        *['--property=' + name + '=' + value for name, value in properties.items()], '--property=DeviceAllow=',
        '--property=DeviceAllow=/dev/null rw', '--property=DeviceAllow=/dev/zero rw',
        '--property=DeviceAllow=/dev/random r', '--property=DeviceAllow=/dev/urandom r',
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'HOME=' + str(transfer.BASE), 'CUDA_VISIBLE_DEVICES=',
        'PYTHONDONTWRITEBYTECODE=1', sys.executable, '-B', script, '--action', 'service', '--output', str(root)]
    transfer.write(root / 'COMMAND.json', dict(command=command, model_loaded=False))
    with (root / 'OUTER.log').open('x') as log:
        controller = subprocess.Popen([sys.executable, '-B', script, '--action', 'outer', '--output', str(root)],
            stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    holder_descriptor = os.pidfd_open(controller.pid)
    lock_descriptor = None
    try:
        wait_for(lambda: (root / 'HEARTBEAT.json').exists(), 12)
        holder = transfer.read(root / 'OUTER_STARTED.json')
        actor = transfer.read(root / 'SERVICE_STARTED.json')
        current_holder = transfer.process_identity(controller.pid)
        transfer.require(current_holder == holder and holder['group'] == holder['session'] == holder['pid'],
                         'exact_probe_outer_session_before_signal')
        transfer.require(actor['session'] != holder['session'] and actor['cgroup'] ==
                         '0::/system.slice/' + unit + '.service', 'separate_actual_systemd_CPU_service')
        lock = transfer.lock_identity(root / 'PROBE_HANDOFF.lock')
        transfer.require(transfer.flock_owners(lock) == [holder['pid']], 'real_probe_lock_owned_by_outer')
        lock_descriptor = os.open(root / 'PROBE_HANDOFF.lock', os.O_RDWR | os.O_NOFOLLOW)
        try:
            fcntl.flock(lock_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise ValueError('probe_lock_must_exclude_before_outer_detach')
        before = transfer.read(root / 'HEARTBEAT.json')
        children = (Path('/proc') / str(holder['pid']) / 'task' / str(holder['pid']) / 'children').read_text().split()
        transfer.require(len(children) == 1, 'one_real_wait_child')
        child = transfer.process_identity(int(children[0]))
        transfer.require(child['argv'] == command, 'real_sudo_systemd_wait_pipe_child')
        transfer.write(root / 'CPU_CONTROLLER_STOP_INTENT.json', dict(holder=holder,
            target='ISOLATED_TEST_CPU_CONTROLLER_ONLY', signal='SIGTERM', no_group_signals=True))
        signal.pidfd_send_signal(holder_descriptor, signal.SIGTERM)
        transfer.require(bool(select.select([holder_descriptor], [], [], 5)[0]), 'probe_outer_exit')
        transfer.require(controller.wait(timeout=1) == -signal.SIGTERM, 'default_SIGTERM_termination')
        fcntl.flock(lock_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        transfer.require(transfer.lock_identity(lock['path']) == lock
                         and transfer.flock_owners(lock) == [os.getpid()], 'same_inode_real_flock_transfer')
        wait_for(lambda: transfer.read(root / 'HEARTBEAT.json')['counter'] >= before['counter'] + 8, 4)
        child_after = transfer.process_identity(child['pid'])
        actor_after = transfer.process_identity(actor['pid'])
        transfer.require(all(child_after[key] == child[key] for key in
            ('pid', 'start_ticks', 'uid', 'session', 'argv_sha256')), 'wait_child_survives_without_signal')
        transfer.require(actor_after == actor, 'systemd_CPU_service_identity_unchanged')
        wait_for(lambda: (root / 'SERVICE_COMPLETE.json').exists(), 18)
        transfer.require(not (root / 'OUTER_TERMINAL.json').exists(), 'detached_outer_did_not_relaunch')
        receipt = dict(status='PASS', real_systemd_wait_pipe=True, service_survived_outer_SIGTERM=True,
            same_inode_flock_acquired=True, sudo_wait_child_survived=True,
            native_equivalent_identity_unchanged=True, model_loaded=False, group_signals=0,
            live_controller_signals=0, production_locks_opened=0,
            service_completed_naturally=transfer.reference(root / 'SERVICE_COMPLETE.json'),
            controller_stop=transfer.reference(root / 'CPU_CONTROLLER_STOP_INTENT.json'),
            test_script=transfer.reference(__file__), helper=transfer.reference(transfer.__file__),
            observed_unix=time.time())
        transfer.write(output / 'DETACH_CPU_INTEGRATION.json', receipt)
        print(json.dumps(transfer.reference(output / 'DETACH_CPU_INTEGRATION.json'), sort_keys=True))
    finally:
        os.close(holder_descriptor)
        if lock_descriptor is not None:
            os.close(lock_descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=('run', 'outer', 'service'), default='run')
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    {'run': run, 'outer': outer, 'service': service}[arguments.action](arguments.output)


if __name__ == '__main__':
    main()
