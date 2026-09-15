"""Exact node5 physical2/6 admission and finite owned native custody."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import orch_r110_admission as admission
from gpu import orch_rich_hot_a100_minor_scan as scanner
from gpu import orch_r108_code_parent_r115_run as run


HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
DEVICES = {2: 'GPU-d62ba12e-ff08-9e5e-ba35-14c723f6e05b', 6: 'GPU-67a989f7-2660-a76b-40e8-3619b9fa2987'}


def bind(index):
    run.policy.require(index in DEVICES, 'own_f3_physical2_6_only')
    def allocation(physical):
        run.policy.require(physical == index, 'exact_f3_slot')
        return DEVICES[physical]
    scanner.pinned.policy = SimpleNamespace(DEVICES={index: DEVICES[index]}, HOST_SHA=HOST_SHA,
        require=run.policy.require, allocation=allocation)
    run.policy.require(scanner.pinned.host_identity() == HOST_SHA, 'hashed_node5_identity')


def verify(root):
    plan = run.read(root / 'PLAN.json')
    bind(plan['physical'])
    run.policy.require(plan['gpu_uuid'] == DEVICES[plan['physical']], 'plan_gpu_uuid')
    for relative, expected in run.read(root / 'SOURCE_SHA256.json').items():
        run.policy.require(run.sha(root / 'source' / relative) == expected, 'immutable_native_source')
    run.policy.require(plan['authorized'] == 'R115_WATCHER_RELAYED_ROHIN_DONE', 'actual_user_done_required')
    run.policy.require(plan['hard_deadline_unix'] - plan['started_unix'] <= 8 * 3600
        and plan['hard_deadline_unix'] <= plan['lease_end_unix'] - 21600, 'finite_lease_bound')
    run.policy.require(plan['native_cap'] == 8192 and plan['parent_cap'] == 1000 and plan['cycles'] == 100,
        'new_distinct_fixed_quotas')
    run.policy.require(run.read(root / 'CPU_READY.json')['passed'] is True, 'own_three_prelaunch_tests')
    return plan


def scan(root):
    plan = run.read(root / 'PLAN.json')
    bind(plan['physical'])
    if os.geteuid() == 0:
        return admission.scan(plan['physical'], root / 'SERVICE_IDENTITY.json')
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(root / 'source'), 'python3', '-B', '-m', 'gpu.orch_r108_code_parent_r115_guard',
        'scan', '--root', str(root)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=True)
    return json.loads(result.stdout)


def guard(root):
    plan = verify(root)
    run.policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_guard_only')
    (root / 'GUARD_ONCE').mkdir()
    if plan['physical'] == 6:
        release = run.read(root / 'PREDECESSOR_RELEASE.json')
        run.policy.require(release.get('explicit_owner_release') is True and release.get('physical') == 6,
            'laplace_explicit_release_required')
    lock = Path('/tmp') / ('orch_r115_f3_' + plan['gpu_uuid'] + '.lock')
    with lock.open('a') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        snapshot = None
        for attempt in range(20):
            snapshot = scan(root)
            run.write_new(root / 'admission' / f'SCAN_{attempt:03d}.json', snapshot)
            if snapshot.get('clear') is True:
                break
            time.sleep(15)
        run.policy.require(snapshot and snapshot['clear'] is True and snapshot['scanner_euid'] == 0
            and snapshot['gpu']['uuid'] == plan['gpu_uuid'] and 'device_minor' in snapshot, 'strict_privileged_admission')
        run.write_new(root / 'ADMISSION.json', snapshot)
        with (root / 'native.log').open('x') as log:
            child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_r108_code_parent_r115_run',
                'native', '--root', str(root)], cwd=root / 'source', stdout=log, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, start_new_session=True,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid'], PYTHONPATH=str(root / 'source'),
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
            identity = scanner.pinned.identity(Path('/proc') / str(child.pid))
            run.write_new(root / 'LAUNCH.json', dict(identity=identity, started_unix=time.time(),
                plan_sha256=run.sha(root / 'PLAN.json'), admission_sha256=run.sha(root / 'ADMISSION.json')))
            while child.poll() is None and time.time() < plan['hard_deadline_unix'] - 5:
                time.sleep(2)
            if child.poll() is None:
                run.policy.require(scanner.pinned.identity(Path('/proc') / str(child.pid)) == identity,
                    'exact_owned_identity_before_stop')
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=20)
            run.write_new(root / 'GUARD_TERMINAL.json', dict(finished_unix=time.time(), returncode=child.returncode,
                completed=(root / 'COMPLETE.json').exists(), exact_identity=identity))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('service', 'scan', 'guard'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.phase == 'service':
        bind(run.read(args.root / 'PLAN.json')['physical'])
        scanner.pinned.service(args.root / 'SERVICE_IDENTITY.json')
    elif args.phase == 'scan':
        print(json.dumps(scan(args.root), sort_keys=True))
    else:
        guard(args.root)
