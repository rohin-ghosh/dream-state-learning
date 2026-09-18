"""Prospective DEV bounds, whole-corpus coverage, and failure-preserving dispatch."""

import pytest

from organism_v6 import orch_combined_l1_dev as dev
from organism_v6.orch_combined_l1_continual import ContinualLayout


def test_global_bound_includes_auxiliary_math_no_extra_calls():
    assert dev.call_cap('INTERMEDIATE', 'route') == 384
    assert sum(dev.call_cap('INTERMEDIATE', family) for family in dev.FAMILIES) == 496
    assert sum(dev.call_cap('TERMINAL', family) for family in dev.FAMILIES) == 208
    assert dev.total_bound() == 1760
    assert dev.DEFAULT_P64_CALLS == 128


@pytest.mark.parametrize('rows', [2394, 2943, 3007, 3196, 3260])
def test_first_traversal_covers_all_whole_targets(rows):
    layout = ContinualLayout(rows, 2)
    boundary = dev.first_boundary(rows)
    observed = {index for update in range(1, boundary + 1) for index in layout.training_indexes(update)[2:]}
    assert observed == set(range(210, rows + 222))
    assert len([index for update in range(1, boundary + 1) for index in layout.training_indexes(update)[2:]]) <= rows + 13


def test_window_shortens_to_exact_boundary_and_resumes_not_reset():
    assert dev.next_window(1536, 1636, False) == 1636
    assert dev.next_window(1636, 1636, True) == 1764
    with pytest.raises(AssertionError, match='missed'):
        dev.next_window(1636, 1636, False)


def test_jobs_pair_both_arms_each_family_within_same_panel():
    assert dev.jobs('INTERMEDIATE') == (('FULL', 'math'), ('OFF', 'math'), ('FULL', 'route'),
        ('OFF', 'route'), ('FULL', 'legacy'), ('OFF', 'legacy'))


def test_every_generation_cap_is_prospective():
    with pytest.raises(AssertionError):
        dev.call_cap('extra_epoch', 'math')
    with pytest.raises(AssertionError):
        dev.call_cap('INTERMEDIATE', 'teacher')


def test_default_prompt_has_only_task_and_answer_contract():
    messages = dev.default_math_messages(dict(question='What is 2 + 2?', gold='4'))
    assert messages == [dict(role='system', content=dev.DEFAULT_MATH_SYSTEM),
                        dict(role='user', content='What is 2 + 2?')]
    assert all(word not in messages[0]['content'] for word in ('tokens', 'first-person', 'exhaust', 'approaches', 'reject'))


def test_stale_abort_not_applied_to_new_controller():
    from organism_v6.orch_combined_l1_continual import abort_applies
    assert not abort_applies(dict(controller_session='old'), 'new')
    assert not abort_applies(dict(time_unix=1), 'new')
    assert abort_applies(dict(controller_session='new'), 'new')
    assert abort_applies(dict(time_unix=1), None)


def test_old_auxiliary_release_schema_never_triggers_expansion(tmp_path):
    import json
    from gpu.orch_combined_l1_continual_guard import auxiliary_available
    (tmp_path / 'TERMINAL.json').write_text(json.dumps(dict(release={'SCALE764_FULL': False})))
    assert not auxiliary_available(tmp_path)
    (tmp_path / 'P64_DEFAULT').mkdir()
    (tmp_path / 'P64_DEFAULT/RELEASED.json').write_text(json.dumps(dict(returncodes=[0, 0], actual_reserved_calls=128)))
    assert auxiliary_available(tmp_path)
