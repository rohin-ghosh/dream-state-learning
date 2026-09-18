"""Dispatch only owned free devices with exact kernel confinement and expiry."""

import argparse
import json
from pathlib import Path
import subprocess
import time


ROOT = '/localhome/local-rohing/orch_r232_age_probe_20260918'
DEVICES = {4: 'GPU-891f01d9-82a7-1c36-5e71-e9f6912cada6', 5: 'GPU-c133443b-2a53-dc7b-294f-06b894a58d05',
    6: 'GPU-17a145a7-e358-3193-a0fc-30b469e6c120', 7: 'GPU-b7ec9035-3ba3-464f-6c2f-7588a3e328c1'}


def dispatch(mode, physical, deadline):
    assert (mode, physical) in [('vision', 7), ('judge', 7), ('source51', 4), ('currentC2', 5), ('base', 6)]
    code = '''import hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path(ROOT)
assert os.getuid()==1352
physical=PHYSICAL; gpu=GPU; mode=MODE; deadline=DEADLINE
assert 60<deadline-time.time()<=7200
mapping=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used','--format=csv,noheader,nounits'],text=True)
line=next(row for row in mapping.splitlines() if row.startswith(str(physical)+','))
columns=[column.strip() for column in line.split(',')]
assert columns[1]==gpu and int(columns[2])<100, 'assigned_device_empty_now'
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
assert gpu not in apps, 'no_resident_process_on_owned_slot'
files=json.loads((root/'SOURCE_MANIFEST.json').read_bytes())
assert all(hashlib.sha256((root/'source'/name).read_bytes()).hexdigest()==checksum for name,checksum in files.items())
name='orch-r232-probe-'+mode+'-20260918'
assert not (root/(mode+'_DISPATCHED.json')).exists(), 'no_duplicate_dispatch'
seconds=int(deadline-time.time())
command=['sudo','-n','systemd-run','--unit='+name,'--property=User=1352','--property=Group=1352',
 '--property=WorkingDirectory='+str(root/'source'),'--property=RuntimeMaxSec='+str(seconds),
 '--property=TimeoutStopSec=30','--property=KillMode=control-group','--property=UMask=0077',
 '--property=DevicePolicy=closed','--property=NoNewPrivileges=yes',
 '--property=StandardOutput=append:'+str(root/(mode+'.log')),'--property=StandardError=append:'+str(root/(mode+'.log'))]
for device in ['/dev/nvidia'+str(physical),'/dev/nvidiactl','/dev/nvidia-uvm','/dev/nvidia-uvm-tools']:
 command.append('--property=DeviceAllow='+device+' rw')
environment=dict(CUDA_VISIBLE_DEVICES=gpu,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
 PYTHONPATH=str(root/'source'),OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',TOKENIZERS_PARALLELISM='false',HOME='/localhome/local-rohing')
command+=['--setenv='+key+'='+value for key,value in environment.items()]
command+=['/localhome/local-rohing/v2/venv/bin/python','-B','-m',
 'research_loop.workers.rohin232_age_probe_20260918.runtime','--root',str(root),'--mode',mode,
 '--physical',str(physical),'--deadline',str(deadline)]
subprocess.run(command,check=True,capture_output=True,timeout=20)
receipt=dict(mode=mode,physical=physical,uuid=gpu,unix=time.time(),deadline=deadline,unit=name,
 source_manifest_sha256=hashlib.sha256((root/'SOURCE_MANIFEST.json').read_bytes()).hexdigest(),
 status='DISPATCHED_NOT_YET_LOADED',existing_process_signals=[])
(root/(mode+'_DISPATCHED.json')).write_text(json.dumps(receipt,sort_keys=True))
print(json.dumps(receipt))
'''
    for marker, value in [('ROOT', ROOT), ('PHYSICAL', physical), ('GPU', DEVICES[physical]), ('MODE', mode), ('DEADLINE', deadline)]:
        code = code.replace(marker, repr(value))
    result = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', 'python3 -B -'], input=code,
        text=True, capture_output=True, timeout=40)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    print(result.stdout.strip())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', required=True)
    parser.add_argument('--physical', required=True, type=int)
    parser.add_argument('--deadline', required=True, type=float)
    args = parser.parse_args()
    dispatch(args.mode, args.physical, args.deadline)
