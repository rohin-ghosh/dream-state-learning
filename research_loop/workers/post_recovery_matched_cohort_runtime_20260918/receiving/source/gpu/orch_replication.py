"""Owned no-fit native replica with source-only archival input extraction."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import time

from gpu import astra_portable_actor_bundle as portable
from gpu import astra_event_two_hop_memory as old_api
from organism_v6 import experienced_event_goal_scale as scale
from organism_v6 import experienced_event_goal_pairs as old_pairs
from organism_v6 import orch_replication as experiment


source = portable.source
require = source.require
BUNDLE = '/tmp/astra_portable_37ec_20260914_attempt1'
BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
TRAIN_ROOT = '/tmp/astra_goal_quality_train_20260914_attempt2'
PROTOCOL = 'research_notes/analysis/orch_replication_protocol_20260914.md'
GPU_MAP = {'ORIGINAL37EC': (5, 'GPU-bc211959-642d-664b-3581-42a0dbe434e9'),
           'FULL_TARGET': (0, 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939'),
           'NEW_TRAJECTORY_LOSS_OFF': (1, 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821')}


def write(directory, name, document):
    source.write(Path(directory) / name, document)


def artifact(path):
    return dict(path=str(path), sha256=source.file_hash(path))


def old_sources():
    root = Path(TRAIN_ROOT)
    bindings = source.read(root / 'prepare/INPUTS.json')['legacy']
    arguments = bindings['transfer']['original_arguments']
    locations = [Path(arguments['collection']), Path(arguments['prior_adult_collection']),
                 Path(arguments['adult_collection']), Path('/tmp/astra_fresh_reader_cycle_20260914_attempt2/collect')]
    bank, episodes, files = [], [], []
    for index, location in enumerate(locations):
        if index == 0:
            bank.extend(source.read(location / 'BANK.json'))
            episodes.extend(source.read(location / 'EPISODES.json'))
            files.extend(artifact(location / name) for name in ('BANK.json', 'EPISODES.json'))
        else:
            document = source.read(location / 'COLLECTION.json')
            bank.extend(document['bank'])
            episodes.extend(document['episodes'])
            files.append(artifact(location / 'COLLECTION.json'))
    require(len(bank) == len(episodes) == 16, 'sixteen_old_sources')
    require(experiment.digest(bank) == bindings['transfer']['old_facts_sha256'], 'old_bank_binding')
    events = [dict(event=fact['event'], raw=episode['event']['raw']) for fact, episode in zip(bank, episodes)]
    rows_path = root / 'FULL_TARGET/train/TRAINING_ROWS.json'
    rows = source.read(rows_path)['memory_rows']
    targets = {row['event']: row['messages'][-1]['content'] for row in rows}
    require(len(rows) == 128 and len(targets) == 16, 'old_archived_material')
    for event in events:
        require(source.material.canonical_event(event['raw']) == targets[event['event']], 'old_raw_target_join')
    held_events = [dict(event=event['event'], raw=targets[event['event']]) for event in events[8:12]]
    held = old_api.audit.build_cases(held_events, old_api.audit.HELD)
    require(held['cases_sha256'] == bindings['held_cases_sha256'] and held['expected_calls'] == 16, 'held_original_identity')
    return dict(bank=bank, events=events, held=held, provenance=files + [artifact(rows_path)])


def prepare(root, commit):
    root.mkdir(parents=True, exist_ok=False)
    manifest = portable.read_manifest(BUNDLE, expected_manifest_sha256=BUNDLE_SHA)
    model_dir = manifest['engine_arguments']['model_dir']
    base_verified = portable.verify_base_files(BUNDLE, model_dir, expected_manifest_sha256=BUNDLE_SHA)
    exclusions = set(manifest['old_ids'])
    for registry in (old_pairs.build_worlds(), scale.breadth.build_worlds()):
        for worlds in registry.values():
            for world in worlds:
                exclusions.update(old_pairs.identifiers(world))
    for registry in scale.validate_registry().values():
        for worlds in registry.values():
            for world in worlds:
                exclusions.update(old_pairs.identifiers(world))
    frozen = experiment.cohort(exclusions)
    saved = {'ORIGINAL37EC': dict(adapter_dir=BUNDLE + '/adapter', state=portable.PARENT_STATE,
                                adapter_files=manifest['adapter_files'])}
    for arm in experiment.STATES[1:]:
        directory = Path(TRAIN_ROOT) / arm / 'train'
        receipt = source.read(directory / 'RESULT.json')
        require(receipt['status'] == 'COMPLETE' and receipt['fits'] == 1 and receipt['updates'] == 2928,
                'saved_training_provenance')
        portable.verify_inventory(directory / 'adapter', receipt['adapter_files'])
        saved[arm] = dict(adapter_dir=str(directory / 'adapter'), state=receipt['adapter_state_after'],
                          adapter_files=receipt['adapter_files'], training_receipt=artifact(directory / 'RESULT.json'))
    retained = old_sources()
    tokenizer = source.native.load_local_tokenizer(model_dir)
    prompt_lengths = []
    for view in (0, 8):
        for event in retained['events']:
            tokens = tokenizer.apply_chat_template(old_api.memory_messages(event['event'], view),
                        tokenize=True, add_generation_prompt=True, return_dict=False)
            prompt_lengths.append(len(tokens))
    for case in retained['held']['cases']:
        prompt_lengths.append(len(tokenizer.apply_chat_template(case['prefix'], tokenize=True,
                                    add_generation_prompt=True, return_dict=False)))
    require(max(prompt_lengths) + experiment.MAX_NEW_TOKENS <= experiment.MAX_CONTEXT, 'retention_prompt_bounds')
    reference = experiment.evaluate(frozen, {}, experiment.first_port, lambda name, value: None)
    write(root, 'COHORT.json', frozen)
    write(root, 'OLD_SOURCE.json', retained)
    write(root, 'REFERENCE.json', reference)
    protocol_path = Path(__file__).resolve().parents[1] / PROTOCOL
    result = dict(status='PREPARED_NO_MODEL', source_commit=commit, model_calls=0, fits=0,
                  protocol_sha256=source.file_hash(protocol_path), cohort_sha256=experiment.digest(frozen),
                  retained_sha256=source.file_hash(root / 'OLD_SOURCE.json'), base_verified=base_verified,
                  bundle_sha256=BUNDLE_SHA, saved=saved, gpu_map=GPU_MAP,
                  readout_cap=experiment.CALL_CAP, source_cap=experiment.SOURCE_CAP,
                  maximum_total_native_calls=784, max_retention_prompt_tokens=max(prompt_lengths),
                  helper_hashes={name: source.file_hash(path) for name, path in dict(
                      driver=__file__, experiment=experiment.__file__, protocol=protocol_path,
                      guardian=Path(__file__).with_name('orch_replication_guard.py')).items()})
    write(root, 'PREPARE.json', result)
    return result


def loaded_state(engine):
    from organism_v6.pcfl_vertical_train import _state_hash

    parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                  if '.lora_A.' in name or '.lora_B.' in name}
    require(bool(parameters), 'named_parameter_adapter_required')
    return _state_hash(parameters)


def native(root, phase, state):
    prepared = source.read(root / 'prepare/PREPARE.json')
    frozen = source.read(root / 'prepare/COHORT.json')
    retained = source.read(root / 'prepare/OLD_SOURCE.json')
    require(experiment.digest(frozen) == prepared['cohort_sha256'], 'frozen_cohort_drift')
    require(source.file_hash(root / 'prepare/OLD_SOURCE.json') == prepared['retained_sha256'], 'old_source_drift')
    protocol_path = Path(__file__).resolve().parents[1] / PROTOCOL
    for name, path in dict(driver=__file__, experiment=experiment.__file__, protocol=protocol_path,
                          guardian=Path(__file__).with_name('orch_replication_guard.py')).items():
        require(source.file_hash(path) == prepared['helper_hashes'][name], 'published_helper_drift:' + name)
    require(phase != 'collect' or state == 'ORIGINAL37EC', 'original_only_collection')
    selected = prepared['saved'][state]
    uuid = GPU_MAP[state][1]
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == uuid, 'physical_uuid_required')
    output = root / ('collection' if phase == 'collect' else state)
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    seconds = 1140 if phase == 'collect' else 2340
    cap = experiment.SOURCE_CAP if phase == 'collect' else experiment.CALL_CAP
    calls = []

    def check(label):
        require(time.monotonic() - started < seconds, 'internal_deadline:' + label)

    result = dict(status='RUNNING', state=state, phase=phase, fits=0, updates=0, trainingAllowed=False,
                  model_calls=0, call_cap=cap, source_commit=prepared['source_commit'],
                  protocol_sha256=prepared['protocol_sha256'], cohort_sha256=prepared['cohort_sha256'],
                  prepare_sha256=source.file_hash(root / 'prepare/PREPARE.json'), pid=os.getpid(), gpu_uuid=uuid)
    write(output, 'REQUEST.json', result)
    try:
        portable.verify_inventory(selected['adapter_dir'], selected['adapter_files'])
        manifest = portable.read_manifest(BUNDLE, expected_manifest_sha256=BUNDLE_SHA)
        arguments = portable.read_bundle(BUNDLE, expected_manifest_sha256=BUNDLE_SHA,
                    model_dir=manifest['engine_arguments']['model_dir'], device='cuda:0', gpu_uuid=uuid)
        arguments.adapter_dir = selected['adapter_dir']
        engine = source.Engine(arguments, source.native.load_local_tokenizer(arguments.model_dir), check=check)
        before = loaded_state(engine)
        require(before == selected['state'], 'EXACT_V3_loaded_named_parameter_state_mismatch')
        result['adapter_state_before'] = before
        result['state_hash_method'] = 'EXACT_V3_pcfl_vertical_train._state_hash_named_parameters_lora_A_B'

        def generate(messages):
            check('call')
            require(len(calls) < cap, 'native_call_cap')
            capture = dict(index=len(calls), messages=deepcopy(messages), response=None, error=None)
            calls.append(capture)
            try:
                tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                            add_generation_prompt=True, return_dict=False)
                require(0 < len(tokens) + experiment.MAX_NEW_TOKENS <= experiment.MAX_CONTEXT,
                        'context_plus_generation_bound_no_truncation')
                capture['prompt_tokens'] = len(tokens)
                capture['response'] = engine.generate(messages, max_new_tokens=experiment.MAX_NEW_TOKENS)
                return capture['response']
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                write(output, f'CALL_{capture["index"]:03d}.json', capture)

        emit = lambda name, value: write(output, name, value)
        if phase == 'collect':
            document = experiment.collect(frozen, generate, emit)
            write(output, 'SOURCE.json', document)
            result.update(accepted_events=document['accepted_events'], event_denominator=32,
                          store_sha256=document['store_sha256'], source_sha256=source.file_hash(output / 'SOURCE.json'))
        else:
            source_result = source.read(root / 'collection/RESULT.json')
            require(source_result['status'] == 'COMPLETE' and source_result['adapter_state_before'] == portable.PARENT_STATE,
                    'completed_original_collection')
            require(all(source_result[field] == result[field] for field in
                        ('source_commit', 'protocol_sha256', 'cohort_sha256', 'prepare_sha256')),
                    'source_collection_binding_drift')
            require(source.file_hash(root / 'collection/SOURCE.json') == source_result['source_sha256'], 'captured_source_drift')
            document = source.read(root / 'collection/SOURCE.json')
            store = experiment.verify_source(frozen, document)
            result['store_sha256'] = document['store_sha256']
            result['routing'] = experiment.evaluate(frozen, store, generate, emit)
            result['retention'] = old_api.recall(retained['events'], lambda messages, **metadata: generate(messages), output, 'OLD')
            audited = old_api.audit.collect_cases(retained['held'], generate, coached=False)
            write(output, 'HELD_AUDIT.json', audited)
            result['audit'] = audited['summary']['overall']
        engine.verify_base()
        result['adapter_state_after'] = loaded_state(engine)
        require(result['adapter_state_after'] == before, 'readonly_state_drift')
        portable.verify_inventory(selected['adapter_dir'], selected['adapter_files'])
        result.update(status='COMPLETE', frozen_base_unchanged=True, runtime=engine.runtime)
    except Exception as error:
        result.update(status='FAILED', error=dict(type=type(error).__name__, message=str(error)))
        write(output, 'FAILED.json', result)
        raise
    finally:
        result.update(model_calls=len(calls), elapsed_seconds=time.monotonic() - started,
                      call_errors=sum(call['error'] is not None for call in calls))
        write(output, 'RESULT.json', result)
    return result


def reduce(root):
    prepared = source.read(root / 'prepare/PREPARE.json')
    frozen = source.read(root / 'prepare/COHORT.json')
    document = source.read(root / 'collection/SOURCE.json')
    store = experiment.verify_source(frozen, document)
    results = {}
    for state in experiment.STATES:
        directory = root / state
        result = source.read(directory / 'RESULT.json')
        require(result['status'] == 'COMPLETE' and result['adapter_state_before'] == result['adapter_state_after']
                == prepared['saved'][state]['state'] and result['frozen_base_unchanged'], 'terminal_native_state')
        require(result['model_calls'] <= experiment.CALL_CAP, 'terminal_call_bound')
        calls = [source.read(directory / f'CALL_{index:03d}.json') for index in range(result['model_calls'])]
        require(len(list(directory.glob('CALL_*.json'))) == len(calls), 'exact_call_inventory')
        require(result['call_errors'] == 0, 'infrastructure_errors_not_clean_comparison')
        cursor = iter(calls)

        def replay_generate(messages):
            call = next(cursor)
            require(call['messages'] == messages and call['error'] is None, 'native_capture_join')
            return call['response']

        def replay_emit(name, value):
            require(source.read(directory / name) == value, 'episode_replay_drift')

        replayed = experiment.evaluate(frozen, store, replay_generate, replay_emit)
        require(replayed == result['routing'], 'independent_routing_replay_drift')
        retained = source.read(root / 'prepare/OLD_SOURCE.json')
        for view in (0, 8):
            correct = 0
            for index, event in enumerate(retained['events']):
                call = next(cursor)
                saved = source.read(directory / f'OLD_RECALL_W{view}_{index:02d}.json')
                require(call['messages'] == old_api.memory_messages(event['event'], view)
                        and saved['response'] == call['response'] and saved['error'] == call['error'], 'retention_native_join')
                expected = source.material.canonical_event(event['raw'])
                successful = (call['error'] is None and call['response']['terminal'] is True
                              and call['response']['truncated'] is False and call['response']['raw'] == expected)
                require(saved['correct'] == successful and saved['expected'] == expected, 'retention_score_drift')
                correct += successful
            require(result['retention'][str(view)] == dict(correct=correct, denominator=16), 'retention_fixed_denominator')
        audit = old_api.audit.collect_cases(retained['held'], replay_generate, coached=False)
        require(audit == source.read(directory / 'HELD_AUDIT.json') and audit['summary']['overall'] == result['audit'],
                'held_audit_replay_drift')
        require(next(cursor, None) is None, 'unaccounted_native_call')
        results[state] = result
    reference = experiment.evaluate(frozen, {}, experiment.first_port, lambda name, value: None)
    require(reference == source.read(root / 'prepare/REFERENCE.json'), 'deterministic_reference_drift')
    result = experiment.compare(results, reference)
    result.update(accepted_source_events=document['accepted_events'], source_event_denominator=32,
                  source_calls=source.read(root / 'collection/RESULT.json')['model_calls'],
                  cohort_sha256=prepared['cohort_sha256'], store_sha256=document['store_sha256'],
                  protocol_sha256=prepared['protocol_sha256'], raw_native_replay_verified=True,
                  result_files={state: artifact(root / state / 'RESULT.json') for state in results})
    write(root, 'COMPARISON.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--phase', choices=('prepare', 'collect', 'readout', 'reduce'), required=True)
    parser.add_argument('--state', choices=experiment.STATES)
    parser.add_argument('--commit')
    options = parser.parse_args()
    if options.phase == 'prepare':
        result = prepare(options.root / 'prepare', options.commit)
    elif options.phase == 'reduce':
        result = reduce(options.root)
    else:
        result = native(options.root, options.phase, options.state)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
