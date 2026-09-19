"""Prospective decoding-budget comparison; no training or retrospective scoring."""

from collections import Counter

from organism_v6 import orch_l2_rich_math as original


SEED = 'ORCH_L2_BUDGET_READOUT_20260915_ATTEMPT1_V1'
ARMS = original.ARMS
CAPS = (512, 1536)
CONTEXT = 4096
SECONDS = 3600
MAX_CALLS = 320
CALLS_PER_ARM = 80
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
STATES = dict(
    GUIDED_SLEEP='d0b7630bfadf571083e9bac495216d4737b9e656670bda63f94852f60c5fe011',
    GUIDED_FROZEN='12354524c434be91deaeae74f411091bc70b4e38c003fd4f800aea797cc770c8',
    UNPARENTED_SLEEP='0d06058c3a304d4d3734cc47ab8142d3285919d899cceabaf73383a98bcf9219',
    BOOTSTRAP_OFF='a525b5b3287a44ce3ce0d64a56c941e7ee33b1be0309f20ce68ded1dee0f9e6d')
DEVICES = dict(zip(ARMS, enumerate((
    'GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0',
    'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4',
    'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05',
    'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733'))))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def task_key(task):
    return tuple(task[name] for name in ('left_modulus', 'right_modulus', 'left_residue', 'right_residue'))


def cohort(previous):
    require(previous == original.cohort(), 'original_cohort_binding_mismatch')
    excluded = {task_key(task) for split in ('train', 'held') for group in previous[split] for task in group}
    require(len(excluded) == 56, 'original_56_required')
    used = set(excluded)
    tasks = []
    for position in range(16):
        left, right = original.PAIRS[position % 4]
        counter = 0
        while True:
            seed = int(original.digest([SEED, position, counter]), 16)
            key = (left, right, seed % left, (seed // left) % right)
            if key not in used:
                break
            counter += 1
        used.add(key)
        task = dict(id=f'{original.FAMILY}_BUDGET_HELD_{position:02d}', family=original.FAMILY,
                    left_modulus=left, right_modulus=right, left_residue=key[2], right_residue=key[3])
        task.update(question=original.question(task), reference_answer=original.reference(task))
        tasks.append(task)
    tasks.sort(key=lambda task: original.digest([SEED, 'ORDER', task['id']]))
    return dict(seed=SEED, tasks=tasks, excluded_keys=[list(key) for key in sorted(excluded)], original_cohort_digest=original.digest(previous),
                budget_order=[list(CAPS if position % 2 == 0 else reversed(CAPS)) for position in range(16)],
                prompt_policy='unchanged original.question; one neutral user message; identical across budgets',
                context=CONTEXT, math_calls_per_arm=32, retention_calls_per_arm=48, total_calls=MAX_CALLS,
                seconds=SECONDS, gpu_hours=4, fits=0, parent_calls=0, retries=0)


def score(task, response):
    registered = original.judge(task, response['raw'])
    correct = bool(registered['correct'] and response['terminal'] and not response['truncated'])
    if correct:
        category = 'registered_correct'
    elif response['truncated']:
        category = 'truncation'
    elif not response['terminal']:
        category = 'nonterminal_other'
    elif registered['answer'] is None:
        category = 'missing_exact_FINAL'
    else:
        category = 'parsed_wrong'
    return dict(answer=registered['answer'], correct=correct, category=category)


def summarize(records):
    results = {}
    for arm in ARMS:
        rows = [row for row in records if row['arm'] == arm and row['kind'] == 'math']
        budgets = {}
        for budget in CAPS:
            selected = [row for row in rows if row['max_new_tokens'] == budget]
            budgets[str(budget)] = dict(correct=sum(row.get('score', {}).get('correct', False) for row in selected),
                denominator=16, completed=len(selected), failures=dict(Counter(
                    row.get('score', {}).get('category', 'call_error') for row in selected)))
        pairs = Counter()
        for task_id in {row['task_id'] for row in rows}:
            pair = {row['max_new_tokens']: row for row in rows if row['task_id'] == task_id}
            if set(pair) != set(CAPS) or any('score' not in row for row in pair.values()):
                pairs['incomplete'] += 1
                continue
            low, high = (pair[budget]['score']['correct'] for budget in CAPS)
            pairs['both' if low and high else '512_only' if low else '1536_only' if high else 'neither'] += 1
        results[arm] = dict(budgets=budgets, paired_outcomes=dict(pairs))
    return results
