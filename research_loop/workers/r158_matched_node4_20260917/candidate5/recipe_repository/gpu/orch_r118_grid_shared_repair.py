"""Continue only the first-call missing-reference failure without replaying it."""

import argparse
from copy import deepcopy
import fcntl
import gc
import json
import os
from pathlib import Path
import subprocess
import time
from types import FunctionType

from gpu import orch_r118_grid_shared_run as run


shared = run.shared
grid = run.grid
require = shared.require
ERA = 'shared_repair_v1'
TERMINAL = 'R118_SHARED_REPAIR_TERMINAL.json'
BATTLEPLAN = 'research_notes/PARENTING_BATTLE_PLAN_v4_2026-09-15.md'
PRINCIPLES = 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md'
BATTLE_SHA = '5f494f5f4b6e2cddb8d909c87b07c7e816d23283553f5e91834a489a6b6dd497'


def verify_bundle(bundle):
    bundle = Path(bundle).resolve(strict=True)
    manifest = shared.read(bundle / 'MANIFEST.json')
    require(manifest['files'][BATTLEPLAN] == BATTLE_SHA and
            manifest['files'][PRINCIPLES] == grid.broker.PRINCIPLES_V2_SHA256,
            'exact_predecessor_non_python_dependencies')
    for name, expected in manifest['files'].items():
        path = bundle / name
        require(path.resolve().is_relative_to(bundle) and shared.sha(path) == expected,
                'repair_bundle_file:' + name)
    frozen = Path(manifest['frozen_source'])
    for name, expected in manifest['frozen_files'].items():
        require(shared.sha(frozen / name) == expected, 'frozen_source_unchanged:' + name)
    require(shared.sha(__file__) == manifest['files']['orch_r118_grid_shared_repair.py'],
            'exact_repair_executable')
    return manifest


def bind_references(bundle):
    verify_bundle(bundle)
    grid.broker.BATTLEPLAN = Path(bundle) / BATTLEPLAN
    require(bool(grid.broker.fixed_parent_template()), 'actual_template_readable')


def interrupted(root):
    root = Path(root).resolve(strict=True)
    config, activation, baseline = run.validate(root)
    terminal = shared.read(root / 'SHARED_TERMINAL.json')
    require(terminal['status'] == 'FAILED' and terminal['exit_code'] == 1,
            'exact_failed_predecessor')
    log = (root / 'shared_guard/NATIVE.log').read_text()
    require('FileNotFoundError' in log and BATTLEPLAN in log and
            'reflection_call_settings' in log, 'only_missing_reference_repair')
    loaded = shared.read(root / 'SHARED_LOADED.json')
    guard = shared.read(root / 'SHARED_GUARD_CPU_LAUNCH.json')
    require(not Path('/proc', str(loaded['pid'])).exists() and
            not run.process_alive(guard['identity']), 'both_own_predecessors_dead')
    raw_lines = (root / 'LEDGER.jsonl').read_bytes().splitlines(keepends=True)
    original_count = baseline['native_charged'] + baseline['parent_charged']
    import hashlib
    require(hashlib.sha256(b''.join(raw_lines[:original_count])).hexdigest() ==
            baseline['ledger']['sha256'], 'unchanged_original_ledger_prefix')
    suffix = [json.loads(line) for line in raw_lines[original_count:]]
    require(len(suffix) == 2 and [row['kind'] for row in suffix] == ['NATIVE', 'PARENT'],
            'exact_one_child_one_parent_no_later_work')
    cycle = baseline['next_cycle']
    tasks = run.cycle_tasks(shared.read(root / 'TRAIN.json'), cycle)
    child, parent = suffix
    require(all(row['cycle'] == cycle and row['task_id'] == tasks[0]['id'] for row in suffix)
            and child['purpose'] == 'episode' and child['split'] == 'TRAIN'
            and not child['attached_readout'] and parent['phase'] == 'experience',
            'first_episode_exact_cursor')
    require(child['number'] == baseline['native_charged'] + 1 and
            parent['number'] == baseline['parent_charged'] + 1, 'charged_cursors_not_reset')
    require(not list((root / 'cycles' / f'{cycle:04d}').rglob('*.json')),
            'no_existing_environment_or_cycle_work')
    require(shared.sha(root / 'CARRY.json') == baseline['carry']['sha256'], 'carry_unchanged')
    for name, expected in baseline['captures'].items():
        require(shared.sha(root / name) == expected, 'historical_capture_unchanged:' + name)
    capture_path = root / 'calls' / f'N{child["number"]:05d}.json'
    capture = shared.read(capture_path)
    require(capture['status'] == 'COMPLETE' and capture['shared_generation'] == 0 and
            capture['shared_child'] == loaded['session'], 'same_adopted_completed_child')
    session = shared.read(root / 'shared_cycles' / f'{cycle:04d}' / 'COLLECTION.json')
    require(run.client.call_binding(session) == loaded['session'], 'same_original_collection')
    run.client.current(session)
    identifier = f'P{parent["number"]:04d}'
    request_path = root / 'parent_queue' / (identifier + '.request.json')
    response_path = root / 'parent_queue' / (identifier + '.response.json')
    request, response = shared.read(request_path), shared.read(response_path)
    require(response['prompt_binding']['battleplan_sha256'] == BATTLE_SHA and
            response['finished_unix'] < terminal['finished_unix'] < request['lane_deadline_unix'],
            'already_published_received_before_original_failure_deadline')
    require(response['request_sha256'] == grid.policy.digest(request), 'same_reserved_parent')
    return dict(config=config, activation=activation, baseline=baseline, terminal=terminal,
                loaded=loaded, session=session, capture=grid.ref(capture_path),
                request=grid.ref(request_path), response=grid.ref(response_path),
                parent_number=parent['number'], cycle=cycle)


def recover_parent(root, state):
    request = shared.read(state['request']['path'])
    response = shared.read(state['response']['path'])
    original_clock = state['terminal']['finished_unix']
    disposition = grid.policy.previous.parent_disposition(request, response, original_clock,
                                                        state['config']['parent_model'])
    settings = grid.reflection_settings(response, request, shared.read(root / 'BROKER_CONFIG.json'),
                                        now=original_clock)
    require(settings['status'] == 'BOUND_FOR_LANE_DECODER', 'real_valid_envelope_regression')
    return dict(request=state['request'], response=state['response'], disposition=disposition,
                reflection_settings=settings, observed_unix=original_clock,
                reconstructed_after_missing_reference_failure=True,
                observation_clock_basis='RECORDED_FAILURE_UPPER_BOUND_AFTER_ORIGINAL_RESPONSE_READ',
                recovered_unix=time.time(), parent_redispatched=False)


def prepare(root, bundle):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_prepare_only')
    bind_references(bundle)
    state = interrupted(root)
    tests = shared.read(bundle / 'CPU_TESTS.json')
    require(tests['passed'] and not tests['cuda_initialized'] and
            tests['manifest_sha256'] == shared.sha(bundle / 'MANIFEST.json'), 'native_tested_bundle')
    folder = root / ERA
    require(not (folder / 'READY.json').exists(), 'no_duplicate_repair_prepare')
    parent_path = root / 'parent_received' / f'P{state["parent_number"]:04d}.json'
    require(not parent_path.exists(), 'no_parent_receipt_overwrite')
    recovered = recover_parent(root, state)
    shared.write(parent_path, recovered)
    paths = [root / 'SHARED_TERMINAL.json', root / 'SHARED_ACTIVATION.json',
             root / 'SHARED_LOADED.json', root / 'CONFIG.json', root / 'LEDGER.jsonl',
             root / 'CARRY.json', root / 'BROKER_CONFIG.json', parent_path,
             Path(state['capture']['path']), Path(state['request']['path']), Path(state['response']['path'])]
    receipt = dict(schema='R118_GRID_SHARED_NO_REPLAY_REPAIR_V1', root=str(root),
                   bundle=str(bundle), manifest_sha256=shared.sha(bundle / 'MANIFEST.json'),
                   tests=grid.ref(bundle / 'CPU_TESTS.json'), source_sha256=shared.sha(__file__),
                   state=state, recovered_parent=grid.ref(parent_path),
                   preserved_files={str(path.relative_to(root)):shared.sha(path) for path in paths},
                   terminal_filename=TERMINAL, bounds=run.inherited_bounds(state['config']),
                   local_optimizer_steps=0, original_calls_retried=0,
                   parent_requests_redispatched=0, created_unix=time.time())
    shared.write(folder / 'READY.json', receipt)
    print(json.dumps(grid.ref(folder / 'READY.json')))


def validate(root, initial=True):
    receipt = shared.read(root / ERA / 'READY.json')
    bundle = Path(receipt['bundle'])
    require(shared.sha(bundle / 'MANIFEST.json') == receipt['manifest_sha256'] and
            shared.sha(__file__) == receipt['source_sha256'], 'exact_repair_bundle_binding')
    require(shared.sha(receipt['tests']['path']) == receipt['tests']['sha256'], 'tests_unchanged')
    bind_references(bundle)
    run.validate(root)
    run.check_deadline('no_replay_repair')
    if initial:
        for name, expected in receipt['preserved_files'].items():
            require(shared.sha(root / name) == expected, 'preserved_failed_cursor:' + name)
        interrupted(root)
    return receipt


def continue_episode(life, task, ordinal, memory, capture, capture_ref, intervention):
    require(ordinal == 0 and capture['cycle'] == life.cycle and capture['task_id'] == task['id']
            and capture['status'] == 'COMPLETE', 'resume_only_saved_first_episode')
    state = grid.policy.game.initial(task)
    messages = [dict(role='system', content=grid.EPISODE), dict(role='user', content=json.dumps(dict(
        observation=grid.policy.public_observation(task, state), prior_own_reflections=memory), sort_keys=True))]
    require(capture['messages'] == messages and capture['cap'] == 384, 'exact_original_prompt_budget')
    first = deepcopy(capture['response'])
    first['reference'] = capture_ref
    remaining = 4096
    last = None
    for step in range(1, 17):
        if state['done'] or remaining <= 0:
            break
        if step == 1:
            reply = first
            life.event('child', reply['raw'], capture_ref['sha256'])
        else:
            reply = life.generate(task, 'episode', messages, min(384, remaining))
        remaining -= len(reply['token_ids'])
        messages.append(dict(role='assistant', content=reply['raw']))
        chosen = reply
        if step == 1:
            life.settings = intervention['reflection_settings']
            guidance = intervention['disposition']['guidance']
            if guidance:
                life.event('parent', guidance, intervention['response']['sha256'])
            if guidance and remaining > 0:
                messages.append(dict(role='user', content=guidance))
                chosen = life.generate(task, 'continuation', messages, min(384, remaining))
                remaining -= len(chosen['token_ids'])
                messages.append(dict(role='assistant', content=chosen['raw']))
        state, feedback, environment_ref = life.environment(task, state, chosen['raw'], 'experience', step)
        messages.append(dict(role='user', content=json.dumps(feedback, sort_keys=True)))
        if step == 1:
            grid.write(life.root / 'triples' / f'C{life.cycle:04d}_E{ordinal}.json', dict(
                before=reply['reference'], intervention=intervention, continuation=chosen['reference'],
                actual_environment=environment_ref, child_state=state, semantic_change='UNASSESSED'))
        last = chosen
    require(last is not None, 'episode_has_original_completed_response')
    return dict(task_id=task['id'], split='TRAIN', final_state=state, last=last['reference'],
                last_trace=last['raw'], original_task_success=state['success'], child_tokens=4096 - remaining)


def continue_cycle(life, tasks, memory, receipt):
    state = receipt['state']
    capture = shared.read(state['capture']['path'])
    intervention = shared.read(receipt['recovered_parent']['path'])
    def episode(actor, task, ordinal, prior):
        if ordinal == 0:
            return continue_episode(actor, task, ordinal, prior, capture, state['capture'], intervention)
        return grid.episode(actor, task, ordinal, prior)
    run.client.current(life.session)
    require(shared.read(life.root / 'shared_cycles' / f'{life.cycle:04d}' / 'COLLECTION.json') ==
            life.session, 'existing_collection_not_rewritten')
    require(not (Path(life.session['shared_root']) / f'generation_{life.session["generation"]:06d}' /
                 (life.session['branch'] + '.json')).exists(), 'no_existing_submission')
    resumed = FunctionType(grid.train_cycle.__code__, dict(grid.__dict__, episode=episode),
                           'continue_interrupted_train', grid.train_cycle.__defaults__)
    resumed(life, tasks, memory)
    life.engine.verify_base()
    return run.client.export_cycle(life.session, life.cycle)


def resident(root):
    receipt = validate(root)
    config = receipt['state']['config']
    run.validate(root, gpu=True)
    session = receipt['state']['session']
    run.client.current(session)
    engine = run.client.load_shared(session, model_dir=config['model_dir'], gpu_uuid=config['uuid'],
        check=run.check_deadline, predecessor_processes=(tuple(receipt['state']['loaded']['process']),))
    require(engine.loaded.optimizer is None, 'no_local_optimizer')
    shared.write(root / ERA / 'LOADED.json', dict(pid=os.getpid(), process=run.client.native.process_identity(),
        session=run.client.call_binding(session), cycle=receipt['state']['cycle'], local_optimizer_steps=0,
        continuation_after_capture=receipt['state']['capture'], observed_unix=time.time()))
    roster = shared.read(root / 'TRAIN.json')
    cycle = receipt['state']['cycle']
    last_completed = cycle - 1
    first_cycle = True
    life = None
    while time.time() < grid.TRAIN_END and (first_cycle or run.can_train(root)):
        run.check_deadline('continued_shared_cycle')
        memory = shared.read(root / 'CARRY.json')
        life = run.life_class(session['branch'])(root, engine, config, cycle, session)
        try:
            submission = (continue_cycle(life, run.cycle_tasks(roster, cycle), memory, receipt) if first_cycle
                          else run.client.run_cycle_and_submit(life, run.cycle_tasks(roster, cycle), memory))
        except grid.TrainWindowClosed as error:
            shared.write(root / 'cycles' / f'{cycle:04d}' / 'CLOCK_BOUNDARY.json', dict(reason=str(error),
                partial_cycle=True, all_completed_calls_preserved=True, submitted=False, optimizer_steps=0))
            break
        first_cycle = False
        shared.write(root / 'shared_cycles' / f'{cycle:04d}' / 'SUBMITTED.json', submission)
        next_session = run.client.wait_for_next(session, deadline=grid.policy.FINAL_UNIX, check=run.check_deadline)
        if next_session.get('status') == 'DEADLINE_WAITING_SHARED_CHECKPOINT':
            shared.write(root / 'SHARED_WAIT_DEADLINE.json', next_session)
            break
        reloaded = run.client.reload_shared(engine, session, next_session)
        session = next_session
        shared.write(root / 'shared_cycles' / f'{cycle:04d}' / 'RELOADED.json', reloaded)
        run.spawn_readout(root, cycle, 'dev', session)
        shared.write(root / 'cycles' / f'{cycle:04d}' / 'CYCLE_COMPLETE.json', dict(cycle=cycle,
            shared_generation=session['generation'], shared_checkpoint_sha256=session['checkpoint_sha256'],
            optimizer_owner='F1', local_optimizer_steps=0, optimizer_steps=0, finished_unix=time.time()))
        last_completed, cycle = cycle, cycle + 1
    engine.verify_base()
    torch = engine.torch
    del life, engine
    gc.collect()
    torch.cuda.empty_cache()
    while time.time() < grid.policy.FINAL_UNIX:
        time.sleep(min(5, grid.policy.FINAL_UNIX - time.time()))
    run.spawn_readout(root, last_completed, 'final_morning', session)
    shared.write(root / 'SHARED_COMPLETE.json', dict(completed_cycle=last_completed,
        shared_generation=session['generation'], local_optimizer_steps=0, original_counters_preserved=True,
        finished_unix=time.time()))


def guard(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard_only')
    receipt = validate(root)
    config = receipt['state']['config']
    folder = root / ERA
    with (folder / 'LOCK').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (folder / 'ONCE').mkdir()
        shared.write(folder / 'PRE_GPU.json', dict(ready=grid.ref(folder / 'READY.json'),
            bounds=receipt['bounds'], local_optimizer_steps=0, observed_unix=time.time()))
        try:
            for attempt in range(90):
                scan = run.scan(root)
                shared.write(folder / 'admission' / f'{attempt:03d}.json', scan)
                if scan['clear'] and scan['scanner_euid'] == 0 and not scan['blocking_reasons']:
                    break
                run.check_deadline('repair_admission')
                time.sleep(2)
            else:
                raise ValueError('strict_repair_admission_not_clear')
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=config['uuid'],
                PYTHONPATH=str(run.SOURCE) + ':' + str(run.SOURCE / 'gpu'), PYTHONDONTWRITEBYTECODE='1',
                HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
            command = ['timeout', '--signal=TERM', '--kill-after=2s',
                str(max(1, int(grid.END - time.time() - 5))) + 's', grid.PYTHON, '-B',
                str(Path(__file__).resolve()), 'resident', '--root', str(root)]
            with (folder / 'NATIVE.log').open('x') as log:
                child = subprocess.Popen(command, cwd=run.SOURCE, env=environment, stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            shared.write(folder / 'LAUNCH.json', dict(pid=child.pid, command=command, observed_unix=time.time()))
            code = child.wait()
            shared.write(root / TERMINAL, dict(status='COMPLETE' if code == 0 else 'FAILED',
                exit_code=code, local_optimizer_steps=0, finished_unix=time.time()))
        except BaseException as error:
            if not (root / TERMINAL).exists():
                shared.write(root / TERMINAL, dict(status='FAILED', error_type=type(error).__name__,
                    error=str(error), local_optimizer_steps=0, finished_unix=time.time()))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'validate', 'guard', 'resident'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--bundle', type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if args.action == 'prepare':
        require(args.bundle is not None, 'bundle_required')
        prepare(root, args.bundle.resolve(strict=True))
    elif args.action == 'validate':
        validate(root)
        print(json.dumps(dict(status='PASS', GPU=False)))
    else:
        (guard if args.action == 'guard' else resident)(root)


if __name__ == '__main__':
    main()
