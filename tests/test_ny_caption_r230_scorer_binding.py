import pytest

from research_loop.workers.rohin221_continuous_caption_20260918.native_proxy import (
    authorized_wrapper, require_future_origin,
)
from research_loop.workers.rohin221_continuous_caption_20260918.new_session_scorer import FutureOnlyHub
from research_loop.workers.rohin221_continuous_caption_20260918.journal_bundle import export_records
from tests.test_ny_caption_r226_shared import Game, records


def test_future_only_native_host_allowlist():
    assert authorized_wrapper(dict(host_alias='ovx')) == 'gpu/ovx_ssh.sh'
    assert authorized_wrapper(dict(host_alias='ovx2')) == 'gpu/ovx2_ssh.sh'
    with pytest.raises(ValueError):
        authorized_wrapper(dict(host_alias='arbitrary'))
    config = dict(minimum_origin_record_index=201)
    require_future_origin(config,dict(origin=dict(record_index=201)))
    for index in (21,200,'201'):
        with pytest.raises(ValueError,match='future_only'):
            require_future_origin(config,dict(origin=dict(record_index=index)))


def test_new_identity_gets_own_game_and_seen_set_no_replays(tmp_path):
    identifier = 'r229_extra_unparented_node2_gpu2'
    config = dict(session_id=identifier,host_alias='ovx',life_root='/actual/new',
        journal=dict(journal_id='new-journal'),minimum_origin_record_index=0)
    hub = FutureOnlyHub(tmp_path/'scorer',dict(rows=[config]),lambda name:Game(),['scene'],{})
    origin = records(tmp_path/'source',journal='new-journal')
    envelope = dict(session_id=identifier,request=dict(origin=origin,metrics=dict(THINK=0,ACT=1,LEARN=0)),
        records=export_records(tmp_path/'source',origin,'new-journal'))
    result = hub.native(envelope)
    assert result['report']['feedback'][0]['result']['accepted']
    assert len(hub.sessions[identifier].seen) == 1
    with pytest.raises(ValueError,match='duplicate_ACT'):
        hub.native(envelope)
    config['minimum_origin_record_index'] = 1
    with pytest.raises(ValueError,match='future_only'):
        hub.native(envelope)


def test_no_existing_session_may_be_relabelled(tmp_path):
    config = dict(session_id='existing',host_alias='ovx',minimum_origin_record_index=0)
    with pytest.raises(ValueError,match='exact_new_session'):
        FutureOnlyHub(tmp_path,dict(rows=[config]),lambda name:Game(),['scene'],{})
