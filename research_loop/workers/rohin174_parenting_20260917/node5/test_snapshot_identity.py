import copy

import pytest

from gpu import orch_r166_parent_snapshot as snapshot
from gpu.orch_r125_stream_journal import _digest
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream
from organism_v6.orch_r125_plain_context import VERSION
from snapshot_identity import exact_visible, install, reconstructed_messages


def fixture(tmp_path):
    state = snapshot.genesis(tmp_path / 'life')
    history = TrainHistory(system_prompt='System.', birth_prompt='Birth.')
    for identifier in ('one', 'two'):
        document = dict(message=dict(id=identifier, actor='parent', split='TRAIN', text='Astra: same'),
                        source_id='/cpu/inbox/' + identifier + '.json', source_sha256=_digest(identifier))
        snapshot._reduce(state, dict(kind='INBOX', document=document, index=1, sha256='a' * 64))
        history.append(TrainEvent(event_id='parent:inbox:' + identifier, actor='parent', text='Astra: same',
            split='TRAIN', phase='experience', episode_id='continual_stream', source_id=document['source_id'],
            source_sha256=document['source_sha256'], origin='TRAIN_COLLECTION'))
        if identifier == 'one':
            history.evict_oldest(history.frontier(), reason='CPU explicit eviction')
    presentation = dict(version=VERSION, system_prompt='System.', birth_prompt='Birth.')
    stream = ContinualStream(history, context_limit=4096, segment_tokens=128, segments_per_sleep=20,
                             deadline_unix=1000, model_state_sha256='f' * 64)
    stream.presentation = presentation
    request = dict(split='TRAIN', segment=0, render_receipt={'all_history_tokens_masked': True},
        messages=reconstructed_messages(history, presentation), history_sha256=_digest(history.checkpoint()))
    stream.pending = _digest(request)
    request['resume_state'] = stream.checkpoint()
    return state, request


def test_exact_saved_history_distinguishes_duplicate_plain_text(tmp_path):
    state, request = fixture(tmp_path)
    visible, ambiguous = snapshot.transcript._visible(request['messages'], state['inbox'])
    assert not visible and ambiguous == {'one', 'two'}
    selected, proof = exact_visible(request, state['inbox'])
    assert selected == {'two'}
    assert proof['token_count_recomputed'] is False and proof['model_calls'] == 0
    assert proof['visible_frontier'] == 1


def test_original_strict_reducer_consumes_only_proven_identity(tmp_path):
    state, request = fixture(tmp_path)
    original = install()
    try:
        snapshot._reduce(state, dict(kind='REQUEST', document=request, index=3, sha256='c' * 64))
        assert set(state['delivered']) == {'two'}
        assert state['request_count'] == 1 and state['response_count'] == 0
        assert state['exact_render_identity']['count'] == 1
        assert snapshot.transcript._visible(request['messages'], state['inbox'])[1] == {'one', 'two'}
    finally:
        snapshot._reduce = original


@pytest.mark.parametrize('mutation', ['checkpoint_hash', 'history_hash', 'request_hash', 'messages', 'source', 'missing', 'masked', 'split'])
def test_incomplete_or_tampered_identity_never_becomes_delivery(tmp_path, mutation):
    state, request = fixture(tmp_path)
    if mutation == 'checkpoint_hash':
        request['resume_state']['sha256'] = '0' * 64
    elif mutation == 'history_hash':
        request['history_sha256'] = '0' * 64
    elif mutation == 'request_hash':
        request['segment'] += 1
    elif mutation == 'messages':
        request['messages'][-1]['content'] += ' altered'
        request['resume_state']['state']['pending'] = _digest({key: value for key, value in request.items() if key != 'resume_state'})
        request['resume_state']['sha256'] = _digest(request['resume_state']['state'])
    elif mutation == 'source':
        state['inbox']['two']['inbox_source_sha256'] = '0' * 64
    elif mutation == 'missing':
        del request['resume_state']
    elif mutation == 'masked':
        request['render_receipt']['all_history_tokens_masked'] = False
    elif mutation == 'split':
        request['split'] = 'FINAL'
    with pytest.raises(ValueError):
        exact_visible(request, state['inbox'])
    assert not state['delivered']


def test_missing_checkpoint_keeps_original_ambiguity_refusal(tmp_path):
    state, request = fixture(tmp_path)
    del request['resume_state']
    original = install()
    try:
        with pytest.raises(ValueError, match='ambiguous_delivery'):
            snapshot._reduce(state, dict(kind='REQUEST', document=request, index=3, sha256='c' * 64))
        assert not state['delivered'] and state['request_count'] == 0
    finally:
        snapshot._reduce = original
