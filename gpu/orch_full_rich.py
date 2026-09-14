"""Owned prepare, native collection/readouts and evidence-only rich reduction."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import time

from gpu import astra_portable_actor_bundle as portable
from gpu.orch_replication import loaded_state
from organism_v6 import experienced_event_goal_pairs as pairs
from organism_v6 import experienced_event_goal_scale as scale
from organism_v6 import orch_full_rich as screen
from organism_v6 import orch_terse_breadth as breadth


source = portable.source
BUNDLE = '/tmp/astra_portable_37ec_20260914_attempt1'
BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
STATES = dict(FULL_TARGET='e226cea230b4b970cd5a94cb2b853350aa8bfb95ab4ba69cba3e78ebdd0ad3bf',
              NEW_TRAJECTORY_LOSS_OFF='4f0dccf5b7cf37b872eafc3a50990e0cdfda027fb0140f0aad999f27606e4ee3',
              ORIGINAL37EC=portable.PARENT_STATE)
DEVICES = dict(FULL_TARGET=(0, 'GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6'),
               NEW_TRAJECTORY_LOSS_OFF=(1, 'GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b'),
               ORIGINAL37EC=(2, 'GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296'))
UNUSED = (3, 'GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8')
PROTOCOL = 'research_notes/analysis/orch_full_rich_20260914_protocol.md'


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def utc():
    return datetime.now(timezone.utc).isoformat()


def helper_hashes():
    checkout = Path(__file__).resolve().parents[1]
    paths = [path for folder in ('gpu', 'organism_v6', 'tests')
             for path in (checkout / folder).rglob('*.py')]
    paths.append(checkout / PROTOCOL)
    return {str(path.relative_to(checkout)): source.file_hash(path) for path in sorted(paths)}


def excluded_ids(manifest):
    worlds = [screen.hop.build_world(), screen.hop.build_world(screen.hop.TRANSFER_MASTER)]
    for registry in (pairs.build_worlds(), scale.breadth.build_worlds()):
        for group in registry.values():
            worlds.extend(group)
    for registry in scale.validate_registry().values():
        for group in registry.values():
            worlds.extend(group)
    for shard in breadth.SHARDS:
        for group in breadth.runtime(shard).build_worlds().values():
            worlds.extend(group)
    worlds.extend(screen.readout.cohort()['worlds'])
    identifiers = set(manifest['old_ids'])
    for world in worlds:
        identifiers.update(pairs.identifiers(world))
    return identifiers


def prepare(options):
    root = options.root
    output = root / 'prepare'
    output.mkdir(exist_ok=False)
    source.require(source.file_hash(options.archive) == options.source_sha, 'source_archive_hash')
    manifest = portable.read_manifest(BUNDLE, expected_manifest_sha256=BUNDLE_SHA)
    model_dir = manifest['engine_arguments']['model_dir']
    verified_base = portable.verify_base_files(BUNDLE, model_dir, expected_manifest_sha256=BUNDLE_SHA)
    exclusions = excluded_ids(manifest)
    frozen = screen.cohort(exclusions)
    archive_exclusions = source.read(root / 'ARCHIVAL_EXCLUSIONS.json')
    source.require(archive_exclusions['status'] == 'PASS' and
                   archive_exclusions['cohort_sha256'] == screen.digest(frozen), 'archival_exclusion_check')
    saved = dict(ORIGINAL37EC=dict(adapter_dir=BUNDLE + '/adapter', state=portable.PARENT_STATE,
                                 adapter_files=manifest['adapter_files']))
    for state in screen.STATES[:2]:
        location = root / 'saved' / state / 'train'
        receipt = source.read(location / 'RESULT.json')
        source.require(receipt['status'] == 'COMPLETE' and receipt['updates'] == 2928 and receipt['fits'] == 1
                       and receipt['adapter_state_after'] == STATES[state], 'saved_training_state_provenance')
        portable.verify_inventory(location / 'adapter', receipt['adapter_files'])
        saved[state] = dict(adapter_dir=str(location / 'adapter'), adapter_files=receipt['adapter_files'],
                            state=STATES[state], receipt_sha256=source.file_hash(location / 'RESULT.json'))
    tokenizer = source.native.load_local_tokenizer(model_dir)
    lengths = []
    for world in frozen['worlds']:
        for task in screen.tasks(world):
            messages = [dict(role='system', content=screen.SYSTEM + '\n\n' + screen.GUIDANCE),
                        dict(role='user', content=screen.readout.display(task['node'], task, task['ports']))]
            lengths.append(len(tokenizer.apply_chat_template(messages, tokenize=True,
                           add_generation_prompt=True, return_dict=False)))
    source.require(max(lengths) + screen.MAX_NEW_TOKENS <= screen.MAX_CONTEXT, 'initial_context_precheck')
    write(output / 'COHORT.json', frozen)
    write(output / 'PREPARE.json', dict(status='PREPARED_NO_GPU', timestamp_utc=utc(), model_calls=0,
        source_commit=options.commit, source_archive=str(options.archive), source_sha256=options.source_sha,
        bundle_sha256=BUNDLE_SHA, verified_base=verified_base, saved=saved, devices=DEVICES,
        excluded_identifier_count=len(exclusions), archival_exclusion_receipt=archive_exclusions,
        cohort_sha256=screen.digest(frozen), model_dir=model_dir, helper_hashes=helper_hashes(),
        initial_prompt_tokens=lengths, protocol_sha256=source.file_hash(PROTOCOL), fits=0,
        trainingAllowed=False))


def native(options):
    root, phase, state = options.root, options.phase, options.state
    prepared = source.read(root / 'prepare/PREPARE.json')
    frozen = source.read(root / 'prepare/COHORT.json')
    source.require(screen.digest(frozen) == prepared['cohort_sha256'], 'cohort_drift')
    source.require(helper_hashes() == prepared['helper_hashes'], 'published_source_file_drift')
    source.require(source.file_hash(prepared['source_archive']) == prepared['source_sha256'], 'archive_drift')
    source.require(phase != 'collect' or state == 'ORIGINAL37EC', 'original_collection_only')
    selected = prepared['saved'][state]
    uuid = DEVICES[state][1]
    source.require(os.environ['CUDA_VISIBLE_DEVICES'] == uuid, 'physical_uuid_binding')
    output = root / ('collection' if phase == 'collect' else state)
    output.mkdir(exist_ok=False)
    cap = screen.SOURCE_CAP if phase == 'collect' else screen.TRAJECTORY_CAP
    started, calls, engine_calls = time.time(), [], []

    def check(label):
        source.require(time.time() < options.deadline, 'native_deadline:' + label)

    result = dict(status='RUNNING', state=state, phase=phase, timestamp_utc=utc(), started_unix=started,
                  pid=os.getpid(), gpu_uuid=uuid, source_commit=prepared['source_commit'],
                  protocol_sha256=prepared['protocol_sha256'], cohort_sha256=prepared['cohort_sha256'],
                  prepare_sha256=source.file_hash(root / 'prepare/PREPARE.json'), fits=0, updates=0,
                  trainingAllowed=False, call_cap=cap)
    write(output / 'REQUEST.json', result)
    try:
        portable.verify_inventory(selected['adapter_dir'], selected['adapter_files'])
        arguments = portable.read_bundle(BUNDLE, expected_manifest_sha256=BUNDLE_SHA,
                    model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid)
        arguments.adapter_dir = selected['adapter_dir']
        engine = source.Engine(arguments, source.native.load_local_tokenizer(arguments.model_dir), check=check)
        source.require(not any(parameter.requires_grad for parameter in engine.model.parameters()), 'frozen_readonly')
        before = loaded_state(engine)
        source.require(before == STATES[state], 'EXACT_V3_NAMED_PARAMETER_STATE')
        result.update(adapter_state_before=before, runtime=engine.runtime,
                      state_hash_method='EXACT_V3_pcfl_vertical_train._state_hash_named_parameters_lora_A_B')
        write(output / 'ACTOR_READY.json', result)

        def generate(messages):
            check('call')
            source.require(len(calls) < cap, 'call_cap')
            capture = dict(index=len(calls), messages=deepcopy(messages), response=None, error=None,
                           engine_invoked=False)
            calls.append(capture)
            try:
                max_new_tokens = 160 if phase == 'collect' else screen.MAX_NEW_TOKENS
                tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                            add_generation_prompt=True, return_dict=False)
                capture['prompt_tokens'] = len(tokens)
                source.require(0 < len(tokens) + max_new_tokens <= screen.MAX_CONTEXT,
                               'context_plus_generation_bound_no_truncation')
                engine_calls.append(capture['index'])
                capture['engine_invoked'] = True
                response = engine.generate(messages, max_new_tokens=max_new_tokens)
                response['generated_text_tokens'] = len(response['token_ids']) - int(response['terminal'])
                capture['response'] = deepcopy(response)
                return response
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                write(output / f'CALL_{capture["index"]:03d}.json', capture)

        if phase == 'collect':
            document = screen.collect(frozen, generate, lambda name, value: write(output / name, value))
            write(output / 'SOURCE.json', document)
            result.update(accepted_events=document['accepted_events'], event_denominator=32,
                          store_sha256=document['store_sha256'])
        else:
            collection_result = source.read(root / 'collection/RESULT.json')
            source.require(collection_result['status'] == 'COMPLETE' and
                           collection_result['adapter_state_before'] == portable.PARENT_STATE and
                           collection_result['prepare_sha256'] == result['prepare_sha256'], 'original_source_join')
            document = source.read(root / 'collection/SOURCE.json')
            store = screen.verify_source(frozen, document)
            result['store_sha256'] = document['store_sha256']
            for world_index, world in enumerate(frozen['worlds']):
                for goal_index, task in enumerate(screen.tasks(world)):
                    record = screen.episode(world, task, generate, store)
                    record.update(world_index=world_index, goal_index=goal_index, state=state)
                    write(output / f'EPISODE_{world_index:02d}_{goal_index}.json', record)
        engine.verify_base()
        result['adapter_state_after'] = loaded_state(engine)
        source.require(result['adapter_state_after'] == before, 'adapter_changed')
        portable.verify_inventory(selected['adapter_dir'], selected['adapter_files'])
        result.update(status='COMPLETE', frozen_base_unchanged=True)
    except Exception as error:
        result.update(status='FAILED', error=dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        result.update(finished_utc=utc(), elapsed_seconds=time.time()-started,
                      attempted_calls=len(calls), model_calls=len(engine_calls))
        write(output / 'RESULT.json', result)


def reduce(root, reviews_path=None):
    frozen = source.read(root / 'prepare/COHORT.json')
    reviews = source.read(reviews_path) if reviews_path else {}
    summaries, rows, episodes, resources = {}, [], [], {}
    collection = source.read(root / 'collection/RESULT.json')
    reference = []
    for world in frozen['worlds']:
        for task in screen.tasks(world):
            reference.append(screen.episode(world, task, screen.first_port, {})['correct'])
    for state in screen.STATES:
        terminal = source.read(root / state / 'RESULT.json')
        source.require(terminal['status'] == 'COMPLETE', 'terminal_state_required')
        source.require(all(terminal[key] == collection[key] for key in
                       ('store_sha256', 'cohort_sha256', 'prepare_sha256', 'source_commit', 'protocol_sha256')),
                       'paired_provenance_drift')
        resources[state] = terminal
        mask, outcomes, row_count, unresolved = [], [], 0, 0
        for world_index, world in enumerate(frozen['worlds']):
            for goal_index, task in enumerate(screen.tasks(world)):
                record = source.read(root / state / f'EPISODE_{world_index:02d}_{goal_index}.json')
                screen.readout.score(world, task, record)
                admitted_route_turns = 0
                for capture in record['captures']:
                    row_id = f'{state}/{world_index}/{goal_index}/{capture["turn"]}'
                    gate = screen.row_gate(record, capture, reviews.get(row_id))
                    row_count += int(gate['admitted'])
                    unresolved += int(gate['semantic_status'] == 'UNRESOLVED')
                    admitted_route_turns += int(gate['admitted'] and capture['command']['kind'] == 'ROUTE')
                    rows.append(dict(row_id=row_id, **gate, capture_sha256=screen.digest(capture),
                        raw_sha256=screen.digest((capture.get('response') or {}).get('raw')),
                        review=reviews.get(row_id), student=screen.student_row(capture) if gate['admitted'] else None))
                qualified = record['correct'] and admitted_route_turns == 2
                mask.append(qualified)
                outcomes.append(record['correct'])
                episodes.append(dict(state=state, world_index=world_index, goal_index=goal_index,
                    success=record['correct'], qualified=qualified, actor_calls=record['actor_calls'],
                    terminal_reason=record['terminal_reason'], routes=record['routes'], reads=record['reads']))
        summaries[state] = dict(successful_episodes=sum(outcomes), qualified_episodes=sum(mask),
            episode_denominator=16, admitted_rows=row_count, unresolved_rows=unresolved, qualified_mask=mask,
            successful_worlds=sum(any(outcomes[index:index+2]) for index in range(0, 16, 2)),
            qualified_worlds=sum(any(mask[index:index+2]) for index in range(0, 16, 2)), world_denominator=8)
        state_rows = [row for row in rows if row['row_id'].startswith(state + '/')]
        tokens = [row['generated_text_tokens'] for row in state_rows if row['generated_text_tokens'] >= 0]
        summaries[state]['tokens'] = dict(count=len(tokens), total=sum(tokens),
            minimum=min(tokens) if tokens else None, maximum=max(tokens) if tokens else None,
            median=statistics.median(tokens) if tokens else None,
            within_150_400=sum(150 <= value <= 400 for value in tokens),
            below_150=sum(value < 150 for value in tokens), above_400=sum(value > 400 for value in tokens),
            all_generated_text_token_counts=tokens)
        summaries[state]['per_world'] = [dict(world_index=index, successful_episodes=sum(outcomes[2*index:2*index+2]),
            qualified_episodes=sum(mask[2*index:2*index+2]), episode_denominator=2) for index in range(8)]
    calls = collection['model_calls'] + sum(result['model_calls'] for result in resources.values())
    source.require(calls <= screen.TOTAL_CAP, 'total_native_cap')
    return dict(status='COMPLETE' if not any(item['unresolved_rows'] for item in summaries.values()) else 'REVIEW_PENDING',
        decision=screen.decision(summaries) if not any(item['unresolved_rows'] for item in summaries.values()) else 'PENDING',
        summaries=summaries, episode_counts=episodes, rows=rows, resources=resources, collection=collection,
        model_calls=calls, native_active_gpu_hours=sum(result['elapsed_seconds'] for result in
        [collection, *resources.values()])/3600, reference=dict(successful_episodes=sum(reference),
        episode_denominator=16, outcomes=reference, policy='FIRST_CURRENT_DISPLAYED_PORT_NO_READ'), fits=0,
        independent_reader='PENDING_NOT_EXECUTED_BY_WORKER', claim='EXPERIMENTAL_CANDIDATE_NO_FIT_NO_H1_H2')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=('prepare', 'collect', 'readout', 'reduce'), required=True)
    parser.add_argument('--state', choices=screen.STATES, default='ORIGINAL37EC')
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--source-sha')
    parser.add_argument('--commit')
    parser.add_argument('--deadline', type=float)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options)
    elif options.phase == 'reduce':
        write(options.output or options.root / 'REDUCTION.json', reduce(options.root, options.reviews))
    else:
        native(options)


if __name__ == '__main__':
    main()
