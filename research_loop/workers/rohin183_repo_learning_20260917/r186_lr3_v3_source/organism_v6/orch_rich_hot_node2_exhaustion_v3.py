"""Prospective exhaustion supply with explicit steering and unaudited claims."""

from collections import Counter
import re
from types import FunctionType

from organism_v6 import orch_rich_hot_node2_floor98 as prior


VERSION = 'ROHIN100_EXHAUSTION_V3'
TARGET = 16384
CONTEXT = 32768
MAX_CALLS = 65536
PER_SLOT = 8192
CONDITIONS = ('EXHAUSTION_ONLY', 'STEERED_LIGHT', 'STEERED_TWO_PASS', 'STEERED_META')
EXHAUSTION = (
    'Enumerate the candidate approaches explicitly. Pursue at least two distinct worked methods: '
    'state each hypothesis, carry out its reasoning using the actual task and available observations, '
    'compare the results, and choose with a reason why the other approaches lose or are less suitable. '
    'Use separate headings APPROACH 1:, APPROACH 2:, and so on for methods you actually work through. '
    'A heading or repeated paraphrase is not a worked method. Do not invent evidence, tests run, '
    'observations or disagreements. Keep rejected paths as part of the reasoning, not as automatic '
    'task failures. Do not pad or repeat to consume the budget. No fixed length or first-person style is required. '
)
STEERING = (
    '',
    'Steering degree1: contrast a direct construction with an independent reverse or boundary check. ',
    'Steering degree2: compare a direct construction and a decomposition; work each through and check '
    'whether both satisfy the task constraints. ',
    'Steering degree3: compare direct, decomposed, and counterexample-based approaches; prioritize '
    'the constraint that could invalidate your provisional choice, and explain how the evidence resolves it. ',
)


def guidance(shard):
    if type(shard) is not int or shard not in range(8):
        raise ValueError('node2_only')
    return EXHAUSTION + STEERING[shard // 2]


def task_at(document, batch, position, shard):
    position = position + 1 if shard == 0 else position
    task = prior.task_at(document, batch, position)
    return dict(task, prompt_version=VERSION,
                prospective_train_source_reuse=True, matched_pair=shard in (0, 1))


def messages(task, shard, previous=None):
    result = prior.previous.messages(task, 'ORIGINAL_RICH')
    result[0] = dict(role='system', content=guidance(shard))
    if task['family'] == 'math':
        result[-1]['content'] += '\nFinish with a separate line FINAL: followed by just the numeric answer.'
    if previous is not None:
        result += [dict(role='assistant', content=previous), dict(role='user', content=(
            'Reassess your own worked methods and comparison; complete any missing substantive work. '
            'No external feedback has been supplied. ' +
            ('Finish with a separate line FINAL: followed by just the numeric answer.' if task['family'] == 'math' else
             'Finish with the expression JSON object on its own last line.')))]
    return result


def effective_budget(prompt_tokens):
    if type(prompt_tokens) is not int or not 0 < prompt_tokens < CONTEXT:
        raise ValueError('context_overflow_no_dispatch_no_cropping')
    return min(TARGET, CONTEXT - prompt_tokens)


def remaining_cap(historical_counts, new_counts, shard):
    return max(0, min(MAX_CALLS - sum(historical_counts) - sum(new_counts),
                      PER_SLOT - historical_counts[shard] - new_counts[shard]))


def claim_metrics(raw):
    labels = re.findall(r'^\s*(?:#+\s*|\*\*)?APPROACH\s+(\d+)\s*:', raw, re.IGNORECASE | re.MULTILINE)
    sentences = [' '.join(part.lower().split()) for part in re.split(r'[.!?\n]+', raw)]
    repeated = Counter(part for part in sentences if len(part.split()) >= 12)
    duplicates = sum(count - 1 for count in repeated.values())
    return dict(claimed_approach_count=len(set(labels)), claim_measure='EXPLICIT_HEADINGS_NOT_SEMANTIC_PROOF',
                audited_semantic_worked_methods=None, branching_semantic_annotation='UNREVIEWED',
                repeated_long_sentence_count=duplicates, repetition_failure_screen=any(count >= 3 for count in repeated.values()),
                repetition_screen_is_not_semantic_verdict=True)


def outcome(task, response):
    return dict(prior.outcome(task, response), **claim_metrics(response['raw']))


def route_task(task, shard, generate):
    source = prior.previous
    world = task['payload']
    environment = source.runtime(world['master'])
    collection = environment['collect_world'](world, lambda prompts: generate('exposure', prompts))
    environment['replay_collection'](collection)
    store = {record['edge']['event']: record['event']['raw'] for record in collection['records'] if record['accepted']}
    namespace = dict(source.route.__dict__, GUIDANCE=guidance(shard))
    episode = FunctionType(source.route.episode.__code__, namespace, 'episode', source.route.episode.__defaults__)
    tasks = [public for index, public in enumerate(environment['build_tasks'](world)) if index in (0, 2)]
    episodes = [episode(world, public, lambda prompts, goal=goal: generate(f'goal{goal}', prompts), store)
                for goal, public in enumerate(tasks)]
    return dict(collection=collection, episodes=episodes, accepted_events=collection['accepted_events'],
                complete_routes=sum(record['correct'] for record in episodes), route_denominator=2,
                semantic_status='UNREVIEWED', trainingAllowed=False, source_exposure_is_not_exhaustion_target=True)
