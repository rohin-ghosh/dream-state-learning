"""Base-only reasoning permission/persistence, distinct from the 37ec run."""

import re
from types import FunctionType, SimpleNamespace

from organism_v6 import orch_rich_hot_node3_r107 as previous


PHASE = 'R107_GENUINE_BASE_REASONING_FIRST_1536_V1'
MAX_CALLS, MAX_SLOT_CALLS = 1536, 768
original, validate, display, tasks = previous.original, previous.validate, previous.display, previous.tasks
SYSTEM = (
    'Reason through this routing task in ordinary prose before committing your '
    'next action. The final protocol action is not the entire response: preceding '
    'prose can examine evidence, uncertainty, and the decision it supports. '
    'Use only the public task and actual conversation; identifiers are opaque '
    'and case-sensitive. There are at most six turns, four distinct memory reads, '
    'and two committed routes. A READ returns actual stored text. A ROUTE commits '
    'a currently listed port and returns the actual receipt and new CURRENT/PORTS. '
    'Arrival at GOAL ends the episode. Do not simulate results or another turn. '
    'After your reasoning, put exactly one action on the final nonempty line: '
    'READ EVENT <listedaddress> or ROUTE <listedport>. Put no text after that '
    'action. No STOP, retry, or multiple executed actions in one response.'
)
REASONING = (
    'You are allowed and encouraged to reason in ordinary prose BEFORE the '
    'required final action. The action-line rule does not restrict the whole '
    'response to a bare command. Work through the evidence, uncertainty, and '
    'consequences that matter for which memory to read or which route to take. '
    'Do not stop merely because you found the first plausible action: pursue '
    'the useful next question or unresolved issue before committing. Let that '
    'work affect the action you choose. Stop elaborating when further text '
    'would be repetition or padding. Do not invent memory contents, receipts, '
    'observations, or results. Read unseen evidence through an actual READ action. '
    'End with exactly one valid READ EVENT or ROUTE action on its own last line.'
)
META = (
    'Choose deliberately where to spend your reasoning effort. When you notice '
    'a limitation or a more useful direction, change the next reasoning step '
    'and, when warranted, the read or route you select. Follow through rather '
    'than merely announcing a realization. No prescribed branch count, check '
    'template, surprise, disagreement, or number of methods is required.'
)


def arm(index):
    previous.arm(index)
    return 'FROZEN_BASE_REASONING_PERSISTENCE' if index == 4 else 'FROZEN_BASE_FUNCTIONAL_ALLOCATION'


def guidance(index):
    return REASONING if arm(index) == 'FROZEN_BASE_REASONING_PERSISTENCE' else REASONING + '\n' + META


def roster(cohort):
    result = previous.roster(cohort)
    result['phase_version'] = PHASE
    for row in result['tasks']:
        row['arm'] = arm(row['index'])
    result['paired_prior_task_ids'] = True
    result['model_and_prompt_both_changed_no_single_factor_claim'] = True
    return result


def episode(world, task, generate, store, index):
    readout = SimpleNamespace(**dict(vars(original.readout), display=display))
    namespace = dict(original.episode.__globals__, SYSTEM=SYSTEM, GUIDANCE=guidance(index), readout=readout)
    function = FunctionType(original.episode.__code__, namespace, original.episode.__name__)
    return function(world, task, generate, store)


def assess(response):
    result = previous.assess(response)
    command_only = bool(re.fullmatch(r'(READ EVENT|ROUTE) [^\s]+', response['raw'].strip()))
    result.update(raw_command_only=command_only, raw_command_only_is_success=False,
                  qualified_action_changing_reasoning=False if command_only else None,
                  functional_metarealisation_to_changed_continuation=None,
                  qualified_functional_count=None, semantic_status='UNREVIEWED',
                  qualification_requires_bound_action_changing_reasoning_review=True,
                  trainingAllowed=False, feedback_claim=False)
    return result
