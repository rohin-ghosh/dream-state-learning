"""Readonly contextual continuation on newly experienced, connected EVENT edges."""

import argparse
from collections import Counter
from contextlib import nullcontext
import os
from pathlib import Path
import time

from gpu import astra_fresh_reader_cycle as previous
from organism_v6 import experienced_event_two_hop as task


source = previous.source
require = source.require
SCHEMA = 'DEV_EVENT_CONTEXT_TWO_HOP_RUN_V1'
PARENT_STATE = '207ad43ef65f1f6ba7c50d37f5d5dfa8c2253d1cb301e585d7b6b7a78bb93990'
CONDITIONS = ('ON_PARAMETRIC', 'ON_OWN_TEXT', 'ON_UNAVAILABLE', 'OFF_OWN_TEXT')
CLAIM = 'ONE_DEV_CONNECTED_WORLD_READONLY_CONTROLLER_DIAGNOSTIC_NOT_PARAMETRIC_ACQUISITION_OR_H1_H2'


def load_parent(options):
    inputs = previous.load_parent(options)
    cycle = Path(options.cycle_root)
    collection, unused_rows, collection_sha = previous.read_collection(cycle / 'collect', inputs)
    unused_selected, before_sha = previous.read_before(cycle / 'before', inputs, collection, collection_sha)
    trained, train_sha = previous.read_training(cycle / 'SELECTED/train', inputs, 'SELECTED', collection_sha, before_sha)
    after, after_sha = previous.read_stage(cycle / 'SELECTED/after', inputs, 'after')
    require(trained['adapter_state_after'] == PARENT_STATE
            and after.get('loaded_adapter_state_sha256') == PARENT_STATE
            and after.get('training_result_sha256') == train_sha
            and after.get('fits') == 0 and after.get('arm') == 'SELECTED', 'complete_selected_A3_parent_required')
    known = {fact[key] for fact in inputs['old_bank'] + collection['bank']
             for key in ('event', 'node', 'port', 'outcome', 'receipt')}
    proposed = {value for edge in task.build_world()['edges'] for value in edge.values()}
    require(not known.intersection(proposed), 'connected_world_must_not_relabel_prior_experiences')
    binding = dict(parent_training_result_sha256=train_sha, parent_after_result_sha256=after_sha,
        parent_adapter_state_sha256=PARENT_STATE, parent_adapter_files=trained['adapter_files'],
        parent_source=inputs['fresh_source'], collection_result_sha256=collection_sha,
        adapter_dir=str(cycle / 'SELECTED/train/adapter'),
        expected_base_sha256=inputs['after']['arguments']['expected_base_sha256'])
    return inputs['after']['arguments'], binding


def read_collection(directory, parent):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_connected_collection_forbidden')
    result = source.read(directory / 'RESULT.json')
    require(result.get('schema') == SCHEMA and result.get('phase') == 'collect'
            and result.get('status') == 'COMPLETE' and result.get('source') == parent
            and result.get('fits') == 0 and result.get('parent_present') is False
            and result.get('loaded_adapter_state_sha256') == PARENT_STATE
            and result.get('adapter_state_after') == PARENT_STATE
            and result.get('frozen_base_unchanged') is True
            and result.get('helper_sha256') == source.file_hash(task.__file__), 'same_parent_connected_collection_required')
    document = source.read(directory / 'COLLECTION.json')
    require(source.file_hash(directory / 'COLLECTION.json') == result.get('collection_sha256'), 'connected_collection_file_drift')
    verified = task.replay_collection(document)
    require(verified['ready'] and verified['model_calls'] == result['model_calls'] == 8,
            'four_complete_connected_exposures_required')
    require(source.read(directory / 'WORLD.json') == verified['world'], 'connected_world_file_drift')
    require(len(list(directory.glob('CALL_*.json'))) == 8, 'connected_collection_call_inventory')
    for index, capture in enumerate(verified['captures']):
        saved = source.read(directory / ('CALL_%03d.json' % index))
        require(saved['messages'] == capture['messages'] and saved['response'] == capture['response']
                and saved['error'] is None and capture['error'] is None, 'connected_collection_native_call_drift')
    return verified, source.file_hash(directory / 'RESULT.json')


def memory_messages(address):
    return [dict(role='system', content=source.world.MEMORY_SYSTEM),
            dict(role='user', content=source.world.WRAPPERS[0].replace('{REQUEST}', 'READ EVENT ' + address))]


def evaluate(world, collection, generate, output):
    store = task.exact_text_store(collection)
    tasks = task.build_tasks(world)
    panels = {}
    for condition in CONDITIONS:
        records = []
        for index, public_task in enumerate(tasks):
            def actor(messages):
                return generate(messages, role='actor', condition=condition, task_index=index,
                                adapter_off=condition == 'OFF_OWN_TEXT')

            def memory(address):
                if condition == 'ON_PARAMETRIC':
                    return generate(memory_messages(address), role='memory', condition=condition,
                                    task_index=index, adapter_off=False)
                if condition == 'ON_UNAVAILABLE':
                    return 'MEMORY UNAVAILABLE'
                require(address in store, 'own_text_address_required')
                return store[address]

            episode = task.run_episode(world, public_task, actor, memory)
            score = task.score_episode(world, public_task, episode)
            entry = dict(condition=condition, task_index=index, task=public_task, episode=episode, score=score,
                memory_origin='PARAMETRIC_UNWRITTEN' if condition == 'ON_PARAMETRIC' else
                    'DECLARED_UNAVAILABLE_SERVICE' if condition == 'ON_UNAVAILABLE' else 'ACTUAL_OWN_EVENT_TEXT')
            source.write(output / ('%s_EPISODE_%02d.json' % (condition, index)), entry)
            records.append(entry)
        panels[condition] = dict(denominator=4, correct=sum(entry['score']['strict_success'] for entry in records),
            reached_goal=sum(entry['score']['reached_goal'] for entry in records),
            actor_calls=sum(entry['score']['actor_calls'] for entry in records),
            memory_calls=sum(entry['score']['memory_calls'] for entry in records),
            terminal_reasons=dict(Counter(entry['score']['terminal_reason'] for entry in records)), episodes=records)
    source.write(output / 'PANELS.json', panels)
    return panels


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'gpu-uuid', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', choices=('prepare', 'collect', 'readout'), required=True)
    parser.add_argument('--collection')
    options = parser.parse_args(argv)
    require(bool(options.collection) == (options.phase == 'readout'), 'collection_only_for_readout')
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    cap = 8 if options.phase == 'collect' else 112
    result = dict(schema=SCHEMA, phase=options.phase, arguments=vars(options).copy(), started_unix=started,
        fits=0, model_calls=0, parent_present=False, automatic_training=False, claim=CLAIM,
        helper_sha256=source.file_hash(task.__file__), entry_sha256=source.file_hash(__file__),
        native_engine_sha256=source.file_hash(source.__file__), conditions=list(CONDITIONS),
        max_native_calls=cap, max_context=2048, max_new_tokens=160)
    source.write(output / 'REQUEST.json', result)
    captures = []

    def check(label):
        require(time.time() < started + (3600 if options.phase == 'readout' else 1800), 'two_hop_deadline:' + label)

    try:
        original_arguments, parent = load_parent(options)
        world = task.build_world()
        result.update(source=parent, world_sha256=task.document_sha256(world))
        source.write(output / 'INPUTS.json', parent)
        source.write(output / 'WORLD.json', world)
        source.write(output / 'TASKS.json', task.build_tasks(world))
        collection = None
        if options.phase == 'readout':
            collection, result['collection_result_sha256'] = read_collection(options.collection, parent)
            source.write(output / 'COLLECTION_SOURCE.json', collection)
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return result
        arguments = argparse.Namespace(**original_arguments)
        arguments.phase, arguments.device = 'readout', 'cuda:0'
        arguments.gpu_uuid, arguments.adapter_dir = options.gpu_uuid, parent['adapter_dir']
        tokenizer = source.native.load_local_tokenizer(arguments.model_dir)
        engine = source.Engine(arguments, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        state = _state_hash(parameters)
        require(bool(parameters) and state == PARENT_STATE, 'mounted_selected_parent_required')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=state)

        def generate(messages, *, role='collection', condition=None, task_index=None, adapter_off=False):
            check('call')
            require(len(captures) < cap, 'two_hop_native_call_cap')
            capture = dict(call_index=len(captures), role=role, condition=condition, task_index=task_index,
                           adapter_off=adapter_off, messages=messages, response=None, error=None)
            captures.append(capture)
            try:
                with engine.model.disable_adapter() if adapter_off else nullcontext():
                    capture['response'] = engine.generate(messages, max_new_tokens=160)
                return capture['response']
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                source.write(output / ('CALL_%03d.json' % capture['call_index']), capture)

        if options.phase == 'collect':
            collection = task.collect_world(world, generate)
            source.write(output / 'COLLECTION.json', collection)
            result.update(accepted_events=collection['accepted_events'],
                          collection_sha256=source.file_hash(output / 'COLLECTION.json'))
            require(collection['ready'] and collection['model_calls'] == len(captures) == 8, 'incomplete_connected_collection')
        else:
            result['panels'] = evaluate(world, collection, generate, output)
            counts = Counter(capture['role'] for capture in captures)
            require(counts['actor'] <= 96 and counts['memory'] <= 16, 'two_hop_role_budget')
            result['native_calls_by_role'] = dict(counts)
        require(not any(capture['error'] is not None for capture in captures), 'two_hop_native_errors_retained')
        engine.verify_base()
        result['adapter_state_after'] = _state_hash(parameters)
        require(result['adapter_state_after'] == state, 'readonly_two_hop_changed_adapter')
        require(all(source.file_hash(Path(parent['adapter_dir']) / name) == digest
                    for name, digest in parent['parent_adapter_files'].items()), 'readonly_two_hop_adapter_files_changed')
        check('final')
        result.update(status='COMPLETE', frozen_base_unchanged=True, model_calls=len(captures), finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), model_calls=len(captures), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
