"""Distinct C2-51 lineage identities; never aliases for the five exited runs."""

try:
    from gpu.r213_policy import prompt as previous_prompt
except ModuleNotFoundError:
    from r213_policy import prompt as previous_prompt

ASSIGNMENTS = {
    'conversational': (0, 'siege', 'envoy'),
    'r213_math_a': (1, 'math', 'strict dense'),
    'r213_math_b_fork': (2, 'math', 'walkthrough'),
    'r213_siege_scout_fork': (3, 'siege', 'scout'),
    'r213_math_c': (4, 'math', 'self derive'),
    'r213_siege_negotiator_fork': (5, 'siege', 'negotiator'),
    'r213_siege_quartermaster_fork': (6, 'siege', 'quartermaster'),
    'r213_siege_challenger_fork': (7, 'siege', 'challenger'),
}
GROUPS = {receiver: tuple(sender for sender in ASSIGNMENTS
    if sender != receiver and ASSIGNMENTS[sender][1] == assignment[1])
    for receiver, assignment in ASSIGNMENTS.items()}
FORKS = tuple(name for name in ASSIGNMENTS if name.endswith('_fork'))
STYLES = dict(zip(FORKS, ('peer_math', 'peer_repo', 'p32', 'lr03', 'lr3')))


def prompt(name, turn=0):
    if name not in FORKS:
        raise ValueError('new_fork_parent_only')
    task = previous_prompt(STYLES[name], turn).split('Write in English.', 1)[1]
    return ('Astra, operator-authored parent. You are a NEW C2 fork named ' + name
        + ', born from fixed checkpoint51, optimizer4908 and context5846. You are not a continuation '
        'of an interrupted node3 trial. Earlier P32 and learning-rate experiments belong to other '
        'histories, not yours. Your baseline recipe is sixteen presentations and learning rate0.00003. '
        'Your own new lineage begins now; do not claim exact continuity with a lost resident state. '
        'Write in English.' + task)
