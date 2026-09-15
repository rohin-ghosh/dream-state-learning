"""Versioned content eligibility without changing historical math labels."""

import hashlib

from organism_v6 import orch_math_rich as original


CONTENT_AXES = ('grounded_operations', 'checkable_expectation', 'reusable_content',
                'no_padding', 'neutral_prefix_compatible')
POLICY = 'ROHIN98_CONTENT_READMISSION_V1'


def reassess(row, decision, gold_review, raw_call_sha256, excluded_ids=()):
    target_hash = hashlib.sha256(row['target'].encode()).hexdigest()
    if row['target_sha256'] != target_hash or row['call']['raw'] != row['target']:
        raise ValueError('source_target_mismatch')
    if decision.get('target_sha256') != target_hash:
        raise ValueError('review_target_mismatch')
    if decision.get('student_prefix_sha256') != original.digest(row['student_prefix']):
        raise ValueError('review_prefix_mismatch')
    if decision.get('raw_call_sha256') != raw_call_sha256:
        raise ValueError('review_capture_mismatch')
    if decision.get('full_text_read') is not True or not decision.get('reason'):
        raise ValueError('attributed_fulltext_review_required')
    spans = decision.get('evidence_spans', [])
    if not spans or any(not span.strip() or span not in row['target'] for span in spans):
        raise ValueError('review_evidence_mismatch')
    if decision.get('status') not in ('PASS', 'FAIL', 'UNRESOLVED'):
        raise ValueError('original_status_required')
    reasons = []
    if row['task_id'] in excluded_ids:
        reasons.append('held_task')
    if gold_review.get('status') != 'VALID':
        reasons.append('gold_not_validated')
    elif original.number(gold_review['independent_answer']) != original.number(row['gold']):
        raise ValueError('gold_answer_mismatch')
    if not row['outcome_pass'] or original.final_value(row['target']) != original.number(row['gold']):
        reasons.append('incorrect_or_missing_registered_final')
    if not row['call']['terminal'] or row['call']['truncated']:
        reasons.append('incomplete_native_output')
    for axis in CONTENT_AXES:
        if decision.get(axis) is not True:
            reasons.append('content_axis_unresolved_or_failed:' + axis)
    if not decision.get('prefix_reason'):
        reasons.append('prefix_disposition_missing')
    count = len(row['call']['token_ids']) - int(row['call']['terminal'])
    if count <= 0 or count != row['generated_tokens']:
        raise ValueError('native_token_count_mismatch')
    return dict(policy=POLICY, eligible=not reasons, reasons=reasons,
                target_sha256=target_hash, source_capture_sha256=raw_call_sha256,
                original_admitted=row['admitted'], original_semantic_status=row['semantic_status'],
                original_token_contract_pass=row['token_contract_pass'],
                first_person=decision.get('first_person'), generated_tokens=count,
                length_tag='under150' if count < 150 else 'over400' if count > 400 else '150to400',
                register_is_gate=False, length_is_quality_gate=False,
                content_axes={axis: decision[axis] for axis in CONTENT_AXES},
                branching_status='NOT_ASSESSED_BY_THIS_EXISTING_REVIEW',
                trainer_context_and_question_hash_exclusions_still_required=True,
                independent_review=False)
