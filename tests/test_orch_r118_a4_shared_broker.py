import pytest

from gpu import orch_r118_a4_shared_broker as broker


def released():
    return dict(root=str(broker.ROOT), branch='A4', status='RELEASED',
        all_predecessors_exited=True, all_charged_captures_preserved=True,
        no_calls_retried=True, next_cycle=7, bounds=dict(parent_wait_seconds=120,
        max_parent_calls=298, hard_end_unix=1789491720.0))


def test_only_terminal_path_changes():
    original = "if store.exists(root / 'TERMINAL.json'):\n    break\nprocess_request()\n"
    changed = broker.terminal_source(original)
    assert changed.replace('SHARED_TERMINAL.json', 'TERMINAL.json') == original
    with pytest.raises(ValueError, match='exact_frozen_terminal_check'):
        broker.terminal_source(original + original)


def test_actual_release_accepted():
    broker.validate_release(released())


@pytest.mark.parametrize('key,value', [('branch', 'F4'), ('status', 'ARMED'),
    ('all_predecessors_exited', False), ('all_charged_captures_preserved', False),
    ('no_calls_retried', False), ('next_cycle', 0)])
def test_no_cross_lane_or_pending_release(key, value):
    document = released()
    document[key] = value
    with pytest.raises(ValueError, match='actual_A4_release_required'):
        broker.validate_release(document)


def test_wait_budget_unchanged():
    document = released()
    document['bounds']['parent_wait_seconds'] = 600
    with pytest.raises(ValueError, match='same_A4_bounds'):
        broker.validate_release(document)
