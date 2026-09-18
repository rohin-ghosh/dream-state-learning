"""Stage a real saved-score handoff; no native or pair device controls."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from research_loop.workers.rohin233_ovx4_recovery_20260918.prepare_renewal import unit_run, ref, write, MODULE


def prepare(payload):
    prior_root=Path('/localhome/local-rohing/orch_r233_ovx4_recovery_20260918/attempt3/base')
    prior=json.loads((prior_root/'EPOCH.json').read_bytes())
    root=Path('/localhome/local-rohing/orch_r233_base_lease_20260918')
    root.mkdir(mode=0o700,exist_ok=False)
    shutil.copytree(prior['source_root'],root/'source')
    for relative,content in payload['files'].items():
        path=root/'source'/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content)
    (root/'scorer').mkdir()
    shutil.copytree((prior_root/'scorer/assets').resolve(),root/'scorer/assets',symlinks=False)
    write(root/'SOURCE_MANIFEST.json',{str(path.relative_to(root/'source')):ref(path)['sha256'] for path in (root/'source').rglob('*.py')})
    config=dict(prior,root=str(root),source_root=str(root/'source'),epoch='R233_LEASE_FROZEN_BASE_5',
        player_physical=3,scorer_physical=2,deadline_unix=1790791170,lease_boundary_unix=1790812800,
        total_opportunities=1000000)
    environment=dict(os.environ,PYTHONPATH=str(root/'source'),CUDA_VISIBLE_DEVICES='')
    subprocess.run(['/localhome/local-rohing/v2/venv/bin/python','-B','-c',
        'import research_loop.workers.rohin233_ovx4_recovery_20260918.base_lease; import research_loop.workers.rohin233_ovx4_recovery_20260918.base_boundary'],
        cwd=root/'source',env=environment,check=True,capture_output=True)
    units=[]
    for mode,physical in [('player',3),('scorer',2)]:
        path=root/(mode+'_CONFIG.private.json')
        write(path,dict(config,mode=mode))
        units.append(unit_run(root,root/'source','base-'+mode,config['deadline_unix'],MODULE+'.base_lease',path,physical))
    end=time.time()+45
    while not (root/'MODEL_WARM.json').exists():
        assert time.time()<end,'actual_base_model_warm_required'
        time.sleep(.1)
    boundary=dict(root=str(root),original_root=prior['original_root'],endpoint=str(prior_root/'scorer/base.sock'),
        player_pid=401005,scorer_pid=400997,deadline_unix=config['deadline_unix'])
    for role in ('player','scorer'):
        boundary[role+'_start_ticks']=Path('/proc',str(boundary[role+'_pid']),'stat').read_text().rsplit(')',1)[1].split()[19]
    write(root/'BOUNDARY_CONFIG.private.json',boundary)
    units.append(unit_run(root,root/'source','base-boundary',config['deadline_unix'],MODULE+'.base_boundary',root/'BOUNDARY_CONFIG.private.json'))
    result=dict(unix=time.time(),units=units,deadline_unix=config['deadline_unix'],model_warm=json.loads((root/'MODEL_WARM.json').read_bytes()),
        status='ACTUAL_MODEL_WARM_AWAITING_REAL_SCORE_BOUNDARY',native_signals=[],history_reset=False,scoring_replays=0)
    write(root/'DISPATCHED.json',result)
    return result
