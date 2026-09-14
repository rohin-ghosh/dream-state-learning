"""Frozen fresh-cohort policy and independent paired math reduction."""

from collections import Counter
import hashlib
import json
import math

from organism_v6.orch_math_rich import MINING, digest, family, final_value, number, prompt


SEED = 'MATH_REPLICATION_FRESH_V1_20260914'
DATA_SHA256 = '17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465'
MANIFEST_SHA256 = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
KINDS = ('terse', 'rich', 'correction', 'record')
AXES = ('first_person', 'grounded_operations', 'checkable_expectation',
        'reusable_content', 'no_padding', 'no_false_premises')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


def build_cohort(records, excluded_ids):
    excluded = set(excluded_ids)
    if len(excluded) != 32:
        raise ValueError('original_32_unique_ids_required')
    pools = {name: [] for name in MINING}
    seen = set()
    for index, record in enumerate(records):
        identity = f'gsm8k-train-{index}'
        question = record['question'].strip()
        question_hash = digest(' '.join(question.lower().split()))
        if question_hash in seen:
            continue
        seen.add(question_hash)
        category = family(question)
        if identity in excluded or category not in pools:
            continue
        pools[category].append(dict(id=identity, question=question,
                                    question_sha256=question_hash, family=category,
                                    source_index=index))
    selected = []
    for category in MINING:
        ordered = sorted(pools[category], key=lambda task: digest(SEED + ':' + task['id']))
        if len(ordered) < 8:
            raise ValueError('insufficient_fixed_family:' + category)
        for task in ordered[:8]:
            answer = records[task['source_index']]['answer']
            suffix = answer.rsplit('####', 1)[-1].strip() if '####' in answer else ''
            try:
                gold = str(number(suffix))
                gold_status = 'PARSED_NOT_SEMANTICALLY_VALIDATED'
            except (ValueError, ZeroDivisionError):
                gold, gold_status = None, 'UNRESOLVED_NUMERIC_GOLD'
            selected.append(dict(task, gold=gold, gold_status=gold_status,
                                 gold_source_suffix=suffix))
    result = dict(tasks=selected, denominator=32, per_family=8, seed=SEED,
                  excluded_original_ids=sorted(excluded), dataset_sha256=DATA_SHA256,
                  no_reference_rationales=True, fits=0, updates=0)
    validate_cohort(result)
    return result


def validate_cohort(document):
    tasks = document['tasks']
    ids = [task['id'] for task in tasks]
    if (document['seed'] != SEED or document['denominator'] != 32
            or document['per_family'] != 8 or len(tasks) != 32 or len(set(ids)) != 32
            or Counter(task['family'] for task in tasks) != Counter({name: 8 for name in MINING})
            or len({task['question_sha256'] for task in tasks}) != 32
            or set(ids) & set(document['excluded_original_ids'])
            or document['dataset_sha256'] != DATA_SHA256):
        raise ValueError('frozen_cohort_contract_changed')
    return tasks


def initial_order(position):
    return ('terse', 'rich') if position % 2 == 0 else ('rich', 'terse')


def capture(task, kind, result, student):
    if kind not in KINDS:
        raise ValueError('unknown_kind')
    raw = result['raw']
    predicted = final_value(raw)
    success = (result.get('error') is None and task['gold'] is not None
               and predicted is not None and predicted == number(task['gold']))
    generated = len(result['token_ids']) - int(bool(result['token_ids']) and result['terminal'])
    bounded = (150 <= generated <= 400 and not result['truncated']
               and result['prompt_tokens'] <= 2048 and result.get('error') is None)
    return dict(task_id=task['id'], family=task['family'], kind=kind,
                gold=task['gold'], gold_status=task['gold_status'], outcome_pass=success,
                token_contract_pass=bounded, generated_tokens=generated,
                candidate=kind != 'terse' and success and bounded,
                semantic_status='UNREVIEWED', admitted=False, student_prefix=student,
                target=raw, target_sha256=hashlib.sha256(raw.encode()).hexdigest(), call=result)


def paired_counts(tasks, by_key):
    rich = terse = rich_only = terse_only = complete_pairs = 0
    for task in tasks:
        rich_row = by_key.get((task['id'], 'rich'))
        terse_row = by_key.get((task['id'], 'terse'))
        rich_pass = bool(rich_row and rich_row['outcome_pass'])
        terse_pass = bool(terse_row and terse_row['outcome_pass'])
        rich += rich_pass
        terse += terse_pass
        rich_only += rich_pass and not terse_pass
        terse_only += terse_pass and not rich_pass
        complete_pairs += bool(rich_row and terse_row
                               and not rich_row['call'].get('error')
                               and not terse_row['call'].get('error'))
    discordant = rich_only + terse_only
    probability = min(1.0, 2 * sum(math.comb(discordant, count)
                      for count in range(min(rich_only, terse_only) + 1)) / 2 ** discordant)
    return dict(denominator=len(tasks), rich=rich, terse=terse, rich_only=rich_only,
                terse_only=terse_only, difference=(rich - terse) / len(tasks),
                exact_mcnemar_two_sided=probability, complete_pairs=complete_pairs,
                complete=complete_pairs == len(tasks))


def reduce_native(document, rows):
    tasks = validate_cohort(document)
    task_map = {task['id']: task for task in tasks}
    by_key = {}
    for row in rows:
        key = (row['task_id'], row['kind'])
        if key in by_key or key[0] not in task_map or key[1] not in KINDS:
            raise ValueError('duplicate_or_foreign_native_row')
        expected = capture(task_map[key[0]], key[1], row['call'], row['student_prefix'])
        if any(row[field] != expected[field] for field in
               ('family', 'outcome_pass', 'candidate', 'target', 'target_sha256',
                'token_contract_pass', 'generated_tokens', 'gold', 'gold_status')):
            raise ValueError('native_row_or_oracle_drift')
        by_key[key] = row
    if len(rows) > 128:
        raise ValueError('call_cap_exceeded')
    families = {name: paired_counts([task for task in tasks if task['family'] == name], by_key)
                for name in MINING}
    for counts in families.values():
        counts['gap_eligible'] = counts['complete'] and counts['rich'] > counts['terse']
    return dict(primary=paired_counts(tasks, by_key), families=families, calls=len(rows),
                failures=sum(bool(row['call'].get('error')) for row in rows),
                candidates=sum(row['candidate'] for row in rows),
                by_kind={kind: dict(calls=sum(row['kind'] == kind for row in rows),
                                   successes=sum(row['kind'] == kind and row['outcome_pass'] for row in rows),
                                   candidates=sum(row['kind'] == kind and row['candidate'] for row in rows))
                         for kind in KINDS},
                unresolved_numeric_gold=[task['id'] for task in tasks if task['gold'] is None],
                fits=0, updates=0, claim='FRESH_PUBLIC_SAME_FAMILY_DEV_PROMPT_SCREEN_ONLY')


def review_row(row, decision):
    if decision.get('status') not in ('PASS', 'FAIL', 'UNRESOLVED'):
        raise ValueError('explicit_fulltext_decision_required')
    if decision.get('target_sha256') != row['target_sha256'] or not decision.get('reason'):
        raise ValueError('exact_target_and_reason_required')
    if decision.get('full_text_read') is not True:
        raise ValueError('fulltext_read_required')
    spans = decision.get('evidence_spans', [])
    if not spans or any(not span.strip() or span not in row['target'] for span in spans):
        raise ValueError('exact_quoted_evidence_required')
    if decision['status'] == 'PASS':
        if not row['candidate'] or not all(decision.get(axis) is True for axis in AXES):
            raise ValueError('all_semantic_axes_and_candidate_required')
        if row['kind'] == 'correction' and decision.get('meaningful_revision') is not True:
            raise ValueError('meaningful_revision_required')
        if row['kind'] == 'record' and decision.get('operational_record') is not True:
            raise ValueError('operational_record_required')
    return dict(row, semantic_status=decision['status'], review=decision)
