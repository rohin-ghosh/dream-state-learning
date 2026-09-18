"""One inherited pilot lifetime, four exact-device bounded stage sequences."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu.orch_l2_rich_math_bootstrap import read, write, sha, SCANNER_SHA
from gpu.orch_l2_rich_math_run import DEVICES
from organism_v6 import orch_l2_rich_math as policy


SERVICES_SHA = 'ed2c9111a50b09bdf20859d3395769945b79ce8ba1f5554ed7fe55b99cfd5117'


def start_ticks(pid):
    return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]


def stop(child, identity):
    if child.poll() is None:
        assert Path(f'/proc/{child.pid}').stat().st_uid == os.getuid()
        assert start_ticks(child.pid) == identity
        child.send_signal(signal.SIGKILL)
        child.wait()


def sequence(root, arm):
    prepared, publication = read(root / 'LANE_PREPARE.json'), read(root / 'LANE_PUBLICATION.json')
    assert publication['prepare_sha256'] == sha(root / 'LANE_PREPARE.json') and publication['cpu_tests_passed']
    assert sha(root / 'scanner.py') == SCANNER_SHA and sha(root / 'node2_service_exceptions.json') == SERVICES_SHA
    deadline = read(root / 'LIFETIME.json')['deadline_unix']
    guardian = root / (arm + '_GUARD')
    guardian.mkdir(exist_ok=False)
    started = time.time()
    device, uuid = DEVICES[arm]
    stages = [('readout', 0)]
    for cycle in (1, 2, 3):
        if arm != 'BOOTSTRAP_OFF':
            stages.extend([('experience', cycle), ('sleep', cycle)])
        stages.append(('readout', cycle))
    child, identity = None, None
    status, error = 'FAILED', None
    try:
        for phase, cycle in stages:
            assert time.time() < deadline
            for attempt in range(4):
                with (root / 'node2_service_exceptions.json').open() as services:
                    scanned = subprocess.run(['python3', str(root / 'scanner.py'), str(device), uuid],
                        stdin=services, capture_output=True, text=True, timeout=40,
                        env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
                report = json.loads(scanned.stdout)
                write(guardian / f'{cycle}_{phase}_SCAN_{attempt}.json', report)
                if scanned.returncode == 0 and report['clear']:
                    break
                if report.get('owners') or not report.get('unresolved') or any(
                        item.get('comm') not in ('sshd', 'sftp-server') for item in report['unresolved']):
                    raise ValueError('physical_admission_failed_no_waiver')
                time.sleep(2)
            else:
                raise ValueError('transport_scan_unresolved')
            with (guardian / f'{cycle}_{phase}.log').open('x') as log:
                child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_l2_rich_math_run',
                    '--root', str(root), '--arm', arm, '--phase', phase, '--cycle', str(cycle)],
                    cwd=root / 'source_lanes', env=dict(os.environ, CUDA_VISIBLE_DEVICES=uuid), stdout=log, stderr=subprocess.STDOUT)
                identity = start_ticks(child.pid)
                write(guardian / f'{cycle}_{phase}_LAUNCH.json', dict(pid=child.pid, start_ticks=identity,
                    device=device, uuid=uuid, started_unix=time.time(), deadline_unix=deadline))
                assert child.wait(timeout=max(1, deadline - time.time())) == 0, 'stage_failed_no_retry'
        status = 'COMPLETE'
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
        raise
    finally:
        if child is not None:
            stop(child, identity)
        write(guardian / 'TERMINAL.json', dict(status=status, error=error, arm=arm,
            started_unix=started, finished_unix=time.time(), assigned_gpu_hours=(time.time() - started) / 3600))


def launch(root):
    assert read(root / 'BOOTSTRAP_TERMINAL.json')['a100_device3_released']
    assert not (root / 'LANES_STARTED.json').exists()
    lifetime = read(root / 'LIFETIME.json')
    assert time.time() < lifetime['deadline_unix']
    write(root / 'LANES_STARTED.json', dict(started_unix=time.time(), inherited_lifetime=lifetime,
                                          owned_devices=DEVICES))
    children = []
    try:
        for arm in policy.ARMS:
            log = (root / (arm + '_guardian.log')).open('x')
            child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_l2_rich_math_guard',
                'sequence', '--root', str(root), '--arm', arm], cwd=root / 'source_lanes',
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), stdout=log, stderr=subprocess.STDOUT)
            children.append((child, start_ticks(child.pid), log))
        for child, unused, log in children:
            child.wait(timeout=max(1, lifetime['hard_deadline_unix'] - time.time()))
    finally:
        for child, identity, log in children:
            stop(child, identity)
            log.close()
        terminals = [read(root / (arm + '_GUARD') / 'TERMINAL.json') for arm in policy.ARMS
                     if (root / (arm + '_GUARD') / 'TERMINAL.json').exists()]
        gpu_hours = read(root / 'BOOTSTRAP_TERMINAL.json')['assigned_gpu_hours'] + sum(row['assigned_gpu_hours'] for row in terminals)
        write(root / 'PILOT_TERMINAL.json', dict(status='COMPLETE' if len(terminals) == 4 and
            all(row['status'] == 'COMPLETE' for row in terminals) else 'INCOMPLETE',
            lane_terminals=terminals, aggregate_assigned_gpu_hours=gpu_hours, finished_unix=time.time(),
            within_gpu_cap=gpu_hours <= policy.GPU_HOURS, lifetime=lifetime))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('launch', 'sequence'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--arm', choices=policy.ARMS)
    options = parser.parse_args()
    root = options.root.resolve()
    assert root == Path('/localhome/local-rohing/orch_l2_rich_math_20260915_attempt1')
    if options.phase == 'launch':
        launch(root)
    else:
        sequence(root, options.arm)


if __name__ == '__main__':
    main()
