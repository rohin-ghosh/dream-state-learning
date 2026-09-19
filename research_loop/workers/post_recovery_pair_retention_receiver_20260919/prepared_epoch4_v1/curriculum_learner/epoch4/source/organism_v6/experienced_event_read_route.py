"""Pure bounded public READ/ROUTE episode; no native calls, fit or compiler."""

import json
import re

from organism_v6 import experienced_event_microloop as micro


PUBLIC_SYSTEM = (
    'Use the public task and conversation. Identifiers are opaque and case-sensitive. '
    'You may output READ EVENT <listedaddress> or ROUTE <listedport>. '
    'Output exactly one command, optionally followed by LF characters, with no other text. '
    'You have at most three actor calls and two distinct memory reads. '
    'A READ returns the memory reader\'s actual text. A ROUTE commits one port and ends '
    'the episode; transition feedback is available only after commitment. There is no retry.'
)
MAX_ACTOR_CALLS = 3
MAX_READS = 2
TASK_KEYS = frozenset(('node', 'goal', 'ports', 'events'))


def _copy(value):
    return json.loads(json.dumps(value, allow_nan=False))


def _identifier(value, prefix):
    return type(value) is str and re.fullmatch(prefix + r'_[A-Z2-7]{10}', value) is not None


def _check_task(task):
    micro._require(type(task) is dict and set(task) == TASK_KEYS, 'public_task_keys_required')
    micro._require(_identifier(task['node'], 'N') and _identifier(task['goal'], 'N'), 'invalid_public_node_or_goal')
    for key, prefix in (('ports', 'P'), ('events', 'E')):
        values = task[key]
        micro._require(type(values) is list and len(values) == 2
                       and all(_identifier(value, prefix) for value in values)
                       and len(set(values)) == 2, 'two_distinct_public_' + key + '_required')


def public_task(fact):
    """Project a microloop fact to public node/goal/lists, never a target mapping."""
    micro._check_fact(fact)
    return dict(node=fact['node'], goal=fact['outcome'],
                ports=list(fact['public_ports']), events=list(fact['public_events']))


def parse_command(raw):
    """Ignore/count only final LF characters; never repair whitespace or IDs."""
    micro._require(type(raw) is str, 'command_string_required')
    core = raw.rstrip('\n')
    final_lfs = len(raw) - len(core)
    read = re.fullmatch(r'READ EVENT (E_[A-Z2-7]{10})', core)
    if read is not None:
        return dict(kind='READ', value=read.group(1), trailing_lfs=final_lfs)
    return dict(kind='ROUTE', value=micro.parse_action(core + '\n'), trailing_lfs=final_lfs)


def run_episode(task, actor, read_memory, transition):
    """Run at most 3 actor/2 reader calls and one committed transition.

    actor(messages) and read_memory(address) return JSON dictionaries with raw
    str, terminal bool (EOT evidence), truncated bool, and optional native fields.
    transition(port) returns an actual outcome identifier string, not a target.
    Invalid tasks raise before callbacks. Callback/transport/action failures end
    the episode with retained traces. Terminal memory text is never interpreted,
    repaired or screened for correctness. Optional native fields must be JSON.
    """
    _check_task(task)
    task = _copy(task)
    messages = [dict(role='system', content=PUBLIC_SYSTEM), dict(role='user', content=(
        f"ROUTE TASK\nNODE {task['node']}\nGOAL {task['goal']}\n"
        f"PORTS {','.join(task['ports'])}\nEVENTS {','.join(task['events'])}"))]
    result = dict(reached_goal=False, terminal_reason='actor_call_cap', action_calls=0,
                  memory_calls=0, traces=[], messages=messages, chosen_port=None, outcome=None)
    addresses = set()

    def receive(callback, argument, trace):
        result['traces'].append(trace)
        try:
            response = callback(argument)
        except Exception as error:
            trace['error'] = dict(type=type(error).__name__, message=str(error))
            result['terminal_reason'] = trace['kind'] + '_callback_error'
            return None
        if type(response) is dict:
            trace.update({name: response.get(name) if type(response.get(name)) in (str, bool, int, type(None))
                          else None for name in ('raw', 'terminal', 'truncated')})
        try:
            trace['response'] = _copy(response)
        except (TypeError, ValueError, OverflowError):
            result['terminal_reason'] = trace['kind'] + '_non_json_response'
            return None
        if (type(response) is not dict or type(response.get('raw')) is not str
                or type(response.get('terminal')) is not bool or type(response.get('truncated')) is not bool):
            result['terminal_reason'] = trace['kind'] + '_invalid_response'
            return None
        if not response['terminal'] or response['truncated']:
            result['terminal_reason'] = trace['kind'] + '_nonterminal_or_truncated'
            return None
        return trace['response']

    for unused in range(MAX_ACTOR_CALLS):
        result['action_calls'] += 1
        trace = dict(kind='actor', messages=_copy(messages))
        response = receive(actor, _copy(messages), trace)
        if response is None:
            return result
        messages.append(dict(role='assistant', content=response['raw']))
        try:
            command = parse_command(response['raw'])
        except ValueError:
            result['terminal_reason'] = 'invalid_command'
            return result
        trace['command'] = command
        value = command['value']
        if command['kind'] == 'READ':
            if value not in task['events']:
                result['terminal_reason'] = 'unsupported_address'
                return result
            if value in addresses:
                result['terminal_reason'] = 'duplicate_address'
                return result
            if result['memory_calls'] >= MAX_READS:
                result['terminal_reason'] = 'memory_call_cap'
                return result
            addresses.add(value)
            result['memory_calls'] += 1
            memory_trace = dict(kind='memory', address=value)
            memory = receive(read_memory, value, memory_trace)
            if memory is None:
                if type(memory_trace.get('raw')) is str:
                    messages.append(dict(role='user', content='MEMORY RESULT\n' + memory_trace['raw']))
                return result
            messages.append(dict(role='user', content='MEMORY RESULT\n' + memory['raw']))
            continue
        if value not in task['ports']:
            result['terminal_reason'] = 'invalid_route'
            return result
        result['chosen_port'] = value
        trace['committed'] = True
        transition_trace = dict(kind='transition', port=value, committed=True)
        result['traces'].append(transition_trace)
        try:
            outcome = transition(value)
            transition_trace['outcome'] = _copy(outcome)
        except Exception as error:
            transition_trace['error'] = dict(type=type(error).__name__, message=str(error))
            result['terminal_reason'] = 'transition_error'
            return result
        result['outcome'] = transition_trace['outcome']
        if not _identifier(outcome, 'N'):
            result['terminal_reason'] = 'invalid_outcome'
            return result
        result['reached_goal'] = outcome == task['goal']
        result['terminal_reason'] = 'reached_goal' if result['reached_goal'] else 'wrong_outcome'
        return result
    return result
