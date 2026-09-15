"""Small native stages over released loading/replay seams, including null cycles."""

import argparse
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


def legacy_encode(root, tokenizer):
    from gpu import astra_goal_quality_train as old

    material = source.read(root / 'LEGACY_MATERIAL.json')
    encoded = tuple(source.encode_row(row['messages'], tokenizer) for row in material['memory_rows'])
    encoded += tuple(old.memory.cues.encode_cue_rows(material['cue_rows'], tokenizer))
    encoded += tuple(old.memory.audit.encode_rows(material['audit_rows'], tokenizer))
    encoded += tuple(old.memory.lesson.lesson.encode_rows(material['trajectory_rows'], tokenizer))
    source.require([asdict(row) for row in encoded] == source.read(root / 'OLD_MASKS.json'), 'legacy_reference_drift')
    return encoded


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
    output.mkdir(parents=True, exist_ok=False)
    deadline = float((root / 'DEADLINE').read_text())

    def check(label):
        source.require(time.time() < deadline, 'allocation_deadline:' + label)

    identity, predecessors = input_identity(root, arm, cycle, phase)
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
    write(output / 'REQUEST.json', dict(arm=arm, cycle=cycle, phase=phase, input_adapter=identity.document(),
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
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
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
            previous_admitted = 0
            if cycle > 1 and phase == 'experience':
                previous_admitted = source.read(root / arm / f'cycle{cycle - 1}' / 'experience/COMPLETE.json')['admitted_rows']

            def parent(payload):
                value = parent_request(root, arm, cycle, payload, check)
                text = value.get('message', '')
                if value.get('speak') and len(loaded.engine.tokenizer.encode(text, add_special_tokens=False)) > 160:
                    return dict(speak=False, message='', rationale='oversized_parent_message_not_truncated', rejected=value)
                return value

            hook = None
            if parent_present and arm == 'LONG':
                from gpu.orch_l2_long_hook import build_parent

                events = []

                def emit(event):
                    events.append(event)
                    write(output / f'LONG_PARENT_EVENT_{len(events):04d}.json', event)

                hook = build_parent(root=root, cycle=cycle, tokenizer=loaded.engine.tokenizer,
                    transport=lambda payload: parent_request(root, arm, cycle, payload, check), emit=emit)
            for world in worlds:
                local_store = {edge['event']: store[edge['event']] for edge in world['edges'] if edge['event'] in store}
                for task in shared.tasks(world):
                    record = guided.episode(world, task, generate, local_store,
                        parent=hook if hook is not None else parent if parent_present else None,
                        telemetry=guided.learner_telemetry(episodes, cycle, previous_admitted), rich_contract=phase == 'experience')
                    episodes.append(record)
                    if hook is not None:
                        hook.observe_episode(record)
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
                            review = parent_request(root, arm, cycle, payload, check)
                            reviews = review.get('reviews', [])
                            write(output / f'REVIEW_{len(episodes):02d}.json', review)
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
                write(output / 'PARENT_DISTILLATION.json', hook.distill_cycle())
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
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error), phase=phase,
                                           process=native.process_identity()))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--phase', choices=('prepare', 'source', 'experience', 'sleep', 'readout'), required=True)
    parser.add_argument('--arm', choices=tuple(DEVICES), default='FROZEN')
    parser.add_argument('--cycle', type=int, default=0)
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(Path(options.root))
    else:
        run(options)


if __name__ == '__main__':
    main()
