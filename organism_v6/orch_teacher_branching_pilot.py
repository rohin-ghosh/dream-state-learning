"""Isolated teacher dose4 compilation; never a continual-ingestion interface."""

from dataclasses import asdict, replace
import hashlib
import json

from organism_v6 import orch_route_parent_campaign_teacher_exemplar as teacher
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


LABEL = 'TEACHER_DISTILLATION'
STATE = '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
CONTEXT = 16384
ARMS = ('FULL_TARGET', 'NEW_TRAJECTORY_LOSS_OFF')
require = teacher.route.require


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def text_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def compile_row(prompt, response, oracle, forbidden_identifiers, source_refs, author_audit):
    teacher.validate_prompt(prompt)
    require(response['source_label'] == LABEL, 'teacher_label_required')
    require(teacher.check_answer(response, oracle)['final_answer_correct'], 'teacher_final_answer_incorrect')
    require(author_audit['author_supported'] is True
            and author_audit['independent_certification'] is False, 'author_only_audit_required')
    require(source_refs and all(len(value['sha256']) == 64 for value in source_refs.values()),
            'hash_bound_teacher_source_required')
    problem = prompt['problem']
    if prompt['observed_events']:
        problem += '\n\nObserved events:\n' + '\n'.join(prompt['observed_events'])
    prefix = [dict(role='user', content=problem)]
    pieces, spans = [], []

    def add(field, value, separator='\n\n'):
        require(isinstance(value, str) and value.strip(), 'nonempty_original_teacher_field')
        if pieces:
            pieces.append(separator)
        start = sum(len(piece) for piece in pieces)
        pieces.append(value)
        spans.append(dict(field=field, start=start, end=start + len(value), sha256=text_hash(value)))

    for ordinal, method in enumerate(response['methods']):
        add(f'methods.{ordinal}.name', method['name'])
        add(f'methods.{ordinal}.explanation', method['explanation'], '\n')
    for ordinal, check in enumerate(response['checks']):
        add(f'checks.{ordinal}', check)
    pieces.append('\n\nFINAL: ')
    add('final_answer', response['final_answer'], '')
    target = ''.join(pieces)
    require(not any(identifier and identifier in json.dumps([prefix, response])
                    for identifier in forbidden_identifiers), 'held_identifier_in_teacher_material')
    return dict(task_id=prompt['task_id'], split='TRAIN', domain=prompt['domain'],
                source_label=LABEL, source_purpose='ISOLATED_TEACHER_DOSE4',
                student_prefix=prefix, student_prefix_sha256=digest(prefix),
                target=target, target_sha256=text_hash(target), target_field_spans=spans,
                omitted_target_fields=['source_label', 'limitations'],
                original_limitations=response['limitations'], source_refs=source_refs,
                author_audit=author_audit, teacher_steering_in_input=False,
                teacher_steering_in_target=False, own_generated=False,
                parenting_experience=False, ongoing_l1_allowed=False,
                training_application_allowed=False, final_answer_verified=True)


def encode_rows(rows, tokenizer):
    from gpu import orch_guided_native as native

    encoded = []
    for row in rows:
        require(row['source_label'] == LABEL and row['split'] == 'TRAIN'
                and not row['ongoing_l1_allowed'] and not row['own_generated'], 'teacher_sink_boundary')
        prefix, target = row['student_prefix'], row['target']
        require(digest(prefix) == row['student_prefix_sha256']
                and text_hash(target) == row['target_sha256'], 'compiled_row_hash_mismatch')
        context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
        full = tokenizer.apply_chat_template(prefix + [dict(role='assistant', content=target)],
            tokenize=False, add_generation_prompt=False, return_dict=False)
        require(full == context + target + tokenizer.eos_token + '\n', 'exact_chat_boundary')
        prefix_ids = native.source.native._encode(tokenizer, context)
        target_ids = native.source.native._encode(tokenizer, target)
        suffix_ids = native.source.native._encode(tokenizer, '\n')
        sequence = native.source.native._encode(tokenizer, full)
        require(0 < len(target_ids) <= 8192 and len(sequence) <= CONTEXT,
                'unsupported_train_context_raw_retained_no_crop')
        require(not set(tokenizer.all_special_ids).intersection(target_ids), 'special_token_in_target')
        require(native.source.native._decode(tokenizer, sequence) == full, 'exact_tokenizer_roundtrip')
        supervised = target_ids + (tokenizer.eos_token_id,)
        require(sequence == prefix_ids + supervised + suffix_ids, 'token_boundary_merge')
        item = native.source.native.EncodedRow(sequence,
            (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix_ids), supervised)
        native.bridge.validate_encoding_boundary(item, prefix_ids=prefix_ids, target_ids=target_ids,
            suffix_ids=suffix_ids, eos_token_id=tokenizer.eos_token_id,
            validate_masks=native.masks.validate_masks)
        encoded.append(item)
    return tuple(encoded)


def paired_rehearsal(legacy, new):
    require(len(legacy) == 222 and len(new) == 16, 'exact_legacy222_teacher16')
    full = tuple(legacy) + tuple(new)
    masked = tuple(legacy) + tuple(replace(row, labels=(-100,) * len(row.labels)) for row in new)
    require(all(left.input_ids == right.input_ids and left.target_ids == right.target_ids
                for left, right in zip(full, masked)), 'paired_inputs_identical')
    require(full[:222] == masked[:222], 'legacy_masks_unchanged')
    layout = GoalReplayLayout(16, 4)
    schedule = [layout.training_indexes(update) for update in range(1, layout.updates + 1)]
    active = {arm: sum(sum(label != -100 for label in rows[index].labels)
                      for indexes in schedule for index in indexes)
              for arm, rows in zip(ARMS, (full, masked))}
    return dict(layouts={arm: layout.manifest(arm) for arm in ARMS},
                schedule_sha256=digest(schedule), active_label_presentations=active,
                reference_denominator='UNCHANGED_FULL_REFERENCE_TOKENS_BOTH_ARMS',
                full_encoded_sha256=digest([asdict(row) for row in full]),
                masked_encoded_sha256=digest([asdict(row) for row in masked]),
                changed_rows=list(range(222, 238)), paired_inputs_identical=True,
                legacy_masks_unchanged=True, teacher_eos_also_masked=True)


def readout_cohort(math_cohort, route_cohort):
    math_tasks = [task for group in math_cohort['held'][:2] for task in group]
    route_worlds = route_cohort['held'][0][:2]
    require(len(math_tasks) == 16 and len(route_worlds) == 2, 'fixed_readout_cohort_shape')
    require(all(task['split'] == 'HELD' for task in math_tasks)
            and all('HELD' in world['master'] for world in route_worlds), 'readout_held_only')
    return dict(math_task_ids=[task['id'] for task in math_tasks],
                math_question_sha256=[task['question_sha256'] for task in math_tasks],
                route_world_masters=[world['master'] for world in route_worlds],
                route_world_sha256=[digest(world) for world in route_worlds],
                selection='FIRST_TWO_EXISTING_HELD_MATH_GROUPS_AND_FIRST_TWO_ROUTE_WORLDS',
                held_outputs_accessed=False, teacher_or_parent_visibility=False)


def protocol():
    return dict(schema='ORCH_TEACHER_BRANCHING_PILOT_DOSE4_V1', source_label=LABEL,
        initial_state_sha256=STATE, initial_base_sha256=BASE, teacher_rows=16,
        teacher_math_rows=8, teacher_route_rows=8, dose=4, updates_per_arm=56,
        arms=list(ARMS), candidate_node='node1', candidate_physical_gpus=[4, 5],
        allocation_status='CANDIDATE_ONLY_MAIN_READINESS_REQUIRED', launch_allowed=False,
        provider_calls=0, parent_calls=0, source_generation_calls=0, fit_calls=0,
        generation_calls_per_arm=dict(math=16, route_max=48, legacy=48),
        generation_calls_pair_max=224, output_caps=dict(math=4096, route=4096, legacy=160),
        output_tokens_pair_max=539648, context=CONTEXT, attempts_per_call=1,
        allocated_seconds_after_future_start=7200, gpu_hours_pair_ceiling=4,
        publisher_quota_changed=False, dose16_authorized=False,
        own_trajectory_success_claim=False, ongoing_l1_allowed=False,
        parent_blind=True, held_output_training_allowed=False)
