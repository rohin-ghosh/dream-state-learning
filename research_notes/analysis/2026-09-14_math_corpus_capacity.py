"""Conditional sizing from recorded routing metadata, not a new collection."""

from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'research_notes/analysis/orch_math_rich_20260914_attempt1'


def calculate():
    names = ('TASKS_VIEW.json', 'REDUCTION.json', 'ADMITTED_ROWS.json', 'DISTRIBUTION.json')
    documents = {name: json.loads((EVIDENCE / name).read_text()) for name in names}
    tasks = documents['TASKS_VIEW.json']
    result = documents['REDUCTION.json']
    admitted = documents['ADMITTED_ROWS.json']
    roster = {task['id']: task for task in tasks['tasks']}
    assert len(roster) == tasks['denominator'] == result['denominator'] == 32
    assert len(admitted) == result['admitted'] == 19
    assert len({row['target_sha256'] for row in admitted}) == len(admitted)
    row_counts, task_sets = Counter(), defaultdict(set)
    for row in admitted:
        assert row['task_id'] in roster
        assert roster[row['task_id']]['family'] == row['family']
        assert hashlib.sha256(row['target'].encode()).hexdigest() == row['target_sha256']
        row_counts[row['family']] += 1
        task_sets[row['family']].add(row['task_id'])
    assert dict(row_counts) == result['admitted_by_family']
    assert sum(map(len, task_sets.values())) == result['admitted_distinct_tasks'] == 16
    families = {}
    row_rates = {}
    remaining = {}
    for family, measured in sorted(result['families'].items()):
        denominator = measured['denominator']
        assert denominator == sum(task['family'] == family for task in roster.values())
        rate = Fraction(row_counts[family], denominator)
        row_rates[family] = rate
        available = tasks['family_counts'][family] - denominator
        remaining[family] = available
        families[family] = {
            'recorded_unique_pool': tasks['family_counts'][family],
            'screen_tasks': denominator, 'remaining_unscreened_metadata_count': available,
            'admitted_rows': row_counts[family], 'admitted_distinct_tasks': len(task_sets[family]),
            'observed_rows_per_task': str(rate),
            'conditional_128_new_tasks_rows': float(128 * rate),
            'conditional_all_remaining_rows': float(available * rate),
        }
    rate_sum = sum(row_rates.values())
    task_cost = result['assigned_gpu_hours_completed'] / result['denominator']
    scenarios = []
    for target_rows in (1000, 5000):
        per_family = math.ceil(Fraction(target_rows) / rate_sum)
        task_count = per_family * len(families)
        scenarios.append({
            'target_new_admitted_rows': target_rows,
            'balanced_tasks_per_family_at_observed_rates': per_family,
            'total_new_tasks': task_count,
            'conditional_new_admitted_rows': float(per_family * rate_sum),
            'fits_recorded_remaining_pool': all(per_family <= available for available in remaining.values()),
            'conditional_screen_only_gpu_hours': task_count * task_cost,
            'conditional_calls_at_observed_three_per_task': 3 * task_count,
        })
    balanced_limit = min(remaining.values())
    return {
        'status': 'POSTHOC_CONDITIONAL_SIZING_NOT_AUTHORIZATION',
        'current_eligible_scale_families': result['eligible_scale_families'],
        'current_fit_ready': result['fit_ready'],
        'held_contents_opened': False,
        'scope': 'Uses recorded family counts and screen metadata only; no new source questions, held items, model calls or semantic re-review.',
        'families': families,
        'all_remaining_mining_tasks': sum(remaining.values()),
        'conditional_all_remaining_rows_at_family_rates': float(sum(remaining[family] * row_rates[family] for family in families)),
        'max_balanced_new_tasks_per_family': balanced_limit,
        'conditional_rows_at_balanced_pool_limit': float(balanced_limit * rate_sum),
        'conditional_128_each_total_rows': float(128 * rate_sum),
        'conditional_128_each_screen_gpu_hours': 128 * len(families) * task_cost,
        'observed_assigned_screen_gpu_hours_per_task': task_cost,
        'observed_distinct_tasks_per_19_rows': 16,
        'scenarios': scenarios,
        'limits': 'Eight measured tasks/family, not an IID yield estimate or confidence interval. Prompt/decoding/review changes invalidate extrapolation. Complete-screen task cost is not marginal generation, review, fit, checkpoint, or transfer cost. Old zero-call engineering overhead excluded; no capacity here is currently approved to scale.',
        'source_sha256': {name: hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest() for name in names},
    }


if __name__ == '__main__':
    print(json.dumps(calculate(), indent=2, sort_keys=True))
