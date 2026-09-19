from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from gpu import orch_r153_community_exchange as exchange
from gpu import orch_r153_community_transport as transport
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream


def records(root, journal_id, raw, *, start=0, previous=None, split='TRAIN'):
    if start == 0:
        previous = exchange._digest(json.loads((root / 'stream' / 'JOURNAL.json').read_bytes()))
    values = []
    request = dict(split=split, resume_state={})
    response = dict(request_sha256=exchange._digest(dict(split=split)),
                    response=dict(raw=raw, terminal=True, truncated=False))
    for offset, (kind, document) in enumerate((('REQUEST', request), ('RESPONSE', response),
            ('COMMITTED', dict(source_sha256=exchange._digest(response))))):
        value = dict(schema='R125_STREAM_JOURNAL_V1', journal_id=journal_id, index=start + offset,
                     kind=kind, document=document, previous_sha256=previous)
        value['sha256'] = exchange._digest(value)
        (root / 'stream' / 'records' / f'{start + offset:020d}.json').write_bytes(exchange.encoded(value))
        values.append(value)
        previous = value['sha256']
    return values


@pytest.fixture
def remote(tmp_path):
    root = tmp_path / 'orch_r153_fixture' / 'life'
    (root / 'stream' / 'records').mkdir(parents=True)
    (root / 'stream' / 'inbox').mkdir()
    journal_id = 'a' * 32
    (root / 'stream' / 'JOURNAL.json').write_bytes(exchange.encoded(
        dict(schema='R125_STREAM_JOURNAL_V1', journal_id=journal_id)))
    return root, journal_id


@pytest.fixture
def native_remote(tmp_path):
    root = tmp_path / 'orch_r153_native' / 'life'
    root.mkdir(parents=True)
    with StreamJournal(root / 'stream', create=True) as journal:
        stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=2,
            deadline_unix=1000, model_state_sha256='f' * 64)
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        stream.step(lambda messages, **kwargs: dict(raw='{"op":"list_workspace","cursor":0}',
            token_ids=[10, 2], terminal=True, truncated=False),
            lambda messages: sum(len(message['content'].split()) + 4 for message in messages),
            journal.record, now=lambda: 100)
    manifest = json.loads((root / 'stream' / 'JOURNAL.json').read_bytes())
    return root, manifest['journal_id'], manifest


def test_native_StreamJournal_genesis_birth_and_resumed_TRAIN_triple(native_remote):
    root, journal_id, manifest = native_remote
    first_record = json.loads((root / 'stream/records' / f'{0:020d}.json').read_bytes())
    assert first_record['kind'] == 'COMMITTED'
    assert first_record['previous_sha256'] == exchange._digest(manifest) != '0' * 64
    first = transport.pull_committed(str(root), journal_id, 0, '0' * 64, max_records=3)
    assert first['next_cursor'] == 3 and first['snapshots'] == []
    assert first['start_head_sha256'] == '0' * 64
    second = transport.pull_committed(str(root), journal_id, 3, first['head_sha256'])
    assert second['next_cursor'] == 4 and len(second['snapshots']) == 1
    assert [record['kind'] for record in second['snapshots'][0]['records']] == ['REQUEST', 'RESPONSE', 'COMMITTED']
    repeated = transport.pull_committed(str(root), journal_id, 0, '0' * 64)
    assert repeated['snapshots'] == second['snapshots']
    with pytest.raises(ValueError, match='remote_cursor_anchor_changed'):
        transport.pull_committed(str(root), journal_id, 3, '0' * 64)


@pytest.mark.parametrize('wrong_genesis', ['0' * 64, 'f' * 64])
def test_native_genesis_tampering_rejected_even_with_rehashed_record(native_remote, wrong_genesis):
    root, journal_id, unused_manifest = native_remote
    path = root / 'stream/records' / f'{0:020d}.json'
    value = json.loads(path.read_bytes())
    value['previous_sha256'] = wrong_genesis
    value['sha256'] = exchange._digest({key: item for key, item in value.items() if key != 'sha256'})
    path.write_bytes(exchange.encoded(value))
    with pytest.raises(ValueError, match='remote_adjacent_chain'):
        transport.pull_committed(str(root), journal_id, 0, '0' * 64)


def test_empty_native_journal_keeps_initial_sentinel(tmp_path):
    root = tmp_path / 'orch_r153_empty' / 'life'
    root.mkdir(parents=True)
    with StreamJournal(root / 'stream', create=True):
        pass
    manifest = json.loads((root / 'stream/JOURNAL.json').read_bytes())
    result = transport.pull_committed(str(root), manifest['journal_id'], 0, '0' * 64)
    assert result['head_sha256'] == '0' * 64 and result['next_cursor'] == 0


@pytest.mark.parametrize('truncated', [True, False])
def test_native_incomplete_commit_skipped_then_complete_response_delivered(tmp_path, truncated):
    root = tmp_path / 'orch_r153_incomplete' / 'life'
    root.mkdir(parents=True)
    with StreamJournal(root / 'stream', create=True) as journal:
        stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=4,
            deadline_unix=1000, model_state_sha256='f' * 64)
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        for terminal in (False, True):
            stream.step(lambda messages, **kwargs: dict(raw='{"op":"list_workspace","cursor":0}',
                token_ids=[10] * 128 if not terminal else [10, 2],
                terminal=terminal, truncated=truncated if not terminal else False),
                lambda messages: sum(len(message['content'].split()) + 4 for message in messages),
                journal.record, now=lambda: 100)
    manifest = json.loads((root / 'stream/JOURNAL.json').read_bytes())
    first = transport.pull_committed(str(root), manifest['journal_id'], 0, '0' * 64, max_records=4)
    assert first['next_cursor'] == 4 and first['snapshots'] == []
    second = transport.pull_committed(str(root), manifest['journal_id'], 4, first['head_sha256'])
    assert second['next_cursor'] == 7 and len(second['snapshots']) == 1
    assert second['snapshots'][0]['records'][1]['index'] == 5
    assert transport.pull_committed(str(root), manifest['journal_id'], 0, '0' * 64)['snapshots'] == second['snapshots']


@pytest.mark.parametrize('fault', ['join', 'raw', 'terminal', 'truncated'])
def test_incomplete_skip_never_bypasses_join_or_generation_types(remote, fault):
    root, journal_id = remote
    chain = records(root, journal_id, 'incomplete')
    generation = chain[1]['document']['response']
    generation.update(terminal=False, truncated=True)
    if fault == 'raw':
        generation['raw'] = None
    elif fault == 'terminal':
        generation['terminal'] = 0
    elif fault == 'truncated':
        generation['truncated'] = 1
    chain[1]['sha256'] = exchange._digest({key: value for key, value in chain[1].items() if key != 'sha256'})
    chain[2]['previous_sha256'] = chain[1]['sha256']
    chain[2]['document']['source_sha256'] = 'f' * 64 if fault == 'join' else exchange._digest(chain[1]['document'])
    chain[2]['sha256'] = exchange._digest({key: value for key, value in chain[2].items() if key != 'sha256'})
    for record in chain[1:]:
        (root / 'stream/records' / f'{record["index"]:020d}.json').write_bytes(exchange.encoded(record))
    with pytest.raises(ValueError, match='TRAIN_request_response_commit_join' if fault == 'join'
                       else 'valid_incomplete_generated_response_required'):
        transport.pull_committed(str(root), journal_id, 0, '0' * 64)


def test_pull_pinned_complete_train_triples_across_cursor_boundary(remote):
    root, journal_id = remote
    chain = records(root, journal_id, '{"op":"list_workspace","cursor":0}')
    first = transport.pull_committed(str(root), journal_id, 0, '0' * 64, max_records=2)
    assert first['next_cursor'] == 2 and first['snapshots'] == []
    second = transport.pull_committed(str(root), journal_id, first['next_cursor'], first['head_sha256'])
    assert second['next_cursor'] == 3 and len(second['snapshots']) == 1
    assert second['snapshots'][0]['records'] == chain
    empty = transport.pull_committed(str(root), journal_id, 3, second['head_sha256'])
    assert empty['snapshots'] == [] and empty['head_sha256'] == second['head_sha256']


@pytest.mark.parametrize('fault', ['journal', 'anchor', 'record', 'split', 'symlink', 'incomplete'])
def test_pull_fail_closed_origin_and_filesystem(remote, fault):
    root, journal_id = remote
    chain = records(root, journal_id, 'child text', split='DEV' if fault == 'split' else 'TRAIN')
    if fault == 'journal':
        journal_id = 'b' * 32
    if fault == 'record':
        path = root / 'stream' / 'records' / f'{1:020d}.json'
        value = json.loads(path.read_bytes())
        value['document']['response']['raw'] = 'changed'
        path.write_bytes(exchange.encoded(value))
    if fault == 'symlink':
        path = root / 'stream' / 'records' / f'{0:020d}.json'
        saved = path.with_suffix('.saved')
        path.rename(saved)
        path.symlink_to(saved)
    if fault == 'incomplete':
        (root / 'stream' / 'records' / f'{2:020d}.json').unlink()
        result = transport.pull_committed(str(root), journal_id, 0, '0' * 64)
        assert result['snapshots'] == [] and result['next_cursor'] == 2
        return
    with pytest.raises((ValueError, OSError)):
        transport.pull_committed(str(root), journal_id, 1 if fault == 'anchor' else 0,
                                 'f' * 64 if fault == 'anchor' else '0' * 64)


def test_pull_bytes_bound_never_skips_large_record(remote):
    root, journal_id = remote
    records(root, journal_id, 'x' * 8000)
    first = transport.pull_committed(str(root), journal_id, 0, '0' * 64, max_bytes=4096)
    assert first['next_cursor'] == 1
    with pytest.raises(ValueError, match='single_record_exceeds_pull_budget'):
        transport.pull_committed(str(root), journal_id, first['next_cursor'], first['head_sha256'], max_bytes=4096)


def fake_cpu(monkeypatch):
    calls = []
    monkeypatch.setattr(transport.cpu, 'verify_gate', lambda root: {'fixture_gate': True})

    def run(raw, spool, gate_root, journal_root, *, code_policy):
        calls.append(dict(root=journal_root, policy=code_policy, gate=gate_root))
        request = transport.cpu.parse_request(raw)
        result = dict(schema='R125_CPU_EXPERIMENT_RESULT_V1', request_id=request['request_id'],
            source_sha256=request['source_sha256'], raw_request_sha256=exchange.sha(raw),
            origin=transport.cpu.verify_origin(request, journal_root, code_policy=code_policy),
            status='COMPLETE', returncode=0, stdout='unit-test fixture; not live execution', stderr='',
            launch_attempted=True)
        path = Path(spool) / request['request_id']
        path.mkdir(parents=True)
        (path / 'RESULT.json').write_bytes(exchange.encoded(result))
        return result

    monkeypatch.setattr(transport.cpu, 'run_request', run)
    return calls, transport.cpu.digest({'fixture_gate': True})


def test_real_origin_CPU_policy_once_and_actual_console_publication(remote, monkeypatch):
    root, journal_id = remote
    chain = records(root, journal_id, '```python\nprint(“hello”)\n```')
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256=chain[1]['sha256'])
    calls, gate_sha256 = fake_cpu(monkeypatch)
    idle = transport.cpu_once(str(root), journal_id, origin, gate_sha256)
    assert idle['status'] == 'NOT_STARTED' and not calls
    first = transport.cpu_once(str(root), journal_id, origin, gate_sha256, start=True)
    second = transport.cpu_once(str(root), journal_id, origin, gate_sha256, start=True)
    assert first == second and len(calls) == 1
    assert calls[0] == dict(root=root, policy=transport.blocks.POLICY, gate=transport.GATE_ROOT)
    assert first['status'] == 'PUBLISHED'
    assert first['origin']['code_transformation']['transformations']
    message = json.loads(Path(first['publication']['path']).read_bytes())
    assert message['actor'] == 'environment' and message['speaker'] == 'Tool'
    assert message['source_receipt']['sha256'] == first['result_sha256']
    assert len(list((root / 'stream' / 'inbox').glob('*.json'))) == 1


def test_nfkc_policy_reaches_cpu_origin_execution_and_publication(remote, monkeypatch):
    root, journal_id = remote
    chain = records(root, journal_id, '```python\nprint(９８)\n```')
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256=chain[1]['sha256'])
    calls, gate_sha256 = fake_cpu(monkeypatch)
    result = transport.cpu_once(str(root), journal_id, origin, gate_sha256, start=True,
                                code_policy=transport.blocks.NFKC_POLICY)
    assert result['status'] == 'PUBLISHED'
    assert calls[0]['policy'] == transport.blocks.NFKC_POLICY
    assert result['origin']['code_transformation']['source_sha256'] == transport.blocks.sha('print(98)\n')
    assert result['origin']['code_transformation']['raw_source_sha256'] == transport.blocks.sha('print(９８)\n')
    assert transport.code_route('```python\nｉｍｐｏｒｔ triton\n```',
                                code_policy=transport.blocks.NFKC_POLICY)[0] == 'KERNEL'
    assert transport.cpu_once(str(root), journal_id, origin, gate_sha256, start=True,
                              code_policy=transport.blocks.NFKC_POLICY) == result
    assert len(calls) == 1


def test_existing_life_cpu_policy_preserves_root_and_journal_binding(remote, monkeypatch):
    root, journal_id = remote
    parent = root.parent
    renamed = parent.with_name('orch_r136_existing')
    parent.rename(renamed)
    root = renamed / 'life'
    chain = records(root, journal_id, '```python\nprint(９８)\n```')
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256=chain[1]['sha256'])
    calls, gate = fake_cpu(monkeypatch)
    with pytest.raises(ValueError, match='new_canonical_R153_life_root'):
        transport.cpu_once(str(root), journal_id, origin, gate, start=True)
    with pytest.raises(ValueError, match='pinned_remote_journal'):
        transport.cpu_once(str(root), 'b' * 32, origin, gate, start=True,
            root_policy=transport.EXISTING_LIFE_CPU_POLICY)
    assert not calls
    result = transport.remote_dispatch(dict(op='cpu', root=str(root), journal_id=journal_id,
        origin=origin, gate_sha256=gate, start=True, artifact_link=None,
        code_policy=transport.blocks.NFKC_POLICY, root_policy=transport.EXISTING_LIFE_CPU_POLICY))
    assert result['status'] == 'PUBLISHED'
    assert calls == [dict(root=root, policy=transport.blocks.NFKC_POLICY, gate=transport.GATE_ROOT)]


def test_existing_life_cpu_policy_never_follows_a_symlink(remote, monkeypatch):
    root, journal_id = remote
    alias = root.parent / 'alias'
    alias.symlink_to(root, target_is_directory=True)
    calls, gate = fake_cpu(monkeypatch)
    with pytest.raises(ValueError, match='canonical_existing_TRAIN_life_root'):
        transport.cpu_once(str(alias), journal_id, {}, gate, start=True,
            root_policy=transport.EXISTING_LIFE_CPU_POLICY)
    assert not calls


def test_CPU_dispatch_crash_never_reexecutes(remote, monkeypatch):
    root, journal_id = remote
    chain = records(root, journal_id, '```\nprint(1)\n```')
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256=chain[1]['sha256'])
    calls, gate = fake_cpu(monkeypatch)

    def fail(*args, **kwargs):
        calls.append('interrupted fixture')
        raise RuntimeError('lost process result')

    monkeypatch.setattr(transport.cpu, 'run_request', fail)
    assert transport.cpu_once(str(root), journal_id, origin, gate, start=True)['status'] == 'UNKNOWN_NO_RETRY'
    assert transport.cpu_once(str(root), journal_id, origin, gate, start=True)['status'] == 'UNKNOWN_NO_RETRY'
    assert len(calls) == 1
    assert list((root / 'stream' / 'inbox').glob('*.json')) == []


def test_CPU_publication_ack_loss_reconciles_without_duplicate(remote, monkeypatch):
    root, journal_id = remote
    chain = records(root, journal_id, '```python\nprint(1)\n```')
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256=chain[1]['sha256'])
    calls, gate = fake_cpu(monkeypatch)
    original = transport.console.publish_tool

    def lost(*args):
        original(*args)
        raise RuntimeError('response lost after publication')

    with monkeypatch.context() as patcher:
        patcher.setattr(transport.console, 'publish_tool', lost)
        with pytest.raises(RuntimeError):
            transport.cpu_once(str(root), journal_id, origin, gate, start=True)
    result = transport.cpu_once(str(root), journal_id, origin, gate, start=False)
    assert result['status'] == 'PUBLISHED' and len(calls) == 1
    assert len(list((root / 'stream' / 'inbox').glob('*.json'))) == 1


@pytest.mark.parametrize('source', ['```triton\npass\n```', '```python\nimport triton\n```', '```cuda\nfoo();\n```',
    '```python\nimport torch, triton\n```', '```python\n@triton.jit\ndef add(): pass\n```'])
def test_kernel_never_dualexecutes_in_CPU_path(remote, monkeypatch, source):
    root, journal_id = remote
    chain = records(root, journal_id, source)
    calls, gate = fake_cpu(monkeypatch)
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256=chain[1]['sha256'])
    with pytest.raises(ValueError, match='CPU_only_route'):
        transport.cpu_once(str(root), journal_id, origin, gate, start=True)
    assert calls == []


def test_wrapper_command_is_pinned_and_request_uses_stdin_only(monkeypatch):
    repository = Path(__file__).resolve().parents[1]
    sources = transport.source_pins(repository)
    hosts = {host: dict(repository='/localhome/local-rohing/r153-code',
        wrapper_sha256=exchange.sha((repository / wrapper).read_bytes()), source_sha256=sources,
        gate_sha256='a' * 64) for host, wrapper in transport.WRAPPERS.items() if host in ('a40r', 'ovx2')}
    client = transport.PinnedTransport(repository, hosts)
    captured = []

    def invoke(argv, payload):
        captured.append((argv, payload))
        return {'fixture': True}

    monkeypatch.setattr(transport, 'run_wrapper', invoke)
    request = dict(op='pull', root='/localhome/local-rohing/r153/life', journal_id='a' * 32,
                   cursor=0, head_sha256='0' * 64, max_records=1, max_bytes=4096)
    assert client.call('ovx2', request) == {'fixture': True}
    argv, payload = captured[0]
    assert argv[:2] == ['bash', str(repository / 'gpu/ovx2_ssh.sh')]
    assert json.loads(payload) == request and request['root'] not in argv[2]
    assert 'remote_main' in argv[2] and sources['gpu/orch_r153_community_transport.py'] in argv[2]
    client.hosts['ovx2']['wrapper_sha256'] = 'f' * 64
    with pytest.raises(ValueError, match='trusted_wrapper_changed'):
        client.call('ovx2', request)
    assert len(captured) == 1


def test_remote_dispatch_rejects_unknown_paths_and_fields():
    with pytest.raises(ValueError, match='exact_remote_operation'):
        transport.remote_dispatch(dict(op='shell', command='rm -rf /'))
    with pytest.raises(ValueError, match='new_canonical_R153_life_root'):
        transport.remote_root('/localhome/local-rohing/old-r127/life')


def test_explicit_gate_root_verified_dispatched_and_bound_to_intent(remote, monkeypatch):
    root, journal_id = remote
    chain = records(root, journal_id, '```python\nprint(1)\n```')
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256=chain[1]['sha256'])
    calls, gate = fake_cpu(monkeypatch)
    verified = []
    gate_root = '/localhome/local-rohing/orch_r153_cpu_smoke_20260916t2245z/gate'

    def verify(path):
        verified.append(path)
        return {'fixture_gate': True}

    monkeypatch.setattr(transport.cpu, 'verify_gate', verify)
    request = dict(op='cpu', root=str(root), journal_id=journal_id, origin=origin,
                   gate_sha256=gate, gate_root=gate_root, start=True, artifact_link=None)
    first = transport.remote_dispatch(request)
    assert first['gate_root'] == gate_root
    assert verified == [gate_root] and calls[0]['gate'] == gate_root
    assert transport.remote_dispatch(request) == first and len(calls) == 1
    with pytest.raises(ValueError, match='CPU_intent_conflict'):
        transport.cpu_once(str(root), journal_id, origin, gate, start=True)
    assert len(calls) == 1


@pytest.mark.parametrize('gate_root', ['/tmp/gate', transport.GATE_ROOT + '/../gate',
    transport.GATE_ROOT + '/', transport.GATE_ROOT + '\n', None])
def test_invalid_gate_root_cannot_dispatch(remote, monkeypatch, gate_root):
    root, journal_id = remote
    calls, gate = fake_cpu(monkeypatch)
    with pytest.raises(ValueError, match='pinned_R153_gate_root'):
        transport.cpu_once(str(root), journal_id, {}, gate, gate_root=gate_root, start=True)
    assert not calls


def test_new_gate_hash_mismatch_creates_no_dispatch_intent(remote, monkeypatch):
    root, journal_id = remote
    chain = records(root, journal_id, '```python\nprint(1)\n```')
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256=chain[1]['sha256'])
    calls, unused_gate = fake_cpu(monkeypatch)
    with pytest.raises(ValueError, match='pinned_CPU_gate_changed'):
        transport.cpu_once(str(root), journal_id, origin, 'f' * 64, start=True,
            gate_root='/localhome/local-rohing/orch_r153_cpu_smoke_20260916t2245z/gate')
    assert not calls and not list(root.rglob('INTENT.json'))


def test_ovx3_wrapper_forwards_explicit_host_gate_root(monkeypatch):
    repository = Path(__file__).resolve().parents[1]
    gate_root = '/localhome/local-rohing/orch_r153_cpu_smoke_20260916t2245z/gate'
    hosts = {'ovx3': dict(repository='/localhome/local-rohing/r153-code',
        wrapper_sha256=exchange.sha((repository / transport.WRAPPERS['ovx3']).read_bytes()),
        source_sha256=transport.source_pins(repository), gate_sha256='a' * 64, gate_root=gate_root)}
    captured = []

    def invoke(argv, payload):
        captured.append((argv, json.loads(payload)))
        return {'fixture': True}

    monkeypatch.setattr(transport, 'run_wrapper', invoke)
    client = transport.PinnedTransport(repository, hosts)
    agent = dict(host='ovx3', root='/localhome/local-rohing/orch_r153_C1/life', journal_id='a' * 32)
    assert client.cpu(agent, {}, start=False) == {'fixture': True}
    assert captured[0][0][:2] == ['bash', str(repository / 'gpu/ovx3_ssh.sh')]
    assert captured[0][1]['gate_root'] == gate_root
    del hosts['ovx3']['gate_root']
    with pytest.raises(ValueError):
        transport.PinnedTransport(repository, hosts)
