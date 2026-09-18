import json

import pytest

from gpu import orch_r108_code_parent_exchange as exchange


def test_snapshot_excludes_held_scores_and_raw(tmp_path, monkeypatch):
    monkeypatch.setattr(exchange, 'ROOTS', {4: str(tmp_path)})
    lane = tmp_path / 'campaign_code_parent'
    (lane / 'cells').mkdir(parents=True)
    (tmp_path / 'READY.json').write_text('{}')
    (lane / 'CYCLE_001_COMPLETE.json').write_text(json.dumps({'held': ['SEALED_DO_NOT_TRANSMIT']}))
    (lane / 'cells' / 'parent.json').write_text(json.dumps(dict(cycle=1, kind='PARENT', status='MISSING', raw='RAW_SECRET')))
    (lane / 'TRIPLE_C001_E1_S2.json').write_text(json.dumps(dict(episode_index=1, continuation_changed=True,
        before={'score': 'SEALED_DO_NOT_TRANSMIT'}, after={'raw': 'RAW_SECRET'})))
    value = exchange.snapshot(tmp_path, 4)
    assert 'SEALED_DO_NOT_TRANSMIT' not in json.dumps(value) and 'RAW_SECRET' not in json.dumps(value)
    assert value['cycles'][0]['unusable_parent_turns'] == 1
    assert value['cycles'][0]['semantic_behavior_change'] == 'UNREVIEWED'


def test_append_only_deduplicated_and_preserves_other_owners(tmp_path):
    path = tmp_path / 'PARENTING_EXCHANGE.md'
    path.write_text('Existing other-half entry\n')
    row = dict(index=4, cycle=1, includes_held_outcomes=False, raw_in_repository=False,
        declared_operations={}, parent_turns_recorded=2, accepted_parent_turns=1,
        unusable_parent_turns=1, changed_train_continuation_texts=1, actual_train_triples=1,
        raw_pointer='/node/raw', source_root='/node/source', ready_sha256='ready', cycle_receipt_sha256='cycle')
    assert exchange.append_exchange(path, [row]) == 1
    first = path.read_bytes()
    assert exchange.append_exchange(path, [row]) == 0 and path.read_bytes() == first
    assert first.startswith(b'Existing other-half entry\n')
    row['includes_held_outcomes'] = True
    with pytest.raises(ValueError):
        exchange.append_exchange(path, [row])
