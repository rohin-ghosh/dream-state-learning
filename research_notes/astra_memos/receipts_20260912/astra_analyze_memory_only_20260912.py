import collections
import datetime
import hashlib
import json
from pathlib import Path


root = Path('/tmp/astra_memory_only_terminal_20260912')
validation = json.loads(Path(str(root) + '.tgz.validation.json').read_text())
assert hashlib.sha256(Path(str(root) + '.tgz').read_bytes()).hexdigest() == validation['sha256']
for name, expected in validation['files'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected
base = root / 'astra_diagnostics/astra_fundamental_memory_only_20260912_attempt1'
plan = json.loads((base / 'plan.json').read_text())
rows = []
for seed in range(3):
    branch = base / f'seed{seed}'
    terminal = json.loads((branch / 'terminal.json').read_text())
    release = json.loads((branch / 'main_release.json').read_text())
    manifest = json.loads((branch / 'adapter/train_manifest.json').read_text())
    assert terminal['status'] == 'COMPLETE' and terminal['release_verified'] and terminal['deadline_met']
    assert release['full_release'] and release['controller_absent']
    assert release['terminal_sha256'] == hashlib.sha256((branch / 'terminal.json').read_bytes()).hexdigest()
    assert manifest['steps'] == 80 and manifest['epochs_run'] == 20 and manifest['nonfinite_batches'] == 0
    panels = {}
    for name, count in (('dev', 48), ('exact', 16)):
        panel = branch / name
        reduction = json.loads((panel / 'reduction.json').read_text())
        assert reduction['complete'] and len(reduction['rows']) == count
        finish_reasons = collections.Counter()
        outputs = []
        for row in reduction['rows']:
            received = json.loads((panel / 'run/data/calls' / (row['call_id'] + '.response.json')).read_text())
            assert received['response']['text'] == row['raw_text']
            finish_reasons[received['response']['finish_reason']] += 1
            outputs.append(row['raw_text'])
        memory = reduction['rows'] if name == 'exact' else [row for row in reduction['rows'] if row['kind'] == 'memory_recall']
        correct = sum(row['raw_text'].strip().lower().removesuffix('.') == row['expected'] for row in memory)
        assert correct == (reduction['counts']['correct'] if name == 'exact' else reduction['counts']['memory']['correct'])
        panels[name] = dict(counts=reduction['counts'], finish_reasons=dict(finish_reasons),
            memory_answers=dict(collections.Counter(row['raw_text'] for row in memory)),
            distinct_outputs=len(set(outputs)), cost=reduction['cost'])
    rows.append(dict(seed=seed, baseline=terminal['result']['baseline_counts'], panels=panels,
        fit_steps=80, epochs=20, full_reservation_seconds=release['full_reservation_seconds'],
        controller_seconds=terminal['reserved_seconds'], worker_seconds=terminal['worker_reserved_seconds'],
        release_utc=release['release_utc']))
result = dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    capsule_sha256=validation['sha256'], verified_files=len(validation['files']), seeds=rows,
    new_fits=3, new_calls=192, new_updates=240, confirmation_calls=0, new_off_calls=0,
    accounting_per_seed=plan['accounting'],
    full_reservation_seconds=sum(row['full_reservation_seconds'] for row in rows),
    controller_seconds=sum(row['controller_seconds'] for row in rows),
    worker_seconds=sum(row['worker_seconds'] for row in rows),
    cost_scope='Nested scopes, never additive; collection delay is in full reservation, not GPU busy time.',
    claim='Authored same-fact memory acquisition with heterogeneous arithmetic-interface retention; no general memory/replay/dose/parenting claim. Exact and dev ask about the same16facts, not32independent facts.')
output = Path('/tmp/astra_memory_only_analysis_20260912.json')
with output.open('x') as target:
    json.dump(result, target, indent=2, sort_keys=True, allow_nan=False)
print(json.dumps(result, indent=2, sort_keys=True))
