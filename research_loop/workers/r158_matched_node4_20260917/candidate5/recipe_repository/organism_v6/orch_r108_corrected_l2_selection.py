"""Separate R108 selection/masking contract; no collection, provider or fit entrypoint."""

import hashlib
import json
from pathlib import Path


SCHEMA = 'ORCH_R108_CORRECTED_L2_SELECTION_V1'
LABEL = 'CORRECTED_L2_CHILD_CONTINUATION'
SINK = 'R108_SEPARATE_CORRECTED_L2_ONLY'
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
KINDS = ('PERCEPTION_UPDATE', 'MEMORY_READ_CHOICE', 'EVIDENCE_HOP_REDIRECT',
         'REASONING_EFFORT_ALLOCATION', 'CONTINUE_OR_STOP')
FIELDS = ('child_state', 'before', 'parent', 'continuation', 'prefix')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def protocol():
    return dict(schema=SCHEMA, source_label=LABEL, sink=SINK, source_purpose='L2_PARENTED_TRAIN',
        split='TRAIN', base_sha256=BASE, maximum_cases=16, parent_text='MASKED_CONTEXT_ONLY',
        targets='EXACT_ACTUAL_CHILD_CONTINUATION_ONLY', historical_stream_append=False,
        original_L1_selector_unchanged=True, held_and_teacher_exemplar_sources=False,
        functional_kinds=list(KINDS), branch_or_hop_count_threshold=None,
        prior_parent_advice_is_not_child_realization=True, causal_effect='UNMEASURED',
        selection_statuses=['CANDIDATE', 'FAILED', 'UNKNOWN'], candidate_is_not_supervision=True,
        no_outcome_voice_length_or_heading_gate=True, context_overflow='SKIP_RETAIN_RAW_NEVER_CROP',
        compile_is_cpu_only=True, fit_or_ingestion_requires_separate_allocation=True,
        positive_and_negative_supervision_from_failed_or_unknown=False)


def verify_bindings(case, registry):
    require(set(case) == set(case_schema()['required']), 'exact_corrected_L2_case_schema')
    require(registry['schema'] == SCHEMA and registry['sink'] == SINK
            and registry['source_purpose'] == 'L2_PARENTED_TRAIN', 'separate_registered_L2_sink')
    require(case['split'] == 'TRAIN' and case['source_root'] in registry['sources'], 'registered_TRAIN_source_only')
    source = registry['sources'][case['source_root']]
    require(source['purpose'] == 'L2_PARENTED_TRAIN' and source['split'] == 'TRAIN'
            and source['teacher_exemplars'] is False, 'no_teacher_or_held_source')
    require(case['task_id'] in source['tasks'] and not case['task_id'].startswith('R107_'),
            'exact_TRAIN_task_not_fixed_capability')
    family = source['tasks'][case['task_id']]
    require(family == case['contamination_family'] and family in registry['train_families']
            and family not in registry['held_families']
            and family not in registry['fixed_capability_families']
            and not set(registry['train_families']) & set(registry['held_families']),
            'whole_contamination_family_exclusion')
    require(set(case['bindings']) == set(FIELDS), 'complete_native_field_bindings')
    expected_kinds = dict(child_state='CHILD_LOADED_IDENTITY', before='CHILD_NATIVE_CALL',
        parent='PARENT_INTERVENTION', continuation='CHILD_NATIVE_CALL', prefix='CHILD_NATIVE_CALL')
    for field in FIELDS:
        binding = case['bindings'][field]
        path = Path(binding['path'])
        require(path.is_absolute() and path.resolve().is_relative_to(Path(case['source_root']).resolve()),
                'source_path_escape')
        artifact = registry['artifacts'][str(path)]
        require(artifact['kind'] == expected_kinds[field] and artifact['split'] == 'TRAIN'
                and artifact['source_root'] == case['source_root'], 'native_role_not_teacher_or_held')
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == artifact['sha256'] == binding['sha256'], 'native_artifact_hash')
        value = json.loads(data)
        for key in binding['pointer']:
            require(isinstance(key, (str, int)) and not isinstance(key, bool), 'exact_json_pointer')
            value = value[key]
        require(value == case[field], 'actual_native_field_not_rewritten')
    require(case['bindings']['prefix']['path'] == case['bindings']['continuation']['path'],
            'prefix_from_same_actual_child_call')
    identity = case['child_state']
    require(identity['base_sha256'] == BASE and identity['state_sha256'] in registry['child_states'],
            'exact_source_child_state')
    require(case['before']['state_sha256'] == case['continuation']['state_sha256'] == identity['state_sha256']
            and case['before']['child_id'] == case['continuation']['child_id'] == identity['child_id'],
            'same_actual_child_no_intervening_fit_confound')
    require(case['before']['finished_unix'] <= case['parent']['started_unix']
            <= case['parent']['finished_unix'] <= case['continuation']['started_unix'], 'actual_intervention_order')
    require(case['parent']['request_visibility'] == 'OWN_TRAIN_PUBLIC_ONLY'
            and case['parent']['teacher_exemplar'] is False, 'parent_blind_to_held_not_teacher_exemplar')
    prefix = case['prefix']
    require(prefix and all(message['role'] in ('system', 'user', 'assistant') for message in prefix),
            'actual_chat_prefix_roles')
    parent_indices = case['parent_message_indices']
    require(parent_indices and len(set(parent_indices)) == len(parent_indices)
            and all(type(index) is int and 0 <= index < len(prefix) for index in parent_indices),
            'parent_context_indices')
    require(all(prefix[index]['role'] == 'user' and case['parent']['text'] in prefix[index]['content']
                for index in parent_indices), 'actual_parent_intervention_in_masked_prefix')
    prior_indices = [index for index, message in enumerate(prefix)
                     if message['role'] == 'assistant' and message['content'] == case['before']['raw']]
    require(prior_indices and max(prior_indices) < min(parent_indices), 'actual_prior_child_before_parent')
    require(case['continuation']['raw'] and case['continuation']['terminal'] is True
            and case['continuation']['truncated'] is False, 'actual_complete_continuation_no_crop')
    return dict(registry_sha256=digest(registry), case_sha256=digest(case),
                source_child_state=identity, original_labels=case['original_labels'])


def span(raw, value):
    require(set(value) == {'start', 'end'} and all(type(item) is int for item in value.values())
            and 0 <= value['start'] < value['end'] <= len(raw), 'exact_native_span')
    return dict(value, text_sha256=text_sha(raw[value['start']:value['end']]))


def select(case, registry, review=None):
    binding = verify_bindings(case, registry)
    result = dict(schema=SCHEMA, source_label=LABEL, sink=SINK, **binding,
        selection_status='UNKNOWN', supervision_status='NONE', trainingAllowed=False,
        historical_continual_allowed=False, target_sha256=text_sha(case['continuation']['raw']),
        parent_intervention_sha256=text_sha(case['parent']['text']),
        original_labels_preserved=True, raw_embedded=False, causal_effect='UNMEASURED')
    if review is None:
        return result
    require(set(review) == {'case_sha256', 'registry_sha256', 'reviewer', 'full_text_read', 'outcome_used',
        'functional_status', 'grounding_status', 'reason', 'prior', 'realization', 'changed_continuation', 'perception_hops'},
        'exact_review_contract_not_branch_count')
    require(review['case_sha256'] == digest(case) and review['registry_sha256'] == digest(registry)
            and review['reviewer'].strip() and review['full_text_read'] is True
            and review['outcome_used'] is False, 'prospective_fulltext_source_review')
    require(review['functional_status'] in ('PASS', 'FAIL', 'UNKNOWN')
            and review['grounding_status'] in ('PASS', 'FAIL', 'UNKNOWN') and review['reason'].strip(),
            'explicit_functional_and_grounding_status')
    evidence = {}
    for field, raw in (('prior', case['before']['raw']), ('realization', case['continuation']['raw']),
                       ('changed_continuation', case['continuation']['raw'])):
        evidence[field] = [span(raw, item) for item in review[field]]
    if review['functional_status'] == 'PASS':
        require(all(evidence.values()) and case['before']['raw'] != case['continuation']['raw'],
                'actual_changed_continuation_not_announcement_only')
        require(max(item['end'] for item in evidence['realization']) <=
                min(item['start'] for item in evidence['changed_continuation']), 'realization_then_continuation')
    hops = []
    for item in review['perception_hops']:
        require(set(item) == {'kind', 'reason', 'evidence'} and item['kind'] in KINDS and item['reason'].strip(),
                'perception_hop_instrument_not_count_gate')
        require(item['evidence'], 'actual_hop_evidence')
        hops.append(dict(kind=item['kind'], reason=item['reason'],
            evidence=[span(case['continuation']['raw'], value) for value in item['evidence']]))
    if review['functional_status'] == review['grounding_status'] == 'PASS':
        result['selection_status'] = 'CANDIDATE'
    elif 'FAIL' in (review['functional_status'], review['grounding_status']):
        result['selection_status'] = 'FAILED'
    result.update(review_sha256=digest(review), functional_status=review['functional_status'],
        grounding_status=review['grounding_status'], evidence=evidence, perception_hops=hops,
        author_supported_not_independent=True, failed_or_unknown_not_negative_targets=True)
    return result


def encode_candidate(case, registry, review, tokenizer, context_limit):
    selected = select(case, registry, review)
    require(selected['selection_status'] == 'CANDIDATE', 'no_failed_unknown_supervision')
    require(type(context_limit) is int and 0 < context_limit <= 8192, 'bounded_new_L2_train_context')
    prefix, target = case['prefix'], case['continuation']['raw']
    require(target != case['parent']['text'], 'no_verbatim_parent_target')
    context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True)
    full = tokenizer.apply_chat_template(prefix + [dict(role='assistant', content=target)],
                                         tokenize=False, add_generation_prompt=False)
    require(full == context + target + tokenizer.eos_token + '\n', 'exact_native_chat_boundary')
    prefix_ids = list(tokenizer.encode(context, add_special_tokens=False))
    target_ids = list(tokenizer.encode(target, add_special_tokens=False))
    suffix_ids = list(tokenizer.encode('\n', add_special_tokens=False))
    input_ids = list(tokenizer.encode(full, add_special_tokens=False))
    require(input_ids == prefix_ids + target_ids + [tokenizer.eos_token_id] + suffix_ids,
            'exact_encoder_boundary_no_token_merge')
    require(tokenizer.decode(input_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False) == full,
            'exact_token_roundtrip')
    require(target_ids and not set(target_ids) & set(tokenizer.all_special_ids), 'no_special_token_target')
    if len(input_ids) > context_limit:
        return dict(selected, encoding_status='SKIP_UNSUPPORTED_TRAIN_CONTEXT', raw_retained=True,
                    sequence_length=len(input_ids), context_limit=context_limit, labels_exported=False)
    labels = [-100] * len(prefix_ids) + target_ids + [tokenizer.eos_token_id] + [-100] * len(suffix_ids)
    return dict(selected, encoding_status='CPU_MASK_VALIDATED_NOT_INGESTED', input_ids=input_ids,
        labels=labels, parent_context_masked=True, all_prior_child_context_masked=True,
        context_length=len(prefix_ids), target_length=len(target_ids), tokenizer_name=tokenizer.name_or_path,
        context_limit=context_limit, labels_are_cpu_candidate_only=True, trainingAllowed=False)


def case_schema():
    return dict(title=SCHEMA, type='object', additionalProperties=False,
        required=['source_root', 'split', 'task_id', 'contamination_family', 'bindings', *FIELDS,
                  'parent_message_indices', 'original_labels'],
        properties={**{field: dict(type='object') for field in ('bindings', 'child_state', 'before', 'parent', 'continuation', 'original_labels')},
            **{field: dict(type='string') for field in ('source_root', 'task_id', 'contamination_family')},
            'split': dict(const='TRAIN'), 'prefix': dict(type='array'),
            'parent_message_indices': dict(type='array', minItems=1, uniqueItems=True, items=dict(type='integer', minimum=0))})
