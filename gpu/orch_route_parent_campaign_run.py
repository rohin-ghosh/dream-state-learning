"""Matched route parenting stages and node3-only bounded guardian."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import FunctionType

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu import orch_oracle_repair_guard as guardian
from gpu import orch_l2_shared_run as shared_run
from gpu.orch_l2_shared_run import write, spend, legacy_encode
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l2_guided as guided
from organism_v6 import orch_route_parent_campaign as policy
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


ROOT = Path(policy.ROOT)
TREE = Path(__file__).resolve().parents[1]
RUN_MODULE = 'gpu.orch_route_parent_campaign_run'
DEVICES = {arm: (index, guardian.DEVICES[index]) for index, arm in enumerate(policy.ARMS)}
require = policy.require
read = native.source.read
sha = bridge.file_sha256
digest = policy.digest


class Engine(native.source.Engine):
    generate = FunctionType(native.source.Engine.generate.__code__,
        dict(native.source.Engine.generate.__globals__, MAX_CONTEXT=policy.CAPS['context']),
        'generate', native.source.Engine.generate.__defaults__)


def verify(root):
    require(root == ROOT and root.resolve() == root, 'own_root_only')
    from gpu import orch_route_parent_campaign_wire_resume as wire

    prepared = read(root / ('PREPARE_WIRE_RESUME.json' if wire.active() else 'PREPARE.json'))
    if wire.active():
        require(prepared['original_prepare_sha256'] == sha(root / 'PREPARE.json'), 'original_prepare_preserved')
    for name, expected in prepared['source_files'].items():
        require(sha(TREE / name) == expected, 'source_drift:' + name)
    for name, expected in prepared['inputs'].items():
        require(sha(root / name) == expected, 'input_drift:' + name)
    bridge.AdapterIdentity.from_document(prepared['initial'])
    return prepared


def prepare(root):
    require(root == ROOT and not (root / 'PREPARE.json').exists(), 'fresh_prepare')
    receipt = read(root / 'initial_source_receipt.json')
    policy.validate_initial(receipt)
    manifest = portable.read_manifest(guardian.BUNDLE, expected_manifest_sha256=shared_run.shared.PORTABLE_SHA)
    base = portable.verify_base_files(guardian.BUNDLE, guardian.MODEL,
                                     expected_manifest_sha256=shared_run.shared.PORTABLE_SHA)
    identity = bridge.AdapterIdentity(str(root / 'initial_adapter'), policy.INITIAL_STATE,
        manifest['expected_base_sha256'], tuple(receipt['adapter_files'].items())).verify()
    cohort = policy.cohort(shared_run.exclusions.excluded_ids(manifest))
    write(root / 'COHORT.json', cohort)
    tokenizer = native.source.native.load_local_tokenizer(guardian.MODEL)
    legacy = legacy_encode(root, tokenizer)
    require(len(legacy) == 222, 'verified222_legacy_rows')
    inputs = {name: sha(root / name) for name in ('initial_source_receipt.json',
        'LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json',
        'COHORT.json', 'SERVICE_IDENTITY.json', 'PROVIDER.json')}
    if (root / 'CONFIG.json').exists():
        inputs['CONFIG.json'] = sha(root / 'CONFIG.json')
    require(read(root / 'PROVIDER.json')['verified'] is True, 'observed_provider_required')
    if policy.CELL['provider'] != 'existing_claude_cli':
        require(read(root / 'PROVIDER.json').get('actual_primary_model') == policy.CELL['provider'],
                'selected_parent_primary_provenance')
    sources = {str(path.relative_to(TREE)): sha(path)
               for folder in ('gpu', 'organism_v6') for path in sorted((TREE / folder).iterdir())
               if path.is_file() and path.suffix in ('.py', '.sh')}
    write(root / 'PREPARE.json', dict(status='PREPARED_NO_MODEL', initial=identity.document(),
        verified_base=base, inputs=inputs, source_files=sources, cohort_sha256=digest(cohort),
        caps=policy.CAPS, cpu_legacy_rows=len(legacy), model_calls=0, updates=0,
        prepared_unix=time.time(), provider=read(root / 'PROVIDER.json')))


def repaired_collection(root, arm, cycle, output, identity, collection):
    folder = root / arm / f'cycle{cycle}/experience'
    recovered, dispositions = [], []
    calls = [read(path) for path in sorted(folder.glob('CALL_*.json'))]
    for episode_path in sorted(folder.glob('EPISODE_*.json')):
        ordinal = episode_path.stem.split('_')[1]
        record = read(episode_path)
        reflection_path = folder / f'REFLECTION_{ordinal}.json'
        reflection = read(reflection_path)
        response = reflection.get('response')
        disposition = dict(episode_sha256=sha(episode_path), original_reflection_sha256=sha(reflection_path))
        try:
            require(response is not None and response['terminal'] and not response['truncated'], 'complete_original_response')
            require(reflection['episode_sha256'] == digest(record)
                    and any(call.get('response') == response for call in calls), 'actual_original_call_binding')
            private = [policy.GUIDANCE] if arm != 'UNPARENTED' else []
            if arm != 'UNPARENTED':
                coach = read(folder / f'SLEEP_COACH_{ordinal}.json')
                private += [item['message'] for item in record['parent_messages'] + [coach]
                            if item.get('speak') and item.get('message')]
            policy.target_gate(response['raw'], private)
            capture = dict(run_id=root.name, arm=arm, cycle=cycle, actor=identity.document(),
                origin='ACTUAL_CHILD_OUTPUT', complete=True, admitted=True, error=None,
                student_prefix=policy.reflection_prefix(record), response=response)
            recovered.append(dict(capture=capture, sha256=digest(capture), private=private,
                                   episode_sha256=digest(record), outcome=record['correct']))
            disposition['candidate'] = True
        except ValueError as error:
            disposition.update(candidate=False, error=str(error))
        dispositions.append(disposition)
    write(output / 'REPLAY_REPROJECTION.json', dict(original_complete_sha256=sha(folder / 'COMPLETE.json'),
        dispositions=dispositions, candidates=len(recovered), model_calls=0, original_artifacts_unchanged=True,
        repair='Remove private nested response.messages metadata from neutral prefix; never alter target bytes'))
    return dict(collection, reflections=recovered, admitted_rows=len(recovered))


def identity_for(root, arm, cycle, phase, initial):
    predecessors = []
    if cycle == 0 or phase == 'source':
        document = initial
    elif phase == 'readout':
        prior = read(root / arm / f'cycle{cycle}/sleep/COMPLETE.json')
        document = prior['output_adapter']
        predecessors = [tuple(prior['process'])]
    else:
        prior = read(root / arm / f'cycle{cycle - 1}/sleep/COMPLETE.json') if cycle > 1 else None
        document = policy.next_identity(initial, arm, cycle, prior)
        if prior:
            predecessors = [tuple(prior['process'])]
    return bridge.AdapterIdentity.from_document(document), tuple(predecessors)


def parent_request(root, arm, cycle, payload, check):
    started = time.time()
    payload = policy.parent_payload(payload)
    number = spend(root, 'PARENT_' + arm, policy.CAPS['parent_calls_per_lane'],
                   dict(cycle=cycle, kind=payload['kind']))
    name = f'{number:04d}_{arm}_C{cycle}'
    request = dict(id=name, payload=payload)
    write(root / 'parent_queue' / (name + '.request.json'), request)
    response_path = root / 'parent_queue' / (name + '.response.json')
    cutoff = time.time() + 240
    while not response_path.exists():
        check('parent_wait')
        require(time.time() < cutoff, 'parent_timeout_no_substitute')
        time.sleep(1)
    response = read(response_path)
    if getattr(policy, 'RECORD_PARENT_WAIT', False):
        write(root / 'parent_queue' / (name + '.WAIT.json'), dict(arm=arm, cycle=cycle,
            started_unix=started, finished_unix=time.time(), elapsed_seconds=time.time() - started,
            response_sha256=sha(response_path), provider_error=bool(response.get('result', {}).get('error'))))
    require(response['id'] == name and response['request_sha256'] == digest(request), 'parent_binding')
    require(not response['result'].get('error'), 'parent_provider_failed_no_substitute')
    return response['result']


def source_store(root, cohort):
    document = read(root / 'SOURCE.json')
    require(document['cohort_sha256'] == digest(cohort), 'source_cohort_drift')
    worlds = [world for group in cohort['train'] + cohort['held'] for world in group]
    require(len(worlds) == len(document['collections']), 'all_source_worlds')
    store = {}
    for world, collection in zip(worlds, document['collections']):
        require(collection['world'] == world, 'source_world_drift')
        policy.runtime(world['master'])['replay_collection'](collection)
        for record in collection['records']:
            if record['accepted']:
                store[record['edge']['event']] = record['event']['raw']
    require(digest(store) == document['store_sha256'], 'source_store_drift')
    return store


def training_store(root, worlds):
    store = {}
    for world in worlds:
        collection = read(root / 'source_capture' / (world['master'] + '.json'))
        require(collection['world'] == world, 'train_source_world_drift')
        policy.runtime(world['master'])['replay_collection'](collection)
        for record in collection['records']:
            if record['accepted']:
                store[record['edge']['event']] = record['event']['raw']
    return store


def stage(root, arm, cycle, phase):
    from gpu import orch_route_parent_campaign_wire_resume as wire

    require(not wire.active() or arm == 'FROZEN', 'wire_repair_only_failed_frozen_lane')
    prepared = verify(root)
    index, uuid = DEVICES[arm]
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == uuid, 'exact_cvd')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline')
    deadline = read(root / 'START.json')['native_deadline_unix']
    output = root / ('source_capture' if phase == 'source' else f'{arm}/cycle{cycle}/{phase}')
    output.mkdir(parents=True, exist_ok=False)
    identity, predecessors = identity_for(root, arm, cycle, phase, prepared['initial'])
    parented = phase == 'experience' and arm != 'UNPARENTED'
    binding = bridge.StageBinding(root.name, arm, cycle,
        'sealed_readout' if phase == 'readout' else 'training' if phase == 'sleep' else 'collection',
        identity, parented, phase == 'readout', digest(dict(arm=arm, cycle=cycle, phase=phase,
            cohort=prepared['cohort_sha256'], identity=identity.document())))
    write(output / 'BINDING.json', asdict(binding))
    write(output / 'REQUEST.json', dict(arm=arm, cycle=cycle, phase=phase,
        input_adapter=identity.document(), process=native.process_identity(), started_unix=time.time()))
    resumed = wire.history(root, arm, cycle, phase, output, identity)

    def check(label):
        require(time.time() < deadline, 'deadline:' + label)

    def complete(result, process):
        write(output / 'COMPLETE.json', dict(status='COMPLETE', arm=arm, cycle=cycle, phase=phase,
            input_adapter=identity.document(), process=process, finished_unix=time.time(), **result))

    try:
        if phase == 'sleep':
            collection = read(root / arm / f'cycle{cycle}/experience/COMPLETE.json')
            require(collection['input_adapter'] == identity.document(), 'same_collecting_child')
            if os.environ.get('ROUTE_PARENT_REPROJECT') == '1' and arm != 'FROZEN':
                collection = repaired_collection(root, arm, cycle, output, identity, collection)
            if arm in ('FROZEN', 'NO_LORA') or not collection['reflections']:
                write(output / 'DOSE_EXPOSURE.json', dict(planned_presentations=policy.presentations_for_cycle(cycle),
                    actual_updates=0, actual_new_target_presentations=0, actual_legacy_target_presentations=0,
                    admitted_reflections=len(collection['reflections']), arm=arm, cycle=cycle,
                    unchanged_child=True, reason=arm if arm in ('FROZEN', 'NO_LORA') else 'NO_VALID_REFLECTIONS'))
                complete(dict(output_adapter=identity.document(), updates=0, fits=0,
                              planned_presentations=policy.presentations_for_cycle(cycle), actual_new_target_presentations=0,
                              reason=arm if arm in ('FROZEN', 'NO_LORA') else 'NO_VALID_REFLECTIONS'), native.process_identity())
                return
        loaded = native.load_stage(binding, model_dir=guardian.MODEL, device='cuda:0', gpu_uuid=uuid,
            context=native.StageContext(private_guidance=(policy.GUIDANCE,) if parented else ()),
            check=check, predecessor_processes=predecessors, engine_factory=Engine)
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
                                           runtime=loaded.engine.runtime, parent_present=parented))

        def generate(messages, **metadata):
            check('dispatch')
            bucket = 'SOURCE' if phase == 'source' else arm
            cap = policy.CAPS['source_calls'] if phase == 'source' else policy.CAPS['child_calls_per_lane']
            number = spend(root, bucket, cap, dict(phase=phase, cycle=cycle, **metadata))
            path = output / f'CALL_{number:04d}.json'
            capture = dict(messages=messages, index=number, metadata=metadata, started_unix=time.time())
            write(path, capture)
            try:
                response = loaded.engine.generate(messages, max_new_tokens=160 if phase == 'source' else 512)
                response['generated_text_tokens'] = len(response['token_ids']) - int(response['terminal'])
                capture['response'] = response
                return response
            except BaseException as error:
                capture['error'] = str(error)
                raise
            finally:
                capture['finished_unix'] = time.time()
                write(path, capture)

        cohort = read(root / 'COHORT.json')
        if phase == 'source':
            require(arm == getattr(policy, 'SOURCE_ARM', 'FROZEN') and cycle == 0, 'single_initial_source_lane')
            collections, store = [], {}
            for group in cohort['train'] + cohort['held']:
                for world in group:
                    collection = policy.runtime(world['master'])['collect_world'](world, generate)
                    policy.runtime(world['master'])['replay_collection'](collection)
                    write(output / (world['master'] + '.json'), collection)
                    collections.append(collection)
                    for record in collection['records']:
                        if record['accepted']:
                            store[record['edge']['event']] = record['event']['raw']
            loaded.verify_unchanged()
            write(root / 'SOURCE.json', dict(collections=collections, store_sha256=digest(store),
                cohort_sha256=digest(cohort), initial=identity.document(), events=len(store)))
            complete(dict(source_events=len(store)), loaded.process)
        elif phase in ('experience', 'readout'):
            worlds = cohort['train'][cycle - 1] if phase == 'experience' else cohort['held'][cycle]
            store = training_store(root, worlds) if phase == 'experience' else source_store(root, cohort)
            episodes, reflections = [], []

            def parent(payload):
                response = parent_request(root, arm, cycle, payload, check)
                text = response.get('message', '')
                require(len(loaded.engine.tokenizer.encode(text, add_special_tokens=False)) <=
                        policy.CAPS['parent_tokens'], 'parent_message_over_budget_no_crop')
                return response

            for world in worlds:
                for task in shared_run.shared.tasks(world):
                    telemetry = dict(cycle=cycle, experienced_episodes=len(episodes),
                        algorithm='All sourced good/bad outcomes to own reflection; failed actions never gold.',
                        recent_outcomes=[record['correct'] for record in episodes[-2:]])
                    if policy.CELL['horizon'] == 'long':
                        history = list(episodes)
                        if cycle > 1:
                            history = [read(path) for path in sorted((root / arm /
                                f'cycle{cycle - 1}/experience').glob('EPISODE_*.json'))] + history
                        telemetry['own_training_history'] = [dict(task=item['task'], messages=item['messages'],
                            outcome=item['correct'], terminal_reason=item['terminal_reason']) for item in history]
                    ordinal = len(episodes) + 1
                    record = wire.cached(resumed, f'EPISODE_{ordinal:02d}.json')
                    if record is None:
                        record = guided.episode(world, task, generate, store, parent=parent if parented else None,
                                                telemetry=telemetry, rich_contract=False)
                    require(record['task'] == task, 'resumed_task_order_unchanged')
                    episodes.append(record)
                    ordinal = len(episodes)
                    write(output / f'EPISODE_{ordinal:02d}.json', record)
                    if phase == 'readout':
                        continue
                    prefix = policy.reflection_prefix(record)
                    private = [policy.GUIDANCE] if parented else []
                    if parented:
                        payload = dict(kind='coach', turn=6, task=deepcopy(task), public_messages=deepcopy(prefix),
                                       prior_parent_messages=record['parent_messages'], learner=telemetry)
                        advice = wire.advice(resumed, ordinal, payload)
                        if advice is None:
                            advice = parent(payload)
                        write(output / f'SLEEP_COACH_{ordinal:02d}.json', advice)
                        private += [item['message'] for item in record['parent_messages'] + [advice]
                                    if item.get('speak') and item.get('message')]
                    messages = deepcopy(prefix)
                    if private:
                        messages[-1]['content'] += '\nTRAINING WHEELS (not evidence, do not quote):\n' + '\n'.join(private)
                    reflection = dict(episode_sha256=digest(record), outcome=record['correct'],
                                      all_experience_in_context=True, teacher_supervised=False)
                    saved_reflection = wire.cached(resumed, f'REFLECTION_{ordinal:02d}.json')
                    if saved_reflection is not None and not saved_reflection.get('admitted'):
                        write(output / f'REFLECTION_{ordinal:02d}.json', saved_reflection)
                        continue
                    try:
                        response = saved_reflection['response'] if saved_reflection is not None else generate(
                            messages, purpose='outcome_tagged_child_consolidation')
                        reflection['response'] = response
                        require(response['terminal'] and not response['truncated'], 'complete_reflection_required')
                        policy.target_gate(response['raw'], private)
                        capture = dict(run_id=root.name, arm=arm, cycle=cycle, actor=identity.document(),
                            origin='ACTUAL_CHILD_OUTPUT', complete=True, admitted=True, error=None,
                            student_prefix=prefix, response=response)
                        if arm != 'NO_LORA':
                            unused, encoded = native.encode_child_captures([capture], [digest(capture)], binding,
                                loaded.engine.tokenizer, private_guidance=tuple(private),
                                max_context=policy.CAPS['context'], max_supervised_tokens=513)
                        item = dict(capture=capture, sha256=digest(capture), private=private,
                                    episode_sha256=digest(record), outcome=record['correct'])
                        reflections.append(item)
                        reflection['admitted'] = True
                    except ValueError as error:
                        reflection.update(admitted=False, error=str(error))
                    write(output / f'REFLECTION_{ordinal:02d}.json', reflection)
            loaded.verify_unchanged()
            if hasattr(policy, 'record_thinking_metrics'):
                policy.record_thinking_metrics(output, episodes, loaded.engine.tokenizer)
            behavior = [dict(task=record['task'], reads=record['reads'], routes=record['routes'],
                first_action=record['captures'][0]['command'], terminal_reason=record['terminal_reason'],
                actor_calls=record['actor_calls'], parent_turns=len(record['parent_messages']),
                episode_sha256=digest(record)) for record in episodes]
            write(output / 'LEARNER_BEHAVIOR.json', dict(parent_free=not parented, episodes=behavior,
                measures=['event_addresses_read', 'route_sequence', 'first_action', 'calls', 'terminal_reason'],
                initial_choice_point_episodes=len(episodes),
                actual_initial_route_attempts=sum(any(str(capture.get('command', '')).startswith('ROUTE ')
                    for capture in record['captures']) for record in episodes),
                actual_valid_initial_choices=sum(bool(record['routes']) for record in episodes),
                cycle=cycle, input_adapter=identity.document()))
            if cycle > 1:
                prior = root / arm / f'cycle{cycle - 1}'
                write(output / 'TAUGHT_TO_NEXT_CYCLE.json', dict(
                    previous_experience_sha256=sha(prior / 'experience/COMPLETE.json'),
                    previous_sleep_sha256=sha(prior / 'sleep/COMPLETE.json'),
                    previous_parent_calls={path.name: sha(path) for path in
                        sorted((root / 'parent_queue').glob(f'*_{arm}_C{cycle - 1}.*.json'))},
                    previous_child=read(prior / 'sleep/COMPLETE.json')['output_adapter'],
                    current_child=identity.document(), current_behavior_sha256=sha(output / 'LEARNER_BEHAVIOR.json'),
                    visibility='PARENT_NEVER_RECEIVES_READOUT_OR_HELD', reward_only=False))
            complete(dict(episodes=len(episodes), successes=sum(record['correct'] for record in episodes),
                reflections=reflections, admitted_rows=len(reflections), all_episode_count=len(episodes),
                failed_episode_count=sum(not record['correct'] for record in episodes),
                parent_free=phase == 'readout', world_denominator=policy.CAPS['worlds'],
                paired_both_correct=sum(episodes[offset]['correct'] and episodes[offset + 1]['correct']
                                        for offset in range(0, len(episodes), 2))), loaded.process)
        else:
            train(root, arm, cycle, output, identity, binding, loaded, collection, check, complete)
    except BaseException as error:
        write(output / 'FAILED.json', dict(error_type=type(error).__name__, error=str(error),
              phase=phase, process=native.process_identity(), finished_unix=time.time()))
        raise


def train(root, arm, cycle, output, identity, binding, loaded, collection, check, complete):
    collection_binding = bridge.StageBinding(root.name, arm, cycle, 'collection', identity,
        arm != 'UNPARENTED', False, read(root / arm / f'cycle{cycle}/experience/BINDING.json')['plan_sha256'])
    new = []
    for item in collection['reflections']:
        policy.target_gate(item['capture']['response']['raw'], item['private'])
        unused, encoded = native.encode_child_captures([item['capture']], [item['sha256']], collection_binding,
            loaded.engine.tokenizer, private_guidance=tuple(item['private']),
            max_context=policy.CAPS['context'], max_supervised_tokens=513)
        new.extend(encoded)
    presentations = policy.presentations_for_cycle(cycle)
    layout = GoalReplayLayout(len(new), presentations)
    require(layout.updates <= policy.CAPS['updates_per_sleep'], 'updates_cap')
    legacy = legacy_encode(root, loaded.engine.tokenizer)
    encoded = native.assemble_replay(legacy, new, layout, legacy_reference=legacy,
                                    eos_token_id=loaded.engine.tokenizer.eos_token_id)
    write(output / 'MASKS.json', [asdict(row) for row in encoded])
    write(output / 'RECIPE.json', dict(shared_run.shared.RECIPE,
        trajectory_presentations=presentations, layout=layout.manifest('FULL_TARGET')))
    torch = loaded.engine.torch
    torch.manual_seed(shared_run.shared.RECIPE['seed'])
    parameters = native.development.enable_existing_adapter(loaded.engine)
    require(native.state_hash(parameters) == identity.state_sha256, 'enable_drift')
    require(not any(parameter.requires_grad for name, parameter in loaded.engine.model.named_parameters()
                    if not native.is_lora(name)), 'base_frozen')
    options = dict(shared_run.shared.RECIPE['optimizer_kwargs'])
    options['betas'] = tuple(options['betas'])
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=shared_run.shared.RECIPE['learning_rate'], **options)
    require(not optimizer.state, 'fresh_optimizer')
    loaded.engine.model.train()
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, layout.updates + 1):
            check('update')
            indexes, batch, reference, active, scale = native.training_batch(encoded, layout, update,
                pad_id=loaded.engine.tokenizer.pad_token_id)
            tensors = {name: torch.tensor(value, dtype=torch.long, device=loaded.engine.device) for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                loss = loaded.engine.model(**tensors, use_cache=False).loss * scale
            require(bool(torch.isfinite(loss)), 'finite_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'finite_gradients')
            optimizer.step()
            stream.write(json.dumps(dict(update=update, loss=loss.item(), rows=indexes,
                                         reference=reference, active=active, scale=scale)) + '\n')
            stream.flush()
    require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()), 'finite_adapter')
    loaded.engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    child = bridge.AdapterIdentity(str(output / 'adapter'), native.state_hash(parameters), identity.base_sha256,
        tuple((path.name, sha(path)) for path in sorted((output / 'adapter').iterdir()) if path.is_file())).verify()
    require(native.observe_adapter(loaded.engine, child) == child, 'saved_adapter_base_verified')
    write(output / 'DOSE_EXPOSURE.json', dict(planned_presentations=presentations,
        actual_updates=layout.updates, actual_new_target_presentations=len(new) * presentations,
        actual_legacy_target_presentations=12 * presentations, admitted_reflections=len(new),
        actual_row_presentations=list(layout.presentation_counts()), arm=arm, cycle=cycle,
        input_child=identity.document(), output_child=child.document(), same_life_continuation=cycle > 1,
        interpretation='EXPLORATORY_ACROSS_CYCLE_NOT_CLEAN_CAUSAL_DOSE_CURVE'))
    complete(dict(output_adapter=child.document(), updates=layout.updates, fits=1,
                  planned_presentations=presentations, actual_new_target_presentations=len(new) * presentations,
                  all_experience_episodes=collection['all_episode_count'], reflection_targets=len(new)), loaded.process)


def admit(root, index, destination, deadline, scanner=None):
    scanner = scanner or guardian.scan
    for attempt in range(12):
        require(time.time() < deadline - 360, 'admission_deadline')
        snapshot = scanner(index, root / 'SERVICE_IDENTITY.json')
        write(destination.with_name(destination.stem + f'_ATTEMPT{attempt}.json'), snapshot)
        write(destination, snapshot)
        if snapshot['clear'] and snapshot['scanner_euid'] == 0:
            return snapshot
        time.sleep(2)
    raise ValueError('full_privileged_admission_no_waiver')


def lane(root, arm, resume=False):
    prepared = verify(root)
    index, uuid = DEVICES[arm]
    output = root / (arm + ('_GUARD_REPAIR1' if resume else '_GUARD'))
    output.mkdir(exist_ok=False)
    deadline = read(root / 'START.json')['hard_deadline_unix']
    child = None

    def stop(signum, frame):
        if child is not None:
            guardian.stop_owned(child)
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    def execute(phase, cycle):
        nonlocal child
        complete_path = root / ('source_capture/COMPLETE.json' if phase == 'source'
                                else f'{arm}/cycle{cycle}/{phase}/COMPLETE.json')
        if resume and complete_path.exists():
            completed = read(complete_path)
            expected, unused = identity_for(root, arm, cycle, phase, prepared['initial'])
            require(completed['status'] == 'COMPLETE' and completed['arm'] == arm
                    and completed['cycle'] == cycle and completed['phase'] == phase
                    and completed['input_adapter'] == expected.document(), 'resume_completed_binding')
            write(output / f'{cycle}_{phase}_PRESERVED.json', dict(sha256=sha(complete_path), native_calls_replayed=0))
            return
        require(time.time() < deadline - 360, 'dispatch_cutoff')
        admit(root, index, output / f'{cycle}_{phase}_ADMISSION.json', deadline)
        command = [guardian.PYTHON, '-B', '-m', RUN_MODULE,
                   '--phase', phase, '--arm', arm, '--cycle', str(cycle)]
        with (output / f'{cycle}_{phase}.log').open('x') as log:
            child = subprocess.Popen(command, cwd=TREE, env=dict(os.environ, CUDA_VISIBLE_DEVICES=uuid,
                HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                PYTHONPATH=str(TREE), TOKENIZERS_PARALLELISM='false'), stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True)
            write(output / f'{cycle}_{phase}_LAUNCH.json', dict(pid=child.pid, guardian_pid=os.getpid(),
                uuid=uuid, physical_index=index, launched_unix=time.time(), deadline=deadline))
            code = child.wait(timeout=max(1, deadline - 180 - time.time()))
        require(code == 0, 'stage_failed:' + phase)

    try:
        source_arm = getattr(policy, 'SOURCE_ARM', 'FROZEN')
        baseline_first = getattr(policy, 'BASELINE_FIRST', False)
        if arm == source_arm:
            execute('source', 0)
        else:
            cohort = read(root / 'COHORT.json')
            for world in cohort['train'][0]:
                while not (root / 'source_capture' / (world['master'] + '.json')).exists():
                    require(not (root / f'{source_arm}_GUARD/FAILED.json').exists(), 'source_failed')
                    require(time.time() < deadline - 360, 'source_deadline')
                    time.sleep(1)
            if not baseline_first:
                execute('experience', 1)
        while not (root / 'SOURCE.json').exists():
            require(not (root / f'{source_arm}_GUARD/FAILED.json').exists(), 'source_failed')
            require(time.time() < deadline - 360, 'source_deadline')
            time.sleep(2)
        execute('readout', 0)
        for cycle in range(1, policy.CAPS['cycles'] + 1):
            if baseline_first or arm == source_arm or cycle != 1:
                execute('experience', cycle)
            execute('sleep', cycle)
            execute('readout', cycle)
        write(output / 'COMPLETE.json', dict(status='COMPLETE', finished_unix=time.time()))
    except BaseException as error:
        write(output / 'FAILED.json', dict(error=str(error), finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            guardian.stop_owned(child)


def launch(root):
    verify(root)
    publication = read(root / 'PUBLICATION.json')
    require(publication['own_cpu_tests_passed'] and publication['dated_builder_receipt'], 'pre_gpu_gate')
    require(sha(root / 'PREPARE.json') == publication['prepare_sha256'], 'pre_gpu_provenance_binding')
    release = read(root / 'RELEASE.json')
    require(release['owner'] == 'Poincare' and release['physical_indices'] == [0, 1, 2]
            and release['released'] is True, 'direct_owner_release_required')
    started = time.time()
    deadline = started + policy.CAPS['seconds']
    require(deadline < guardian.LEASE_CUTOFF - 6 * 3600, 'six_hour_lease_margin')
    require(not (root / 'START.json').exists(), 'no_clock_reset')
    write(root / 'START.json', dict(started_unix=started, hard_deadline_unix=deadline,
        native_deadline_unix=deadline - 300, caps=policy.CAPS, devices=DEVICES, assigned_gpu_hours=12,
        lease_cutoff_unix=guardian.LEASE_CUTOFF, release_sha256=sha(root / 'RELEASE.json')))
    children = []
    try:
        for arm, (index, uuid) in DEVICES.items():
            snapshot = guardian.scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / f'PREFLIGHT_{index}.json', snapshot)
            require(snapshot['clear'], 'fresh_ownership_not_clear')
        for arm in policy.ARMS:
            with (root / (arm + '_guardian.log')).open('x') as log:
                child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_route_parent_campaign_run',
                    '--phase', 'lane', '--arm', arm], cwd=TREE, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
                    PYTHONPATH=str(TREE)), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                children.append(child)
                write(root / ('LAUNCH_' + arm + '.json'), dict(guardian_pid=child.pid, launched_unix=time.time()))
        while any(child.poll() is None for child in children):
            require(time.time() < deadline - 120, 'hard_guardian_deadline')
            time.sleep(2)
        write(root / 'TERMINAL.json', dict(exit_codes=[child.returncode for child in children], finished_unix=time.time()))
    finally:
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=30)


def main():
    global ROOT

    config_path = os.environ.get('ROUTE_PARENT_CONFIG')
    if config_path:
        policy.activate(read(config_path))
        ROOT = Path(policy.ROOT)
        require(Path(config_path) == ROOT / 'CONFIG.json', 'own_config_path')
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=('prepare', 'launch', 'lane', 'source', 'experience', 'sleep', 'readout'), required=True)
    parser.add_argument('--arm', choices=policy.ARMS, default='GUIDED')
    parser.add_argument('--cycle', type=int, default=0)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.phase in ('prepare', 'launch'):
        globals()[args.phase](ROOT)
    elif args.phase == 'lane':
        lane(ROOT, args.arm, args.resume)
    else:
        stage(ROOT, args.arm, args.cycle, args.phase)


if __name__ == '__main__':
    main()
