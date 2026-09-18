"""Independent refresh safety probes: no signals, remote access, or credentials."""

import importlib.util
import json
from pathlib import Path

import pytest


specification = importlib.util.spec_from_file_location(
    'r169_refresh_review_subject', Path(__file__).with_name('refresh.py'))
refresh = importlib.util.module_from_spec(specification)
specification.loader.exec_module(refresh)


def ledger_fixture(tmp_path, schedule='response'):
    config = dict(branch='review', programme='creative_writing', schedule_on=schedule,
                  start_after_response_count=10, start_after_request_count=11)
    (tmp_path / 'STARTED.json').write_text(json.dumps(config))
    for index, status in enumerate(('MISSING', 'PUBLISHED', 'SILENT')):
        directory = tmp_path / f'parent_{index:06d}'
        directory.mkdir()
        source = dict(head_sha256=str(index) * 64, response_count=12 + index,
                      request_count=13 + index)
        result = dict(branch='review', status=status, source_head_sha256=source['head_sha256'],
                      source_response_count=source['response_count'],
                      inbox_publication=dict(id='review-existing-inbox'))
        (directory / 'SOURCE.json').write_text(json.dumps(source))
        (directory / 'RESULT.json').write_text(json.dumps(result))
    return config


@pytest.mark.parametrize('schedule, expected', [('response', 14), ('request', 15)])
def test_every_settled_status_reserves_its_source_cursor(tmp_path, schedule, expected):
    config = ledger_fixture(tmp_path, schedule)
    ledger = refresh.settled(tmp_path, config)
    assert ledger['cursor'] == expected
    assert ledger['statuses'] == dict(MISSING=1, PUBLISHED=1, SILENT=1)
    assert ledger['pending_inbox_ids'] == ['review-existing-inbox']
    assert len(ledger['pins']) == 6


def test_missing_result_refuses_unsettled_attempt(tmp_path):
    config = ledger_fixture(tmp_path)
    (tmp_path / 'parent_000002/RESULT.json').unlink()
    with pytest.raises(ValueError, match='unsettled_attempt_wait'):
        refresh.settled(tmp_path, config)


def test_mismatched_result_source_refuses_cursor_transfer(tmp_path):
    config = ledger_fixture(tmp_path)
    path = tmp_path / 'parent_000002/RESULT.json'
    result = json.loads(path.read_text())
    result['source_head_sha256'] = 'wrong'
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match='bound_result_source'):
        refresh.settled(tmp_path, config)


@pytest.mark.xfail(strict=True, reason='scope blocker: -m is searched anywhere, not parsed as Python entry')
def test_nonparent_script_with_parent_module_argument_is_refused():
    process = dict(argv=['python3', '/tmp/nonparent.py', '-m', 'gpu.orch_r133_programme_parent'],
                   cwd=str(refresh.REPO))
    with pytest.raises(ValueError):
        refresh.source_for(process)


@pytest.mark.xfail(strict=True, reason='scope blocker: lexical parent path accepts traversal outside scope')
def test_standalone_parent_path_cannot_escape_legacy_scope():
    escaped = refresh.REPO / 'research_loop/workers/r167_legacy_parent_rollout/../foreign/PARENT.py'
    process = dict(argv=['python3', str(escaped)], cwd=str(refresh.REPO))
    with pytest.raises(ValueError):
        refresh.source_for(process)


@pytest.mark.xfail(strict=True, reason='preflight gap: load_parent validates config but not serve startup')
def test_receiving_preflight_rejects_failing_serve_startup(tmp_path):
    parent = tmp_path / 'SOURCE.py'
    provider = tmp_path / 'PROVIDER.py'
    config = tmp_path / 'CONFIG.json'
    parent.write_text('def validate(config):\n    return config\n'
                      'def serve(*args):\n    last_count = 0\n'
                      '    raise ValueError("startup_gate_failed")\n')
    provider.write_text(f'STRONG = {refresh.MODEL!r}\ndef strong(*args):\n    return None\n')
    config.write_text('{}')
    binding = dict(source_copy=str(parent), source_sha256=refresh.sha(parent),
        original_source=str(parent), provider_copy=str(provider), provider_sha256=refresh.sha(provider),
        config=str(config), config_sha256=refresh.sha(config),
        operator_sha256=refresh.sha(refresh.__file__), cursor=15)
    with pytest.raises(ValueError, match='startup_gate_failed'):
        refresh.load_parent(binding)
