import datetime
import json
from pathlib import Path
import subprocess

from organism_v6 import fresh_behavior_panel as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free

root = Path.home() / 'astra_diagnostics/astra_fresh_behavior_panel_20260912_attempt2'
read = diagnostic.custody._read
digest = diagnostic.custody._digest
preflight = read(root / 'preflight.json')
assert digest(diagnostic.__file__) == preflight['helper_sha256']
diagnostic.custody.verify_source_snapshot(preflight['source_snapshot'])
report = read(root / 'first_act_report.json')
assert report['reducer_sha256'] == preflight['helper_sha256']
model_inventory = diagnostic.file_hashes(diagnostic.MODEL)
adapters = []
devices = []
for seed in range(3):
    execution = root / f'seed{seed}_execution'
    launch = read(execution / 'launch.json')
    terminal = read(execution / 'result.json')
    assert terminal['status'] == 'BOTH_PAIRS_COMPLETE_PENDING_MAIN_REDUCTION'
    assert not (Path('/proc') / str(launch['pid'])).exists()
    gpu, xml = check_free(str(seed + 1))
    with (root / f'main_release_gpu{seed + 1}.xml').open('x') as output:
        output.write(xml)
    devices.append(dict(seed=seed, device=str(seed + 1), gpu=gpu,
        controller_pid=launch['pid'], controller_seconds=terminal['controller_seconds'],
        started_utc=launch['started_utc'], finished_utc=terminal['finished_utc']))
    for arm in ('useful', 'corrupt'):
        spec = read(root / 'specs' / f'seed{seed}_{arm}.json')
        assert model_inventory == spec['expected_model_hashes']
        assert diagnostic.file_hashes(spec['adapter_path']) == spec['expected_adapter_hashes']
        adapters.append(dict(seed=seed, arm=arm, path=spec['adapter_path'],
            hashes=spec['expected_adapter_hashes']))
release = dict(status='TERMINAL_MAIN_FULL_RELEASE_AND_CURRENT_INPUTS_VERIFIED',
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    devices=devices, actual_adapters=adapters, actual_model=model_inventory,
    report_sha256=digest(root / 'first_act_report.json'),
    reducer_sha256=report['reducer_sha256'], source_snapshot=preflight['source_snapshot'],
    original_reducer_verified=True, fits=0, conditions=12, episode_cells=192,
    model_origin='UNRESOLVED_LOCAL_HASHES_ONLY',
    prior_exposure_warning='Four selected IDs 1900071/72/73/75 have earlier correction-utility readouts; mixed-exposure development only')
diagnostic._write(root / 'main_release.json', release)
archive = Path('/tmp/astra_fresh_behavior_terminal_20260912.tgz')
assert not archive.exists()
subprocess.run(['tar', '-czf', str(archive), '-C', str(root.parent), root.name], check=True)
print(json.dumps(dict(archive=str(archive), sha256=digest(archive),
    release_utc=release['observed_utc'], devices=devices, inputs_verified=True), sort_keys=True))
