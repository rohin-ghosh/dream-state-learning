import datetime
import json
from pathlib import Path

from organism_v6 import fundamental_teaching_readout as readout
from gpu.astra_mini_sudoku_diagnostic import check_free

base = readout.base
root = Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1'
prepared = base.read(root / 'readout_preparation.json')
assert prepared['readout_source'] == str(base.REPO)
assert not (root / 'readout_main_release.json').exists()
for cell in ('OFF', 'teach', 'control'):
    selected = root / 'readouts' / cell
    launched = base.read(selected / 'launch' / 'launch.json')
    assert not (Path('/proc') / str(launched['pid'])).exists(), 'controller still present: ' + cell
    assert base.read(selected / 'run' / 'worker' / 'supervision.json')['ok']
    assert not (selected / 'reduction.json').exists(), 'already reduced; inspect before resuming'
results = {}
for cell in ('OFF', 'teach', 'control'):
    selected = root / 'readouts' / cell
    launched = base.read(selected / 'launch' / 'launch.json')
    result = readout.reduce(selected)
    assert result['plan_sha256'] == prepared['cells'][cell]['plan_sha256']
    gpu, xml = check_free(launched['device'])
    with (selected / 'main_release.xml').open('x') as stream:
        stream.write(xml)
    observed = datetime.datetime.now(datetime.timezone.utc)
    reservation = (observed - datetime.datetime.fromisoformat(launched['started_utc'])).total_seconds()
    results[cell] = dict(counts=result['counts'], cost=result['cost'],
        supervised_seconds=result['reserved_seconds'], full_reservation_seconds=reservation,
        release_utc=observed.isoformat(), gpu=gpu, controller_pid=launched['pid'],
        device=launched['device'], full_release=True,
        reduction_sha256=base.digest(selected / 'reduction.json'))
    print(json.dumps(dict(cell=cell, **results[cell]), sort_keys=True), flush=True)
assert len({base.value_hash(base.read(root / 'readouts' / cell / 'plan.json')['model_files'])
    for cell in results}) == 1
fits = base.read(root / 'fit_main_release.json')
for cell in ('teach', 'control'):
    current = base.tree_hashes(fits['fits'][cell]['adapter'])
    assert current == fits['fits'][cell]['adapter_files']
    assert current == base.read(root / 'readouts' / cell / 'plan.json')['adapter_files']
total = dict(requests=0, native_input_tokens=0, native_output_tokens=0, generation_seconds=0.0,
    output_token_ceiling=0, supervised_readout_seconds=0.0, full_readout_reservation_seconds=0.0)
for result in results.values():
    for key in ('requests', 'native_input_tokens', 'native_output_tokens', 'generation_seconds', 'output_token_ceiling'):
        total[key] += result['cost']['readout'][key]
    total['supervised_readout_seconds'] += result['supervised_seconds']
    total['full_readout_reservation_seconds'] += result['full_reservation_seconds']
base.write_json(root / 'readout_main_release.json', dict(status='THREE_FIXED_DEV_READOUTS_COMPLETE',
    cells=results, totals=total, confirmation_requests=0, fit_adapter_hashes_rechecked=True,
    source=str(base.REPO), model_origin='UNRESOLVED_LOCAL_HASHES_ONLY',
    limits=readout.CLAIM_LIMITS))
print(json.dumps(dict(status='THREE_FIXED_DEV_READOUTS_COMPLETE', totals=total), sort_keys=True))
