"""Finite-corpus specialization; preserve266 optimizer and reference normalization."""

from dataclasses import asdict, replace
from types import FunctionType

from gpu import astra_goal_quality_train as original
from organism_v6 import orch_terse_breadth as design


source = original.source
require = source.require


def controlled_masks(encoded, arm):
    require(arm in design.ARMS, 'fixed_arm_required')
    design.updates(len(encoded) - 222)
    return tuple(replace(row, labels=(-100,) * len(row.labels))
                 if arm == design.ARMS[1] and index >= 222 else row for index, row in enumerate(encoded))


def training_batch(encoded, update, arm, presentations=4):
    indexes = design.indexes(update, len(encoded) - 222, presentations)
    require(arm in design.ARMS, 'fixed_arm_required')
    controlled = [replace(encoded[index], labels=(-100,) * len(encoded[index].labels))
                  if arm == design.ARMS[1] and index >= 222 else encoded[index] for index in indexes]
    batch = source.native.collate(controlled, pad_id=151643)
    reference_batch = source.native.collate([encoded[index] for index in indexes], pad_id=151643)
    require(batch['input_ids'] == reference_batch['input_ids']
            and batch['attention_mask'] == reference_batch['attention_mask']
            and all(batch['labels'][slot] == reference_batch['labels'][slot]
                    for slot, index in enumerate(indexes) if index < 222), 'paired_inputs_old_labels_required')
    reference, active, scale = original.development.loss_normalization(encoded, indexes, batch)
    return indexes, batch, reference, active, scale


def dose(encoded, arm, presentations=4):
    batches, counts = [], [0] * len(encoded)
    for update in range(1, design.updates(len(encoded) - 222, presentations) + 1):
        indexes, unused, reference, active, scale = training_batch(encoded, update, arm, presentations)
        for index in indexes:
            counts[index] += 1
        batches.append(dict(update=update, row_indexes=list(indexes), reference_labels=reference,
                            active_labels=active, loss_scale=scale))
    require(set(counts[210:]) == {presentations}, 'exact_declared_presentations_required')
    return dict(batches=batches, row_presentations=counts,
                actual_supervised_tokens=sum(item['active_labels'] for item in batches),
                reference_supervised_tokens=sum(item['reference_labels'] for item in batches))


def recipe(new_count, arm, seed, protocol_sha, presentations=4):
    require(type(seed) is int and seed in design.SEEDS and arm in design.ARMS, 'frozen_seed_and_arm_required')
    require((seed, presentations) in design.SEED_DOSES, 'fixed_seed_dose_cell_required')
    count = design.updates(new_count, presentations)
    return dict(schema='ORCH_TERSE_BREADTH_V1', arm=arm, seed=seed, initial_state=original.PARENT_STATE,
        updates=count, batch_size=4, learning_rate=3e-5, rank=8, lora_dropout=0.05,
        optimizer='FRESH_ADAMW', optimizer_kwargs=dict(source.native.OPTIMIZER),
        schedule=[list(design.indexes(update, new_count, presentations)) for update in range(1, count + 1)],
        group_order=list(original.GROUPS), group_sizes=[128, 20, 62, 12, new_count],
        encoded_rows=222 + new_count, new_target_presentations=presentations * new_count,
        trajectory_presentations=presentations,
        old_trajectory_presentations=presentations * 12, old_memory_presentations=count, old_behavior_presentations=count,
        new_supervised_presentations=presentations * new_count if arm == design.ARMS[0] else 0,
        masked_row_indexes=list(range(222, 222 + new_count)) if arm == design.ARMS[1] else [],
        loss='MEAN_CAUSAL_CE_TIMES_ACTIVE_OVER_FULL_REFERENCE_LABELS',
        protocol_sha256=protocol_sha, actual_token_equality_claim=False)


def encode_new_rows(rows, tokenizer):
    require(tokenizer.eos_token == original.quality.lesson.TARGET_EOT
            and type(tokenizer.eos_token_id) is int
            and source.native._encode(tokenizer, tokenizer.eos_token) == (tokenizer.eos_token_id,),
            'exact_goal_pair_eot_required')
    encoded = []
    for row in rows:
        prefix = row['prefix']
        require([message['role'] for message in prefix] == ['system', 'user']
                + ['assistant', 'user'] * row['episode_call_index'], 'alternating_goal_pair_student_prefix_required')
        require(all(original.quality.lesson.PARENT_GUIDANCE not in message['content'] for message in prefix),
                'parent_free_student_prefix_required')
        messages = prefix + [dict(role='assistant', content=row['assistant'])]
        context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
        require(full == context + row['assistant'] + tokenizer.eos_token + '\n', 'exact_goal_pair_template_boundary_required')
        prefix_ids = source.native._encode(tokenizer, context)
        target = source.native._encode(tokenizer, row['assistant'])
        suffix = source.native._encode(tokenizer, '\n')
        require(not set(tokenizer.all_special_ids).intersection(target), 'goal_pair_target_special_token_forbidden')
        supervised = target + (tokenizer.eos_token_id,)
        sequence = source.native._encode(tokenizer, full)
        require(sequence == prefix_ids + supervised + suffix and len(sequence) <= 2048
                and len(supervised) <= 160, 'untruncated_bounded_goal_pair_sequence_required')
        require(source.native._decode(tokenizer, sequence) == full
                and source.native._decode(tokenizer, prefix_ids) == context
                and source.native._decode(tokenizer, supervised) == row['assistant'] + tokenizer.eos_token
                and source.native._decode(tokenizer, suffix) == '\n', 'goal_pair_token_roundtrip_failed')
        require(tuple(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
            return_dict=False, truncation=False, padding=False)) == sequence, 'goal_pair_template_token_ids_mismatch')
        encoded.append(source.native.EncodedRow(sequence, (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix), supervised))
    return tuple(encoded)


def encode_material(inputs, tokenizer):
    material = inputs['material']
    encoded = tuple(source.encode_row(row['messages'], tokenizer) for row in material['memory_rows'])
    encoded += tuple(original.memory.cues.encode_cue_rows(material['cue_rows'], tokenizer))
    encoded += tuple(original.memory.audit.encode_rows(material['audit_rows'], tokenizer))
    encoded += tuple(original.memory.lesson.lesson.encode_rows(material['trajectory_rows'], tokenizer))
    original.same([asdict(row) for row in encoded], inputs['old_masks'], 'unchanged_original_222_encodings_required')
    encoded += encode_new_rows(material['new_trajectory_rows'], tokenizer)
    require(len(encoded) == 222 + len(material['new_trajectory_rows']) and tokenizer.pad_token_id == 151643,
            'native_encoding_size_required')
    original.masks.validate_masks(encoded, tokenizer.eos_token_id)
    return encoded


def train(engine, inputs, output, arm, seed):
    count = len(inputs['material']['new_trajectory_rows'])
    presentations = inputs['trajectory_presentations']
    namespace = dict(vars(original), UPDATES=design.updates(count, presentations), encode_material=encode_material,
        dose=lambda encoded, selected: dose(encoded, selected, presentations), controlled_masks=controlled_masks,
        training_batch=lambda encoded, update, selected: training_batch(encoded, update, selected, presentations),
        recipe=lambda selected_arm, selected_seed: recipe(count, selected_arm, selected_seed, inputs['protocol_sha256'], presentations))
    implementation = original.train
    bound = FunctionType(implementation.__code__, namespace, implementation.__name__,
                         implementation.__defaults__, implementation.__closure__)
    return bound(engine, inputs, output, arm, seed)
