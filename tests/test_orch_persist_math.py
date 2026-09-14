import json

import pytest

from organism_v6 import orch_persist_math as math


def record_for(task, steps=2):
    offset = math.advance(task, 0, steps)
    return dict(steps=steps, multiplier=(math.advance(task, 1, steps) - offset) % task['modulus'], offset=offset)


def answer(task, records=None):
    return 'FINAL ' + json.dumps(dict(answer=math.advance(task, task['start'], task['steps']),
        records=[record_for(task)] if records is None else records))


def test_registry_and_many_distinct_instances():
    tasks = math.curriculum()
    assert len(tasks) == len({task['task_id'] for task in tasks}) == 128
    assert len({(task['block'], task['start'], task['steps']) for task in tasks}) == 128
    assert {task['family'] for task in tasks} == {math.FAMILIES['L1mining']}
    assert len(set(math.FAMILIES.values())) == 4
    assert len(math.curriculum(4)) == 16


@pytest.mark.parametrize('count', [True, 0, 33, -1])
def test_invalid_curriculum_size(count):
    with pytest.raises(ValueError):
        math.curriculum(count)


def test_record_is_checked_for_every_residue_not_just_task_start():
    task = math.curriculum(1)[0]
    record = record_for(task)
    assert math.check_record(task, record)['valid']
    wrong = dict(record, multiplier=(record['multiplier'] + 1) % task['modulus'],
        offset=(record['offset'] - task['start']) % task['modulus'])
    assert (wrong['multiplier'] * task['start'] + wrong['offset']) % task['modulus'] == math.advance(task, task['start'], 2)
    assert not math.check_record(task, wrong)['valid']


@pytest.mark.parametrize('record', [None, {}, {'steps': True, 'multiplier': 1, 'offset': 0},
    {'steps': 1000000, 'multiplier': 1, 'offset': 0}, {'steps': 2, 'multiplier': -1, 'offset': 0}])
def test_invalid_records_are_bounded(record):
    assert not math.check_record(math.curriculum(1)[0], record)['valid']


@pytest.mark.parametrize('raw', ['FINAL {"answer":1,"answer":2,"records":[]}',
    'FINAL {"answer":true,"records":[]}', 'FINAL {"answer":1,"records":[]}\ntrailer',
    'FINAL {}\nFINAL {}', 'FINAL {"answer":1,"records":[],"extra":1}',
    'Evidence FINAL {"answer":1,"records":[]}'])
def test_strict_projection_keeps_malformed_raw_rejected(raw):
    assert not math.judge(math.curriculum(1)[0], raw)['accepted']


def test_outcome_success_not_record_or_semantic_admission():
    task = math.curriculum(1)[0]
    verdict = math.judge(task, answer(task, []))
    assert verdict['outcome_success'] and not verdict['accepted']
    assert not math.judge(task, answer(task), terminal=False)['accepted']
    assert not math.judge(task, answer(task, [record_for(task, 1)]))['accepted']


def test_persistence_correction_and_failed_raw_preserved():
    tasks = {task['task_id']: task for task in math.curriculum(4)}
    failures = set()
    captured = {}

    def generate(messages, task_id, turn):
        task = tasks[task_id]
        if task_id not in failures:
            failures.add(task_id)
            return dict(raw='I mistakenly submit an unsupported claim.', terminal=True)
        assert messages[-2]['content'] == 'I mistakenly submit an unsupported claim.'
        assert 'Deterministic checker feedback' in messages[-1]['content']
        return dict(raw=answer(task), terminal=True)

    result = math.screen(generate, 'RICH', lambda name, value: captured.update({name: value}))
    assert result['model_calls'] == 32
    assert result['corrected'] == result['outcome_and_record'] == result['tasks'] == 16
    assert result['tasks_with_prior_records'] == 12
    assert result['admitted_targets'] == result['fits'] == result['updates'] == 0
    assert result['semantic_status'] == 'UNREVIEWED'
    for episode in result['episodes']:
        if episode['task']['task_id'].endswith('I00'):
            assert not episode['records_before']
        assert episode['turns'][0]['response']['raw'] == 'I mistakenly submit an unsupported claim.'
        assert all(record['source_task'] != episode['task']['task_id'] for record in episode['records_before'])


def test_no_failed_records_enter_store():
    def generate(messages, **metadata):
        return dict(raw='FINAL {"answer":-1,"records":[]}', terminal=True)

    result = math.screen(generate, 'TERSE')
    assert result['model_calls'] == 32
    assert result['outcome_and_record'] == result['tasks_with_prior_records'] == 0
    assert all(not episode['records_after'] for episode in result['episodes'])


def test_prompts_share_task_and_records_and_have_no_reference_answer():
    task = math.curriculum(1)[0]
    rich = math.initial_messages(task, [], 'RICH')
    terse = math.initial_messages(task, [], 'TERSE')
    assert rich[1] == terse[1]
    assert '150–400' in rich[0]['content']
    assert 'reference solution' not in rich[1]['content']
    assert 'FINAL {' not in rich[0]['content']


def test_reducer_replays_original_calls_and_rejects_tampering(tmp_path):
    from gpu import orch_persist_math_reduce as reducer

    tasks = {task['task_id']: task for task in math.curriculum(4)}
    directory = tmp_path / 'RICH'
    directory.mkdir()
    calls = []

    def generate(messages, **metadata):
        response = dict(raw=answer(tasks[metadata['task_id']]), terminal=True, truncated=False,
            messages=messages, prompt_tokens=100, token_ids=[1, 2, 3])
        calls.append(dict(call_index=len(calls), messages=messages, metadata=metadata,
            error=None, response=response, prose_tokens=0))
        return response

    data = math.screen(generate, 'RICH')
    result = dict(status='COMPLETE', fits=0, updates=0, admitted_targets=0, frozen_base_unchanged=True,
        adapter_state_after='fixture-state', loaded_adapter_state_sha256='fixture-state',
        model_calls=len(calls), started_unix=0, finished_unix=1,
        summary={key: value for key, value in data.items() if key != 'episodes'})
    for filename, document in [('DATA.json', data), ('RESULT.json', result)] + [
            (f'CALL_{index:03d}.json', capture) for index, capture in enumerate(calls)]:
        (directory / filename).write_text(json.dumps(document))
    reduced = reducer.reduce_arm(tmp_path, 'RICH')
    assert reduced['outcome_and_record'] == 16
    assert reduced['model_calls'] == 16
    assert reduced['admitted_targets'] == 0
    calls[0]['metadata']['task_id'] = 'tampered'
    (directory / 'CALL_000.json').write_text(json.dumps(calls[0]))
    with pytest.raises(ValueError, match='call_prefix_or_order_join_failed'):
        reducer.reduce_arm(tmp_path, 'RICH')
