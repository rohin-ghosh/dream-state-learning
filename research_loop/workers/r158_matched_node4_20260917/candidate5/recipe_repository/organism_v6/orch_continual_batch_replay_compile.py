"""TRAIN-only checkpoint replay compilation; fitting and held readouts are external."""

import hashlib
import json
from pathlib import Path, PurePosixPath

from organism_v6 import orch_continual_batch as policy


BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'


def compile_row(row, native_call, registration, exclusions):
    policy.require(registration['source_kind'] == 'CHECKPOINT_DERIVED_TRAIN' and
        registration['source_purpose'] == 'L1_EXTERNAL_GENERATION' and registration['split'] == 'TRAIN', 'registered_checkpoint_TRAIN_only')
    policy.require(registration['parenting_experience'] is False and registration['teacher_exemplars'] is False and
                   registration['held_readout_outputs'] is False, 'no_parenting_teacher_or_held_experiences')
    policy.require(registration['native_root'] in registration['allowlisted_generation_roots'], 'registered_source_root_required')
    native_path = PurePosixPath(row['provenance']['source_native_path'])
    source_root = PurePosixPath(registration['native_root'])
    policy.require('..' not in native_path.parts and source_root in native_path.parents, 'native_source_root_binding')
    policy.require(row['actor']['state_sha256'] == registration['source_state_sha256'] == registration['lineage']['child_state_sha256'] and
                   row['actor']['base_sha256'] == registration['base_sha256'] == BASE, 'exact_checkpoint_and_frozen_base_required')
    policy.require(row['task_id'] not in exclusions['math_ids'] and row['question_sha256'] not in exclusions['question_hashes'], 'held_source_excluded')
    policy.require(not any(identifier in json.dumps(row['student_prefix'], ensure_ascii=False) + row['target'] for identifier in exclusions['route_ids']), 'held_route_excluded')
    policy.require(row['provenance']['parenting_experience'] is False and row['provenance']['source_purpose'] == 'L1_EXTERNAL_GENERATION', 'row_source_purpose_required')
    policy.require(row['mechanical_pass'] is True and row['outcome_pass'] is True and row['token_contract_pass'] is True and
                   row['batch_training_allowed'] is True, 'source_outcome_and_batch_admission_required')
    response = native_call['response']
    policy.require(response['raw'] == row['target'] and hashlib.sha256(row['target'].encode()).hexdigest() == row['target_sha256'], 'original_native_target_binding')
    policy.require(response['terminal'] is True and response['truncated'] is False, 'complete_native_response_required')
    tokens = response['token_ids']
    policy.require(tokens and tokens[-1] == registration['eos_token_id'], 'native_eos_binding')
    encoding = row['training_encoding']
    inputs, labels = encoding['input_ids'], encoding['labels']
    policy.require(len(inputs) == len(labels) <= 2048 and all(type(value) is int for value in inputs + labels), 'exact_supported_context_no_crop')
    positions = [index for index, value in enumerate(labels) if value != -100]
    policy.require(positions and positions == list(range(positions[0], positions[0] + len(tokens))) and
                   [labels[index] for index in positions] == tokens and all(inputs[index] == labels[index] for index in positions),
                   'only_exact_own_native_target_supervised')
    review = row.get('review')
    if review:
        policy.require(review['status'] == 'PASS' and review['target_sha256'] == row['target_sha256'], 'bound_sampled_PASS_only')
        policy.validate_review([row], dict(reviews=[review]))
    return dict(target_sha256=row['target_sha256'], task_id=row['task_id'], native_source_path=str(native_path),
        original_native_task_id=row['provenance'].get('original_native_task_id', row['task_id']),
        native_source_sha256=row['provenance']['raw_call_sha256'], source_state_sha256=row['actor']['state_sha256'],
        source_kind='CHECKPOINT_DERIVED_TRAIN', source_lineage=registration['lineage'],
        encoding_sha256=policy.digest(encoding), sequence_length=len(inputs), supervised_tokens=len(tokens),
        individual_semantic_status='PASS' if review else 'UNREVIEWED',
        branch_metrics=review.get('branch_metrics') if review else dict(measurement_status='UNKNOWN',
            semantic_distinct_approaches_considered=None, semantic_distinct_approaches_pursued=None, repetition_failure=None),
        coherence_tag=review.get('coherence_tag', 'UNKNOWN') if review else 'UNKNOWN',
        instruction_regime=row['provenance'].get('instruction_regime', 'UNKNOWN'),
        mechanical_branch_counts=row['provenance'].get('mechanical_branch_counts'),
        self_reported_branch_counts=row['provenance'].get('self_reported_branch_counts'))


def read_bound(reference, root):
    path = Path(reference['path'])
    policy.require(path.is_absolute() and '..' not in path.parts and
                   Path(root).resolve() in path.resolve().parents, 'file_outside_registered_native_root')
    payload = path.read_bytes()
    policy.require(hashlib.sha256(payload).hexdigest() == reference['sha256'], 'immutable_file_hash_mismatch')
    return json.loads(payload)


def normalize_native_call(call, task, registration, provenance):
    native_format = registration.get('native_format', 'NEUTRAL_MATH_NATIVE_V1')
    if native_format == 'NEUTRAL_MATH_NATIVE_V1':
        return call
    policy.require(native_format == 'NODE2_CHECKPOINT99_MATH_V1', 'unsupported_native_replay_format')
    policy.require(call['family'] == 'math' and call['stage'] == 'final_0' and
                   call['condition'] == 'ORIGINAL_RICH' and len(call['messages']) == 2,
                   'checkpoint99_single_pass_math_only')
    policy.require(call['source_task_id'] == task['id'] and call['task_id'] == provenance['original_native_task_id'],
                   'original_repeated_TRAIN_task_binding')
    policy.require(call['generator_identity']['state_sha256'] == registration['source_state_sha256'] and
                   call['generator_identity']['base_sha256'] == BASE and
                   call['source_checkpoint_commit_sha256'] == registration['lineage']['checkpoint_commit_sha256'] and
                   call['source_code_sha256'] == registration['source_code_sha256'], 'per_call_checkpoint_source_binding')
    policy.require(call['outcome']['correct'] is True and call['outcome']['admitted'] is False and
                   call['trainingAllowed'] is False, 'original_unadmitted_observed_oracle_required')
    policy.require(policy.math.final_value(call['response']['raw']) == policy.math.number(task['gold']),
                   'original_math_oracle_failure')
    return dict(call, task_id=task['id'], gold=task['gold'], stage='source', strategy=call['condition'],
                outcome=dict(call['outcome'], outcome_pass=call['outcome']['correct']))


def compile_bound_batch(request, tokenizer):
    root = request['native_evidence_root']
    registration = read_bound(request['registration'], root)
    admission = policy
    if registration.get('arm') == 'ROHIN101_FULL256_MATH32_V1':
        from organism_v6 import orch_continual_batch_replay32 as admission
        policy.require(registration['source_state_sha256'] == admission.STATE and registration['batch_size'] == 32,
                       'separate_FULL256_32_arm_only')
    policy.require(registration['native_root'] in registration['allowlisted_generation_roots'],
                   'registered_source_root_required')
    registry = read_bound(request['source_registry'], root)
    registered = registry['sources'][registration['native_root']]
    for key in ('source_kind', 'source_purpose', 'split', 'parenting_experience', 'teacher_exemplars',
                'held_readout_outputs', 'source_state_sha256', 'base_sha256'):
        policy.require(registered[key] == registration[key], 'registered_source_purpose_or_identity_drift')
    exclusions = read_bound(request['exclusions'], root)
    checkpoint = read_bound(request['checkpoint_handoff'], root)
    policy.require(request['checkpoint_handoff']['sha256'] == registration['lineage']['checkpoint_manifest_sha256'],
                   'checkpoint_manifest_lineage_binding')
    policy.require(checkpoint['adapter']['state_sha256'] == registration['source_state_sha256'] and
                   checkpoint['adapter']['base_sha256'] == registration['base_sha256'] == BASE,
                   'checkpoint_handoff_actor_binding')
    loaded = read_bound(request['loaded'], root)
    policy.require(loaded['observed']['state_sha256'] == registration['source_state_sha256'] and
                   loaded['observed']['base_sha256'] == BASE, 'native_loaded_child_binding')
    tasks = read_bound(request['tasks'], root)['tasks']
    policy.require(len({task['id'] for task in tasks}) == len(tasks), 'duplicate_source_tasks')
    tasks = {task['id']: task for task in tasks}
    candidates = read_bound(request['candidates'], root)
    reviews = read_bound(request['reviews'], root)
    sample = read_bound(request['sample'], root)
    selected = admission.sample(candidates)
    policy.require(sample['semantic_results_seen'] is False and
                   sample['candidates_sha256'] == request['candidates']['sha256'] and
                   sample['registration_sha256'] == request['registration']['sha256'] and
                   sample['sample_target_sha256s'] == [row['target_sha256'] for row in selected],
                   'prospective_sample_binding')
    policy.validate_review(selected, dict(reviews=reviews))
    decision, exported = admission.adjudicate(candidates, reviews)
    policy.require(decision['accepted'], 'batch_author_admission_required')
    checked, skipped = {}, []
    for row in candidates:
        provenance = row['provenance']
        policy.require(provenance['source_registry_sha256'] == request['source_registry']['sha256'],
                       'row_source_registry_binding')
        native_call = read_bound(dict(path=provenance['source_native_path'],
                                     sha256=provenance['raw_call_sha256']), registration['native_root'])
        intent = read_bound(provenance['native_intent_ref'], registration['native_root'])
        policy.require(intent and all(native_call.get(key) == value for key, value in intent.items()),
                       'native_intent_binding')
        policy.require(row['actor'] == loaded['observed'], 'row_loaded_actor_binding')
        native_call = normalize_native_call(native_call, tasks[row['task_id']], registration, provenance)
        if native_call['stage'] != 'source':
            previous = read_bound(provenance['previous_own_call_ref'], registration['native_root'])
            policy.require(previous['task_id'] == row['task_id'] and previous['stage'] == 'source' and
                           previous['response']['raw'] == native_call['messages'][2]['content'],
                           'prior_own_response_binding')
        try:
            rebuilt = policy.mechanical(native_call, tasks[row['task_id']], loaded,
                dict(initial=loaded['observed']), tokenizer, exclusions, provenance)
        except ValueError as error:
            if str(error) != 'skip_unsupported_traincontext_no_crop':
                raise
            skipped.append(dict(target_sha256=row['target_sha256'], native_source_path=provenance['source_native_path'],
                                native_source_sha256=provenance['raw_call_sha256'], reason=str(error)))
            continue
        policy.require(all(rebuilt[key] == row[key] for key in rebuilt), 'native_recompile_row_drift')
        checked[row['target_sha256']] = native_call
    compiled, rows = [], []
    for row in exported:
        if row['target_sha256'] in checked:
            compiled.append(compile_row(row, checked[row['target_sha256']], registration, exclusions))
            rows.append(row)
    policy.require(compiled, 'no_supported_replay_rows')
    return dict(registration=registration, compiled=compiled, rows=rows, skipped=skipped,
                batch_decision=decision, input_bindings=request,
                compiler_scope='NEUTRAL_OR_NODE2_CHECKPOINT99_MATH_ONLY_ROUTE_CODE_REQUIRE_BOUND_ADAPTER')


def handoff(compiled, registration, native_rows_path, native_rows_sha256):
    scope = registration.get('fit_scope', 'CURRENT_MIXED_CONTINUAL_APPEND')
    policy.require(scope in ('CURRENT_MIXED_CONTINUAL_APPEND', 'ISOLATED_PAIRED_WINDOW',
                            'PENDING_LAPLACE_ISOLATED_PAIRED_WINDOW'), 'explicit_fit_scope')
    if scope == 'ISOLATED_PAIRED_WINDOW':
        policy.require(registration.get('paired_window_id') and registration.get('paired_initial_state_sha256') and
                       registration.get('control') == 'MATCHED_MASKED_TARGET', 'prospective_paired_window_binding_required')
    return dict(schema='ORCH_REPLAY_COMPILE_HANDOFF_V1', recipient='Laplace', source_kind='CHECKPOINT_DERIVED_TRAIN',
        native_rows_path=native_rows_path, native_rows_sha256=native_rows_sha256, source_state_sha256=registration['source_state_sha256'],
        source_lineage=registration['lineage'], compiled_rows=compiled, fit_scope=scope,
        paired_window_id=registration.get('paired_window_id'), source_split='TRAIN',
        raw_storage='NATIVE_ONLY', held_readout_outputs_compiled=False, teacher_exemplars_compiled=False,
        training_application_allowed=scope != 'PENDING_LAPLACE_ISOLATED_PAIRED_WINDOW',
        parenting_experiences_compiled=False, paired_fit_executed=False, held_readout_executed=False,
        claim_scope='NO_ISOLATED_OWN_OUTPUT_CLAIM_WITHOUT_LAPLACE_PAIRED_FIT_AND_RICHNESS_FIRST_HELD_READOUT',
        preserve_adapter_optimizer_rng_cursor=True, unsampled_individual_semantics='UNREVIEWED_UNKNOWN')
