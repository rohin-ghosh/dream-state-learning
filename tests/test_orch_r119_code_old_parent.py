import inspect
import pytest

from gpu import orch_r119_code_old_parent as parent


def test_same_historical_caps_new_lease_and_nonblocking():
    plan = dict(root='/native/code',wrapper='ovx2',parent_cadence='EPISODE',parent_wait_seconds=0,
        parent_ttl_seconds=600,train_end_unix=100,hard_end_unix=220,lease_end_unix=21820,
        ancestry=dict(parent_cap=500,parent_used=128))
    config = dict(remote_root='/native/code',deadline_unix=100,max_parent_calls=372,
        parent_effort='low',max_output_tokens=512)
    parent.validate_scope(plan,config,'ovx2')
    for patch in ({'max_parent_calls':500},{'deadline_unix':221},{'parent_effort':'max'}):
        with pytest.raises(ValueError):
            parent.validate_scope(plan,dict(config,**patch),'ovx2')


def test_transport_keeps_original_fixed_prompt_memory_and_lock():
    source = inspect.getsource(parent.serve)
    assert 'parse_output=parser.parse_output' in source
    assert 'provider.evaluate.__code__' in source
    assert "evaluate.__kwdefaults__ = dict(provider.evaluate.__kwdefaults__)" in source
    assert 'build_system=' not in source and 'provider_lock_path=' not in source
    assert 'queue.pending_listing' in source
