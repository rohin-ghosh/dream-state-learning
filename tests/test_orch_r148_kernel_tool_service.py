"""Synthetic TRAIN journals, real bridge/locks/console, mocked GPU boundaries."""

from dataclasses import replace
import datetime
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r148_kernel_tool_service as service


START = 834


def document(path):
    return service.cpu.read_document(Path(path).read_bytes())


def make_record(index, kind, body, previous, journal_id='a' * 32):
    value = dict(schema='R125_STREAM_JOURNAL_V1', index=index, kind=kind, document=body,
                 previous_sha256=previous, journal_id=journal_id)
    value['sha256'] = service.cpu.digest(value)
    return value


def write_records(config, records):
    for value in records:
        path = Path(config['root']) / 'stream/records' / f'{value["index"]:020d}.json'
        path.write_bytes(service.encoded(value))


def chain(config, source=None, *, raw=None, index=START, split='TRAIN', terminal=True, truncated=False):
    if raw is None:
        raw = '```python experiment\n' + (source or service.executor.EXAMPLE_SOURCE) + '```\n'
    request = make_record(index - 1, 'REQUEST', dict(split=split, resume_state={}), '0' * 64)
    response = make_record(index, 'RESPONSE', dict(request_sha256=service.cpu.digest(dict(split=split)),
        response=dict(raw=raw, terminal=terminal, truncated=truncated)), request['sha256'])
    committed = make_record(index + 1, 'COMMITTED',
        dict(source_sha256=service.cpu.digest(response['document'])), response['sha256'])
    write_records(config, [request, response, committed])
    config.update(service.pin_config(config))
    return [request, response, committed]


def rehash(records):
    for position, value in enumerate(records):
        if position:
            value['previous_sha256'] = records[position - 1]['sha256']
        value['sha256'] = service.cpu.digest({key: item for key, item in value.items() if key != 'sha256'})


def publications(config):
    return [document(path) for path in sorted((Path(config['root']) / 'stream/inbox').glob('*.json'))]


def evidence(config):
    state = document(Path(config['state']) / 'STATE.json')
    return Path(config['state']) / f'{state.get("pending_index", config["start_index"]):020d}'


@pytest.fixture
def rig(tmp_path, monkeypatch):
    clock = SimpleNamespace(now=1000.0)
    clock.time = lambda: clock.now
    clock.monotonic = lambda: clock.now
    clock.sleep = lambda seconds: setattr(clock, 'now', clock.now + seconds)
    monkeypatch.setattr(service, 'time', clock)
    monkeypatch.setattr(service.executor, 'time', clock)
    monkeypatch.setattr(service.executor, 'LOCK_PATH', tmp_path / 'GPU.lock')
    monkeypatch.setattr(service.subprocess, 'Popen', Mock(side_effect=AssertionError('GPU subprocess forbidden')))
    root = tmp_path / 'child'
    (root / 'stream/records').mkdir(parents=True)
    (root / 'stream/inbox').mkdir()
    (root / 'stream/JOURNAL.json').write_bytes(service.encoded(
        dict(schema='R125_STREAM_JOURNAL_V1', journal_id='a' * 32)))
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    (runtime / 'file').write_bytes(b'fixture')
    manifest = dict(schema='R132_RUNTIME_MANIFEST_V1', files={'file': service.sha(b'fixture')})
    (runtime / 'MANIFEST.json').write_bytes(service.encoded(manifest))
    runtime_hash = service.sha(service.encoded(manifest))
    monkeypatch.setattr(service.executor, 'validate_runtime', Mock(return_value=runtime_hash))
    devices = dict(gpu_uuid=service.executor.GPU_UUID, physical_index=2,
                   nodes={'/dev/nvidia1': [195, 1]})
    identity = dict(devices=devices, runtime_manifest_sha256=runtime_hash, test_only=True)
    monkeypatch.setattr(service.executor, 'device_identity', Mock(return_value=devices))
    monkeypatch.setattr(service.executor, 'policy_identity', Mock(return_value=identity))
    census = Mock(return_value=b'<fixture>empty assigned GPU, not a live census</fixture>')
    monkeypatch.setattr(service, 'census', census)
    gate_dir = tmp_path / 'gate'
    gate_dir.mkdir()
    checks = {}
    for name in service.executor.GATE_CHECKS:
        path = gate_dir / (name + '.json')
        receipt = dict(identity=identity, passed=True, checks={name: True})
        path.write_bytes(service.encoded(receipt))
        checks[name] = dict(passed=True, receipt_path=str(path), receipt_sha256=service.sha(path.read_bytes()))
    gate = dict(schema='R132_GPU_CONFINEMENT_GATE_V1', identity=identity, passed=True,
                observed_unix=clock.now, expires_unix=clock.now + 3600, checks=checks)
    gate_path = gate_dir / 'GATE.json'
    gate_path.write_bytes(service.encoded(gate))
    lease_path = tmp_path / 'LEASE.json'
    lease_path.write_bytes(service.encoded(dict(conservative_lease_end_utc=
        datetime.datetime.fromtimestamp(100000, datetime.timezone.utc).isoformat(), margin_seconds=21600)))
    config = dict(root=str(root), state=str(tmp_path / 'state'), spool=str(tmp_path / 'spool'),
        source_root=str(Path(service.__file__).resolve().parents[1]), runtime_root=str(runtime),
        gate_path=str(gate_path), lease_receipt_path=str(lease_path), start_index=START,
        gpu_uuid=service.executor.GPU_UUID, device_minor=1, executor_lock=str(service.executor.LOCK_PATH),
        main_authorized=True, exclusive_gpu_custody=True, wall_seconds=600, poll_seconds=0.1,
        max_polls=8, max_calls=1, max_reads=10000, max_read_bytes=100 * 1024**3,
        max_request_bytes=100000, max_output_bytes=service.OUTPUT_RESERVATION,
        max_runtime_files=100, max_runtime_bytes=1048576)
    write_records(config, [make_record(START - 1, 'REQUEST', dict(split='TRAIN', resume_state={}), '0' * 64)])
    config = service.pin_config(config)

    def gpu(raw, *, spool, runtime_root, gate_path, admission_path, origin_verifier):
        request = service.executor.parse_request(raw)
        admitted = document(admission_path)
        assert admitted['request_id'] == request['request_id']
        assert admitted['source_sha256'] == request['source_sha256']
        assert admitted['origin'] == request['origin']
        assert document(evidence(config) / 'DISPATCH_PUBLICATION_INTENT.json')['phase'] == 'DISPATCH_PUBLICATION_INTENT'
        with pytest.raises(BlockingIOError):
            with service.lock_file(service.executor.LOCK_PATH):
                pass
        service.executor.validate_runtime(runtime_root)
        service.executor.validate_gate(gate_path, identity, clock.now)
        service.executor.validate_admission(admission_path, clock.now)
        result = dict(schema='R132_KERNEL_RESULT_V1', status='CORRECT', launch_attempted=True,
            cgroup_removed=True, capture={'returncode': 0}, origin=origin_verifier(request),
            request_id=request['request_id'], source_sha256=request['source_sha256'],
            measurement=dict(status='CORRECT', cases={str(size): dict(correct=True,
                reference_ms=1.0, candidate_ms=0.5, reported_speedup=2.0) for size in service.executor.LENGTHS}))
        destination = Path(spool) / request['request_id']
        destination.mkdir()
        (destination / 'REQUEST.json').write_bytes(raw)
        (destination / 'RESULT.json').write_bytes(service.encoded(result))
        clock.now += 1
        return result

    action = Mock(side_effect=gpu)
    monkeypatch.setattr(service.executor, '_run_request', action)
    return SimpleNamespace(config=config, clock=clock, action=action, census=census,
                           gate=gate, identity=identity, tmp=tmp_path)


def test_exact_accepted_uses_unchanged_bridge_real_lock_console_and_source(rig):
    chain(rig.config)
    result = service.run(rig.config)
    assert result['state']['reason'] == 'CALL_LIMIT'
    assert rig.action.call_count == rig.census.call_count == 1
    receipt = document(evidence(rig.config) / 'BRIDGE_RECEIPT.json')
    messages = publications(rig.config)
    assert len(messages) == 1
    assert messages[0]['id'] == receipt['delivery']['id']
    assert messages[0]['speaker'] == 'Tool'
    assert 'reported_speedup=2.0' in messages[0]['text']
    assert messages[0]['source_receipt']['path'] == receipt['result_path']
    assert (evidence(rig.config) / 'source.py').read_text() == service.executor.EXAMPLE_SOURCE
    assert document(rig.config['executor_lock'])['result_status'] == 'CORRECT'


def test_exact_invalid_AST_keeps_bridge_rejection_receipt(rig):
    chain(rig.config, source='import os\n')
    service.run(rig.config)
    rig.action.assert_not_called()
    assert rig.census.call_count == 1
    receipt = document(evidence(rig.config) / 'BRIDGE_RECEIPT.json')
    result = document(receipt['result_path'])
    assert result['status'] == 'REQUEST_REJECTED' and result['launch_attempted'] is False
    assert document(Path(receipt['result_path']).parent / 'REQUEST.json')['source'] == 'import os\n'
    assert 'REQUEST_REJECTED' in publications(rig.config)[0]['text']


def test_R153_plain_first_block_survives_origin_admission_dispatch_and_publication(rig):
    rig.config['code_policy'] = service.cpu.code_blocks.POLICY
    raw = '```python\n' + service.executor.EXAMPLE_SOURCE + '```\n```python\nraise Exception()\n```'
    chain(rig.config, raw=raw)
    service.run(rig.config)
    assert rig.action.call_count == 1
    receipt = document(evidence(rig.config) / 'BRIDGE_RECEIPT.json')
    result = document(receipt['result_path'])
    assert result['origin']['code_transformation']['policy'] == service.cpu.code_blocks.POLICY
    assert document(Path(receipt['result_path']).parent / 'REQUEST.json')['source'] == service.executor.EXAMPLE_SOURCE
    assert len(publications(rig.config)) == 1


@pytest.mark.parametrize('raw', ['Please describe the interface.', 'print(1)',
    '```python\nprint(1)\n```\n', '```pythonexperiment\nprint(1)\n```\n',
    '```python experiment\r\nprint(1)\r\n```\r\n',
    '```python experiment\nprint(1)\n```\n```python experiment\nprint(2)\n```\n',
    '````text\n```python experiment\nprint(1)\n```\n````\n'])
def test_no_prose_plain_malformed_multiple_or_nested_dispatch_or_feedback(rig, raw):
    chain(rig.config, raw=raw)
    service.run(rig.config)
    rig.action.assert_not_called()
    rig.census.assert_not_called()
    assert publications(rig.config) == []


def test_RESPONSE_before_COMMITTED_revisited_without_intent(rig):
    records = chain(rig.config)
    commit_path = Path(rig.config['root']) / 'stream/records' / f'{START + 1:020d}.json'
    commit_path.unlink()

    def append_commit(seconds):
        state = document(Path(rig.config['state']) / 'STATE.json')
        assert state['phase'] == 'READY' and state['next_index'] == START and state['calls'] == 0
        assert state['pending_response_sha256'] == service.sha(service.encoded(records[1]))
        assert not evidence(rig.config).exists()
        assert not Path(rig.config['executor_lock']).exists()
        rig.clock.now += seconds
        write_records(rig.config, [records[2]])

    rig.clock.sleep = append_commit
    result = service.run(rig.config)
    assert result['state']['calls'] == 1 and rig.action.call_count == 1


def test_restart_pending_tail_continues_without_skipping_or_resetting_budgets(rig):
    records = chain(rig.config)
    (Path(rig.config['root']) / 'stream/records' / f'{START + 1:020d}.json').unlink()
    rig.clock.sleep = Mock(side_effect=KeyboardInterrupt)
    with pytest.raises(KeyboardInterrupt):
        service.run(rig.config)
    before = document(Path(rig.config['state']) / 'STATE.json')
    write_records(rig.config, [records[2]])
    result = service.run(rig.config)
    assert rig.action.call_count == 1
    assert result['state']['polls'] > before['polls']
    assert result['state']['deadline_unix'] == before['deadline_unix']


@pytest.mark.parametrize('when', ['before_dispatch', 'after_GPU', 'after_publication'])
def test_uncertain_dispatch_or_publication_never_replayed(rig, monkeypatch, when):
    chain(rig.config)
    if when == 'before_dispatch':
        monkeypatch.setattr(service.bridge, 'dispatch', Mock(side_effect=RuntimeError('uncertain')))
    elif when == 'after_GPU':
        monkeypatch.setattr(service.bridge, 'publish_result', Mock(side_effect=RuntimeError('uncertain')))
    else:
        original = service.bridge.publish_result

        def publish_then_fail(*args):
            original(*args)
            raise RuntimeError('uncertain')

        monkeypatch.setattr(service.bridge, 'publish_result', publish_then_fail)
    first = service.run(rig.config)
    calls, messages = rig.action.call_count, len(publications(rig.config))
    assert first['state']['phase'] == 'DISPATCH_PUBLICATION_INTENT'
    assert service.run(rig.config)['status'] == 'STOPPED_NO_REPLAY'
    assert rig.action.call_count == calls and len(publications(rig.config)) == messages
    assert messages == (1 if when == 'after_publication' else 0)


def test_successful_restart_does_not_duplicate_publication(rig):
    chain(rig.config)
    service.run(rig.config)
    service.run(rig.config)
    assert rig.action.call_count == 1 and len(publications(rig.config)) == 1


@pytest.mark.parametrize('failure', ['response_hash', 'response_join', 'commit_hash', 'commit_join',
    'chain', 'journal_id', 'split', 'prefix', 'manifest'])
def test_journal_failures_never_dispatch(rig, failure):
    records = chain(rig.config)
    if failure == 'response_hash':
        records[1]['sha256'] = 'b' * 64
    elif failure == 'response_join':
        records[1]['document']['request_sha256'] = 'b' * 64
        rehash(records)
    elif failure == 'commit_hash':
        records[2]['sha256'] = 'b' * 64
    elif failure == 'commit_join':
        records[2]['document']['source_sha256'] = 'b' * 64
        rehash(records)
    elif failure == 'chain':
        records[1]['previous_sha256'] = 'b' * 64
        records[1]['sha256'] = service.cpu.digest({key: value for key, value in records[1].items() if key != 'sha256'})
    elif failure == 'journal_id':
        records[2]['journal_id'] = 'b' * 32
        rehash(records)
    elif failure == 'split':
        records = chain(rig.config, split='HELD')
    elif failure == 'prefix':
        records[0]['document']['extra'] = 1
        rehash(records)
    else:
        (Path(rig.config['root']) / 'stream/JOURNAL.json').write_bytes(b'{}')
    write_records(rig.config, records)
    result = service.run(rig.config)
    assert result['status'] == 'STOPPED_NO_REPLAY'
    rig.action.assert_not_called()
    rig.census.assert_not_called()
    assert not publications(rig.config)


@pytest.mark.parametrize('failure', ['gate_expired', 'gate_hash', 'gate_check', 'gate_identity',
    'lease_hash', 'lease_wall', 'runtime_hash', 'census_busy', 'UUID', 'old_census', 'source'])
def test_gate_census_lease_and_source_fail_closed(rig, monkeypatch, failure):
    chain(rig.config)
    if failure == 'gate_expired':
        rig.clock.now = rig.gate['expires_unix']
    elif failure == 'gate_hash':
        Path(rig.config['gate_path']).write_bytes(b'{}')
    elif failure == 'gate_check':
        Path(next(iter(rig.gate['checks'].values()))['receipt_path']).write_bytes(b'{}')
    elif failure == 'gate_identity':
        monkeypatch.setattr(service.executor, 'policy_identity', Mock(return_value={}))
    elif failure == 'lease_hash':
        Path(rig.config['lease_receipt_path']).write_bytes(b'{}')
    elif failure == 'lease_wall':
        path = Path(rig.config['lease_receipt_path'])
        lease = document(path)
        lease['conservative_lease_end_utc'] = datetime.datetime.fromtimestamp(
            rig.clock.now + 21601, datetime.timezone.utc).isoformat()
        path.write_bytes(service.encoded(lease))
        rig.config.update(service.pin_config(rig.config))
    elif failure == 'runtime_hash':
        monkeypatch.setattr(service.executor, 'validate_runtime', Mock(return_value='0' * 64))
    elif failure == 'census_busy':
        rig.census.side_effect = ValueError('reserved_GPU_not_empty')
    elif failure == 'UUID':
        service.executor.device_identity.side_effect = ValueError('assigned_uuid_index_mismatch')
    elif failure == 'old_census':
        def slow_census():
            rig.clock.now += 31
            return b'fixture'
        rig.census.side_effect = slow_census
    else:
        rig.config['source_closure'][str(Path(service.bridge.__file__).resolve())] = '0' * 64
    result = service.run(rig.config)
    assert result['status'] == 'STOPPED_NO_REPLAY'
    rig.action.assert_not_called()
    assert publications(rig.config) == []


def test_repeated_runtime_validation_cannot_age_admission_past_sixty_seconds(rig):
    chain(rig.config)
    count = 0
    original_hash = rig.config['runtime_manifest_sha256']

    def slow_runtime(root):
        nonlocal count
        count += 1
        if count == 2:
            rig.clock.now += 61
        return original_hash

    service.executor.validate_runtime.side_effect = slow_runtime
    result = service.run(rig.config)
    assert 'fresh_admission' in result['error']
    assert result['state']['phase'] == 'DISPATCH_PUBLICATION_INTENT'
    assert publications(rig.config) == []


def test_admission_expiry_is_capped_by_gate_and_service_deadline(rig):
    chain(rig.config)
    rig.gate['expires_unix'] = rig.clock.now + 200
    Path(rig.config['gate_path']).write_bytes(service.encoded(rig.gate))
    rig.config.update(service.pin_config(rig.config))
    service.run(rig.config)
    admitted = document(evidence(rig.config) / 'ADMISSION.json')
    assert admitted['expires_unix'] == rig.gate['expires_unix']
    assert admitted['hard_wall_unix'] == 1000 + rig.config['wall_seconds']


@pytest.mark.parametrize('field,value,reason', [
    ('wall_seconds', 180, 'WALL_RESERVE'), ('max_polls', 1, 'POLL_LIMIT'),
    ('max_reads', 1, 'READ_LIMIT'), ('max_read_bytes', 1, 'READ_BYTE_LIMIT'),
    ('max_request_bytes', 1, 'REQUEST_BYTE_LIMIT'), ('max_output_bytes', 1, 'OUTPUT_BUDGET_LIMIT'),
    ('max_runtime_bytes', 1, 'runtime_byte_budget')])
def test_finite_limits(rig, field, value, reason):
    rig.config[field] = value
    chain(rig.config, raw='Only prose.' if field == 'max_polls' else None)
    result = service.run(rig.config)
    assert reason in result['error']
    rig.action.assert_not_called()


def test_hard_wall_interrupt_retains_intent(rig, monkeypatch):
    chain(rig.config)
    monkeypatch.setattr(service.bridge, 'dispatch', Mock(side_effect=service.common.WallExpired))
    result = service.run(rig.config)
    assert result['status'] == 'WALL_LIMIT_NO_REPLAY'
    assert result['state']['phase'] == 'DISPATCH_PUBLICATION_INTENT'
    assert service.run(rig.config)['status'] == 'STOPPED_NO_REPLAY'


@pytest.mark.parametrize('status', ['ADMISSION_IN_PROGRESS', 'TEARDOWN_UNVERIFIED', 'DISPATCH_FAILED_NO_RETRY'])
def test_orphan_executor_lock_requires_Main_reconciliation(rig, status):
    chain(rig.config)
    path = Path(rig.config['executor_lock'])
    path.write_bytes(service.encoded(dict(last_finished_unix=900, result_status=status)))
    path.chmod(0o600)
    result = service.run(rig.config)
    assert 'orphan_executor_intent' in result['error']
    rig.action.assert_not_called()
    rig.census.assert_not_called()


def test_another_owner_between_census_and_executor_lock_is_rejected(rig, monkeypatch):
    chain(rig.config)
    original = service.bridge.dispatch

    def other_owner(*args, **kwargs):
        path = Path(rig.config['executor_lock'])
        path.write_bytes(service.encoded(dict(last_finished_unix=rig.clock.now + 1, result_status='CORRECT')))
        return original(*args, **kwargs)

    monkeypatch.setattr(service.bridge, 'dispatch', other_owner)
    result = service.run(rig.config)
    assert 'new_Main_census' in result['error']
    rig.action.assert_not_called()


def test_generic_positive_start_uses_exact_manually_selected_predecessor(rig):
    rig.config['start_index'] = 2
    chain(rig.config, index=2)
    result = service.run(rig.config)
    assert result['state']['calls'] == 1
    assert document(Path(rig.config['state']) / 'PREDECESSOR.record.json')['index'] == 1


@pytest.mark.parametrize('field,value', [('wall_seconds', 1801), ('poll_seconds', float('nan')),
    ('main_authorized', False), ('exclusive_gpu_custody', False), ('device_minor', 2),
    ('start_index', 0), ('max_calls', True), ('gpu_uuid', 'GPU-other')])
def test_invalid_config_is_not_authority(rig, field, value):
    rig.config[field] = value
    with pytest.raises(ValueError):
        service.run(rig.config)
    rig.action.assert_not_called()


def test_symlink_record_refused(rig):
    chain(rig.config)
    path = Path(rig.config['root']) / 'stream/records' / f'{START:020d}.json'
    target = rig.tmp / 'substitute.json'
    path.rename(target)
    path.symlink_to(target)
    assert service.run(rig.config)['status'] == 'STOPPED_NO_REPLAY'
    rig.action.assert_not_called()


def test_check_cli_is_read_only_and_does_not_obtain_census(rig, capsys):
    path = rig.tmp / 'CONFIG.json'
    path.write_bytes(service.encoded(rig.config))
    assert service.main(['check', '--config', str(path)]) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'STATIC_PINS_CHECKED_NOT_ADMITTED'
    assert not Path(rig.config['state']).exists()
    assert not Path(rig.config['spool']).exists()
    rig.action.assert_not_called()
    rig.census.assert_not_called()


def test_real_stream_journal_with_active_writer_is_not_blocked(rig):
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r124_train_history import TrainHistory
    from organism_v6.orch_r125_continual_stream import ContinualStream

    root = rig.tmp / 'real_child'
    root.mkdir()
    with StreamJournal(root / 'stream', create=True) as journal:
        stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=2,
            deadline_unix=2000, model_state_sha256='f' * 64)
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        config = {key: value for key, value in rig.config.items() if key in service.BASE_KEYS}
        config.update(root=str(root), start_index=1)
        rig.config.clear()
        rig.config.update(service.pin_config(config))
        source = '```python experiment\n' + service.executor.EXAMPLE_SOURCE + '```\n'
        stream.step(lambda *args, **kwargs: dict(raw=source, token_ids=[10, 2], terminal=True, truncated=False),
            lambda messages: sum(len(message['content'].split()) + 4 for message in messages),
            journal.record, now=lambda: 1000)
        service.run(rig.config)
        assert rig.action.call_count == 1
        assert len(publications(rig.config)) == 1
        assert journal.latest_checkpoint() is not None


@pytest.mark.parametrize('terminal,truncated', [(False, False), (False, True), (True, True)])
def test_incomplete_generation_is_skipped_not_dispatched(rig, terminal, truncated):
    chain(rig.config, terminal=terminal, truncated=truncated)
    result = service.run(rig.config)
    assert result['state']['reason'] == 'POLL_LIMIT'
    assert result['state']['last_disposition'] == 'INCOMPLETE_GENERATION_NO_EXECUTION'
    rig.action.assert_not_called()
    rig.census.assert_not_called()
    assert publications(rig.config) == []


def test_real_inbox_truncated_sleep_updates_compaction_then_exact(rig, monkeypatch):
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r124_train_history import TrainHistory
    from organism_v6.orch_r125_continual_stream import ContinualStream

    root = rig.tmp / 'lifecycle_child'
    root.mkdir()
    with StreamJournal(root / 'stream', create=True) as journal:
        stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=1,
            deadline_unix=2000, model_state_sha256='f' * 64)
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        config = {key: value for key, value in rig.config.items() if key in service.BASE_KEYS}
        config.update(root=str(root), start_index=1, max_polls=100)
        rig.config.clear()
        rig.config.update(service.pin_config(config))
        journal.record('LOADED', dict(runtime='fixture', readout_path='/DO_NOT_OPEN_HELD'))
        service.console.publish_parent(root, 'Rohin', 'Synthetic TRAIN-only feedback.')
        incoming = journal.read_inbox()
        source = '```python experiment\n' + service.executor.EXAMPLE_SOURCE + '```\n'
        counter = lambda messages: sum(len(message['content'].split()) + 4 for message in messages)
        stream.step(lambda *args, **kwargs: dict(raw=source, token_ids=[10] * 128, terminal=False, truncated=True),
                    counter, journal.record, incoming=incoming, now=lambda: 1000)
        summary = replace(stream.history.events[-2], event_id='compaction:1', phase='compaction')
        stream.history.compact(summary, through=stream.history.frontier())
        journal.record('COMPACTION', dict(state=stream.checkpoint()))
        pending = stream.checkpoint()
        pending['state']['pending'] = 'sleep:' + service.cpu.digest([row['source_sha256'] for row in stream.pending_rows()])
        pending['sha256'] = service.cpu.digest(pending['state'])
        journal.record('SLEEP_REQUEST', dict(cycle=1, resume_state=pending))
        for kind in ('UPDATE', 'CHECKPOINT', 'TARGET_ELIGIBILITY', 'COMPACTION_SKIPPED',
                     'CHECKPOINT_METADATA'):
            journal.record(kind, dict(cycle=1, path='/DO_NOT_OPEN_HELD', state=stream.checkpoint()))
        receipt = dict(status='COMPLETE', optimizer_steps=1, cycle=1,
                       new_row_sha256=[row['source_sha256'] for row in stream.pending_rows()],
                       checkpoint_sha256={'adapter': 'a' * 64, 'optimizer': 'b' * 64, 'rng': 'c' * 64})
        stream.commit_sleep(receipt, journal.record)
        stream.step(lambda *args, **kwargs: dict(raw=source, token_ids=[10, 2], terminal=True, truncated=False),
                    counter, journal.record, now=lambda: 1000)
        original_read = service.read

        def checked_read(path, limit):
            assert 'DO_NOT_OPEN' not in str(path)
            return original_read(path, limit)

        monkeypatch.setattr(service, 'read', checked_read)
        result = service.run(rig.config)
        assert result['state']['calls'] == 1
        assert rig.action.call_count == rig.census.call_count == 1
        assert len(publications(rig.config)) == 2
        assert result['state']['reason'] == 'CALL_LIMIT'
        assert journal.latest_checkpoint() is not None
        skipped = list(Path(rig.config['state']).glob('NO_EXECUTION_*.json'))
        assert len(skipped) == 1
        assert document(skipped[0])['disposition'] == 'INCOMPLETE_GENERATION_NO_EXECUTION'


@pytest.mark.parametrize('body,reason', [
    ('<gpu><uuid>OTHER</uuid><processes/></gpu>', 'census_UUID_mismatch'),
    ('<gpu><uuid>{uuid}</uuid><processes><process_info><pid>42</pid></process_info></processes></gpu>',
     'reserved_GPU_not_empty'),
    ('<gpu><uuid>{uuid}</uuid><processes>N/A</processes></gpu>', 'census_process_visibility_required'),
    ('<gpu><uuid>{uuid}</uuid></gpu>', 'census_process_visibility_required'),
    ('<gpu><uuid>{uuid}</uuid><processes/></gpu>', None),
    ('x' * 70000, 'bounded_census_failed')])
def test_fixed_census_command_real_bounded_CPU_capture(monkeypatch, body, reason):
    original = subprocess.Popen
    raw = ('<nvidia_smi_log>' + body.format(uuid=service.executor.GPU_UUID) + '</nvidia_smi_log>').encode()

    def fixture_process(command, **kwargs):
        assert command == ['/usr/bin/nvidia-smi', '--id=' + service.executor.GPU_UUID, '-q', '-x']
        assert 'shell' not in kwargs
        return original([sys.executable, '-c', 'import sys; sys.stdout.buffer.write(' + repr(raw) + ')'], **kwargs)

    monkeypatch.setattr(service.subprocess, 'Popen', fixture_process)
    if reason:
        with pytest.raises(ValueError, match=reason):
            service.census()
    else:
        assert service.census() == raw


def test_two_requests_get_distinct_fresh_admissions_and_stop_at_call_budget(rig):
    rig.config.update(max_calls=2, max_output_bytes=2 * service.OUTPUT_RESERVATION, max_request_bytes=200000)

    def runtime_time(root):
        rig.clock.now += 0.1
        return rig.config['runtime_manifest_sha256']

    service.executor.validate_runtime.side_effect = runtime_time
    first = chain(rig.config)
    second = chain(rig.config, index=START + 3)
    second[0]['previous_sha256'] = first[-1]['sha256']
    rehash(second)
    write_records(rig.config, second)
    result = service.run(rig.config)
    assert result['state']['reason'] == 'CALL_LIMIT'
    assert rig.action.call_count == rig.census.call_count == 2
    admissions = [document(path) for path in sorted(Path(rig.config['state']).glob('*/ADMISSION.json'))]
    assert len(admissions) == 2
    assert admissions[1]['observed_unix'] > admissions[0]['observed_unix']
    assert admissions[0]['request_id'] != admissions[1]['request_id']
    assert len(publications(rig.config)) == 2


def test_pending_response_change_after_restart_stops_without_dispatch(rig):
    records = chain(rig.config)
    (Path(rig.config['root']) / 'stream/records' / f'{START + 1:020d}.json').unlink()
    rig.clock.sleep = Mock(side_effect=KeyboardInterrupt)
    with pytest.raises(KeyboardInterrupt):
        service.run(rig.config)
    records[1]['document']['response']['raw'] += '\nChanged.'
    rehash(records)
    write_records(rig.config, records)
    result = service.run(rig.config)
    assert result['error'] == 'pending_response_changed'
    rig.action.assert_not_called()


def test_hash_valid_source_change_during_census_rejected(rig):
    records = chain(rig.config)

    def changing_census():
        records[1]['document']['response']['raw'] = '```python experiment\nimport os\n```\n'
        rehash(records)
        records[2]['document']['source_sha256'] = service.cpu.digest(records[1]['document'])
        rehash(records)
        write_records(rig.config, records)
        return b'fixture'

    rig.census.side_effect = changing_census
    result = service.run(rig.config)
    assert result['error'] == 'source_changed_before_admission'
    rig.action.assert_not_called()


def test_expiring_gate_during_runtime_preparation_stops_before_census(rig):
    chain(rig.config)
    rig.gate['expires_unix'] = rig.clock.now + 200
    Path(rig.config['gate_path']).write_bytes(service.encoded(rig.gate))
    rig.config.update(service.pin_config(rig.config))

    def delay(root):
        rig.clock.now += 51
        return rig.config['runtime_manifest_sha256']

    service.executor.validate_runtime.side_effect = delay
    result = service.run(rig.config)
    assert result['error'] == 'fresh_gate_required'
    rig.action.assert_not_called()
    rig.census.assert_not_called()
