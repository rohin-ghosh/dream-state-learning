"""One portable, readonly 37ec scale shard; no ancestor reads or fitting.

Execution completion is not case success. Partial source/teaching outcomes and
actual native failures stay recorded, with all-or-none 192-target admission.
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


source = portable.source
require = source.require
PARENT_STATE = portable.PARENT_STATE
SCHEMA = 'DEV_GOAL_SCALE_COLLECTION_V1'
CAPS = dict(prepare=0, expose=80, teach=192, baseline=288)
CONDITIONS = ('OWN_TEXT', 'UNAVAILABLE')
PROTOCOL_PATH = 'research_notes/analysis/2026-09-14_goal_scale_collection_protocol.md'
PROTOCOL_SHA = 'dd1d078a01d9f547219afd23790c467ca0ccb413f3148a2af9b963b63e652f24'


def same(actual, expected, reason):
    require(scale.document_sha256(actual) == scale.document_sha256(expected), reason)


def helpers():
    return dict(driver=source.file_hash(__file__),
        guard=source.file_hash(Path(__file__).with_name('astra_goal_scale_collection_guard.sh')),
        scale=source.file_hash(scale.__file__), breadth=source.file_hash(breadth.__file__),
        portable_contract=portable.contract())


def load_inputs(options):
    require(type(PROTOCOL_PATH) is str and type(PROTOCOL_SHA) is str, 'prospective_scale_protocol_not_bound')
    protocol = Path(__file__).resolve().parents[1] / PROTOCOL_PATH
    require(source.file_hash(protocol) == PROTOCOL_SHA, 'committed_scale_protocol_required')
    scale.runtime(options.shard)
    manifest = portable.read_manifest(options.bundle, expected_manifest_sha256=options.bundle_sha)
    verified = portable.verify_base_files(options.bundle, options.model_dir, expected_manifest_sha256=options.bundle_sha)
    require(manifest['parent_state'] == PARENT_STATE and verified['verified'], 'verified_portable_37ec_required')
    old_ids = set(manifest['old_ids'])
    for worlds in breadth.build_worlds(old_ids=old_ids).values():
        for world in worlds:
            old_ids.update(breadth.identifiers(world))
    registry = scale.validate_registry(old_ids=old_ids)
    worlds = registry[options.shard]
    binding = dict(bundle_sha256=options.bundle_sha, source_contract=manifest['source_contract'],
        protocol_sha256=PROTOCOL_SHA, shard=options.shard, state=PARENT_STATE,
        expected_base_sha256=manifest['expected_base_sha256'], base_files=manifest['base_files'],
        tokenizer_files=manifest['tokenizer_files'], adapter_files=manifest['adapter_files'],
        old_ids=sorted(old_ids), registry_sha256=scale.document_sha256(registry), worlds=worlds, helpers=helpers())
    return dict(binding=binding, manifest=manifest, shard=options.shard, worlds=worlds, registry=registry,
                old_ids=sorted(old_ids), base_verification=verified)


def execute_phase(phase, inputs, generate, exposure=None, emit=None):
    goal = SimpleNamespace(**scale.runtime(inputs['shard']))
    emit = emit or (lambda name, document: None)
    if phase == 'expose':
        collections = []
        for split in ('TRAIN', 'PROBE'):
            for world in inputs['worlds'][split]:
                document = goal.collect_world(world, lambda messages: generate(messages,
                    role='exposure', master=world['master']), old_ids=inputs['old_ids'])
                goal.replay_collection(document, old_ids=inputs['old_ids'])
                collections.append(document)
                emit(f'COLLECTION_{len(collections) - 1:02d}.json', document)
        ready = all(item['ready'] for item in collections)
        return dict(collections=collections, source_ready=ready,
            case_failures=sum(not record['accepted'] for item in collections for record in item['records']),
            data_status='SOURCE_READY' if ready else 'PARTIAL_SOURCE_FAILURES')
    require(phase in ('teach', 'baseline') and exposure is not None and exposure['source_ready'],
            'complete_ten_world_exposure_required')
    collections = exposure['collections']
    require(tuple(item['master'] for item in collections) == goal.MASTERS, 'fixed_shard_collection_order_required')
    if phase == 'teach':
        document = goal.collect_lessons(collections[:8],
            lambda messages: generate(messages, role='coached_actor'), old_ids=inputs['old_ids'])
        emit('LESSONS.json', document)
        rows = goal.replay_lessons(document)
        require(len(rows) == (192 if document['ready'] else 0), 'all_or_none_192_actual_targets_required')
        require(all(row['master'] in goal.TRAIN_MASTERS for row in rows), 'shard_train_only_targets_required')
        probe_ids = set().union(*(scale.identifiers(world) for worlds in inputs['registry'].values()
                                  for world in worlds['PROBE']))
        serialized = source.json.dumps(rows, allow_nan=False)
        require(not any(identifier in serialized for identifier in probe_ids), 'no_scale_probe_training_rows')
        require(all('PARENT PROCEDURAL GUIDANCE' not in source.json.dumps(row['prefix']) for row in rows),
                'student_prefix_must_exclude_parent')
        return dict(lessons=document, row_count=len(rows), curriculum_ready=document['ready'], source_ready=True,
            case_failures=sum(not episode['complete'] for episode in document['episodes']),
            data_status='CURRICULUM_READY' if document['ready'] else 'PARTIAL_TEACHING_FAILURES')
    panels = []
    for index, collection in enumerate(collections):
        split, world_index = ('TRAIN', index) if index < 8 else ('PROBE', index - 8)
        world, store = collection['world'], goal.exact_text_store(collection)
        for condition in (('OWN_TEXT',) if split == 'TRAIN' else CONDITIONS):
            episodes = []
            for task_index, task in enumerate(goal.build_tasks(world)):
                def actor(messages):
                    return generate(messages, role='actor', master=world['master'],
                                    condition=condition, task_index=task_index, graph=split)

                def read(address):
                    return store[address] if condition == 'OWN_TEXT' else 'MEMORY UNAVAILABLE'

                episode = goal.run_episode(world, task, actor, read)
                goal.replay_episode(world, task, episode)
                episodes.append(episode)
                emit(f'{split}_{world_index}_{condition}_{task_index}.json', episode)
            panels.append(dict(master=world['master'], split=split, condition=condition,
                collection_sha256=collection['collection_sha256'], shared_text_sha256=scale.document_sha256(store),
                episodes=episodes, summary=goal.summarize_pairs(collection, episodes)))
    failures = sum(not score['correct'] for panel in panels for score in panel['summary']['scores'])
    return dict(panels=panels, source_ready=True, case_failures=failures, data_status='READOUT_RECORDED')


def read_stage(directory, phase, inputs, exposure=None, dependencies=None):
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    require(not (directory / 'FAILED.json').exists() and result.get('schema') == SCHEMA
        and result.get('phase') == phase and result.get('status') == 'COMPLETE'
        and result.get('shard') == inputs['shard'] and result.get('fits') == result.get('updates') == 0
        and result.get('trainingAllowed') is False
        and result.get('loaded_adapter_state_sha256') == result.get('adapter_state_after') == PARENT_STATE
        and result.get('frozen_base_unchanged') is True and result.get('protocol') == breadth.PROTOCOL
        and result.get('parent_present') == (phase == 'teach')
        and result.get('max_native_calls') == CAPS[phase], 'complete_readonly_scale_stage_required')
    same(result['binding'], inputs['binding'], 'scale_stage_binding_drift')
    same(result['dependencies'], dependencies or {}, 'scale_stage_join_drift')
    same(source.read(directory / 'STATES.json'), dict(before=PARENT_STATE, after=PARENT_STATE), 'scale_stage_state_drift')
    files = result['output_files']
    require(set(files) == {path.name for path in directory.glob('*.json') if path.name != 'RESULT.json'},
            'scale_stage_file_inventory_drift')
    portable.transfer.verify_files(directory, files)
    count = result['model_calls']
    require(type(count) is int and 0 <= count <= CAPS[phase], 'bounded_scale_native_inventory')
    require({path.name for path in directory.glob('CALL_*.json')} == {f'CALL_{index:03d}.json' for index in range(count)},
            'exact_scale_native_inventory')
    captures = [source.read(directory / f'CALL_{index:03d}.json') for index in range(count)]
    cursor = iter(enumerate(captures))

    def generate(messages, **metadata):
        item = next(cursor, None)
        require(item is not None, 'missing_scale_native_call')
        index, capture = item
        expected = dict(call_index=index, shard=inputs['shard'], messages=messages,
                        response=capture['response'], error=None, **metadata)
        same(capture, expected, 'scale_native_capture_drift')
        return deepcopy(capture['response'])

    def emit(name, document):
        same(source.read(directory / name), document, 'scale_stage_artifact_drift:' + name)

    document = execute_phase(phase, inputs, generate, exposure, emit)
    require(next(cursor, None) is None, 'unknown_scale_native_call')
    same(source.read(directory / 'DATA.json'), document, 'scale_stage_replay_drift')
    same(result['role_calls'], dict(Counter(capture['role'] for capture in captures)), 'scale_role_count_drift')
    for key in ('source_ready', 'case_failures', 'data_status'):
        same(result[key], document[key], 'scale_data_status_drift:' + key)
    if phase == 'teach':
        require(result['curriculum_ready'] == document['curriculum_ready']
                and result['row_count'] == document['row_count'], 'scale_curriculum_summary_drift')
    if phase == 'baseline':
        same(result['summaries'], [{key: panel[key] for key in ('master', 'split', 'condition', 'summary')}
                                  for panel in document['panels']], 'scale_baseline_summary_drift')
    return document, source.file_hash(directory / 'RESULT.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'bundle-sha', 'model-dir', 'output', 'gpu-uuid'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--shard', type=int, choices=scale.SHARDS, required=True)
    parser.add_argument('--phase', choices=tuple(CAPS), required=True)
    parser.add_argument('--exposure')
    parser.add_argument('--teaching')
    options = parser.parse_args(argv)
    require(bool(options.exposure) == (options.phase in ('teach', 'baseline'))
            and bool(options.teaching) == (options.phase == 'baseline'), 'scale_phase_arguments')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    require(not output.exists() and not output.is_symlink(), 'fresh_immutable_scale_phase_required')
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, shard=options.shard, arguments=vars(options), started_unix=started,
        fits=0, updates=0, trainingAllowed=False, automatic_training=False, model_calls=0,
        max_native_calls=CAPS[options.phase], parent_present=options.phase == 'teach', protocol=breadth.PROTOCOL,
        max_context=2048, max_new_tokens=160, claim=scale.CLAIM, entry_sha256=source.file_hash(__file__),
        protocol_sha256=PROTOCOL_SHA, expected_train_targets=192,
        interpretation='EXECUTION_COMPLETION_IS_NOT_CASE_SUCCESS_OR_GENERAL_PLANNING')
    source.write(output / 'REQUEST.json', result)
    captures, engine, cap_hit = [], None, False

    def check(label):
        require(time.time() < started + 3500, 'scale_stage_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result.update(binding=inputs['binding'], dependencies={}, base_file_verification=inputs['base_verification'])
        for name, document in (('INPUTS.json', inputs['binding']), ('WORLDS.json', inputs['worlds']),
                               ('REGISTRY.json', inputs['registry'])):
            source.write(output / name, document)
        exposure = None
        if options.exposure:
            exposure, exposure_sha = read_stage(options.exposure, 'expose', inputs)
            require(exposure['source_ready'], 'complete_ten_world_exposure_required')
            result['dependencies']['exposure_result_sha256'] = exposure_sha
        if options.teaching:
            unused_teaching, teaching_sha = read_stage(options.teaching, 'teach', inputs, exposure,
                dict(exposure_result_sha256=exposure_sha))
            result['dependencies']['teaching_result_sha256'] = teaching_sha
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
        require(not any(parameter.requires_grad for unused, parameter in engine.model.named_parameters()),
                'scale_actor_must_be_frozen')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=PARENT_STATE)

        def generate(messages, **metadata):
            nonlocal cap_hit
            check('call')
            if len(captures) >= CAPS[options.phase]:
                cap_hit = True
                raise ValueError('scale_native_call_cap')
            capture = dict(call_index=len(captures), shard=options.shard, messages=deepcopy(messages),
                           response=None, error=None, **metadata)
            captures.append(capture)
            try:
                capture['response'] = deepcopy(engine.generate(deepcopy(messages), max_new_tokens=160))
                return deepcopy(capture['response'])
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                source.write(output / f"CALL_{capture['call_index']:03d}.json", capture)

        document = execute_phase(options.phase, inputs, generate, exposure,
                                 lambda name, value: source.write(output / name, value))
        source.write(output / 'DATA.json', document)
        require(not cap_hit, 'scale_native_call_cap')
        require(not any(capture['error'] is not None for capture in captures), 'native_errors_retained')
        engine.verify_base()
        final_state = _state_hash(parameters)
        require(final_state == PARENT_STATE, 'readonly_scale_state_drift')
        portable.verify_base_files(options.bundle, arguments.model_dir, expected_manifest_sha256=options.bundle_sha)
        same(helpers(), inputs['binding']['helpers'], 'runtime_scale_helper_drift')
        source.write(output / 'STATES.json', dict(before=PARENT_STATE, after=final_state))
        result.update(status='COMPLETE', adapter_state_after=final_state, frozen_base_unchanged=True,
            model_calls=len(captures), role_calls=dict(Counter(capture['role'] for capture in captures)),
            source_ready=document['source_ready'], case_failures=document['case_failures'],
            data_status=document['data_status'], finished_unix=time.time())
        if options.phase == 'teach':
            result.update(curriculum_ready=document['curriculum_ready'], row_count=document['row_count'])
        if options.phase == 'baseline':
            result['summaries'] = [{key: panel[key] for key in ('master', 'split', 'condition', 'summary')}
                                   for panel in document['panels']]
        result['output_files'] = {path.name: source.file_hash(path) for path in output.glob('*.json')}
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
