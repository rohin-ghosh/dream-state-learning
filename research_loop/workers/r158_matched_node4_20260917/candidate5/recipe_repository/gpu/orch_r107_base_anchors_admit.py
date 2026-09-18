"""One bounded zero-dispatch admission recovery; no native call or clock reset."""

import argparse
import math
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r107_base_anchors_run as run


def eligible(root):
    run.policy.require((root/'LAUNCH_ONCE').is_dir() and not (root/'LAUNCH.json').exists()
        and not (root/'readout').exists(),'only_zero_dispatch_recovery')
    scans=sorted((root/'ADMISSIONS').glob('*.json'))
    run.policy.require(scans and all(run.rescan.transient(run.read(path)) for path in scans),
        'only_preserved_transient_scans')
    for folder in Path('/proc').glob('[0-9]*'):
        try:
            if folder.stat().st_uid != os.getuid():
                continue
            arguments=(folder/'cmdline').read_bytes().split(b'\0')
            run.policy.require(not (b'gpu.orch_r107_base_anchors_run' in arguments and b'launch' in arguments
                and str(root).encode() in arguments),'original_launcher_still_active')
        except (FileNotFoundError,ProcessLookupError):
            continue


def recover(root,publication_path):
    run.require_host()
    run.policy.require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','cpu_recovery_only')
    plan=run.validate(run.read(root/'PLAN.json'),time.time())
    run.ready_check(root,plan)
    eligible(root)
    publication=run.read(publication_path)
    run.policy.require(publication['source_sha256']==run.sha(__file__)
        and publication['plan_sha256']==run.sha(root/'PLAN.json')
        and publication['own_cpu_tests_passed'] is True and publication['dated_builder_publication'],
        'bound_recovery_publication')
    folder=root/'ADMISSION_RECOVERY'
    folder.mkdir(exist_ok=False)
    cutoff=min(time.time()+120,plan['native_deadline_unix'])
    report=None
    for index in range(60):
        run.policy.require(time.time()<cutoff,'rescan_window_exhausted')
        report=run.ownership.continual.scan(0,run.ownership.continual.ROOT/'SERVICE_IDENTITY.json')
        run.write(folder/f'{index:03d}.json',report)
        if report['clear'] is True:
            run.ownership.validate_scan(report,time.time())
            break
        run.policy.require(run.rescan.transient(report),'real_ownership_block_no_waiver')
        time.sleep(1)
    run.policy.require(report is not None and report['clear'] is True,'strict_clear_required')
    eligible(root)
    run.natural_release()
    run.validate(plan,time.time())
    run.write(root/'ADMISSION.json',dict(plan_sha256=run.sha(root/'PLAN.json'),snapshot=report,
        recovery_publication_sha256=run.sha(publication_path)))
    seconds=math.floor(plan['hard_deadline_unix']-time.time()-5)
    run.policy.require(seconds>0,'original_lifetime_exhausted')
    environment=dict(os.environ,CUDA_VISIBLE_DEVICES=run.GPU_UUID,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(run.SOURCE_ROOT))
    command=['timeout','--signal=TERM','--kill-after=5s',str(seconds)+'s',run.ownership.continual.PYTHON,
        '-B','-m','gpu.orch_r107_base_anchors_run','run','--root',str(root)]
    with (root/'native.log').open('x') as log:
        child=subprocess.Popen(command,cwd=run.SOURCE_ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    receipt=dict(status='LAUNCHED',timeout_identity=run.ownership.continual.minor_scan.pinned.identity(Path('/proc')/str(child.pid)),
        plan_sha256=run.sha(root/'PLAN.json'),admission_sha256=run.sha(root/'ADMISSION.json'),
        hard_deadline_unix=plan['hard_deadline_unix'],launched_unix=time.time(),call_cap=64,
        original_source_and_admissions_preserved=True,recovery_source_sha256=run.sha(__file__))
    run.write(root/'LAUNCH.json',receipt)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--publication',type=Path,required=True)
    arguments=parser.parse_args()
    print(run.ownership.json.dumps(recover(arguments.root,arguments.publication),sort_keys=True))
