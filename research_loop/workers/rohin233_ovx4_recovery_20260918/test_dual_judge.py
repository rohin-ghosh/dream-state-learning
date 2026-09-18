from types import SimpleNamespace

from research_loop.workers.rohin233_ovx4_recovery_20260918.dual_judge import EpochJudge, EpochSessionMixin
from research_loop.workers.rohin233_ovx4_recovery_20260918.judge_epoch import EpochLedger


def ledger(root):
    return EpochLedger(root,dict(player='synthetic',primary_step=15625,primary_rank=8,shadow_step=6250,
        shadow_seconds=3600,previous_session_sha256='a'*64,new_judge_manifest_sha256='b'*64,
        old_judge_manifest_sha256='c'*64))


class Scalar:
    def score(self,rows):
        return [10.0]*len(rows)

    def score_as(self,rows,alias):
        assert alias=='default'
        return [-10.0]*len(rows)


def judge():
    return EpochJudge(Scalar(),{'scene':[0.0]*64},{'scene':[0.0]*64},
        SimpleNamespace(score=lambda scene,caption:1.0,threshold=0.1),
        SimpleNamespace(contests=[SimpleNamespace(canonical_scene='scene',contest_id='dev')]))


def test_distinct_adapter_ranks_and_one_shadow_per_new_string(tmp_path):
    callback=judge()
    callback.ledger=ledger(tmp_path)
    callback.origin='d'*64
    result=callback('scene','Synthetic caption.')
    assert result.rank==1 and result.accepted
    assert callback.pending[0]['shadow']['rank']==65
    assert not callback.pending[0]['shadow']['accepted']
    callback('scene','Synthetic caption.')
    assert len(callback.pending)==1


class EmptySession:
    def process_verified(self,request,raw,**kwargs):
        return {'receipt_sha256':'f'*64,'report':{'feedback':[]}}


class EmptyEpoch(EpochSessionMixin,EmptySession):
    pass


def test_empty_or_cached_act_cannot_start_shadow_hour(tmp_path):
    session=EmptyEpoch()
    session.seen=set()
    session.game=SimpleNamespace(_judge=judge())
    session.epoch_ledger=ledger(tmp_path)
    result=session.process_verified({'origin':{'record_sha256':'d'*64}},'No caption.',identifier='d'*64)
    assert result['receipt_sha256']=='f'*64
    assert result['judge_epoch']['new_scored']==0
    assert result['judge_epoch']['shadow_end_unix'] is None
    assert not (tmp_path/'ACTIVE.json').exists()


def test_shadow_failure_preserves_primary_and_pending_diagnostic(tmp_path):
    callback=judge()
    callback.ledger=ledger(tmp_path)
    callback.origin='d'*64
    def fail(rows,alias):
        raise RuntimeError('synthetic')
    callback.dual.score_as=fail
    assert callback('scene','Synthetic caption.').accepted
    pending=callback.pending[0]
    assert pending['shadow'] is None and pending['shadow_error']=='RuntimeError'
    receipt=callback.ledger.completed(pending['key'],{'rank':1,'accepted':True},None,'e'*64)
    assert receipt['shadow_status']=='PENDING_OR_FAILED_NOT_A_ZERO_SCORE'
