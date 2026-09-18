import json
import os
from unittest.mock import Mock

import pytest

from gpu import orch_r128_code_queue_recovery as policy


@pytest.fixture
def queue(tmp_path):
    (tmp_path / 'parent_queue').mkdir()
    (tmp_path / 'parent_claude').mkdir()
    return tmp_path


def request(root, identifier='TRAIN_C001_E1_parent2', deadline=200, created=100):
    path = root / 'parent_queue' / (identifier + '.request.json')
    path.write_text(json.dumps(dict(id=identifier, lane_deadline_unix=deadline)))
    os.utime(path, (created, created))
    return path


def test_empty_queue_emits_no_newline(queue):
    assert policy.listing(queue, 90, 150) == ''
    assert policy.listing(queue, 90, 150).splitlines() == []


def test_already_answered_queue_emits_no_newline(queue):
    path = request(queue)
    path.with_name(path.name.replace('.request.', '.response.')).write_text('{}')
    assert policy.listing(queue, 90, 150) == ''


@pytest.mark.parametrize('name', ['bad name.request.json', '../outside.request.json', '.request.json', 'x' * 101 + '.request.json'])
def test_real_invalid_filename_rejected(queue, name):
    with pytest.raises(ValueError, match='queue_filename'):
        policy.eligible(queue, name, 90, 150)


def test_invalid_filename_not_hidden_by_listing(queue):
    request(queue, 'bad name')
    with pytest.raises(ValueError, match='queue_filename'):
        policy.listing(queue, 90, 150)


def test_claimed_request_never_retried(queue):
    path = request(queue)
    claim = queue / 'parent_claude' / (path.name.removesuffix('.request.json') + '.claim')
    claim.mkdir()
    assert policy.listing(queue, 90, 150) == ''
    assert claim.exists() and path.exists()


@pytest.mark.parametrize('deadline', [149, 150])
def test_expired_request_never_claimed(queue, deadline):
    path = request(queue, deadline=deadline)
    before = path.read_bytes()
    assert policy.listing(queue, 90, 150) == ''
    assert path.read_bytes() == before


def test_pre_recovery_request_not_reissued(queue):
    request(queue, created=89)
    assert policy.listing(queue, 90, 150) == ''


def test_future_live_request_retains_exact_filename(queue):
    path = request(queue)
    assert policy.listing(queue, 90, 150) == path.name


def test_blank_only_is_skipped_not_whitespace():
    delegate, allowed = Mock(), Mock(return_value=True)
    args = (None, {}, {}, '', None, None, None)
    assert policy.guarded_request(delegate, allowed, *args) == 'EMPTY_LISTING'
    delegate.assert_not_called()
    with pytest.raises(ValueError, match='queue_filename'):
        policy.guarded_request(delegate, allowed, None, {}, {}, ' ', None, None, None)


def test_dispatch_rechecks_racing_claim(queue):
    path = request(queue)
    assert policy.listing(queue, 90, 150) == path.name
    (queue / 'parent_claude' / (path.name.removesuffix('.request.json') + '.claim')).mkdir()
    delegate = Mock()
    allowed = lambda name: policy.eligible(queue, name, 90, 150)
    assert policy.guarded_request(delegate, allowed, None, {}, {}, path.name, None, None, None) == 'INELIGIBLE_NO_RETRY'
    delegate.assert_not_called()


def test_exact_root_ownership_and_caps(tmp_path):
    config = dict(remote_root=policy.ROOTS['ovx2'], deadline_unix=200, max_parent_calls=372)
    config_path = tmp_path / 'CONFIG.json'
    config_path.write_text(json.dumps(config))
    recovery = dict(root=config['remote_root'], wrapper='ovx2', authorization='R128_CODE_ONLY_QUEUE_RECOVERY',
        not_before_unix=100, deadline_unix=200, max_parent_calls=372, retry_old_claims=False,
        change_actor=False, local_files=[], config=dict(path=str(config_path), sha256=policy.sha(config_path)))
    policy.validate_recovery(recovery, config, 'ovx2', 150)
    for patch in ({'remote_root': policy.ROOTS['a40r']}, {'max_parent_calls': 500}, {'deadline_unix': 300}):
        with pytest.raises(ValueError):
            policy.validate_recovery(recovery, dict(config, **patch), 'ovx2', 150)
    with pytest.raises(ValueError):
        policy.validate_recovery(recovery, config, 'ovx2', 201)


def test_original_broker_retains_exclusive_lock_and_real_validation():
    import inspect
    from gpu import orch_r119_code_old_parent as inherited
    source = inspect.getsource(inherited.provider.serve)
    assert "ledger / 'RUNNER.lock'" in source
    assert "'single_lane_broker'" in source
    assert 'provider.serve.__code__' in inspect.getsource(policy.serve)
    assert 'provider.process_request.__code__' in inspect.getsource(policy.serve)


def test_existing_custody_lock_blocks_second_broker(tmp_path, monkeypatch):
    from types import FunctionType, SimpleNamespace
    from gpu import orch_r119_code_old_parent as inherited
    provider = inherited.provider
    config = dict(remote_root='/native/code', principles_sha256=provider.PRINCIPLES_V2_SHA256)
    config_path, launch_path = tmp_path / 'config.json', tmp_path / 'launch.json'
    config_path.write_text(json.dumps(config))
    launch_path.write_text('{}')
    calls = []

    class OccupiedStore:
        def __init__(self, root):
            pass

        def shell(self, command, check=True):
            calls.append(command)
            return SimpleNamespace(returncode=1 if 'RUNNER.lock' in command else 0)

    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    namespace = dict(provider.serve.__globals__, ROOT=tmp_path,
        validate_config=lambda *args: None, validate_launch=lambda *args: None,
        validate_cli_allowlist=lambda *args: None, sha=lambda *args: provider.PRINCIPLES_V2_SHA256,
        shutil=SimpleNamespace(disk_usage=lambda *args: SimpleNamespace(free=20 * 1024 ** 3)),
        Store=OccupiedStore)
    function = FunctionType(provider.serve.__code__, namespace, 'serve', provider.serve.__defaults__)
    function.__kwdefaults__ = provider.serve.__kwdefaults__
    with pytest.raises(ValueError, match='single_lane_broker'):
        function(config_path, launch_path, tmp_path, tmp_path / 'principles')
    assert len(calls) == 2
