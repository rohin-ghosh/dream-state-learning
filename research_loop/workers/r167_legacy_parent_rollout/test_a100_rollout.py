"""CPU-only old R133 receipt and parent-only handoff regressions."""

import json
from pathlib import Path
import signal
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import a100_rollout as rollout
import legacy_takeover as legacy
from test_legacy_takeover import FakeOperations


def fixture(tmp_path, status='PUBLISHED'):
    config = dict(branch='a100_6_classroom_creative', programme='creative_writing', root='/life')
    root = tmp_path / 'old'
    directory = root / 'parent_000000'
    directory.mkdir(parents=True)
    legacy.write(root / 'STARTED.json', dict(branch=config['branch'], programme=config['programme']))
    source = dict(response_count=12, head_sha256='a' * 64)
    legacy.write(directory / 'SOURCE.json', source)
    result = dict(branch=config['branch'], programme=config['programme'], source_response_count=12,
        source_head_sha256='a' * 64, started_unix=1, finished_unix=2, status=status)
    if status == 'PUBLISHED':
        result['inbox_publication'] = dict(id='originalid', path='/life/stream/inbox/originalid.json', sha256='b'*64)
    elif status == 'MISSING':
        result.update(error_code='parent_call_or_delivery_failed', error_type='HTTPError')
    legacy.write(directory / 'RESULT.json', result)
    return config, root, directory


def test_actual_old_receipts_do_not_require_invented_dispatch_or_schedule(tmp_path):
    config, root, directory = fixture(tmp_path)
    previous = rollout.ledger(root, config, rollout.adapter.SOURCE_SHA256)
    assert previous['reserved_response_count'] == 12
    assert previous['pending_inbox_ids'] == ['originalid']
    assert not (directory / 'DISPATCH_INTENT.json').exists()
    assert 'schedule_count' not in json.loads((directory / 'RESULT.json').read_text())


def test_old_prepublication_failure_preserves_missing(tmp_path):
    config, root, directory = fixture(tmp_path, 'MISSING')
    before = (directory / 'RESULT.json').read_bytes()
    previous = rollout.ledger(root, config, rollout.adapter.SOURCE_SHA256)
    assert previous['statuses'] == {'MISSING': 1} and previous['reserved_response_count'] == 12
    assert (directory / 'RESULT.json').read_bytes() == before


@pytest.mark.parametrize('key,value', [('sent_unix', None), ('response', None), ('inbox_publication', {}),
    ('source_response_count', 11), ('source_head_sha256', 'wrong'), ('finished_unix', 0),
    ('branch', 'other'), ('status', 'UNKNOWN')])
def test_old_ambiguous_or_unbound_result_rejected(tmp_path, key, value):
    config, root, directory = fixture(tmp_path, 'MISSING')
    path = directory / 'RESULT.json'
    document = json.loads(path.read_text())
    document[key] = value
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        rollout.ledger(root, config, rollout.adapter.SOURCE_SHA256)


def test_wrong_source_cannot_supply_missing_controlflow_proof(tmp_path):
    config, root, directory = fixture(tmp_path, 'MISSING')
    with pytest.raises(ValueError):
        rollout.ledger(root, config, 'wrong')


def binding():
    operations = FakeOperations()
    value = dict(branch='a100_6_classroom_creative', node='a100', parent=operations.observed.copy(),
        original_source=dict(sha256=rollout.adapter.SOURCE_SHA256),
        original_config=dict(path='/config'), old_output='/old')
    return value, operations


def test_busy_A100_parent_continued_without_termination():
    value, operations = binding()
    operations.busy = True
    with pytest.raises(ValueError):
        with rollout.quiesce(value, operations):
            pytest.fail('busy')
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]


@pytest.mark.parametrize('change', ['branch', 'node', 'source', 'native', 'pid_reuse', 'stopped'])
def test_no_signals_for_unverified_A100_process(change):
    value, operations = binding()
    if change == 'branch':
        value['branch'] = 'C1'
    elif change == 'node':
        value['node'] = 'ovx2'
    elif change == 'source':
        value['original_source']['sha256'] = 'other'
    elif change == 'native':
        operations.observed['argv'][2] = 'gpu.orch_r125_continual_guard'
    elif change == 'pid_reuse':
        operations.observed['start_ticks'] = 'new'
    else:
        operations.observed['state'] = 'T'
    with pytest.raises(ValueError):
        with rollout.quiesce(value, operations):
            pytest.fail('unverified')
    assert not operations.signals


def test_Main_adapter_bytes_exact():
    assert legacy.ref(rollout.ADAPTER_PATH)['sha256'] == rollout.ADAPTER_SHA


@pytest.mark.parametrize('mode,expected', [('control-native', True), ('control-supervise', False),
    ('native', False), ('--readout-manifest', False)])
def test_control_probe_exact_entrypoint_not_readout(mode, expected):
    from remote_control_metadata import selected
    argv = ['python3', '-B', '-m', 'gpu.orch_r136_node1_launcher', mode, '--config', '/guard']
    assert selected(argv) is expected


def test_control_probe_bytes_exact():
    assert legacy.ref(legacy.HERE / 'remote_control_metadata.py')['sha256'] == rollout.CONTROL_PROBE_SHA


def test_control_native_rejects_wrong_process_before_remote(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('must refuse before remote')
    monkeypatch.setattr(rollout.subprocess, 'run', forbidden)
    with pytest.raises(ValueError, match='exact_control_native_profile'):
        rollout.native_check(dict(branch=rollout.CONTROLS[0], node='a100', native=dict(entrypoint='readout')))
