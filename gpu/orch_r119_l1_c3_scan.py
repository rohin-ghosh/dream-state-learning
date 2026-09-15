"""Pinned three-observation argv reconciliation, retaining zero-MiB ownership."""

import argparse
import ast
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace


def require(value,reason):
    if not value:raise ValueError(reason)


def strict_reconcile(reconciler,report,observations):
    if report['scanner_euid']!=0 or report['gpu']['memory_used_mib']!=0:
        return report
    selected={}
    for process,samples in observations.items():
        if len(samples)>=3 and all(sample.get('cvd')==samples[0].get('cvd') for sample in samples):
            selected[process]=samples
    return reconciler(report,selected)


def libraries(root):
    manifest=json.loads((root/'SCAN_MANIFEST.json').read_text())
    for name,expected in manifest['files'].items():
        require(hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,'pinned_scan_source:'+name)
    for name in ('orch_r110_admission','orch_r111_route_admission','orch_math_feedback_uptake_r118_argv_admission'):
        spec=importlib.util.spec_from_file_location('gpu.'+name,root/(name+'.py'))
        module=importlib.util.module_from_spec(spec)
        sys.modules['gpu.'+name]=module
        spec.loader.exec_module(module)
    argv=module
    reconciler=argv.reconcile
    argv.reconcile=lambda report,observations:strict_reconcile(reconciler,report,observations)
    source=(root/'orch_math_feedback_uptake_r125_runtime_scan.py').read_text()
    tree=ast.parse(source)
    functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('extra_samples','enriched_scan')]
    require(len(functions)==2,'exact_existing_sampling_helpers')
    namespace=dict(os=os,inspect=inspect,argv=argv,run=SimpleNamespace(require=require),__file__=__file__)
    exec(compile(ast.Module(body=functions,type_ignores=[]),__file__,'exec'),namespace)
    return namespace['enriched_scan'],argv


def scan(root,index,service):
    require(os.geteuid()==0 and index in (0,1),'root_owned_C3_training_slots_only')
    from gpu import orch_combined_l1_continual_run as original
    enriched,argv=libraries(root)
    minor=argv.original.minor
    previous=minor.pinned.policy
    minor.pinned.policy=SimpleNamespace(DEVICES=original.DEVICES,HOST_SHA=original.combined.HOST_SHA,
        require=previous.require,allocation=lambda number:previous.require(number in (0,1),'C3_only'))
    try:
        report=enriched(index,service)
    finally:
        minor.pinned.policy=previous
    report.pop('host',None)
    report['C3_enrichment_manifest_sha256']=hashlib.sha256((root/'SCAN_MANIFEST.json').read_bytes()).hexdigest()
    report['C3_zero_mib_required']=True
    return report


def scan_process(root,index,service):
    command=['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+os.environ['PYTHONPATH'],'python3','-B',str(root/'orch_r119_l1_c3_scan.py'),
        '--root',str(root),'--index',str(index),'--service',str(service)]
    result=subprocess.run(command,capture_output=True,text=True,check=True,timeout=90)
    return json.loads(result.stdout)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--index',type=int,required=True)
    parser.add_argument('--service',type=Path,required=True)
    options=parser.parse_args()
    print(json.dumps(scan(options.root,options.index,options.service)))
