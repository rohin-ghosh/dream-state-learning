import json
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from gpu.ny_caption_life_service import LifeSession
from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches
from research_loop.workers.rohin221_continuous_caption_20260918.scene_schedule import (
    POLICY, assignment, prompt, verified_active_scene,
)
from research_loop.workers.rohin221_continuous_caption_20260918.controller import Controller, Plan


SCENES = [dict(contest_id='first', canonical_scene='A crib.'),
          dict(contest_id='second', canonical_scene='A windmill.')]


def test_bare_numbers_only_use_explicit_bound_active_scene_and_keep_spans():
    raw = '1. "First literal ９８， joke."\n2. "Second literal."'
    actions, diagnostic = extract_batches(raw, SCENES)
    assert not actions and diagnostic['ambiguous_caption_lines'] == 2
    assert not diagnostic['no_caption_act']
    actions, diagnostic = extract_batches(raw, SCENES, active_scene='second')
    assert actions[0]['contest_id'] == 'second' and actions[0]['count'] == 2
    for source, caption in zip(diagnostic['caption_sources'], actions[0]['captions']):
        assert raw[source['start']:source['end']] == caption
    with pytest.raises(ValueError):
        extract_batches(raw, SCENES, active_scene='unregistered')


def test_explicit_other_or_unknown_scene_never_silently_uses_default():
    actions, diagnostic = extract_batches('Scene2:\n"Other."\nFor unknown scene:\n"Unbound."',
        SCENES, active_scene='first')
    assert [action['contest_id'] for action in actions] == ['second']
    assert diagnostic['ambiguous_caption_lines'] == 1


def test_no_caption_promises_and_mermaid_distinct_from_ambiguity(tmp_path):
    raw = 'I will write some funny captions.\n```mermaid\ngraph TD; A-->B;\n```'
    game = SimpleNamespace(snapshot=lambda: {}, submit_caption=lambda *args: pytest.fail('not a caption'))
    session = LifeSession(game, tmp_path, tmp_path / 'service', SCENES)
    result = session.process_verified(dict(origin={}, metrics=dict(THINK=0, ACT=1, LEARN=0)),
        raw, identifier='a'*64, active_scene='first')
    report = result['report']
    assert report['format_metrics']['no_caption_act']
    assert report['format_metrics']['ambiguous_caption_lines'] == 0
    assert report['error'] == 'no_caption_found' and report['feedback'] == []
    assert report['next_stage'] == 'ACT'
    assert 'No caption found in your output—write the captions themselves, one per line, for the scene you choose' in report['instruction']
    assert 'suggestion, not a required format' in report['instruction']


def test_schedule_requires_actual_prompt_and_rotates_not_each_repair():
    assert [assignment(SCENES, number)['number'] for number in [1, 1, 2, 3]] == [1, 1, 2, 1]
    request = dict(binding=dict(plan=dict(scene_schedule=POLICY)), opportunity=2,
                   messages=[dict(role='user', content=prompt(SCENES, 2))])
    assert verified_active_scene(request, SCENES) == 'second'
    request['messages'] = []
    with pytest.raises(ValueError, match='actual_model_input'):
        verified_active_scene(request, SCENES)
    request['binding']['plan']['scene_schedule'] = None
    assert verified_active_scene(request, SCENES) is None


def test_planning_bullets_and_unfenced_diagram_not_counted_as_captions():
    raw = ('Scene2:\n- "Actual one."\n- "Actual two."\n#### Reflection\n'
           '- We will create more captions.\n`sequenceDiagram`\nparticipant Judge\n'
           '_classifier->Judge: "Not a submitted caption."\nWe will await feedback.')
    actions, diagnostic = extract_batches(raw, SCENES)
    assert actions[0]['captions'] == ['Actual one.', 'Actual two.']
    assert diagnostic['candidate_lines'] == 2 and not diagnostic['no_caption_act']


def test_controller_binds_scene_to_think_and_act_without_requiring_output_shape(tmp_path):
    plan = Plan(condition='synthetic', rule_sha256='a'*64, scene_schedule=POLICY)
    scorer = SimpleNamespace(binding=dict(rule_sha256=plan.rule_sha256, top_k=50, reference_count=64,
        relevance=True, novelty=True, condition=plan.condition))
    backend = SimpleNamespace(state_receipt=lambda: dict(kind='CPU_TEST'), kind='CPU_TEST',
                              count_tokens=lambda messages: 100)
    with Controller(tmp_path, plan, backend, scorer, SCENES, extract_batches) as controller:
        for stage in ['THINK', 'ACT']:
            messages, removed = controller.messages(stage)
            assert dict(role='user', content=prompt(SCENES, 1)) in messages
            assert 'No fields, fixed count, or special output format' in json.dumps(messages)
        assert controller.binding['plan'] == asdict(plan)
