from pathlib import Path
import pytest

from gpu import orch_r109_grid_status as status


def test_empty_campaign_is_not_reported_as_running(tmp_path):
    status.write_once(tmp_path/'READY.json',dict(lane='ovx'))
    status.write_once(tmp_path/'SOURCE_SHA256.json',{})
    result=status.collect(tmp_path,'ovx')
    assert result['models_mounted']==0 and result['native_complete']==0
    assert result['parent_complete']==0 and result['unique_source_joined_triples']==0
    assert result['functional_helpfulness']=='UNASSESSED'
    assert result['weight_learning_claim'] is False


def test_token_time_reductions_and_no_failed_call_refund(tmp_path):
    status.write_once(tmp_path/'READY.json',dict(lane='ovx'))
    status.write_once(tmp_path/'SOURCE_SHA256.json',{})
    (tmp_path/'LEDGER.jsonl').write_text('{"kind":"NATIVE"}\n{"kind":"NATIVE"}\n{"kind":"PARENT"}\n')
    status.write_once(tmp_path/'calls/N1.json',dict(status='COMPLETE',purpose='proposal',started_unix=1,finished_unix=3,
        response=dict(token_ids=[1,2,3],terminal=True,truncated=False)))
    status.write_once(tmp_path/'calls/N2.json',dict(status='FAILED'))
    result=status.collect(tmp_path,'ovx')
    assert result['native_reserved']==2 and result['native_complete']==1 and result['native_failed']==1
    assert result['tokens_by_purpose']['proposal']['total']==3 and result['native_seconds']['median']==2
    assert result['parent_reserved']==1 and result['parent_complete']==0


def test_status_evidence_cannot_overwrite(tmp_path):
    status.write_once(tmp_path/'receipt.json',{'old':True})
    with pytest.raises(FileExistsError):status.write_once(tmp_path/'receipt.json',{'old':False})


def test_summary_and_lane_binding(tmp_path):
    assert status.summary([1,4,9])['median']==4
    assert status.summary([])['mean'] is None
    status.write_once(tmp_path/'READY.json',dict(lane='ovx2'))
    with pytest.raises(ValueError,match='status_lane'):status.collect(tmp_path,'ovx')
