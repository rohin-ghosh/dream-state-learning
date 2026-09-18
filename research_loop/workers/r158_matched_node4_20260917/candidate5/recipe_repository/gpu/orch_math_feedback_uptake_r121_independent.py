"""Prospective independent math forks; no shared dispatch or historical relabelling."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from gpu import orch_math_feedback_uptake_r115_native as math
from gpu import orch_r116_shared_learner as shared
from gpu import orch_r119_lease_clock as clock_policy


ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r121_independent_20260915_attempt3')
PREINPUT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r121_independent_20260915_attempt2')
ORIGINAL = math.policy.ROOT
STAGED = Path('/localhome/local-rohing/orch_math_feedback_uptake_r119_shared_20260915_attempt1')
COMMON = Path('/localhome/local-rohing/orch_r116_shared_node5_20260915_attempt1')
CLOCK = dict(path='/localhome/local-rohing/orch_r119_lease_continuation_20260915/CLOCK.json',
             sha256='a1aa51349c1784ec9f78e6411912576be43b55942c5fcdf1858ca391fd81c510')
CHECKPOINT_SHA = '43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d'
OPTIMIZER_SHA = '2afebd67c922367e3735ef9b5ed31b3c9a7c6e329758478781e5ea3cb469c0b5'
ANCHORS = Path('/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1')
ANCHOR_SHA = '2ad09dbe9673f95cbe92cd41e70d83635702b615fb7295b8b3f850e9ee674753'
SOURCE = Path(__file__).resolve().parents[1]
MODULE = 'gpu.orch_math_feedback_uptake_r121_independent_native'
MORNING = 1789538400
read, write, sha, require = shared.read, shared.write, shared.sha, shared.require


def ref(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=sha(path))


def checked(reference):
    require(set(reference) == {'path', 'sha256'} and sha(reference['path']) == reference['sha256'], 'exact_source_reference')
    return read(reference['path'])


def identity_alive(identity, proc=Path('/proc')):
    directory = proc/str(identity['pid'])
    try:
        parts = (directory/'stat').read_text().rsplit(')', 1)[1].split()
        return (parts[0] not in ('Z', 'X') and int(parts[19]) == int(identity['start_ticks'])
            and (proc/'sys/kernel/random/boot_id').read_text().strip() == identity['boot_id']
            and sha(directory/'cmdline') == identity['command_sha256'] and directory.stat().st_uid == identity['uid'])
    except (FileNotFoundError, ProcessLookupError):
        return False


def fork_contract(runtime, state, counters):
    require(state['generation'] == 1 and state['checkpoint']['path_sha256'] == CHECKPOINT_SHA
            and state['checkpoint']['optimizer_path_sha256'] == OPTIMIZER_SHA, 'actual_committed_gen1_AdamW')
    require(runtime['session']['generation'] == 1 and runtime['session']['checkpoint'] == state['checkpoint'], 'same_staged_seed')
    require(counters['native'] == runtime['session'].get('native_used', counters['native'])
            and all(type(value) is int and value >= 0 for value in counters.values()), 'historical_counts')
    return dict(lineage='EXPLICIT_INDEPENDENT_FORK_OF_SHARED_GEN1_AND_ADAMW',
        historical_math_optimizer_continuity=False, optimizer_reset=False,
        initial_optimizer_steps=state['optimizer_steps'], inherited_counters=deepcopy(counters),
        next_cycle=runtime['next_cycle'], initial_checkpoint=deepcopy(state['checkpoint']),
        seed_state=deepcopy(state), anchor_loss_weight=.25, new_presentations=16,
        rehearsal_presentations=1, episodes_per_sleep=2, parent_wait_seconds=0,
        parent_injection='NEXT_COMPLETED_TRAIN_TURN_BOUNDARY', outcome_selects_life=False,
        objective='OWN_CAUSAL_CONTINUATION_SFT_NOT_UNLIKELIHOOD',
        no_common_optimizer_session_or_barrier=True)


def preinput_proof(root):
    root = Path(root)
    terminal = read(root/'GUARD_TERMINAL.json')
    launch = read(root/'LAUNCH.json')
    require(terminal['returncode'] != 0 and terminal['identity'] == launch['identity']
        and not identity_alive(launch['identity']), 'actual_failed_preinput_process_absent')
    require(not list((root/'reservations').glob('*.json')) and not list(root.glob('cycle*/CALL*'))
        and not list(root.glob('checkpoints/*')) and not list(root.glob('cycle*/sleep/*')), 'no_model_load_or_input_charge')
    log = (root/'native.log').read_text()
    require('too many values to unpack (expected 2)' in log and 'inventory.load_inventory' in log,
        'exact_postload_anchor_interface_failure')
    require(read(root/'OPTIMIZER_RESTORED.json')['step'] == read(root/'COUNTERS.json')['optimizer_steps'] == 3009,
        'restored_but_no_optimizer_updates')
    return dict(launch=ref(root/'LAUNCH.json'), terminal=ref(root/'GUARD_TERMINAL.json'),
        log=ref(root/'native.log'), plan=ref(root/'PLAN.json'), counters=ref(root/'COUNTERS.json'),
        model_inputs=0, optimizer_loads=1, optimizer_updates=0, actual_process_absent=True,
        original_attempt_preserved=True, previous_failure_chain=read(root/'PLAN.json')['preinput_failure'])


def prepare(index):
    require(index in (1, 5), 'math_owned_physical1_5')
    root, original, staged = ROOT/f'lane{index}', ORIGINAL/f'lane{index}', STAGED/f'lane{index}'
    require(not root.exists(), 'unique_new_fork_root')
    require(not (staged/'GUARD_STARTED.json').exists() and not (staged/'LAUNCH.json').exists(), 'shared_campaign_never_launched')
    clock = clock_policy.validate(CLOCK)
    runtime = read(staged/'RUNTIME.json')
    failed_preinput = preinput_proof(PREINPUT/f'lane{index}')
    state, counters = read(COMMON/'STATE.json'), read(original/'COUNTERS.json')
    contract = fork_contract(runtime, state, counters)
    shared.checked_checkpoint(state['checkpoint'])
    require(sha(ANCHORS/'ANCHOR_MANIFEST.json') == ANCHOR_SHA, 'same42_anchor_manifest')
    require(sha(runtime['carry']['path']) == runtime['carry']['sha256'], 'actual_prior_carry')
    cohort = read(ORIGINAL/'TRAIN.json')
    require(len(cohort) == 96 and all(len(tasks) == 2 for tasks in cohort), 'existing_two_episode_cohort')
    config = read(COMMON/'CONFIG.json')
    history = []
    seen = set()
    for rows in config['initial_history'].values():
        for row in rows:
            require(row['source_call_sha256'] not in seen, 'no_duplicate_initial_rehearsal')
            seen.add(row['source_call_sha256'])
            history.append(row)
    for path in sorted((COMMON/'generation_000000').glob('*.json')):
        item = read(path)
        if item.get('branch') not in shared.BRANCHES or 'rows' not in item:
            continue
        for row in item['rows']:
            require(row['source_call_sha256'] not in seen, 'trained_gen0_not_new')
            seen.add(row['source_call_sha256'])
            history.append(row)
    for row in history:
        source = read(row['source_call_path'])
        require(sha(row['source_call_path']) == row['source_call_sha256'], 'historical_source_bytes')
        shared.replay.verify_source(row, source)
    root.mkdir(parents=True)
    write(root/'HISTORY_INITIAL.json', history)
    write(root/'CARRY_INITIAL.json', checked(runtime['carry'])['own_reflection'])
    write(root/'CONFIG.json', dict(index=index, uuid=math.policy.DEVICES[index]))
    write(root/'COUNTERS.json', dict(counters, optimizer_steps=state['optimizer_steps'],
        child_token_exposures=state['child_token_exposures'], anchor_token_exposures=state['anchor_token_exposures']))
    manifest = ref(SOURCE/'SOURCE_MANIFEST.json')
    tests = ref(SOURCE/'CPU_TESTS.json')
    plan = dict(schema='R121_MATH_INDEPENDENT_PLAN_V1', root=str(root), original_root=str(original),
        branch='F2' if index == 1 else 'A2', index=index, uuid=math.policy.DEVICES[index],
        source_root=str(SOURCE), source_manifest=manifest, tests=tests, contract=contract,
        preserved_runtime=ref(staged/'RUNTIME.json'), preserved_owner=ref(staged/'FRESH_OWNER.json'),
        initial_counters=ref(original/'COUNTERS.json'), initial_carry=ref(root/'CARRY_INITIAL.json'),
        initial_history=ref(root/'HISTORY_INITIAL.json'), initial_state=ref(COMMON/'STATE.json'),
        train=ref(ORIGINAL/'TRAIN.json'), dev=ref(ORIGINAL/'DEV8.json'),
        final=ref(ORIGINAL/'sealed/FINAL8.json'), anchors=str(ANCHORS), anchor_sha256=ANCHOR_SHA,
        clock=CLOCK, bounds=dict(clock), created_unix=time.time(),
        prospective_capacity=dict(native=10000000, parent=100000, cycles=None,
            rule='LEASE_WALL_NOT_OLD43_OR96_CAP', historical_caps=runtime['inherited_bounds']),
        final_schedule=[dict(key='R121_SEP16_0600_FINAL8', due_unix=MORNING, calls=8),
            dict(key='R121_LEASE_WALL_FINAL8', due_unix=clock['hard_end_unix']-600, calls=8)],
        no_old_final_repetition=True, seed=2026091500+index,
        preinput_failure=failed_preinput,
        parent_models=['claude-fable-5-1', 'claude-sonnet-4-6'] if index == 1 else ['openai/openai/gpt-6-astra'])
    write(root/'PLAN.json', plan)
    return ref(root/'PLAN.json')


def validate(root):
    root = Path(root).resolve(strict=True)
    plan = read(root/'PLAN.json')
    require(root == ROOT/f"lane{plan['index']}" and plan['root'] == str(root), 'exact_independent_root')
    require(plan['source_root'] == str(SOURCE), 'frozen_native_source_root')
    manifest = checked(plan['source_manifest'])
    tests = checked(plan['tests'])
    require(tests['passed'] is True and tests['source_manifest_sha256'] == plan['source_manifest']['sha256'], 'CPU_provenance')
    for name, digest in manifest.items():
        require(sha(SOURCE/name) == digest, 'immutable_source:'+name)
    for name in ('train', 'dev', 'final', 'initial_carry', 'initial_history'):
        require(sha(plan[name]['path']) == plan[name]['sha256'], 'immutable_data:'+name)
    require(sha(plan['clock']['path']) == plan['clock']['sha256'], 'immutable_lease_authorization')
    require(time.time() < plan['bounds']['hard_end_unix'], 'actual_lease_wall')
    return plan


def reserve(root, kind, metadata, count=1):
    root = Path(root)
    require(kind in ('native', 'parent') and type(count) is int and count > 0, 'known_positive_charge')
    with (root/'LEDGER.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        counters = read(root/'COUNTERS.json')
        first = counters[kind]+1
        counters[kind] += count
        math.atomic(root/'COUNTERS.json', counters)
        write(root/'reservations'/f'{kind}_{first:08d}.json', dict(first=first, count=count,
            kind=kind, metadata=metadata, reserved_unix=time.time(), retries=0))
        return first


def append_parent(plan, root, task, experience, cycle, episode, phase):
    queue_root = Path(plan['original_root'])
    config_path = queue_root/'parent_claude/CONFIG.json'
    config = read(config_path)
    identifier = f'R121_C{cycle:06d}_E{episode}_{phase}'
    payload = experience.payload(task, config['life_id'], cycle, episode, phase, config['cohort_sha256'])
    request = dict(id=identifier, payload=payload, payload_sha256=math.policy.digest(payload),
        lane_deadline_unix=min(time.time()+600, plan['bounds']['train_end_unix']))
    math.broker.validate_request(request, config)
    reserve(root, 'parent', dict(id=identifier, nonblocking=True))
    write(root/'parent_pending'/f'{identifier}.json', dict(request=request,
        response_path=str(queue_root/'parent_queue'/f'{identifier}.response.json'), task_id=task['id']))
    write(queue_root/'parent_queue'/f'{identifier}.request.json', request)
    return identifier


def poll_parent(plan, root, experience, phase):
    results = []
    for pending in sorted((Path(root)/'parent_pending').glob('*.json')):
        destination = Path(root)/'parent_delivered'/pending.name
        if destination.exists():
            continue
        item = read(pending)
        request = item['request']
        response_path = Path(item['response_path'])
        if not response_path.exists():
            if time.time() < request['lane_deadline_unix']:
                continue
            write(destination, dict(id=request['id'], status='MISSING', reason='ASYNC_DEADLINE_NO_WAIT',
                request_sha256=shared.digest(request), delivered_unix=time.time()))
            continue
        try:
            response = read(response_path)
            require(response['id'] == request['id'] and response['request_sha256'] == shared.digest(request), 'exact_async_join')
            archive = response['transcript_receipt']
            archive_root = Path(archive['remote_root'])
            require(archive_root == Path(plan['original_root'])/'parent_transcripts'/request['id'], 'native_parent_archive')
            for name, digest in archive['files'].items():
                require(Path(name).name == name and sha(archive_root/name) == digest, 'preserved_parent_bytes')
            require(response['status'] in ('COMPLETE', 'MISSING', 'SILENT'), 'parent_disposition')
            if response['status'] in ('COMPLETE', 'SILENT'):
                require(response['actual_model'] in plan['parent_models'], 'verified_allowed_actual_parent')
            if response['status'] == 'COMPLETE':
                experience.append(math.policy.event('parent', response['plan']['guidance'], 'TRAIN', response))
            delivered = dict(status=response['status'], actual_model=response.get('actual_model'),
                response=ref(response_path), origin_task_id=item['task_id'], injected_before=phase,
                elapsed_seconds=time.time()-pending.stat().st_mtime, delivered_unix=time.time(),
                nonblocking=True, id=request['id'])
            write(destination, delivered)
            results.append((response, request, read(Path(plan['original_root'])/'parent_claude/CONFIG.json')))
        except (ValueError, KeyError, OSError) as error:
            write(destination, dict(id=request['id'], status='MISSING', reason='INVALID_ASYNC_RECEIPT', error=str(error)))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare',))
    parser.add_argument('--index', type=int, choices=(1, 5), required=True)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.index)))
