from collections import Counter
from copy import deepcopy
import json

import pytest

from organism_v6 import orch_r107_capability as policy


CHECKPOINT = '1' * 64
CODE_ANSWERS = (
    'value * value', 'abs(left - right)',
    'sum([item for item in values if item % 2 == 0])', 'sorted(values)',
    'min(max(value, lower), upper)', 'values[::-1]',
    'sum([1 for item in values if item >= threshold])',
    'sum([left_values[index] * right_values[index] for index in range(len(left_values))])',
)


def answer(task):
    if task['family'] == 'code':
        return json.dumps(dict(expression=CODE_ANSWERS[int(task['id'].rsplit('_', 1)[1])]))
    if task['family'] == 'toolcall':
        return json.dumps(task['oracle'])
    return task['oracle']['answer']


def response(task, raw=None, cap=512):
    return dict(raw=answer(task) if raw is None else raw, messages=policy.messages(task),
        token_ids=[7, 8, 9, 99], terminal=True, truncated=False,
        prompt_tokens=20, max_new_tokens=cap, context=2048, eos_token_id=99)


def capture(task, arm='ON', native=None):
    return policy.capture(task, arm, response(task) if native is None else native,
        checkpoint_sha256=CHECKPOINT, base_sha256=policy.BASE_SHA256, lora_enabled=arm == 'ON')


def reduce(rows, cap=512):
    return policy.reduce_paired(rows, checkpoint_sha256=CHECKPOINT,
                               base_sha256=policy.BASE_SHA256, max_new_tokens=cap)


def full_rows(cap=512):
    return [capture(task, arm, response(task, cap=cap)) for task in policy.tasks() for arm in policy.ARMS]


def test_fixed_balanced_unique_tasks_and_hashes():
    suite = policy.tasks()
    assert policy.digest(suite) == '32a1d71ff23e168f42366ec4c96777aceb59247020e7a3ae98b6f64b4b9b602c'
    assert len(suite) == len({task['id'] for task in suite}) == 32
    assert Counter(task['family'] for task in suite) == dict.fromkeys(policy.FAMILIES, 8)
    assert len({task['content_sha256'] for task in suite}) == 32
    assert suite == policy.tasks()
    for task in suite:
        private = {key: value for key, value in task.items() if key not in ('content_sha256', 'prompt_sha256')}
        assert policy.digest(private) == task['content_sha256']
        assert policy.digest(policy.messages(task)) == task['prompt_sha256']
        assert not task['trainingAllowed'] and task['source'] == policy.SOURCE
    suite[0]['oracle']['cases'][0]['expected'] = 999
    assert suite != policy.tasks()


def test_model_messages_are_only_public_minimal_prompt():
    for task in policy.tasks():
        actual = policy.messages(task)
        assert actual == [dict(role='user', content=task['prompt'])]
        assert not any(word in actual[0]['content'] for word in ('"oracle"', '"expected"', '"cases"', 'LoRA', 'checkpoint', 'parent'))
        actual[0]['content'] = 'mutated projection'
        assert policy.messages(task)[0]['content'] == task['prompt']


@pytest.mark.parametrize('task', policy.tasks(), ids=lambda task: task['id'])
def test_every_private_oracle_has_reference_parity(task):
    result = policy.score(task, answer(task))
    assert result['passed'] is True and result['category'] == 'correct'
    if task['family'] == 'code':
        assert result['passed_cases'] == result['total_cases'] == 4
        assert not result['arbitrary_execution']
    if task['family'] == 'toolcall':
        assert result['schema_valid'] and result['mock_only']


@pytest.mark.parametrize('changed', ['prompt', 'oracle', 'content_sha256', 'id', 'trainingAllowed'])
def test_tampered_task_cannot_be_rehashed_into_suite(changed):
    task = policy.tasks()[0]
    task[changed] = 0 if changed == 'trainingAllowed' else 'changed'
    with pytest.raises(ValueError, match='task_content'):
        policy.messages(task)
    with pytest.raises(ValueError, match='task_content'):
        policy.score(task, '{}')


@pytest.mark.parametrize('expression', [
    '__import__("os").system("touch never")', 'open("never")', 'value.__class__',
    '(lambda item: item)(value)', '2 ** 1000000', '[0] * 1000000000',
    'list(range(1000000000))', '1 / 0', 'unknown_name', '"literal"',
])
def test_code_is_bounded_no_generated_python_execution(expression):
    result = policy.score(policy.tasks()[0], json.dumps(dict(expression=expression)))
    assert not result['passed']
    assert result['category'] == 'unsafe_or_invalid_expression'
    assert not result['arbitrary_execution']


def test_code_wrong_answer_and_bool_not_integer():
    for expression in ('0', 'True'):
        result = policy.score(policy.tasks()[0], json.dumps(dict(expression=expression)))
        assert not result['passed']
    assert not policy._equal(True, 1)
    assert not policy._equal([True], [1])
    assert policy._equal(3.0, 3)


@pytest.mark.parametrize('raw', ['```json\n{"expression":"value*value"}\n```',
    '{"expression":"0","expression":"value*value"}',
    '{"expression":"value*value","note":"extra"}', '{"expression":7}', '[]'])
def test_code_exact_json_schema(raw):
    assert not policy.score(policy.tasks()[0], raw)['passed']


@pytest.mark.parametrize('raw', ['FINAL: 45', 'The answer is45.', '45 then46', 'NaN', 'Infinity', '1/0', '4,5', '45.001'])
def test_math_no_prose_or_nonfinite_salvage(raw):
    assert not policy.score(policy.tasks()[8], raw)['passed']


def test_math_numeric_equivalence_and_missing():
    task = policy.tasks()[8]
    for raw in ('45', '+45', '45.0', '90/2', ' 45\n'):
        assert policy.score(task, raw)['passed']
    for raw in ('', ' \n'):
        assert policy.score(task, raw)['category'] == 'missing_answer'


@pytest.mark.parametrize('raw', [
    '{"tool":"weather","arguments":{"city":"Oslo","unit":"C","extra":1}}',
    '{"tool":"weather","arguments":{"city":"Oslo","city":"Kyoto","unit":"C"}}',
    '{"tool":"weather","arguments":{"city":"Oslo"}}',
    '{"tool":"weather","arguments":{"city":"Oslo","unit":"K"}}',
    '{"tool":"search_documents","arguments":{"query":"lunar geology","limit":true}}',
    '{"tool":"convert","arguments":{"value":NaN,"from_unit":"km","to_unit":"m"}}',
    '{"tool":"delete_files","arguments":{}}',
    '{"tool":"weather","arguments":{"city":"Oslo","unit":"C"},"execute":true}',
])
def test_mock_tool_schema_strict_and_duplicate_keys(raw):
    assert not policy.score(policy.tasks()[16], raw)['passed']


def test_mock_tool_right_schema_wrong_tool_or_args():
    task = policy.tasks()[16]
    for document in (dict(tool='weather', arguments=dict(city='Kyoto', unit='C')),
                     dict(tool='set_timer', arguments=dict(seconds=120, label='tea'))):
        result = policy.score(task, json.dumps(document))
        assert not result['passed'] and result['schema_valid']
        assert result['category'] == 'wrong_tool_or_arguments' and result['mock_only']
    huge = dict(tool='convert', arguments=dict(value=10 ** 400, from_unit='km', to_unit='m'))
    assert policy.score(task, json.dumps(huge))['category'] == 'invalid_tool_schema'


@pytest.mark.parametrize('suffix', ['\n', ' ', '.', '\nExplanation'])
def test_concise_exact_constraints(suffix):
    for task in policy.tasks()[24:]:
        assert not policy.score(task, answer(task) + suffix)['passed']


@pytest.mark.parametrize('cap', [512, 1536])
def test_complete_paired_reduction_keeps_each_family(cap):
    rows = full_rows(cap)
    original = deepcopy(rows)
    report = reduce(rows, cap)
    assert rows == original
    assert report['expected_cells'] == report['recorded_cells'] == 64
    assert report['all_pairs_complete'] and report['all_cells_recorded']
    assert report['overall']['pairs']['counts']['both_pass'] == 32
    assert report['overall']['arms']['ON']['generation_metrics']['generated_tokens']['known_sum'] == 128
    assert report['overall']['arms']['ON']['generation_metrics']['content_tokens']['known_sum'] == 96
    for family in policy.FAMILIES:
        assert report['families'][family]['pairs']['denominator'] == 8
        assert report['families'][family]['pairs']['counts']['both_pass'] == 8
    assert report['thinking_metrics'] is None


def test_missing_rows_keep_denominators_and_unknown_tokens():
    report = reduce([])
    assert report['expected_cells'] == 64 and report['recorded_cells'] == 0
    assert not report['all_pairs_complete']
    assert report['overall']['pairs']['counts']['incomplete_pair'] == 32
    assert report['overall']['pairs']['counts']['both_fail'] == 0
    for arm in policy.ARMS:
        assert report['overall']['arms'][arm]['denominator'] == 32
        assert report['overall']['arms'][arm]['completion_counts']['missing'] == 32
        assert report['overall']['arms'][arm]['generation_metrics']['content_tokens']['unknown_count'] == 32


def test_truncation_retains_text_outcome_but_not_success_or_complete_pair():
    task = policy.tasks()[8]
    native = response(task)
    native.update(token_ids=[7] * 512, terminal=False, truncated=True)
    row = capture(task, native=native)
    assert row['result']['machine_outcome']['passed']
    assert not row['result']['passed'] and row['result']['completion'] == 'truncated'
    assert row['result']['generation_metrics']['content_tokens'] == 512
    report = reduce([row, capture(task, 'OFF')])
    assert report['overall']['arms']['ON']['completion_counts']['truncated'] == 1
    assert report['overall']['pairs']['complete'] == 0


def test_empty_answer_is_completed_machine_failure_not_missing_execution():
    task = policy.tasks()[8]
    native = response(task, '')
    native['token_ids'] = [99]
    row = capture(task, native=native)
    assert row['result']['completion'] == 'complete'
    assert row['result']['category'] == 'missing_answer'
    assert not row['result']['passed']
    assert row['result']['generation_metrics']['content_tokens'] == 0


def test_error_and_nonterminal_and_explicit_missing_separate():
    task = policy.tasks()[8]
    error = capture(task, native=dict(error=dict(type='load_error')))
    assert error['result']['completion'] == 'execution_error'
    partial = response(task)
    partial.update(token_ids=[7, 8], terminal=False)
    assert capture(task, native=partial)['result']['completion'] == 'incomplete'
    missing = policy.capture(task, 'ON', None, checkpoint_sha256=CHECKPOINT,
                            base_sha256=policy.BASE_SHA256, lora_enabled=True)
    assert missing['result']['completion'] == 'missing'
    assert reduce([missing])['all_cells_recorded'] is False


def test_error_preserves_known_partial_tokens_without_success():
    task = policy.tasks()[8]
    native = response(task)
    native.update(error=dict(type='native_failure'), token_ids=[7, 8], terminal=False)
    row = capture(task, native=native)
    assert row['result']['completion'] == 'execution_error'
    assert row['result']['generation_metrics']['generated_tokens'] == 2
    assert row['result']['generation_metrics']['content_tokens'] == 2
    assert row['result']['machine_outcome'] is None and not row['result']['passed']


def test_reducer_order_independent_and_missing_key_not_silently_defaulted():
    rows = full_rows()
    assert reduce(rows) == reduce(list(reversed(rows)))
    row = deepcopy(rows[0])
    del row['response']
    with pytest.raises(ValueError, match='outcome_drift'):
        reduce([row])


def test_discordant_pairs_do_not_absorb_missing_pairs():
    suite = policy.tasks()
    rows = [capture(suite[8], 'ON'), capture(suite[8], 'OFF', response(suite[8], '0')),
            capture(suite[9], 'ON', response(suite[9], '0')), capture(suite[9], 'OFF')]
    counts = reduce(rows)['overall']['pairs']['counts']
    assert counts == dict(both_pass=0, ON_only=1, OFF_only=1, both_fail=0, incomplete_pair=30)


@pytest.mark.parametrize('field,value', [('checkpoint_sha256', '2' * 64), ('base_sha256', '3' * 64),
    ('task_sha256', '4' * 64), ('suite_sha256', '5' * 64), ('prompt_sha256', '6' * 64),
    ('response_sha256', '7' * 64), ('family', 'toolcall'), ('thinking_metrics', {'novel': True})])
def test_reducer_rejects_identity_and_hash_and_heuristic_drift(field, value):
    row = capture(policy.tasks()[0])
    row[field] = value
    with pytest.raises(ValueError):
        reduce([row])


def test_reducer_recomputes_outcomes_and_rejects_boolean_numeric_tampering():
    for value in (False, 1):
        row = capture(policy.tasks()[0])
        row['result']['passed'] = value
        with pytest.raises(ValueError, match='outcome_drift'):
            reduce([row])


def test_duplicate_unknown_and_wrong_control_rejected():
    task = policy.tasks()[0]
    row = capture(task)
    with pytest.raises(ValueError, match='duplicate'):
        reduce([row, deepcopy(row)])
    for arm, enabled in [('OFF', True), ('ON', False), ('ON', 1)]:
        with pytest.raises(ValueError, match='control_mismatch'):
            policy.capture(task, arm, response(task), checkpoint_sha256=CHECKPOINT,
                           base_sha256=policy.BASE_SHA256, lora_enabled=enabled)
    for field, value in [('task_id', 'unknown'), ('arm', 'BASE')]:
        changed = deepcopy(row)
        changed[field] = value
        with pytest.raises(ValueError, match='unknown'):
            reduce([changed])


def test_budget_and_prompt_and_decode_must_match_within_pair():
    task = policy.tasks()[0]
    with pytest.raises(ValueError, match='budget_mismatch'):
        reduce([capture(task, native=response(task, cap=1536))])
    for field, value, message in [('prompt_tokens', 21, 'prompt_token'), ('context', 4096, 'decode_configuration')]:
        native = response(task)
        native[field] = value
        with pytest.raises(ValueError, match=message):
            reduce([capture(task), capture(task, 'OFF', native)])
    native = response(task)
    native['messages'][0]['content'] += ' Extra hint.'
    with pytest.raises(ValueError, match='exact_prompt'):
        capture(task, native=native)


@pytest.mark.parametrize('change', [dict(terminal=1), dict(terminal=True, truncated=True),
    dict(token_ids=[]), dict(prompt_tokens=0), dict(max_new_tokens=511), dict(context=21),
    dict(token_ids=[99, 7, 99]), dict(eos_token_id=100), dict(truncated=True, terminal=False),
    dict(token_ids=[7] * 512, terminal=False, truncated=False)])
def test_invalid_native_counts_and_flags_rejected(change):
    task = policy.tasks()[0]
    native = response(task)
    native.update(change)
    with pytest.raises(ValueError):
        capture(task, native=native)
