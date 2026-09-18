from copy import deepcopy

import pytest

from gpu import orch_r118_route_recovery_bind as binder


@pytest.fixture
def inputs():
    plan = dict(shared_learner=dict(root='/common'), bounds=dict(native_calls=700, hard_end_unix=1789491720),
        source_files={'frozen': 'old'}, parallel_control=dict(train_end_unix=1789491300,
        campaign=dict(path='/old', sha256='old'), activation_directory='/old/activations'))
    campaign = dict(root='/common', first_generation=1, deadline_unix=1789491300,
        source_files={'frozen': 'old', 'recovery': 'new'}, activation_directory='/new/activations')
    owner = dict(source_files=dict(campaign['source_files']))
    return plan, campaign, owner


def test_only_two_control_fields_change(inputs):
    plan, campaign, owner = inputs
    original = deepcopy(plan)
    changed = binder.campaign_plan(plan, campaign, dict(path='/new', sha256='new'), owner)
    assert plan == original
    assert changed['bounds'] == plan['bounds']
    assert changed['source_files'] == plan['source_files']
    changed['parallel_control']['campaign'] = plan['parallel_control']['campaign']
    changed['parallel_control']['activation_directory'] = plan['parallel_control']['activation_directory']
    assert changed == original


@pytest.mark.parametrize('field,value', [('root', '/foreign'), ('first_generation', 2),
    ('deadline_unix', 1789491301), ('source_files', {'frozen': 'old'})])
def test_changed_bounds_lineage_or_missing_closure_rejected(inputs, field, value):
    plan, campaign, owner = inputs
    campaign[field] = value
    with pytest.raises(ValueError):
        binder.campaign_plan(plan, campaign, {}, owner)


def test_new_metadata_never_overwrites_old(tmp_path):
    path = tmp_path / 'OLD_PLAN.json'
    binder.write_new(path, dict(original=True))
    with pytest.raises(FileExistsError):
        binder.write_new(path, dict(original=False))


def test_extension_after_old_expiry_preserves_old_request_and_bounds(monkeypatch):
    monkeypatch.setattr(binder.time, 'time', lambda: 1789488601)
    request = dict(expires_unix=1789488600, bounds=dict(train_end_unix=1789491300, native_calls=700),
                   attempt_directory='/old/R118_STARTUP_RECOVERY_1552')
    original = deepcopy(request)
    changed = binder.startup_window(request, 1789489500)
    assert request == original
    assert changed['expires_unix'] == 1789489500
    assert changed['bounds'] == original['bounds']
    assert changed['attempt_directory'] == original['attempt_directory']


@pytest.mark.parametrize('deadline', [1789489501, 1789488599, None, True])
def test_startup_extension_is_explicit_and_bounded(deadline):
    with pytest.raises(ValueError):
        binder.startup_window(dict(expires_unix=1789488600), deadline)
