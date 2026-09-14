"""Frozen L1 TextWorld paired inference protocol; no fit or automatic admission."""

import hashlib
import math
import re


BANK_SHA = '805f55a821f291715ae14360a1bc881d733c7688a4f33099d3ffc44c13ae2cd9'
MAX_TURNS = 6
MAX_CONTEXT = 2048
MAX_GENERATED = 512
PAIRS = 8
RICH = ('For each turn, write 150–400 tokens of first-person reasoning. Name exact '
        'observable evidence, connect it to your goal, and state a checkable expectation '
        'for your next action. Distinguish uncertainty from what you observed. If '
        'feedback rejects your earlier action, explain the mistake, revise your plan '
        'and state a useful lesson. Include a short reusable record in your own words '
        'grounded in this experience. Do not invent observations or claim success '
        'before the environment confirms it. Put exactly one command on the final '
        'line, prefixed ACTION: . No text after that line.')
TERSE = ('Output only exactly one command on one line, prefixed ACTION: . '
         'No explanation or additional text.')
COMMON = ('You act in a native TextWorld game. Reach the stated goal within six '
          'actions. Native commands include open NAME, take NAME, take NAME from '
          'CONTAINER, and insert NAME into CONTAINER. Use names from observations '
          'and the goal. There is no need to repeat look or inventory: both are '
          'provided every turn. An invalid format consumes a turn without action. ')


def digest(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


def parse(raw, arm, terminal=True, truncated=False):
    if not terminal or truncated:
        raise ValueError('unterminated_or_truncated')
    if arm not in ('RICH', 'TERSE') or not isinstance(raw, str):
        raise ValueError('invalid_arm_or_raw')
    lines = raw.splitlines()
    if not lines or raw.endswith('\n\n') or len([line for line in lines if line.startswith('ACTION:')]) != 1:
        raise ValueError('unique_final_action_required')
    match = re.fullmatch(r'ACTION: ([a-z][a-z0-9 -]*(?:[a-z0-9]))', lines[-1])
    if not match or len(match.group(1)) > 120:
        raise ValueError('strict_final_action_format')
    if arm == 'TERSE' and len(lines) != 1:
        raise ValueError('terse_action_only')
    prose = '\n'.join(lines[:-1])
    if arm == 'RICH' and not prose.strip():
        raise ValueError('rich_prose_required')
    return dict(action=match.group(1), prose=prose)


def observation(task, state, turn, format_feedback=None):
    feedback = state['feedback'].split('\n>')[0].strip() if turn else ''
    return (f"TASK {task['id']} | turn {turn + 1}/6\nGOAL: {task['goal']}\n"
            f"[OBS{turn}] {state['description']}\n[INV{turn}] {state['inventory']}\n"
            f"[FEEDBACK{turn}] {format_feedback or feedback}")


def messages(task, state, arm, turn, previous=None, format_feedback=None):
    result = [dict(role='system', content=COMMON + (RICH if arm == 'RICH' else TERSE))]
    if previous:
        result.extend([dict(role='user', content=previous['observation']),
                       dict(role='assistant', content=previous['raw'])])
    result.append(dict(role='user', content=observation(task, state, turn, format_feedback)))
    return result


def student_prefix(task, state):
    return [dict(role='user', content=f"GOAL: {task['goal']}\n"
                 f"{state['description']}\n{state['inventory']}")]


def eligible(rich_success, terse_success):
    if len(rich_success) != PAIRS or len(terse_success) != PAIRS:
        raise ValueError('fixed_eight_pair_denominator')
    wins = sum(rich and not terse for rich, terse in zip(rich_success, terse_success))
    losses = sum(terse and not rich for rich, terse in zip(rich_success, terse_success))
    discordant = wins + losses
    probability = sum(math.comb(discordant, count) for count in range(wins, discordant + 1)) / 2 ** discordant
    return dict(rich=sum(rich_success), terse=sum(terse_success), pairs=PAIRS,
                wins=wins, losses=losses, one_sided_sign_p=probability,
                outcome_gap_pass=sum(rich_success) >= 5 and wins - losses >= 3 and probability <= .05)
