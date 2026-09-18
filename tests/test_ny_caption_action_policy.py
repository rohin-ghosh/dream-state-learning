import json

from gpu.ny_caption_action_policy import CaptionActionPolicy
from gpu.ny_caption_development import parse_actions
from gpu.orch_r189_outcome_allocation import SCHEMA as OUTCOME_SCHEMA


class Game:
    def __init__(self):
        self.calls = []

    def submit_caption(self, contest, caption):
        self.calls.append((contest, caption))
        return dict(ok=True, accepted=caption != 'rejected', status='NEW_PIXEL', q=0.8)


def batch(count, direction='juxtaposition', contest='development-a'):
    return dict(tool='caption_batch', contest_id=contest, count=count, direction=direction,
        captions=[f'own caption {number}' for number in range(count)])


def test_gradual_child_selected_volumes_and_each_real_result():
    game = Game()
    policy = CaptionActionPolicy(game)
    for count in (10, 15, 25, 50, 100, 5):
        result = policy.submit(batch(count))
        assert result['ok'] and len(result['feedback']) == count
        assert result['direction'] == 'juxtaposition'
        assert result['next_stage'] == 'THINK'
    assert len(game.calls) == 205


def test_jump_or_unprovided_captions_do_not_call_judge():
    game = Game()
    policy = CaptionActionPolicy(game)
    assert policy.submit(batch(100))['error'] == 'batch_growth_too_large'
    missing = batch(10)
    missing['captions'].pop()
    assert policy.submit(missing)['error'] == 'invalid_caption_batch'
    invalid = batch(1)
    invalid['count'] = True
    assert policy.submit(invalid)['error'] == 'invalid_caption_batch'
    assert game.calls == []


def test_unknown_failure_is_not_retried_or_reported_as_feedback():
    class FailedGame:
        calls = 0

        def submit_caption(self, *arguments):
            self.calls += 1
            raise RuntimeError('synthetic failure after dispatch')

    game = FailedGame()
    result = CaptionActionPolicy(game).submit(batch(10))
    assert not result['ok'] and game.calls == 1
    assert result['feedback'][0]['accepted'] is None
    assert result['feedback'][0]['outcome'] == 'UNKNOWN_AFTER_DISPATCH'


def test_volume_state_survives_restoration_and_direction_is_child_owned():
    game = Game()
    policy = CaptionActionPolicy(game)
    policy.submit(batch(10))
    restored = CaptionActionPolicy(game, policy.snapshot())
    assert restored.submit(batch(25))['error'] == 'batch_growth_too_large'
    assert restored.submit(batch(15, 'punk references'))['direction'] == 'punk references'
    assert restored.submit(batch(15, contest='development-b'))['error'] == 'batch_growth_too_large'


def test_existing_parser_accepts_batch_alongside_existing_tools():
    action = batch(2)
    assert parse_actions('```json\n' + json.dumps(action) + '\n```') == [action]
    assert parse_actions(json.dumps(dict(tool='submit_caption', contest_id='a', text='one'))) == [
        dict(tool='submit_caption', contest_id='a', text='one')]


def test_outcome_opt_in_tracks_real_novelty_and_stage_shares_across_restore():
    class RealShapeGame(Game):
        def submit_caption(self, contest, caption):
            return dict(ok=True, accepted=True, status='new_pixel', replayed=False)

    policy = CaptionActionPolicy(RealShapeGame(), outcome_policy=OUTCOME_SCHEMA)
    assert policy.guidance('development-a')['think_segments_budget'] == 3
    for unused in range(2):
        result = policy.submit(batch(2), cycle_metrics=dict(THINK=60, ACT=40, LEARN=0))
    report = result['outcome_allocation']
    assert report['think_token_share'] == 0.6
    assert report['guess_volume'] == 2
    assert report['running_success_rate'] == 1
    assert report['guidance_next']['think_segments_budget'] == 1
    restored = CaptionActionPolicy(RealShapeGame(), policy.snapshot(), outcome_policy=OUTCOME_SCHEMA)
    assert restored.snapshot() == policy.snapshot()
    assert restored.guidance('development-a') == policy.guidance('development-a')


def test_cached_new_pixel_and_similar_repeat_are_never_new_successes():
    class RepeatedGame:
        def submit_caption(self, contest, caption):
            return dict(ok=True, accepted=True, status='new_pixel' if caption.endswith('0') else 'repeat',
                        replayed=caption.endswith('0'))

    policy = CaptionActionPolicy(RepeatedGame(), outcome_policy=OUTCOME_SCHEMA)
    result = policy.submit(batch(2))
    observation = result['outcome_allocation']['observation']
    assert observation['cached'] == 1
    assert observation['quality_accepted'] == observation['repeats'] == 1
    assert observation['successes'] == 0
    assert all(item['repeat'] for item in result['feedback'])
    assert result['outcome_allocation']['guidance_next']['mode'] == 'REDUNDANT_DATA'


def test_partial_dispatch_unknown_and_unattempted_have_separate_denominators():
    class PartialGame:
        calls = 0

        def submit_caption(self, contest, caption):
            self.calls += 1
            if self.calls == 2:
                raise TimeoutError('synthetic unknown dispatch')
            return dict(ok=True, accepted=False, status='rejected')

    game = PartialGame()
    result = CaptionActionPolicy(game, outcome_policy=OUTCOME_SCHEMA).submit(batch(5))
    observation = result['outcome_allocation']['observation']
    assert game.calls == 2
    assert observation['requested'] == 5
    assert observation['evaluated'] == observation['unknown'] == 1
    assert observation['not_dispatched'] == 3
    assert result['outcome_allocation']['running_success_rate'] == 0


def test_bad_metrics_or_schema_cannot_dispatch_or_silently_drop_policy():
    import pytest
    game = Game()
    policy = CaptionActionPolicy(game, outcome_policy=OUTCOME_SCHEMA)
    with pytest.raises(ValueError):
        policy.submit(batch(2), cycle_metrics=dict(THINK=True, ACT=3, LEARN=0))
    assert not game.calls and not policy.previous
    with pytest.raises(ValueError):
        CaptionActionPolicy(game, policy.snapshot())
    with pytest.raises(ValueError):
        CaptionActionPolicy(game, outcome_policy='unregistered')
    assert CaptionActionPolicy(game).snapshot() == dict(schema='R187_CAPTION_ACTION_POLICY_V1', previous={})


def test_rejected_growth_records_unattempted_guesses_not_semantic_failures():
    game = Game()
    policy = CaptionActionPolicy(game, outcome_policy=OUTCOME_SCHEMA)
    result = policy.submit(batch(50), cycle_metrics=dict(THINK=10, ACT=30, LEARN=0))
    assert result['error'] == 'batch_growth_too_large'
    report = result['outcome_allocation']
    assert report['guess_volume'] == report['observation']['not_dispatched'] == 50
    assert report['observation']['evaluated'] == 0
    assert report['running_success_rate'] is None
    assert not game.calls and not policy.previous
