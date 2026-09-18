"""Bounded fresh-DEV-world, matched-stimulus readonly interface transfer."""

import argparse
import os
from pathlib import Path
import time

from gpu import astra_event_two_hop as prior
from gpu import astra_event_two_hop_lesson as lesson_driver


hop = prior.task
source = prior.source
require = source.require
SCHEMA = 'DEV_EVENT_TWO_HOP_MATCHED_TRANSFER_V1'
TRAINED_STATE = '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
SOURCE_COMMIT = '0b495971f8ecb2353162757abbdb938effa4493b'
CONDITIONS = ('OWN_TEXT', 'UNAVAILABLE')
CLAIM = 'ONE_FRESH_DEV_GRAPH_MATCHED_STIMULUS_INTERFACE_TRANSFER_NOT_WHOLE_LIVES_OR_H1_H2'
LESSON_ROOT = '/tmp/astra_event_two_hop_lesson_20260914_attempt1'


def helpers():
    return {name: source.file_hash(path) for name, path in dict(
        hop=hop.__file__, driver=__file__, prior=prior.__file__,
        lesson_driver=lesson_driver.__file__, native_engine=source.__file__,
        micro=hop.micro.__file__, commands=hop.commands.__file__, native=source.native.__file__).items()}


def verify_files(directory, files):
    require(bool(files), 'nonempty_file_inventory_required')
    for name, digest in files.items():
        require(Path(name).name == name and source.file_hash(Path(directory) / name) == digest,
                'readonly_file_drift:' + name)


def base_files(directory):
    directory = Path(directory)
    config = source.read(directory / 'config.json')
    require(config.get('model_type') == 'qwen2' and config.get('hidden_size') == 3584
            and config.get('num_hidden_layers') == 28, 'original_qwen_7b_required')
    weights = sorted(directory.glob('*.safetensors'))
    require(bool(weights), 'local_base_weights_required')
    paths = [directory / 'config.json'] + weights
    paths += sorted(directory.glob('*.safetensors.index.json'))
    return {path.name: source.file_hash(path) for path in paths}


def load_inputs(options):
    original, parent = prior.load_parent(options)
    require(parent['parent_adapter_state_sha256'] == prior.PARENT_STATE
            and original['expected_base_sha256'] == parent['expected_base_sha256'], 'original_parent_required')
    root = Path(options.lesson_root)
    require((root / 'launch/source_commit.txt').read_text().strip() == SOURCE_COMMIT,
            'captured_lesson_source_commit_required')
    training = source.read(root / 'train/RESULT.json')
    recorded = training['binding']
    require(recorded['parent'] == parent, 'recorded_original_parent_required')
    for field, relative in (('lesson_helper_sha256', 'organism_v6/experienced_event_two_hop_lesson.py'),
                            ('actor_helper_sha256', 'organism_v6/experienced_event_two_hop.py')):
        require(source.file_hash(root / 'source' / relative) == recorded[field], 'captured_lesson_helper_drift')
    lessons = source.read(root / 'collect/RESULT.json')
    require(not (root / 'collect/FAILED.json').exists() and lessons.get('status') == 'COMPLETE'
            and lessons.get('binding') == recorded and lessons.get('fits') == 0
            and lessons.get('loaded_adapter_state_sha256') == prior.PARENT_STATE
            and lessons.get('adapter_state_after') == prior.PARENT_STATE
            and lessons.get('frozen_base_unchanged') is True, 'recorded_lessons_required')
    trained, training_sha = lesson_driver.read_training(root / 'train', recorded,
        source.file_hash(root / 'collect/RESULT.json'))
    after = source.read(root / 'after/RESULT.json')
    require(not (root / 'after/FAILED.json').exists() and after.get('schema') == lesson_driver.SCHEMA
            and after.get('phase') == 'after' and after.get('status') == 'COMPLETE'
            and after.get('binding') == recorded and after.get('fits') == 0
            and after.get('parent_present') is False and trained.get('parent_present') is False
            and after.get('training_result_sha256') == training_sha
            and after.get('lessons_result_sha256') == trained['lessons_result_sha256']
            and trained.get('adapter_state_after') == TRAINED_STATE
            and after.get('loaded_adapter_state_sha256') == TRAINED_STATE
            and after.get('adapter_state_after') == TRAINED_STATE
            and after.get('frozen_base_unchanged') is True, 'completed_parent_free_trajectory_required')
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(trained['adapter_files'])
            and {'TRAINING_ROWS.json', 'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl'} <= set(trained['training_files']),
            'complete_training_inventory_required')
    for directory, files in ((parent['adapter_dir'], parent['parent_adapter_files']),
                             (root / 'train/adapter', trained['adapter_files'])):
        verify_files(directory, files)
        require(source.read(Path(directory) / 'adapter_config.json').get('r') == 8, 'rank_eight_required')
    previous = prior.previous.load_parent(options)
    current, unused_rows, collection_sha = prior.previous.read_collection(Path(options.cycle_root) / 'collect', previous)
    facts = previous['old_bank'] + current['bank']
    require(len(previous['old_bank']) == 12 and len(current['bank']) == 4
            and len({fact['event'] for fact in facts}) == 16, 'actual_sixteen_old_facts_required')
    world = hop.build_world(master=hop.TRANSFER_MASTER)
    known = {fact[key] for fact in facts + hop.build_world()['edges']
             for key in ('event', 'node', 'port', 'outcome', 'receipt')}
    proposed = {value for edge in world['edges'] for value in edge.values()}
    require(not known.intersection(proposed), 'fresh_namespace_collision')
    binding = dict(parent=parent, training_result_sha256=training_sha,
        after_result_sha256=source.file_hash(root / 'after/RESULT.json'),
        lessons_result_sha256=trained['lessons_result_sha256'], recorded_training_binding=recorded,
        source_commit=SOURCE_COMMIT, trained_state=TRAINED_STATE, original_state=prior.PARENT_STATE,
        trained_adapter_dir=str(root / 'train/adapter'), trained_adapter_files=trained['adapter_files'],
        original_arguments=original, base_files=base_files(original['model_dir']),
        helper_hashes=helpers(), world_sha256=hop.document_sha256(world),
        old_facts_sha256=hop.document_sha256(facts), old_collection_sha256=collection_sha,
        original_world_sha256=hop.document_sha256(hop.build_world()))
    return original, binding, world


def verify_captures(directory, document):
    captures = document['captures']
    require(len(captures) == len(list(Path(directory).glob('CALL_*.json'))) == 8, 'native_call_inventory')
    for index, capture in enumerate(captures):
        saved = source.read(Path(directory) / ('CALL_%03d.json' % index))
        require(saved['call_index'] == index and saved['role'] == 'collection'
                and saved['messages'] == capture['messages'] and saved['response'] == capture['response']
                and saved['error'] is None and capture['error'] is None, 'native_capture_drift')


def read_collection(directory, binding, world):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_transfer_collection')
    result = source.read(directory / 'RESULT.json')
    require(result.get('schema') == SCHEMA and result.get('status') == 'COMPLETE'
            and result.get('phase') == 'collect' and result.get('arm') == 'TRAINED'
            and result.get('binding') == binding and result.get('fits') == 0
            and result.get('trainingAllowed') is False and result.get('parent_present') is False
            and result.get('loaded_adapter_state_sha256') == TRAINED_STATE
            and result.get('adapter_state_after') == TRAINED_STATE
            and result.get('frozen_base_unchanged') is True and result.get('model_calls') == 8,
            'complete_trained_transfer_collection_required')
    require(source.file_hash(directory / 'COLLECTION.json') == result['collection_sha256'], 'collection_file_drift')
    document = hop.replay_collection(source.read(directory / 'COLLECTION.json'))
    require(document['world'] == world == source.read(directory / 'WORLD.json')
            and document['ready'] and document['accepted_events'] == 4 and document['model_calls'] == 8,
            'four_actual_fresh_exposures_required')
    verify_captures(directory, document)
    return document, source.file_hash(directory / 'RESULT.json')


def evaluate(world, collection, generate, output):
    store = hop.exact_text_store(collection)
    panels = {}
    for condition in CONDITIONS:
        records = []
        for index, public_task in enumerate(hop.build_tasks(world)):
            def actor(messages):
                return generate(messages, role='actor', condition=condition, task_index=index)

            def memory(address):
                return store[address] if condition == 'OWN_TEXT' else 'MEMORY UNAVAILABLE'

            episode = hop.run_episode(world, public_task, actor, memory, protocol='turnbound')
            source.write(output / ('EPISODE_%s_%02d.json' % (condition, index)), episode)
            score = hop.score_episode(world, public_task, episode)
            records.append(dict(task_index=index, task=public_task, goal=public_task['goal'],
                routes=episode['routes'], reads=[trace for trace in episode['traces'] if trace['kind'] == 'memory'],
                terminal=episode['terminal_reason'], score=score))
            source.write(output / ('SCORE_%s_%02d.json' % (condition, index)), records[-1])
        panels[condition] = dict(correct=sum(record['score']['correct'] for record in records),
                                 denominator=4, tasks=records)
    source.write(output / 'SUMMARY.json', dict(panels=panels, trainingAllowed=False, claim=CLAIM))
    return panels


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--lesson-root', default=LESSON_ROOT)
    parser.add_argument('--phase', choices=('prepare', 'collect', 'readout'), required=True)
    parser.add_argument('--arm', choices=('TRAINED', 'ORIGINAL'))
    parser.add_argument('--collection')
    options = parser.parse_args(argv)
    require(bool(options.collection) == (options.phase == 'readout'), 'collection_only_for_readout')
    require(options.arm in ('TRAINED', 'ORIGINAL') if options.phase == 'readout'
            else options.arm in (None, 'TRAINED'), 'trained_collection_only')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or bool(options.gpu_uuid)
            and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    arm = options.arm or 'TRAINED'
    cap = dict(prepare=0, collect=8, readout=48)[options.phase]
    state = TRAINED_STATE if arm == 'TRAINED' else prior.PARENT_STATE
    result = dict(schema=SCHEMA, phase=options.phase, arm=arm, arguments=vars(options),
        started_unix=started, fits=0, updates=0, trainingAllowed=False, automatic_training=False,
        parent_present=False, claim=CLAIM, model_calls=0, max_native_calls=cap,
        protocol='turnbound', conditions=list(CONDITIONS), max_context=2048, max_new_tokens=160,
        max_actor_calls_per_task=6, max_reads_per_task=4, max_actions_per_task=2,
        stimulus='SAME_CAPTURED_TRAINED_CHILD_TEXT_THIRDPARTY_CONTEXT_FOR_ORIGINAL')
    source.write(output / 'REQUEST.json', result)
    captures = []
    engine = None

    def check(label):
        require(time.time() < started + 1800, 'transfer_deadline:' + label)

    try:
        original, binding, world = load_inputs(options)
        result['binding'] = binding
        source.write(output / 'INPUTS.json', binding)
        source.write(output / 'WORLD.json', world)
        source.write(output / 'TASKS.json', hop.build_tasks(world))
        collection = None
        if options.phase == 'readout':
            collection, result['collection_result_sha256'] = read_collection(options.collection, binding, world)
            source.write(output / 'COLLECTION_SOURCE.json', collection)
            result['shared_text_sha256'] = hop.document_sha256(hop.exact_text_store(collection))
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return result
        arguments = argparse.Namespace(**original)
        arguments.phase, arguments.device, arguments.gpu_uuid = 'readout', 'cuda:0', options.gpu_uuid
        arguments.adapter_dir = binding['trained_adapter_dir'] if arm == 'TRAINED' else binding['parent']['adapter_dir']
        files = binding['trained_adapter_files'] if arm == 'TRAINED' else binding['parent']['parent_adapter_files']
        tokenizer = source.native.load_local_tokenizer(arguments.model_dir)
        engine = source.Engine(arguments, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        require(bool(parameters) and _state_hash(parameters) == state, 'mounted_transfer_state_required')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=state)

        def generate(messages, *, role='collection', condition=None, task_index=None):
            check('call')
            require(len(captures) < cap, 'transfer_native_call_cap')
            capture = dict(call_index=len(captures), role=role, condition=condition, task_index=task_index,
                           messages=messages, response=None, error=None)
            captures.append(capture)
            try:
                capture['response'] = engine.generate(messages, max_new_tokens=160)
                return capture['response']
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                source.write(output / ('CALL_%03d.json' % capture['call_index']), capture)

        if options.phase == 'collect':
            collection = hop.collect_world(world, generate)
            source.write(output / 'COLLECTION.json', collection)
            result.update(collection_sha256=source.file_hash(output / 'COLLECTION.json'),
                          accepted_events=collection['accepted_events'])
            require(collection['ready'] and collection['accepted_events'] == 4
                    and collection['model_calls'] == len(captures) == 8, 'incomplete_transfer_collection')
            verify_captures(output, hop.replay_collection(collection))
        else:
            result['panels'] = evaluate(world, collection, generate, output)
        require(not any(capture['error'] is not None for capture in captures), 'native_errors_retained')
        engine.verify_base()
        result['adapter_state_after'] = _state_hash(parameters)
        source.write(output / 'STATES.json', dict(before=state, after=result['adapter_state_after']))
        require(result['adapter_state_after'] == state, 'readonly_adapter_state_drift')
        verify_files(arguments.adapter_dir, files)
        verify_files(arguments.model_dir, binding['base_files'])
        require(helpers() == binding['helper_hashes'], 'runtime_helper_drift')
        result.update(status='COMPLETE', model_calls=len(captures), frozen_base_unchanged=True, finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        if engine is not None:
            try:
                result['adapter_state_after'] = _state_hash({name: parameter for name, parameter in
                    engine.model.named_parameters() if '.lora_A.' in name or '.lora_B.' in name})
                engine.verify_base()
                result['frozen_base_unchanged'] = True
                verify_files(arguments.adapter_dir, files)
                verify_files(arguments.model_dir, binding['base_files'])
            except BaseException as verification_error:
                result['failure_verification_error'] = repr(verification_error)
            if not (output / 'STATES.json').exists():
                source.write(output / 'STATES.json', dict(before=result.get('loaded_adapter_state_sha256'),
                    expected=state, after=result.get('adapter_state_after')))
        result.update(status='FAILED', error=repr(error), model_calls=len(captures), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
