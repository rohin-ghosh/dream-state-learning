"""Fresh frozen-base route parenting discovery; context changes, never weights."""

from copy import deepcopy
import re
from types import FunctionType

from organism_v6 import orch_full_rich as gym


VERSION = 'R108_ROUTE_BASE_INDEPENDENT_STYLES_V1'
PREFIX = 'ORCH-R108-ROUTE-PARENT-20260915-A2-'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
STOP_SHA = '1fe38d9fea6bed06f07c3a5eb0ccbb029635d7af148b38367d8cd51dddfc2ceb'
DEVICES = {2: 'GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296',
           3: 'GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8',
           6: 'GPU-6de3930d-104a-f969-7d36-009271368dd1'}
HOST_SHA = '6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'
STYLES = {2: 'perception-curiosity/supportive',
          3: 'persistence-goal-regulation/supportive',
          6: 'metacognition-reflective-value/supportive'}
STYLE_INSTRUCTIONS = {
    2: 'Distinguish visible identifiers from observed evidence. Help choose useful questions and gather evidence rather than invent contents.',
    3: 'Support useful depth beyond the first plausible action and maintain the actual goal and subgoals. Redirect unsupported or repetitive cognition without forcing length or futile persistence.',
    6: 'Support recognizing cognitive limits, purposeful redirection, grounded multi-angle reflection, and affective-value regulation rather than performative self-description.'
}
NATIVE_CAP, PARENT_CAP, CYCLES = 140, 4, 2
CONTEXT, OUTPUT = 32768, 8192
require, digest = gym.hop.require, gym.digest
SYSTEM = (
    'Reason through this routing task in ordinary prose before committing your '
    'next action. Use only the public task and actual conversation. Identifiers '
    'are opaque and case-sensitive. There are at most six turns, four distinct '
    'memory reads, and two committed routes. A READ returns actual stored text; '
    'a ROUTE commits a currently listed port and returns the actual receipt and '
    'new CURRENT/PORTS. Arrival at GOAL ends the episode. Do not simulate results '
    'or another turn. End with exactly one action on the final nonempty line: '
    'READ EVENT <listedaddress> or ROUTE <listedport>. Nothing follows that action. '
    'No STOP, retry, or multiple executed actions in one response.'
)
GUIDANCE = (
    'Use reasoning where it can improve your next decision, rather than stopping '
    'automatically at the first plausible action. When actual evidence or a '
    'recognized limitation warrants changing how you proceed, follow through. '
    'No prescribed branch count, surprise, check template, length, or padding. '
    'Do not treat an unread event identifier as knowledge of its contents.'
)
SOURCE_SYSTEM = (
    'This is a researcher-scheduled action exposure, not an autonomous route '
    'solution or a teacher answer. Reason in ordinary prose if useful, then put '
    'the single offered ROUTE action on the last line. After the real receipt, '
    'record your own account and end with the requested EVENT line grounded '
    'only in that receipt. Do not simulate a receipt, rename identifiers, or '
    'repair a failed action. The entire response need not be a bare command.'
)
REFLECTION_SYSTEM = (
    'Reflect on your actual route experience and the supplied parent message. '
    'Describe what you learned or still do not know and how that should change '
    'your next reasoning or action. Distinguish actual observations from guesses. '
    'Do not merely echo advice, invent experience, or continue repetitive prose. '
    'No protocol action, fixed format, branch count, or minimum length is required.'
)
PARENT_INSTRUCTIONS = (
    'You are the actual supportive Astra parent for frozen-base ROUTE discovery. '
    'Follow the separately registered lineage style, not a control arm. Work only '
    'from the supplied actual TRAIN experience, including unread-evidence '
    'dismissals when present. Intervention classes: perception, persistence, '
    'metacognition, curiosity, goal/meta-goal regulation, reflection, action '
    'steering, affective-value. Choose relevant classes and identify them in '
    'your rationale. Intervene constructively on failure, never prescribe an '
    'answer or a solved route. Separate motivating observations from hoped-for '
    'behavioral change. No invented receipts, event contents, or teacher '
    'solutions. No prescribed branch counts, length, checklist, or padding. '
    'You have no tools, held tasks, or sealed scores. Episode order is fixed. '
    'Return the requested JSON plan grounded in this actual episode.'
)
REFLECTION_SYSTEM += (
    ' Consider useful perspectives on what you actually perceived, remaining '
    'uncertainty, your goals, and allocation of attention. Choose relevant angles '
    'rather than a checklist. An intention is not an observed behavioral change. '
    'Do not repeat passages or invent facts.'
)


def allocation(index):
    require(type(index) is int and index in DEVICES, 'only_allocated_A100_2_3_6')
    return DEVICES[index]


def runtime(master):
    require(master.startswith(PREFIX), 'new_registered_route_namespace')
    namespace = dict(gym.hop.__dict__, MASTER=master, TRANSFER_MASTER=master)
    for name, function in gym.hop.__dict__.items():
        if isinstance(function, FunctionType) and function.__globals__ is gym.hop.__dict__:
            namespace[name] = FunctionType(function.__code__, namespace, name,
                (master,) if name == 'build_world' else function.__defaults__, function.__closure__)
    return namespace


def identifiers(document):
    import json
    return set(re.findall(r'\b[NEPR]_[A-Z0-9]{10}\b', json.dumps(document)))


def cohort(excluded, index):
    allocation(index)
    seen = set(excluded)
    groups = {}
    for split in ('TRAIN', 'HELD'):
        groups[split.lower()] = []
        for cycle in (1, 2):
            master = f'{PREFIX}S{index}-{split}-C{cycle}'
            world = runtime(master)['build_world'](master)
            require(not identifiers(world).intersection(seen), 'route_namespace_collision')
            seen.update(identifiers(world))
            tasks = runtime(master)['build_tasks'](world)
            if split == 'TRAIN':
                tasks = [tasks[0], tasks[2]]
            groups[split.lower()].append(dict(world=world, tasks=[dict(task,
                task_id=f'{split}-'+digest(task)) for task in tasks]))
    return dict(groups, version=VERSION, exclusion_sha256=digest(sorted(excluded)),
        fixed_order=True, train_episodes_per_cycle=2, held_episodes_per_cycle=4,
        parents_never_receive_held=True, weight_updates=0)


def token_budget(prompt_tokens):
    require(type(prompt_tokens) is int and 0 < prompt_tokens < CONTEXT, 'uncropped_context_fit')
    return min(OUTPUT, CONTEXT - prompt_tokens)


def last_action(raw):
    lines = raw.rstrip().splitlines()
    match = re.fullmatch(r'(READ EVENT|ROUTE) ([^\s]+)', lines[-1]) if lines else None
    return dict(kind=match[1], value=match[2]) if match else None


def public_record(record):
    return dict(task=deepcopy(record['task']), messages=deepcopy(record['messages']),
                terminal_reason=record['terminal_reason'],
                attempted_actions_are_not_gold=True)


def episode(world, task, generate, store, own_memory=''):
    guidance = GUIDANCE
    if own_memory:
        guidance += '\n\nYour own prior TRAIN reflection (not a new observation):\n' + own_memory
    namespace = dict(gym.episode.__globals__, SYSTEM=SYSTEM, GUIDANCE=guidance)
    function = FunctionType(gym.episode.__code__, namespace, gym.episode.__name__)
    return function(world, task, generate, store)


def collect_source(world, generate):
    records, store = [], {}
    for edge in world['edges']:
        record = dict(edge=deepcopy(edge), accepted=False, action=None, event=None, transition=None)
        messages = [dict(role='system', content=SOURCE_SYSTEM), dict(role='user', content=
            f"EXPOSURE TASK\nCURRENT {edge['node']}\nPORTS {edge['port']}\n"
            'Reason if useful; finish with ROUTE <listedport>.')]
        try:
            response = generate(messages)
            record['action'] = response
            require(response['terminal'] and not response['truncated'], 'source_action_not_complete')
            require(last_action(response['raw']) == dict(kind='ROUTE', value=edge['port']),
                    'unoffered_source_action')
            transition = dict(source=edge['node'], port=edge['port'], destination=edge['outcome'], receipt=edge['receipt'])
            record['transition'] = transition
            messages += [dict(role='assistant', content=response['raw']), dict(role='user', content=
                gym.hop.micro.RECEIPT_WIRE.format(**transition) +
                '\nRecord only the receipt actually observed. Reasoning may precede your final line. '
                'Final line grammar: EVENT <event_id> AT <source> DID <port> GOT <destination> EVIDENCE <receipt_id>\n'
                f"AVAILABLE EVENT ADDRESS {edge['event']}\n"
                'Use the available address and exact observed identifiers; nothing follows the final EVENT line.')]
            response = generate(messages)
            record['event'] = response
            require(response['terminal'] and not response['truncated'], 'source_event_not_complete')
            final = response['raw'].rstrip().splitlines()[-1]
            canonical = gym.hop.micro.canonical_event(final)
            require(gym.hop.micro.parse_event_line(canonical) == dict(event=edge['event'], **transition),
                    'child_event_must_match_actual_receipt')
            store[edge['event']] = response['raw']
            record['accepted'] = True
        except ValueError as error:
            record['error'] = str(error)
        records.append(record)
    return dict(records=records, store=store, source_kind='ACTUAL_SCHEDULED_CHILD_EXPOSURE',
        accepted_events=len(store), missing_events_return_unavailable=True,
        template_or_gold_fallback=False, no_retry=True)


def parent_payload(index, cycle, episode_index, record, memories, parent_messages):
    allocation(index)
    task = record['task']
    payload = dict(split='TRAIN', style=STYLES[index], cycle=cycle, episode_index=episode_index,
        episodes=[dict(task_id=task['task_id'], public_experience=public_record(record))],
        prior_own_reflections=list(memories), prior_parent_messages=list(parent_messages))
    validate_parent_payload(payload)
    return payload


def validate_parent_payload(payload):
    require(set(payload) == {'split', 'style', 'cycle', 'episode_index', 'episodes',
        'prior_own_reflections', 'prior_parent_messages'}, 'parent_strict_allowlist')
    require(payload['split'] == 'TRAIN' and payload['style'] in STYLES.values(), 'parent_train_only')
    require(payload['cycle'] in (1, 2) and payload['episode_index'] in (1, 2), 'bounded_parent_cycle')
    require(len(payload['episodes']) == 1, 'one_actual_completed_episode_per_intervention')
    for episode in payload['episodes']:
        require(set(episode) == {'task_id', 'public_experience'}, 'no_hidden_world_to_parent')
        require(episode['task_id'].startswith('TRAIN-'), 'no_held_task_to_parent')
        public = episode['public_experience']
        require(set(public) == {'task', 'messages', 'terminal_reason', 'attempted_actions_are_not_gold'}, 'public_only_record')
        require(set(public['task']) == {'node', 'goal', 'ports', 'events', 'task_id'}, 'no_world_edges_or_scores')
        require(public['task']['task_id'] == episode['task_id'], 'actual_task_binding')
        require(all(set(message) == {'role', 'content'} and message['role'] in ('system', 'user', 'assistant')
            and isinstance(message['content'], str) for message in public['messages']), 'public_message_schema')
    require(all(isinstance(text, str) for text in payload['prior_own_reflections'] + payload['prior_parent_messages']),
            'textual_train_history_only')
    return payload
