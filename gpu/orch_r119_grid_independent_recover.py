"""A4 packaging-crash recovery, exact cached C9 replay without model redispatch."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import time


HERE = Path(__file__).resolve().parent
OLD_SOURCE = Path('/localhome/local-rohing/orch_r119_grid_independent_source_20260915_v1/gpu')
ORIGINAL_SHA = 'a4129eca891e0cd9dc2f49f607e5d53d292c662b56a501d4a1611779feb8be7c'
PROMPT_SHA = '5f494f5f4b6e2cddb8d909c87b07c7e816d23283553f5e91834a489a6b6dd497'
ERA = 'independent_r119_recovery_v1'


class CachedBoundary(BaseException):
    pass


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def clean(value):
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items() if key not in ('created_unix', 'finished_unix')}
    if isinstance(value, list):
        return [clean(item) for item in value]
    return value


def replay_class(grid, parent_type, cached, *, dry=False):
    class ReplayLife(parent_type):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.cached = cached if self.cycle == 9 else []
            self.cursor = 0

        def calls(self, tasks, purpose, messages, cap, *, attached_readout=False):
            if self.cursor == len(self.cached):
                if dry:
                    raise CachedBoundary()
                return super().calls(tasks, purpose, messages, cap, attached_readout=attached_readout)
            row = self.cached[self.cursor]
            require(not attached_readout and len(tasks) == 1 and row['kind'] == 'NATIVE'
                and row['task_id'] == tasks[0]['id'] and row['purpose'] == purpose, 'cached_causal_sequence')
            path = self.root / 'calls' / f'N{row["number"]:05d}.json'
            document = grid.read(path)
            require(document['status'] == 'COMPLETE' and document['messages'] == messages[0]
                and document['cap'] == cap, 'exact_cached_prompt_target_cap')
            self.cursor += 1
            response = deepcopy(document['response'])
            response['reference'] = grid.ref(path)
            self.event('child', response['raw'], grid.sha(path))
            return [response]

        def ask(self, task, episode, phase):
            if self.cursor == len(self.cached):
                if dry:
                    raise CachedBoundary()
                return super().ask(task, episode, phase)
            if phase == 'experience':
                triple = grid.read(self.root / 'triples' / f'C0009_E{episode}.json')
                result = triple['intervention']
            else:
                result = dict(request=None, response=None,
                    disposition=dict(status='PENDING', guidance=None, continue_life=True),
                    nonblocking=True, wait_seconds=0, backlog_backpressure=True,
                    delivery_policy='next_TRAIN_generation_boundary', observed_unix=0)
            if result['request'] is not None:
                row = self.cached[self.cursor]
                require(row['kind'] == 'PARENT' and row['phase'] == phase
                    and row['task_id'] == task['id'], 'same_cached_parent_reservation')
                path = self.root / 'parent_queue' / f'P{row["number"]:04d}.request.json'
                require(grid.ref(path) == result['request'], 'same_queued_parent_no_provider_replay')
                request = grid.read(path)
                actual = grid.policy.queue_request(request['id'], self.config['life_id'], self.cycle,
                    episode, phase, task, self.events, self.config['cohort_sha256'], 0)
                require(actual['payload'] == request['payload'], 'same_actual_parent_causal_context')
                self.cursor += 1
            require(result['disposition']['status'] == 'PENDING' and not result['disposition']['guidance'],
                    'no_retroactive_parent_application')
            return result
    return ReplayLife


def loader():
    path = OLD_SOURCE / 'orch_r119_grid_independent.py'
    require(hashlib.sha256(path.read_bytes()).hexdigest() == ORIGINAL_SHA, 'immutable_failed_source')
    spec = importlib.util.spec_from_file_location('failed_independent', path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    old.ERA, old.TERMINAL = ERA, 'R119_GRID_INDEPENDENT_RECOVERY_TERMINAL.json'
    return old


def state(old):
    grid, admission, root, config, checkpoint = old.configure('A4')
    require(grid.sha(old.OLD / 'research_notes/PARENTING_BATTLE_PLAN_v4_2026-09-15.md') == PROMPT_SHA,
            'restored_exact_packaged_prompt')
    require(grid.read(root / 'R119_GRID_INDEPENDENT_TERMINAL.json')['status'] == 'FAILED',
            'original_crash_preserved')
    rows = [json.loads(line) for line in (root / 'LEDGER.jsonl').read_text().splitlines() if line]
    require(sum(row['kind'] == 'NATIVE' for row in rows) == 592
        and sum(row['kind'] == 'PARENT' for row in rows) == 41, 'exact_crashed_counters')
    cached = [row for row in rows if row['cycle'] == 9]
    require(all(row['kind'] == 'PARENT' or row['split'] == 'TRAIN' and not row['attached_readout']
                for row in cached), 'TRAIN_only_cached_reconstruction')
    return grid, root, config, cached


def cpu(old):
    grid, root, config, cached = state(old)
    original = grid.write

    def check(path, value, replace=False):
        require(Path(path).exists() and clean(grid.read(path)) == clean(value),
                'CPU_exact_reconstructed_evidence_no_writes:' + str(path))

    grid.write = check
    life = replay_class(grid, old.mailbox.life_class(grid, ERA), cached, dry=True)(root, None, config, 9)
    try:
        roster = grid.read(root / 'TRAIN.json')
        grid.train_cycle(life, [roster[0], roster[8]], grid.read(root / 'CARRY.json'))
        raise ValueError('expected_next_uncharged_call')
    except CachedBoundary:
        require(life.cursor == len(cached), 'all_cached_rows_reconstructed')
    finally:
        grid.write = original
    previous = grid.read(root / 'independent_r119_v1/READY.json')
    document = dict(previous, old_ledger=grid.ref(root / 'LEDGER.jsonl'), old_carry=grid.ref(root / 'CARRY.json'),
        source_files=dict(previous['source_files'], **{str(Path(__file__).resolve()): grid.sha(__file__)}),
        recovery=True, cached_rows=len(cached), model_calls_replayed=0, provider_calls_replayed=0,
        crash=grid.ref(root / 'R119_GRID_INDEPENDENT_TERMINAL.json'),
        restored_packaged_prompt=grid.ref(old.OLD / 'research_notes/PARENTING_BATTLE_PLAN_v4_2026-09-15.md'),
        counts=dict(NATIVE=592, PARENT=41), observed_unix=time.time())
    folder = root / ERA
    original(folder / 'LEASE_BUDGET.json', grid.read(root / 'independent_r119_v1/LEASE_BUDGET.json'))
    original(folder / 'READY.json', document)
    print(json.dumps(grid.ref(folder / 'READY.json')))


def native(old):
    grid, root, config, cached = state(old)
    writer = grid.write

    def preserve(path, value, replace=False):
        if Path(path).exists() and not replace:
            require(clean(grid.read(path)) == clean(value), 'existing_evidence_identical')
            return
        return writer(path, value, replace=replace)

    grid.write = preserve
    original = old.mailbox.life_class
    old.mailbox.life_class = lambda module, era: replay_class(module, original(module, era), cached)
    old.native('A4')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('cpu', 'guard', 'native', 'scan'))
    parser.add_argument('--branch', choices=('A4',), required=True)
    args = parser.parse_args()
    old = loader()
    if args.mode == 'cpu':
        cpu(old)
    elif args.mode == 'native':
        native(old)
    else:
        old.__file__ = __file__
        result = getattr(old, args.mode)('A4')
        if result is not None:
            print(json.dumps(result))
