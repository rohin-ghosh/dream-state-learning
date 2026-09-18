import copy
import hashlib
import json

import pytest

from research_loop.workers.rohin221_continuous_caption_20260918 import seed_packet


@pytest.fixture
def candidates():
    document = json.loads((seed_packet.ROOT / 'R230_FROZEN_BASE_SEED_PACKET_v1.json').read_bytes())
    audit = json.loads((seed_packet.ROOT / 'R230_SEED_SELECTION_AUDIT_v1.json').read_bytes())
    rows, examples = [], []
    for row in audit['rows']:
        rows.append(dict(sequence=row['sequence'], text_sha256=row['caption_sha256'],
            receipt_sha256=row['receipt_sha256'], contest_id=row['contest_id'], rank=row['rank'], status='new_pixel'))
    for example in document['examples']:
        source = example['source']
        matching = next(row for row in rows if row['text_sha256'] == example['caption_sha256'])
        matching['literal_text'] = example['caption']
        examples.append(dict(literal_child_caption=example['caption'], exact_source_span=source['literal_span'],
            result=example['historical_result'], novelty=example['novelty_proof'], exact_generation_hashes_verified=True,
            scorer_result=dict(sha256=source['result_receipt_sha256']), scene=example['scene'],
            scored_utc=example['scored_utc'], opportunity=source['opportunity'], attempt=source['attempt'],
            generation=dict(sha256=source['generation_file_sha256']), request_sha256=source['request_sha256'],
            response_sha256=source['response_sha256'], ACT_finished_utc=source['ACT_finished_utc']))
    return dict(frozen_cut_sha256=seed_packet.SOURCE_CUT_SHA256, review_rows=rows, examples=examples)


def test_only_actual_reviewed_two_no_quota_padding(candidates):
    packet, audit = seed_packet.build_packet(candidates)
    assert packet['selected_examples'] == 2 and not packet['quota_filled']
    assert len(audit['rows']) == 47 and sum(row['included'] for row in audit['rows']) == 2
    assert [item['historical_result']['rank'] for item in packet['examples']] == [14,21]
    assert packet['rollout']['status'] == 'PREPARED_NOT_DELIVERED'
    assert packet['usage']['preserve_frozen_base_unseeded_control']
    assert not packet['usage']['count_as_new_exploration']
    assert packet['usage']['training_eligibility_unchanged']


@pytest.mark.parametrize('key,value', [('accepted', False), ('status', 'repeat'), ('replayed', True)])
def test_repeat_cached_or_rejected_seed_disallowed(candidates, key, value):
    candidates['examples'][0]['result'][key] = value
    with pytest.raises(ValueError, match='actual_new_noncached_ACT_proof_required'):
        seed_packet.select_examples(candidates)


def test_changed_caption_or_receipt_not_a_seed(candidates):
    changed = copy.deepcopy(candidates)
    changed['examples'][0]['literal_child_caption'] += ' Manufactured improvement.'
    with pytest.raises(ValueError, match='exact_literal_caption_required'):
        seed_packet.select_examples(changed)
    candidates['examples'][0]['scorer_result']['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='exact_result_receipt_required'):
        seed_packet.select_examples(candidates)


def test_wrong_cut_and_unproven_origin_rejected(candidates):
    changed = copy.deepcopy(candidates)
    changed['frozen_cut_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='exact_reviewed_cut_required'):
        seed_packet.select_examples(changed)
    candidates['examples'][0]['exact_generation_hashes_verified'] = False
    with pytest.raises(ValueError, match='actual_new_noncached_ACT_proof_required'):
        seed_packet.select_examples(candidates)


def test_historical_rank_cannot_be_improved(candidates):
    candidates['examples'][0]['result']['rank'] = 1
    with pytest.raises(ValueError, match='unchanged_historical_rank_required'):
        seed_packet.select_examples(candidates)


def test_packet_context_hash_and_literal_content():
    packet = json.loads((seed_packet.ROOT / 'R230_FROZEN_BASE_SEED_PACKET_v1.json').read_bytes())
    context = (seed_packet.ROOT / packet['child_context']['file']).read_bytes()
    assert hashlib.sha256(context).hexdigest() == packet['child_context']['sha256']
    assert seed_packet.child_context(packet).encode() == context
    for example in packet['examples']:
        assert example['caption'].encode() in context
        assert hashlib.sha256(example['caption'].encode()).hexdigest() == example['caption_sha256']
    assert b'not your attempts or new judge feedback' in context
    assert 'First actual REQUEST' in packet['rollout']['curve_boundary']
