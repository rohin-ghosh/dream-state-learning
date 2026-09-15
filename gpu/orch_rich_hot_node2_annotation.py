"""Validate human/author semantic annotations; never infer branching from words."""

from collections import Counter
import hashlib
import json


RELEVANCE = {'NONE_IDENTIFIED', 'CONDITIONAL_INACTIVE', 'DECISION_OR_SCOPE', 'OPTIONAL_PITFALL'}
OBSERVATION = {'NO_ALTERNATIVE', 'CONDITIONAL_CHECK', 'IMPLICIT_DECISION',
               'DECISIVE_CLARIFICATION', 'EXPLICIT_ALTERNATIVE'}


def validate_annotation(annotation, capture, expected_sha256, raw_bytes):
    if hashlib.sha256(raw_bytes).hexdigest() != expected_sha256:
        raise ValueError('raw_capture_binding_changed')
    if json.loads(raw_bytes) != capture:
        raise ValueError('parsed_capture_differs_from_bound_bytes')
    if (annotation['task_id'], annotation['condition']) != (capture['task_id'], capture['condition']):
        raise ValueError('annotation_identity_mismatch')
    if annotation['relevance'] not in RELEVANCE or annotation['observation'] not in OBSERVATION:
        raise ValueError('unknown_semantic_category')
    if annotation.get('full_text_read') is not True or not annotation.get('rationale'):
        raise ValueError('full_text_author_annotation_required')
    if type(annotation.get('grounded_rejection_or_discrimination')) is not bool:
        raise ValueError('explicit_grounding_disposition')
    spans = annotation.get('response_spans', [])
    if not spans or any(not span or span not in capture['response']['raw'] for span in spans):
        raise ValueError('response_evidence_span_mismatch')
    if annotation.get('admitted') is not False or annotation.get('trainingAllowed') is not False:
        raise ValueError('descriptive_annotation_cannot_admit')
    return dict(annotation, native_capture_sha256=expected_sha256,
                target_sha256=hashlib.sha256(capture['response']['raw'].encode()).hexdigest(),
                original_outcome=capture['outcome'], response_span_offsets=[
                    dict(start=capture['response']['raw'].index(span), end=capture['response']['raw'].index(span) + len(span))
                    for span in spans])


def summarize(rows):
    if len({(row['condition'], row['task_id']) for row in rows}) != len(rows):
        raise ValueError('duplicate_sample_row')
    return dict(sample_size=len(rows), author_descriptive_only=True,
                relevance=dict(Counter(row['relevance'] for row in rows)),
                observation=dict(Counter(row['observation'] for row in rows)),
                by_condition={condition: dict(Counter(row['observation'] for row in rows if row['condition'] == condition))
                              for condition in sorted({row['condition'] for row in rows})},
                explicit_alternative_with_grounded_reason=sum(row['observation'] == 'EXPLICIT_ALTERNATIVE'
                    and row['grounded_rejection_or_discrimination'] for row in rows),
                under150_tokens=sum(row['original_outcome']['content_tokens'] < 150 for row in rows),
                original_registered_correct=sum(row['original_outcome']['category'] == 'registered_correct' for row in rows),
                qualification_decisions=0, register_or_length_rejections=0, admission_changes=0,
                keyword_branching_classifier=False, paired_condition_comparison=False)
