"""Existing strict systemd device policy adapted only for the assigned node2 GPU."""

import argparse
import errno
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import require,write,digest


DEVICE='GPU-0cc84073-37a0-4f7a-e555-11671425bd03'
MINOR=5
MODULE='gpu.r184_node2_confinement'


def command(config_path,mode,now=None):
    from gpu import orch_r125_continual_guard as guard
    config,plan=guard.validate(config_path)
    now=time.time() if now is None else now
    remaining=min(7200,int(plan['hard_end_unix']-now-15))
    require(mode in ('probe','child') and 30<remaining<=21600,'bounded_assigned_child_service')
    unit='orch-r186-c2-lr03-'+mode+'-'+digest(Path(config_path).read_bytes())[:16]
    properties=dict(User='2524',Group='2524',NoNewPrivileges='yes',DevicePolicy='strict',
        CapabilityBoundingSet='',AmbientCapabilities='',ProtectControlGroups='yes',
        RuntimeMaxSec='60' if mode=='probe' else str(remaining),TimeoutStopSec='5',KillMode='control-group',
        WorkingDirectory=plan['source_root'],MemoryMax=str(64*1024**3),TasksMax='256')
    properties['BindPaths']=config['copy_raw']+':'+plan['root']
    devices=['/dev/null rw','/dev/zero rw','/dev/random r','/dev/urandom r',
        '/dev/nvidia5 rw','/dev/nvidiactl rw','/dev/nvidia-uvm rw']
    return ['sudo','-n','/usr/bin/systemd-run','--quiet','--wait','--pipe','--unit='+unit,
        *['--property='+key+'='+value for key,value in properties.items()], '--property=DeviceAllow=',
        *['--property=DeviceAllow='+value for value in devices],'/usr/bin/env','-i',
        'PATH=/usr/bin:/bin','HOME='+str(Path(config['attempt_dir']).parent),'TMPDIR=/tmp',
        'CUDA_VISIBLE_DEVICES='+DEVICE,'PYTHONDONTWRITEBYTECODE=1','PYTHONPATH='+plan['source_root'],
        'HF_HUB_OFFLINE=1','TRANSFORMERS_OFFLINE=1','OMP_NUM_THREADS=1','MKL_NUM_THREADS=1',
        'TOKENIZERS_PARALLELISM=false',sys.executable,'-B','-m',MODULE,mode,'--config',str(config_path),'--unit',unit]


def device_checks(opener=os.open,closer=os.close):
    allowed,denied=[],[]
    for minor in range(8):
        path='/dev/nvidia'+str(minor)
        try:
            descriptor=opener(path,os.O_RDWR|os.O_CLOEXEC)
        except OSError as error:
            require(minor!=MINOR and error.errno in (errno.EPERM,errno.EACCES),'actual_foreign_device_denial')
            denied.append(minor)
        else:
            closer(descriptor)
            require(minor==MINOR,'foreign_GPU_open_abort')
            allowed.append(path)
    for path in ('/dev/nvidiactl','/dev/nvidia-uvm'):
        descriptor=opener(path,os.O_RDWR|os.O_CLOEXEC)
        closer(descriptor)
        allowed.append(path)
    require(denied==[0, 1, 2, 3, 4, 6, 7],'all_seven_foreign_minors_denied')
    return dict(allowed_open_close=allowed,denied_foreign_minors=denied)


def verify(unit):
    require(os.getuid()==os.getgid()==2524,'nonroot_service_identity')
    cgroup=Path('/proc/self/cgroup').read_text().strip()
    require(cgroup=='0::/system.slice/'+unit+'.service','actual_systemd_device_cgroup')
    status=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    require(int(status['CapEff'].strip(),16)==0 and status['NoNewPrivs'].strip()=='1','no_privilege_escalation')
    info=Path('/proc/driver/nvidia/gpus/0000:d1:00.0/information')
    fields=dict(line.split(':',1) for line in info.read_text().splitlines() if ':' in line)
    require(fields['GPU UUID'].strip()==DEVICE and int(fields['Device Minor'])==MINOR,'kernel_UUID_and_minor')
    metadata=Path('/dev/nvidia5').lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev)==195 and os.minor(metadata.st_rdev)==MINOR,'actual_character_device')
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            require(not os.readlink(descriptor).startswith('/dev/nvidia'),'no_inherited_GPU_descriptor')
        except FileNotFoundError:
            pass
    require(os.environ.get('CUDA_VISIBLE_DEVICES')==DEVICE,'UUID_environment')
    return dict(schema='R183_STRICT_GPU2_CPU_OPEN_CLOSE_V1',observed_unix=time.time(),pid=os.getpid(),
        cgroup=cgroup,unit=unit,gpu_uuid=DEVICE,target_minor=MINOR,checks=device_checks(),GPU_model_calls=0)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=('dispatch','probe','child'))
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--unit')
    args=parser.parse_args()
    from gpu import orch_r125_continual_guard as guard
    config,plan=guard.validate(args.config)
    attempt=Path(config['attempt_dir'])
    if args.mode=='dispatch':
        require(Path(config['copy_raw']).is_dir() and not (attempt/'OUTER_STARTED.json').exists(),'once_only_saved41_copy')
        cpu=json.loads((attempt/'RECEIVING_CPU.json').read_bytes())
        require(cpu['passed'] and cpu['source_pins']==config['source_pins'],'actual_receiving_CPU_source_binding')
        write(attempt/'OUTER_STARTED.json',dict(pid=os.getpid(),started_unix=time.time(),no_retry=True,
            config_sha256=digest(args.config.read_bytes()),cpu_sha256=digest((attempt/'RECEIVING_CPU.json').read_bytes())))
        try:
            subprocess.run(command(args.config,'probe'),check=True,timeout=100)
            scan=['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH='+plan['source_root'],sys.executable,'-B','-m','gpu.orch_r125_continual_guard','scan','--config',str(args.config)]
            report=json.loads(subprocess.check_output(scan,text=True,timeout=100))
            require(report['scanner_euid']==0 and report['clear'] and not report['blocking_reasons'],'fresh_privileged_target_clear')
            write(attempt/'PRE_SERVICE_ADMISSION.json',dict(report=report,verified_unix=time.time(),
                guard_sha256=digest(args.config.read_bytes())))
            argv=command(args.config,'child')
            write(attempt/'OUTER_COMMAND.json',dict(command=argv,issued_unix=time.time()))
            status=subprocess.run(argv,check=False).returncode
            write(attempt/'OUTER_EXIT.json',dict(status=status,finished_unix=time.time()))
        except BaseException as error:
            write(attempt/'OUTER_FAILED.json',dict(error_type=type(error).__name__,error=str(error),
                finished_unix=time.time(),no_retry=True))
            raise
    else:
        proof=verify(args.unit)
        write(attempt/('CONFINEMENT_CPU.json' if args.mode=='probe' else 'CONFINEMENT_CHILD.json'),proof)
        if args.mode=='child':
            guard.supervise(args.config)


if __name__=='__main__':
    main()
