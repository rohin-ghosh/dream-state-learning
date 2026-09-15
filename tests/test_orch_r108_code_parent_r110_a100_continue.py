import pytest

from gpu import orch_r108_code_parent_r110_a100_continue as a100


def test_exact_charged_counts_include_failed_parent():
    rows = [dict(kind='NATIVE', status='COMPLETE')] * 6 + [dict(kind='PARENT', status='COMPLETE')] * 2 + [dict(kind='PARENT', status='FAILED')]
    assert a100.inherited_counts(rows) == dict(consumed_native=6, consumed_parent=3, accepted_parent=2)
    rows.append(dict(kind='NATIVE', status='STARTED'))
    with pytest.raises(ValueError, match='no_partial_native'):
        a100.inherited_counts(rows)


def test_complete_parent_reuses_exact_archive_without_new_call(tmp_path, monkeypatch):
    task = dict(cycle=1, slot=1, task_id='existing')
    result = dict(status='COMPLETE', plan={'unchanged': True})
    record = dict(status='COMPLETE', kind='PARENT', result=result, lesson='Exact previous advice')
    monkeypatch.setattr(a100.continuation, 'inherited_cell', lambda *args: record)
    monkeypatch.setattr(a100.continuation, 'verified_result', lambda *args: (result, tmp_path))
    monkeypatch.setattr(a100.continuation, 'parent', lambda *args: pytest.fail('must not dispatch inherited accepted parent'))
    assert a100.parent(tmp_path, a100.ARM, task, 1, [], '', [], lambda label: None) is record
    record['result'] = {'status': 'FAILED'}
    with pytest.raises(ValueError, match='exact_previous_accepted_parent'):
        a100.parent(tmp_path, a100.ARM, task, 1, [], '', [], lambda label: None)


def test_failed_parent_delegates_missing_without_replacing_charge(tmp_path, monkeypatch):
    monkeypatch.setattr(a100.continuation, 'inherited_cell', lambda *args: {'status': 'FAILED'})
    monkeypatch.setattr(a100.continuation, 'parent', lambda *args: {'status': 'MISSING', 'no_retry': True})
    assert a100.parent(tmp_path, a100.ARM, {'slot': 2}, 1, [], '', [], lambda label: None)['no_retry']


def test_original_a100_caps_and_deadline():
    config = a100.policy.allocation(a100.ARM)
    value = a100.run.lifetime(config, 1790463900)
    assert value['native_cap'] == 1700 and value['parent_cap'] == 700
    assert value['started_unix'] == 1789462920 and value['hard_deadline_unix'] == 1789491720
