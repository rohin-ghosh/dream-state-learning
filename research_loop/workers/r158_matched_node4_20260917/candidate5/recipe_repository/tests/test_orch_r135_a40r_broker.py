import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
from types import ModuleType, SimpleNamespace

import pytest

from gpu import orch_r135_a40r_broker as broker


def snapshot(physical):
    config = broker.slot(physical)
    return dict(physical=physical, uuid=config['uuid'], host_sha256=broker.HOST_SHA,
        campaign=str(broker.campaign(physical)), main_ready_sha256=config['main_sha'],
        epoch_sha256=config['epoch_sha'], ready_sha256=config['ready_sha'],
        principles_sha256=broker.PRINCIPLES_SHA, next_parent_number=config['floor'],
        publication_present=True, provider_files={broker.PRINCIPLES: broker.PRINCIPLES_SHA})


@pytest.mark.parametrize('physical', [0, 2])
def test_only_new_request_range_and_exact_campaign(physical):
    config = broker.slot(physical)
    campaign = broker.campaign(physical)
    request = campaign / 'parent_queue' / f"GUIDED_SLEEP_C{config['cycle']}_P{config['floor']}.request.json"
    assert broker.validate_request_path(physical, campaign, request) == (config['cycle'], config['floor'])
    for bad_path in [request.with_name(f"GUIDED_SLEEP_C{config['cycle']}_P{config['floor']-1}.request.json"),
            request.with_name('GUIDED_SLEEP_C60_P641.request.json'),
            request.with_name('GUIDED_SLEEP_C257_P128.request.json'),
            request.with_name('GUIDED_SLEEP_C1_P128.request.json'),
            request.with_name('GUIDED_SLEEP_C60_P0128.request.json'),
            request.with_name('GUIDED_SLEEP_C60_P128.response.json'),
            request.parent / '../GUIDED_SLEEP_C60_P128.request.json',
            Path(config['root']) / config['prior'] / 'campaign_node1_7/parent_queue' / request.name]:
        with pytest.raises(ValueError):
            broker.validate_request_path(physical, campaign, bad_path)
    with pytest.raises(ValueError):
        broker.validate_request_path(physical, broker.campaign(2 if physical == 0 else 0), request)
    with pytest.raises(ValueError):
        broker.campaign(physical, '/other')
    with pytest.raises(ValueError):
        broker.campaign(physical, lane='node1_6')


@pytest.mark.parametrize('physical', [1, 3, 7, True, '2'])
def test_unowned_slots_rejected(physical):
    with pytest.raises(ValueError):
        broker.slot(physical)


@pytest.mark.parametrize('physical', [0, 2])
@pytest.mark.parametrize('key', ['physical', 'uuid', 'host_sha256', 'campaign', 'main_ready_sha256',
    'epoch_sha256', 'ready_sha256', 'principles_sha256', 'next_parent_number'])
def test_remote_binding_drift_fails_closed(physical, key):
    value = snapshot(physical)
    broker.validate_snapshot(physical, value)
    value[key] = 'not-the-pinned-value'
    with pytest.raises(ValueError):
        broker.validate_snapshot(physical, value)


def test_provider_and_principles_hashes_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(broker, 'DEPENDENCY', tmp_path)
    relative = 'provider.py'
    (tmp_path / relative).write_text('FROZEN = True\n')
    pin = broker.sha(tmp_path / relative)
    principles = tmp_path / broker.PRINCIPLES
    principles.parent.mkdir()
    principles.write_text('frozen shared principles')
    monkeypatch.setattr(broker, 'PRINCIPLES_SHA', broker.sha(principles))
    monkeypatch.setattr(broker, 'PINS', {relative: pin})
    broker.verify_dependencies({relative: pin})
    with pytest.raises(ValueError):
        broker.verify_dependencies({relative: 'drift'})
    with pytest.raises(ValueError):
        broker.verify_dependencies({'../outside.py': pin})
    (tmp_path / relative).write_text('modified')
    with pytest.raises(ValueError):
        broker.verify_dependencies({relative: pin})


@pytest.mark.parametrize('devices', [(1, 1, 1), (1, 2, 1), (3, 2, 1)])
def test_raw_storage_cannot_fall_back_to_VMroot(devices):
    with pytest.raises(ValueError):
        broker.validate_data_device(*devices)
    broker.validate_data_device(36, 36, 64513)


def test_exact_compatibility_symlink_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(broker, 'DATA_PARENT', tmp_path)
    monkeypatch.setattr(broker, 'validate_data_device', lambda *args: None)
    original_path = broker.Path
    alias = tmp_path / 'compatibility_parent'

    def paths(value):
        if str(value) == '/tmp/orch_r135_broker_a40r0_v1':
            return alias
        return original_path(value)

    monkeypatch.setattr(broker, 'Path', paths)
    target, result_alias = broker.storage(0)
    assert not target.exists() and result_alias == alias
    alias.symlink_to(target, target_is_directory=True)
    assert broker.storage(0) == (target, alias)
    alias.unlink()
    alias.symlink_to(tmp_path / 'wrong', target_is_directory=True)
    with pytest.raises(ValueError, match='exact_tmp_compatibility_parent'):
        broker.storage(0)


def test_single_flock_and_no_dirty_buffer_restart(tmp_path, monkeypatch):
    target, alias = tmp_path / 'data', tmp_path / 'compatibility'
    monkeypatch.setattr(broker, 'storage', lambda physical: (target, alias))
    with broker.queue_owner(0) as (buffer, receipts):
        assert alias.is_symlink() and alias.resolve() == target
        assert buffer == alias / 'buffer' and receipts == alias / 'receipts'
        assert not buffer.exists() and not receipts.exists()
        with (target / 'QUEUE.lock').open('a') as other:
            with pytest.raises(BlockingIOError):
                fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
        buffer.mkdir()
        assert buffer.resolve().parent == target
    with pytest.raises(ValueError, match='new_bounded_buffer_receipts_only'):
        with broker.queue_owner(0):
            pytest.fail('Dirty buffer was reused')


@pytest.mark.parametrize('physical', [0, 2])
@pytest.mark.parametrize('mutation', ['none', 'renamed_old_id', 'missing_intent', 'wrong_ready', 'held', 'wrong_mode'])
def test_request_gate_reads_metadata_before_unchanged_claim(tmp_path, monkeypatch, physical, mutation):
    config = dict(broker.slot(physical), root=str(tmp_path))
    monkeypatch.setitem(broker.SLOTS, physical, config)
    directory = broker.campaign(physical) / 'parent_queue'
    directory.mkdir(parents=True)
    path = directory / f"GUIDED_SLEEP_C{config['cycle']}_P{config['floor']}.request.json"
    request = dict(id=path.name.removesuffix('.request.json'), ready_sha256=config['ready_sha'],
        payload=dict(cycle=config['cycle'], split='TRAIN', mode='BEHAVIOR', turn=0))
    intent = dict(kind='PARENT', number=config['floor'], lane=broker.LANE, cycle=config['cycle'], mode='BEHAVIOR', turn=0)
    if mutation == 'renamed_old_id':
        request['id'] = f"GUIDED_SLEEP_C{config['cycle']}_P{config['floor']-1}"
    elif mutation == 'wrong_ready':
        request['ready_sha256'] = 'wrong'
    elif mutation == 'held':
        request['payload']['split'] = 'HELD'
    elif mutation == 'wrong_mode':
        intent['mode'] = 'OTHER'
    path.write_text(json.dumps(request))
    (tmp_path / 'RESERVATIONS.jsonl').write_text('' if mutation == 'missing_intent' else json.dumps(intent) + '\n')
    commands = []

    def shell(command, check):
        commands.append(command)
        assert check is False
        parts = shlex.split(command)
        assert parts[:2] == ['python3', '-c']
        try:
            exec(compile(parts[2], 'remote-CPU-fixture', 'exec'), {})
            return SimpleNamespace(returncode=0, stdout='R135_REQUEST_SCOPE_OK\n')
        except AssertionError:
            return SimpleNamespace(returncode=1, stdout='')

    if mutation == 'none':
        broker.request_gate(SimpleNamespace(shell=shell), physical, path, config['ready_sha'])
    else:
        with pytest.raises(ValueError):
            broker.request_gate(SimpleNamespace(shell=shell), physical, path, config['ready_sha'])
    assert len(commands) == 1
    assert not list(directory.glob('*.claim'))


def source_function(relative, name):
    path = broker.DEPENDENCY / relative
    assert broker.sha(path) == broker.PINS[relative]
    text = path.read_text()
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == name)
    return ast.get_source_segment(text, node)


@pytest.mark.parametrize('physical', [0, 2])
def test_actual_recovery_broker_seam_polls_only_new_queue_and_delegates_unchanged(tmp_path, monkeypatch, physical):
    config = broker.slot(physical)
    target, alias = tmp_path / 'data', tmp_path / 'compatibility'
    target.mkdir()
    alias.symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(broker, 'storage', lambda physical: (target, alias))
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    provider_calls, checked, sleeps, finds = [], [], [], []
    policy = SimpleNamespace(HOSTS={'node1': dict(wrapper='gpu/a40r_ssh.sh', scp='gpu/a40r_scp.sh', sha256=broker.HOST_SHA)},
        LANES={broker.LANE:dict(host='node1', physical=7, uuid='old', learned=False, cadence='hundred')},
        DEVICES={broker.LANE:'old'}, PRINCIPLES_SHA=broker.PRINCIPLES_SHA, PRINCIPLES_PATH=broker.PRINCIPLES,
        require=broker.require, allocation=lambda lane: None)
    remote_ready = dict(hard_deadline_unix=1000, provider_files={}, parent_cap=640)
    request_path = broker.campaign(physical) / 'parent_queue' / f"GUIDED_SLEEP_C{config['cycle']}_P{config['floor']}.request.json"

    class Store:
        def __init__(self, repository, root, lane):
            assert root == Path(config['root']) and lane == broker.LANE
            self.polls = 0

        def exists(self, path):
            assert path.parent == broker.campaign(physical)
            if path.name == 'PUBLICATION.json':
                return True
            assert path.name == 'TERMINAL.json'
            self.polls += 1
            return self.polls > 1

        def shell(self, command):
            if command.startswith('cat '):
                assert str(broker.campaign(physical) / 'READY.json') in command
                return SimpleNamespace(stdout=json.dumps(remote_ready))
            if command.startswith('sha256sum '):
                return SimpleNamespace(stdout=config['ready_sha'])
            assert command.startswith('find ')
            finds.append(command)
            return SimpleNamespace(stdout=str(request_path))

    old_broker = ModuleType('fixture_frozen_broker')
    old_broker.__dict__.update(policy=policy, os=os, json=json, Path=Path, shlex=shlex, Store=Store,
        time=SimpleNamespace(time=lambda: 10, sleep=sleeps.append),
        existing=SimpleNamespace(transport=SimpleNamespace(parent=SimpleNamespace(sha=lambda path: broker.PRINCIPLES_SHA))),
        provider_calls=provider_calls)
    exec('def process(*args):\n    provider_calls.append(args)\n', old_broker.__dict__)
    original_process = old_broker.process
    original_code = original_process.__code__
    serve_source = source_function('gpu/orch_r109_route_broker.py', 'serve')
    exec(compile(serve_source, 'frozen_serve', 'exec'), old_broker.__dict__)
    recovery = ModuleType('fixture_frozen_recovery')
    recovery.__file__ = str(tmp_path / 'dependency/gpu/orch_r111_route_recovery.py')
    principles = tmp_path / 'dependency' / broker.PRINCIPLES
    principles.parent.mkdir(parents=True)
    principles.write_text('Exact principles text')
    recovery.__dict__.update(old_broker=old_broker, old=SimpleNamespace(policy=policy), Path=Path,
        inspect=SimpleNamespace(getsource=lambda function: serve_source),
        replace_once=lambda source, old, new: source.replace(old,new))
    exec(compile(source_function('gpu/orch_r111_route_recovery.py', 'broker'), 'frozen_recovery_broker', 'exec'), recovery.__dict__)
    monkeypatch.setattr(broker, 'request_gate', lambda *args: checked.append(args))
    broker.bind(recovery, physical)
    with pytest.raises(ValueError, match='one_exact_queue_binding'):
        broker.bind(recovery, physical)
    assert recovery.directory(Path(config['root']), broker.LANE) == broker.campaign(physical)
    assert policy.LANES[broker.LANE]['physical'] == physical and policy.DEVICES[broker.LANE] == config['uuid']
    assert policy.LANES[broker.LANE]['cadence'] == 'hundred'
    recovery.broker(tmp_path, Path(config['root']), broker.LANE, alias/'buffer', alias/'receipts')
    assert len(provider_calls) == len(checked) == len(finds) == 1
    assert provider_calls[0][1:] == (broker.campaign(physical), request_path, alias/'buffer', alias/'receipts',
        config['ready_sha'], 'Exact principles text', 1000)
    assert sleeps == [2]
    assert original_process.__code__ is original_code
    assert original_process is not old_broker.process


def test_check_preflight_has_no_storage_or_serve_side_effects(tmp_path, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(broker, 'remote_snapshot', lambda *args: snapshot(0))
    monkeypatch.setattr(broker, 'verify_dependencies', lambda *args: None)
    monkeypatch.setattr(broker, 'storage', lambda physical: (tmp_path/'data', tmp_path/'alias'))
    monkeypatch.setattr(broker, 'queue_owner', lambda *args: pytest.fail('Owner acquired during check'))
    before = list(tmp_path.iterdir())
    response, receipt = broker.preflight(0, broker.REPOSITORY)
    assert list(tmp_path.iterdir()) == before
    assert not receipt['broker_started'] and receipt['provider_calls'] == 0
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', 'GPU-not-CPU')
    with pytest.raises(ValueError):
        broker.preflight(0, broker.REPOSITORY)


def test_transport_check_uses_only_existing_wrapper_without_credentials(monkeypatch):
    calls = []

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps(snapshot(2)))

    monkeypatch.setattr(broker.subprocess, 'run', run)
    assert broker.remote_snapshot(broker.REPOSITORY, 2) == snapshot(2)
    assert calls[0][0] == ['bash', str(broker.REPOSITORY/'gpu/a40r_ssh.sh'), 'python3 -']
    assert calls[0][1]['input'] == broker.remote_code(2)
    assert 'MAIN_READY.json' in calls[0][1]['input'] and 'EPOCH.json' in calls[0][1]['input']
    assert 'R135.runtime' not in Path(broker.__file__).read_text()
