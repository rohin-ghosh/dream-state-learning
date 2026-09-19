import hashlib
import io
import json
from pathlib import Path
import subprocess

import pytest

from gpu import orch_r125_cpu_experiment as runner
from organism_v6.orch_r125_experiment_request import make_request


def record(index, kind, document, previous):
    result = dict(schema='R125_STREAM_JOURNAL_V1', journal_id='a' * 32,
        index=index, kind=kind, document=document, previous_sha256=previous)
    result['sha256'] = runner.digest(result)
    return result


def child_request(tmp_path, *, split='TRAIN', kind='RESPONSE', terminal=True, extra_block=False):
    directory = tmp_path / 'stream' / 'records'
    directory.mkdir(parents=True)
    source = 'print(1 + 1)\n'
    opening = record(0, 'REQUEST', {'split': split, 'resume_state': {}}, '0' * 64)
    response_document = dict(request_sha256=runner.digest({'split': split}), response=dict(
        raw='```python experiment\n' + source + '```\n' + ('```python experiment\npass\n```' if extra_block else ''),
        terminal=terminal, truncated=not terminal))
    response = record(1, kind, response_document, opening['sha256'])
    commit = record(2, 'COMMITTED', {'source_sha256': runner.digest(response_document)}, response['sha256'])
    for item in (opening, response, commit):
        (directory / f'{item["index"]:020d}.json').write_text(json.dumps(item))
    request = make_request(source, dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256=response['sha256']))
    return request


def test_explicit_committed_child_code_is_bound(tmp_path):
    request = child_request(tmp_path)
    result = runner.verify_origin(request, tmp_path)
    assert result['child_generated'] is True
    assert result['record_sha256'] == request['origin']['record_sha256']


@pytest.mark.parametrize('split', ['DEV', 'FINAL', 'HELD'])
def test_held_never_enters_experiment(tmp_path, split):
    request = child_request(tmp_path, split=split)
    with pytest.raises(ValueError, match='TRAIN_request'):
        runner.verify_origin(request, tmp_path)


@pytest.mark.parametrize('kwargs', [{'kind': 'REQUEST'}, {'terminal': False}, {'extra_block': True}])
def test_unqualified_response_rejected(tmp_path, kwargs):
    request = child_request(tmp_path, **kwargs)
    with pytest.raises(ValueError):
        runner.verify_origin(request, tmp_path)


def test_source_substitution_rejected(tmp_path):
    request = child_request(tmp_path)
    substitute = make_request('print(99)\n', request['origin'])
    with pytest.raises(ValueError, match='explicit_experiment'):
        runner.verify_origin(substitute, tmp_path)


def test_uncommitted_child_response_rejected(tmp_path):
    request = child_request(tmp_path)
    (tmp_path / 'stream' / 'records' / '00000000000000000002.json').unlink()
    with pytest.raises(FileNotFoundError):
        runner.verify_origin(request, tmp_path)


def test_builder_fixture_never_claims_child_generated(tmp_path):
    request = make_request('print(1)', dict(kind='BUILDER_TEST', record_index=0, record_sha256='0' * 64))
    assert runner.verify_origin(request, None) == {'kind': 'BUILDER_TEST', 'child_generated': False}
    with pytest.raises(ValueError):
        runner.verify_origin(request, tmp_path)


def test_regular_read_rejects_symlinks_and_oversize(tmp_path):
    path = tmp_path / 'input'
    path.write_bytes(b'abcd')
    with pytest.raises(ValueError):
        runner.read_regular(path, 3)
    link = tmp_path / 'link'
    link.symlink_to(path)
    with pytest.raises(OSError):
        runner.read_regular(link, 9)


def gates(root):
    for mode in ('basic', 'files', 'output', 'timeout', 'memory'):
        checks = runner.BASIC_CHECKS if mode == 'basic' else {'file_size_limit', 'scratch_limit'}
        value = dict(schema=runner.profile.SCHEMA, mode=mode, passed=True,
            source_sha256=hashlib.sha256(Path(runner.profile.__file__).read_bytes()).hexdigest(),
            capture_source_sha256=hashlib.sha256(Path(__import__('gpu.orch_r125_bounded_capture', fromlist=['']).__file__).read_bytes()).hexdigest(),
            boot_id_sha256=runner.profile.boot_identity(), cgroup_removed_after_stop=True, verified_limits=True,
            command=runner.profile.command(root / mode, 'orch-r125-cpu-test'),
            host_observation={'cgroup_files': {'cpu.max': '25000 100000', 'memory.max': '134217728',
                'memory.swap.max': '0', 'pids.max': '8'}, 'bpf': [{'attach_type': 'cgroup_device'}]},
            payload_result={'passed': True, 'checks': {key: True for key in checks}},
            unit_outcome={'Result': 'oom-kill'}, capture={'limit_reason': 'OUTPUT_LIMIT' if mode == 'output' else 'TIMEOUT',
                'teardown_error': None})
        (root / (mode + '.json')).write_text(json.dumps(value))


def test_complete_build_boot_bound_gates_pass(tmp_path):
    gates(tmp_path)
    assert len(runner.verify_gate(tmp_path)) == 5


@pytest.mark.parametrize('field,value', [('passed', False), ('source_sha256', '0' * 64),
    ('boot_id_sha256', '0' * 64), ('cgroup_removed_after_stop', False), ('verified_limits', False),
    ('payload_result', {'passed': True, 'checks': {}})])
def test_malformed_or_stale_gate_rejected(tmp_path, field, value):
    gates(tmp_path)
    path = tmp_path / 'basic.json'
    receipt = json.loads(path.read_text())
    receipt[field] = value
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        runner.verify_gate(tmp_path)


def test_refuse_to_stop_other_job(monkeypatch, tmp_path):
    calls = []

    def run(arguments, **kwargs):
        calls.append(arguments)
        return subprocess.CompletedProcess(arguments, 0, 'LoadState=loaded\nRootDirectory=/unrelated\n', '')

    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises(ValueError, match='unowned'):
        runner.stop_owned('orch-r125-cpu-test', tmp_path)
    assert len(calls) == 1


@pytest.mark.parametrize('raw', [b'{"passed":false,"passed":true}',
    b'{"outer":{"key":0,"key":1}}', b'{"index":NaN}', b'{"index":1e999}', b'[]'])
def test_ambiguous_or_nonfinite_evidence_rejected(raw):
    with pytest.raises(ValueError):
        runner.read_document(raw)


def test_symlink_gate_directory_rejected(tmp_path):
    actual = tmp_path / 'actual'
    actual.mkdir()
    gates(actual)
    link = tmp_path / 'link'
    link.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ValueError, match='gate_path_symlinks'):
        runner.verify_gate(link)


def test_boolean_journal_index_rejected_even_with_rebound_chain(tmp_path):
    request = child_request(tmp_path)
    directory = tmp_path / 'stream' / 'records'
    path = directory / '00000000000000000001.json'
    response = json.loads(path.read_text())
    response['index'] = True
    response['sha256'] = runner.digest({key: value for key, value in response.items() if key != 'sha256'})
    path.write_text(json.dumps(response))
    request = make_request(request['source'], dict(request['origin'], record_sha256=response['sha256']))
    with pytest.raises(ValueError, match='journal_record_hash'):
        runner.verify_origin(request, tmp_path)


def fake_dispatch(monkeypatch):
    calls = []
    process = subprocess.CompletedProcess([], 0)
    process.stdout = io.BytesIO()
    process.stderr = io.BytesIO()
    process.wait = lambda **kwargs: 0
    process.kill = lambda: calls.append('kill-client')
    monkeypatch.setattr(runner, 'verify_gate', lambda root: {})

    def run(arguments, **kwargs):
        calls.append('preflight')
        return subprocess.CompletedProcess(arguments, 1, 'LoadState=not-found\n', '')

    def popen(*args, **kwargs):
        calls.append('launch')
        return process

    def capture(*args, **kwargs):
        return dict(stdout=b'285\n', stderr=b'', returncode=0, limit_reason=None, teardown_error=None)

    monkeypatch.setattr(runner.subprocess, 'run', run)
    monkeypatch.setattr(runner.subprocess, 'Popen', popen)
    monkeypatch.setattr(runner, 'capture', capture)
    monkeypatch.setattr(runner, 'stop_owned', lambda *args: calls.append('stop'))
    monkeypatch.setattr(runner, 'source_closure', lambda: {'dispatcher': 'f' * 64})
    request = make_request('print(285)\n', dict(kind='BUILDER_TEST', record_index=0, record_sha256='0' * 64))
    return request, process, calls


def test_success_receipt_exact_payload_and_no_replay(monkeypatch, tmp_path):
    request, process, calls = fake_dispatch(monkeypatch)
    raw = json.dumps(request).encode()
    result = runner.run_request(raw, tmp_path, tmp_path)
    root = tmp_path / request['request_id']
    assert result['status'] == 'COMPLETE'
    assert result['origin']['child_generated'] is False
    assert result['requested_origin'] == request['origin']
    assert result['raw_request_sha256'] == hashlib.sha256(raw).hexdigest()
    assert (root / 'payload.py').read_bytes() == request['source'].encode('utf-8')
    assert json.loads((root / 'RESULT.json').read_bytes()) == result
    assert process.stdout.closed and process.stderr.closed
    with pytest.raises(FileExistsError):
        runner.run_request(raw, tmp_path, tmp_path)
    assert calls == ['preflight', 'launch', 'stop']


@pytest.mark.parametrize('returncode,stdout', [(0, 'LoadState=loaded\n'),
    (2, 'LoadState=not-found\n'), (0, 'prefixLoadState=not-found\n')])
def test_failed_preflight_never_launches_or_stops_existing_unit(monkeypatch, tmp_path, returncode, stdout):
    request, process, calls = fake_dispatch(monkeypatch)
    monkeypatch.setattr(runner.subprocess, 'run', lambda *args, **kwargs:
        subprocess.CompletedProcess([], returncode, stdout, ''))
    result = runner.run_request(json.dumps(request).encode(), tmp_path, tmp_path)
    assert result['status'] == 'DISPATCH_FAILED_NO_RETRY'
    assert result['launch_attempted'] is False
    assert calls == []


def test_capture_failure_stops_owned_job_and_persists_no_retry(monkeypatch, tmp_path):
    request, process, calls = fake_dispatch(monkeypatch)

    def failed(*args, **kwargs):
        raise OSError('synthetic capture failure')

    monkeypatch.setattr(runner, 'capture', failed)
    result = runner.run_request(json.dumps(request).encode(), tmp_path, tmp_path)
    assert result['status'] == 'DISPATCH_FAILED_NO_RETRY'
    assert calls == ['preflight', 'launch', 'stop']
    assert process.stdout.closed and process.stderr.closed
    assert (tmp_path / request['request_id'] / 'RESULT.json').is_file()


def test_client_timeout_kills_only_owned_client_and_never_claims_success(monkeypatch, tmp_path):
    request, process, calls = fake_dispatch(monkeypatch)
    waits = []

    def wait(**kwargs):
        waits.append(1)
        if len(waits) == 1:
            raise subprocess.TimeoutExpired('owned-client', 5)
        return 0

    process.wait = wait
    result = runner.run_request(json.dumps(request).encode(), tmp_path, tmp_path)
    assert result['status'] == 'TEARDOWN_UNVERIFIED'
    assert calls == ['preflight', 'launch', 'stop', 'kill-client']
    assert len(waits) == 2


def test_spool_lock_symlink_rejected_before_launch(monkeypatch, tmp_path):
    request, process, calls = fake_dispatch(monkeypatch)
    target = tmp_path / 'keep'
    target.write_text('unchanged')
    (tmp_path / 'DISPATCH.lock').symlink_to(target)
    with pytest.raises(OSError):
        runner.run_request(json.dumps(request).encode(), tmp_path, tmp_path)
    assert target.read_text() == 'unchanged'
    assert calls == []


def test_writable_shared_spool_rejected_before_launch(monkeypatch, tmp_path):
    request, process, calls = fake_dispatch(monkeypatch)
    tmp_path.chmod(0o777)
    with pytest.raises(ValueError, match='private_broker_owned_spool'):
        runner.run_request(json.dumps(request).encode(), tmp_path, tmp_path)
    assert calls == []
