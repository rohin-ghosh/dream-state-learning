"""One DEV parent-free adult experience/write cycle, not an H2 slope study."""

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


def read_adult_collection(directory, initial_receipt):
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    require(result.get('status') == 'COLLECTION_COMPLETE' and result.get('schema') == SCHEMA
            and result.get('initial_training_result_sha256') == initial_receipt
            and result.get('frozen_base_unchanged') is True, 'same_child_complete_adult_collection_required')
    require(not (directory / 'FAILED.json').exists(), 'failed_adult_collection_forbidden')
    require(source.file_hash(directory / 'COLLECTION.json') == result['collection_sha256'], 'adult_collection_changed')
    record = source.read(directory / 'COLLECTION.json')
    rows = adult.replay_collection(record)
    require(len(rows) == 32, 'four_grounded_adult_events_required')
    return record, rows, dict(path=str(directory), result_sha256=source.file_hash(directory / 'RESULT.json'),
                             collection_sha256=result['collection_sha256'])


def training_batch(encoded, update, cue_count, arm):
    indexes = adult.adult_indexes(update, cue_count)
    batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
    if arm == 'CUE_LOSS_OFF':
        batch['labels'][1] = [-100] * len(batch['labels'][1])
    original, active, scale = development.loss_normalization(encoded, indexes, batch)
    return indexes, batch, original, active, scale


def train(engine, old_rows, cue_rows, new_rows, output, arm):
    from organism_v6.pcfl_vertical_train import _state_hash

    torch = engine.torch
    encoded = source.encode_rows(old_rows, engine.tokenizer) + cue_material.encode_cue_rows(cue_rows, engine.tokenizer)
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
            indexes, batch, original, active, scale = training_batch(encoded, update, len(cue_rows), arm)
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
        new_memory_presentations=800, supervised_tokens=active_tokens, original_supervised_tokens=original_tokens,
        adapter_state_before=before, adapter_state_after=after, optimizer='FRESH_ADAMW',
        adapter_files={path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()})


def evaluate(engine, collection, old_bank, old_episodes, output, *, reader_wrapper=8):
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
        result['panels']['OLD_RECALL_W%d' % view] = dict(denominator=4, correct=sum(row['correct'] for row in rows), rows=rows)
    result['model_calls'] += 8
    require(result['model_calls'] <= 84, 'adult_readout_call_cap')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('collect', 'train', 'readout'), required=True)
    parser.add_argument('--state', choices=('BEFORE', 'AFTER'), default='BEFORE')
    parser.add_argument('--development-arm', choices=development.TRAINING_ARMS, required=True)
    for name in ('model-dir', 'expected-base-sha256', 'initial-adapter-dir', 'expected-initial-adapter-sha256',
                 'collection', 'cue-collection', 'output', 'gpu-uuid'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--adult-collection')
    parser.add_argument('--adapter-dir')
    parser.add_argument('--reader-wrapper', type=int, choices=(0, 8), default=8)
    parser.add_argument('--device', default='cuda:0')
    args = parser.parse_args(argv)
    require(args.state == 'BEFORE' or args.phase == 'readout', 'after_only_for_fresh_readout')
    require(args.phase == 'readout' or args.reader_wrapper == 8, 'reader_variant_only_for_readout')
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
        arguments=vars(args).copy(), started_unix=started, master=adult.MASTER,
        claim='SINGLE_ADULT_CYCLE_EXOGENOUS_EXPOSURE_NOT_H2_SLOPE_OR_AUTONOMOUS_SELECTION',
        runner_sha256=source.file_hash(__file__), material_sha256=source.file_hash(adult.__file__))
    source.write(output / 'REQUEST.json', result)

    def check(label):
        require(time.time() < started + seconds, 'adult_deadline:' + label)

    try:
        old_bank, old_episodes, old_rows, memory_source = source.load_collection(args.collection, serialization='FINAL_LF_ONLY')
        cue_rows, cue_source = cue_material.load_cue_rows(args.cue_collection, expected_actor_sha256=access.ADAPTER_SHA256)
        initial_receipt = development.check_second_sleep(args.initial_adapter_dir, memory_source, cue_source,
                                                        training_arm=args.development_arm, train_seed=0)
        require(source.file_hash(Path(args.initial_adapter_dir) / 'adapter_model.safetensors')
                == args.expected_initial_adapter_sha256, 'selected_development_artifact_required')
        initial = source.read(Path(args.initial_adapter_dir).parent / 'RESULT.json')
        development.validate_base_sources(args.expected_base_sha256, initial,
            source.read(Path(args.collection) / 'RESULT.json'), source.read(Path(args.cue_collection) / 'RESULT.json'))
        result.update(initial_training_result_sha256=initial_receipt, memory_source=memory_source, cue_source=cue_source)
        collection = new_rows = None
        if phase != 'collect':
            collection, new_rows, adult_source = read_adult_collection(args.adult_collection, initial_receipt)
            development.validate_base_sources(args.expected_base_sha256,
                                               source.read(Path(args.adult_collection) / 'RESULT.json'))
            result['adult_source'] = adult_source
        if args.state == 'AFTER':
            trained = source.read(Path(args.adapter_dir).parent / 'RESULT.json')
            require(trained.get('schema') == SCHEMA and trained.get('status') == 'COMPLETE'
                    and trained.get('phase') == 'train' and trained.get('updates') == UPDATES
                    and trained.get('initial_training_result_sha256') == initial_receipt
                    and trained.get('development_arm') == args.development_arm
                    and trained.get('adult_source') == result['adult_source']
                    and trained.get('frozen_base_unchanged') is True, 'completed_same_adult_training_required')
            require(not (Path(args.adapter_dir).parent / 'FAILED.json').exists(), 'failed_adult_fit_forbidden')
            for name, digest in trained['adapter_files'].items():
                require(Path(name).name == name and source.file_hash(Path(args.adapter_dir) / name) == digest,
                        'adult_saved_adapter_drift')
            development.validate_base_sources(args.expected_base_sha256, trained)
        else:
            args.adapter_dir = args.initial_adapter_dir
        args.phase = 'readout'
        tokenizer = source.native.load_local_tokenizer(args.model_dir)
        result['tokenizer'] = source.native.tokenizer_signature(tokenizer)
        if phase == 'train':
            source.encode_rows(old_rows, tokenizer)
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
            collection = adult.collect(engine.generate)
            source.write(output / 'COLLECTION.json', collection)
            result.update(collection_sha256=source.file_hash(output / 'COLLECTION.json'),
                          accepted_events=collection['accepted_events'], model_calls=len(collection['captures']))
            require(collection['infrastructure_failures'] == 0, 'adult_collection_infrastructure_failure')
        elif phase == 'train':
            result.update(train(engine, old_rows, cue_rows, new_rows, output, args.development_arm))
        else:
            result.update(evaluate(engine, collection, old_bank, old_episodes, output,
                                   reader_wrapper=args.reader_wrapper))
        engine.verify_base()
        if phase != 'train':
            require(_state_hash(parameters) == before, 'read_only_adult_stage_changed_adapter')
        require(source.file_hash(Path(args.initial_adapter_dir).parent / 'RESULT.json') == initial_receipt
                and source.file_hash(Path(args.initial_adapter_dir) / 'adapter_model.safetensors')
                == args.expected_initial_adapter_sha256, 'initial_child_artifact_changed')
        result.update(status=('COLLECTION_COMPLETE' if result['accepted_events'] == 4 else 'COLLECTION_INCOMPLETE_NO_FIT')
                      if phase == 'collect' else 'COMPLETE', frozen_base_unchanged=True, finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
