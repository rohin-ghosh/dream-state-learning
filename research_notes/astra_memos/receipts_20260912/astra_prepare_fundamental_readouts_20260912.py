import datetime
import json
from pathlib import Path

from organism_v6 import fundamental_teaching_readout as readout
from gpu.astra_mini_sudoku_diagnostic import check_free

base = readout.base
root = Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1'
plan = base.read(root / 'plan.json')
fits = {}
for arm, device in (('teach', '0'), ('control', '1')):
    result = base.read(root / ('fit_' + arm) / 'result.json')
    launch = base.read(root / ('launch_' + arm) / 'launch.json')
    assert result['status'] == 'FIT_COMPLETE_PENDING_PAIRED_READOUT'
    assert result['supervised']['ok'] and result['supervised']['reservation_release_verified']
    assert base.tree_hashes(result['adapter']) == result['adapter_files']
    assert result['manifest']['config'] == plan['config'] and result['manifest']['steps'] == 80
    assert not (Path('/proc') / str(launch['pid'])).exists()
    gpu, xml = check_free(device)
    with (root / ('fit_' + arm + '_main_release.xml')).open('x') as output:
        output.write(xml)
    fits[arm] = dict(adapter=result['adapter'], adapter_files=result['adapter_files'],
        controller_pid=launch['pid'], full_release=True, gpu=gpu,
        final_loss=result['manifest']['final_loss'], supervised_seconds=result['supervised']['reserved_seconds'])
base.write_json(root / 'fit_main_release.json', dict(fits=fits,
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    full_device_process_queue_checks=True, next_readouts_not_yet_launched=True))
parent = root / 'readouts'
parent.mkdir()
prepared = {}
for cell, device in (('OFF', '2'), ('teach', '0'), ('control', '1')):
    adapter = None if cell == 'OFF' else fits[cell]['adapter']
    actual = readout.prepare(parent / cell, plan['model'], adapter, device, plan['lease_end'])
    assert actual['model_files'] == plan['model_files']
    assert actual['adapter_files'] == ({} if cell == 'OFF' else fits[cell]['adapter_files'])
    assert actual['source_hashes']['fundamental_teaching_corpus.py'] == plan['source_hashes']['fundamental_teaching_corpus.py']
    assert [case['id'] for case in actual['cases']] == plan['eval_dev_ids']
    prepared[cell] = dict(root=str(parent / cell), device=device,
        plan_sha256=base.digest(parent / cell / 'plan.json'), cases=48)
base.write_json(root / 'readout_preparation.json', dict(status='ALL_THREE_NATIVE_READOUTS_PREPARED',
    cells=prepared, fit_source='06c90d1bbd00fd7ab1867bf069944554b84580cf',
    readout_source=str(base.REPO), native_model_calls=0, confirmation_model_calls=0,
    source_and_adapter_link_verified=True))
print(json.dumps(dict(status='ALL_THREE_NATIVE_READOUTS_PREPARED', fits=fits, cells=prepared), sort_keys=True))
