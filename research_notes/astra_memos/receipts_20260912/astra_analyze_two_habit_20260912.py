import datetime
import hashlib
import json
from pathlib import Path
import re


root = Path('/tmp/astra_two_habit_terminal_20260912')
validation = json.loads(Path(str(root) + '.tgz.validation.json').read_text())
assert hashlib.sha256(Path(str(root) + '.tgz').read_bytes()).hexdigest() == validation['sha256']
for name, expected in validation['files'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected
base = root / 'astra_diagnostics/astra_fundamental_two_habit_20260912_attempt1/seed0'
plan = json.loads((base / 'plan.json').read_text())
terminal = json.loads((base / 'run/terminal.json').read_text())
release = json.loads((base / 'run/main_release.json').read_text())
assert terminal['status'] == 'COMPLETE' and release['full_release'] and release['controller_absent']
assert release['terminal_sha256'] == hashlib.sha256((base / 'run/terminal.json').read_bytes()).hexdigest()
arms = {}
for arm in ('input_before', 'input_after'):
    folder = base / 'run' / arm
    scores = json.loads((folder / 'two-habit-scores.json').read_text())
    reduction = json.loads((folder / 'readout/reduction.json').read_text())
    manifest = json.loads((folder / 'adapter/train_manifest.json').read_text())
    assert manifest['steps'] == 80 and manifest['epochs_run'] == 4 and manifest['nonfinite_batches'] == 0
    assert len(scores['rows']) == len(reduction['rows']) == 48
    own_exact = 0
    for row in reduction['rows']:
        stem = folder / 'readout/run/data/calls' / row['call_id']
        response = json.loads(Path(str(stem) + '.response.json').read_text())['response']
        assert response['text'] == row['raw_text']
        if row['kind'] != 'addition':
            continue
        operands = re.search(r'Add (\d+) and (\d+)\.', response['rendered_prompt'])
        assert operands
        left, right = map(int, operands.groups())
        fields = [f'INPUT: {left}, {right}', f'PREDICT: {left + right}', f'ACT: {left + right}']
        expected = fields if arm == 'input_before' else fields[1:] + fields[:1]
        own_exact += response['text'] == '\n'.join(expected)
    counts = scores['counts']
    assert own_exact == counts['addition']['own_order_success']
    baseline_memory = plan['parent']['baseline']['counts']['memory']
    passed = (own_exact >= 28 and counts['addition']['opposite_order_count'] <= 4 and
        counts['addition']['original_adherence'] >= 30 and counts['addition']['act_success'] >= 31 and
        counts['memory']['tag_spill'] - baseline_memory['tag_spill'] <= 1 and
        (counts['memory']['invalid'] - baseline_memory['invalid']) / 16 <= .05)
    arms[arm] = dict(counts=counts, raw_exact_own_map=own_exact, gate_pass=passed,
        input_presentations=manifest['tokens']['total'] * 4,
        target_presentations=manifest['tokens']['target'] * 4, cost=reduction['cost'])
result = dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    capsule_sha256=validation['sha256'], verified_files=len(validation['files']), arms=arms,
    gate_pass=all(arm['gate_pass'] for arm in arms.values()), baseline_counts=terminal['reused_H_counts'],
    new_calls=96, new_fits=2, original_parent_seeds=[0], new_updates=160,
    new_off_calls=0, confirmation_calls=0, full_reservation_seconds=release['full_reservation_seconds'],
    controller_seconds=terminal['reserved_seconds'], worker_seconds=terminal['worker_reserved_seconds'],
    release_utc=release['release_utc'], cost_scope='Nested clocks, not additive.',
    claim='Single-root authored compatible-convention coexistence with rehearsal. Not input-selective cognition, reliable memory, parenting, or H1/H2. No root1/2 repetition under predeclared progression.')
with Path('/tmp/astra_two_habit_analysis_20260912.json').open('x') as output:
    json.dump(result, output, indent=2, sort_keys=True, allow_nan=False)
print(json.dumps(result, indent=2, sort_keys=True))
