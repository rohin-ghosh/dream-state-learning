"""Tested carry-preserving overlay and strict custody; requires Main adoption."""

import argparse
from copy import deepcopy
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace

from gpu import orch_r108_code_parent_r115_guard as original
from gpu import orch_r108_code_parent_r116_shared as client
from gpu import orch_r108_code_parent_r116_shared_run as lifecycle
from gpu import orch_r108_code_parent_r118_handoff as handoff


run=client.run
require=client.require
MODULE='gpu.orch_r108_code_parent_r118_activate'


def bound(path, expected):
    path=Path(path)
    require(path.is_absolute() and run.sha(path)==expected,'exact_artifact_reference')
    return run.read(path)


def handoff_document(root):
    document=run.read(root/'R118_SHARED_HANDOFF_BRANCH.json')
    require(document['root']==str(root.resolve()),'same_handoff_root')
    require(all(not (Path('/proc')/str(identity['pid'])).exists()
        for identity in document['predecessors']),'all_predecessors_exited')
    require(all(run.sha(root/name)==digest for name,digest in document['preserved_files'].items()),
        'all_preserved_handoff_files')
    return document


def prepare(root, initialized, source):
    root=Path(root).resolve(strict=True)
    source=Path(source).resolve(strict=True)
    released=handoff_document(root)
    plan=run.read(root/'PLAN.json')
    branch={2:'F3',6:'A3'}.get(plan['physical'])
    require(branch==released['branch'],'own_CODE_branch')
    receipt=run.read(initialized)
    require(receipt['schema']=='R118_SHARED_INITIALIZED_V1','Main_initialization_required')
    binding=receipt['bindings'][branch]
    common=Path(binding['root'])
    require(Path(initialized).resolve()==common/'INITIALIZED.json','actual_Main_initialization_path')
    adoption=bound(binding['adoption_path'],binding['adoption_sha256'])
    require(adoption['schema']=='R118_SHARED_ADOPTION_V1' and adoption['no_lifetime_reset'] is True,
        'Main_adopted_released_F1')
    require(adoption['branch_bounds'][branch]==released['bounds'], 'same_adopted_bounds')
    config=bound(common/'CONFIG.json',binding['config_sha256'])
    require(config['owner']=='F1' and config['initial_checkpoint']==adoption['checkpoint']
        and config['initial_history']==adoption['initial_history'], 'exact_Main_history_and_checkpoint')
    cpu=run.read(source.parent/'CPU_TESTS.json')
    manifest=run.read(source.parent/'SOURCE_SHA256.json')
    require(cpu['passed'] is True and cpu['cuda_initialized'] is False
        and cpu['source_manifest_sha256']==run.sha(source.parent/'SOURCE_SHA256.json'),'tested_overlay')
    require(all(run.sha(source/name)==digest for name,digest in manifest.items()),'frozen_overlay_source')
    activation=dict(schema='R118_CODE_ACTIVATION_V1',predecessor_plan_sha256=run.sha(root/'PLAN.json'),
        inherited_bounds=released['bounds'],shared_learner=binding,
        predecessor_identity=released['predecessors'][0],
        previous_reservations={Path(name).name:digest for name,digest in released['preserved_files'].items()
            if name.startswith('reservations/')},
        handoff=dict(path=str(root/'R118_SHARED_HANDOFF_BRANCH.json'),
            sha256=run.sha(root/'R118_SHARED_HANDOFF_BRANCH.json')),
        initialization=dict(path=str(Path(initialized).resolve()),sha256=run.sha(initialized)),
        successor_source=str(source),source_manifest_sha256=run.sha(source.parent/'SOURCE_SHA256.json'),
        cpu_test_sha256=run.sha(source.parent/'CPU_TESTS.json'),
        command_module=MODULE,original_roster_source_unchanged=True)
    target=root/'SHARED_ACTIVATION.json'
    if target.exists():
        require(run.read(target)==activation,'immutable_activation')
    else:
        run.write_new(target,activation)
    return activation


def validate_activation(root):
    activation=run.read(root/'SHARED_ACTIVATION.json')
    require(activation['schema']=='R118_CODE_ACTIVATION_V1','explicit_adopted_CODE_activation')
    released=bound(activation['handoff']['path'],activation['handoff']['sha256'])
    require(handoff_document(root)==released,'actual_preserved_release')
    initialized=bound(activation['initialization']['path'],activation['initialization']['sha256'])
    branch=released['branch']
    require(initialized['bindings'][branch]==activation['shared_learner'],'actual_Main_branch_binding')
    source=Path(activation['successor_source'])
    require(source==Path(__file__).resolve().parents[1],'actual_frozen_overlay_execution')
    manifest_path=source.parent/'SOURCE_SHA256.json'
    manifest=bound(manifest_path,activation['source_manifest_sha256'])
    require(all(run.sha(source/name)==digest for name,digest in manifest.items()),'frozen_overlay_source')
    tests=bound(source.parent/'CPU_TESTS.json',activation['cpu_test_sha256'])
    require(tests['passed'] is True and tests['cuda_initialized'] is False
        and tests['source_manifest_sha256']==activation['source_manifest_sha256'],'own_CPU_before_GPU')
    plan=run.read(root/'PLAN.json')
    require(run.sha(root/'PLAN.json')==activation['predecessor_plan_sha256']
        and {key:plan[key] for key in client.BOUND_FIELDS}==activation['inherited_bounds']==released['bounds'],
        'original_PLAN_caps_deadline')
    require(time.time()<plan['hard_deadline_unix']-120,'remaining_original_lifetime')
    require(plan['hard_deadline_unix']<=plan['lease_end_unix']-21600,'original_lease_margin')
    client.Session(root,dict(plan,shared_learner=activation['shared_learner']))
    return plan,activation


class CarryDriver(client.Driver):
    def __init__(self,root,engine,session):
        super().__init__(root,engine,session)
        released=run.read(self.root/'R118_SHARED_HANDOFF_BRANCH.json')
        saved=bound(released['carry']['path'],released['carry']['sha256'])
        require(saved['schema']=='R118_CODE_CARRY_V1' and saved['old_experience_replayed'] is False,
            'actual_original_carry')
        self.settings=deepcopy(saved['reflection_settings'])
        run.write_new(self.root/'R118_CARRY_RESTORED.json',dict(carry_sha256=released['carry']['sha256'],
            source_id=saved['reflection_source_id'],settings=self.settings,prior_experience_replayed=False))


def native(root):
    validate_activation(root)
    namespace=dict(lifecycle.native.__globals__,client=SimpleNamespace(**dict(vars(client),Driver=CarryDriver)))
    FunctionType(lifecycle.native.__code__,namespace,'native')(root)


def scan(root):
    source=Path(__file__).resolve().parents[1]
    result=subprocess.run(['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(source),'python3','-B','-m','gpu.orch_r108_code_parent_r115_admission',
        'scan','--root',str(root)],capture_output=True,text=True,timeout=120,check=True)
    return run.json.loads(result.stdout)


def admitted(snapshot, plan):
    return snapshot.get('clear') is True and snapshot.get('scanner_euid')==0 \
        and snapshot.get('gpu',{}).get('uuid')==plan['gpu_uuid'] \
        and 'device_minor' in snapshot and not snapshot.get('blocking_reasons')


def guard(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU_guard_only')
    plan,activation=validate_activation(root)
    original.bind(plan['physical'])
    require(plan['gpu_uuid']==original.DEVICES[plan['physical']],'exact_owned_UUID')
    (root/'R118_SHARED_GUARD_ONCE').mkdir()
    with (Path('/tmp')/('orch_r115_f3_'+plan['gpu_uuid']+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for attempt in range(30):
            require(time.time()<plan['hard_deadline_unix']-120,'remaining_original_lifetime')
            snapshot=scan(root)
            run.write_new(root/'r118_shared_admission'/f'SCAN_{attempt:03d}.json',snapshot)
            if admitted(snapshot,plan):
                break
            time.sleep(10)
        require(admitted(snapshot,plan),'fresh_full_privileged_admission')
        run.write_new(root/'R118_SHARED_ADMISSION.json',snapshot)
        validate_activation(root)
        with (root/'R118_SHARED_NATIVE.log').open('x') as output:
            child=subprocess.Popen([sys.executable,'-B','-m',MODULE,'native','--root',str(root)],
                cwd=activation['successor_source'],stdout=output,stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,start_new_session=True,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES=plan['gpu_uuid'],
                    PYTHONPATH=activation['successor_source'],HF_HUB_OFFLINE='1',
                    TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
            identity=original.scanner.pinned.identity(Path('/proc')/str(child.pid))
            run.write_new(root/'R118_SHARED_NATIVE_LAUNCH.json',dict(identity=identity,
                started_unix=time.time(),activation_sha256=run.sha(root/'SHARED_ACTIVATION.json'),
                admission_sha256=run.sha(root/'R118_SHARED_ADMISSION.json')))
            while child.poll() is None and time.time()<plan['hard_deadline_unix']-5:
                time.sleep(2)
            if child.poll() is None:
                require(original.scanner.pinned.identity(Path('/proc')/str(child.pid))==identity,
                    'exact_owned_successor_identity')
                os.killpg(child.pid,signal.SIGTERM)
                child.wait(timeout=20)
            run.write_new(root/'R118_SHARED_GUARD_TERMINAL.json',dict(returncode=child.returncode,
                finished_unix=time.time(),original_deadline_unchanged=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entry',choices=('prepare','guard','native'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--initialized',type=Path)
    parser.add_argument('--source',type=Path)
    args=parser.parse_args()
    if args.entry=='prepare':
        require(args.initialized is not None and args.source is not None,'explicit_Main_adoption_and_source')
        prepare(args.root,args.initialized,args.source)
    elif args.entry=='guard':
        guard(args.root)
    else:
        native(args.root)
