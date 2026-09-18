"""Only physical6/7, fresh admission, unchanged source battery, finite allocation."""

import argparse
import json
from pathlib import Path
import subprocess
import time


def dispatch(root, mode, deadline):
    physical = {'player': 6, 'judge': 7}[mode]
    code = '''import pathlib,json,hashlib,os,subprocess,time
root=pathlib.Path(ROOT);mode=MODE;physical=PHYSICAL;deadline=DEADLINE
assert os.getuid()==1352 and 60<deadline-time.time()<=3600 and deadline<=1789739970
assert not (root/(mode+'_DISPATCHED.json')).exists()
mapping=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used','--format=csv,noheader,nounits'],text=True)
row=next(line for line in mapping.splitlines() if int(line.split(',')[0])==physical)
fields=[value.strip() for value in row.split(',')];gpu=fields[1]
assert int(fields[2])<100
assert gpu not in subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
files=json.loads((root/'SOURCE_MANIFEST.json').read_bytes())
assert all(hashlib.sha256((root/'source'/name).read_bytes()).hexdigest()==expected for name,expected in files.items())
assert json.loads((root/'FRESHNESS_VERIFIED.json').read_bytes())['eligible']
identity=json.loads((root/'CONDITION.json').read_bytes())
assert identity['parent_tokens']==0 and not identity['source_parent_text_loaded']
unit='orch-'+root.name.removeprefix('orch_').replace('_','-')+'-'+mode
command=['sudo','-n','systemd-run','--unit='+unit,'--property=User=1352','--property=Group=1352',
 '--property=WorkingDirectory='+str(root/'source'),'--property=RuntimeMaxSec='+str(int(deadline-time.time())),
 '--property=TimeoutStopSec=15','--property=KillMode=control-group','--property=UMask=0077',
 '--property=DevicePolicy=closed','--property=NoNewPrivileges=yes',
 '--property=StandardOutput=append:'+str(root/(mode+'.log')),'--property=StandardError=append:'+str(root/(mode+'.log'))]
for device in ['/dev/nvidia'+str(physical),'/dev/nvidiactl','/dev/nvidia-uvm','/dev/nvidia-uvm-tools']:
 command.append('--property=DeviceAllow='+device+' rw')
environment=dict(CUDA_VISIBLE_DEVICES=gpu,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
 PYTHONPATH=str(root/'source'),OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',TOKENIZERS_PARALLELISM='false',HOME='/localhome/local-rohing')
command+=['--setenv='+key+'='+value for key,value in environment.items()]
command+=['/localhome/local-rohing/v2/venv/bin/python','-B','-m','research_loop.workers.rohin233_kept_age_probe_20260918.probe',
 '--root',str(root),'--mode',mode,'--physical',str(physical),'--deadline',str(deadline)]
subprocess.run(command,check=True,capture_output=True,timeout=20)
receipt=dict(unix=time.time(),mode=mode,physical=physical,deadline=deadline,unit=unit,
 status='DISPATCHED_NOT_YET_LOADED',condition=identity['condition'],parent_tokens=0,
 source_manifest_sha256=hashlib.sha256((root/'SOURCE_MANIFEST.json').read_bytes()).hexdigest(),
 existing_life_or_service_signals=[])
(root/(mode+'_DISPATCHED.json')).write_text(json.dumps(receipt,sort_keys=True));print(json.dumps(receipt))
'''
    code = ('ROOT=' + repr(root) + '\nMODE=' + repr(mode) + '\nPHYSICAL=' + repr(physical)
        + '\nDEADLINE=' + repr(deadline) + '\n' + code)
    result = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', 'python3 -B -'], input=code,
        text=True, capture_output=True, timeout=40)
    if result.returncode:
        raise RuntimeError(result.stderr[-1800:])
    receipt = json.loads(result.stdout)
    output = Path(__file__).resolve().parent / 'dispatches'
    output.mkdir(exist_ok=True)
    (output / (receipt['condition'] + '_' + mode + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--mode', required=True, choices=['player', 'judge'])
    parser.add_argument('--deadline', type=float, default=time.time() + 2400)
    args = parser.parse_args()
    dispatch(args.root, args.mode, args.deadline)
