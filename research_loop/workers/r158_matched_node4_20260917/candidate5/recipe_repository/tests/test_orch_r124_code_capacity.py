from copy import deepcopy

import pytest

from gpu import orch_r124_code_capacity as capacity


def reference(name):
    return dict(path='/native/'+name, sha256='a'*64)


def plan(wrapper='a40r', physical=4):
    return dict(wrapper=wrapper, physical=physical, root='/native/branch', gpu_uuid='GPU-actual',
        cycle_limit=100, first_cycle=27, ancestry=dict(native_cap=1500, parent_cap=500),
        optimizer_updates=0, parent_wait_seconds=0, parent_cadence='EPISODE', parent_ttl_seconds=600,
        train_end_unix=1000, hard_end_unix=1120, lease_end_unix=22720,
        adapter=None if wrapper=='a40r' else {'path':'/native/frozen_gen1'})


def boundary():
    return dict(terminal_status='COMPLETE', completed_cycle=100, latest_charged_cycle=100,
        native_inflight=0, actor_exited=True, guard_exited=True, readonly_verified=True,
        terminal=reference('terminal'), cycle_complete=reference('cycle100'), context=reference('context100'),
        ledger_manifest=reference('all_charges'), after=reference('after'), context_cycle=100,
        all_charges_preserved=True, native_used=1493, parent_used=276,
        pending_parent_references=[reference('pending_parent_original')])


def test_all_seven_allocations_and_no_node5_mix():
    for wrapper, slots in capacity.ALLOCATIONS.items():
        for slot in slots:
            result=capacity.capacity(plan(wrapper,slot),reference('plan'))
            assert not result['activation_ready'] and not result['current_actor_mutation']
    with pytest.raises(ValueError,match='seven_allocated'):
        capacity.capacity(plan('ovx3',2),reference('plan'))


def test_absolute_wall_and_old_caps_not_reset():
    original=plan();before=deepcopy(original)
    result=capacity.capacity(original,reference('plan'))
    assert original==before and result['train_end_unix']==1000 and result['hard_end_unix']==1120
    assert result['prospective_native_increment']==61440
    assert result['prospective_parent_increment']==8192
    assert result['last_new_cycle']==4196


def test_new_chunk_deterministic_excludes_original_registry():
    prior=capacity.original.tasks('node3_episode')
    rows=capacity.chunk_registry(0,[row['task_id'] for row in prior],
        [row['prompt_sha256'] for row in prior],[row['question_sha256'] for row in prior])
    assert rows==capacity.chunk_registry(0)
    assert len(rows)==384 and min(row['cycle'] for row in rows)==101
    manifest=capacity.chunk_manifest(0,rows)
    assert manifest['train_tasks']==128 and manifest['held_tasks']==256
    assert manifest['native_slots']==960 and manifest['parent_slots']==128
    assert manifest['raw_registry_node_only']


def test_future_chunks_do_not_relabel_previous_content():
    prior=capacity.chunk_registry(0)
    rows=capacity.chunk_registry(1,[row['task_id'] for row in prior],
        [row['prompt_sha256'] for row in prior],[row['question_sha256'] for row in prior])
    assert min(row['cycle'] for row in rows)==165
    with pytest.raises(ValueError,match='new_content_disjoint'):
        capacity.chunk_registry(0,excluded_prompts=[prior[0]['prompt_sha256']])


def test_task_validators_remain_existing_safe_interpreter():
    for row in capacity.chunk_registry(0)[:12]:
        for example in row['tests']:
            assert capacity.original.prior.gym.evaluate(row['reference_expression'],example['arguments'])==example['expected']


def test_cumulative_handoff_preserves_pending_without_reissue():
    contract=capacity.capacity(plan(),reference('plan'))
    actual=boundary();before=deepcopy(actual)
    result=capacity.settled_handoff(contract,actual)
    assert actual==before and result['carried_native_used']==1493
    assert result['new_absolute_native_cap']==1493+61440
    assert result['new_absolute_parent_cap']==276+8192
    assert result['pending_parent_references']==actual['pending_parent_references']
    assert result['native_calls_replayed']==result['parent_requests_reissued']==0


@pytest.mark.parametrize('patch',[{'terminal_status':'FAILED'},{'native_inflight':1},
    {'completed_cycle':99},{'latest_charged_cycle':101},{'context_cycle':99},
    {'actor_exited':False},{'guard_exited':False},{'all_charges_preserved':False},
    {'native_used':1501},{'readonly_verified':False}])
def test_reject_partial_or_fabricated_release(patch):
    with pytest.raises(ValueError):
        capacity.settled_handoff(capacity.capacity(plan(),reference('plan')),dict(boundary(),**patch))


def test_capacity_bounded_without_auto_extension():
    for invalid in (-1,64,True):
        with pytest.raises(ValueError):
            capacity.chunk_registry(invalid)
