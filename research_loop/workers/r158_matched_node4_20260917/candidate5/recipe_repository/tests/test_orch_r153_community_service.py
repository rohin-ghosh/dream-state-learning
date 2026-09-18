from concurrent.futures import Future
from copy import deepcopy
import json
from pathlib import Path
import time

import pytest

from gpu import orch_r153_community_exchange as exchange
from gpu import orch_r153_community_service as service_module
from gpu import orch_r153_community_transport as transport
from tests.test_orch_r153_community_transport import records, fake_cpu, StreamJournal, ContinualStream, TrainHistory


class ImmediateExecutor:
    def submit(self, function, *args, **kwargs):
        future = Future()
        try:
            future.set_result(function(*args, **kwargs))
        except Exception as error:
            future.set_exception(error)
        return future


class LocalTransport:
    def __init__(self, config):
        self.hosts = config['hosts']
        self.calls = []
        self.lose_push_ack = False

    def pull(self, agent, cursor, head_sha256, **limits):
        self.calls.append(('pull', agent['host'], agent['root']))
        return transport.pull_committed(agent['root'], agent['journal_id'], cursor, head_sha256, **limits)

    def push(self, agent, packet):
        self.calls.append(('push', agent['host'], agent['root']))
        result = transport.remote_dispatch(dict(op='install', root=agent['root'], packet=packet,
            document_sha256=exchange.sha(exchange.encoded(transport.delivery_document(agent['root'], packet)))))
        if self.lose_push_ack:
            self.lose_push_ack = False
            raise OSError('simulated lost ack')
        return result

    def cpu(self, agent, origin, *, start, artifact_link=None):
        self.calls.append(('cpu', agent['host'], agent['root']))
        return transport.cpu_once(agent['root'], agent['journal_id'], origin,
            self.hosts[agent['host']]['gate_sha256'], start=start, artifact_link=artifact_link,
            gate_root=self.hosts[agent['host']].get('gate_root', transport.GATE_ROOT))


@pytest.fixture
def configured(tmp_path, monkeypatch):
    repository = Path(__file__).resolve().parents[1]
    calls, gate = fake_cpu(monkeypatch)
    hosts = {host: dict(repository='/localhome/local-rohing/r153-code', wrapper_sha256=exchange.sha(
        (repository / wrapper).read_bytes()), source_sha256=transport.source_pins(repository), gate_sha256=gate)
        for host, wrapper in transport.WRAPPERS.items() if host in ('a40r', 'ovx2')}
    agents = {}
    for position, actor in enumerate(exchange.ACTORS, start=1):
        root = tmp_path / ('orch_r153_' + actor) / 'life'
        (root / 'stream' / 'records').mkdir(parents=True)
        (root / 'stream' / 'inbox').mkdir()
        journal_id = f'{position:032x}'
        (root / 'stream' / 'JOURNAL.json').write_bytes(exchange.encoded(
            dict(schema='R125_STREAM_JOURNAL_V1', journal_id=journal_id)))
        agents[actor] = dict(host='ovx2' if position <= 2 else 'a40r', root=str(root),
                            journal_id=journal_id, start_index=0, start_after_sha256='0' * 64)
    config = dict(schema=service_module.SCHEMA, repository=str(repository), broker_root=str(tmp_path / 'broker'),
                  mirror_root=str(tmp_path / 'mirrors'), hosts=hosts, agents=agents, poll_seconds=0.05,
                  max_records=12, max_bytes=1024 * 1024, max_polls=2, deadline_unix=time.time() + 600,
                  max_cpu_calls_per_actor=8, kernel_policy='DISABLED_SEPARATE_OWNER_REQUIRED')
    client = LocalTransport(config)
    service = service_module.CommunityService(config, transport=client, executor=ImmediateExecutor())
    return service, config, client, calls


def append(config, actor, raw):
    agent = config['agents'][actor]
    root = Path(agent['root'])
    existing = sorted((root / 'stream' / 'records').glob('*.json'))
    start = len(existing)
    head = json.loads(existing[-1].read_bytes())['sha256'] if existing else '0' * 64
    return records(root, agent['journal_id'], raw, start=start, previous=head)


def action(config, actor, **fields):
    return append(config, actor, exchange.encoded(fields).decode())


def rows(service, statement):
    with service.broker._locked() as database:
        return [dict(row) for row in database.execute(statement)]


def test_five_real_receiver_roots_write_publish_read_message_and_CPU(configured):
    service, config, client, calls = configured
    for actor in exchange.ACTORS:
        action(config, actor, op='write_workspace', name='code.py', text='print(1)\n')
    service.tick()
    assert all((Path(config['mirror_root']) / actor / 'workspace' / 'code.py').read_text() == 'print(1)\n'
               for actor in exchange.ACTORS)
    for actor in exchange.ACTORS:
        action(config, actor, op='publish_artifact', name='code.py')
    service.tick()
    artifact = rows(service, "SELECT id FROM artifacts WHERE actor='C1'")[0]['id']
    for actor in exchange.ACTORS:
        action(config, actor, op='open_artifact', artifact_id=artifact)
    service.tick()
    action(config, 'C1', op='send_message', recipient='C4', text='Please inspect my public code.')
    service.tick()
    message = rows(service, 'SELECT id FROM messages')[0]['id']
    action(config, 'C4', op='read_message', message_id=message)
    for actor in exchange.ACTORS:
        append(config, actor, '```python\nprint(1)\n```')
    service.tick()
    assert len(calls) == 5
    assert {str(call['root']) for call in calls} == {agent['root'] for agent in config['agents'].values()}
    cpu_jobs = rows(service, "SELECT outcome FROM service_jobs WHERE status='CPU_DONE'")
    assert len(cpu_jobs) == 5
    assert all(json.loads(job['outcome'])['artifact_link']['artifact_id'] == artifact for job in cpu_jobs)
    for actor, agent in config['agents'].items():
        actual = list((Path(agent['root']) / 'stream' / 'inbox').glob('*.json'))
        assert len(actual) >= 4
        assert all(json.loads(path.read_bytes())['actor'] == 'environment' for path in actual)
        assert list((Path(config['mirror_root']) / actor / 'stream' / 'inbox').glob('*.json')) == []
    assert len([call for call in client.calls if call[0] == 'cpu']) == 5


def test_all5_ovx3_profile_preserves_five_exchange_and_CPU_paths(configured):
    unused_service, config, unused_client, calls = configured
    repository = Path(config['repository'])
    gate_root = '/localhome/local-rohing/orch_r153_cpu_smoke_20260916t2245z/gate'
    host = dict(config['hosts']['ovx2'], gate_root=gate_root,
        wrapper_sha256=exchange.sha((repository / transport.WRAPPERS['ovx3']).read_bytes()))
    config['hosts'] = {'ovx3': host}
    config['profile'] = 'ALL5_OVX3'
    config['broker_root'] += '_ovx3'
    config['mirror_root'] += '_ovx3'
    for agent in config['agents'].values():
        agent['host'] = 'ovx3'
    client = LocalTransport(config)
    service = service_module.CommunityService(config, transport=client, executor=ImmediateExecutor())
    test_five_real_receiver_roots_write_publish_read_message_and_CPU((service, config, client, calls))
    assert {call['gate'] for call in calls} == {gate_root}
    config['kernel_policy'] = 'R148_FILTERED_A40R'
    with pytest.raises(ValueError):
        service_module.validate_config(config)


def test_native_five_journals_existing_zero_cursors_ingest_and_restart(configured):
    service, config, client, unused_calls = configured
    for agent in config['agents'].values():
        (Path(agent['root']) / 'stream/WRITER.lock').touch()
        with StreamJournal(Path(agent['root']) / 'stream') as journal:
            stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
                context_limit=4096, segment_tokens=128, segments_per_sleep=2,
                deadline_unix=1000, model_state_sha256='f' * 64)
            journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
            stream.step(lambda messages, **kwargs: dict(raw='{"op":"list_workspace","cursor":0}',
                token_ids=[10, 2], terminal=True, truncated=False),
                lambda messages: sum(len(message['content'].split()) + 4 for message in messages),
                journal.record, now=lambda: 100)
    service.tick()
    assert len(rows(service, 'SELECT * FROM service_jobs')) == 5
    assert all(row['next_index'] == 4 and row['error'] is None
               for row in rows(service, 'SELECT * FROM service_cursors'))
    before = {actor: len(list((Path(agent['root']) / 'stream/inbox').glob('*.json')))
              for actor, agent in config['agents'].items()}
    assert all(count == 1 for count in before.values())
    resumed = service_module.CommunityService(config, transport=client, executor=ImmediateExecutor())
    resumed.tick()
    assert len(rows(resumed, 'SELECT * FROM service_jobs')) == 5
    assert before == {actor: len(list((Path(agent['root']) / 'stream/inbox').glob('*.json')))
                      for actor, agent in config['agents'].items()}


def test_restart_cursor_and_lost_push_ack_no_duplicate_remote_delivery(configured):
    service, config, client, calls = configured
    action(config, 'C1', op='write_workspace', name='note.txt', text='persist')
    client.lose_push_ack = True
    service.tick()
    actual = Path(config['agents']['C1']['root']) / 'stream' / 'inbox'
    assert len(list(actual.glob('*.json'))) == 1
    assert service.broker.pending_deliveries('C1')
    reopened = service_module.CommunityService(config, transport=client, executor=ImmediateExecutor())
    reopened.tick()
    assert len(list(actual.glob('*.json'))) == 1
    assert reopened.broker.pending_deliveries('C1') == []
    assert len(rows(reopened, 'SELECT * FROM notes')) == 1
    assert rows(reopened, "SELECT next_index FROM service_cursors WHERE actor='C1'")[0]['next_index'] == 3


def test_no_automatic_thought_or_kernel_execution_and_json_fence_supported(configured):
    service, config, client, calls = configured
    append(config, 'C1', 'I am reflecting; no message chosen.')
    append(config, 'C2', '```triton\nimport triton\n```')
    append(config, 'C3', '```json\n{"op":"list_artifacts","cursor":0}\n```')
    service.tick()
    assert rows(service, "SELECT status FROM service_jobs WHERE actor='C1'")[0]['status'] == 'IGNORED'
    assert rows(service, "SELECT status FROM service_jobs WHERE actor='C2'")[0]['status'] == 'KERNEL_UNCONNECTED'
    assert calls == []
    assert not list((Path(config['agents']['C1']['root']) / 'stream' / 'inbox').glob('*.json'))
    assert len(rows(service, 'SELECT * FROM effects')) == 1


def test_CPU_inflight_does_not_block_other_exchange_operations(configured):
    service, config, client, calls = configured

    class PendingExecutor:
        def __init__(self):
            self.jobs = []

        def submit(self, function, *args, **kwargs):
            future = Future()
            self.jobs.append((function, args, kwargs, future))
            return future

    executor = PendingExecutor()
    service.executor = executor
    for actor in exchange.ACTORS:
        append(config, actor, '```python\nprint(1)\n```')
        action(config, actor, op='write_workspace', name='ongoing.txt', text='I keep working')
    status = service.tick()
    assert len(executor.jobs) == 5 and status['cpu_inflight'] == list(exchange.ACTORS)
    assert len(rows(service, 'SELECT * FROM notes')) == 5
    assert len(rows(service, "SELECT * FROM service_jobs WHERE status='CPU_INTENT'")) == 5


def test_restart_CPU_intent_recovers_remote_result_without_rerun(configured):
    service, config, client, calls = configured
    append(config, 'C1', '```python\nprint(1)\n```')
    service.tick()
    assert len(calls) == 1
    with service.broker._locked() as database:
        database.execute("UPDATE service_jobs SET status='CPU_INTENT', outcome=NULL WHERE actor='C1'")
    reopened = service_module.CommunityService(config, transport=client, executor=ImmediateExecutor())
    reopened.tick()
    assert len(calls) == 1
    assert rows(reopened, "SELECT status FROM service_jobs WHERE actor='C1'")[0]['status'] == 'CPU_DONE'


def test_validation_launch_modes_no_remote_check_or_implicit_start(configured, tmp_path, capsys, monkeypatch):
    service, config, client, calls = configured
    path = tmp_path / 'config.json'
    path.write_bytes(exchange.encoded(config))
    monkeypatch.setattr(service_module, 'CommunityService', lambda configuration: (_ for unused in ()).throw(
        AssertionError('check-config must not instantiate running service')))
    assert service_module.main(['--config', str(path), '--check-config']) == 0
    assert json.loads(capsys.readouterr().out)['remote_checked'] is False
    assert calls == [] and client.calls == []
    with pytest.raises(SystemExit):
        service_module.main(['--config', str(path)])


@pytest.mark.parametrize('mutation', ['host_count', 'shared_journal', 'kernel_owner', 'deadline', 'gate_pin'])
def test_invalid_launch_configuration_rejected(configured, mutation):
    service, config, client, calls = configured
    value = deepcopy(config)
    if mutation == 'host_count':
        value['agents']['C1']['host'] = 'a40r'
    elif mutation == 'shared_journal':
        value['agents']['C1']['journal_id'] = value['agents']['C2']['journal_id']
    elif mutation == 'kernel_owner':
        value['kernel_policy'] = 'run_every_block_in_both'
    elif mutation == 'deadline':
        value['deadline_unix'] = float('inf')
    else:
        value['hosts']['ovx2']['gate_sha256'] = 'not-a-hash'
    with pytest.raises(ValueError):
        service_module.validate_config(value)


def test_remote_actor_error_does_not_stop_other_lives(configured):
    service, config, client, calls = configured
    for actor in exchange.ACTORS:
        action(config, actor, op='write_workspace', name='note.txt', text=actor)
    root = Path(config['agents']['C1']['root'])
    (root / 'stream' / 'JOURNAL.json').write_bytes(exchange.encoded(
        dict(schema='R125_STREAM_JOURNAL_V1', journal_id='f' * 32)))
    service.tick()
    assert len(rows(service, 'SELECT * FROM notes')) == 4
    assert rows(service, "SELECT error FROM service_cursors WHERE actor='C1'")[0]['error'] == 'pinned_remote_journal'


def test_opt_in_R148_routes_a40r_only_without_CPU_execution(configured, tmp_path):
    service, config, client, calls = configured
    config = deepcopy(config)
    config.update(broker_root=str(tmp_path / 'external-broker'), mirror_root=str(tmp_path / 'external-mirrors'),
                  kernel_policy='R148_FILTERED_A40R')
    connected = service_module.CommunityService(config, transport=client, executor=ImmediateExecutor())
    for actor in exchange.ACTORS:
        append(config, actor, '```python\nimport torch, triton\n```')
    status = connected.tick()
    assert calls == [] and status['kernel_connected'] is False and status['external_kernel_configured'] is True
    assert len(rows(connected, "SELECT * FROM service_jobs WHERE status='ROUTED_KERNEL'")) == 3
    assert len(rows(connected, "SELECT * FROM service_jobs WHERE status='KERNEL_UNCONNECTED'")) == 2
    outcomes = [json.loads(row['outcome']) for row in rows(connected, 'SELECT outcome FROM service_jobs')]
    assert {outcome['route'] for outcome in outcomes} == {'routed_kernel', 'not_connected'}
