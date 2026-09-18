import json
import hashlib

import pytest

from research_loop.workers.rohin233_ovx4_recovery_20260918.judge_epoch import EpochLedger, verified_source


def binding(player='synthetic'):
    return dict(player=player,primary_step=15625,primary_rank=8,shadow_step=6250,shadow_seconds=3600,
        previous_session_sha256='a'*64,new_judge_manifest_sha256='b'*64,old_judge_manifest_sha256='c'*64)


def test_independent_new_string_shadow_hour_and_no_replay(tmp_path):
    first=EpochLedger(tmp_path/'first',binding())
    assert not first.admit('d'*64,'scene','Synthetic caption.',cached=True,unix=1)['admitted']
    assert not (tmp_path/'first/ACTIVE.json').exists()
    admitted=first.admit('d'*64,'scene','Synthetic caption.',unix=100)
    assert admitted['record']['shadow_due']
    assert not first.admit('e'*64,'scene','Synthetic caption.',unix=101)['admitted']
    second=EpochLedger(tmp_path/'second',binding('other'))
    assert second.admit('e'*64,'scene','Synthetic caption.',unix=101)['admitted']
    assert not first.admit('f'*64,'scene','Another synthetic caption.',unix=3700)['record']['shadow_due']
    record=first.completed(admitted['key'],dict(rank=2,accepted=True,status='repeat'),None,'f'*64)
    assert record['shadow_status']=='PENDING_OR_FAILED_NOT_A_ZERO_SCORE'
    assert not record['shadow_counted_as_player_discovery']
    resumed=EpochLedger(tmp_path/'first',binding())
    assert not resumed.admit('d'*64,'scene','Synthetic caption.',unix=3701)['admitted']
    with pytest.raises(ValueError):
        EpochLedger(tmp_path/'first',binding('changed'))


def test_exact_rank_checkpoint_not_directory_label(tmp_path):
    (tmp_path/'adapter').mkdir()
    (tmp_path/'COMPLETE.json').write_text(json.dumps(dict(optimizer_step=15625)))
    (tmp_path/'adapter/adapter_config.json').write_text(json.dumps(dict(r=8)))
    (tmp_path/'adapter/adapter_model.safetensors').write_bytes(b'synthetic-not-a-real-model')
    def sha(name):
        return hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
    assert verified_source(tmp_path,sha('COMPLETE.json'),sha('adapter/adapter_model.safetensors'),
        sha('adapter/adapter_config.json'))['optimizer_step']==15625
    (tmp_path/'COMPLETE.json').write_text(json.dumps(dict(optimizer_step=146)))
    with pytest.raises(ValueError,match='not_selected_warm146'):
        verified_source(tmp_path,sha('COMPLETE.json'),sha('adapter/adapter_model.safetensors'),sha('adapter/adapter_config.json'))
