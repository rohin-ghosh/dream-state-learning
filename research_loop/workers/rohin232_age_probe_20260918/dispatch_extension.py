"""Separate C0 inference allocation; original results and all other owners unchanged."""

import argparse
import subprocess


ROOT='/localhome/local-rohing/orch_r232_age_probe_C0_s84_20260918'
DEVICES={4:'GPU-891f01d9-82a7-1c36-5e71-e9f6912cada6',7:'GPU-b7ec9035-3ba3-464f-6c2f-7588a3e328c1'}


def dispatch(mode,physical,deadline):
    assert (mode,physical) in [('player',4),('judge',7)]
    code='''import pathlib,json,hashlib,os,subprocess,time
root=pathlib.Path(ROOT);mode=MODE;physical=PHYSICAL;gpu=GPU;deadline=DEADLINE
assert os.getuid()==1352 and 60<deadline-time.time()<=7200
assert not (root/(mode+'_DISPATCHED.json')).exists()
mapping=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used','--format=csv,noheader,nounits'],text=True)
row=next(line for line in mapping.splitlines() if line.startswith(str(physical)+','));fields=[value.strip() for value in row.split(',')]
assert fields[1]==gpu and int(fields[2])<100
assert gpu not in subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
files=json.loads((root/'SOURCE_MANIFEST.json').read_bytes())
assert all(hashlib.sha256((root/'source'/name).read_bytes()).hexdigest()==expected for name,expected in files.items())
assert json.loads((root/'FRESHNESS_VERIFIED.json').read_bytes())['eligible']
unit='orch-r232-c0-s84-'+mode+'-20260918'
command=['sudo','-n','systemd-run','--unit='+unit,'--property=User=1352','--property=Group=1352',
 '--property=WorkingDirectory='+str(root/'source'),'--property=RuntimeMaxSec='+str(int(deadline-time.time())),
 '--property=TimeoutStopSec=30','--property=KillMode=control-group','--property=UMask=0077',
 '--property=DevicePolicy=closed','--property=NoNewPrivileges=yes',
 '--property=StandardOutput=append:'+str(root/(mode+'.log')),'--property=StandardError=append:'+str(root/(mode+'.log'))]
for device in ['/dev/nvidia'+str(physical),'/dev/nvidiactl','/dev/nvidia-uvm','/dev/nvidia-uvm-tools']:
 command.append('--property=DeviceAllow='+device+' rw')
environment=dict(CUDA_VISIBLE_DEVICES=gpu,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
 PYTHONPATH=str(root/'source'),OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',TOKENIZERS_PARALLELISM='false',HOME='/localhome/local-rohing')
command+=['--setenv='+key+'='+value for key,value in environment.items()]
command+=['/localhome/local-rohing/v2/venv/bin/python','-B','-m','research_loop.workers.rohin232_age_probe_20260918.extension',
 '--root',str(root),'--mode',mode,'--physical',str(physical),'--deadline',str(deadline)]
subprocess.run(command,check=True,capture_output=True,timeout=20)
receipt=dict(unix=time.time(),mode=mode,physical=physical,uuid=gpu,deadline=deadline,unit=unit,
 status='DISPATCHED_NOT_YET_LOADED',source_manifest_sha256=hashlib.sha256((root/'SOURCE_MANIFEST.json').read_bytes()).hexdigest(),
 existing_life_or_service_signals=[])
(root/(mode+'_DISPATCHED.json')).write_text(json.dumps(receipt,sort_keys=True));print(json.dumps(receipt))
'''
    for marker,value in [('ROOT',ROOT),('MODE',mode),('PHYSICAL',physical),('GPU',DEVICES[physical]),('DEADLINE',deadline)]:
        code=code.replace(marker,repr(value))
    result=subprocess.run(['bash','gpu/ovx4_ssh.sh','python3 -B -'],input=code,text=True,capture_output=True,timeout=40)
    if result.returncode:
        raise RuntimeError(result.stderr[-1800:])
    print(result.stdout.strip())


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['player','judge'],required=True)
    parser.add_argument('--physical',type=int,required=True)
    parser.add_argument('--deadline',type=float,required=True)
    args=parser.parse_args()
    dispatch(args.mode,args.physical,args.deadline)
