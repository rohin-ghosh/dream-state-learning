"""Prospective matched own-record yield test; no learning or scaling."""

from collections import Counter
from math import comb

from organism_v6 import orch_math_rich as original


PER_FAMILY = 16
DENOMINATOR = 64
AXES = ('first_person', 'grounded_operations', 'checkable_expectation',
        'reusable_content', 'no_padding')
NEW_RECORD = (
    'The final value passed the exact-answer checker. Write your own reusable '
    'record as an autobiographical account of how you solved this task, rather '
    'than instructions to another solver. Describe the evidence you actually '
    'used, the operation you chose and why, what you expected its result to '
    'mean, and the concrete check you made or can make from this problem. '
    'Explain which operation you would reuse and when. Distinguish given '
    'facts from your assumptions; do not claim observations you did not make. '
    'Retain its final answer. '
) + original.RICH_GUIDANCE


def build_tasks(records, excluded):
    excluded_ids = {task['id'] for task in excluded['tasks']}
    seen = {task['question_sha256'] for task in excluded['tasks']}
    pools = {name: [] for name in original.MINING}
    for index, record in enumerate(records):
        question = record['question'].strip()
        identity = original.digest(' '.join(question.lower().split()))
        task_id = f'gsm8k-train-{index}'
        name = original.family(question)
        if identity in seen or task_id in excluded_ids or name not in pools:
            continue
        seen.add(identity)
        pools[name].append(dict(id=task_id, question=question, question_sha256=identity,
                               family=name, gold=str(original.number(record['answer'].rsplit('####', 1)[1]))))
    tasks = []
    for name in original.MINING:
        ordered = sorted(pools[name], key=lambda task: original.digest('MATH_RECORD_SCREEN_V1:' + task['id']))
        if len(ordered) < PER_FAMILY:
            raise ValueError('insufficient_fresh_tasks')
        tasks.extend(ordered[:PER_FAMILY])
    document = dict(tasks=tasks, denominator=DENOMINATOR, per_family=PER_FAMILY,
                    seed='MATH_RECORD_SCREEN_V1', excluded_ids=sorted(excluded_ids),
                    no_l2_l3_access=True, fit_ready=False)
    validate(document)
    return document


def validate(document):
    tasks = document['tasks']
    assert document['denominator'] == len(tasks) == DENOMINATOR
    assert document['per_family'] == PER_FAMILY
    assert Counter(task['family'] for task in tasks) == dict.fromkeys(original.MINING, PER_FAMILY)
    assert len({task['id'] for task in tasks}) == len({task['question_sha256'] for task in tasks}) == DENOMINATOR
    assert not ({task['id'] for task in tasks} & set(document['excluded_ids']))


def prompt(task, kind, previous=None):
    if kind == 'rich':
        return original.prompt(task, 'rich')
    guided, student = original.prompt(task, 'record', previous)
    if kind == 'old_record':
        return guided, student
    if kind != 'new_record':
        raise ValueError('unknown_condition')
    return guided[:-1] + [dict(role='user', content=NEW_RECORD)], student


def pair_order(position):
    return ('old_record', 'new_record') if (position // 4) % 2 else ('new_record', 'old_record')


def paired_criterion(old, new, grounded_old, grounded_new, false_old, false_new, complete):
    wins = sum(after and not before for before, after in zip(old, new))
    losses = sum(before and not after for before, after in zip(old, new))
    discordant = wins + losses
    probability = sum(comb(discordant, count) for count in range(wins, discordant + 1)) / 2 ** discordant
    passed = (complete and wins - losses >= 8 and probability <= .05
              and grounded_new >= grounded_old and false_new <= false_old)
    return dict(wins=wins, losses=losses, difference=wins-losses, one_sided_exact_p=probability,
                grounded_old=grounded_old, grounded_new=grounded_new,
                false_old=false_old, false_new=false_new, prospectively_successful=passed)
