"""DEV second sleep: the saved learner's cue actions plus its old EVENT replay."""

import argparse
from contextlib import nullcontext
from dataclasses import asdict
import os
from pathlib import Path
import time

from gpu import astra_experienced_event_microloop as source
from gpu import astra_experienced_event_read_route as access
from gpu import astra_experienced_event_cue_collect as collector
from organism_v6 import experienced_event_cue_sleep as material
from organism_v6 import experienced_event_read_route as controller


SCHEMA = 'DEV_SAME_ADAPTER_CUE_SECOND_SLEEP_V1'
HELD_MASTER = 'ASTRA-CUE-SECOND-SLEEP-HELD-20260914-A1'
UPDATES = 200
TRAINING_ARMS = ('CUE_REPLAY', 'CUE_LOSS_OFF')
TRAIN_SEEDS = (0, 1, 2)
require = source.require


def validate_training_choice(training_arm, train_seed):
    require(training_arm in TRAINING_ARMS, 'known_training_arm_required')
    require(type(train_seed) is int and train_seed in TRAIN_SEEDS, 'known_train_seed_required')


def recorded_training_choice(result):
    training_arm = result.get('training_arm', 'CUE_REPLAY')
    train_seed = result.get('train_seed', 0)
    validate_training_choice(training_arm, train_seed)
    arguments = result.get('arguments', {})
    require(arguments.get('training_arm', training_arm) == training_arm
            and type(arguments.get('train_seed', train_seed)) is int
            and arguments.get('train_seed', train_seed) == train_seed, 'recorded_training_choice_mismatch')
    return training_arm, train_seed


def training_batch(encoded, update, cue_count, pad_id, training_arm='CUE_REPLAY'):
    validate_training_choice(training_arm, 0)
    indexes = material.mixed_indexes(update, cue_count)
    batch = source.native.collate([encoded[index] for index in indexes], pad_id=pad_id)
    if training_arm == 'CUE_LOSS_OFF':
        batch['labels'][2:] = [[-100] * len(labels) for labels in batch['labels'][2:]]
    return indexes, batch


def supervised_token_count(batch):
    return sum(label != -100 for labels in batch['labels'] for label in labels)


def loss_normalization(encoded, indexes, batch):
    require(all(encoded[index].labels[0] == -100 for index in indexes)
            and all(labels[0] == -100 for labels in batch['labels']), 'first_causal_label_must_be_masked')
    original = sum(label != -100 for index in indexes for label in encoded[index].labels[1:])
    active = sum(label != -100 for labels in batch['labels'] for label in labels[1:])
    require(0 < active <= original, 'positive_matched_loss_denominator_required')
    return original, active, active / original


def validate_base_sources(expected, *receipts):
    require(bool(receipts) and all(receipt.get('arguments', {}).get('expected_base_sha256') == expected
                                  for receipt in receipts), 'same_frozen_base_across_stages_required')


def stage_seconds(phase):
    require(phase in ('prepare', 'train', 'readout'), 'known_phase_required')
    return 3600 if phase == 'train' else 1800


def enable_existing_adapter(engine):
    selected = {}
    for name, parameter in engine.model.named_parameters():
        trainable = '.lora_A.' in name or '.lora_B.' in name
        parameter.requires_grad_(trainable)
        if trainable:
            require(parameter.dtype == engine.torch.float32, 'fp32_existing_lora_required')
            selected[name] = parameter
    require(bool(selected), 'existing_adapter_required')
    engine.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    engine.model.enable_input_require_grads()
    engine.model.config.use_cache = False
    return selected


def train(engine, memory_rows, cue_rows, output, *, training_arm='CUE_REPLAY', train_seed=0):
    from organism_v6.pcfl_vertical_train import _state_hash

    validate_training_choice(training_arm, train_seed)
    torch = engine.torch
    encoded = source.encode_rows(memory_rows, engine.tokenizer) + material.encode_cue_rows(cue_rows, engine.tokenizer)
    parameters = enable_existing_adapter(engine)
    before = _state_hash(parameters)
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, **source.native.OPTIMIZER)
    torch.manual_seed(train_seed)
    engine.model.train()
    supervised_tokens = 0
    original_supervised_tokens = 0
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, UPDATES + 1):
            engine.check('second_sleep_update')
            indexes, batch = training_batch(encoded, update, len(cue_rows),
                                           engine.tokenizer.pad_token_id, training_arm)
            original_count, active_count, loss_scale = loss_normalization(encoded, indexes, batch)
            tensors = {name: torch.tensor(value, dtype=torch.long, device=engine.device)
                       for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                loss = engine.model(**tensors, use_cache=False).loss
                if training_arm == 'CUE_LOSS_OFF':
                    loss = loss * loss_scale
            require(bool(torch.isfinite(loss)) and loss.requires_grad, 'invalid_second_sleep_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'invalid_second_sleep_gradient')
            optimizer.step()
            supervised_tokens += active_count
            original_supervised_tokens += original_count
            stream.write(source.json.dumps(dict(update=update, loss=loss.item(), row_indexes=indexes,
                original_label_count=original_count, active_label_count=active_count, loss_scale=loss_scale)) + '\n')
            stream.flush()
    require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()), 'nonfinite_adapter')
    after = _state_hash(parameters)
    require(after != before, 'no_parameter_update')
    engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    return dict(updates=UPDATES, memory_presentations=400, cue_presentations=400,
        training_arm=training_arm, train_seed=train_seed, cue_forward_presentations=400,
        cue_supervised_presentations=400 if training_arm == 'CUE_REPLAY' else 0,
        supervised_tokens=supervised_tokens, actual_supervised_tokens=supervised_tokens,
        original_supervised_tokens=original_supervised_tokens,
        loss_normalization='ORIGINAL_UNMASKED_BATCH_CAUSAL_LABEL_COUNT',
        adapter_state_before=before, adapter_state_after=after,
        optimizer='FRESH_ADAMW_NOT_PREVIOUS_OPTIMIZER_RESUME', learning_rate=3e-5,
        adapter_files={path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()})


def check_second_sleep(adapter_dir, memory_source, cue_source, *, training_arm=None, train_seed=None):
    adapter = Path(adapter_dir)
    result = source.read(adapter.parent / 'RESULT.json')
    recorded_arm, recorded_seed = recorded_training_choice(result)
    require((training_arm is None or training_arm == recorded_arm)
            and (train_seed is None or type(train_seed) is int and train_seed == recorded_seed),
            'requested_training_choice_mismatch')
    require(result.get('schema') == SCHEMA and result.get('status') == 'COMPLETE'
            and result.get('phase') == 'train' and result.get('updates') == UPDATES
            and result.get('frozen_base_unchanged') is True
            and result.get('memory_source') == memory_source and result.get('cue_source') == cue_source
            and result.get('initial_artifact_sha256') == 'c42010e12efed8a06c1e98901f09d576cf0c568175e837fa66255138e3c8a40f',
            'complete_second_sleep_required')
    require(not (adapter.parent / 'FAILED.json').exists(), 'failed_second_sleep_forbidden')
    for name, digest in result['adapter_files'].items():
        require(Path(name).name == name and source.file_hash(adapter / name) == digest, 'second_sleep_file_drift')
    return source.file_hash(adapter.parent / 'RESULT.json')


def evaluate(engine, bank, episodes, output, *, reader_wrapper=8):
    require(type(reader_wrapper) is int and reader_wrapper in (0, 8), 'known_reader_wrapper_required')
    captures, panels = [], {}

    def generate(messages, panel, role, *, reader_off=False):
        require(len(captures) < 76, 'readout_call_cap')
        with engine.model.disable_adapter() if reader_off else nullcontext():
            generation = engine.generate(messages)
        captures.append(dict(panel=panel, role=role, reader_adapter_disabled=reader_off, generation=generation))
        source.write(output / ('CALL_%03d.json' % len(captures)), captures[-1])
        return generation

    def run_bank(facts, panel, external_memory=None, *, reader_off=False):
        records = []

        def reader(address):
            if external_memory is not None:
                return dict(raw=external_memory[address], terminal=True, truncated=False,
                            source='RESEARCHER_SUPPLIED_EVAL_TEXT_NOT_PARAMETRIC_MEMORY')
            messages = [dict(role='system', content=source.world.MEMORY_SYSTEM),
                        dict(role='user', content=source.world.WRAPPERS[reader_wrapper].replace('{REQUEST}', 'READ EVENT ' + address))]
            return generate(messages, panel, 'reader', reader_off=reader_off)

        for fact in facts:
            transitions = {other['port']: other['outcome'] for other in facts if other['node'] == fact['node']}
            episode = controller.run_episode(controller.public_task(fact),
                lambda messages: generate(messages, panel, 'actor'), reader, lambda port: transitions[port])
            records.append(dict(event=fact['event'], episode=episode))
            source.write(output / (panel + '_EPISODE_%02d.json' % len(records)), records[-1])
            require(not episode['terminal_reason'].endswith(('_callback_error', '_invalid_response', '_non_json_response'))
                    and episode['terminal_reason'] not in ('transition_error', 'invalid_outcome'),
                    'readout_infrastructure_failure')
        panels[panel] = dict(denominator=len(facts), reached_goal=sum(row['episode']['reached_goal'] for row in records),
            with_reads=sum(row['episode']['memory_calls'] > 0 for row in records),
            second_reads=sum(row['episode']['memory_calls'] == 2 for row in records), episodes=records)

    run_bank(bank, 'OWN_PARAMETRIC')
    run_bank(bank, 'OWN_READER_OFF', reader_off=True)
    excluded = {fact[key] for fact in bank for key in ('world', 'event', 'node', 'port', 'outcome', 'receipt')}
    excluded.update(fact[key] for training_bank in collector.training_banks() for fact in training_bank
                    for key in ('world', 'event', 'node', 'port', 'outcome', 'receipt'))
    for index in range(2):
        facts = source.material.build_bank(HELD_MASTER + '-' + str(index))
        identifiers = {fact[key] for fact in facts for key in ('world', 'event', 'node', 'port', 'outcome', 'receipt')}
        require(not excluded.intersection(identifiers), 'held_identity_overlap')
        excluded.update(identifiers)
        run_bank(facts, 'HELD_TEXT_%d' % index,
                 {fact['event']: source.material._event(fact) for fact in facts})
    for wrapper in (0, 8):
        rows = []
        for fact, episode in zip(bank, episodes):
            messages = [dict(role='system', content=source.world.MEMORY_SYSTEM),
                        dict(role='user', content=source.world.WRAPPERS[wrapper].replace('{REQUEST}', 'READ EVENT ' + fact['event']))]
            response = generate(messages, 'RECALL_W%d' % wrapper, 'memory_probe')
            expected = source.material.canonical_event(episode['event']['raw'])
            rows.append(dict(event=fact['event'], correct=response.get('terminal') is True
                and response.get('truncated') is False and response['raw'] == expected,
                expected=expected, generation=response))
        panels['RECALL_W%d' % wrapper] = dict(denominator=4, correct=sum(row['correct'] for row in rows), rows=rows)
    rows = []
    for fact in source.material.build_bank(source.MASTER + '-UNSEEN-MISS'):
        messages = [dict(role='system', content=source.world.MEMORY_SYSTEM),
                    dict(role='user', content=source.world.WRAPPERS[8].replace('{REQUEST}', 'READ EVENT ' + fact['event']))]
        response = generate(messages, 'UNSEEN_MISS', 'memory_probe')
        rows.append(dict(correct=response.get('terminal') is True and response.get('truncated') is False
                         and response['raw'] == 'MISS\n', generation=response))
    panels['UNSEEN_MISS'] = dict(denominator=4, correct=sum(row['correct'] for row in rows), rows=rows)
    source.write(output / 'PANELS.json', panels)
    return dict(panels=panels, model_calls=len(captures), fits=0, parent_present=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('prepare', 'train', 'readout'), required=True)
    for name in ('model-dir', 'expected-base-sha256', 'adapter-dir', 'collection', 'cue-collection', 'output', 'gpu-uuid'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--state', choices=('SLEEP1', 'SLEEP2'), default='SLEEP1')
    parser.add_argument('--device', default='cuda:0')
    parser.add_argument('--training-arm', choices=TRAINING_ARMS, default='CUE_REPLAY')
    parser.add_argument('--train-seed', type=int, choices=TRAIN_SEEDS, default=0)
    args = parser.parse_args(argv)
    require(args.phase == 'readout' or args.state == 'SLEEP1', 'train_from_selected_sleep1_only')
    require(os.environ.get('HF_HUB_OFFLINE') == '1' and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    if args.phase != 'prepare':
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == args.gpu_uuid, 'exact_gpu_required')
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    allowed_seconds = stage_seconds(args.phase)
    result = dict(schema=SCHEMA, phase=args.phase, state=args.state, arguments=vars(args).copy(),
        training_arm=args.training_arm, train_seed=args.train_seed,
        started_unix=started, held_master=HELD_MASTER, claim='SINGLE_SEED_DEV_SECOND_SLEEP_NOT_PARENTING_OR_H1_H2',
        runner_sha256=source.file_hash(__file__), source_sha256=source.file_hash(material.__file__))
    source.write(output / 'REQUEST.json', result)

    def check(phase):
        require(time.time() < started + allowed_seconds, 'deadline:' + phase)

    try:
        bank, episodes, memory_rows, provenance = source.load_collection(args.collection, serialization='FINAL_LF_ONLY')
        cue_rows, cue_provenance = material.load_cue_rows(args.cue_collection, expected_actor_sha256=access.ADAPTER_SHA256)
        result.update(memory_source=provenance, cue_source=cue_provenance)
        result['initial_artifact_sha256'] = (access.validate_adapter(args.adapter_dir, provenance)
            if args.state == 'SLEEP1' else check_second_sleep(args.adapter_dir, provenance, cue_provenance,
                training_arm=args.training_arm, train_seed=args.train_seed))
        validate_base_sources(args.expected_base_sha256,
            source.read(Path(args.cue_collection) / 'RESULT.json'),
            source.read(Path(args.collection) / 'RESULT.json'),
            source.read(Path(args.adapter_dir).parent / 'RESULT.json'))
        require(cue_provenance['actor_training_result_sha256']
                == 'c42010e12efed8a06c1e98901f09d576cf0c568175e837fa66255138e3c8a40f',
                'cue_rows_must_come_from_selected_sleep1')
        tokenizer = source.native.load_local_tokenizer(args.model_dir)
        result['tokenizer'] = source.native.tokenizer_signature(tokenizer)
        encoded = source.encode_rows(memory_rows, tokenizer) + material.encode_cue_rows(cue_rows, tokenizer)
        result.update(memory_rows=len(memory_rows), cue_rows=len(cue_rows),
                      max_context=max(len(row.input_ids) for row in encoded))
        source.write(output / 'TRAINING_ROWS.json', dict(memory=memory_rows, cue=cue_rows))
        source.write(output / 'MASKS.json', [asdict(row) for row in encoded])
        if args.phase == 'prepare':
            result.update(status='CPU_PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return
        phase = args.phase
        args.phase = 'readout'
        engine = source.Engine(args, tokenizer, check=check)
        result['runtime'] = engine.runtime
        from organism_v6.pcfl_vertical_train import _state_hash

        adapter_parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                              if '.lora_A.' in name or '.lora_B.' in name}
        require(bool(adapter_parameters), 'loaded_adapter_required')
        result['loaded_adapter_state_sha256'] = _state_hash(adapter_parameters)
        if args.state == 'SLEEP1':
            require(result['loaded_adapter_state_sha256'] == 'c08852cb6eb2c8bfa106cf2b7976fc5a2ba5f4cb06d79d53a3a3ac7222b865db',
                    'selected_initial_adapter_state_required')
        result.update(train(engine, memory_rows, cue_rows, output,
                            training_arm=args.training_arm, train_seed=args.train_seed) if phase == 'train'
                      else evaluate(engine, bank, episodes, output))
        engine.verify_base()
        if phase == 'readout':
            require(_state_hash(adapter_parameters) == result['loaded_adapter_state_sha256'], 'readout_changed_adapter')
        if args.state == 'SLEEP1':
            require(access.validate_adapter(args.adapter_dir, provenance) == result['initial_artifact_sha256'],
                    'source_adapter_changed')
        result.update(status='COMPLETE', frozen_base_unchanged=True, finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
