import copy
import hashlib
import json
from pathlib import Path

import pytest

from organism_v6 import orch_math_scale as policy
from organism_v6 import orch_math_record as record_policy
from organism_v6 import orch_math_rich as original


def roster():
    return json.loads(Path('research_notes/analysis/orch_math_scale_20260914_attempt1/TASKS.json').read_text())


def row_and_review():
    task = roster()['tasks'][0]
    target = 'I used the given quantities to multiply and check the result.\nFINAL: ' + task['gold']
    row = original.capture(task, 'rich', dict(raw=target, token_ids=list(range(201)),
        terminal=True, truncated=False, prompt_tokens=50), policy.prompt(task, 'rich')[1])
    review = dict(status='PASS', target_sha256=hashlib.sha256(target.encode()).hexdigest(),
        student_prefix_sha256=original.digest(row['student_prefix']), reason='test fixture only',
        evidence_spans=['I used the given quantities'], full_text_read=True,
        prefix_reason='test fixture only', **dict.fromkeys(policy.AXES, True))
    return row, review


def test_frozen_roster():
    policy.validate(roster())


@pytest.mark.parametrize('field', ['id', 'question_sha256'])
def test_no_duplicate_roster(field):
    document = roster()
    document['tasks'][1][field] = document['tasks'][0][field]
    with pytest.raises(AssertionError):
        policy.validate(document)


def test_exact_existing_prompts():
    task = roster()['tasks'][0]
    for kind in ('rich', 'new_record'):
        assert policy.prompt(task, kind, 'my prior solution') == record_policy.prompt(task, kind, 'my prior solution')
    messages, student = policy.prompt(task, 'new_record', 'my prior solution')
    assert student[-1]['content'] == 'Write your own reusable record of this solved task.'
    assert messages[-1]['content'] == record_policy.NEW_RECORD
    assert len(messages) == 3
    with pytest.raises(ValueError):
        policy.prompt(task, 'old_record', 'prior')


def test_substantive_and_prefix_axes_required():
    row, review = row_and_review()
    assert policy.admit(row, review, {'status': 'VALID'})['admitted']
    for axis in policy.AXES:
        rejected = dict(review, **{axis: False})
        with pytest.raises(ValueError):
            policy.admit(row, rejected, {'status': 'VALID'})


def test_checker_claim_disposition_not_rewrite():
    row, review = row_and_review()
    row['target'] += '\nThe exact-answer checker confirmed my answer.'
    row['target_sha256'] = hashlib.sha256(row['target'].encode()).hexdigest()
    review.update(target_sha256=row['target_sha256'], status='FAIL', neutral_prefix_compatible=False,
                  prefix_reason='Checker event absent from neutral prefix.')
    result = policy.admit(row, review, {'status': 'VALID'})
    assert not result['admitted'] and result['target'] == row['target']


@pytest.mark.parametrize('field,value', [('full_text_read', False), ('student_prefix_sha256', 'wrong'),
                                        ('target_sha256', 'wrong'), ('prefix_reason', '')])
def test_review_bindings(field, value):
    row, review = row_and_review()
    review[field] = value
    with pytest.raises(ValueError):
        policy.admit(row, review, {'status': 'VALID'})


def test_suspect_gold_never_admitted():
    row, review = row_and_review()
    for status in ('INVALID', 'AMBIGUOUS', 'UNREVIEWED'):
        assert not policy.admit(row, review, {'status': status})['admitted']
    assert row['outcome_pass']


@pytest.mark.parametrize('tokens,expected', [(149, False), (150, True), (400, True), (401, False)])
def test_unchanged_length(tokens, expected):
    row, review = row_and_review()
    task = roster()['tasks'][0]
    row = original.capture(task, 'rich', dict(raw=row['target'], token_ids=list(range(tokens)),
        terminal=False, truncated=False, prompt_tokens=2048), row['student_prefix'])
    assert row['token_contract_pass'] is expected


def test_no_automatic_fit_or_padding():
    row, review = row_and_review()
    row = policy.admit(row, review, {'status': 'VALID'})
    assert not policy.corpus_gate([row], True, True)['corpus_threshold_met']
    with pytest.raises(ValueError):
        policy.corpus_gate([row, copy.deepcopy(row)], True, True)
    rows = [dict(row, task_id=str(index), target_sha256=str(index)) for index in range(1000)]
    assert policy.corpus_gate(rows, True, True)['corpus_threshold_met']
    assert not policy.corpus_gate(rows, True, True)['fit_ready']
    assert not policy.corpus_gate(rows, True, False)['corpus_threshold_met']


def test_reader_schema_requires_all_axes_and_hashes():
    from gpu.orch_math_scale_review import schema
    properties = schema()['properties']['reviews']['items']['properties']
    assert set(policy.AXES) <= set(properties)
    assert {'raw_call_sha256', 'target_sha256', 'student_prefix_sha256', 'full_text_read'} <= set(properties)


@pytest.mark.parametrize('gib,expected', [(1, 0), (1.499, 0), (1.5, 1), (2.99, 1), (3, 2), (20, 2)])
def test_memory_resource_only_gate(gib, expected):
    from gpu.orch_math_scale_review import memory_limit
    assert memory_limit(gib * 1024 ** 3) == expected


def test_reducer_rejects_raw_or_generation_prefix_changes(tmp_path):
    from gpu.orch_math_scale_reduce import reduce
    from gpu.orch_math_rich_screen import write
    task = roster()['tasks'][0]
    guided, student = policy.prompt(task, 'rich')
    target = 'I compute the answer.\nFINAL: ' + task['gold']
    row = original.capture(task, 'rich', dict(raw=target, messages=guided, token_ids=list(range(201)),
        terminal=True, truncated=False, prompt_tokens=40), student)
    write(tmp_path / 'TASKS.json', roster())
    directory = tmp_path / 'shard0'
    directory.mkdir()
    write(directory / 'CALL_0001.json', row)
    result, _ = reduce(tmp_path)
    assert result['denominator'] == 1024 and result['calls'] == 1
    assert not result['complete'] and result['admitted_distinct_targets'] == 0
    row['call']['messages'] = student
    write(directory / 'CALL_0001.json', row)
    with pytest.raises(AssertionError):
        reduce(tmp_path)
