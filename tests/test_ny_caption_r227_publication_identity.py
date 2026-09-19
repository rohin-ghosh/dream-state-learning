import io
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

from research_loop.workers.rohin221_continuous_caption_20260918.sanitized_source import observe_fleet


@pytest.mark.parametrize('expected', [None, '', 'two words', 'user@node', 'node\n', '-node', 'x' * 254])
def test_missing_or_invalid_private_identity_is_rejected(expected):
    with pytest.raises(ValueError, match='private_expected_hostname_missing_or_invalid'):
        observe_fleet.validate_expected_hostname(expected)


def test_private_hosts_configuration_not_inherited_or_published(tmp_path, monkeypatch):
    hosts = tmp_path / 'hosts.env'
    hosts.write_text('OVX2_EXPECTED_HOSTNAME=synthetic-node-a\necho private-noise\n')
    monkeypatch.setenv('OVX2_EXPECTED_HOSTNAME', 'synthetic-inherited-node')
    assert observe_fleet.load_expected_node3_hostname(hosts) == 'synthetic-node-a'
    hosts.write_text('echo private-noise\n')
    with pytest.raises(ValueError, match='private_expected_hostname_missing_or_invalid'):
        observe_fleet.load_expected_node3_hostname(hosts)


def test_missing_private_hosts_file_fails_closed(tmp_path):
    with pytest.raises(ValueError, match='private_identity_configuration_unavailable'):
        observe_fleet.load_expected_node3_hostname(tmp_path / 'absent.env')


@pytest.mark.parametrize('payload', [{}, [], {'expected_hostname': None}, {'expected_hostname': ''}])
def test_remote_guard_rejects_absent_identity_before_artifact_reads(payload, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps(payload)))
    result = {}
    namespace = dict(json=json, result=result)
    with pytest.raises(ValueError, match='private_expected_hostname_missing_or_invalid'):
        exec(observe_fleet.IDENTITY_GUARD + "\nresult['artifact_read']=True", namespace)
    assert result == {}


@pytest.mark.parametrize('observed', ['synthetic-node-b', 'SYNTHETIC-NODE-A'])
def test_remote_identity_is_exact_and_mismatch_precedes_reads(observed, monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps({'expected_hostname': 'synthetic-node-a'})))
    result = {}
    namespace = dict(json=json, result=result,
        subprocess=SimpleNamespace(check_output=lambda *args, **kwargs: observed + '\n'))
    with pytest.raises(ValueError, match='remote_identity_mismatch') as failure:
        exec(observe_fleet.IDENTITY_GUARD + "\nresult['artifact_read']=True", namespace)
    assert result == {}
    assert observed not in str(failure.value)


def test_remote_identity_success_emits_only_logical_alias(monkeypatch):
    expected = 'synthetic-node-a'
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps({'expected_hostname': expected})))
    result = {}
    namespace = dict(json=json, result=result,
        subprocess=SimpleNamespace(check_output=lambda *args, **kwargs: expected + '\n'))
    exec(observe_fleet.IDENTITY_GUARD, namespace)
    assert result == {'identity_verified': True, 'node_alias': 'node3'}
    assert expected not in json.dumps(result)


@pytest.fixture
def isolated_collector(tmp_path, monkeypatch):
    for name in ('freeform.py', 'audit_metrics.py'):
        (tmp_path / name).write_text('\n')
    monkeypatch.setattr(observe_fleet, 'ROOT', tmp_path)
    return observe_fleet


def test_identity_stdin_not_command_or_public_receipt(isolated_collector, monkeypatch):
    expected = 'synthetic-node-a'
    calls = []

    def run(command, **options):
        calls.append((command, options))
        return SimpleNamespace(returncode=0,
            stdout=json.dumps(dict(identity_verified=True, node_alias='node3')), stderr='')

    monkeypatch.setattr(observe_fleet.subprocess, 'run', run)
    result = isolated_collector.remote_census('ovx2', 'result["artifact_read"]=True', expected)
    command, options = calls[0]
    assert command[:2] == ['bash', 'gpu/ovx2_ssh.sh']
    assert expected not in ' '.join(command)
    assert json.loads(options['input']) == {'expected_hostname': expected}
    assert command[-1].index('remote_identity_mismatch') < command[-1].index('artifact_read')
    assert result == {'identity_verified': True, 'node_alias': 'node3'}


def test_missing_identity_prevents_remote_dispatch(isolated_collector, monkeypatch):
    calls = []
    monkeypatch.setattr(observe_fleet.subprocess, 'run', lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError, match='private_expected_hostname_missing_or_invalid'):
        isolated_collector.remote_census('ovx2', 'result["artifact_read"]=True')
    assert calls == []


def test_main_requires_private_configuration_before_any_dispatch(monkeypatch):
    calls = []

    def missing_identity():
        raise ValueError('private_expected_hostname_missing_or_invalid')

    monkeypatch.setattr(observe_fleet, 'load_expected_node3_hostname', missing_identity)
    monkeypatch.setattr(observe_fleet, 'remote_census', lambda *args: calls.append(args))
    with pytest.raises(ValueError, match='private_expected_hostname_missing_or_invalid'):
        observe_fleet.main()
    assert calls == []


@pytest.mark.parametrize('stdout,error', [('not-json', 'invalid_remote_census_json'),
    ('[]', 'invalid_remote_census_schema'), ('{}', 'missing_verified_remote_identity')])
def test_malformed_or_unverified_result_not_counted(isolated_collector, monkeypatch, stdout, error):
    monkeypatch.setattr(observe_fleet.subprocess, 'run', lambda *args, **kwargs:
        SimpleNamespace(returncode=0, stdout=stdout, stderr='private-noise'))
    assert isolated_collector.remote_census('ovx2', '', 'synthetic-node-a') == {'error': error}


def test_transport_failure_does_not_publish_raw_stderr(isolated_collector, monkeypatch):
    private_text = 'synthetic-node-a private-noise'
    monkeypatch.setattr(observe_fleet.subprocess, 'run', lambda *args, **kwargs:
        SimpleNamespace(returncode=255, stdout=private_text, stderr=private_text))
    result = isolated_collector.remote_census('ovx2', '', 'synthetic-node-a')
    assert result == {'error': 'remote_census_failed', 'returncode': 255}
    assert private_text not in json.dumps(result)


@pytest.mark.parametrize('failure,code', [
    (subprocess.TimeoutExpired(['synthetic-private-command'], 35, stderr='private-noise'), 'bounded_remote_timeout'),
    (OSError('synthetic-private-path'), 'remote_transport_unavailable')])
def test_transport_exceptions_are_sanitized(isolated_collector, monkeypatch, failure, code):
    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(observe_fleet.subprocess, 'run', fail)
    assert isolated_collector.remote_census('ovx2', '', 'synthetic-node-a') == {'error': code}


def test_publication_source_has_no_literal_infrastructure_identity():
    source = Path(observe_fleet.__file__).read_text()
    assert not re.search(r'\bipp\d+-', source)
    assert not re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', source)
    assert 'source "$1"' in source
    assert 'OVX2_EXPECTED_HOSTNAME' in source
    assert 'if not root.is_dir()' in observe_fleet.NODE3
    assert 'hostname=' not in observe_fleet.COMMON
