"""Scoped route recovery dispatch with the tested one-MiB idle reconciliation."""

import argparse
import json
import os
from pathlib import Path
import subprocess
from types import FunctionType, SimpleNamespace

from gpu import orch_r111_route_recovery as recovery
from gpu import orch_r111_route_admission as idle


def scan(lane, service):
    recovery.old.policy.require(lane == 'node3_3', 'only_owned_node3_recovery')
    entry = recovery.old.admission.bind(lane)
    if os.geteuid() != 0:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                   'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]), 'python3', '-B',
                   '-m', 'gpu.orch_r118_route_dispatch', 'scan', '--lane', lane, '--service', str(service)]
        return json.loads(subprocess.check_output(command, text=True, timeout=100))
    return idle.scan(entry['physical'], service)


def guard(root, lane):
    recovery.old.policy.require(lane == 'node3_3', 'only_owned_node3_recovery')
    original = recovery.old.guard
    replacement = FunctionType(original.__code__, dict(original.__globals__,
                               admission=SimpleNamespace(scan=scan)), original.__name__)
    previous = recovery.old.guard
    try:
        recovery.old.guard = replacement
        return recovery.guard(root, lane)
    finally:
        recovery.old.guard = previous


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('scan', 'guard'))
    parser.add_argument('--lane', choices=('node3_3',), required=True)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--service', type=Path)
    args = parser.parse_args()
    if args.phase == 'scan':
        print(json.dumps(scan(args.lane, args.service)))
    else:
        guard(args.root, args.lane)
