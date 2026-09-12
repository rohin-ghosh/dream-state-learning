import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from organism_v6 import fundamental_memory_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free

base = diagnostic.base
seed0 = Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1'
root = Path.home() / 'astra_diagnostics/astra_fundamental_memory_trainprompt_20260912_attempt1'
devices = {'OFF': '4', 'teach': '5', 'control': '6'}
plan = base.read(seed0 / 'plan.json')
assert base.digest(seed0 / 'plan.json') == 'd5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e'
assert plan['lease_end'] - datetime.datetime.now(datetime.timezone.utc).timestamp() > 21600 + 1800
cpu = Path('/tmp/astra_fundamental_memory_native_cpu_20260912.log')
assert 'Ran 61 tests' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
stage = sys.argv[1]
assert stage in ('prepare', 'launch', 'finish')
if stage == 'prepare':
    assert not root.exists()
    root.mkdir()
    cells = {}
    for cell, device in devices.items():
        fit = None if cell == 'OFF' else base.read(seed0 / ('fit_' + cell) / 'result.json')
        adapter = None if fit is None else fit['adapter']
        actual = diagnostic.prepare(root / cell, plan['model'], adapter, device, plan['lease_end'])
        assert actual['model_files'] == plan['model_files']
        assert actual['adapter_files'] == ({} if fit is None else fit['adapter_files'])
        actual_training = base.read(seed0 / ('teach.json' if cell == 'OFF' else cell + '.json'))['corpus']
        memory_training = [row for row in actual_training if row['view'] == 'memory']
        for case, request in zip(actual['cases'], actual['native_inputs']):
            matched = [row for row in memory_training if row['group'] == case['id']]
            assert len(matched) == 1 and matched[0]['spans'][0][0] == request['rendered_prompt']
        cells[cell] = dict(root=str(root / cell), device=device,
            plan_sha256=base.digest(root / cell / 'plan.json'), calls=16)
    base.write_json(root / 'preparation.json', dict(cells=cells, source=str(base.REPO),
        label=diagnostic.LABEL, confirmation_requests=0, model_calls=0,
        actual_training_prompt_bytes_verified=True))
    print(json.dumps(cells, sort_keys=True), flush=True)
elif stage == 'launch':
    prepared = base.read(root / 'preparation.json')
    assert prepared['source'] == str(base.REPO)
    for cell, device in devices.items():
        selected = root / cell
        assert base.digest(selected / 'plan.json') == prepared['cells'][cell]['plan_sha256']
        assert not (selected / 'launch').exists() and not (selected / 'run').exists()
        gpu, xml = check_free(device)
        logs = selected / 'launch'
        logs.mkdir()
        with (logs / 'gpu.xml').open('x') as output:
            output.write(xml)
        command = [sys.executable, '-B', '-m', 'organism_v6.fundamental_memory_diagnostic',
            'run', '--root', str(selected), '--allow-gpu']
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=device, V6_MODEL=plan['model'],
            PYTHONPATH=str(base.REPO), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
        with (logs / 'controller.log').open('xb') as output:
            process = subprocess.Popen(command, cwd=base.REPO, env=environment,
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        receipt = dict(node=3, device=device, cell=cell, pid=process.pid,
            status='LAUNCHED_NOT_COMPLETED', source=str(base.REPO), command=command,
            started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            plan_sha256=prepared['cells'][cell]['plan_sha256'], launcher_sha256=base.digest(__file__),
            gpu=gpu, continuous_reservation=True, label=diagnostic.LABEL)
        base.write_json(logs / 'launch.json', receipt)
        print(json.dumps(receipt, sort_keys=True), flush=True)
else:
    results = {}
    for cell, device in devices.items():
        selected = root / cell
        launched = base.read(selected / 'launch' / 'launch.json')
        assert not (Path('/proc') / str(launched['pid'])).exists()
        assert not (selected / 'reduction.json').exists()
        result = diagnostic.reduce(selected)
        gpu, xml = check_free(device)
        with (selected / 'main_release.xml').open('x') as output:
            output.write(xml)
        results[cell] = dict(counts=result['counts'], cost=result['cost'],
            supervised_seconds=result['reserved_seconds'], gpu=gpu, device=device,
            release_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            controller_pid=launched['pid'], full_release=True,
            reduction_sha256=base.digest(selected / 'reduction.json'))
        print(json.dumps(dict(cell=cell, **results[cell]), sort_keys=True), flush=True)
    base.write_json(root / 'main_release.json', dict(cells=results,
        label=diagnostic.LABEL, status='COMPLETE_IN_SAMPLE_DIAGNOSTIC', confirmation_requests=0))
