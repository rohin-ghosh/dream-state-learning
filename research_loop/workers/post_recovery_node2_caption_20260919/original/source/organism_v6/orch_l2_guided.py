"""Episode-local coach hooks and exact neutral-prefix captures."""

from copy import deepcopy

from organism_v6 import orch_full_rich as rich
from organism_v6 import orch_l2_shared as shared


def episode(world, task, generate, store, parent=None, telemetry=None, *, rich_contract=True):
    current, ports = task['node'], list(task['ports'])
    public = [dict(role='system', content=rich.SYSTEM),
              dict(role='user', content=rich.readout.display(current, task, ports))]
    reads, routes, captures, interventions = [], [], [], []
    reason = 'actor_call_cap'
    for turn in range(6):
        intervention = None
        if parent is not None and turn in (0, 2, 4):
            context = dict(kind='coach', turn=turn, task=deepcopy(task),
                           public_messages=deepcopy(public),
                           prior_parent_messages=deepcopy(interventions),
                           learner=deepcopy(telemetry or {}))
            intervention = parent(context)
            interventions.append(deepcopy(intervention))
        messages = deepcopy(public)
        if rich_contract:
            messages[0]['content'] += '\n\n' + rich.GUIDANCE
        for previous in interventions:
            if previous.get('speak') and previous.get('message'):
                messages[-1]['content'] += '\n\nPARENT LEARNING COACH:\n' + previous['message']
        capture = dict(turn=turn, messages=deepcopy(messages), student_prefix=deepcopy(public),
                       prior_reads=deepcopy(reads), response=None, error=None, command=None,
                       parent_messages=deepcopy(interventions))
        captures.append(capture)
        try:
            response = generate(messages)
            capture['response'] = response
            raw = rich.readout.response_text(response)
            command = raw.rstrip('\n').splitlines()[-1]
            capture['command'] = command
            public.append(dict(role='assistant', content=raw))
            if command.startswith('READ EVENT '):
                address = command[len('READ EVENT '):]
                rich.hop.require(address in task['events'] and address not in reads and len(reads) < 4,
                                 'invalid_or_repeated_read')
                reads.append(address)
                public.append(dict(role='user', content=store.get(address, rich.readout.UNAVAILABLE)))
            elif command.startswith('ROUTE '):
                port = command[len('ROUTE '):]
                rich.hop.require(port in ports and len(routes) < 2, 'invalid_route')
                route = next(edge for edge in world['edges'] if edge['node'] == current and edge['port'] == port)
                routes.append(dict(source=current, port=route['port'], destination=route['outcome'], receipt=route['receipt']))
                current = route['outcome']
                ports = sorted(edge['port'] for edge in world['edges'] if edge['node'] == current)
                public.append(dict(role='user', content=rich.hop.micro.RECEIPT_WIRE.format(**routes[-1])
                                   + '\n' + rich.readout.display(current, task, ports)))
                if current == task['goal'] or not ports:
                    reason = 'reached_goal' if current == task['goal'] else 'dead_end'
                    break
            else:
                raise ValueError('action_last_required')
        except Exception as error:
            capture['error'] = dict(type=type(error).__name__, message=str(error))
            reason = 'capture_error'
            break
    result = dict(task=deepcopy(task), current=current, reads=reads, routes=routes,
                  captures=captures, messages=public, parent_messages=interventions,
                  actor_calls=len(captures), terminal_reason=reason,
                  correct=current == task['goal'] and len(routes) == 2)
    rich.readout.score(world, task, result)
    return result


def learner_telemetry(episodes, cycle, admitted_previous=0):
    return dict(cycle=cycle, completed_experience_episodes=len(episodes),
                successful_experience_episodes=sum(item['correct'] for item in episodes),
                previous_admitted_rows=admitted_previous,
                recent_failures=[item['terminal_reason'] for item in episodes[-4:]],
                previous_last_responses=[item['captures'][-1]['response']['raw']
                    for item in episodes[-2:] if item['captures'][-1].get('response')],
                algorithm='Frozen base; only own successful grounded raw turns replayed four times in LoRA; fresh AdamW each sleep.',
                readout_visibility='NO_READOUT_DATA')


def admitted_captures(episode_record, reviews):
    indexed = {review['capture_sha256']: review for review in reviews}
    result = []
    for capture in episode_record['captures']:
        gate = rich.row_gate(episode_record, capture, indexed.get(rich.digest(capture)))
        result.append(dict(capture_sha256=rich.digest(capture), gate=gate, capture=capture))
    return result
