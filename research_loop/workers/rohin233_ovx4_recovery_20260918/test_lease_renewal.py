import pytest

from research_loop.workers.rohin233_ovx4_recovery_20260918.lease_bridge import validate
from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import allocation_guard
from research_loop.workers.rohin233_ovx4_recovery_20260918.transport_proxy import validate_deadline


def test_reported_long_lease_keeps_six_hour_margin():
    now = 1789753000
    config = dict(deadline_unix=1790791170, lease_boundary_unix=1790812800,
        allocation=dict(conservative_lease_boundary_unix=1790812800,
            authorized_job_end_unix=1790791170, lease_source_sha256='a'*64, authority_sha256='b'*64))
    validate(config, now)
    allocation_guard(config, 2, now)
    validate_deadline(config['deadline_unix'], config['lease_boundary_unix'], now)
    for deadline in (now, 1790791201):
        with pytest.raises(ValueError):
            validate(dict(config, deadline_unix=deadline), now)
    with pytest.raises(ValueError):
        allocation_guard(config, 0, now)


def test_finalize_actual_pending_score_once_without_generation(tmp_path):
    from dataclasses import asdict
    from research_loop.workers.rohin221_continuous_caption_20260918.controller import Plan
    from research_loop.workers.rohin233_ovx4_recovery_20260918.base_boundary import finalize_pending
    plan=Plan(condition='synthetic',rule_sha256='a'*64)
    request=dict(request_id='b'*64,rule_sha256='a'*64)
    attempt=dict(parsed=1,format_reason=None,source={'request_id':'b'*64},opportunity=1,attempt=1)
    state=dict(binding={'plan':asdict(plan)},backend_state={'kind':'FROZEN_BASE_NO_LORA_NO_LEARNING'},
        pending=dict(kind='SCORE',request=request,attempt=attempt),history=[],events=[],generations=[],
        completed_opportunities=0,opportunity=1,attempt=1,stage='ACT',total_generated_tokens=17)
    response=dict(request_id='b'*64,rule_sha256='a'*64,receipt_sha256='c'*64,
        report=dict(requested_count=1,feedback=[dict(result=dict(ok=True,accepted=True,status='new_pixel',rank=3))]))
    result=finalize_pending(tmp_path,state,response,clock=lambda:1234)
    assert result['pending'] is None and len(result['events'])==1
    assert result['total_generated_tokens']==17 and result['events'][0]['accepted']==1
    assert state['pending'] is not None and not state['events']
    with pytest.raises(ValueError):
        finalize_pending(tmp_path,result,response)


def test_boundary_service_cannot_spawn_privileged_controls():
    import ast
    import inspect
    from research_loop.workers.rohin233_ovx4_recovery_20260918 import base_boundary
    tree=ast.parse(inspect.getsource(base_boundary))
    imports=[alias.name for item in ast.walk(tree) if isinstance(item,ast.Import) for alias in item.names]
    assert 'subprocess' not in imports
    calls=[item.func.attr for item in ast.walk(tree) if isinstance(item,ast.Call) and isinstance(item.func,ast.Attribute)]
    assert not set(calls).intersection({'kill','system','popen','execv','execve'})
