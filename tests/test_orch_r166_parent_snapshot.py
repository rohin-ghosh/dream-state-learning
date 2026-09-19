"""Synthetic CPU-only journals; not delivery or learning evidence for any real life."""

import copy
import json

import pytest

from gpu import orch_r166_parent_snapshot as snapshot
from gpu.orch_r125_stream_journal import StreamJournal, _digest
from gpu.orch_r127_pilot_console import publish_parent
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream


def generate(messages, **kwargs):
    return dict(raw='I checked the actual observation.', token_ids=[10, 2], terminal=True, truncated=False)


def populate(root, count=2):
    root.mkdir()
    with StreamJournal(root/'stream', create=True) as journal:
        stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=20,
            deadline_unix=1000, model_state_sha256='f'*64)
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        publication = publish_parent(root, 'Astra', 'Compare the observation with your prediction.')
        for unused in range(count):
            stream.step(generate, lambda messages: sum(len(message['content'].split())+4 for message in messages), journal.record,
                incoming=journal.read_inbox(), now=lambda: 100)
    return publication


def test_incremental_matches_full_and_publication_is_not_delivery(tmp_path):
    root = tmp_path/'life'
    publication = populate(root)
    first = snapshot.poll(root, max_records=2)
    assert not first['snapshot']['caught_up']
    assert not first['snapshot']['delivered']
    current = first
    while not current['snapshot']['caught_up']:
        current = snapshot.poll(root, current['cursor'], cursor_sha256=current['cursor_sha256'], max_records=2)
    full = snapshot.poll(root)
    assert current['cursor'] == full['cursor']
    assert full['snapshot']['response_count'] == 2
    assert full['snapshot']['delivered'][publication['id']]['request_count'] == 1
    assert full['snapshot']['delivered'][publication['id']]['sleep_count'] == 0
    assert len([event for event in full['snapshot']['events'] if event['actor'] == 'child']) == 2
    idle = snapshot.poll(root, current['cursor'], cursor_sha256=current['cursor_sha256'])
    assert idle['snapshot']['source_bytes'] < full['snapshot']['source_bytes']
    assert idle['snapshot']['new_records'] == 0


def test_megabyte_record_not_one_megabyte_reader_limit(tmp_path):
    root = tmp_path/'life'
    root.mkdir()
    with StreamJournal(root/'stream', create=True) as journal:
        journal.record('CPU_FIXTURE', dict(context='x' * (1024 * 1024 + 50)))
    result = snapshot.poll(root)
    assert result['snapshot']['source_bytes'] > 1024 * 1024
    assert result['snapshot']['caught_up']
    with pytest.raises(ValueError, match='poll_byte_limit'):
        snapshot.poll(root, max_bytes=1024)


@pytest.mark.parametrize('mutation', ['gap', 'digest', 'symlink', 'boundary', 'rewind'])
def test_tamper_and_gaps_refused(tmp_path, mutation):
    root = tmp_path/'life'
    populate(root)
    current = snapshot.poll(root)
    records = sorted((root/'stream'/'records').glob('*.json'))
    if mutation == 'gap':
        records[1].unlink()
    elif mutation == 'rewind':
        records[-1].unlink()
    elif mutation == 'symlink':
        raw = records[-1].read_bytes()
        records[-1].unlink()
        target = tmp_path/'target'
        target.write_bytes(raw)
        records[-1].symlink_to(target)
    else:
        records[-1].write_bytes(records[-1].read_bytes() + b' ')
        if mutation == 'digest':
            value = json.loads(records[-1].read_bytes())
            value['document']['tampered'] = True
            records[-1].write_text(json.dumps(value))
    with pytest.raises((ValueError, OSError)):
        snapshot.poll(root, current['cursor'], cursor_sha256=current['cursor_sha256'])


def test_cursor_authority_and_root_required(tmp_path):
    root = tmp_path/'life'
    populate(root)
    current = snapshot.poll(root)
    cursor = copy.deepcopy(current['cursor'])
    cursor['response_count'] = 999
    with pytest.raises(ValueError, match='trusted_cursor_pin'):
        snapshot.poll(root, cursor, cursor_sha256=current['cursor_sha256'])
    with pytest.raises(ValueError, match='cursor_root'):
        snapshot.poll(tmp_path/'different', current['cursor'], cursor_sha256=current['cursor_sha256'])


@pytest.mark.parametrize('change,reason', [({'split': 'FINAL'}, 'TRAIN'),
    ({'render_receipt': {'all_history_tokens_masked': False}}, 'masked')])
def test_request_visibility_guard(change, reason, tmp_path):
    state = snapshot.genesis(tmp_path/'life')
    request = dict(split='TRAIN', render_receipt={'all_history_tokens_masked': True})
    request.update(change)
    with pytest.raises(ValueError, match=reason):
        snapshot._reduce(state, dict(kind='REQUEST', document=request, index=1, sha256='a'*64))


def test_uncommitted_response_not_exported(tmp_path):
    root = tmp_path/'life'
    populate(root, count=1)
    records = sorted((root/'stream'/'records').glob('*.json'))
    assert json.loads(records[-1].read_bytes())['kind'] == 'COMMITTED'
    records[-1].unlink()
    result = snapshot.poll(root)
    assert result['snapshot']['response_count'] == 0
    assert not any(event['actor'] == 'child' for event in result['snapshot']['events'])
    assert result['cursor']['response'] is not None


def test_disjoint_store_and_exact_reference(tmp_path):
    root = tmp_path/'life'
    populate(root)
    with pytest.raises(ValueError, match='disjoint'):
        snapshot.stored_poll(root, root/'parent')
    result = snapshot.stored_poll(root, tmp_path/'cursor')
    result2 = snapshot.stored_poll(root, tmp_path/'cursor', result['reference'])
    assert result2['snapshot']['new_records'] == 0
    assert result2['reference'] != result['reference']
    result['reference']['sha256'] = '0'*64
    with pytest.raises(ValueError, match='cursor_file_pin'):
        snapshot.stored_poll(root, tmp_path/'cursor', result['reference'])


def test_ambiguous_plain_delivery_refused(tmp_path):
    state = snapshot.genesis(tmp_path/'life')
    for identifier in ('one', 'two'):
        snapshot._reduce(state, dict(kind='INBOX', index=0, sha256='a'*64,
            document=dict(message=dict(id=identifier, actor='parent', split='TRAIN', text='same'),
                          source_id=identifier, source_sha256='a'*64)))
    with pytest.raises(ValueError, match='ambiguous_delivery'):
        snapshot._reduce(state, dict(kind='REQUEST', index=1, sha256='b'*64, document=dict(
            split='TRAIN', segment=1, render_receipt={'all_history_tokens_masked': True}, messages=[
                dict(role='system', content='system'), dict(role='user', content='birth'),
                dict(role='user', content='same')])) )


def test_prior_history_not_reread_or_falsely_reaudited(tmp_path):
    root = tmp_path/'life'
    populate(root)
    result = snapshot.poll(root)
    first = root/'stream'/'records'/'00000000000000000000.json'
    first.write_text('Historical bytes changed after trusted cursor was produced.')
    continued = snapshot.poll(root, result['cursor'], cursor_sha256=result['cursor_sha256'])
    assert continued['snapshot']['new_records'] == 0
    with pytest.raises(ValueError):
        snapshot.poll(root)
