import pytest

from gpu import orch_r106_composition as measure
from gpu import orch_r106_author_annotations as author


def test_decimal_and_complete_coverage():
    text = 'We have 2.5 units. Check the scale. FINAL: 5'
    spans = measure.segments(text)
    assert ''.join(text[start:end] for start, end in spans) == text
    assert len(spans) == 3
    assert '2.5' in text[spans[0][0]:spans[0][1]]


def test_checks_are_not_method_counts():
    text = 'Compute 2+2. Check by subtraction. FINAL: 4'
    spans = measure.segments(text)
    annotation = dict(text_sha256=measure.digest(text.encode()),
        labels=['direct_computation', 'checks_verification', 'final_answer'],
        worked_methods=1, departures_and_returns=[dict(main=0, departure=1,
            return_phase='terminal_check_or_aside', kind='check', reason='Verification then answer')])
    annotation['departures_and_returns'][0]['return'] = 2
    assert measure.validate_annotation(annotation, text, spans) == annotation['labels']
    assert annotation['worked_methods'] == 1


@pytest.mark.parametrize('change', ['hash', 'missing_label', 'return_before_departure'])
def test_reject_unbound_annotations(change):
    text = 'Compute. Check. FINAL: 4'
    spans = measure.segments(text)
    annotation = dict(text_sha256=measure.digest(text.encode()),
        labels=['direct_computation', 'checks_verification', 'final_answer'],
        worked_methods=1, departures_and_returns=[])
    if change == 'hash':
        annotation['text_sha256'] = 'wrong'
    elif change == 'missing_label':
        annotation['labels'].pop()
    else:
        annotation['departures_and_returns'] = [{'main': 0, 'departure': 2, 'return': 1}]
    with pytest.raises(ValueError):
        measure.validate_annotation(annotation, text, spans)


def test_token_counts_conserve_cross_boundary_tokens():
    counts = measure.count_tokens([(0, 2), (2, 6), (6, 8)], [(0, 3), (3, 8)],
                                  ['direct_computation', 'checks_verification'])
    assert sum(counts.values()) == 3
    assert counts['direct_computation'] == 1
    assert counts['checks_verification'] == 2


def test_proxy_is_not_semantic_branching():
    assert measure.proxy_label('Check the result.') == 'checks_verification'
    assert measure.proxy_label('Next, multiply by 2.') == 'direct_computation'
    assert measure.proxy_label('My reasoning needs revision.') == 'meta_comments'


def test_empty_output_rejected():
    with pytest.raises(ValueError):
        measure.segments('  ')


def test_fixed_sample_separate_from_selected_positive_cases():
    annotations = author.annotations()
    assert len(annotations) == 23
    assert sum(row['sample'] == 'fixed_first4' for row in annotations.values()) == 12
    assert sum(bool(row['departures_and_returns']) for row in annotations.values()) == 11
    assert all(row['worked_methods'] == 1 for row in annotations.values())
    branches = [branch for row in annotations.values() for branch in row['departures_and_returns']]
    assert sum(branch['return_phase'] == 'mid_solution' for branch in branches) == 3


def test_terminal_check_cannot_inflate_mid_solution_count():
    text = 'Compute 2+2. Check by subtraction. FINAL: 4'
    annotation = dict(text_sha256=measure.digest(text.encode()), worked_methods=1,
        labels=['direct_computation', 'checks_verification', 'final_answer'],
        departures_and_returns=[{'main': 0, 'departure': 1, 'return': 2,
            'kind': 'check', 'reason': 'verification', 'return_phase': 'mid_solution'}])
    with pytest.raises(ValueError, match='return phase'):
        measure.validate_annotation(annotation, text, measure.segments(text))
