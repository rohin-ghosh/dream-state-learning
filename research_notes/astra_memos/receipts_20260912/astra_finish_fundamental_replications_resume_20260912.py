from collections import Counter
import datetime
import json
from pathlib import Path

from organism_v6 import fundamental_teaching_readout as readout
from gpu.astra_mini_sudoku_diagnostic import check_free

base = readout.base
bundle = Path.home() / 'astra_diagnostics/astra_fundamental_replications_20260912_attempt1'
assert not (bundle / 'readout_main_release.json').exists()
for seed in (1, 2):
    for arm in ('teach', 'control'):
        root = bundle / ('seed' + str(seed))
        launched = base.read(root / ('launch_readout_' + arm) / 'launch.json')
        assert not (Path('/proc') / str(launched['pid'])).exists()
        reduction = root / 'readouts' / arm / 'reduction.json'
        if seed == 1 and arm == 'teach':
            assert base.digest(reduction) == 'c216db3b54fa91777b56da99a5cca53b7226f90378a49a19111c8f4bf491e9a3'
        else:
            assert not reduction.exists()
cells = {}
for seed in (1, 2):
    root = bundle / ('seed' + str(seed))
    prepared = base.read(root / 'readout_preparation.json')
    for arm in ('teach', 'control'):
        launched = base.read(root / ('launch_readout_' + arm) / 'launch.json')
        selected = root / 'readouts' / arm
        if seed == 1 and arm == 'teach':
            plan, cases = readout.verify(selected)
            result = base.read(selected / 'reduction.json')
            assert result['complete'] and result['native_token_text_audit']
            assert base.read(selected / 'run' / 'worker' / 'supervision.json')['ok']
            capture = selected / 'run' / 'data'
            assert base.read(capture / 'manifest.json')['files'] == base.tree_hashes(capture, ('manifest.json',))
            assert result['capture_sha256'] == base.digest(capture / 'manifest.json')
        else:
            result = readout.reduce(selected)
        assert result['plan_sha256'] == prepared['cells'][arm]['plan_sha256']
        verified = base.read(root / ('fit_' + arm) / 'verified.json')
        assert result['adapter_files'] == verified['adapter_files'] == base.tree_hashes(verified['adapter'])
        gpu, xml = check_free(launched['device'])
        with (selected / 'main_release.xml').open('x') as output:
            output.write(xml)
        observed = datetime.datetime.now(datetime.timezone.utc)
        memory = [row['raw_text'] for row in result['rows'] if row['kind'] == 'memory_recall']
        row = dict(seed=seed, arm=arm, counts=result['counts'], cost=result['cost'],
            supervised_seconds=result['reserved_seconds'], memory_answers=dict(Counter(memory)),
            device=launched['device'], controller_pid=launched['pid'], full_release=True, gpu=gpu,
            release_utc=observed.isoformat(),
            full_reservation_seconds=(observed-datetime.datetime.fromisoformat(launched['started_utc'])).total_seconds(),
            reduction_sha256=base.digest(selected / 'reduction.json'))
        cells[str(seed) + '_' + arm] = row
        print(json.dumps(row, sort_keys=True), flush=True)
totals = {key: sum(row['cost']['readout'][key] for row in cells.values())
    for key in ('requests','native_input_tokens','native_output_tokens','generation_seconds','output_token_ceiling')}
totals['supervised_readout_seconds'] = sum(row['supervised_seconds'] for row in cells.values())
totals['full_readout_reservation_seconds'] = sum(row['full_reservation_seconds'] for row in cells.values())
base.write_json(bundle / 'readout_main_release.json', dict(cells=cells, totals=totals,
    status='FOUR_REPLICATION_DEV_READOUTS_COMPLETE', confirmation_requests=0, new_off_requests=0,
    off_root=str(Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1/readouts/OFF'),
    source=str(base.REPO), limits=readout.CLAIM_LIMITS))
print(json.dumps(dict(totals=totals), sort_keys=True), flush=True)
