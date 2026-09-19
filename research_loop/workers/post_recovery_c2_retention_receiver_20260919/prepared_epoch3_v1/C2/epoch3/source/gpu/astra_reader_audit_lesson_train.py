"""CPU-importable bounded trainer, not a reader-audit collection or launcher.

The driver authenticates the same corrective actor, lesson coverage, source
records, rank-eight adapter and frozen base. The lesson encoder owns parent-safe
student prefixes. This helper never constructs lesson targets or memory rows.
"""

from dataclasses import asdict
from importlib import import_module
from pathlib import Path

from gpu import astra_experienced_event_cue_sleep as development
from gpu import astra_experienced_event_microloop as source
from organism_v6 import experienced_event_cue_sleep as cue_material


SCHEMA = 'DEV_READER_AUDIT_LESSON_SLEEP_V1'
ARMS = ('AUDIT_SFT', 'AUDIT_LOSS_OFF')
UPDATES = 200
MEMORY_COUNT = 80
CUE_COUNT = 20
LESSON_OFFSET = MEMORY_COUNT + CUE_COUNT
MAX_LESSONS = 64
LOSS_NORMALIZATION = 'TREATMENT_BATCH_CAUSAL_LABEL_COUNT'
LESSON_MODULE = 'organism_v6.experienced_event_reader_audit_lesson'
require = source.require


def validate_choice(arm, lesson_count):
    require(arm in ARMS, 'known_reader_audit_arm_required')
    require(type(lesson_count) is int and 1 <= lesson_count <= MAX_LESSONS,
            'nonempty_at_most_64_lessons_required')


def training_indexes(update, lesson_count):
    validate_choice('AUDIT_SFT', lesson_count)
    require(type(update) is int and 1 <= update <= UPDATES, 'fixed_200_update_range')
    offset = update - 1
    return (offset % MEMORY_COUNT, MEMORY_COUNT + offset % CUE_COUNT,
            LESSON_OFFSET + 2 * offset % lesson_count,
            LESSON_OFFSET + (2 * offset + 1) % lesson_count)


def training_batch(encoded, update, lesson_count, arm):
    validate_choice(arm, lesson_count)
    require(len(encoded) == LESSON_OFFSET + lesson_count, 'exact_80_20_lesson_encoded_layout_required')
    indexes = training_indexes(update, lesson_count)
    batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
    if arm == 'AUDIT_LOSS_OFF':
        batch['labels'][2:] = [[-100] * len(labels) for labels in batch['labels'][2:]]
    reference, actual, scale = development.loss_normalization(encoded, indexes, batch)
    return indexes, batch, reference, actual, scale


def encode_memory_rows(rows, tokenizer):
    require(type(rows) in (list, tuple) and len(rows) == MEMORY_COUNT, 'exact_80_memory_rows_required')
    original = tuple(encoded for offset in (0, 32)
                     for encoded in source.encode_rows(rows[offset:offset + 32], tokenizer))
    return original + tuple(source.encode_row(row['messages'], tokenizer) for row in rows[64:])


def validate_masks(encoded, eos_token_id):
    for row in encoded:
        require(len(row.input_ids) == len(row.labels) and bool(row.target_ids)
                and row.target_ids[-1] == eos_token_id, 'target_and_eot_only_required')
        active = [index for index, label in enumerate(row.labels) if label != -100]
        require(bool(active) and active[0] > 0
                and active == list(range(active[0], active[0] + len(row.target_ids)))
                and tuple(row.labels[index] for index in active) == tuple(row.target_ids)
                and all(row.input_ids[index] == row.labels[index] for index in active),
                'masked_prefix_and_exact_target_span_required')


def recipe(arm, lesson_count):
    validate_choice(arm, lesson_count)
    return dict(schema=SCHEMA, arm=arm, updates=UPDATES, batch_size=4, train_seed=0,
        learning_rate=3e-5, optimizer='FRESH_ADAMW', optimizer_kwargs=dict(source.native.OPTIMIZER),
        expected_lora_rank=8, adapter_dtype='float32', loss_normalization=LOSS_NORMALIZATION,
        row_order='MEMORY80_CUE20_LESSONS', encoded_row_count=LESSON_OFFSET + lesson_count,
        memory_row_count=MEMORY_COUNT, cue_row_count=CUE_COUNT, lesson_row_count=lesson_count,
        memory_presentations=200, cue_presentations=200, lesson_presentations=400,
        lesson_supervised_presentations=400 if arm == 'AUDIT_SFT' else 0,
        schedule=dict(memory='(update-1)%80', cue='80+(update-1)%20',
                      lessons='100+(2*(update-1)+slot)%lesson_count; slot=0,1'),
        actual_token_equality_claim=False, readiness_and_source_binding='CALLER_OWNED')


def train(engine, memory_rows, cue_rows, lesson_rows, output, *, arm):
    from organism_v6 import pcfl_vertical_train as writer

    require(type(lesson_rows) in (list, tuple), 'lesson_rows_required')
    config = recipe(arm, len(lesson_rows))
    require(type(memory_rows) in (list, tuple) and len(memory_rows) == MEMORY_COUNT,
            'exact_80_memory_rows_required')
    require(type(cue_rows) in (list, tuple) and len(cue_rows) == CUE_COUNT, 'exact_20_cue_rows_required')
    output = Path(output)
    artifacts = ('MASKS.json', 'RECIPE.json', 'LOSSES.jsonl', 'ADAPTER_PROVENANCE.json', 'adapter')
    require(output.is_dir() and not any((output / name).exists() for name in artifacts),
            'fresh_training_artifact_paths_required')
    require(engine.tokenizer.pad_token_id == 151643, 'fixed_native_pad_required')
    engine.check('reader_audit_train_start')
    lesson_material = import_module(LESSON_MODULE)
    encoded = encode_memory_rows(memory_rows, engine.tokenizer)
    cue_encoded = tuple(cue_material.encode_cue_rows(cue_rows, engine.tokenizer))
    lesson_encoded = tuple(lesson_material.encode_rows(lesson_rows, engine.tokenizer))
    require(len(encoded) == MEMORY_COUNT and len(cue_encoded) == CUE_COUNT
            and len(lesson_encoded) == len(lesson_rows), 'exact_80_20_lesson_encoded_layout_required')
    encoded += cue_encoded + lesson_encoded
    validate_masks(encoded, engine.tokenizer.eos_token_id)
    source.write(output / 'MASKS.json', [asdict(row) for row in encoded])
    source.write(output / 'RECIPE.json', config)
    code_sources = {
        'trainer': (__file__, 'fixed recipe, schedule, control masking and provenance'),
        'memory_encoder': (source.__file__, 'original EVENT messages, target/EOT encoding'),
        'cue_encoder': (cue_material.__file__, 'retained action prefixes, final action/EOT encoding'),
        'lesson_encoder': (lesson_material.__file__, 'parent-safe student prefix and actual child lesson encoding'),
        'adapter_and_normalization': (development.__file__, 'existing FP32 LoRA only, causal label denominator'),
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
    with (output / 'LOSSES.jsonl').open('x') as stream:
        for update in range(1, UPDATES + 1):
            engine.check('reader_audit_update')
            indexes, batch, reference, actual, scale = training_batch(encoded, update, len(lesson_rows), arm)
            tensors = {name: torch.tensor(value, dtype=torch.long, device=engine.device)
                       for name, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                mean_loss = engine.model(**tensors, use_cache=False).loss
                loss = mean_loss * scale
            require(bool(torch.isfinite(mean_loss)) and bool(torch.isfinite(loss)) and loss.requires_grad,
                    'invalid_reader_audit_loss')
            loss.backward()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in parameters.values()), 'invalid_reader_audit_gradients')
            optimizer.step()
            actual_tokens += actual
            reference_tokens += reference
            stream.write(source.json.dumps(dict(update=update, row_indexes=indexes,
                reference_row_indexes=indexes, actual_label_count=actual, reference_label_count=reference,
                active_label_count=actual, original_label_count=reference, loss_scale=scale,
                actual_mean_loss=mean_loss.item(), loss=loss.item()), allow_nan=False) + '\n')
            stream.flush()
    require(all(bool(torch.isfinite(parameter).all()) for parameter in parameters.values()), 'nonfinite_reader_audit_adapter')
    after = writer._state_hash(parameters)
    require(after != before, 'no_parameter_update')
    engine.check('reader_audit_checkpoint')
    engine.model.save_pretrained(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
    adapter_files = {path.name: source.file_hash(path) for path in (output / 'adapter').iterdir() if path.is_file()}
    require('adapter_model.safetensors' in adapter_files, 'reader_audit_adapter_file_required')
    provenance = dict(schema=SCHEMA, arm=arm, adapter_state_before=before, adapter_state_after=after,
        adapter_files=adapter_files, code_provenance=code_provenance,
        training_artifact_sha256={name: source.file_hash(output / name)
                                 for name in ('MASKS.json', 'RECIPE.json', 'LOSSES.jsonl')})
    source.write(output / 'ADAPTER_PROVENANCE.json', provenance)
    return dict(**provenance, updates=UPDATES, recipe=config, train_seed=0, optimizer='FRESH_ADAMW', learning_rate=3e-5,
        memory_presentations=200, cue_presentations=200, lesson_presentations=400,
        lesson_supervised_presentations=config['lesson_supervised_presentations'],
        supervised_tokens=actual_tokens, actual_supervised_tokens=actual_tokens,
        original_supervised_tokens=reference_tokens, reference_supervised_tokens=reference_tokens,
        loss_normalization=LOSS_NORMALIZATION, actual_token_equality_claim=False)
