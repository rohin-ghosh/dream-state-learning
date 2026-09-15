"""Continue admission-only F2 startup; never replay an activated native process."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_math_feedback_uptake_r115_native as native


def launch(root, index):
    native.validate(root)
    lane = root/f'lane{index}'
    native.require(not (lane/'LAUNCH.json').exists(), 'no_duplicate_native_lifetime')
    native.require(not (lane/'COUNTERS.json').exists(), 'admission_only_no_native_or_parent_spend')
    release=native.read(lane/'RELEASE.json')
    native.require(release['released'] is True and release['uuid']==native.policy.DEVICES[index], 'exact_owner_release')
    publication=native.read(root/'PUBLICATION.json')
    native.require(publication['ready_sha256']==native.policy.sha(root/'READY.json'), 'published_original_native_source')
    native.require(native.read(root/'GO.json')['authorization']=='WATCHER_RELAYED_ROHIN_DONE', 'r115_actual_go')
    previous=lane/'ACTIVATION.json'
    if previous.exists():
        activation=native.read(previous)
        before=activation['guardian']
        directory=Path('/proc')/str(before['pid'])
        if directory.exists():
            native.require(native.scanner.pinned.identity(directory)!=before,'prior_guardian_still_live')
        for name in ('TERMINAL.json','GUARDIAN_FAILED.json'):
            path=lane/name
            if path.exists():
                path.rename(lane/('ADMISSION_ONLY_'+name))
    else:
        native.write(previous,dict(started_unix=time.time(),native_deadline_unix=native.NATIVE,
            hard_deadline_unix=native.HARD,index=index,guardian=native.scanner.pinned.identity(Path('/proc')/str(os.getpid()))))
    output=lane/'R116_STARTUP'
    output.mkdir(exist_ok=False)
    native.write(output/'SUPERVISOR.json',native.scanner.pinned.identity(Path('/proc')/str(os.getpid())))
    child=identity=None
    status='FAILED'
    def interrupted(signum,frame):
        raise SystemExit(128+signum)
    signal.signal(signal.SIGTERM,interrupted)
    signal.signal(signal.SIGINT,interrupted)
    try:
        admitted=False
        for attempt in range(180):
            native.require(time.time()<native.NATIVE-120,'original_native_deadline')
            result=subprocess.run(['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH='+str(native.SOURCE),'python3','-B',str(Path(native.__file__)),'scan',
                '--root',str(root),'--index',str(index)],capture_output=True,text=True,timeout=90,check=True)
            report=json.loads(result.stdout)
            native.write(output/f'ADMISSION_{attempt:03d}.json',report)
            if report['clear'] and not report['blocking_reasons'] and report['scanner_euid']==0:
                admitted=True
                break
            time.sleep(.3)
        native.require(admitted,'strict_original_scan_no_waiver')
        with (output/'RESIDENT.log').open('x') as log:
            child=subprocess.Popen([native.PYTHON,'-B',str(Path(native.__file__)),'resident','--root',str(root),'--index',str(index)],
                cwd=native.SOURCE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES=native.policy.DEVICES[index],PYTHONPATH=str(native.SOURCE),
                    PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',
                    MKL_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false'))
            identity=native.common.process_identity(Path('/proc')/str(child.pid))
            native.write(lane/'LAUNCH.json',dict(identity=identity,uuid=native.policy.DEVICES[index],started_unix=time.time(),
                admission_only_continuation=True,original_activation_unchanged=True))
            while child.poll() is None:
                native.require(time.time()<native.HARD,'original_hard_wall')
                time.sleep(1)
            native.require(child.returncode==0,'native_error_preserved_no_replay')
            status='COMPLETE'
    except BaseException as error:
        native.write(output/'FAILED.json',dict(error=str(error),type=type(error).__name__,finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            native.common.stop_owned(child,identity)
        native.stop_readouts(lane)
        native.write(lane/'TERMINAL.json',dict(status=status,finished_unix=time.time(),peer_processes_signalled=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=native.policy.ROOT)
    parser.add_argument('--index',type=int,choices=(1,5),required=True)
    args=parser.parse_args()
    launch(args.root,args.index)
