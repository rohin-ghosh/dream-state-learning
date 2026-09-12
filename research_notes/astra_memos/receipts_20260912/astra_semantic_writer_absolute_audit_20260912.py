import hashlib
import json
import math
from pathlib import Path
import statistics


def absolute_shift(off, on):
    baseline = [math.exp(value) for value in off]
    fitted = [math.exp(value) for value in on]
    if sum(baseline) > 1.000001 or sum(fitted) > 1.000001:
        raise ValueError('disjoint terminated sequence mass exceeds one')
    changes = [right - left for left, right in zip(baseline, fitted)]
    return dict(off_candidate_mass=sum(baseline), on_candidate_mass=sum(fitted),
        coarse_three_category_tv=(sum(abs(value) for value in changes) + abs(sum(changes))) / 2,
        mean_sequence_logprob_shift=statistics.mean(right - left for left, right in zip(off, on)))


def legality_changes(off, on):
    changes = [int(right is not None) - int(left is not None) for left, right in zip(off, on)]
    return dict(valid_to_invalid=changes.count(-1), invalid_to_valid=changes.count(1),
        mean_absolute_itemwise_change=statistics.mean(abs(value) for value in changes),
        original_absolute_mean_change=abs(statistics.mean(changes)),
        changed_action_count=sum(left != right for left, right in zip(off, on)))


if __name__ == '__main__':
    fixture = absolute_shift([-100, -101], [-1, -2])
    assert fixture['coarse_three_category_tv'] > .50
    assert fixture['mean_sequence_logprob_shift'] == 99
    cancellation = legality_changes(['valid', None], [None, 'valid'])
    assert cancellation['mean_absolute_itemwise_change'] == 1
    assert cancellation['original_absolute_mean_change'] == 0
    path = Path('/tmp/astra_semantic_writer_replay_20260912.json')
    expected = '9e4480d176da221c1f16f9915aa13dcf78014d76bcaa100102ce56d7e2cd57eb'
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('original-source replay identity differs')
    report = json.loads(path.read_bytes())
    indexed = {tuple(row['coordinate']): row['result'] for row in report['details']}
    assert len(indexed) == 1712
    cells = []
    for state, root in [('r0_plus', 0), ('r0_minus', 0), ('r1_plus', 1), ('r1_minus', 1)]:
        for family, count in [('primary', 64), ('missing', 8), ('unsupported', 8), ('neighbour', 16), ('wrong_root', 64)]:
            probe, baseline_family = (1 - root, 'primary') if family == 'wrong_root' else (root, family)
            rows, off_actions, on_actions = [], [], []
            for index in range(count):
                off = indexed['OFF', probe, baseline_family, index, 'score']
                on = indexed[state, probe, family, index, 'score']
                assert all(math.isfinite(value) and value <= 0 for value in off + on)
                rows.append(dict(index=index, **absolute_shift(off, on)))
                off_actions.append(indexed['OFF', probe, baseline_family, index, 'generate']['action'])
                on_actions.append(indexed[state, probe, family, index, 'generate']['action'])
            fields = ['off_candidate_mass', 'on_candidate_mass', 'coarse_three_category_tv', 'mean_sequence_logprob_shift']
            cells.append(dict(state=state, family=family, n=count, rows=rows,
                means={field: statistics.mean(row[field] for row in rows) for field in fields},
                legality=legality_changes(off_actions, on_actions)))
    output = dict(status='POST_HOC_DIAGNOSTIC_NO_GATE_REPLACEMENT', source_replay_sha256=expected,
        interpretation='Absolute mass is for two full candidate sequences including LF and EOS; coarse TV is a lower bound, not full-distribution TV. Greedy outputs omit LF, so candidate mass is not literal greedy frequency.',
        new_fits=0, new_model_calls=0, original_label=report['label'], original_gates=report['gates'],
        synthetic_regression_checks=2, cells=cells)
    print(json.dumps(output, sort_keys=True, indent=2, allow_nan=False))
