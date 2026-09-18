import json
import types
import urllib.error
import urllib.request

import pytest

from provider_route import ENDPOINT, MODEL, routed


def fake_strong(prompt, directory, deadline, instruction='', *, reasoning_effort=None):
    request = urllib.request.Request(prompt, data=json.dumps(dict(model=MODEL)).encode(),
        headers={'Authorization': '[REDACTED_SECRET]'})
    return urllib.request.build_opener().open(request, timeout=1)


def configured(monkeypatch, sent):
    monkeypatch.setenv('NVIDIA_API_KEY', 'privately_inherited_test_value')
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *handlers: types.SimpleNamespace(
        open=lambda request, timeout: sent.append((request.full_url, request.data, timeout))))


def test_actual_route_and_key_not_exported(monkeypatch, tmp_path):
    sent = []
    configured(monkeypatch, sent)
    routed(fake_strong, tmp_path)(ENDPOINT, tmp_path, 1)
    assert sent[0][0] == ENDPOINT
    raw = (tmp_path / 'OUTBOUND_ROUTE.json').read_text()
    assert 'privately_inherited_test_value' not in raw
    receipt = json.loads(raw)
    assert not receipt['route_changed'] and receipt['actual_model'] == MODEL
    assert not receipt['secret_values_or_hashes_exported']


def test_working_route_preserved_once(monkeypatch, tmp_path):
    sent = []
    configured(monkeypatch, sent)
    routed(fake_strong, tmp_path)(ENDPOINT, tmp_path, 1)
    assert len(sent) == 1
    assert not json.loads((tmp_path / 'OUTBOUND_ROUTE.json').read_text())['route_changed']


def test_no_key_no_send(monkeypatch, tmp_path):
    sent = []
    configured(monkeypatch, sent)
    monkeypatch.delenv('NVIDIA_API_KEY')
    with pytest.raises(ValueError, match='privately_inherited'):
        routed(fake_strong, tmp_path)(ENDPOINT, tmp_path, 1)
    assert not sent


def test_consumed_send_receipt_forbids_second_call(monkeypatch, tmp_path):
    sent = []
    configured(monkeypatch, sent)
    routed(fake_strong, tmp_path)(ENDPOINT, tmp_path, 1)
    with pytest.raises(FileExistsError):
        routed(fake_strong, tmp_path)(ENDPOINT, tmp_path, 1)
    assert len(sent) == 1


def test_wrong_endpoint_refused_not_rewritten(monkeypatch, tmp_path):
    sent = []
    configured(monkeypatch, sent)
    with pytest.raises(ValueError, match='no_URL_rewrite'):
        routed(fake_strong, tmp_path)('https://[REDACTED_HOST]/responses', tmp_path, 1)
    assert not sent
