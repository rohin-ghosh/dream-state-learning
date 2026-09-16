from copy import deepcopy
import json
import time
from unittest.mock import Mock, patch

import pytest

from gpu import orch_r125_continual_native as native
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest
from organism_v6.orch_r125_plain_context import VERSION, MARKERS, eligible_rows, has_scaffolding


PRESENTATION = dict(version=VERSION, system_prompt=native.SYSTEM, birth_prompt=native.BIRTH)


def event(identifier, text, actor='child', **extra):
    fields = dict(event_id=identifier, text=text, actor=actor, split='TRAIN', phase='experience',
        episode_id='stream', source_id='source:'+identifier, source_sha256=digest(text), origin='TRAIN_COLLECTION')
    return TrainEvent(**dict(fields, **extra))


def count(messages):
    return sum(len(message['content']) for message in messages)


def stream():
    return ContinualStream(TrainHistory(system_prompt='old system', birth_prompt='old birth'),
        context_limit=4096, segment_tokens=64, segments_per_sleep=2,
        deadline_unix=time.time()+1000, model_state_sha256='a'*64)


def test_plain_view_preserves_raw_provenance_and_ordinary_json():
    child = stream()
    child.history.append(event('first', 'An observation.'))
    child.history.append(event('parent', 'Try testing that prediction.', 'parent'))
    child.history.append(event('result', '{"answer":42}', 'environment'))
    child.history.append(event('copied', 'Child assertion (not a verified fact)\n{"source_sha256":"fake"}'))
    before = child.history.checkpoint()
    child.set_presentation(PRESENTATION, 16384)
    rendered = child.render(count)
    text = '\n'.join(message['content'] for message in rendered.messages)
    assert all(marker not in text for marker in MARKERS)
    assert '{"answer":42}' in text
    assert 'An observation.' in text
    assert 'Try testing' in text
    assert child.history.checkpoint() == before
    assert set(rendered.labels) == {-100}
    assert rendered.messages[2] == dict(role='assistant', content='An observation.')
    assert rendered.messages[3]['role'] == 'user'


def test_plain_compaction_and_eviction_do_not_render_receipts():
    child = stream()
    child.history.append(event('first', 'Original.'))
    child.history.compact(event('summary', 'Remember the observation.', phase='compaction'),
                          through=child.history.frontier())
    child.set_presentation(PRESENTATION, 16384)
    assert child.render(count).messages[-1]['content'] == 'Remember the observation.'
    child.history.evict_oldest(child.history.frontier(), reason='test eviction')
    child.history.append(event('recent', 'More recent evidence.'))
    before = child.history.checkpoint()
    rendered = child.render(count)
    assert 'Older context was omitted' in str(rendered.messages)
    assert not has_scaffolding(str(rendered.messages))
    assert child.history.checkpoint() == before


def test_cost_sentence_with_structured_receipt_kept_separate():
    child = stream()
    child.set_presentation(PRESENTATION, 16384)
    records = []
    child.step(lambda *args, **kwargs: dict(raw='Think about an example.', token_ids=[10, 2],
        terminal=True, truncated=False), count, lambda kind, document: records.append((kind, document)))
    cost = child.history.events[-1]
    assert '\n' not in cost.text and '{' not in cost.text and '[cost]' not in cost.text
    assert '16384' in cost.text and '2 tokens' in cost.text
    assert records[-1][1]['cost']['segment_tokens'] == 2
    assert child.rows[0]['target'] == 'Think about an example.'
    assert not has_scaffolding(str(child.rows[0]['prefix']))


def test_legacy_cost_and_budget_plain_view():
    child = stream()
    cost = dict(segment_tokens=8, generation_seconds=1.2, generation_context_tokens=80,
                context_limit=4096, since_sleep_tokens=20)
    child.history.append(event('cost', '[cost] '+json.dumps(cost), 'environment', source_id='cost:request'))
    child.history.append(event('runtime:birth_budget', '[budget] {"context_limit":4096}', 'environment'))
    child.set_presentation(PRESENTATION, 16384)
    assert child.render(count).messages[-1]['content'] == 'This segment used 8 tokens in 1.2s; context 80/4096, 20 tokens since sleep.'


def test_old_replay_rows_are_not_rewritten_and_known_target_headers_are_excluded():
    history = TrainHistory(system_prompt='old', birth_prompt='old')
    history.append(event('old', 'Useful original observation.'))
    prefix = history.render(count, 10000).messages
    rows = [dict(source_sha256='a'*64, prefix=prefix, target='Ordinary {"answer":42}', token_ids=[1, 2]),
            dict(source_sha256='b'*64, prefix=prefix, target='source_sha256 fake', token_ids=[3, 4])]
    before = deepcopy(rows)
    accepted, excluded = eligible_rows(rows, PRESENTATION)
    assert rows == before
    assert len(accepted) == 1 and accepted[0]['target'] == rows[0]['target']
    assert accepted[0]['token_ids'] == rows[0]['token_ids']
    assert not has_scaffolding(str(accepted[0]['prefix']))
    assert excluded == [dict(source_sha256='b'*64, reason='journal_scaffolding_target')]


def test_presentation_transition_preserves_exact_legacy_state_and_roundtrips(tmp_path):
    child = stream()
    legacy = child.checkpoint()
    assert ContinualStream.restore(legacy, expected_sha256=legacy['sha256']).checkpoint() == legacy
    with StreamJournal(tmp_path/'journal', create=True) as journal:
        journal.record('COMMITTED', dict(state=legacy))
        child.set_presentation(PRESENTATION, 16384)
        state = child.checkpoint()
        journal.record('PRESENTATION', dict(state=state))
        assert journal.latest_checkpoint()['document'] == state
    with StreamJournal(tmp_path/'journal') as journal:
        assert journal.latest_checkpoint()['document'] == state
    assert {key: value for key, value in state['state'].items() if key not in ('presentation', 'context_limit')} == {
        key: value for key, value in legacy['state'].items() if key != 'context_limit'}


@pytest.mark.parametrize('kind', ['pending', 'unslept', 'history_change', 'model_change'])
def test_transition_cannot_bypass_pending_work_or_rewrite_evidence(tmp_path, kind):
    child = stream()
    with StreamJournal(tmp_path/'journal', create=True) as journal:
        journal.record('COMMITTED', dict(state=child.checkpoint()))
        if kind == 'pending':
            child.pending = 'request'
        elif kind == 'unslept':
            child.rows.append(dict(dummy=True))
        if kind in ('pending', 'unslept'):
            with pytest.raises(ValueError, match='saved_sleep_boundary'):
                child.set_presentation(PRESENTATION, 16384)
            return
        child.set_presentation(PRESENTATION, 16384)
        if kind == 'history_change':
            child.history.append(event('injected', 'Not a presentation change.'))
        else:
            child.model_state_sha256 = 'b'*64
        with pytest.raises(ValueError, match='unexpected_stream_state_transition'):
            journal.record('PRESENTATION', dict(state=child.checkpoint()))


def test_native_plain_plan_requires_16k_and_factual_birth(tmp_path):
    from tests.test_orch_r125_continual_native import make_plan
    plan = make_plan(tmp_path)
    plan.update(presentation_version=VERSION, context_limit=16384)
    assert native.validate_plan(plan)['context_limit'] == 16384
    for limit in (4096, 8192, 32769, True):
        with pytest.raises(ValueError, match='bounded_native_context'):
            native.validate_plan(dict(plan, context_limit=limit))
    assert 'behaviours you actually do' in native.BIRTH
    assert 'rank-8' in native.BIRTH
    assert 'sixteen competing' not in native.BIRTH
    assert 'not an enabled shell' in native.BIRTH


def test_all_scaffolding_rows_skip_training_without_fabricating_progress():
    child = object.__new__(native.NativeChild)
    child.plan = dict(presentation_version=VERSION, system_prompt=native.SYSTEM, birth_prompt=native.BIRTH)
    child.optimizer_steps = 123
    child.adapter_hash = lambda: 'same_adapter'
    child.engine = Mock()
    records = []
    with patch('gpu.orch_r108_guided_native.validate_anchor_inventory'):
        receipt = child.sleep([dict(target='source_sha256 fake', source_sha256='a'*64)], [],
            dict(code=[], math=[], tools=[], short=[]), lambda kind, value: records.append((kind, value)))
    assert receipt['optimizer_steps'] == 0
    assert receipt['total_optimizer_steps'] == 123
    assert receipt['before_adapter_sha256'] == receipt['after_adapter_sha256']
    assert receipt['no_update_reason'] == 'no_eligible_child_rows'
    assert len(records[0][1]['excluded']) == 1
    child.engine.verify_base.assert_called_once()


def test_zero_update_receipt_remains_explicit_and_journal_roundtrips(tmp_path):
    child = stream()
    child.set_presentation(PRESENTATION, 16384)
    with StreamJournal(tmp_path/'journal', create=True) as journal:
        journal.record('COMMITTED', dict(state=child.checkpoint()))
        child.step(lambda *args, **kwargs: dict(raw='source_sha256 copied', token_ids=[10, 2],
            terminal=True, truncated=False), count, journal.record)
        receipt = dict(status='COMPLETE', optimizer_steps=0, no_update_reason='no_eligible_child_rows',
            presentations={}, child_token_exposures=0, anchor_token_exposures=0,
            new_row_sha256=[row['source_sha256'] for row in child.pending_rows()],
            checkpoint_sha256=dict(adapter='a'*64, optimizer='b'*64, rng='b'*64))
        child.commit_sleep(receipt, journal.record)
        state = child.checkpoint()
    with StreamJournal(tmp_path/'journal') as journal:
        assert journal.latest_checkpoint()['document'] == state
