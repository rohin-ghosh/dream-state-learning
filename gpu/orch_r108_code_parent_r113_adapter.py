"""CPU-only F3 request adapter for Hubble's existing R113 parent broker."""

import math
import re

from organism_v6 import orch_r108_code_parent_r113_f3 as policy


def request(task, events, *, identifier, life_id, cycle, episode, phase, lane_deadline_unix):
    policy.require(isinstance(identifier, str) and re.fullmatch('[a-zA-Z0-9_-]{1,100}', identifier), 'request_id')
    policy.require(isinstance(life_id, str) and life_id, 'life_id')
    policy.require(type(cycle) is int and cycle >= 0 and type(episode) is int and episode in (0, 1), 'scheduled_position')
    policy.require(phase in ('experience', 'presleep_metacognition', 'reflection'), 'parent_train_phase')
    policy.require(type(lane_deadline_unix) in (int, float) and math.isfinite(lane_deadline_unix), 'absolute_existing_deadline')
    train = {row['task_id']: row for row in policy.tasks('TRAIN')}
    policy.require(task.get('task_id') in train and task == train[task['task_id']], 'fixed_train_task_only')
    visible = policy.public_events(events)
    children = [event for event in events if event.get('actor') == 'child'
        and event.get('split') == 'TRAIN' and event.get('visibility') == 'CHILD_VISIBLE']
    policy.require(children and all(event.get('completed_response') is True for event in children), 'completed_child_response_required')
    wire_events = []
    for event in visible:
        wire = {key: event[key] for key in ('sequence', 'actor', 'text', 'source_sha256', 'event_type')}
        wire['visibility'] = 'TRAIN_PUBLIC'
        if wire['actor'] == 'checker':
            wire['actor'] = 'oracle'
        if wire['event_type'] == 'checker_feedback':
            wire['event_type'] = 'checker_output'
        if 'child_received' in event:
            wire['child_received'] = event['child_received']
        wire.update({key: event[key] for key in policy.FEEDBACK_KEYS if key in event})
        wire_events.append(wire)
    policy.require(any(event['actor'] == 'child' and event['text'] for event in wire_events), 'actual_child_text_required')
    payload = dict(schema='r111_train_public_v1', life_id=life_id, game='code', cycle=cycle, episode=episode,
        phase=phase, task_id=task['task_id'], task_provenance=dict(split='TRAIN',
            task_sha256=task['content_sha256'], cohort_sha256=policy.digest(list(train.values()))), events=wire_events)
    return dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload), lane_deadline_unix=lane_deadline_unix)
