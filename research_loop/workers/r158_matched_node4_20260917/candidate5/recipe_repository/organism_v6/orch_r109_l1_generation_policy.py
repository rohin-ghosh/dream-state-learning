"""Prospective V3 elicitation and descriptive persistence, never admission."""

import json
import re


VERSION = 'R109_GENERATION_PERSISTENCE_DISCRETION_V3'
COMMON = ('Allocate effort as you judge useful for this task. You may persist through difficulty, '
          'revisit an earlier idea, try an alternative, check a consequential uncertainty, or stop when '
          'the goal is satisfied. These are options, not required steps. The token budget is a limit, '
          'not a target. Retain enough room to finish with your final answer within the budget. '
          'Use only actual task evidence; do not invent observations, actions, or tests. '
          'No prescribed headings, method counts, or minimum response length.')
GUIDANCE = {
    'ORDINARY_CONTROL': 'Solve the actual task and finish with the final answer.',
    'PERSISTENCE': 'You may keep working when a genuine unresolved obstacle remains; decide when further work is useful and when to finish.',
    'FUNCTIONAL_METACOGNITION': 'You may allocate effort to uncertainty that could change your answer or next action; decide what deserves attention.',
    'PERCEPTION': 'You may examine a relevant observation, relation, unit, or boundary; distinguish supplied evidence from assumptions.',
    'EVIDENCE_HOPS': 'You may follow relevant supplied evidence and use what you actually obtain; revisiting an item is optional and is not itself success.',
}


def guidance(condition):
    return COMMON + ' ' + GUIDANCE[condition]


def opportunity():
    return ('You have another opportunity to work on this task, if useful. Decide whether to revisit, '
            'change, check, continue, or finish from the work you actually did. You may simply finish '
            'if the goal is already satisfied. No external feedback or new observation was supplied. '
            'Do not manufacture a correction or additional work. Finish with the required final answer.')


def first_answer_end(text, family):
    if family == 'math':
        match = re.search(r'(?im)^\s*FINAL:[^\n]*|the answer is[^\n]*', text)
    elif family == 'route':
        match = re.search(r'(?im)^\s*ROUTE\b[^\n]*', text)
    elif family == 'code':
        match = re.search(r'```[^\n]*\n.*?```', text, re.S)
    else:
        match = None
    return match.end() if match else None


def final_present(text, family):
    last = text.strip().splitlines()[-1] if text.strip() else ''
    if family == 'math':
        return bool(re.fullmatch(r'\s*FINAL:\s*[-+\d.,/%$ ]+\s*', last, re.I) and re.search(r'\d', last))
    if family == 'route':
        return bool(re.match(r'\s*ROUTE\b', last, re.I))
    if family == 'code':
        if text.rstrip().endswith('```'):
            return first_answer_end(text, family) is not None
        try:
            return isinstance(json.loads(last).get('expression'), str)
        except (ValueError, AttributeError):
            return False
    return False


def measure(content_ids, marker_end, *, final, terminal, cap_hit, total_generated, budget):
    ids = list(content_ids)
    seen = set()
    repeated = 0
    post_repeated = 0
    post_positions = 0
    for position in range(3, len(ids)):
        gram = tuple(ids[position-3:position+1])
        repeated += gram in seen
        if marker_end is not None and position-3 >= marker_end:
            post_positions += 1
            post_repeated += gram in seen
        seen.add(gram)
    post_tokens = len(ids)-marker_end if marker_end is not None else 0
    novelty = 1-post_repeated/post_positions if post_positions else 0
    within_budget = terminal and final and not cap_hit and total_generated < budget
    return dict(schema=VERSION, descriptive_only=True, functional_admission=False,
        marker_found=marker_end is not None, post_first_answer_child_tokens=post_tokens,
        post_first_answer_4gram_novelty=novelty, rep4_self=repeated/max(1,len(ids)-3),
        revisitation_status='MEASURED_TOKEN_REPETITION_NOT_ASSUMED_SEMANTIC_RETURN',
        semantic_revisitation='UNREVIEWED',
        cap_hit=cap_hit, final_present=final, terminated_with_final_within_budget=bool(within_budget),
        persistence=bool(marker_end is not None and post_tokens >= 64 and novelty >= .8 and within_budget))
