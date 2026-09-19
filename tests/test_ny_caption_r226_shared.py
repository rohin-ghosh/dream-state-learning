import base64
import hashlib
import json
from pathlib import Path

import pytest

from gpu.ny_caption_life import child_act
from gpu.orch_r125_stream_journal import _digest
from research_loop.workers.rohin221_continuous_caption_20260918.journal_bundle import (
    export_records, import_records,
)
from research_loop.workers.rohin221_continuous_caption_20260918.shared_scorer import Hub


def records(root, journal='actual-journal'):
    directory = root / 'stream/records'
    directory.mkdir(parents=True)
    response = dict(response=dict(raw='Scene1:\n"Actual literal."'))
    previous, rows = 'seed', []
    for index, (kind, document) in enumerate([
            ('RESPONSE', response), ('COMMITTED', dict(source_sha256=_digest(response))),
            ('R184_STAGE',dict(stage='ACT', source_sha256=_digest(response))) ]):
        row = dict(index=index,journal_id=journal,kind=kind,document=document,previous_sha256=previous)
        row['sha256'] = _digest(row)
        previous = row['sha256']
        (directory / f'{index:020d}.json').write_text(json.dumps(row))
        rows.append(row)
    return dict(kind='TRAIN_CHILD_RESPONSE',record_index=0,record_sha256=rows[0]['sha256'])


def test_actual_byte_mirror_roundtrip_and_foreign_or_changed_evidence_rejected(tmp_path):
    origin = records(tmp_path/'source')
    bundle = export_records(tmp_path/'source',origin,'actual-journal')
    import_records(tmp_path/'mirror',bundle,'actual-journal')
    assert child_act(tmp_path/'mirror',origin) == 'Scene1:\n"Actual literal."'
    with pytest.raises(ValueError,match='bound_journal'):
        import_records(tmp_path/'other',bundle,'other-journal')
    broken = json.loads(json.dumps(bundle))
    broken[0]['raw'] = base64.b64encode(b'changed').decode()
    with pytest.raises(ValueError,match='exact_transferred'):
        import_records(tmp_path/'mirror',broken,'actual-journal')


class Game:
    def __init__(self):
        self.captions = []

    def snapshot(self):
        return dict(captions=list(self.captions))

    def submit_caption(self, contest, caption):
        self.captions.append(caption)
        return dict(ok=True, accepted=True, status='new_pixel', rank=1, reference_count=64, top_k=50)


def test_shared_factory_keeps_games_seen_and_origin_bindings_independent(tmp_path):
    registry = dict(rows=[dict(session_id=identifier, life_root='/actual/'+identifier,
        journal=dict(journal_id=identifier)) for identifier in ['first','second']])
    hub = Hub(tmp_path/'shared',registry,lambda identifier:Game(),['scene'],{})
    for identifier in ['first','second']:
        origin = records(tmp_path/identifier,journal=identifier)
        bundle = export_records(tmp_path/identifier,origin,identifier)
        request = dict(origin=origin,metrics=dict(THINK=0,ACT=1,LEARN=0))
        result = hub.native(dict(session_id=identifier,request=request,records=bundle))
        assert result['report']['feedback'][0]['result']['status'] == 'new_pixel'
        with pytest.raises(ValueError,match='duplicate_ACT'):
            hub.native(dict(session_id=identifier,request=request,records=bundle))
    assert hub.sessions['first'].game is not hub.sessions['second'].game
    assert len(hub.sessions['first'].seen) == len(hub.sessions['second'].seen) == 1
    with pytest.raises(ValueError,match='registered_session'):
        hub.native(dict(session_id='../escape',request={},records=[]))
