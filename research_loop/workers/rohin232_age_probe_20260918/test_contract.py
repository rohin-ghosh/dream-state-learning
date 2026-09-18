from copy import deepcopy

import pytest

from research_loop.workers.rohin232_age_probe_20260918.contract import initial_messages, run_cell, select_fresh


SCENE = dict(contest_id='development_x', canonical_scene='A person stands beside an enormous clock.')


class Backend:
    def __init__(self, length):
        self.length = length
        self.calls = []

    def seed(self, seed):
        self.current_seed = seed

    def generate(self, messages, max_new_tokens):
        self.calls.append((deepcopy(messages), max_new_tokens))
        length = min(self.length, max_new_tokens)
        return dict(messages=messages, token_ids=[4] * length, raw='"Late again."',
            prompt_tokens=12, terminal=length < max_new_tokens, truncated=length == max_new_tokens)


def score(raw, stage, origin):
    return dict(feedback='Rank 20 of 65; accepted; new pixel.', new_pixels=1)


def test_all_generated_tokens_exact_budget_early_eos_and_last_cap():
    backend, emitted = Backend(53), []
    result = run_cell(backend, SCENE, 23201, score, emitted.append)
    assert result['generated_tokens'] == 1024
    assert sum(row['event']['actual_generated_tokens'] for row in emitted) == 1024
    assert {row['event']['origin']['stage'] for row in emitted} == {'THINK', 'ACT'}
    assert backend.calls[-1][1] == 17
    assert result['parent_tokens'] == result['learn_or_other_reply_tokens'] == 0


def test_zero_token_explicit_incomplete():
    result = run_cell(Backend(0), SCENE, 23201, score, lambda value: None)
    assert result['status'].startswith('INCOMPLETE') and result['generated_tokens'] == 0


def test_fresh_context_is_source_independent_and_rejects_history():
    assert initial_messages(SCENE) == initial_messages(deepcopy(SCENE))
    with pytest.raises(ValueError, match='no_source_state'):
        initial_messages(dict(SCENE, resume_state='private'))


def test_excludes_either_life_and_not_only_current_three():
    packet = dict(pool='agent_development', FINAL_included=False,
        historical_captions_included=False, ratings_included=False,
        tasks=[dict(contest_id=str(index)) for index in range(10)])
    evidence = dict(complete=True, unresolved_request_content=0,
        excluded_contest_ids=['0', '1', '2', '4', '5'])
    assert [row['contest_id'] for row in select_fresh(packet, evidence)] == ['3', '6', '7']
    with pytest.raises(ValueError):
        select_fresh(packet, dict(evidence, unresolved_request_content=1))
    with pytest.raises(ValueError):
        select_fresh(dict(packet, FINAL_included=True), evidence)


def test_forged_request_or_overbudget_not_accepted():
    class BadBackend(Backend):
        def generate(self, messages, max_new_tokens):
            value = super().generate(messages, max_new_tokens)
            value['token_ids'] *= 5
            return value
    with pytest.raises(ValueError, match='actual_generation_budget'):
        run_cell(BadBackend(128), SCENE, 23201, score, lambda value: None)


def test_freshness_description_overlap_in_inherited_source_state(tmp_path):
    import json
    from research_loop.workers.rohin232_age_probe_20260918.exposure import audit
    records = tmp_path/'stream/records'
    records.mkdir(parents=True)
    source = dict(index=2, kind='SLEEP_COMPLETE', document=dict(resume_state=dict(history=[SCENE['canonical_scene']])))
    (records/f'{2:020d}.json').write_text(json.dumps(source))
    evidence = audit(tmp_path, dict(contests=[SCENE]), dict(sources=[dict(sleep_complete_index=2)],
        head_index=2, head_sha256='f'*64, exposure=dict(complete=True)))
    assert not evidence['eligible']
    assert evidence['matched_record_indices'][SCENE['contest_id']] == [2]


def test_plain_caption_active_scene_source_spans_and_no_count_gate():
    from research_loop.workers.rohin221_continuous_caption_20260918.freeform import extract_batches
    text = '\n'.join(f'{index}. "My deadline has its own deadline {index}."' for index in range(1, 13))
    actions, receipt = extract_batches(text, [SCENE], active_scene=SCENE['contest_id'])
    assert sum(len(action['captions']) for action in actions) == 12
    for source, caption in zip(receipt['caption_sources'], actions[0]['captions']):
        assert text[source['start']:source['end']] == caption


def test_receipt_not_visible_until_complete_and_never_overwritten(tmp_path, monkeypatch):
    import json
    from research_loop.workers.rohin232_age_probe_20260918 import runtime
    original = runtime.data.private_write
    target = tmp_path/'ready.json'
    def checked(path, value):
        assert not target.exists()
        result = original(path, value)
        assert not target.exists()
        return result
    monkeypatch.setattr(runtime.data, 'private_write', checked)
    runtime.write(target, dict(complete=True))
    assert json.loads(target.read_bytes()) == dict(complete=True)
    monkeypatch.setattr(runtime.data, 'private_write', original)
    with pytest.raises(FileExistsError):
        runtime.write(target, dict(complete=False))
    assert json.loads(target.read_bytes()) == dict(complete=True)
