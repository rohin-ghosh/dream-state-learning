from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3

import pytest

from gpu import orch_r153_community_exchange as exchange
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream
from organism_v6.orch_r125_plain_context import VERSION as PLAIN_CONTEXT_VERSION


def make_record(index, kind, document, previous, journal_id):
    record = dict(schema='R125_STREAM_JOURNAL_V1', index=index, kind=kind,
                  document=document, previous_sha256=previous, journal_id=journal_id)
    record['sha256'] = exchange._digest(record)
    return record


def committed(bindings, actor, action, *, index=1, split='TRAIN', raw=None, terminal=True, truncated=False):
    binding = bindings[actor]
    request = make_record(index - 1, 'REQUEST', dict(split=split, resume_state={}), '0' * 64,
                          binding['journal_id'])
    response = make_record(index, 'RESPONSE', dict(request_sha256=exchange._digest(dict(split=split)),
        response=dict(raw=exchange.encoded(action).decode() if raw is None else raw,
                      terminal=terminal, truncated=truncated)), request['sha256'], binding['journal_id'])
    commit = make_record(index + 1, 'COMMITTED', dict(source_sha256=exchange._digest(response['document'])),
                         response['sha256'], binding['journal_id'])
    directory = Path(binding['root']) / 'stream' / 'records'
    for record in (request, response, commit):
        (directory / f'{record["index"]:020d}.json').write_bytes(exchange.encoded(record))
    return dict(kind='TRAIN_CHILD_RESPONSE', record_index=index, record_sha256=response['sha256'])


@pytest.fixture
def configured(tmp_path):
    bindings = {}
    for position, actor in enumerate(exchange.ACTORS, start=1):
        root = tmp_path / actor
        (root / 'stream' / 'records').mkdir(parents=True)
        (root / 'stream' / 'inbox').mkdir()
        (root / 'workspace').mkdir()
        journal_id = f'{position:032x}'
        (root / 'stream' / 'JOURNAL.json').write_bytes(exchange.encoded(
            dict(schema='R125_STREAM_JOURNAL_V1', journal_id=journal_id)))
        bindings[actor] = dict(root=str(root), workspace=str(root / 'workspace'), journal_id=journal_id)
    broker = exchange.CommunityExchange(tmp_path / 'broker', bindings)
    return broker, bindings


def perform(configured, actor, action, index=1):
    broker, bindings = configured
    return broker.apply(actor, committed(bindings, actor, action, index=index), action)


def sql(broker, statement, parameters=()):
    with sqlite3.connect(broker.root / 'state.sqlite3') as database:
        return database.execute(statement, parameters).fetchall()


def test_service_database_has_bounded_headroom_above_old_64mib(configured):
    broker, unused_bindings = configured
    with broker._locked() as database:
        assert database.execute('PRAGMA max_page_count').fetchone()[0] == 131072
        assert database.execute('PRAGMA page_size').fetchone()[0] == 4096
        database.execute('CREATE TABLE headroom_test (payload BLOB)')
        database.execute('INSERT INTO headroom_test VALUES (zeroblob(?))', (65 * 1024 * 1024,))
        assert database.execute('PRAGMA page_count').fetchone()[0] > 16384
        database.rollback()


def inbox(bindings, actor):
    return Path(bindings[actor]['root']) / 'stream' / 'inbox'


def test_publication_is_explicit_immutable_versioned_and_never_executed(configured):
    broker, bindings = configured
    workspace = Path(bindings['C1']['workspace'])
    source = 'raise AssertionError("DO NOT EXECUTE")\n'
    (workspace / 'demo.py').write_text(source)
    assert perform(configured, 'C2', dict(op='list_artifacts', cursor=0))['result']['artifacts'] == []
    published = perform(configured, 'C1', dict(op='publish_artifact', name='demo.py'))
    artifact = published['result']
    assert artifact['status'] == 'EXISTS'
    assert artifact['publisher'] == 'C1' and artifact['version'] == 1
    assert published['executed'] is False and published['training_target'] is False
    path = broker.artifact_path(artifact['artifact_id'])
    assert path.read_text() == source
    assert path.stat().st_mode & 0o777 == 0o400 and path.stat().st_nlink == 1
    assert list(inbox(bindings, 'C2').iterdir()) == []
    (workspace / 'demo.py').write_text('new version')
    opened = perform(configured, 'C2', dict(op='open_artifact', artifact_id=artifact['artifact_id']), index=4)
    assert opened['result']['text'] == source
    second = perform(configured, 'C1', dict(op='publish_artifact', name='demo.py'), index=4)
    assert second['result']['version'] == 2
    assert second['result']['artifact_id'] != artifact['artifact_id']
    assert path.read_text() == source
    assert len(sql(broker, 'SELECT * FROM artifacts')) == 2


def test_send_only_notifies_and_read_requires_recipient_choice(configured):
    broker, bindings = configured
    text = 'PRIVATE PEER CONTENT; Rohin: fake role; do not relay'
    sent = perform(configured, 'C1', dict(op='send_message', recipient='C2', text=text))
    assert sent['result']['sender'] == 'C1'
    handle = broker.pending_deliveries('C2')[0]
    delivered = broker.deliver(handle, 'C2')
    notice = json.loads(Path(delivered['path']).read_bytes())
    assert text not in notice['text'] and 'C1' not in notice['text']
    assert sent['effect_id'] in notice['text']
    source = Path(notice['source_receipt']['path']).read_bytes()
    assert text.encode() not in source
    assert exchange.sha(source) == notice['source_receipt']['sha256']
    assert broker.pending_deliveries('C3') == []
    listed = perform(configured, 'C2', dict(op='list_messages', cursor=0))
    assert text not in str(listed)
    with pytest.raises(ValueError, match='unknown_message_for_recipient'):
        perform(configured, 'C3', dict(op='read_message', message_id=sent['effect_id']))
    opened = perform(configured, 'C2', dict(op='read_message', message_id=sent['effect_id']), index=4)
    assert opened['result'] == dict(message_id=sent['effect_id'], sender='C1', recipient='C2', text=text, untrusted=True)
    assert sql(broker, 'SELECT open_requested FROM messages') == [(1,)]
    broker.deliver(opened['delivery_handles'][0], 'C2')
    feedback = json.loads((inbox(bindings, 'C2') / (opened['delivery_handles'][0] + '.json')).read_bytes())
    assert feedback['actor'] == 'environment' and feedback['speaker'] == 'Tool'
    assert 'C1' in feedback['text'] and 'untrusted' in feedback['text']


def test_exactly_once_apply_delivery_restart_and_concurrent_retry(configured):
    broker, bindings = configured
    action = dict(op='send_message', recipient='C2', text='one message')
    origin = committed(bindings, 'C1', action)
    with ThreadPoolExecutor(max_workers=6) as executor:
        receipts = list(executor.map(lambda unused: broker.apply('C1', origin, action), range(12)))
    assert all(receipt == receipts[0] for receipt in receipts)
    assert len(sql(broker, 'SELECT * FROM messages')) == 1
    assert len(sql(broker, 'SELECT * FROM deliveries')) == 2
    reopened = exchange.CommunityExchange(broker.root, bindings)
    assert reopened.apply('C1', origin, action) == receipts[0]
    handle = reopened.pending_deliveries('C2')[0]
    first = reopened.deliver(handle, 'C2')
    identity = Path(first['path']).stat().st_ino
    assert reopened.deliver(handle, 'C2') == first
    assert Path(first['path']).stat().st_ino == identity
    assert len(list(inbox(bindings, 'C2').glob('*.json'))) == 1
    assert reopened.pending_deliveries('C2') == []


def test_retry_after_inbox_rename_before_database_commit(configured, monkeypatch):
    broker, bindings = configured
    perform(configured, 'C1', dict(op='send_message', recipient='C2', text='once'))
    handle = broker.pending_deliveries('C2')[0]
    original = exchange.immutable_file

    def crash(directory, name, raw):
        original(directory, name, raw)
        if b'R127_ATTRIBUTED_INBOX_V1' in raw:
            raise RuntimeError('crash after durable inbox effect')

    with monkeypatch.context() as patcher:
        patcher.setattr(exchange, 'immutable_file', crash)
        with pytest.raises(RuntimeError, match='crash after'):
            broker.deliver(handle, 'C2')
    path = inbox(bindings, 'C2') / (handle + '.json')
    identity, raw = path.stat().st_ino, path.read_bytes()
    reopened = exchange.CommunityExchange(broker.root, bindings)
    assert reopened.pending_deliveries('C2') == [handle]
    reopened.deliver(handle, 'C2')
    assert path.stat().st_ino == identity and path.read_bytes() == raw
    assert reopened.pending_deliveries('C2') == []


def test_retry_after_committed_publication_uses_original_snapshot(configured, monkeypatch):
    broker, bindings = configured
    workspace = Path(bindings['C1']['workspace'])
    (workspace / 'note.txt').write_text('original snapshot')
    action = dict(op='publish_artifact', name='note.txt')
    origin = committed(bindings, 'C1', action)
    with monkeypatch.context() as patcher:
        patcher.setattr(broker, '_artifact_file', lambda *args: (_ for unused in ()).throw(RuntimeError('crash')))
        with pytest.raises(RuntimeError, match='crash'):
            broker.apply('C1', origin, action)
    (workspace / 'note.txt').write_text('later mutable bytes')
    reopened = exchange.CommunityExchange(broker.root, bindings)
    receipt = reopened.apply('C1', origin, action)
    assert reopened.artifact_path(receipt['result']['artifact_id']).read_text() == 'original snapshot'
    assert len(sql(broker, 'SELECT * FROM artifacts')) == 1


@pytest.mark.parametrize('name', ['../C2/item.txt', '/etc/passwd', 'sub/item.txt', '.env', 'x..y',
    'sealed.txt', 'readout.json', 'credentials.json', 'api_token.txt', 'private.pem', 'final.txt',
    'benchmark.txt', 'ssh-key.txt', '', 'nul\0name'])
def test_host_reserved_and_nested_paths_denied(configured, name):
    with pytest.raises(ValueError):
        perform(configured, 'C1', dict(op='publish_artifact', name=name))


@pytest.mark.parametrize('kind', ['symlink', 'hardlink', 'fifo', 'directory', 'oversize', 'binary', 'nul'])
def test_unsafe_workspace_inputs_denied(configured, kind, tmp_path):
    broker, bindings = configured
    name = Path(bindings['C1']['workspace']) / 'payload.txt'
    foreign = tmp_path / 'foreign.txt'
    foreign.write_text('outside workspace')
    if kind == 'symlink':
        name.symlink_to(foreign)
    elif kind == 'hardlink':
        os.link(foreign, name)
    elif kind == 'fifo':
        os.mkfifo(name)
    elif kind == 'directory':
        name.mkdir()
    else:
        name.write_bytes({'oversize': b'a' * (exchange.ARTIFACT_LIMIT + 1),
                          'binary': b'\xff', 'nul': b'\0'}[kind])
    with pytest.raises((ValueError, OSError)):
        perform(configured, 'C1', dict(op='publish_artifact', name='payload.txt'))
    assert sql(broker, 'SELECT * FROM artifacts') == []
    assert broker.pending_deliveries('C1') == []


def test_workspace_listing_and_read_only_own_flat_files(configured):
    broker, bindings = configured
    for actor in ('C1', 'C2'):
        (Path(bindings[actor]['workspace']) / 'note.txt').write_text(actor)
    workspace = Path(bindings['C1']['workspace'])
    (workspace / 'sealed.txt').write_text('not admissible')
    (workspace / 'alias.txt').symlink_to(Path(bindings['C2']['workspace']) / 'note.txt')
    assert perform(configured, 'C1', dict(op='list_workspace', cursor=0))['result']['names'] == ['note.txt']
    assert perform(configured, 'C1', dict(op='read_workspace', name='note.txt'), index=4)['result']['text'] == 'C1'
    assert sql(broker, 'SELECT * FROM artifacts') == []
    assert broker.pending_deliveries('C2') == []


@pytest.mark.parametrize('split', ['DEV', 'FINAL', 'READOUT'])
def test_non_train_origin_rejected(configured, split):
    broker, bindings = configured
    action = dict(op='list_workspace', cursor=0)
    origin = committed(bindings, 'C1', action, split=split)
    with pytest.raises(ValueError, match='TRAIN_request_response_commit_join'):
        broker.apply('C1', origin, action)


@pytest.mark.parametrize('change', ['actor', 'origin_hash', 'record_hash', 'commit_missing', 'commit_join',
                                    'request_join', 'journal', 'raw_mismatch', 'truncated', 'incomplete'])
def test_origin_chain_and_actor_forgery_rejected(configured, change):
    broker, bindings = configured
    action = dict(op='list_workspace', cursor=0)
    origin = committed(bindings, 'C1', action, terminal=change != 'incomplete', truncated=change == 'truncated')
    actor = 'C2' if change == 'actor' else 'C1'
    records = Path(bindings['C1']['root']) / 'stream' / 'records'
    if change == 'origin_hash':
        origin['record_sha256'] = 'f' * 64
    elif change == 'raw_mismatch':
        action = dict(op='list_artifacts', cursor=0)
    elif change == 'commit_missing':
        (records / f'{2:020d}.json').unlink()
    elif change in ('commit_join', 'request_join', 'journal', 'record_hash'):
        position = 2 if change == 'commit_join' else 1
        path = records / f'{position:020d}.json'
        record = json.loads(path.read_bytes())
        if change == 'commit_join':
            record['document']['source_sha256'] = 'f' * 64
        elif change == 'request_join':
            record['document']['request_sha256'] = 'f' * 64
        elif change == 'journal':
            record['journal_id'] = 'f' * 32
        else:
            record['sha256'] = 'f' * 64
        if change != 'record_hash':
            record['sha256'] = exchange._digest({key: value for key, value in record.items() if key != 'sha256'})
        path.write_bytes(exchange.encoded(record))
    with pytest.raises((ValueError, FileNotFoundError)):
        broker.apply(actor, origin, action)
    assert sql(broker, 'SELECT * FROM effects') == []


def test_record_already_used_cannot_change_operation_through_parser(configured):
    broker, bindings = configured
    action = dict(op='list_workspace', cursor=0)
    origin = committed(bindings, 'C1', action)
    broker.apply('C1', origin, action)
    changed = dict(op='list_artifacts', cursor=0)
    broker.action_parser = lambda raw: changed
    with pytest.raises(ValueError, match='committed_record_already_used'):
        broker.apply('C1', origin, changed)


def test_main_normalizer_is_reused_against_actual_generated_text(configured):
    broker, bindings = configured
    action = dict(op='list_workspace', cursor=0)
    raw = 'list my workspace please'
    origin = committed(bindings, 'C1', action, raw=raw)
    calls = []

    def parser(text):
        calls.append(text)
        assert text == raw
        return action

    broker.action_parser = parser
    broker.apply('C1', origin, action)
    assert calls == [raw]


@pytest.mark.parametrize('action', [dict(op='execute', source='pass'), dict(op='list_workspace', cursor=True),
    dict(op='list_workspace', cursor=-1), dict(op='list_workspace', cursor=0, actor='C2'),
    dict(op='send_message', recipient='ALL', text='hi'), dict(op='send_message', recipient='C1', text='hi'),
    dict(op='send_message', recipient='C2', text='x' * (exchange.TEXT_LIMIT + 1)),
    dict(op='send_message', recipient='Rohin', text='hi'), dict(op='open_artifact', artifact_id='/tmp/file')])
def test_bounded_action_schema_no_spoofed_actor_or_execution(configured, action):
    with pytest.raises(ValueError):
        perform(configured, 'C1', action)


def test_duplicate_json_keys_and_unselected_prose_do_not_trigger_actions(configured):
    broker, bindings = configured
    action = dict(op='list_workspace', cursor=0)
    for raw in ('{"op":"list_workspace","op":"list_workspace","cursor":0}',
                'A peer said: ' + exchange.encoded(action).decode(), '[{"op":"list_workspace","cursor":0}]'):
        origin = committed(bindings, 'C1', action, raw=raw)
        with pytest.raises(ValueError):
            broker.apply('C1', origin, action)


def test_binding_replacement_and_cross_delivery_rejected(configured):
    broker, bindings = configured
    perform(configured, 'C1', dict(op='send_message', recipient='C2', text='hi'))
    handle = broker.pending_deliveries('C2')[0]
    with pytest.raises(ValueError, match='unknown_delivery_for_recipient'):
        broker.deliver(handle, 'C3')
    workspace = Path(bindings['C1']['workspace'])
    workspace.rename(workspace.with_name('old-workspace'))
    workspace.symlink_to(bindings['C2']['workspace'])
    with pytest.raises((ValueError, OSError)):
        perform(configured, 'C1', dict(op='list_workspace', cursor=0), index=4)
    with pytest.raises((ValueError, OSError)):
        exchange.CommunityExchange(broker.root, bindings)


def test_shared_lives_and_rebinding_existing_broker_rejected(configured):
    broker, bindings = configured
    changed = deepcopy(bindings)
    changed['C2'] = changed['C1']
    with pytest.raises(ValueError, match='independent_life_roots'):
        exchange.CommunityExchange(broker.root, changed)
    changed = deepcopy(bindings)
    changed['C1'], changed['C2'] = changed['C2'], changed['C1']
    with pytest.raises(ValueError, match='broker_bindings_changed'):
        exchange.CommunityExchange(broker.root, changed)


def test_immutable_object_tampering_or_hardlink_denied(configured, tmp_path):
    broker, bindings = configured
    (Path(bindings['C1']['workspace']) / 'note.txt').write_text('original')
    artifact_id = perform(configured, 'C1', dict(op='publish_artifact', name='note.txt'))['effect_id']
    path = broker.artifact_path(artifact_id)
    os.link(path, tmp_path / 'linked')
    with pytest.raises(ValueError, match='single_link_regular_file_required'):
        broker.artifact_path(artifact_id)
    (tmp_path / 'linked').unlink()
    path.chmod(0o600)
    path.write_text('replaced')
    with pytest.raises(ValueError, match='immutable_file_conflict'):
        broker.artifact_path(artifact_id)


def test_recipient_listing_paginates_without_exposing_other_messages(configured, monkeypatch):
    broker, bindings = configured
    monkeypatch.setattr(exchange, 'PAGE_SIZE', 2)
    for number in range(4):
        perform(configured, 'C1', dict(op='send_message', recipient='C2' if number != 1 else 'C3',
                                     text=f'message {number}'), index=number * 3 + 1)
    first = perform(configured, 'C2', dict(op='list_messages', cursor=0))['result']
    second = perform(configured, 'C2', dict(op='list_messages', cursor=first['next_cursor']), index=4)['result']
    assert [message['sequence'] for message in first['messages'] + second['messages']] == [1, 2, 3]
    assert second['next_cursor'] is None
    assert 'text' not in str(first) and 'C3' not in str(first)
    assert len(broker.pending_deliveries('C2')) == 2


def test_quotas_are_per_actor_and_duplicate_does_not_consume_quota(configured, monkeypatch):
    broker, bindings = configured
    monkeypatch.setattr(exchange, 'EFFECTS_PER_ACTOR', 1)
    action = dict(op='list_workspace', cursor=0)
    origin = committed(bindings, 'C1', action)
    first = broker.apply('C1', origin, action)
    assert broker.apply('C1', origin, action) == first
    with pytest.raises(ValueError, match='actor_effect_quota'):
        perform(configured, 'C1', action, index=4)
    assert perform(configured, 'C2', action)['actor'] == 'C2'


def test_existing_journal_inbox_integration_only_child_generated_targets(configured):
    broker, bindings = configured
    recipient = Path(bindings['C2']['root'])
    original_stream = recipient / 'stream'
    original_stream.rename(recipient / 'fixture-stream')
    with StreamJournal(original_stream, create=True) as journal:
        bindings['C2']['journal_id'] = json.loads((original_stream / 'JOURNAL.json').read_bytes())['journal_id']
        broker = exchange.CommunityExchange(broker.root.with_name('integration-broker'), bindings)
        action = dict(op='send_message', recipient='C2', text='unrequested peer content')
        broker.apply('C1', committed(bindings, 'C1', action), action)
        broker.deliver(broker.pending_deliveries('C2')[0], 'C2')
        events = journal.read_inbox()
        assert len(events) == 1 and events[0].actor == 'environment'
        assert events[0].split == 'TRAIN' and events[0].text.startswith('Tool: ')
        assert 'unrequested peer content' not in events[0].text
        stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=2,
            deadline_unix=1000, model_state_sha256='f' * 64)
        stream.set_presentation(dict(version=PLAIN_CONTEXT_VERSION, system_prompt='System.', birth_prompt='Birth.'), 16384)
        generated = 'My own independent continuation.'

        def generate(messages, **kwargs):
            return dict(raw=generated, token_ids=[10, 2], terminal=True, truncated=False)

        stream.step(generate, lambda messages: sum(len(message['content'].split()) + 4 for message in messages),
                    journal.record, incoming=events, now=lambda: 100)
        assert len(stream.rows) == 1
        assert stream.rows[0]['actor'] == 'child'
        assert stream.rows[0]['prefix_loss'] is False and stream.rows[0]['target_loss'] is True
        assert generated in str(stream.rows[0])
        assert journal.read_inbox() == events


def test_durable_workspace_write_versions_private_until_publish(configured):
    broker, bindings = configured
    first_action = dict(op='write_workspace', name='program.py', text='print("first longer revision")')
    origin = committed(bindings, 'C1', first_action)
    first = broker.apply('C1', origin, first_action)
    assert first['result']['status'] == 'EXISTS' and first['result']['published'] is False
    assert first['result']['sha256'] == exchange.sha(first_action['text'].encode())
    assert first['result']['version'] == 1
    workspace = Path(bindings['C1']['workspace'])
    assert (workspace / 'program.py').read_text() == first_action['text']
    assert sql(broker, 'SELECT * FROM artifacts') == []
    assert broker.pending_deliveries('C2') == []
    second_action = dict(op='write_workspace', name='program.py', text='print(2)')
    second = perform(configured, 'C1', second_action, index=4)
    assert second['result']['version'] == 2
    assert (workspace / 'program.py').read_text() == 'print(2)'
    assert broker.apply('C1', origin, first_action) == first
    assert (workspace / 'program.py').read_text() == 'print(2)'
    assert len(sql(broker, 'SELECT * FROM notes')) == 2
    reopened = exchange.CommunityExchange(broker.root, bindings)
    action = dict(op='publish_artifact', name='program.py')
    published = reopened.apply('C1', committed(bindings, 'C1', action, index=7), action)
    assert reopened.artifact_path(published['effect_id']).read_text() == 'print(2)'
    assert published['result']['sha256'] == second['result']['sha256']


def test_workspace_write_retry_after_durable_commit_and_before_file(configured, monkeypatch):
    broker, bindings = configured
    action = dict(op='write_workspace', name='note.txt', text='durable state')
    origin = committed(bindings, 'C1', action)
    with monkeypatch.context() as patcher:
        patcher.setattr(broker, '_workspace_current', lambda *args: (_ for unused in ()).throw(RuntimeError('crash')))
        with pytest.raises(RuntimeError, match='crash'):
            broker.apply('C1', origin, action)
    assert len(sql(broker, 'SELECT * FROM notes')) == 1
    assert not (Path(bindings['C1']['workspace']) / 'note.txt').exists()
    reopened = exchange.CommunityExchange(broker.root, bindings)
    handle = reopened.pending_deliveries('C1')[0]
    packet = reopened.export_delivery(handle, 'C1')
    assert packet['source']['result']['status'] == 'EXISTS'
    assert (Path(bindings['C1']['workspace']) / 'note.txt').read_text() == 'durable state'
    reopened.apply('C1', origin, action)
    assert len(sql(broker, 'SELECT * FROM notes')) == 1


def test_workspace_write_does_not_overwrite_unmanaged_data(configured):
    broker, bindings = configured
    path = Path(bindings['C1']['workspace']) / 'existing.txt'
    path.write_text('preserve prior work')
    with pytest.raises(ValueError, match='unmanaged_workspace_file_not_overwritten'):
        perform(configured, 'C1', dict(op='write_workspace', name='existing.txt', text='replacement'))
    assert path.read_text() == 'preserve prior work'
    assert sql(broker, 'SELECT * FROM notes') == []


def test_workspace_utf8_byte_quota_and_revision_quota(configured, monkeypatch):
    broker, bindings = configured
    with pytest.raises(ValueError, match='bounded_text'):
        perform(configured, 'C1', dict(op='write_workspace', name='note.txt', text='é' * exchange.ARTIFACT_LIMIT))
    monkeypatch.setattr(exchange, 'ARTIFACTS_PER_ACTOR', 1)
    perform(configured, 'C1', dict(op='write_workspace', name='note.txt', text='first'), index=4)
    with pytest.raises(ValueError, match='actor_workspace_quota'):
        perform(configured, 'C1', dict(op='write_workspace', name='note.txt', text='second'), index=7)
    assert (Path(bindings['C1']['workspace']) / 'note.txt').read_text() == 'first'


def snapshot_for(bindings, actor, origin):
    stream = Path(bindings[actor]['root']) / 'stream'
    return dict(manifest=json.loads((stream / 'JOURNAL.json').read_bytes()), records=[
        json.loads((stream / 'records' / f'{number:020d}.json').read_bytes())
        for number in (origin['record_index'] - 1, origin['record_index'], origin['record_index'] + 1)])


def test_pure_remote_snapshot_import_is_actor_pinned_and_resumable(configured, tmp_path):
    broker, bindings = configured
    action = dict(op='write_workspace', name='remote.txt', text='from ovx2')
    origin = committed(bindings, 'C4', action)
    snapshot = snapshot_for(bindings, 'C4', origin)
    mirror_bindings = deepcopy(bindings)
    mirror = tmp_path / 'C4-central-mirror'
    (mirror / 'stream' / 'records').mkdir(parents=True)
    (mirror / 'stream' / 'inbox').mkdir()
    (mirror / 'workspace').mkdir()
    (mirror / 'stream' / 'JOURNAL.json').write_bytes(exchange.encoded(snapshot['manifest']))
    mirror_bindings['C4'] = dict(root=str(mirror), workspace=str(mirror / 'workspace'),
                                 journal_id=bindings['C4']['journal_id'])
    central = exchange.CommunityExchange(tmp_path / 'central-broker', mirror_bindings)
    proof = exchange.verify_snapshot('C4', bindings['C4']['journal_id'], origin, snapshot, action)
    assert proof['actor'] == 'C4'
    with pytest.raises(ValueError, match='pinned_snapshot_journal'):
        central.apply_snapshot('C3', snapshot, action)
    receipt = central.apply_snapshot('C4', snapshot, action)
    assert central.apply_snapshot('C4', snapshot, action) == receipt
    assert (mirror / 'workspace' / 'remote.txt').read_text() == 'from ovx2'
    assert not (Path(bindings['C4']['workspace']) / 'remote.txt').exists()
    assert len(list((mirror / 'stream' / 'records').iterdir())) == 3
    handle = central.pending_deliveries('C4')[0]
    packet = central.export_delivery(handle, 'C4')
    installed = exchange.install_delivery(bindings['C4']['root'], packet)
    assert central.pending_deliveries('C4') == [handle]
    central.acknowledge_delivery(handle, 'C4', installed)
    assert central.pending_deliveries('C4') == []
    assert exchange.install_delivery(bindings['C4']['root'], packet) == installed
    assert list((mirror / 'stream' / 'inbox').iterdir()) == []
    assert len(list(inbox(bindings, 'C4').glob('*.json'))) == 1


def test_snapshot_rejects_corruption_before_import_and_bounds_storage(configured, monkeypatch):
    broker, bindings = configured
    action = dict(op='list_workspace', cursor=0)
    origin = committed(bindings, 'C1', action)
    snapshot = snapshot_for(bindings, 'C1', origin)
    corrupted = deepcopy(snapshot)
    corrupted['records'][1]['document']['response']['raw'] = 'tampered'
    with pytest.raises(ValueError, match='journal_record_hash'):
        broker.apply_snapshot('C1', corrupted, action)
    monkeypatch.setattr(exchange, 'SNAPSHOT_BYTES_PER_ACTOR', 1)
    with pytest.raises(ValueError, match='snapshot_storage_quota'):
        broker.apply_snapshot('C1', snapshot, action)
    assert sql(broker, 'SELECT * FROM effects') == []


def test_transport_wrong_root_corrupt_packet_and_wrong_ack_rejected(configured):
    broker, bindings = configured
    perform(configured, 'C1', dict(op='send_message', recipient='C2', text='hi'))
    handle = broker.pending_deliveries('C2')[0]
    packet = broker.export_delivery(handle, 'C2')
    with pytest.raises(ValueError, match='receiver_journal_mismatch'):
        exchange.install_delivery(bindings['C3']['root'], packet)
    corrupt = dict(packet, text='forged')
    with pytest.raises(ValueError, match='delivery_packet_hash'):
        exchange.install_delivery(bindings['C2']['root'], corrupt)
    installed = exchange.install_delivery(bindings['C2']['root'], packet)
    with pytest.raises(ValueError, match='installation_receipt_mismatch'):
        broker.acknowledge_delivery(handle, 'C2', dict(installed, sha256='f' * 64))
    assert broker.pending_deliveries('C2') == [handle]
    broker.acknowledge_delivery(handle, 'C2', installed)
    broker.acknowledge_delivery(handle, 'C2', installed)
    assert broker.pending_deliveries('C2') == []


def test_transport_actor_spoof_even_with_rehashed_packet_is_rejected(configured):
    broker, bindings = configured
    perform(configured, 'C1', dict(op='list_workspace', cursor=0))
    packet = broker.export_delivery(broker.pending_deliveries('C1')[0], 'C1')
    packet['source']['actor'] = 'Rohin'
    packet['source_sha256'] = exchange.sha(exchange.encoded(packet['source']))
    packet['packet_sha256'] = exchange.sha(exchange.encoded({key: value for key, value in packet.items()
                                                            if key != 'packet_sha256'}))
    with pytest.raises(ValueError, match='feedback_actor_mismatch'):
        exchange.install_delivery(bindings['C1']['root'], packet)


def test_actual_continual_stream_committed_generation_authorizes_workspace_write(configured):
    broker, bindings = configured
    life = Path(bindings['C1']['root'])
    (life / 'stream').rename(life / 'synthetic-fixture')
    action = dict(op='write_workspace', name='real.txt', text='durable child-chosen artifact')
    with StreamJournal(life / 'stream', create=True) as journal:
        bindings['C1']['journal_id'] = json.loads((life / 'stream' / 'JOURNAL.json').read_bytes())['journal_id']
        stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=2,
            deadline_unix=1000, model_state_sha256='f' * 64)

        def generate(messages, **kwargs):
            return dict(raw=exchange.encoded(action).decode(), token_ids=[10, 2], terminal=True, truncated=False)

        stream.step(generate, lambda messages: sum(len(message['content'].split()) + 4 for message in messages),
                    journal.record, now=lambda: 100)
        records = [json.loads(path.read_bytes()) for path in sorted((life / 'stream' / 'records').glob('*.json'))]
        response = next(record for record in records if record.get('kind') == 'RESPONSE')
        origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=response['index'], record_sha256=response['sha256'])
        actual = exchange.CommunityExchange(broker.root.with_name('actual-broker'), bindings)
        receipt = actual.apply('C1', origin, action)
        assert receipt['result']['status'] == 'EXISTS'
        assert (life / 'workspace' / 'real.txt').read_text() == action['text']
        actual.deliver(actual.pending_deliveries('C1')[0], 'C1')
        assert journal.read_inbox()[0].actor == 'environment'
