"""No-fit breadth collection: eight TRAIN and two PROBE fixed-topology worlds.

Fresh readonly 37ec processes capture actual exposures, four coaching blocks,
and unassisted baselines. Old SEQ255 evidence supplies namespace exclusions,
never new targets. No model sees PROBE cases during teaching; no score gate.
"""

import argparse
from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import time

from gpu import astra_goal_pair_collection as prior
from organism_v6 import experienced_event_goal_breadth as goal


memory = prior.memory
source = memory.source
require = memory.require
same = memory.same
PARENT_STATE = memory.PARENT_STATE
CONDITIONS = prior.CONDITIONS
SCHEMA = 'DEV_GOAL_BREADTH_COLLECTION_V1'
CAPS = dict(prepare=0, expose=80, teach=192, baseline=288)
PRIOR_COLLECTION_ROOT = '/tmp/astra_goal_pair_collection_20260914_attempt1'
COLLECTION_ROOT = '/tmp/astra_goal_breadth_collection_20260914_attempt1'
PROTOCOL_PATH = 'research_notes/analysis/2026-09-14_goal_breadth_recipe_design.md'
PROTOCOL_SHA = '3f2e4307dab0ad7aa2d8cf62accf14203da1b6ac32fd58779c62840929640ed7'


def helpers():
    return dict(driver=source.file_hash(__file__),
        guard=source.file_hash(Path(__file__).with_name('astra_goal_breadth_collection_guard.sh')),
        goal=source.file_hash(goal.__file__), prior=prior.helpers())


def load_inputs(options):
    protocol = Path(__file__).resolve().parents[1] / PROTOCOL_PATH
    require(source.file_hash(protocol) == PROTOCOL_SHA, 'committed_breadth_protocol_required')
    previous = prior.load_inputs(options)
    root = Path(getattr(options, 'prior_collection_root', PRIOR_COLLECTION_ROOT))
    exposure, exposure_sha = prior.read_stage(root / 'expose', 'expose', previous)
    require(exposure['source_ready'] and tuple(item['master'] for item in exposure['collections']) == prior.goal.MASTERS,
            'actual_four_seq255_worlds_required')
    old_ids = set(previous['old_ids'])
    for collection in exposure['collections']:
        old_ids.update(goal.identifiers(collection['world']))
    worlds = goal.build_worlds(old_ids=old_ids)
    require(len(worlds['TRAIN']) == 8 and len(worlds['PROBE']) == 2, 'fixed_eight_train_two_probe_required')
    return dict(arguments=previous['arguments'], parent=previous['parent'], old_ids=sorted(old_ids), worlds=worlds,
        binding=dict(memory=previous['binding']['memory'], prior_collection=previous['binding'],
            prior_exposure_result_sha256=exposure_sha, protocol_sha256=PROTOCOL_SHA,
            old_ids=sorted(old_ids), worlds=worlds, state=PARENT_STATE, helpers=helpers()))


def execute_phase(phase, inputs, generate, exposure=None, emit=None):
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
        return dict(collections=collections, source_ready=all(item['ready'] for item in collections))
    require(phase in ('teach', 'baseline') and exposure is not None and exposure['source_ready'],
            'complete_ten_world_exposure_required')
    collections = exposure['collections']
    require(tuple(item['master'] for item in collections) == goal.MASTERS, 'fixed_breadth_collection_order_required')
    if phase == 'teach':
        document = goal.collect_lessons(collections[:8],
            lambda messages: generate(messages, role='coached_actor'), old_ids=inputs['old_ids'])
        emit('LESSONS.json', document)
        rows = goal.replay_lessons(document)
        require(len(rows) == (192 if document['ready'] else 0), 'all_or_none_192_actual_targets_required')
        require(all(row['master'] in goal.TRAIN_MASTERS for row in rows), 'breadth_train_only_targets_required')
        probe_ids = set().union(*(goal.identifiers(world) for world in inputs['worlds']['PROBE']))
        serialized = source.json.dumps(rows, allow_nan=False)
        require(not any(identifier in serialized for identifier in probe_ids), 'no_breadth_probe_training_rows')
        require(all('PARENT PROCEDURAL GUIDANCE' not in source.json.dumps(row['prefix']) for row in rows),
                'student_prefix_must_exclude_parent')
        return dict(lessons=document, row_count=len(rows), curriculum_ready=document['ready'], source_ready=True)
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
                collection_sha256=collection['collection_sha256'], shared_text_sha256=goal.document_sha256(store),
                episodes=episodes, summary=goal.summarize_pairs(collection, episodes)))
    return dict(panels=panels, source_ready=True)


def read_stage(directory, phase, inputs, exposure=None, dependencies=None):
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    require(not (directory / 'FAILED.json').exists() and result.get('schema') == SCHEMA
        and result.get('phase') == phase and result.get('status') == 'COMPLETE'
        and result.get('fits') == result.get('updates') == 0 and result.get('trainingAllowed') is False
        and result.get('loaded_adapter_state_sha256') == result.get('adapter_state_after') == PARENT_STATE
        and result.get('frozen_base_unchanged') is True and result.get('protocol') == goal.PROTOCOL
        and result.get('parent_present') == (phase == 'teach')
        and result.get('max_native_calls') == CAPS[phase], 'complete_readonly_breadth_stage_required')
    same(result['binding'], inputs['binding'], 'breadth_stage_binding_drift')
    same(result['dependencies'], dependencies or {}, 'breadth_stage_join_drift')
    same(source.read(directory / 'STATES.json'), dict(before=PARENT_STATE, after=PARENT_STATE), 'breadth_stage_state_drift')
    files = result['output_files']
    require(set(files) == {path.name for path in directory.glob('*.json') if path.name != 'RESULT.json'},
            'breadth_stage_file_inventory_drift')
    memory.transfer.verify_files(directory, files)
    captures = memory.read_calls(directory, result['model_calls'], CAPS[phase])
    cursor = iter(captures)

    def generate(messages, **metadata):
        capture = next(cursor, None)
        require(capture is not None, 'missing_breadth_native_call')
        expected = dict(call_index=capture['call_index'], messages=messages,
                        response=capture['response'], error=None, **metadata)
        same(capture, expected, 'breadth_native_capture_drift')
        return deepcopy(capture['response'])

    def emit(name, document):
        same(source.read(directory / name), document, 'breadth_stage_artifact_drift:' + name)

    document = execute_phase(phase, inputs, generate, exposure, emit)
    require(next(cursor, None) is None, 'unknown_breadth_native_call')
    same(source.read(directory / 'DATA.json'), document, 'breadth_stage_replay_drift')
    same(result['role_calls'], dict(Counter(capture['role'] for capture in captures)), 'breadth_role_count_drift')
    require(result['source_ready'] == document['source_ready'], 'breadth_source_ready_drift')
    if phase == 'teach':
        require(result['curriculum_ready'] == document['curriculum_ready']
                and result['row_count'] == document['row_count'], 'breadth_curriculum_summary_drift')
    if phase == 'baseline':
        same(result['summaries'], [{key: panel[key] for key in ('master', 'split', 'condition', 'summary')}
                                  for panel in document['panels']], 'breadth_baseline_summary_drift')
    return document, source.file_hash(directory / 'RESULT.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--lesson-root', default=memory.transfer.LESSON_ROOT)
    parser.add_argument('--transfer-root', default=memory.TRANSFER_ROOT)
    parser.add_argument('--prior-collection-root', default=PRIOR_COLLECTION_ROOT)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--phase', choices=tuple(CAPS), required=True)
    parser.add_argument('--exposure')
    parser.add_argument('--teaching')
    options = parser.parse_args(argv)
    require(bool(options.exposure) == (options.phase in ('teach', 'baseline'))
            and bool(options.teaching) == (options.phase == 'baseline'), 'breadth_phase_arguments')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or bool(options.gpu_uuid)
            and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, arguments=vars(options), started_unix=started,
        fits=0, updates=0, trainingAllowed=False, automatic_training=False, model_calls=0,
        max_native_calls=CAPS[options.phase], parent_present=options.phase == 'teach', protocol=goal.PROTOCOL,
        max_context=2048, max_new_tokens=160, claim=goal.CLAIM, entry_sha256=source.file_hash(__file__),
        protocol_sha256=PROTOCOL_SHA, probe_scope='NEW_IDENTIFIER_DEV_FIXED_TOPOLOGY_NOT_CLEAN_LINEAGE',
        expected_train_targets=192, prior_seq255_targets=0)
    source.write(output / 'REQUEST.json', result)
    captures, engine, cap_hit = [], None, False

    def check(label):
        require(time.time() < started + 3500, 'breadth_stage_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result.update(binding=inputs['binding'], dependencies={})
        source.write(output / 'INPUTS.json', inputs['binding'])
        source.write(output / 'WORLDS.json', inputs['worlds'])
        exposure = None
        if options.exposure:
            exposure, exposure_sha = read_stage(options.exposure, 'expose', inputs)
            require(exposure['source_ready'], 'complete_ten_world_exposure_required')
            result['dependencies']['exposure_result_sha256'] = exposure_sha
        if options.teaching:
            unused_teaching, teaching_sha = read_stage(options.teaching, 'teach', inputs, exposure,
                dict(exposure_result_sha256=exposure_sha))
            result['dependencies']['teaching_result_sha256'] = teaching_sha
        arguments = argparse.Namespace(**inputs['arguments'])
        arguments.phase, arguments.device, arguments.gpu_uuid = 'readout', 'cuda:0', options.gpu_uuid
        arguments.adapter_dir = inputs['parent']['trained_adapter_dir']
        files = inputs['parent']['trained_adapter_files']
        memory.transfer.verify_files(arguments.adapter_dir, files)
        memory.transfer.verify_files(arguments.model_dir, inputs['parent']['base_files'])
        require(source.read(Path(arguments.adapter_dir) / 'adapter_config.json').get('r') == 8, 'mounted_rank_eight_required')
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return result
        tokenizer = source.native.load_local_tokenizer(arguments.model_dir)
        engine = source.Engine(arguments, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        require(bool(parameters) and _state_hash(parameters) == PARENT_STATE, 'mounted_37ec_state_required')
        require(not any(parameter.requires_grad for unused, parameter in engine.model.named_parameters()),
                'breadth_actor_must_be_frozen')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=PARENT_STATE)

        def generate(messages, **metadata):
            nonlocal cap_hit
            check('call')
            if len(captures) >= CAPS[options.phase]:
                cap_hit = True
                raise ValueError('breadth_native_call_cap')
            capture = dict(call_index=len(captures), messages=deepcopy(messages), response=None, error=None, **metadata)
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
        require(not cap_hit, 'breadth_native_call_cap')
        require(not any(capture['error'] is not None for capture in captures), 'native_errors_retained')
        engine.verify_base()
        final_state = _state_hash(parameters)
        require(final_state == PARENT_STATE, 'readonly_breadth_state_drift')
        memory.transfer.verify_files(arguments.adapter_dir, files)
        memory.transfer.verify_files(arguments.model_dir, inputs['parent']['base_files'])
        same(helpers(), inputs['binding']['helpers'], 'runtime_breadth_helper_drift')
        source.write(output / 'STATES.json', dict(before=PARENT_STATE, after=final_state))
        result.update(status='COMPLETE', adapter_state_after=final_state, frozen_base_unchanged=True,
            model_calls=len(captures), role_calls=dict(Counter(capture['role'] for capture in captures)),
            source_ready=document['source_ready'], finished_unix=time.time())
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
                memory.transfer.verify_files(arguments.adapter_dir, files)
                memory.transfer.verify_files(arguments.model_dir, inputs['parent']['base_files'])
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
