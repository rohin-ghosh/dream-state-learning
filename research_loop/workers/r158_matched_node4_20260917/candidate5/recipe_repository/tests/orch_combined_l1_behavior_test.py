"""Descriptions never become form-based admission or invented behavioral scores."""

from copy import deepcopy
import json

import pytest

from gpu.orch_combined_l1_behavior import analyze
from organism_v6.orch_combined_l1_behavior import describe, text_hash


TEXT = 'I could add the rates. Multiplying rates gives the wrong units. I reject multiplication because the units are squared.'


def annotation():
    return dict(response_sha256=text_hash(TEXT), review_kind='AUTHOR_DESCRIPTIVE_FULL_OUTPUT',
        full_output_read=True, parent_access=False, reviewer='test-author', reason='Two different rate operations are evaluated.',
        considered_paths=[dict(id='sum', operation='add rates', evidence='add the rates',
            actually_considered_not_merely_named=True),
            dict(id='product', operation='multiply rates', evidence='Multiplying rates',
                actually_considered_not_merely_named=True, substantively_distinct=True,
                distinction_reason='Product changes dimensionality; sum preserves rates.')],
        rejections=[dict(path_id='product', rejection_evidence='I reject multiplication',
            reason_evidence='because the units are squared', problem_grounded_reason=True)])


def test_no_lexical_proxy_claims_considered_alternatives():
    result = describe('Alternative alternative reject reconsider. FINAL: 7')
    assert result['semantic']['status'] == 'UNASSESSED'
    assert result['semantic']['distinct_alternatives_considered'] is None


def test_evidence_bound_descriptive_paths_and_rejection():
    result = describe(TEXT, annotation())['semantic']
    assert result['distinct_alternatives_considered'] == 1
    assert result['paths_rejected_with_grounded_reason'] == 1
    assert not result['improvement_claim'] and not result['used_as_quality_gate']


@pytest.mark.parametrize('change', ['hash', 'duplicate', 'evidence', 'parent', 'named_only', 'ungrounded'])
def test_invalid_semantic_annotation_rejected(change):
    review = deepcopy(annotation())
    if change == 'hash':
        review['response_sha256'] = 'bad'
    elif change == 'duplicate':
        review['considered_paths'][1]['operation'] = ' ADD   RATES '
    elif change == 'evidence':
        review['rejections'][0]['reason_evidence'] = 'not present'
    elif change == 'parent':
        review['parent_access'] = True
    elif change == 'named_only':
        review['considered_paths'][1]['actually_considered_not_merely_named'] = False
    else:
        review['rejections'][0]['problem_grounded_reason'] = False
    with pytest.raises(AssertionError):
        describe(TEXT, review)


def test_repetition_descriptive_not_gate_and_empty_safe():
    result = describe('Compute the total now.\nCompute the total now.')['repetition']
    assert result['repeated_sentence_occurrences'] == 1
    assert result['repeated_fourgram_occurrences'] >= 1
    assert result['used_as_quality_gate'] is False
    assert describe('')['repetition']['word_fourgrams'] == 0


@pytest.mark.parametrize('purpose', ['math_held', 'math'])
def test_reads_same_held_outputs_preserves_failure_and_never_rewrites(tmp_path, purpose):
    readout = tmp_path / 'readout'
    readout.mkdir()
    (readout / 'LOADED.json').write_text(json.dumps(dict(parent_present=False)))
    good = dict(position=0, status='COMPLETE', metadata=dict(purpose=purpose, task_id='task1'), response=dict(raw=TEXT))
    failed = dict(position=1, status='FAILED', metadata=dict(purpose='math_held', task_id='task2'), error='preserved')
    for position, call in enumerate((good, failed)):
        (readout / f'CALL_{position:03d}.json').write_text(json.dumps(call))
    before = {path.name: path.read_bytes() for path in readout.iterdir()}
    output = tmp_path / 'sealed'
    report = analyze(readout, output)
    assert analyze(readout, output) == report
    data = json.loads(report.read_text())
    assert data['completed'] == data['failed'] == data['semantic_unassessed'] == 1
    assert data['native_calls'] == 0 and data['semantic_reviewed'] == 0
    assert {path.name: path.read_bytes() for path in readout.iterdir()} == before


def test_parent_readout_rejected(tmp_path):
    root = tmp_path / 'readout'
    root.mkdir()
    (root / 'LOADED.json').write_text(json.dumps(dict(parent_present=True)))
    with pytest.raises(AssertionError, match='parent_free'):
        analyze(root, tmp_path / 'sealed')


def test_exact_token_and_eos_vs_ceiling_metrics():
    from organism_v6.orch_combined_l1_behavior import token_metrics
    result = token_metrics(dict(token_ids=[1, 2, 3], terminal=True, truncated=False), 3)
    assert result['generated_tokens'] == 3 and result['text_tokens'] == 2
    assert result['eos'] and not result['ceiling']
    result = token_metrics(dict(token_ids=[1, 2, 3], terminal=False, truncated=True), 3)
    assert not result['eos'] and result['ceiling']
    assert token_metrics('plain', 3)['generated_tokens'] is None


def test_richness_first_keeps_accuracy_and_no_semantic_proxy():
    result = describe(TEXT)
    assert result['report_order'] == ['richness', 'accuracy']
    assert result['accuracy_retained'] and not result['correctness_is_primary']
    assert result['coherence']['judgment'] is None
    assert result['semantic']['distinct_paths_considered'] is None
