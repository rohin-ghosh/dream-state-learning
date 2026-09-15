"""Successor portability binding; reuse tested A1004 logic without editing it."""

import argparse
import json
import os
from pathlib import Path
import subprocess
from types import FunctionType, SimpleNamespace

from gpu import orch_r118_a1004_grid_run as template
from gpu import orch_r111_route_admission as idle_baseline


ROOT = Path('/localhome/local-rohing/orch_r118_node3_6_grid_20260915_attempt1')
SOURCE = Path(__file__).resolve().parents[1]
HOST_SHA = '3e10ebcb89f013079c1e088fa82820188b1a805b879ebb85a7ffeb689e7b86e9'
UUID = 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8'
LEASE_END = 1789689600.0
LIFE_ID = 'R118_NODE3_6_ASTRA'
MANIFEST = 'R118_NODE3_6_SOURCE_SHA256.json'
grid, require = template.grid, template.require


def allocation(physical):
    require(physical == 6, 'only_explicitly_allocated_node3_physical6')


def command(mode, root, *extra):
    return [grid.PYTHON, '-B', '-m', 'gpu.orch_r118_node3_6_grid_run', mode,
            '--root', str(root), *extra]


def scan(root):
    require(root == ROOT, 'exact_new_root')
    if os.geteuid() != 0:
        argv = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(SOURCE), 'python3', '-B', '-m', 'gpu.orch_r118_node3_6_grid_run',
            'scan', '--root', str(root)]
        return json.loads(subprocess.check_output(argv, text=True, timeout=100))
    grid.admission.minor.pinned.policy = SimpleNamespace(DEVICES={6: UUID}, HOST_SHA=HOST_SHA,
        require=require, allocation=allocation)
    return idle_baseline.scan(6, root / 'SERVICE_IDENTITY.json')


def bound_functions():
    namespace = dict(template.__dict__, ROOT=ROOT, SOURCE=SOURCE, HOST_SHA=HOST_SHA,
        UUID=UUID, LEASE_END=LEASE_END, LIFE_ID=LIFE_ID, MANIFEST=MANIFEST,
        allocation=allocation, command=command, scan=scan)
    for name in ('validate', 'spawn_readout', 'prepare', 'guard'):
        original = getattr(template, name)
        code = original.__code__
        if name == 'prepare':
            require(sum(type(value) is int and value == 4 for value in code.co_consts) == 1
                    and code.co_consts.count('R118_A1004_GRID_V1') == 1, 'exact_template_portability_constants')
            constants = tuple(6 if type(value) is int and value == 4 else
                'R118_NODE3_6_GRID_V1' if value == 'R118_A1004_GRID_V1' else value
                for value in code.co_consts)
            code = code.replace(co_consts=constants)
        namespace[name] = FunctionType(code, namespace, name, original.__defaults__)
    return namespace


_bound = bound_functions()
validate, spawn_readout, prepare, guard = (_bound[name] for name in
                                         ('validate', 'spawn_readout', 'prepare', 'guard'))


def install_portability():
    grid.validate = validate
    grid.spawn_readout = spawn_readout


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'scan', 'guard', 'resident', 'readout'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cycle', type=int)
    parser.add_argument('--scope')
    args = parser.parse_args()
    install_portability()
    if args.mode in ('prepare', 'scan'):
        print(json.dumps((prepare if args.mode == 'prepare' else scan)(args.root), sort_keys=True))
    elif args.mode == 'readout':
        grid.readout(args.root, args.cycle, args.scope)
    else:
        (guard if args.mode == 'guard' else grid.resident)(args.root)
