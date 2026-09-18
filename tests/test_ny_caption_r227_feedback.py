from copy import deepcopy
import json
from unittest.mock import Mock

from gpu.ny_caption_life import attributed_tool_feedback, caption_feedback_payload
from organism_v6.orch_r125_plain_context import event_message, has_scaffolding, replay_prefix
from tests.test_orch_r125_plain_context import PRESENTATION, count, event, stream


def result():
    return dict(origin=dict(kind='TRAIN_CHILD_RESPONSE',record_index=113,record_sha256='a'*64),
        receipt_sha256='b'*64, source_transport=dict(source_life_root='/private/transport/path'),
        report=dict(ok=True,requested_count=1,not_dispatched_count=0,
            caption_sources=[dict(stage='ACT',start=3,end=20,line=1,text_sha256='c'*64,
                                 source_sha256='d'*64,origin='TRAIN_COLLECTION')],
            feedback=[dict(caption_source_index=0,result=dict(ok=True,rank=54,reference_count=64,
                top_k=50,accepted=False,status='rejected',replayed=False,relevance_score=.42,
                relevance_threshold=.1,rejection_reason='outside_top_k'))],
            format_metrics=dict(format_fault=False)))


def test_exact_failure_and_future_view_retained_in_request_masked_prefix_and_replay():
    original = result()
    before = deepcopy(original)
    raw = json.dumps(original)
    assert has_scaffolding(raw)
    assert event_message(event('old',raw,'environment',phase='feedback')) is None
    text = attributed_tool_feedback(original)
    assert text.startswith('Tool: ') and not has_scaffolding(text)
    child = stream()
    child.set_presentation(PRESENTATION,16384)
    child.history.append(event('future',text,'environment',phase='feedback'))
    rendered = child.render(count)
    expected = dict(role='user',content=text)
    assert expected in rendered.messages
    assert set(rendered.labels) == {-100} and rendered.target_token_ids == ()
    generate = Mock(return_value=dict(raw='I observed the actual rank and will reconsider.',
                                     token_ids=[10,2],terminal=True,truncated=False))
    child.step(generate,count,lambda *args:None)
    assert expected in generate.call_args.args[0]
    assert expected in child.rows[-1]['prefix']
    assert expected in replay_prefix(child.rows[-1]['prefix'],PRESENTATION)
    assert child.rows[-1]['target'] == generate.return_value['raw']
    assert original == before
    payload = caption_feedback_payload(original)
    assert payload['scorer_receipt'] == 'b'*64
    assert payload['response_digest'] == 'a'*64
    assert payload['observations'][0]['rank'] == 54
    assert '/private/' not in text


def test_think_provenance_cache_and_semantic_repeat_are_not_relabelled():
    original = result()
    original['report']['caption_sources'][0]['stage'] = 'THINK'
    original['report']['feedback'][0]['result'].update(accepted=True,status='repeat',replayed=True)
    observation = caption_feedback_payload(original)['observations'][0]
    assert observation['source_stage'] == 'THINK'
    assert observation['status'] == 'repeat' and observation['replayed']


def test_unknown_and_scene_clarification_remain_data_not_fabricated_judgments():
    original = result()
    original['report'].update(ok=False,error='ORIGIN_TRANSPORT_NOT_DISPATCHED',feedback=[],
        format_metrics=dict(format_fault=True,ambiguous_caption_lines=2))
    payload = caption_feedback_payload(original)
    assert payload['observations'] == [] and payload['ok'] is False
    assert 'no fixed format' in payload['clarification']
    assert not has_scaffolding(attributed_tool_feedback(original))
