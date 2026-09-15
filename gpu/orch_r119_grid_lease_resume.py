"""New execution era: tested FP32 learned fork and explicit lease headroom."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import orch_r119_grid_lease_budget as budget


PINS = {
    'orch_r119_grid_a40r7_continue.py': '46c7f7ddbe5fa29892d221adf42798f5a523a0f1af718b141e7d8aef193611ac',
    'orch_r119_grid_learned_fork.py': '20f403f51196a024e817ca2dc75dda69121768eda66e71da624e15cf3e1c401f',
}


def load_adapter(physical):
    name = 'orch_r119_grid_a40r7_continue.py' if physical == 6 else 'orch_r119_grid_learned_fork.py'
    path = HERE / name
    raw = path.read_bytes()
    budget.require(hashlib.sha256(raw).hexdigest() == PINS[name], 'frozen_predecessor_source')
    module = importlib.util.module_from_spec(importlib.util.spec_from_file_location('r119_lease_adapter', path))
    text = raw.decode()
    if physical == 7:
        budget.require(text.count('autocast_adapter_dtype=False') == 1, 'exact_dtype_repair_site')
        text = text.replace('autocast_adapter_dtype=False', 'autocast_adapter_dtype=True')
    exec(compile(text, str(path), 'exec'), module.__dict__)
    return module


def runtime(args):
    adapter = load_adapter(args.physical)
    base = adapter.load_base() if args.physical == 6 else adapter.load_runtime()
    original = adapter.configure if args.physical == 6 else base.configure
    era = 'lease_budget_r119_base' if args.physical == 6 else 'lease_budget_r119_learned'
    terminal = 'R119_LEASE_BASE_TERMINAL.json' if args.physical == 6 else 'R119_LEASE_LEARNED_TERMINAL.json'
    adapter.ERA, adapter.__file__ = era, __file__

    def configure(arguments):
        module, grid, root, config = original(arguments)
        if arguments.physical == 7:
            failure = grid.read(root / 'R119_LEARNED_GRID_TERMINAL.json')
            probe = grid.read(root / 'learned_fork_r119/CPU_DTYPE_REPAIR_PROBE.json')
            budget.require(failure['status'] == 'FAILED' and probe['status'] == 'PASS'
                and probe['observed'] == probe['expected'] and not probe['cuda_initialized']
                and probe['model_inputs_dispatched'] == 0, 'preserved_failure_exact_CPU_identity')
        authorization = root / era / 'LEASE_BUDGET.json'
        ledger = (root / 'LEDGER.jsonl').read_bytes()
        rows = [json.loads(line) for line in ledger.splitlines() if line]
        values = dict(root=root, ledger_bytes=ledger, rows=rows,
            config_sha256=grid.sha(root / 'CONFIG.json'), lease_end=module.LEASE_END, hard_end=grid.END)
        if arguments.mode == 'authorize':
            grid.write(authorization, budget.authorize(**values, now=time.time()))
        document = grid.read(authorization)
        caps = budget.validate(document, **values)
        grid.MAX_NATIVE, grid.MAX_PARENT = caps['NATIVE'], caps['PARENT']
        original_write = grid.write

        def write(path, value, replace=False):
            if Path(path) == root / era / 'BROKER_CONFIG.json':
                value = dict(value, max_parent_calls=caps['PARENT'])
            if Path(path) == root / era / 'CPU_READY.json':
                value = dict(value, lease_budget=grid.ref(authorization), historical_caps=budget.HISTORICAL,
                    readout_policy='NO_FINAL_REARM; explicit prospective lease headroom; cumulative charges unchanged')
            return original_write(path, value, replace=replace)

        grid.write = write
        return module, grid, root, config

    base.configure = configure
    base.__file__, base.ERA, base.TERMINAL = __file__, era, terminal
    return base, adapter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('authorize', 'cpu', 'guard', 'native', 'service', 'scan'))
    parser.add_argument('--physical', type=int, choices=(6, 7), required=True)
    parser.add_argument('--old-source', type=Path, required=True)
    args = parser.parse_args()
    base, adapter = runtime(args)
    if args.mode in ('authorize', 'service', 'scan'):
        module, grid, root, config = base.configure(args)
        if args.mode == 'service':
            budget.require(args.physical == 6, 'a40r_service_only')
            grid.admission.minor.pinned.policy = SimpleNamespace(DEVICES={7: adapter.UUID},
                HOST_SHA=adapter.HOST_SHA, require=grid.require,
                allocation=lambda physical: grid.require(physical == 7, 'assigned7'))
            grid.admission.minor.pinned.service(root / base.ERA / 'SERVICE_IDENTITY.json')
        elif args.mode == 'scan':
            print(json.dumps(module.scan(root)))
        else:
            print(json.dumps(grid.ref(root / base.ERA / 'LEASE_BUDGET.json')))
    else:
        result = getattr(base, args.mode)(args)
        if result is not None:
            print(json.dumps(result))


if __name__ == '__main__':
    main()
