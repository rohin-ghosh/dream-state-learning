"""Fixed fresh L1 collection; admission requires grounded, prefix-bound reading."""

from collections import Counter
import hashlib

from organism_v6 import orch_math_record as record_policy
from organism_v6 import orch_math_rich as original


DENOMINATOR = 1024
PER_FAMILY = 256
HELD_PER_FAMILY = 32
MAX_CALLS = 2048
SEED = 'MATH_SCALE_V1_20260914'
AXES = record_policy.AXES + ('neutral_prefix_compatible',)


def build_tasks(records, prior_documents):
    prior = [task for document in prior_documents for task in document['tasks']]
    excluded_ids = {task['id'] for task in prior}
    excluded_hashes = {original.digest(' '.join(task['question'].lower().split())) for task in prior}
    seen = set(excluded_hashes)
    pools = {name: [] for name in original.MINING + original.VALIDATION}
    for index, entry in enumerate(records):
        question = entry['question'].strip()
        identity = original.digest(' '.join(question.lower().split()))
        task_id = f'gsm8k-train-{index}'
        name = original.family(question)
        if identity in seen or task_id in excluded_ids or name not in pools:
            continue
        seen.add(identity)
        pools[name].append(dict(id=task_id, question=question, question_sha256=identity,
                               family=name, gold=str(original.number(entry['answer'].rsplit('####', 1)[1]))))
    mining, held = [], []
    for name, pool in pools.items():
        count = PER_FAMILY if name in original.MINING else HELD_PER_FAMILY
        ordered = sorted(pool, key=lambda task: original.digest(SEED + ':' + task['id']))
        if len(ordered) < count:
            raise ValueError('insufficient_fresh_family:' + name)
        (mining if name in original.MINING else held).extend(ordered[:count])
    document = dict(tasks=mining, held_tasks=held, denominator=DENOMINATOR,
                    per_family=PER_FAMILY, held_denominator=64, seed=SEED,
                    pool_counts={name: len(pool) for name, pool in pools.items()},
                    excluded_ids=sorted(excluded_ids), excluded_question_hashes=sorted(excluded_hashes),
                    no_l2_l3_access=True, maximum_calls=MAX_CALLS, fit_ready=False)
    validate(document)
    return document


def validate(document):
    tasks, held = document['tasks'], document['held_tasks']
    assert document['seed'] == SEED
    assert document['denominator'] == len(tasks) == DENOMINATOR
    assert document['per_family'] == PER_FAMILY
    assert document['held_denominator'] == len(held) == 64
    assert document['maximum_calls'] == MAX_CALLS
    assert Counter(task['family'] for task in tasks) == dict.fromkeys(original.MINING, PER_FAMILY)
    assert Counter(task['family'] for task in held) == dict.fromkeys(original.VALIDATION, HELD_PER_FAMILY)
    combined = tasks + held
    assert len({task['id'] for task in combined}) == len(combined)
    assert len({task['question_sha256'] for task in combined}) == len(combined)
    assert not {task['id'] for task in combined} & set(document['excluded_ids'])
    assert not {task['question_sha256'] for task in combined} & set(document['excluded_question_hashes'])
    for task in combined:
        assert task['question_sha256'] == original.digest(' '.join(task['question'].lower().split()))
        assert task['family'] == original.family(task['question'])
        original.number(task['gold'])


def prompt(task, kind, previous=None):
    if kind not in ('rich', 'new_record'):
        raise ValueError('scale_has_no_old_or_correction_branch')
    return record_policy.prompt(task, kind, previous)


def admit(row, decision, gold_review):
    if decision.get('student_prefix_sha256') != original.digest(row['student_prefix']):
        raise ValueError('review_must_bind_neutral_prefix')
    if decision.get('full_text_read') is not True:
        raise ValueError('full_text_review_required')
    if decision.get('neutral_prefix_compatible') not in (True, False, None):
        raise ValueError('explicit_prefix_axis_required')
    if 'neutral_prefix_compatible' not in decision or not decision.get('prefix_reason'):
        raise ValueError('explicit_prefix_disposition_required')
    if decision['status'] == 'PASS' and decision['neutral_prefix_compatible'] is not True:
        raise ValueError('unsupported_generation_only_claim')
    if hashlib.sha256(row['target'].encode()).hexdigest() != row['target_sha256']:
        raise ValueError('raw_target_changed')
    return original.admit(row, decision, gold_review.get('status') == 'VALID')


def corpus_gate(rows, complete, all_reviewed):
    admitted = [row for row in rows if row['admitted']]
    identities = {(row['task_id'], row['kind']) for row in admitted}
    unique_targets = {row['target_sha256'] for row in admitted}
    if len(identities) != len(admitted) or len(unique_targets) != len(admitted):
        raise ValueError('duplicate_targets_cannot_pad_corpus')
    return dict(admitted_distinct_targets=len(admitted),
                distinct_tasks=len({row['task_id'] for row in admitted}),
                corpus_threshold_met=bool(complete and all_reviewed and len(admitted) >= 1000),
                fit_ready=False, fit_recipe_published=False)
