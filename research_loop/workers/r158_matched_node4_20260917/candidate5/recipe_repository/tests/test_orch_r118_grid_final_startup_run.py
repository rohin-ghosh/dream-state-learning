from copy import deepcopy

import pytest

from gpu import orch_r118_grid_final_startup_run as final


def proof():
    own=dict(native_process_dispatched=False,model_load_attempted=False,new_generation_calls=0,
        new_provider_charges=0,optimizer_steps=0,execution_markers={'ENTRY.json':False},
        canonical_bootstrap_exists=False,bootstrap_start_exists=False,preserved_mismatches=[],
        new_call_parent_triple_files=[],ledger_counts={'NATIVE':567,'PARENT':40})
    return dict(session={'sha256':final.SECOND_SESSION_SHA},GO_exists=False,branches={'A4':own})


def test_exact_no_call_second_failure():
    document=proof()
    original=deepcopy(document)
    final.validate_second_proof(document,'A4')
    assert document == original
    assert final.TERMINAL == 'R118_GRID_PARALLEL_RECOVERY_V2_TERMINAL.json'


@pytest.mark.parametrize('field,value',[('native_process_dispatched',True),('model_load_attempted',True),
    ('new_generation_calls',1),('new_provider_charges',1),('optimizer_steps',1),
    ('canonical_bootstrap_exists',True),('bootstrap_start_exists',True),('preserved_mismatches',['changed'])])
def test_any_real_work_rejects_no_work_recovery(field,value):
    document=proof();document['branches']['A4'][field]=value
    with pytest.raises(ValueError): final.validate_second_proof(document,'A4')


def test_no_sliding_or_second_session(monkeypatch):
    monkeypatch.setattr(final.time,'time',lambda:final.STARTUP_END)
    with pytest.raises(ValueError,match='before_1635'): final.validate_active({},None)
    monkeypatch.setattr(final.time,'time',lambda:final.STARTUP_END-1)
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256',final.SECOND_SESSION_SHA)
    with pytest.raises(ValueError,match='before_1635'): final.validate_active({},None)


def test_original_scientific_runner_is_reused():
    runner=final.configured_runner({})
    assert runner.TERMINAL == final.TERMINAL
    assert runner.__file__ == final.__file__
