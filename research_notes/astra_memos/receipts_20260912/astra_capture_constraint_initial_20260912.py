import datetime
import json
from pathlib import Path

from organism_v6 import constraint_check_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free, write_new

root = Path.home() / 'astra_diagnostics/astra_constraint_check_20260912_attempt1'
prep = Path.home() / 'astra_diagnostics/astra_constraint_check_preparation_20260912_attempt1'
assert (root / 'COMPLETED.json').is_file() and not (root / 'FAILED.json').exists()
assert not Path('/proc/118954').exists()
diagnostic.validate_preparation(prep)
report = diagnostic.analyze_pair(root, prep)
assert report == diagnostic.read(root / 'COMPLETED.json')
cleanups = list(root.glob('*.cleanup.json'))
assert len(cleanups) == 2
for path in cleanups:
    cleanup = diagnostic.read(path)
    assert cleanup['owned_group_empty'] and cleanup['gpu_processes_absent'] and cleanup['cleanup_error'] is None
gpu, xml = check_free('1')
write_new(root / 'MAIN_TERMINAL_AUDIT.json', dict(
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='NATIVE_PRODUCTION_REPLAY_AND_RELEASE_PASS', native_reduction_equal=True,
    controller_absent=True, cleanup_count=2, report_sha256=diagnostic.formation._hash(root / 'COMPLETED.json'),
    gpu=gpu, xml=xml, released=True))
print(json.dumps(dict(status='NATIVE_PRODUCTION_REPLAY_AND_RELEASE_PASS',
    arms={arm: {key: value for key, value in data.items() if key != 'cases'} for arm,data in report['arms'].items()},
    process_minus_format=report['process_minus_format'])))
