from pathlib import Path

import pytest

from gpu import orch_r108_code_parent_r118_handoff as handoff


def test_carry_uses_latest_actual_binding_including_silent_not_later_missing():
    rows=[dict(kind='PARENT',id='FIRST',status='COMPLETE',finished_unix=1,
        reflection_settings={'effective_max_new_tokens':128}),
        dict(kind='PARENT',id='SILENT',status='SILENT',finished_unix=2,
        reflection_settings={'effective_max_new_tokens':512}),
        dict(kind='PARENT',id='MISSING',status='MISSING',finished_unix=3,
        reflection_settings={'effective_max_new_tokens':8192})]
    value=handoff.carry(rows)
    assert value['reflection_settings']['effective_max_new_tokens'] == 512
    assert value['reflection_source_id'] == 'SILENT' and value['old_experience_replayed'] is False
    assert rows[-1]['reflection_settings']['effective_max_new_tokens'] == 8192


@pytest.fixture
def released(tmp_path):
    root=tmp_path/'life'
    plan=dict(physical=2,started_unix=1,hard_deadline_unix=100,lease_end_unix=30000,
        native_cap=8192,parent_cap=1000,cycles=100)
    write=handoff.run.write_new
    write(root/'PLAN.json',plan)
    bounds={key:plan[key] for key in handoff.client.BOUND_FIELDS}
    prepared=tmp_path/'EIGHT_READY.json'
    write(prepared,dict(branch_specs={'F3':{'root':str(root)}},branch_bounds={'F3':bounds}))
    roster=tmp_path/'ROSTER.json';write(roster,{'F3':{}})
    request=dict(receiver_ready=True,branch='F3',bounds=bounds,predecessors=[{'pid':123}],
        predecessor_plan_sha256=handoff.run.sha(root/'PLAN.json'),
        roster=dict(path=str(roster),sha256=handoff.run.sha(roster)),
        eight_ready=dict(path=str(prepared),sha256=handoff.run.sha(prepared)))
    write(root/'RELEASE_AFTER_CYCLE.json',request)
    write(root/'CYCLE_RELEASE_READY.json',dict(cycle=3,request_sha256=handoff.run.sha(root/'RELEASE_AFTER_CYCLE.json')))
    write(root/'cycles/C003_COMPLETE.json',{'cycle':3})
    write(root/'reservations/OLD.json',dict(id='OLD',kind='NATIVE',status='FAILED',cycle=2))
    write(root/'reservations/NEW.json',dict(id='NEW',kind='NATIVE',status='COMPLETE',cycle=3))
    return root


def test_boundary_requires_actual_native_guard_exit(released):
    with pytest.raises(ValueError,match='all_exit'):
        handoff.validate(released,process_exists=lambda pid:True)
    result=handoff.validate(released,process_exists=lambda pid:False)
    assert result['next_cycle'] == 4 and len(result['rows']) == 2


@pytest.mark.parametrize('change',[{'status':'STARTED'},{'cycle':4}])
def test_pending_or_future_charged_cell_blocks(released,change):
    path=released/'reservations/NEW.json'
    handoff.run.write(path,dict(handoff.run.read(path),**change))
    with pytest.raises(ValueError,match='settled_no_later'):
        handoff.validate(released,process_exists=lambda pid:False)


def test_original_request_and_plan_cannot_change(released):
    handoff.run.write(released/'PLAN.json',dict(handoff.run.read(released/'PLAN.json'),native_cap=9000))
    with pytest.raises(ValueError,match='PLAN_binding'):
        handoff.validate(released,process_exists=lambda pid:False)


def test_unpublished_parent_blocks_without_retry(released):
    handoff.run.write_new(released/'parent_queue/LATE.request.json',{'id':'LATE'})
    with pytest.raises(ValueError,match='await_original_parent'):
        handoff.validate(released,process_exists=lambda pid:False)
