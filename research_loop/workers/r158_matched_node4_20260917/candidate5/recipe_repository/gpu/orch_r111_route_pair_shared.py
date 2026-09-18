"""R116 successor route lives using the eight-branch shared learner."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_guided_native as native
from gpu import orch_r111_parent_provider as hook
from gpu import orch_r109_route_engine as causal
from gpu import orch_route_parent_campaign_run as campaign
from gpu import orch_r107_base_anchors_inventory as anchors_module
from gpu import orch_r111_route_boundary as boundary
from organism_v6 import orch_full_rich as gym
from organism_v6 import orch_l2_shared as shared
from organism_v6 import orch_r107_parented_replay as replay


SCHEMA = 'R115V4_F1_MATCHED_FRESH_BASE_ROUTE'
PRINCIPLES_SHA = '5a6a3d28a2f0c9f99dd76873496a07468075509b4451373d90c11ce8d8b363f2'
HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
UUIDS = {0: 'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a',
         4: 'GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d'}
MODELS = {0: 'claude-fable-5-1', 4: 'openai/openai/gpt-6-astra'}
MODEL = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
ANCHOR_ROOT = '/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1'
ANCHOR_SHA = '2ad09dbe9673f95cbe92cd41e70d83635702b615fb7295b8b3f850e9ee674753'
MORNING_CUT = 1789491600
HARD_WALL = 1789596240
JUDGE_SHA = '0466c6fa8bbd8c75f8e2d4c625498423835b2b5285e58c4f703069e8b6c532fd'
OPEN_PROMPT = ('The task is over; the environment is still here. You may continue if there is something '
               'you want to pursue, or stop. To interact, end with READ EVENT <listedaddress> or '
               'ROUTE <listedport>; to stop, end with STOP.')
EPISODE_PROMPT = (
    'Work through the public route task using the records you actually read and the receipts you actually receive. '
    'Reason in ordinary prose when that helps you decide how to proceed. You may address your parent. '
    'Do not invent an observation or treat an unread address as knowledge. '
    'End your response with a valid action on its final nonempty line: READ EVENT <listedaddress> '
    'or ROUTE <listedport>. Nothing follows the action.'
)
PRESLEEP_PROMPT = 'Take some time with what you just experienced and what you want to carry with you.'
REFLECTION_PROMPT = (
    'Reflect freely on these actual experiences in a way that could help your future self. '
    'Stay with what you perceived rather than repeating passages or inventing experience.'
)
HELD_PROMPT = 'Use the public task and available records. End with READ EVENT <listedaddress> or ROUTE <listedport>.'
require, digest, read, sha, write = hook.require, hook.digest, hook.load, hook.file_sha, campaign.write


def prompts():
    return dict(episode=EPISODE_PROMPT, presleep=PRESLEEP_PROMPT, reflection=REFLECTION_PROMPT)


def parent_result(response, request, provider_model, now=None):
    now = time.time() if now is None else now
    missing = dict(status='MISSING', parent_text='', tag=None, intervention_class=None,
                   functional_change='UNKNOWN')
    if response is None or now > request['lane_deadline_unix']:
        return dict(missing, reason='missing_or_late')
    if response.get('id') != request['id'] or response.get('request_sha256') != digest(request):
        return dict(missing, reason='binding_mismatch')
    if response.get('status') == 'MISSING' or response.get('error'):
        return dict(missing, reason='provider_missing')
    if response.get('actual_model') != provider_model:
        return dict(missing, reason='provider_identity_mismatch')
    plan = response.get('plan') or {}
    metadata = response.get('parent_metadata') or {}
    head_settings = (response.get('prompt_binding') or {}).get('head_settings', {})
    text = plan.get('message')
    if text == '[SILENT]' or response.get('status') == 'SILENT':
        return dict(status='SILENT', parent_text='', tag=None, intervention_class=None,
                    functional_change='UNKNOWN', actual_model=response['actual_model'], head_settings=head_settings)
    if response.get('status') != 'COMPLETE' or not isinstance(text, str) or not text.strip():
        return dict(missing, reason='malformed_reply')
    if metadata.get('tag') not in ('ADD', 'STOP', 'SHIFT'):
        return dict(missing, reason='explicit_text_plan_conversion_required')
    receipt = response.get('transcript_receipt', {})
    if not (receipt.get('node_only') and receipt.get('all_verified')):
        return dict(missing, reason='node_archive_not_verified')
    return dict(status='COMPLETE', parent_text=text, tag=metadata['tag'],
                intervention_class=metadata['intervention_class'], actual_model=response['actual_model'],
                receipt=receipt, functional_change='UNKNOWN', head_settings=head_settings)


def public_payload(root, plan, task, cycle, episode_index, messages, phase, capture_sha256):
    require(phase in ('experience', 'presleep', 'reflection', 'open_turn'), 'no_held_parent')
    require(all(set(message) == {'role', 'content'} for message in messages), 'public_messages_only')
    events = []
    for message in messages:
        if message['role'] == 'system':
            continue
        events.append(dict(sequence=len(events), actor='child' if message['role'] == 'assistant' else 'environment',
                           text=message['content'], source_sha256=capture_sha256, visibility='TRAIN_PUBLIC'))
    require(any(event['actor'] == 'child' for event in events), 'actual_child_before_parent')
    return dict(schema='r111_train_public_v1', life_id=root.name, cycle=cycle, episode=episode_index,
                phase='presleep_metacognition' if phase == 'presleep' else phase, game='route',
                task_id=task['id'], task_provenance=dict(split='TRAIN', task_sha256=digest(task['task']),
                                                       cohort_sha256=plan['cohort_sha256']), events=events)


def reserve(root, kind, detail):
    plan = read(root/'PLAN.json')
    with (root/'RESERVATIONS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        rows = [json.loads(line) for line in stream if line.strip()]
        number = 1 + sum(row['kind'] == kind for row in rows)
        require(number <= plan['bounds'][kind.lower()+'_calls'], 'declared_lifetime_call_bound')
        stream.write(json.dumps(dict(kind=kind, number=number, unix=time.time(), **detail), sort_keys=True)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    return number


def parent_call(root, plan, task, cycle, episode_index, phase, messages, capture_sha256):
    number = reserve(root, 'PARENT', dict(cycle=cycle, phase=phase))
    identity = f'{number:06d}_F1_C{cycle:04d}'
    deadline = min(time.time()+plan['parent_wait_seconds'], plan['bounds']['hard_end_unix'])
    payload = public_payload(root, plan, task, cycle, episode_index, messages, phase, capture_sha256)
    request = dict(id=identity, payload=payload, payload_sha256=digest(payload), lane_deadline_unix=deadline)
    queue = root/'parent_queue'
    queue.mkdir(exist_ok=True)
    write(queue/(identity+'.request.json'), request)
    response_path = queue/(identity+'.response.json')
    while time.time() < deadline:
        if response_path.exists():
            try:
                result = parent_result(read(response_path), request, plan['provider'])
            except (ValueError, OSError):
                result = parent_result(None, request, plan['provider'])
            break
        time.sleep(.1)
    else:
        result = parent_result(None, request, plan['provider'])
    write(queue/(identity+'.observed.json'), dict(result, id=identity, request_sha256=digest(request),
                                                 observed_unix=time.time(), no_retry=True))
    return dict(result, id=identity, request_sha256=digest(request))


def source_inventory(assets):
    cohort = read(assets/'COHORT.json')
    source = read(assets/'SOURCE.json')
    require(source['cohort_sha256'] == campaign.policy.digest(cohort), 'original_source_cohort_hash')
    train_worlds = [world for group in cohort['train'] for world in group]
    held_worlds = cohort['held'][0]
    require(len(held_worlds) == 4, 'four_held_worlds_eight_tasks')
    final_worlds = cohort['held'][1]
    worlds = train_worlds + held_worlds + final_worlds
    collections = {item['world']['master']: item for item in source['collections']}
    store = {}
    for world in worlds:
        collection = collections[world['master']]
        require(collection['world'] == world, 'existing_world_source_binding')
        campaign.policy.runtime(world['master'])['replay_collection'](collection)
        for record in collection['records']:
            if record['accepted']:
                store[record['edge']['event']] = record['event']['raw']
    train = [dict(world=world, task=task, id='TRAIN-'+digest(task)[:24])
             for world in train_worlds for task in shared.tasks(world)]
    held = [dict(world=world, task=task, id='HELD-'+digest(task)[:24])
            for world in held_worlds for task in shared.tasks(world)]
    final = [dict(world=world, task=task, id='FINAL-'+digest(task)[:24])
             for world in final_worlds for task in shared.tasks(world)]
    require(len(final) == 8 and not {digest(row['task']) for row in final}.intersection(
        digest(row['task']) for row in train+held), 'separate_final_never_train_or_dev')
    require(len(held) == 8 and not {row['id'][6:] for row in train}.intersection(row['id'][5:] for row in held),
            'fixed_disjoint_held')
    final_addresses = {edge['event'] for world in final_worlds for edge in world['edges']}
    final_store = {address: text for address, text in store.items() if address in final_addresses}
    store = {address: text for address, text in store.items() if address not in final_addresses}
    return dict(train=train, held=held, store=store, sealed_final=dict(tasks=final, store=final_store),
                source_sha256=sha(assets/'SOURCE.json'),
                original_cohort_sha256=sha(assets/'COHORT.json'), same_pair_source=True)


def fresh_adapter(destination, model_dir, seed_value=8203):
    import torch
    import peft
    from transformers import AutoConfig, AutoModelForCausalLM
    require(not torch.cuda.is_initialized(), 'fresh_adapter_cpu_only')
    config = AutoConfig.from_pretrained(model_dir, local_files_only=True, trust_remote_code=False)
    require(config.model_type == 'qwen2' and config.max_position_embeddings >= 16384, 'original_qwen_context')
    recipe = peft.LoraConfig(r=8, lora_alpha=16, lora_dropout=.05,
        target_modules=list(native.source.native.TARGET_MODULES), bias='none', task_type='CAUSAL_LM',
        init_lora_weights=True, use_rslora=False, use_dora=False)
    with torch.device('meta'):
        model = peft.get_peft_model(AutoModelForCausalLM.from_config(config, trust_remote_code=False), recipe)
    torch.manual_seed(seed_value)
    for module in model.modules():
        if hasattr(module, 'lora_A') and 'default' in module.lora_A:
            module.lora_A['default'].to_empty(device='cpu')
            module.lora_B['default'].to_empty(device='cpu')
            module.reset_lora_parameters('default', init_lora_weights=True)
    selected = {name: value for name, value in model.named_parameters() if native.is_lora(name)}
    require(selected and all(value.device.type == 'cpu' for value in selected.values()), 'fresh_adapter_materialized')
    require(all(torch.count_nonzero(value).item() == 0 for name, value in selected.items() if '.lora_B.' in name),
            'fresh_zero_delta_adapter')
    require(all(value.device.type == 'meta' for name, value in model.named_parameters() if not native.is_lora(name)),
            'no_pretrained_adapter_or_base_tensor_loaded')
    destination.mkdir(parents=True, exist_ok=False)
    model.save_pretrained(destination, safe_serialization=True, save_embedding_layers=False)
    identity = native.bridge.AdapterIdentity(str(destination), native.state_hash(selected), BASE_SHA,
        tuple((path.name, sha(path)) for path in sorted(destination.iterdir()) if path.is_file())).verify()
    write(destination.parent/'FRESH_BIRTH.json', dict(adapter=identity.document(), seed=seed_value,
        no_l1_seed=True, no_l2_seed=True, zero_delta=True, gpu_initialized=torch.cuda.is_initialized(),
        base_config_sha256=sha(Path(model_dir)/'config.json'), initialized_unix=time.time()))
    return identity


def prepare(root, assets, physical, parent_prompt, principles, battleplan, *, native_calls,
            parent_calls, cycles, hard_end_unix, judge_sha256):
    require(physical in UUIDS, 'paired_owned_slots_only')
    require(root.is_absolute() and root.resolve() == root and root.name.startswith('orch_r111_'), 'new_owned_root')
    require(not (root/'PLAN.json').exists(), 'fresh_segment_no_quota_reset')
    require(time.time() < hard_end_unix <= HARD_WALL, 'prospective_node5_lease_bound')
    require(all(type(value) is int and value > 0 for value in (native_calls, parent_calls, cycles)), 'explicit_bounds')
    require(sha(principles) == PRINCIPLES_SHA, 'principles_v2_exact')
    require(judge_sha256 == JUDGE_SHA, 'published_v4_judge_hash_required')
    adapter = fresh_adapter(root/'birth_adapter', MODEL)
    inventory = source_inventory(assets)
    root.mkdir(parents=True, exist_ok=True)
    write(root/'SEALED_FINAL.json', inventory.pop('sealed_final'))
    os.chmod(root/'SEALED_FINAL.json', 0o600)
    write(root/'COHORT.json', inventory)
    require(sha(Path(ANCHOR_ROOT)/'ANCHOR_MANIFEST.json') == ANCHOR_SHA, 'shared42_anchor_manifest')
    source_paths = [Path(__file__), Path(hook.__file__), Path(campaign.__file__), Path(causal.__file__),
                    Path(native.__file__), Path(gym.__file__), Path(shared.__file__), Path(replay.__file__),
                    Path(anchors_module.__file__)]
    plan = dict(schema=SCHEMA, physical=physical, uuid=UUIDS[physical], provider=MODELS[physical],
                host_sha256=HOST_SHA, root=str(root), model_dir=MODEL,
                mode='FROZEN_BASE_FRESH_RANK8_NO_L1_NO_L2_SEED', initial_adapter=adapter.document(),
                initial_optimizer='fresh_AdamW_at_this_life_birth_then_persistent', seed=8203,
                assets=str(assets), principles_path=str(principles), principles_sha256=PRINCIPLES_SHA,
                battleplan_path=str(battleplan), battleplan_sha256=sha(battleplan),
                parent_prompt_path=str(parent_prompt), parent_prompt_sha256=sha(parent_prompt),
                child_prompts=prompts(), child_prompts_sha256=digest(prompts()),
                held_ids=[row['id'] for row in inventory['held']], held_sha256=digest(inventory['held']),
                held_prompt=HELD_PROMPT, held_prompt_sha256=digest(HELD_PROMPT), judge_sha256=judge_sha256,
                cohort_sha256=sha(root/'COHORT.json'),
                anchor_root=ANCHOR_ROOT, anchor_manifest_sha256=ANCHOR_SHA, anchor_count=42, anchor_lambda=.25,
                rehearsal_presentations_per_later_sleep=1, comparison='PARENTING_SYSTEMS_NOT_MODEL_ONLY',
                final_sha256=sha(root/'SEALED_FINAL.json'), final_readouts=('sleep0', '2026-09-15T17:00:00Z'),
                final_visibility='NEVER_PARENT_HEAD_OR_EXCHANGE', morning_cut_unix=MORNING_CUT,
                decoder=dict(do_sample=False, num_beams=1, context=16384, generation=4096,
                             readout_max_new_tokens=2048, reflection_no_repeat_ngram_size=16),
                style='training-wheels, supportive', nudging='none', reflection='short', cadence='segment',
                parent_wait_seconds=120, parent_missing='MISSING_CONTINUE', silent='VALID_NO_INTERVENTION',
                episodes_per_sleep=2, presentations_per_row=16, earlier_life_rehearsal=True,
                sleep0_required=True, readout_fresh_process=True, readout_parent_free=True,
                controls='NO_NEW_CONTROL_TRIPLE', outcome_gates=False,
                bounds=dict(native_calls=native_calls, parent_calls=parent_calls, cycles=cycles,
                            hard_end_unix=hard_end_unix, gpu_hours=(hard_end_unix-time.time())/3600,
                            lease_end_unix=HARD_WALL+21600, lease_margin_seconds=21600),
                source_files={str(path.resolve()): sha(path) for path in source_paths})
    require(plan['bounds']['hard_end_unix'] <= plan['bounds']['lease_end_unix']-21600, 'lease_margin')
    write(root/'PLAN.json', plan)
    pair_keys = ('mode', 'initial_adapter', 'initial_optimizer', 'seed', 'child_prompts_sha256',
                 'held_ids', 'held_sha256', 'held_prompt_sha256', 'decoder', 'style', 'nudging',
                 'reflection', 'cadence', 'parent_wait_seconds', 'episodes_per_sleep',
                 'presentations_per_row', 'earlier_life_rehearsal', 'parent_prompt_sha256',
                 'principles_sha256', 'judge_sha256', 'anchor_manifest_sha256', 'anchor_lambda',
                 'rehearsal_presentations_per_later_sleep', 'final_sha256')
    contract = {key: plan[key] for key in pair_keys}
    contract['initial_adapter'] = {key: value for key, value in adapter.document().items() if key != 'path'}
    write(root/'PAIR_CONTRACT.json', contract)
    write(root/'SLEEP0_STATUS.json', dict(status='NOT_RUN', no_measured_baseline_yet=True))
    return dict(root=str(root), plan_sha256=sha(root/'PLAN.json'), physical=physical, mode=plan['mode'],
                child_prompts=prompts(), held_ids=plan['held_ids'], held_sha256=plan['held_sha256'],
                sleep0='NOT_RUN', provider_calls=0, gpu_launched=False)


def verify(root, *, gpu=False):
    plan = read(root/'PLAN.json')
    require(plan['schema'] == SCHEMA and plan['root'] == str(root.resolve()), 'plan_root_binding')
    for path, expected in plan['source_files'].items():
        require(sha(path) == expected, 'immutable_source')
    if plan.get('shared_learner'):
        from gpu import orch_r111_route_shared as pooled
        for module in (pooled, pooled.coordinator):
            path = str(Path(module.__file__).resolve())
            require(plan['source_files'].get(path) == sha(path), 'shared_successor_source_pinned')
    require(sha(root/'COHORT.json') == plan['cohort_sha256'], 'cohort_unchanged')
    require(sha(root/'SEALED_FINAL.json') == plan['final_sha256'], 'sealed_final_unchanged')
    require(sha(plan['principles_path']) == PRINCIPLES_SHA, 'fixed_principles')
    if gpu:
        require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'hashed_node5')
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['uuid'], 'exact_uuid_cvd')
        require((root/'ADMISSION.json').is_file() and (root/'PUBLICATION.json').is_file(), 'admission_publication')
        if plan['physical'] == 0:
            approval = read(root/'ROHIN_GO.json')
            require(approval.get('authorization') == 'WATCHER_RELAYED_ROHIN_DONE'
                    and approval.get('plan_sha256') == sha(root/'PLAN.json')
                    and approval.get('parent_prompt_sha256') == plan['parent_prompt_sha256']
                    and bool(approval.get('source_reference')), 'R115_EXPLICIT_DONE_NO_SILENCE_WINDOW')
    return plan


def generate(engine, messages, cap=4096, reflection=False):
    engine.check('generation')
    engine.model.requires_grad_(False)
    engine.model.eval()
    tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
    cap = min(cap, 16384-len(tokens))
    require(cap > 0, 'no_prompt_cropping_context_exhausted')
    tensors = engine.torch.tensor([tokens], dtype=engine.torch.long, device=engine.device)
    configuration = engine.transformers.GenerationConfig(do_sample=False, num_beams=1, max_new_tokens=cap,
        use_cache=True, eos_token_id=engine.tokenizer.eos_token_id, pad_token_id=engine.tokenizer.pad_token_id,
        no_repeat_ngram_size=16 if reflection else 0)
    with engine.torch.inference_mode():
        output = engine.model.generate(input_ids=tensors, attention_mask=engine.torch.ones_like(tensors),
                                       generation_config=configuration)
    require(output[0, :len(tokens)].tolist() == tokens, 'full_actual_native_prefix')
    tail = output[0, len(tokens):].tolist()
    terminal = bool(tail) and tail[-1] == engine.tokenizer.eos_token_id
    raw = engine.tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False,
                                  clean_up_tokenization_spaces=False)
    return dict(messages=messages, raw=raw, token_ids=tail, terminal=terminal,
                truncated=not terminal and len(tail) == cap, input_truncated=False,
                full_prompt_prefix_verified=True, prompt_tokens=len(tokens),
                prompt_token_ids_sha256=digest(tokens), effective_generation_cap=cap)


def episode(world, task, generate_call, store, system=EPISODE_PROMPT):
    namespace = dict(gym.episode.__globals__, SYSTEM=system, GUIDANCE='')
    return FunctionType(gym.episode.__code__, namespace, 'episode')(world, task, generate_call, store)


def reflection_cap(settings, default=1024):
    if settings.get('status') != 'BOUND_REQUESTED_SETTINGS':
        return default
    requested = settings.get('fields', {}).get('REFLECTION', {})
    cap = requested.get('max_new_tokens')
    require(requested.get('mode') in ('short', 'long') and type(cap) is int and 1 <= cap <= 8192,
            'bound_head_reflection_cap')
    return cap


class OpenEnvironment:
    def __init__(self, world, record, store):
        self.world, self.task, self.store = world, record['task'], store
        self.current = record['current']
        self.calls = []

    def step(self, action):
        matched = re.fullmatch(r'(READ EVENT|ROUTE) ([^\s]+)', action)
        require(matched is not None, 'strict_open_environment_action')
        kind, value = matched.groups()
        if kind == 'READ EVENT':
            require(value in self.task['events'], 'listed_open_inspection')
            response = 'MEMORY RESULT\n'+self.store.get(value, gym.readout.UNAVAILABLE)
        else:
            candidates = [edge for edge in self.world['edges'] if edge['node'] == self.current and edge['port'] == value]
            require(len(candidates) == 1, 'available_open_route')
            edge = candidates[0]
            route = dict(source=self.current, port=value, destination=edge['outcome'], receipt=edge['receipt'])
            self.current = edge['outcome']
            ports = sorted(edge['port'] for edge in self.world['edges'] if edge['node'] == self.current)
            response = gym.hop.micro.RECEIPT_WIRE.format(**route)+'\n'+gym.readout.display(self.current, self.task, ports)
        receipt = dict(action=action, response=response, response_sha256=digest(response), actual_environment_call=True)
        self.calls.append(receipt)
        return response


def open_turn(world, record, store, generate_call):
    environment = OpenEnvironment(world, record, store)
    messages = deepcopy(record['messages'])
    messages[0] = dict(role='system', content='You can reason freely. Use only actual available observations. '+OPEN_PROMPT)
    messages.append(dict(role='user', content=OPEN_PROMPT))
    captures = []
    stopped = False
    for turn in range(2):
        response = generate_call(messages)
        captures.append(response)
        messages.append(dict(role='assistant', content=response['raw']))
        lines = response['raw'].rstrip().splitlines()
        action = lines[-1] if lines else ''
        if action == 'STOP':
            stopped = True
            break
        if re.fullmatch(r'(READ EVENT|ROUTE) ([^\s]+)', action) is None:
            break
        try:
            observation = environment.step(action)
        except ValueError as error:
            observation = 'ENVIRONMENT ERROR: '+str(error)
        messages.append(dict(role='user', content=observation))
    return dict(messages=messages, captures=captures, environment_calls=environment.calls,
                observed_stop=stopped, initiative='UNKNOWN_PENDING_SHARED_JUDGE',
                continuation_after_inspection=len(captures)>1 and bool(environment.calls))


def training_row_allowed(phase):
    return phase in ('experience', 'presleep', 'reflection', 'open_turn')


def append_training_row(rows, phase, call, path):
    require(training_row_allowed(phase), 'readouts_never_training_buffer')
    rows.append(causal.replay_row(call, path, sha(path)))


def sleep_schedule(new_rows, previous_rows, anchor_rows=42):
    require(anchor_rows == 42, 'shared42_exact')
    own = [('NEW', index) for presentation in range(16) for index in range(new_rows)]
    own += [('REHEARSAL', index) for index in range(previous_rows)]
    count = max(1, len(own))
    return [dict(own=own[step] if own else None,
                 anchors=[index % 42 for index in range(step, max(42, count), count)])
            for step in range(count)]


def train_sleep(engine, optimizer, rows, history, anchors, output, check, context_limit=16384):
    encoded, rejected = [], []
    for row in rows:
        try:
            encoded.append(replay.encode_row(row, engine.tokenizer, context_limit))
        except ValueError as error:
            rejected.append(dict(source=row['source_call_sha256'], error=str(error)))
    write(output/'ENCODING.json', dict(rows=len(rows), encoded=len(encoded), rejected=rejected,
                                      structural_only=True, outcome_selection=False))
    previous, previous_rejected = [], []
    for row in history:
        try:
            previous.append(replay.encode_row(row, engine.tokenizer, context_limit))
        except ValueError as error:
            previous_rejected.append(dict(source=row['source_call_sha256'], error=str(error)))
    require(len(anchors) == 42, 'all42_shared_anchors')
    native.development.enable_existing_adapter(engine)
    engine.model.train()
    engine.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    engine.model.enable_input_require_grads()
    engine.model.config.use_cache = False
    updates, child_token_exposure, anchor_token_exposure = 0, 0, 0
    for allocation in sleep_schedule(len(encoded), len(previous)):
            check('optimizer_update')
            selected = allocation['own']
            batch = []
            if selected:
                kind, index = selected
                item = encoded[index] if kind == 'NEW' else previous[index]
                batch.append((item, .75))
                child_token_exposure += len(item.target_ids)
            for index in allocation['anchors']:
                item = anchors[index]['encoded']
                batch.append((item, .25/len(allocation['anchors'])))
                anchor_token_exposure += len(item.target_ids)
            optimizer.zero_grad(set_to_none=True)
            losses = []
            for item, weight in batch:
                inputs = engine.torch.tensor([item.input_ids], dtype=engine.torch.long, device=engine.device)
                labels = engine.torch.tensor([item.labels], dtype=engine.torch.long, device=engine.device)
                with engine.torch.autocast(device_type='cuda', dtype=engine.torch.bfloat16):
                    loss = engine.model(input_ids=inputs, attention_mask=engine.torch.ones_like(inputs), labels=labels).loss*weight
                require(bool(engine.torch.isfinite(loss)), 'nonfinite_optimizer_loss_crash')
                loss.backward()
                losses.append(float(loss.detach().cpu()))
            optimizer.step()
            updates += 1
            with (output/'UPDATES.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(update=updates, allocation=allocation, losses=losses,
                    anchor_lambda=.25, child_token_exposure_including_eos=child_token_exposure,
                    anchor_token_exposure_including_eos=anchor_token_exposure))+'\n')
                stream.flush()
    engine.model.requires_grad_(False)
    engine.model.eval()
    engine.model.gradient_checkpointing_disable()
    engine.model.config.use_cache = True
    engine.verify_base()
    return dict(updates=updates, presentations_per_encoded_row=16, encoded_rows=len(encoded),
                rehearsal_presentations_per_row=1, previous_encoded_rows=len(previous),
                previous_structural_rejections=previous_rejected,
                rejected_structural_rows=len(rejected), optimizer_reset=False, outcome_selection=False,
                anchor_lambda=.25, anchor_inventory_count=42, anchor_manifest_sha256=ANCHOR_SHA,
                child_token_exposure_including_eos=child_token_exposure,
                anchor_token_exposure_including_eos=anchor_token_exposure)


def load_engine(root, plan, identity_document, check, readout=False, predecessors=()):
    identity = native.bridge.AdapterIdentity.from_document(identity_document)
    binding = native.bridge.StageBinding(root.name, native.bridge.ARMS[0], 0,
        'sealed_readout' if readout else 'training', identity, not readout, readout, sha(root/'PLAN.json'))
    loaded = native.load_stage(binding, model_dir=plan['model_dir'], device='cuda:0', gpu_uuid=plan['uuid'],
        context=native.StageContext(private_guidance=() if readout else ('R111_PRIVATE_PARENT',)),
        check=check, predecessor_processes=predecessors)
    expected = loaded.engine.transformers.AutoConfig.from_pretrained(plan['model_dir'],
        local_files_only=True, trust_remote_code=False)
    require(expected.max_position_embeddings >= 16384, 'native_context_support')
    verify_rope_config(loaded.engine.model.config, expected)
    return loaded


def verify_rope_config(actual, expected):
    for field in ('max_position_embeddings', 'rope_scaling', 'rope_parameters', 'rope_theta'):
        require(getattr(actual, field, None) == getattr(expected, field, None),
                'no_rope_modification:'+field)


def checkpoint(engine, optimizer, destination, sleeps, cycle):
    destination.mkdir(parents=True, exist_ok=False)
    engine.verify_base()
    adapter = destination/'adapter'
    engine.model.save_pretrained(adapter, safe_serialization=True, save_embedding_layers=False)
    parameters = {name: value for name, value in engine.model.named_parameters() if native.is_lora(name)}
    identity = native.bridge.AdapterIdentity(str(adapter), native.state_hash(parameters), BASE_SHA,
        tuple((path.name, sha(path)) for path in sorted(adapter.iterdir()) if path.is_file())).verify()
    state_path = destination/'optimizer_rng.pt'
    engine.torch.save(dict(optimizer=optimizer.state_dict(), cpu_rng=engine.torch.get_rng_state(),
                           cuda_rng=engine.torch.cuda.get_rng_state_all()), state_path)
    result = dict(adapter=identity.document(), optimizer_rng_sha256=sha(state_path),
                  source_process=native.process_identity(), sleeps=sleeps, cycle=cycle,
                  complete=True, saved_unix=time.time())
    write(destination/'CHECKPOINT.json', result)
    return result


def final_due(index, now):
    return index == 0 or now >= MORNING_CUT


def readout_directory(root, index, scope):
    require(scope in ('dev', 'final', 'open'), 'readout_scope')
    if scope == 'open':
        return root/'open_readouts'/f'readout_{index:04d}'
    return root/f'readout_{index:04d}' if scope == 'dev' else root/'sealed_final_readouts'/f'readout_{index:04d}'


def run_readout(root, index, checkpoint_path, plan, scope='dev'):
    require(scope != 'final' or final_due(index, time.time()), 'final_only_sleep0_or_morning')
    output = readout_directory(root, index, scope)
    if output.exists():
        return dict(status='PRESERVED_EXISTING_READOUT', no_replay=True)
    output.mkdir(parents=True, mode=0o700)
    command = [sys.executable, '-B', '-m', 'gpu.orch_r111_route_pair_shared', 'readout',
               '--root', str(root), '--sleep-index', str(index), '--checkpoint', str(checkpoint_path), '--scope', scope]
    environment = {key: value for key, value in os.environ.items() if not key.startswith(('PARENT_', 'CLAUDE_'))}
    environment.update(CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONDONTWRITEBYTECODE='1',
                       HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    with (output/'process.log').open('x') as stream:
        process = subprocess.Popen(command, env=environment, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        write(output/'LAUNCH.json', dict(pid=process.pid, started_unix=time.time(), parent_free=True,
                                         context_free=True, checkpoint=str(checkpoint_path)))
        timeout = max(.1, min(420, plan['bounds']['hard_end_unix']-time.time()))
        try:
            process.wait(timeout=timeout)
            status = 'COMPLETE' if process.returncode == 0 else 'CRASHED_READOUT_CONTINUE_LIFE'
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            status = 'READOUT_WALL_CONTINUE_LIFE'
    result = dict(status=status, returncode=process.returncode, finished_unix=time.time(),
                  never_conditions_life=True, semantic_change='UNKNOWN')
    write(output/'PROCESS_RESULT.json', result)
    if index == 0 and scope == 'dev':
        write(root/'SLEEP0_STATUS.json', result)
    return result


def run(root):
    plan = verify(root, gpu=True)
    shared_session = None
    if plan.get('shared_learner'):
        from gpu import orch_r111_route_shared as pooled
        shared_session = pooled.Session(root, plan)
    life_lock = (root/'LIFE_LOCK').open('a')
    fcntl.flock(life_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    start = time.time()
    require(start < plan['bounds']['hard_end_unix'], 'lifetime_wall')
    attempts = sorted(root.glob('cycle_*/START.json'))
    checkpoints = sorted(root.glob('cycle_*/checkpoint/CHECKPOINT.json'))
    previous = read(checkpoints[-1]) if checkpoints else None
    next_cycle = boundary.successor_cycle(root, plan.get('route_boundary_release'))
    sleeps = previous['sleeps'] if previous else 0
    history = []
    for path in sorted(root.glob('cycle_*/ROWS.json')):
        if (path.parent/'checkpoint/CHECKPOINT.json').exists():
            history.extend(read(path))
    write(root/('RECOVERY_'+str(time.time_ns())+'.json'), dict(next_cycle=next_cycle, checkpoint=previous,
        skipped_partial_cycles=[str(path.parent) for path in attempts
                                if not (path.parent/'checkpoint/CHECKPOINT.json').exists()],
        original_charges_preserved=True, no_completed_native_replay=True))

    def check(label):
        require(time.time() < plan['bounds']['hard_end_unix'], 'lifetime_wall:'+label)

    def interrupt(signum, frame):
        raise TimeoutError('owned_lifetime_signal')

    signal.signal(signal.SIGTERM, interrupt)
    initial = previous['adapter'] if previous else plan['initial_adapter']
    if shared_session:
        initial = read(shared_session.loaded_reference['path'])['adapter']
    loaded = load_engine(root, plan, initial, check)
    engine = loaded.engine
    engine.torch.manual_seed(plan['seed'])
    optimizer = None
    if shared_session is None or shared_session.owner:
        parameters = native.development.enable_existing_adapter(engine)
        optimizer = engine.torch.optim.AdamW(list(parameters.values()), lr=3e-5, betas=(.9, .999),
                                            eps=1e-8, weight_decay=.01, foreach=False, fused=False)
    if shared_session and shared_session.owner:
        pooled.restore_optimizer(engine, optimizer, shared_session.loaded_reference, owner='F1')
    elif previous and shared_session is None:
        state_path = checkpoints[-1].parent/'optimizer_rng.pt'
        require(sha(state_path) == previous['optimizer_rng_sha256'], 'optimizer_rng_binding')
        state = engine.torch.load(state_path, map_location='cpu', weights_only=False)
        optimizer.load_state_dict(state['optimizer'])
        engine.torch.set_rng_state(state['cpu_rng'])
        engine.torch.cuda.set_rng_state_all(state['cuda_rng'])
    engine.model.requires_grad_(False)
    engine.model.gradient_checkpointing_disable()
    engine.model.config.use_cache = True
    inventory, anchor_receipt = anchors_module.build_inventory(ANCHOR_ROOT, engine.tokenizer, 16384,
                                                             expected_manifest_sha256=ANCHOR_SHA)
    anchors = [row for family in sorted(inventory) for row in inventory[family]]
    require(len(anchors) == 42, 'native_encoded42_anchor_provenance')
    write(root/'ANCHOR_INVENTORY.json', anchor_receipt)
    write(root/'ACTOR_READY.json', dict(pid=os.getpid(), process=loaded.process, uuid=plan['uuid'],
        started_unix=start, loaded_unix=time.time(), adapter=initial,
        optimizer_restored=shared_session.owner if shared_session else bool(previous),
        shared_learner=shared_session.capture_metadata() if shared_session else None,
        mode='R116_SHARED_F1_OPTIMIZER' if shared_session else plan['mode'],
        no_quota_reset=True, no_replay_of_partial_cycles=True))
    if not (root/'INITIAL_CHECKPOINT.json').exists():
        write(root/'INITIAL_CHECKPOINT.json', dict(adapter=initial, source_process=loaded.process, sleeps=0, cycle=0))
    run_readout(root, 0, root/'INITIAL_CHECKPOINT.json', plan)
    run_readout(root, 0, root/'INITIAL_CHECKPOINT.json', plan, scope='final')
    cohort = read(root/'COHORT.json')
    parent_history = []
    head_settings = {}
    pending = read(root/'PENDING_TRIPLE.json') if (root/'PENDING_TRIPLE.json').exists() else None
    if pending and pending['intervention']['status'] == 'COMPLETE':
        parent_history.append(pending['intervention']['parent_text'])
    own_memory = read(root/'OWN_CARRY.json')['reflection'] if (root/'OWN_CARRY.json').exists() else ''
    try:
        for cycle in range(next_cycle, plan['bounds']['cycles']+1):
            check('cycle')
            output = root/f'cycle_{cycle:04d}'
            start_path = boundary.successor_start(root, output, plan.get('route_boundary_release'))
            write(start_path, dict(cycle=cycle, started_unix=time.time(), sleeps=sleeps,
                                           process=loaded.process, same_optimizer=True))
            rows, records = [], []
            task_entry, episode_index = None, 0

            def child(messages, phase='experience'):
                nonlocal pending, head_settings
                require(training_row_allowed(phase), 'readouts_never_training_buffer')
                actual = deepcopy(messages)
                if own_memory:
                    actual[-1]['content'] += '\n\nYour prior reflection, not a new observation:\n'+own_memory
                if parent_history:
                    actual[-1]['content'] += '\n\nPrior parent conversation (advice, not observed facts):\n' + '\n'.join(parent_history)
                number = reserve(root, 'NATIVE', dict(cycle=cycle, phase=phase, task_id=task_entry['id']))
                path = output/f'CALL_{number:06d}.json'
                call = dict(task_id=task_entry['id'], phase=phase, started_unix=time.time(), messages=actual)
                if shared_session:
                    call.update(shared_session.capture_metadata())
                write(path, call)
                try:
                    call['requested_cap'] = reflection_cap(head_settings) if phase=='reflection' else 4096
                    call['head_settings'] = deepcopy(head_settings)
                    call['response'] = generate(engine, actual, cap=call['requested_cap'], reflection=phase=='reflection')
                except BaseException as error:
                    call['error_type'] = type(error).__name__
                    raise
                finally:
                    call['finished_unix'] = time.time()
                    write(path, call)
                append_training_row(rows, phase, call, path)
                if pending is not None:
                    write(output/(f'TRIPLE_{number:06d}.json'), dict(before=pending['before'],
                        parent_intervention=pending['intervention'], after=dict(call_path=str(path), call_sha256=sha(path)),
                        behavioral_change='UNKNOWN', outcome_criterion=False))
                response = call['response']
                public = actual+[dict(role='assistant', content=response['raw'])]
                intervention = parent_call(root, plan, task_entry, cycle, episode_index, phase, public, sha(path))
                if intervention.get('head_settings', {}).get('status') == 'BOUND_REQUESTED_SETTINGS':
                    head_settings = intervention['head_settings']
                pending = dict(before=dict(call_path=str(path), call_sha256=sha(path)), intervention=intervention)
                write(root/'PENDING_TRIPLE.json', pending)
                if intervention['status'] == 'COMPLETE':
                    parent_history.append(intervention['parent_text'])
                write(root/'STATUS.json', dict(phase=phase, cycle=cycle, sleeps=sleeps, pid=os.getpid(),
                    observed_unix=time.time(), last_native=number, last_parent_status=intervention['status'],
                    semantic_changes=None, hard_end_unix=plan['bounds']['hard_end_unix']))
                return response

            for episode_index in range(2):
                task_entry = cohort['train'][((cycle-1)*2+episode_index) % len(cohort['train'])]
                record = episode(task_entry['world'], task_entry['task'], child, cohort['store'])
                write(output/f'EPISODE_{episode_index}.json', record)
                if any(capture.get('error') and capture.get('response') is None for capture in record['captures']):
                    raise RuntimeError('native_generation_crash_preserved')
                records.append(record)
                opened = open_turn(task_entry['world'], record, cohort['store'],
                                   lambda messages: child(messages, phase='open_turn'))
                write(output/f'OPEN_TRAIN_{episode_index}.json', opened)
                write(output/f'OBSTACLE_{episode_index}.json', dict(
                    classification='UNKNOWN_PENDING_SHARED_JUDGE', allowed_labels=['PERSISTED', 'ABANDONED', 'LOOPED'],
                    episode_path=str(output/f'EPISODE_{episode_index}.json'), no_outcome_criterion=True))
            evidence = [dict(task=record['task'], messages=record['messages']) for record in records]
            context = [dict(role='system', content=PRESLEEP_PROMPT),
                       dict(role='user', content=json.dumps(evidence, sort_keys=True))]
            first = child(context, phase='presleep')
            context += [dict(role='assistant', content=first['raw']),
                        dict(role='user', content='You may continue the conversation.')]
            second = child(context, phase='presleep')
            reflection_messages = [dict(role='system', content=REFLECTION_PROMPT),
                dict(role='user', content=json.dumps(dict(experiences=evidence,
                    own_conversation=[first['raw'], second['raw']]), sort_keys=True))]
            reflected = child(reflection_messages, phase='reflection')
            write(output/'ROWS.json', rows)
            if shared_session:
                def save_shared(destination, generation, metrics):
                    checkpoint(engine, optimizer, destination, sleeps+1, cycle)
                    return pooled.checkpoint_reference(destination/'CHECKPOINT.json')

                episode_ids = [cohort['train'][((cycle-1)*2+index) % len(cohort['train'])]['id']
                               for index in range(2)]
                receipt = shared_session.sleep(engine, optimizer, anchors, rows, episode_ids,
                                               output, save_shared, check)
                saved = read(shared_session.loaded_reference['path'])
                (output/'checkpoint').mkdir(exist_ok=False)
                write(output/'checkpoint/CHECKPOINT.json', dict(saved, sleeps=sleeps+1, cycle=cycle,
                      shared_checkpoint=shared_session.loaded_reference))
                result = dict(updates=receipt['local_optimizer_steps'],
                    shared_generation=receipt['state']['generation'], pooled_metrics=receipt['metrics'],
                    lifetime_totals=receipt['adopted_plus_shared_totals'], optimizer_owner='F1')
            else:
                result = train_sleep(engine, optimizer, rows, history, anchors, output, check)
                saved = checkpoint(engine, optimizer, output/'checkpoint', sleeps+1, cycle)
            sleeps += 1
            own_memory = reflected['raw']
            write(root/'OWN_CARRY.json', dict(reflection=own_memory, checkpoint_sha256=sha(output/'checkpoint/CHECKPOINT.json')))
            write(output/'SLEEP.json', dict(result, sleeps=sleeps, checkpoint_sha256=sha(output/'checkpoint/CHECKPOINT.json')))
            history.extend(rows)
            if optimizer is not None:
                optimizer.zero_grad(set_to_none=True)
            engine.torch.cuda.empty_cache()
            run_readout(root, sleeps, output/'checkpoint/CHECKPOINT.json', plan)
            run_readout(root, sleeps, output/'checkpoint/CHECKPOINT.json', plan, scope='open')
            if time.time() >= MORNING_CUT and not (root/'FINAL_MORNING_REQUESTED.json').exists():
                write(root/'FINAL_MORNING_REQUESTED.json', dict(sleep=sleeps, requested_unix=time.time()))
                run_readout(root, sleeps, output/'checkpoint/CHECKPOINT.json', plan, scope='final')
            write(output/'COMPLETE.json', dict(cycle=cycle, sleeps=sleeps, completed_unix=time.time(),
                                              updates=result['updates'], checkpoint=saved['adapter']))
            parent_history = [pending['intervention']['parent_text']] if pending and pending['intervention']['status']=='COMPLETE' else []
        write(root/'TERMINAL.json', dict(status='DECLARED_SEGMENT_BOUND', finished_unix=time.time(), sleeps=sleeps,
                                        no_outcome_stop=True, no_automatic_quota_extension=True))
    except BaseException as error:
        write(root/('CRASH_'+str(time.time_ns())+'.json'), dict(error_type=type(error).__name__,
            finished_unix=time.time(), latest_complete_checkpoint=str(checkpoints[-1]) if checkpoints else None,
            all_charges_preserved=True, partial_raw_preserved=True))
        raise
    finally:
        life_lock.close()


def generate_batch(engine, messages_batch, cap):
    tokenizer = engine.tokenizer
    tokens = [tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                           return_dict=False) for messages in messages_batch]
    width = max(map(len, tokens))
    cap = min(cap, 16384-width)
    require(cap > 0, 'batch_full_context_no_crop')
    pad = tokenizer.pad_token_id
    inputs = engine.torch.tensor([[pad]*(width-len(row))+row for row in tokens],
                                 dtype=engine.torch.long, device=engine.device)
    mask = engine.torch.tensor([[0]*(width-len(row))+[1]*len(row) for row in tokens],
                               dtype=engine.torch.long, device=engine.device)
    config = engine.transformers.GenerationConfig(do_sample=False, num_beams=1, max_new_tokens=cap,
        use_cache=True, eos_token_id=tokenizer.eos_token_id, pad_token_id=pad)
    with engine.torch.inference_mode():
        output = engine.model.generate(input_ids=inputs, attention_mask=mask, generation_config=config)
    require(engine.torch.equal(output[:, :width], inputs), 'full_batch_native_prefix')
    results = []
    for position, prompt in enumerate(tokens):
        tail = output[position, width:].tolist()
        terminal = tokenizer.eos_token_id in tail
        if terminal:
            tail = tail[:tail.index(tokenizer.eos_token_id)+1]
        raw = tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False,
                               clean_up_tokenization_spaces=False)
        results.append(dict(messages=messages_batch[position], prompt_tokens=len(prompt), raw=raw,
                            token_ids=tail, terminal=terminal, truncated=not terminal and len(tail)==cap,
                            input_truncated=False, full_prompt_prefix_verified=True))
    return results


def readout(root, sleep_index, checkpoint_path, scope='dev'):
    plan = verify(root, gpu=True)
    require(scope != 'final' or final_due(sleep_index, time.time()), 'sealed_final_schedule')
    output = readout_directory(root, sleep_index, scope)
    start = time.time()

    def check(label):
        require(time.time() < min(start+415, plan['bounds']['hard_end_unix']), 'readout_wall')

    document = read(checkpoint_path)
    loaded = load_engine(root, plan, document['adapter'], check, readout=True,
                         predecessors=(tuple(document['source_process']),))
    engine = loaded.engine
    write(output/'LOADED.json', dict(process=loaded.process, parent_free=True, context_free=True,
                                    checkpoint_sha256=sha(checkpoint_path), adapter=document['adapter']))
    if scope in ('dev', 'open'):
        cohort = read(root/'COHORT.json')
    else:
        sealed = read(root/'SEALED_FINAL.json')
        cohort = dict(held=sealed['tasks'], store=sealed['store'])

    def batch(messages, identities, cap=2048, condition='LORA_ON'):
        paths = []
        for task_id, prompt in zip(identities, messages):
            number = reserve(root, 'NATIVE', dict(phase='readout', sleep=sleep_index, task_id=task_id, condition=condition))
            path = output/f'CALL_{number:06d}.json'
            write(path, dict(task_id=task_id, messages=prompt, started_unix=time.time(), status='PENDING'))
            paths.append(path)
        responses = generate_batch(engine, messages, cap)
        for path, task_id, response in zip(paths, identities, responses):
            write(path, dict(task_id=task_id, response=response, finished_unix=time.time(), status='COMPLETE',
                             condition=condition, parent_free=True, semantic_behavior='UNKNOWN'))
        return responses

    if scope == 'open':
        prior = read(root/f"cycle_{document['cycle']:04d}"/'EPISODE_1.json')
        entry = next(item for item in cohort['train'] if item['task'] == prior['task'])
        ports = sorted(edge['port'] for edge in entry['world']['edges'] if edge['node'] == prior['current'])
        public_state = dict(task=prior['task'], current=prior['current'], messages=[
            dict(role='system', content=HELD_PROMPT),
            dict(role='user', content=gym.readout.display(prior['current'], prior['task'], ports))])
        opened = open_turn(entry['world'], public_state, cohort['store'],
                          lambda messages: batch([messages], ['OPEN-READOUT-'+entry['id']], cap=1024)[0])
        write(output/'OPEN.json', dict(opened, parent_free=True, training_buffer=False,
                                       inherited_parent_context=False))
        loaded.verify_unchanged()
        write(output/'COMPLETE.json', dict(scope='OPEN_READOUT', parent_calls=0, training_rows=0,
                                           fresh_process=True, finished_unix=time.time()))
        return

    caches = [[] for row in cohort['held']]
    final = [None]*8
    for turn in range(6):
        pending = []
        for position, entry in enumerate(cohort['held']):
            cursor = [0]
            needed = []
            def cached(prompt):
                ordinal = cursor[0]
                cursor[0] += 1
                if ordinal < len(caches[position]):
                    return caches[position][ordinal]
                needed.append(prompt)
                raise LookupError('BATCH_NEXT_NATIVE')
            record = episode(entry['world'], entry['task'], cached, cohort['store'], system=HELD_PROMPT)
            final[position] = record
            remaining = 2048-sum(len(response['token_ids']) for response in caches[position])
            if needed and remaining > 0:
                pending.append((position, needed[0], remaining))
        if not pending:
            break
        responses = batch([item[1] for item in pending], [cohort['held'][item[0]]['id'] for item in pending],
                          cap=min(item[2] for item in pending))
        for item, response in zip(pending, responses):
            caches[item[0]].append(response)
    for position, entry in enumerate(cohort['held']):
        cursor = [0]
        def replay_final(prompt):
            ordinal = cursor[0]
            cursor[0] += 1
            if ordinal >= len(caches[position]):
                raise LookupError('TASK_TOKEN_BUDGET_EXHAUSTED')
            return caches[position][ordinal]
        final[position] = episode(entry['world'], entry['task'], replay_final, cohort['store'], system=HELD_PROMPT)
    write(output/'HELD.json', dict(ids=[entry['id'] for entry in cohort['held']], scope=scope,
                                   records=final, cached_responses=caches,
                                   batched_first_turn=True, per_task_token_cap=2048, selection=False))
    if scope == 'final':
        loaded.verify_unchanged()
        write(output/'COMPLETE.json', dict(scope='FINAL', parent_calls=0, fresh_process=True,
            context_free=True, held_tasks=8, finished_unix=time.time(), never_export_to_parents_or_exchange=True))
        return
    focused = []
    for entry in cohort['held'][:2]:
        remaining = [2048]
        def focused_generate(messages):
            require(remaining[0] > 0, 'focused_task_budget')
            response = batch([messages], ['FOCUSED-'+entry['id']], cap=min(512, remaining[0]))[0]
            remaining[0] -= len(response['token_ids'])
            return response
        focused.append(episode(entry['world'], entry['task'], focused_generate, cohort['store'],
                               system=HELD_PROMPT+' focus and give the answer'))
    write(output/'FOCUSED.json', dict(records=focused, tasks=2, training_rows=0, parent_calls=0,
                                      prompt_suffix='focus and give the answer'))
    from gpu import astra_goal_quality_train as old
    legacy = read(Path(plan['assets'])/'LEGACY_READOUT.json')
    events = legacy['old_bank']
    require(len(events) == 16, 'sixteen_old_facts')
    batch([old.memory.memory_messages(event['event'], 0) for event in events],
          ['OLD-'+event['event'] for event in events], cap=512)
    cases = legacy['held']['cases']
    audit = [next(case for case in cases if case['kind'] == kind) for kind in ('true', 'fault')]
    batch([old.memory.audit._messages(case, False) for case in audit],
          ['AUDIT-'+case['case_sha256'] for case in audit], cap=512)
    if sleep_index and sleep_index % 4 == 0:
        from organism_v6 import orch_r107_capability as capability
        from gpu import orch_r107_capability_run as capability_runtime
        tasks = capability.tasks()
        selected = [task for position, task in enumerate(tasks) if position % 8 < 4]
        require(len(selected) == 16, 'sixteen_items_on_off_32_calls')
        for condition in ('LORA_ON', 'LORA_OFF'):
            with capability_runtime.readonly_condition(engine.model, condition):
                for offset in range(0, len(selected), 8):
                    group = selected[offset:offset+8]
                    batch([capability.messages(task) for task in group],
                          ['CAP-'+digest(task)[:24] for task in group], cap=512, condition=condition)
    loaded.verify_unchanged()
    write(output/'COMPLETE.json', dict(parent_calls=0, fresh_process=True, context_free=True,
        held_tasks=8, old_facts=16, audit_cases=2, finished_unix=time.time(), semantic_behavior='UNKNOWN'))


def scan(root, service_only=False):
    from gpu import orch_rich_hot_a100_minor_scan as minor
    from gpu import orch_r111_route_admission as reconciler
    plan = read(root/'PLAN.json')
    require(os.geteuid() == 0, 'privileged_scanner_required')
    minor.pinned.policy = SimpleNamespace(HOST_SHA=HOST_SHA, DEVICES=UUIDS, require=require,
        allocation=lambda index: require(index == plan['physical'], 'single_allocated_slot'))
    service = root/'SERVICE_IDENTITY.json'
    if service_only:
        if not service.exists():
            minor.pinned.service(service)
        return
    report = reconciler.scan(plan['physical'], service)
    path = root/('SCAN_'+str(time.time_ns())+'.json')
    write(path, report)
    print(json.dumps(dict(clear=report['clear'], blocking_reasons=report['blocking_reasons'],
                          scan_path=str(path), scan_sha256=sha(path), scanned_unix=time.time())))


def launch(root, recovery=False):
    plan = verify(root)
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'node_local_launch_only')
    publication = read(root/'PUBLICATION.json')
    require(publication['plan_sha256'] == sha(root/'PLAN.json') and publication['cpu_tests_passed'] is True
            and publication.get('coordination_reference') and publication.get('board_reference'), 'published_cpu_allocation')
    if plan['physical'] == 0:
        approval = read(root/'ROHIN_GO.json')
        require(approval.get('authorization') == 'WATCHER_RELAYED_ROHIN_DONE'
                and approval.get('plan_sha256') == sha(root/'PLAN.json')
                and approval.get('parent_prompt_sha256') == plan['parent_prompt_sha256']
                and approval.get('source_reference'), 'R115_EXPLICIT_DONE_NO_SILENCE_WINDOW')
    else:
        handoff = read(root/'HANDOFF.json')
        require(handoff.get('released_by') == 'Cicero' and handoff.get('uuid') == plan['uuid']
                and handoff.get('complete_cycle') is True and handoff.get('owned_process_exited') is True,
                'Cicero_complete_cycle_handoff_required')
    if recovery:
        prior = read(root/'DISPATCH.json')
        require(not Path('/proc', str(prior['supervisor_pid'])).exists(), 'previous_supervisor_absent')
        for path in root.glob('actor_attempt_*.json'):
            require(not Path('/proc', str(read(path)['pid'])).exists(), 'previous_owned_actor_absent')
    else:
        require(not (root/'DISPATCH.json').exists(), 'single_initial_dispatch')
    prefix = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
              'PYTHONPATH='+str(Path(__file__).resolve().parents[1]), 'python3', '-B',
              '-m', 'gpu.orch_r111_route_pair_shared']
    subprocess.run(prefix+['service', '--root', str(root)], capture_output=True, check=True, timeout=90)
    receipt = subprocess.run(prefix+['scan', '--root', str(root)], capture_output=True, check=True, timeout=100)
    compact = json.loads(receipt.stdout)
    require(compact['clear'], 'strict_fresh_admission_blocked_no_waiver')
    write(root/'ADMISSION.json', compact)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], HF_HUB_OFFLINE='1',
                       TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
    supervisor_log = root/('supervisor_recovery_'+str(time.time_ns())+'.log' if recovery else 'supervisor.log')
    with supervisor_log.open('x') as stream:
        process = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_r111_route_pair_shared',
            'supervise', '--root', str(root)], env=environment, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    result = dict(supervisor_pid=process.pid, started_unix=time.time(), physical=plan['physical'],
                  uuid=plan['uuid'], plan_sha256=sha(root/'PLAN.json'), native_loaded=False)
    write(root/('DISPATCH_RECOVERY_'+str(time.time_ns())+'.json' if recovery else 'DISPATCH.json'), result)
    return result


def supervise(root):
    plan = verify(root, gpu=True)
    lock = (root/'SUPERVISOR_LOCK').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    attempt = max((int(path.stem.split('_')[-1]) for path in root.glob('actor_attempt_*.json')), default=0)
    while time.time() < plan['bounds']['hard_end_unix']:
        attempt += 1
        with (root/f'actor_attempt_{attempt:04d}.log').open('x') as stream:
            process = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_r111_route_pair_shared',
                'run', '--root', str(root)], stdout=stream, stderr=subprocess.STDOUT)
            write(root/f'actor_attempt_{attempt:04d}.json', dict(pid=process.pid, launched_unix=time.time(),
                same_owned_life=True, no_quota_reset=True, no_outcome_gate=True))
            try:
                process.wait(timeout=max(.1, plan['bounds']['hard_end_unix']-time.time()))
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=30)
                break
        if (root/'TERMINAL.json').exists():
            break
        write(root/f'crash_recovery_{attempt:04d}.json', dict(returncode=process.returncode,
            observed_unix=time.time(), restoring_last_checkpoint=True, charges_unchanged=True))
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                   'PYTHONPATH='+str(Path(__file__).resolve().parents[1]), 'python3', '-B',
                   '-m', 'gpu.orch_r111_route_pair_shared', 'scan', '--root', str(root)]
        report = json.loads(subprocess.check_output(command, text=True, timeout=100))
        require(report['clear'], 'fresh_privileged_recovery_admission_no_foreign_takeover')
        time.sleep(1)
    lock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('run', 'readout', 'scan', 'service', 'launch', 'recover', 'supervise'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--sleep-index', type=int)
    parser.add_argument('--scope', choices=('dev', 'final', 'open'), default='dev')
    arguments = parser.parse_args()
    if arguments.phase == 'run':
        run(arguments.root)
    elif arguments.phase == 'readout':
        readout(arguments.root, arguments.sleep_index, arguments.checkpoint, arguments.scope)
    elif arguments.phase in ('scan', 'service'):
        scan(arguments.root, service_only=arguments.phase == 'service')
    elif arguments.phase in ('launch', 'recover'):
        print(json.dumps(launch(arguments.root, recovery=arguments.phase=='recover'), sort_keys=True))
    else:
        supervise(arguments.root)


if __name__ == '__main__':
    main()
