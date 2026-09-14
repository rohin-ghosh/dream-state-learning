"""Posthoc native-table progress diagnostic; no model calls or score changes."""

import collections
import functools
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from organism_v6 import orch_game_screen as screen


def analyze():
    evidence = ROOT / 'research_notes/analysis/orch_game_20260914_attempt1'
    bank_path = evidence / 'FROZEN_BANK.json'
    bank = json.loads(bank_path.read_text())
    paths = sorted(evidence.glob('native_evidence/shard*/screen/*_EPISODE.json'))
    assert len(paths) == 32
    expected = {(item['id'], arm) for item in screen.freeze(bank)
                if item['split'] == 'mining' for arm in ('RICH', 'TERSE')}
    seen = set()
    counts = {arm: collections.Counter() for arm in ('RICH', 'TERSE')}
    rows = []
    bindings = {str(bank_path.relative_to(ROOT)): hashlib.sha256(bank_path.read_bytes()).hexdigest()}

    @functools.lru_cache(None)
    def distance(state):
        return screen.shortest_distance(bank, state)

    for path in paths:
        entry = json.loads(path.read_text())
        key = entry['instance']['id'], entry['arm']
        assert key in expected and key not in seen
        seen.add(key)
        bindings[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        arm_counts = counts[entry['arm']]
        arm_counts['episodes'] += 1
        state = entry['instance']['state']
        assert distance(state) == entry['instance']['oracle_distance'] <= screen.MAX_TURNS
        history = []
        previous_noop_action = None
        previous_reject = False
        first_loss = None
        for index, turn in enumerate(entry['turns']):
            assert turn['turn'] == index
            observation = screen.observe(bank, entry['instance'], state, index, history)
            assert observation == turn['observation']
            assert screen.messages(observation, entry['arm']) == turn['messages']
            before = distance(state)
            feasible_before = before <= screen.MAX_TURNS - index
            arm_counts['turns'] += 1
            arm_counts['feasible_turns'] += feasible_before
            if previous_noop_action is not None:
                arm_counts['after_native_noop'] += 1
                arm_counts['repeat_native_noop'] += turn.get('action') == previous_noop_action
            if previous_reject:
                arm_counts['after_format_reject'] += 1
                arm_counts['repeat_format_reject'] += not turn['format_pass']
            previous_noop_action = None
            previous_reject = not turn['format_pass']
            if turn['format_pass']:
                action = screen.parse_action(turn['response']['raw'], entry['arm'])
                assert screen.ACTIONS[action] == turn['action']
                outcome = screen.transition(bank, state, action)
                assert outcome == turn['outcome']
                after = 0 if outcome['terminal'] and outcome['reward'] == 20 else distance(outcome['state'])
                category = 'progress' if after < before else 'same_distance' if after == before else 'regress'
                if outcome['state'] == state and not outcome['terminal']:
                    previous_noop_action = turn['action']
                    arm_counts['native_noop'] += 1
                next_row, next_column = bank['decoded'][str(outcome['state'])][:2]
                history.append(f'{observation["reference"]}: {turn["action"]} -> '
                               f'row={next_row}, column={next_column}, reward={outcome["reward"]}, '
                               f'terminal={outcome["terminal"]}.')
                state = outcome['state']
            else:
                assert turn['outcome'] is None
                try:
                    screen.parse_action(turn['response']['raw'], entry['arm'])
                except ValueError as error:
                    assert str(error) == turn['error']['message']
                else:
                    raise AssertionError('recorded_rejection_not_reproduced')
                category, after = 'format_reject', before
                history.append(f'{observation["reference"]}: action not executed; '
                               f'{turn["error"]["type"]}: {turn["error"]["message"]}. State unchanged.')
            arm_counts[category] += 1
            if feasible_before:
                arm_counts['feasible_' + category] += 1
            if feasible_before and after > screen.MAX_TURNS - index - 1:
                assert first_loss is None
                first_loss = {'turn': index + 1, 'category': category,
                              'distance_before': before, 'distance_after': after}
                arm_counts['first_infeasible_' + category] += 1
            if index == 0:
                arm_counts['first_turn_' + category] += 1
        assert state == entry['final_state'] and not entry['success']
        assert first_loss is not None
        rows.append({'id': key[0], 'arm': key[1], 'initial_distance': entry['instance']['oracle_distance'],
                     'first_budget_infeasible': first_loss})
    assert seen == expected
    assert all(total['turns'] == 96 and total['episodes'] == 16 for total in counts.values())
    source = Path(screen.__file__)
    bindings[str(source.relative_to(ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest()
    return {'posthoc': True, 'changes_admission': False, 'model_calls': 0,
            'definition': 'Progress reduces native shortest delivery distance. Feasible means remaining turns suffice under an optimal continuation, not observed success.',
            'limitations': 'Descriptive state/action checks, not a causal test of reflection. Repeated no-op counts include doomed prefixes; feasible categories are separate. No hidden thought quality inference.',
            'arms': {arm: dict(sorted(total.items())) for arm, total in counts.items()},
            'episodes': rows, 'source_hashes': bindings}


if __name__ == '__main__':
    print(json.dumps(analyze(), indent=2, sort_keys=True))
