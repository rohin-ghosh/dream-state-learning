from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from gpu import orch_r111_route_pair as route
from gpu import orch_r111_route_shared as client
from gpu import orch_r116_shared_learner as coordinator
from test_orch_r111_route_pair import native_shape_engine


def reference(folder):
    folder.mkdir(parents=True)
    result = {}
    for field in ('path', 'optimizer_path'):
        path = folder / (field + '.json')
        coordinator.write(path, dict(kind=field, adapter={}))
        result[field] = str(path)
        result[field + '_sha256'] = coordinator.sha(path)
    return result


def capture(folder, task, branch, checkpoint, ordinal=0, historical=False, phase='experience'):
    response = route.generate(native_shape_engine(), [dict(role='user', content='Actual task')], cap=8)
    call = dict(task_id=task, phase=phase, response=response)
    if not historical:
        call.update(shared_generation=0, shared_checkpoint_sha256=checkpoint['path_sha256'],
                    shared_learner=dict(branch=branch, generation=0,
                                        checkpoint_sha256=checkpoint['path_sha256']))
    path = folder / ('CALL_' + str(ordinal) + '.json')
    coordinator.write(path, call)
    return route.causal.replay_row(call, path, coordinator.sha(path))


@pytest.fixture
def fixture(tmp_path):
    specs = {branch: dict(root=str(tmp_path / branch), train_ids=[branch+'-one', branch+'-two'])
             for branch in coordinator.BRANCHES}
    initial = reference(tmp_path / 'initial')
    prior = dict(optimizer_steps=113, child_token_exposures=None, anchor_token_exposures=700)
    old = capture(tmp_path / 'F1', 'F1-one', 'F1', initial, ordinal=99, historical=True)
    shared_root = tmp_path / 'shared'
    coordinator.initialize(shared_root, specs, initial, excluded_ids=['DEV', 'FINAL'],
                           prior_metrics=prior, initial_history={'F1': [old]})
    bounds = dict(hard_end_unix=9999999999, native_calls=32768, parent_calls=16384, cycles=512)
    adoption = tmp_path / 'ADOPTION.json'
    coordinator.write(adoption, dict(checkpoint=initial, prior_metrics=prior,
                                    branch_bounds={'F1': bounds, 'A1': bounds}))
    plans = {}
    for branch, slot in (('F1', 0), ('A1', 4)):
        root = tmp_path / branch
        coordinator.write(root / 'COHORT.json', dict(train=[dict(id=task) for task in specs[branch]['train_ids']]))
        coordinator.write(root / 'SEALED_FINAL.json', dict(tasks=[dict(id='FINAL')]))
        plans[branch] = dict(physical=slot, held_ids=['DEV'], bounds=bounds, shared_learner=dict(
            branch=branch, root=str(shared_root), config_sha256=coordinator.sha(shared_root / 'CONFIG.json'),
            adoption_path=str(adoption), adoption_sha256=coordinator.sha(adoption)))
    return SimpleNamespace(root=tmp_path, specs=specs, initial=initial, prior=prior, old=old,
                           shared_root=shared_root, plans=plans)


def arrive(fixture, branch):
    rows = [capture(fixture.root / branch, task, branch, fixture.initial, ordinal=index)
            for index, task in enumerate(fixture.specs[branch]['train_ids'])]
    coordinator.submit(fixture.shared_root, branch, 0, fixture.initial['path_sha256'],
                       fixture.specs[branch]['train_ids'], rows)
    return rows


def test_actual_route_response_shape_roundtrip_and_historical_capture_unchanged(fixture):
    session = client.Session(fixture.root / 'F1', fixture.plans['F1'])
    rows = arrive(fixture, 'F1')
    assert rows[0]['append_eos'] is True
    assert coordinator.read(rows[0]['source_call_path'])['response']['input_truncated'] is False
    assert 'shared_generation' not in coordinator.read(fixture.old['source_call_path'])
    assert session.capture_metadata()['shared_generation'] == 0


def test_owner_consolidates_all_eight_preserves_history_and_unknown_totals(fixture):
    session = client.Session(fixture.root / 'F1', fixture.plans['F1'])
    rows = None
    for branch in coordinator.BRANCHES:
        submitted = arrive(fixture, branch)
        if branch == 'F1':
            rows = submitted
    optimizer = object()
    trained = []

    def train(engine, actual_optimizer, new, history, anchors, output, check):
        assert actual_optimizer is optimizer
        assert len(new) == 16 and history == [fixture.old]
        trained.append(True)
        return dict(optimizer_steps=257, child_token_exposures=514, anchor_token_exposures=257)

    result = session.sleep(None, optimizer, [], rows, fixture.specs['F1']['train_ids'],
        fixture.root / 'F1' / 'cycle_0002', lambda output, generation, metrics: reference(output),
        lambda label: None, train_call=train, pause=lambda seconds: pytest.fail('unexpected wait'))
    assert trained == [True]
    assert result['adopted_plus_shared_totals']['optimizer_steps'] == 370
    assert result['adopted_plus_shared_totals']['child_token_exposures'] is None
    assert result['shared_only_totals']['optimizer_steps'] == 257
    assert result['local_optimizer_steps'] == 257


def test_nonowner_waits_and_reloads_without_optimizer(fixture):
    session = client.Session(fixture.root / 'A1', fixture.plans['A1'])
    rows = arrive(fixture, 'A1')
    for branch in coordinator.BRANCHES:
        if branch != 'A1':
            arrive(fixture, branch)
    reloaded = []

    def advance(seconds):
        coordinator.consolidate(fixture.shared_root, 'F1', fixture.initial['path_sha256'],
            None, object(), [], lambda output, generation, metrics: reference(output), lambda label: None,
            train_call=lambda *args: dict(optimizer_steps=7, child_token_exposures=14, anchor_token_exposures=7))

    result = session.sleep(None, None, [], rows, fixture.specs['A1']['train_ids'],
        fixture.root / 'A1' / 'cycle_0001', lambda *args: pytest.fail('nonowner save'), lambda label: None,
        reload_call=lambda engine, checkpoint: reloaded.append(checkpoint), pause=advance)
    assert len(reloaded) == 1 and result['local_optimizer_steps'] == 0
    assert session.capture_metadata()['shared_generation'] == 1


@pytest.mark.parametrize('branch,optimizer', [('F1', None), ('A1', object())])
def test_wrong_optimizer_owner_fails_before_submission(fixture, branch, optimizer):
    session = client.Session(fixture.root / branch, fixture.plans[branch])
    with pytest.raises(ValueError, match='F1_optimizer_only'):
        session.sleep(None, optimizer, [], [], [], fixture.root, None, lambda label: None)


def test_deadline_checked_during_wait_no_quota_reset(fixture):
    session = client.Session(fixture.root / 'A1', fixture.plans['A1'])
    rows = arrive(fixture, 'A1')
    def check(label):
        if label == 'shared_barrier_wait':
            raise TimeoutError('original lifetime wall')
    with pytest.raises(TimeoutError):
        session.sleep(None, None, [], rows, fixture.specs['A1']['train_ids'],
                      fixture.root / 'A1' / 'cycle_0001', None, check)
    with pytest.raises(ValueError, match='partial_shared_cycle'):
        client.Session(fixture.root / 'A1', fixture.plans['A1'])


@pytest.mark.parametrize('mutation,error', [('bounds', 'no_bound_reset'), ('slot', 'physical_binding'),
                                          ('held', 'all_route_dev_final')])
def test_successor_contract_is_bound(fixture, mutation, error):
    plan = deepcopy(fixture.plans['A1'])
    if mutation == 'bounds':
        plan['bounds']['native_calls'] += 1
    elif mutation == 'slot':
        plan['physical'] = 0
    else:
        plan['held_ids'].append('OTHER_DEV')
    with pytest.raises(ValueError, match=error):
        client.Session(fixture.root / 'A1', plan)


def test_untagged_historical_rows_cannot_be_submitted_as_new(fixture):
    session = client.Session(fixture.root / 'F1', fixture.plans['F1'])
    with pytest.raises(ValueError, match='actual_common_child_capture_binding'):
        session.sleep(None, object(), [], [fixture.old], fixture.specs['F1']['train_ids'],
                      fixture.root / 'F1' / 'cycle_0002', None, lambda label: None)


def test_optimizer_restore_only_owner_and_actual_rng_shape(fixture):
    torch = SimpleNamespace(load=Mock(return_value=dict(optimizer={'state': 113}, cpu_rng='cpu', cuda_rng=['gpu'])),
                            set_rng_state=Mock(), cuda=SimpleNamespace(set_rng_state_all=Mock()))
    optimizer = Mock()
    client.restore_optimizer(SimpleNamespace(torch=torch), optimizer, fixture.initial, owner='F1')
    optimizer.load_state_dict.assert_called_once_with({'state': 113})
    torch.cuda.set_rng_state_all.assert_called_once_with(['gpu'])
    with pytest.raises(ValueError, match='only_F1'):
        client.restore_optimizer(SimpleNamespace(torch=torch), optimizer, fixture.initial, owner='A1')


def test_no_completed_checkpoint_adoption_invents_no_optimizer(tmp_path):
    with pytest.raises(ValueError, match='no_complete_F1_cycle'):
        client.adoption_inputs(tmp_path)
