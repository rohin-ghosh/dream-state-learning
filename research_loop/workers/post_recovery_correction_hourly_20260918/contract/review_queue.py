"""Bounded source-reference triage, never automatic semantic adjudication."""

import hashlib
import json

from audit import exposure_id, frames, ref, text_sha


OWNER = 'Main: semantic review handoff requested; acceptance not inferred'


def identity(journal_id, category, source):
    value = json.dumps([journal_id, category, source], separators=(',', ':'))
    return hashlib.sha256(value.encode()).hexdigest()


def output_ref(frame):
    return dict(request=ref(frame['request']), response=ref(frame['response']),
        committed=ref(frame['commit']), stage=frame['stage'],
        stage_receipt=ref(frame['stage_receipt']))


def build_queue(evidence, label, traces=(), previous=None, limit=4):
    if not 1 <= limit <= 8:
        raise ValueError('bounded_review_queue_limit')
    previous = previous or {}
    journal_id = evidence['journal_id']
    if previous.get('journal_id', journal_id) != journal_id:
        raise ValueError('review_cursor_incarnation_changed')
    through = evidence['through']['index']
    prior_through = previous.get('through_index')
    if prior_through is not None and through < prior_through:
        raise ValueError('review_cursor_must_not_move_backwards')
    generation = previous.get('generation', 0) + 1
    ordered = frames(evidence)
    reviewed = {trace['correction_key'] for trace in traces}
    inboxes = {row['event_id']: row for row in evidence['records'] if row['kind'] == 'INBOX'}
    inputs = {}
    for request in sorted((row for row in evidence['records'] if row['kind'] == 'REQUEST'), key=lambda row: row['index']):
        if request.get('masked') is not True:
            raise ValueError('review_queue_requires_verified_masked_render')
        for event in request['external']:
            key = exposure_id(event)
            if key in inputs or key in reviewed:
                continue
            following = [frame for frame in ordered if frame['request']['index'] >= request['index']]
            next_act = next((frame for frame in following if frame['stage'] == 'ACT'), None)
            inbox = inboxes.get(event['event_id'])
            inputs[key] = dict(queue_id=identity(journal_id, 'input', key),
                kind='UNADJUDICATED_RENDERED_INPUT', status='PENDING_MAIN_SEMANTIC_REVIEW',
                feedback_key=key, actor=event['actor'], event_id=event['event_id'],
                source_sha256=event['source_sha256'], body_sha256=text_sha(event['text']),
                inbox=ref(inbox) if inbox else None, first_observed_request=ref(request),
                following_outputs=[output_ref(frame) for frame in following[:3]],
                next_actual_ACT=output_ref(next_act) if next_act else None,
                new_since_previous_collection=prior_through is not None and request['index'] > prior_through)
    windows = list(previous.get('pending_output_windows', []))
    new_acts = [frame for frame in ordered if prior_through is not None
        and frame['stage'] == 'ACT' and frame['response']['index'] > prior_through]
    if new_acts:
        window = dict(queue_id=identity(journal_id, 'output_window', [prior_through, through]),
            kind='NEW_ACTS_REQUIRE_SEMANTIC_REVIEW', status='PENDING_MAIN_SEMANTIC_REVIEW',
            after_index=prior_through, through_index=through, actual_new_ACT_count=len(new_acts),
            outputs=[output_ref(frame) for frame in new_acts[:3]],
            latest_ACT=output_ref(new_acts[-1]),
            existing_annotation_keys=sorted(reviewed), new_since_previous_collection=True)
        if all(item['queue_id'] != window['queue_id'] for item in windows):
            windows.append(window)
    current_window = windows[-1]['queue_id'] if new_acts else None
    windows = [dict(item, new_since_previous_collection=item['queue_id'] == current_window) for item in windows]
    pending = list(inputs.values()) + windows
    offered = previous.get('offered_generation', {})
    def order(item):
        role_order = 0 if item['kind'] == 'NEW_ACTS_REQUIRE_SEMANTIC_REVIEW' else (1 if item['actor'] == 'parent' else 2)
        record_index = item.get('after_index', item.get('first_observed_request', {}).get('index', 0))
        return (offered.get(item['queue_id'], 0), role_order, record_index, item['queue_id'])
    fresh = sorted((item for item in pending if item['new_since_previous_collection']), key=order)
    selected = fresh[:min(2, limit)]
    selected_ids = {item['queue_id'] for item in selected}
    selected.extend(sorted((item for item in pending if item['queue_id'] not in selected_ids), key=order)[:limit-len(selected)])
    valid_ids = {item['queue_id'] for item in pending}
    offered = {key: value for key, value in offered.items() if key in valid_ids}
    offered.update({item['queue_id']: generation for item in selected})
    cursor = dict(journal_id=journal_id, through_index=through, generation=generation,
        offered_generation=offered, pending_output_windows=windows)
    result = dict(label=label, journal_id=journal_id, owner=OWNER,
        automatic_semantic_review=False, new_semantic_judgments=0, model_calls=0,
        status='PENDING_MAIN_SEMANTIC_REVIEW' if pending else 'NO_PENDING_ITEMS_IN_COLLECTED_WINDOW',
        pending_rendered_input_count=len(inputs), pending_output_windows=len(windows),
        new_rendered_input_count=sum(item['new_since_previous_collection'] for item in inputs.values()),
        new_ACT_count=len(new_acts), pending_total=len(pending), displayed=len(selected),
        omitted_pending_count=len(pending)-len(selected), items=selected,
        selection='At most two fresh items, then least-recently-offered backlog; role/index tie-breaks only.',
        interpretation='All rendered external inputs are triage candidates, including tasks and telemetry; none is classified as a correction here.',
        stage_scope='Following child outputs require actual R184_STAGE; unframed console outputs are not relabelled.')
    return result, cursor
