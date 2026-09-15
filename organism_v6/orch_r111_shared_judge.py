"""Blind annotation contract; model execution and raw storage remain node-local."""

import hashlib
import json
from pathlib import Path
import re


PROMPT_PATH = Path(__file__).resolve().parents[1] / 'research_notes/R111_SHARED_JUDGE_PROMPT.md'
MODEL = 'Qwen2.5-14B-Instruct'
TEMPERATURE = 0
CLASSES = ('curiosity', 'perception', 'metacognition', 'persistence', 'reflection',
    'goal/meta-goal', 'self-perception', 'distilled emotion')
FIELDS = {
    'held': {'kind', 'task_text', 'child_text'},
    'reflection': {'kind', 'child_text', 'current_episodes', 'earlier_episodes'},
    'intervention': {'kind', 'before_text', 'after_text', 'before_token_count',
        'after_token_count', 'parent_text', 'intervention_class'},
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def sentences(text):
    require(isinstance(text, str), 'text_required')
    return [part.strip() for part in re.split(r'(?<=[.!?])\s+|\n+', text) if part.strip()]


def persistence_measure(content_token_ids, first_answer_end, *, final_answer_present, cap_hit):
    require(isinstance(content_token_ids, list) and all(type(token) is int for token in content_token_ids),
        'native_content_tokens_required')
    require(type(final_answer_present) is bool and type(cap_hit) is bool, 'observed_termination_required')
    require(first_answer_end is None or type(first_answer_end) is int
        and 0 <= first_answer_end <= len(content_token_ids), 'aligned_first_answer_marker')
    if first_answer_end is None:
        return dict(persistent=False, marker_present=False, post_marker_tokens=0,
            novelty=None, final_answer_present=final_answer_present, cap_hit=cap_hit)
    before = content_token_ids[:first_answer_end]
    after = content_token_ids[first_answer_end:]
    prior = {tuple(before[index:index + 4]) for index in range(max(0, len(before) - 3))}
    grams = [tuple(after[index:index + 4]) for index in range(max(0, len(after) - 3))]
    novelty = sum(gram not in prior for gram in grams) / len(grams) if grams else None
    return dict(persistent=len(after) >= 64 and novelty is not None and novelty >= 0.8
        and final_answer_present and not cap_hit, marker_present=True,
        post_marker_tokens=len(after), novelty=novelty, final_answer_present=final_answer_present,
        cap_hit=cap_hit, measure_only_never_a_branch_stop=True)


def request(document):
    require(isinstance(document, dict) and document.get('kind') in FIELDS, 'known_annotation_kind')
    kind = document['kind']
    require(set(document) == FIELDS[kind], 'blind_input_allowlist')
    payload = dict(document)
    if kind in ('held', 'reflection'):
        payload['sentences'] = sentences(document['child_text'])
    if kind == 'held':
        require(isinstance(document['task_text'], str), 'public_task_text_required')
    if kind == 'reflection':
        for field in ('current_episodes', 'earlier_episodes'):
            require(isinstance(document[field], dict), 'reference_inventory_required')
            require(all(isinstance(key, str) and isinstance(value, str)
                for key, value in document[field].items()), 'reference_text_only')
    if kind == 'intervention':
        require(document['intervention_class'] in CLASSES, 'known_intervention_class')
        require(isinstance(document['parent_text'], str)
            and document['parent_text'].strip() not in ('', '[SILENT]', 'MISSING'), 'actual_intervention_required')
        for side in ('before', 'after'):
            count = document[side + '_token_count']
            require(type(count) is int and 0 <= count <= 200, 'native_window_cap')
            payload[side + '_sentences'] = sentences(document[side + '_text'])
    prompt = PROMPT_PATH.read_text()
    return dict(schema='R111_BLIND_JUDGE_REQUEST_V1', model=MODEL, temperature=TEMPERATURE,
        do_sample=False, prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        input_sha256=digest(document), messages=[dict(role='system', content=prompt),
            dict(role='user', content=json.dumps(payload, sort_keys=True))])


def validate_held_annotation(document, annotation):
    require(document['kind'] == 'held', 'held_annotation_only')
    require(set(annotation) == {'status', 'reason', 'sentences', 'shift_sentence_indices', 'classes'},
        'annotation_schema')
    require(annotation['status'] in ('COMPLETE', 'UNRESOLVED')
        and isinstance(annotation['reason'], str), 'annotation_status')
    require(isinstance(annotation['sentences'], list)
        and isinstance(annotation['shift_sentence_indices'], list)
        and isinstance(annotation['classes'], list), 'annotation_lists')
    count = len(sentences(document['child_text']))
    if annotation['status'] == 'UNRESOLVED':
        require(bool(annotation['reason'].strip()), 'unresolved_reason_required')
        return dict(status='UNRESOLVED', departures_and_returns=None, shifts=None)
    rows = annotation['sentences']
    require([row.get('index') for row in rows] == list(range(count)), 'every_sentence_once')
    for row in rows:
        require(set(row) == {'index', 'label', 'legacy_template_check', 'evidence'}, 'sentence_schema')
        require(row['label'] in ('MAIN', 'DEPART', 'RETURN')
            and type(row['legacy_template_check']) is bool and isinstance(row['evidence'], str), 'sentence_label')
    shifts = annotation['shift_sentence_indices']
    require(len(set(shifts)) == len(shifts) and all(type(index) is int and 0 <= index < count
        for index in shifts), 'shift_indices')
    require(len(set(annotation['classes'])) == len(annotation['classes'])
        and set(annotation['classes']) <= set(CLASSES), 'class_inventory')
    departures, in_departure = 0, False
    for row in rows:
        if row['legacy_template_check']:
            in_departure = False
        elif row['label'] == 'DEPART':
            in_departure = True
        elif row['label'] == 'RETURN':
            if in_departure:
                departures += 1
            in_departure = False
        else:
            in_departure = False
    return dict(status='COMPLETE', departures_and_returns=departures, shifts=len(shifts),
        legacy_template_checks=sum(row['legacy_template_check'] for row in rows),
        semantic_labels_are_model_judgments=True)
