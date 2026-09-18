"""Read-only privileged node2 full-process admission for the eight owned UUIDs."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from gpu import orch_l2_budget_readout_scan as adapter
from organism_v6 import orch_rich_hot_node2 as policy


def scan(index, service_path, timeout_seconds=45):
    policy.require(index in range(8), 'only_node2_physical0_to7')
    if os.geteuid() != 0:
        result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]), 'python3', '-B', '-m',
            'gpu.orch_rich_hot_node2_scan', 'scan', '--index', str(index), '--service', str(service_path)],
            capture_output=True, text=True, timeout=timeout_seconds, check=True)
        return json.loads(result.stdout)
    adapter.policy = policy
    return adapter.scan(index, service_path, timeout_seconds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('service', 'scan'))
    parser.add_argument('--index', type=int)
    parser.add_argument('--service', type=Path, required=True)
    options = parser.parse_args()
    if options.phase == 'service':
        adapter.service(options.service)
    else:
        print(json.dumps(scan(options.index, options.service), indent=2))
