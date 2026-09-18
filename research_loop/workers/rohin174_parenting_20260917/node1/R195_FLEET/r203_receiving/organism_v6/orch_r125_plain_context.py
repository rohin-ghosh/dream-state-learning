"""Versioned presentation only; callers retain original TRAIN evidence."""

from copy import deepcopy
import json


VERSION = 'R125_PLAIN_CONTEXT_V1'
MARKERS = ('Child assertion (not a verified fact)', 'CHILD_ASSERTION_NOT_VERIFIED_FACT',
           'Recorded environment observation', 'Parent advice (not an observed fact)',
           'source_sha256', 'receipt_sha256', 'TRAIN_COLLECTION', '<|endoftext|>Human:', '<|im_start|>')


def has_scaffolding(text):
    return (any(marker in text for marker in MARKERS)
            or sum('"'+key+'"' in text for key in ('actor', 'episode_id', 'event_id', 'source_id', 'split')) >= 3)


def _repo_tool_feedback(text):
    if not text.startswith('Tool: '):
        return False
    try:
        result = json.loads(text[len('Tool: '):])
    except json.JSONDecodeError:
        return False
    if not isinstance(result, dict):
        return False
    origin = result.get('origin')
    return (result.get('schema') == 'R183_ACTUAL_TOOL_RESULT_V1'
            and result.get('status') == 'COMPLETE' and isinstance(origin, dict)
            and origin.get('actor') == 'child' and origin.get('split') == 'TRAIN'
            and not any(marker in text for marker in MARKERS
                        if marker not in ('source_sha256', 'receipt_sha256')))


def cost_sentence(cost):
    return (f"This segment used {cost['segment_tokens']} tokens in {cost['generation_seconds']:.1f}s; "
            f"context {cost['generation_context_tokens']}/{cost['context_limit']}, "
            f"{cost['since_sleep_tokens']} tokens since sleep.")


def event_message(event):
    text = event.text
    if event.actor == 'environment' and event.source_id.startswith('cost:') and text.startswith('[cost] {'):
        text = cost_sentence(json.loads(text[len('[cost] '):]))
    elif event.actor == 'environment' and event.event_id == 'runtime:birth_budget' and text.startswith('[budget] {'):
        return None
    if has_scaffolding(text) and not (event.actor == 'environment' and event.phase == 'feedback'
                                     and _repo_tool_feedback(text)):
        return None
    return dict(role='assistant' if event.actor == 'child' else 'user', content=text)


def replay_prefix(messages, presentation):
    from organism_v6.orch_r124_train_history import TrainEvent
    result = [dict(role='system', content=presentation['system_prompt']),
              dict(role='user', content=presentation['birth_prompt'])]
    labels = ('Child assertion (not a verified fact)', 'Parent advice (not an observed fact)',
              'Recorded environment observation')
    for message in messages[2:]:
        content = message['content']
        if content.startswith('History omission notice (not a child assertion):\n'):
            result.append(dict(role='user', content='Older context was omitted to make room.'))
            continue
        pieces = content.split('\n', 2)
        if len(pieces) == 3 and pieces[0] in labels:
            fields = json.loads(pieces[1])
            fields.pop('summary_status', None)
            fields.pop('consumed_frontier', None)
            fields['text'] = pieces[2]
            event = TrainEvent.restore(fields)
            expected_role = 'assistant' if event.actor == 'child' else 'user'
            if message['role'] != expected_role:
                raise ValueError('legacy_prefix_actor_role_mismatch')
            plain = event_message(event)
            if plain is not None:
                result.append(plain)
        elif (not has_scaffolding(content)
              or (message['role'] == 'user' and _repo_tool_feedback(content))):
            result.append(deepcopy(message))
    return result


def eligible_rows(rows, presentation):
    accepted, excluded = [], []
    for row in rows:
        if has_scaffolding(row['target']):
            excluded.append(dict(source_sha256=row['source_sha256'], reason='journal_scaffolding_target'))
            continue
        clean = deepcopy(row)
        clean['prefix'] = replay_prefix(row['prefix'], presentation)
        accepted.append(clean)
    return accepted, excluded
