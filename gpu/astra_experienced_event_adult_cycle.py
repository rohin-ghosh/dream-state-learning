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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('collect', 'train', 'readout', 'recollect', 'recollect_revision'), required=True)
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
    parser.add_argument('--device', default='cuda:0')
    args = parser.parse_args(argv)
    require((args.cycle == 2) == bool(args.prior_adult_collection), 'prior_collection_only_required_for_cycle2')
    require(args.state == 'BEFORE' or args.phase == 'readout', 'after_only_for_fresh_readout')
    require(args.phase == 'readout' or args.reader_wrapper == 8, 'reader_variant_only_for_readout')
    require((args.phase == 'recollect_revision') == (args.sleep_recipe == 'parental_revision_v1')
            and (args.phase == 'recollect_revision') == bool(args.previous_recollection), 'explicit_parental_revision_source_required')
    require(args.phase in ('recollect', 'recollect_revision') or args.sleep_recipe == 'novelty_optional_v1', 'sleep_recipe_only_for_recollection')
    require(args.phase == 'collect' or args.adult_collection, 'experienced_adult_source_required')
    require((args.state == 'AFTER') == bool(args.adapter_dir), 'explicit_after_adapter_only')
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == args.gpu_uuid, 'exact_gpu_required')
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    phase = args.phase
    started = time.time()
    seconds = 5400 if phase == 'train' else 1800
    result = dict(schema=SCHEMA, phase=phase, state=args.state, development_arm=args.development_arm,
        arguments=vars(args).copy(), started_unix=started, master=adult.master_for_cycle(args.cycle), cycle=args.cycle,
        claim=('SINGLE_ADULT_CYCLE_EXOGENOUS_EXPOSURE_NOT_H2_SLOPE_OR_AUTONOMOUS_SELECTION' if args.cycle == 1
               else 'SECOND_ADULT_CYCLE_EXOGENOUS_EXPOSURE_NOT_H2_SLOPE_OR_AUTONOMOUS_SELECTION'),
        runner_sha256=source.file_hash(__file__), material_sha256=source.file_hash(adult.__file__))
    if phase == 'recollect_revision':
        result.update(parent_present=True, fits=0, sleep_recipe='parental_revision_v1',
            training_admission='UNREVIEWED_NO_FIT',
            claim='PARENT_FEEDBACK_RESPONSIVENESS_ONLY_NOT_LEARNING_TRANSFER_OR_UTILITY')
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
        if args.state == 'AFTER':
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
        elif phase == 'recollect':
            result.update(recollect(engine, collection, output, recipe=args.sleep_recipe))
        elif phase == 'recollect_revision':
            result.update(recollect_revision(engine, revision_messages, output, revision_source))
        else:
            result.update(evaluate(engine, collection, old_bank, old_episodes, output,
                                   reader_wrapper=args.reader_wrapper))
        engine.verify_base()
        if phase != 'train':
            require(_state_hash(parameters) == before, 'read_only_adult_stage_changed_adapter')
        require(source.file_hash(Path(args.initial_adapter_dir).parent / 'RESULT.json') == initial_receipt
                and source.file_hash(Path(args.initial_adapter_dir) / 'adapter_model.safetensors')
                == args.expected_initial_adapter_sha256, 'initial_child_artifact_changed')
        status = 'COMPLETE'
        if phase == 'collect':
            status = 'COLLECTION_COMPLETE' if result['accepted_events'] == 4 else 'COLLECTION_INCOMPLETE_NO_FIT'
        elif phase in ('recollect', 'recollect_revision'):
            status = 'RECOLLECTION_CAPTURED_NO_FIT'
        result.update(status=status, frozen_base_unchanged=True, finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
