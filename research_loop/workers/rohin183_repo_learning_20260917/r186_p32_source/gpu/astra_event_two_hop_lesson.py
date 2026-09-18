"""Bounded coached EVENT trajectories, one sleep, and parent-free continuation."""

import argparse
from dataclasses import asdict
from pathlib import Path
import os
import time

from gpu import astra_event_two_hop as prior
from organism_v6 import experienced_event_two_hop_lesson as lesson


source = prior.source
require = source.require
SCHEMA = 'DEV_EVENT_TWO_HOP_TRAJECTORY_LESSON_V1'
CLAIM = 'ONE_EXPOSED_GRAPH_COACHED_INTERFACE_SFT_NOT_UNSEEN_WORLD_OR_H1_H2'
UPDATES = 100


def load_inputs(options):
    arguments, parent = prior.load_parent(options)
    collection, collection_sha = prior.read_collection(options.event_collection, parent)
    baseline_path = Path(options.baseline)
    require(not (baseline_path / 'FAILED.json').exists(), 'failed_two_hop_baseline')
    baseline = source.read(baseline_path / 'RESULT.json')
    require(baseline.get('status') == 'COMPLETE' and baseline.get('schema') == prior.SCHEMA
            and baseline.get('phase') == 'readout' and baseline.get('fits') == 0
            and baseline.get('arguments', {}).get('protocol') == 'turnbound'
            and baseline.get('source') == parent
            and baseline.get('collection_result_sha256') == collection_sha
            and baseline.get('adapter_state_after') == prior.PARENT_STATE
            and baseline.get('loaded_adapter_state_sha256') == prior.PARENT_STATE
            and baseline.get('frozen_base_unchanged') is True, 'same_parent_turnbound_baseline_required')
    previous = prior.previous.load_parent(options)
    fresh_collection, fresh_rows, unused_digest = prior.previous.read_collection(Path(options.cycle_root) / 'collect', previous)
    memory = previous['memory_rows'] + fresh_rows
    old_bank = previous['old_bank'] + fresh_collection['bank']
    old_episodes = previous['old_episodes'] + fresh_collection['episodes']
    require(len(memory) == 128 and len(old_bank) == len(old_episodes) == 16, 'all_sixteen_old_facts_required')
    binding = dict(parent=parent, collection_result_sha256=collection_sha,
        baseline_result_sha256=source.file_hash(baseline_path / 'RESULT.json'),
        memory_rows_sha256=source.native._digest(memory), cue_rows_sha256=source.native._digest(previous['cue_rows']),
        audit_rows_sha256=source.native._digest(previous['lesson_rows']),
        lesson_helper_sha256=source.file_hash(lesson.__file__), actor_helper_sha256=source.file_hash(prior.task.__file__))
    return dict(arguments=arguments, binding=binding, collection=collection, memory_rows=memory,
        cue_rows=previous['cue_rows'], audit_rows=previous['lesson_rows'], old_bank=old_bank,
        old_episodes=old_episodes, held_audit=previous['held'])


def read_lessons(directory, binding):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_trajectory_collection')
    result = source.read(directory / 'RESULT.json')
    require(result.get('schema') == SCHEMA and result.get('phase') == 'collect'
            and result.get('status') == 'COMPLETE' and result.get('binding') == binding
            and result.get('fits') == 0 and result.get('loaded_adapter_state_sha256') == prior.PARENT_STATE
            and result.get('adapter_state_after') == prior.PARENT_STATE
            and result.get('frozen_base_unchanged') is True, 'own_coached_collection_required')
    document = source.read(directory / 'LESSONS.json')
    require(source.file_hash(directory / 'LESSONS.json') == result.get('lessons_sha256'), 'lesson_file_drift')
    rows = lesson.replay_lessons(document)
    require(document['ready'] and len(rows) == result['model_calls'] == 12, 'both_complete_trajectories_required')
    require(len(list(directory.glob('CALL_*.json'))) == 12, 'coached_native_call_inventory')
    require(len(document['captures']) == 12, 'coached_capture_inventory')
    for index, capture in enumerate(document['captures']):
        saved = source.read(directory / ('CALL_%03d.json' % index))
        require(saved['messages'] == capture['messages'] and saved['response'] == capture['response']
                and saved['error'] is None and capture['error'] is None, 'coached_native_capture_drift')
    return rows, source.file_hash(directory / 'RESULT.json')


def read_training(directory, binding, lessons_sha):
    directory = Path(directory)
    require(not (directory / 'FAILED.json').exists(), 'failed_trajectory_training')
    result = source.read(directory / 'RESULT.json')
    require(result.get('schema') == SCHEMA and result.get('phase') == 'train'
            and result.get('status') == 'COMPLETE' and result.get('binding') == binding
            and result.get('fits') == 1 and result.get('updates') == UPDATES
            and result.get('lessons_result_sha256') == lessons_sha
            and result.get('loaded_adapter_state_sha256') == prior.PARENT_STATE
            and result.get('adapter_state_after') != prior.PARENT_STATE
            and result.get('frozen_base_unchanged') is True, 'own_completed_trajectory_sleep_required')
    for field, folder in (('adapter_files', directory / 'adapter'), ('training_files', directory)):
        require(bool(result.get(field)), 'training_inventory_required')
        for name, digest in result[field].items():
            require(Path(name).name == name and source.file_hash(folder / name) == digest, 'saved_training_file_drift')
    return result, source.file_hash(directory / 'RESULT.json')


def training_indexes(update):
    require(type(update) is int and 1 <= update <= UPDATES, 'fixed_100_updates_required')
    offset = update - 1
    return (offset % 128, 128 + offset % 82, 210 + (2 * offset) % 12, 210 + (2 * offset + 1) % 12)


def train(engine, inputs, rows, output):
    from gpu import astra_experienced_event_cue_sleep as development
    from gpu import astra_reader_audit_lesson_train as masks
    from organism_v6 import experienced_event_cue_sleep as cues
    from organism_v6 import experienced_event_reader_audit_lesson as audit_lesson
    from organism_v6.pcfl_vertical_train import _state_hash

    require(tuple(map(len, (inputs['memory_rows'], inputs['cue_rows'], inputs['audit_rows'], rows)))
            == (128, 20, 62, 12), 'fixed_trajectory_mixture_required')
    encoded = tuple(source.encode_row(row['messages'], engine.tokenizer) for row in inputs['memory_rows'])
    encoded += tuple(cues.encode_cue_rows(inputs['cue_rows'], engine.tokenizer))
    encoded += tuple(audit_lesson.encode_rows(inputs['audit_rows'], engine.tokenizer))
    encoded += tuple(lesson.encode_rows(rows, engine.tokenizer))
    require(len(encoded) == 222, 'exact_222_encoded_rows_required')
    masks.validate_masks(encoded, engine.tokenizer.eos_token_id)
    source.write(output / 'TRAINING_ROWS.json', dict(memory_rows=inputs['memory_rows'], cue_rows=inputs['cue_rows'],
        audit_rows=inputs['audit_rows'], trajectory_rows=rows))
    source.write(output / 'MASKS.json', [asdict(row) for row in encoded])
    source.write(output / 'RECIPE.json', dict(updates=UPDATES, learning_rate=3e-5, optimizer='FRESH_ADAMW',
        seed=0, batch_size=4, loss='MEAN_CAUSAL_CE', schedule=[training_indexes(step) for step in range(1, UPDATES + 1)],
        group_sizes=[128, 20, 62, 12], trajectory_target_source='ACTUAL_COACHED_CHILD_COMMANDS_PARENT_HINTS_REMOVED'))
    parameters = development.enable_existing_adapter(engine)
    require(_state_hash(parameters) == prior.PARENT_STATE, 'initial_trajectory_parent_must_match')
    torch = engine.torch
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, **source.native.OPTIMIZER)
    torch.manual_seed(0)
    engine.model.train()
    tokens = 0
    doses = [0] * 12
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, UPDATES + 1):
            engine.check('trajectory_update')
            indexes = training_indexes(update)
            batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
            active = sum(label != -100 for labels in batch['labels'] for label in labels[1:])
            require(active > 0, 'positive_trajectory_labels_required')
            tensors = {name: torch.tensor(value, dtype=torch.long, device=engine.device) for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                loss = engine.model(**tensors, use_cache=False).loss
            require(bool(torch.isfinite(loss)) and loss.requires_grad, 'invalid_trajectory_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'invalid_trajectory_gradient')
            optimizer.step()
            require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()), 'nonfinite_trajectory_adapter')
            tokens += active
            for index in indexes[2:]:
                doses[index - 210] += 1
            stream.write(source.json.dumps(dict(update=update, row_indexes=indexes,
                active_label_count=active, loss=loss.item()), allow_nan=False) + '\n')
            stream.flush()
    state = _state_hash(parameters)
    require(state != prior.PARENT_STATE, 'trajectory_update_must_change_adapter')
    engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    adapter_files = {path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()}
    require('adapter_model.safetensors' in adapter_files, 'saved_trajectory_adapter_required')
    return dict(fits=1, updates=UPDATES, adapter_state_after=state, adapter_files=adapter_files,
        actual_supervised_tokens=tokens, trajectory_presentations=doses,
        training_files={name: source.file_hash(output / name) for name in
                        ('TRAINING_ROWS.json', 'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl')})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'gpu-uuid', 'event-collection', 'baseline', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--phase', choices=('prepare', 'collect', 'train', 'after'), required=True)
    parser.add_argument('--lessons')
    parser.add_argument('--training')
    options = parser.parse_args(argv)
    require(bool(options.lessons) == (options.phase in ('train', 'after'))
            and bool(options.training) == (options.phase == 'after'), 'trajectory_phase_arguments')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    cap = 12 if options.phase == 'collect' else 160 if options.phase == 'after' else 0
    result = dict(schema=SCHEMA, phase=options.phase, arguments=vars(options), started_unix=started,
        fits=0, model_calls=0, parent_present=options.phase == 'collect', claim=CLAIM,
        entry_sha256=source.file_hash(__file__), max_native_calls=cap, max_context=2048, max_new_tokens=160)
    source.write(output / 'REQUEST.json', result)
    captures = []

    def check(label):
        require(time.time() < started + (1800 if options.phase == 'collect' else 3500), 'trajectory_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result['binding'] = inputs['binding']
        source.write(output / 'INPUTS.json', inputs['binding'])
        rows = None
        state = prior.PARENT_STATE
        arguments = argparse.Namespace(**inputs['arguments'])
        arguments.phase, arguments.device = 'readout', 'cuda:0'
        arguments.gpu_uuid = options.gpu_uuid
        arguments.adapter_dir = inputs['binding']['parent']['adapter_dir']
        if options.phase in ('train', 'after'):
            rows, result['lessons_result_sha256'] = read_lessons(options.lessons, inputs['binding'])
        if options.phase == 'after':
            trained, result['training_result_sha256'] = read_training(options.training, inputs['binding'], result['lessons_result_sha256'])
            state = trained['adapter_state_after']
            arguments.adapter_dir = str(Path(options.training) / 'adapter')
        if options.phase == 'prepare':
            result.update(status='PREPARED_NO_MODEL', finished_unix=time.time())
            source.write(output / 'RESULT.json', result)
            return result
        tokenizer = source.native.load_local_tokenizer(arguments.model_dir)
        engine = source.Engine(arguments, tokenizer, check=check)
        from organism_v6.pcfl_vertical_train import _state_hash

        parameters = {name: parameter for name, parameter in engine.model.named_parameters()
                      if '.lora_A.' in name or '.lora_B.' in name}
        require(bool(parameters) and _state_hash(parameters) == state, 'mounted_trajectory_state_required')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=state)

        def generate(messages, *, role='coached_child', condition=None, task_index=None, adapter_off=False):
            from contextlib import nullcontext

            check('call')
            require(len(captures) < cap, 'trajectory_native_call_cap')
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
            document = lesson.collect_lessons(inputs['collection'], generate)
            source.write(output / 'LESSONS.json', document)
            result['lessons_sha256'] = source.file_hash(output / 'LESSONS.json')
            rows = lesson.replay_lessons(document)
            require(document['ready'] and len(rows) == len(captures) == 12, 'both_coached_trajectories_required')
        elif options.phase == 'train':
            result.update(train(engine, inputs, rows, output))
        else:
            result['panels'] = prior.evaluate(prior.task.build_world(), inputs['collection'], generate, output, protocol='turnbound')
            recalls = []
            for view in (0, 8):
                for index, (fact, episode) in enumerate(zip(inputs['old_bank'], inputs['old_episodes'])):
                    messages = [dict(role='system', content=source.world.MEMORY_SYSTEM),
                        dict(role='user', content=source.world.WRAPPERS[view].replace('{REQUEST}', 'READ EVENT ' + fact['event']))]
                    response = generate(messages, role='retention')
                    expected = source.material.canonical_event(episode['event']['raw'])
                    entry = dict(view=view, event=fact['event'], response=response, expected=expected,
                        correct=response['terminal'] and not response['truncated'] and response['raw'] == expected)
                    source.write(output / ('OLD_RECALL_W%d_%02d.json' % (view, index)), entry)
                    recalls.append(entry)
            result['retention'] = {str(view): dict(correct=sum(entry['correct'] for entry in recalls if entry['view'] == view),
                denominator=16) for view in (0, 8)}
            from organism_v6 import experienced_event_reader_audit_lesson as audit_lesson

            audited = audit_lesson.collect_cases(inputs['held_audit'], lambda messages: generate(messages, role='held_audit'), coached=False)
            source.write(output / 'HELD_AUDIT.json', audited)
            result['held_audit'] = audited['summary']
        require(not any(capture['error'] is not None for capture in captures), 'trajectory_native_error_retained')
        engine.verify_base()
        if options.phase != 'train':
            require(_state_hash(parameters) == state, 'readonly_trajectory_phase_changed_adapter')
            files = trained['adapter_files'] if options.phase == 'after' else inputs['binding']['parent']['parent_adapter_files']
            require(all(source.file_hash(Path(arguments.adapter_dir) / name) == digest for name, digest in files.items()),
                    'readonly_trajectory_adapter_files_changed')
            result['adapter_state_after'] = state
        result.update(status='COMPLETE', model_calls=len(captures), frozen_base_unchanged=True, finished_unix=time.time())
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), model_calls=len(captures), finished_unix=time.time())
        source.write(output / 'FAILED.json', result)
        raise


if __name__ == '__main__':
    main()
