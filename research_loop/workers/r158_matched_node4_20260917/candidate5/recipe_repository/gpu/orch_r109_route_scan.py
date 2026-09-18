"""Exact owned lane adapter to existing full privileged inventory scanners."""

import argparse
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

from gpu import orch_rich_hot_a100_minor_scan as minor
from gpu import orch_rich_hot_node1_scan as node1
from gpu import orch_r110_admission as argv_identity
from organism_v6 import orch_r109_route as policy


def bind(lane):
    policy.allocation(lane)
    entry = policy.LANES[lane]
    minor.pinned.policy = SimpleNamespace(HOST_SHA=policy.HOSTS[entry['host']]['sha256'],
        DEVICES={entry['physical']:entry['uuid']}, require=policy.require,
        allocation=lambda index: policy.require(index == entry['physical'], 'owned_physical_only'))
    return entry


def scan(lane, service):
    entry = bind(lane)
    if os.geteuid() != 0:
        result = subprocess.run(['sudo','-n','env','CUDA_VISIBLE_DEVICES=',
            'PYTHONDONTWRITEBYTECODE=1','PYTHONPATH='+str(Path(__file__).resolve().parents[1]),
            'python3','-B','-m','gpu.orch_r109_route_scan','scan','--lane',lane,'--service',str(service)],
            capture_output=True, text=True, check=True, timeout=90)
        return json.loads(result.stdout)
    return node1.scan(entry['physical'], service) if entry['host'] == 'node1' else argv_identity.scan(entry['physical'], service)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('scan','service'))
    parser.add_argument('--lane', required=True, choices=policy.LANES)
    parser.add_argument('--service', required=True, type=Path)
    args = parser.parse_args()
    entry = bind(args.lane)
    if args.phase == 'service':
        (node1.service if entry['host'] == 'node1' else minor.pinned.service)(args.service)
    else:
        print(json.dumps(scan(args.lane,args.service)))
