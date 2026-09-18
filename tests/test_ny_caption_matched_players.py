from copy import deepcopy
import json

from research_loop.workers.rohin209_first_game_20260918 import matched_players as players


class Backend:
    def __init__(self, raw):
        self.raw = raw
        self.requests = []

    def generate(self, messages, max_new_tokens):
        self.requests.append(deepcopy(messages))
        return dict(messages=messages, raw=self.raw if len(self.requests) == 2 else 'Try contrasting needs.',
                    prompt_tokens=500, token_ids=[21, 22], terminal=True, truncated=False)

    def verify_unchanged(self):
        return dict(unchanged=True)


def test_matched_inputs_and_literal_captions(tmp_path):
    scenes = [dict(contest_id='private-contest-key-123', canonical_scene='Two people beside a crib.')]
    backends = [Backend('Check: same approach.\nScene: １\nDirection: conflict\nCount: １\nCaption: Literal ９８，joke')
                for _ in range(2)]
    for ordinal, backend in enumerate(backends):
        output = tmp_path / str(ordinal)
        output.mkdir()
        players.opportunity(backend, scenes, output)
        actions = json.loads((output / 'actions.json').read_text())
        assert actions[0]['text'] == 'Literal ９８，joke'
        result = json.loads((output / 'RESULT.json').read_text())
        assert not result['game_scored'] and not result['learning_or_retention_demonstrated']
    assert backends[0].requests == backends[1].requests
    assert 'humour contest' in backends[0].requests[0][0]['content']
    assert 'rank <= 50 of 65' in backends[0].requests[0][0]['content']
    assert 'private-contest-key-123' not in str(backends[0].requests)


def test_bad_action_preserves_raw_without_substitution(tmp_path):
    backend = Backend('I got a score of 99!')
    players.opportunity(backend, [dict(contest_id='id', canonical_scene='Scene')], tmp_path)
    assert json.loads((tmp_path / 'ACT_GENERATION.json').read_text())['raw'] == 'I got a score of 99!'
    assert json.loads((tmp_path / 'actions.json').read_text()) == []
    result = json.loads((tmp_path / 'RESULT.json').read_text())
    assert result['format_metrics']['unscored_reason'] == 'scene_not_unambiguously_identified'


def test_missing_prefix_is_scored_separately_from_format_fault(tmp_path):
    backend = Backend('Scene: 3\nDirection: absurdity\nCount: 2\n\n'
                      "Caption: Even the windmill knows this meeting's ridiculous. \n"
                      "Formal wear isn't optional in a tilted windmill meeting.")
    scenes = [dict(contest_id=str(index), canonical_scene='Scene') for index in range(3)]
    players.opportunity(backend, scenes, tmp_path)
    actions = json.loads((tmp_path / 'actions.json').read_text())
    assert len(actions) == 2
    assert actions[0]['text'].endswith('. ')
    assert actions[1]['text'] == "Formal wear isn't optional in a tilted windmill meeting."
    assert all(action['contest_id'] == '2' for action in actions)
    assert json.loads((tmp_path / 'RESULT.json').read_text())['format_metrics']['unprefixed_lines'] == 1


def test_undeclared_unprefixed_caption_is_not_silently_lost():
    from gpu.ny_caption_life import extract_batch

    batch, metrics = extract_batch('Scene: 1\nDirection: contrast\nCount: 1\nCaption: First.\nSecond.', ['id'])
    assert batch['captions'] == ['First.', 'Second.'] and batch['count'] == 2
    assert metrics['format_fault'] and metrics['recovered_count'] == 2
