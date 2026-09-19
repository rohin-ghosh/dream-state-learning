"""One bounded DEV parametric memory write and actual action-loop readout.

The trajectory parent and its readouts are reused baselines, not independent
learners. No clean ancestry, matched whole-life, H1/H2 or token-equality claim.
UNAVAILABLE denotes an external declared service, not a parametric MISS.
"""

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import os
from pathlib import Path
import time

from gpu import astra_event_two_hop_transfer as transfer
from organism_v6 import experienced_event_two_hop_memory as memory
from organism_v6 import experienced_event_cue_sleep as cues
from organism_v6 import experienced_event_reader_audit_lesson as audit


source = transfer.source
hop = transfer.hop
lesson = transfer.lesson_driver
require = source.require
SCHEMA = 'DEV_EVENT_TWO_HOP_MEMORY_CLOSURE_V1'
CLAIM = 'ONE_DEV_PARAMETRIC_WRITE_AND_ACTION_LOOP_NOT_CLEAN_ANCESTRY_MATCHED_LIVES_OR_H1_H2'
TRANSFER_ROOT = '/tmp/astra_event_two_hop_transfer_20260914_attempt2'
PARENT_STATE = transfer.TRAINED_STATE
UPDATES = 100
GROUPS = ('memory_rows', 'cue_rows', 'audit_rows', 'trajectory_rows', 'new_rows')
GROUP_SIZES = (128, 20, 62, 12, 32)
CAPS = dict(prepare=0, before=48, train=0, after=168)
CONDITIONS = ('PARAMETRIC', 'OWN_TEXT', 'UNAVAILABLE')


def same(actual, expected, reason):
    require(hop.document_sha256(actual) == hop.document_sha256(expected), reason)


def helpers():
    return {name: source.file_hash(path) for name, path in dict(
        driver=__file__, guard=Path(__file__).with_name('astra_event_two_hop_memory_guard.sh'),
        memory=memory.__file__, transfer=transfer.__file__, hop=hop.__file__,
        lesson=lesson.__file__, trajectory=lesson.lesson.__file__, cues=cues.__file__,
        audit=audit.__file__, engine=source.__file__, native=source.native.__file__).items()}


def memory_messages(address, view=0):
    return [dict(role='system', content=source.world.MEMORY_SYSTEM),
            dict(role='user', content=source.world.WRAPPERS[view].format(REQUEST='READ EVENT ' + address))]


def read_calls(directory, count, cap):
    require(type(count) is int and 0 <= count <= cap, 'bounded_native_call_inventory')
    directory = Path(directory)
    names = {f'CALL_{index:03d}.json' for index in range(count)}
    require({path.name for path in directory.glob('CALL_*.json')} == names, 'exact_native_call_inventory')
    calls = [source.read(directory / f'CALL_{index:03d}.json') for index in range(count)]
    require(all(call['call_index'] == index and call['error'] is None for index, call in enumerate(calls)),
            'complete_error_free_native_calls_required')
    return calls


def verify_episode_calls(episode, world, task, store, condition, calls, task_index, *, graph=None):
    verified = hop.replay_episode(world, task, episode)
    require(verified.get('protocol') == 'turnbound', 'literal_turnbound_episode_required')
    for trace in verified['traces']:
        if trace['kind'] == 'transition':
            continue
        if trace['kind'] == 'memory' and condition != 'PARAMETRIC':
            expected = 'MEMORY UNAVAILABLE' if condition == 'UNAVAILABLE' else store[trace['address']]
            require(trace['error'] is None and trace['response'] == expected, 'literal_memory_service_required')
            continue
        call = next(calls, None)
        require(call is not None and call['role'] == ('actor' if trace['kind'] == 'actor' else 'memory')
                and call['condition'] == condition and call['task_index'] == task_index
                and (graph is None or call['graph'] == graph)
                and not call.get('adapter_off', False), 'episode_native_call_role_drift')
        expected_messages = trace['messages'] if trace['kind'] == 'actor' else memory_messages(trace['address'])
        same({key: call[key] for key in ('messages', 'response', 'error')},
             dict(messages=expected_messages, response=trace['response'], error=trace['error']),
             'episode_native_output_drift')
    return hop.score_episode(world, task, verified)


def read_transfer_readout(directory, binding, world, collection, collection_sha, arm):
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    state = PARENT_STATE if arm == 'TRAINED' else transfer.prior.PARENT_STATE
    store = hop.exact_text_store(collection)
    require(not (directory / 'FAILED.json').exists() and result.get('schema') == transfer.SCHEMA
        and result.get('phase') == 'readout' and result.get('status') == 'COMPLETE'
        and result.get('arm') == arm and result.get('binding') == binding
        and result.get('fits') == result.get('updates') == 0 and result.get('trainingAllowed') is False
        and result.get('parent_present') is False and result.get('protocol') == 'turnbound'
        and result.get('conditions') == list(transfer.CONDITIONS)
        and result.get('collection_result_sha256') == collection_sha
        and result.get('shared_text_sha256') == hop.document_sha256(store)
        and result.get('loaded_adapter_state_sha256') == result.get('adapter_state_after') == state
        and result.get('frozen_base_unchanged') is True, 'complete_matched_transfer_readout_required')
    same(source.read(directory / 'WORLD.json'), world, 'transfer_readout_world_drift')
    same(source.read(directory / 'TASKS.json'), hop.build_tasks(world), 'transfer_readout_task_drift')
    same(source.read(directory / 'COLLECTION_SOURCE.json'), collection, 'transfer_readout_source_drift')
    calls = iter(read_calls(directory, result['model_calls'], 48))
    panels = {}
    for condition in transfer.CONDITIONS:
        records = []
        for index, task in enumerate(hop.build_tasks(world)):
            episode = source.read(directory / f'EPISODE_{condition}_{index:02d}.json')
            score = verify_episode_calls(episode, world, task, store, condition, calls, index)
            record = dict(task_index=index, task=task, goal=task['goal'], routes=episode['routes'],
                reads=[trace for trace in episode['traces'] if trace['kind'] == 'memory'],
                terminal=episode['terminal_reason'], score=score)
            same(record, source.read(directory / f'SCORE_{condition}_{index:02d}.json'), 'transfer_score_drift')
            records.append(record)
        panels[condition] = dict(correct=sum(record['score']['correct'] for record in records), denominator=4, tasks=records)
    require(next(calls, None) is None, 'unknown_transfer_readout_call')
    same(panels, result['panels'], 'transfer_panel_drift')
    return dict(result_sha256=source.file_hash(directory / 'RESULT.json'), state=state,
                world_sha256=hop.document_sha256(world), shared_text_sha256=hop.document_sha256(store),
                protocol='turnbound', panels=panels)


def panel(entries):
    return dict(denominator=4, correct=sum(entry['score']['strict_success'] for entry in entries),
        reached_goal=sum(entry['score']['reached_goal'] for entry in entries),
        actor_calls=sum(entry['score']['actor_calls'] for entry in entries),
        memory_calls=sum(entry['score']['memory_calls'] for entry in entries),
        terminal_reasons=dict(Counter(entry['score']['terminal_reason'] for entry in entries)), episodes=entries)


def read_original_baseline(root, transfer_binding, collection):
    directory = Path(root) / 'after'
    result = source.read(directory / 'RESULT.json')
    require(not (directory / 'FAILED.json').exists() and result.get('schema') == lesson.SCHEMA
        and result.get('status') == 'COMPLETE' and result.get('phase') == 'after'
        and result.get('fits') == 0 and result.get('parent_present') is False
        and result.get('binding') == transfer_binding['recorded_training_binding']
        and result.get('training_result_sha256') == transfer_binding['training_result_sha256']
        and result.get('loaded_adapter_state_sha256') == result.get('adapter_state_after') == PARENT_STATE
        and result.get('frozen_base_unchanged') is True, 'original_graph_same_parent_baseline_required')
    require(source.file_hash(directory / 'RESULT.json') == transfer_binding['after_result_sha256'],
            'original_after_result_drift')
    all_calls = read_calls(directory, result['model_calls'], 160)
    calls = iter(call for call in all_calls if call.get('condition') == 'ON_OWN_TEXT')
    world, store = collection['world'], hop.exact_text_store(collection)
    require(world == hop.build_world(), 'original_taught_world_required')
    entries = []
    for index, task in enumerate(hop.build_tasks(world)):
        entry = source.read(directory / f'ON_OWN_TEXT_EPISODE_{index:02d}.json')
        score = verify_episode_calls(entry['episode'], world, task, store, 'ON_OWN_TEXT', calls, index)
        expected = dict(condition='ON_OWN_TEXT', task_index=index, task=task, episode=entry['episode'],
                        score=score, memory_origin='ACTUAL_OWN_EVENT_TEXT')
        same(entry, expected, 'original_baseline_task_or_score_drift')
        entries.append(entry)
    require(next(calls, None) is None, 'unknown_original_own_text_call')
    same(panel(entries), result['panels']['ON_OWN_TEXT'], 'original_baseline_panel_drift')
    return dict(result_sha256=transfer_binding['after_result_sha256'], state=PARENT_STATE,
        world_sha256=hop.document_sha256(world), shared_text_sha256=hop.document_sha256(store),
        protocol='turnbound', panel=panel(entries), interpretation='REUSED_PARENT_NOT_INDEPENDENT_LEARNER')


def load_inputs(options):
    arguments, transfer_binding, world = transfer.load_inputs(options)
    collection, collection_sha = transfer.read_collection(Path(options.transfer_root) / 'collect', transfer_binding, world)
    baselines = {arm: read_transfer_readout(Path(options.transfer_root) / arm, transfer_binding, world,
                 collection, collection_sha, arm) for arm in ('TRAINED', 'ORIGINAL')}
    root = Path(options.lesson_root)
    recorded = transfer_binding['recorded_training_binding']
    trajectory_rows, lessons_sha = lesson.read_lessons(root / 'collect', recorded)
    trained, training_sha = lesson.read_training(root / 'train', recorded, lessons_sha)
    require(training_sha == transfer_binding['training_result_sha256'] and trained['adapter_state_after'] == PARENT_STATE,
            'same_completed_parent_training_required')
    material = source.read(root / 'train/TRAINING_ROWS.json')
    require(set(material) == set(GROUPS[:-1]) and tuple(len(material[key]) for key in GROUPS[:-1]) == GROUP_SIZES[:-1],
            'exact_archived_128_20_62_12_material_required')
    for key in ('memory_rows', 'cue_rows', 'audit_rows'):
        require(source.native._digest(material[key]) == recorded[key + '_sha256'], 'archived_material_hash_drift:' + key)
    same(material['trajectory_rows'], trajectory_rows, 'archived_trajectory_rows_drift')
    previous = transfer.prior.previous.load_parent(options)
    fresh, fresh_rows, unused_digest = transfer.prior.previous.read_collection(Path(options.cycle_root) / 'collect', previous)
    same(material['memory_rows'], previous['memory_rows'] + fresh_rows, 'actual_old_memory_source_drift')
    same(material['cue_rows'], previous['cue_rows'], 'actual_cue_source_drift')
    same(material['audit_rows'], previous['lesson_rows'], 'actual_audit_source_drift')
    old_bank, old_episodes = previous['old_bank'] + fresh['bank'], previous['old_episodes'] + fresh['episodes']
    require(len(old_bank) == len(old_episodes) == 16, 'sixteen_old_recall_sources_required')
    require(hop.document_sha256(old_bank) == transfer_binding['old_facts_sha256'], 'old_fact_binding_drift')
    held = previous['held']
    same(held, audit.build_cases(held['events'], audit.HELD), 'original_held_cases_drift')
    require(held['expected_calls'] == 16, 'sixteen_original_held_calls_required')
    original_collection = hop.replay_collection(source.read(root / 'collect/LESSONS.json')['collection'])
    baselines['TAUGHT_GRAPH'] = read_original_baseline(root, transfer_binding, original_collection)
    material['new_rows'] = memory.compile_rows(collection)
    require(tuple(len(material[key]) for key in GROUPS) == GROUP_SIZES, 'exact_254_row_layout_required')
    binding = dict(transfer=transfer_binding, transfer_collection_result_sha256=collection_sha,
        shared_text_sha256=hop.document_sha256(hop.exact_text_store(collection)),
        material_sha256=hop.document_sha256(material), archived_rows_sha256=source.file_hash(root / 'train/TRAINING_ROWS.json'),
        lessons_result_sha256=lessons_sha, parent_training_result_sha256=training_sha,
        held_cases_sha256=held['cases_sha256'], baselines=baselines, helper_hashes=helpers())
    return dict(arguments=arguments, binding=binding, world=world, collection=collection, material=material,
        original_collection=original_collection, old_bank=old_bank, old_episodes=old_episodes, held=held)


def training_indexes(update):
    require(type(update) is int and 1 <= update <= UPDATES, 'fixed_100_updates_required')
    offset = update - 1
    return (offset % 128, 128 + offset % 94, 222 + (2 * offset) % 32, 222 + (2 * offset + 1) % 32)


def recipe():
    return dict(updates=UPDATES, seed=0, optimizer='FRESH_ADAMW', learning_rate=3e-5,
        optimizer_kwargs=dict(source.native.OPTIMIZER), rank=8, batch_size=4, group_sizes=list(GROUP_SIZES),
        group_order=list(GROUPS), encoded_rows=254, loss='MEAN_CAUSAL_CE', actual_token_equality_claim=False,
        schedule=[list(training_indexes(update)) for update in range(1, UPDATES + 1)],
        presentations=dict(old_memory=100, cue=26, audit=62, trajectory=12, new_memory=200),
        new_fact_presentations=[50] * 4, claim=CLAIM)


def encode_material(inputs, tokenizer):
    from gpu import astra_reader_audit_lesson_train as masks

    material = inputs['material']
    require(tuple(len(material[key]) for key in GROUPS) == GROUP_SIZES, 'exact_254_row_layout_required')
    memory.replay_rows(material['new_rows'], inputs['collection'])
    encoded = tuple(source.encode_row(row['messages'], tokenizer) for row in material['memory_rows'])
    encoded += tuple(cues.encode_cue_rows(material['cue_rows'], tokenizer))
    encoded += tuple(audit.encode_rows(material['audit_rows'], tokenizer))
    encoded += tuple(lesson.lesson.encode_rows(material['trajectory_rows'], tokenizer))
    encoded += tuple(source.encode_rows(material['new_rows'], tokenizer))
    require(len(encoded) == 254, 'exact_254_encoded_rows_required')
    masks.validate_masks(encoded, tokenizer.eos_token_id)
    return encoded


def train(engine, inputs, output):
    from gpu import astra_experienced_event_cue_sleep as development
    from organism_v6.pcfl_vertical_train import _state_hash

    require(inputs.get('verified_before_sha256'), 'verified_before_required_before_gradient')
    encoded = encode_material(inputs, engine.tokenizer)
    require(engine.tokenizer.pad_token_id == 151643, 'fixed_native_pad_required')
    source.write(output / 'TRAINING_ROWS.json', inputs['material'])
    source.write(output / 'MASKS.json', [asdict(row) for row in encoded])
    source.write(output / 'RECIPE.json', recipe())
    parameters = development.enable_existing_adapter(engine)
    require(_state_hash(parameters) == PARENT_STATE, 'initial_memory_parent_must_match')
    torch = engine.torch
    torch.manual_seed(0)
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, **source.native.OPTIMIZER)
    engine.model.train()
    tokens, doses = 0, [0] * 254
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, UPDATES + 1):
            engine.check('memory_update')
            indexes = training_indexes(update)
            batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
            active = sum(label != -100 for labels in batch['labels'] for label in labels[1:])
            require(active > 0, 'positive_memory_labels_required')
            tensors = {name: torch.tensor(value, dtype=torch.long, device=engine.device) for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                loss = engine.model(**tensors, use_cache=False).loss
            require(bool(torch.isfinite(loss)) and loss.requires_grad, 'invalid_memory_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'invalid_memory_gradient')
            optimizer.step()
            require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()), 'nonfinite_memory_adapter')
            tokens += active
            for index in indexes:
                doses[index] += 1
            stream.write(source.json.dumps(dict(update=update, row_indexes=indexes,
                active_label_count=active, loss=loss.item()), allow_nan=False) + '\n')
            stream.flush()
    state = _state_hash(parameters)
    require(state != PARENT_STATE, 'memory_write_must_change_adapter')
    engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    adapter_files = {path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()}
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(adapter_files), 'saved_memory_adapter_required')
    require(source.read(output / 'adapter/adapter_config.json').get('r') == 8, 'saved_rank_eight_required')
    return dict(fits=1, updates=UPDATES, adapter_state_after=state, adapter_files=adapter_files,
        actual_supervised_tokens=tokens, row_presentations=doses,
        training_files={name: source.file_hash(output / name) for name in
                        ('TRAINING_ROWS.json', 'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl')})


def evaluate_graph(world, collection, generate, output, conditions, graph):
    store = hop.exact_text_store(collection)
    panels = {}
    for condition in conditions:
        entries = []
        for index, task in enumerate(hop.build_tasks(world)):
            def actor(messages):
                return generate(messages, role='actor', condition=condition, task_index=index, graph=graph)

            def reader(address):
                if condition == 'PARAMETRIC':
                    return generate(memory_messages(address), role='memory', condition=condition, task_index=index, graph=graph)
                return store[address] if condition == 'OWN_TEXT' else 'MEMORY UNAVAILABLE'

            episode = hop.run_episode(world, task, actor, reader, protocol='turnbound')
            entry = dict(graph=graph, condition=condition, task_index=index, task=task, episode=episode,
                score=hop.score_episode(world, task, episode), memory_origin=(
                    'ACTUAL_PARAMETRIC_RESPONSE_NO_FALLBACK' if condition == 'PARAMETRIC' else
                    'ACTUAL_CAPTURED_CHILD_TEXT' if condition == 'OWN_TEXT' else 'DECLARED_UNAVAILABLE_SERVICE'))
            source.write(output / f'{graph}_{condition}_EPISODE_{index:02d}.json', entry)
            entries.append(entry)
        panels[condition] = panel(entries)
    return panels


def recall(events, generate, output, label):
    entries = []
    for view in (0, 8):
        for index, event in enumerate(events):
            messages = memory_messages(event['event'], view)
            outcome = hop._invoke(lambda prompt: generate(prompt, role=label.lower() + '_recall', graph=label), messages)
            response = outcome['response']
            expected = source.material.canonical_event(event['raw'])
            correct = (outcome['error'] is None and type(response) is dict
                and response.get('terminal') is True and response.get('truncated') is False and response.get('raw') == expected)
            entry = dict(view=view, event=event['event'], messages=messages, expected=expected, correct=correct, **outcome)
            source.write(output / f'{label}_RECALL_W{view}_{index:02d}.json', entry)
            entries.append(entry)
    return {str(view): dict(correct=sum(entry['correct'] for entry in entries if entry['view'] == view),
                            denominator=len(events)) for view in (0, 8)}


def evaluate(inputs, generate, output, phase):
    conditions = ('PARAMETRIC',) if phase == 'before' else CONDITIONS
    result = dict(panels=evaluate_graph(inputs['world'], inputs['collection'], generate, output, conditions, 'FRESH'))
    events = [dict(event=record['edge']['event'], raw=record['event']['raw']) for record in inputs['collection']['records']]
    result['new_recall'] = recall(events, generate, output, 'NEW')
    if phase == 'after':
        old_events = [dict(event=fact['event'], raw=episode['event']['raw'])
                      for fact, episode in zip(inputs['old_bank'], inputs['old_episodes'])]
        result['old_recall'] = recall(old_events, generate, output, 'OLD')
        audited = audit.collect_cases(inputs['held'], lambda messages: generate(messages, role='held_audit', graph='HELD'), coached=False)
        source.write(output / 'HELD_AUDIT.json', audited)
        result['held_audit'] = audited['summary']
        original = inputs['original_collection']
        result['taught_graph'] = evaluate_graph(original['world'], original, generate, output, ('OWN_TEXT',), 'TAUGHT')
    return result


def verify_output_files(directory, result):
    directory = Path(directory)
    files = result.get('output_files')
    require(type(files) is dict and bool(files), 'readonly_output_inventory_required')
    require({path.name for path in directory.glob('*.json') if path.name != 'RESULT.json'} == set(files),
            'readonly_output_inventory_drift')
    transfer.verify_files(directory, files)


def read_before(directory, inputs):
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    require(not (directory / 'FAILED.json').exists() and result.get('schema') == SCHEMA
        and result.get('phase') == 'before' and result.get('status') == 'COMPLETE'
        and result.get('binding') == inputs['binding'] and result.get('fits') == result.get('updates') == 0
        and result.get('protocol') == 'turnbound' and result.get('parent_present') is False
        and result.get('loaded_adapter_state_sha256') == result.get('adapter_state_after') == PARENT_STATE
        and result.get('frozen_base_unchanged') is True and result.get('max_native_calls') == CAPS['before'],
        'complete_unchanged_before_required')
    verify_output_files(directory, result)
    calls = iter(read_calls(directory, result['model_calls'], CAPS['before']))
    entries = []
    store = hop.exact_text_store(inputs['collection'])
    for index, task in enumerate(hop.build_tasks(inputs['world'])):
        entry = source.read(directory / f'FRESH_PARAMETRIC_EPISODE_{index:02d}.json')
        score = verify_episode_calls(entry['episode'], inputs['world'], task, store, 'PARAMETRIC', calls, index, graph='FRESH')
        same(entry, dict(graph='FRESH', condition='PARAMETRIC', task_index=index, task=task,
             episode=entry['episode'], score=score, memory_origin='ACTUAL_PARAMETRIC_RESPONSE_NO_FALLBACK'), 'before_episode_drift')
        entries.append(entry)
    same(result['panels'], dict(PARAMETRIC=panel(entries)), 'before_panel_drift')
    recalls = []
    for view in (0, 8):
        for index, record in enumerate(inputs['collection']['records']):
            event = record['edge']['event']
            entry = source.read(directory / f'NEW_RECALL_W{view}_{index:02d}.json')
            call = next(calls, None)
            require(call is not None and call['role'] == 'new_recall' and call['graph'] == 'NEW', 'before_recall_call_drift')
            expected = source.material.canonical_event(record['event']['raw'])
            response = call['response']
            correct = (type(response) is dict and response.get('terminal') is True
                       and response.get('truncated') is False and response.get('raw') == expected)
            same(entry, dict(view=view, event=event, messages=memory_messages(event, view), expected=expected,
                             correct=correct, response=response, error=None), 'before_recall_output_drift')
            same(call['messages'], entry['messages'], 'before_recall_prompt_drift')
            recalls.append(entry)
    same(result['new_recall'], {str(view): dict(correct=sum(entry['correct'] for entry in recalls if entry['view'] == view),
         denominator=4) for view in (0, 8)}, 'before_recall_summary_drift')
    require(next(calls, None) is None, 'unknown_before_native_call')
    return result, source.file_hash(directory / 'RESULT.json')


def read_training(directory, inputs, before_sha):
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    state = result.get('adapter_state_after')
    require(not (directory / 'FAILED.json').exists() and result.get('schema') == SCHEMA
        and result.get('phase') == 'train' and result.get('status') == 'COMPLETE'
        and result.get('binding') == inputs['binding'] and result.get('before_result_sha256') == before_sha
        and result.get('fits') == 1 and result.get('updates') == UPDATES and result.get('model_calls') == 0
        and result.get('loaded_adapter_state_sha256') == PARENT_STATE and result.get('parent_present') is False
        and type(state) is str and len(state) == 64 and all(char in '0123456789abcdef' for char in state)
        and state != PARENT_STATE and result.get('frozen_base_unchanged') is True, 'own_completed_memory_write_required')
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(result.get('adapter_files', {}))
        and set(result.get('training_files', {})) == {'TRAINING_ROWS.json', 'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl'},
        'complete_memory_training_inventory_required')
    transfer.verify_files(directory / 'adapter', result['adapter_files'])
    transfer.verify_files(directory, result['training_files'])
    require(source.read(directory / 'adapter/adapter_config.json').get('r') == 8, 'saved_rank_eight_required')
    same(source.read(directory / 'TRAINING_ROWS.json'), inputs['material'], 'saved_memory_training_source_drift')
    same(source.read(directory / 'RECIPE.json'), recipe(), 'saved_memory_recipe_drift')
    return result, source.file_hash(directory / 'RESULT.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--lesson-root', default=transfer.LESSON_ROOT)
    parser.add_argument('--transfer-root', default=TRANSFER_ROOT)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--phase', choices=tuple(CAPS), required=True)
    parser.add_argument('--before')
    parser.add_argument('--training')
    options = parser.parse_args(argv)
    require(bool(options.before) == (options.phase in ('train', 'after'))
            and bool(options.training) == (options.phase == 'after'), 'memory_phase_arguments')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or bool(options.gpu_uuid)
            and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started, cap = time.time(), CAPS[options.phase]
    result = dict(schema=SCHEMA, phase=options.phase, arguments=vars(options), started_unix=started,
        fits=0, updates=0, model_calls=0, max_native_calls=cap, parent_present=False, protocol='turnbound',
        max_context=2048, max_new_tokens=160, claim=CLAIM, entry_sha256=source.file_hash(__file__),
        automatic_training=False, reused_baseline_interpretation='REUSED_37EC_PARENT_NOT_INDEPENDENT_LEARNERS')
    source.write(output / 'REQUEST.json', result)
    captures, engine, cap_hit = [], None, False

    def check(label):
        require(time.time() < started + (1800 if options.phase == 'before' else 3500), 'memory_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result['binding'] = inputs['binding']
        for name, value in (('INPUTS.json', inputs['binding']), ('WORLD.json', inputs['world']),
                ('TASKS.json', hop.build_tasks(inputs['world'])), ('COLLECTION_SOURCE.json', inputs['collection']),
                ('NEW_ROWS.json', inputs['material']['new_rows'])):
            source.write(output / name, value)
        state = PARENT_STATE
        transfer_binding = inputs['binding']['transfer']
        arguments = argparse.Namespace(**inputs['arguments'])
        arguments.phase, arguments.device, arguments.gpu_uuid = 'readout', 'cuda:0', options.gpu_uuid
        arguments.adapter_dir = transfer_binding['trained_adapter_dir']
        files = transfer_binding['trained_adapter_files']
        if options.phase in ('train', 'after'):
            unused_before, before_sha = read_before(options.before, inputs)
            inputs['verified_before_sha256'] = result['before_result_sha256'] = before_sha
        if options.phase == 'after':
            trained, result['training_result_sha256'] = read_training(options.training, inputs, before_sha)
            state = trained['adapter_state_after']
            arguments.adapter_dir, files = str(Path(options.training) / 'adapter'), trained['adapter_files']
        transfer.verify_files(arguments.adapter_dir, files)
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
        require(bool(parameters) and _state_hash(parameters) == state, 'mounted_memory_state_required')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=state)

        def generate(messages, *, role, condition=None, task_index=None, graph=None):
            nonlocal cap_hit
            check('call')
            if len(captures) >= cap:
                cap_hit = True
                raise ValueError('memory_native_call_cap')
            capture = dict(call_index=len(captures), role=role, condition=condition, task_index=task_index,
                           graph=graph, messages=deepcopy(messages), response=None, error=None)
            captures.append(capture)
            try:
                capture['response'] = deepcopy(engine.generate(deepcopy(messages), max_new_tokens=160))
                return deepcopy(capture['response'])
            except Exception as error:
                capture['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                source.write(output / f"CALL_{capture['call_index']:03d}.json", capture)

        if options.phase == 'train':
            result.update(train(engine, inputs, output))
        else:
            result.update(evaluate(inputs, generate, output, options.phase))
        require(not cap_hit, 'memory_native_call_cap')
        require(not any(capture['error'] is not None for capture in captures), 'native_errors_retained')
        engine.verify_base()
        final_state = _state_hash(parameters)
        if options.phase == 'train':
            require(final_state == result['adapter_state_after'] and final_state != state, 'saved_memory_state_drift')
            transfer.verify_files(output / 'adapter', result['adapter_files'])
        else:
            require(final_state == state, 'readonly_memory_state_drift')
        transfer.verify_files(arguments.adapter_dir, files)
        transfer.verify_files(arguments.model_dir, transfer_binding['base_files'])
        same(helpers(), inputs['binding']['helper_hashes'], 'runtime_memory_helper_drift')
        result['adapter_state_after'] = final_state
        source.write(output / 'STATES.json', dict(before=state, after=final_state))
        result.update(status='COMPLETE', model_calls=len(captures), frozen_base_unchanged=True,
            role_calls=dict(Counter(capture['role'] for capture in captures)), finished_unix=time.time())
        if options.phase != 'train':
            result['output_files'] = {path.name: source.file_hash(path) for path in output.glob('*.json')}
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        if engine is not None:
            try:
                result['adapter_state_after'] = _state_hash(parameters)
                engine.verify_base()
                transfer.verify_files(arguments.adapter_dir, files)
                transfer.verify_files(arguments.model_dir, inputs['binding']['transfer']['base_files'])
                result['frozen_base_unchanged'] = True
            except BaseException as verification_error:
                result['failure_verification_error'] = repr(verification_error)
            if not (output / 'STATES.json').exists():
                source.write(output / 'STATES.json', dict(before=result.get('loaded_adapter_state_sha256'),
                    expected=state, after=result.get('adapter_state_after')))
        result.update(status='FAILED', error=repr(error), model_calls=len(captures), cap_hit=cap_hit, finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
