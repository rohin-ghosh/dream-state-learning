"""High-budget child-only richness generation; nothing is automatically qualified."""

from organism_v6 import orch_math_rich as original
from organism_v6.orch_rich_intensity import LIGHT
from organism_v6.orch_rich_twopass import CONTINUE_GUIDANCE, BRANCH_GUIDANCE


CONDITIONS = ('ORIGINAL_RICH', 'LIGHT_BRANCH', 'TWO_PASS', 'META_EVALUATE')
CAP = 8192
CONTEXT = 16384
SECONDS = 16 * 3600
MAX_TASKS = 1024
SOURCE_SHA = '17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465'
INITIAL_STATE = '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
UUIDS = ('GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0', 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4',
         'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05', 'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733',
         'GPU-d304a15c-516a-16a0-a926-a560304077cc', 'GPU-0cc84073-37a0-4f7a-e555-11671425bd03',
         'GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf', 'GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed')
DEVICES = {f'shard{index}': (index, uuid) for index, uuid in enumerate(UUIDS)}
RICH = original.RICH_GUIDANCE.replace(', using 150–400 tokens', '')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def question_hash(question):
    return original.digest(' '.join(question.lower().split()))


def roster(records, excluded_ids, excluded_questions):
    tasks, seen = [], set(excluded_questions)
    for index, record in enumerate(records):
        identity = f'gsm8k-train-{index}'
        question = record['question'].strip()
        digest = question_hash(question)
        if identity in excluded_ids or digest in seen:
            continue
        gold = str(original.number(record['answer'].rsplit('####', 1)[1]))
        tasks.append(dict(id=identity, question=question, question_sha256=digest,
                          gold=gold, family=original.family(question) or 'other'))
        seen.add(digest)
    tasks.sort(key=lambda task: original.digest(['ORCH_RICH_HOT_NODE2_20260915_V1', task['id']]))
    selected = tasks[:MAX_TASKS]
    require(bool(selected), 'no_fresh_cached_tasks')
    return dict(tasks=selected, denominator=len(selected), available=len(tasks), conditions=list(CONDITIONS),
                max_calls=6 * len(selected), max_new_tokens=CAP, context=CONTEXT, seconds=SECONDS,
                excluded_ids=sorted(excluded_ids), excluded_question_hashes=sorted(excluded_questions),
                parent_calls=0, fits=0, semantic_reviews=0, admitted_rows=0)


def messages(task, condition, previous=None):
    require(condition in CONDITIONS, 'unknown_condition')
    guidance = LIGHT if condition == 'LIGHT_BRANCH' else RICH
    initial = [dict(role='system', content=guidance), dict(role='user', content=task['question'])]
    if previous is None:
        return initial
    require(condition in ('TWO_PASS', 'META_EVALUATE'), 'second_pass_not_allocated')
    instruction = CONTINUE_GUIDANCE if condition == 'TWO_PASS' else BRANCH_GUIDANCE
    instruction += ' Finish with a separate line FINAL: followed by just the numeric answer.'
    return initial + [dict(role='assistant', content=previous), dict(role='user', content=instruction)]


def outcome(task, response):
    answer = original.final_value(response['raw'])
    correct = answer is not None and answer == original.number(task['gold']) and response['terminal'] and not response['truncated']
    category = ('registered_correct' if correct else 'truncation' if response['truncated'] else
                'nonterminal_other' if not response['terminal'] else 'missing_exact_FINAL' if answer is None else 'parsed_wrong')
    return dict(answer=str(answer) if answer is not None else None, correct=bool(correct), category=category,
                semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False,
                content_tokens=len(response['token_ids']) - int(response['terminal']), raw_above_400_retained=True)
