import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

import astra_fundamental_replication_20260912 as replication
from gpu.astra_mini_sudoku_diagnostic import check_free

base = replication.base
bundle = Path.home() / 'astra_diagnostics/astra_fundamental_replications_20260912_attempt1'
stage = sys.argv[1]
assert stage in ('fit', 'readout')
assert base.digest(replication.__file__) == 'fcd3dd3870a8b118df7b55eb987b860a90903b81ddaf5f17871f3ca98c2419e0'
cpu = Path('/tmp/astra_fundamental_replication_native_cpu_20260912.log')
assert 'Ran 20 tests' in cpu.read_text() and cpu.read_text().rstrip().endswith('OK')
plans = {seed: replication.verify(bundle / ('seed' + str(seed))) for seed in (1, 2)}
for seed, plan in plans.items():
    assert plan['lease_end'] - datetime.datetime.now(datetime.timezone.utc).timestamp() > 21600 + 1800
    for arm in ('teach', 'control'):
        root = bundle / ('seed' + str(seed))
        assert not (root / ('launch_' + stage + '_' + arm)).exists()
        if stage == 'fit':
            assert not (root / ('fit_' + arm)).exists()
        else:
            replication.verify_fit(root, arm, seal=False)
            assert not (root / 'readouts' / arm / 'run').exists()
for seed, plan in plans.items():
    root = bundle / ('seed' + str(seed))
    for arm in ('teach', 'control'):
        device = replication.device_for(plan, arm)
        gpu, xml = check_free(device)
        logs = root / ('launch_' + stage + '_' + arm)
        logs.mkdir()
        with (logs / 'gpu.xml').open('x') as output:
            output.write(xml)
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', V6_MODEL=plan['model'],
            PYTHONPATH=str(base.REPO), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
        command = [sys.executable, '-B', str(Path(replication.__file__).resolve()),
            'launch-' + stage, '--root', str(root), '--arm', arm, '--allow-gpu']
        with (logs / 'controller.log').open('xb') as output:
            process = subprocess.Popen(command, cwd=base.REPO, env=environment,
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        receipt = dict(status='LAUNCHED_NOT_COMPLETED', node=3, device=device,
            seed=seed, arm=arm, stage=stage, pid=process.pid,
            started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            source=str(base.REPO), root=str(root), command=command,
            plan_sha256=base.digest(root / 'plan.json'), gpu=gpu,
            launcher_sha256=base.digest(__file__), replication_script_sha256=base.digest(replication.__file__),
            native_cpu_sha256=base.digest(cpu), continuous_reservation=True)
        base.write_json(logs / 'launch.json', receipt)
        print(json.dumps(receipt, sort_keys=True), flush=True)
