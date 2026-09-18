"""Same-life TRAIN continuation; cached charged responses never reach a model."""

import argparse
from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import socket
import hashlib
import subprocess
import sys
import time


ERA = 'continuation_r119_1710'
TERMINAL = 'R119_CONTINUATION_TERMINAL.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def clean(value):
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()
                if key not in ('created_unix', 'finished_unix')}
    if isinstance(value, list):
        return [clean(item) for item in value]
    return value


def training(row):
    return row['kind'] == 'PARENT' or (row.get('split') == 'TRAIN'
                                      and not row.get('attached_readout', False))


class CachedBoundary(BaseException):
    pass


def replay_class(grid):
    class ReplayLife(grid.Life):
        def __init__(self, *args, cached, dry=False, **kwargs):
            super().__init__(*args, **kwargs)
            self.cached, self.cursor, self.dry = cached, 0, dry

        def take(self, kind, expected):
            if self.cursor == len(self.cached):
                if self.dry:
                    raise CachedBoundary()
                return None
            item = self.cached[self.cursor]
            require(item['kind'] == kind and all(item.get(key) == value
                    for key, value in expected.items()), 'exact_causal_charge_order')
            self.cursor += 1
            return item

        def calls(self, tasks, purpose, messages, cap, *, attached_readout=False):
            require(not attached_readout and all(task['split'] == 'TRAIN' for task in tasks),
                    'TRAIN_only_no_held_reconstruction')
            require(len(tasks) == len(messages) == 1, 'sequential_dependent_episode')
            row = self.take('NATIVE', dict(task_id=tasks[0]['id'], purpose=purpose,
                                           split='TRAIN', attached_readout=False))
            if row is None:
                return super().calls(tasks, purpose, messages, cap)
            path = self.root / 'calls' / f'N{row["number"]:05d}.json'
            record = grid.read(path)
            require(record['status'] == 'COMPLETE' and record['messages'] == messages[0]
                    and record['cap'] == cap, 'cached_actual_messages_cap_complete')
            response = deepcopy(record['response'])
            response['reference'] = grid.ref(path)
            self.event('child', response['raw'], grid.sha(path))
            return [response]

        def ask(self, task, episode, phase):
            row = self.take('PARENT', dict(task_id=task['id'], phase=phase))
            if row is None:
                return super().ask(task, episode, phase)
            identifier = f'P{row["number"]:04d}'
            path = self.root / 'parent_queue' / (identifier + '.request.json')
            request = grid.read(path)
            regenerated = grid.policy.queue_request(identifier, self.config['life_id'], self.cycle,
                episode, phase, task, self.events, self.config['cohort_sha256'], 0)
            require(request['payload'] == regenerated['payload'], 'cached_exact_parent_context')
            result = grid.read(self.root / 'parent_received' / (identifier + '.json'))
            require(result['request'] == grid.ref(path), 'cached_parent_source_binding')
            if result['reflection_settings']['status'] == 'BOUND_FOR_LANE_DECODER':
                self.settings = result['reflection_settings']
            if result['disposition']['guidance']:
                response = path.with_name(identifier + '.response.json')
                require(result['response'] == grid.ref(response), 'cached_parent_response_binding')
                self.event('parent', result['disposition']['guidance'], grid.sha(response))
            return result
    return ReplayLife


def existing_writer(grid, root, *, dry):
    original = grid.write

    def write(path, value, replace=False):
        path = Path(path)
        if path.exists() and not replace:
            require(path.is_relative_to(root) and clean(grid.read(path)) == clean(value),
                    'preserve_existing_reconstructed_evidence:' + str(path))
            return
        require(not dry, 'CPU_reconstruction_must_not_write:' + str(path))
        original(path, value, replace=replace)
    return write


def configure(args):
    source = Path(args.old_source).resolve(strict=True)
    sys.path.insert(0, str(source))
    module = importlib.import_module(f'gpu.orch_r118_node3_{args.physical}_grid_run')
    grid = module.grid
    root = module.ROOT
    config = grid.read(root / 'CONFIG.json')
    require(args.physical in (6, 7), 'owned_node3_6_7_only')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == module.HOST_SHA,
            'exact_node3_host')
    require(config['physical'] == args.physical and config['uuid'] == module.UUID
            and config['root'] == str(root) and config['life_id'] == module.LIFE_ID,
            'original_life_identity')
    require(config['lease_end_unix'] == module.LEASE_END == 1789689600,
            'actual_pinned_node3_lease')
    require(grid.sha(source / module.MANIFEST) == config['source_manifest_sha256'],
            'original_manifest_unchanged')
    for name, digest in grid.read(source / module.MANIFEST).items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
                and grid.sha(source / name) == digest, 'original_source:' + name)
    for name, digest in config['inputs'].items():
        require(grid.sha(root / name) == digest, 'original_input:' + name)
    require(config['base_sha256'] == grid.policy.game.BASE_SHA and config['optimizer_steps'] == 0,
            'frozen_BASE_context_continuity_not_optimizer_claim')
    grid.END = config['lease_end_unix'] - 21600
    grid.TRAIN_END = grid.END - 300
    require(time.time() < grid.TRAIN_END, 'verified_lease_margin_remaining')
    return module, grid, root, config


def state(grid, root):
    rows = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line]
    for kind in ('NATIVE', 'PARENT'):
        require([row['number'] for row in rows if row['kind'] == kind]
                == list(range(1, sum(row['kind'] == kind for row in rows) + 1)),
                'contiguous_inherited_charge_counters')
    completed = sorted(root.glob('cycles/*/TRAIN_COMPLETE.json'))
    require(bool(completed), 'actual_saved_context_checkpoint')
    previous = grid.read(completed[-1])
    require(grid.read(root / 'CARRY.json') == previous['carry'], 'carry_matches_last_complete_TRAIN')
    cycle = int(completed[-1].parent.name) + 1
    cached = [row for row in rows if row.get('cycle') == cycle and training(row)]
    require(all(row.get('cycle', 0) <= cycle for row in rows), 'no_later_partial_cycle_discard')
    for row in cached:
        folder = 'calls' if row['kind'] == 'NATIVE' else 'parent_received'
        name = f'N{row["number"]:05d}.json' if row['kind'] == 'NATIVE' else f'P{row["number"]:04d}.json'
        value = grid.read(root / folder / name)
        require(row['kind'] != 'NATIVE' or value['status'] == 'COMPLETE', 'no_incomplete_call_retry')
    return rows, cycle, cached, previous['carry']


def tasks_for(roster, cycle):
    return [roster[(cycle - 1) % 8], roster[8 + (cycle - 1) % 8]]


def cpu(args):
    module, grid, root, config = configure(args)
    rows, cycle, cached, memory = state(grid, root)
    preserved = {str(path.relative_to(root)): grid.sha(path) for path in root.rglob('*.json')
                 if ERA not in path.parts and 'sealed' not in str(path.relative_to(root))}
    before = grid.ref(root / 'LEDGER.jsonl')
    original = grid.write
    grid.write = existing_writer(grid, root, dry=True)
    life = replay_class(grid)(root, None, config, cycle, cached=cached, dry=True)
    try:
        grid.train_cycle(life, tasks_for(grid.read(root / 'TRAIN.json'), cycle), memory)
        raise ValueError('expected_next_uncharged_boundary')
    except CachedBoundary:
        require(life.cursor == len(cached), 'all_cached_TRAIN_reconstructed')
    finally:
        grid.write = original
    require(grid.ref(root / 'LEDGER.jsonl') == before, 'CPU_zero_new_charges')
    output = root / ERA
    broker = grid.read(root / 'BROKER_CONFIG.json')
    broker['deadline_unix'] = grid.END
    grid.write(output / 'BROKER_CONFIG.json', broker)
    grid.write(output / 'CPU_READY.json', dict(schema='R119_GRID_CONTINUATION_V1', status='PASS',
        root=str(root), physical=args.physical, uuid=module.UUID, old_source=str(args.old_source),
        source=grid.ref(Path(__file__)), inherited_ledger=before, inherited_carry=grid.ref(root / 'CARRY.json'),
        last_complete=grid.ref(root / 'cycles' / f'{cycle-1:04d}' / 'TRAIN_COMPLETE.json'),
        next_cycle=cycle, reconstructed_rows=len(cached), preserved_files=preserved,
        native_charges=sum(row['kind'] == 'NATIVE' for row in rows),
        parent_charges=sum(row['kind'] == 'PARENT' for row in rows),
        native_cap=grid.MAX_NATIVE, parent_cap=grid.MAX_PARENT,
        lease_end_unix=module.LEASE_END, train_end_unix=grid.TRAIN_END, hard_end_unix=grid.END,
        gpu_launch=False, model_calls=0, provider_calls=0, readout_retries=0,
        readout_policy='NO_FINAL_REARM; continuation TRAIN only within remaining lifetime calls',
        observed_unix=time.time()))
    return grid.ref(output / 'CPU_READY.json')


def check_ready(grid, root):
    ready = grid.read(root / ERA / 'CPU_READY.json')
    require(ready['source'] == grid.ref(Path(__file__)), 'frozen_continuation_source')
    require(ready['inherited_ledger'] == grid.ref(root / 'LEDGER.jsonl')
            and ready['inherited_carry'] == grid.ref(root / 'CARRY.json'), 'exact_initial_continuity')
    for name, digest in ready['preserved_files'].items():
        require(grid.sha(root / name) == digest, 'preserved_predecessor_evidence:' + name)
    return ready


def native(args):
    module, grid, root, config = configure(args)
    ready = check_ready(grid, root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == module.UUID
            and ('CUDA_VISIBLE_DEVICES=' + module.UUID).encode() in
            Path('/proc/self/environ').read_bytes().split(b'\0'), 'initial_exact_GPU_UUID')
    rows, cycle, cached, memory = state(grid, root)
    folder = root / ERA
    engine = grid.load_engine(config)
    grid.write(folder / 'LOADED.json', dict(pid=os.getpid(), observed_unix=time.time(),
        base_sha256=engine.loaded_base_sha256, no_adapter=engine.no_adapter,
        optimizer_steps=0, inherited_carry=ready['inherited_carry'], next_cycle=cycle))
    original_write = grid.write
    grid.write = existing_writer(grid, root, dry=False)
    roster = grid.read(root / 'TRAIN.json')
    while time.time() < grid.TRAIN_END:
        ledger = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line]
        if any(sum(row['kind'] == kind for row in ledger) > cap - reserve
               for kind, cap, reserve in [('NATIVE', grid.MAX_NATIVE, 120), ('PARENT', grid.MAX_PARENT, 6)]):
            original_write(folder / 'BUDGET_STOP.json', dict(cycle=cycle, reason='original_lifetime_caps',
                native_cap=grid.MAX_NATIVE, parent_cap=grid.MAX_PARENT, observed_unix=time.time()))
            break
        life = replay_class(grid)(root, engine, config, cycle, cached=cached)
        try:
            grid.train_cycle(life, tasks_for(roster, cycle), memory)
        except grid.TrainWindowClosed:
            original_write(folder / 'CLOCK_STOP.json', dict(cycle=cycle, observed_unix=time.time()))
            break
        require(life.cursor == len(cached), 'cached_prefix_fully_consumed')
        memory = grid.read(root / 'CARRY.json')
        original_write(folder / f'C{cycle:04d}_CONTINUED.json', dict(cycle=cycle,
            reconstructed_rows=len(cached), carry=grid.ref(root / 'CARRY.json'),
            ledger=grid.ref(root / 'LEDGER.jsonl'), observed_unix=time.time(), optimizer_steps=0))
        cached = []
        cycle += 1


def guard(args):
    module, grid, root, config = configure(args)
    folder = root / ERA
    check_ready(grid, root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard')
    grid.write(folder / 'GUARD_ONCE.json', dict(pid=os.getpid(), observed_unix=time.time()))
    try:
        for attempt in range(30):
            report = module.scan(root)
            grid.write(folder / 'admission' / f'{attempt:03d}.json', report)
            if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
                require(report['gpu']['uuid'] == module.UUID, 'exact_admitted_UUID')
                break
            time.sleep(2)
        else:
            raise ValueError('fresh_strict_admission_failed')
        check_ready(grid, root)
        command = ['timeout', '--signal=TERM', '--kill-after=5s', str(int(grid.END-time.time()-5))+'s',
            grid.PYTHON, '-B', str(Path(__file__).resolve()), 'native', '--physical', str(args.physical),
            '--old-source', str(args.old_source)]
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=module.UUID,
            PYTHONPATH=str(args.old_source), PYTHONDONTWRITEBYTECODE='1',
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        with (folder / 'NATIVE.log').open('x') as stream:
            child = subprocess.Popen(command, env=environment, cwd=args.old_source,
                stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        grid.write(folder / 'LAUNCH.json', dict(pid=child.pid, command=command, observed_unix=time.time()))
        code = child.wait()
        grid.write(root / TERMINAL, dict(status='COMPLETE' if code == 0 else 'FAILED',
            exit_code=code, no_retry=True, finished_unix=time.time()))
    except BaseException as error:
        if not (root / TERMINAL).exists():
            grid.write(root / TERMINAL, dict(status='FAILED', error_type=type(error).__name__,
                reason=str(error), no_retry=True, finished_unix=time.time()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('cpu', 'guard', 'native'))
    parser.add_argument('--physical', type=int, choices=(6, 7), required=True)
    parser.add_argument('--old-source', type=Path, required=True)
    arguments = parser.parse_args()
    result = {'cpu': cpu, 'guard': guard, 'native': native}[arguments.mode](arguments)
    if result is not None:
        print(json.dumps(result, sort_keys=True))
