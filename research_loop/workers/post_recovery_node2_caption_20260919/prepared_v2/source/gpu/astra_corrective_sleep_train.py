"""Bounded Stage B fit after caller-authenticated, source-valid child selection.

No selector, eligibility test, evaluation, model loading, or launch entry point.
The caller owns immutable actor/source binding and the conditional paired forks.
"""

from dataclasses import asdict
from pathlib import Path

from gpu import astra_experienced_event_cue_sleep as development
from gpu import astra_experienced_event_microloop as source
from organism_v6 import experienced_event_cue_sleep as cue_material


REPLAY_ARMS = ('CHILD_CORRECTIVE', 'UNIFORM_REPLAY')
UPDATES = 100
OLD_COUNT = 64
CUE_COUNT = 20
NEW_COUNT = 32
NEW_OFFSET = OLD_COUNT + CUE_COUNT
ENCODED_COUNT = NEW_OFFSET + NEW_COUNT
LOSS_NORMALIZATION = 'UNIFORM_BATCH_CAUSAL_LABEL_COUNT'
require = source.require


def selected_new_indexes(replay_arm, selected_source_indexes):
    """Return original encoded-row indexes, not positions in a repeated corpus."""
    require(replay_arm in REPLAY_ARMS, 'known_corrective_replay_arm_required')
    require(type(selected_source_indexes) in (list, tuple)
            and 1 <= len(selected_source_indexes) <= 4,
            'one_to_four_source_valid_selections_required')
    require(all(type(index) is int and 0 <= index < 4 for index in selected_source_indexes),
            'source_event_index_zero_to_three_required')
    if replay_arm == 'UNIFORM_REPLAY':
        return tuple(range(NEW_OFFSET, ENCODED_COUNT))
    return tuple(NEW_OFFSET + 4 * view + index
                 for index in selected_source_indexes for view in range(8))


def training_indexes(update, replay_arm, selected_source_indexes):
    """Actual and reference batch indexes for the same one-based update."""
    require(type(update) is int and 1 <= update <= UPDATES, 'fixed_100_update_range')
    new_indexes = selected_new_indexes(replay_arm, selected_source_indexes)
    offset = update - 1
    shared = (offset % OLD_COUNT, OLD_COUNT + offset % CUE_COUNT)
    actual = shared + tuple(new_indexes[(2 * offset + slot) % len(new_indexes)] for slot in range(2))
    reference = shared + tuple(NEW_OFFSET + (2 * offset + slot) % NEW_COUNT for slot in range(2))
    return actual, reference


def selection_layout(replay_arm, selected_source_indexes):
    new_indexes = selected_new_indexes(replay_arm, selected_source_indexes)
    return dict(replay_arm=replay_arm, selected_source_indexes=list(selected_source_indexes),
        encoded_row_count=ENCODED_COUNT, row_order='OLD64_CUE20_NEW32_WRAPPER_MAJOR',
        old_row_indexes=list(range(OLD_COUNT)), cue_row_indexes=list(range(OLD_COUNT, NEW_OFFSET)),
        selected_case_row_indexes=[list(selected_new_indexes('CHILD_CORRECTIVE', [index]))
                                   for index in selected_source_indexes],
        arm_new_row_indexes=list(new_indexes), uniform_new_row_indexes=list(range(NEW_OFFSET, ENCODED_COUNT)),
        updates=UPDATES, loss_normalization=LOSS_NORMALIZATION)


def loss_normalization(encoded, reference_indexes, batch):
    """Pool actual causal targets over the original UNIFORM batch denominator."""
    require(len(encoded) == ENCODED_COUNT, 'exact_116_encoded_rows_required')
    require(len(reference_indexes) == 4
            and all(type(index) is int and 0 <= index < ENCODED_COUNT for index in reference_indexes),
            'four_original_reference_indexes_required')
    require(len(batch['labels']) == 4, 'batch_four_required')
    require(all(encoded[index].labels and encoded[index].labels[0] == -100 for index in reference_indexes)
            and all(labels and labels[0] == -100 for labels in batch['labels']),
            'first_causal_label_must_be_masked')
    reference = sum(label != -100 for index in reference_indexes for label in encoded[index].labels[1:])
    actual = sum(label != -100 for labels in batch['labels'] for label in labels[1:])
    require(reference > 0 and actual > 0, 'positive_matched_loss_denominator_required')
    return reference, actual, actual / reference


def training_batch(encoded, update, replay_arm, selected_source_indexes):
    require(len(encoded) == ENCODED_COUNT, 'exact_116_encoded_rows_required')
    indexes, reference_indexes = training_indexes(update, replay_arm, selected_source_indexes)
    batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
    reference, actual, scale = loss_normalization(encoded, reference_indexes, batch)
    return indexes, reference_indexes, batch, reference, actual, scale


def validate_row_layout(old_rows, cue_rows, new_rows):
    for rows, count in ((old_rows, OLD_COUNT), (cue_rows, CUE_COUNT), (new_rows, NEW_COUNT)):
        require(type(rows) in (list, tuple) and len(rows) == count, 'exact_old64_cue20_new32_required')
    events = [row.get('event') for row in new_rows[:4]]
    require(all(type(event) is str and event for event in events) and len(set(events)) == 4,
            'four_distinct_new_events_required')
    require(all(row.get('event') == events[index % 4] and row.get('wrapper') == 'W%d' % (index // 4)
                for index, row in enumerate(new_rows)), 'original_wrapper_major_new_rows_required')


def train(engine, old_rows, cue_rows, new_rows, output, *, replay_arm, selected_source_indexes):
    from organism_v6.pcfl_vertical_train import _state_hash

    layout = selection_layout(replay_arm, selected_source_indexes)
    selected_source_indexes = tuple(layout['selected_source_indexes'])
    validate_row_layout(old_rows, cue_rows, new_rows)
    output = Path(output)
    require(output.is_dir() and not any((output / name).exists() for name in
        ('MASKS.json', 'SELECTION_LAYOUT.json', 'LOSSES.jsonl', 'adapter', 'ADAPTER_PROVENANCE.json')),
        'fresh_training_artifact_paths_required')
    require(engine.tokenizer.pad_token_id == 151643, 'fixed_native_pad_required')
    engine.check('corrective_train_start')
    torch = engine.torch
    encoded = tuple(row for offset in (0, 32)
                    for row in source.encode_rows(old_rows[offset:offset + 32], engine.tokenizer))
    encoded += tuple(cue_material.encode_cue_rows(cue_rows, engine.tokenizer))
    encoded += tuple(source.encode_rows(new_rows, engine.tokenizer))
    require(len(encoded) == ENCODED_COUNT, 'exact_116_encoded_rows_required')
    source.write(output / 'MASKS.json', [asdict(row) for row in encoded])
    source.write(output / 'SELECTION_LAYOUT.json', layout)
    parameters = development.enable_existing_adapter(engine)
    before = _state_hash(parameters)
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, **source.native.OPTIMIZER)
    torch.manual_seed(0)
    engine.model.train()
    actual_tokens = reference_tokens = 0
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, UPDATES + 1):
            engine.check('corrective_update')
            indexes, reference_indexes, batch, reference, actual, scale = training_batch(
                encoded, update, replay_arm, selected_source_indexes)
            tensors = {name: torch.tensor(value, dtype=torch.long, device=engine.device)
                       for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                mean_loss = engine.model(**tensors, use_cache=False).loss
                loss = mean_loss * scale
            require(bool(torch.isfinite(mean_loss)) and bool(torch.isfinite(loss)) and loss.requires_grad,
                    'invalid_corrective_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'invalid_corrective_gradients')
            optimizer.step()
            require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()),
                    'nonfinite_corrective_adapter')
            actual_tokens += actual
            reference_tokens += reference
            stream.write(source.json.dumps(dict(update=update, row_indexes=indexes,
                reference_row_indexes=reference_indexes, actual_label_count=actual,
                reference_label_count=reference, active_label_count=actual, original_label_count=reference,
                loss_scale=scale, actual_mean_loss=mean_loss.item(), loss=loss.item()), allow_nan=False) + '\n')
            stream.flush()
    after = _state_hash(parameters)
    require(after != before, 'no_parameter_update')
    engine.check('corrective_checkpoint')
    engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    adapter_files = {path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()}
    require('adapter_model.safetensors' in adapter_files, 'corrective_adapter_file_required')
    provenance = dict(adapter_state_before=before, adapter_state_after=after, adapter_files=adapter_files,
        runner_sha256=source.file_hash(__file__),
        training_artifact_sha256={name: source.file_hash(output / name)
                                 for name in ('MASKS.json', 'SELECTION_LAYOUT.json', 'LOSSES.jsonl')})
    source.write(output / 'ADAPTER_PROVENANCE.json', provenance)
    budgets = dict(old_memory_presentations=100, old_cue_presentations=100, new_memory_presentations=200,
                   original_bank_presentations=64, first_adult_presentations=36)
    return dict(updates=UPDATES, replay_arm=replay_arm, selected_source_indexes=list(selected_source_indexes),
        budgets=budgets, **budgets, old_fact_count=8, train_seed=0,
        supervised_tokens=actual_tokens, actual_supervised_tokens=actual_tokens,
        original_supervised_tokens=reference_tokens, reference_supervised_tokens=reference_tokens,
        loss_normalization=LOSS_NORMALIZATION, optimizer='FRESH_ADAMW', learning_rate=3e-5,
        **provenance)
