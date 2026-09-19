"""Up to two DEV parent-free adult cycles, not an H2 slope study."""

import argparse
from dataclasses import asdict
import os
from pathlib import Path
import time

from gpu import astra_experienced_event_cue_sleep as development
from gpu import astra_experienced_event_microloop as source
from gpu import astra_experienced_event_read_route as access
from organism_v6 import experienced_event_adult_cycle as adult
from organism_v6 import experienced_event_cue_sleep as cue_material


SCHEMA = 'DEV_PARENT_FREE_ADULT_CYCLE_V1'
UPDATES = 400
require = source.require


def read_adult_collection(directory, initial_receipt, *, cycle=1, prior_adult_source=None):
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    require(result.get('status') == 'COLLECTION_COMPLETE' and result.get('schema') == SCHEMA
            and result.get('initial_training_result_sha256') == initial_receipt
            and result.get('frozen_base_unchanged') is True, 'same_child_complete_adult_collection_required')
    require(not (directory / 'FAILED.json').exists(), 'failed_adult_collection_forbidden')
    require(result.get('cycle', 1) == cycle
            and result.get('master') == adult.master_for_cycle(cycle), 'adult_collection_cycle_mismatch')
    if cycle == 2:
        require(prior_adult_source is not None and result.get('prior_adult_source') == prior_adult_source,
                'prior_adult_collection_binding_required')
    require(source.file_hash(directory / 'COLLECTION.json') == result['collection_sha256'], 'adult_collection_changed')
    record = source.read(directory / 'COLLECTION.json')
    require(record.get('cycle', 1) == cycle, 'captured_adult_cycle_mismatch')
    rows = adult.replay_collection(record)
    require(len(rows) == 32, 'four_grounded_adult_events_required')
    return record, rows, dict(path=str(directory), result_sha256=source.file_hash(directory / 'RESULT.json'),
                             collection_sha256=result['collection_sha256'])


def check_adult_training(adapter_dir, *, cycle, arm, expected_base_sha256, memory_source,
                         cue_source, adult_source, initial_receipt=None, prior_adult_source=None):
    adapter = Path(adapter_dir)
    result = source.read(adapter.parent / 'RESULT.json')
    require(result.get('schema') == SCHEMA and result.get('status') == 'COMPLETE'
            and result.get('phase') == 'train' and result.get('updates') == UPDATES
            and type(result.get('cycle', 1)) is int and result.get('cycle', 1) == cycle
            and result.get('master') == adult.master_for_cycle(cycle)
            and result.get('development_arm') == arm and arm in development.TRAINING_ARMS
            and result.get('memory_source') == memory_source and result.get('cue_source') == cue_source
            and result.get('adult_source') == adult_source
            and result.get('frozen_base_unchanged') is True, 'completed_same_adult_training_required')
    require(type(result.get('initial_training_result_sha256')) is str
            and (initial_receipt is None or result['initial_training_result_sha256'] == initial_receipt),
            'adult_initial_receipt_mismatch')
    if cycle == 2:
        require(prior_adult_source is not None and result.get('prior_adult_source') == prior_adult_source,
                'prior_adult_training_binding_required')
    require(not (adapter.parent / 'FAILED.json').exists(), 'failed_adult_fit_forbidden')
    require('adapter_model.safetensors' in result.get('adapter_files', {}), 'adult_adapter_file_required')
    for name, digest in result['adapter_files'].items():
        require(Path(name).name == name and source.file_hash(adapter / name) == digest, 'adult_saved_adapter_drift')
    development.validate_base_sources(expected_base_sha256, result)
    return source.file_hash(adapter.parent / 'RESULT.json')


def load_cycle2_initial(adapter_dir, prior_directory, *, arm, expected_base_sha256, memory_source, cue_source):
    initial = source.read(Path(adapter_dir).parent / 'RESULT.json')
    require(type(initial.get('cycle', 1)) is int and initial.get('cycle', 1) == 1,
            'cycle2_requires_cycle1_initial')
    record, rows, provenance = read_adult_collection(prior_directory,
        initial.get('initial_training_result_sha256'), cycle=1)
    prior = source.read(Path(prior_directory) / 'RESULT.json')
    require(prior.get('memory_source') == memory_source and prior.get('cue_source') == cue_source
            and prior.get('development_arm') == arm, 'same_own_prior_adult_source_required')
    development.validate_base_sources(expected_base_sha256, prior)
    receipt = check_adult_training(adapter_dir, cycle=1, arm=arm,
        expected_base_sha256=expected_base_sha256, memory_source=memory_source,
        cue_source=cue_source, adult_source=provenance)
    return receipt, record, rows, provenance


def encode_old_rows(rows, tokenizer):
    require(len(rows) in (32, 64), 'exact_old_memory_layout_required')
    return tuple(encoded for offset in range(0, len(rows), 32)
                 for encoded in source.encode_rows(rows[offset:offset + 32], tokenizer))


def training_batch(encoded, update, cue_count, arm, *, old_count=32):
    indexes = adult.adult_indexes(update, cue_count, old_count=old_count)
    batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
    if arm == 'CUE_LOSS_OFF':
        batch['labels'][1] = [-100] * len(batch['labels'][1])
    original, active, scale = development.loss_normalization(encoded, indexes, batch)
    return indexes, batch, original, active, scale


def train(engine, old_rows, cue_rows, new_rows, output, arm):
    from organism_v6.pcfl_vertical_train import _state_hash

    torch = engine.torch
    encoded = encode_old_rows(old_rows, engine.tokenizer) + cue_material.encode_cue_rows(cue_rows, engine.tokenizer)
    encoded += source.encode_rows(new_rows, engine.tokenizer)
    require(engine.tokenizer.pad_token_id == 151643, 'fixed_native_pad_required')
    source.write(output / 'MASKS.json', [asdict(row) for row in encoded])
    parameters = development.enable_existing_adapter(engine)
    before = _state_hash(parameters)
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, **source.native.OPTIMIZER)
    torch.manual_seed(0)
    engine.model.train()
    active_tokens = original_tokens = 0
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, UPDATES + 1):
            engine.check('adult_update')
            indexes, batch, original, active, scale = training_batch(encoded, update, len(cue_rows), arm,
                                                                    old_count=len(old_rows))
            tensors = {name: torch.tensor(value, dtype=torch.long, device=engine.device) for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                loss = engine.model(**tensors, use_cache=False).loss
                if arm == 'CUE_LOSS_OFF':
                    loss = loss * scale
            require(bool(torch.isfinite(loss)) and loss.requires_grad, 'invalid_adult_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'invalid_adult_gradients')
            optimizer.step()
            active_tokens += active
            original_tokens += original
            stream.write(source.json.dumps(dict(update=update, row_indexes=indexes, loss=loss.item(),
                original_label_count=original, active_label_count=active, loss_scale=scale)) + '\n')
            stream.flush()
    after = _state_hash(parameters)
    require(after != before and all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()),
            'invalid_adult_adapter_state')
    engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    return dict(updates=UPDATES, old_memory_presentations=400, old_cue_presentations=400,
        old_fact_count=len(old_rows) // 8,
        new_memory_presentations=800, supervised_tokens=active_tokens, original_supervised_tokens=original_tokens,
        adapter_state_before=before, adapter_state_after=after, optimizer='FRESH_ADAMW',
        adapter_files={path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()})


def evaluate(engine, collection, old_bank, old_episodes, output, *, reader_wrapper=8):
    require(len(old_bank) in (4, 8) and len(old_episodes) == len(old_bank)
            and len({fact['event'] for fact in old_bank}) == len(old_bank)
            and all(episode['fact'] == fact for fact, episode in zip(old_bank, old_episodes)),
            'complete_distinct_old_retention_bank_required')
    directory = output / 'new_task'
    directory.mkdir(exist_ok=False)
    result = development.evaluate(engine, collection['bank'], collection['episodes'], directory,
                                  reader_wrapper=reader_wrapper)
    result['reader_wrapper'] = reader_wrapper
    for view in (0, 8):
        rows = []
        for fact, episode in zip(old_bank, old_episodes):
            messages = [dict(role='system', content=source.world.MEMORY_SYSTEM),
                        dict(role='user', content=source.world.WRAPPERS[view].replace('{REQUEST}', 'READ EVENT ' + fact['event']))]
            generation = engine.generate(messages)
            expected = source.material.canonical_event(episode['event']['raw'])
            rows.append(dict(event=fact['event'], generation=generation, expected=expected,
                correct=generation['terminal'] and not generation['truncated'] and generation['raw'] == expected))
            source.write(output / ('OLD_RECALL_W%d_%02d.json' % (view, len(rows))), rows[-1])
        result['panels']['OLD_RECALL_W%d' % view] = dict(denominator=len(old_bank), correct=sum(row['correct'] for row in rows), rows=rows)
    result['model_calls'] += 2 * len(old_bank)
    require(result['model_calls'] <= 76 + 2 * len(old_bank), 'adult_readout_call_cap')
    return result


def recollect(engine, collection, output, *, recipe='novelty_optional_v1'):
    from organism_v6 import experienced_event_sleep_recollection as recollection

    messages = recollection.build_messages(collection, recipe=recipe)
    source.write(output / 'SLEEP_PROMPT.json', messages)
    generation = engine.generate(messages, max_new_tokens=recollection.MAX_NEW_TOKENS)
    source.write(output / 'SLEEP_NOTE.json', generation)
    return dict(recollection_schema=recollection.SCHEMA, sleep_recipe=recipe, model_calls=1, fits=0,
        parent_present=False, training_admission='UNREVIEWED_NO_FIT',
        claim='TRACE_SUPPORTED_POSED_SLEEP_NOTE_NOT_LEARNED_SELECTION_OR_UTILITY',
        note_sha256=source.file_hash(output / 'SLEEP_NOTE.json'),
        terminal=generation['terminal'], truncated=generation['truncated'])


def load_recollection_revision(directory, collection, current, *, expected_adapter_state_sha256):
    from organism_v6 import experienced_event_sleep_recollection as recollection

    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_previous_recollection_forbidden')
    previous = source.read(directory / 'RESULT.json')
    request = source.read(directory / 'REQUEST.json')
    prompt = source.read(directory / 'SLEEP_PROMPT.json')
    note = source.read(directory / 'SLEEP_NOTE.json')
    require(all(type(document) is dict for document in (previous, request, note)) and type(prompt) is list,
            'previous_recollection_documents_required')
    require(previous.get('schema') == SCHEMA and previous.get('phase') == 'recollect'
            and previous.get('status') == 'RECOLLECTION_CAPTURED_NO_FIT'
            and previous.get('state') == 'BEFORE' and previous.get('sleep_recipe') == 'rehearsal_allowed_v2'
            and previous.get('recollection_schema') == recollection.SCHEMA
            and previous.get('parent_present') is False and previous.get('frozen_base_unchanged') is True
            and type(previous.get('fits')) is int and previous['fits'] == 0
            and type(previous.get('model_calls')) is int and previous['model_calls'] == 1
            and previous.get('training_admission') == 'UNREVIEWED_NO_FIT', 'previous_rehearsal_no_fit_required')
    for key in ('initial_training_result_sha256', 'adult_source', 'memory_source', 'cue_source',
                'development_arm', 'cycle', 'master'):
        require(key in current and previous.get(key) == current[key], 'previous_recollection_source_mismatch:' + key)
    require(previous.get('prior_adult_source') == current.get('prior_adult_source'),
            'previous_recollection_ancestor_mismatch')
    require(previous.get('loaded_adapter_state_sha256') == expected_adapter_state_sha256,
            'previous_recollection_actor_state_mismatch')
    arguments = previous.get('arguments', {})
    require(arguments.get('sleep_recipe') == 'rehearsal_allowed_v2'
            and arguments.get('phase') == 'recollect' and arguments.get('state') == 'BEFORE',
            'previous_rehearsal_arguments_required')
    for key in ('expected_base_sha256', 'expected_initial_adapter_sha256'):
        require(key in current['arguments'] and arguments.get(key) == current['arguments'][key],
                'previous_recollection_identity_mismatch:' + key)
    require(request.get('arguments') == arguments
            and all(request.get(key) == previous.get(key) for key in
                    ('schema', 'phase', 'state', 'cycle', 'master', 'development_arm', 'runner_sha256', 'material_sha256')),
            'previous_recollection_request_mismatch')
    require(source.file_hash(directory / 'SLEEP_NOTE.json') == previous.get('note_sha256'),
            'previous_recollection_note_hash_mismatch')
    require(previous.get('terminal') is True and previous.get('truncated') is False
            and note.get('terminal') is True and note.get('truncated') is False,
            'terminal_previous_recollection_required')
    require(prompt == recollection.build_messages(collection, recipe='rehearsal_allowed_v2')
            and note.get('messages') == prompt, 'exact_previous_rehearsal_prompt_required')
    messages = recollection.build_messages(collection, recipe='parental_revision_v1', previous_note=note)
    provenance = dict(directory=str(directory),
        source_files={name: source.file_hash(directory / name) for name in
                      ('RESULT.json', 'REQUEST.json', 'SLEEP_PROMPT.json', 'SLEEP_NOTE.json')},
        initial_training_result_sha256=previous['initial_training_result_sha256'],
        adult_source=previous['adult_source'], loaded_adapter_state_sha256=expected_adapter_state_sha256,
        prior_note_sha256=previous['note_sha256'], prior_whole_note_disposition='REJECTED_NOT_TRAINING_MATERIAL',
        feedback=recollection.PARENT_FEEDBACK,
        feedback_sha256=source.hashlib.sha256(recollection.PARENT_FEEDBACK.encode('utf-8')).hexdigest())
    return messages, provenance


def recollect_revision(engine, messages, output, provenance):
    from organism_v6 import experienced_event_sleep_recollection as recollection

    require(len(messages) == 4 and messages[-1] == dict(role='user', content=recollection.PARENT_FEEDBACK),
            'exact_parental_revision_feedback_required')
    source.write(output / 'SLEEP_PROMPT.json', messages)
    source.write(output / 'SLEEP_REVISION_SOURCE.json', provenance)
    generation = engine.generate(messages, max_new_tokens=recollection.MAX_NEW_TOKENS)
    source.write(output / 'SLEEP_NOTE.json', generation)
    require(generation.get('messages') == messages, 'revision_generation_prompt_mismatch')
    require(generation.get('terminal') is True and generation.get('truncated') is False,
            'terminal_untruncated_revision_required')
    return dict(recollection_schema=recollection.SCHEMA, sleep_recipe='parental_revision_v1', model_calls=1, fits=0,
        parent_present=True, training_admission='UNREVIEWED_NO_FIT',
        claim='PARENT_FEEDBACK_RESPONSIVENESS_ONLY_NOT_LEARNING_TRANSFER_OR_UTILITY',
        revision_source=provenance, note_sha256=source.file_hash(output / 'SLEEP_NOTE.json'),
        terminal=True, truncated=False)


def load_base_diagnostic_sources(directory, collection, current, *, expected_adapter_state_sha256):
    from organism_v6 import experienced_event_sleep_recollection as recollection

    messages, provenance = load_recollection_revision(directory, collection, current,
        expected_adapter_state_sha256=expected_adapter_state_sha256)
    revision_directory = Path(directory).parent / 'recollect_revision'
    require(not (revision_directory / 'FAILED.json').exists(), 'failed_on_revision_forbidden')
    revision = source.read(revision_directory / 'RESULT.json')
    note = source.read(revision_directory / 'SLEEP_NOTE.json')
    prompt = source.read(revision_directory / 'SLEEP_PROMPT.json')
    require(revision.get('schema') == SCHEMA and revision.get('phase') == 'recollect_revision'
            and revision.get('status') == 'RECOLLECTION_CAPTURED_NO_FIT' and revision.get('state') == 'BEFORE'
            and revision.get('sleep_recipe') == 'parental_revision_v1' and revision.get('parent_present') is True
            and type(revision.get('fits')) is int and revision['fits'] == 0
            and type(revision.get('model_calls')) is int and revision['model_calls'] == 1
            and revision.get('frozen_base_unchanged') is True
            and revision.get('training_admission') == 'UNREVIEWED_NO_FIT'
            and revision.get('loaded_adapter_state_sha256') == expected_adapter_state_sha256
            and revision.get('revision_source') == provenance, 'same_actor_on_revision_required')
    for key in ('initial_training_result_sha256', 'adult_source', 'memory_source', 'cue_source',
                'development_arm', 'cycle', 'master'):
        require(revision.get(key) == current[key], 'on_revision_source_mismatch:' + key)
    require(prompt == messages and note.get('messages') == messages, 'on_revision_prompt_mismatch')
    require(source.file_hash(revision_directory / 'SLEEP_NOTE.json') == revision.get('note_sha256'),
            'on_revision_note_hash_mismatch')
    require(revision.get('terminal') is True and revision.get('truncated') is False
            and note.get('terminal') is True and note.get('truncated') is False, 'terminal_on_revision_required')
    provenance = dict(provenance, on_revision_source=dict(directory=str(revision_directory),
        source_files={name: source.file_hash(revision_directory / name)
                      for name in ('RESULT.json', 'SLEEP_PROMPT.json', 'SLEEP_NOTE.json')}))
    return recollection.base_diagnostic_prompts(collection, messages), provenance


def recollect_base_diagnostic(engine, prompts, output, provenance):
    from organism_v6 import experienced_event_sleep_recollection as recollection
    from organism_v6.pcfl_vertical_train import _state_hash

    require(len(prompts) == 2 and [(item['name'], item['recipe'], item['parent_present']) for item in prompts]
            == [('SLEEP_BASE_REHEARSAL', 'rehearsal_allowed_v2', False),
                ('SLEEP_BASE_REVISION', 'parental_revision_v1', True)], 'fixed_two_base_diagnostic_conditions_required')
    modules = {name: module for name, module in engine.model.named_modules()
               if hasattr(module, 'lora_A') and hasattr(module, 'lora_B')}
    parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                  if '.lora_A.' in name or '.lora_B.' in name}
    require(bool(modules) and bool(parameters) and engine.model.training is False, 'loaded_eval_adapter_required')
    original_flags = {name: module.disable_adapters for name, module in modules.items()}
    require(all(value is False for value in original_flags.values()), 'initial_adapter_must_be_enabled')
    before = _state_hash(parameters)
    source.write(output / 'SLEEP_BASE_SOURCE.json', provenance)
    for item in prompts:
        source.write(output / (item['name'] + '_PROMPT.json'), item['messages'])
    records = {}
    try:
        with engine.model.disable_adapter():
            require(all(module.disable_adapters is True for module in modules.values()), 'adapter_off_context_required')
            for item in prompts:
                generation = engine.generate(item['messages'], max_new_tokens=recollection.MAX_NEW_TOKENS)
                source.write(output / (item['name'] + '.json'), generation)
                require(generation.get('messages') == item['messages'], 'base_diagnostic_prompt_drift')
                records[item['name']] = dict(sleep_recipe=item['recipe'], parent_present=item['parent_present'],
                    actor_mode='INFERENCE_ADAPTER_OFF', own_experience_actor=False,
                    training_admission='EXCLUDED_FROM_TRAINING', model_calls=1, fits=0,
                    note_sha256=source.file_hash(output / (item['name'] + '.json')),
                    prompt_sha256=source.file_hash(output / (item['name'] + '_PROMPT.json')),
                    terminal=generation.get('terminal'), truncated=generation.get('truncated'))
    finally:
        restored_flags = {name: module.disable_adapters for name, module in modules.items()}
        after = _state_hash(parameters)
        source.write(output / 'SLEEP_BASE_RESTORATION.json', dict(adapter_state_before=before,
            adapter_state_after=after, original_disabled_flags=original_flags, restored_disabled_flags=restored_flags))
        require(restored_flags == original_flags and after == before and engine.model.training is False,
                'base_diagnostic_adapter_not_restored')
    require(all(record['terminal'] is True and record['truncated'] is False for record in records.values()),
            'terminal_untruncated_base_diagnostic_required')
    return dict(recollection_schema=recollection.SCHEMA, actor_mode='INFERENCE_ADAPTER_OFF',
        own_experience_actor=False, training_admission='EXCLUDED_FROM_TRAINING', fits=0, model_calls=2,
        claim='ADAPTER_VS_PROMPT_FAILURE_DIAGNOSTIC_NOT_CHILD_MATERIAL_EFFICACY_OR_PARENTING_SUCCESS',
        diagnostic_source=provenance, diagnostic_panels=records,
        adapter_restored=True, adapter_state_before=before, adapter_state_after=after)


def load_correction_before(directory, collection, current, *, expected_adapter_state_sha256):
    from organism_v6 import experienced_event_corrective_replay as corrective

    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_correction_before_forbidden')
    pins = {}

    def read(name):
        path = directory / name
        document = source.read(path)
        pins[name] = source.file_hash(path)
        return document

    before, request = read('RESULT.json'), read('REQUEST.json')
    require(type(before) is dict and type(request) is dict and before.get('schema') == SCHEMA
            and before.get('status') == 'COMPLETE' and before.get('phase') == 'readout'
            and before.get('state') == 'BEFORE' and type(before.get('cycle')) is int and before['cycle'] == 2
            and before.get('development_arm') == 'CUE_REPLAY' and before.get('frozen_base_unchanged') is True
            and type(before.get('fits')) is int and before['fits'] == 0, 'complete_own_correction_before_required')
    for key in ('initial_training_result_sha256', 'adult_source', 'memory_source', 'cue_source',
                'prior_adult_source', 'prior_adult_training_result_sha256', 'cycle', 'master', 'development_arm'):
        require(key in current and before.get(key) == current[key], 'correction_before_source_mismatch:' + key)
    require(before.get('loaded_adapter_state_sha256') == expected_adapter_state_sha256,
            'correction_before_actor_state_mismatch')
    arguments = before.get('arguments', {})
    require(arguments.get('phase') == 'readout' and arguments.get('state') == 'BEFORE'
            and arguments.get('cycle') == 2 and arguments.get('development_arm') == 'CUE_REPLAY',
            'correction_before_arguments_mismatch')
    for key in ('expected_base_sha256', 'expected_initial_adapter_sha256'):
        require(key in current['arguments'] and arguments.get(key) == current['arguments'][key],
                'correction_before_identity_mismatch:' + key)
    require(type(before.get('reader_wrapper')) is int and before['reader_wrapper'] in (0, 8)
            and arguments.get('reader_wrapper') == before['reader_wrapper'], 'correction_before_reader_binding_mismatch')
    require(request.get('arguments') == arguments and all(request.get(key) == before.get(key) for key in
            ('schema', 'phase', 'state', 'cycle', 'master', 'development_arm', 'runner_sha256', 'material_sha256')),
            'correction_before_request_mismatch')
    panel = before.get('panels', {}).get('OWN_PARAMETRIC')
    require(type(panel) is dict and panel.get('denominator') == 4, 'four_before_own_tasks_required')
    require(read('new_task/PANELS.json').get('OWN_PARAMETRIC') == panel, 'correction_before_panel_drift')
    names = ['OWN_PARAMETRIC_EPISODE_%02d.json' % index for index in range(1, 5)]
    require(sorted(path.name for path in (directory / 'new_task').glob('OWN_PARAMETRIC_EPISODE_*.json')) == names,
            'complete_before_own_episode_inventory_required')
    records = [read('new_task/' + name) for name in names]
    require(records == panel.get('episodes'), 'correction_before_episode_drift')
    cases = corrective.prepare_cases(collection, records)
    require(cases['expected_calls'] == len(cases['cases']) <= corrective.MAX_CALLS,
            'bounded_correction_cases_required')
    provenance = dict(directory=str(directory), result_sha256=pins['RESULT.json'], source_files=pins,
        initial_training_result_sha256=before['initial_training_result_sha256'],
        loaded_adapter_state_sha256=expected_adapter_state_sha256, adult_source=before['adult_source'],
        reader_wrapper=before['reader_wrapper'], helper_sha256=source.file_hash(corrective.__file__),
        preparation_sha256=cases['preparation_sha256'])
    return cases, provenance


def select_corrective(engine, cases, output, provenance):
    from organism_v6 import experienced_event_corrective_replay as corrective

    require(cases['expected_calls'] == len(cases['cases']) <= corrective.MAX_CALLS,
            'bounded_correction_cases_required')
    source.write(output / 'CORRECTION_SOURCE.json', provenance)
    source.write(output / 'CORRECTION_CASES.json', cases)
    calls = []

    def generate(messages):
        index = len(calls)
        require(index < cases['expected_calls'] and index < corrective.MAX_CALLS,
                'corrective_callback_cap')
        require(messages == cases['cases'][index]['messages'], 'corrective_callback_prompt_order_drift')
        capture = dict(call_index=index, messages=adult._copy(messages), response=None, error=None)
        calls.append(capture)
        try:
            capture['response'] = engine.generate(messages, max_new_tokens=source.MAX_NEW_TOKENS)
            return capture['response']
        except Exception as error:
            capture['error'] = dict(type=type(error).__name__, message=str(error))
            raise
        finally:
            source.write(output / ('CALL_%03d.json' % index), capture)

    selection = corrective.collect_selection(cases, generate)
    require(selection['model_calls'] == len(calls) == cases['expected_calls'], 'corrective_call_count_mismatch')
    source.write(output / 'SELECTION.json', selection)
    return dict(corrective_schema=corrective.SCHEMA, model_calls=len(calls), fits=0, parent_present=False,
        own_experience_actor=True, task_denominator=4, selection_source=provenance,
        actual_wrong_goal_cases=cases['expected_calls'], admitted_selections=selection['admitted_selections'],
        selection_sha256=source.file_hash(output / 'SELECTION.json'),
        training_admission='SOURCE_VALID_SELECTION_ONLY_NO_FIT_AUTHORIZATION',
        claim='CHILD_EXTRACTION_UNDER_EXTERNALLY_POSED_CORRECTION_TASK_NOT_CORRECTION_EFFICACY')


def load_corrective_selection(directory, before_directory, collection, current, *, expected_adapter_state_sha256):
    from organism_v6 import experienced_event_corrective_replay as corrective

    cases, before_source = load_correction_before(before_directory, collection, current,
        expected_adapter_state_sha256=expected_adapter_state_sha256)
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_corrective_selection_forbidden')
    names = ['RESULT.json', 'REQUEST.json', 'CORRECTION_SOURCE.json', 'CORRECTION_CASES.json', 'SELECTION.json']
    documents = {name: source.read(directory / name) for name in names}
    result, request = documents['RESULT.json'], documents['REQUEST.json']
    require(result.get('schema') == SCHEMA and result.get('status') == 'SELECTION_CAPTURED_NO_FIT'
            and result.get('phase') == 'select_corrective' and result.get('state') == 'BEFORE'
            and result.get('fits') == 0 and result.get('parent_present') is False
            and result.get('frozen_base_unchanged') is True, 'completed_no_fit_selection_required')
    for key in ('initial_training_result_sha256', 'adult_source', 'memory_source', 'cue_source',
                'prior_adult_source', 'prior_adult_training_result_sha256', 'cycle', 'master', 'development_arm'):
        require(result.get(key) == current[key], 'corrective_selection_source_drift:' + key)
    require(result.get('loaded_adapter_state_sha256') == expected_adapter_state_sha256,
            'corrective_selection_actor_drift')
    arguments = result.get('arguments', {})
    require(arguments.get('phase') == 'select_corrective' and arguments.get('state') == 'BEFORE'
            and arguments.get('cycle') == 2 and arguments.get('development_arm') == 'CUE_REPLAY',
            'corrective_selection_arguments_drift')
    for key in ('expected_base_sha256', 'expected_initial_adapter_sha256'):
        require(arguments.get(key) == current['arguments'][key], 'corrective_selection_identity_drift:' + key)
    require(request.get('arguments') == arguments and all(request.get(key) == result.get(key) for key in
        ('schema', 'phase', 'state', 'cycle', 'master', 'development_arm', 'runner_sha256', 'material_sha256')),
        'corrective_selection_request_drift')
    require(documents['CORRECTION_SOURCE.json'] == before_source == result.get('selection_source')
            and documents['CORRECTION_CASES.json'] == cases, 'corrective_selection_before_drift')
    selection = documents['SELECTION.json']
    require(source.file_hash(directory / 'SELECTION.json') == result.get('selection_sha256'),
            'corrective_selection_hash_drift')
    count = cases['expected_calls']
    require(result.get('model_calls') == selection['model_calls'] == count
            and result.get('admitted_selections') == selection['admitted_selections']
            and result.get('actual_wrong_goal_cases') == count, 'corrective_selection_counts_drift')
    call_names = ['CALL_%03d.json' % index for index in range(count)]
    require(sorted(path.name for path in directory.glob('CALL_*.json')) == call_names,
            'corrective_selection_call_inventory_drift')
    for name, capture in zip(call_names, selection['captures']):
        require(source.read(directory / name) == {key: capture[key] for key in
                ('call_index', 'messages', 'response', 'error')}, 'corrective_selection_call_drift')
    require(len(selection['captures']) == count and all(capture['error'] is None for capture in selection['captures']),
            'all_selection_calls_must_succeed')
    captures = iter(selection['captures'])

    def replay(messages):
        capture = next(captures)
        require(capture['messages'] == messages, 'corrective_selection_prompt_drift')
        return adult._copy(capture['response'])

    require(corrective.collect_selection(cases, replay) == selection, 'corrective_selection_replay_drift')
    selected = selection['chosen_source_indexes']
    require(1 <= count <= 4 and selection['admitted_selections'] == count and len(selected) == count,
            'all_nonempty_cases_must_be_source_valid')
    require(len({selected.count(index) for index in range(4)}) > 1,
            'uniform_selection_has_no_sampling_contrast')
    return selected, dict(directory=str(directory), result_sha256=source.file_hash(directory / 'RESULT.json'),
        source_files={name: source.file_hash(directory / name) for name in names + call_names},
        before_source=before_source, selected_source_indexes=selected)


def check_corrective_training(adapter_dir, current, *, replay_arm, selected_source_indexes,
                              expected_adapter_state_sha256):
    from gpu import astra_corrective_sleep_train as corrective_train

    adapter = Path(adapter_dir)
    directory = adapter.parent
    result = source.read(directory / 'RESULT.json')
    require(not (directory / 'FAILED.json').exists() and result.get('schema') == SCHEMA
            and result.get('status') == 'COMPLETE' and result.get('phase') == 'train_corrective'
            and result.get('state') == 'BEFORE' and result.get('updates') == 100
            and result.get('fits') == 1 and result.get('train_seed') == 0
            and result.get('replay_arm') == replay_arm and replay_arm in corrective_train.REPLAY_ARMS
            and result.get('selected_source_indexes') == selected_source_indexes
            and result.get('frozen_base_unchanged') is True, 'completed_same_corrective_training_required')
    for key in ('initial_training_result_sha256', 'adult_source', 'memory_source', 'cue_source',
                'prior_adult_source', 'prior_adult_training_result_sha256', 'cycle', 'master',
                'development_arm', 'corrective_selection_source'):
        require(result.get(key) == current[key], 'corrective_training_source_drift:' + key)
    require(result.get('adapter_state_before') == result.get('loaded_adapter_state_sha256')
            == expected_adapter_state_sha256 and type(result.get('adapter_state_after')) is str
            and result['adapter_state_after'] != expected_adapter_state_sha256,
            'corrective_training_actor_drift')
    require(result.get('old_fact_count') == 8 and result.get('loss_normalization') == corrective_train.LOSS_NORMALIZATION
            and result.get('optimizer') == 'FRESH_ADAMW' and result.get('learning_rate') == 3e-5,
            'corrective_training_recipe_drift')
    arguments = result.get('arguments', {})
    require(arguments.get('phase') == 'train_corrective' and arguments.get('replay_arm') == replay_arm,
            'corrective_training_arguments_drift')
    for key in ('expected_base_sha256', 'expected_initial_adapter_sha256'):
        require(arguments.get(key) == current['arguments'][key], 'corrective_training_identity_drift:' + key)
    require(source.read(directory / 'REQUEST.json').get('arguments') == arguments, 'corrective_training_request_drift')
    development.validate_base_sources(current['arguments']['expected_base_sha256'], result)
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(result.get('adapter_files', {})),
            'corrective_adapter_files_required')
    for name, digest in result['adapter_files'].items():
        require(Path(name).name == name and source.file_hash(adapter / name) == digest, 'corrective_adapter_file_drift')
    artifacts = result.get('training_artifact_sha256', {})
    require(set(artifacts) == {'MASKS.json', 'SELECTION_LAYOUT.json', 'LOSSES.jsonl'}, 'corrective_training_artifacts_required')
    for name, digest in artifacts.items():
        require(source.file_hash(directory / name) == digest, 'corrective_training_artifact_drift')
    provenance = source.read(directory / 'ADAPTER_PROVENANCE.json')
    require(all(provenance.get(key) == result.get(key) for key in ('adapter_state_before', 'adapter_state_after',
        'adapter_files', 'runner_sha256', 'training_artifact_sha256')), 'corrective_adapter_provenance_drift')
    require(source.read(directory / 'SELECTION_LAYOUT.json') ==
            corrective_train.selection_layout(replay_arm, selected_source_indexes), 'corrective_training_layout_drift')
    masks = source.read(directory / 'MASKS.json')
    require(len(masks) == 116 and all(row['labels'][0] == -100 for row in masks), 'corrective_training_masks_drift')
    losses = [source.json.loads(line) for line in (directory / 'LOSSES.jsonl').read_text().splitlines()]
    require(len(losses) == 100, 'corrective_100_loss_rows_required')
    actual_total = reference_total = 0
    for update, row in enumerate(losses, 1):
        actual_indexes, reference_indexes = corrective_train.training_indexes(update, replay_arm, selected_source_indexes)
        actual = sum(label != -100 for index in actual_indexes for label in masks[index]['labels'][1:])
        reference = sum(label != -100 for index in reference_indexes for label in masks[index]['labels'][1:])
        require(row.get('update') == update and row.get('row_indexes') == list(actual_indexes)
                and row.get('reference_row_indexes') == list(reference_indexes)
                and actual > 0 and reference > 0 and row.get('actual_label_count') == row.get('active_label_count') == actual
                and row.get('reference_label_count') == row.get('original_label_count') == reference
                and row.get('loss_scale') == actual / reference, 'corrective_training_budget_drift')
        actual_total += actual
        reference_total += reference
    require(result.get('actual_supervised_tokens') == result.get('supervised_tokens') == actual_total
            and result.get('reference_supervised_tokens') == result.get('original_supervised_tokens') == reference_total,
            'corrective_training_token_totals_drift')
    budgets = dict(old_memory_presentations=100, old_cue_presentations=100, new_memory_presentations=200,
                   original_bank_presentations=64, first_adult_presentations=36)
    require(result.get('budgets') == budgets and all(result.get(key) == value for key, value in budgets.items()),
            'corrective_training_presentations_drift')
    return source.file_hash(directory / 'RESULT.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('collect', 'train', 'readout', 'recollect', 'recollect_revision',
                                           'recollect_base_diagnostic', 'select_corrective',
                                           'train_corrective', 'readout_corrective'), required=True)
    parser.add_argument('--state', choices=('BEFORE', 'AFTER'), default='BEFORE')
    parser.add_argument('--development-arm', choices=development.TRAINING_ARMS, required=True)
    for name in ('model-dir', 'expected-base-sha256', 'initial-adapter-dir', 'expected-initial-adapter-sha256',
                 'collection', 'cue-collection', 'output', 'gpu-uuid'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--adult-collection')
    parser.add_argument('--adapter-dir')
    parser.add_argument('--cycle', type=int, choices=(1, 2), default=1)
    parser.add_argument('--prior-adult-collection')
    parser.add_argument('--reader-wrapper', type=int, choices=(0, 8), default=8)
    parser.add_argument('--sleep-recipe', choices=('novelty_optional_v1', 'rehearsal_allowed_v2', 'parental_revision_v1'),
                        default='novelty_optional_v1')
    parser.add_argument('--previous-recollection')
    parser.add_argument('--correction-before')
    parser.add_argument('--corrective-selection')
    parser.add_argument('--replay-arm', choices=('CHILD_CORRECTIVE', 'UNIFORM_REPLAY'))
    parser.add_argument('--device', default='cuda:0')
    args = parser.parse_args(argv)
    corrective_phase = args.phase in ('train_corrective', 'readout_corrective')
    require((args.phase == 'select_corrective' or corrective_phase) == bool(args.correction_before), 'correction_before_only_for_selection')
    require(corrective_phase == bool(args.corrective_selection) == bool(args.replay_arm), 'explicit_corrective_selection_and_arm_required')
    require(not corrective_phase or (args.cycle == 2 and args.development_arm == 'CUE_REPLAY'
            and args.state == ('AFTER' if args.phase == 'readout_corrective' else 'BEFORE')),
            'corrective_collecting_a1_cycle2_forks_only')
    require(args.phase != 'readout_corrective' or args.reader_wrapper == 0, 'corrective_cold_readout_w0_required')
    require(args.phase != 'select_corrective' or (args.cycle == 2 and args.development_arm == 'CUE_REPLAY'
            and args.state == 'BEFORE'), 'collecting_a1_cue_actor_only_for_selection')
    require((args.cycle == 2) == bool(args.prior_adult_collection), 'prior_collection_only_required_for_cycle2')
    require(args.state == 'BEFORE' or args.phase in ('readout', 'readout_corrective'), 'after_only_for_fresh_readout')
    require(args.phase in ('readout', 'readout_corrective') or args.reader_wrapper == 8, 'reader_variant_only_for_readout')
    require((args.phase == 'recollect_revision') == (args.sleep_recipe == 'parental_revision_v1')
            and (args.phase in ('recollect_revision', 'recollect_base_diagnostic')) == bool(args.previous_recollection),
            'explicit_parental_revision_source_required')
    require(args.phase in ('recollect', 'recollect_revision') or args.sleep_recipe == 'novelty_optional_v1', 'sleep_recipe_only_for_recollection')
    require(args.phase == 'collect' or args.adult_collection, 'experienced_adult_source_required')
    require((args.state == 'AFTER') == bool(args.adapter_dir), 'explicit_after_adapter_only')
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == args.gpu_uuid, 'exact_gpu_required')
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    phase = args.phase
    started = time.time()
    seconds = 5400 if phase in ('train', 'train_corrective') else 1800
    result = dict(schema=SCHEMA, phase=phase, state=args.state, development_arm=args.development_arm,
        arguments=vars(args).copy(), started_unix=started, master=adult.master_for_cycle(args.cycle), cycle=args.cycle,
        claim=('SINGLE_ADULT_CYCLE_EXOGENOUS_EXPOSURE_NOT_H2_SLOPE_OR_AUTONOMOUS_SELECTION' if args.cycle == 1
               else 'SECOND_ADULT_CYCLE_EXOGENOUS_EXPOSURE_NOT_H2_SLOPE_OR_AUTONOMOUS_SELECTION'),
        runner_sha256=source.file_hash(__file__), material_sha256=source.file_hash(adult.__file__))
    if corrective_phase:
        result.update(replay_arm=args.replay_arm, parent_present=False,
            claim='CONDITIONAL_CHILD_SELECTED_VS_UNIFORM_REPLAY_DEV_NOT_AUTONOMOUS_SELECTION_OR_H2')
    if phase == 'recollect_revision':
        result.update(parent_present=True, fits=0, sleep_recipe='parental_revision_v1',
            training_admission='UNREVIEWED_NO_FIT',
            claim='PARENT_FEEDBACK_RESPONSIVENESS_ONLY_NOT_LEARNING_TRANSFER_OR_UTILITY')
    if phase == 'recollect_base_diagnostic':
        result.update(actor_mode='INFERENCE_ADAPTER_OFF', own_experience_actor=False, fits=0,
            training_admission='EXCLUDED_FROM_TRAINING',
            parent_present_by_panel=dict(SLEEP_BASE_REHEARSAL=False, SLEEP_BASE_REVISION=True),
            claim='ADAPTER_VS_PROMPT_FAILURE_DIAGNOSTIC_NOT_CHILD_MATERIAL_EFFICACY_OR_PARENTING_SUCCESS')
    if phase == 'select_corrective':
        result.update(parent_present=False, fits=0, own_experience_actor=True,
            training_admission='SOURCE_VALID_SELECTION_ONLY_NO_FIT_AUTHORIZATION',
            claim='CHILD_EXTRACTION_UNDER_EXTERNALLY_POSED_CORRECTION_TASK_NOT_CORRECTION_EFFICACY')
    source.write(output / 'REQUEST.json', result)

    def check(label):
        require(time.time() < started + seconds, 'adult_deadline:' + label)

    try:
        old_bank, old_episodes, old_rows, memory_source = source.load_collection(args.collection, serialization='FINAL_LF_ONLY')
        cue_rows, cue_source = cue_material.load_cue_rows(args.cue_collection, expected_actor_sha256=access.ADAPTER_SHA256)
        prior_adult_source = None
        if args.cycle == 1:
            initial_receipt = development.check_second_sleep(args.initial_adapter_dir, memory_source, cue_source,
                                                            training_arm=args.development_arm, train_seed=0)
        else:
            initial_receipt, prior_record, prior_rows, prior_adult_source = load_cycle2_initial(
                args.initial_adapter_dir, args.prior_adult_collection, arm=args.development_arm,
                expected_base_sha256=args.expected_base_sha256, memory_source=memory_source, cue_source=cue_source)
            old_bank = old_bank + prior_record['bank']
            old_episodes = old_episodes + prior_record['episodes']
            old_rows = old_rows + prior_rows
            result.update(prior_adult_source=prior_adult_source, prior_master=adult.MASTER,
                          prior_adult_training_result_sha256=initial_receipt)
        require(source.file_hash(Path(args.initial_adapter_dir) / 'adapter_model.safetensors')
                == args.expected_initial_adapter_sha256, 'selected_development_artifact_required')
        initial = source.read(Path(args.initial_adapter_dir).parent / 'RESULT.json')
        development.validate_base_sources(args.expected_base_sha256, initial,
            source.read(Path(args.collection) / 'RESULT.json'), source.read(Path(args.cue_collection) / 'RESULT.json'))
        result.update(initial_training_result_sha256=initial_receipt, memory_source=memory_source, cue_source=cue_source,
                      old_fact_count=len(old_bank), old_memory_rows=len(old_rows), new_fact_count=4)
        collection = new_rows = None
        if phase != 'collect':
            collection, new_rows, adult_source = read_adult_collection(args.adult_collection, initial_receipt,
                cycle=args.cycle, prior_adult_source=prior_adult_source)
            development.validate_base_sources(args.expected_base_sha256,
                                               source.read(Path(args.adult_collection) / 'RESULT.json'))
            result['adult_source'] = adult_source
        if phase == 'recollect_revision':
            revision_messages, revision_source = load_recollection_revision(args.previous_recollection,
                collection, result, expected_adapter_state_sha256=initial['adapter_state_after'])
            result['revision_source'] = revision_source
        if phase == 'recollect_base_diagnostic':
            diagnostic_prompts, diagnostic_source = load_base_diagnostic_sources(args.previous_recollection,
                collection, result, expected_adapter_state_sha256=initial['adapter_state_after'])
            result['diagnostic_source'] = diagnostic_source
        if phase == 'select_corrective':
            correction_cases, correction_source = load_correction_before(args.correction_before, collection, result,
                expected_adapter_state_sha256=initial['adapter_state_after'])
            result['selection_source'] = correction_source
        if corrective_phase:
            selected_indexes, selection_source = load_corrective_selection(args.corrective_selection,
                args.correction_before, collection, result, expected_adapter_state_sha256=initial['adapter_state_after'])
            result.update(corrective_selection_source=selection_source, selected_source_indexes=selected_indexes)
        if args.state == 'AFTER':
            if corrective_phase:
                result['corrective_training_result_sha256'] = check_corrective_training(args.adapter_dir, result,
                    replay_arm=args.replay_arm, selected_source_indexes=selected_indexes,
                    expected_adapter_state_sha256=initial['adapter_state_after'])
            else:
                check_adult_training(args.adapter_dir, cycle=args.cycle, arm=args.development_arm,
                    expected_base_sha256=args.expected_base_sha256, memory_source=memory_source, cue_source=cue_source,
                    adult_source=result['adult_source'], initial_receipt=initial_receipt,
                    prior_adult_source=prior_adult_source)
            trained = source.read(Path(args.adapter_dir).parent / 'RESULT.json')
        else:
            args.adapter_dir = args.initial_adapter_dir
        args.phase = 'readout'
        tokenizer = source.native.load_local_tokenizer(args.model_dir)
        result['tokenizer'] = source.native.tokenizer_signature(tokenizer)
        if phase == 'recollect_revision':
            prompt_ids = tokenizer.apply_chat_template(revision_messages, tokenize=True,
                add_generation_prompt=True, return_dict=False, truncation=False, padding=False)
            require(0 < len(prompt_ids) <= source.MAX_CONTEXT, 'revision_context_bound_exceeded_no_truncation')
            result['revision_prompt_tokens'] = len(prompt_ids)
        if phase == 'recollect_base_diagnostic':
            result['diagnostic_prompt_tokens'] = {}
            for item in diagnostic_prompts:
                prompt_ids = tokenizer.apply_chat_template(item['messages'], tokenize=True,
                    add_generation_prompt=True, return_dict=False, truncation=False, padding=False)
                require(0 < len(prompt_ids) <= source.MAX_CONTEXT, 'base_diagnostic_context_bound_exceeded_no_truncation')
                result['diagnostic_prompt_tokens'][item['name']] = len(prompt_ids)
        if phase == 'select_corrective':
            result['correction_prompt_tokens'] = []
            for case in correction_cases['cases']:
                prompt_ids = tokenizer.apply_chat_template(case['messages'], tokenize=True,
                    add_generation_prompt=True, return_dict=False, truncation=False, padding=False)
                require(0 < len(prompt_ids) <= source.MAX_CONTEXT, 'correction_context_bound_exceeded_no_truncation')
                result['correction_prompt_tokens'].append(len(prompt_ids))
        if phase == 'train':
            encode_old_rows(old_rows, tokenizer)
            source.encode_rows(new_rows, tokenizer)
            cue_material.encode_cue_rows(cue_rows, tokenizer)
            source.write(output / 'TRAINING_ROWS.json', dict(old_memory=old_rows, cue=cue_rows, new_memory=new_rows))
        engine = source.Engine(args, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        before = _state_hash(parameters)
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=before)
        require(bool(parameters) and before == (trained['adapter_state_after'] if args.state == 'AFTER'
                                               else initial['adapter_state_after']), 'loaded_expected_adult_state_required')
        if phase == 'collect':
            collection = adult.collect(engine.generate, cycle=args.cycle)
            source.write(output / 'COLLECTION.json', collection)
            result.update(collection_sha256=source.file_hash(output / 'COLLECTION.json'),
                          accepted_events=collection['accepted_events'], model_calls=len(collection['captures']))
            require(collection['infrastructure_failures'] == 0, 'adult_collection_infrastructure_failure')
        elif phase == 'train':
            result.update(train(engine, old_rows, cue_rows, new_rows, output, args.development_arm))
        elif phase == 'train_corrective':
            from gpu import astra_corrective_sleep_train as corrective_train

            result.update(corrective_train.train(engine, old_rows, cue_rows, new_rows, output,
                replay_arm=args.replay_arm, selected_source_indexes=selected_indexes), fits=1)
        elif phase == 'recollect':
            result.update(recollect(engine, collection, output, recipe=args.sleep_recipe))
        elif phase == 'recollect_revision':
            result.update(recollect_revision(engine, revision_messages, output, revision_source))
        elif phase == 'recollect_base_diagnostic':
            result.update(recollect_base_diagnostic(engine, diagnostic_prompts, output, diagnostic_source))
        elif phase == 'select_corrective':
            result.update(select_corrective(engine, correction_cases, output, correction_source))
        else:
            result.update(evaluate(engine, collection, old_bank, old_episodes, output,
                                   reader_wrapper=args.reader_wrapper))
        engine.verify_base()
        if phase not in ('train', 'train_corrective'):
            require(_state_hash(parameters) == before, 'read_only_adult_stage_changed_adapter')
        require(source.file_hash(Path(args.initial_adapter_dir).parent / 'RESULT.json') == initial_receipt
                and source.file_hash(Path(args.initial_adapter_dir) / 'adapter_model.safetensors')
                == args.expected_initial_adapter_sha256, 'initial_child_artifact_changed')
        status = 'COMPLETE'
        if phase == 'collect':
            status = 'COLLECTION_COMPLETE' if result['accepted_events'] == 4 else 'COLLECTION_INCOMPLETE_NO_FIT'
        elif phase in ('recollect', 'recollect_revision', 'recollect_base_diagnostic'):
            status = 'RECOLLECTION_CAPTURED_NO_FIT'
        elif phase == 'select_corrective':
            status = 'SELECTION_CAPTURED_NO_FIT'
        result.update(status=status, frozen_base_unchanged=True, finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
