"""Bounded own-memory repair after actual sourced reader-audit selections.

No collection, filtering, model loading or launch. The driver binds each cell
to its own post-lesson actor, rank-eight adapter, frozen base and source records.
Lesson encoding retains only the existing parent-safe student behavior corpus.
"""

from dataclasses import asdict
from importlib import import_module
from pathlib import Path

from gpu import astra_experienced_event_cue_sleep as development
from gpu import astra_experienced_event_microloop as source
from gpu import astra_reader_audit_lesson_train as audit
from organism_v6 import experienced_event_cue_sleep as cue_material


SCHEMA = 'DEV_SELECTED_READER_REPAIR_SLEEP_V1'
MATERIAL_ARMS = ('SELECTED', 'UNIFORM')
UPDATES = 100
MEMORY_COUNT = 80
CUE_COUNT = 20
LESSON_COUNT = 62
BEHAVIOR_COUNT = CUE_COUNT + LESSON_COUNT
NEW_OFFSET = MEMORY_COUNT + BEHAVIOR_COUNT
NEW_COUNT = 32
ENCODED_COUNT = NEW_OFFSET + NEW_COUNT
LOSS_NORMALIZATION = 'UNIFORM_BATCH_CAUSAL_LABEL_COUNT'
require = source.require


def selected_new_indexes(material_arm, selected_source_indexes):
    require(material_arm in MATERIAL_ARMS, 'known_repair_material_arm_required')
    require(type(selected_source_indexes) in (list, tuple) and 1 <= len(selected_source_indexes) <= 8,
            'one_to_eight_actual_selections_required')
    require(all(type(index) is int and 0 <= index < 4 for index in selected_source_indexes),
            'source_event_index_zero_to_three_required')
    if material_arm == 'UNIFORM':
        return tuple(range(NEW_OFFSET, ENCODED_COUNT))
    return tuple(NEW_OFFSET + 4 * view + index for index in selected_source_indexes for view in range(8))


def training_indexes(update, material_arm, selected_source_indexes):
    require(type(update) is int and 1 <= update <= UPDATES, 'fixed_100_update_range')
    pool = selected_new_indexes(material_arm, selected_source_indexes)
    offset = update - 1
    shared = (offset % MEMORY_COUNT, MEMORY_COUNT + offset % BEHAVIOR_COUNT)
    actual = shared + tuple(pool[(2 * offset + slot) % len(pool)] for slot in range(2))
    reference = shared + tuple(NEW_OFFSET + (2 * offset + slot) % NEW_COUNT for slot in range(2))
    return actual, reference


def training_batch(encoded, update, material_arm, selected_source_indexes):
    require(len(encoded) == ENCODED_COUNT, 'exact_194_encoded_rows_required')
    indexes, reference_indexes = training_indexes(update, material_arm, selected_source_indexes)
    batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
    require(all(encoded[index].labels and encoded[index].labels[0] == -100
                for index in indexes + reference_indexes), 'first_causal_label_must_be_masked')
    reference = sum(label != -100 for index in reference_indexes for label in encoded[index].labels[1:])
    actual = sum(label != -100 for labels in batch['labels'] for label in labels[1:])
    require(reference > 0 and actual > 0, 'positive_matched_loss_denominator_required')
    return indexes, reference_indexes, batch, reference, actual, actual / reference


def validate_row_layout(memory_rows, cue_rows, lesson_rows, new_rows):
    for rows, count in ((memory_rows, MEMORY_COUNT), (cue_rows, CUE_COUNT),
                        (lesson_rows, LESSON_COUNT), (new_rows, NEW_COUNT)):
        require(type(rows) in (list, tuple) and len(rows) == count, 'exact_80_20_62_32_rows_required')
    events = [row.get('event') for row in new_rows[:4]]
    require(all(type(event) is str and event for event in events) and len(set(events)) == 4,
            'four_distinct_new_source_events_required')
    require(all(row.get('event') == events[index % 4] and row.get('wrapper') == 'W%d' % (index // 4)
                for index, row in enumerate(new_rows)), 'original_wrapper_major_new_rows_required')


def recipe(material_arm, selected_source_indexes):
    pool = selected_new_indexes(material_arm, selected_source_indexes)
    return dict(schema=SCHEMA, material_arm=material_arm, selected_source_indexes=list(selected_source_indexes),
        updates=UPDATES, batch_size=4, train_seed=0, learning_rate=3e-5, optimizer='FRESH_ADAMW',
        optimizer_kwargs=dict(source.native.OPTIMIZER), expected_lora_rank=8, adapter_dtype='float32',
        row_order='MEMORY80_CUE20_LESSON62_NEW32_WRAPPER_MAJOR', encoded_row_count=ENCODED_COUNT,
        memory_row_count=MEMORY_COUNT, cue_row_count=CUE_COUNT, lesson_row_count=LESSON_COUNT,
        new_row_count=NEW_COUNT, new_row_offset=NEW_OFFSET, arm_new_row_indexes=list(pool),
        uniform_new_row_indexes=list(range(NEW_OFFSET, ENCODED_COUNT)),
        schedule=dict(memory='(update-1)%80', behavior='80+(update-1)%82',
                      new='arm_new_row_indexes[(2*(update-1)+slot)%pool_length]; slot=0,1'),
        loss_normalization=LOSS_NORMALIZATION, actual_token_equality_claim=False,
        actor_and_source_binding='CALLER_OWNED')


def train(engine, memory_rows, cue_rows, lesson_rows, new_rows, output, *, material_arm, selected_source_indexes):
    from organism_v6 import pcfl_vertical_train as writer

    config = recipe(material_arm, selected_source_indexes)
    selected_source_indexes = tuple(config['selected_source_indexes'])
    validate_row_layout(memory_rows, cue_rows, lesson_rows, new_rows)
    config['new_source_events'] = [row['event'] for row in new_rows[:4]]
    output = Path(output)
    require(output.is_dir() and not any((output / name).exists() for name in
        ('MASKS.json', 'RECIPE.json', 'LOSSES.jsonl', 'ADAPTER_PROVENANCE.json', 'adapter')),
        'fresh_training_artifact_paths_required')
    require(engine.tokenizer.pad_token_id == 151643, 'fixed_native_pad_required')
    engine.check('selected_reader_repair_start')
    lesson_material = import_module(audit.LESSON_MODULE)
    groups = (tuple(source.encode_row(row['messages'], engine.tokenizer) for row in memory_rows),
              tuple(cue_material.encode_cue_rows(cue_rows, engine.tokenizer)),
              tuple(lesson_material.encode_rows(lesson_rows, engine.tokenizer)),
              tuple(source.encode_rows(new_rows, engine.tokenizer)))
    require(tuple(map(len, groups)) == (80, 20, 62, 32), 'exact_80_20_62_32_encoded_groups_required')
    encoded = tuple(row for group in groups for row in group)
    audit.validate_masks(encoded, engine.tokenizer.eos_token_id)
    source.write(output / 'MASKS.json', [asdict(row) for row in encoded])
    source.write(output / 'RECIPE.json', config)
    code_sources = {
        'trainer': (__file__, 'selected material schedule and shared uniform denominator'),
        'memory_and_new_encoder': (source.__file__, 'original own EVENT target/EOT encoding'),
        'cue_encoder': (cue_material.__file__, 'retained cue action target/EOT encoding'),
        'lesson_encoder': (lesson_material.__file__, 'actual child lessons with parent-safe student prefixes'),
        'mask_validator': (audit.__file__, 'masked prefix and exact target/EOT span checks'),
        'adapter_setup': (development.__file__, 'existing FP32 LoRA only; freeze all other parameters'),
        'native_recipe': (source.native.__file__, 'collation and native AdamW settings'),
        'state_hash': (writer.__file__, 'adapter tensor state digest'),
    }
    code_provenance = {name: dict(path=str(path), sha256=source.file_hash(path), role=role)
                       for name, (path, role) in code_sources.items()}
    torch = engine.torch
    parameters = development.enable_existing_adapter(engine)
    before = writer._state_hash(parameters)
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, **source.native.OPTIMIZER)
    torch.manual_seed(0)
    engine.model.train()
    actual_tokens = reference_tokens = 0
    new_fact_presentations = [0] * 4
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, UPDATES + 1):
            engine.check('selected_reader_repair_update')
            indexes, reference_indexes, batch, reference, actual, scale = training_batch(
                encoded, update, material_arm, selected_source_indexes)
            tensors = {name: torch.tensor(value, dtype=torch.long, device=engine.device)
                       for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                mean_loss = engine.model(**tensors, use_cache=False).loss
                loss = mean_loss * scale
            require(bool(torch.isfinite(mean_loss)) and bool(torch.isfinite(loss)) and loss.requires_grad,
                    'invalid_selected_reader_repair_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'invalid_selected_reader_repair_gradients')
            optimizer.step()
            require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()),
                    'nonfinite_selected_reader_repair_adapter')
            actual_tokens += actual
            reference_tokens += reference
            for index in indexes[2:]:
                new_fact_presentations[(index - NEW_OFFSET) % 4] += 1
            stream.write(source.json.dumps(dict(update=update, row_indexes=indexes,
                reference_row_indexes=reference_indexes, actual_label_count=actual, reference_label_count=reference,
                active_label_count=actual, original_label_count=reference, loss_scale=scale,
                actual_mean_loss=mean_loss.item(), loss=loss.item()), allow_nan=False) + '\n')
            stream.flush()
    after = writer._state_hash(parameters)
    require(after != before, 'no_parameter_update')
    engine.check('selected_reader_repair_checkpoint')
    engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    adapter_files = {path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()}
    require('adapter_model.safetensors' in adapter_files, 'selected_reader_repair_adapter_file_required')
    provenance = dict(schema=SCHEMA, material_arm=material_arm, adapter_state_before=before, adapter_state_after=after,
        adapter_files=adapter_files, code_provenance=code_provenance,
        training_artifact_sha256={name: source.file_hash(output / name)
                                 for name in ('MASKS.json', 'RECIPE.json', 'LOSSES.jsonl')})
    source.write(output / 'ADAPTER_PROVENANCE.json', provenance)
    budgets = dict(memory_presentations=100, behavior_presentations=100, cue_presentations=38,
                   lesson_presentations=62, new_memory_presentations=200)
    return dict(**provenance, updates=UPDATES, recipe=config, budgets=budgets, **budgets,
        selected_source_indexes=list(selected_source_indexes), new_fact_presentations=new_fact_presentations,
        new_source_events=config['new_source_events'], train_seed=0, optimizer='FRESH_ADAMW', learning_rate=3e-5,
        supervised_tokens=actual_tokens, actual_supervised_tokens=actual_tokens,
        original_supervised_tokens=reference_tokens, reference_supervised_tokens=reference_tokens,
        loss_normalization=LOSS_NORMALIZATION, actual_token_equality_claim=False)
