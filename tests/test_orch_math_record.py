import json
from pathlib import Path

import pytest

from organism_v6 import orch_math_record as policy
from organism_v6 import orch_math_rich as original


def test_roster_fresh_fixed():
    source = Path('gpu_artifacts_local/orch_math_rich_20260914_attempt1')
    records = [json.loads(line) for line in (source / 'gsm8k_train.jsonl').read_text().splitlines()]
    old = json.loads((source / 'TASKS.json').read_text())
    roster = policy.build_tasks(records, old)
    assert roster == policy.build_tasks(records, old)
    assert len(roster['tasks']) == 64
    assert not ({task['question_sha256'] for task in roster['tasks']} &
                {task['question_sha256'] for task in old['tasks']})
    assert all(set(task) == {'id', 'question', 'question_sha256', 'family', 'gold'} for task in roster['tasks'])


def test_exact_old_and_common_history():
    task = dict(question='Two bags each contain three apples. How many apples?', gold='6')
    previous = 'My common solution. FINAL: 6'
    old, student = policy.prompt(task, 'old_record', previous)
    assert (old, student) == original.prompt(task, 'record', previous)
    new, other_student = policy.prompt(task, 'new_record', previous)
    assert old[:-1] == new[:-1] and student == other_student
    assert new[-1]['content'] == policy.NEW_RECORD
    assert '150–400' in old[-1]['content'] and '150–400' in new[-1]['content']
    assert 'first-person' in old[-1]['content'] and 'first-person' in new[-1]['content']
    assert 'checker' not in student[-1]['content']
    assert '6' not in new[-1]['content']
    assert old[-1]['content'].startswith('The final value passed the exact-answer checker.')


def test_counterbalanced_within_shards():
    for shard in range(4):
        assert sum(policy.pair_order(position)[0] == 'old_record' for position in range(shard, 64, 4)) == 8


def test_missing_calls_keep_fixed_denominator(tmp_path):
    from gpu.orch_math_record_reduce import reduction
    source = Path('research_notes/analysis/orch_math_record_20260914_attempt1/TASKS.json')
    (tmp_path / 'TASKS.json').write_bytes(source.read_bytes())
    result, rows = reduction(tmp_path)
    assert result['denominator'] == 64 and result['skipped_record_pairs'] == 64
    assert not result['complete'] and not result['primary']['prospectively_successful']
    assert all(condition['admitted'] == 0 for condition in result['conditions'].values())
    assert rows == []


def test_prospective_success_and_grounding_protection():
    old = [False] * 64
    new = [True] * 8 + [False] * 56
    assert policy.paired_criterion(old, new, 40, 40, 2, 2, True)['prospectively_successful']
    assert not policy.paired_criterion(old, new, 40, 39, 2, 2, True)['prospectively_successful']
    assert not policy.paired_criterion(old, new, 40, 40, 2, 3, True)['prospectively_successful']
    assert not policy.paired_criterion(old, new, 40, 40, 2, 2, False)['prospectively_successful']
    assert policy.paired_criterion(old, old, 40, 40, 2, 2, True)['one_sided_exact_p'] == 1


@pytest.mark.parametrize('tokens,passes', [(149, False), (150, True), (400, True), (401, False)])
def test_unchanged_token_gate(tokens, passes):
    result = dict(raw='FINAL: 6', token_ids=[1] * tokens, terminal=False, truncated=False, prompt_tokens=2048)
    task = dict(id='task', family='group_accounting', gold='6')
    row = original.capture(task, 'new_record', result, [])
    assert row['token_contract_pass'] is passes
    assert not row['admitted']
