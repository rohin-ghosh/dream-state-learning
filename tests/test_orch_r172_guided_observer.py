import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research_loop/workers/rohin172_c2_pilot_20260917/watch_guided.py'
SPEC = importlib.util.spec_from_file_location('guided_observer', SOURCE)
observer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observer)
CONFIG = json.loads((SOURCE.parent / 'PILOT_CONFIG_V1.json').read_text())


def trace():
    return dict(schema='R175_PINNED_LESSON_TRACE_V1', root=CONFIG['source_life'],
                journal_id=CONFIG['source_journal_id'], anchor_index=4943,
                anchor_sha256=CONFIG['pre_intervention_checkpoint']['sleep_record_sha256'],
                caught_up=True, no_writes_to_life=True, success_claim=False,
                first_rendered_guidance=None, guided_committed_responses=0,
                guided_generated_tokens=0, first_eligible_completed_sleep=None,
                observed_utc='2026-09-17T21:16:39+00:00', status='AWAITING_GUIDANCE_EXPOSURE',
                end_index=5066, head_sha256='a' * 64)


def test_fixed_source_and_wrapper_command():
    assert observer.REPO == ROOT
    assert observer.sha(SOURCE.parent / 'PILOT_CONFIG_V1.json') == observer.CONFIG_SHA
    command = observer.command(CONFIG)
    assert command[:2] == ['bash', str(ROOT / 'gpu/ovx3_ssh.sh')]
    assert 'sha256sum -c' in command[2]
    assert CONFIG['already_published_guidance']['rohin_inbox_id'] in command[2]
    assert 'stream_console' not in command[2]


def test_no_publication_implies_no_exposure():
    result = observer.summarize(trace(), CONFIG)
    assert not result['question_review_due']
    assert result['parent_calls'] == result['child_writes'] == 0


@pytest.mark.parametrize('field,value', [('caught_up', False), ('success_claim', True),
    ('no_writes_to_life', False), ('root', '/another/life'), ('anchor_sha256', 'f' * 64)])
def test_rejects_unbound_or_partial_trace(field, value):
    document = trace()
    document[field] = value
    with pytest.raises(ValueError):
        observer.summarize(document, CONFIG)


def test_question_is_review_only_not_a_second_publication():
    document = trace()
    document.update(first_rendered_guidance=dict(inbox_id=CONFIG['already_published_guidance']['rohin_inbox_id']),
                    guided_committed_responses=1, guided_generated_tokens=200, status='GUIDED_PHASE')
    result = observer.summarize(document, CONFIG)
    assert result['question_review_due']
    assert result['question_not_automatically_sent']
    assert result['parent_calls'] == 0
    wrong = copy.deepcopy(document)
    wrong['first_rendered_guidance']['inbox_id'] = 'not_rohin'
    with pytest.raises(ValueError, match='bound_Rohin_exposure'):
        observer.summarize(wrong, CONFIG)


def test_selection_requires_four_commits_and_is_not_success():
    document = trace()
    document.update(first_rendered_guidance=dict(inbox_id=CONFIG['already_published_guidance']['rohin_inbox_id']),
                    guided_committed_responses=3, first_eligible_completed_sleep={'cycle': 42})
    with pytest.raises(ValueError, match='four_committed'):
        observer.summarize(document, CONFIG)
    document['guided_committed_responses'] = 4
    result = observer.summarize(document, CONFIG)
    assert result['checkpoint_selection_not_a_success_claim']
    assert not result['question_review_due']
