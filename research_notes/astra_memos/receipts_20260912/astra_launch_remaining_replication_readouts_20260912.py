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
assert base.digest(replication.__file__) == 'fcd3dd3870a8b118df7b55eb987b860a90903b81ddaf5f17871f3ca98c2419e0'
for seed, arm in ((1, 'control'), (2, 'teach'), (2, 'control')):
    root = bundle / ('seed' + str(seed))
    plan = replication.sealed_plan(root)
    prepared = base.read(root / 'readout_preparation.json')
    target = root / 'readouts' / arm
    assert base.digest(target / 'plan.json') == prepared['cells'][arm]['plan_sha256']
    logs = root / ('launch_readout_' + arm)
    assert not logs.exists() and not (target / 'run').exists() and not (target / 'launch').exists()
    device = replication.device_for(plan, arm)
    assert plan['lease_end'] - datetime.datetime.now(datetime.timezone.utc).timestamp() > 21600 + 1800
    gpu, xml = check_free(device)
    logs.mkdir()
    with (logs / 'gpu.xml').open('x') as output:
        output.write(xml)
    command = [sys.executable, '-B', str(Path(replication.__file__).resolve()),
        'launch-readout', '--root', str(root), '--arm', arm, '--allow-gpu']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', V6_MODEL=plan['model'],
        PYTHONPATH=str(base.REPO), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
    with (logs / 'controller.log').open('xb') as output:
        process = subprocess.Popen(command, cwd=base.REPO, env=environment,
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status='LAUNCHED_NOT_COMPLETED', node=3, device=device, seed=seed,
        arm=arm, stage='readout', pid=process.pid, command=command, source=str(base.REPO),
        root=str(root), started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        plan_sha256=base.digest(root / 'plan.json'), readout_plan_sha256=base.digest(target / 'plan.json'),
        launcher_sha256=base.digest(__file__), gpu=gpu, continuous_reservation=True,
        earlier_batch_partial=True, seed1_teach_preserved=True)
    base.write_json(logs / 'launch.json', receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
