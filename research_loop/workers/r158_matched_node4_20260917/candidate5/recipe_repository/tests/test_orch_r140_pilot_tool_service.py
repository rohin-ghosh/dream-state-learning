import io
import json
from pathlib import Path
import signal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r140_pilot_tool_service as service


START = 1699
ORIGINAL_RUN_REQUEST = service.cpu.run_request


def record(index, kind, document, previous, journal_id='a' * 32):
    value = dict(schema='R125_STREAM_JOURNAL_V1', index=index, kind=kind,
                 document=document, previous_sha256=previous, journal_id=journal_id)
    value['sha256'] = service.cpu.digest(value)
    return value


def chain(config, raw, index=START, *, split='TRAIN', terminal=True, truncated=False):
    request = record(index - 1, 'REQUEST', dict(split=split, resume_state={}), '0' * 64)
    response = record(index, 'RESPONSE', dict(request_sha256=service.cpu.digest(dict(split=split)),
        response=dict(raw=raw, terminal=terminal, truncated=truncated)), request['sha256'])
    committed = record(index + 1, 'COMMITTED',
                       dict(source_sha256=service.cpu.digest(response['document'])), response['sha256'])
    records = [request, response, committed]
    write_records(config, records)
    return records


def write_records(config, records):
    for value in records:
        path = Path(config['root']) / 'stream' / 'records' / f'{value["index"]:020d}.json'
        path.write_bytes(service.encoded(value))
        if value['index'] == config['start_index'] - 1:
            config['start_after_sha256'] = service.sha(path.read_bytes())


def rehash(records):
    for position, value in enumerate(records):
        if position:
            value['previous_sha256'] = records[position - 1]['sha256']
        value['sha256'] = service.cpu.digest({key: item for key, item in value.items() if key != 'sha256'})


@pytest.fixture
def config(tmp_path, monkeypatch):
    root = tmp_path / 'pilot'
    (root / 'stream' / 'records').mkdir(parents=True)
    (root / 'stream' / 'inbox').mkdir()
    (root / 'stream' / 'JOURNAL.json').write_bytes(service.encoded(
        dict(schema='R125_STREAM_JOURNAL_V1', journal_id='a' * 32)))
    gate = tmp_path / 'gate'
    gate.mkdir()
    monkeypatch.setattr(service.cpu, 'verify_gate', Mock(return_value={'fixture': 'CPU gate, no runtime'}))
    monkeypatch.setattr(service.cpu, 'run_request', Mock(side_effect=AssertionError('real runtime forbidden')))
    clock = SimpleNamespace(now=1000.0)

    def sleep(seconds):
        clock.now += seconds

    monkeypatch.setattr(service, 'time', SimpleNamespace(time=lambda: clock.now,
        monotonic=lambda: clock.now, sleep=sleep))
    value = dict(root=str(root), gate_root=str(gate), state=str(tmp_path / 'state'),
        spool=str(tmp_path / 'spool'), start_index=START, wall_seconds=300, poll_seconds=0.1,
        max_polls=10, max_inspections=10, max_calls=2,
        max_request_bytes=2 * 100000, max_output_bytes=2 * service.OUTPUT_RESERVATION)
    write_records(value, [record(START - 1, 'REQUEST', dict(split='TRAIN', resume_state={}), '0' * 64)])
    value.update(service.pins(root, gate, START))
    return value


def evidence(config, index=START):
    return Path(config['state']) / f'{index:020d}'


def document(path):
    return json.loads(path.read_bytes())


def publications(config):
    return [document(path) for path in sorted((Path(config['root']) / 'stream' / 'inbox').glob('*.json'))]


def fake_result(raw, config, proof):
    request = service.cpu.parse_request(raw)
    root = Path(config['spool']) / request['request_id']
    unit = 'orch-r125-cpu-' + service.sha(str(root).encode())[:16]
    return dict(schema='R125_CPU_EXPERIMENT_RESULT_V1', status='COMPLETE', returncode=0,
        stdout='actual result\n', stderr='', retained_bytes=14,
        request_id=request['request_id'], source_sha256=request['source_sha256'],
        raw_request_sha256=service.sha(raw), requested_origin=request['origin'], origin=proof['origin'],
        gate=service.cpu.verify_gate(config['gate_root']), source_closure_sha256=service.cpu.source_closure(),
        command=service.cpu.profile.command(root, unit), GPU_access=False, environment_injected=False,
        output_is_untrusted=True, cgroup_removed_after_stop=True, teardown_error=None)


def install_dispatch(monkeypatch, config, transform=None):
    def dispatch(raw, selected, destination, remaining):
        state = document(Path(config['state']) / 'STATE.json')
        assert state['phase'] == 'DISPATCH_INTENT'
        assert state['calls'] >= 1
        assert state['request_bytes'] >= len(raw)
        assert state['output_reserved'] >= service.OUTPUT_RESERVATION
        assert selected == config
        assert remaining >= service.DISPATCH_RESERVATION
        proof = document(destination / 'PROOF.json')
        result = fake_result(raw, selected, proof)
        if transform:
            transform(result)
        result_raw = json.dumps(result, indent=3, ensure_ascii=False).encode() + b'\n\n'
        service.store(destination / 'RESULT.json', result_raw)
        return result_raw

    mocked = Mock(side_effect=dispatch)
    monkeypatch.setattr(service, 'dispatch', mocked)
    return mocked


@pytest.mark.parametrize('source', ['print(2)\n', '  print("é")  \n\n', 'print("\\n")\r\n'])
def test_exact_source_and_result_bytes_publication(config, monkeypatch, source):
    raw = 'An explicit request.\n```python experiment\n' + source + '```\nPrediction only.'
    chain(config, raw)
    before = {path.name: path.read_bytes() for path in (Path(config['root']) / 'stream' / 'records').iterdir()}
    dispatch = install_dispatch(monkeypatch, config)
    original_publish = service.console.publish_tool

    def publish(root, path):
        intent = document(Path(config['state']) / 'STATE.json')
        assert intent['phase'] == 'PUBLISH_INTENT'
        assert intent['publication_sha256'] == service.sha(path.read_bytes())
        return original_publish(root, path)

    publisher = Mock(side_effect=publish)
    monkeypatch.setattr(service.console, 'publish_tool', publisher)
    service.run(config)
    dispatch.assert_called_once()
    publisher.assert_called_once_with(config['root'], evidence(config) / 'RESULT.json')
    assert (evidence(config) / 'source.py').read_bytes() == source.encode()
    assert document(evidence(config) / 'REQUEST.json')['source'] == source
    assert document(evidence(config) / 'RESPONSE.record.json')['document']['response']['raw'] == raw
    inbox = publications(config)
    assert len(inbox) == 1
    assert inbox[0]['actor'] == 'environment' and inbox[0]['speaker'] == 'Tool'
    assert inbox[0]['source_receipt'] == dict(path=str(evidence(config) / 'RESULT.json'),
                                            sha256=service.sha((evidence(config) / 'RESULT.json').read_bytes()))
    assert 'actual result' in inbox[0]['text']
    assert before == {path.name: path.read_bytes() for path in (Path(config['root']) / 'stream' / 'records').iterdir()}
    assert document(evidence(config) / 'PROOF.json')['provenance_valid'] is True


def test_R153_plain_first_block_receipt_preserves_normalization_and_journal(config, monkeypatch):
    config['code_policy'] = service.cpu.code_blocks.POLICY
    raw = '```python\nprint（“hello”）\n```\n```python\nprint(99)\n```'
    chain(config, raw)
    before = {path.name: path.read_bytes() for path in (Path(config['root']) / 'stream/records').iterdir()}
    dispatch = install_dispatch(monkeypatch, config)
    service.run(config)
    assert dispatch.call_count == 1
    proof = document(evidence(config) / 'PROOF.json')
    assert proof['origin']['code_transformation']['source_sha256'] == service.sha(b'print("hello")\n')
    assert document(evidence(config) / 'REQUEST.json')['source'] == 'print("hello")\n'
    assert len(publications(config)) == 1
    assert before == {path.name: path.read_bytes() for path in (Path(config['root']) / 'stream/records').iterdir()}


MALFORMED = [
    '```python experiment\nprint(2)\n',
    '```python experiment\npass\n```\n```python experiment\npass\n```',
    ' ```python experiment\npass\n```',
    '```python experiment \npass\n```',
    '~~~python experiment\npass\n~~~',
    '````python experiment\npass\n````',
    '```python experiment\r\npass\r\n```\r\n',
    '```python experiment\n```',
    '```python experiment\npass\n```extra\n```',
    '```python experiment\npass\n```\n~~~python experiment\npass\n~~~',
    '```python\npython experiment\nprint(2)\n```\n```text\n2\n```',
]


@pytest.mark.parametrize('raw', MALFORMED)
def test_malformed_fence_is_truthful_validation_only(config, monkeypatch, raw):
    chain(config, raw)
    dispatch = install_dispatch(monkeypatch, config)
    verifier = Mock(wraps=service.cpu.verify_origin)
    monkeypatch.setattr(service.cpu, 'verify_origin', verifier)
    service.run(config)
    dispatch.assert_not_called()
    verifier.assert_called_once()
    receipt = document(evidence(config) / 'REJECTED.json')
    assert receipt['schema'] == 'R140_EXPERIMENT_VALIDATION_V1'
    assert receipt['status'] == 'REJECTED' and receipt['validation_only'] and not receipt['executed']
    assert not {'stdout', 'stderr', 'returncode', 'source_sha256'} & receipt.keys()
    for reference in (*receipt['original_records'].values(), receipt['proof']):
        assert service.sha(Path(reference['path']).read_bytes()) == reference['sha256']
    assert len(publications(config)) == 1
    assert 'No experiment was executed' in publications(config)[0]['text']
    assert publications(config)[0]['source_receipt']['sha256'] == service.sha((evidence(config) / 'REJECTED.json').read_bytes())
    assert not (evidence(config) / 'source.py').exists()


@pytest.mark.parametrize('raw', ['print(2)', '```python\nprint(2)\n```',
    'I could run a python experiment.', '```text\nordinary example\n```',
    '```python  experiment\npass\n```', '```Python experiment\npass\n```',
    '````text\n```python experiment\npass\n```\n````',
    '```text python experiment\nprose\n```',
    '```python\nprint("python experiment")\n```',
    '```python\n# discussing an experiment\npython experiment\n```'])
def test_nonrequests_never_execute_or_publish(config, monkeypatch, raw):
    chain(config, raw)
    dispatch = install_dispatch(monkeypatch, config)
    service.run(config)
    dispatch.assert_not_called()
    assert publications(config) == []
    assert document(evidence(config) / 'PROOF.json')['disposition'] == 'NO_EXPLICIT_REQUEST'


@pytest.mark.parametrize('malformed', [False, True])
@pytest.mark.parametrize('fault', ['hash', 'chain', 'request_join', 'commit_join',
    'held', 'truncated', 'unterminated', 'journal_id', 'kind', 'index', 'schema'])
def test_bad_origin_never_bypassed_by_fence_failure(config, monkeypatch, malformed, fault):
    raw = MALFORMED[-1] if malformed else '```python experiment\npass\n```'
    records = chain(config, raw)
    if fault == 'held':
        records = chain(config, raw, split='HELD')
    elif fault == 'truncated':
        records = chain(config, raw, truncated=True)
    elif fault == 'unterminated':
        records = chain(config, raw, terminal=False)
    elif fault == 'hash':
        records[1]['sha256'] = 'b' * 64
    elif fault == 'chain':
        records[2]['previous_sha256'] = 'b' * 64
        records[2]['sha256'] = service.cpu.digest({key: value for key, value in records[2].items() if key != 'sha256'})
    elif fault in ('request_join', 'commit_join'):
        position, key = (1, 'request_sha256') if fault == 'request_join' else (2, 'source_sha256')
        records[position]['document'][key] = 'b' * 64
        rehash(records)
    elif fault == 'journal_id':
        for value in records[1:]:
            value['journal_id'] = 'b' * 32
        rehash(records)
    elif fault == 'kind':
        records[2]['kind'] = 'HELD'
        rehash(records)
    elif fault == 'schema':
        records[1]['schema'] = 'other'
        rehash(records)
    elif fault == 'index':
        records[1]['index'] = True
        rehash(records)
    if fault == 'index':
        path = Path(config['root']) / 'stream' / 'records' / f'{START:020d}.json'
        path.write_bytes(service.encoded(records[1]))
    else:
        write_records(config, records)
    dispatch = install_dispatch(monkeypatch, config)
    service.run(config)
    dispatch.assert_not_called()
    assert publications(config) == []
    proof = document(evidence(config) / 'PROOF.json')
    assert proof['disposition'] == 'INVALID_ORIGIN' and proof['provenance_valid'] is False
    assert not (evidence(config) / 'REJECTED.json').exists()


@pytest.mark.parametrize('error', [ValueError('other_origin_failure'), KeyError('unexpected_origin'), OSError('origin_io')])
def test_only_exact_fence_error_can_produce_validation_receipt(config, monkeypatch, error):
    chain(config, MALFORMED[-1])
    monkeypatch.setattr(service.cpu, 'verify_origin', Mock(side_effect=error))
    service.run(config)
    assert publications(config) == []
    assert document(evidence(config) / 'PROOF.json')['provenance_valid'] is False


def test_scans_only_pinned_root_from_explicit_index(config, monkeypatch):
    chain(config, '```python experiment\nprint("old")\n```', index=START)
    chain(config, '```python experiment\nprint("new")\n```', index=START + 3)
    config['start_index'] = START + 3
    prefix = Path(config['root']) / 'stream' / 'records' / f'{START + 2:020d}.json'
    config['start_after_sha256'] = service.sha(prefix.read_bytes())
    other = Path(config['root']).parent / 'other-root'
    other.mkdir()
    (other / 'secret.py').write_text('never inspected')
    dispatch = install_dispatch(monkeypatch, config)
    service.run(config)
    dispatch.assert_called_once()
    assert service.cpu.parse_request(dispatch.call_args.args[0])['source'] == 'print("new")\n'
    assert not evidence(config, START).exists()


@pytest.mark.parametrize('limit,value,reason', [
    ('max_calls', 1, 'CALL_LIMIT'), ('max_inspections', 1, 'INSPECTION_LIMIT'),
    ('max_polls', 1, 'POLL_LIMIT'), ('max_request_bytes', 1, 'REQUEST_BYTE_LIMIT'),
    ('max_output_bytes', 65535, 'OUTPUT_BUDGET_LIMIT'), ('wall_seconds', 74, 'WALL_RESERVE')])
def test_persisted_hard_caps(config, monkeypatch, limit, value, reason):
    chain(config, '```python experiment\npass\n```')
    chain(config, '```python experiment\npass\n```', index=START + 3)
    config[limit] = value
    dispatch = install_dispatch(monkeypatch, config)
    result = service.run(config)
    assert result['state']['reason'] == reason
    assert dispatch.call_count == (1 if limit in ('max_calls', 'max_inspections', 'max_polls') else 0)
    calls = dispatch.call_count
    assert service.run(config)['status'] == 'STOPPED_NO_REPLAY'
    assert dispatch.call_count == calls


def test_poll_budget_with_no_records(config):
    config['max_polls'] = 3
    result = service.run(config)
    assert result['state']['polls'] == 3 and result['state']['inspections'] == 0
    assert result['state']['reason'] == 'POLL_LIMIT'


def test_uncommitted_tail_waits_without_side_effect_intent(config, monkeypatch):
    records = chain(config, '```python experiment\npass\n```')
    commit = Path(config['root']) / 'stream' / 'records' / f'{START + 1:020d}.json'
    commit.unlink()
    config.update(max_calls=1, max_polls=4)
    dispatch = install_dispatch(monkeypatch, config)
    original_sleep = service.time.sleep

    def commit_after_poll(seconds):
        state = document(Path(config['state']) / 'STATE.json')
        assert state['phase'] == 'READY'
        assert state['next_index'] == state['pending_index'] == START
        assert state['polls'] == state['inspections'] == 1
        assert state['calls'] == 0 and state['request_bytes'] == state['output_reserved'] == 0
        assert not evidence(config).exists() and publications(config) == []
        write_records(config, [records[2]])
        original_sleep(seconds)

    monkeypatch.setattr(service.time, 'sleep', commit_after_poll)
    result = service.run(config)
    dispatch.assert_called_once()
    assert result['state']['calls'] == 1
    assert result['state']['polls'] == result['state']['inspections'] == 2
    assert len(publications(config)) == 1


def test_uncommitted_tail_exhausts_persistent_poll_budget(config, monkeypatch):
    records = chain(config, '```python experiment\npass\n```')
    (Path(config['root']) / 'stream' / 'records' / f'{START + 1:020d}.json').unlink()
    config['max_polls'] = 3
    dispatch = install_dispatch(monkeypatch, config)
    first = service.run(config)
    assert first['state']['reason'] == 'POLL_LIMIT'
    assert first['state']['next_index'] == START
    assert first['state']['polls'] == first['state']['inspections'] == 3
    write_records(config, [records[2]])
    assert service.run(config)['status'] == 'STOPPED_NO_REPLAY'
    dispatch.assert_not_called()
    assert publications(config) == []


def test_pending_tail_restart_keeps_budget_and_revisits(config, monkeypatch):
    records = chain(config, '```python experiment\npass\n```')
    (Path(config['root']) / 'stream' / 'records' / f'{START + 1:020d}.json').unlink()
    config['max_calls'] = 1
    dispatch = install_dispatch(monkeypatch, config)

    class Crash(BaseException):
        pass

    with monkeypatch.context() as patch:
        patch.setattr(service.time, 'sleep', Mock(side_effect=Crash()))
        with pytest.raises(Crash):
            service.run(config)
    before = document(Path(config['state']) / 'STATE.json')
    assert before['phase'] == 'READY'
    write_records(config, [records[2]])
    after = service.run(config)['state']
    assert after['polls'] == before['polls'] + 1
    assert after['inspections'] == before['inspections'] + 1
    assert after['deadline_unix'] == before['deadline_unix']
    dispatch.assert_called_once()


def test_pending_tail_invalid_commit_rejected(config, monkeypatch):
    records = chain(config, MALFORMED[-1])
    (Path(config['root']) / 'stream' / 'records' / f'{START + 1:020d}.json').unlink()
    original_sleep = service.time.sleep
    records[2]['sha256'] = 'b' * 64

    def invalid_commit(seconds):
        write_records(config, [records[2]])
        original_sleep(seconds)

    monkeypatch.setattr(service.time, 'sleep', invalid_commit)
    dispatch = install_dispatch(monkeypatch, config)
    service.run(config)
    dispatch.assert_not_called()
    assert publications(config) == []
    assert document(evidence(config) / 'PROOF.json')['disposition'] == 'INVALID_ORIGIN'


@pytest.mark.parametrize('index', [0, 1, 1695, 1698])
def test_main_owned_historical_probe_is_never_replayed(config, index):
    config['start_index'] = index
    with pytest.raises(ValueError, match='bounded_start_index'):
        service.run(config)
    assert not Path(config['state']).exists()


def test_wall_budget_includes_poll_sleep(config):
    config.update(wall_seconds=1, poll_seconds=10)
    result = service.run(config)
    assert result['state']['polls'] == 1
    assert result['state']['reason'] == 'WALL_LIMIT'


def test_hard_wall_interrupts_blocked_mock():
    with pytest.raises(service.WallExpired):
        with service.hard_wall(0.02):
            signal.pause()


@pytest.mark.parametrize('where', ['dispatch', 'result_saved', 'publish_before', 'publish_after'])
def test_uncertain_actions_never_replayed(config, monkeypatch, where):
    chain(config, '```python experiment\npass\n```')
    dispatch = install_dispatch(monkeypatch, config)
    dispatch_action = dispatch.side_effect
    original_publish = service.console.publish_tool

    def uncertain_dispatch(*args):
        if where == 'result_saved':
            dispatch_action(*args)
        raise RuntimeError('uncertain dispatch')

    def uncertain_publish(*args):
        if where == 'publish_after':
            original_publish(*args)
        raise RuntimeError('uncertain publication')

    if where in ('dispatch', 'result_saved'):
        dispatch.side_effect = uncertain_dispatch
    publisher = Mock(side_effect=uncertain_publish)
    monkeypatch.setattr(service.console, 'publish_tool', publisher)
    first = service.run(config)
    assert first['status'] == 'STOPPED_NO_REPLAY'
    phase = 'DISPATCH_INTENT' if where in ('dispatch', 'result_saved') else 'PUBLISH_INTENT'
    assert document(Path(config['state']) / 'STATE.json')['phase'] == phase
    assert service.run(config)['status'] == 'STOPPED_NO_REPLAY'
    dispatch.assert_called_once()
    assert publisher.call_count == (0 if phase == 'DISPATCH_INTENT' else 1)
    assert len(publications(config)) == (1 if where == 'publish_after' else 0)


def test_restart_ready_keeps_cursor_budget_and_deadline(config, monkeypatch):
    chain(config, '```python experiment\npass\n```')
    chain(config, '```python experiment\npass\n```', index=START + 3)
    dispatch = install_dispatch(monkeypatch, config)
    original_save = service.save_state

    class Crash(BaseException):
        pass

    def crash_after_ready(directory, state):
        original_save(directory, state)
        if state['phase'] == 'READY' and state['next_index'] == START + 1:
            raise Crash()

    with monkeypatch.context() as patch:
        patch.setattr(service, 'save_state', crash_after_ready)
        with pytest.raises(Crash):
            service.run(config)
    before = document(Path(config['state']) / 'STATE.json')
    assert before['calls'] == 1 and before['next_index'] == START + 1
    service.time.sleep(5)
    after = service.run(config)['state']
    assert after['calls'] == 2 and after['reason'] == 'CALL_LIMIT'
    assert after['deadline_unix'] == before['deadline_unix']
    assert dispatch.call_count == len(publications(config)) == 2


def test_existing_spool_and_changed_config_refused(config):
    spool = Path(config['spool'])
    spool.mkdir(mode=0o700)
    with pytest.raises(ValueError, match='new_spool'):
        service.run(config)
    spool.rmdir()
    service.run(config)
    config['max_calls'] += 1
    with pytest.raises(ValueError, match='namespace_config_changed'):
        service.run(config)


@pytest.mark.parametrize('field', ['source_closure_sha256', 'gate_sha256', 'journal_id',
                                  'journal_manifest_sha256', 'start_after_sha256'])
def test_fixed_pins_are_required_before_any_namespace(config, field):
    config[field] = 'f' * len(config[field])
    with pytest.raises(ValueError, match='pinned_gate_source_or_journal_changed'):
        service.run(config)
    assert not Path(config['state']).exists()


@pytest.mark.parametrize('field,value', [('max_calls', True), ('max_inspections', 0), ('max_polls', 10001),
    ('poll_seconds', float('nan')), ('poll_seconds', 0), ('wall_seconds', 3601), ('start_index', -1)])
def test_invalid_limits_rejected(config, field, value):
    config[field] = value
    with pytest.raises(ValueError, match='bounded_'):
        service.validate_config(config)


def test_path_alias_and_overlap_rejected(config):
    config['state'] = str(Path(config['root']) / 'state')
    with pytest.raises(ValueError, match='disjoint'):
        service.validate_config(config)
    config['state'] = str(Path(config['root']).parent / 'state')
    alias = Path(config['root']).parent / 'alias'
    alias.symlink_to(config['root'], target_is_directory=True)
    config['root'] = str(alias)
    with pytest.raises(ValueError, match='symlink_free'):
        service.validate_config(config)


@pytest.mark.parametrize('field,value', [('GPU_access', True), ('source_sha256', 'f' * 64),
    ('raw_request_sha256', 'f' * 64), ('gate', {}), ('source_closure_sha256', {}),
    ('status', 'DISPATCH_INCOMPLETE'), ('status', 'TEARDOWN_UNVERIFIED'),
    ('cgroup_removed_after_stop', False), ('retained_bytes', 65537), ('command', ['python'])])
def test_result_binding_and_uncertainty_prevent_publication(config, monkeypatch, field, value):
    chain(config, '```python experiment\npass\n```')
    dispatch = install_dispatch(monkeypatch, config, lambda result: result.update({field: value}))
    assert service.run(config)['status'] == 'STOPPED_NO_REPLAY'
    assert publications(config) == []
    assert (evidence(config) / 'RESULT.json').exists()
    service.run(config)
    dispatch.assert_called_once()


def test_dispatch_worker_reuses_runner_and_preserves_exact_result(config, monkeypatch, tmp_path):
    records = chain(config, '```python experiment\npass\n```')
    request = service.encoded(service.make_request('pass\n', dict(kind='TRAIN_CHILD_RESPONSE',
        record_index=START, record_sha256=records[1]['sha256'])))
    destination = tmp_path / 'worker'
    destination.mkdir(mode=0o700)
    request_id = service.cpu.parse_request(request)['request_id']
    result_root = Path(config['spool']) / request_id
    result_root.mkdir(parents=True)
    result_raw = b'{ "status" : "fixture" }\n\n'
    (result_root / 'RESULT.json').write_bytes(result_raw)
    runner = Mock(return_value=json.loads(result_raw))
    monkeypatch.setattr(service.cpu, 'run_request', runner)
    monkeypatch.setattr(service.signal, 'signal', Mock())
    service.dispatch_worker(request, config, destination)
    runner.assert_called_once_with(request, Path(config['spool']), Path(config['gate_root']), Path(config['root']))
    assert (destination / 'RESULT.json').read_bytes() == result_raw


def test_overdue_worker_is_not_retried_or_published(config, monkeypatch, tmp_path):
    worker = Mock()
    worker.is_alive.side_effect = [True, True, False, False]
    context = Mock()
    context.Process.return_value = worker
    monkeypatch.setattr(service.multiprocessing, 'get_context', Mock(return_value=context))
    with pytest.raises(ValueError, match='uncertain_dispatch'):
        service.dispatch(b'fixture', config, tmp_path, 2)
    worker.start.assert_called_once()
    worker.terminate.assert_called_once()
    worker.join.assert_any_call(1)
    assert publications(config) == []


def test_check_cli_is_read_only(config, tmp_path, capsys):
    path = tmp_path / 'config.json'
    path.write_bytes(service.encoded(config))
    assert service.main(['check', '--config', str(path)]) == 0
    assert json.loads(capsys.readouterr().out)['gate_sha256'] == config['gate_sha256']
    assert not Path(config['state']).exists() and not Path(config['spool']).exists()
    assert publications(config) == []


def test_full_runner_and_real_console_with_mocked_runtime_only(config, monkeypatch):
    source = 'print("exact source é")  \n'
    chain(config, '```python experiment\n' + source + '```\n')
    config['max_calls'] = 1
    captured_closure = service.cpu.source_closure()
    monkeypatch.setattr(service.cpu, 'run_request', ORIGINAL_RUN_REQUEST)
    monkeypatch.setattr(service.cpu, 'source_closure', lambda: captured_closure)
    preflight = Mock(return_value=SimpleNamespace(returncode=1, stdout='LoadState=not-found\n'))
    monkeypatch.setattr(service.cpu.subprocess, 'run', preflight)
    process = Mock(stdout=io.BytesIO(), stderr=io.BytesIO())
    process.wait.return_value = 0
    launch = Mock(return_value=process)
    monkeypatch.setattr(service.cpu.subprocess, 'Popen', launch)
    monkeypatch.setattr(service.cpu, 'stop_owned', Mock())
    monkeypatch.setattr(service.cpu, 'capture', Mock(return_value=dict(stdout=b'real fixture\n', stderr=b'',
        retained_bytes=13, observed_bytes=13, returncode=0, limit_reason=None, teardown_error=None)))

    def inline_dispatch(raw, selected, destination, remaining):
        assert document(Path(config['state']) / 'STATE.json')['phase'] == 'DISPATCH_INTENT'
        with monkeypatch.context() as patch:
            patch.setattr(service.signal, 'signal', Mock())
            service.dispatch_worker(raw, selected, destination)
        return (destination / 'RESULT.json').read_bytes()

    monkeypatch.setattr(service, 'dispatch', inline_dispatch)
    result = service.run(config)
    assert result['state']['reason'] == 'CALL_LIMIT'
    preflight.assert_called_once()
    launch.assert_called_once()
    request = document(evidence(config) / 'REQUEST.json')
    dispatched = Path(config['spool']) / request['request_id']
    assert (dispatched / 'payload.py').read_bytes() == source.encode('utf-8')
    assert (dispatched / 'REQUEST.json').read_bytes() == (evidence(config) / 'REQUEST.json').read_bytes()
    assert (dispatched / 'RESULT.json').read_bytes() == (evidence(config) / 'RESULT.json').read_bytes()
    assert 'real fixture' in publications(config)[0]['text']


def test_result_arriving_after_wall_is_preserved_not_published(config, monkeypatch):
    chain(config, '```python experiment\npass\n```')
    dispatch = install_dispatch(monkeypatch, config)
    original_dispatch = dispatch.side_effect

    def late_result(*args):
        raw = original_dispatch(*args)
        service.time.sleep(config['wall_seconds'] + 1)
        return raw

    dispatch.side_effect = late_result
    assert service.run(config)['status'] == 'STOPPED_NO_REPLAY'
    assert (evidence(config) / 'RESULT.json').exists()
    assert publications(config) == []
    service.run(config)
    dispatch.assert_called_once()


def test_pending_response_change_stops_without_execution(config, monkeypatch):
    records = chain(config, '```python experiment\npass\n```')
    (Path(config['root']) / 'stream' / 'records' / f'{START + 1:020d}.json').unlink()
    original_sleep = service.time.sleep

    def change_response(seconds):
        records[1]['document']['response']['raw'] = '```python experiment\nprint("changed")\n```'
        rehash(records)
        write_records(config, records)
        original_sleep(seconds)

    monkeypatch.setattr(service.time, 'sleep', change_response)
    dispatch = install_dispatch(monkeypatch, config)
    result = service.run(config)
    assert result['status'] == 'STOPPED_NO_REPLAY' and result['error'] == 'pending_response_changed'
    dispatch.assert_not_called()
    assert publications(config) == []


def test_wall_clock_rollback_cannot_reset_restart_budget(config, monkeypatch):
    class Crash(BaseException):
        pass

    with monkeypatch.context() as patch:
        patch.setattr(service.time, 'sleep', Mock(side_effect=Crash()))
        with pytest.raises(Crash):
            service.run(config)
    saved = document(Path(config['state']) / 'STATE.json')
    service.time.sleep(config['wall_seconds'] + 1)
    monkeypatch.setattr(service.time, 'time', lambda: 0)
    result = service.run(config)
    assert result['state']['reason'] == 'WALL_LIMIT'
    assert result['state']['deadline_monotonic'] == saved['deadline_monotonic']
