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
stored = diagnostic.read(root / 'report.json')
replay_path = Path('/tmp/astra_cumulative_reduction_replay_20260912.json')
assert not replay_path.exists()
replay = diagnostic.reduce(root, launch['manifest_sha256'], replay_path)
normalized = json.loads(json.dumps(replay, allow_nan=False))
assert stored == diagnostic.read(replay_path) == normalized
assert replay != stored
assert all(isinstance(key, int) for key in replay['native_old_summaries']['A1_before']['per_dose'])
assert all(isinstance(key, str) for key in stored['native_old_summaries']['A1_before']['per_dose'])
assert stored['cost']['new_fit_steps'] == 12765
gpu, xml = check_free('0')
write_new(root / 'MAIN_TERMINAL_AUDIT.json', dict(
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='NATIVE_CUMULATIVE_REDUCTION_AND_RELEASE_PASS',
    manifest_sha256=launch['manifest_sha256'], report_sha256=diagnostic.file_sha(root / 'report.json'),
    replay_sha256=diagnostic.file_sha(replay_path),
    capture_repair='Original comparison used integer in-memory dose keys versus JSON string keys; JSON-normalized native replay exactly matches preserved report',
    gpu_experiment_rerun=False, original_report_preserved=True,
    adapter_verification='Actual native A1 and both fitted adapter trees independently verified again by reducer',
    fresh_workers=6, controller_absent=True, gpu=gpu, xml=xml, released=True,
    starting_state=diagnostic.STARTING_STATE))
print(json.dumps(dict(status='NATIVE_CUMULATIVE_REDUCTION_AND_RELEASE_PASS',
    report_sha256=diagnostic.file_sha(root / 'report.json'),
    reserved_gpu_seconds=finished['reserved_gpu_seconds'],
    native_fact_retention_fraction=stored['native_fact_retention_fraction'],
    no_update=stored['no_update'], native_old_gates=stored['native_old_gates'],
    descriptive=stored['descriptive'], new_fit_steps=stored['cost']['new_fit_steps']),
    sort_keys=True, allow_nan=False))
