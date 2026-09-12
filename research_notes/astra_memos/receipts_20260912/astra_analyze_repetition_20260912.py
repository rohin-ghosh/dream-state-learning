from collections import Counter
import hashlib
import json
from pathlib import Path

capsule = Path('/tmp/astra_fundamental_repetition_terminal_20260912.tgz')
validation = json.loads(Path(str(capsule) + '.validation.json').read_text())
assert hashlib.sha256(capsule.read_bytes()).hexdigest() == validation['sha256']
extracted = Path('/tmp/astra_repetition_terminal_20260912')
for name, expected in validation['files'].items():
    assert hashlib.sha256((extracted / name).read_bytes()).hexdigest() == expected
root = extracted / 'astra_diagnostics/astra_fundamental_repetition_20260912_attempt1'
read = lambda path: json.loads(path.read_text())
release = read(root / 'readout_main_release.json')
fit_release = read(root / 'fit_main_release.json')
cells, events = {}, []
for cell, released in release['cells'].items():
    target = root / 'cells' / cell
    fit = read(target / 'fit' / 'result.json')
    result = read(target / 'readout' / 'reduction.json')
    launch = read(target / 'readout' / 'launch' / 'launch.json')
    assert result['complete'] and result['native_token_text_audit'] is True
    assert released['full_release'] and fit_release['cells'][cell]['full_release']
    assert result['counts'] == released['counts'] and fit['manifest']['steps'] == 80
    cells[cell] = dict(counts=result['counts'], memory_answers=dict(Counter(
        row['raw_text'] for row in result['rows'] if row['kind'] == 'memory_recall')),
        fit_seconds=fit['supervised']['reserved_seconds'], readout_seconds=result['reserved_seconds'],
        cost=result['cost'], input_tokens_seen=fit['manifest']['train_tokens_seen'],
        target_tokens_seen=4 * fit['manifest']['tokens']['target'],
        full_readout_reservation_seconds=released['full_reservation_seconds'])
    events.extend([
        dict(event_id=f'fundamental:repetition:seed0:{cell}:readout_launch', event_type='launch',
             run_id=root.name, phase='readout', **launch),
        dict(event_id=f'fundamental:repetition:seed0:{cell}:terminal', event_type='terminal',
             run_id=root.name, cell=cell, status='FIT_AND_READOUT_COMPLETE_MAIN_RELEASED',
             release_utc=released['release_utc'], source_commit='ed3aac9f888935a40e3a2f8f4e0e1953e17f2ea9',
             capsule_sha256=validation['sha256'], **cells[cell])])
supervised = sum(cell['fit_seconds'] + cell['readout_seconds'] for cell in cells.values())
analysis = dict(cells=cells, readout_calls=192, new_off_calls=0, confirmation_calls=0,
    supervised_seconds=supervised, supervised_A40_minutes=supervised / 60,
    cumulative_with_SEQ098_100_seconds=1510.1359360829883 + supervised,
    cumulative_with_SEQ098_100_A40_minutes=(1510.1359360829883 + supervised) / 60,
    claims='Seed0 dev repetition/context sentinel; not parenting, conditional cognition, final confirmation or identified cause of memory failure',
    capsule_sha256=validation['sha256'])
with Path('/tmp/astra_repetition_main_analysis_20260912.json').open('x') as output:
    json.dump(analysis, output, indent=2, sort_keys=True)
with Path('/tmp/astra_repetition_run_events_20260912.jsonl').open('x') as output:
    output.write(''.join(json.dumps(event, sort_keys=True) + '\n' for event in events))
print(json.dumps(analysis, indent=2, sort_keys=True))
