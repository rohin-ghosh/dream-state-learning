import json

import pytest

from r188_stop import digest, retained_update


def fixture(tmp_path, kind='UPDATE'):
    record = dict(kind=kind,journal_id='actual',index=5248,previous_sha256='previous',
        document=dict(optimizer_step=4531,finished_unix=1.0))
    record['sha256'] = digest(record)
    path = tmp_path / '00000000000000005248.json'
    path.write_text(json.dumps(record))
    path.with_name(path.stem + '.intent.json').write_text(json.dumps(dict(record_sha256=record['sha256'],
        index=record['index'],previous_sha256=record['previous_sha256'])))
    return path


def test_loss_count_is_recorded_only(tmp_path):
    proof = retained_update(fixture(tmp_path), 'actual', 4428)
    assert proof['discarded_recorded_updates'] == 103
    assert proof['possible_unlogged_inflight_update'] == 'UNKNOWN_SEPARATE_FROM_RECORDED_COUNT'


def test_no_other_boundary_or_life(tmp_path):
    path = fixture(tmp_path, 'SLEEP_COMPLETE')
    with pytest.raises(ValueError, match='retained_UPDATE'):
        retained_update(path, 'actual', 4428)


def test_broken_intent_no_stop_proof(tmp_path):
    path = fixture(tmp_path)
    path.with_name(path.stem + '.intent.json').write_text('{}')
    with pytest.raises((ValueError, KeyError)):
        retained_update(path, 'actual', 4428)
