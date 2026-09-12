import datetime
import json
from pathlib import Path

from gpu import astra_memory_cumulative_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free, write_new

root = Path.home() / 'astra_diagnostics/astra_cumulative_20260912_attempt1'
launch = diagnostic.read(root.with_name(root.name + '_launch') / 'launch.json')
finished = diagnostic.read(root / 'RUN_FINISHED.json')
assert finished['completed'] and finished['failure'] is None
assert not Path(f"/proc/{launch['pid']}").exists()
digest = launch['manifest_sha256']
report = diagnostic.reduce(root, digest, root / 'report.json')
assert diagnostic.read(root / 'report.json') == report
assert report['cost']['new_fit_steps'] == 12765
gpu, xml = check_free('0')
write_new(root / 'MAIN_TERMINAL_AUDIT.json', dict(
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='NATIVE_CUMULATIVE_REDUCTION_AND_RELEASE_PASS',
    manifest_sha256=digest, report_sha256=diagnostic.file_sha(root / 'report.json'),
    adapter_verification='Actual native A1 and both new adapter trees verified by primary reducer',
    fresh_workers=6, controller_absent=True, gpu=gpu, xml=xml, released=True,
    starting_state=diagnostic.STARTING_STATE))
print(json.dumps(dict(status='NATIVE_CUMULATIVE_REDUCTION_AND_RELEASE_PASS',
    report_sha256=diagnostic.file_sha(root / 'report.json'),
    reserved_gpu_seconds=finished['reserved_gpu_seconds'],
    native_fact_retention_fraction=report['native_fact_retention_fraction'],
    no_update=report['no_update'],
    new_fit_steps=report['cost']['new_fit_steps'],
    native_old_gates=report['native_old_gates'],
    descriptive=report['descriptive']), sort_keys=True, allow_nan=False))
