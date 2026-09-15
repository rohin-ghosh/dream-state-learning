"""New physical1/5 scope over the existing full privileged UUID/minor scanner."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from gpu import orch_rich_hot_a100_minor_scan as minor
from organism_v6 import orch_r107_route_parent_r108 as policy


def bind():
    minor.pinned.policy = policy


def scan(index, service):
    policy.allocation(index)
    if os.geteuid() != 0:
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
            'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]),
            'python3', '-B', '-m', 'gpu.orch_r107_route_parent_r108_scan', 'scan',
            '--index', str(index), '--service', str(service)], text=True, capture_output=True,
            timeout=90, check=True)
        return json.loads(result.stdout)
    bind()
    return minor.scan(index, service)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('service', 'scan'))
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=(2, 3, 6))
    options = parser.parse_args()
    bind()
    if options.phase == 'service':
        minor.pinned.service(options.service)
    else:
        print(json.dumps(scan(options.index, options.service)))
