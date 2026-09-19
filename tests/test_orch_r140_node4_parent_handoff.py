import json
from pathlib import Path

import pytest

from gpu import orch_r140_node4_parent_handoff as handoff


@pytest.fixture
def config():
    return dict(physical=3, node='a40r', cadence_responses=3, cadence_label='SPARSE',
        parent_style='Socratic', branch='raw3', programme='raw_parented', hard_end_unix=1789754400)


def call(root, number, count, config, status='PUBLISHED'):
    directory = root / f'parent_{number:06d}'
    directory.mkdir()
    source = dict(response_count=count, head_sha256=str(number)*64)
    result = dict(source_response_count=count, source_head_sha256=source['head_sha256'],
        schedule_on='response', schedule_count=count, branch=config['branch'], programme=config['programme'],
        status=status, started_unix=1, finished_unix=2, inbox_publication={'id': 'published'})
    (directory/'SOURCE.json').write_text(json.dumps(source))
    (directory/'RESULT.json').write_text(json.dumps(result))
    return directory


def test_sparse_cursor_includes_silent_and_failed_reserved_calls(tmp_path, config):
    for index, status in enumerate(['PUBLISHED', 'SILENT', 'MISSING']):
        call(tmp_path, index, (index+1)*3, config, status)
    state = handoff.reservation(tmp_path, config)
    assert state['response_cursor'] == 9 and len(state['receipts']) == 3


def test_inflight_call_blocks_parent_handoff(tmp_path, config):
    directory = call(tmp_path, 0, 3, config)
    (directory/'RESULT.json').unlink()
    with pytest.raises(ValueError, match='unfinished_parent_call'):
        handoff.reservation(tmp_path, config)


@pytest.mark.parametrize('patch', [{'source_response_count': 2}, {'schedule_count': 4},
    {'source_head_sha256': 'wrong'}, {'status': 'STARTED'}, {'inbox_publication': None}, {'programme': 'other'}])
def test_uncertain_or_mismatched_reservation_blocks_handoff(tmp_path, config, patch):
    directory = call(tmp_path, 0, 3, config)
    path = directory/'RESULT.json'
    path.write_text(json.dumps(dict(json.loads(path.read_text()), **patch)))
    with pytest.raises(ValueError):
        handoff.reservation(tmp_path, config)


def test_successor_changes_only_language_and_cursor_provenance(tmp_path, config, monkeypatch):
    path = tmp_path/'old.json'
    path.write_text(json.dumps(config))
    monkeypatch.setattr(handoff.adapter, 'validate', lambda value: value)
    spec = dict(old_config=str(path), old_output='/old/output', old_started_sha256='oldhash',
        english_programme_path='/new/programme', english_programme_sha256='newhash')
    result = handoff.successor_config(spec, {'response_cursor': 27})
    assert all(result[key] == value for key, value in config.items())
    assert result['start_after_response_count'] == 27
    assert result['parent_language'] == 'English'
    assert result['predecessor_output'] == '/old/output'
    assert 'poll_interval_seconds' not in result and 'schedule_on' not in result


def test_wrong_physical_handoff_never_calls_signal_library(tmp_path, config, monkeypatch):
    path = tmp_path/'old.json'
    path.write_text(json.dumps(dict(config, physical=0)))
    monkeypatch.setattr(handoff.adapter, 'validate', lambda value: value)
    called = []
    monkeypatch.setattr(handoff.idle, 'handoff', lambda spec: called.append(spec))
    with pytest.raises(ValueError, match='only_raw3'):
        handoff.handoff(dict(old_config=str(path)))
    assert not called


def test_handoff_restores_shared_helper_bindings_on_failure(tmp_path, config, monkeypatch):
    path = tmp_path/'old.json'
    path.write_text(json.dumps(config))
    monkeypatch.setattr(handoff.adapter, 'validate', lambda value: value)
    monkeypatch.setattr(handoff.idle, 'sha', lambda path: 'pin')
    original = handoff.idle.MODULE, handoff.idle.reservation, handoff.idle.successor_config
    def fail(spec):
        assert handoff.idle.MODULE == 'gpu.orch_r136_node4_parent'
        assert handoff.idle.reservation is handoff.reservation
        raise ValueError('test stop')
    monkeypatch.setattr(handoff.idle, 'handoff', fail)
    with pytest.raises(ValueError, match='test stop'):
        handoff.handoff(dict(old_config=str(path), english_programme_path='/programme', english_programme_sha256='pin'))
    assert (handoff.idle.MODULE, handoff.idle.reservation, handoff.idle.successor_config) == original
