import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location('community_refresh', Path(__file__).with_name('refresh.py'))
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


def create_attempt(tmp_path, status='PROVIDER_FAILED'):
    attempt = tmp_path / 'parent_000000000123'
    attempt.mkdir()
    result = dict(status=status, message='A bounded message.', publication=dict(id='publication', sha256='inboxhash'))
    refresh.write(attempt / 'RESULT.json', result)
    return attempt, result


def test_failed_attempt_not_completion_or_render(tmp_path):
    create_attempt(tmp_path)
    value = refresh.summary(tmp_path)
    assert value['status_counts'] == {'PROVIDER_FAILED': 1}
    assert value['rendered_count'] == 0
    assert value['pending_publications'] == 0


def test_publication_is_not_delivery(tmp_path):
    create_attempt(tmp_path, 'PUBLISHED')
    value = refresh.summary(tmp_path)
    assert value['pending_publications'] == 1
    assert value['rendered_count'] == 0


def test_silent_completed_provider_is_not_publication(tmp_path):
    attempt, unused = create_attempt(tmp_path, 'SILENT')
    refresh.write(attempt / 'stdout.json', dict(status='completed', model=refresh.MODEL))
    value = refresh.summary(tmp_path)
    assert value['entries'][0]['provider_complete']
    assert value['rendered_count'] == value['pending_publications'] == 0


def test_tampered_delivery_refused(tmp_path):
    attempt, result = create_attempt(tmp_path, 'PUBLISHED')
    refresh.write(attempt / 'DELIVERED.json', dict(status='RENDERED', result_sha256='wrong',
        publication=result['publication'], rendered=dict(inbox_sha256='inboxhash',
            text_sha256=hashlib.sha256(result['message'].encode()).hexdigest())))
    with pytest.raises(AssertionError):
        refresh.summary(tmp_path)


def test_scope_excludes_children_and_legacy():
    assert refresh.BRANCHES == ('C1', 'C2', 'C3', 'C4', 'C5')
    assert refresh.MODEL == 'openai/openai/gpt-6-astra'
