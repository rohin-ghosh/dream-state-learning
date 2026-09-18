"""Move the exact released BASE context life onto assigned a40r physical7."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from types import SimpleNamespace


HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
UUID = 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98'
LEASE_PATH = Path('/localhome/local-rohing/orch_rich_hot_node1_20260915_exhaustion_v1/LEASE.json')
LEASE_SHA = 'ac20665cb03ba0e2f8eebb0f7e441383334fbbf20b4a4e7125757ce7413ea8e6'
ROOT = Path('/localhome/local-rohing/orch_r118_node3_6_grid_20260915_attempt1')
ERA = 'migration_a40r7_r119'
BASE_SOURCE_SHA = '9de64111bc02c2db61050e36aa244bc8c558440b7682ac8699f4590515d9439b'


def load_base():
    path = Path(__file__).with_name('orch_r119_grid_continuation.py')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == BASE_SOURCE_SHA
    spec = importlib.util.spec_from_file_location('r119_frozen_continuation', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lease_wall(document):
    assert document['margin_seconds'] >= 21600 and document['no_extension_or_new_onboarding'] is True
    expiry = datetime.fromisoformat(document['conservative_lease_end_utc']).timestamp()
    assert expiry == datetime(2026, 9, 19, tzinfo=timezone.utc).timestamp()
    return expiry, expiry-document['margin_seconds']


def configure(args):
    source = Path(args.old_source).resolve(strict=True)
    sys.path.insert(0, str(source))
    old = importlib.import_module('gpu.orch_r118_node3_6_grid_run')
    grid = old.grid
    require = grid.require
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA,
            'only_assigned_a40r_node')
    require(grid.sha(LEASE_PATH) == LEASE_SHA, 'actual_a40r_lease_bytes')
    expiry, wall = lease_wall(grid.read(LEASE_PATH))
    config = grid.read(ROOT / 'CONFIG.json')
    require(config['root'] == str(ROOT) and config['physical'] == 6 and config['uuid'] == old.UUID,
            'unchanged_migrated_predecessor_CONFIG')
    require(grid.sha(source / old.MANIFEST) == config['source_manifest_sha256'], 'original_manifest')
    for name, digest in grid.read(source / old.MANIFEST).items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and grid.sha(source / name) == digest, 'original_source:' + name)
    for name, digest in config['inputs'].items():
        require(grid.sha(ROOT / name) == digest, 'original_input:' + name)
    release = grid.read(ROOT / 'continuation_r119_1710/SCOPED_SETTLED_RELEASE.json')
    require(release['pid'] == 2276639 and release['all_charged_current_TRAIN_and_parents_terminal']
            and release['ledger_sha256'] == '8cc0a654bbd48e6c3eb04e48c383ffc6382c3f283f3ede3ec048c50a79f39e43',
            'actual_released_predecessor_no_concurrent_life')
    require(config['base_sha256'] == grid.policy.game.BASE_SHA and config['optimizer_steps'] == 0,
            'same_frozen_BASE_not_learned_claim')
    grid.END, grid.TRAIN_END = wall, wall-300
    original = grid.policy.queue_request

    def queue(*values, **kwargs):
        request = original(*values, **kwargs)
        request['lane_deadline_unix'] += 480
        return request

    grid.policy.queue_request = queue
    require(grid.time.time() < grid.TRAIN_END, 'lease_margin_remaining')

    def allocation(physical):
        require(physical == 7, 'only_assigned_physical7')

    def scan(root):
        require(root == ROOT, 'migrated_same_root')
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'python3', '-B', str(Path(__file__).resolve()), 'scan', '--physical', '6',
            '--old-source', str(source)]
        if os.geteuid() != 0:
            return json.loads(subprocess.check_output(command, text=True, timeout=100))
        grid.admission.minor.pinned.policy = SimpleNamespace(DEVICES={7: UUID}, HOST_SHA=HOST_SHA,
            require=require, allocation=allocation)
        return old.idle_baseline.scan(7, ROOT / ERA / 'SERVICE_IDENTITY.json')

    return SimpleNamespace(UUID=UUID, LEASE_END=expiry, scan=scan), grid, ROOT, dict(config,
        physical=7, uuid=UUID, lease_end_unix=expiry, hard_end_unix=wall, train_end_unix=wall-300)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('cpu', 'service', 'scan', 'guard', 'native'))
    parser.add_argument('--physical', type=int, choices=(6,), required=True)
    parser.add_argument('--old-source', type=Path, required=True)
    args = parser.parse_args()
    base = load_base()
    base.__file__ = __file__
    base.ERA, base.TERMINAL = ERA, 'R119_A40R7_CONTINUATION_TERMINAL.json'
    base.configure = configure
    if args.mode == 'service':
        module, grid, root, config = configure(args)
        grid.admission.minor.pinned.policy = SimpleNamespace(DEVICES={7: UUID}, HOST_SHA=HOST_SHA,
            require=grid.require, allocation=lambda physical: grid.require(physical == 7, 'assigned7'))
        grid.admission.minor.pinned.service(root / ERA / 'SERVICE_IDENTITY.json')
    elif args.mode == 'scan':
        module, grid, root, config = configure(args)
        print(json.dumps(module.scan(root)))
    else:
        result = getattr(base, args.mode)(args)
        if result is not None:
            print(json.dumps(result))


if __name__ == '__main__':
    main()
