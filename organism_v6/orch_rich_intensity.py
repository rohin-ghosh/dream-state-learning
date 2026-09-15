"""Paired generator selection with unchanged outcome and fulltext admission."""

from collections import Counter

from organism_v6 import orch_math_rich as original
from organism_v6 import orch_math_scale as scale


CONDITIONS = ('control', 'light', 'dense')
CONTEXT_LIMIT = 4096
TASKS_SHA = '3e320ce8c06878a13da0400475977082cedd8379eab780ad82c5de8f1aa50c43'
BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
LIGHT = (
    'Solve this problem in your own voice. Think expansively where it matters: '
    'explore the considerations that could change the answer and concentrate '
    'on the most consequential uncertainty. Evaluate your provisional '
    'conclusion and pursue the most useful question or check it raises. '
    'Let the evidence determine how far each branch deserves to go. Use '
    'the available space for useful reasoning, not padding or repetition; '
    'do not invent facts or observations. Finish with a separate line '
    'FINAL: followed by just the numeric answer.'
)
DENSE = (
    'Solve this problem in your own voice by developing and testing useful '
    'branches of reasoning. First identify the requested quantity, its units, '
    'the relevant given facts and any assumptions. Consider genuinely '
    'different possible operations, interpretations, or checks. For each '
    'relevant consideration, explain what it implies for this problem and '
    'which given evidence supports or rules it out; do not manufacture '
    'disagreement where the evidence is clear. Prioritize the consideration '
    'whose uncertainty or consequence could most change your answer. Spend '
    'more reasoning on that branch and less on already settled details. '
    'Carry the chosen operations through to a provisional numerical answer. '
    'Evaluate that conclusion against the original quantities, units and '
    'constraints. Ask what useful unresolved question follows from this '
    'evaluation. Develop its consequence or perform an informative independent '
    'check, then explain whether this strengthens or revises your answer and '
    'why. State the concrete operation you would reuse and the circumstances '
    'where it applies. Distinguish given facts from assumptions throughout. '
    'No requirement for headings, equal-length branches, or a particular '
    'length: continue only while the reasoning adds something. Do not pad, '
    'repeat, invent observations, or substitute generic advice for working '
    'with this problem. Finish with a separate line FINAL: followed by just '
    'the numeric answer.'
)
PROMPTS = dict(control=original.RICH_GUIDANCE, light=LIGHT, dense=DENSE)


def generation_cap(condition, kind):
    if condition not in CONDITIONS or kind not in ('rich', 'new_record'):
        raise ValueError('unknown_generation_condition_or_kind')
    return 512 if condition == 'control' or kind == 'new_record' else 1536


def capture(task, kind, result, student):
    row = original.capture(task, kind, result, student)
    bounded = (150 <= row['generated_tokens'] <= 400 and not result['truncated']
               and result['prompt_tokens'] <= CONTEXT_LIMIT)
    row.update(token_contract_pass=bounded, candidate=bool(row['outcome_pass'] and bounded),
               prospective_context_limit=CONTEXT_LIMIT, raw85_source_not_automatic_training_row=True)
    return row


def validate(document):
    tasks = document['tasks']
    assert len(tasks) == document['denominator'] == 256
    assert document['per_family'] == 64 and document['maximum_calls'] == 1536
    assert document['seed'] == 'RICH_INTENSITY_COMMON_V1_20260915'
    assert Counter(task['family'] for task in tasks) == dict.fromkeys(original.MINING, 64)
    assert len({task['id'] for task in tasks}) == len({task['question_sha256'] for task in tasks}) == 256
    assert len(set(document['excluded_ids'])) == len(set(document['excluded_question_hashes'])) == 1216
    assert not {task['id'] for task in tasks} & set(document['excluded_ids'])
    assert not {task['question_sha256'] for task in tasks} & set(document['excluded_question_hashes'])
    for task in tasks:
        assert task['question_sha256'] == original.digest(' '.join(task['question'].lower().split()))
        assert task['family'] == original.family(task['question'])
        original.number(task['gold'])


def allocation(index):
    if index not in range(6):
        raise ValueError('only_owned_node3_physical_0_to_5')
    return CONDITIONS[index // 2], index % 2


def prompt(task, condition, kind, previous=None):
    if condition not in CONDITIONS:
        raise ValueError('unknown_condition')
    if kind == 'rich':
        guided, student = original.prompt(task, 'rich')
        return [dict(role='system', content=PROMPTS[condition])] + guided[1:], student
    if kind != 'new_record':
        raise ValueError('no_corrections_or_additional_calls')
    return scale.prompt(task, kind, previous)


def admit(row, decision, gold_review):
    return scale.admit(row, decision, gold_review)
