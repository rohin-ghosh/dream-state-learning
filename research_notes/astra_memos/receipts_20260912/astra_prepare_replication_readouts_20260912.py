import datetime
import json
from pathlib import Path

import astra_fundamental_replication_20260912 as replication
from gpu.astra_mini_sudoku_diagnostic import check_free

base = replication.base
bundle = Path.home() / 'astra_diagnostics/astra_fundamental_replications_20260912_attempt1'
assert not (bundle / 'fit_main_release.json').exists()
results = {}
for seed in (1, 2):
    root = bundle / ('seed' + str(seed))
    for arm in ('teach', 'control'):
        launched = base.read(root / ('launch_fit_' + arm) / 'launch.json')
        assert not (Path('/proc') / str(launched['pid'])).exists()
        verified = base.read(root / ('fit_' + arm) / 'verified.json')
        assert verified['status'] == 'FIT_COMPLETE_PENDING_PAIRED_READOUT'
        assert base.tree_hashes(verified['adapter']) == verified['adapter_files']
        supervision = base.read(root / ('fit_' + arm) / 'worker' / 'supervision.json')
        replication.successful_supervision(supervision, launched['device'])
        gpu, xml = check_free(launched['device'])
        with (root / ('fit_' + arm + '_main_release.xml')).open('x') as output:
            output.write(xml)
        results[str(seed) + '_' + arm] = dict(device=launched['device'], controller_pid=launched['pid'],
            launch=launched, supervised_seconds=supervision['reserved_seconds'], gpu=gpu, full_release=True,
            release_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            final_loss=base.read(Path(verified['adapter']) / 'train_manifest.json')['final_loss'])
base.write_json(bundle / 'fit_main_release.json', dict(cells=results,
    supervised_seconds=sum(row['supervised_seconds'] for row in results.values())))
print(json.dumps(dict(fit_release=results), sort_keys=True), flush=True)
for seed in (1, 2):
    root = bundle / ('seed' + str(seed))
    result = replication.prepare_readouts(root)
    print(json.dumps(dict(seed=seed, preparation=result), sort_keys=True), flush=True)
