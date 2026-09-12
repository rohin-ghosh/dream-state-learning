import csv
import hashlib
import json
from pathlib import Path

archive = Path('/tmp/astra_fundamental_fading_terminal_20260912.tgz')
validation = json.loads(Path(str(archive) + '.validation.json').read_text())
assert hashlib.sha256(archive.read_bytes()).hexdigest() == validation['sha256']
extracted = Path('/tmp/astra_fading_terminal_20260912')
for name, expected in validation['files'].items():
    assert hashlib.sha256((extracted / name).read_bytes()).hexdigest() == expected
root = extracted / 'astra_diagnostics/astra_fundamental_fading_20260912_attempt1/runs'
read = lambda path: json.loads(path.read_text())
plan = read(root / 'plan.json')
baseline = read(Path('/tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1/readouts/teach/reduction.json'))
rates, rows, events = {}, [], []
for rate, device in plan['devices'].items():
    lineage = root / ('rate-' + rate)
    terminal = read(lineage / 'terminal.json')
    release = read(lineage / 'main_release.json')
    assert release['full_release'] and release['terminal_status'] == terminal['status']
    curve = [dict(phase=0, cumulative_new_updates=0, counts=baseline['counts'], inherited_baseline=True)]
    for phase in terminal['phases']:
        stage = lineage / phase['phase']
        result = read(stage / 'readout' / 'reduction.json')
        assert hashlib.sha256((stage / 'readout' / 'reduction.json').read_bytes()).hexdigest() == phase['reduction_sha256']
        assert result['complete'] and result['native_token_text_audit'] is True
        assert len(result['rows']) == 48 and result['counts']['total'] == 48
        actual_plan = read(stage / 'readout' / 'plan.json')
        assert actual_plan['cases'] == plan['cases']
        manifest = read(stage / 'adapter' / 'train_manifest.json')
        fit = read(stage / 'fit-result.json')
        assert manifest['steps'] == fit['steps'] == 16
        if rate == '0':
            assert fit['parameter_state_unchanged'] is True
        phase_index = len(curve)
        assert manifest['warm_start']['cumulative_steps'] == 80 + 16 * phase_index
        curve.append(dict(phase=phase_index, cumulative_new_updates=16 * phase_index,
            counts=result['counts'], inherited_baseline=False,
            parameter_state_unchanged=fit['parameter_state_unchanged'],
            fit_seconds=phase['fit_cost']['reserved_seconds'],
            readout_seconds=result['reserved_seconds'], cost=result['cost'],
            cumulative_training_steps=manifest['warm_start']['cumulative_steps']))
    if terminal['status'] == 'COMPLETE':
        assert len(curve) == 5 and terminal['release_verified'] and terminal['deadline_met']
    rates[rate] = dict(status=terminal['status'], error=terminal['error'], curve=curve,
        controller_seconds=terminal['reserved_seconds'], worker_seconds=terminal['worker_reserved_seconds'],
        full_reservation_seconds=release['full_reservation_seconds'])
    for point in curve:
        rows.append(dict(rate=rate, phase=point['phase'], new_updates=point['cumulative_new_updates'],
            habit=point['counts']['addition']['adherence'], habit_denominator=32,
            correct_action=point['counts']['addition']['correct_action'], action_denominator=32,
            memory=point['counts']['memory']['correct'], memory_denominator=16,
            inherited_baseline=point['inherited_baseline']))
    events.append(dict(event_id='fundamental:fading:seed0:'+rate+':terminal', event_type='terminal',
        run_id=root.parent.name, rate=rate, node=3, device=device, status=terminal['status'],
        release_utc=release['release_utc'], controller_pid=terminal['controller_pid'],
        capsule_sha256=validation['sha256'], controller_seconds=terminal['reserved_seconds'],
        worker_seconds=terminal['worker_reserved_seconds'], full_release=True, curve=curve))
analysis = dict(rates=rates, capsule_sha256=validation['sha256'],
    controller_seconds=sum(row['controller_seconds'] for row in rates.values()),
    worker_seconds=sum(row['worker_seconds'] for row in rates.values()),
    full_reservation_seconds=sum(row['full_reservation_seconds'] for row in rates.values()),
    new_readout_calls=sum(48 * (len(row['curve']) - 1) for row in rates.values()),
    new_off_calls=0, confirmation_calls=0, independent_initial_teaching_seeds=1,
    claim='Four-phase task-only competing-update sentinel, not passive fading or parenting; shared original baseline is counted once',
    cost_scope='Controller includes workers and between-phase CPU; do not sum controller and worker seconds')
with Path('/tmp/astra_fading_main_analysis_20260912.json').open('x') as output:
    json.dump(analysis, output, indent=2, sort_keys=True)
with Path('/tmp/astra_fading_curves_20260912.csv').open('x') as output:
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
with Path('/tmp/astra_fading_run_events_20260912.jsonl').open('x') as output:
    output.write(''.join(json.dumps(event, sort_keys=True) + '\n' for event in events))
print(json.dumps(dict(rows=rows, controller_seconds=analysis['controller_seconds'],
                     worker_seconds=analysis['worker_seconds']), indent=2, sort_keys=True))
