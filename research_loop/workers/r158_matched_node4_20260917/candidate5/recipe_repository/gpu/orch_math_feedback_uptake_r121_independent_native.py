"""Independent LoRA/AdamW math residents with asynchronous parent consumption."""

import argparse
from dataclasses import replace
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_math_feedback_uptake_r121_independent as control
from gpu import orch_guided_native as native
from gpu import orch_guided_native_generation as generation
from gpu import orch_math_feedback_uptake_r118_preinfer as admission
from gpu import orch_r107_base_anchors_inventory as inventory
from gpu import orch_r109_route_engine as replay_engine


math, shared, require = control.math, control.shared, control.require
read, write, sha, ref = control.read, control.write, control.sha, control.ref


class Actor:
    purpose = 'episode'

    def __init__(self, loaded):
        self.loaded = loaded

    def __getattr__(self, name):
        return getattr(self.loaded.engine, name)

    def generate(self, messages, *, max_new_tokens):
        if self.purpose in ('reflection', 'presleep'):
            response = math.Engine.generate(self, messages, max_new_tokens=max_new_tokens)
        else:
            response = generation.generate(self.loaded, messages, max_prompt_tokens=16384-max_new_tokens,
                max_new_tokens=max_new_tokens)
            response.update(input_truncated=False, context_limit=16384,
                requested_generation_cap=max_new_tokens, effective_generation_cap=max_new_tokens)
        if response.get('reflection_guard'):
            response['reflection_guard']['fit_eligibility'] = 'SOURCE_ENCODER_CHECK_REQUIRED_NOT_AUTOMATIC'
        return response

    def batch(self, prompts, cap):
        return math.Engine.batch(self, prompts, cap)


def load(plan, checkpoint, check, readout=False):
    document = read(checkpoint['path'])
    require(sha(checkpoint['path']) == checkpoint['path_sha256'], 'exact_checkpoint_bytes')
    identity = native.bridge.AdapterIdentity.from_document(document['adapter']).verify()
    stage = native.bridge.StageBinding(plan['branch']+'_R121', native.bridge.ARMS[0], 0,
        'sealed_readout' if readout else 'training', identity, not readout, True, sha(Path(plan['root'])/'PLAN.json'))
    loaded = native.load_stage(stage, model_dir=math.MODEL, device='cuda:0', gpu_uuid=plan['uuid'],
        context=native.StageContext(private_guidance=() if readout else ('R121_PRIVATE_PARENT_TRAIN_ONLY',)),
        check=check, predecessor_processes=(tuple(document['source_process']),))
    engine = loaded.engine
    if not readout:
        require(sha(checkpoint['optimizer_path']) == checkpoint['optimizer_path_sha256'] == document['optimizer_rng_sha256'], 'exact_AdamW_checkpoint')
        payload = engine.torch.load(checkpoint['optimizer_path'], map_location='cpu', weights_only=False)
        parameters = native.development.enable_existing_adapter(engine)
        optimizer = engine.torch.optim.AdamW(list(parameters.values()), lr=3e-5,
            betas=(.9, .999), eps=1e-8, weight_decay=.01, foreach=False, fused=False)
        require(len(payload['optimizer']['param_groups']) == 1 and
            len(payload['optimizer']['param_groups'][0]['params']) == len(parameters), 'exact_optimizer_parameter_count')
        optimizer.load_state_dict(payload['optimizer'])
        for parameter, state in optimizer.state.items():
            for name in ('exp_avg', 'exp_avg_sq'):
                require(state[name].shape == parameter.shape, 'optimizer_slot_parameter_shape')
        steps = {int(state['step'].item()) for state in optimizer.state.values()}
        require(steps == {plan['contract']['initial_optimizer_steps']}, 'actual_inherited_AdamW_step')
        loaded.optimizer = optimizer
        engine.torch.manual_seed(plan['seed'])
        engine.torch.cuda.manual_seed_all(plan['seed'])
        engine.model.requires_grad_(False)
        engine.model.eval()
        loaded.binding = replace(loaded.binding, phase='collection')
        write(Path(plan['root'])/'OPTIMIZER_RESTORED.json', dict(step=next(iter(steps)),
            optimizer_source=checkpoint['optimizer_path'], optimizer_sha256=checkpoint['optimizer_path_sha256'],
            forked_independent_optimizer=True, historical_math_optimizer_continuity=False,
            rng_policy='EXPLICIT_NEW_BRANCH_STREAM', seed=plan['seed'], parameter_count=len(parameters),
            restored_unix=time.time(), actual_process=native.process_identity()))
    return Actor(loaded)


def checkpoint(actor, root, cycle):
    destination = Path(root)/'checkpoints'/f'{cycle:06d}'
    destination.mkdir(parents=True, exist_ok=False)
    engine = actor.loaded.engine
    engine.verify_base()
    adapter = destination/'adapter'
    engine.model.save_pretrained(adapter, safe_serialization=True, save_embedding_layers=False)
    parameters = {name: value for name, value in engine.model.named_parameters() if native.is_lora(name)}
    identity = native.bridge.AdapterIdentity(str(adapter), native.state_hash(parameters), math.direct.BASE_SHA,
        tuple((path.name, sha(path)) for path in sorted(adapter.iterdir()) if path.is_file())).verify()
    path = destination/'optimizer_rng.pt'
    engine.torch.save(dict(optimizer=actor.loaded.optimizer.state_dict(), cpu_rng=engine.torch.get_rng_state(),
        cuda_rng=engine.torch.cuda.get_rng_state_all()), path)
    document = dict(adapter=identity.document(), optimizer_rng_sha256=sha(path),
        source_process=native.process_identity(), cycle=cycle, complete=True, saved_unix=time.time())
    write(destination/'CHECKPOINT.json', document)
    result = dict(path=str(destination/'CHECKPOINT.json'), path_sha256=sha(destination/'CHECKPOINT.json'),
        optimizer_path=str(path), optimizer_path_sha256=sha(path))
    actor.loaded.binding = replace(actor.loaded.binding, adapter=identity)
    actor.loaded.observed = identity
    require(native.observe_adapter(engine, identity) == identity, 'actual_saved_adapter_mounted')
    math.atomic(Path(root)/'COMMITTED.json', dict(checkpoint=result, cycle=cycle, committed_unix=time.time()))
    return result


def child(plan, root, actor, output, task, experience, invitation, phase, cap, carry=None):
    deliveries = control.poll_parent(plan, root, experience, phase)
    messages = math.policy.messages(experience, invitation, carry)
    prefix = actor.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
    cap = min(cap, 16384-len(prefix))
    require(cap > 0, 'no_context_cropping')
    number = control.reserve(root, 'native', dict(phase=phase, split='TRAIN', task_id=task['id']))
    path = output/f'CALL_{number:08d}.json'
    current = read(Path(root)/'COMMITTED.json') if (Path(root)/'COMMITTED.json').exists() else None
    checkpoint_ref = current['checkpoint'] if current else plan['contract']['initial_checkpoint']
    request = dict(phase=phase, split='TRAIN', task_id=task['id'], messages=messages,
        requested_cap=cap, started_unix=time.time(), checkpoint_sha256=checkpoint_ref['path_sha256'],
        independent_branch=plan['branch'], source_question_sha256=task['question_sha256'])
    write(path.with_suffix('.request.json'), request)
    actor.purpose = phase
    try:
        if phase == 'reflection' and deliveries:
            response, settings = math.policy.reflection_generate(actor, messages, *deliveries[-1], now=time.time(), context_cap=cap)
        else:
            response, settings = actor.generate(messages, max_new_tokens=cap), None
        outcome = math.policy.previous.original.source.judge(task, response)
        call = dict(request, response=response, outcome=outcome, reflection_settings=settings,
            request_sha256=sha(path.with_suffix('.request.json')), status='COMPLETE', finished_unix=time.time())
        write(path, call)
        item = math.policy.event('child', response['raw'], 'TRAIN', call)
        experience.append(item)
        math.atomic(Path(root)/'LATEST_CHILD.json', dict(path=str(path), tokens=len(response['token_ids']),
            phase=phase, checkpoint_sha256=request['checkpoint_sha256'], completed_unix=time.time()))
        return response, item
    except BaseException as error:
        if not path.exists():
            write(path, dict(request, status='FAILED', error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise


def collect(plan, root, actor, cycle, tasks, carry):
    require(len(tasks) == 2 and len({task['id'] for task in tasks}) == 2
        and all(task['split'] == 'TRAIN' for task in tasks), 'exact_two_TRAIN_episodes')
    output = Path(root)/f'cycle{cycle:06d}'
    output.mkdir(exist_ok=False)
    write(output/'START.json', dict(cycle=cycle, episode_ids=[task['id'] for task in tasks], started_unix=time.time()))
    combined, original_responses = math.policy.Experience(), []
    for episode, task in enumerate(tasks):
        experience = math.policy.Experience()
        experience.append(math.policy.event('environment', task['question']+'\n\n'+math.policy.ENVIRONMENT, 'TRAIN', task['question_sha256']))
        response, item = child(plan, root, actor, output, task, experience,
            math.policy.previous.original.EPISODE.format(question=task['question']), 'episode', 2048, carry)
        outcome = math.policy.previous.original.source.judge(task, response)
        original_responses.append(response)
        experience.append(math.policy.event('environment', 'Checker feedback delivered to you: '+json.dumps(outcome), 'TRAIN', outcome))
        control.append_parent(plan, root, task, experience, cycle, episode, 'experience')
        response, item = child(plan, root, actor, output, task, experience, math.policy.previous.OPEN_TURN, 'open_turn', 1024)
        observations = math.environment(experience, task, response)
        write(output/f'OPEN_ENVIRONMENT_E{episode}.json', dict(observations=observations, actual_environment_executed=True))
        for event in experience.events:
            combined.append(event)
    child(plan, root, actor, output, tasks[-1], combined, math.policy.previous.original.PRESLEEP, 'presleep', 4096)
    response, carry = child(plan, root, actor, output, tasks[-1], combined, math.policy.previous.original.REFLECTION, 'reflection', 3072)
    rows = []
    for path in sorted(output.glob('CALL_*.json')):
        if path.name.endswith('.request.json'):
            continue
        call = read(path)
        require(call['status'] == 'COMPLETE' and call['split'] == 'TRAIN', 'actual_child_TRAIN_only')
        row = replay_engine.replay_row(call, path, sha(path))
        row.update(recorded_outcome=call['outcome'], negative_example=call['outcome'].get('correct') is False,
            observed_fact_endorsement=False, outcome_conditioning='ACTUAL_PREFIX_FEEDBACK_ONLY_NOT_RETROACTIVE')
        rows.append(row)
    require(len(rows) == 6 and {row['episode_id'] for row in rows} == {task['id'] for task in tasks}, 'all_six_sourced_utterances_both_episodes')
    write(output/'ROWS.json', rows)
    write(output/'EXPERIENCE.json', combined.events)
    write(output/'COLLECTION_COMPLETE.json', dict(rows=6, episode_ids=[task['id'] for task in tasks],
        own_reflection=carry, original_responses=original_responses,
        parent_wait_seconds=0, finished_unix=time.time(), negative_outcomes_retained=True))
    return output, rows, carry


def fresh_readout(root, plan, checkpoint_ref, key, split='DEV'):
    output = Path(root)/('sealed' if split == 'FINAL' else 'readouts')/key
    if output.exists():
        return dict(status='EXISTING_ATTEMPT_NEVER_RETRIED')
    output.mkdir(parents=True, exist_ok=False)
    binding = dict(root=str(root), checkpoint=checkpoint_ref, parent_free=True, train_rows=False,
        split=split, key=key, actual_resident_process=native.process_identity(), count=8 if split == 'FINAL' else 20)
    write(output/'BINDING.json', binding)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'])
    with (output/'process.log').open('x') as log:
        process = subprocess.Popen([sys.executable, '-B', '-m', control.MODULE, 'readout', '--root', str(root),
            '--binding', str(output/'BINDING.json')], env=environment, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        identity = math.common.process_identity(Path('/proc')/str(process.pid))
        write(output/'LAUNCH.json', dict(identity=identity, started_unix=time.time()))
        try:
            process.wait(timeout=max(.1, min(900, plan['bounds']['hard_end_unix']-time.time())))
        except subprocess.TimeoutExpired:
            math.common.stop_owned(process, identity)
        result = dict(status='COMPLETE' if process.returncode == 0 else 'FAILED_NO_RETRY',
            returncode=process.returncode, finished_unix=time.time(), outcome_never_controls_life=True)
        write(output/'PROCESS_RESULT.json', result)
    return result


def readout(root, binding_path):
    plan = control.validate(root)
    binding = read(binding_path)
    output = Path(binding_path).parent
    require(binding['root'] == str(root) and binding['parent_free'] is True and binding['train_rows'] is False, 'isolated_eval_binding')
    require(tuple(binding['actual_resident_process']) != native.process_identity(), 'fresh_native_readout_process')
    split = binding['split']
    require(split in ('DEV', 'FINAL'), 'readout_only')
    if split == 'FINAL':
        schedule = next(item for item in plan['final_schedule'] if item['key'] == binding['key'])
        require(time.time() >= schedule['due_unix'], 'no_early_new_FINAL')
    def check(label):
        require(time.time() < plan['bounds']['hard_end_unix'], 'readout_lease_wall:'+label)
    math.mounted(Path(plan['original_root']), 'independent_readout_before')
    actor = load(plan, binding['checkpoint'], check, readout=True)
    write(output/'BEFORE.json', dict(adapter=native.observe_adapter(actor.loaded.engine, actor.loaded.observed).document(),
        process=native.process_identity(), parent_calls=0, optimizer_updates=0))
    tasks = control.checked(plan['dev' if split == 'DEV' else 'final'])
    require(len(tasks) == 8, 'fixed_eight_readout_tasks')
    completed = 0
    def batch(selected, purpose, previous=None, cap=2048):
        nonlocal completed
        prompts = [math.policy.readout_messages(task, purpose, None if previous is None else previous[position])
            for position, task in enumerate(selected)]
        first = control.reserve(root, 'native', dict(split=split, key=binding['key'], purpose=purpose), len(selected))
        request = dict(ids=[task['id'] for task in selected], messages=prompts, purpose=purpose, cap=cap,
            checkpoint_sha256=binding['checkpoint']['path_sha256'], parent_free=True, never_rows_or_buffer=True)
        write(output/f'BATCH_{first:08d}.request.json', request)
        responses = actor.batch(prompts, cap)
        for position, (task, response) in enumerate(zip(selected, responses)):
            write(output/f'CALL_{first+position:08d}.json', dict(task_id=task['id'], split=split,
                purpose=purpose, messages=prompts[position], response=response, status='COMPLETE',
                raw_saved_before_parser=True, token_count=len(response['token_ids']), completed_unix=time.time()))
            completed += 1
        return responses
    try:
        responses = batch(tasks, 'held')
        if split == 'DEV':
            batch(tasks, 'open_turn', responses, 1024)
            batch(tasks[:2], 'focused')
            cycle = int(binding['key'].split('C')[-1])
            probes = [dict(task, split='PROBE') for task in control.checked(plan['train'])[cycle-1]]
            originals = read(Path(root)/f'cycle{cycle:06d}'/'COLLECTION_COMPLETE.json')['original_responses']
            batch(probes, 'open_turn', originals, cap=1024)
        require(completed == binding['count'], 'complete_readout_denominator')
        write(output/'COMPLETE.json', dict(completed=completed, native=binding['count'], parent=0,
            optimizer_steps=0, finished_unix=time.time(), full_raw_and_tokens=True))
    finally:
        write(output/'AFTER.json', dict(adapter=native.observe_adapter(actor.loaded.engine, actor.loaded.observed).document(),
            mounted=math.mounted(Path(plan['original_root']), 'independent_readout_after'),
            completed=completed, planned=binding['count']))


def resident(root):
    plan = control.validate(root)
    lifetime = (Path(root)/'LIFE.lock').open('a')
    fcntl.flock(lifetime, fcntl.LOCK_EX | fcntl.LOCK_NB)
    def check(label):
        require(time.time() < plan['bounds']['train_end_unix'], 'lease_native_wall:'+label)
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(TimeoutError('owned_lease_signal')))
    write(Path(root)/'MOUNTED_BEFORE.json', math.mounted(Path(plan['original_root']), 'independent_before'))
    actor = load(plan, plan['contract']['initial_checkpoint'], check)
    write(Path(root)/'LOADED.json', dict(actual_process=native.process_identity(), loaded_unix=time.time(),
        adapter=native.observe_adapter(actor.loaded.engine, actor.loaded.observed).document(), optimizer_restored=True))
    anchors_by_family, receipt = inventory.build_inventory(plan['anchors'], actor.tokenizer, 16384)
    anchors = [entry for family in sorted(anchors_by_family) for entry in anchors_by_family[family]]
    require(len(anchors) == 42, 'all42_anchors')
    write(Path(root)/'ANCHORS.json', receipt)
    history = control.checked(plan['initial_history'])
    carry = control.checked(plan['initial_carry'])
    tasks_by_cycle = control.checked(plan['train'])
    cycle, last_checkpoint = plan['contract']['next_cycle'], plan['contract']['initial_checkpoint']
    try:
        while time.time() < plan['bounds']['train_end_unix']:
            for scheduled in plan['final_schedule']:
                if time.time() >= scheduled['due_unix']:
                    fresh_readout(root, plan, last_checkpoint, scheduled['key'], 'FINAL')
            require(cycle <= len(tasks_by_cycle), 'prospective_cohort_extension_required_before_dispatch')
            output, rows, carry = collect(plan, root, actor, cycle, tasks_by_cycle[cycle-1], carry)
            sleep = output/'sleep'
            sleep.mkdir()
            started = time.time()
            before = native.state_hash({name:value for name,value in actor.model.named_parameters() if native.is_lora(name)})
            actor.loaded.binding = replace(actor.loaded.binding, phase='training')
            metrics = shared.train(actor.loaded.engine, actor.loaded.optimizer, rows, history, anchors, sleep, check)
            after = native.state_hash({name:value for name,value in actor.model.named_parameters() if native.is_lora(name)})
            require(metrics['optimizer_steps'] > 0 and before != after, 'actual_LoRA_sleep_update')
            last_checkpoint = checkpoint(actor, root, cycle)
            actor.loaded.binding = replace(actor.loaded.binding, phase='collection')
            counters = read(Path(root)/'COUNTERS.json')
            for name in ('optimizer_steps', 'child_token_exposures', 'anchor_token_exposures'):
                counters[name] += metrics[name]
            math.atomic(Path(root)/'COUNTERS.json', counters)
            write(sleep/'COMPLETE.json', dict(metrics, checkpoint=last_checkpoint, started_unix=started,
                finished_unix=time.time(), before_adapter_sha256=before, after_adapter_sha256=after,
                cumulative_optimizer_steps=counters['optimizer_steps'], independent_optimizer=True))
            history.extend(rows)
            write(output/'CARRY.json', carry)
            fresh_readout(root, plan, last_checkpoint, f'DEV_C{cycle:06d}')
            write(output/'COMPLETE.json', dict(cycle=cycle, checkpoint=last_checkpoint,
                finished_unix=time.time(), next_cycle=cycle+1, no_shared_barrier=True))
            cycle += 1
        for scheduled in plan['final_schedule']:
            if time.time() >= scheduled['due_unix']:
                fresh_readout(root, plan, last_checkpoint, scheduled['key'], 'FINAL')
        write(Path(root)/'TERMINAL.json', dict(status='LEASE_BOUNDARY', checkpoint=last_checkpoint,
            counters=read(Path(root)/'COUNTERS.json'), finished_unix=time.time()))
    except BaseException as error:
        if not (Path(root)/'TERMINAL.json').exists():
            write(Path(root)/'TERMINAL.json', dict(status='FAILED', error_type=type(error).__name__, error=str(error),
                last_committed_checkpoint=last_checkpoint, counters=read(Path(root)/'COUNTERS.json'),
                no_retry=True, finished_unix=time.time()))
        raise


def scan(root):
    plan = control.validate(root)
    return admission.fresh_scan(control.ORIGINAL, plan['index'])


def guard(root):
    root = Path(root)
    plan = control.validate(root)
    write(root/'GUARD_STARTED.json', dict(identity=math.common.process_identity(Path('/proc')/str(os.getpid())), started_unix=time.time()))
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(control.SOURCE), sys.executable, '-B', '-m', control.MODULE, 'scan', '--root', str(root)]
    process = subprocess.run(command, text=True, capture_output=True, timeout=180)
    require(process.returncode == 0, 'privileged_scan_failed:'+process.stderr[-1500:])
    report = json.loads(process.stdout)
    write(root/'ADMISSION.json', report)
    require(report['clear'] and report['scanner_euid'] == 0 and report['gpu']['uuid'] == plan['uuid'], 'strict_full_admission_no_waiver')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONDONTWRITEBYTECODE='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONPATH=str(control.SOURCE), OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    with (root/'native.log').open('x') as log:
        actor = subprocess.Popen([sys.executable, '-B', '-m', control.MODULE, 'resident', '--root', str(root)],
            env=environment, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        identity = math.common.process_identity(Path('/proc')/str(actor.pid))
        write(root/'LAUNCH.json', dict(identity=identity, started_unix=time.time(), plan=ref(root/'PLAN.json')))
        try:
            actor.wait(timeout=max(.1, plan['bounds']['hard_end_unix']-time.time()))
        except subprocess.TimeoutExpired:
            math.common.stop_owned(actor, identity)
        write(root/'GUARD_TERMINAL.json', dict(returncode=actor.returncode, finished_unix=time.time(), identity=identity))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('guard', 'resident', 'scan', 'readout'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--binding', type=Path)
    arguments = parser.parse_args()
    if arguments.phase == 'scan':
        print(json.dumps(scan(arguments.root)))
    elif arguments.phase == 'readout':
        readout(arguments.root, arguments.binding)
    else:
        globals()[arguments.phase](arguments.root)
