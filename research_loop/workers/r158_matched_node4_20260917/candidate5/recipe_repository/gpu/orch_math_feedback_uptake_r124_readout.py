"""Same-prompt checkpoint probes and memory-isolated independent math successors."""

import argparse
from copy import deepcopy
from dataclasses import replace
import fcntl
import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import FunctionType

from gpu import orch_math_feedback_uptake_r121_independent_native as old
from gpu import orch_math_feedback_uptake_r123_f2_recovery as recovery


control, math, native, shared = old.control, old.math, old.native, old.shared
read, write, sha, ref, require = old.read, old.write, old.sha, old.ref, old.require
SOURCE = Path(__file__).resolve().parents[1]
ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r124_readout_20260915_attempt1')
MODULE = 'gpu.orch_math_feedback_uptake_r124_readout'
PREDECESSORS = {'F2': recovery.ROOT, 'A2': Path('/localhome/local-rohing/orch_math_feedback_uptake_r121_independent_20260915_attempt3/lane5')}


def validate_prompts(tasks, prompts):
    require(len(tasks) == len(prompts) == 8 and len({task['id'] for task in tasks}) == 8, 'exact_DEV8')
    require(all(task['split'] == 'DEV' for task in tasks), 'DEV_only_no_FINAL')
    require(prompts == [math.policy.readout_messages(task, 'held') for task in tasks], 'same_existing_prompts')
    require(all(len(messages) == 2 and [item['role'] for item in messages] == ['system', 'user'] for messages in prompts), 'empty_context_two_messages_only')
    return math.policy.digest(prompts)


def checkpoint_before(root, cycle, after):
    rows = read(root / f'cycle{cycle:06d}/ROWS.json')
    before_hashes = set()
    for row in rows:
        require(sha(row['source_call_path']) == row['source_call_sha256'], 'actual_source_capture')
        call = read(row['source_call_path'])
        shared.replay.verify_source(row, call)
        before_hashes.add(call['checkpoint_sha256'])
    require(len(before_hashes) == 1 and after['path_sha256'] not in before_hashes, 'one_real_pre_sleep_checkpoint')
    previous = root / f'checkpoints/{cycle - 1:06d}/CHECKPOINT.json'
    if previous.exists():
        result = dict(path=str(previous), path_sha256=sha(previous), optimizer_path=str(previous.with_name('optimizer_rng.pt')),
            optimizer_path_sha256=sha(previous.with_name('optimizer_rng.pt')))
    else:
        result = read(root / 'PLAN.json')['contract']['initial_checkpoint']
    require(result['path_sha256'] == next(iter(before_hashes)), 'predecessor_matches_actual_collected_inputs')
    return result


def prepare(branch):
    from gpu import orch_math_feedback_uptake_r124_boundary as boundary
    require(branch in PREDECESSORS, 'owned_math_only')
    source_root = PREDECESSORS[branch]
    prior = read(source_root / 'PLAN.json')
    root = ROOT / branch
    root.mkdir(parents=True, exist_ok=False)
    tasks = control.checked(prior['dev'])
    prompts = [math.policy.readout_messages(task, 'held') for task in tasks]
    prompt_hash = validate_prompts(tasks, prompts)
    write(root / 'PROMPTS.json', prompts)
    manifest, tests = ref(SOURCE / 'R124_SOURCE_MANIFEST.json'), ref(SOURCE / 'R124_CPU_TESTS.json')
    request = dict(schema='R124_MATH_SAFE_MEASUREMENT_V1', branch=branch, root=str(root),
        predecessor_root=str(source_root), predecessor_plan=ref(source_root / 'PLAN.json'),
        actor=boundary.owned_actor(source_root), source_root=str(SOURCE), source_manifest=manifest, tests=tests,
        prompts=ref(root / 'PROMPTS.json'), prompt_semantic_sha256=prompt_hash, dev=prior['dev'],
        index=prior['index'], uuid=prior['uuid'], bounds=prior['bounds'],
        additional_native_cap=16, additional_parent_cap=0, decoder=dict(cap=2048, do_sample=False, num_beams=1,
            batch_size=8, repetition_penalty=1.0, template='UNCHANGED_HELD'),
        selection='LATEST_FULLY_SAVED_SLEEP_AT_OWNED_READOUT_BOUNDARY',
        comparison='RESPONSE_CHANGE_NOT_IMPROVEMENT_OR_MATCHED_CONTROL_EFFECT',
        new_probe_keys_only=True, preserve_failed_DEV=True, created_unix=time.time(),
        boundary_expires_unix=min(time.time()+2700, prior['bounds']['train_end_unix']-1200))
    write(root / 'REQUEST.json', request)
    return ref(root / 'REQUEST.json')


def build_successor(request, release):
    root, prior_root = Path(request['root']), Path(request['predecessor_root'])
    prior = read(prior_root / 'PLAN.json')
    cycle = release['cycle']
    after = release['checkpoint']
    before = checkpoint_before(prior_root, cycle, after)
    history = control.checked(prior['initial_history'])
    for path in sorted(prior_root.glob('cycle*/sleep/COMPLETE.json')):
        if int(path.parent.parent.name[5:]) <= cycle:
            history.extend(read(path.parent.parent / 'ROWS.json'))
    for row in history:
        require(sha(row['source_call_path']) == row['source_call_sha256'], 'preserved_rehearsal_source')
    require(len({row['source_call_sha256'] for row in history}) == len(history), 'no_duplicate_history_append')
    carry = read(prior_root / f'cycle{cycle:06d}/CARRY.json')
    write(root / 'HISTORY_INITIAL.json', history)
    write(root / 'CARRY_INITIAL.json', carry)
    write(root / 'COUNTERS.json', release['counters'])
    for name in ('parent_pending', 'parent_delivered'):
        for path in (prior_root / name).glob('*.json'):
            write(root / name / path.name, read(path))
    plan = deepcopy(prior)
    plan.update(root=str(root), source_root=str(SOURCE), source_manifest=request['source_manifest'], tests=request['tests'],
        initial_history=ref(root / 'HISTORY_INITIAL.json'), initial_carry=ref(root / 'CARRY_INITIAL.json'),
        release=ref(root / 'RELEASED.json'), predecessor_root=str(prior_root),
        predecessor_plan=request['predecessor_plan'], probe_request=ref(root / 'REQUEST.json'),
        preserved=release['preserved'], paired_checkpoints=dict(before=before, after=after),
        paired_sleep_cycle=cycle, additional_probe_native_cap=16, created_unix=time.time())
    plan['contract'].update(initial_checkpoint=after, initial_optimizer_steps=release['counters']['optimizer_steps'],
        inherited_counters=release['counters'], next_cycle=cycle+1)
    write(root / 'PLAN.json', plan)
    return ref(root / 'PLAN.json')


def validate(root):
    root = Path(root)
    require(root in [ROOT / branch for branch in PREDECESSORS], 'owned_successor_root')
    plan = read(root / 'PLAN.json')
    require(plan['root'] == str(root) and plan['source_root'] == str(SOURCE), 'actual_source_root')
    for key in ('source_manifest', 'tests', 'initial_history', 'initial_carry', 'release', 'probe_request', 'train', 'dev', 'final', 'clock'):
        require(sha(plan[key]['path']) == plan[key]['sha256'], 'immutable_' + key)
    require(read(plan['tests']['path'])['passed'], 'own_CPU_tests')
    for name, digest in read(plan['source_manifest']['path']).items():
        require(sha(SOURCE / name) == digest, 'frozen_source:' + name)
    for name, digest in plan['preserved'].items():
        require(sha(Path(plan['predecessor_root']) / name) == digest, 'preserved_old_charge_and_state:' + name)
    for checkpoint in plan['paired_checkpoints'].values():
        require(sha(checkpoint['path']) == checkpoint['path_sha256'] and
            sha(checkpoint['optimizer_path']) == checkpoint['optimizer_path_sha256'], 'actual_saved_checkpoints')
    require(time.time() < plan['bounds']['hard_end_unix'], 'unchanged_lease_wall')
    return plan


def probe(root, binding_path):
    plan = validate(root)
    binding = read(binding_path)
    output = Path(binding_path).parent
    require(binding['role'] in ('before', 'after') and binding['checkpoint'] == plan['paired_checkpoints'][binding['role']], 'exact_paired_checkpoint')
    request = control.checked(plan['probe_request'])
    tasks, prompts = control.checked(request['dev']), control.checked(request['prompts'])
    require(validate_prompts(tasks, prompts) == request['prompt_semantic_sha256'], 'identical_empty_context_prompts')
    def check(label):
        require(time.time() < min(binding['deadline_unix'], plan['bounds']['train_end_unix']), 'bounded_probe:' + label)
    write(output / 'MOUNTED_BEFORE.json', math.mounted(Path(plan['original_root']), 'paired_DEV_before'))
    actor = old.load(plan, binding['checkpoint'], check, readout=True)
    write(output / 'LOADED.json', dict(process=native.process_identity(), adapter=actor.loaded.observed.document(),
        checkpoint=binding['checkpoint'], parent_free=True, optimizer_loaded=False, empty_context=True))
    count = 0
    try:
        first = control.reserve(root, 'native', dict(split='DEV', key=binding['key'], purpose='R124_MATCHED_EMPTY_CONTEXT', checkpoint=binding['checkpoint']), 8)
        write(output / 'BATCH.request.json', dict(ids=[task['id'] for task in tasks], messages=prompts,
            first_native_reservation=first, checkpoint=binding['checkpoint'], cap=2048,
            prompt_semantic_sha256=request['prompt_semantic_sha256'], started_unix=time.time(), empty_context=True))
        responses = actor.batch(prompts, 2048)
        for position, (task, response) in enumerate(zip(tasks, responses)):
            write(output / f'CALL_{first+position:08d}.json', dict(task_id=task['id'], split='DEV', purpose='held',
                messages=prompts[position], response=response, token_count=len(response['token_ids']),
                status='COMPLETE', checkpoint=binding['checkpoint'], raw_saved_before_parser=True,
                completed_unix=time.time(), parent_free=True, empty_context=True, never_rows_or_buffer=True))
            count += 1
        require(count == 8, 'full_eight_denominator')
        write(output / 'COMPLETE.json', dict(completed=8, parent=0, optimizer_steps=0,
            prompt_semantic_sha256=request['prompt_semantic_sha256'], checkpoint=binding['checkpoint'], finished_unix=time.time()))
    finally:
        write(output / 'AFTER.json', dict(completed=count, planned=8,
            adapter=native.observe_adapter(actor.loaded.engine, actor.loaded.observed).document(),
            mounted=math.mounted(Path(plan['original_root']), 'paired_DEV_after')))


def paired_probe(root, plan):
    for role in ('before', 'after'):
        output = root / 'paired_DEV' / role
        require(not output.exists(), 'new_probe_attempt_never_retried')
        output.mkdir(parents=True)
        binding = dict(role=role, key=f'R124_{role.upper()}_C{plan["paired_sleep_cycle"]}_DEV8',
            checkpoint=plan['paired_checkpoints'][role], deadline_unix=min(time.time()+600, plan['bounds']['train_end_unix']))
        write(output / 'BINDING.json', binding)
        with (output / 'process.log').open('x') as stream:
            process = subprocess.Popen([sys.executable, '-B', '-m', MODULE, 'probe', '--root', str(root), '--binding', str(output / 'BINDING.json')],
                env=os.environ.copy(), stdout=stream, stderr=subprocess.STDOUT)
            identity = math.common.process_identity(Path('/proc') / str(process.pid))
            write(output / 'LAUNCH.json', dict(identity=identity, started_unix=time.time()))
            try:
                code = process.wait(timeout=max(.1, binding['deadline_unix']-time.time()))
            except subprocess.TimeoutExpired:
                math.common.stop_owned(process, identity)
                code = process.returncode
            write(output / 'PROCESS_RESULT.json', dict(returncode=code, status='COMPLETE' if code == 0 else 'FAILED_NO_RETRY', finished_unix=time.time()))
    write(root / 'PAIRED_PROBE_FINISHED.json', dict(roles={role:read(root/'paired_DEV'/role/'PROCESS_RESULT.json')['status'] for role in ('before','after')},
        comparison='RESPONSE_CHANGE_NOT_IMPROVEMENT_OR_MATCHED_CONTROL_EFFECT', finished_unix=time.time()))


def restore(plan, check):
    captured = []
    loader = FunctionType(old.load.__code__, dict(old.load.__globals__, write=lambda path, value: captured.append(value)),
        'restore_saved_branch', old.load.__defaults__)
    actor = loader(plan, plan['contract']['initial_checkpoint'], check)
    saved = actor.torch.load(plan['contract']['initial_checkpoint']['optimizer_path'], map_location='cpu', weights_only=False)
    require(len(saved['cuda_rng']) == 1, 'saved_single_GPU_RNG')
    actor.torch.set_rng_state(saved['cpu_rng'])
    actor.torch.cuda.set_rng_state_all(saved['cuda_rng'])
    require(actor.torch.equal(actor.torch.get_rng_state(), saved['cpu_rng']) and
        actor.torch.equal(actor.torch.cuda.get_rng_state(), saved['cuda_rng'][0]), 'actual_saved_RNG_restored')
    write(Path(plan['root']) / 'OPTIMIZER_RESTORED.json', dict(captured[0], branch=plan['branch'],
        historical_math_optimizer_continuity=True, forked_independent_optimizer=False,
        rng_policy='EXACT_SAVED_PREDECESSOR_CPU_CUDA_RNG', restored_unix=time.time()))
    return actor


def offloaded_readout(root, actor, plan, checkpoint, key, split='DEV'):
    output = Path(root)/('sealed' if split == 'FINAL' else 'readouts')/key
    if output.exists() or (Path(root)/'offloads'/(key+'.json')).exists():
        return dict(status='EXISTING_ATTEMPT_NEVER_RETRIED')
    actor.loaded.optimizer.zero_grad(set_to_none=True)
    actor.model.to('cpu')
    for state in actor.loaded.optimizer.state.values():
        for name, value in state.items():
            if actor.torch.is_tensor(value):
                state[name] = value.to('cpu')
    gc.collect()
    actor.torch.cuda.empty_cache()
    write(root / 'offloads' / (key + '.json'), dict(allocated_bytes=actor.torch.cuda.memory_allocated(),
        reserved_bytes=actor.torch.cuda.memory_reserved(), optimizer_preserved=True, checkpoint=checkpoint))
    try:
        return old.fresh_readout(root, plan, checkpoint, key, split)
    finally:
        actor.model.to('cuda:0')
        for parameter, state in actor.loaded.optimizer.state.items():
            for name in ('exp_avg', 'exp_avg_sq'):
                if name in state:
                    state[name] = state[name].to(parameter.device)
        require(native.observe_adapter(actor.loaded.engine, actor.loaded.observed) == actor.loaded.observed, 'exact_state_returned_after_readout')


def resident(root):
    root = Path(root)
    plan = validate(root)
    with (root / 'LIFE.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        paired_probe(root, plan)
        def check(label):
            require(time.time() < plan['bounds']['train_end_unix'], 'lease_wall:' + label)
        write(root / 'MOUNTED_BEFORE.json', math.mounted(Path(plan['original_root']), 'successor_before'))
        actor = restore(plan, check)
        write(root / 'LOADED.json', dict(actual_process=native.process_identity(),
            checkpoint=plan['contract']['initial_checkpoint'], loaded_unix=time.time()))
        inventory, receipt = old.inventory.build_inventory(plan['anchors'], actor.tokenizer, 16384)
        anchors = [entry for family in sorted(inventory) for entry in inventory[family]]
        write(root / 'ANCHORS.json', receipt)
        history, carry = control.checked(plan['initial_history']), control.checked(plan['initial_carry'])
        tasks = control.checked(plan['train'])
        cycle, checkpoint = plan['contract']['next_cycle'], plan['contract']['initial_checkpoint']
        try:
            while time.time() < plan['bounds']['train_end_unix']:
                require(cycle <= len(tasks), 'prospective_cohort_extension_required_before_dispatch')
                output, rows, carry = old.collect(plan, root, actor, cycle, tasks[cycle-1], carry)
                sleep = output / 'sleep'
                sleep.mkdir()
                actor.loaded.binding = replace(actor.loaded.binding, phase='training')
                started = time.time()
                metrics = shared.train(actor.loaded.engine, actor.loaded.optimizer, rows, history, anchors, sleep, check)
                checkpoint = old.checkpoint(actor, root, cycle)
                actor.loaded.binding = replace(actor.loaded.binding, phase='collection')
                counters = read(root / 'COUNTERS.json')
                for name in ('optimizer_steps', 'child_token_exposures', 'anchor_token_exposures'):
                    counters[name] += metrics[name]
                math.atomic(root / 'COUNTERS.json', counters)
                write(sleep / 'COMPLETE.json', dict(metrics, checkpoint=checkpoint, started_unix=started,
                    finished_unix=time.time(), cumulative_optimizer_steps=counters['optimizer_steps'], independent_optimizer=True))
                history.extend(rows)
                write(output / 'CARRY.json', carry)
                offloaded_readout(root, actor, plan, checkpoint, f'DEV_C{cycle:06d}')
                write(output / 'COMPLETE.json', dict(cycle=cycle, next_cycle=cycle+1, checkpoint=checkpoint, finished_unix=time.time()))
                cycle += 1
                for scheduled in plan['final_schedule']:
                    if time.time() >= scheduled['due_unix'] and not (Path(plan['predecessor_root']) / 'sealed' / scheduled['key']).exists():
                        offloaded_readout(root, actor, plan, checkpoint, scheduled['key'], 'FINAL')
            write(root / 'TERMINAL.json', dict(status='LEASE_BOUNDARY', counters=read(root / 'COUNTERS.json'), checkpoint=checkpoint))
        except BaseException as error:
            write(root / 'TERMINAL.json', dict(status='FAILED', error=str(error), error_type=type(error).__name__,
                last_committed_checkpoint=checkpoint, counters=read(root / 'COUNTERS.json'), finished_unix=time.time()))
            raise


def configure():
    control.ROOT, control.SOURCE, control.MODULE, control.validate = ROOT, SOURCE, MODULE, validate


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'guard', 'resident', 'scan', 'probe', 'readout'))
    parser.add_argument('--branch', choices=('F2', 'A2'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--binding', type=Path)
    args = parser.parse_args()
    configure()
    if args.phase == 'prepare':
        print(json.dumps(prepare(args.branch)))
    elif args.phase == 'scan':
        print(json.dumps(old.scan(args.root)))
    elif args.phase == 'guard':
        old.guard(args.root)
    elif args.phase == 'probe':
        probe(args.root, args.binding)
    elif args.phase == 'readout':
        old.readout(args.root, args.binding)
    else:
        resident(args.root)
