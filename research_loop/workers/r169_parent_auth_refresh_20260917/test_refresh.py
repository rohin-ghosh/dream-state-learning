import importlib.util
import json
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location('refresh', Path(__file__).with_name('refresh.py'))
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


def test_only_initial_cursor_changes():
    raw = 'def serve():\n    last_count = 3\n    values = [last_count]\n    for value in [20]:\n        last_count = value\n        values.append(last_count)\n    return values\n'
    namespace = {}
    exec(refresh.patched_code(raw, '<test>', 15), namespace)
    assert namespace['serve']() == [15, 20]


def test_cursor_never_moves_backwards():
    namespace = {}
    exec(refresh.patched_code('def serve():\n    last_count=30\n    return last_count\n', '<test>', 15), namespace)
    assert namespace['serve']() == 30


@pytest.mark.parametrize('raw', ['def serve():\n    pass\n', 'def serve():\n    last_count=0\n    last_count=1\n'])
def test_unknown_source_refused(raw):
    with pytest.raises(ValueError, match='one_initial_cursor_only'):
        refresh.patched_code(raw, '<test>', 0)


def test_native_cannot_be_selected():
    with pytest.raises(ValueError, match='standard_parent_only'):
        refresh.source_for(dict(argv=['python', '-m', 'gpu.orch_r125_continual_native'], cwd='/tmp'))


def test_identity_binds_ticks_not_state():
    before = dict(pid=1, ticks='2', argv=['python'], cwd='/tmp', uid=5, state='S')
    assert refresh.same_process(before, dict(before, state='T'))
    assert not refresh.same_process(before, dict(before, ticks='3'))


@pytest.mark.parametrize('clock', ['request_count', 'response_count'])
def test_all_reserved_attempts_including_missing_advance_cursor(tmp_path, clock):
    config = dict(branch='test', programme='raw_parented', schedule_on=clock.removesuffix('_count'))
    (tmp_path/'STARTED.json').write_text(json.dumps(config))
    for index, status in enumerate(['MISSING', 'SILENT', 'PUBLISHED']):
        directory = tmp_path/f'parent_{index:06d}'
        directory.mkdir()
        source = dict(head_sha256='a'*64, response_count=10+index, request_count=20+index)
        result = dict(branch='test', source_head_sha256=source['head_sha256'],
            source_response_count=source['response_count'], status=status,
            inbox_publication=dict(id='pending_unchanged'))
        (directory/'SOURCE.json').write_text(json.dumps(source))
        (directory/'RESULT.json').write_text(json.dumps(result))
    ledger = refresh.settled(tmp_path, config)
    assert ledger['cursor'] == (22 if clock == 'request_count' else 12)
    assert ledger['pending_inbox_ids'] == ['pending_unchanged']
    assert ledger['statuses'] == dict(MISSING=1, SILENT=1, PUBLISHED=1)
    assert len(ledger['pins']) == 6


def test_unsettled_dispatch_never_admitted(tmp_path):
    config = dict(branch='test', programme='raw_parented')
    (tmp_path/'STARTED.json').write_text(json.dumps(config))
    (tmp_path/'parent_000000').mkdir()
    with pytest.raises(ValueError, match='unsettled_attempt_wait'):
        refresh.settled(tmp_path, config)
