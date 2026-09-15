from pathlib import Path

import pytest

from gpu import orch_r119_code_astra_broker as broker


def test_remaps_only_explicit_terminal_and_config_not_ledger():
    root, service = Path('/A3'), Path('/A3/service2')
    assert broker.mapped(root / 'TERMINAL.json', root, service) == service / 'GUARD_TERMINAL.json'
    assert broker.mapped(root / 'parent_claude/CONFIG.json', root, service) == service / 'BROKER_LEDGER_CONFIG.json'
    for name in ('parent_claude/RUNNER.lock', 'parent_claude/request.claim', 'parent_queue/request.response.json'):
        assert broker.mapped(root / name, root, service) == root / name


def test_only_clock_changes_and_shared_clock_required():
    original = dict(remote_root=str(broker.shared.ROOT), deadline_unix=1, max_parent_calls=1000)
    runtime = dict(schema='R119_CODE_LEASE_RUNTIME_V1', root=original['remote_root'],
        train_end_unix=1000, hard_end_unix=1120, common_root='/common')
    policy = dict(train_end_unix=1000, hard_end_unix=1120)
    campaign = dict(deadline_unix=1000, root='/common')
    broker.validate_binding(dict(original, deadline_unix=1000), original, runtime, policy, campaign)
    with pytest.raises(ValueError, match='only_canonical_deadline'):
        broker.validate_binding(dict(original, deadline_unix=1000, max_parent_calls=1001),
            original, runtime, policy, campaign)
    with pytest.raises(ValueError, match='one_Main_clock'):
        broker.validate_binding(dict(original, deadline_unix=1000), original, runtime,
            dict(policy, train_end_unix=999), campaign)


def test_original_HTTP_slots_and_actual_astra_parser_retained():
    provider = broker.shared.astra
    assert provider.evaluate.__module__ == 'gpu.orch_r108_code_parent_r115_astra'
    assert provider.http_slots.__name__ == 'gpu.orch_r118_astra_slots'
