from pathlib import Path

from gpu import orch_r118_code_parallel_broker as broker


def test_A3_custody_maps_only_terminal_not_queue_ledger_or_parent_publication():
    root, service = Path('/synthetic/A3'), Path('/synthetic/service')
    for name in ('TERMINAL.json', 'SHARED_TERMINAL.json'):
        assert broker.terminal_path(root / name, root, service) == service / 'GUARD_TERMINAL.json'
    for name in ('parent_queue/C001.request.json', 'parent_claude/CONFIG.json',
                 'parent_claude/C001.claim/PUBLISHED.json', 'reservations/C001.json'):
        assert broker.terminal_path(root / name, root, service) == root / name
    foreign = Path('/synthetic/F3/SHARED_TERMINAL.json')
    assert broker.terminal_path(foreign, root, service) == foreign


def test_actual_Astra_provider_parser_HTTP_slot_remain_original():
    provider = broker.shared.astra
    assert provider.evaluate.__module__ == 'gpu.orch_r108_code_parent_r115_astra'
    assert provider.parse.__module__ == provider.evaluate.__module__
    assert provider.http_slots.__name__ == 'gpu.orch_r118_astra_slots'
