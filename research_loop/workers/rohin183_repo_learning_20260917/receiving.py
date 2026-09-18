"""CPU-only receiving verification before the one-shot device-confined dispatch."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    root=Path(__file__).resolve().parent
    source=root/'source'
    sys.path.insert(0,str(source))
    from gpu import orch_r125_continual_guard as guard
    from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import require,write,permitted_path
    config,plan=guard.validate(root/'control/GUARD.json')
    lease=json.loads((root/'LEASE.json').read_bytes())
    require(sha(lease['original_bound_lease_path'])==lease['original_bound_lease_sha256'],'unchanged_actual_original_lease')
    require(not Path(plan['root']).exists(),'fresh_no_saved_life')
    tools=json.loads((root/'TOOLS.json').read_bytes())
    require(sha(root/'SNAPSHOT_MANIFEST.json')==tools['snapshot_manifest']['sha256'],'snapshot_manifest_bytes')
    manifest=json.loads((root/'SNAPSHOT_MANIFEST.json').read_bytes())
    actual={str(path.relative_to(root/'snapshot')) for path in (root/'snapshot').rglob('*') if path.is_file()}
    require(actual==set(manifest['files']),'only_released_manifest_files')
    for name,item in manifest['files'].items():
        require(permitted_path(name),'current_safe_path_policy')
        path=root/'snapshot'/name
        require(not path.is_symlink() and path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],'received_safe_snapshot_bytes')
    command=[sys.executable,'-B','-m','unittest','tests.test_orch_r125_stream_journal',
        'tests.test_orch_r125_continual_native','tests.test_orch_r125_continual_stream','tests.test_orch_r127_pilot_console',
        'research_loop.workers.rohin183_repo_learning_20260917.test_runtime','-q']
    result=subprocess.run(command,cwd=source,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(source),PYTHONDONTWRITEBYTECODE='1'),
        text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
    log=write(root/'control/RECEIVING_CPU.log',result.stdout.encode())
    receipt=write(root/'control/RECEIVING_CPU.json',dict(passed=result.returncode==0,exit_code=result.returncode,log=log,
        observed_unix=time.time(),source_pins=config['source_pins'],command=command,safe_files=len(actual),
        snapshot_bytes=manifest['snapshot_bytes'],GPU_model_calls=0,learner_signals=0,model_loaded=False))
    print(json.dumps(dict(receipt=receipt,passed=result.returncode==0,safe_files=len(actual),log_summary=result.stdout[-800:]),sort_keys=True))
    require(result.returncode==0,'receiving_CPU_failed_no_launch')


if __name__=='__main__':
    main()
