"""F2 crash continuation: saved AdamW/RNG, partial C13, no charged-call retry."""

import argparse
from copy import deepcopy
from dataclasses import replace
import fcntl
import gc
import json
import os
from pathlib import Path
import sys
import time
from types import FunctionType

from gpu import orch_math_feedback_uptake_r121_independent_native as previous


control, math, native, shared = previous.control, previous.math, previous.native, previous.shared
read, write, sha, ref, require = previous.read, previous.write, previous.sha, previous.ref, previous.require
SOURCE = Path(__file__).resolve().parents[1]
ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r123_f2_recovery_20260915_attempt1/lane1')
OLD = Path('/localhome/local-rohing/orch_math_feedback_uptake_r121_independent_20260915_attempt3/lane1')
MODULE = 'gpu.orch_math_feedback_uptake_r123_f2_recovery'
CHECKPOINT_SHA = 'f978cee8e8d256bc07724783e305efd95ae8e735541f4081b3f303b6224183bc'
OPTIMIZER_SHA = '4fbe43c4dc4df4c5ed8cf1b94c4687f1743d51aa8617c966e272f9278771b0d3'
DOCUMENT_SHA = '79c36d2468cf1ab6668ebcc6bf6929bae37a9a9a6fbe19272339c67c9fff31a9'


def interrupted_contract(terminal, committed, counters, calls):
    require(terminal['status'] == 'FAILED' and terminal['error_type'] == 'FileNotFoundError'
        and 'PARENTING_BATTLE_PLAN_v4_2026-09-15.md' in terminal['error'], 'exact_packaging_crash')
    require(committed['cycle'] == 12 and committed['checkpoint']['path_sha256'] == CHECKPOINT_SHA
        and committed['checkpoint']['optimizer_path_sha256'] == OPTIMIZER_SHA, 'genuine_C12_adapter_AdamW')
    require(counters == terminal['counters'] and counters['native'] == 292
        and counters['parent'] == 66 and counters['optimizer_steps'] == 3555, 'exact_preserved_counters')
    require([call['phase'] for call in calls] == ['episode', 'open_turn', 'episode', 'open_turn', 'presleep', 'reflection'], 'partial_C13_sequence')
    require(all(call['status'] == 'COMPLETE' for call in calls[:5])
        and calls[5]['status'] == 'FAILED' and 'response' not in calls[5], 'five_actual_calls_failed292')
    require(len({call['task_id'] for call in calls[:5]}) == 2, 'two_already_experienced_episodes')
    return dict(same_independent_F2_life=True, optimizer_reset=False, rng_restored_from_saved_C12=True,
        failed_native_reservation=292, skipped_failed_reflection_not_retried=True,
        pending_cycle=13, pending_actual_rows=5, pending_episode_count=2,
        first_new_episode_cycle=14, first_new_native_reservation=293,
        partial_C13_sleep_uses_recorded_presleep_not_fabricated_reflection=True)


def prepare():
    terminal, committed, counters = (read(OLD / name) for name in ('TERMINAL.json', 'COMMITTED.json', 'COUNTERS.json'))
    paths = [OLD / f'cycle000013/CALL_{number:08d}.json' for number in range(287, 293)]
    calls = [read(path) for path in paths]
    contract = interrupted_contract(terminal, committed, counters, calls)
    launch = read(OLD / 'LAUNCH.json')
    require(not control.identity_alive(launch['identity']) and not Path('/proc', str(launch['identity']['pid'])).exists(), 'actual_old_process_absent')
    guard = read(OLD / 'GUARD_TERMINAL.json')
    require(guard['returncode'] == 1 and guard['identity'] == launch['identity'], 'real_guard_failure')
    document = SOURCE / 'research_notes/PARENTING_BATTLE_PLAN_v4_2026-09-15.md'
    require(sha(document) == DOCUMENT_SHA, 'exact_restored_document_bytes')
    plan = deepcopy(read(OLD / 'PLAN.json'))
    history = control.checked(plan['initial_history'])
    for cycle in (11, 12):
        require(read(OLD / f'cycle{cycle:06d}/sleep/COMPLETE.json')['independent_optimizer'], 'genuine_completed_sleep')
        history.extend(read(OLD / f'cycle{cycle:06d}/ROWS.json'))
    pending = [previous.replay_engine.replay_row(call, path, sha(path)) for call, path in zip(calls[:5], paths[:5])]
    for row in history + pending:
        require(sha(row['source_call_path']) == row['source_call_sha256'], 'actual_source_bytes')
        shared.replay.verify_source(row, read(row['source_call_path']))
    require(not {row['source_call_sha256'] for row in history}.intersection(row['source_call_sha256'] for row in pending), 'no_retraining_as_new')
    ROOT.mkdir(parents=True, exist_ok=False)
    write(ROOT / 'HISTORY_INITIAL.json', history)
    write(ROOT / 'PENDING_C13_ROWS.json', pending)
    write(ROOT / 'CARRY_INITIAL.json', math.policy.event('child', calls[4]['response']['raw'], 'TRAIN', ref(paths[4])))
    write(ROOT / 'COUNTERS.json', counters)
    preserved = {str(path.relative_to(OLD)): sha(path) for path in [*paths,
        OLD / 'TERMINAL.json', OLD / 'COMMITTED.json', OLD / 'COUNTERS.json', OLD / 'PLAN.json',
        OLD / 'LAUNCH.json', OLD / 'GUARD_TERMINAL.json', OLD / 'reservations/native_00000292.json']}
    for directory in ('parent_pending', 'parent_delivered'):
        for path in (OLD / directory).glob('*.json'):
            write(ROOT / directory / path.name, read(path))
            preserved[str(path.relative_to(OLD))] = sha(path)
    plan.update(root=str(ROOT), source_root=str(SOURCE), source_manifest=ref(SOURCE / 'R123_SOURCE_MANIFEST.json'),
        tests=ref(SOURCE / 'R123_CPU_TESTS.json'), initial_history=ref(ROOT / 'HISTORY_INITIAL.json'),
        initial_carry=ref(ROOT / 'CARRY_INITIAL.json'), pending_rows=ref(ROOT / 'PENDING_C13_ROWS.json'),
        recovery=contract, predecessor_root=str(OLD), preserved=preserved, restored_document=ref(document),
        fresh_readout_memory_policy='OFFLOAD_RESIDENT_MODEL_AND_OPTIMIZER_DURING_FRESH_PROCESS',
        created_unix=time.time())
    plan['contract'].update(initial_checkpoint=committed['checkpoint'], initial_optimizer_steps=3555,
        inherited_counters=counters, next_cycle=13)
    write(ROOT / 'PLAN.json', plan)
    return ref(ROOT / 'PLAN.json')


def validate(root):
    require(Path(root) == ROOT, 'only_owned_F2_recovery')
    plan = read(ROOT / 'PLAN.json')
    require(plan['index'] == 1 and plan['branch'] == 'F2' and plan['source_root'] == str(SOURCE), 'exact_F2_source')
    for key in ('source_manifest', 'tests', 'initial_history', 'initial_carry', 'pending_rows', 'restored_document', 'train', 'dev', 'final', 'clock'):
        require(sha(plan[key]['path']) == plan[key]['sha256'], 'pinned_' + key)
    require(read(plan['tests']['path'])['passed'], 'CPU_tests')
    for name, digest in read(plan['source_manifest']['path']).items():
        require(sha(SOURCE / name) == digest, 'frozen_source:' + name)
    for name, digest in plan['preserved'].items():
        require(sha(OLD / name) == digest, 'preserved_failed_history:' + name)
    checkpoint = plan['contract']['initial_checkpoint']
    require(sha(checkpoint['path']) == CHECKPOINT_SHA and sha(checkpoint['optimizer_path']) == OPTIMIZER_SHA, 'saved_C12_bytes')
    require(time.time() < plan['bounds']['hard_end_unix'], 'unchanged_lease_wall')
    return plan


def restore(plan, check):
    recorded = []
    loader = FunctionType(previous.load.__code__, dict(previous.load.__globals__, write=lambda path, value: recorded.append((path, value))),
        'restore_saved_F2', previous.load.__defaults__)
    actor = loader(plan, plan['contract']['initial_checkpoint'], check)
    payload = actor.torch.load(plan['contract']['initial_checkpoint']['optimizer_path'], map_location='cpu', weights_only=False)
    require('cpu_rng' in payload and 'cuda_rng' in payload and len(payload['cuda_rng']) == 1, 'saved_single_GPU_RNG_required')
    actor.torch.set_rng_state(payload['cpu_rng'])
    actor.torch.cuda.set_rng_state_all(payload['cuda_rng'])
    require(actor.torch.equal(actor.torch.get_rng_state(), payload['cpu_rng'])
        and all(actor.torch.equal(actual, expected) for actual, expected in zip(actor.torch.cuda.get_rng_state_all(), payload['cuda_rng'])), 'actual_RNG_restored')
    require(len(recorded) == 1, 'single_load_receipt')
    write(ROOT / 'OPTIMIZER_RESTORED.json', dict(recorded[0][1], rng_policy='EXACT_SAVED_C12_CPU_CUDA_RNG',
        historical_math_optimizer_continuity=True, forked_independent_optimizer=False,
        continuation_of_independent_F2=True, rng_restored_unix=time.time()))
    return actor


def readout_with_offload(actor, plan, checkpoint, key, split='DEV'):
    actor.loaded.optimizer.zero_grad(set_to_none=True)
    actor.model.to('cpu')
    for state in actor.loaded.optimizer.state.values():
        for name, value in state.items():
            if actor.torch.is_tensor(value):
                state[name] = value.to('cpu')
    gc.collect()
    actor.torch.cuda.empty_cache()
    write(ROOT / 'offloads' / (key + '.json'), dict(actual_process=native.process_identity(),
        allocated_bytes=actor.torch.cuda.memory_allocated(), reserved_bytes=actor.torch.cuda.memory_reserved(),
        optimizer_preserved=True, checkpoint=checkpoint, observed_unix=time.time()))
    try:
        return previous.fresh_readout(ROOT, plan, checkpoint, key, split)
    finally:
        actor.model.to('cuda:0')
        for parameter, state in actor.loaded.optimizer.state.items():
            for name in ('exp_avg', 'exp_avg_sq'):
                if name in state:
                    state[name] = state[name].to(parameter.device)
        require(native.observe_adapter(actor.loaded.engine, actor.loaded.observed) == actor.loaded.observed, 'reloaded_exact_adapter_after_DEV')


def resident(root):
    plan = validate(root)
    lock = (ROOT / 'LIFE.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    require(not control.identity_alive(read(OLD / 'LAUNCH.json')['identity']), 'old_actor_absent')
    def check(label):
        require(time.time() < plan['bounds']['train_end_unix'], 'unchanged_native_wall:' + label)
    write(ROOT / 'MOUNTED_BEFORE.json', math.mounted(Path(plan['original_root']), 'recovery_before'))
    actor = restore(plan, check)
    write(ROOT / 'LOADED.json', dict(actual_process=native.process_identity(), loaded_unix=time.time(),
        adapter=native.observe_adapter(actor.loaded.engine, actor.loaded.observed).document(), optimizer_steps=3555,
        first_action='SLEEP_EXISTING_PARTIAL_C13_NO_MODEL_CALL_REPLAY'))
    inventory, receipt = previous.inventory.build_inventory(plan['anchors'], actor.tokenizer, 16384)
    anchors = [entry for family in sorted(inventory) for entry in inventory[family]]
    write(ROOT / 'ANCHORS.json', receipt)
    history, carry = control.checked(plan['initial_history']), control.checked(plan['initial_carry'])
    tasks = control.checked(plan['train'])
    checkpoint = plan['contract']['initial_checkpoint']
    cycle = 13
    try:
        while time.time() < plan['bounds']['train_end_unix']:
            if cycle == 13:
                output = ROOT / 'cycle000013'
                rows = control.checked(plan['pending_rows'])
                write(output / 'ROWS.json', rows)
                old_calls = [read(OLD / f'cycle000013/CALL_{number:08d}.json') for number in (287, 289)]
                write(output / 'COLLECTION_COMPLETE.json', dict(status='PARTIAL_PREDECESSOR_NOT_COMPLETE',
                    original_responses=[item['response'] for item in old_calls], failed_reflection_reserved=292,
                    actual_rows=5, new_generation_calls=0, own_reflection=carry))
            else:
                require(cycle <= len(tasks), 'prospective_cohort_extension_required_before_dispatch')
                output, rows, carry = previous.collect(plan, ROOT, actor, cycle, tasks[cycle - 1], carry)
            sleep = output / 'sleep'
            sleep.mkdir(parents=True)
            actor.loaded.binding = replace(actor.loaded.binding, phase='training')
            started = time.time()
            metrics = shared.train(actor.loaded.engine, actor.loaded.optimizer, rows, history, anchors, sleep, check)
            require(metrics['optimizer_steps'] > 0, 'actual_saved_sleep_updates')
            checkpoint = previous.checkpoint(actor, ROOT, cycle)
            actor.loaded.binding = replace(actor.loaded.binding, phase='collection')
            counters = read(ROOT / 'COUNTERS.json')
            for name in ('optimizer_steps', 'child_token_exposures', 'anchor_token_exposures'):
                counters[name] += metrics[name]
            math.atomic(ROOT / 'COUNTERS.json', counters)
            write(sleep / 'COMPLETE.json', dict(metrics, checkpoint=checkpoint, started_unix=started,
                finished_unix=time.time(), cumulative_optimizer_steps=counters['optimizer_steps'],
                partial_failed_predecessor_cycle=cycle == 13, independent_optimizer=True))
            history.extend(rows)
            write(output / 'CARRY.json', carry)
            readout_with_offload(actor, plan, checkpoint, f'DEV_C{cycle:06d}')
            write(output / 'COMPLETE.json', dict(cycle=cycle, checkpoint=checkpoint, next_cycle=cycle + 1,
                missing_predecessor_reflection_not_relabelled=cycle == 13, completed_unix=time.time()))
            cycle += 1
            for scheduled in plan['final_schedule']:
                if time.time() >= scheduled['due_unix']:
                    readout_with_offload(actor, plan, checkpoint, scheduled['key'], 'FINAL')
        write(ROOT / 'TERMINAL.json', dict(status='LEASE_BOUNDARY', last_committed_checkpoint=checkpoint, counters=read(ROOT / 'COUNTERS.json')))
    except BaseException as error:
        write(ROOT / 'TERMINAL.json', dict(status='FAILED', error_type=type(error).__name__, error=str(error),
            last_committed_checkpoint=checkpoint, counters=read(ROOT / 'COUNTERS.json'), no_retry=True, finished_unix=time.time()))
        raise


def configure():
    control.ROOT, control.SOURCE, control.MODULE, control.validate = ROOT.parent, SOURCE, MODULE, validate


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'guard', 'resident', 'scan', 'readout'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--binding', type=Path)
    args = parser.parse_args()
    configure()
    if args.phase == 'prepare':
        print(json.dumps(prepare()))
    elif args.phase == 'scan':
        print(json.dumps(previous.scan(args.root)))
    elif args.phase == 'guard':
        previous.guard(args.root)
    elif args.phase == 'readout':
        previous.readout(args.root, args.binding)
    else:
        resident(args.root)
