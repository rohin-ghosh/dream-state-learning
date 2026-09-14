"""QUALITY_BREADTH: one finite paired actual-corpus fit, independent of scale admission."""

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
import os
from pathlib import Path
from types import SimpleNamespace
import time
from tempfile import TemporaryDirectory

from gpu import astra_goal_quality_collection as collector
from gpu import astra_experienced_event_cue_sleep as development
from gpu import astra_reader_audit_lesson_train as masks


memory = collector.portable.collector.memory
quality = collector.quality
goal = collector.original.scale
source = collector.source
require = collector.require
same = collector.same
PARENT_STATE = collector.PARENT_STATE
SCHEMA = 'DEV_GOAL_QUALITY_BREADTH_FIT_V1'
ARMS = ('FULL_TARGET', 'NEW_TRAJECTORY_LOSS_OFF')
UPDATES = 2928
TRAIN_SECONDS = 10800
AFTER_SECONDS = 3600
AFTER_CALLS = 960
SEEDS = (0,)
GROUPS = ('memory_rows', 'cue_rows', 'audit_rows', 'trajectory_rows', 'new_trajectory_rows')
GROUP_SIZES = (128, 20, 62, 12, 1452)
PROTOCOL_PATH = 'research_notes/analysis/2026-09-14_goal_quality_fit_protocol.md'
PROTOCOL_SHA = '1683ca250ef6f95cb41c7972685279a07ec3693fb9ab34e049ffb975e8eb96e9'
COLLECTION_PROTOCOL_SHA = 'cf742f62dc45810caeea3ec68272a9e1a8c97d3b7c6c06f148639252ba1738f1'
CLAIM = 'QUALITY_BREADTH_LOWER_DOSE_ONE_EXPOSED_DEV_LINEAGE_NOT_DOSE_ISOLATED_OR_H1_H2'
ASSEMBLY_SHA = 'cbe638aa1377a98ada6c60a3fc1b264c685a2e31c95b5121f2dd3f860bda1a1e'
ASSEMBLY_RESULT_SHA = 'dc28974727b60e147ce2920eabbf9a7550f02e4c943c236bcd7bd6739d9bdfe4'
TRAIN_SELECTION = ((0, 0), (1, 0), (4, 0), (6, 0))
TRAINING_FILES = ('TRAINING_ROWS.json', 'REFERENCE_MASKS.json', 'MASKS.json', 'RECIPE.json', 'DOSE.json', 'LOSSES.jsonl')


def helpers():
    return dict(driver=source.file_hash(__file__),
        guard=source.file_hash(Path(__file__).with_name('astra_goal_quality_train_guard.sh')),
        collector=collector.helpers(), development=source.file_hash(development.__file__), masks=source.file_hash(masks.__file__))


def training_indexes(update):
    require(type(update) is int and 1 <= update <= UPDATES, 'fixed_2928_update_range')
    offset = update - 1
    return (offset % 128, 128 + offset % 82, 210 + (2 * offset) % 1464, 210 + (2 * offset + 1) % 1464)


def recipe(arm, seed=0):
    require(type(seed) is int and seed in SEEDS, 'fixed_seed_zero_required')
    require(arm in ARMS, 'fixed_goal_fit_arm_required')
    return dict(schema=SCHEMA, arm=arm, initial_state=PARENT_STATE, updates=UPDATES, batch_size=4,
        learning_rate=3e-5, seed=seed, rank=8, optimizer='FRESH_ADAMW', optimizer_kwargs=dict(source.native.OPTIMIZER),
        lora_dropout=0.05, seed_scope='SAME_CORPUS_TRAINING_RNG_NOT_INDEPENDENT_DEVELOPMENT',
        group_order=list(GROUPS), group_sizes=list(GROUP_SIZES), encoded_rows=1674,
        schedule=[list(training_indexes(update)) for update in range(1, UPDATES + 1)],
        masked_row_indexes=list(range(222, 1674)) if arm == ARMS[1] else [],
        loss='MEAN_CAUSAL_CE_TIMES_ACTIVE_OVER_FULL_REFERENCE_LABELS', actual_token_equality_claim=False,
        old_trajectory_presentations=48, new_target_presentations=5808, new_supervised_presentations=5808 if arm == ARMS[0] else 0,
        old_memory_presentations=2928, old_behavior_presentations=2928, protocol_sha256=PROTOCOL_SHA)


def controlled_masks(encoded, arm):
    require(arm in ARMS and len(encoded) == 1674, 'exact_1674_rows_and_fixed_arm_required')
    return tuple(replace(row, labels=(-100,) * len(row.labels)) if arm == ARMS[1] and index >= 222 else row
                 for index, row in enumerate(encoded))


def training_batch(encoded, update, arm):
    indexes = training_indexes(update)
    require(arm in ARMS and len(encoded) == 1674, 'exact_1674_rows_and_fixed_arm_required')
    controlled = [replace(encoded[index], labels=(-100,) * len(encoded[index].labels))
                  if arm == ARMS[1] and index >= 222 else encoded[index] for index in indexes]
    batch = source.native.collate(controlled, pad_id=151643)
    reference_batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
    require(batch['input_ids'] == reference_batch['input_ids'] and batch['attention_mask'] == reference_batch['attention_mask']
            and all(batch['labels'][slot] == reference_batch['labels'][slot]
                    for slot, index in enumerate(indexes) if index < 222), 'matched_goal_inputs_and_old_labels_required')
    reference, active, scale = development.loss_normalization(encoded, indexes, batch)
    return indexes, batch, reference, active, scale


def dose(encoded, arm):
    batches, presentations = [], [0] * 1674
    for update in range(1, UPDATES + 1):
        indexes, unused_batch, reference, active, scale = training_batch(encoded, update, arm)
        for index in indexes:
            presentations[index] += 1
        batches.append(dict(update=update, row_indexes=list(indexes), reference_labels=reference,
                            active_labels=active, loss_scale=scale))
    require(sum(presentations[:128]) == sum(presentations[128:210]) == 2928
            and sum(presentations[210:222]) == 48 and sum(presentations[222:]) == 5808
            and set(presentations[210:]) == {4}, 'fixed_goal_dose_required')
    return dict(batches=batches, row_presentations=presentations,
        actual_supervised_tokens=sum(batch['active_labels'] for batch in batches),
        reference_supervised_tokens=sum(batch['reference_labels'] for batch in batches))


def read_assembly(options, admitted):
    directory = Path(options.quality_root)
    require(source.file_hash(directory/'CAPSULE.json') == ASSEMBLY_SHA
            and source.file_hash(directory/'RESULT.json') == ASSEMBLY_RESULT_SHA, 'exact_actual_quality_assembly_required')
    result = source.read(directory/'RESULT.json')
    require(not (directory/'FAILED.json').exists() and result['schema'] == collector.SCHEMA
            and result['phase'] == 'assemble' and result['status'] == 'COMPLETE_NO_MODEL'
            and result['model_calls'] == result['fits'] == result['updates'] == 0
            and result['trainingAllowed'] is False and result['row_count'] == 1452 and result['new_calls'] == 696,
            'completed_1452_actual_quality_assembly_required')
    same(result['binding'], admitted['binding'], 'assembly_native_binding_drift')
    require(set(result['output_files']) == {path.name for path in directory.glob('*.json') if path.name != 'RESULT.json'},
            'assembly_inventory_drift')
    memory.transfer.verify_files(directory, result['output_files'])
    wrapper = source.read(directory/'CAPSULE.json')
    locations = options.unit_roots or result['arguments']['unit_roots']
    require(len(locations) == 4 and len({str(Path(path).resolve()) for path in locations}) == 4,
            'four_distinct_quality_units_required')
    units = [collector.read_unit(location, admitted, unit) for location, unit in zip(locations, quality.UNITS)]
    same(wrapper['native_binding'], admitted['binding'], 'capsule_native_binding_drift')
    same(wrapper['unit_results'], [dict(unit=unit, result_sha256=source.file_hash(Path(location)/'RESULT.json'))
         for location, unit in zip(locations, quality.UNITS)], 'assembled_native_unit_receipts_drift')
    capsule = quality.assemble(admitted['exposures'], admitted['teachings'], units)
    same(wrapper['capsule'], capsule, 'actual_quality_capsule_replay_drift')
    require(capsule['row_count'] == 1452 and capsule['admitted_pairs'] == 121
            and len(capsule['reused']['rows']) == 756 and capsule['new_calls'] == 696, 'fixed_actual_quality_yield_required')
    return capsule


def load_inputs(options):
    started = time.monotonic()
    require(source.file_hash(Path(__file__).resolve().parents[1]/PROTOCOL_PATH) == PROTOCOL_SHA,
            'exact_quality_fit_protocol_required')
    original = memory.load_inputs(options)
    legacy_seconds = time.monotonic() - started
    parent, arguments = original['binding']['transfer'], dict(original['arguments'])
    if options.model_dir:
        arguments['model_dir'] = options.model_dir
    admitted = collector.load_inputs(SimpleNamespace(**dict(vars(options), model_dir=arguments['model_dir'])))
    manifest = admitted['manifest']
    require(admitted['binding']['protocol_sha256'] == COLLECTION_PROTOCOL_SHA
            and parent['trained_state'] == manifest['parent_state'] == PARENT_STATE
            and parent['training_result_sha256'] == manifest['receipt_locators']['training']['sha256']
            and arguments['expected_base_sha256'] == manifest['expected_base_sha256'], 'same_37ec_legacy_bundle_parent_required')
    same(parent['trained_adapter_files'], manifest['adapter_files'], 'same_37ec_adapter_files_required')
    same(parent['base_files'], manifest['base_files'], 'same_frozen_base_files_required')
    capsule = read_assembly(options, admitted)
    old = {key: deepcopy(original['material'][key]) for key in GROUPS[:-1]}
    same(old, source.read(Path(options.lesson_root)/'train/TRAINING_ROWS.json'), 'exact_original_222_rows_required')
    material = dict(old, new_trajectory_rows=capsule['rows'])
    require(tuple(len(material[key]) for key in GROUPS) == GROUP_SIZES, 'fixed_1674_row_mixture_required')
    require(all(row['master'] in goal.runtime(row['shard'])['TRAIN_MASTERS'] for row in capsule['rows']),
            'actual_train_only_quality_rows_required')
    probe_ids = set().union(*(goal.identifiers(entry['world']) for entry in capsule['source_plan']['probes']))
    serialized = source.json.dumps(material, allow_nan=False)
    require(not any(identifier in serialized for identifier in probe_ids),
            'probe_identifiers_forbidden_in_training')
    binding = dict(quality=admitted['binding'], legacy=original['binding'], bundle_sha256=options.bundle_sha,
        assembly_sha256=ASSEMBLY_SHA, assembly_result_sha256=ASSEMBLY_RESULT_SHA,
        material_sha256=goal.document_sha256(material), protocol_sha256=PROTOCOL_SHA,
        old_masks_sha256=source.file_hash(Path(options.lesson_root)/'train/MASKS.json'),
        helper_hashes=helpers(), initial_state=PARENT_STATE,
        readout=dict(train_selection=[list(item) for item in TRAIN_SELECTION], calls=AFTER_CALLS,
                     source_plan_sha256=capsule['source_plan']['plan_sha256'], public_system=quality.hop.TURNBOUND_SYSTEM))
    return dict(arguments=arguments, parent=parent, binding=binding, material=material,
        old_masks=source.read(Path(options.lesson_root)/'train/MASKS.json'),
        exposure=dict(shards=[entry['collections'] for entry in admitted['exposures']]),
        source_plan=capsule['source_plan'], original=original,
        admission_timing=dict(legacy_seconds=legacy_seconds, quality_seconds=time.monotonic()-started-legacy_seconds,
                             total_seconds=time.monotonic()-started))

def encode_new_rows(rows, tokenizer):
    require(len(rows) == 1452, 'actual_1452_rows_before_encoding_required')
    require(tokenizer.eos_token == quality.lesson.TARGET_EOT and type(tokenizer.eos_token_id) is int
            and source.native._encode(tokenizer, quality.lesson.TARGET_EOT) == (tokenizer.eos_token_id,), 'exact_goal_pair_eot_required')
    encoded = []
    for row in rows:
        prefix = row['prefix']
        require([message['role'] for message in prefix] == ['system', 'user']
                + ['assistant', 'user'] * row['episode_call_index'], 'alternating_goal_pair_student_prefix_required')
        messages = prefix + [dict(role='assistant', content=row['assistant'])]
        context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
        require(full == context + row['assistant'] + quality.lesson.TARGET_EOT + '\n', 'exact_goal_pair_template_boundary_required')
        prefix_ids = source.native._encode(tokenizer, context)
        target = source.native._encode(tokenizer, row['assistant'])
        suffix = source.native._encode(tokenizer, '\n')
        require(not set(tokenizer.all_special_ids).intersection(target), 'goal_pair_target_special_token_forbidden')
        supervised = target + (tokenizer.eos_token_id,)
        sequence = source.native._encode(tokenizer, full)
        require(sequence == prefix_ids + supervised + suffix and len(sequence) <= 2048
                and len(supervised) <= 160, 'untruncated_bounded_goal_pair_sequence_required')
        require(source.native._decode(tokenizer, sequence) == full and source.native._decode(tokenizer, prefix_ids) == context
                and source.native._decode(tokenizer, supervised) == row['assistant'] + quality.lesson.TARGET_EOT
                and source.native._decode(tokenizer, suffix) == '\n', 'goal_pair_token_roundtrip_failed')
        require(tuple(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
            return_dict=False, truncation=False, padding=False)) == sequence, 'goal_pair_template_token_ids_mismatch')
        encoded.append(source.native.EncodedRow(sequence, (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix), supervised))
    return tuple(encoded)

def encode_material(inputs, tokenizer):
    material = inputs['material']
    encoded = tuple(source.encode_row(row['messages'], tokenizer) for row in material['memory_rows'])
    encoded += tuple(memory.cues.encode_cue_rows(material['cue_rows'], tokenizer))
    encoded += tuple(memory.audit.encode_rows(material['audit_rows'], tokenizer))
    encoded += tuple(memory.lesson.lesson.encode_rows(material['trajectory_rows'], tokenizer))
    same([asdict(row) for row in encoded], inputs['old_masks'], 'unchanged_original_222_encodings_required')
    encoded += tuple(encode_new_rows(material['new_trajectory_rows'], tokenizer))
    require(len(encoded) == 1674 and tokenizer.pad_token_id == 151643, 'fixed_native_encoding_required')
    masks.validate_masks(encoded, tokenizer.eos_token_id)
    return encoded


def train(engine, inputs, output, arm, seed=0):
    recipe(arm, seed)
    from organism_v6.pcfl_vertical_train import _state_hash

    encoded = encode_material(inputs, engine.tokenizer)
    evidence = dose(encoded, arm)
    source.write(output / 'TRAINING_ROWS.json', inputs['material'])
    source.write(output / 'REFERENCE_MASKS.json', [asdict(row) for row in encoded])
    source.write(output / 'MASKS.json', [asdict(row) for row in controlled_masks(encoded, arm)])
    source.write(output / 'RECIPE.json', recipe(arm, seed))
    source.write(output / 'DOSE.json', evidence)
    parameters = development.enable_existing_adapter(engine)
    require(_state_hash(parameters) == PARENT_STATE, 'same_37ec_before_gradient_required')
    torch = engine.torch
    torch.manual_seed(seed)
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, **source.native.OPTIMIZER)
    engine.model.train()
    fit_started = time.monotonic()
    actual_total, reference_total = 0, 0
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, UPDATES + 1):
            engine.check('goal_quality_update')
            indexes, batch, reference, active, scale = training_batch(encoded, update, arm)
            expected = evidence['batches'][update - 1]
            same(dict(update=update, row_indexes=list(indexes), reference_labels=reference, active_labels=active,
                      loss_scale=scale), expected, 'pregradient_goal_batch_drift')
            tensors = {key: torch.tensor(value, dtype=torch.long, device=engine.device) for key, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                mean_loss = engine.model(**tensors, use_cache=False).loss
                loss = mean_loss * scale
            require(bool(torch.isfinite(loss)) and loss.requires_grad, 'invalid_goal_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'invalid_goal_gradient')
            optimizer.step()
            require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()), 'nonfinite_goal_adapter')
            actual_total += active
            reference_total += reference
            stream.write(source.json.dumps(dict(expected, mean_loss=mean_loss.item(), loss=loss.item(),
                fit_elapsed_seconds=time.monotonic() - fit_started), allow_nan=False) + '\n')
            stream.flush()
    state = _state_hash(parameters)
    require(state != PARENT_STATE and actual_total == evidence['actual_supervised_tokens']
            and reference_total == evidence['reference_supervised_tokens'], 'completed_goal_fit_dose_required')
    engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    files = {path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()}
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(files), 'saved_goal_adapter_required')
    return dict(fits=1, updates=UPDATES, adapter_state_after=state, adapter_files=files,
        actual_supervised_tokens=actual_total, reference_supervised_tokens=reference_total,
        row_presentations=evidence['row_presentations'],
        training_files={name: source.file_hash(output / name) for name in TRAINING_FILES})


def read_training(directory, inputs, arm, seed=0):
    directory = Path(directory)
    receipt = source.read(directory / 'RESULT.json')
    require(not (directory / 'FAILED.json').exists() and receipt.get('schema') == SCHEMA
            and receipt.get('phase') == 'train' and receipt.get('status') == 'COMPLETE'
            and receipt.get('arm') == arm and receipt.get('seed') == seed and receipt.get('fits') == 1 and receipt.get('updates') == UPDATES
            and receipt.get('trainingAllowed') is True and receipt.get('model_calls') == 0
            and receipt.get('loaded_adapter_state_sha256') == PARENT_STATE
            and isinstance(receipt.get('adapter_state_after'), str) and len(receipt['adapter_state_after']) == 64
            and all(character in '0123456789abcdef' for character in receipt['adapter_state_after'])
            and receipt['adapter_state_after'] != PARENT_STATE and receipt.get('frozen_base_unchanged') is True
            and receipt.get('parent_present') is False, 'own_completed_goal_arm_required')
    same(receipt['binding'], inputs['binding'], 'saved_goal_fit_binding_drift')
    require(receipt.get('baseline_contract_sha256') == goal.document_sha256(inputs['binding']['readout']),
            'saved_baseline_readout_contract_required')
    require(set(receipt['training_files']) == set(TRAINING_FILES), 'goal_training_inventory_required')
    memory.transfer.verify_files(directory, receipt['training_files'])
    collector.portable.verify_inventory(directory / 'adapter', receipt['adapter_files'])
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(receipt['adapter_files'])
            and source.read(directory / 'adapter/adapter_config.json').get('r') == 8, 'saved_goal_rank_eight_required')
    same(source.read(directory / 'TRAINING_ROWS.json'), inputs['material'], 'saved_goal_rows_drift')
    same(source.read(directory / 'RECIPE.json'), recipe(arm, seed), 'saved_goal_recipe_drift')
    reference = source.read(directory / 'REFERENCE_MASKS.json')
    same(reference[:222], inputs['old_masks'], 'saved_original_masks_drift')
    encoded = tuple(source.native.EncodedRow(**{key: tuple(value) for key, value in row.items()}) for row in reference)
    require(len(encoded) == 1674, 'saved_1674_encodings_required')
    masks.validate_masks(encoded, 151645)
    same(source.read(directory / 'MASKS.json'), [asdict(row) for row in controlled_masks(encoded, arm)], 'saved_control_masks_drift')
    evidence = dose(encoded, arm)
    same(source.read(directory / 'DOSE.json'), evidence, 'saved_goal_dose_drift')
    for field in ('actual_supervised_tokens', 'reference_supervised_tokens', 'row_presentations'):
        same(receipt[field], evidence[field], 'saved_goal_total_drift:' + field)
    logs = [source.json.loads(line) for line in (directory / 'LOSSES.jsonl').read_text().splitlines()]
    require(len(logs) == UPDATES and all(all(log.get(key) == value for key, value in expected.items())
        for log, expected in zip(logs, evidence['batches'])), 'saved_goal_update_log_drift')
    same(source.read(directory / 'STATES.json'), dict(before=PARENT_STATE, after=receipt['adapter_state_after']), 'saved_goal_state_drift')
    return receipt, source.file_hash(directory / 'RESULT.json')


def first_ports(world, tasks):
    ports = []
    for task in tasks:
        candidates = [edge['port'] for edge in world['edges'] if edge['node'] == task['node']
            and any(second['node'] == edge['outcome'] and second['outcome'] == task['goal'] for second in world['edges'])]
        require(len(candidates) == 1, 'unique_environment_goal_route_required')
        ports.append(candidates[0])
    return ports


def summarize_world(collection, episodes, runtime):
    world, tasks = collection['world'], runtime.build_tasks(collection['world'])
    require(len(episodes) == 4, 'all_four_fixed_tasks_required')
    raw_runtime = runtime._block(runtime.MASTER_BLOCK[world['master']])['_runtime'](world['master'])
    scores = [raw_runtime['score_episode'](world, task, runtime.replay_episode(world, task, episode))
              for task, episode in zip(tasks, episodes)]
    expected = first_ports(world, tasks)
    pairs = []
    for indexes in runtime.goal.GOAL_PAIRS:
        actual = [episodes[index]['routes'][0]['port'] if episodes[index]['routes'] else None for index in indexes]
        ports = [expected[index] for index in indexes]
        both = all(scores[index]['correct'] for index in indexes)
        distinct = actual == ports and len(set(actual)) == 2
        commits = all(scores[index]['legal_routes'] == 2 for index in indexes)
        pairs.append(dict(task_indexes=list(indexes), both_goals_correct=both, distinct_source_correct_first_ports=distinct,
            two_legal_commits=commits, source_first_ports=ports, actual_first_ports=actual, correct=both and distinct and commits))
    return dict(individual=dict(correct=sum(score['correct'] for score in scores), denominator=4),
        paired=dict(correct=sum(pair['correct'] for pair in pairs), denominator=2), pairs=pairs, scores=scores)


def first_port_reference(collection, runtime):
    def actor(messages):
        public = next(message['content'] for message in reversed(messages) if message['content'].startswith('ROUTE TASK\n'))
        ports = next(line[6:] for line in public.splitlines() if line.startswith('PORTS '))
        return dict(raw='ROUTE ' + ports.split(',')[0], terminal=True, truncated=False)
    episodes = [runtime.run_episode(collection['world'], task, actor, lambda address: quality.UNAVAILABLE)
                for task in runtime.build_tasks(collection['world'])]
    return dict(policy='FIRST_CURRENT_DISPLAYED_PORT_NO_READS', native_calls=0, episodes=episodes,
                summary=summarize_world(collection, episodes, runtime))

def evaluate_goal_world(collection, condition, generate, output, split, world_index, runtime):
    world = collection['world']
    store = {record['edge']['event']: record['event']['raw'] if record['accepted'] else quality.UNAVAILABLE
             for record in collection['records']}
    episodes = []
    for task_index, task in enumerate(runtime.build_tasks(world)):
        def actor(messages):
            return generate(messages, role='actor', master=world['master'], condition=condition, task_index=task_index, graph=split)

        def reader(address):
            return store[address] if condition == 'OWN_TEXT' else 'MEMORY UNAVAILABLE'

        episode = runtime.run_episode(world, task, actor, reader)
        source.write(output / f'{split}_{world_index}_{condition}_{task_index}.json', episode)
        episodes.append(episode)
    summary = summarize_world(collection, episodes, runtime)
    expected_ports = first_ports(world, runtime.build_tasks(world))
    diagnostics = []
    for index, episode in enumerate(episodes):
        expected_first = expected_ports[index]
        first = episode['routes'][0]['port'] if episode['routes'] else None
        failure = None if summary['scores'][index]['correct'] else 'no_first_commit' if first is None else (
            'wrong_first_port' if first != expected_first else 'second_step_failure')
        diagnostics.append(dict(task_index=index, task=episode['task'], actual_first_port=first,
            source_first_port=expected_first, failure=failure, terminal=episode['terminal_reason'],
            routes=episode['routes'], actor_commands=[trace['response'].get('raw') if isinstance(trace['response'], dict)
                else None for trace in episode['traces'] if trace['kind'] == 'actor']))
    return dict(master=world['master'], condition=condition, collection_sha256=collection['collection_sha256'],
        shared_text_sha256=runtime.document_sha256(store), summary=summary, tasks=diagnostics)


def evaluate(inputs, generate, output):
    panels = dict(TRAIN=[], PROBE=[])
    references = []
    require(len(inputs['exposure']['shards']) == 8, 'all_eight_readout_shards_required')
    for shard, collections in enumerate(inputs['exposure']['shards']):
        runtime = SimpleNamespace(**goal.runtime(shard))
        require(tuple(collection['master'] for collection in collections) == runtime.MASTERS,
                'fixed_scale_readout_worlds_required')
        for collection in collections:
            if collection['master'] in runtime.TRAIN_MASTERS:
                train_index = runtime.TRAIN_MASTERS.index(collection['master'])
                if (shard, train_index) in TRAIN_SELECTION:
                    panel = evaluate_goal_world(collection, 'OWN_TEXT', generate, output, 'TRAIN', shard, runtime)
                    panels['TRAIN'].append(dict(panel, shard=shard))
                    source.write(output/f'TRAIN_{shard}_SUMMARY.json', dict(panel, shard=shard))
                continue
            world_index = 2 * shard + runtime.PROBE_MASTERS.index(collection['master'])
            for condition in collector.original.CONDITIONS:
                panel = evaluate_goal_world(collection, condition, generate, output, 'PROBE', world_index, runtime)
                panels['PROBE'].append(dict(panel, shard=shard))
                source.write(output / f'PROBE_{world_index}_{condition}_SUMMARY.json', dict(panel, shard=shard))
            reference = dict(shard=shard, master=collection['master'], **first_port_reference(collection, runtime))
            source.write(output / f'PROBE_{world_index}_FIRST_PORT_REFERENCE.json', reference)
            references.append(reference)
    original = inputs['original']
    events = [dict(event=fact['event'], raw=episode['event']['raw'])
              for fact, episode in zip(original['old_bank'], original['old_episodes'])]
    retention = memory.recall(events, generate, output, 'OLD')
    audited = memory.audit.collect_cases(original['held'], lambda messages: generate(messages, role='held_audit', graph='HELD'), coached=False)
    source.write(output / 'HELD_AUDIT.json', audited)
    taught = memory.evaluate_graph(original['original_collection']['world'], original['original_collection'], generate,
        output, ('OWN_TEXT',), 'TAUGHT')
    fresh = memory.evaluate_graph(original['world'], original['collection'], generate, output, ('OWN_TEXT',), 'PREVIOUS_FRESH')
    primary_worlds = [dict(master=panel['master'], **panel['summary']['paired'])
                      for panel in panels['PROBE'] if panel['condition'] == 'OWN_TEXT']
    primary = dict(metric='PROBE_OWN_TEXT_STRICT_GOAL_PAIRS', correct=sum(world['correct'] for world in primary_worlds),
        denominator=32, worlds=primary_worlds, individual=dict(correct=sum(panel['summary']['individual']['correct']
            for panel in panels['PROBE'] if panel['condition'] == 'OWN_TEXT'), denominator=64))
    checks = dict(old_w0=retention['0']['correct'] >= 15, old_w8=retention['8']['correct'] >= 15,
        audit=audited['summary']['overall']['correct'] >= 15, taught=taught['OWN_TEXT']['correct'] >= 3,
        previous_fresh=fresh['OWN_TEXT']['correct'] >= 3)
    engineering = dict(checks, probe_pairs=primary['correct'] >= 24,
                       each_probe_world=len(primary_worlds) == 16 and all(world['correct'] >= 1 for world in primary_worlds))
    result = dict(panels=panels, primary=primary, deterministic_first_port=references, old_recall=retention,
        held_audit=audited['summary'], taught_graph=taught, previous_fresh_graph=fresh,
        retention_checks=checks, retention_target_met=all(checks.values()), engineering_checks=engineering,
        engineering_target_met=all(engineering.values()), train_after='FOUR_FIXED_WORLDS_ALL_TASKS',
        source_defects=inputs['source_plan']['excluded_train'] + [entry for entry in inputs['source_plan']['probes'] if not entry['source_ready']],
        efficacy_decision='REQUIRES_SEPARATE_MATCHED_CONTROL_AND_BASELINE_COMPARISON', claim=CLAIM)
    source.write(output / 'SUMMARY.json', result)
    return result


def read_baseline(directory, inputs):
    directory = Path(directory)
    receipt = source.read(directory/'RESULT.json')
    require(not (directory/'FAILED.json').exists() and receipt['schema'] == SCHEMA and receipt['phase'] == 'baseline'
            and receipt['status'] == 'COMPLETE' and receipt['fits'] == receipt['updates'] == 0
            and receipt['arm'] is None and receipt['seed'] == 0 and receipt['max_native_calls'] == AFTER_CALLS
            and receipt['trainingAllowed'] is False and receipt['parent_present'] is False
            and receipt['loaded_adapter_state_sha256'] == receipt['adapter_state_after'] == PARENT_STATE
            and receipt['frozen_base_unchanged'] is True, 'complete_matched_quality_baseline_required')
    same(receipt['binding'], inputs['binding'], 'baseline_source_task_prompt_binding_drift')
    require(set(receipt['output_files']) == {path.name for path in directory.glob('*.json') if path.name != 'RESULT.json'},
            'baseline_inventory_drift')
    memory.transfer.verify_files(directory, receipt['output_files'])
    same(source.read(directory/'STATES.json'), dict(before=PARENT_STATE,after=PARENT_STATE), 'baseline_state_drift')
    calls = memory.read_calls(directory, receipt['model_calls'], AFTER_CALLS)
    pending = iter(calls)
    def replay(messages, **metadata):
        call = next(pending, None)
        require(call is not None and all(call.get(key) == value for key,value in metadata.items()), 'baseline_call_metadata_drift')
        same(call['messages'], messages, 'baseline_native_prompt_drift')
        return deepcopy(call['response'])
    with TemporaryDirectory(prefix='quality-baseline-replay-') as temporary:
        summary = evaluate(inputs, replay, Path(temporary))
        for path in Path(temporary).glob('*.json'):
            same(source.read(directory/path.name), source.read(path), 'baseline_readout_replay_drift:'+path.name)
    require(next(pending,None) is None, 'extra_baseline_native_calls')
    same({key: receipt[key] for key in summary}, summary, 'baseline_receipt_summary_drift')
    return receipt, source.file_hash(directory/'RESULT.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--lesson-root', default=memory.transfer.LESSON_ROOT)
    parser.add_argument('--transfer-root', default=memory.TRANSFER_ROOT)
    parser.add_argument('--shard-roots', nargs=8, required=True)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--bundle-sha', required=True)
    parser.add_argument('--model-dir')
    parser.add_argument('--quality-root', required=True)
    parser.add_argument('--unit-roots', nargs=4)
    parser.add_argument('--baseline')
    parser.add_argument('--seed', type=int, choices=SEEDS, default=0)
    parser.add_argument('--phase', choices=('prepare', 'baseline', 'train', 'after'), required=True)
    parser.add_argument('--arm', choices=ARMS)
    parser.add_argument('--training')
    parser.add_argument('--gpu-uuid')
    options = parser.parse_args(argv)
    require((options.phase in ('prepare', 'baseline') and options.arm is None) or options.arm in ARMS, 'goal_phase_arm_required')
    require(bool(options.baseline) == (options.phase in ('train', 'after')), 'baseline_location_required_for_train_after')
    require(bool(options.training) == (options.phase == 'after'), 'saved_training_only_for_after')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or bool(options.gpu_uuid)
            and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output).resolve()
    for value in options.shard_roots + (options.unit_roots or []) + [options.quality_root, options.baseline] + [getattr(options, name) for name in (
            'bundle', 'model_dir', 'lesson_root', 'transfer_root', 'base_after', 'campaign',
            'audit_root', 'repair_root', 'cycle_root', 'training')]:
        if value:
            reference = Path(value).resolve()
            require(output != reference and reference not in output.parents, 'reference_output_overlap_forbidden')
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, arm=options.arm, seed=options.seed, arguments=vars(options), started_unix=started,
        fits=0, updates=0, trainingAllowed=options.phase == 'train', automatic_training=False, parent_present=False,
        model_calls=0, max_native_calls=AFTER_CALLS if options.phase in ('baseline', 'after') else 0, max_context=2048, max_new_tokens=160,
        protocol=goal.breadth.PROTOCOL, protocol_sha256=PROTOCOL_SHA, entry_sha256=source.file_hash(__file__), claim=CLAIM)
    source.write(output / 'REQUEST.json', result)
    engine, captures, cap_hit = None, [], False

    def check(label):
        require(time.time() < started + (TRAIN_SECONDS if options.phase == 'train' else AFTER_SECONDS), 'goal_fit_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result['binding'] = inputs['binding']
        result['admission_timing'] = inputs['admission_timing']
        source.write(output / 'INPUTS.json', inputs['binding'])
        if options.phase == 'prepare':
            source.write(output / 'TRAINING_ROWS.json', inputs['material'])
            source.write(output / 'RECIPES.json', {arm: recipe(arm, options.seed) for arm in ARMS})
            result.update(status='PREPARED_NO_MODEL', row_count=1674, new_actual_train_targets=1452,
                probe_training_rows=0, tokenization='VALIDATED_IN_TRAIN_BEFORE_GRADIENT', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return result
        if options.phase == 'train':
            result['baseline_contract_sha256'] = goal.document_sha256(inputs['binding']['readout'])
            result['baseline_status'] = 'NOT_READ_TRAIN_INDEPENDENT_OF_BASELINE_RESULTS'
        if options.phase == 'after':
            baseline, result['baseline_result_sha256'] = read_baseline(options.baseline, inputs)
        arguments = argparse.Namespace(**inputs['arguments'])
        state = PARENT_STATE
        arguments.phase, arguments.device, arguments.gpu_uuid = 'readout', 'cuda:0', options.gpu_uuid
        arguments.adapter_dir = inputs['parent']['trained_adapter_dir']
        files = inputs['parent']['trained_adapter_files']
        if options.phase == 'after':
            trained, result['training_result_sha256'] = read_training(options.training, inputs, options.arm, options.seed)
            require(trained['baseline_contract_sha256'] == goal.document_sha256(inputs['binding']['readout']),
                    'same_baseline_contract_train_after_required')
            state, files = trained['adapter_state_after'], trained['adapter_files']
            arguments.adapter_dir = str(Path(options.training) / 'adapter')
        engine = source.Engine(arguments, source.native.load_local_tokenizer(arguments.model_dir), check=check)
        if options.phase == 'after':
            same([asdict(row) for row in encode_material(inputs, engine.tokenizer)],
                 source.read(Path(options.training)/'REFERENCE_MASKS.json'), 'saved_actual_row_encoding_drift')
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters() if '.lora_A.' in name or '.lora_B.' in name}
        require(bool(parameters) and _state_hash(parameters) == state, 'mounted_goal_fit_state_required')
        require(not any(parameter.requires_grad for unused, parameter in engine.model.named_parameters()),
                'initial_goal_actor_must_be_frozen')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=state)

        def generate(messages, *, role, master=None, condition=None, task_index=None, graph=None):
            nonlocal cap_hit
            check('call')
            if len(captures) >= result['max_native_calls']:
                cap_hit = True
                raise ValueError('goal_fit_native_call_cap')
            capture = dict(call_index=len(captures), role=role, master=master, condition=condition,
                task_index=task_index, graph=graph, messages=deepcopy(messages), response=None, error=None)
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
            result.update(train(engine, inputs, output, options.arm, options.seed))
        else:
            result.update(evaluate(inputs, generate, output))
            if options.phase == 'after':
                result['baseline_comparison'] = dict(baseline_pairs=baseline['primary']['correct'],
                    after_pairs=result['primary']['correct'], improves_over_baseline=result['primary']['correct'] > baseline['primary']['correct'],
                    paired_control='SEPARATE_MATCHED_ARM_REQUIRED')
        require(not cap_hit and not any(capture['error'] is not None for capture in captures), 'goal_native_failure_retained')
        engine.verify_base()
        final_state = _state_hash(parameters)
        if options.phase == 'train':
            require(final_state == result['adapter_state_after'] and final_state != state, 'saved_goal_state_changed')
            memory.transfer.verify_files(output / 'adapter', result['adapter_files'])
        else:
            require(final_state == state, 'readonly_goal_state_drift')
        memory.transfer.verify_files(arguments.adapter_dir, files)
        memory.transfer.verify_files(arguments.model_dir, inputs['parent']['base_files'])
        same(helpers(), inputs['binding']['helper_hashes'], 'runtime_goal_helper_drift')
        source.write(output / 'STATES.json', dict(before=state, after=final_state))
        result.update(status='COMPLETE', adapter_state_after=final_state, frozen_base_unchanged=True,
            model_calls=len(captures), role_calls=dict(Counter(capture['role'] for capture in captures)), finished_unix=time.time(),
            generated_tokens=sum(len(capture['response'].get('token_ids', [])) for capture in captures if isinstance(capture['response'], dict)),
            gpu_assigned_wall_seconds=time.time() - started)
        if options.phase in ('baseline', 'after'):
            result['output_files'] = {path.name: source.file_hash(path) for path in output.glob('*.json')}
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        if options.phase == 'train':
            losses = output / 'LOSSES.jsonl'
            result['fit_attempted'] = losses.exists()
            result['completed_updates'] = len(losses.read_text().splitlines()) if losses.exists() else 0
        if engine is not None:
            try:
                result['adapter_state_after'] = _state_hash(parameters)
                engine.verify_base()
                memory.transfer.verify_files(arguments.adapter_dir, files)
                memory.transfer.verify_files(arguments.model_dir, inputs['parent']['base_files'])
            except BaseException as verification_error:
                result['failure_verification_error'] = repr(verification_error)
            if not (output / 'STATES.json').exists():
                source.write(output / 'STATES.json', dict(before=result.get('loaded_adapter_state_sha256'), after=result.get('adapter_state_after')))
        result.update(status='FAILED', error=repr(error), model_calls=len(captures), cap_hit=cap_hit, finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
