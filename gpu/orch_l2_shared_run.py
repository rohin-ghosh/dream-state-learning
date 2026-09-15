"""Small native stages over released loading/replay seams, including null cycles."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu import orch_full_rich as exclusions
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l2_shared as shared
from organism_v6 import orch_l2_guided as guided
from organism_v6 import orch_full_rich as rich
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


source = native.source
ROOT = Path('/tmp/orch_l2_shared_20260914_attempt1')
BUNDLE = '/tmp/astra_portable_37ec_20260914_attempt1'
DEVICES = {'SHORT': (0, 'GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6'),
           'LONG': (1, 'GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b'),
           'FROZEN': (2, 'GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296'),
           'UNPARENTED': (3, 'GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8')}


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.partial')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def prepare(root):
    source.require(root == ROOT and not (root / 'PREPARE.json').exists(), 'fresh_own_preparation_required')
    manifest = portable.read_manifest(BUNDLE, expected_manifest_sha256=shared.PORTABLE_SHA)
    model = manifest['engine_arguments']['model_dir']
    verified = portable.verify_base_files(BUNDLE, model, expected_manifest_sha256=shared.PORTABLE_SHA)
    prior = source.read(root / 'initial_source_receipt.json')
    source.require(prior['status'] == 'COMPLETE' and prior['adapter_state_after'] == shared.INITIAL_STATE
                   and prior['updates'] == 2928, 'actual266_completed_source_required')
    identity = bridge.AdapterIdentity(str(root / 'initial_adapter'), shared.INITIAL_STATE,
        manifest['expected_base_sha256'], tuple(prior['adapter_files'].items())).verify()
    cohort = shared.cohort(exclusions.excluded_ids(manifest))
    write(root / 'INITIAL.json', identity.document())
    write(root / 'COHORT.json', cohort)
    local_source = Path(__file__).resolve().parents[1]
    files = sorted(path for folder in ('gpu', 'organism_v6') for path in (local_source / folder).glob('*.py'))
    prepared = dict(model_dir=model, initial=identity.document(), caps=shared.CAPS,
                    cohort_sha256=rich.digest(cohort), verified_base=verified,
                    prior_receipt_sha256=bridge.file_sha256(root / 'initial_source_receipt.json'),
                    source_files={str(path.relative_to(local_source)): bridge.file_sha256(path) for path in files},
                    protocol_sha256=bridge.file_sha256(local_source / 'research_notes/analysis/orch_l2_shared_20260914_interface.md'),
                    legacy_files={name: bridge.file_sha256(root / name) for name in
                        ('LEGACY_MATERIAL.json', 'OLD_MASKS.json', 'LEGACY_READOUT.json')},
                    prepared_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    model_calls=0, updates=0)
    write(root / 'PREPARE.json', prepared)
    return prepared


def spend(root, bucket, cap, metadata):
    path = root / ('CALLS_' + bucket + '.jsonl')
    import fcntl

    with path.open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        count = sum(1 for unused in stream)
        source.require(count < cap, 'call_budget_exhausted:' + bucket)
        stream.write(json.dumps(dict(index=count, reserved_unix=time.time(), **metadata)) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    return count


def parent_request(root, arm, cycle, payload, check):
    bucket = 'PARENT_' + arm if arm in ('FROZEN', 'LONG') else 'PARENT_SHORT'
    index = spend(root, bucket, shared.CAPS['parent_calls_per_parented_lane'],
                  dict(arm=arm, cycle=cycle, kind=payload['kind']))
    name = f'{index:04d}_{arm}_C{cycle}'
    request = dict(id=name, payload=payload, cap_response_tokens=160 if payload['kind'] == 'coach' else
                   256 if payload['kind'] == 'long_coach' else 2048)
    write(root / 'parent_queue' / (name + '.request.json'), request)
    response = root / 'parent_queue' / (name + '.response.json')
    until = min(time.time() + 600, float((root / 'DEADLINE').read_text()))
    while not response.exists() and time.time() < until:
        check('parent_wait')
        time.sleep(2)
    if not response.exists():
        return dict(speak=False, message='', rationale='parent_timeout_no_substitute', reviews=[], error='timeout')
    value = source.read(response)
    source.require(value['id'] == name and value['request_sha256'] == rich.digest(request), 'parent_response_binding')
    return value['result']


def input_identity(root, arm, cycle, phase):
    if phase == 'source' or cycle == 0 or arm == 'FROZEN':
        return bridge.AdapterIdentity.from_document(source.read(root / 'INITIAL.json')), []
    previous = cycle if phase == 'readout' else cycle - 1
    if previous == 0:
        return bridge.AdapterIdentity.from_document(source.read(root / 'INITIAL.json')), []
    receipt_path = root / arm / f'cycle{previous}' / 'sleep' / 'COMPLETE.json'
    receipt = source.read(receipt_path)
    source.require(receipt['status'] == 'COMPLETE' and receipt['arm'] == arm
                   and receipt['cycle'] == previous, 'previous_actual_child_required')
    return bridge.AdapterIdentity.from_document(receipt['output_adapter']), [tuple(receipt['process'])]


class RecordedParentTransport:
    def __init__(self, root, arm, cycle, check, output):
        self.root, self.arm, self.cycle, self.check, self.output = root, arm, cycle, check, output
        self.requests = sorted((root / 'parent_queue').glob(f'*_{arm}_C{cycle}.request.json'))
        self.position = 0
        self.restoring = True

    def __call__(self, payload):
        if self.position == len(self.requests):
            source.require(not self.restoring, 'restoration_must_not_dispatch')
            return parent_request(self.root, self.arm, self.cycle, payload, self.check)
        request_path = self.requests[self.position]
        request = source.read(request_path)
        source.require(rich.digest(request['payload']) == rich.digest(payload), 'recorded_parent_request_drift')
        name = request['id']
        source.require(request_path.name == name + '.request.json', 'recorded_parent_identity_drift')
        original_path = request_path.with_name(name + '.response.json')
        response_path = request_path.with_name(name + '.recovered.response.json')
        if not response_path.exists():
            response_path = original_path
        response = source.read(response_path)
        source.require(response['id'] == name and response['request_sha256'] == rich.digest(request)
                       and not response['result'].get('error'), 'recorded_parent_response_failed_or_unbound')
        if response_path != original_path:
            recovery = response['recovery']
            source.require(recovery['provider_calls'] == 0
                and recovery['request_file_sha256'] == bridge.file_sha256(request_path)
                and recovery['original_response_sha256'] == bridge.file_sha256(original_path),
                'recorded_recovery_binding_drift')
        self.position += 1
        write(self.output / f'PARENT_CACHE_{self.position:04d}.json', dict(
            request=str(request_path), request_sha256=bridge.file_sha256(request_path),
            response=str(response_path), response_sha256=bridge.file_sha256(response_path),
            provider_calls=0, request_reservations=0, restoring_completed_episode=self.restoring))
        return response['result']


def continuation_records(root, arm, cycle, output, identity, worlds):
    source.require(arm == 'LONG' and cycle == 1 and not (output / 'COMPLETE.json').exists(),
                   'only_recorded_long_cycle1_boundary')
    request = source.read(output / 'REQUEST.json')
    loaded = source.read(output / 'LOADED.json')
    failure = source.read(output / 'FAILED.json')
    source.require(request['arm'] == arm and request['cycle'] == cycle and request['phase'] == 'experience'
        and request['input_adapter'] == identity.document() and loaded['observed'] == identity.document()
        and failure['message'] == 'long_parent_transport_failed_no_canned_fallback', 'continuation_input_binding_drift')
    manifests = list(root.glob('PREPARE*.json')) + [root.parent / 'orch_l2_long_20260914_attempt1/PREPARE_LONG.json']
    source.require(any(path.is_file() and bridge.file_sha256(path) == request['runtime_manifest_sha256']
                       for path in manifests), 'original_runtime_manifest_missing')
    paths = sorted(output.glob('EPISODE_*.json'))
    source.require([path.name for path in paths] == [f'EPISODE_{index:02d}.json' for index in range(1, 5)],
                   'exact_four_completed_episodes_required')
    records = [source.read(path) for path in paths]
    tasks = [task for world in worlds for task in shared.tasks(world)]
    calls = [source.read(path) for path in sorted(output.glob('CALL_*.json'))]
    captures = [capture for record in records for capture in record['captures']]
    source.require(len(calls) == len(captures) == 16, 'unrecorded_partial_child_call_cannot_resume')
    source.require(all(record['task'] == tasks[index] and record['actor_calls'] == len(record['captures'])
                       for index, record in enumerate(records)), 'completed_episode_task_drift')
    source.require(all(call.get('response') is not None and call.get('error') is None
        and call['messages'] == capture['messages'] and call['response'] == capture['response']
        for call, capture in zip(calls, captures)), 'completed_capture_call_drift')
    return records


def restore_parent_episode(hook, record, telemetry):
    seen = []
    for capture in record['captures']:
        if capture['turn'] not in (0, 2, 4):
            continue
        payload = dict(kind='coach', turn=capture['turn'], task=deepcopy(record['task']),
            public_messages=deepcopy(capture['student_prefix']), prior_parent_messages=deepcopy(seen),
            learner=deepcopy(telemetry))
        restored = hook(payload)
        original = capture['parent_messages'][-1]
        comparable = deepcopy(original)
        restored = deepcopy(restored)
        for value in (comparable, restored):
            if 'long_decision' in value:
                value['long_decision'].pop('elapsed_seconds', None)
                value['long_decision'].pop('created_unix', None)
        source.require(restored == comparable, 'recorded_parent_delivery_drift')
        seen.append(deepcopy(original))
    source.require(seen == record['parent_messages'], 'recorded_parent_turn_drift')
    hook.observe_episode(record)


def legacy_encode(root, tokenizer):
    from gpu import astra_goal_quality_train as old

    material = source.read(root / 'LEGACY_MATERIAL.json')
    encoded = tuple(source.encode_row(row['messages'], tokenizer) for row in material['memory_rows'])
    encoded += tuple(old.memory.cues.encode_cue_rows(material['cue_rows'], tokenizer))
    encoded += tuple(old.memory.audit.encode_rows(material['audit_rows'], tokenizer))
    encoded += tuple(old.memory.lesson.lesson.encode_rows(material['trajectory_rows'], tokenizer))
    verify_legacy_reference(encoded, source.read(root / 'OLD_MASKS.json'))
    return encoded


def verify_legacy_reference(encoded, reference):
    actual = [asdict(row) for row in encoded]
    source.require(len(actual) == len(reference) == 222 and rich.digest(actual) == rich.digest(reference),
                   'legacy_reference_drift')


def experience_store(root, frozen, cycle, check):
    worlds = frozen['train'][cycle - 1]
    collections, store = [], {}
    for world in worlds:
        path = root / 'source_capture' / (world['master'] + '.json')
        while not path.exists():
            check('current_cycle_source_wait')
            source.require(not (root / 'SOURCE_GUARD/FAILED.json').exists(), 'shared_source_failed')
            time.sleep(2)
        collection = source.read(path)
        source.require(collection['world'] == world, 'partial_source_world_drift')
        shared.runtime(world['master'])['replay_collection'](collection)
        collections.append(collection)
        for record in collection['records']:
            if record['accepted']:
                store[record['edge']['event']] = record['event']['raw']
    document = dict(cohort_sha256=rich.digest(frozen), cycle=cycle, collections=collections,
                    store=store, store_sha256=rich.digest(store), world_denominator=8,
                    policy='EXACT_CURRENT_TRAIN_SUBSET_OF_SINGLE_SHARED_INITIAL_SOURCE')
    path = root / f'TRAIN_SOURCE_C{cycle}.json'
    if path.exists():
        source.require(source.read(path) == document, 'published_train_source_drift')
    else:
        write(path, document)
    return store


def run(options):
    root, arm, cycle, phase = Path(options.root), options.arm, options.cycle, options.phase
    manifest_path = root / os.environ.get('L2_NATIVE_MANIFEST', 'PREPARE.json')
    prepared = source.read(manifest_path)
    frozen = source.read(root / 'COHORT.json')
    source.require(rich.digest(frozen) == prepared['cohort_sha256'], 'cohort_changed')
    tree = Path(__file__).resolve().parents[1]
    source.require(all(bridge.file_sha256(tree / name) == digest for name, digest in prepared['source_files'].items()),
                   'published_source_drift')
    source.require(all(bridge.file_sha256(root / name) == digest for name, digest in prepared['legacy_files'].items()),
                   'legacy_file_drift')
    source.require(os.environ.get('CUDA_VISIBLE_DEVICES') == DEVICES[arm][1], 'own_uuid_required')
    source.require(phase != 'source' or arm == 'FROZEN', 'shared_source_lane2_only')
    output = root / ('source_capture' if phase == 'source' else f'{arm}/cycle{cycle}/{phase}')
    resuming = getattr(options, 'resume_experience', False)
    source.require(not resuming or phase == 'experience', 'experience_resume_only')
    output.mkdir(parents=True, exist_ok=resuming)
    deadline = float((root / 'DEADLINE').read_text())

    def check(label):
        source.require(time.time() < deadline, 'allocation_deadline:' + label)

    identity, predecessors = input_identity(root, arm, cycle, phase)
    resumed_records = continuation_records(root, arm, cycle, output, identity, frozen['train'][cycle - 1]) if resuming else []
    attempt = output / 'CONTINUATION_V5' if resuming else output
    if resuming:
        attempt.mkdir(exist_ok=False)
        predecessors.append(tuple(source.read(output / 'LOADED.json')['process']))
        write(attempt / 'PRESERVED.json', dict(files={path.name: bridge.file_sha256(path)
            for path in sorted(output.glob('*.json'))}, episodes=len(resumed_records), child_calls=16,
            next_episode_index=4, next_turn=0, deadline=deadline, original_calls_replayed=0))
    if phase == 'readout' and cycle and not predecessors:
        predecessors = [tuple(source.read(root / arm / f'cycle{cycle}' / 'experience/COMPLETE.json')['process'])]
    parent_present = phase == 'experience' and arm in ('SHORT', 'FROZEN', 'LONG')
    binding = bridge.StageBinding(root.name, arm, cycle,
        'sealed_readout' if phase == 'readout' else 'collection' if phase in ('source', 'experience') else 'training',
        identity, parent_present, phase == 'readout', rich.digest(dict(prepared=prepared['cohort_sha256'],
            input=identity.document(), arm=arm, cycle=cycle, phase=phase)))
    context = native.StageContext(private_guidance=(rich.GUIDANCE,) if parent_present else ())
    kwargs = dict(model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=DEVICES[arm][1],
                  context=context, check=check, predecessor_processes=tuple(predecessors))
    write(attempt / 'REQUEST.json', dict(arm=arm, cycle=cycle, phase=phase, input_adapter=identity.document(),
                                      process=native.process_identity(), started_unix=time.time(),
                                      runtime_manifest_sha256=bridge.file_sha256(manifest_path)))
    try:
        if phase == 'sleep':
            collection = source.read(root / arm / f'cycle{cycle}' / 'experience/COMPLETE.json')
            source.require(collection['input_adapter'] == identity.document(), 'collector_trainer_prior_child_mismatch')
            if not collection['admitted'] or arm == 'FROZEN':
                result = dict(output_adapter=identity.document(), updates=0, fits=0, unchanged=True,
                              reason='FROZEN' if arm == 'FROZEN' else 'ZERO_YIELD_NO_UPDATE')
                write(output / 'COMPLETE.json', dict(status='COMPLETE', arm=arm, cycle=cycle,
                     phase=phase, input_adapter=identity.document(), process=native.process_identity(), **result))
                return
            recipe = {name: shared.RECIPE[name] for name in ('optimizer', 'optimizer_kwargs', 'learning_rate', 'seed')}
            plan = SimpleNamespace(binding=lambda unused: binding,
                contract=SimpleNamespace(manifest=lambda unused: dict(recipe=recipe)), lineage=SimpleNamespace(arm=arm))
            loaded = native.load_training(plan, **kwargs)
        else:
            loaded = native.load_readout(binding, **kwargs) if phase == 'readout' else native.load_stage(binding, **kwargs)
        write(attempt / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
                                           runtime=loaded.engine.runtime, phase=phase))

        def generate(messages, **metadata):
            check('call')
            bucket = 'SOURCE' if phase == 'source' else arm
            cap = shared.CAPS['source_calls'] if phase == 'source' else shared.CAPS['learner_calls_per_lane']
            index = spend(root, bucket, cap, dict(phase=phase, cycle=cycle))
            capture = dict(messages=messages, metadata=metadata, index=index)
            write(output / f'CALL_{index:04d}.json', capture)
            try:
                result = loaded.engine.generate(messages, max_new_tokens=160 if phase == 'source' else 512)
                result['generated_text_tokens'] = len(result['token_ids']) - int(result['terminal'])
                capture['response'] = result
                return result
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                write(output / f'CALL_{index:04d}.json', capture)

        if phase == 'source':
            document = shared.source_document(frozen, generate, lambda name, value: write(output / name, value))
            loaded.verify_unchanged()
            write(root / 'SOURCE.json', document)
            result = dict(source_sha256=rich.digest(document), source_events=len(document['store']))
        elif phase in ('experience', 'readout'):
            store = experience_store(root, frozen, cycle, check) if phase == 'experience' else shared.verify_source(frozen, source.read(root / 'SOURCE.json'))
            worlds = frozen['train'][cycle - 1] if phase == 'experience' else frozen['held'][cycle]
            episodes, admitted, gates = [], [], []
            transport = RecordedParentTransport(root, arm, cycle, check, attempt) if resuming else None

            def request_parent(payload):
                return transport(payload) if transport is not None else parent_request(root, arm, cycle, payload, check)

            previous_admitted = 0
            if cycle > 1 and phase == 'experience':
                previous_admitted = source.read(root / arm / f'cycle{cycle - 1}' / 'experience/COMPLETE.json')['admitted_rows']

            def parent(payload):
                value = request_parent(payload)
                text = value.get('message', '')
                if value.get('speak') and len(loaded.engine.tokenizer.encode(text, add_special_tokens=False)) > 160:
                    return dict(speak=False, message='', rationale='oversized_parent_message_not_truncated', rejected=value)
                return value

            hook = None
            if parent_present and arm == 'LONG':
                from gpu.orch_l2_long_hook import build_parent

                event_index = max([int(path.stem.rsplit('_', 1)[1]) for path in output.glob('LONG_PARENT_EVENT_*.json')] or [0])

                def emit(event):
                    nonlocal event_index
                    event_index += 1
                    event_output = attempt if transport is not None and transport.restoring else output
                    write(event_output / f'LONG_PARENT_EVENT_{event_index:04d}.json', event)

                hook = build_parent(root=root, cycle=cycle, tokenizer=loaded.engine.tokenizer,
                    transport=request_parent, emit=emit)
            for world in worlds:
                local_store = {edge['event']: store[edge['event']] for edge in world['edges'] if edge['event'] in store}
                for task in shared.tasks(world):
                    restoring = len(episodes) < len(resumed_records)
                    telemetry = guided.learner_telemetry(episodes, cycle, previous_admitted)
                    if transport is not None:
                        transport.restoring = restoring
                    if restoring:
                        record = resumed_records[len(episodes)]
                        restore_parent_episode(hook, record, telemetry)
                    else:
                        record = guided.episode(world, task, generate, local_store,
                            parent=hook if hook is not None else parent if parent_present else None,
                            telemetry=telemetry, rich_contract=phase == 'experience')
                    episodes.append(record)
                    if hook is not None and not restoring:
                        hook.observe_episode(record)
                    if not restoring:
                        write(output / f'EPISODE_{len(episodes):02d}.json', record)
                    if phase == 'experience':
                        candidates = [capture for capture in record['captures']
                                      if rich.row_gate(record, capture)['eligible_for_semantic_review']]
                        reviews = []
                        if candidates:
                            payload = dict(kind='semantic', episode=record,
                                candidates=[dict(capture_sha256=rich.digest(capture),
                                    raw_sha256=rich.digest(capture['response']['raw']), capture=capture)
                                    for capture in candidates], rubric=list(rich.RUBRIC))
                            review = request_parent(payload)
                            reviews = review.get('reviews', [])
                            write((attempt if restoring else output) / f'REVIEW_{len(episodes):02d}.json', review)
                        for item in guided.admitted_captures(record, reviews):
                            capture = item['capture']
                            if item['gate']['admitted']:
                                raw_capture = dict(run_id=binding.run_id, arm=arm, cycle=cycle,
                                    actor=identity.document(), origin='ACTUAL_CHILD_OUTPUT', complete=True,
                                    admitted=True, error=None, student_prefix=capture['student_prefix'],
                                    response=capture['response'])
                                private = (rich.GUIDANCE,) + tuple(message['message'] for message in record['parent_messages']
                                    if message.get('speak') and message.get('message')) if parent_present else ()
                                try:
                                    native.encode_child_captures([raw_capture], [rich.digest(raw_capture)], binding,
                                        loaded.engine.tokenizer, private_guidance=private, max_context=2048,
                                        max_supervised_tokens=401)
                                    admitted.append(dict(capture=raw_capture, sha256=rich.digest(raw_capture), private=list(private)))
                                except ValueError as error:
                                    item['projection_error'] = str(error)
                            gates.append(item)
            result = dict(episodes=len(episodes), successes=sum(record['correct'] for record in episodes),
                          admitted=admitted, admitted_rows=len(admitted), gates=gates,
                          episode_denominator=16, world_denominator=8)
            if phase == 'readout':
                from gpu import astra_goal_quality_train as old

                legacy = source.read(root / 'LEGACY_READOUT.json')
                events = [dict(event=fact['event'], raw=episode['event']['raw'])
                          for fact, episode in zip(legacy['old_bank'], legacy['old_episodes'])]
                result['retention'] = old.memory.recall(events, generate, output, 'OLD')
                audit = old.memory.audit.collect_cases(legacy['held'], generate, coached=False)
                write(output / 'AUDIT.json', audit)
                result['audit'] = audit['summary']
            elif hook is not None:
                distillation = hook.distill_cycle()
                if resuming:
                    distillation['continuation_provenance'] = dict(
                        original_receipts=str(attempt / 'PRESERVED.json'),
                        restored_episode_count=len(resumed_records),
                        original_backend_failure_preserved=True,
                        restored_callback_times_are_cpu_not_provider_latency=True,
                        recovered_responses_are_original_provider_bytes=True,
                        additional_provider_calls_for_recovery=0)
                write(output / 'PARENT_DISTILLATION.json', distillation)
            elif parent_present:
                distill = parent_request(root, arm, cycle, dict(kind='distill',
                    learner=guided.learner_telemetry(episodes, cycle),
                    experience_summary=dict(episodes=16, successes=result['successes'], admitted_rows=len(admitted)),
                    examples=[dict(public=record['messages'], parent=record['parent_messages']) for record in episodes[-2:]]), check)
                write(output / 'PARENT_DISTILLATION.json', distill)
            loaded.verify_unchanged()
        else:
            collected = collection['admitted']
            new_encoded = []
            collection_binding = bridge.StageBinding(root.name, arm, cycle, 'collection', identity,
                arm in ('SHORT', 'LONG'), False, source.read(root / arm / f'cycle{cycle}/experience/BINDING.json')['plan_sha256'])
            for item in collected:
                unused, encoded = native.encode_child_captures([item['capture']], [item['sha256']], collection_binding,
                    loaded.engine.tokenizer, private_guidance=tuple(item['private']), max_context=2048, max_supervised_tokens=401)
                new_encoded.extend(encoded)
            layout = GoalReplayLayout(len(new_encoded), 4)
            source.require(layout.updates <= shared.CAPS['updates_per_sleep'], 'sleep_update_cap')
            legacy = legacy_encode(root, loaded.engine.tokenizer)
            encoded = native.assemble_replay(legacy, new_encoded, layout, legacy_reference=legacy,
                                             eos_token_id=loaded.engine.tokenizer.eos_token_id)
            write(output / 'MASKS.json', [asdict(row) for row in encoded])
            write(output / 'RECIPE.json', dict(shared.RECIPE, layout=layout.manifest('FULL_TARGET')))
            torch = loaded.engine.torch
            parameters = {name: parameter for name, parameter in loaded.engine.model.named_parameters() if native.is_lora(name)}
            with (output / 'LOSSES.jsonl').open('x') as stream:
                for update in range(1, layout.updates + 1):
                    check('update')
                    indexes, batch, reference, active, scale = native.training_batch(encoded, layout, update,
                        pad_id=loaded.engine.tokenizer.pad_token_id)
                    tensors = {name: torch.tensor(value, dtype=torch.long, device=loaded.engine.device) for name, value in batch.items()}
                    loaded.optimizer.zero_grad(set_to_none=True)
                    with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                        loss = loaded.engine.model(**tensors, use_cache=False).loss * scale
                    source.require(bool(torch.isfinite(loss)), 'nonfinite_loss')
                    loss.backward()
                    source.require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                                       for parameter in parameters.values()), 'nonfinite_gradient')
                    loaded.optimizer.step()
                    stream.write(json.dumps(dict(update=update, loss=loss.item(), rows=indexes,
                        reference=reference, active=active, scale=scale)) + '\n')
                    stream.flush()
            source.require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()), 'nonfinite_adapter')
            loaded.engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
            identity_out = bridge.AdapterIdentity(str(output / 'adapter'), native.state_hash(parameters), identity.base_sha256,
                tuple((path.name, bridge.file_sha256(path)) for path in sorted((output / 'adapter').iterdir()) if path.is_file())).verify()
            observed = native.observe_adapter(loaded.engine, identity_out)
            source.require(observed == identity_out, 'actual_output_child_drift')
            result = dict(output_adapter=identity_out.document(), updates=layout.updates, fits=1,
                          unchanged=identity_out.state_sha256 == identity.state_sha256)
        write(output / 'BINDING.json', asdict(binding))
        write(output / 'COMPLETE.json', dict(status='COMPLETE', arm=arm, cycle=cycle, phase=phase,
            process=loaded.process, input_adapter=identity.document(), finished_unix=time.time(), **result))
    except Exception as error:
        write(attempt / 'FAILED.json', dict(type=type(error).__name__, message=str(error), phase=phase,
                                           process=native.process_identity()))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--phase', choices=('prepare', 'source', 'experience', 'sleep', 'readout'), required=True)
    parser.add_argument('--arm', choices=tuple(DEVICES), default='FROZEN')
    parser.add_argument('--cycle', type=int, default=0)
    parser.add_argument('--resume-experience', action='store_true')
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(Path(options.root))
    else:
        run(options)


if __name__ == '__main__':
    main()
