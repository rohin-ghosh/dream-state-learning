"""Receiving CPU/source admission and measured warm-scorer dispatch only."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from research_loop.workers.rohin233_ovx4_recovery_20260918.prepare_renewal import BASE, MODULE, read, ref, write, unit_run
from research_loop.workers.rohin233_ovx4_recovery_20260918.judge_epoch import verified_source


def prepare(payload):
    role=payload['role']
    current=Path(payload['current_root'])
    previous=read(current/('scorer_CONFIG.private.json' if role=='base' else 'CONFIG.private.json'))
    pid=payload['predecessor_pid']
    stat=Path('/proc',str(pid),'stat')
    ticks=stat.read_text().rsplit(')',1)[1].split()[19]
    kind='base' if role=='base' else previous['kind']
    root=BASE/'orch_r233_judge15625_20260918'/payload['identity']
    root.mkdir(mode=0o700,exist_ok=False)
    source=root/'source'
    shutil.copytree(current/'source',source)
    for name,content in payload['files'].items():
        target=source/MODULE.replace('.','/')/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(content)
    manifest={str(path.relative_to(source)):ref(path)['sha256'] for path in source.rglob('*.py')}
    write(root/'SOURCE_MANIFEST.json',manifest)
    config=dict(root=str(root),kind=kind,physical=payload['physical'],predecessor_pid=pid,
        predecessor_start_ticks=ticks,deadline_unix=previous['deadline_unix'],
        lease_boundary_unix=previous['lease_boundary_unix'],source_manifest=ref(root/'SOURCE_MANIFEST.json'),
        checkpoint_root=str(root.parent/'checkpoint'),checkpoint_complete_sha256=payload['complete_sha256'],
        checkpoint_adapter_sha256=payload['adapter_sha256'],checkpoint_config_sha256=payload['config_sha256'],
        reference_panels=ref(root.parent/'REFERENCE_PANELS.private.json'),
        socket='/tmp/r233-judge-'+payload['identity']+'.sock')
    verified_source(config['checkpoint_root'],payload['complete_sha256'],payload['adapter_sha256'],payload['config_sha256'])
    if kind=='p3':
        prior=read(previous['prior_config']['path'])
        args=prior['arguments']
        config.update(old_scalar=ref(args['judge_config']),game_manifest=ref(args['game_manifest']),
            encoder_manifest=ref(args['encoder_manifest']),pixel_config=ref(args['pixel_config']),
            relevance_threshold=read(args['relevance_config'])['threshold'],
            endpoint=previous['socket'],states={'p3':str(current/'session/SESSION_STATE.private.json')},
            outputs={'p3':str(current/'session')})
    else:
        prior=previous if kind=='base' else read(previous['prior_config']['path'])
        original=Path(prior['original_root'] if kind=='base' else prior['service_root'])
        assets=current/'scorer/assets' if kind=='base' else original/'assets'
        rule=read(assets/'RULE.json')
        config.update(old_scalar=ref(current/('scorer/scalar_runtime.json' if kind=='base' else 'scalar_runtime.json')),
            game_manifest=ref(assets/'GAME_MANIFEST.json'),encoder_manifest=ref(assets/'embedding_snapshot.json'),
            pixel_config=ref(assets/'pixel_config.json'),old_panel_scores=ref(assets/'PANEL_SCORES.private.json'),
            relevance_threshold=rule['relevance_threshold'])
        if kind=='base':
            config.update(endpoint=str(current/'scorer/base.sock'),transition=ref(current/'TRANSITION.private.json'),
                states={'base':str(original/'scorer/SESSION_STATE.private.json')},outputs={'base':str(original/'scorer')})
        else:
            registry=read(prior['registry']['path'])
            outputs={item['session_id']:str(original/'sessions'/item['session_id']) for item in registry['rows']}
            config.update(endpoint=str(current/'sockets/native.sock'),outputs=outputs,
                states={identifier:str(Path(output)/'SESSION_STATE.private.json') for identifier,output in outputs.items()})
    write(root/'CONFIG.private.json',config)
    environment=dict(os.environ,PYTHONPATH=str(source),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([str(BASE/'v2/venv/bin/python'),'-B','-c',
        'import '+MODULE+'.judge_service'],cwd=source,env=environment,check=True,capture_output=True,timeout=90)
    assert stat.read_text().rsplit(')',1)[1].split()[19]==ticks
    unit=unit_run(root,source,payload['identity'],config['deadline_unix'],MODULE+'.judge_service',root/'CONFIG.private.json',payload['physical'])
    receipt=dict(unix=time.time(),role=role,physical=payload['physical'],unit=unit,
        deadline_unix=config['deadline_unix'],source_manifest_sha256=config['source_manifest']['sha256'],
        status='WARM_DISPATCHED_NOT_ADOPTED',predecessor_pid=pid,CPU_import_pass=True,native_signals=[])
    write(root/'DISPATCHED.json',receipt)
    return receipt
