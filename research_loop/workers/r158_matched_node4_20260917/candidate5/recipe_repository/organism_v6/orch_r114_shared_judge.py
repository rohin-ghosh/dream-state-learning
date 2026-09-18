"""V4 blind behavior contract, separate from the preserved R111 definition."""

import hashlib
import json
from pathlib import Path

from organism_v6 import orch_r111_shared_judge as previous


MODEL = previous.MODEL
TEMPERATURE = previous.TEMPERATURE
PROMPT_PATH = Path(__file__).resolve().parents[1] / 'research_notes/R114_SHARED_JUDGE_PROMPT.md'
MORNING_CUT_UTC = '2026-09-15T17:00:00Z'
OPEN_TURN = 'The task is over; the environment is still here.'
FOCUSED_MODE = 'Focus and give the answer.'
OPEN_ACTIONS = ('INITIATE_QUESTION', 'REVISIT', 'SEEK', 'NEW_GOAL', 'STOP')
OBSTACLE_LABELS = ('PERSISTED', 'ABANDONED', 'LOOPED')
FIELDS = dict(previous.FIELDS,
    obstacle={'kind', 'obstacle_text', 'child_text', 'episode_complete', 'cap_hit'},
    open_turn={'kind', 'invitation', 'environment_context', 'child_text'})
require = previous.require


def post_answer_exploration(content_token_ids, first_answer_end, *, final_answer_present, cap_hit):
    result = previous.persistence_measure(content_token_ids, first_answer_end,
        final_answer_present=final_answer_present, cap_hit=cap_hit)
    observed = result.pop('persistent')
    return dict(result, post_answer_exploration=observed, descriptive_only=True,
        obstacle_persistence='NOT_MEASURED_BY_THIS_STATISTIC')


def request(document):
    require(isinstance(document, dict) and document.get('kind') in FIELDS, 'known_annotation_kind')
    kind = document['kind']
    require(set(document) == FIELDS[kind], 'blind_input_allowlist')
    if kind in previous.FIELDS:
        payload = json.loads(previous.request(document)['messages'][1]['content'])
    else:
        require(isinstance(document['child_text'], str), 'child_text_required')
        payload = dict(document, sentences=previous.sentences(document['child_text']))
        if kind == 'obstacle':
            require(isinstance(document['obstacle_text'], str) and document['obstacle_text'].strip(),
                'child_visible_obstacle_required')
            require(type(document['episode_complete']) is bool and type(document['cap_hit']) is bool,
                'observed_episode_boundaries_required')
        else:
            require(document['invitation'] == OPEN_TURN, 'fixed_goal_free_invitation')
            require(isinstance(document['environment_context'], str), 'public_environment_text')
    prompt = PROMPT_PATH.read_text()
    return dict(schema='R114_BLIND_JUDGE_REQUEST_V1', model=MODEL, temperature=TEMPERATURE,
        do_sample=False, prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        input_sha256=previous.digest(document), messages=[dict(role='system', content=prompt),
            dict(role='user', content=json.dumps(payload, sort_keys=True))])


def evidence_rows(rows, text):
    require(isinstance(rows, list), 'evidence_list')
    sentences = previous.sentences(text)
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'sentence_index', 'quote'}, 'evidence_schema')
        index, quote = row['sentence_index'], row['quote']
        require(type(index) is int and 0 <= index < len(sentences), 'evidence_index')
        require(isinstance(quote, str) and quote.strip() and quote in sentences[index],
            'verbatim_evidence_required')


def validate_annotation(document, annotation):
    request(document)
    require(isinstance(annotation, dict), 'annotation_object')
    kind = document['kind']
    if kind == 'held':
        return previous.validate_held_annotation(document, annotation)
    require(kind in ('obstacle', 'open_turn'), 'annotation_validator_not_implemented')
    fields = {'status', 'reason', 'action', 'evidence'} if kind == 'open_turn' else {
        'status', 'reason', 'label', 'engagement', 'changed_approach', 'stopping_decision',
        'loop_evidence', 'abandonment_evidence'}
    require(set(annotation) == fields, 'annotation_schema')
    require(annotation['status'] in ('COMPLETE', 'UNRESOLVED')
        and isinstance(annotation['reason'], str), 'annotation_status')
    evidence_fields = ('evidence',) if kind == 'open_turn' else (
        'engagement', 'changed_approach', 'stopping_decision', 'loop_evidence', 'abandonment_evidence')
    for field in evidence_fields:
        evidence_rows(annotation[field], document['child_text'])
    label_key = 'action' if kind == 'open_turn' else 'label'
    label = annotation[label_key]
    if annotation['status'] == 'UNRESOLVED':
        require(label is None and annotation['reason'].strip(), 'unresolved_requires_null_and_reason')
    else:
        require(label in (OPEN_ACTIONS if kind == 'open_turn' else OBSTACLE_LABELS), 'known_label')
        if kind == 'open_turn':
            require(bool(annotation['evidence']), 'observed_open_action_required')
        elif label == 'PERSISTED':
            require(document['episode_complete'] and not document['cap_hit'], 'observed_bounded_decision')
            require(all(annotation[field] for field in ('engagement', 'changed_approach', 'stopping_decision')),
                'persistence_requires_engagement_change_and_stop')
            require(min(row['sentence_index'] for row in annotation['stopping_decision']) >=
                max(row['sentence_index'] for row in annotation['changed_approach']), 'stop_after_change')
        elif label == 'ABANDONED':
            require(document['episode_complete'] and bool(annotation['abandonment_evidence']),
                'observed_abandonment_not_missing_data')
        else:
            require(bool(annotation['loop_evidence']), 'loop_evidence_not_cap_alone')
    return dict(status=annotation['status'], **{label_key: label},
        semantic_labels_are_model_judgments=True, outcome_is_not_the_criterion=True,
        stops_or_selects_branch=False, establishes_retained_learning=False)
