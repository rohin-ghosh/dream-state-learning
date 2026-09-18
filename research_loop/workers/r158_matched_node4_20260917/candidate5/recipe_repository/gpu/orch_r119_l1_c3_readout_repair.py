"""Continue missing held calls only; preserve failed ON captures and optimizer."""

import argparse
import importlib.util
import inspect
import os
from pathlib import Path
import subprocess
import sys
import time


def remaining_readout_source(source):
    begin = source.index('        for task in capability.tasks():')
    end = source.index("        held=read(ROOT/'input/prior/LEGACY_READOUT.json')['held']",begin)
    removed = source[begin:end]
    assert removed.count('loaded.engine.generate(')==1 and "CAPABILITY_" in removed
    assert source.count('    calls=[]')==1
    result=source[:begin].replace('    calls=[]','    calls=preserved_capabilities')+source[end:]
    return result.replace('base_and_adapter_unchanged=True,finished_unix=',
        "base_and_adapter_unchanged=True,base_and_adapter_unchanged_scope='REPAIR_PROCESS_ONLY',inherited_capability_postcheck_missing=True,preserved_capability_calls=32,new_capability_calls=0,finished_unix=")


def load(root):
    spec=importlib.util.spec_from_file_location('frozen_C3',root/'orch_r119_l1_c3_consumer.py')
    consumer=importlib.util.module_from_spec(spec);spec.loader.exec_module(consumer)
    frozen,config=consumer.configuration(root)
    repair=frozen.trainer.read(root/'REPAIR_PLAN.json')
    assert frozen.trainer.sha(__file__)==repair['source_sha256']
    for path,expected in repair['pins'].items():
        assert frozen.trainer.sha(path)==expected
    assert repair['arm']=='CONTROL' and repair['previous_condition']=='ON'
    return consumer,frozen,config,repair


def native(root,condition):
    consumer,frozen,config,repair=load(root)
    trainer=frozen.trainer
    resume=Path(repair['checkpoint'])
    bound_frozen,frozen_config,stage,bound,context=consumer.stage_namespace(root,'CONTROL',repair['segment'],resume)
    if condition=='OFF':
        context['readout']('CONTROL','OFF',repair['segment'],resume)
        return
    from organism_v6 import orch_r107_capability as capability
    metadata=trainer.storage.verify_checkpoint(resume)['metadata']
    captures=[]
    for path,task in zip(repair['capabilities'],capability.tasks(),strict=True):
        record=trainer.read(path)
        assert record['task_id']==task['id'] and record['checkpoint_sha256']==metadata['adapter']['state_sha256']
        assert record['suite_sha256']==capability.digest(capability.tasks())
        assert record['lora_enabled'] is True
        captures.append(record)
    assert len(captures)==32
    namespace=dict(trainer.__dict__,ROOT=stage,load_plan=context['load_plan'],preserved_capabilities=captures)
    exec(compile(remaining_readout_source(inspect.getsource(trainer.readout)),__file__,'exec'),namespace)
    namespace['readout']('CONTROL',1,'ON',repair['segment'],resume)
    output=stage/'fit'/'CONTROL'/('segment%03d'%repair['segment'])/'readout'/'ON'
    for index,path in enumerate(repair['capabilities']):
        (output/('CAPABILITY_%03d.json'%index)).symlink_to(Path(path))
    trainer.write(stage/'RECOVERED_ON_PROVENANCE.json',dict(
        original_capability_paths=repair['capabilities'],original_capability_calls=32,new_capability_calls=0,
        original_process_postcheck='MISSING_AFTER_DEPENDENCY_FAILURE_PRESERVED',
        repair_process_postcheck='PASSED_FOR_FRESH_HELD_ONLY_PROCESS',
        no_replay=True,original_failure_preserved=True,observed_unix=time.time()))


def supervise(root):
    consumer,frozen,config,repair=load(root)
    trainer=frozen.trainer
    ready=trainer.read(root/'PRE_GPU.json')
    assert ready['cpu_passed'] and ready['builder_line'].startswith('[Builder]')
    for identity in repair['absent_identities']:
        process=Path('/proc',str(identity['pid']),'stat')
        assert not process.exists() or process.read_text().rsplit(')',1)[1].split()[0]=='Z'
    assert not (root/'REPAIR_STARTED.json').exists()
    trainer.write(root/'REPAIR_STARTED.json',dict(identity=frozen.identity(os.getpid()),observed_unix=time.time()))
    consumer.stage_namespace(root,'CONTROL',repair['segment'],Path(repair['stage_resume']),create=True)
    from gpu import orch_combined_l1_continual_run as admission
    import orch_r119_l1_c3_scan as enrichment
    admission.scan=lambda index,service:enrichment.scan_process(root,index,service)
    scan=admission.scan
    for condition in ('ON','OFF'):
        while time.time()<config['hard_deadline_unix']:
            try:
                report=scan(1,Path(config['service_identity']))
            except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
                report=dict(clear=False,error_type=type(error).__name__)
            report.pop('host',None)
            trainer.write(root/('ADMISSION_%s_%d.json'%(condition,time.time_ns())),report)
            if report['clear']:
                assert report['scanner_euid']==0 and report['gpu']['uuid']==config['uuid_by_index'][1]
                break
            time.sleep(2)
        else:
            return
        with (root/('REPAIR_'+condition+'.log')).open('x') as log:
            child=subprocess.Popen([sys.executable,'-B','-u',str(Path(__file__).resolve()),'native',
                '--root',str(root),'--condition',condition],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=config['uuid_by_index'][1],
                    HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        identity=frozen.identity(child.pid)
        trainer.write(root/('REPAIR_'+condition+'_LAUNCH.json'),dict(identity=identity,observed_unix=time.time()))
        while child.poll() is None:
            trainer.write(root/'REPAIR_HEARTBEAT.json',dict(identity=identity,condition=condition,observed_unix=time.time()))
            if time.time()>=config['hard_deadline_unix']:
                frozen.original.stop(child,identity,'ORIGINAL_LEASE_MARGIN');return
            time.sleep(2)
        trainer.write(root/('REPAIR_'+condition+'_EXIT.json'),dict(returncode=child.returncode,observed_unix=time.time()))
        assert child.returncode==0,'failed_repair_preserved_no_replay'
    checkpoint=Path(repair['checkpoint'])
    stage=root/'CONTROL'/('segment%03d'%repair['segment'])
    proofs=consumer.readout_proof(trainer,stage,'CONTROL',repair['segment'],checkpoint)
    trainer.write(root/'RELEASED_CONTROL.json',dict(status='RELEASED',arm='CONTROL',checkpoint=str(checkpoint),
        next_segment=repair['segment']+1,campaign_sha256=trainer.sha(root/'CAMPAIGN.json'),
        commit_sha256=trainer.sha(checkpoint/'COMMIT.json'),optimizer_sha256=trainer.sha(checkpoint/'optimizer.pt'),
        rng_sha256=trainer.sha(checkpoint/'rank0.pt'),readouts=proofs,
        original_ON_capability_postcheck_missing=True,repair_provenance_sha256=trainer.sha(stage/'RECOVERED_ON_PROVENANCE.json'),
        no_replay=True,optimizer_reset=False,observed_unix=time.time()))
    consumer.supervise(root,'CONTROL')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('supervise','native'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--condition',choices=('ON','OFF'))
    options=parser.parse_args()
    if options.action=='supervise':supervise(options.root)
    else:native(options.root,options.condition)
