"""One matched-rehearsal trajectory-loss-off counterfactual, never a new SFT."""

import argparse
from contextlib import nullcontext
from dataclasses import asdict, replace
import os
from pathlib import Path
import time

from gpu import astra_event_two_hop as prior
from gpu import astra_event_two_hop_lesson as lesson_driver
from gpu import astra_event_two_hop_transfer as transfer
from gpu import astra_experienced_event_cue_sleep as development
from gpu import astra_reader_audit_lesson_train as masks
from organism_v6 import experienced_event_cue_sleep as cues
from organism_v6 import experienced_event_reader_audit_lesson as audit_lesson


source = prior.source
hop = prior.task
require = source.require
SCHEMA = 'DEV_EVENT_TWO_HOP_TRAJECTORY_LOSS_OFF_V1'
ARM = 'TRAJECTORY_LOSS_OFF'
REFERENCE_TOKENS = 8245
UPDATES = 100
CLAIM = 'MATCHED_WRITER_REHEARSAL_TRAJECTORY_GRADIENT_CONTROL_NOT_WHOLE_PARENTING_LIFE_OR_H1_H2'
TRAINING_FILES = ('TRAINING_ROWS.json', 'REFERENCE_MASKS.json', 'MASKS.json', 'RECIPE.json',
                  'PREFLIGHT.json', 'LOSSES.jsonl')


def normalized(value):
    return source.json.loads(source.json.dumps(value, allow_nan=False))


def control_masks(encoded):
    require(len(encoded) == 222, 'exact_222_reference_rows_required')
    return tuple(row if index < 210 else replace(row, labels=(-100,) * len(row.labels))
                 for index, row in enumerate(encoded))


def training_batch(encoded, update):
    indexes = lesson_driver.training_indexes(update)
    reference_batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
    controlled = control_masks(encoded)
    batch = source.native.collate([controlled[index] for index in indexes], pad_id=151643)
    require(batch['input_ids'] == reference_batch['input_ids']
            and batch['attention_mask'] == reference_batch['attention_mask']
            and batch['labels'][:2] == reference_batch['labels'][:2]
            and all(label == -100 for labels in batch['labels'][2:] for label in labels),
            'only_trajectory_labels_may_change')
    reference, active, scale = development.loss_normalization(encoded, indexes, batch)
    return indexes, batch, reference, active, scale


def validate_reference(rows, encoded, recipe, losses, trained):
    require(tuple(map(len, (rows['memory_rows'], rows['cue_rows'], rows['audit_rows'], rows['trajectory_rows'])))
            == (128, 20, 62, 12), 'exact_reference_row_groups_required')
    require(len(encoded) == 222, 'exact_222_reference_rows_required')
    masks.validate_masks(encoded, 151645)
    require(all(len(row.input_ids) <= 2048 and row.labels[0] == -100 for row in encoded),
            'untruncated_reference_masks_required')
    expected = dict(updates=UPDATES, learning_rate=3e-5, optimizer='FRESH_ADAMW', seed=0, batch_size=4,
        loss='MEAN_CAUSAL_CE', schedule=[list(lesson_driver.training_indexes(step)) for step in range(1, 101)],
        group_sizes=[128, 20, 62, 12], trajectory_target_source='ACTUAL_COACHED_CHILD_COMMANDS_PARENT_HINTS_REMOVED')
    require(recipe == expected, 'exact_reference_recipe_required')
    require(len(losses) == UPDATES, 'reference_100_updates_required')
    batches, doses = [], [0] * 222
    for update, saved in enumerate(losses, 1):
        indexes, unused_batch, reference, active, scale = training_batch(encoded, update)
        require(saved['update'] == update and saved['row_indexes'] == list(indexes)
                and saved['active_label_count'] == reference, 'reference_batch_token_or_schedule_drift')
        for index in indexes:
            doses[index] += 1
        batches.append(dict(update=update, row_indexes=list(indexes), reference_labels=reference,
                            active_control_labels=active, loss_scale=scale))
    total = sum(batch['reference_labels'] for batch in batches)
    require(total == trained.get('actual_supervised_tokens') == REFERENCE_TOKENS, 'reference_8245_tokens_required')
    require(trained.get('trajectory_presentations') == doses[210:], 'reference_trajectory_doses_required')
    return dict(batches=batches, row_presentations=doses, trajectory_supervised_presentations=[0] * 12,
        reference_tokens=total, active_control_tokens=sum(batch['active_control_labels'] for batch in batches),
        input_tokens_identical=True, common_labels_identical=True, teacher_hints_in_student_prefix=False,
        loss_normalization='CONTROL_MEAN_CE_TIMES_ACTIVE_CONTROL_OVER_FULL_REFERENCE_PER_BATCH')


def verify_episode_calls(directory, episode, cursor, *, condition, task_index, old):
    for trace in episode['traces']:
        if trace['kind'] not in ('actor', 'memory') or (trace['kind'] == 'memory' and not isinstance(trace['response'], dict)):
            continue
        saved = source.read(directory / ('CALL_%03d.json' % cursor))
        messages = trace['messages'] if trace['kind'] == 'actor' else prior.memory_messages(trace['address'])
        require(saved['call_index'] == cursor and saved['role'] == trace['kind']
                and saved['condition'] == condition and saved['task_index'] == task_index
                and saved['messages'] == messages and saved['response'] == trace['response']
                and saved['error'] is None and trace['error'] is None, 'reference_native_call_drift')
        if old:
            require(saved['adapter_off'] == (condition == 'OFF_OWN_TEXT'), 'reference_adapter_mode_drift')
        cursor += 1
    return cursor


def verify_panels(directory, result, world, collection, *, old):
    conditions = prior.CONDITIONS if old else transfer.CONDITIONS
    require(set(result['panels']) == set(conditions), 'reference_condition_drift')
    tasks = hop.build_tasks(world)
    store = hop.exact_text_store(collection)
    cursor = 0
    for condition in conditions:
        panel = result['panels'][condition]
        entries = panel['episodes'] if old else panel['tasks']
        require(panel['denominator'] == len(entries) == 4, 'reference_four_tasks_required')
        scores = []
        for index, public_task in enumerate(tasks):
            entry = entries[index]
            path = directory / (('%s_EPISODE_%02d.json' % (condition, index)) if old
                                else ('EPISODE_%s_%02d.json' % (condition, index)))
            saved = source.read(path)
            episode = saved['episode'] if old else saved
            require(entry['task'] == public_task and episode['task'] == public_task
                    and episode.get('protocol') == 'turnbound', 'reference_task_prompt_compatibility_required')
            score = hop.score_episode(world, public_task, episode)
            require(entry['score'] == score and (not old or saved == entry), 'reference_score_drift')
            for trace in episode['traces']:
                if trace['kind'] == 'memory' and condition != 'ON_PARAMETRIC':
                    expected = 'MEMORY UNAVAILABLE' if 'UNAVAILABLE' in condition else store[trace['address']]
                    require(trace['response'] == expected, 'reference_shared_stimulus_drift')
            cursor = verify_episode_calls(directory, episode, cursor, condition=condition, task_index=index, old=old)
            scores.append(score)
        require(panel['correct'] == sum(score['correct'] for score in scores), 'reference_panel_score_drift')
    require(len(list(directory.glob('CALL_*.json'))) == result['model_calls']
            and (cursor <= result['model_calls'] if old else cursor == result['model_calls']), 'reference_call_inventory')


def load_inputs(options):
    original, reference, fresh_world = transfer.load_inputs(options)
    parent = reference['parent']
    root = Path(options.lesson_root)
    trained = source.read(root / 'train/RESULT.json')
    recorded = trained['binding']
    rows, lessons_sha = lesson_driver.read_lessons(root / 'collect', recorded)
    require(lessons_sha == reference['lessons_result_sha256'], 'actual_lesson_result_join')
    original_collection = Path(trained['arguments']['event_collection'])
    collection, collection_sha = prior.read_collection(original_collection, parent)
    require(collection_sha == recorded['collection_result_sha256']
            and source.file_hash(Path(trained['arguments']['baseline']) / 'RESULT.json') == recorded['baseline_result_sha256'],
            'original_collection_and_baseline_join')
    require(source.read(root / 'collect/LESSONS.json')['collection'] == collection, 'actual_lesson_source_collection_join')
    raw_rows = source.read(root / 'train/TRAINING_ROWS.json')
    previous = prior.previous.load_parent(options)
    current, fresh_rows, unused_digest = prior.previous.read_collection(Path(options.cycle_root) / 'collect', previous)
    expected = dict(memory_rows=previous['memory_rows'] + fresh_rows, cue_rows=previous['cue_rows'],
                    audit_rows=previous['lesson_rows'], trajectory_rows=rows)
    require(raw_rows == normalized(expected), 'same_actual_222_raw_rows_required')
    for key, field in (('memory_rows', 'memory_rows_sha256'), ('cue_rows', 'cue_rows_sha256'), ('audit_rows', 'audit_rows_sha256')):
        require(source.native._digest(raw_rows[key]) == recorded[field], 'recorded_rehearsal_rows_drift')
    saved_masks = source.read(root / 'train/MASKS.json')
    encoded = tuple(source.native.EncodedRow(**{key: tuple(value) for key, value in row.items()}) for row in saved_masks)
    recipe = source.read(root / 'train/RECIPE.json')
    losses = [source.json.loads(line) for line in (root / 'train/LOSSES.jsonl').read_text().splitlines()]
    preflight = validate_reference(raw_rows, encoded, recipe, losses, trained)
    old_after = source.read(root / 'after/RESULT.json')
    verify_panels(root / 'after', old_after, hop.build_world(), collection, old=True)
    transfer_root = Path(options.transfer_root)
    fresh_collection, fresh_sha = transfer.read_collection(transfer_root / 'collect', reference, fresh_world)
    readouts = {}
    shared_sha = hop.document_sha256(hop.exact_text_store(fresh_collection))
    for arm, state in (('TRAINED', transfer.TRAINED_STATE), ('ORIGINAL', prior.PARENT_STATE)):
        directory = transfer_root / arm
        receipt = source.read(directory / 'RESULT.json')
        require(not (directory / 'FAILED.json').exists() and receipt.get('schema') == transfer.SCHEMA
                and receipt.get('status') == 'COMPLETE' and receipt.get('phase') == 'readout'
                and receipt.get('arm') == arm and receipt.get('binding') == reference
                and receipt.get('fits') == 0 and receipt.get('trainingAllowed') is False
                and receipt.get('parent_present') is False and receipt.get('frozen_base_unchanged') is True
                and receipt.get('loaded_adapter_state_sha256') == receipt.get('adapter_state_after') == state
                and receipt.get('collection_result_sha256') == fresh_sha
                and receipt.get('shared_text_sha256') == shared_sha and receipt.get('model_calls', 49) <= 48,
                'completed_matched_transfer_arms_required')
        verify_panels(directory, receipt, fresh_world, fresh_collection, old=False)
        readouts[arm] = dict(result_sha256=source.file_hash(directory / 'RESULT.json'), panels=receipt['panels'])
    bank = previous['old_bank'] + current['bank']
    episodes = previous['old_episodes'] + current['episodes']
    require(len(bank) == len(episodes) == 16 and len(previous['held']['cases']) == 16,
            'all_sixteen_retention_and_audit_cases_required')
    binding = dict(reference=reference, raw_rows_sha256=source.file_hash(root / 'train/TRAINING_ROWS.json'),
        reference_masks_sha256=source.file_hash(root / 'train/MASKS.json'),
        reference_recipe_sha256=source.file_hash(root / 'train/RECIPE.json'),
        reference_training_files=trained['training_files'], reference_readouts=readouts,
        fresh_collection_result_sha256=fresh_sha, shared_text_sha256=shared_sha,
        held_audit_sha256=hop.document_sha256(previous['held']),
        old_episodes_sha256=hop.document_sha256(episodes), control_helper_sha256=source.file_hash(__file__),
        encoder_hashes={module.__name__: source.file_hash(module.__file__) for module in
            (lesson_driver.lesson, cues, audit_lesson, masks, development)})
    return dict(arguments=original, binding=binding, rows=raw_rows, encoded=encoded, preflight=preflight,
        collection=collection, fresh_collection=fresh_collection, fresh_world=fresh_world,
        old_bank=bank, old_episodes=episodes, held_audit=previous['held'], reference_old_panels=old_after['panels'])


def encode_reference(inputs, tokenizer):
    rows = inputs['rows']
    encoded = tuple(source.encode_row(row['messages'], tokenizer) for row in rows['memory_rows'])
    encoded += tuple(cues.encode_cue_rows(rows['cue_rows'], tokenizer))
    encoded += tuple(audit_lesson.encode_rows(rows['audit_rows'], tokenizer))
    encoded += tuple(lesson_driver.lesson.encode_rows(rows['trajectory_rows'], tokenizer))
    masks.validate_masks(encoded, tokenizer.eos_token_id)
    require(normalized([asdict(row) for row in encoded]) == normalized([asdict(row) for row in inputs['encoded']]),
            'reencoded_reference_masks_must_match_exactly')
    return encoded


def control_recipe(preflight):
    return dict(arm=ARM, updates=100, learning_rate=3e-5, seed=0, batch_size=4,
        optimizer='FRESH_ADAMW', optimizer_kwargs=source.native.OPTIMIZER, rank=8,
        loss_normalization=preflight['loss_normalization'],
        schedule=[list(lesson_driver.training_indexes(step)) for step in range(1, 101)],
        row_groups=[128, 20, 62, 12], masked_row_indexes=list(range(210, 222)))


def train(engine, inputs, output):
    from organism_v6.pcfl_vertical_train import _state_hash

    encoded = encode_reference(inputs, engine.tokenizer)
    controlled = control_masks(encoded)
    source.write(output / 'TRAINING_ROWS.json', inputs['rows'])
    source.write(output / 'REFERENCE_MASKS.json', [asdict(row) for row in encoded])
    source.write(output / 'MASKS.json', [asdict(row) for row in controlled])
    source.write(output / 'PREFLIGHT.json', inputs['preflight'])
    source.write(output / 'RECIPE.json', control_recipe(inputs['preflight']))
    parameters = development.enable_existing_adapter(engine)
    require(_state_hash(parameters) == prior.PARENT_STATE, 'control_initial_207_parent_required')
    torch = engine.torch
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, **source.native.OPTIMIZER)
    torch.manual_seed(0)
    engine.model.train()
    active_total, reference_total = 0, 0
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, 101):
            engine.check('control_update')
            indexes, batch, reference, active, scale = training_batch(encoded, update)
            require(dict(update=update, row_indexes=list(indexes), reference_labels=reference,
                active_control_labels=active, loss_scale=scale) == inputs['preflight']['batches'][update - 1],
                'pregradient_batch_drift')
            tensors = {name: torch.tensor(value, dtype=torch.long, device=engine.device) for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                mean_loss = engine.model(**tensors, use_cache=False).loss
                loss = mean_loss * scale
            require(bool(torch.isfinite(loss)) and loss.requires_grad, 'invalid_control_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'invalid_control_gradient')
            optimizer.step()
            require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()), 'nonfinite_control_adapter')
            active_total += active
            reference_total += reference
            stream.write(source.json.dumps(dict(update=update, row_indexes=indexes, active_control_labels=active,
                reference_labels=reference, loss_scale=scale, control_mean_loss=mean_loss.item(), loss=loss.item()),
                allow_nan=False) + '\n')
            stream.flush()
    state = _state_hash(parameters)
    require(state != prior.PARENT_STATE and reference_total == REFERENCE_TOKENS
            and active_total == inputs['preflight']['active_control_tokens'], 'completed_control_dose_required')
    engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    files = {path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()}
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(files), 'saved_control_adapter_required')
    return dict(fits=1, updates=100, adapter_state_after=state, adapter_files=files,
        actual_supervised_tokens=active_total, reference_supervised_tokens=reference_total,
        trajectory_presentations=inputs['preflight']['row_presentations'][210:],
        trajectory_supervised_presentations=[0] * 12,
        training_files={name: source.file_hash(output / name) for name in TRAINING_FILES})


def read_training(directory, inputs):
    directory = Path(directory)
    receipt = source.read(directory / 'RESULT.json')
    require(not (directory / 'FAILED.json').exists() and receipt.get('schema') == SCHEMA
            and receipt.get('phase') == 'train' and receipt.get('arm') == ARM and receipt.get('status') == 'COMPLETE'
            and receipt.get('binding') == inputs['binding'] and receipt.get('fits') == 1 and receipt.get('updates') == 100
            and receipt.get('loaded_adapter_state_sha256') == prior.PARENT_STATE
            and isinstance(receipt.get('adapter_state_after'), str)
            and len(receipt['adapter_state_after']) == 64 and all(character in '0123456789abcdef'
                for character in receipt['adapter_state_after']) and receipt['adapter_state_after'] != prior.PARENT_STATE
            and receipt.get('parent_present') is False and receipt.get('frozen_base_unchanged') is True
            and receipt.get('reference_supervised_tokens') == REFERENCE_TOKENS
            and receipt.get('actual_supervised_tokens') == inputs['preflight']['active_control_tokens']
            and receipt.get('trajectory_presentations') == inputs['preflight']['row_presentations'][210:]
            and receipt.get('trajectory_supervised_presentations') == [0] * 12, 'completed_own_control_training_required')
    require(set(receipt['training_files']) == set(TRAINING_FILES), 'control_training_inventory_required')
    transfer.verify_files(directory, receipt['training_files'])
    transfer.verify_files(directory / 'adapter', receipt['adapter_files'])
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(receipt['adapter_files']), 'control_adapter_inventory_required')
    require(source.read(directory / 'adapter/adapter_config.json').get('r') == 8, 'saved_rank_eight_required')
    require(source.read(directory / 'TRAINING_ROWS.json') == inputs['rows']
            and source.read(directory / 'REFERENCE_MASKS.json') == normalized([asdict(row) for row in inputs['encoded']])
            and source.read(directory / 'MASKS.json') == normalized([asdict(row) for row in control_masks(inputs['encoded'])])
            and source.read(directory / 'PREFLIGHT.json') == inputs['preflight']
            and source.read(directory / 'RECIPE.json') == normalized(control_recipe(inputs['preflight'])),
            'saved_control_inputs_and_masks_drift')
    losses = [source.json.loads(line) for line in (directory / 'LOSSES.jsonl').read_text().splitlines()]
    require(len(losses) == UPDATES and all(all(saved.get(key) == value for key, value in expected.items())
        for saved, expected in zip(losses, inputs['preflight']['batches'])), 'saved_control_dose_log_drift')
    return receipt, source.file_hash(directory / 'RESULT.json')


def evaluate(engine, inputs, generate, output):
    old_output, fresh_output = output / 'old', output / 'fresh'
    old_output.mkdir()
    fresh_output.mkdir()
    old = prior.evaluate(hop.build_world(), inputs['collection'], generate, old_output, protocol='turnbound')
    fresh = transfer.evaluate(inputs['fresh_world'], inputs['fresh_collection'], generate, fresh_output)
    recalls = []
    for view in (0, 8):
        for index, (fact, episode) in enumerate(zip(inputs['old_bank'], inputs['old_episodes'])):
            messages = [dict(role='system', content=source.world.MEMORY_SYSTEM), dict(role='user',
                content=source.world.WRAPPERS[view].replace('{REQUEST}', 'READ EVENT ' + fact['event']))]
            response = generate(messages, role='retention')
            expected = source.material.canonical_event(episode['event']['raw'])
            record = dict(view=view, event=fact['event'], response=response, expected=expected,
                correct=response['terminal'] and not response['truncated'] and response['raw'] == expected)
            source.write(output / ('OLD_RECALL_W%d_%02d.json' % (view, index)), record)
            recalls.append(record)
    audited = audit_lesson.collect_cases(inputs['held_audit'], lambda messages: generate(messages, role='held_audit'), coached=False)
    source.write(output / 'HELD_AUDIT.json', audited)
    result = dict(old_panels=old, fresh_panels=fresh,
        retention={str(view): dict(correct=sum(record['correct'] for record in recalls if record['view'] == view),
            denominator=16) for view in (0, 8)}, held_audit=audited['summary'],
        reference_old_panels=inputs['reference_old_panels'], reference_fresh=inputs['binding']['reference_readouts'],
        shared_text_sha256=inputs['binding']['shared_text_sha256'], claim=CLAIM)
    source.write(output / 'SUMMARY.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--lesson-root', default=transfer.LESSON_ROOT)
    parser.add_argument('--transfer-root', default='/tmp/astra_event_two_hop_transfer_20260914_attempt2')
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--phase', choices=('prepare', 'train', 'after'), required=True)
    parser.add_argument('--training')
    options = parser.parse_args(argv)
    require(bool(options.training) == (options.phase == 'after'), 'saved_training_only_for_after')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or bool(options.gpu_uuid)
            and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output).resolve()
    for directory in (options.lesson_root, options.transfer_root, options.cycle_root, options.base_after,
                      options.campaign, options.audit_root, options.repair_root, options.training):
        if directory:
            reference_path = Path(directory).resolve()
            require(output != reference_path and reference_path not in output.parents, 'reference_output_overlap_forbidden')
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    result = dict(schema=SCHEMA, phase=options.phase, arm=ARM, status='STARTED', arguments=vars(options),
        fits=0, updates=0, model_calls=0, parent_present=False, trainingAllowed=options.phase == 'train',
        max_native_calls=208 if options.phase == 'after' else 0, max_context=2048, max_new_tokens=160,
        started_unix=started, claim=CLAIM, reference_sft_rerun=False)
    source.write(output / 'REQUEST.json', result)
    captures = []
    engine = None

    def check(label):
        require(time.time() < started + 3600, 'control_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result['binding'] = inputs['binding']
        source.write(output / 'INPUTS.json', inputs['binding'])
        if options.phase == 'prepare':
            source.write(output / 'PREFLIGHT.json', inputs['preflight'])
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return result
        arguments = argparse.Namespace(**inputs['arguments'])
        parent = inputs['binding']['reference']['parent']
        state, files = prior.PARENT_STATE, parent['parent_adapter_files']
        arguments.phase, arguments.device, arguments.gpu_uuid = 'readout', 'cuda:0', options.gpu_uuid
        arguments.adapter_dir = parent['adapter_dir']
        if options.phase == 'after':
            trained, result['training_result_sha256'] = read_training(options.training, inputs)
            state, files = trained['adapter_state_after'], trained['adapter_files']
            arguments.adapter_dir = str(Path(options.training) / 'adapter')
        engine = source.Engine(arguments, source.native.load_local_tokenizer(arguments.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        require(bool(parameters) and _state_hash(parameters) == state, 'mounted_control_state_required')
        result.update(loaded_adapter_state_sha256=state, runtime=engine.runtime)

        def generate(messages, *, role='actor', condition=None, task_index=None, adapter_off=False):
            check('call')
            require(len(captures) < result['max_native_calls'], 'control_native_call_cap')
            capture = dict(call_index=len(captures), messages=messages, response=None, error=None,
                role=role, condition=condition, task_index=task_index, adapter_off=adapter_off)
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

        if options.phase == 'train':
            result.update(train(engine, inputs, output))
        else:
            result.update(evaluate(engine, inputs, generate, output))
            require(not any(capture['error'] is not None for capture in captures), 'control_native_errors_retained')
            require(_state_hash(parameters) == state, 'readonly_control_state_drift')
            result['adapter_state_after'] = state
        engine.verify_base()
        transfer.verify_files(arguments.adapter_dir, files)
        transfer.verify_files(arguments.model_dir, inputs['binding']['reference']['base_files'])
        transfer.verify_files(Path(options.lesson_root) / 'train', inputs['binding']['reference_training_files'])
        source.write(output / 'STATES.json', dict(before=state, after=_state_hash(parameters)))
        result.update(status='COMPLETE', frozen_base_unchanged=True, model_calls=len(captures), finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        if engine is not None:
            try:
                result['adapter_state_after'] = _state_hash({name: parameter for name, parameter in engine.model.named_parameters()
                    if '.lora_A.' in name or '.lora_B.' in name})
                engine.verify_base()
                transfer.verify_files(arguments.adapter_dir, files)
                transfer.verify_files(arguments.model_dir, inputs['binding']['reference']['base_files'])
            except BaseException as verification_error:
                result['failure_verification_error'] = repr(verification_error)
        result.update(status='FAILED', error=repr(error), model_calls=len(captures), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
