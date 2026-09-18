"""V4 F3 open-turn request binding; existing broker owns provider dispatch."""

from gpu import orch_r108_code_parent_r113_adapter as previous
from organism_v6 import orch_r108_code_parent_r114_f3 as policy


def request(task, events, *, phase, **position):
    if phase == 'open_turn':
        invitations = [index for index, event in enumerate(events)
            if event.get('actor') == 'environment' and event.get('text') == policy.OPEN_TURN_PROMPT
            and event.get('child_received') is True and event.get('split') == 'TRAIN'
            and event.get('visibility') == 'CHILD_VISIBLE']
        responses = [index for index, event in enumerate(events)
            if event.get('actor') == 'child' and event.get('completed_response') is True
            and event.get('split') == 'TRAIN' and event.get('visibility') == 'CHILD_VISIBLE']
        policy.require(invitations and responses and max(invitations) < max(responses), 'actual_open_invitation_then_child_response')
    value = previous.request(task, events, phase='experience' if phase == 'open_turn' else phase, **position)
    value['payload']['phase'] = phase
    value['payload_sha256'] = policy.digest(value['payload'])
    return value
