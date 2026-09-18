"""Scoped physical4/5/7 binding of the existing privileged pinned scanner."""

import argparse
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

from gpu import orch_rich_hot_a100_minor_scan as minor
from organism_v6.orch_guided_bridge import require
from organism_v6 import orch_math_pipeline_l2 as policy


def bind():
    devices = dict(policy.DEVICES.values())
    def allocation(index):
        require(index in devices, 'only_current_assigned_device')
        return devices[index]
    minor.pinned.policy = SimpleNamespace(DEVICES=devices, HOST_SHA=policy.HOST_SHA,
        allocation=allocation, require=require)


def scan(index, service_path, timeout_seconds=60):
    assert index in dict(policy.DEVICES.values())
    if os.geteuid() != 0:
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
            'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]),
            'python3', '-B', '-m', 'gpu.orch_math_pipeline_l2_scan', 'scan',
            '--index', str(index), '--service', str(service_path)],
            capture_output=True, text=True, timeout=timeout_seconds, check=True)
        return json.loads(result.stdout)
    bind()
    return minor.scan(index, service_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('service', 'scan'))
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--index', type=int)
    options = parser.parse_args()
    bind()
    if options.phase == 'service':
        minor.pinned.service(options.service)
    else:
        print(json.dumps(scan(options.index, options.service), indent=2))
