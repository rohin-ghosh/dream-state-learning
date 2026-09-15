"""Continue the completed C8 TRAIN state; preserve its failed DEV and all charges."""

import argparse
import gc
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r118_node3_6_grid_run as previous


ROOT = previous.ROOT
SOURCE = Path(__file__).resolve().parents[1]
ERA = 'recovery_1336_v1'
TERMINAL = 'R118_NODE3_6_RECOVERY_TERMINAL.json'
OLD_TERMINAL_SHA = '7f68c9cf541fa2d3d10c78f8ebfa48ebfbc78afd436d2272b387aaa783444b7c'
LEDGER_SHA = '575d4b0b0ce53acfdec29672f15b9aa51db721531a86c26092e97930968e6ead'
CARRY_SHA = 'fc2d28473eac4991ccc400fa13531d29c69f0122a516b3cbbfcead56ccdd6a50'
TRAIN_SHA = '3dace6b75475a44db09999d0d09a3ad80aabb6d0b72fd0e4d23c3063c68c403d'
grid, require = previous.grid, previous.require


def ledger():
    return [json.loads(line) for line in (ROOT / 'LEDGER.jsonl').read_text().splitlines() if line]


def train_charge(item):
    return item['kind'] == 'NATIVE' and item['split'] == 'TRAIN' and not item.get('attached_readout', False)


def initial_state():
    require(grid.sha(ROOT / 'TERMINAL.json') == OLD_TERMINAL_SHA, 'preserve_old_FAILED_terminal')
    require(grid.sha(ROOT / 'LEDGER.jsonl') == LEDGER_SHA and grid.sha(ROOT / 'CARRY.json') == CARRY_SHA,
            'exact_unmodified_failed_life_state')
    require(grid.sha(ROOT / 'cycles/0008/TRAIN_COMPLETE.json') == TRAIN_SHA, 'actual_C8_TRAIN_complete')
    require(grid.read(ROOT / 'CARRY.json') == grid.read(ROOT / 'cycles/0008/TRAIN_COMPLETE.json')['carry'],
            'exact_inherited_context_memory')
    rows = ledger()
    for kind, expected in (('NATIVE', 558), ('PARENT', 40)):
        require([item['number'] for item in rows if item['kind'] == kind] == list(range(1, expected + 1)),
                'original_contiguous_charge_counters')
    require(max(item['cycle'] for item in rows) == 8 and not (ROOT / 'cycles/0009').exists(), 'next_cycle9_only')
    require((ROOT / 'readouts/0008/dev/STARTED.json').is_file()
            and not (ROOT / 'readouts/0008/dev/COMPLETE.json').exists(), 'failed_DEV_not_retried')
    for item in rows:
        if train_charge(item):
            require(grid.read(ROOT / 'calls' / f'N{item["number"]:05d}.json')['status'] == 'COMPLETE',
                    'no_unfinished_TRAIN_to_replay')
        elif item['kind'] == 'PARENT':
            require((ROOT / 'parent_received' / f'P{item["number"]:04d}.json').is_file(), 'parents_already_disposed')
    return dict(next_cycle=9, inherited_native_charges=558, inherited_parent_charges=40,
                carry=grid.ref(ROOT / 'CARRY.json'), ledger=grid.ref(ROOT / 'LEDGER.jsonl'))


def runtime():
    previous.install_portability()
    previous.validate(ROOT)
    return grid.read(ROOT / 'CONFIG.json')


def cpu_prepare():
    runtime()
    state = initial_state()
    require(all(not Path('/proc', str(pid)).exists() for pid in (2107612, 2107861, 2107862)),
            'old_guard_timeout_native_gone_no_signals')
    folder = ROOT / ERA
    preserved = {}
    for path in ROOT.rglob('*.json'):
        if not path.is_relative_to(folder):
            preserved[str(path.relative_to(ROOT))] = grid.sha(path)
    grid.write(folder / 'INHERITED_CARRY.json', grid.read(ROOT / 'CARRY.json'))
    grid.write(folder / 'CPU_READY.json', dict(status='PASS', state=state, preserved_files=preserved,
        old_terminal_sha256=OLD_TERMINAL_SHA, terminal_filename=TERMINAL,
        source=grid.ref(Path(__file__)), model_calls=0, provider_calls=0, optimizer_steps=0,
        readout_retries=0, hard_end_unix=grid.END, train_end_unix=grid.TRAIN_END,
        max_native_calls=grid.MAX_NATIVE, max_parent_calls=grid.MAX_PARENT, observed_unix=time.time()))
    return grid.ref(folder / 'CPU_READY.json')


def offloaded_readout(engine, callback, collect=gc.collect):
    engine.verify_base()
    engine.model.to('cpu')
    collect()
    engine.torch.cuda.empty_cache()
    try:
        return callback()
    finally:
        engine.model.to('cuda:0')
        engine.verify_base()


def native():
    config = runtime()
    previous.validate(ROOT, gpu=True)
    state = initial_state()
    folder = ROOT / ERA
    engine = grid.load_engine(config)
    grid.write(folder / 'LOADED.json', dict(pid=os.getpid(), loaded_unix=time.time(),
        base_sha256=engine.loaded_base_sha256, no_adapter=engine.no_adapter, optimizer_steps=0,
        next_cycle=state['next_cycle'], inherited_native_charges=558, inherited_parent_charges=40,
        inherited_carry=grid.ref(ROOT / 'CARRY.json')))
    roster = grid.read(ROOT / 'TRAIN.json')
    cycle = state['next_cycle']
    while time.time() < grid.TRAIN_END:
        rows = ledger()
        if sum(item['kind'] == 'NATIVE' for item in rows) > grid.MAX_NATIVE - 120 or sum(
                item['kind'] == 'PARENT' for item in rows) > grid.MAX_PARENT - 6:
            grid.write(folder / 'BUDGET_TRAIN_END.json', dict(cycle=cycle, observed_unix=time.time(), refill=False))
            break
        life = grid.Life(ROOT, engine, config, cycle)
        tasks = [roster[(cycle - 1) % 8], roster[8 + (cycle - 1) % 8]]
        try:
            grid.train_cycle(life, tasks, grid.read(ROOT / 'CARRY.json'))
        except grid.TrainWindowClosed as error:
            grid.write(ROOT / 'cycles' / f'{cycle:04d}' / 'CLOCK_BOUNDARY.json', dict(
                reason=str(error), partial_cycle=True, all_completed_calls_preserved=True, optimizer_steps=0))
            break
        offloaded_readout(engine, lambda: previous.spawn_readout(ROOT, cycle, 'dev'))
        grid.write(ROOT / 'cycles' / f'{cycle:04d}' / 'CYCLE_COMPLETE.json', dict(cycle=cycle,
            optimizer_steps=0, mode='ELICITATION_ONLY_SYSTEMS', finished_unix=time.time()))
        cycle += 1
    engine.verify_base()
    engine.model.to('cpu')
    gc.collect()
    engine.torch.cuda.empty_cache()
    while time.time() < grid.policy.FINAL_UNIX:
        time.sleep(max(0, min(5, grid.policy.FINAL_UNIX - time.time())))
    previous.spawn_readout(ROOT, cycle, 'final_morning')
    grid.write(folder / 'COMPLETE.json', dict(finished_unix=time.time(), optimizer_steps=0, last_cycle=cycle))


def guard():
    runtime()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard')
    folder = ROOT / ERA
    (folder / 'GUARD_ONCE').mkdir()
    try:
        ready = grid.read(folder / 'CPU_READY.json')
        require(ready['source'] == grid.ref(Path(__file__)) and ready['status'] == 'PASS', 'frozen_CPU_ready')
        require(grid.read(folder / 'PUBLICATION.json')['dated_builder'], 'dated_Builder_preGPU')
        initial_state()
        require(all(not Path('/proc', str(pid)).exists() for pid in (2107612, 2107861, 2107862)), 'no_old_owner_active')
        for attempt in range(120):
            report = previous.scan(ROOT)
            grid.write(folder / 'admission' / f'{attempt:03d}.json', report)
            if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
                require(report['gpu']['uuid'] == previous.UUID, 'exact_GPU6')
                break
            require(time.time() < grid.TRAIN_END, 'no_new_training_after_original_deadline')
            time.sleep(2)
        else:
            raise ValueError('fresh_full_admission_failed_no_waiver')
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=previous.UUID, PYTHONPATH=str(SOURCE),
            PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        command = ['timeout', '--signal=TERM', '--kill-after=5s', str(int(grid.END - time.time() - 5)) + 's',
            grid.PYTHON, '-B', '-m', 'gpu.orch_r118_node3_6_grid_recover', 'native']
        with (folder / 'NATIVE.log').open('x') as log:
            child = subprocess.Popen(command, cwd=SOURCE, env=environment, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        grid.write(folder / 'LAUNCH.json', dict(pid=child.pid, command=command, started_unix=time.time()))
        code = child.wait()
        grid.write(ROOT / TERMINAL, dict(status='COMPLETE' if code == 0 else 'FAILED',
            exit_code=code, finished_unix=time.time(), no_retry=True))
    except BaseException as error:
        if not (ROOT / TERMINAL).exists():
            grid.write(ROOT / TERMINAL, dict(status='FAILED', error_type=type(error).__name__,
                error=str(error), finished_unix=time.time()))
        raise
    finally:
        grid.write(folder / 'FINAL_RELEASE.json', previous.scan(ROOT))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('cpu', 'guard', 'native'))
    args = parser.parse_args()
    if args.mode == 'cpu':
        print(json.dumps(cpu_prepare(), sort_keys=True))
    else:
        (guard if args.mode == 'guard' else native)()
