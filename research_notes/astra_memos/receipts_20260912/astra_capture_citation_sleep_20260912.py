import datetime
import json
from pathlib import Path

from organism_v6 import citation_sleep_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free, write_new

root = Path.home() / 'astra_diagnostics/astra_citation_sleep_20260912_attempt1'
prep = Path.home() / 'astra_diagnostics/astra_citation_sleep_preparation_20260912_attempt1'
logs = root.with_name(root.name + '_launch')
launch = diagnostic.read(logs / 'launch.json')
assert not Path(f"/proc/{launch['pid']}").exists()
stored = diagnostic.read(root / 'COMPLETED.json')
diagnostic.load_preparation(prep, native=True)
report = diagnostic.analyze(root, prep)
assert {key: stored[key] for key in report} == json.loads(json.dumps(report, allow_nan=False))
assert set(stored) - set(report) == {'elapsed_seconds', 'stage_seconds'}
assert 0 < stored['elapsed_seconds'] < 2700
assert all(0 < value < 900 for value in stored['stage_seconds'].values())
gpu, xml = check_free('1')
write_new(logs / 'MAIN_TERMINAL_AUDIT.json', dict(
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='NATIVE_CITATION_SLEEP_REPLAY_AND_RELEASE_PASS',
    report_sha256=diagnostic.digest(root / 'COMPLETED.json'),
    preparation_sha256=launch['preparation_sha256'],
    source_model_and_actual_adapters_verified=True, native_reduction_equal=True,
    controller_absent=True, cleanup_count=5, gpu=gpu, xml=xml, released=True))
print(json.dumps(dict(status='NATIVE_CITATION_SLEEP_REPLAY_AND_RELEASE_PASS',
    report_sha256=diagnostic.digest(root / 'COMPLETED.json'),
    elapsed_seconds=stored['elapsed_seconds'], stage_seconds=stored['stage_seconds'],
    reads={key: {field: value[field] for field in ['counts', 'actual_prompt_tokens', 'actual_output_tokens']}
           for key, value in stored['reads'].items()}, fits=stored['fits'],
    gain_vs_shared_off=stored['gain_vs_shared_off'], full_minus_syntax=stored['full_minus_syntax']),
    sort_keys=True, allow_nan=False))
