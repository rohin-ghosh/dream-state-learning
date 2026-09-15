"""Finite synthetic navigation environments; contextual parenting, never RL fitting."""

from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re


SCHEMA = 'R109_GRID_R110_RESIDENT_CONTEXTUAL_PARENTING_V2'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
STRONG = 'openai/openai/gpt-6-astra'
PRINCIPLES_PATH = 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md'
PRINCIPLES_SHA = 'b7f4d6baef8158b41533d15acf0f7c924b4bc1e875a30d6ca31f874b5e1c589d'
HARD_END = datetime(2026, 9, 15, 17, 2, tzinfo=timezone.utc).timestamp()
START_BOUND = datetime(2026, 9, 15, 9, 2, tzinfo=timezone.utc).timestamp()
NATIVE_END = HARD_END - 300
CYCLES = 8
EPISODES = 2
MAX_STEPS = 16
OUTPUT_CAP = 384
REFLECTION_CAP = 2048
CONTEXT = 32768
CADENCES = ('segment', 'hundred_segments', 'episode')
CLASSES = ('perception', 'persistence', 'metacognition', 'curiosity', 'goal_regulation',
    'meta_goal_regulation', 'reflection', 'action_steering', 'affective_value_regulation')
ACTIONS = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1), 'WAIT': (0, 0)}
LANES = {
    'ovx': dict(index=7, uuid='GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed',
        host_sha256='0e183169e60b06badac84e0eca6036a53b7ad90c433b8cd69b2a9aaf9159389b',
        lease_end=1789980180.0, style='supportive', order=list(CADENCES)),
    'ovx2': dict(index=5, uuid='GPU-bc211959-642d-664b-3581-42a0dbe434e9',
        host_sha256='3e10ebcb89f013079c1e088fa82820188b1a805b879ebb85a7ffeb689e7b86e9',
        lease_end=1789689600.0, style='critical', order=list(reversed(CADENCES))),
}
SYSTEM = ('You control an agent in a simulated grid game. Only the observation is known. '
    'Coordinates are row,column; UP decreases row. # is a wall, . open floor, K a key, '
    'D a locked door, G the goal, ? unknown. Entering a key collects it; a key opens a door. '
    'Reach G within the remaining moves. Invalid moves consume a move. '
    'Reason briefly about what to do, then end with exactly ACTION: UP, DOWN, LEFT, RIGHT, or WAIT. '
    'Actions affect only this toy game; no external tools or commands exist.')
PARENT_SYSTEM = ('You are a real parent of a frozen child navigating a safe toy grid. '
    'Use only the supplied TRAIN observations and actual child proposal, never hidden maps or held results. '
    'ADD useful behavior, STOP wasteful behavior, or SHIFT effort/strategy proactively; never wait for failure. '
    'During metacognition discuss effort allocation, self-perception, reflection, and how the child learns. '
    'Help functional perception, persistence, uncertainty regulation or strategy revision; do not provide '
    'a path or the next action. Return JSON with exactly speak (boolean), message (<=90 words), rationale. '
    'If speak is false message must be empty. Start rationale with one intervention class followed by a colon: '
    + ', '.join(CLASSES) + '. Do not demand branch counts or claim learning.')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def principles():
    raw = (Path(__file__).resolve().parents[1]/PRINCIPLES_PATH).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PRINCIPLES_SHA, 'exact_parenting_principles_snapshot')
    return raw.decode()


def bounds():
    proposals = CYCLES * EPISODES * MAX_STEPS
    interventions = proposals + proposals // 100 + CYCLES * EPISODES
    parents = interventions + len(CADENCES)*CYCLES
    native = len(CADENCES) * (2 * proposals + 2*CYCLES) + interventions
    return dict(native_per_lane=native, parent_per_lane=parents, total_native=2*native,
        total_parent=2*parents, gpu_hours_cap=16, hard_end=HARD_END, native_end=NATIVE_END)


def task(split, cycle, episode, nonce=0):
    require(split in ('TRAIN', 'HELD') and 1 <= cycle <= CYCLES and episode in (1, 2), 'task_scope')
    identifier = f'R109_GRID_{split}_C{cycle:02d}_E{episode}'
    rng = random.Random(int(digest((identifier,nonce)), 16))
    size = 4 if episode == 1 else 5
    cells = [['.' for column in range(size)] for row in range(size)]
    if episode == 1:
        for row in range(1, size):
            for column in range(size-1):
                if rng.random() < .2:
                    cells[row][column] = '#'
    else:
        for row in range(size):
            cells[row][2] = '#'
        cells[3][2] = 'D'
        cells[0][1] = 'K'
        for row in range(3):
            for column in (3, 4):
                if rng.random() < .25:
                    cells[row][column] = '#'
    cells[-1][-1] = 'G'
    start = [0, 0]
    for rotation in range(rng.randrange(4)):
        cells = [list(line) for line in zip(*cells[::-1])]
        start = [start[1], size - 1 - start[0]]
    result = dict(id=identifier, split=split, difficulty='easy' if episode == 1 else 'hard',
        cells=[''.join(line) for line in cells], start=start, max_steps=MAX_STEPS,
        visibility='full' if episode == 1 else 'local_radius1_with_persistent_map', generation_nonce=nonce)
    result['task_sha256'] = digest(result)
    return result


def roster():
    seen = set()
    result = {'TRAIN': [], 'HELD': []}
    for split in result:
        for cycle in range(1,CYCLES+1):
            group = []
            for episode in (1,2):
                for nonce in range(1000):
                    spec = task(split,cycle,episode,nonce)
                    geometry = digest({name:spec[name] for name in ('cells','start','visibility')})
                    if geometry not in seen:
                        seen.add(geometry); group.append(spec); break
                else:
                    raise ValueError('prospective_distinct_geometry_exhausted')
            result[split].append(group)
    return result


def initial(spec):
    return reveal(spec, dict(position=list(spec['start']), key=False, steps=0, total_reward=0.0,
        done=False, success=False, observed={}, collisions=0, invalid_actions=0,
        visits={','.join(map(str, spec['start'])): 1}))


def reveal(spec, state):
    state = deepcopy(state)
    for row, line in enumerate(spec['cells']):
        for column, symbol in enumerate(line):
            if spec['visibility'] == 'full' or abs(row-state['position'][0])+abs(column-state['position'][1]) <= 1:
                state['observed'][f'{row},{column}'] = symbol
    return state


def observation(spec, state):
    size = len(spec['cells'])
    return dict(task_id=spec['id'], difficulty=spec['difficulty'], position=state['position'],
        map=[''.join(state['observed'].get(f'{row},{column}', '?') for column in range(size)) for row in range(size)],
        has_key=state['key'], moves_remaining=MAX_STEPS-state['steps'], total_reward=state['total_reward'],
        terminal=state['done'], success=state['success'])


def transition(spec, previous, action):
    require(not previous['done'], 'terminal_state_no_more_actions')
    state = deepcopy(previous)
    state['steps'] += 1
    reward, event = -.01, 'moved'
    if action not in ACTIONS:
        state['invalid_actions'] += 1
        reward, event = -.1, 'invalid_action'
    else:
        movement = ACTIONS[action]
        target = [state['position'][0]+movement[0], state['position'][1]+movement[1]]
        size = len(spec['cells'])
        symbol = spec['cells'][target[0]][target[1]] if all(0 <= part < size for part in target) else '#'
        if symbol == '#' or (symbol == 'D' and not state['key']):
            state['collisions'] += 1
            reward, event = -.1, 'blocked'
        else:
            state['position'] = target
            if symbol == 'K' and not state['key']:
                state['key'], reward, event = True, .1, 'key_collected'
            if symbol == 'G':
                state['done'], state['success'], reward, event = True, True, 1.0, 'goal_reached'
            if action == 'WAIT':
                event = 'waited'
    state['total_reward'] = round(state['total_reward']+reward, 6)
    state['done'] = state['done'] or state['steps'] >= MAX_STEPS
    location = ','.join(map(str, state['position']))
    state['visits'][location] = state['visits'].get(location, 0)+1
    return reveal(spec, state), dict(action=action, reward=reward, event=event)


def shortest_solution(spec):
    queue = deque([(initial(spec), [])])
    seen = set()
    while queue:
        state, actions = queue.popleft()
        if state['success']:
            return actions
        key = (tuple(state['position']), state['key'])
        if key in seen or state['done']:
            continue
        seen.add(key)
        for action in ('UP', 'DOWN', 'LEFT', 'RIGHT'):
            following, unused = transition(spec, state, action)
            queue.append((following, actions+[action]))
    raise ValueError('unsolvable_generated_environment')


def parse_action(raw):
    matches = re.findall(r'^ACTION:\s*(UP|DOWN|LEFT|RIGHT|WAIT)\s*$', raw, re.MULTILINE)
    return matches[0] if len(matches) == 1 and raw.strip().endswith('ACTION: '+matches[0]) else 'INVALID'


def intervene(cadence, proposal_number, episode_step):
    require(cadence in CADENCES and proposal_number >= 1 and episode_step >= 1, 'cadence_counter')
    return cadence == 'segment' or (cadence == 'hundred_segments' and proposal_number % 100 == 0) or (
        cadence == 'episode' and episode_step == 1)


def child_messages(spec, state, memory=(), history=(), guidance=None):
    require(spec['split'] == 'TRAIN' or (not memory and not guidance), 'held_parent_and_memory_free')
    system = SYSTEM
    if memory:
        system += '\nYour earlier own TRAIN reflections (unverified): '+json.dumps(list(memory))
    messages = [dict(role='system', content=system), dict(role='user', content=json.dumps(dict(
        observation=observation(spec, state), previous_actions=list(history))))]
    if guidance is not None:
        messages.append(dict(role='assistant', content=guidance['proposal']))
        messages.append(dict(role='user', content='Parent guidance: '+guidance['message']+
            '\nDecide your next action yourself. Use the same ACTION format.'))
    return messages


def parent_payload(spec, state, proposal, history, memory, cadence, style, number, purpose='intervention'):
    require(spec['split'] == 'TRAIN' and style in ('supportive', 'critical'), 'parent_train_only')
    require(cadence in CADENCES, 'parent_cadence')
    return dict(schema=SCHEMA, task_id=spec['id'], split='TRAIN', observation=observation(spec, state),
        child_proposal=proposal, executed_history=list(history), own_reflections=list(memory),
        cadence=cadence, style=style, proposal_number=number, base_sha256=BASE_SHA, adapter=None, purpose=purpose)


def validate_parent(payload, plan):
    require(set(payload) == {'schema','task_id','split','observation','child_proposal','executed_history',
        'own_reflections','cadence','style','proposal_number','base_sha256','adapter','purpose'}, 'parent_visibility_keys')
    require(payload['schema'] == SCHEMA and payload['split'] == 'TRAIN' and '_TRAIN_' in payload['task_id']
        and payload['base_sha256'] == BASE_SHA and payload['adapter'] is None, 'parent_source')
    require(payload['purpose'] in ('intervention','metacognition'), 'parent_purpose')
    require(set(plan) == {'speak','message','rationale'} and type(plan['speak']) is bool
        and isinstance(plan['message'], str) and len(plan['message'].split()) <= 90
        and (plan['speak'] or not plan['message']), 'parent_plan_schema')
    require(isinstance(plan['rationale'], str) and plan['rationale'].split(':', 1)[0] in CLASSES,
        'explicit_intervention_class')
    return plan['rationale'].split(':', 1)[0]
