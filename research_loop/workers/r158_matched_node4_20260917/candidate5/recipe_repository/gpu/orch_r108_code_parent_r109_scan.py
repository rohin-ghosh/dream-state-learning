"""Exact two-location R109 scope over the full privileged minor-aware scanner."""

import argparse
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

from gpu import orch_rich_hot_a100_minor_scan as scanner
from organism_v6 import orch_r108_code_parent_r109 as policy


def bind(arm):
    config=policy.allocation(arm)
    def allocation(index):
        policy.require(type(index) is int and index==config['index'], 'only_exact_r109_slot')
        return config['uuid']
    scanner.pinned.policy=SimpleNamespace(DEVICES={config['index']:config['uuid']},
        HOST_SHA=config['host_sha256'],require=policy.require,allocation=allocation)
    policy.require(scanner.pinned.host_identity()==config['host_sha256'], 'exact_hashed_node')
    return config


def scan(root,arm):
    config=bind(arm)
    if os.geteuid()==0:
        return scanner.scan(config['index'],root/'SERVICE_IDENTITY.json')
    result=subprocess.run(['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(Path(__file__).resolve().parents[1]),'python3','-B','-m',
        'gpu.orch_r108_code_parent_r109_scan','scan','--root',str(root),'--arm',arm],
        text=True,capture_output=True,timeout=90,check=True)
    report=json.loads(result.stdout)
    policy.require(report['gpu']['index']==config['index'] and report['gpu']['uuid']==config['uuid']
        and report['host_sha256']==config['host_sha256'] and report['scanner_euid']==0
        and 'device_minor' in report,'full_privileged_slot_binding')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('scan','service'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--arm',choices=tuple(policy.ARMS),required=True)
    args=parser.parse_args()
    bind(args.arm)
    if args.phase=='service':
        scanner.pinned.service(args.root/'SERVICE_IDENTITY.json')
    else:
        print(json.dumps(scan(args.root,args.arm),sort_keys=True))
