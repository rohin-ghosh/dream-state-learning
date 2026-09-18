import json
from pathlib import Path

import pytest

from gpu import orch_r108_code_parent_r110_continue as continuation


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    root = tmp_path / 'new'
    old = tmp_path / 'old'
    for directory in (root, old):
        (directory / continuation.run.LANE / 'cells').mkdir(parents=True)
        (directory / continuation.run.LANE / continuation.run.QUEUE).mkdir()
    monkeypatch.setattr(continuation, 'PREVIOUS', old)
    tasks = continuation.policy.tasks(continuation.ARM)
    task = tasks[0]
    schedule = continuation.policy.schedule(tasks, continuation.ARM)
    continuation.write(root / 'RESERVATIONS.json', schedule)
    continuation.write(root / 'INHERITED_CELLS.json', {})
    continuation.write(root / 'READY.json', {'test': True})
    continuation.write(root / 'LIFETIME.json', {'native_deadline_unix': 10**12})
    return root, old, task


def inherit(root, old, task, phase, status, response=None):
    reservation = next(row for row in continuation.read(root / 'RESERVATIONS.json')
        if row['task_id'] == task['task_id'] and row['phase'] == phase)
    record = dict(reservation, status=status, response=response)
    name = reservation['cell_id'] + '.json'
    old_path = old / continuation.run.LANE / 'cells' / name
    new_path = root / continuation.run.LANE / 'cells' / name
    continuation.write(old_path, record)
    new_path.write_bytes(old_path.read_bytes())
    manifest = continuation.read(root / 'INHERITED_CELLS.json')
    manifest[reservation['cell_id']] = dict(path=str(old_path), sha256=continuation.sha(old_path))
    continuation.write(root / 'INHERITED_CELLS.json', manifest)
    return record, old_path, new_path


def archive_result(root, request, status='FAILED'):
    directory = root / 'parent_transcripts' / continuation.run.LANE / 'TEST'
    directory.mkdir(parents=True)
    raw = directory / 'RAW_RESPONSE.json'
    raw.write_text('{"preserved": "malformed"')
    result = dict(status=status, request_sha256=continuation.sha(request), plan=None,
        archive=dict(remote_root=str(directory), all_verified=True, files={'RAW_RESPONSE.json': continuation.sha(raw)}))
    response = request.with_name(request.name.replace('.request.json', '.response.json'))
    continuation.write(response, result)
    return response


def test_inherited_complete_native_never_regenerates(prepared, monkeypatch):
    root, old, task = prepared
    expected, old_path, new_path = inherit(root, old, task, 'segment1', 'COMPLETE', {'raw': 'old', 'token_ids': [3]})
    monkeypatch.setattr(continuation, 'original_generate', lambda *args: pytest.fail('no repeated model call'))
    assert continuation.generate(root, None, task, 'segment1', [], lambda label: None) == expected
    assert old_path.read_bytes() == new_path.read_bytes()
    new_path.write_text('{}')
    with pytest.raises(ValueError, match='no_inherited_drift'):
        continuation.generate(root, None, task, 'segment1', [], lambda label: None)


def test_inherited_failed_parent_charged_not_retried(prepared, monkeypatch):
    root, old, task = prepared
    record, old_path, new_path = inherit(root, old, task, 'parent2', 'FAILED')
    request = old / continuation.run.LANE / continuation.run.QUEUE / 'GUIDED_SLEEP_C1_P1_S2.request.json'
    continuation.write(request, {'previous': 'request'})
    archive_result(old, request)
    monkeypatch.setattr(continuation.run, 'begin', lambda *args: pytest.fail('no repeated parent reservation'))
    result = continuation.parent(root, continuation.ARM, task, 2, [], '', [], lambda label: None)
    assert result['status'] == 'MISSING' and not result['intervention_available'] and result['lesson'] == ''
    assert result['inherited_charged_call'] and result['no_retry']
    assert old_path.read_bytes() == new_path.read_bytes() and continuation.read(new_path)['status'] == 'FAILED'
    assert not list((root / continuation.run.LANE / continuation.run.QUEUE).iterdir())


def test_archive_corruption_fails_closed(prepared):
    root, old, task = prepared
    request = root / 'request.request.json'
    continuation.write(request, {'bound': True})
    response = archive_result(root, request)
    result = continuation.read(response)
    result['archive']['files']['RAW_RESPONSE.json'] = 'wrong'
    continuation.write(response, result)
    with pytest.raises(ValueError, match='archive_hash'):
        continuation.verified_result(response, request, root)


def test_missing_intervention_reflects_without_invented_parent(prepared, monkeypatch):
    root, old, task = prepared
    captured = []
    monkeypatch.setattr(continuation, 'generate', lambda *args: captured.append(args[4]) or {'response': {'raw': 'own'}})
    continuation.reflection(root, None, task, 2, [{'response': {'raw': 'own code'}}],
        {'intervention_available': False, 'lesson': ''}, '', lambda label: None)
    payload = json.loads(captured[0][1]['content'])
    assert payload['intervention_available'] is False and 'actual_parent_message' not in payload


def test_missing_record_not_counted_as_parent_triple(prepared):
    root, old, task = prepared
    row = {'response': {'raw': 'own'}, 'outcome': {'passed': False}}
    continuation.save_triple(root, continuation.ARM, task, 2, row, {'intervention_available': False}, row, row)
    assert not list((root / continuation.run.LANE).glob('TRIPLE_*'))
    assert len(list((root / continuation.run.LANE).glob('MISSING_INTERVENTION_CONTINUATION_*'))) == 1


def test_future_provider_failure_continues_without_same_retry(prepared, monkeypatch):
    root, old, task = prepared
    original_write = continuation.write
    def responding_write(path, value):
        original_write(path, value)
        if path.name.endswith('.request.json'):
            archive_result(root, path)
    monkeypatch.setattr(continuation, 'write', responding_write)
    monkeypatch.setattr(continuation.policy, 'validate_parent_payload', lambda payload: payload)
    result = continuation.parent(root, continuation.ARM, task, 2, [], '', [], lambda label: None, payload={})
    assert result['status'] == 'MISSING' and result['no_retry']
    with pytest.raises(FileExistsError):
        continuation.parent(root, continuation.ARM, task, 2, [], '', [], lambda label: None, payload={})


def test_same_lifetime_total_caps_and_other_arm_rejected():
    config = continuation.policy.allocation(continuation.ARM)
    bound = continuation.run.lifetime(config, 1789689600)
    assert bound['started_unix'] == 1789462920 and bound['hard_deadline_unix'] == 1789491720
    assert bound['native_cap'] == 1500 and bound['parent_cap'] == 500
    with pytest.raises(ValueError, match='node3_only'):
        continuation.validate(Path('/unused'), 'a100_segment')


def test_next_scheduled_native_after_inheritance_dispatches_once(prepared, monkeypatch):
    root, old, task = prepared
    calls = []
    monkeypatch.setattr(continuation, 'original_generate', lambda *args: calls.append(args[3]) or {})
    continuation.generate(root, None, task, 'reflection2', [], lambda label: None)
    assert calls == ['reflection2']


def test_unusable_parent_then_own_reflection_then_next_scheduled_parent(prepared, monkeypatch):
    root, old, task = prepared
    inherit(root, old, task, 'parent2', 'FAILED')
    request = old / continuation.run.LANE / continuation.run.QUEUE / 'GUIDED_SLEEP_C1_P1_S2.request.json'
    continuation.write(request, {'charged': True})
    archive_result(old, request)
    event_order = []
    result = continuation.parent(root, continuation.ARM, task, 2, [], '', [], lambda label: None)
    monkeypatch.setattr(continuation, 'generate', lambda *args: event_order.append('own_reflection') or {})
    continuation.reflection(root, None, task, 2, [], result, '', lambda label: None)
    original_write = continuation.write
    def responding_write(path, value):
        original_write(path, value)
        if path.name.endswith('.request.json'):
            event_order.append(path.name)
            archive_result(root, path)
    monkeypatch.setattr(continuation, 'write', responding_write)
    monkeypatch.setattr(continuation.policy, 'validate_parent_payload', lambda payload: payload)
    next_task = next(row for row in continuation.policy.tasks(continuation.ARM) if row['cycle'] == 1 and row['slot'] == 2)
    result = continuation.parent(root, continuation.ARM, next_task, 2, [], '', [], lambda label: None, payload={})
    assert event_order == ['own_reflection', 'GUIDED_SLEEP_C1_P2_S2.request.json']
    assert result['status'] == 'MISSING'


def test_malformed_complete_plan_is_missing_not_salvaged(prepared, monkeypatch):
    root, old, task = prepared
    original_write = continuation.write
    def responding_write(path, value):
        original_write(path, value)
        if path.name.endswith('.request.json'):
            archive_result(root, path, status='COMPLETE')
    monkeypatch.setattr(continuation, 'write', responding_write)
    monkeypatch.setattr(continuation.policy, 'validate_parent_payload', lambda payload: payload)
    result = continuation.parent(root, continuation.ARM, task, 2, [], '', [], lambda label: None, payload={})
    assert result['missing_reason'] == 'UNUSABLE_PARSED_PLAN' and result['classification'] == 'UNCLASSIFIED'


def test_node3_scan_race_allows_rescan_not_clear():
    config = continuation.policy.allocation(continuation.ARM)
    snapshot = dict(clear=False, scanner_euid=0, gpu=dict(index=4, uuid=config['uuid'], memory_used_mib=1,
        utilization_percent=0), compute_processes=[], blocking_reasons=['process_identity_drift:31'])
    assert continuation.transient_scan(snapshot) and snapshot['clear'] is False
    snapshot['blocking_reasons'].append('open_device_pid:41')
    assert not continuation.transient_scan(snapshot)
    snapshot['blocking_reasons'] = ['minor_scan_identity_changed:31']
    snapshot['compute_processes'] = [{'gpu_uuid': config['uuid'], 'pid': 41}]
    assert not continuation.transient_scan(snapshot)
    snapshot['compute_processes'] = []
    snapshot['gpu']['memory_used_mib'] = 33
    assert not continuation.transient_scan(snapshot)
