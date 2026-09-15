from contextlib import contextmanager

import pytest

from gpu import orch_r118_node3_6_grid_broker_http as broker


def test_same_helper_four_slots_no_private_pool():
    assert broker.slots.LIMIT == 4
    assert str(broker.slots.ROOT) == '/tmp/orch_astra_http_slots'
    assert broker.evaluate.__globals__['slots'] is broker.slots
    assert broker.evaluate.__globals__['parse'] is broker.astra.parse


def test_owned_roots_and_transports_only():
    assert set(broker.LANES) == {'A4', 'A1004', 'NODE3_6'}
    assert broker.LANES['A4'][0].endswith('/A4')
    assert broker.LANES['A1004'][2] is broker.a100.Store
    assert broker.LANES['NODE3_6'][2] is broker.node3.Store


def test_http_slot_retains_cutoff_memory_floor_and_one_provider_attempt(tmp_path, monkeypatch):
    transport = broker.astra.transport
    monkeypatch.setattr(transport, 'validate_config', lambda config: None)
    monkeypatch.setattr(transport, 'validate_request', lambda request, config: {})
    monkeypatch.setattr(transport, 'build_system', lambda *args: ('system', b'fixed prompt', {}))
    monkeypatch.setitem(broker.evaluate.__globals__, 'authorize', lambda *args: None)
    now = broker.astra.time.time()
    received = []
    @contextmanager
    def acquire(cutoff):
        received.append(cutoff)
        yield dict(slot=0, maximum_http_concurrency=4, cli_lock_used=False)
    monkeypatch.setattr(broker.slots, 'acquire', acquire)
    calls = []
    def runner(*args):
        calls.append(args)
        return dict(status='COMPLETE', actual_model=broker.astra.MODEL)
    request = dict(id='P1', payload_sha256='a'*64, lane_deadline_unix=now+120)
    config = dict(branch='F4', family='grid', deadline_unix=now+300, min_available_bytes=1024)
    result = broker.evaluate(request, tmp_path/'packet', now+100, config=config, launch={},
        prompt_root=tmp_path, principles_path=tmp_path, runner=runner, memory=lambda: 2048)
    assert received == [now+90] and len(calls) == 1
    assert result['provider_dispatched'] and result['retry'] is False
    assert (tmp_path/'packet/HTTP_SLOT.json').exists()
    result = broker.evaluate(request, tmp_path/'low_memory', now+100, config=config, launch={},
        prompt_root=tmp_path, principles_path=tmp_path, runner=runner, memory=lambda: 1)
    assert result['status'] == 'MISSING' and not result['provider_dispatched'] and len(calls) == 1


def test_other_root_never_dispatches(tmp_path):
    path = tmp_path/'config.json'
    path.write_text('{"remote_root":"/wrong","life_id":"wrong"}')
    with pytest.raises(ValueError, match='exact_existing_grid_parent_lane'):
        broker.serve('A4', path, None, None, None)
