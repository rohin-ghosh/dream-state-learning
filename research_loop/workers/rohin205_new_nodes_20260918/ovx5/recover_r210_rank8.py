"""One new dispatch identity after preserved zero-update admission failure."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from ddp_pilot import require, sha, write


def main():
    os.environ['CUDA_VISIBLE_DEVICES']=''
    old=Path('/localhome/local-rohing/orch_r210_ovx5_mixed1m_rank8_20260918_continuation1')
    root=Path('/localhome/local-rohing/orch_r210_ovx5_mixed1m_rank8_20260918_continuation2')
    require(not (old/'training').exists(),'failed_dispatch_had_zero_loaded_or_training')
    source=json.loads((old/'PILOT_CONFIG.json').read_bytes())
    subprocess.run(['sudo','-n',sys.executable,'-B',str(old/'four_gpu_admission.py'),'scan','--root',str(old)],check=True,timeout=40)
    root.mkdir(mode=0o700)
    names=set(source['source_pin'])|set(json.loads((old/'PACKET.json').read_bytes())['files'])
    names.update(['test_ddp_pilot.py','test_r210_mixed_train.py'])
    for name in names:
        if name=='four_gpu_admission.py':continue
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
        os.link(old/name,target)
    shutil.copy2(Path(__file__).parent/'four_gpu_admission.py',root/'four_gpu_admission.py')
    config=dict(source,unit_prefix='orch-r210-ovx5-mixed-rank8-continuation2-',pilot_end_unix=time.time()+3600,
        runtime_max_seconds=int(source['training_end_unix']-time.time()),dispatch_recovery_of=str(old))
    config['source_pin']=dict(source['source_pin'],**{'four_gpu_admission.py':sha(root/'four_gpu_admission.py')})
    write(root/'PILOT_CONFIG.json',config)
    transition=json.loads((old/'R210_TRANSITION.json').read_bytes())
    write(root/'R210_TRANSITION.json',dict(transition,failed_R210_dispatch_preserved=str(old),failed_dispatch_updates=0))
    result=subprocess.run([sys.executable,'-B',str(root/'test_r210_mixed_train.py')],cwd=root,capture_output=True,text=True,check=False,timeout=60)
    (root/'RECEIVING_CPU.log').write_text(result.stdout+result.stderr)
    require(result.returncode==0 and 'skipped' not in result.stderr,'five_receiving_CPU_tests_again')
    write(root/'RECEIVING_CPU.json',dict(passed=True,actual_Torch_CPU_tests=5,CUDA_initialized=False,
        config_sha256=sha(root/'PILOT_CONFIG.json'),observed_unix=time.time(),source_pin=config['source_pin'],
        zero_update_failure_preserved=True,source_and_optimizer_unchanged=True,only_admission_failure_receipt_added=True))
    print(json.dumps(dict(root=str(root),status='CPU_READY_NEW_IDENTITY_AFTER_FRESH_CLEAR_SCAN',resume_step=config['resume_step'])))


if __name__=='__main__':
    main()
