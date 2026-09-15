"""R110 resident route parenting with explicit observable cadence units."""

from copy import deepcopy
import re
from types import FunctionType

from organism_v6 import orch_full_rich as gym


VERSION = 'R110_ROUTE_RESIDENT_V1'
PRINCIPLES_PATH = 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md'
PRINCIPLES_SHA = 'b7f4d6baef8158b41533d15acf0f7c924b4bc1e875a30d6ca31f874b5e1c589d'
PREFIX = 'ORCH-R109-ROUTE-20260915-'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
STOP_SHA = '1fe38d9fea6bed06f07c3a5eb0ccbb029635d7af148b38367d8cd51dddfc2ceb'
LANES = {
    'a100_1': dict(host='a100', physical=1, uuid='GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b', learned=False, cadence='episode'),
    'a100_2': dict(host='a100', physical=2, uuid='GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296', learned=True, cadence='segment'),
    'a100_3': dict(host='a100', physical=3, uuid='GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8', learned=True, cadence='hundred'),
    'a100_5': dict(host='a100', physical=5, uuid='GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9', learned=True, cadence='episode'),
    'a100_6': dict(host='a100', physical=6, uuid='GPU-6de3930d-104a-f969-7d36-009271368dd1', learned=True, cadence='episode'),
    'node3_3': dict(host='node3', physical=3, uuid='GPU-e1277146-04f2-c38f-d1ae-1a98132f907e', learned=False, cadence='segment'),
    'node1_7': dict(host='node1', physical=7, uuid='GPU-6eac3b9d-551a-d786-f598-04ef6d701c98', learned=False, cadence='hundred')
}
HOSTS = {
    'a100': dict(wrapper='gpu/a100_ssh.sh', scp='gpu/a100_scp.sh', sha256='6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'),
    'node3': dict(wrapper='gpu/ovx2_ssh.sh', scp='gpu/ovx2_scp.sh', sha256='3e10ebcb89f013079c1e088fa82820188b1a805b879ebb85a7ffeb689e7b86e9'),
    'node1': dict(wrapper='gpu/a40r_ssh.sh', scp='gpu/a40r_scp.sh', sha256='e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b')
}
CLASSES = ('perception', 'persistence', 'metacognition', 'curiosity', 'goal/meta-goal regulation', 'reflection', 'action steering', 'affective-value')
NATIVE_CAP, CYCLES = 16384, 256
PARENT_CAPS = {'segment': 2048, 'hundred': 128, 'episode': 512}
REFLECTION_TURNS = {'a100_1': 2, 'a100_2': 2, 'a100_3': 4, 'a100_5': 4,
                    'a100_6': 2, 'node3_3': 4, 'node1_7': 2}
SEGMENT_UNIT = 'One completed TRAIN native response, including source actions/records, route decisions and scheduled own reflections; excludes all HELD responses. No hidden thought count.'
STYLES = {key:'supportive/' + value['cadence'] for key,value in LANES.items()}
DEVICES = {key:value['uuid'] for key,value in LANES.items()}
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
    'Parent the behavior of thinking, not the game outcome. ADD, STOP or SHIFT '
    'behavior based on the actual child state; never gate intervention on failure '
    'or success. Outcomes are background. Never prescribe an answer, route, '
    'tool call or hypothesis. Use the exact attached principles snapshot. '
    'For METACOGNITION_CONVERSATION conduct pure metacognitive context '
    'distillation: discuss what matters, what context is leaving, attention, '
    'self-perception, reflection and how the child learns. Converse with the '
    'actual last child reply rather than supplying a compiled lesson. '
    'Reflection is additive and replaces a semantic compiler. Do not enforce '
    'a checklist, branch count, surprise, length, padding or literal repetition. '
    'In rationale identify intended ADD/STOP/SHIFT and relevant intervention '
    'classes; intentions are not verified changes. All held context is sealed. '
    'Return the requested JSON; order is fixed and episode_guidance is advice '
    'to this one observed child state, never a solution.'
)
REFLECTION_SYSTEM += (
    ' Consider useful perspectives on what you actually perceived, remaining '
    'uncertainty, your goals, and allocation of attention. Choose relevant angles '
    'rather than a checklist. An intention is not an observed behavioral change. '
    'Do not repeat passages or invent facts.'
)


def allocation(index):
    require(type(index) is str and index in LANES, 'only_R109_route_allocations')
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
        for cycle in range(1, CYCLES + 1):
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


def due(cadence, segments, *, episode_end=False):
    require(cadence in PARENT_CAPS and type(segments) is int and segments >= 0, 'cadence_counter')
    return episode_end if cadence == 'episode' else (not episode_end and segments > 0 and
        (cadence == 'segment' or segments % 100 == 0))


def parent_payload(lane, cycle, episode, segments, messages, response, execution_state,
                   principles, mode='BEHAVIOR', turn=0):
    allocation(lane)
    payload = dict(split='TRAIN', lane=lane, cycle=cycle, episode=episode, segments=segments,
        unit=SEGMENT_UNIT, cadence=LANES[lane]['cadence'], messages=deepcopy(messages),
        child_response=response, execution_state=execution_state,
        principles=principles, principles_sha256=PRINCIPLES_SHA, mode=mode, turn=turn,
        episodes=[dict(task_id=f'TRAIN-OBSERVATION-{lane}-{cycle}-{episode}-{segments}-{mode}-{turn}')])
    return validate_parent_payload(payload)


def validate_parent_payload(payload):
    require(set(payload) == {'split','lane','cycle','episode','segments','unit','cadence','messages','child_response','execution_state',
        'principles','principles_sha256','mode','turn','episodes'}, 'parent_allowlist')
    import hashlib
    require(hashlib.sha256(payload['principles'].encode()).hexdigest() == payload['principles_sha256'] == PRINCIPLES_SHA,
            'exact_shared_principles_snapshot')
    require(payload['mode'] in ('BEHAVIOR','METACOGNITION_CONVERSATION'), 'parent_mode')
    require(type(payload['turn']) is int and 0 <= payload['turn'] <= REFLECTION_TURNS[payload['lane']], 'reflection_turn_bound')
    require(len(payload['episodes']) == 1 and set(payload['episodes'][0]) == {'task_id'}
            and payload['episodes'][0]['task_id'].startswith('TRAIN-OBSERVATION-'), 'transport_observation_not_held')
    require(payload['split'] == 'TRAIN' and payload['lane'] in LANES, 'parent_train_lane')
    require(type(payload['cycle']) is int and 1 <= payload['cycle'] <= CYCLES and payload['episode'] in (0,1,2), 'parent_cycle')
    require(payload['unit'] == SEGMENT_UNIT and payload['cadence'] == LANES[payload['lane']]['cadence'], 'honest_cadence')
    require(all(set(message) == {'role','content'} and message['role'] in ('system','user','assistant')
        and isinstance(message['content'],str) for message in payload['messages']), 'actual_public_messages')
    require(isinstance(payload['child_response'],str) and payload['execution_state'] in
        ('GENERATED_NOT_YET_EXECUTED','COMPLETED_REFLECTION','COMPLETED_EPISODE'), 'truthful_observation_stage')
    return payload


def validate_plan(plan):
    require(set(plan) == {'guidance','rationale','order','episode_guidance'}, 'parent_plan_schema')
    require(all(isinstance(plan[key],str) for key in ('guidance','rationale')), 'parent_plan_text')
    require(isinstance(plan['order'],list) and isinstance(plan['episode_guidance'],dict)
        and set(plan['order']) == set(plan['episode_guidance']) and len(plan['order']) == 1, 'one_observed_state')
    return plan


def parent_cap(lane):
    allocation(lane)
    return PARENT_CAPS[LANES[lane]['cadence']] + CYCLES * REFLECTION_TURNS[lane]
