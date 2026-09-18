from concurrent.futures import Future
from copy import deepcopy
import json
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from gpu.ny_caption_development import (
    CONTINUITY_POLICY, DevelopmentBridge, DevelopmentConfig, GenerationProxy, OUTCOME_POLICY, STAGED_SCHEMA,
    allocation_view, drive_native, parent_request, parse_actions,
)
from gpu.orch_r189_outcome_allocation import PARENT_STOP_CHECK
from gpu.orch_r191_exploration_dataset import ExplorationDataset
from gpu.orch_r193_continuity import PARENT_QUESTION


class ControlledExecutor:
    def __init__(self):
        self.jobs = []

    def submit(self, callback, *arguments):
        future = Future()
        self.jobs.append((future, callback, arguments))
        return future

    def complete(self, index):
        future, callback, arguments = self.jobs[index]
        future.set_result(callback(*arguments))


class FakeGame:
    def __init__(self):
        self.calls = []

    def submit_caption(self, contest_id, text):
        self.calls.append((contest_id, text))
        return dict(accepted=True, q=0.8, status='new_pixel', pixel_count=len(self.calls))

    def inspect_image(self, contest_id, question):
        self.calls.append((contest_id, question))
        return dict(observations='A synthetic fixture square.', uncertainty='Fixture only.')

    def snapshot(self):
        return dict(calls=self.calls)


def bridge(tmp_path, lane='UNPARENTED', **extra):
    executor = ControlledExecutor()
    game = FakeGame()
    if lane == 'PARENTED':
        extra.setdefault('parent', lambda request: dict(guidance='Check what the observation supports.', object_id='object'))
        extra.setdefault('policy', dict(version='v1', model_id='configured-model', text='Process guidance only.'))
    return DevelopmentBridge(DevelopmentConfig(lane), game, tmp_path.resolve(), executor=executor, **extra), executor, game


@pytest.mark.parametrize('mode', ['FINAL', 'final', None])
def test_final_is_not_silently_a_development_run(mode):
    with pytest.raises(ValueError, match='FINAL_not_implemented'):
        DevelopmentConfig('PARENTED', mode=mode)


@pytest.mark.parametrize('lane', ['FROZEN', 'LEARNER', 'third_arm'])
def test_obsolete_rev5_lineages_refuse(lane):
    with pytest.raises(ValueError, match='R161_two_learning'):
        DevelopmentConfig(lane)


def test_tool_parser_accepts_json_fences_and_smart_quotes_not_arbitrary_code():
    raw = 'I will inspect. ```json\n{“tool”:“inspect_image”,“contest_id”:“a”,“question”:“What is visible?”}\n```'
    assert parse_actions(raw) == [dict(tool='inspect_image', contest_id='a', question='What is visible?')]
    assert parse_actions('```python\nprint("hello")\n```') == []
    assert parse_actions('{"tool":"submit_caption","contest_id":"a","text":"x","hidden":"payload"}') == []


def test_batch_has_individually_routed_captions():
    raw = '[{"tool":"submit_caption","contest_id":"a","text":"x"}, {"tool":"submit_caption","contest_id":"b","text":"y"}]'
    assert [entry['contest_id'] for entry in parse_actions(raw)] == ['a', 'b']


def test_unparented_lane_cannot_have_a_parent(tmp_path):
    with pytest.raises(ValueError, match='parent_required_only'):
        bridge(tmp_path, parent=lambda request: {})


def test_caption_batch_returns_each_actual_result_as_masked_environment_input(tmp_path):
    import json
    connection, executor, game = bridge(tmp_path)
    action = dict(tool='caption_batch', contest_id='a', direction='juxtaposition',
        count=2, captions=['first own caption', 'second own caption'])
    connection.after_generation(dict(raw=json.dumps(action), token_ids=[1, 2, 3]))
    assert not game.calls
    executor.complete(0)
    events = connection.before_generation()
    assert len(events) == 1 and events[0].actor == 'environment'
    feedback = json.loads(events[0].text)
    assert feedback['requested_count'] == 2 and len(feedback['feedback']) == 2
    assert game.calls == [('a', 'first own caption'), ('a', 'second own caption')]
    assert connection.checkpoint()['action_policy']['previous']['a']['count'] == 2


def test_caption_action_volume_state_is_restorable(tmp_path):
    connection, executor, unused_game = bridge(tmp_path / 'first')
    connection.action_policy.previous = {'a': dict(count=10, direction='contrast')}
    restored, unused_executor, game = bridge(tmp_path / 'second',
        action_state=connection.checkpoint()['action_policy'])
    action = dict(tool='caption_batch', contest_id='a', direction='contrast',
        count=25, captions=['own caption'] * 25)
    assert restored.action_policy.submit(action)['error'] == 'batch_growth_too_large'
    assert game.calls == []


def test_tool_execution_does_not_block_generation_or_fabricate_observation(tmp_path):
    connection, executor, game = bridge(tmp_path)
    connection.after_generation(dict(raw='{"tool":"inspect_image","contest_id":"a","question":"What?"}', token_ids=[1, 2]))
    assert connection.before_generation() == []
    assert game.calls == []
    executor.complete(0)
    events = connection.before_generation()
    assert len(events) == 1 and events[0].actor == 'environment'
    assert events[0].split == 'TRAIN'
    assert Path(events[0].source_id).is_file()
    assert 'synthetic fixture square' in events[0].text
    assert connection.before_generation() == []


def test_parent_pending_does_not_hold_tool_or_child(tmp_path):
    connection, executor, game = bridge(tmp_path, 'PARENTED')
    assert connection.before_generation('own child') == []
    response = dict(raw='own continuation', token_ids=[1, 2, 3])
    proxy = GenerationProxy(SimpleNamespace(generate=lambda *args, **kwargs: response), connection)
    assert proxy.generate([], max_new_tokens=512) == response
    assert connection.total_tokens == 3
    assert connection.before_generation('more own text') == []
    assert len(executor.jobs) == 1
    executor.complete(0)
    events = connection.before_generation()
    assert len(events) == 1 and events[0].actor == 'parent'
    assert connection.object_turns == {'object': 1}


def test_parent_failure_is_logged_missing_without_invented_turn(tmp_path):
    def failed(request):
        raise RuntimeError('fixture provider fault')

    connection, executor, unused_game = bridge(tmp_path, 'PARENTED', parent=failed)
    connection.before_generation()
    executor.complete(0)
    assert connection.before_generation() == []
    assert 'MISSING' in (tmp_path / 'parent_results/00000000.json').read_text()


def test_generation_reserves_maximum_tokens_before_native_call(tmp_path):
    connection, unused_executor, unused_game = bridge(tmp_path)
    connection.total_tokens = 29999
    calls = []
    with pytest.raises(ValueError, match='reserve_full_generation'):
        connection.generate(lambda *args, **kwargs: calls.append(True), [], max_new_tokens=512)
    assert calls == []


def test_lanes_and_receipts_remain_separate(tmp_path):
    first, first_executor, unused_first_game = bridge(tmp_path / 'first')
    second, second_executor, unused_second_game = bridge(tmp_path / 'second')
    response = dict(raw='{"tool":"submit_caption","contest_id":"a","text":"own caption"}', token_ids=[1])
    first.after_generation(response)
    first_executor.complete(0)
    assert len(first.before_generation()) == 1
    assert second.before_generation() == []
    assert second.checkpoint()['child_tokens'] == 0
    assert second_executor.jobs == []


def test_queue_is_bounded_without_provider_work(tmp_path):
    connection, executor, unused_game = bridge(tmp_path)
    raw = '{"tool":"submit_caption","contest_id":"a","text":"candidate"}'
    for unused in range(9):
        connection.after_generation(dict(raw=raw, token_ids=[1]))
    assert len(executor.jobs) == len(connection.pending) == 8
    assert len(list((tmp_path / 'tool_rejections').glob('*.json'))) == 1


def staged_bridge(tmp_path, *, game=None, lane='UNPARENTED', executor=None, window_tokens=1000,
                  outcome_policy=OUTCOME_POLICY, continuity_policy=None, feedback_timeout_seconds=120, **extra):
    game = game or FakeGame()
    game.manifest = SimpleNamespace(contests=(SimpleNamespace(contest_id='a'), SimpleNamespace(contest_id='b')))
    executor = executor or ControlledExecutor()
    if lane == 'PARENTED':
        extra.setdefault('parent', lambda request: dict(guidance='Inspect your actual evidence.', object_id='object'))
        extra.setdefault('policy', dict(version='v1', model_id='synthetic-only', text='Process guidance only.'))
    connection = DevelopmentBridge(DevelopmentConfig(lane, outcome_policy=outcome_policy,
        outcome_window_tokens=window_tokens, continuity_policy=continuity_policy,
        feedback_timeout_seconds=feedback_timeout_seconds), game,
        tmp_path.resolve(), executor=executor, **extra)
    return connection, executor, game


def response(raw, tokens=2):
    return dict(raw=raw, token_ids=list(range(tokens)), terminal=True, truncated=False)


def batch(contest='a', captions=None):
    captions = captions or ['synthetic own caption']
    return dict(tool='caption_batch', contest_id=contest, direction='own contrast',
        count=len(captions), captions=captions)


def act_and_collect(connection, executor, action=None, *, think_tokens=2, act_tokens=3):
    connection.after_generation(response('Ready to act', think_tokens))
    connection.after_generation(response(json.dumps(action or batch()), act_tokens))
    executor.complete(len(executor.jobs) - 1)
    return connection.before_generation(deadline_unix=20, now=lambda: 10)


@pytest.mark.parametrize('policy', ['', True, {}, 'R189_OUTCOME_ALLOCATION_V2'])
def test_outcome_policy_requires_exact_opt_in(policy):
    with pytest.raises(ValueError, match='known_outcome_policy'):
        DevelopmentConfig('UNPARENTED', outcome_policy=policy)


def test_legacy_snapshot_and_parent_request_bytes_have_no_r189_fields(tmp_path):
    connection, unused_executor, unused_game = bridge(tmp_path)
    snapshot = connection.checkpoint()
    assert snapshot == dict(schema='R177_CAPTION_DEVELOPMENT_V1', lane='UNPARENTED', child_tokens=0,
        generation_count=0, parent_count=0, next_parent_tokens=0, object_turns={}, pending_tool_ids=[],
        pending_parent_id=None, game=dict(calls=[]), action_policy=dict(schema='R187_CAPTION_ACTION_POLICY_V1',
        previous={}), feedback=[], recent_raw='', external_text_training_target=False, stage='DEVELOPMENT')
    policy = dict(version='v1', model_id='synthetic', text='Process only.')
    arguments = dict(recent_child_text='own', own_feedback=[], token_count=4, prior_object_turns={})
    old = parent_request(policy, **arguments)
    assert json.dumps(old).encode() == json.dumps(parent_request(policy, allocation=None, **arguments)).encode()
    assert old['messages'][1]['content'] == ('{"recent_child_text": "own", "own_public_feedback": [], '
        '"child_tokens": 4, "prior_object_turns": {}}')
    assert PARENT_STOP_CHECK not in old['messages'][0]['content']
    assert connection.before_generation() == []


def test_initial_three_think_segments_do_not_execute_tool_text(tmp_path):
    connection, executor, game = staged_bridge(tmp_path)
    for expected_used in range(1, 4):
        events = connection.before_generation()
        assert events[-1].actor == 'environment' and events[-1].split == 'TRAIN'
        assert events[-1].source_id.endswith(':THINK')
        connection.after_generation(response(json.dumps(batch())))
        assert executor.jobs == [] and game.calls == []
        assert connection.staged['think_segments_used'] == expected_used
    assert connection.staged['phase'] == 'ACT'
    assert connection.staged['transition'] == 'BUDGET_EXHAUSTED'
    assert connection.before_generation()[-1].source_id.endswith(':ACT')
    connection.after_generation(response(json.dumps(batch())))
    assert len(executor.jobs) == 1 and game.calls == []
    executor.complete(0)
    events = connection.before_generation(deadline_unix=20, now=lambda: 10)
    assert len(game.calls) == 1
    assert events[0].phase == 'feedback' and 'feedback' in json.loads(events[0].text)
    assert events[-1].source_id.endswith(':THINK')


@pytest.mark.parametrize('raw', ['Ready to act', 'A hypothesis.\nReady to act.', '{"ready_to_act":true}'])
def test_child_can_choose_act_after_one_think(tmp_path, raw):
    connection, executor, unused_game = staged_bridge(tmp_path)
    connection.after_generation(response(raw))
    assert connection.staged['phase'] == 'ACT'
    assert connection.staged['transition'] == 'CHILD_READY'
    assert connection.staged['think_segments_used'] == 1
    assert executor.jobs == []


@pytest.mark.parametrize('raw', ['I am not ready to act', 'Quoted "Ready to act"', '{"ready_to_act":false}',
    '{"ready_to_act":1}', 'Example:\n```text\nReady to act\n```',
    '~~~text\nI am ready to act.\n~~~', '```json\n{"ready_to_act":true}\n```', '> Ready to act'])
def test_readiness_is_explicit_not_a_substring_or_truthy_value(tmp_path, raw):
    connection, unused_executor, unused_game = staged_bridge(tmp_path)
    connection.after_generation(response(raw))
    assert connection.staged['phase'] == 'THINK'


def test_readiness_after_a_closed_example_uses_shared_explicit_detector(tmp_path):
    connection, executor, unused_game = staged_bridge(tmp_path)
    connection.after_generation(response('```text\nI am not ready to act.\n```\nI am ready to act.'))
    assert connection.staged['phase'] == 'ACT' and connection.staged['transition'] == 'CHILD_READY'
    assert executor.jobs == []


def test_truncated_readiness_does_not_dispatch_or_skip_budget(tmp_path):
    connection, executor, unused_game = staged_bridge(tmp_path)
    connection.after_generation(dict(response('Ready to act'), truncated=True))
    assert connection.staged['phase'] == 'THINK' and executor.jobs == []


def test_two_genuine_successes_switch_to_one_think_segment(tmp_path):
    connection, executor, unused_game = staged_bridge(tmp_path)
    act_and_collect(connection, executor)
    assert connection.staged['allocation']['think_segments_budget'] == 3
    act_and_collect(connection, executor)
    assert connection.staged['allocation']['mode'] == 'CONSOLIDATE_SUCCESS'
    assert connection.staged['allocation']['think_segments_budget'] == 1
    connection.after_generation(response('Consider the current evidence.'))
    assert connection.staged['phase'] == 'ACT'
    assert connection.staged['transition'] == 'BUDGET_EXHAUSTED'


def test_repeated_actual_failures_keep_three_think_segments(tmp_path):
    class FailedGame(FakeGame):
        def submit_caption(self, contest_id, text):
            self.calls.append((contest_id, text))
            return dict(ok=True, accepted=False, status='rejected')

    connection, executor, unused_game = staged_bridge(tmp_path, game=FailedGame())
    for unused in range(2):
        act_and_collect(connection, executor)
    assert connection.staged['allocation']['mode'] == 'SUSTAINED_FAILURE'
    for expected in ('THINK', 'THINK', 'ACT'):
        connection.after_generation(response('Consider another hypothesis.'))
        assert connection.staged['phase'] == expected


def test_awaits_real_feedback_with_deadline_and_no_generation_or_retry(tmp_path, monkeypatch):
    connection, executor, game = staged_bridge(tmp_path)
    connection.after_generation(response('Ready to act'))
    connection.after_generation(response(json.dumps(batch())))
    future = executor.jobs[0][0]
    timeouts = []

    def timed_out(*, timeout):
        timeouts.append(timeout)
        raise TimeoutError('synthetic unresolved receipt')

    with monkeypatch.context() as patch:
        patch.setattr(future, 'result', timed_out)
        with pytest.raises(TimeoutError):
            connection.before_generation(deadline_unix=25, now=lambda: 10)
    timeout = json.loads(next((tmp_path / 'tool_timeouts').glob('*.json')).read_text())
    assert timeout['status'] == 'UNKNOWN_AFTER_DISPATCH'
    assert timeout['accepted'] is None and timeout['sleep_allowed'] is False and timeout['retry_allowed'] is False
    assert timeouts == [15] and game.calls == [] and connection.feedback == []
    called = []
    with pytest.raises(ValueError, match='await_actual_feedback'):
        connection.generate(lambda *args, **kwargs: called.append(True), [], max_new_tokens=512)
    assert called == [] and len(executor.jobs) == 1
    executor.complete(0)
    connection.before_generation(deadline_unix=25, now=lambda: 10)
    connection.before_generation(deadline_unix=25, now=lambda: 10)
    assert len(executor.jobs) == len(game.calls) == len(connection.feedback) == 1


@pytest.mark.parametrize('deadline', [None, float('inf'), float('nan'), True, 9])
def test_wait_requires_finite_live_deadline(tmp_path, deadline):
    connection, executor, game = staged_bridge(tmp_path)
    connection.after_generation(response('Ready to act'))
    connection.after_generation(response(json.dumps(batch())))
    with pytest.raises(ValueError, match='feedback_'):
        connection.before_generation(deadline_unix=deadline, now=lambda: 10)
    assert len(executor.jobs) == 1 and game.calls == []


@pytest.mark.parametrize('timeout', [0, -1, True, None, float('nan'), float('inf')])
def test_feedback_timeout_must_be_explicit_positive_finite_seconds(timeout):
    with pytest.raises(ValueError, match='positive_finite_feedback_timeout'):
        DevelopmentConfig('UNPARENTED', outcome_policy=OUTCOME_POLICY, feedback_timeout_seconds=timeout)


@pytest.mark.parametrize('hardwall, expected_deadline', [(1000, 12), (11, 11)])
def test_action_budget_is_fixed_at_dispatch_and_never_renewed(tmp_path, monkeypatch, hardwall, expected_deadline):
    clock = [10.0]
    connection, executor, game = staged_bridge(tmp_path, feedback_timeout_seconds=2, now=lambda: clock[0])
    connection.after_generation(response('Ready to act'))
    connection.after_generation(response(json.dumps(batch())))
    future = executor.jobs[0][0]
    waits = []

    def not_done(*, timeout):
        waits.append(timeout)
        raise TimeoutError('synthetic bounded wait')

    monkeypatch.setattr(future, 'result', not_done)
    with pytest.raises(TimeoutError):
        connection.before_generation(deadline_unix=hardwall, now=lambda: clock[0])
    clock[0] += 0.5
    with pytest.raises(TimeoutError):
        connection.before_generation(deadline_unix=hardwall + 1000, now=lambda: clock[0])
    assert waits == [expected_deadline - 10, expected_deadline - 10.5]
    assert connection.staged['feedback_started_unix'] == 10
    assert connection.staged['feedback_deadline_unix'] == expected_deadline
    clock[0] = expected_deadline
    with pytest.raises(ValueError, match='feedback_deadline_reached'):
        connection.before_generation(deadline_unix=hardwall + 2000, now=lambda: clock[0])
    receipt = json.loads(next((tmp_path / 'tool_timeouts').glob('*.json')).read_text())
    assert receipt['deadline_unix'] == expected_deadline and receipt['feedback_started_unix'] == 10
    assert receipt['physical_cancellation_claimed'] is False
    assert receipt['provider_may_continue_until_its_guard'] is True
    assert not future.cancelled() and len(executor.jobs) == 1 and game.calls == []


def test_native_feedback_clock_starts_once_after_commit_before_tool_submission(tmp_path):
    clock = [10.0]
    connection, executor, unused_game = staged_bridge(tmp_path, feedback_timeout_seconds=0.5, now=lambda: clock[0])
    connection.after_generation(response('Ready to act'))
    with connection.native_generation():
        connection.after_generation(response(json.dumps(batch())))
        assert connection.staged['feedback_started_unix'] is None and executor.jobs == []
        clock[0] = 11
    assert connection.staged['feedback_started_unix'] == 11
    assert connection.staged['feedback_deadline_unix'] == 11.5
    executor.complete(0)
    connection.before_generation(deadline_unix=1000, now=lambda: 11.1)
    assert connection.staged['feedback_started_unix'] is None
    assert connection.staged['feedback_deadline_unix'] is None
    assert connection.checkpoint()['staged']['feedback_timeout_seconds'] == 0.5


def test_learn_tokens_are_measured_without_dispatch_and_restored(tmp_path):
    connection, executor, game = staged_bridge(tmp_path / 'first')
    connection.after_generation(response('Think about evidence.', 3))
    with connection.learning_phase():
        connection.after_generation(response(json.dumps(batch()), 5))
    assert executor.jobs == [] and connection.staged['think_segments_used'] == 1
    saved = connection.checkpoint()
    restored, restored_executor, unused_game = staged_bridge(tmp_path / 'second', game=game,
        state=saved, action_state=saved['action_policy'])
    assert restored.checkpoint() == saved
    events = act_and_collect(restored, restored_executor, think_tokens=2, act_tokens=7)
    metrics = json.loads(events[0].text)['outcome_allocation']['stage_tokens']
    assert metrics == {'THINK': 5, 'ACT': 7, 'LEARN': 5}
    assert restored.total_tokens == 17
    assert restored.staged['total_stage_tokens'] == metrics
    assert restored.staged['cycle_metrics'] == {'THINK': 0, 'ACT': 0, 'LEARN': 0}
    assert restored.staged['cycle'] == 1
    assert len(game.calls) == 1 and executor.jobs == []


@pytest.mark.parametrize('outcome, expected', [
    (dict(accepted=True, status='new_pixel'), 'successes'),
    (dict(accepted=True, status='repeat'), 'repeats'),
    (dict(accepted=True, status='new_pixel', replayed=True), 'cached'),
    (dict(accepted=True, status='NEW_PIXEL'), 'unknown'),
    (dict(ok=False, accepted=None), 'unknown'),
    (dict(accepted=False, status='rejected'), 'evaluated'),
])
def test_single_caption_accounted_without_inventing_child_direction(tmp_path, outcome, expected):
    class OutcomeGame(FakeGame):
        def submit_caption(self, contest_id, text):
            self.calls.append((contest_id, text))
            return dict(outcome, private_evaluator_answer='never release')

    connection, executor, game = staged_bridge(tmp_path, game=OutcomeGame())
    events = act_and_collect(connection, executor, dict(tool='submit_caption', contest_id='a', text='own caption'))
    result = json.loads(events[0].text)
    assert result['outcome_allocation']['observation'][expected] == 1
    assert result['outcome_allocation']['stage_tokens'] == {'THINK': 2, 'ACT': 3, 'LEARN': 0}
    assert 'private_evaluator_answer' not in events[0].text
    assert connection.action_policy.previous == {} and len(game.calls) == 1


def test_unknown_partial_batch_is_not_retried_or_called_a_failure(tmp_path):
    class PartialGame(FakeGame):
        def submit_caption(self, contest_id, text):
            self.calls.append((contest_id, text))
            if len(self.calls) == 2:
                raise RuntimeError('synthetic unknown after dispatch')
            return dict(accepted=True, status='new_pixel')

    connection, executor, game = staged_bridge(tmp_path, game=PartialGame())
    events = act_and_collect(connection, executor, batch(captions=['own 1', 'own 2', 'own 3']))
    observed = json.loads(events[0].text)['outcome_allocation']['observation']
    assert observed['successes'] == observed['unknown'] == observed['not_dispatched'] == 1
    connection.before_generation()
    assert len(executor.jobs) == 1 and len(game.calls) == 2


def test_inspection_is_actual_feedback_not_caption_success(tmp_path):
    connection, executor, game = staged_bridge(tmp_path)
    events = act_and_collect(connection, executor, dict(tool='inspect_image', contest_id='a', question='What?'))
    assert 'synthetic fixture square' in events[0].text
    assert 'outcome_allocation' not in json.loads(events[0].text)
    assert connection.action_policy.snapshot()['allocation']['environments'] == {}
    assert len(game.calls) == 1


@pytest.mark.parametrize('raw', ['no action', json.dumps([batch(), batch()]), json.dumps(batch('not_public'))])
def test_invalid_act_gets_explicit_non_dispatch_feedback(tmp_path, raw):
    connection, executor, game = staged_bridge(tmp_path)
    connection.after_generation(response('Ready to act'))
    connection.after_generation(response(raw))
    events = connection.before_generation(deadline_unix=20, now=lambda: 10)
    assert json.loads(events[0].text)['dispatched'] is False
    assert executor.jobs == [] and game.calls == []
    assert connection.staged['allocation']['mode'] == 'GUIDED_EXPLORATION'


def test_parent_gets_two_way_stop_question_and_only_public_allocation(tmp_path):
    connection, executor, game = staged_bridge(tmp_path, lane='PARENTED')
    game.private_caption = 'synthetic secret must stay private'
    connection.before_generation()
    request = executor.jobs[0][2][0]
    assert PARENT_STOP_CHECK in request['messages'][0]['content']
    visible = json.loads(request['messages'][1]['content'])['outcome_allocation']
    assert set(visible) == {'schema', 'mode', 'instruction', 'think_segments_budget', 'rates', 'evidence'}
    assert game.private_caption not in json.dumps(request)
    assert 'previous' not in visible and 'game' not in visible
    allocation = deepcopy(visible)
    allocation['evidence']['caption'] = game.private_caption
    with pytest.raises(ValueError, match='aggregate_evidence_only'):
        allocation_view(allocation)


def test_resolved_checkpoint_restores_success_and_next_receipt_ids(tmp_path):
    connection, executor, game = staged_bridge(tmp_path / 'first')
    for unused in range(2):
        act_and_collect(connection, executor)
    snapshot = json.loads(json.dumps(connection.checkpoint()))
    restored, restored_executor, unused_game = staged_bridge(tmp_path / 'second', game=game, state=snapshot)
    assert restored.staged['allocation']['think_segments_budget'] == 1
    assert restored.generation_count == 4 and restored.total_tokens == 10
    restored.after_generation(response('Think.'))
    restored.after_generation(response(json.dumps(batch())))
    assert restored.pending[0][0] == '00000005_00'
    assert len(restored_executor.jobs) == 1


def test_restored_active_contest_is_not_first_manifest_entry(tmp_path):
    connection, executor, game = staged_bridge(tmp_path / 'first')
    for unused in range(2):
        act_and_collect(connection, executor, batch('b'))
    connection.after_generation(response('Plan for this contest.'))
    saved = connection.checkpoint()
    restored, unused_executor, unused_game = staged_bridge(tmp_path / 'second', game=game, state=saved)
    assert restored.staged['contest_id'] == 'b' and restored.staged['phase'] == 'ACT'
    assert restored.staged['allocation']['mode'] == 'CONSOLIDATE_SUCCESS'
    prompt = restored.before_generation()[-1].text
    assert 'only to contest b:' in prompt and 'only to contest a:' not in prompt
    assert 'contests' not in saved['staged']


def test_cached_duplicates_do_not_create_success_or_one_think_budget(tmp_path):
    class CachedGame(FakeGame):
        def submit_caption(self, contest_id, text):
            self.calls.append((contest_id, text))
            return dict(accepted=True, status='new_pixel', replayed=True)

    connection, executor, unused_game = staged_bridge(tmp_path, game=CachedGame())
    for unused in range(3):
        act_and_collect(connection, executor)
    allocation = connection.staged['allocation']
    assert allocation['mode'] == 'REDUNDANT_DATA' and allocation['think_segments_budget'] == 3
    assert allocation['evidence']['lifetime']['successes'] == 0
    assert allocation['evidence']['lifetime']['cached'] == 3
    assert allocation['rates']['lifetime']['success_rate'] is None


@pytest.mark.parametrize('action, requested', [
    (dict(tool='caption_batch', contest_id='a', count=3), 3),
    (dict(tool='caption_batch', contest_id='a', count='unknown'), 0),
    (batch(captions=['own caption'] * 11), 11),
])
def test_invalid_or_oversized_batch_uses_shared_not_dispatched_accounting(tmp_path, action, requested):
    connection, executor, game = staged_bridge(tmp_path)
    events = act_and_collect(connection, executor, action)
    observation = json.loads(events[0].text)['outcome_allocation']['observation']
    assert observation['requested'] == observation['not_dispatched'] == requested
    assert observation['evaluated'] == observation['successes'] == 0
    assert game.calls == []
    assert connection.staged['allocation']['mode'] == 'UNOBSERVED_OUTCOME'


def test_single_caption_unknown_exception_is_accounted_without_retry(tmp_path):
    class BrokenGame(FakeGame):
        def submit_caption(self, contest_id, text):
            self.calls.append((contest_id, text))
            raise RuntimeError('synthetic unknown')

    connection, executor, game = staged_bridge(tmp_path, game=BrokenGame())
    events = act_and_collect(connection, executor, dict(tool='submit_caption', contest_id='a', text='own'))
    result = json.loads(events[0].text)
    assert result['outcome_allocation']['observation']['unknown'] == 1
    assert result['outcome_allocation']['running_success_rate'] is None
    connection.before_generation()
    assert len(game.calls) == len(executor.jobs) == 1


def test_action_state_only_can_enable_existing_caption_policy_without_fake_tokens(tmp_path):
    connection, executor, unused_game = staged_bridge(tmp_path / 'first')
    act_and_collect(connection, executor)
    restored, unused_executor, unused_game = staged_bridge(tmp_path / 'second',
        action_state=connection.action_policy.snapshot())
    assert restored.action_policy.snapshot() == connection.action_policy.snapshot()
    assert restored.total_tokens == 0 and restored.generation_count == 0


def test_conflicting_action_state_is_rejected(tmp_path):
    connection, unused_executor, game = staged_bridge(tmp_path / 'first')
    with pytest.raises(ValueError, match='action_state_mismatch'):
        staged_bridge(tmp_path / 'second', game=game, state=connection.checkpoint(), action_state={})


def test_feedback_late_at_deadline_is_not_consumed_as_on_time(tmp_path):
    connection, executor, game = staged_bridge(tmp_path)
    connection.after_generation(response('Ready to act'))
    connection.after_generation(response(json.dumps(batch())))
    executor.complete(0)
    clock = iter([10, 21])
    with pytest.raises(ValueError, match='feedback_deadline_reached'):
        connection.before_generation(deadline_unix=20, now=lambda: next(clock))
    assert connection.staged['phase'] == 'AWAIT_FEEDBACK' and connection.feedback == []
    assert len(game.calls) == len(executor.jobs) == len(connection.pending) == 1


def test_pending_action_state_cannot_be_replayed_on_restore(tmp_path):
    connection, executor, game = staged_bridge(tmp_path / 'first')
    connection.after_generation(response('Ready to act'))
    connection.after_generation(response(json.dumps(batch())))
    with pytest.raises(ValueError, match='unresolved_dispatch_state_never_replayed'):
        staged_bridge(tmp_path / 'second', game=game, state=connection.checkpoint())
    assert len(executor.jobs) == 1 and game.calls == []


def test_pending_parent_cannot_be_replayed_on_restore(tmp_path):
    connection, executor, game = staged_bridge(tmp_path / 'first', lane='PARENTED')
    connection.before_generation()
    with pytest.raises(ValueError, match='unresolved_dispatch_state_never_replayed'):
        staged_bridge(tmp_path / 'second', game=game, lane='PARENTED', state=connection.checkpoint())
    assert len(executor.jobs) == 1


@pytest.mark.parametrize('mutation', [
    lambda state: state.update(schema='old'),
    lambda state: state.update(child_tokens=True),
    lambda state: state.update(outcome_policy=None),
    lambda state: state['staged'].update(phase='LEARN'),
    lambda state: state['staged'].update(think_segments_used=3),
    lambda state: state['staged']['total_stage_tokens'].update(THINK=99),
    lambda state: state['staged']['allocation'].update(think_segments_budget=2),
    lambda state: state['staged']['cycle_metrics'].update(ACT=None),
])
def test_corrupt_or_different_version_staged_state_refuses(tmp_path, mutation):
    connection, unused_executor, game = staged_bridge(tmp_path / 'first')
    state = connection.checkpoint()
    mutation(state)
    with pytest.raises(ValueError):
        staged_bridge(tmp_path / 'second', game=game, state=state)


def test_missing_token_ids_are_not_reported_as_zero(tmp_path):
    connection, executor, unused_game = staged_bridge(tmp_path)
    with pytest.raises(ValueError, match='actual_generated_token_ids'):
        connection.after_generation(dict(raw='Ready to act'))
    assert executor.jobs == [] and connection.total_tokens == 0


@pytest.mark.parametrize('think_segments', [1, 3])
def test_native_staged_loop_sleeps_only_after_cycle_without_extra_presleep_generation(tmp_path, think_segments):
    from organism_v6.orch_r124_train_history import TrainHistory
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest

    class InlineExecutor:
        def submit(self, callback, *arguments):
            future = Future()
            future.set_result(callback(*arguments))
            return future

    class Journal:
        def __init__(self):
            self.records = []

        def record(self, kind, document):
            self.records.append((kind, document))

        def read_inbox(self):
            return []

    class Child:
        def __init__(self):
            self.plan = dict(segment_tokens=512, segments_per_sleep=2, hard_end_unix=time.time() + 60,
                compaction_invitation='LEARN: consolidate only your own evidence, without tools.')
            think = ['Ready to act'] if think_segments == 1 else ['Explore.', 'Reconsider.', 'Choose a test.']
            self.outputs = iter((think + [json.dumps(batch())]) * 2)
            self.calls = []
            self.optimizer_steps = 0

        def generate(self, messages, **limits):
            self.calls.append((messages, limits))
            return response(next(self.outputs), 4)

        def count_tokens(self, messages):
            return sum(len(message['content'].split()) + 4 for message in messages)

    child, journal = Child(), Journal()
    stream = ContinualStream(TrainHistory(system_prompt='Synthetic only.', birth_prompt='Use own captions.'),
        context_limit=8192, segment_tokens=512, segments_per_sleep=2,
        deadline_unix=child.plan['hard_end_unix'], model_state_sha256='f' * 64)
    connection, unused_executor, game = staged_bridge(tmp_path / 'tools', executor=InlineExecutor())
    row_counts = []

    def synthetic_finish(child, stream, journal, anchors, root, cycle):
        assert connection.staged['phase'] == 'THINK' and connection.staged['think_segments_used'] == 0
        assert connection.staged['cycle'] == cycle and not connection.pending
        row_counts.append(len(stream.pending_rows()))
        child.optimizer_steps += len(stream.pending_rows())
        stream.sleep_frontier = len(stream.rows)
        return dict(synthetic=True, cycle=cycle)

    def forbidden_presleep(*arguments):
        raise AssertionError('R193 forbids an extra presleep generation')

    native = SimpleNamespace(prepare_sleep=forbidden_presleep, digest=digest, finish_sleep=synthetic_finish,
        fresh_readout=lambda *arguments: None)
    result = drive_native(child, stream, journal, [], tmp_path.resolve(), connection, 'synthetic-plan',
        native_module=native)
    assert result['complete'] and row_counts == [think_segments + 1] * 2
    assert len(child.calls) == 2 * (think_segments + 1) and len(game.calls) == 2
    assert all(limits == dict(max_new_tokens=512, deadline_unix=child.plan['hard_end_unix'])
        for unused_messages, limits in child.calls)
    assert all(not row['prefix_loss'] and row['target_loss'] and not row['append_eos'] for row in stream.rows)
    assert all(document['render_receipt']['all_history_tokens_masked']
        for kind, document in journal.records if kind == 'REQUEST')
    assert all(row['actor'] == 'child' for row in stream.rows)
    assert any('THINK:' in message['content'] for message in stream.rows[0]['prefix'])
    assert any('ACT:' in message['content'] for message in stream.rows[think_segments]['prefix'])
    assert any('outcome_allocation' in message['content'] for message in stream.rows[think_segments + 1]['prefix'])
    assert connection.staged['total_stage_tokens'] == {'THINK': 8 * think_segments, 'ACT': 8, 'LEARN': 0}
    assert connection.feedback[0]['outcome_allocation']['stage_tokens'] == {
        'THINK': 4 * think_segments, 'ACT': 4, 'LEARN': 0}
    assert connection.feedback[1]['outcome_allocation']['stage_tokens'] == {
        'THINK': 4 * think_segments, 'ACT': 4, 'LEARN': 0}
    saved = json.loads((tmp_path / 'caption_game/sleep_000002.json').read_text())
    assert saved['schema'] == STAGED_SCHEMA and saved['staged']['cycle_metrics']['LEARN'] == 0
    assert result['pixel_readout']['cumulative_coverage'] == 2
    assert all(not document['extra_presleep_generation'] for kind, document in journal.records
        if kind == 'R189_SLEEP_BOUNDARY')


def test_fixed_child_token_windows_count_new_pixels_not_acceptance_rate(tmp_path):
    class SequenceGame(FakeGame):
        def submit_caption(self, contest_id, text):
            self.calls.append((contest_id, text))
            return [dict(accepted=True, status='new_pixel'), dict(accepted=True, status='repeat'),
                dict(accepted=True, status='new_pixel', replayed=True), dict(accepted=True, status='new_pixel'),
                dict(accepted=False, status='rejected')][len(self.calls) - 1]

    connection, executor, game = staged_bridge(tmp_path / 'first', game=SequenceGame(), window_tokens=10)
    for unused in range(5):
        act_and_collect(connection, executor, dict(tool='submit_caption', contest_id='a', text='own caption'))
    report = connection.pixel_readout()
    assert report['primary_metric'] == 'NEW_ACCEPTED_PIXELS_PER_CHILD_TOKEN_WINDOW'
    assert report['window_tokens'] == 10 and report['cumulative_coverage'] == 2
    assert [row['new_accepted_pixels'] for row in report['windows']] == [1, 1, 0]
    assert [row['child_tokens'] for row in report['windows']] == [10, 10, 5]
    assert [row['status'] for row in report['windows']] == ['FULL', 'FULL', 'UNDERFILLED']
    assert [row['cumulative_coverage'] for row in report['windows']] == [1, 2, 2]
    assert [row['new_accepted_pixels_per_child_token'] for row in report['windows']] == [0.1, 0.1, 0.0]
    assert report['new_accepted_pixels_per_child_token'] == 2 / 25
    assert report['outcome_attribution'] == 'ACT_END_CHILD_TOKEN_WINDOW'
    restored, unused_executor, unused_game = staged_bridge(tmp_path / 'second', game=game,
        state=connection.checkpoint(), window_tokens=10)
    assert restored.pixel_readout() == report
    with pytest.raises(ValueError, match='fixed_pixel_window_state'):
        staged_bridge(tmp_path / 'third', game=game, state=connection.checkpoint(), window_tokens=1000)


def test_default_window_is_provisional_thousand_tokens_and_final_window_underfilled(tmp_path):
    connection, executor, unused_game = staged_bridge(tmp_path)
    act_and_collect(connection, executor)
    report = connection.pixel_readout()
    assert report['window_tokens'] == 1000 and report['provisional_developer_default']
    assert len(report['windows']) == 1 and report['windows'][0]['status'] == 'UNDERFILLED'
    assert report['windows'][0]['child_tokens'] == 5 and report['windows'][0]['new_accepted_pixels'] == 1
    prompt = connection.before_generation()[-1].text
    assert 'not acceptance-rate maximization' in prompt and 'bounded breadth' in prompt


def test_exportable_stage_and_cycle_metadata_omit_caption_and_pixel_identity(tmp_path):
    connection, executor, unused_game = staged_bridge(tmp_path)
    act_and_collect(connection, executor, batch(captions=['synthetic private caption text']))
    stage_files = sorted((tmp_path / 'stage_events').glob('*.json'))
    assert [json.loads(path.read_text())['stage'] for path in stage_files] == ['THINK', 'ACT']
    assert [json.loads(path.read_text())['generated_tokens'] for path in stage_files] == [2, 3]
    cycle_path = next((tmp_path / 'action_cycles').glob('*.json'))
    cycle = json.loads(cycle_path.read_text())
    assert cycle['stage_tokens'] == {'THINK': 2, 'ACT': 3, 'LEARN': 0}
    assert cycle['child_token_start'] == 0 and cycle['child_token_end'] == 5
    assert cycle['observation']['successes'] == 1
    assert cycle['pixel_readout']['cumulative_coverage'] == 1
    assert not cycle['caption_text_included']
    assert all('synthetic private caption text' not in path.read_text() for path in stage_files + [cycle_path])


@pytest.mark.parametrize('window', [0, -1, True, 1.5, 30001])
def test_outcome_window_is_explicit_positive_integer_within_total_child_budget(window):
    with pytest.raises(ValueError, match='positive_bounded_outcome_window'):
        DevelopmentConfig('UNPARENTED', outcome_policy=OUTCOME_POLICY, outcome_window_tokens=window)


def test_native_action_cannot_dispatch_before_response_commit(tmp_path):
    connection, executor, game = staged_bridge(tmp_path)
    connection.after_generation(response('Ready to act'))
    with connection.native_generation():
        connection.after_generation(response(json.dumps(batch())))
        assert executor.jobs == [] and game.calls == []
    assert len(executor.jobs) == 1 and game.calls == []
    executor.complete(0)
    assert len(game.calls) == 1


def test_failed_native_commit_preserves_unresolved_action_without_tool_dispatch(tmp_path):
    connection, executor, game = staged_bridge(tmp_path)
    connection.after_generation(response('Ready to act'))
    child = SimpleNamespace(plan=dict(segment_tokens=512, segments_per_sleep=2, hard_end_unix=time.time() + 60),
        count_tokens=lambda messages: 20, generate=lambda *args, **kwargs: response(json.dumps(batch())),
        optimizer_steps=0)
    journal = SimpleNamespace(read_inbox=lambda: [], record=lambda *args: None)

    def failed_step(generate, *arguments, **keywords):
        generate([], max_new_tokens=512, deadline_unix=child.plan['hard_end_unix'])
        raise RuntimeError('synthetic response commit failed')

    stream = SimpleNamespace(step=failed_step)
    with pytest.raises(RuntimeError, match='commit failed'):
        drive_native(child, stream, journal, [], tmp_path, connection, 'synthetic-plan',
            native_module=SimpleNamespace())
    assert executor.jobs == [] and game.calls == []
    assert connection.staged['phase'] == 'AWAIT_FEEDBACK'
    assert not connection.defer_tools and connection.deferred_action is None
    with pytest.raises(ValueError, match='unresolved_dispatch_state_never_replayed'):
        staged_bridge(tmp_path / 'restore', game=game, state=connection.checkpoint())


@pytest.mark.parametrize('policy', ['', False, {}, 'R193_CONTINUITY_V2'])
def test_continuity_requires_exact_independent_opt_in(policy):
    with pytest.raises(ValueError, match='known_continuity_policy'):
        DevelopmentConfig('UNPARENTED', continuity_policy=policy)


@pytest.mark.parametrize('outcome_policy', [None, OUTCOME_POLICY])
def test_continuity_prompts_are_open_and_caption_specific(tmp_path, outcome_policy):
    connection, executor, unused_game = staged_bridge(tmp_path, outcome_policy=outcome_policy,
        continuity_policy=CONTINUITY_POLICY)
    think = connection.before_generation()[-1].text
    assert all(word in think for word in ('PRESERVE', 'CHANGE', 'EXPECTED', 'STANDING PRACTICE'))
    assert 'Nothing changed is an acceptable answer' in think
    assert 'without reciting a fixed field block' in think
    connection.after_generation(response('Ready to act'))
    act = connection.before_generation()[-1].text
    assert 'Check in one line' in act and 'Deliberately continue' in act
    assert 'caption_batch' in act and 'submit_caption' in act
    assert 'Python' not in act and 'CPU' not in act
    assert executor.jobs == []


def test_continuity_parent_suffix_is_separate_from_outcome_allocator(tmp_path):
    connection, executor, unused_game = staged_bridge(tmp_path, lane='PARENTED', outcome_policy=None,
        continuity_policy=CONTINUITY_POLICY)
    connection.before_generation()
    request = executor.jobs[0][2][0]
    assert PARENT_QUESTION in request['messages'][0]['content']
    assert PARENT_STOP_CHECK not in request['messages'][0]['content']
    assert 'outcome_allocation' not in json.loads(request['messages'][1]['content'])
    legacy, legacy_executor, unused_game = bridge(tmp_path / 'legacy', lane='PARENTED')
    legacy.before_generation()
    assert PARENT_QUESTION not in legacy_executor.jobs[0][2][0]['messages'][0]['content']
    assert 'continuity_policy' not in legacy.checkpoint()


def test_continuity_without_outcome_uses_fixed_budget_and_real_pixel_observations(tmp_path):
    connection, executor, game = staged_bridge(tmp_path / 'first', outcome_policy=None,
        continuity_policy=CONTINUITY_POLICY)
    for unused in range(2):
        events = act_and_collect(connection, executor)
        assert 'outcome_allocation' not in json.loads(events[0].text)
    assert connection.staged['allocation'] is None and connection._think_budget() == 3
    assert connection.pixel_readout()['cumulative_coverage'] == 2
    state = connection.checkpoint()
    restored, unused_executor, unused_game = staged_bridge(tmp_path / 'second', game=game, state=state,
        outcome_policy=None, continuity_policy=CONTINUITY_POLICY)
    assert restored.checkpoint() == state
    with pytest.raises(ValueError, match='bridge_state_schema'):
        staged_bridge(tmp_path / 'wrong', game=game, state=state)


def test_empty_pixel_window_has_no_invented_rate(tmp_path):
    connection, unused_executor, unused_game = staged_bridge(tmp_path)
    report = connection.pixel_readout()
    assert report['windows'] == [] and report['new_accepted_pixels_per_child_token'] is None


class InlineExecutor:
    def submit(self, callback, *arguments):
        future = Future()
        future.set_result(callback(*arguments))
        return future


def real_journal_fixture(tmp_path, *, outputs=None, executor=None, lane='UNPARENTED',
                         continuity_policy=CONTINUITY_POLICY, outcome_policy=OUTCOME_POLICY):
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r124_train_history import TrainHistory
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest

    class Child:
        def __init__(self):
            self.plan = dict(segment_tokens=512, segments_per_sleep=2, hard_end_unix=time.time() + 60)
            self.optimizer_steps = 0
            self.outputs = iter(outputs or ['Ready to act', json.dumps(batch()), 'Ready to act', json.dumps(batch())])
            self.calls = []

        def count_tokens(self, messages):
            return sum(len(message['content'].split()) + 4 for message in messages)

        def generate(self, messages, **arguments):
            self.calls.append(deepcopy(messages))
            output = next(self.outputs)
            return deepcopy(output) if type(output) is dict else response(output, 4)

    game = FakeGame()
    game.agent_id = 'synthetic-caption-life'
    connection, executor, game = staged_bridge(tmp_path / 'tools', game=game, lane=lane,
        executor=executor or InlineExecutor(), outcome_policy=outcome_policy, continuity_policy=continuity_policy)
    child = Child()
    stream = ContinualStream(TrainHistory(system_prompt='Synthetic CPU test.', birth_prompt='Explore captions.'),
        context_limit=8192, segment_tokens=512, segments_per_sleep=2, deadline_unix=child.plan['hard_end_unix'],
        model_state_sha256='f' * 64)
    journal = StreamJournal(tmp_path / 'journal', create=True)
    journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))

    def finish(child, stream, journal, anchors, root, cycle):
        rows = stream.pending_rows()
        child.optimizer_steps += len(rows)
        receipt = dict(status='COMPLETE', synthetic=True, cycle=cycle, new_row_sha256=[row['source_sha256'] for row in rows],
            optimizer_steps=len(rows), checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))
        stream.commit_sleep(receipt, journal.record)
        return dict(synthetic=True, cycle=cycle)

    def forbidden_presleep(*arguments):
        raise AssertionError('no additional presleep generation')

    native = SimpleNamespace(digest=digest, finish_sleep=finish, prepare_sleep=forbidden_presleep,
        fresh_readout=lambda *arguments: None)
    return connection, executor, game, child, stream, journal, native


def journal_records(journal):
    return [json.loads(path.read_text()) for path in sorted((journal.root / 'records').glob('*.json'))
        if '.intent.' not in path.name]


@pytest.mark.parametrize('outcome_policy', [None, OUTCOME_POLICY])
def test_real_journal_saves_typed_child_state_and_exports_actual_stage_rows(tmp_path, outcome_policy):
    from organism_v6.orch_r125_continual_stream import ContinualStream

    outputs = [
        'POSSIBILITY [contrast]: Try a different angle.\nNext intention: compare own attempts.\nReady to act.',
        'EXPERIMENT [contrast]: Try one contrast and expect a new pixel.\n' + json.dumps(batch()),
        'STANDING PRACTICE [contrast]: Keep contrast provisionally; one observation is weak.\nReady to act.',
        json.dumps(batch('b')),
    ]
    connection, unused_executor, game, child, stream, journal, native = real_journal_fixture(
        tmp_path, outputs=outputs, lane='PARENTED', outcome_policy=outcome_policy)
    connection.parent = lambda request: dict(guidance='STANDING PRACTICE [parentonly]: parent input, not child state.',
        object_id='synthetic-parent')
    try:
        result = drive_native(child, stream, journal, [], tmp_path, connection, 'synthetic-plan', native_module=native)
        assert result['complete'] and len(child.calls) == 4 and len(game.calls) == 2
        restored_stream = ContinualStream.restore(**journal.latest_checkpoint())
        assert restored_stream.history.working_state == stream.history.working_state
        entries = {entry['id']: entry for entry in restored_stream.history.working_state['entries']}
        assert entries['contrast']['text'].startswith('STANDING PRACTICE [contrast]:')
        assert entries['contrast']['source_event_id'] == stream.rows[2]['event_id']
        assert entries['contrast']['source_sha256'] == stream.rows[2]['source_sha256']
        assert entries['next_intention']['text'] == 'compare own attempts.'
        assert 'parentonly' not in entries
        assert all(not row['prefix_loss'] and row['target_loss'] for row in stream.rows)
        assert any('Working state' in message['content'] or 'POSSIBILITY [contrast]' in message['content']
            for message in stream.rows[1]['prefix'])
        after_sleep_state = next(message['content'] for message in stream.rows[2]['prefix']
            if message['content'].startswith('Child working state (not a verified fact)'))
        assert 'EXPERIMENT [contrast]: Try one contrast and expect a new pixel.' in after_sleep_state
        assert 'STANDING PRACTICE [contrast]' not in after_sleep_state
        following_act_state = next(message['content'] for message in stream.rows[3]['prefix']
            if message['content'].startswith('Child working state (not a verified fact)'))
        assert 'STANDING PRACTICE [contrast]: Keep contrast provisionally; one observation is weak.' in following_act_state
        assert 'parentonly' not in after_sleep_state and 'parentonly' not in following_act_state
        records = journal_records(journal)
        commits = [record for record in records if record['kind'] == 'COMMITTED' and 'segment' in record['document']]
        assert commits[0]['document']['consolidation']['status'] == 'UPDATED'
        assert commits[0]['document']['state']['state']['history']['working_state']['revision'] == 1
        assert all(record['document']['render_receipt']['all_history_tokens_masked']
            for record in records if record['kind'] == 'REQUEST')
        assert not any(record['kind'] == 'R191_CAPTION_EXPORT_FAILED' for record in records)
        dataset = ExplorationDataset(journal.root / 'exploration', game.agent_id)
        rows = list(dataset.iter_rows())
        assert [row['stage'] for row in rows] == ['THINK', 'ACT', 'THINK', 'ACT']
        assert rows[0]['outcome'] is None and rows[2]['outcome'] is None
        assert rows[1]['outcome']['feedback'][0]['result']['status'] == 'new_pixel'
        assert rows[0]['parent_turns'] and all(turn['target_loss'] is False and turn['source_id']
            for turn in rows[0]['parent_turns'])
        assert rows[0]['state_before']['state']['rows'] == []
        assert rows[0]['state_after']['state']['rows'][0]['target'] == outputs[0]
        assert rows[1]['action']['raw'] == outputs[1] and rows[1]['action']['token_ids'] == [0, 1, 2, 3]
        for row in rows:
            for kind in ('request', 'response', 'committed'):
                source = row['source'][kind]
                actual = json.loads(Path(source['path']).read_text())
                assert actual['sha256'] == source['sha256'] and actual['kind'].lower() == kind
        saved = json.loads((tmp_path / 'caption_game/sleep_000002.json').read_text())
        assert saved['continuity_policy'] == CONTINUITY_POLICY
        assert len(saved['staged']['buffered_feedback']) == 1
        restored, unused_executor, unused_game = staged_bridge(tmp_path / 'restart', game=game, state=saved,
            lane='PARENTED', executor=InlineExecutor(), outcome_policy=outcome_policy, continuity_policy=CONTINUITY_POLICY)
        events = restored.before_generation()
        assert events[0].phase == 'feedback' and json.loads(events[0].text)['contest_id'] == 'b'
        assert restored.staged['contest_id'] == 'b' and restored.staged['buffered_feedback'] == []
    finally:
        journal.close()


def test_continuity_disabled_does_not_consolidate_status_lines(tmp_path):
    outputs = ['POSSIBILITY [idea]: own tentative idea.\nReady to act', json.dumps(batch())] * 2
    connection, unused_executor, unused_game, child, stream, journal, native = real_journal_fixture(
        tmp_path, outputs=outputs, continuity_policy=None)
    try:
        result = drive_native(child, stream, journal, [], tmp_path, connection, 'synthetic-plan', native_module=native)
        assert result['complete'] and stream.history.working_state['revision'] == 0
        assert 'continuity_policy' not in connection.checkpoint()
        assert all('consolidation' not in record['document'] for record in journal_records(journal)
            if record['kind'] == 'COMMITTED')
    finally:
        journal.close()


def test_overflow_retains_prior_typed_state_and_informs_next_stage(tmp_path):
    outputs = ['POSSIBILITY [idea]: keep this.\nReady to act', json.dumps(batch()),
        'STANDING PRACTICE [idea]: ' + 'x' * 2200 + '\nReady to act', json.dumps(batch())]
    connection, unused_executor, unused_game, child, stream, journal, native = real_journal_fixture(tmp_path, outputs=outputs)
    try:
        result = drive_native(child, stream, journal, [], tmp_path, connection, 'synthetic-plan', native_module=native)
        assert result['complete']
        assert stream.history.working_state['entries'][0]['text'] == 'POSSIBILITY [idea]: keep this.'
        assert any('Your state edit was rejected; prior state is retained' in message['content']
            for message in child.calls[-1])
        third = [record for record in journal_records(journal) if record['kind'] == 'COMMITTED'
            and record['document'].get('segment') == 2][0]
        assert third['document']['consolidation']['status'] == 'REJECTED_PRIOR_STATE_RETAINED'
    finally:
        journal.close()


def test_exporter_errors_are_journaled_without_stopping_learner(tmp_path):
    class BrokenDataset:
        def append(self, row):
            raise OSError('synthetic exporter failure')

    connection, unused_executor, game, child, stream, journal, native = real_journal_fixture(tmp_path)
    try:
        result = drive_native(child, stream, journal, [], tmp_path, connection, 'synthetic-plan',
            native_module=native, exploration_dataset=BrokenDataset())
        assert result['complete'] and len(game.calls) == 2
        failures = [record for record in journal_records(journal) if record['kind'] == 'R191_CAPTION_EXPORT_FAILED']
        assert len(failures) == 4 and all(record['document']['error_type'] == 'OSError' for record in failures)
    finally:
        journal.close()


def test_failed_truncated_response_exports_raw_action_without_dispatch(tmp_path):
    malformed = dict(response(json.dumps(batch())), terminal=False, truncated=True)
    connection, unused_executor, game, child, stream, journal, native = real_journal_fixture(
        tmp_path, outputs=['Ready to act', malformed])
    try:
        with pytest.raises(ValueError, match='cap_flag_matches_tokens'):
            drive_native(child, stream, journal, [], tmp_path, connection, 'synthetic-plan', native_module=native)
        rows = list(ExplorationDataset(journal.root / 'exploration', game.agent_id).iter_rows())
        assert len(rows) == 2 and rows[-1]['stage'] == 'ACT'
        assert rows[-1]['action'] == malformed and rows[-1]['outcome'] is None
        assert not rows[-1]['committed'] and rows[-1]['state_after'] is None
        assert 'response' in rows[-1]['source'] and 'committed' not in rows[-1]['source']
        assert game.calls == [] and len(stream.rows) == 1
    finally:
        journal.close()


def test_timeout_then_late_feedback_appends_new_dataset_row_without_retry(tmp_path):
    class DelayedExecutor(ControlledExecutor):
        def submit(self, callback, *arguments):
            future = super().submit(callback, *arguments)
            original_result = future.result

            def bounded_result(*args, **kwargs):
                if not future.done():
                    raise TimeoutError('synthetic bounded wait')
                return original_result(*args, **kwargs)

            future.result = bounded_result
            return future

    connection, executor, game, child, stream, journal, native = real_journal_fixture(tmp_path, executor=DelayedExecutor())
    try:
        with pytest.raises(TimeoutError):
            drive_native(child, stream, journal, [], tmp_path, connection, 'synthetic-plan', native_module=native)
        dataset = ExplorationDataset(journal.root / 'exploration', game.agent_id)
        before = dataset.path.read_bytes()
        initial = list(dataset.iter_rows())
        assert len(initial) == 2 and initial[-1]['outcome'] is None and game.calls == []
        executor.complete(0)
        rows = list(dataset.iter_rows())
        assert len(rows) == 3 and dataset.path.read_bytes().startswith(before)
        assert rows[-1]['late_feedback_for'] == initial[-1]['row_id']
        assert rows[-1]['row_id'] != initial[-1]['row_id']
        assert rows[-1]['late_feedback_only'] is True
        assert rows[-1]['outcome']['feedback'][0]['result']['accepted'] is True
        assert rows[-1]['status'] == 'LATE_REAL_TOOL_RECEIPT_NO_REDISPATCH'
        assert len(executor.jobs) == len(game.calls) == 1
        assert connection.staged['phase'] == 'AWAIT_FEEDBACK' and stream.sleep_frontier == 0
    finally:
        journal.close()
