import copy
import hashlib
import json
from pathlib import Path

import pytest

from gpu import orch_rich_intensity_guard as guard
from organism_v6 import orch_math_rich as original
from organism_v6 import orch_math_scale as scale
from organism_v6 import orch_rich_intensity as policy


ROSTER = Path('research_notes/analysis/orch_rich_intensity_20260915_attempt1/TASKS.json')


def test_exact_roster_source_and_exclusions():
    document = json.loads(ROSTER.read_text())
    policy.validate(document)
    assert hashlib.sha256(ROSTER.read_bytes()).hexdigest() == policy.TASKS_SHA
    provenance = json.loads(ROSTER.with_name('DATA_PROVENANCE.json').read_text())
    assert provenance['source_sha256'] == '17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465'
    assert provenance['tasks_sha256'] == policy.TASKS_SHA
    changed = copy.deepcopy(document)
    changed['excluded_ids'].append(changed['tasks'][0]['id'])
    with pytest.raises(AssertionError):
        policy.validate(changed)


def test_future_branch_guidance_is_explicit_and_not_in_control():
    for condition in ('light', 'dense'):
        guidance = policy.PROMPTS[condition]
        assert 'Before the FINAL line' in guidance or 'Before the FINAL' in guidance
        assert 'alternative you considered' in guidance
        assert 'made you reject it, when relevant' in guidance
        assert 'do not invent an alternative' in guidance
    assert policy.PROMPTS['control'] == original.RICH_GUIDANCE


def test_control_bytes_and_neutral_masks():
    task = json.loads(ROSTER.read_text())['tasks'][0]
    assert policy.prompt(task, 'control', 'rich') == original.prompt(task, 'rich')
    for condition in policy.CONDITIONS:
        guided, student = policy.prompt(task, condition, 'rich')
        assert student == [dict(role='user', content=task['question'])]
        assert guided[0]['content'] == policy.PROMPTS[condition]
        previous = 'Unedited prior child text.'
        assert policy.prompt(task, condition, 'new_record', previous) == scale.prompt(task, 'new_record', previous)
        _, record_student = policy.prompt(task, condition, 'new_record', previous)
        assert record_student[1]['content'] == previous
        assert all(message['role'] != 'system' for message in record_student)
        assert 'checker' not in json.dumps(record_student)


def test_budget_pairing_and_peer_exclusion():
    document = json.loads(ROSTER.read_text())
    for condition in policy.CONDITIONS:
        indices = [index for index in range(6) if policy.allocation(index)[0] == condition]
        selected = [task['id'] for index in indices for position, task in enumerate(document['tasks'])
                    if position % 2 == policy.allocation(index)[1]]
        assert len(selected) == len(set(selected)) == 256
    assert 2 * 256 * len(policy.CONDITIONS) == 1536
    assert 6 * 120 / 60 == 12
    assert set(guard.DEVICES) == set(range(6))
    for index in (6, 7, -1):
        with pytest.raises(ValueError):
            policy.allocation(index)


def test_scan_unknown_pid_is_not_free():
    snapshot = dict(gpu=dict(index=0, uuid=guard.DEVICES[0], memory_used_mib=1, utilization_percent=0),
        all_gpu_uuids=list(guard.DEVICES.values()), all_gpu_indices=list(map(str, range(8))),
        compute_processes=[], processes=[dict(pid=999, unreadable=True)])
    assert guard.existing.evaluate(snapshot, 0) == ['unknown_visibility:999']
    snapshot['processes'] = [dict(pid=998, cvd='6', target_device_open=False)]
    assert not guard.existing.evaluate(snapshot, 0)
    snapshot['processes'] = [dict(pid=997, cvd=guard.DEVICES[0])]
    assert guard.existing.evaluate(snapshot, 0) == ['reserved_cvd_pid:997']


@pytest.mark.parametrize('tokens,expected', [(149, False), (150, True), (400, True), (401, False)])
def test_unchanged_raw_target_budget(tokens, expected):
    task = json.loads(ROSTER.read_text())['tasks'][0]
    raw = 'Own raw text.\nFINAL: ' + task['gold']
    row = original.capture(task, 'rich', dict(raw=raw, token_ids=list(range(tokens)),
        terminal=False, truncated=False, prompt_tokens=2048), [])
    assert row['target'] == raw and row['token_contract_pass'] is expected
    assert not row['admitted']


def test_no_unread_target_admission():
    task = json.loads(ROSTER.read_text())['tasks'][0]
    row = original.capture(task, 'rich', dict(raw='FINAL: ' + task['gold'],
        token_ids=list(range(200)), terminal=False, truncated=False, prompt_tokens=100), [])
    with pytest.raises(ValueError):
        policy.admit(row, dict(student_prefix_sha256=original.digest([]), full_text_read=False), {'status': 'VALID'})


def test_raw85_heavy_budgets_and_source_not_automatic_target():
    task = json.loads(ROSTER.read_text())['tasks'][0]
    assert [policy.generation_cap(condition, 'rich') for condition in policy.CONDITIONS] == [512, 1536, 1536]
    assert all(policy.generation_cap(condition, 'new_record') == 512 for condition in policy.CONDITIONS)
    assert all('150–400' not in policy.PROMPTS[condition] for condition in ('light', 'dense'))
    for tokens, context, expected in ((200,4096,True),(200,4097,False),(401,100,False),(1536,100,False)):
        row = policy.capture(task, 'rich', dict(raw='FINAL: ' + task['gold'],
            token_ids=list(range(tokens)), terminal=False, truncated=False, prompt_tokens=context), [])
        assert row['candidate'] is expected
        assert not row['admitted']


def test_native_generation_caps_fail_before_model_access():
    from gpu.orch_rich_intensity_screen import Engine
    engine = object.__new__(Engine)
    for cap in (0, 513, 1537, True):
        with pytest.raises(ValueError, match='raw85_fixed_generation_caps'):
            engine.generate([], max_new_tokens=cap)
