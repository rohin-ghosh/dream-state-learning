import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

import pytest

from gpu.ny_caption_life import extract_batches, latest_own_think, child_act
from gpu.ny_caption_life_service import LifeSession
from gpu.orch_r125_stream_journal import _digest


SCENES = [dict(contest_id='opaque-a', name='crib', canonical_scene='Two adults beside a crib.'),
          dict(contest_id='opaque-b', name='windmill', canonical_scene='A meeting in a tilted windmill.')]


def test_actual_routing_shape_two_literals_not_closing_commentary():
    raw = 'Here are two captions for Scene1:\nCaption: First literal ９８， joke.\nCaption: Second literal.\nThese captions should work well.'
    actions, metrics = extract_batches(raw, SCENES)
    assert actions[0]['captions'] == ['First literal ９８， joke.', 'Second literal.']
    assert metrics['recovered_count'] == 2 and metrics['declared_count'] is None
    assert metrics['unparsed_lines'][0]['reason'] == 'commentary_not_caption'
    assert not metrics['clarification_needed']
    for source, caption in zip(metrics['caption_sources'], actions[0]['captions']):
        assert raw[source['start']:source['end']] == caption
        assert source['text_sha256'] == hashlib.sha256(caption.encode()).hexdigest()


def test_named_numbered_multiple_scenes_no_required_fields_or_count():
    raw = 'For the crib:\n"First joke."\nScene ２:\n- Second joke.\n- Third joke.'
    actions, metrics = extract_batches(raw, SCENES)
    assert [action['contest_id'] for action in actions] == ['opaque-a', 'opaque-b']
    assert actions[1]['captions'] == ['Second joke.', 'Third joke.']
    assert metrics['recovered_count'] == 3 and not metrics['planned_count_required']
    assert not metrics['format_fault']


def test_bare_literal_caption_under_named_scene_is_valid():
    actions, metrics = extract_batches('Windmill:\nThe meeting finally has a spin cycle.', SCENES)
    assert actions[0]['captions'] == ['The meeting finally has a spin cycle.']
    assert not metrics['format_fault']


def test_optional_incorrect_count_does_not_gate_game():
    actions, metrics = extract_batches('Scene: 1\nCount: 6\nCaption: Just one actual joke.', SCENES)
    assert len(actions[0]['captions']) == 1 and metrics['declared_count'] == 6
    assert not metrics['clarification_needed']


def test_scene_without_space_inline_caption_keeps_exact_span():
    raw = 'Scene1: "No fields necessary."'
    actions, metrics = extract_batches(raw, SCENES)
    assert actions[0]['captions'] == ['No fields necessary.']
    source = metrics['caption_sources'][0]
    assert raw[source['start']:source['end']] == 'No fields necessary.'


def test_mixed_labelled_bare_and_quoted_dialogue_are_not_format_gated():
    actions, metrics = extract_batches('Captions for the crib:\nCaption: First.\nSecond.\n'
        'For Scene2 — "I think this is a real joke."', SCENES)
    assert actions[0]['captions'] == ['First.', 'Second.']
    assert actions[1]['captions'] == ['I think this is a real joke.']
    assert not metrics['clarification_needed']


def test_unknown_named_scene_does_not_inherit_previous_scene():
    actions, metrics = extract_batches('Crib:\nCaption: Known.\nFor an unknown scene:\nCaption: Not routed.', SCENES)
    assert actions[0]['captions'] == ['Known.'] and metrics['clarification_needed']


def test_feedback_sources_match_after_interleaved_scene_grouping(tmp_path):
    raw = 'Crib:\nCaption: First.\nWindmill:\nCaption: Second.\nCrib:\nCaption: Third.'
    session = LifeSession(Game(), tmp_path, tmp_path / 'service', SCENES)
    with patch('gpu.ny_caption_life_service.child_act', return_value=raw):
        report = session.process(dict(origin=dict(kind='TRAIN_CHILD_RESPONSE', record_index=1,
            record_sha256='a'*64), metrics=dict(THINK=1, ACT=1, LEARN=0)))['report']
    assert [item['caption_source_index'] for item in report['feedback']] == [0, 2, 1]


def test_many_unparsed_lines_return_bounded_diagnostics():
    actions, metrics = extract_batches(('Question: what now?\n')*2000, SCENES)
    assert not actions and len(metrics['unparsed_lines']) == 32
    assert metrics['unparsed_line_count'] == 2000


@pytest.mark.parametrize('previous_count,total', [(None, 100), (1, 23), (2, 17)])
def test_freeform_count_never_dropped_by_legacy_growth_gate(tmp_path, previous_count, total):
    game = Game()
    session = LifeSession(game, tmp_path, tmp_path / 'service', SCENES)
    if previous_count:
        session.policy.previous['opaque-a'] = dict(count=previous_count, direction='old')
    raw = 'Scene1:\n' + '\n'.join(f'Caption: Actual joke {ordinal}.' for ordinal in range(total))
    with patch('gpu.ny_caption_life_service.child_act', return_value=raw):
        report = session.process(dict(origin=dict(kind='TRAIN_CHILD_RESPONSE', record_index=1,
            record_sha256='a'*64), metrics=dict(THINK=5, ACT=20, LEARN=0)))['report']
    assert len(game.received) == total == len(report['feedback'])
    assert report['ok'] and report['not_dispatched_count'] == 0
    assert all(batch['ok'] for batch in report['batch_reports'])
    assert [item['caption_source_index'] for item in report['feedback']] == list(range(total))


def test_question_and_unknown_scene_clarify_instead_of_inventing_caption():
    actions, metrics = extract_batches('Scene: 999\nCaption: Unknown.\nHow does the judge rank captions?', SCENES)
    assert not actions and metrics['clarification_needed']
    assert any(item['reason'] == 'question_for_next_input' for item in metrics['unparsed_lines'])


def test_ambiguous_scene_name_not_guessed_and_code_never_executed(tmp_path):
    scenes = [dict(contest_id='a', canonical_scene='A crib.'), dict(contest_id='b', canonical_scene='Another crib.')]
    actions, unused = extract_batches('For the crib:\nCaption: Ambiguous.', scenes)
    assert not actions
    target = tmp_path / 'must-not-exist'
    actions, metrics = extract_batches(f'Scene: 1\n```python\nopen({str(target)!r}, "w").write("bad")\n```', SCENES)
    assert not actions and not target.exists() and metrics['clarification_needed']


def journal(root, think, act, *, barrier=False):
    records = root / 'stream/records'
    records.mkdir(parents=True)
    think_document, act_document = dict(response=dict(raw=think)), dict(response=dict(raw=act))
    sequence = [('RESPONSE', think_document), ('COMMITTED', dict(source_sha256=_digest(think_document))),
        ('R184_STAGE', dict(stage='THINK', source_sha256=_digest(think_document)))]
    if barrier:
        sequence.append(('LOADED', dict(test=True)))
    sequence += [('REQUEST', dict(stage='ACT')), ('RESPONSE', act_document),
        ('COMMITTED', dict(source_sha256=_digest(act_document))),
        ('R184_STAGE', dict(stage='ACT', source_sha256=_digest(act_document)))]
    previous, result = 'genesis', []
    for index, (kind, document) in enumerate(sequence):
        record = dict(index=index, kind=kind, document=document, journal_id='same-child', previous_sha256=previous)
        record['sha256'] = _digest(record)
        (records / f'{index:020d}.json').write_text(json.dumps(record))
        previous = record['sha256']
        result.append(record)
    response = result[-3]
    return dict(kind='TRAIN_CHILD_RESPONSE', record_index=response['index'], record_sha256=response['sha256'])


class Game:
    def __init__(self):
        self.received = []

    def snapshot(self):
        return dict(received=list(self.received))

    def restore(self, state):
        assert not self.received
        self.received = [tuple(item) for item in state['received']]

    def submit_caption(self, contest, caption):
        duplicate = (contest, caption) in self.received
        self.received.append((contest, caption))
        return dict(ok=True, accepted=True, status='repeat' if duplicate else 'new_pixel',
                    rank=12, top_k=50, reference_count=64)


def test_same_child_committed_think_salvage_has_actual_stage_origin(tmp_path):
    raw = 'For the crib:\nCaption: Own thought joke.\nI will choose this approach.'
    origin = journal(tmp_path, raw, 'How should I format this?')
    found = latest_own_think(tmp_path, origin)
    assert found['origin']['record_index'] == 0 and found['stage'] == 'THINK'
    game = Game()
    session = LifeSession(game, tmp_path, tmp_path / 'service', SCENES)
    result = session.process(dict(origin=origin, metrics=dict(THINK=40, ACT=10, LEARN=0)))
    assert game.received == [('opaque-a', 'Own thought joke.')]
    source = result['report']['caption_sources'][0]
    assert source['stage'] == 'THINK' and source['origin'] == found['origin']
    assert source['actual_trigger_ACT'] == origin
    assert result['report']['next_stage'] == 'ACT'
    assert result['report']['feedback'][0]['result']['rank'] == 12


def test_no_salvage_across_loaded_boundary_or_hash_tampering(tmp_path):
    origin = journal(tmp_path, 'Scene: 1\nCaption: Historic.', 'Question: format?', barrier=True)
    assert latest_own_think(tmp_path, origin) is None
    origin['record_sha256'] = '0'*64
    with pytest.raises(ValueError):
        child_act(tmp_path, origin)


def test_malformed_act_returns_clarification_and_session_handles_next_act(tmp_path):
    game = Game()
    session = LifeSession(game, tmp_path, tmp_path / 'service', SCENES)
    with patch('gpu.ny_caption_life_service.child_act', side_effect=['Question: how?', 'Captions for Scene1:\nCaption: New.']):
        for ordinal in [1, 2]:
            result = session.process(dict(origin=dict(kind='TRAIN_CHILD_RESPONSE', record_index=ordinal,
                record_sha256=str(ordinal)*64), metrics=dict(THINK=1, ACT=1, LEARN=0)))
            if ordinal == 1:
                assert result['report']['next_stage'] == 'ACT' and not result['report']['feedback']
    assert game.received == [('opaque-a', 'New.')]


def test_restore_keeps_novelty_and_replay_set_no_new_empty_game(tmp_path):
    game = Game()
    session = LifeSession(game, tmp_path, tmp_path / 'service', SCENES)
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=1, record_sha256='a'*64)
    request = dict(origin=origin, metrics=dict(THINK=1, ACT=1, LEARN=0))
    with patch('gpu.ny_caption_life_service.child_act', return_value='Scene: 1\nCaption: Same joke.'):
        assert session.process(request)['report']['feedback'][0]['result']['status'] == 'new_pixel'
        state = session.snapshot()
        restored = LifeSession(Game(), tmp_path, tmp_path / 'restored', SCENES, resume_state=state)
        with pytest.raises(ValueError, match='duplicate_ACT'):
            restored.process(request)
        request['origin'] = dict(origin, record_index=2, record_sha256='b'*64)
        assert restored.process(request)['report']['feedback'][0]['result']['status'] == 'repeat'
    state['phase'] = 'PENDING'
    with pytest.raises(ValueError, match='same_complete_session_resume'):
        LifeSession(Game(), tmp_path, tmp_path / 'unsafe', SCENES, resume_state=state)


def test_loaded_restoration_evidence_hashes_actual_state_without_caption_payload(tmp_path):
    from gpu import ny_caption_data as data
    from gpu.ny_caption_life_service import restoration_evidence
    session = LifeSession(Game(), tmp_path, tmp_path / 'service', SCENES)
    session.game.received = [('opaque-a', 'PRIVATE synthetic caption not in public evidence')]
    session.seen = {'a'*64, 'b'*64}
    state = session.snapshot()
    restored = LifeSession(Game(), tmp_path, tmp_path / 'restored', SCENES, resume_state=state)
    reference = dict(path=str(tmp_path / 'old-state.private.json'), sha256='c'*64)
    evidence = restoration_evidence(restored, reference)
    assert evidence['resume_state_input_sha256'] == 'c'*64
    assert evidence['restored_seen_count'] == 2 and evidence['resumed_complete_state']
    assert evidence['restored_game_snapshot_sha256'] == data.digest(state['game'])
    assert evidence['restored_policy_snapshot_sha256'] == data.digest(state['policy'])
    assert 'PRIVATE synthetic caption' not in json.dumps(evidence)


def test_two_scenes_actual_counts_no_forced_six(tmp_path):
    game = Game()
    session = LifeSession(game, tmp_path, tmp_path / 'service', SCENES)
    with patch('gpu.ny_caption_life_service.child_act', return_value='Crib:\n"One."\nWindmill:\n"Two."'):
        result = session.process(dict(origin=dict(kind='TRAIN_CHILD_RESPONSE', record_index=1,
            record_sha256='a'*64), metrics=dict(THINK=4, ACT=10, LEARN=0)))
    assert result['report']['requested_count'] == 2
    assert [item[0] for item in game.received] == ['opaque-a', 'opaque-b']


def test_native_clarification_next_ACT_same_opportunity_charges_actual_tokens_once():
    from gpu import orch_r184_think_act_learn as stages
    from gpu.ny_caption_life import activate, POLICY
    events, records, corrections = [], [], []
    driver = SimpleNamespace(config=dict(trial_id='synthetic'),
        stream=SimpleNamespace(rows=[], history=SimpleNamespace(append=events.append)),
        cycle_metrics=dict(THINK=7, ACT=0, LEARN=0), allocation=None, dataset=None,
        journal=SimpleNamespace(record=lambda kind, document: records.append((kind, document))),
        record_corrections=lambda *args: corrections.append(args))
    def generate(stage):
        assert stage == 'ACT'
        ordinal = len(driver.stream.rows) + 1
        if ordinal == 2:
            assert events[-2].actor == 'environment'
        driver.cycle_metrics['ACT'] += 3
        driver.stream.rows.append(dict(target='Question?' if ordinal == 1 else 'Scene1: A joke.'))
        driver.last_response = dict(kind='TRAIN_CHILD_RESPONSE', record_index=ordinal, record_sha256=str(ordinal)*64)
        return dict(source_sha256=str(ordinal)*64, segment=ordinal)
    driver.generate_stage = generate
    def respond(socket, origin, metrics):
        return dict(policy=POLICY, origin=origin, report=dict(ok=origin['record_index']==2,
            feedback=[], next_stage='ACT' if origin['record_index']==1 else 'THINK'))
    with patch.object(stages.ThinkActLearn, 'act', stages.ThinkActLearn.act):
        activate('/tmp/synthetic-caption.sock')
        with patch('gpu.ny_caption_life.request', side_effect=respond) as transport:
            stages.ThinkActLearn.act(driver)
    assert [call.args[2] for call in transport.call_args_list] == [
        dict(THINK=7, ACT=3, LEARN=0), dict(THINK=0, ACT=3, LEARN=0)]
    assert len(corrections) == 1
    assert records[-1][0] == 'R223_CAPTION_OPPORTUNITY'
    assert len(records[-1][1]['attempts']) == 2 and records[-1][1]['life_continues']
