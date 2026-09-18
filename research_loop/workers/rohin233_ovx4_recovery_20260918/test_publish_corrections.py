import copy
import hashlib
import pytest

from research_loop.workers.rohin233_ovx4_recovery_20260918 import publish_corrections as subject


def sample():
    caption = 'Synthetic café caption.'
    checksum = hashlib.sha256(caption.encode()).hexdigest()
    row = dict(player='P3', caption=caption, caption_sha256=checksum, parent_correction_eligible=True,
        old_raw_accepted=True, new_rank_relevance_pass=False, old_rank=14, new_rank=60,
        source=dict(origin=dict(kind='TRAIN_CHILD_RESPONSE', record_index=7, record_sha256='a'*64),
                    stage='ACT', start=0, end=len(caption), text_sha256=checksum))
    return row, dict(rows=[copy.deepcopy(row)])


def test_verified_own_only_and_changed_outcomes(tmp_path):
    row, complete = sample()
    seed = dict(row, player='FROZEN_BASE_SEED')
    rows = subject.verified_rows([row, seed], complete, tmp_path, lambda *args: row['caption'])
    text, changed = subject.notice(rows)
    assert rows == changed == [row]
    assert 'not new submissions' in text and 'novelty and pixel awards were NOT recomputed' in text
    assert 'new rank 60' in text and 'Synthetic café caption.' in text
    with pytest.raises(ValueError, match='exact_own_caption_span'):
        subject.verified_rows([row], complete, tmp_path, lambda *args: 'X'+row['caption'][1:])
    with pytest.raises(ValueError, match='own_origin_verified_only'):
        subject.verified_rows([dict(row, parent_correction_eligible=False)], complete, tmp_path)


def test_deterministic_publication_and_retry(tmp_path):
    life = tmp_path/'life'
    (life/'stream/inbox').mkdir(parents=True)
    output = tmp_path/'output'
    output.mkdir()
    row, _ = sample()
    text, _ = subject.notice([row])
    projection = dict(text=text, rows=[row])
    first, reused = subject.publish(life, output, text, projection)
    assert not reused
    second, reused = subject.publish(life, output, text, projection)
    assert second == first and reused
    assert len(list((life/'stream/inbox').glob('*.json'))) == 1


def test_metadata_shaped_display_survives_without_changing_payload():
    row, _ = sample()
    row['caption'] = 'source_sha256 is untrusted child text.'
    text, changed = subject.notice([row])
    assert not subject.has_scaffolding('Tool: ' + text)
    assert changed[0]['caption'] == row['caption']
