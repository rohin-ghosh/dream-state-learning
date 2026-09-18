"""One prospective strengthened-trajectory memory-writer engineering repair.

Reuse the complete reference BEFORE and terminal AFTER without generating new
material. Start the same 37ec parent, not the reference writer. Batch six adds
200 actual old trajectory presentations: increased budget, not equal-token
causal efficacy, a dose sweep, independent learners, or H1/H2 evidence.
"""

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import os
from pathlib import Path
import time

from gpu import astra_event_two_hop_memory as memory


source = memory.source
hop = memory.hop
require = memory.require
SCHEMA = 'DEV_EVENT_TWO_HOP_MEMORY_TRAJECTORY_REPLAY_V1'
CLAIM = 'ONE_INCREASED_BUDGET_ENGINEERING_REPAIR_NOT_EQUAL_TOKEN_CAUSAL_EFFICACY_OR_H1_H2'
REFERENCE_ROOT = '/tmp/astra_event_two_hop_memory_20260914_attempt1'
PARENT_STATE = memory.PARENT_STATE
UPDATES = 100
CAPS = dict(prepare=0, train=0, after=168)


def helpers():
    return dict(driver=source.file_hash(__file__),
        guard=source.file_hash(Path(__file__).with_name('astra_event_two_hop_memory_replay_guard.sh')),
        unchanged_memory_helpers=memory.helpers())


def training_indexes(update):
    base = memory.training_indexes(update)
    offset = update - 1
    return base + (210 + (2 * offset) % 12, 210 + (2 * offset + 1) % 12)


def recipe():
    return dict(updates=UPDATES, seed=0, optimizer='FRESH_ADAMW', learning_rate=3e-5,
        optimizer_kwargs=dict(source.native.OPTIMIZER), rank=8, batch_size=6,
        group_sizes=list(memory.GROUP_SIZES), group_order=list(memory.GROUPS), encoded_rows=254,
        loss='MEAN_CAUSAL_CE', actual_token_equality_claim=False, increased_budget=True,
        schedule=[list(training_indexes(update)) for update in range(1, UPDATES + 1)],
        presentations=dict(old_memory=100, cue=26, audit=62, trajectory=212, new_memory=200),
        extra_actual_trajectory_presentations=200, new_fact_presentations=[50] * 4,
        initial_state=PARENT_STATE, claim=CLAIM)


def collate_six(rows, *, pad_id):
    """Use the native right-padding rule, bounded to this six-row recipe."""
    require(len(rows) == 6, 'batch_six_required')
    width = max(len(row.input_ids) for row in rows)
    return dict(input_ids=[list(row.input_ids) + [pad_id] * (width - len(row.input_ids)) for row in rows],
                labels=[list(row.labels) + [-100] * (width - len(row.labels)) for row in rows],
                attention_mask=[[1] * len(row.input_ids) + [0] * (width - len(row.input_ids)) for row in rows])


def verify_graph(directory, inputs, result, calls, *, graph, collection, conditions, field):
    world, store = collection['world'], hop.exact_text_store(collection)
    panels = {}
    for condition in conditions:
        entries = []
        for index, task in enumerate(hop.build_tasks(world)):
            entry = source.read(directory / f'{graph}_{condition}_EPISODE_{index:02d}.json')
            score = memory.verify_episode_calls(entry['episode'], world, task, store, condition, calls, index, graph=graph)
            expected = dict(graph=graph, condition=condition, task_index=index, task=task,
                episode=entry['episode'], score=score, memory_origin=(
                    'ACTUAL_PARAMETRIC_RESPONSE_NO_FALLBACK' if condition == 'PARAMETRIC' else
                    'ACTUAL_CAPTURED_CHILD_TEXT' if condition == 'OWN_TEXT' else 'DECLARED_UNAVAILABLE_SERVICE'))
            memory.same(entry, expected, 'reference_episode_or_score_drift')
            entries.append(entry)
        panels[condition] = memory.panel(entries)
    memory.same(panels, result[field], 'reference_graph_panel_drift')


def verify_recall(directory, events, result, calls, label, field):
    entries = []
    for view in (0, 8):
        for index, event in enumerate(events):
            entry = source.read(directory / f'{label}_RECALL_W{view}_{index:02d}.json')
            call = next(calls, None)
            require(call is not None and call['role'] == label.lower() + '_recall' and call['graph'] == label
                    and call.get('condition') is None and call.get('task_index') is None, 'reference_recall_call_drift')
            expected = source.material.canonical_event(event['raw'])
            response = call['response']
            correct = (type(response) is dict and response.get('terminal') is True
                       and response.get('truncated') is False and response.get('raw') == expected)
            messages = memory.memory_messages(event['event'], view)
            memory.same(entry, dict(view=view, event=event['event'], messages=messages, expected=expected,
                        correct=correct, response=response, error=None), 'reference_recall_output_drift')
            memory.same(call['messages'], messages, 'reference_recall_prompt_drift')
            entries.append(entry)
    memory.same(result[field], {str(view): dict(correct=sum(entry['correct'] for entry in entries if entry['view'] == view),
        denominator=len(events)) for view in (0, 8)}, 'reference_recall_summary_drift')


def read_reference_after(directory, inputs, training, training_sha, before_sha):
    """Verify the entire reference terminal, including all readout/native joins."""
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    state = training['adapter_state_after']
    require(not (directory / 'FAILED.json').exists() and result.get('schema') == memory.SCHEMA
        and result.get('phase') == 'after' and result.get('status') == 'COMPLETE'
        and result.get('binding') == inputs['binding'] and result.get('before_result_sha256') == before_sha
        and result.get('training_result_sha256') == training_sha and result.get('fits') == result.get('updates') == 0
        and result.get('protocol') == 'turnbound' and result.get('parent_present') is False
        and result.get('loaded_adapter_state_sha256') == result.get('adapter_state_after') == state
        and result.get('frozen_base_unchanged') is True and result.get('max_native_calls') == 168,
        'full_completed_reference_after_required')
    memory.verify_output_files(directory, result)
    for name, expected in (('INPUTS.json', inputs['binding']), ('WORLD.json', inputs['world']),
            ('TASKS.json', hop.build_tasks(inputs['world'])), ('COLLECTION_SOURCE.json', inputs['collection']),
            ('NEW_ROWS.json', inputs['material']['new_rows']), ('STATES.json', dict(before=state, after=state))):
        memory.same(source.read(directory / name), expected, 'reference_readout_input_or_state_drift')
    captures = memory.read_calls(directory, result['model_calls'], 168)
    calls = iter(captures)
    verify_graph(directory, inputs, result, calls, graph='FRESH', collection=inputs['collection'],
                 conditions=memory.CONDITIONS, field='panels')
    events = [dict(event=record['edge']['event'], raw=record['event']['raw']) for record in inputs['collection']['records']]
    verify_recall(directory, events, result, calls, 'NEW', 'new_recall')
    events = [dict(event=fact['event'], raw=episode['event']['raw'])
              for fact, episode in zip(inputs['old_bank'], inputs['old_episodes'])]
    verify_recall(directory, events, result, calls, 'OLD', 'old_recall')

    def captured_audit(messages):
        call = next(calls, None)
        require(call is not None and call['role'] == 'held_audit' and call['graph'] == 'HELD'
                and call.get('condition') is None and call.get('task_index') is None, 'reference_audit_call_drift')
        memory.same(call['messages'], messages, 'reference_audit_prompt_drift')
        return deepcopy(call['response'])

    audited = memory.audit.collect_cases(inputs['held'], captured_audit, coached=False)
    memory.same(audited, source.read(directory / 'HELD_AUDIT.json'), 'reference_full_audit_drift')
    memory.same(audited['summary'], result['held_audit'], 'reference_audit_summary_drift')
    verify_graph(directory, inputs, result, calls, graph='TAUGHT', collection=inputs['original_collection'],
                 conditions=('OWN_TEXT',), field='taught_graph')
    require(next(calls, None) is None, 'unknown_reference_native_call')
    memory.same(result['role_calls'], dict(Counter(call['role'] for call in captures)), 'reference_native_role_count_drift')
    return result, source.file_hash(directory / 'RESULT.json')


def load_inputs(options):
    """Keep old bindings unchanged; reuse its exact BEFORE and saved 254 rows."""
    inputs = memory.load_inputs(options)
    root = Path(options.reference_root)
    before, before_sha = memory.read_before(root / 'before', inputs)
    training, training_sha = memory.read_training(root / 'train', inputs, before_sha)
    after, after_sha = read_reference_after(root / 'after', inputs, training, training_sha, before_sha)
    saved = source.read(root / 'train/TRAINING_ROWS.json')
    memory.same(saved, inputs['material'], 'exact_saved_reference_material_required')
    inputs['material'] = saved
    inputs['verified_before_sha256'] = before_sha
    inputs['verified_reference_after_sha256'] = after_sha
    inputs['run_binding'] = dict(memory_binding=deepcopy(inputs['binding']), reference_root=str(root),
        reference_before_result_sha256=before_sha, reference_training_result_sha256=training_sha,
        reference_after_result_sha256=after_sha, reference_adapter_state=training['adapter_state_after'],
        starting_parent_state=PARENT_STATE, saved_rows_sha256=source.file_hash(root / 'train/TRAINING_ROWS.json'),
        recipe_sha256=hop.document_sha256(recipe()), helper_hashes=helpers())
    inputs['reference_summary'] = dict(interpretation='REUSED_REFERENCE_NOT_EQUAL_BUDGET_CAUSAL_CONTROL',
        before_parametric=before['panels']['PARAMETRIC']['correct'],
        after_panels={name: dict(correct=panel['correct'], denominator=panel['denominator']) for name, panel in after['panels'].items()},
        new_recall=after['new_recall'], old_recall=after['old_recall'], held_audit=after['held_audit'],
        taught_graph=dict(correct=after['taught_graph']['OWN_TEXT']['correct'], denominator=4))
    return inputs


def train(engine, inputs, output):
    from gpu import astra_experienced_event_cue_sleep as development
    from organism_v6.pcfl_vertical_train import _state_hash

    require(inputs.get('verified_before_sha256') and inputs.get('verified_reference_after_sha256'),
            'complete_reference_before_and_after_required_before_gradient')
    encoded = memory.encode_material(inputs, engine.tokenizer)
    require(engine.tokenizer.pad_token_id == 151643, 'fixed_native_pad_required')
    source.write(output / 'TRAINING_ROWS.json', inputs['material'])
    source.write(output / 'MASKS.json', [asdict(row) for row in encoded])
    source.write(output / 'RECIPE.json', recipe())
    parameters = development.enable_existing_adapter(engine)
    require(_state_hash(parameters) == PARENT_STATE, 'same_37ec_parent_not_reference_writer_required')
    torch = engine.torch
    torch.manual_seed(0)
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, **source.native.OPTIMIZER)
    engine.model.train()
    tokens, doses = 0, [0] * 254
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, UPDATES + 1):
            engine.check('memory_trajectory_replay_update')
            indexes = training_indexes(update)
            batch = collate_six([encoded[index] for index in indexes], pad_id=151643)
            active = sum(label != -100 for labels in batch['labels'] for label in labels[1:])
            require(active > 0, 'positive_replay_labels_required')
            tensors = {name: torch.tensor(value, dtype=torch.long, device=engine.device) for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                loss = engine.model(**tensors, use_cache=False).loss
            require(bool(torch.isfinite(loss)) and loss.requires_grad, 'invalid_replay_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'invalid_replay_gradient')
            optimizer.step()
            require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()), 'nonfinite_replay_adapter')
            tokens += active
            for index in indexes:
                doses[index] += 1
            stream.write(source.json.dumps(dict(update=update, row_indexes=indexes,
                active_label_count=active, loss=loss.item()), allow_nan=False) + '\n')
            stream.flush()
    state = _state_hash(parameters)
    require(state != PARENT_STATE, 'replay_write_must_change_adapter')
    engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    files = {path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()}
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(files), 'saved_replay_adapter_required')
    require(source.read(output / 'adapter/adapter_config.json').get('r') == 8, 'saved_rank_eight_required')
    return dict(fits=1, updates=UPDATES, adapter_state_after=state, adapter_files=files,
        actual_supervised_tokens=tokens, row_presentations=doses,
        training_files={name: source.file_hash(output / name) for name in
                        ('TRAINING_ROWS.json', 'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl')})


def read_training(directory, inputs):
    directory = Path(directory)
    result = source.read(directory / 'RESULT.json')
    state = result.get('adapter_state_after')
    require(not (directory / 'FAILED.json').exists() and result.get('schema') == SCHEMA
        and result.get('phase') == 'train' and result.get('status') == 'COMPLETE'
        and result.get('binding') == inputs['run_binding'] and result.get('fits') == 1 and result.get('updates') == UPDATES
        and result.get('model_calls') == 0 and result.get('parent_present') is False
        and result.get('before_result_sha256') == inputs['verified_before_sha256']
        and result.get('reference_after_result_sha256') == inputs['verified_reference_after_sha256']
        and result.get('loaded_adapter_state_sha256') == PARENT_STATE and result.get('frozen_base_unchanged') is True
        and type(state) is str and len(state) == 64 and all(char in '0123456789abcdef' for char in state)
        and state != PARENT_STATE, 'own_completed_replay_write_required')
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(result.get('adapter_files', {}))
        and set(result.get('training_files', {})) == {'TRAINING_ROWS.json', 'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl'},
        'complete_replay_training_inventory_required')
    memory.transfer.verify_files(directory / 'adapter', result['adapter_files'])
    memory.transfer.verify_files(directory, result['training_files'])
    require(source.read(directory / 'adapter/adapter_config.json').get('r') == 8, 'saved_rank_eight_required')
    memory.same(source.read(directory / 'TRAINING_ROWS.json'), inputs['material'], 'saved_replay_material_drift')
    memory.same(source.read(directory / 'RECIPE.json'), recipe(), 'saved_replay_recipe_drift')
    expected_doses = [0] * 254
    records = [source.json.loads(line) for line in (directory / 'LOSSES.jsonl').read_text().splitlines()]
    require(len(records) == UPDATES, 'full_replay_update_log_required')
    for update, record in enumerate(records, 1):
        require(record['update'] == update and record['row_indexes'] == list(training_indexes(update))
                and type(record['active_label_count']) is int and record['active_label_count'] > 0,
                'replay_update_log_drift')
        for index in training_indexes(update):
            expected_doses[index] += 1
    memory.same(result['row_presentations'], expected_doses, 'replay_presentation_count_drift')
    require(result['actual_supervised_tokens'] == sum(record['active_label_count'] for record in records),
            'replay_actual_token_count_drift')
    return result, source.file_hash(directory / 'RESULT.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-after', 'campaign', 'audit-root', 'repair-root', 'cycle-root', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--lesson-root', default=memory.transfer.LESSON_ROOT)
    parser.add_argument('--transfer-root', default=memory.TRANSFER_ROOT)
    parser.add_argument('--reference-root', default=REFERENCE_ROOT)
    parser.add_argument('--gpu-uuid')
    parser.add_argument('--phase', choices=tuple(CAPS), required=True)
    parser.add_argument('--training')
    options = parser.parse_args(argv)
    require(bool(options.training) == (options.phase == 'after'), 'replay_phase_arguments')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_required')
    require(options.phase == 'prepare' or bool(options.gpu_uuid)
            and os.environ.get('CUDA_VISIBLE_DEVICES') == options.gpu_uuid, 'exact_gpu_required')
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    started, cap = time.time(), CAPS[options.phase]
    result = dict(schema=SCHEMA, phase=options.phase, arguments=vars(options), started_unix=started,
        fits=0, updates=0, model_calls=0, max_native_calls=cap, parent_present=False, protocol='turnbound',
        max_context=2048, max_new_tokens=160, claim=CLAIM, entry_sha256=source.file_hash(__file__),
        automatic_training=False, increased_budget=True, actual_token_equality_claim=False)
    source.write(output / 'REQUEST.json', result)
    captures, engine, cap_hit = [], None, False

    def check(label):
        require(time.time() < started + 3500, 'replay_deadline:' + label)

    try:
        inputs = load_inputs(options)
        result.update(binding=inputs['run_binding'], reference_summary=inputs['reference_summary'],
            before_result_sha256=inputs['verified_before_sha256'], reference_after_result_sha256=inputs['verified_reference_after_sha256'])
        for name, value in (('INPUTS.json', inputs['run_binding']), ('WORLD.json', inputs['world']),
                ('TASKS.json', hop.build_tasks(inputs['world'])), ('COLLECTION_SOURCE.json', inputs['collection']),
                ('NEW_ROWS.json', inputs['material']['new_rows']), ('REFERENCE.json', inputs['reference_summary'])):
            source.write(output / name, value)
        parent = inputs['binding']['transfer']
        state = PARENT_STATE
        arguments = argparse.Namespace(**inputs['arguments'])
        arguments.phase, arguments.device, arguments.gpu_uuid = 'readout', 'cuda:0', options.gpu_uuid
        arguments.adapter_dir, files = parent['trained_adapter_dir'], parent['trained_adapter_files']
        if options.phase == 'after':
            trained, result['training_result_sha256'] = read_training(options.training, inputs)
            state = trained['adapter_state_after']
            arguments.adapter_dir, files = str(Path(options.training) / 'adapter'), trained['adapter_files']
        memory.transfer.verify_files(arguments.adapter_dir, files)
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
        require(bool(parameters) and _state_hash(parameters) == state, 'mounted_replay_state_required')
        result.update(runtime=engine.runtime, loaded_adapter_state_sha256=state)

        def generate(messages, *, role, condition=None, task_index=None, graph=None):
            nonlocal cap_hit
            check('call')
            if len(captures) >= cap:
                cap_hit = True
                raise ValueError('replay_native_call_cap')
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
            result.update(memory.evaluate(inputs, generate, output, 'after'))
        require(not cap_hit, 'replay_native_call_cap')
        require(not any(capture['error'] is not None for capture in captures), 'native_errors_retained')
        engine.verify_base()
        final_state = _state_hash(parameters)
        if options.phase == 'train':
            require(final_state == result['adapter_state_after'] and final_state != state, 'saved_replay_state_drift')
            memory.transfer.verify_files(output / 'adapter', result['adapter_files'])
        else:
            require(final_state == state, 'readonly_replay_state_drift')
        memory.transfer.verify_files(arguments.adapter_dir, files)
        memory.transfer.verify_files(arguments.model_dir, parent['base_files'])
        memory.same(memory.helpers(), inputs['binding']['helper_hashes'], 'unchanged_memory_helper_drift')
        memory.same(helpers(), inputs['run_binding']['helper_hashes'], 'runtime_replay_helper_drift')
        source.write(output / 'STATES.json', dict(before=state, after=final_state))
        result.update(status='COMPLETE', adapter_state_after=final_state, model_calls=len(captures),
            frozen_base_unchanged=True, role_calls=dict(Counter(capture['role'] for capture in captures)), finished_unix=time.time())
        if options.phase == 'after':
            result['output_files'] = {path.name: source.file_hash(path) for path in output.glob('*.json')}
        source.write(output / 'RESULT.json', result)
        return result
    except BaseException as error:
        if engine is not None:
            try:
                result['adapter_state_after'] = _state_hash(parameters)
                engine.verify_base()
                memory.transfer.verify_files(arguments.adapter_dir, files)
                memory.transfer.verify_files(arguments.model_dir, inputs['binding']['transfer']['base_files'])
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
