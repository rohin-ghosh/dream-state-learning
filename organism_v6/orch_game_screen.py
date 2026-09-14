"""Bounded matched DEV screen using an exported native Gym Taxi transition table."""

from collections import deque
from copy import deepcopy
import hashlib
import json
import math
import random
import re


ACTIONS = ('SOUTH', 'NORTH', 'EAST', 'WEST', 'PICKUP', 'DROPOFF')
FAMILIES = (('mining', 'R', 14001), ('mining', 'G', 14002),
            ('held_l1', 'Y', 24001), ('held_l1', 'B', 24002))
MAX_TURNS = 6
MAX_CONTEXT = 2048
MAX_NEW_TOKENS = 512
COMMON = ('Play the deterministic taxi game using only the supplied observations. '
          'The passenger is already aboard. Deliver to the named destination. '
          'Rows increase southward and columns eastward. A vertical | between cells '
          'blocks east/west travel; : is open. Each action consumes one turn. '
          'Allowed actions: SOUTH, NORTH, EAST, WEST, PICKUP, DROPOFF. '
          'Finish with exactly one final line ACTION: <allowed action>.')
RICH = ('Before the final action, write a useful first-person account, preferably '
        '150–400 tokens: refer to the supplied observation ID and actual evidence, '
        'connect that evidence to the delivery goal, and state a checkable expectation '
        'for this action. After a mistake, use the actual feedback to revise your '
        'choice and articulate a useful lesson. Do not claim unobserved events. '
        'No headings are required.')
TERSE = 'Return only the final action line, without explanation.'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def transition(bank, state, action):
    outcomes = bank['transitions'][str(state)][str(action)]
    if len(outcomes) != 1 or outcomes[0][0] != 1.0:
        raise ValueError('deterministic_native_transition_required')
    probability, next_state, reward, terminal = outcomes[0]
    return dict(state=next_state, reward=reward, terminal=terminal)


def shortest_distance(bank, initial):
    queue, seen = deque([(initial, 0)]), {initial}
    while queue:
        state, distance = queue.popleft()
        for action in range(len(ACTIONS)):
            outcome = transition(bank, state, action)
            if outcome['terminal'] and outcome['reward'] == 20:
                return distance + 1
            if not outcome['terminal'] and outcome['state'] not in seen:
                seen.add(outcome['state'])
                queue.append((outcome['state'], distance + 1))
    raise ValueError('unreachable_native_state')


def freeze(bank):
    instances = []
    for split, destination, seed in FAMILIES:
        destination_index = 'RGYB'.index(destination)
        eligible = []
        for state, decoded in sorted(bank['decoded'].items(), key=lambda item: int(item[0])):
            if decoded[2:] != [4, destination_index]:
                continue
            distance = shortest_distance(bank, int(state))
            if 3 <= distance <= MAX_TURNS:
                eligible.append((int(state), distance))
        random.Random(seed).shuffle(eligible)
        if len(eligible) < 8:
            raise ValueError('insufficient_unique_native_states')
        for index, (state, distance) in enumerate(eligible[:8]):
            instances.append(dict(id=f'{split}_{destination}_{seed}_{index}', split=split,
                family=f'Taxi-v3/aboard-delivery-{destination}', seed=seed,
                state=state, oracle_distance=distance, shard=index % 4))
    return instances


def observe(bank, instance, state, turn, history):
    row, column, passenger, destination = bank['decoded'][str(state)]
    reference = f"{instance['id']}/OBS{turn}"
    goal_row, goal_column = bank['locations'][destination]
    text = (f'Observation {reference}\nMap (row0 at top; columns0–4):\n'
            + '\n'.join(bank['map']) + '\n'
            + f'Taxi row={row}, column={column}; passenger='
            + ('aboard' if passenger == 4 else 'at ' + 'RGYB'[passenger])
            + f'. Goal destination {"RGYB"[destination]} at row={goal_row}, column={goal_column}.\n'
            + f'Turn {turn + 1}/{MAX_TURNS}.\n')
    if history:
        text += 'Actual prior action feedback:\n' + '\n'.join(history) + '\n'
    return dict(reference=reference, text=text, state=state)


def messages(observation, arm):
    if arm not in ('RICH', 'TERSE'):
        raise ValueError('unknown_arm')
    return [{'role': 'system', 'content': COMMON + '\n' + (RICH if arm == 'RICH' else TERSE)},
            {'role': 'user', 'content': observation['text']}]


def parse_action(raw, arm):
    lines = raw.strip().splitlines()
    if not lines or sum(line.startswith('ACTION:') for line in lines) != 1:
        raise ValueError('unique_final_action_required')
    match = re.fullmatch(r'ACTION: (SOUTH|NORTH|EAST|WEST|PICKUP|DROPOFF)', lines[-1])
    if not match or (arm == 'TERSE' and len(lines) != 1):
        raise ValueError('invalid_final_action_format')
    if arm == 'RICH' and not '\n'.join(lines[:-1]).strip():
        raise ValueError('missing_rich_text')
    return ACTIONS.index(match.group(1))


def episode(bank, instance, arm, generate, emit):
    if instance['split'] != 'mining':
        raise ValueError('held_l1_generation_forbidden_in_screen')
    state, history, records = instance['state'], [], []
    success = False
    for turn in range(MAX_TURNS):
        observation = observe(bank, instance, state, turn, history)
        record = dict(turn=turn, observation=observation, messages=messages(observation, arm),
                      response=None, error=None, format_pass=False, outcome=None)
        try:
            response = generate(deepcopy(record['messages']))
            record['response'] = deepcopy(response)
            if response['prompt_tokens'] > MAX_CONTEXT:
                raise ValueError('context_budget_violation')
            if len(response['token_ids']) > MAX_NEW_TOKENS:
                raise ValueError('generation_budget_violation')
            if not response['terminal'] or response['truncated']:
                raise ValueError('unterminated_generation')
            action = parse_action(response['raw'], arm)
            record['format_pass'] = True
            record['action'] = ACTIONS[action]
            outcome = transition(bank, state, action)
            record['outcome'] = outcome
            next_row, next_column = bank['decoded'][str(outcome['state'])][:2]
            history.append(f'{observation["reference"]}: {ACTIONS[action]} -> '
                           f'row={next_row}, column={next_column}, reward={outcome["reward"]}, '
                           f'terminal={outcome["terminal"]}.')
            state = outcome['state']
            success = outcome['terminal'] and outcome['reward'] == 20
        except Exception as error:
            record['error'] = dict(type=type(error).__name__, message=str(error))
            history.append(f'{observation["reference"]}: action not executed; '
                           f'{type(error).__name__}: {error}. State unchanged.')
        records.append(record)
        emit(turn, record)
        if success:
            break
    return dict(instance=instance, arm=arm, turns=records, success=success,
                final_state=state, semantic_status='UNREVIEWED', admitted_rows=0,
                fit_ready=False, parent_present=False)


def summarize(episodes, expected_ids):
    keyed = {(entry['instance']['id'], entry['arm']): entry for entry in episodes}
    if len(keyed) != len(episodes):
        raise ValueError('duplicate_episode')
    expected = {(instance_id, arm) for instance_id in expected_ids for arm in ('RICH', 'TERSE')}
    if set(keyed) != expected:
        raise ValueError('complete_matched_denominators_required')
    rich_wins = terse_wins = both = neither = 0
    for instance_id in expected_ids:
        rich = keyed[instance_id, 'RICH']['success']
        terse = keyed[instance_id, 'TERSE']['success']
        rich_wins += rich and not terse
        terse_wins += terse and not rich
        both += rich and terse
        neither += not rich and not terse
    discordant = rich_wins + terse_wins
    probability = (sum(math.comb(discordant, count) for count in range(rich_wins, discordant + 1))
                   / 2 ** discordant) if discordant else 1.0
    pool_pass = rich_wins - terse_wins >= 4 and probability <= .05 and rich_wins + both >= 8
    return dict(pairs=len(expected_ids), episodes=len(episodes), rich_only=rich_wins,
                terse_only=terse_wins, both=both, neither=neither,
                rich_success=rich_wins + both, terse_success=terse_wins + both,
                paired_one_sided_sign_p=probability, outcome_pool_pass=pool_pass,
                format_failures=sum(not turn['format_pass'] for entry in episodes for turn in entry['turns']),
                attempted_turns=sum(len(entry['turns']) for entry in episodes),
                semantic_reviewed_turns=0, admitted_rows=0, fit_ready=False,
                recommendation='REVIEW_CONTENT_NO_AUTOMATIC_FIT' if pool_pass else 'DEALLOCATE_DECLARED_SCREEN')
