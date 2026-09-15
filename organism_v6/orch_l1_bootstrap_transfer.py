"""Prospective fixed-elicitation readout; never automatic semantic admission."""

from collections import Counter
import hashlib

from organism_v6 import orch_math_rich as original


ARMS = ('FULL', 'OFF', 'ORIGINAL37EC')
STATES = dict(FULL='12354524c434be91deaeae74f411091bc70b4e38c003fd4f800aea797cc770c8',
    OFF='a525b5b3287a44ce3ce0d64a56c941e7ee33b1be0309f20ce68ded1dee0f9e6d',
    ORIGINAL37EC='37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0')
DEVICES = dict(FULL=(4, 'GPU-31583768-d90f-520c-51ed-5dac761526d0'),
    OFF=(5, 'GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9'),
    ORIGINAL37EC=(6, 'GPU-6de3930d-104a-f969-7d36-009271368dd1'))
SEED = 'L1_BOOTSTRAP_TRANSFER_20260915_ATTEMPT1_V1'
SOURCE_SHA = '17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465'
PACKET_SHA = '52197d8d0f73528af69b61e6f244e5b1570f2bcfafd5ebb79d4058c959946837'
HOST_SHA = '6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'
CAP = 1536
SECONDS = 5400
IN_FAMILIES = ('percentages',)
QUOTAS = dict(percentages=16, work_rates=4, fractional_quantities=4,
    group_accounting=4, geometry_measurement=2, age_time_relations=2)


def question_hash(question):
    return original.digest(' '.join(question.lower().split()))


def exclusions(documents):
    identifiers, hashes = set(), set()

    def visit(value):
        if isinstance(value, dict):
            for key in ('id', 'task_id'):
                if isinstance(value.get(key), str):
                    identifiers.add(value[key])
            if isinstance(value.get('question'), str):
                hashes.add(question_hash(value['question']))
            identifiers.update(value.get('excluded_ids', []))
            hashes.update(value.get('excluded_question_hashes', []))
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    for document in documents:
        visit(document)
    return identifiers, hashes


def cohort(records, documents):
    identifiers, hashes = exclusions(documents)
    pools = {family: [] for family in QUOTAS}
    seen = set(hashes)
    for index, record in enumerate(records):
        task_id = f'gsm8k-train-{index}'
        question = record['question'].strip()
        digest = question_hash(question)
        family = original.family(question)
        if task_id in identifiers or digest in seen or family not in pools:
            continue
        seen.add(digest)
        pools[family].append(dict(id=task_id, question=question, question_sha256=digest,
            gold=str(original.number(record['answer'].rsplit('####', 1)[1])), family=family,
            stratum='in_family' if family in IN_FAMILIES else 'out_family'))
    tasks = []
    for family, count in QUOTAS.items():
        assert len(pools[family]) >= count, ('insufficient_fresh_pool', family)
        tasks.extend(sorted(pools[family], key=lambda task: original.digest(SEED + ':' + task['id']))[:count])
    tasks.sort(key=lambda task: original.digest(SEED + ':ORDER:' + task['id']))
    assert len(tasks) == len({task['id'] for task in tasks}) == 32
    assert len({task['question_sha256'] for task in tasks}) == 32
    assert Counter(task['family'] for task in tasks) == QUOTAS
    return dict(tasks=tasks, seed=SEED, denominator=32, quotas=QUOTAS,
        pool_counts={family: len(pool) for family, pool in pools.items()},
        excluded_ids=sorted(identifiers), excluded_question_hashes=sorted(hashes),
        prompts=[original.prompt(task, 'rich')[0] for task in tasks],
        max_new_tokens=CAP, max_calls=96, seconds=SECONDS, gpu_hours=4.5,
        training=False, parent_calls=0, record_calls=0, retries=0)


def score(task, response):
    parsed = original.final_value(response['raw'])
    token_count = len(response['token_ids']) - int(bool(response['token_ids']) and response['terminal'])
    return dict(answer=str(parsed) if parsed is not None else None,
        outcome_pass=parsed is not None and parsed == original.number(task['gold']),
        generated_tokens=token_count, total_generated_ids=len(response['token_ids']),
        token_contract_pass=150 <= token_count <= 400 and not response['truncated']
            and response['prompt_tokens'] <= 2048,
        terminal=response['terminal'], truncated=response['truncated'],
        target_sha256=hashlib.sha256(response['raw'].encode()).hexdigest(),
        semantic_status='UNREVIEWED', qualified_rich=None)


def summarize(cohort_document, records):
    expected = {(arm, task['id']) for arm in ARMS for task in cohort_document['tasks']}
    by_key = {(record['arm'], record['task_id']): record for record in records}
    assert len(by_key) == len(records) and set(by_key) <= expected
    arms = {}
    for arm in ARMS:
        counts = {}
        for stratum in ('all', 'in_family', 'out_family'):
            tasks = [task for task in cohort_document['tasks'] if stratum == 'all' or task['stratum'] == stratum]
            rows = [by_key.get((arm, task['id']), {}) for task in tasks]
            counts[stratum] = dict(denominator=len(tasks), completed=sum('response' in row for row in rows),
                outcome_pass=sum(row.get('score', {}).get('outcome_pass', False) for row in rows),
                failed=sum('error' in row for row in rows), not_completed=sum('response' not in row for row in rows),
                qualified_rich=None, semantic_status='AUTHOR_FULLTEXT_REVIEW_PENDING')
        arms[arm] = counts
    pairs = {}
    for comparator in ARMS[1:]:
        cells = Counter()
        for task in cohort_document['tasks']:
            full = by_key.get(('FULL', task['id']), {}).get('score', {}).get('outcome_pass', False)
            control = by_key.get((comparator, task['id']), {}).get('score', {}).get('outcome_pass', False)
            cells[f'{int(full)}{int(control)}'] += 1
        pairs[comparator] = dict(denominator=32, cells=dict(cells),
            net_outcome_difference=cells['10'] - cells['01'])
    return dict(arms=arms, paired_outcome=pairs, reserved_calls=len(records), maximum_calls=96,
        training=False, promotion=False, independent_review=False,
        claim='RETAINED_RICHNESS_FIXED_ELICITATION_NOT_SPONTANEOUS_H1_H2_OR_REPEATED_CYCLE_GAIN')
