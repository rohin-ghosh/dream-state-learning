from collections import Counter
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from organism_v6 import fundamental_teaching_readout as readout
from gpu.astra_mini_sudoku_diagnostic import check_free

base = readout.base
root = Path.home() / 'astra_diagnostics/astra_fundamental_repetition_20260912_attempt1'
plan = base.read(root / 'fit_plan.json')
off_root = Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1/readouts/OFF'
off = base.read(off_root / 'plan.json')
assert plan['source'] == str(base.REPO) and off['source_hashes'] == readout.sources()
assert off['model_files'] == plan['model_files']
stage = sys.argv[1]
assert stage in ('prepare', 'launch', 'finish')
if stage == 'prepare':
    assert not (root / 'readout_preparation.json').exists()
    fits, cells = {}, {}
    for cell, device in plan['devices'].items():
        target = root / 'cells' / cell
        launched = base.read(target / 'launch' / 'launch.json')
        assert not (Path('/proc') / str(launched['pid'])).exists()
        fit = base.read(target / 'fit' / 'result.json')
        assert fit['status'] == 'FIT_COMPLETE_PENDING_READOUT'
        assert fit['supervised']['ok'] and fit['supervised']['reservation_release_verified']
        assert base.tree_hashes(fit['adapter']) == fit['adapter_files']
        assert fit['manifest']['config'] == plan['configs'][cell]
        gpu, xml = check_free(device)
        with (target / 'fit_main_release.xml').open('x') as output:
            output.write(xml)
        fits[cell] = dict(supervised_seconds=fit['supervised']['reserved_seconds'],
            controller_pid=launched['pid'], device=device, gpu=gpu, full_release=True,
            release_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        actual = readout.prepare(target / 'readout', plan['model'], fit['adapter'], device, plan['lease_end'])
        assert actual['adapter_files'] == fit['adapter_files']
        assert actual['cases'] == off['cases'] and actual['requests'] == off['requests']
        assert actual['native_inputs'] == off['native_inputs'] and actual['model_files'] == off['model_files']
        cells[cell] = dict(root=str(target / 'readout'), device=device,
            plan_sha256=base.digest(target / 'readout' / 'plan.json'))
    base.write_json(root / 'fit_main_release.json', dict(cells=fits,
        supervised_seconds=sum(row['supervised_seconds'] for row in fits.values())))
    base.write_json(root / 'readout_preparation.json', dict(cells=cells, source=str(base.REPO),
        off_plan_sha256=base.digest(off_root / 'plan.json'), new_off_requests=0, confirmation_requests=0))
    print(json.dumps(dict(fits=fits, prepared=cells), sort_keys=True), flush=True)
elif stage == 'launch':
    prepared = base.read(root / 'readout_preparation.json')
    for cell, device in plan['devices'].items():
        target = root / 'cells' / cell / 'readout'
        assert base.digest(target / 'plan.json') == prepared['cells'][cell]['plan_sha256']
        assert not (target / 'launch').exists() and not (target / 'run').exists()
        gpu, xml = check_free(device)
        logs = target / 'launch'
        logs.mkdir()
        with (logs / 'gpu.xml').open('x') as output:
            output.write(xml)
        command = [sys.executable, '-B', '-m', 'organism_v6.fundamental_teaching_readout',
            'run', '--root', str(target), '--allow-gpu']
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=device, V6_MODEL=plan['model'],
            PYTHONPATH=str(base.REPO), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
        with (logs / 'controller.log').open('xb') as output:
            process = subprocess.Popen(command, cwd=base.REPO, env=environment, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        receipt = dict(status='LAUNCHED_NOT_COMPLETED', cell=cell, node=3, device=device,
            pid=process.pid, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            source=str(base.REPO), command=command, plan_sha256=base.digest(target / 'plan.json'),
            script_sha256=base.digest(__file__), gpu=gpu, continuous_reservation=True)
        base.write_json(logs / 'launch.json', receipt)
        print(json.dumps(receipt, sort_keys=True), flush=True)
else:
    results = {}
    for cell, device in plan['devices'].items():
        target = root / 'cells' / cell / 'readout'
        launched = base.read(target / 'launch' / 'launch.json')
        assert not (Path('/proc') / str(launched['pid'])).exists()
        assert not (target / 'reduction.json').exists()
        result = readout.reduce(target)
        gpu, xml = check_free(device)
        with (target / 'main_release.xml').open('x') as output:
            output.write(xml)
        observed = datetime.datetime.now(datetime.timezone.utc)
        results[cell] = dict(counts=result['counts'], cost=result['cost'], supervised_seconds=result['reserved_seconds'],
            memory_answers=dict(Counter(row['raw_text'] for row in result['rows'] if row['kind'] == 'memory_recall')),
            device=device, controller_pid=launched['pid'], full_release=True, gpu=gpu,
            release_utc=observed.isoformat(), full_reservation_seconds=(observed-datetime.datetime.fromisoformat(launched['started_utc'])).total_seconds(),
            reduction_sha256=base.digest(target / 'reduction.json'))
        print(json.dumps(dict(cell=cell, **results[cell]), sort_keys=True), flush=True)
    base.write_json(root / 'readout_main_release.json', dict(cells=results,
        status='FOUR_REPETITION_DEV_READOUTS_COMPLETE', confirmation_requests=0, new_off_requests=0))
