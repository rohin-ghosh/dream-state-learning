"""Portable readonly rich actor/critic capture with explicit action projections.

Four fresh-process phases preserve actual native outputs. Only extracted child
action bytes execute; critiques are unreviewed candidates and never fit targets.
"""

import argparse
from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import time
from types import SimpleNamespace

from gpu import astra_portable_actor_bundle as portable
from organism_v6 import experienced_event_goal_breadth as breadth
from organism_v6 import experienced_event_goal_scale as scale
from organism_v6 import experienced_event_rich_trajectory as rich


source = portable.source
require = source.require
PARENT_STATE = portable.PARENT_STATE
SCHEMA = 'DEV_RICH_TRAJECTORY_COLLECTION_V1'
CAPS = dict(prepare=0, expose=40, teach=96, critique=16, baseline=144)
TOKEN_CAPS = dict(prepare=0, expose=160, teach=512, critique=512, baseline=160)
CONDITIONS = ('OWN_TEXT', 'UNAVAILABLE')
PROTOCOL_PATH = 'research_notes/analysis/2026-09-14_rich_trajectory_collection_protocol.md'
PROTOCOL_SHA = '339c25c05cdb1bd6ba07bfd22520c68df6f23117fed0627cb245e23c6ba2bd2f'


def same(actual, expected, reason):
    require(rich.document_sha256(actual) == rich.document_sha256(expected), reason)


def helpers():
    return dict(driver=source.file_hash(__file__),
        guard=source.file_hash(Path(__file__).with_name('astra_rich_trajectory_collection_guard.sh')),
        rich=source.file_hash(rich.__file__), scale=source.file_hash(scale.__file__),
        breadth=source.file_hash(breadth.__file__), portable_contract=portable.contract())


def load_inputs(options):
    require(type(PROTOCOL_PATH) is str and type(PROTOCOL_SHA) is str, 'prospective_rich_protocol_not_bound')
    protocol = Path(__file__).resolve().parents[1] / PROTOCOL_PATH
    require(source.file_hash(protocol) == PROTOCOL_SHA, 'committed_rich_protocol_required')
    rich.runtime(options.shard)
    manifest = portable.read_manifest(options.bundle, expected_manifest_sha256=options.bundle_sha)
    verified = portable.verify_base_files(options.bundle, options.model_dir, expected_manifest_sha256=options.bundle_sha)
    require(manifest['parent_state'] == PARENT_STATE and verified['verified'], 'verified_portable_37ec_required')
    old_ids = set(manifest['old_ids'])
    for worlds in breadth.build_worlds(old_ids=old_ids).values():
        for world in worlds:
            old_ids.update(breadth.identifiers(world))
    for worlds in scale.validate_registry(old_ids=old_ids).values():
        for world in worlds['TRAIN'] + worlds['PROBE']:
            old_ids.update(scale.identifiers(world))
    registry = rich.validate_registry(old_ids=old_ids)
    worlds = registry[options.shard]
    binding = dict(bundle_sha256=options.bundle_sha, source_contract=manifest['source_contract'],
        protocol_path=PROTOCOL_PATH, protocol_sha256=PROTOCOL_SHA, shard=options.shard, state=PARENT_STATE,
        expected_base_sha256=manifest['expected_base_sha256'], base_files=manifest['base_files'],
        tokenizer_files=manifest['tokenizer_files'], adapter_files=manifest['adapter_files'],
        old_ids=sorted(old_ids), registry_sha256=rich.document_sha256(registry), worlds=worlds,
        rich_protocol=deepcopy(rich.PROTOCOL), helpers=helpers())
    return dict(binding=binding, manifest=manifest, shard=options.shard, worlds=worlds, registry=registry,
                old_ids=sorted(old_ids), base_verification=verified)


def execute_phase(phase, inputs, generate, exposure=None, teaching=None, emit=None):
    goal = SimpleNamespace(**rich.runtime(inputs['shard']))
    emit = emit or (lambda name, document: None)
    if phase == 'expose':
        collections = []
        for split in ('TRAIN', 'PROBE'):
            for world in inputs['worlds'][split]:
                document = rich.collect_world(world, lambda messages: generate(messages,
                    role='exposure', master=world['master']), old_ids=inputs['old_ids'])
                rich.replay_collection(document, old_ids=inputs['old_ids'])
                collections.append(document)
                emit(f'COLLECTION_{len(collections) - 1:02d}.json', document)
        ready = all(item['ready'] for item in collections)
        return dict(collections=collections, source_ready=ready,
            case_failures=sum(not record['accepted'] for item in collections for record in item['records']),
            data_status='SOURCE_READY' if ready else 'PARTIAL_SOURCE_FAILURES')
    require(phase in ('teach', 'critique', 'baseline') and exposure is not None and exposure['source_ready'],
            'complete_five_world_exposure_required')
    collections = exposure['collections']
    require(tuple(item['master'] for item in collections) == goal.MASTERS, 'fixed_rich_shard_collection_order_required')
    if phase == 'teach':
        document = rich.collect_teaching(inputs['shard'], collections[:4],
            lambda messages: generate(messages, role='rich_actor'), old_ids=inputs['old_ids'],
            protocol=inputs['binding']['rich_protocol'])
        emit('LESSONS.json', document)
        rows = rich.replay_teaching(document)
        counts = {form: len(rows[form]) for form in rich.FORMS}
        require(len(set(counts.values())) == 1 and 0 <= counts['RICH'] <= 96 and counts['RICH'] % 6 == 0,
                'matched_bounded_complete_episode_rows_required')
        require(document['fit_ready'] is False, 'rich_candidates_not_fit_ready')
        by_call = {capture['call_index']: capture for capture in document['captures']}
        retained = [by_call[index] for episode in document['episodes'] if episode['complete']
                    for index in episode['call_indexes']]
        episode_ids = [episode['episode_id'] for episode in document['episodes'] if episode['complete']
                       for index in episode['call_indexes']]
        identity_keys = ('master', 'world_index', 'task_index', 'episode_call_index', 'call_sha256', 'source_sha256')
        identities = [[capture[key] for key in identity_keys] for capture in retained]
        require(len(retained) == len({capture['call_index'] for capture in retained}), 'unique_completed_episode_calls_required')
        for form in rich.FORMS:
            same([[row[key] for key in identity_keys] for row in rows[form]], identities,
                 'all_and_only_completed_episode_pairs_required:' + form)
            same([row['episode_id'] for row in rows[form]], episode_ids, 'matched_source_episode_ids_required:' + form)
        complete_corpus = counts['RICH'] == 96
        require(all(row['master'] in goal.TRAIN_MASTERS for form in rich.FORMS for row in rows[form]),
                'rich_train_only_targets_required')
        probe_ids = set().union(*(rich.identifiers(world) for worlds in inputs['registry'].values() for world in worlds['PROBE']))
        require(not any(identifier in source.json.dumps(rows, allow_nan=False) for identifier in probe_ids),
                'no_rich_probe_training_rows')
        projections = [dict(call_index=capture['call_index'], call_sha256=capture['call_sha256'],
            projection=capture['projection'], validation_error=capture['validation_error']) for capture in document['captures']]
        emit('ACTION_PROJECTIONS.json', projections)
        return dict(lessons=document, row_count=counts['RICH'], row_counts=counts, curriculum_ready=complete_corpus,
            candidate_count=counts['RICH'], complete_corpus=complete_corpus, fit_ready=False,
            source_ready=True, case_failures=sum(not entry['complete'] for entry in document['episodes']),
            rejection_counts=dict(Counter(capture['validation_error']['message'] for capture in document['captures']
                                          if capture['validation_error'] is not None)),
            data_status='COMPLETE_RICH_CANDIDATES_NO_FIT' if complete_corpus else 'PARTIAL_RICH_CANDIDATES_NO_FIT')
    if phase == 'critique':
        require(teaching is not None, 'saved_actual_teaching_required')
        document = rich.collect_critiques(teaching['lessons'], lambda messages: generate(messages, role='critic'))
        emit('CRITIQUES.json', document)
        rich.replay_critiques(document)
        require(len(document['critiques']) == len(teaching['lessons']['episodes']) == 16,
                'all_attempted_train_episodes_critiqued')
        return dict(critiques=document, source_ready=True, candidate_only=True, reviewed=False,
                    data_status='CRITIQUE_CANDIDATES_ONLY',
                    case_failures=sum(item['validation_error'] is not None for item in document['critiques']))
    panels = []
    for index, collection in enumerate(collections):
        split, world_index = ('TRAIN', index) if index < 4 else ('PROBE', index - 4)
        world, store = collection['world'], goal.exact_text_store(collection)
        for condition in (('OWN_TEXT',) if split == 'TRAIN' else CONDITIONS):
            episodes = []
            for task_index, task in enumerate(goal.build_tasks(world)):
                def actor(messages):
                    return generate(messages, role='actor', master=world['master'], condition=condition,
                                    task_index=task_index, graph=split)

                def read(address):
                    return store[address] if condition == 'OWN_TEXT' else 'MEMORY UNAVAILABLE'

                episode = goal.run_episode(world, task, actor, read)
                goal.replay_episode(world, task, episode)
                episodes.append(episode)
                emit(f'{split}_{world_index}_{condition}_{task_index}.json', episode)
            panels.append(dict(master=world['master'], split=split, condition=condition,
                collection_sha256=collection['collection_sha256'], shared_text_sha256=rich.document_sha256(store),
                episodes=episodes, summary=goal.summarize_pairs(collection, episodes)))
    return dict(panels=panels, source_ready=True, data_status='COMMAND_ONLY_READOUT_RECORDED',
                case_failures=sum(not score['correct'] for panel in panels for score in panel['summary']['scores']))


def native_metrics(captures):
    calls = []
    for capture in captures:
        response = capture['response']
        response = response if type(response) is dict else {}
        raw, tokens = response.get('raw'), response.get('token_ids')
        calls.append(dict(call_index=capture['call_index'], role=capture['role'],
            prompt_tokens=response.get('prompt_tokens'),
            generated_tokens=len(tokens) if type(tokens) is list else None,
            words=len(raw.split()) if type(raw) is str else None,
            terminal=response.get('terminal'), truncated=response.get('truncated'),
            error=capture['error']))
    return dict(calls=calls, totals={key: sum(item[key] for item in calls if type(item[key]) is int)
        for key in ('prompt_tokens', 'generated_tokens', 'words')},
        missing_token_counts=sum(item['prompt_tokens'] is None or item['generated_tokens'] is None for item in calls),
        equal_compute_claim=False)


def paired_token_report(document, tokenizer):
    if not document['row_count']:
        return dict(status='NO_COMPLETE_PAIRS', ready=False, fits=0, fit_ready=False,
                    candidate_count=0, complete_corpus=False)
    try:
        paired = rich.encode_paired_rows(rich.replay_teaching(document['lessons']), tokenizer)
        counts = {form: {key: sum(row['forms'][form][key] for row in paired['ledger'])
                        for key in ('input_tokens', 'active_tokens', 'action_tokens', 'rationale_and_delimiter_tokens')}
                  for form in rich.FORMS}
        action = counts['RICH']['action_tokens']
        return dict(status='VERIFIED_PAIRED_TOKEN_BOUNDARIES', ready=True, fits=0,
            ledger=paired['ledger'], totals=counts, equal_compute_claim=False, candidate_count=document['row_count'],
            complete_corpus=document['complete_corpus'], fit_ready=False,
            rationale_and_delimiter_to_action_ratio=counts['RICH']['rationale_and_delimiter_tokens'] / action,
            interpretation='RECORDED_TOKENIZER_CHECK_NOT_INDEPENDENT_TENSOR_AUTHENTICATION')
    except Exception as error:
        return dict(status='PAIRED_ENCODING_REJECTED', ready=False, fits=0, fit_ready=False,
                    candidate_count=document['row_count'], complete_corpus=document['complete_corpus'],
                    error=dict(type=type(error).__name__, message=str(error)))


def read_stage(directory, phase, inputs, exposure=None, teaching=None, dependencies=None):
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    require(not (directory / 'FAILED.json').exists() and result.get('schema') == SCHEMA
        and result.get('phase') == phase and result.get('status') == 'COMPLETE'
        and result.get('shard') == inputs['shard'] and result.get('fits') == result.get('updates') == 0
        and result.get('trainingAllowed') is False
        and result.get('loaded_adapter_state_sha256') == result.get('adapter_state_after') == PARENT_STATE
        and result.get('frozen_base_unchanged') is True
        and result.get('parent_present') == (phase == 'teach')
        and result.get('max_native_calls') == CAPS[phase] and result.get('max_new_tokens') == TOKEN_CAPS[phase],
        'complete_readonly_rich_stage_required')
    same(result['binding'], inputs['binding'], 'rich_stage_binding_drift')
    same(result['dependencies'], dependencies or {}, 'rich_stage_join_drift')
    same(source.read(directory / 'STATES.json'), dict(before=PARENT_STATE, after=PARENT_STATE), 'rich_stage_state_drift')
    files = result['output_files']
    require(set(files) == {path.name for path in directory.glob('*.json') if path.name != 'RESULT.json'},
            'rich_stage_file_inventory_drift')
    portable.transfer.verify_files(directory, files)
    count = result['model_calls']
    require(type(count) is int and 0 <= count <= CAPS[phase], 'bounded_rich_native_inventory')
    require({path.name for path in directory.glob('CALL_*.json')} == {f'CALL_{index:03d}.json' for index in range(count)},
            'exact_rich_native_inventory')
    captures = [source.read(directory / f'CALL_{index:03d}.json') for index in range(count)]
    cursor = iter(enumerate(captures))

    def generate(messages, **metadata):
        item = next(cursor, None)
        require(item is not None, 'missing_rich_native_call')
        index, capture = item
        expected = dict(call_index=index, shard=inputs['shard'], messages=messages, max_new_tokens=TOKEN_CAPS[phase],
                        response=capture['response'], error=None, **metadata)
        same(capture, expected, 'rich_native_capture_drift')
        return deepcopy(capture['response'])

    def emit(name, document):
        same(source.read(directory / name), document, 'rich_stage_artifact_drift:' + name)

    document = execute_phase(phase, inputs, generate, exposure, teaching, emit)
    require(next(cursor, None) is None, 'unknown_rich_native_call')
    same(source.read(directory / 'DATA.json'), document, 'rich_stage_replay_drift')
    same(source.read(directory / 'NATIVE_METRICS.json'), native_metrics(captures), 'rich_native_metrics_drift')
    same(result['role_calls'], dict(Counter(capture['role'] for capture in captures)), 'rich_role_count_drift')
    for key in ('source_ready', 'case_failures', 'data_status'):
        same(result[key], document[key], 'rich_data_status_drift:' + key)
    if phase == 'teach':
        for key in ('curriculum_ready', 'row_count', 'row_counts', 'rejection_counts', 'candidate_count', 'complete_corpus', 'fit_ready'):
            same(result[key], document[key], 'rich_pair_summary_drift:' + key)
        same(result['encoded_pairs_ready'], source.read(directory / 'PAIRED_TOKEN_REPORT.json')['ready'],
             'rich_encoded_pair_summary_drift')
    if phase == 'critique':
        require(result.get('candidate_only') is True and result.get('reviewed') is False
                and result.get('fit_targets') == 0, 'critique_candidates_not_fit_targets')
    if phase == 'baseline':
        same(result['summaries'], [{key: panel[key] for key in ('master', 'split', 'condition', 'summary')}
                                  for panel in document['panels']], 'rich_baseline_summary_drift')
    return document, source.file_hash(directory / 'RESULT.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'bundle-sha', 'model-dir', 'output', 'gpu-uuid'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--shard', type=int, choices=rich.SHARDS, required=True)
    parser.add_argument('--phase', choices=tuple(CAPS), required=True)
    parser.add_argument('--exposure')
    parser.add_argument('--teaching')
    parser.add_argument('--critique')
    options = parser.parse_args(argv)
    require(bool(options.exposure) == (options.phase in ('teach', 'critique', 'baseline'))
        and bool(options.teaching) == (options.phase in ('critique', 'baseline'))
        and bool(options.critique) == (options.phase == 'baseline'), 'rich_phase_arguments')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    require(not output.exists() and not output.is_symlink(), 'fresh_immutable_rich_phase_required')
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, shard=options.shard, arguments=vars(options), started_unix=started,
        fits=0, updates=0, trainingAllowed=False, automatic_training=False, model_calls=0,
        max_native_calls=CAPS[options.phase], parent_present=options.phase == 'teach',
        action_protocol='turnbound', max_context=2048, max_new_tokens=TOKEN_CAPS[options.phase],
        entry_sha256=source.file_hash(__file__), protocol_sha256=PROTOCOL_SHA, expected_paired_targets=96,
        claim='RICH_DEV_DATA_NOT_RATIONALE_TRUTH_OR_GENERAL_PLANNING',
        probe_scope='NEW_IDENTIFIER_DEV_EXISTING_GRAMMAR_NOT_CLEAN_LINEAGE',
        interpretation='EXECUTION_COMPLETION_IS_NOT_CASE_SUCCESS_CRITICS_ARE_CANDIDATES_ONLY')
    source.write(output / 'REQUEST.json', result)
    captures, engine, cap_hit = [], None, False

    def check(label):
        require(time.time() < started + 3500, 'rich_stage_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result.update(binding=inputs['binding'], dependencies={}, base_file_verification=inputs['base_verification'])
        for name, document in (('INPUTS.json', inputs['binding']), ('WORLDS.json', inputs['worlds']), ('REGISTRY.json', inputs['registry'])):
            source.write(output / name, document)
        exposure, teaching = None, None
        if options.exposure:
            exposure, exposure_sha = read_stage(options.exposure, 'expose', inputs)
            require(exposure['source_ready'], 'complete_five_world_exposure_required')
            result['dependencies']['exposure_result_sha256'] = exposure_sha
        if options.teaching:
            teaching, teaching_sha = read_stage(options.teaching, 'teach', inputs, exposure,
                dependencies=dict(exposure_result_sha256=exposure_sha))
            result['dependencies']['teaching_result_sha256'] = teaching_sha
        if options.critique:
            unused_critique, critique_sha = read_stage(options.critique, 'critique', inputs, exposure, teaching,
                dict(exposure_result_sha256=exposure_sha, teaching_result_sha256=teaching_sha))
            result['dependencies']['critique_result_sha256'] = critique_sha
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return result
        arguments = portable.read_bundle(options.bundle, expected_manifest_sha256=options.bundle_sha,
            model_dir=options.model_dir, device='cuda:0', gpu_uuid=options.gpu_uuid)
        engine = source.Engine(arguments, source.native.load_local_tokenizer(arguments.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        require(bool(parameters) and _state_hash(parameters) == PARENT_STATE, 'mounted_37ec_state_required')
        require(not any(parameter.requires_grad for unused, parameter in engine.model.named_parameters()), 'rich_actor_must_be_frozen')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=PARENT_STATE)

        def generate(messages, **metadata):
            nonlocal cap_hit
            check('call')
            if len(captures) >= CAPS[options.phase]:
                cap_hit = True
                raise ValueError('rich_native_call_cap')
            capture = dict(call_index=len(captures), shard=options.shard, messages=deepcopy(messages),
                max_new_tokens=TOKEN_CAPS[options.phase], response=None, error=None, **metadata)
            captures.append(capture)
            try:
                capture['response'] = deepcopy(engine.generate(deepcopy(messages), max_new_tokens=TOKEN_CAPS[options.phase]))
                return deepcopy(capture['response'])
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                source.write(output / f"CALL_{capture['call_index']:03d}.json", capture)

        document = execute_phase(options.phase, inputs, generate, exposure, teaching,
                                 lambda name, value: source.write(output / name, value))
        source.write(output / 'DATA.json', document)
        source.write(output / 'NATIVE_METRICS.json', native_metrics(captures))
        require(not cap_hit, 'rich_native_call_cap')
        require(not any(capture['error'] is not None for capture in captures), 'native_errors_retained')
        engine.verify_base()
        final_state = _state_hash(parameters)
        require(final_state == PARENT_STATE, 'readonly_rich_state_drift')
        portable.verify_base_files(options.bundle, arguments.model_dir, expected_manifest_sha256=options.bundle_sha)
        same(helpers(), inputs['binding']['helpers'], 'runtime_rich_helper_drift')
        source.write(output / 'STATES.json', dict(before=PARENT_STATE, after=final_state))
        result.update(status='COMPLETE', adapter_state_after=final_state, frozen_base_unchanged=True,
            model_calls=len(captures), role_calls=dict(Counter(capture['role'] for capture in captures)),
            source_ready=document['source_ready'], case_failures=document['case_failures'],
            data_status=document['data_status'], finished_unix=time.time())
        if options.phase == 'teach':
            result.update(curriculum_ready=document['curriculum_ready'], row_count=document['row_count'],
                          row_counts=document['row_counts'], rejection_counts=document['rejection_counts'],
                          candidate_count=document['candidate_count'], complete_corpus=document['complete_corpus'], fit_ready=False)
            paired = paired_token_report(document, engine.tokenizer)
            source.write(output / 'PAIRED_TOKEN_REPORT.json', paired)
            result['encoded_pairs_ready'] = paired['ready']
        if options.phase == 'critique':
            result.update(candidate_only=True, reviewed=False, fit_targets=0)
        if options.phase == 'baseline':
            result['summaries'] = [{key: panel[key] for key in ('master', 'split', 'condition', 'summary')} for panel in document['panels']]
        result['output_files'] = {path.name: source.file_hash(path) for path in output.glob('*.json')}
        result['wall_seconds'] = result['finished_unix'] - started
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        if engine is not None:
            try:
                result['adapter_state_after'] = _state_hash(parameters)
                engine.verify_base()
                portable.verify_base_files(options.bundle, options.model_dir, expected_manifest_sha256=options.bundle_sha)
                result['frozen_base_unchanged'] = True
            except BaseException as verification_error:
                result['failure_verification_error'] = repr(verification_error)
            source.write(output / 'STATES.json', dict(before=result.get('loaded_adapter_state_sha256'),
                expected=PARENT_STATE, after=result.get('adapter_state_after')))
        result.update(status='FAILED', error=repr(error), model_calls=len(captures), cap_hit=cap_hit, finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
