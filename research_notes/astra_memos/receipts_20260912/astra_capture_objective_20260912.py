import datetime
import json
import math
from pathlib import Path

from gpu import astra_semantic_objective_probe as probe
from gpu.astra_mini_sudoku_diagnostic import check_free

root = Path.home() / 'astra_diagnostics/astra_semantic_objective_20260912_attempt1'
assert (root / 'COMPLETED.json').is_file() and not (root / 'FAILED.json').exists()
assert not Path('/proc/120373').exists()
out, prepared, rows, tokenizer = probe.verify_prepared(root)
report = probe.reduce(out, prepared, rows, tokenizer)
stored = probe.read(root / 'report.json')
assert math.isfinite(stored['elapsed_seconds']) and 0 < stored['elapsed_seconds'] < 1800
report.update(prepared_sha256=probe.file_hash(root / 'PREPARED.json'), elapsed_seconds=stored['elapsed_seconds'])
assert report == stored
assert probe.file_hash(root / 'report.json') == probe.read(root / 'COMPLETED.json')['report_sha256']
cleanups = list(root.glob('*.cleanup.json'))
assert len(cleanups) == 5
for path in cleanups:
    cleanup = probe.read(path)
    assert cleanup['owned_group_empty'] and cleanup['gpu_processes_absent'] and cleanup['cleanup_error'] is None
gpu, xml = check_free('0')
probe.write(root, 'MAIN_TERMINAL_AUDIT.json', dict(
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='NATIVE_OBJECTIVE_REPLAY_AND_RELEASE_PASS', native_reduction_equal=True,
    elapsed_scope='Recorded controller elapsed retained and range-checked, not recomputed',
    controller_absent=True, cleanup_count=5, report_sha256=probe.file_hash(root / 'report.json'),
    gpu=gpu, xml=xml, released=True,
    adapter_trees_native_verified={arm: fitted['adapter_sha256'] for arm, fitted in report['fits'].items()}))
print(json.dumps(dict(status='NATIVE_OBJECTIVE_REPLAY_AND_RELEASE_PASS',
    states={state: dict(n=data['n'], correct=data['correct'], valid=data['valid'], action_counts=data['action_counts'])
            for state,data in report['states'].items()}, report_sha256=probe.file_hash(root / 'report.json'),
    elapsed_seconds=report['elapsed_seconds'])))
