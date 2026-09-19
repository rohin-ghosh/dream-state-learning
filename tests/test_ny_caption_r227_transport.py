import json

import pytest

from gpu.ny_caption_life import child_act, latest_own_think
from gpu.orch_r125_stream_journal import _digest
from research_loop.workers.rohin221_continuous_caption_20260918 import journal_bundle, journal_transport


def actual_chain(root):
    directory = root / 'stream/records'
    directory.mkdir(parents=True)
    previous, origin = 'seed', None
    documents = []
    for stage in ['THINK', 'ACT']:
        response = dict(response=dict(raw='Scene1:\n"'+stage+' literal."'))
        documents.extend([('RESPONSE', response),
            ('COMMITTED', dict(source_sha256=_digest(response), state='retained-state-' * 30)),
            ('R184_STAGE', dict(stage=stage, source_sha256=_digest(response)))])
    for index, (kind, document) in enumerate(documents):
        record = dict(index=index, journal_id='actual-journal', previous_sha256=previous, kind=kind, document=document)
        record['sha256'] = _digest(record)
        previous = record['sha256']
        (directory / f'{index:020d}.json').write_text(json.dumps(record))
        if index == 3:
            origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=index, record_sha256=record['sha256'])
    return origin


def test_complete_think_ancestry_exceeding_single_envelope_keeps_exact_bytes(tmp_path, monkeypatch):
    origin = actual_chain(tmp_path / 'source')
    monkeypatch.setattr(journal_bundle, 'MAX_BYTES', 1200)
    monkeypatch.setattr(journal_transport, 'MAX_BYTES', 1200)
    with pytest.raises(ValueError, match='bounded_journal_transfer'):
        journal_bundle.export_records(tmp_path / 'source', origin, 'actual-journal')
    envelope = journal_transport.export_chunks(tmp_path / 'source', origin, 'actual-journal')
    assert len(envelope['chunks']) > 1 and envelope['complete_THINK_ancestry']
    for chunk in envelope['chunks']:
        journal_bundle.import_records(tmp_path / 'mirror', chunk, 'actual-journal')
    assert child_act(tmp_path / 'mirror', origin) == 'Scene1:\n"ACT literal."'
    assert latest_own_think(tmp_path / 'mirror', origin)['raw'] == 'Scene1:\n"THINK literal."'
    for path in (tmp_path / 'source/stream/records').iterdir():
        assert (tmp_path / 'mirror/stream/records' / path.name).read_bytes() == path.read_bytes()


def test_total_bound_and_foreign_journal_stay_rejected(tmp_path, monkeypatch):
    origin = actual_chain(tmp_path / 'source')
    with pytest.raises(ValueError, match='same_bound_journal'):
        journal_transport.export_chunks(tmp_path / 'source', origin, 'foreign')
    monkeypatch.setattr(journal_transport, 'MAX_TOTAL_BYTES', 100)
    with pytest.raises(ValueError, match='bounded_total_journal'):
        journal_transport.export_chunks(tmp_path / 'source', origin, 'actual-journal')
