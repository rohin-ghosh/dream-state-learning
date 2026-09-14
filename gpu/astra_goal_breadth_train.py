"""Two fixed incremental goal-breadth fits; no recollection or score-based selection."""

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
import os
from pathlib import Path
import time

from gpu import astra_goal_breadth_collection as collector
from gpu import astra_experienced_event_cue_sleep as development
from gpu import astra_reader_audit_lesson_train as masks


memory = collector.memory
goal = collector.goal
source = collector.source
require = collector.require
same = collector.same
PARENT_STATE = collector.PARENT_STATE
SCHEMA = 'DEV_GOAL_BREADTH_INCREMENTAL_FIT_V1'
ARMS = ('FULL_TARGET', 'NEW_TRAJECTORY_LOSS_OFF')
UPDATES = 1632
GROUPS = ('memory_rows', 'cue_rows', 'audit_rows', 'trajectory_rows', 'new_trajectory_rows')
GROUP_SIZES = (128, 20, 62, 12, 192)
PROTOCOL_PATH = 'research_notes/analysis/2026-09-14_goal_breadth_recipe_design.md'
PROTOCOL_SHA = '3f2e4307dab0ad7aa2d8cf62accf14203da1b6ac32fd58779c62840929640ed7'
CLAIM = 'BREADTH_AND_LEGACY_REHEARSAL_ACTUAL_TRAJECTORY_GRADIENTS_ONE_LINEAGE_TWO_DEV_PROBE_INSTANCES_NOT_WHOLE_LIVES_OR_H1_H2'
TRAINING_FILES = ('TRAINING_ROWS.json', 'REFERENCE_MASKS.json', 'MASKS.json', 'RECIPE.json', 'DOSE.json', 'LOSSES.jsonl')


def helpers():
    return dict(driver=source.file_hash(__file__),
        guard=source.file_hash(Path(__file__).with_name('astra_goal_breadth_train_guard.sh')),
        collector=collector.helpers(), development=source.file_hash(development.__file__), masks=source.file_hash(masks.__file__))


def training_indexes(update):
    require(type(update) is int and 1 <= update <= UPDATES, 'fixed_1632_update_range')
    offset = update - 1
    return (offset % 128, 128 + offset % 82, 210 + (2 * offset) % 204, 210 + (2 * offset + 1) % 204)


def recipe(arm):
    require(arm in ARMS, 'fixed_goal_fit_arm_required')
    return dict(schema=SCHEMA, arm=arm, initial_state=PARENT_STATE, updates=UPDATES, batch_size=4,
        learning_rate=3e-5, seed=0, rank=8, optimizer='FRESH_ADAMW', optimizer_kwargs=dict(source.native.OPTIMIZER),
        group_order=list(GROUPS), group_sizes=list(GROUP_SIZES), encoded_rows=414,
        schedule=[list(training_indexes(update)) for update in range(1, UPDATES + 1)],
        masked_row_indexes=list(range(222, 414)) if arm == ARMS[1] else [],
        loss='MEAN_CAUSAL_CE_TIMES_ACTIVE_OVER_FULL_REFERENCE_LABELS', actual_token_equality_claim=False,
        old_trajectory_presentations=192, new_target_presentations=3072, new_supervised_presentations=3072 if arm == ARMS[0] else 0,
        old_memory_presentations=1632, old_behavior_presentations=1632, protocol_sha256=PROTOCOL_SHA)


def controlled_masks(encoded, arm):
    require(arm in ARMS and len(encoded) == 414, 'exact_414_rows_and_fixed_arm_required')
    return tuple(replace(row, labels=(-100,) * len(row.labels)) if arm == ARMS[1] and index >= 222 else row
                 for index, row in enumerate(encoded))


def training_batch(encoded, update, arm):
    indexes = training_indexes(update)
    controlled = controlled_masks(encoded, arm)
    batch = source.native.collate([controlled[index] for index in indexes], pad_id=151643)
    reference_batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
    require(batch['input_ids'] == reference_batch['input_ids'] and batch['attention_mask'] == reference_batch['attention_mask']
            and all(batch['labels'][slot] == reference_batch['labels'][slot]
                    for slot, index in enumerate(indexes) if index < 222), 'matched_goal_inputs_and_old_labels_required')
    reference, active, scale = development.loss_normalization(encoded, indexes, batch)
    return indexes, batch, reference, active, scale


def dose(encoded, arm):
    batches, presentations = [], [0] * 414
    for update in range(1, UPDATES + 1):
        indexes, unused_batch, reference, active, scale = training_batch(encoded, update, arm)
        for index in indexes:
            presentations[index] += 1
        batches.append(dict(update=update, row_indexes=list(indexes), reference_labels=reference,
                            active_labels=active, loss_scale=scale))
    require(sum(presentations[:128]) == sum(presentations[128:210]) == 1632
            and sum(presentations[210:222]) == 192 and sum(presentations[222:]) == 3072
            and set(presentations[210:]) == {16}, 'fixed_goal_dose_required')
    return dict(batches=batches, row_presentations=presentations,
        actual_supervised_tokens=sum(batch['active_labels'] for batch in batches),
        reference_supervised_tokens=sum(batch['reference_labels'] for batch in batches))


def load_inputs(options):
    protocol = Path(__file__).resolve().parents[1] / PROTOCOL_PATH
    require(source.file_hash(protocol) == PROTOCOL_SHA, 'committed_goal_protocol_required')
    collected_inputs = collector.load_inputs(options)
    root = Path(options.collection_root)
    exposure, exposure_sha = collector.read_stage(root / 'expose', 'expose', collected_inputs)
    teaching, teaching_sha = collector.read_stage(root / 'teach', 'teach', collected_inputs, exposure,
        dict(exposure_result_sha256=exposure_sha))
    baseline, baseline_sha = collector.read_stage(root / 'baseline', 'baseline', collected_inputs, exposure,
        dict(exposure_result_sha256=exposure_sha, teaching_result_sha256=teaching_sha))
    require(exposure['source_ready'] and teaching['curriculum_ready'] and teaching['row_count'] == 192,
            'all_192_actual_train_targets_required')
    new_rows = goal.replay_lessons(teaching['lessons'])
    require(len(new_rows) == 192 and all(row['master'] in goal.TRAIN_MASTERS for row in new_rows), 'train_only_actual_rows_required')
    original = memory.load_inputs(options)
    same(original['binding'], collected_inputs['binding']['memory'], 'same_collector_parent_material_required')
    old = {key: deepcopy(original['material'][key]) for key in GROUPS[:-1]}
    same(old, source.read(Path(options.lesson_root) / 'train/TRAINING_ROWS.json'), 'exact_original_222_rows_required')
    material = dict(old, new_trajectory_rows=new_rows)
    require(tuple(len(material[key]) for key in GROUPS) == GROUP_SIZES, 'fixed_414_row_mixture_required')
    probe_ids = set().union(*(goal.identifiers(world) for world in collected_inputs['worlds']['PROBE']))
    serialized = source.json.dumps(material, allow_nan=False)
    require(not any(identifier in serialized for identifier in probe_ids), 'probe_identifiers_forbidden_in_training')
    binding = dict(collection=collected_inputs['binding'], exposure_result_sha256=exposure_sha,
        teaching_result_sha256=teaching_sha, baseline_result_sha256=baseline_sha,
        material_sha256=goal.document_sha256(material), protocol_sha256=PROTOCOL_SHA,
        old_masks_sha256=source.file_hash(Path(options.lesson_root) / 'train/MASKS.json'),
        helper_hashes=helpers(), initial_state=PARENT_STATE)
    return dict(arguments=original['arguments'], parent=original['binding']['transfer'], binding=binding,
        material=material, old_masks=source.read(Path(options.lesson_root) / 'train/MASKS.json'),
        exposure=exposure, baseline=baseline, original=original)


def encode_material(inputs, tokenizer):
    material = inputs['material']
    encoded = tuple(source.encode_row(row['messages'], tokenizer) for row in material['memory_rows'])
    encoded += tuple(memory.cues.encode_cue_rows(material['cue_rows'], tokenizer))
    encoded += tuple(memory.audit.encode_rows(material['audit_rows'], tokenizer))
    encoded += tuple(memory.lesson.lesson.encode_rows(material['trajectory_rows'], tokenizer))
    same([asdict(row) for row in encoded], inputs['old_masks'], 'unchanged_original_222_encodings_required')
    encoded += tuple(goal.encode_rows(material['new_trajectory_rows'], tokenizer))
    require(len(encoded) == 414 and tokenizer.pad_token_id == 151643, 'fixed_native_encoding_required')
    masks.validate_masks(encoded, tokenizer.eos_token_id)
    return encoded


def train(engine, inputs, output, arm):
    from organism_v6.pcfl_vertical_train import _state_hash

    encoded = encode_material(inputs, engine.tokenizer)
    evidence = dose(encoded, arm)
    source.write(output / 'TRAINING_ROWS.json', inputs['material'])
    source.write(output / 'REFERENCE_MASKS.json', [asdict(row) for row in encoded])
    source.write(output / 'MASKS.json', [asdict(row) for row in controlled_masks(encoded, arm)])
    source.write(output / 'RECIPE.json', recipe(arm))
    source.write(output / 'DOSE.json', evidence)
    parameters = development.enable_existing_adapter(engine)
    require(_state_hash(parameters) == PARENT_STATE, 'same_37ec_before_gradient_required')
    torch = engine.torch
    torch.manual_seed(0)
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, **source.native.OPTIMIZER)
    engine.model.train()
    actual_total, reference_total = 0, 0
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, UPDATES + 1):
            engine.check('goal_breadth_update')
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
            stream.write(source.json.dumps(dict(expected, mean_loss=mean_loss.item(), loss=loss.item()), allow_nan=False) + '\n')
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


def read_training(directory, inputs, arm):
    directory = Path(directory)
    receipt = source.read(directory / 'RESULT.json')
    require(not (directory / 'FAILED.json').exists() and receipt.get('schema') == SCHEMA
            and receipt.get('phase') == 'train' and receipt.get('status') == 'COMPLETE'
            and receipt.get('arm') == arm and receipt.get('fits') == 1 and receipt.get('updates') == UPDATES
            and receipt.get('loaded_adapter_state_sha256') == PARENT_STATE
            and isinstance(receipt.get('adapter_state_after'), str) and len(receipt['adapter_state_after']) == 64
            and all(character in '0123456789abcdef' for character in receipt['adapter_state_after'])
            and receipt['adapter_state_after'] != PARENT_STATE and receipt.get('frozen_base_unchanged') is True
            and receipt.get('parent_present') is False, 'own_completed_goal_arm_required')
    same(receipt['binding'], inputs['binding'], 'saved_goal_fit_binding_drift')
    require(set(receipt['training_files']) == set(TRAINING_FILES), 'goal_training_inventory_required')
    memory.transfer.verify_files(directory, receipt['training_files'])
    memory.transfer.verify_files(directory / 'adapter', receipt['adapter_files'])
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(receipt['adapter_files'])
            and source.read(directory / 'adapter/adapter_config.json').get('r') == 8, 'saved_goal_rank_eight_required')
    same(source.read(directory / 'TRAINING_ROWS.json'), inputs['material'], 'saved_goal_rows_drift')
    same(source.read(directory / 'RECIPE.json'), recipe(arm), 'saved_goal_recipe_drift')
    reference = source.read(directory / 'REFERENCE_MASKS.json')
    same(reference[:222], inputs['old_masks'], 'saved_original_masks_drift')
    encoded = tuple(source.native.EncodedRow(**{key: tuple(value) for key, value in row.items()}) for row in reference)
    require(len(encoded) == 414, 'saved_414_encodings_required')
    masks.validate_masks(encoded, encoded[0].target_ids[-1])
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


def first_port_reference(collection):
    def actor(messages):
        public = next(message['content'] for message in reversed(messages) if message['content'].startswith('ROUTE TASK\n'))
        ports = next(line[6:] for line in public.splitlines() if line.startswith('PORTS '))
        return dict(raw='ROUTE ' + ports.split(',')[0], terminal=True, truncated=False)

    episodes = [goal.run_episode(collection['world'], task, actor, lambda address: 'MEMORY UNAVAILABLE')
                for task in goal.build_tasks(collection['world'])]
    return dict(policy='FIRST_CURRENT_DISPLAYED_PORT_NO_READS', native_calls=0, episodes=episodes,
                summary=goal.summarize_pairs(collection, episodes))


def evaluate_goal_world(collection, condition, generate, output, split, world_index):
    world, store = collection['world'], goal.exact_text_store(collection)
    episodes = []
    for task_index, task in enumerate(goal.build_tasks(world)):
        def actor(messages):
            return generate(messages, role='actor', master=world['master'], condition=condition, task_index=task_index, graph=split)

        def reader(address):
            return store[address] if condition == 'OWN_TEXT' else 'MEMORY UNAVAILABLE'

        episode = goal.run_episode(world, task, actor, reader)
        source.write(output / f'{split}_{world_index}_{condition}_{task_index}.json', episode)
        episodes.append(episode)
    summary = goal.summarize_pairs(collection, episodes)
    cases = goal.build_cases(collection)['cases']
    diagnostics = []
    for index, episode in enumerate(episodes):
        expected_first = cases[index]['plan'][4]['command'].split(' ', 1)[1]
        first = episode['routes'][0]['port'] if episode['routes'] else None
        failure = None if summary['scores'][index]['correct'] else 'no_first_commit' if first is None else (
            'wrong_first_port' if first != expected_first else 'second_step_failure')
        diagnostics.append(dict(task_index=index, task=episode['task'], actual_first_port=first,
            source_first_port=expected_first, failure=failure, terminal=episode['terminal_reason'],
            routes=episode['routes'], actor_commands=[trace['response'].get('raw') if isinstance(trace['response'], dict)
                else None for trace in episode['traces'] if trace['kind'] == 'actor']))
    return dict(master=world['master'], condition=condition, collection_sha256=collection['collection_sha256'],
        shared_text_sha256=goal.document_sha256(store), summary=summary, tasks=diagnostics)


def evaluate(inputs, generate, output):
    panels = dict(TRAIN=[], PROBE=[])
    references = []
    collections = inputs['exposure']['collections']
    require(tuple(collection['master'] for collection in collections) == goal.MASTERS, 'fixed_breadth_readout_worlds_required')
    for collection in collections:
        master = collection['master']
        split = 'TRAIN' if master in goal.TRAIN_MASTERS else 'PROBE'
        masters = goal.TRAIN_MASTERS if split == 'TRAIN' else goal.PROBE_MASTERS
        world_index = masters.index(master)
        conditions = ('OWN_TEXT',) if split == 'TRAIN' else collector.CONDITIONS
        for condition in conditions:
            panel = evaluate_goal_world(collection, condition, generate, output, split, world_index)
            panels[split].append(panel)
            source.write(output / f'{split}_{world_index}_{condition}_SUMMARY.json', panel)
        if split == 'PROBE':
            reference = dict(master=collection['master'], **first_port_reference(collection))
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
        denominator=4, worlds=primary_worlds, individual=dict(correct=sum(panel['summary']['individual']['correct']
            for panel in panels['PROBE'] if panel['condition'] == 'OWN_TEXT'), denominator=8))
    checks = dict(probe_pairs=primary['correct'] >= 3, each_probe_world=all(world['correct'] >= 1 for world in primary_worlds),
        old_w0=retention['0']['correct'] >= 15, old_w8=retention['8']['correct'] >= 15,
        audit=audited['summary']['overall']['correct'] >= 15, taught=taught['OWN_TEXT']['correct'] >= 3,
        previous_fresh=fresh['OWN_TEXT']['correct'] >= 3)
    result = dict(panels=panels, primary=primary, deterministic_first_port=references, old_recall=retention,
        held_audit=audited['summary'], taught_graph=taught, previous_fresh_graph=fresh,
        baseline=inputs['baseline']['panels'], engineering_checks=checks, engineering_target_met=all(checks.values()),
        interpretation='REPORT_ALL_COUNTS_REQUIRES_ARM_COMPARISON_NOT_AUTOMATIC_PROMOTION', claim=CLAIM)
    source.write(output / 'SUMMARY.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--lesson-root', default=memory.transfer.LESSON_ROOT)
    parser.add_argument('--transfer-root', default=memory.TRANSFER_ROOT)
    parser.add_argument('--collection-root', default='/tmp/astra_goal_breadth_collection_20260914_attempt1')
    parser.add_argument('--prior-collection-root', default=collector.PRIOR_COLLECTION_ROOT)
    parser.add_argument('--phase', choices=('prepare', 'train', 'after'), required=True)
    parser.add_argument('--arm', choices=ARMS)
    parser.add_argument('--training')
    parser.add_argument('--gpu-uuid')
    options = parser.parse_args(argv)
    require((options.phase == 'prepare' and options.arm is None) or options.arm in ARMS, 'goal_phase_arm_required')
    require(bool(options.training) == (options.phase == 'after'), 'saved_training_only_for_after')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or bool(options.gpu_uuid)
            and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output).resolve()
    for name in ('collection_root', 'prior_collection_root', 'lesson_root', 'transfer_root', 'base_after', 'campaign', 'audit_root', 'repair_root', 'cycle_root', 'training'):
        value = getattr(options, name)
        if value:
            reference = Path(value).resolve()
            require(output != reference and reference not in output.parents, 'reference_output_overlap_forbidden')
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, arm=options.arm, arguments=vars(options), started_unix=started,
        fits=0, updates=0, trainingAllowed=options.phase == 'train', automatic_training=False, parent_present=False,
        model_calls=0, max_native_calls=384 if options.phase == 'after' else 0, max_context=2048, max_new_tokens=160,
        protocol=goal.PROTOCOL, protocol_sha256=PROTOCOL_SHA, entry_sha256=source.file_hash(__file__), claim=CLAIM)
    source.write(output / 'REQUEST.json', result)
    engine, captures, cap_hit = None, [], False

    def check(label):
        require(time.time() < started + (7200 if options.phase == 'train' else 3600), 'goal_fit_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result['binding'] = inputs['binding']
        source.write(output / 'INPUTS.json', inputs['binding'])
        if options.phase == 'prepare':
            source.write(output / 'TRAINING_ROWS.json', inputs['material'])
            source.write(output / 'RECIPES.json', {arm: recipe(arm) for arm in ARMS})
            result.update(status='PREPARED_NO_MODEL', row_count=414, new_actual_train_targets=192,
                probe_training_rows=0, tokenization='VALIDATED_IN_TRAIN_BEFORE_GRADIENT', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return result
        arguments = argparse.Namespace(**inputs['arguments'])
        state = PARENT_STATE
        arguments.phase, arguments.device, arguments.gpu_uuid = 'readout', 'cuda:0', options.gpu_uuid
        arguments.adapter_dir = inputs['parent']['trained_adapter_dir']
        files = inputs['parent']['trained_adapter_files']
        if options.phase == 'after':
            trained, result['training_result_sha256'] = read_training(options.training, inputs, options.arm)
            state, files = trained['adapter_state_after'], trained['adapter_files']
            arguments.adapter_dir = str(Path(options.training) / 'adapter')
        engine = source.Engine(arguments, source.native.load_local_tokenizer(arguments.model_dir), check=check)
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
            result.update(train(engine, inputs, output, options.arm))
        else:
            result.update(evaluate(inputs, generate, output))
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
            model_calls=len(captures), role_calls=dict(Counter(capture['role'] for capture in captures)), finished_unix=time.time())
        if options.phase == 'after':
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
