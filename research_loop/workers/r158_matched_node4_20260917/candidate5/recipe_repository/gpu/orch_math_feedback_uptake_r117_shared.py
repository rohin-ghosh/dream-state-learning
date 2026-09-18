"""Prospective math shared-child boundary client; no launcher or optimizer."""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import time

from gpu import orch_guided_native as native
from gpu import orch_guided_native_generation as generation
from gpu import orch_math_feedback_uptake_r115_native as math
from gpu import orch_r109_route_engine as route
from gpu import orch_r116_shared_learner as shared


require = shared.require
PHASES = ('episode', 'open_turn', 'episode', 'open_turn', 'presleep', 'reflection')
BRANCHES = {'F2': math.policy.ROOT / 'lane1', 'A2': math.policy.ROOT / 'lane5'}


def prepare(shared_root, branch):
    require(branch in BRANCHES, 'math_shared_branch_only')
    with shared.locked(shared_root) as root:
        config = shared.read(root / 'CONFIG.json')
        state = shared.read(root / 'STATE.json')
        require(config['owner'] == 'F1', 'sole_optimizer_owner_F1')
        require(state['config_sha256'] == shared.sha(root / 'CONFIG.json'), 'shared_config_hash')
        require(type(state['generation']) is int and state['generation'] >= 0, 'integer_generation')
        spec = config['branches'][branch]
        require(Path(spec['root']).resolve() == BRANCHES[branch], 'registered_math_root')
        checkpoint = shared.checked_checkpoint(state['checkpoint'])
        document = shared.read(checkpoint['path'])
        require(document['complete'] is True, 'complete_shared_checkpoint')
        require(document['optimizer_rng_sha256'] == checkpoint['optimizer_path_sha256'], 'owner_optimizer_binding')
        identity = native.bridge.AdapterIdentity.from_document(document['adapter'])
        identity.verify()
        require(identity.base_sha256 == math.direct.BASE_SHA, 'original_frozen_base')
        return dict(shared_root=str(root.resolve()), branch=branch, branch_root=spec['root'],
            generation=state['generation'], checkpoint_sha256=checkpoint['path_sha256'],
            checkpoint=checkpoint, adapter=identity.document(), config_sha256=state['config_sha256'],
            train_ids=list(spec['train_ids']), source_process=document['source_process'], optimizer_owner='F1')


def current(session):
    root = Path(session['shared_root'])
    state = shared.read(root / 'STATE.json')
    require(shared.sha(root / 'CONFIG.json') == session['config_sha256'] == state['config_sha256'],
        'shared_configuration_changed')
    require(type(session['generation']) is int and type(state['generation']) is int
        and state['generation'] == session['generation']
        and state['checkpoint'] == session['checkpoint']
        and state['checkpoint']['path_sha256'] == session['checkpoint_sha256'], 'shared_child_changed')
    return state


def binding(session):
    return dict(shared_generation=session['generation'], shared_checkpoint_sha256=session['checkpoint_sha256'],
        shared_branch=session['branch'], shared_config_sha256=session['config_sha256'])


class SharedEngine:
    purpose = 'episode'

    def __init__(self, loaded, session):
        self.loaded, self.session = loaded, deepcopy(session)
        self.poisoned = False
        self.verify_base()

    def __getattr__(self, name):
        return getattr(self.loaded.engine, name)

    def verify_base(self):
        require(not self.poisoned and self.loaded.optimizer is None, 'readonly_math_shared_actor')
        require(self.loaded.binding.adapter.document() == self.session['adapter'], 'mounted_session_adapter')
        return self.loaded.verify_unchanged()

    def generate(self, messages, *, max_new_tokens):
        current(self.session)
        require(not self.poisoned and self.loaded.optimizer is None, 'readonly_math_shared_actor')
        require(not any(parameter.requires_grad for parameter in self.model.parameters()), 'frozen_actor_parameters')
        if self.purpose in ('reflection', 'presleep'):
            require(self.loaded.binding.phase == 'collection', 'reflection_only_train_collection')
            response = math.Engine.generate(self, messages, max_new_tokens=max_new_tokens)
            response['reflection_guard']['fit_eligibility'] = 'UNASSESSED_SOURCE_PRESERVED_OWNER_ENCODER_CHECKS'
        else:
            response = generation.generate(self.loaded, messages, max_prompt_tokens=16384-max_new_tokens,
                max_new_tokens=max_new_tokens)
            response.update(input_truncated=False, context_limit=16384,
                requested_generation_cap=max_new_tokens, effective_generation_cap=max_new_tokens)
        current(self.session)
        return response

    def batch(self, prompts, cap):
        require(self.loaded.binding.phase == 'sealed_readout', 'batch_only_parent_free_readout')
        current(self.session)
        self.verify_base()
        return math.Engine.batch(self, prompts, cap)


def load(session, *, model_dir, gpu_uuid, check, readout=False, loader=None):
    current(session)
    index = {'F2': 1, 'A2': 5}[session['branch']]
    require(gpu_uuid == math.policy.DEVICES[index], 'allocated_branch_uuid')
    require(Path(model_dir).resolve() == Path(math.MODEL).resolve(), 'same_verified_cached_base_directory')
    mounted = math.mounted(Path(session['branch_root']), 'r117_shared_load_before')
    require(mounted['uuid'] == gpu_uuid, 'mounted_branch_uuid')
    checkpoint = shared.checked_checkpoint(session['checkpoint'])
    document = shared.read(checkpoint['path'])
    require(document['adapter'] == session['adapter'], 'published_adapter_binding')
    identity = native.bridge.AdapterIdentity.from_document(session['adapter'])
    require(identity.base_sha256 == math.direct.BASE_SHA, 'original_frozen_base')
    stage = native.bridge.StageBinding(session['branch'], native.bridge.ARMS[0], session['generation'],
        'sealed_readout' if readout else 'collection', identity, not readout, readout, session['config_sha256'])
    def forward_check(label):
        check(label)
    loaded = (loader or native.load_stage)(stage, model_dir=model_dir, device='cuda:0', gpu_uuid=gpu_uuid,
        context=native.StageContext(private_guidance=() if readout else ('R117_MATH_PRIVATE_PARENT',)),
        check=forward_check, predecessor_processes=(tuple(session['source_process']),))
    current(session)
    actor = SharedEngine(loaded, session)
    actor.mount_receipt = dict(mounted, adapter=actor.verify_base().document(), optimizer=None, **binding(session))
    return actor


def reload_at_boundary(engine, session, submission):
    require(engine.loaded.binding.phase == 'collection', 'collection_boundary_only')
    engine.verify_base()
    prior = engine.session
    require(session['shared_root'] == prior['shared_root'] and session['branch'] == prior['branch']
        and session['branch_root'] == prior['branch_root']
        and session['config_sha256'] == prior['config_sha256']
        and session['generation'] == prior['generation'] + 1, 'next_common_generation_only')
    receipt_path = Path(submission['path'])
    require(receipt_path.resolve() == Path(prior['shared_root']).resolve() /
        f"generation_{prior['generation']:06d}" / (prior['branch'] + '.json'), 'own_barrier_receipt')
    require(shared.sha(receipt_path) == submission['sha256'], 'accepted_submission_hash')
    receipt = shared.read(receipt_path)
    require(receipt['generation'] == prior['generation'] and receipt['branch'] == prior['branch']
        and receipt['checkpoint_sha256'] == prior['checkpoint_sha256'], 'completed_previous_submission')
    current(session)
    shared.checked_checkpoint(session['checkpoint'])
    require(shared.read(session['checkpoint']['path'])['adapter'] == session['adapter'], 'published_adapter_binding')
    identity = native.bridge.AdapterIdentity.from_document(session['adapter'])
    identity.verify()
    require(identity.base_sha256 == math.direct.BASE_SHA, 'original_frozen_base')
    require(shared.read(Path(identity.path) / 'adapter_config.json') ==
        shared.read(Path(prior['adapter']['path']) / 'adapter_config.json'), 'unchanged_adapter_recipe')
    from safetensors import safe_open
    selected = {name.replace('.default.weight', '.weight'): parameter
        for name, parameter in engine.model.named_parameters() if native.is_lora(name)}
    with safe_open(Path(identity.path) / 'adapter_model.safetensors', framework='pt', device='cpu') as archive:
        require(set(selected) == set(archive.keys()), 'exact_shared_adapter_tensor_keys')
        require(all(list(archive.get_slice(name).get_shape()) == list(parameter.shape)
            for name, parameter in selected.items()), 'exact_shared_adapter_tensor_shapes')
        engine.poisoned = True
        with engine.torch.no_grad():
            for name, parameter in selected.items():
                parameter.copy_(archive.get_tensor(name).to(device=parameter.device, dtype=parameter.dtype))
    observed = native.observe_adapter(engine.loaded.engine, identity)
    require(observed == identity, 'actual_reloaded_adapter_hash')
    current(session)
    engine.loaded.binding = replace(engine.loaded.binding, cycle=session['generation'], adapter=identity)
    engine.loaded.observed = observed
    engine.session = deepcopy(session)
    engine.poisoned = False
    engine.verify_base()
    return dict(**binding(session), actual_adapter=observed.document(), optimizer=None,
        resident_process=native.process_identity(), observed_unix=time.time())


def child_call(lane, engine, output, task, experience, invitation, phase, cap, carry=None, settings=None):
    session = engine.session
    current(session)
    require(Path(lane).resolve() == Path(session['branch_root']).resolve(), 'registered_branch_capture')
    require(phase in PHASES and task['split'] == 'TRAIN' and task['id'] in session['train_ids'], 'bound_train_only')
    require(engine.loaded.binding.phase == 'collection', 'collection_not_readout_capture')
    prompt = math.policy.messages(experience, invitation, carry)
    tokens = engine.tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True, return_dict=False)
    actual_cap = min(cap, 16384-len(tokens))
    require(actual_cap > 0, 'uncropped_context_has_generation_space')
    number = math.reserve(lane, 'native', 1, dict(phase=phase, task_id=task['id'], split='TRAIN', **binding(session)))
    path = Path(output) / f'CALL_{number:04d}.json'
    request = dict(phase=phase, split='TRAIN', task_id=task['id'], started_unix=time.time(),
        requested_cap=cap, context_limited_cap=actual_cap, messages=prompt,
        source_question_sha256=task['question_sha256'], **binding(session))
    request_path = path.with_suffix('.request.json')
    shared.write(request_path, request)
    engine.purpose = phase
    try:
        if phase == 'reflection' and settings:
            response, applied = math.policy.reflection_generate(engine, prompt, *settings,
                now=time.time(), context_cap=actual_cap)
        else:
            response, applied = engine.generate(prompt, max_new_tokens=actual_cap), None
        require(response['messages'] == prompt and response['prompt_tokens'] == len(tokens), 'actual_causal_prefix')
        current(session)
        item = math.policy.event('child', response['raw'], 'TRAIN', dict(request=request, response=response))
        experience.append(item)
        shared.write(path, dict(request, response=response, reflection_settings=applied,
            request_sha256=shared.sha(request_path), finished_unix=time.time(), status='COMPLETE'))
        return response, item
    except BaseException as error:
        if not path.exists():
            shared.write(path, dict(request, error=dict(type=type(error).__name__, message=str(error)),
                request_sha256=shared.sha(request_path), finished_unix=time.time(), status='FAILED'))
        raise


def export_cycle(session, output, episode_ids):
    current(session)
    require(len(episode_ids) == 2 and len(set(episode_ids)) == 2
        and all(identifier in session['train_ids'] for identifier in episode_ids), 'two_distinct_bound_episodes')
    output = Path(output).resolve()
    require(output.is_relative_to(Path(session['branch_root']).resolve()), 'cycle_inside_branch')
    paths = sorted(output.glob('CALL_[0-9]*.json'))
    paths = [path for path in paths if not path.name.endswith('.request.json')]
    requests = sorted(output.glob('CALL_*.request.json'))
    require(len(paths) == len(PHASES) and {path.with_suffix('.request.json') for path in paths} == set(requests),
        'all_six_train_attempts_required')
    calls = [shared.read(path) for path in paths]
    require(tuple(call['phase'] for call in calls) == PHASES, 'two_sequential_episodes_then_reflection')
    require([call['task_id'] for call in calls] == [episode_ids[0]] * 2 + [episode_ids[1]] * 4,
        'exact_cycle_episode_assignment')
    rows = []
    config = shared.read(Path(session['shared_root']) / 'CONFIG.json')
    for path, call in zip(paths, calls):
        require(call['status'] == 'COMPLETE', 'failed_attempt_preserved_no_silent_drop')
        require(call['split'] == 'TRAIN' and type(call.get('shared_generation')) is int
            and all(call.get(key) == value for key, value in binding(session).items()), 'prospective_shared_capture_only')
        request_path = path.with_suffix('.request.json')
        require(shared.sha(request_path) == call['request_sha256'], 'predispatch_request_hash')
        request = shared.read(request_path)
        require(all(call.get(key) == value for key, value in request.items())
            and request['messages'] == call['response']['messages'], 'immutable_predispatch_capture')
        row = route.replay_row(call, path, shared.sha(path))
        shared.validate_row(row, config['branches'][session['branch']], config['excluded_ids'],
            generation=session['generation'], checkpoint_sha256=session['checkpoint_sha256'])
        rows.append(row)
    result = shared.submit(session['shared_root'], session['branch'], session['generation'],
        session['checkpoint_sha256'], episode_ids, rows)
    return dict(result, source_calls=len(rows), source_tokens=sum(len(row['source_generated_token_ids']) for row in rows),
        optimizer_owner='F1', branch_weight_updates=0)


def collect_cycle(lane, engine, cycle, tasks, carry=None):
    lane = Path(lane)
    current(engine.session)
    require(type(cycle) is int and 1 <= cycle <= math.policy.CYCLES, 'original_cycle_cap')
    require(time.time() < math.NATIVE-120, 'original_native_wall')
    require(tasks == shared.read(lane.parent/'TRAIN.json')[cycle-1], 'unchanged_prospective_cycle_cohort')
    require(len(tasks) == 2 and len({task['id'] for task in tasks}) == 2, 'two_distinct_bound_episodes')
    output = lane / f'cycle{cycle:03d}'
    output.mkdir(exist_ok=False)
    started = time.time()
    shared.write(output/'SHARED_BEFORE.json', dict(**binding(engine.session),
        actual_adapter=engine.verify_base().document(), optimizer=None, started_unix=started))
    combined, originals = math.policy.Experience(), []
    try:
        for episode, task in enumerate(tasks):
            experience = math.policy.Experience()
            experience.append(math.policy.event('environment', task['question']+'\n\n'+math.policy.ENVIRONMENT,
                'TRAIN', task['question_sha256']))
            response, item = child_call(lane, engine, output, task, experience,
                math.policy.previous.original.EPISODE.format(question=task['question']), 'episode', 2048, carry)
            originals.append(response)
            verdict = math.policy.previous.original.source.judge(task, response)
            experience.append(math.policy.event('environment', 'Checker feedback delivered to you: '+json.dumps(verdict),
                'TRAIN', verdict))
            math.parent(lane, task, experience, cycle, episode, 'experience')
            response, item = child_call(lane, engine, output, task, experience,
                math.policy.previous.OPEN_TURN, 'open_turn', 1024)
            observations = math.environment(experience, task, response)
            shared.write(output/f'OPEN_ENVIRONMENT_E{episode}.json',
                dict(observations=observations, actual_environment_executed=True))
            math.parent(lane, task, experience, cycle, episode, 'open_turn')
            for event in experience.events:
                combined.append(event)
        child_call(lane, engine, output, tasks[-1], combined, math.policy.previous.original.PRESLEEP, 'presleep', 4096)
        settings = math.parent(lane, tasks[-1], combined, cycle, 1, 'presleep_metacognition')
        response, carry = child_call(lane, engine, output, tasks[-1], combined,
            math.policy.previous.original.REFLECTION, 'reflection', 8192, settings=settings)
        math.parent(lane, tasks[-1], combined, cycle, 1, 'reflection')
        shared.write(output/'TRAIN_EXPERIENCE.json', combined.events)
        shared.write(output/'BOUNDARY.json', dict(original_responses=originals, own_reflection=carry,
            source_history_sha256=math.policy.digest(combined.events), **binding(engine.session),
            label='SHARED_COLLECTION_NOT_YET_SLEEP', weight_updates=0, optimizer_steps=0, finished_unix=time.time()))
        engine.verify_base()
        submission = export_cycle(engine.session, output, [task['id'] for task in tasks])
        shared.write(output/'TRAIN_COMPLETE.json', dict(submission=submission, **binding(engine.session),
            started_unix=started, finished_unix=time.time(), readout_complete=False, sleep_complete=False))
        return dict(carry=carry, submission=submission, original_responses=originals)
    except BaseException as error:
        shared.write(output/'TRAIN_FAILED.json', dict(error=str(error), error_type=type(error).__name__,
            **binding(engine.session), finished_unix=time.time(), no_retry=True, all_captures_preserved=True))
        raise
