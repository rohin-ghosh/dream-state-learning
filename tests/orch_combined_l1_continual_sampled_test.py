"""Sampled admission is batch-level, exact-source-bound and append-once."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from gpu import orch_combined_l1_continual_sampled as sampled
from gpu import orch_combined_l1_continual_content as content
from organism_v6 import orch_combined_l1_continual as state_policy


def fixture():
    root = Path(__file__).resolve().parents[1] / 'research_notes/analysis/orch_combined_l1_continual_20260915_attempt1'
    pending = root / 'SAMPLED_QUEUE_PENDING/highbudget_math_sampled_001_20260915_content_v2'
    if not pending.exists():
        pytest.skip('source-only checkout without sampled64 proof')
    return json.loads((pending / 'BOUND_PACKET.json').read_text()), json.loads((pending / 'EXCLUSIONS.json').read_text())


def test_all64_append_once_preserve_unsampled_historical_labels():
    packet, exclusions = fixture()
    before = deepcopy(packet)
    state = state_policy.initial_state([], 'initial')
    result = content.append(state, packet, exclusions)
    assert result['ingested'][-1]['added'] == 64
    assert sum(entry['row']['review'] is None for entry in result['rows']) == 52
    assert all(entry['row']['admitted'] is False and entry['row']['trainingAllowed'] is False for entry in result['rows'])
    assert all(entry['row']['semantic_status'] == 'UNREVIEWED' for entry in result['rows'] if entry['row']['review'] is None)
    assert packet == before
    assert content.append(result, packet, exclusions) is result


@pytest.mark.parametrize('change', ['label', 'review', 'target', 'sample', 'teacher', 'parent', 'policy', 'candidate'])
def test_mutations_fail_closed(change):
    packet, exclusions = fixture()
    if change == 'label':
        packet['rows'][0]['row']['admitted'] = True
    elif change == 'review':
        packet['proof']['reviews'][0]['grounded_operations'] = False
    elif change == 'target':
        packet['rows'][0]['row']['target'] += ' rescued'
    elif change == 'sample':
        packet['proof']['sample_registration']['semantic_results_seen'] = True
    elif change == 'teacher':
        packet['strong_teacher_source'] = True
    elif change == 'parent':
        packet['parenting_experience'] = True
    elif change == 'policy':
        packet['policy_sha256'] = 'unbound'
    else:
        packet['proof']['candidates'][0]['gold'] = '99999'
    packet['rows_sha256'] = state_policy.digest(packet['rows'])
    with pytest.raises((AssertionError, ValueError)):
        sampled.validate_packet(packet, exclusions)


def test_exact_whole_current_corpus_dedup():
    packet, exclusions = fixture()
    existing = state_policy.initial_state([packet['rows'][0]], 'initial')
    result = sampled.append(existing, packet, exclusions)
    assert len(result['rows']) == 64 and result['ingested'][-1]['added'] == 63
    assert result['rows'][0] == packet['rows'][0]
    assert len(result['duplicates']) == 1


@pytest.mark.parametrize('key', ['held_math', 'held_question_hashes'])
def test_held_exclusion_even_if_batch_accepted(key):
    packet, exclusions = fixture()
    row = packet['rows'][0]['row']
    exclusions[key].append(row['task_id'] if key == 'held_math' else row['question_sha256'])
    with pytest.raises(AssertionError, match='held_'):
        sampled.validate_packet(packet, exclusions)


def test_same_batch_id_cannot_rebind():
    packet, exclusions = fixture()
    state = sampled.append(state_policy.initial_state([], 'initial'), packet, exclusions)
    packet['provenance']['invented'] = True
    with pytest.raises(AssertionError, match='rebound'):
        sampled.append(state, packet, exclusions)


def test_unreviewed_gold_review_remains_absent():
    packet, exclusions = fixture()
    for entry in packet['rows']:
        content.validate_entry(entry, exclusions)
        if entry['row']['review'] is None:
            assert entry['gold_review'] is None
            assert entry['eligibility']['semantic_branching_measured'] is False
            assert set(entry['eligibility']['content_axes'].values()) == {None}


def test_three_rank_cli_admits_already_supported_partition():
    from gpu.orch_combined_l1_continual_run import argument_parser
    args = argument_parser().parse_args(['train', '--root', '/tmp/owned', '--arm', 'FULL',
        '--rank', '2', '--world-size', '3', '--index', '6'])
    assert state_policy.rank_positions(args.rank, args.world_size) == (2,)
