import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def withdrawal(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'research_loop/workers/rohin174_parenting_20260917/withdraw_raw_control.py'
    specification = importlib.util.spec_from_file_location('control_withdrawal', path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    root = tmp_path / 'life'
    (root / 'stream/inbox').mkdir(parents=True)
    (root / 'stream/records').mkdir()
    message = dict(id=module.IDENTIFIER, actor='parent', speaker='Astra', text='Unconsumed test invitation')
    raw = json.dumps(message).encode()
    source = root / 'stream/inbox' / (module.IDENTIFIER + '.json')
    source.write_bytes(raw)
    record = root / 'stream/records/00000000000000000000.json'
    record.write_text(json.dumps(dict(kind='UPDATE', document={}, index=0, sha256='a' * 64)))
    plan = tmp_path / 'PLAN.json'
    plan.write_text(json.dumps({'root': str(root)}))
    guard = tmp_path / 'GUARD.json'
    guard.write_text(json.dumps({'plan_path': str(plan)}))
    module.ROOT, module.ARCHIVE, module.CONFIG = root, tmp_path / 'archive', str(guard)
    module.EXPECTED_SHA = hashlib.sha256(raw).hexdigest()
    process = {'state': 'R', 'signals': []}

    def signal(descriptor, action):
        process['signals'].append(action)
        process['state'] = 'T' if action == module.signal.SIGSTOP else 'R'

    monkeypatch.setattr(module, 'identity', lambda: process['state'])
    monkeypatch.setattr(module.os, 'pidfd_open', lambda unused: 123456)
    monkeypatch.setattr(module.os, 'close', lambda unused: None)
    monkeypatch.setattr(module.signal, 'pidfd_send_signal', signal)
    return module, source, record, raw, process


def test_unconsumed_message_preserved_and_native_resumed(withdrawal):
    module, source, unused, raw, process = withdrawal
    module.main()
    assert not source.exists()
    assert (module.ARCHIVE / source.name).read_bytes() == raw
    receipt = json.loads((module.ARCHIVE / 'WITHDRAWAL_RECEIPT.json').read_text())
    assert receipt['status'] == 'WITHDRAWN_BEFORE_INGESTION'
    assert receipt['native_resumed'] and not receipt['native_restart']
    assert process['signals'] == [module.signal.SIGSTOP, module.signal.SIGCONT]


def test_already_ingested_never_erases_history_and_still_resumes(withdrawal):
    module, source, record, raw, process = withdrawal
    record.write_text(json.dumps(dict(kind='INBOX', document={'message': {'id': module.IDENTIFIER}})))
    with pytest.raises(ValueError, match='already_ingested'):
        module.main()
    assert source.read_bytes() == raw
    assert not (module.ARCHIVE / source.name).exists()
    assert process['state'] == 'R'


def test_wrong_publication_never_signals(withdrawal):
    module, source, unused, unused_raw, process = withdrawal
    source.write_text('tampered')
    with pytest.raises(ValueError, match='exact_publication_hash'):
        module.main()
    assert process['signals'] == []


def test_pre_stopped_native_never_touched(withdrawal):
    module, source, unused, raw, process = withdrawal
    process['state'] = 'T'
    with pytest.raises(ValueError, match='not_pre_stopped'):
        module.main()
    assert source.read_bytes() == raw
    assert process['signals'] == []
