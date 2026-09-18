"""Retry a failed listener from its exact drained snapshot, no history mutation."""

from pathlib import Path
import os
import shutil
import subprocess
import time

from research_loop.workers.rohin233_ovx4_recovery_20260918.prepare_renewal import BASE, MODULE, read, ref, write, unit_run


def retry(previous_root,identity,files):
    previous=Path(previous_root)
    old=read(previous/'CONFIG.private.json')
    loaded=read(previous/'LOADED.json')
    assert not Path('/proc',str(old['predecessor_pid'])).exists()
    assert not Path('/proc',str(loaded['pid'])).exists()
    assert not list((previous/'epochs').glob('*/ACT_*.json')),'cannot_retry_over_scored_epoch'
    handoff=read(previous/'HANDOFF.json')
    for identifier,state in handoff['sessions'].items():
        assert ref(old['states'][identifier])['sha256']==state['sha256'],'exact_unchanged_drained_state'
    root=previous.parent/identity
    root.mkdir(mode=0o700)
    shutil.copytree(previous/'source',root/'source')
    for name,content in files.items():
        (root/'source'/MODULE.replace('.','/')/name).write_text(content)
    write(root/'SOURCE_MANIFEST.json',{str(path.relative_to(root/'source')):ref(path)['sha256'] for path in (root/'source').rglob('*.py')})
    config=dict(old,root=str(root),socket='/tmp/r233-'+identity+'.sock',source_manifest=ref(root/'SOURCE_MANIFEST.json'))
    write(root/'CONFIG.private.json',config)
    write(root/'HANDOFF.json',handoff)
    subprocess.run([str(BASE/'v2/venv/bin/python'),'-B','-c','import '+MODULE+'.judge_service'],
        cwd=root/'source',env=dict(os.environ,PYTHONPATH=str(root/'source'),CUDA_VISIBLE_DEVICES=''),
        check=True,capture_output=True,timeout=90)
    unit=unit_run(root,root/'source',identity,config['deadline_unix'],MODULE+'.judge_service',root/'CONFIG.private.json',config['physical'])
    receipt=dict(unix=time.time(),unit=unit,previous_failed_pid=loaded['pid'],reason='exclusive_old_LISTENING_receipt_preserved_new_listener_output',
        state_unchanged=True,old_results_rescored=False,CPU_import_pass=True,status='RETRY_DISPATCHED_NOT_YET_LOADED')
    write(root/'DISPATCHED.json',receipt)
    return receipt
