from collections import Counter
import json
from pathlib import Path

root = Path('/tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1')
plan = json.loads((root / 'plan.json').read_text())
release = json.loads((root / 'readout_main_release.json').read_text())
rows = {}
for cell in ('OFF', 'teach', 'control'):
    result = json.loads((root / 'readouts' / cell / 'reduction.json').read_text())
    assert [row['case_id'] for row in result['rows']] == plan['eval_dev_ids']
    assert result['model_files'] == plan['model_files']
    assert result['counts'] == release['cells'][cell]['counts']
    memory = [row for row in result['rows'] if row['kind'] == 'memory_recall']
    rows[cell] = dict(counts=result['counts'], memory_answers=dict(Counter(row['raw_text'] for row in memory)),
        expected_memory_colors=dict(Counter(row['expected'] for row in memory)))
fit_cost = {}
for arm in ('teach', 'control'):
    result = json.loads((root / ('fit_' + arm) / 'result.json').read_text())
    manifest = result['manifest']
    assert manifest['config'] == plan['config']
    assert manifest['steps'] == 80 and manifest['train_tokens_seen'] == 18068
    assert manifest['tokens']['target'] == 912
    fit_cost[arm] = dict(train_seconds=manifest['train_seconds'], worker_wall_seconds=manifest['wall_seconds'],
        supervised_seconds=result['supervised']['reserved_seconds'], target_by_view_per_epoch=manifest['tokens']['target_by_view'])
summary = dict(cells=rows, fit_cost=fit_cost, readout_totals=release['totals'],
    supervised_fit_plus_readout_seconds=sum(row['supervised_seconds'] for row in fit_cost.values()) + release['totals']['supervised_readout_seconds'],
    confirmation_requests=0, seed=0, exploratory=True,
    interpretation='Textual format transfer after reload; factual device-color binding not demonstrated; no parenting or improved arithmetic ability claim.')
destination = Path('/tmp/astra_fundamental_seed0_main_analysis_20260912.json')
with destination.open('x') as output:
    json.dump(summary, output, indent=2, sort_keys=True)
print(json.dumps(dict(fit_cost=fit_cost, readout_totals=summary['readout_totals'],
    supervised_fit_plus_readout_seconds=summary['supervised_fit_plus_readout_seconds']), indent=2))
