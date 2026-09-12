import collections
import datetime
import hashlib
import json
from pathlib import Path


root = Path('/tmp/astra_plasticity_replications_terminal_20260912')
validation = json.loads(Path(str(root) + '.tgz.validation.json').read_text())
assert hashlib.sha256(Path(str(root) + '.tgz').read_bytes()).hexdigest() == validation['sha256']
for name, expected in validation['files'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
base = root / 'astra_diagnostics/astra_fundamental_plasticity_replications_20260912_attempt1'
plan = json.loads((base / 'plan.json').read_text())
rows = []
for branch in sorted(base.glob('seed*-rate-*')):
    reduction = json.loads((branch / 'readout/reduction.json').read_text())
    terminal = json.loads((branch / 'terminal.json').read_text())
    release = json.loads((branch / 'main_release.json').read_text())
    fit = json.loads((branch / 'fit-result.json').read_text())
    assert terminal['status'] == 'COMPLETE' and terminal['release_verified'] and terminal['deadline_met']
    assert release['full_release'] and release['controller_absent']
    assert release['terminal_sha256'] == hashlib.sha256((branch / 'terminal.json').read_bytes()).hexdigest()
    assert terminal['result']['reduction_sha256'] == hashlib.sha256((branch / 'readout/reduction.json').read_bytes()).hexdigest()
    assert fit['steps'] == 16 and reduction['complete'] and len(reduction['rows']) == 48
    addition = [item for item in reduction['rows'] if item['kind'] == 'addition']
    memory = [item for item in reduction['rows'] if item['kind'] == 'memory_recall']
    assert len(addition) == 32 and len(memory) == 16
    exact_act = sum(item['raw_text'].strip() == 'ACT: ' + str(item['expected']) for item in addition)
    memory_correct = sum(item['raw_text'].strip().lower() == item['expected'] for item in memory)
    assert memory_correct == reduction['counts']['memory']['correct']
    rate = branch.name.split('-rate-')[1]
    assert fit['parameter_state_unchanged'] == (rate == '0')
    rows.append(dict(branch=branch.name, counts=reduction['counts'], exact_correct_act_only=exact_act,
        memory_answers=dict(collections.Counter(item['raw_text'] for item in memory)),
        parameter_state_unchanged=fit['parameter_state_unchanged'], new_updates=16,
        optimizer_seed=plan['optimizer_seed'], full_reservation_seconds=release['full_reservation_seconds'],
        controller_seconds=terminal['reserved_seconds'], worker_seconds=terminal['worker_reserved_seconds'],
        release_utc=release['release_utc']))
result = dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    capsule_sha256=validation['sha256'], verified_files=len(validation['files']),
    plan_sha256=hashlib.sha256((base / 'plan.json').read_bytes()).hexdigest(), branches=rows,
    new_calls=288, new_fits=6, new_original_parent_seeds=[1, 2],
    continuation_optimizer_seeds=[0], confirmation_calls=0, new_off_calls=0,
    full_reservation_seconds=sum(item['full_reservation_seconds'] for item in rows),
    controller_seconds=sum(item['controller_seconds'] for item in rows),
    worker_seconds=sum(item['worker_seconds'] for item in rows),
    cost_scope='Nested clocks, never additive. Prior seed0 phase1 from SEQ102 is inherited.',
    claim='Competing-objective habit revisability across three initial teaching seeds with inherited SEQ102; not passive fading, optimal rate, child sleep, or general G3/H1/H2.')
output = Path('/tmp/astra_plasticity_replications_analysis_20260912.json')
with output.open('x') as target:
    json.dump(result, target, indent=2, sort_keys=True, allow_nan=False)
print(json.dumps(result, indent=2, sort_keys=True))
