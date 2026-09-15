import pytest

from gpu import orch_r118_a4_repair_broker as broker


def document():
    return dict(root=str(broker.prior.ROOT), schema='R118_GRID_SHARED_NO_REPLAY_REPAIR_V1',
        terminal_filename=broker.TERMINAL, parent_requests_redispatched=0,
        bounds=dict(parent_wait_seconds=120, max_parent_calls=298, hard_end_unix=1789491720.0))


def test_no_old_request_replay():
    assert all(broker.historical(f'P{number:04d}.request.json') for number in range(1, 33))
    assert not broker.historical('P0033.request.json')


def test_exact_repair_era():
    broker.validate_ready(document())


@pytest.mark.parametrize('key,value', [('root','/other'),('terminal_filename','SHARED_TERMINAL.json'),
    ('parent_requests_redispatched',1),('schema','wrong')])
def test_rejects_changed_era(key,value):
    value_doc=document()
    value_doc[key]=value
    with pytest.raises(ValueError, match='exact_A4_repair'):
        broker.validate_ready(value_doc)


def test_wait_not_extended():
    value_doc=document()
    value_doc['bounds']['parent_wait_seconds']=600
    with pytest.raises(ValueError, match='exact_A4_repair'):
        broker.validate_ready(value_doc)
