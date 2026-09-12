import datetime
import json
import math
from pathlib import Path

from organism_v6 import constraint_check_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free, write_new

reports = []
for seed, device in ((7101, '1'), (7102, '2'), (7103, '3')):
    root = Path.home() / f'astra_diagnostics/astra_constraint_v2_20260912_seed{seed}_attempt1'
    prep = Path.home() / f'astra_diagnostics/astra_constraint_v2_preparation_20260912_seed{seed}_attempt1'
    launch = diagnostic.read(root.with_name(root.name + '_launch') / 'launch.json')
    assert (root / 'COMPLETED.json').is_file() and not (root / 'FAILED.json').exists()
    assert not Path(f"/proc/{launch['pid']}").exists()
    diagnostic.validate_preparation(prep)
    report = diagnostic.analyze_pair(root, prep, generation_seed=seed)
    stored = diagnostic.read(root / 'COMPLETED.json')
    assert math.isfinite(stored['elapsed_seconds']) and 0 < stored['elapsed_seconds'] < 1800
    report['elapsed_seconds'] = stored['elapsed_seconds']
    assert report == stored
    cleanups = list(root.glob('*.cleanup.json'))
    assert len(cleanups) == 2
    for path in cleanups:
        cleanup = diagnostic.read(path)
        assert cleanup['owned_group_empty'] and cleanup['gpu_processes_absent'] and cleanup['cleanup_error'] is None
    gpu, xml = check_free(device)
    write_new(root / 'MAIN_TERMINAL_AUDIT.json', dict(
        observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='NATIVE_V2_PRODUCTION_REPLAY_AND_RELEASE_PASS', native_reduction_equal=True,
        elapsed_scope='Original controller elapsed retained and range-checked, not recomputed by reduction',
        controller_absent=True, cleanup_count=2, report_sha256=diagnostic.formation._hash(root / 'COMPLETED.json'),
        gpu=gpu, xml=xml, released=True, generation_seed=seed))
    reports.append(dict(seed=seed, elapsed_seconds=stored['elapsed_seconds'],
        report_sha256=diagnostic.formation._hash(root / 'COMPLETED.json'),
        arms={arm: {key: value for key, value in data.items() if key != 'cases'}
              for arm, data in report['arms'].items()}, process_minus_format=report['process_minus_format']))
print(json.dumps(dict(status='ALL_THREE_NATIVE_PAIRS_REPLAY_AND_RELEASE_PASS',
    seed_role=diagnostic.SEED_ROLE, pairs=reports), sort_keys=True))
