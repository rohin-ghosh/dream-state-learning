import importlib.util
import json
from pathlib import Path
from copy import deepcopy

import pytest


spec = importlib.util.spec_from_file_location('f4_switch', Path(__file__).parents[1] / 'gpu/orch_r137_grid_astra_switch.py')
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


def fixture_request():
    request = dict(id='P0317', lane_deadline_unix=500, payload=dict(life_id='F4_FABLE',
        game='grid', cycle=100, phase='experience', task_provenance=dict(split='TRAIN')))
    reservation = dict(kind='PARENT', number=317, reserved_unix=201)
    boundary = dict(after_parent=316, after_cycle=99, publication_unix=200,
                    train_end_unix=1000, cumulative_parent_ceiling=404430)
    return request, reservation, boundary


def test_truthful_Astra_is_rejected_by_actual_F4_consumer():
    result = subject.consumer_probe()
    assert result['F4_reason'] == 'actual_parent_model_mismatch'
    assert result['A4_truthful_Astra_status'] == 'COMPLETE'
    assert result['model_identity_spoofed'] is False


def test_future_only_inputs_immutable_and_not_authorized():
    values = fixture_request()
    before = deepcopy(values)
    assert subject.eligibility(*values, now=210) == 'METADATA_ELIGIBLE_NOT_AUTHORIZED'
    assert values == before


@pytest.mark.parametrize('flag', ['claimed', 'received', 'response_exists'])
def test_no_retry_any_prior_disposition(flag):
    assert subject.eligibility(*fixture_request(), now=210, **{flag: True}) == 'DISPOSED_NO_REDISPATCH'


@pytest.mark.parametrize('change,expected', [
    ('old_id', 'HISTORICAL_NO_REDISPATCH'),
    ('old_reservation', 'NOT_NEW_RESERVATION'),
    ('wrong_join', 'NOT_NEW_RESERVATION'),
    ('old_cycle', 'HISTORICAL_CYCLE'),
    ('open_turn', 'A4_NON_EPISODE_CADENCE_SKIP'),
    ('DEV', 'VISIBILITY_OR_LIFE_MISMATCH'),
    ('FINAL', 'VISIBILITY_OR_LIFE_MISMATCH'),
    ('expired', 'EXPIRED_NO_REDISPATCH'),
    ('cap', 'CUMULATIVE_CAP_EXHAUSTED'),
])
def test_exclusions(change, expected):
    request, reservation, boundary = fixture_request()
    if change == 'old_id':
        request['id'] = 'P0316'
    elif change == 'old_reservation':
        reservation['reserved_unix'] = 200
    elif change == 'wrong_join':
        reservation['number'] = 400
    elif change == 'old_cycle':
        request['payload']['cycle'] = 99
    elif change == 'open_turn':
        request['payload']['phase'] = 'open_turn'
    elif change in ('DEV', 'FINAL'):
        request['payload']['task_provenance']['split'] = change
    elif change == 'expired':
        request['lane_deadline_unix'] = 240
    elif change == 'cap':
        boundary['cumulative_parent_ceiling'] = 316
    assert subject.eligibility(request, reservation, boundary, now=210) == expected


def test_missing_is_not_reconstructed():
    request, reservation, boundary = fixture_request()
    assert subject.eligibility(None, reservation, boundary, now=210) == 'MISSING_NO_REDISPATCH'
    assert subject.eligibility(request, None, boundary, now=210) == 'MISSING_NO_REDISPATCH'


@pytest.fixture
def root(tmp_path):
    def write(relative, value):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
    write('CONFIG.json', dict(life_id='F4_FABLE', parent_model=subject.CLAUDE))
    write('parent_claude/CONFIG.json', dict(max_parent_calls=298, remote_root=str(tmp_path)))
    ledger = b''.join(json.dumps(dict(kind='PARENT', number=position, cycle=position // 3,
                       reserved_unix=position)).encode() + b'\n' for position in range(1, 317))
    (tmp_path / 'LEDGER.jsonl').write_bytes(ledger)
    write('independent_r119_v1/LEASE_BUDGET.json', dict(root=str(tmp_path),
        config_sha256=subject.sha((tmp_path / 'CONFIG.json').read_bytes()),
        ledger_prefix_bytes=len(ledger), ledger_prefix_sha256=subject.sha(ledger),
        historical_caps=dict(PARENT=298), counter_reset=False, optimizer_reset=False,
        hard_end_unix=subject.HARD_END, lease_end_unix=subject.HARD_END + 21600,
        prospective_caps=dict(PARENT=404430)))
    for position in range(1, 299):
        (tmp_path / 'parent_claude' / f'P{position:04d}.claim').mkdir()
    (tmp_path / 'parent_queue').mkdir()
    (tmp_path / 'parent_received').mkdir()
    write('parent_queue/P0316.request.json', dict(id='P0316', lane_deadline_unix=500,
        payload=dict(cycle=105, phase='experience', events='RAW_MUST_NOT_EXPORT')))
    return tmp_path


def test_snapshot_read_only_preserves_caps_and_no_raw(root):
    before = {str(path): path.read_bytes() for path in root.rglob('*') if path.is_file()}
    result = subject.inspect(root, clock=lambda: 400)
    assert result['boundary']['after_parent'] == 316
    assert result['allocation']['proposed_segment_cap'] == 404114
    assert result['allocation']['authorized_segment_cap'] == 0
    assert result['status'] == 'BLOCKED_CONSUMER_MODEL_BINDING'
    assert 'RAW_MUST_NOT_EXPORT' not in json.dumps(result)
    assert result['provider_calls'] == result['input_writes'] == 0
    assert before == {str(path): path.read_bytes() for path in root.rglob('*') if path.is_file()}


def test_ledger_reserved_without_request_still_sets_boundary(root):
    (root / 'parent_queue/P0316.request.json').unlink()
    result = subject.inspect(root)
    assert result['boundary']['after_parent'] == 316
    assert result['latest_request'] is None


def test_ambiguous_json_and_parent_ids_rejected():
    with pytest.raises(ValueError, match='duplicate_JSON_key'):
        subject.load('{"max_parent_calls":298,"max_parent_calls":999}')
    with pytest.raises(ValueError, match='parent_filename'):
        subject.number('../P0317.request.json')


def test_erasing_old_claims_is_rejected(root):
    (root / 'parent_claude/P0298.claim').rmdir()
    with pytest.raises(ValueError, match='original_298_claims_retained'):
        subject.inspect(root)


def test_symlinked_input_rejected(root):
    source = root / 'CONFIG.json'
    target = root / 'other.json'
    source.rename(target)
    source.symlink_to(target)
    with pytest.raises(ValueError, match='regular_immutable_input'):
        subject.inspect(root)


def test_pinned_live_loop_has_no_parent_model_reload():
    repository = Path(__file__).resolve().parents[1]
    if not (repository / 'gpu/orch_r119_grid_independent.py').is_file():
        repository = Path('/localhome/local-rohing/orch_r119_grid_independent_source_20260915_v1')
    assert subject.verify_native_source(repository) == subject.SOURCE_PINS
    native = (repository / 'gpu/orch_r119_grid_independent.py').read_text()
    mailbox = (repository / 'gpu/orch_r119_grid_async_parent.py').read_text()
    assert 'life_type(root, engine, config, cycle)' in native
    assert "self.config['parent_model']" in mailbox
    assert 'SIGHUP' not in native + mailbox


def test_no_publication_never_eligible():
    request, reservation, boundary = fixture_request()
    boundary['publication_unix'] = None
    assert subject.eligibility(request, reservation, boundary, now=210) == 'NOT_PUBLISHED'


def test_change_during_read_is_rejected(root, monkeypatch):
    original = Path.read_bytes
    reads = []
    def racing(path):
        raw = original(path)
        if path == root / 'LEDGER.jsonl':
            reads.append(True)
            if len(reads) == 2:
                return raw + b'changed'
        return raw
    monkeypatch.setattr(Path, 'read_bytes', racing)
    with pytest.raises(ValueError, match='snapshot_changed_repeat_read_only'):
        subject.inspect(root)
