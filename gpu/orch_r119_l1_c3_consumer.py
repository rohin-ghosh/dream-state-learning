"""Immutable segment-bound C3 consumer with exact optimizer/RNG handoff."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import FunctionType, SimpleNamespace


def dependencies(root):
    spec = importlib.util.spec_from_file_location('frozen_continuation', root / 'orch_r119_l1_resume.py')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    return frozen


def cohort_for(update, activation_update):
    assert type(update) is int and type(activation_update) is int
    assert update >= 15460 and (update - 15460) % 128 == 0
    assert activation_update > 15460 and (activation_update - 15460) % 128 == 0
    return 'C3' if update >= activation_update else 'C2'


def completed_exit(stat_text):
    fields = stat_text.rsplit(')',1)[1].split()
    if fields[0] != 'Z':
        return False
    assert int(fields[49]) == 0, 'failed_native_readout_preserved_not_replayed'
    return True


def verify_cohort(trainer, record):
    folder = Path(record['path'])
    assert trainer.sha(folder / 'PLAN.json') == record['plan_sha256']
    assert trainer.sha(folder / 'PREPARED.json') == record['prepared_sha256']
    plan, prepared = trainer.read(folder / 'PLAN.json'), trainer.read(folder / 'PREPARED.json')
    assert prepared['plan_sha256'] == record['plan_sha256'] and prepared['status'] == 'PASS'
    assert trainer.sha(folder / 'ENCODED.json') == prepared['encoded_sha256']
    assert trainer.sha(folder / 'ELIGIBLE.json') == plan['eligible_sha256']
    assert plan['seed_update'] == plan['original_schedule_seed_update'] == 9444
    return folder, plan, prepared


def configuration(root):
    frozen = dependencies(root)
    config = frozen.trainer.read(root / 'CAMPAIGN.json')
    assert frozen.trainer.sha(__file__) == config['source_sha256']
    assert frozen.trainer.sha(frozen.__file__) == config['frozen_source_sha256']
    assert frozen.trainer.sha(frozen.experience.__file__) == config['experience_source_sha256']
    assert config['slots'] == {'FULL':0, 'CONTROL':1}
    assert config['hard_deadline_unix'] == config['lease_end_unix'] - 21600
    assert time.time() < config['hard_deadline_unix']
    for record in config['cohorts'].values():
        verify_cohort(frozen.trainer, record)
    return frozen, config


def stage_namespace(root, arm, segment, resume, create=False):
    frozen, config = configuration(root)
    trainer = frozen.trainer
    commit = trainer.storage.verify_checkpoint(resume)['metadata']
    stage = root / arm / ('segment%03d' % segment)
    if create:
        stage.mkdir(parents=True, exist_ok=False)
        selected = cohort_for(commit['update'], config['activation_update'])
        folder, plan, prepared = verify_cohort(trainer, config['cohorts'][selected])
        (stage / 'ENCODED.json').symlink_to(folder / 'ENCODED.json')
        (stage / 'input/prior').mkdir(parents=True)
        (stage / 'input/prior/LEGACY_READOUT.json').symlink_to(Path(config['held_path']))
        trainer.write(stage / 'BINDING.json', dict(cohort=selected, cohort_record=config['cohorts'][selected],
            campaign_sha256=trainer.sha(root / 'CAMPAIGN.json'), arm=arm, segment=segment,
            resume=str(resume), resume_commit_sha256=trainer.sha(resume / 'COMMIT.json'),
            start_update=commit['update'], end_update=commit['update']+128,
            activation_update=config['activation_update'], observed_unix=time.time()))
    bound = trainer.read(stage / 'BINDING.json')
    assert bound['arm'] == arm and bound['segment'] == segment
    assert bound['campaign_sha256'] == trainer.sha(root / 'CAMPAIGN.json')
    assert bound['cohort'] == cohort_for(bound['start_update'],config['activation_update'])
    assert bound['cohort_record'] == config['cohorts'][bound['cohort']]
    folder, plan, prepared = verify_cohort(trainer,bound['cohort_record'])
    plan = dict(plan, uuid_by_index=config['uuid_by_index'], model_dir=config['model_dir'],
        train_slots=config['slots'], prior_lifetime=plan['lifetime'],
        lifetime=dict(started_unix=plan['lifetime']['started_unix'], hard_deadline_unix=config['hard_deadline_unix'],
            native_deadline_unix=config['hard_deadline_unix'], lease_end_unix=config['lease_end_unix'], max_gpus=14))

    def load_plan(actual_arm, checkpoint, training):
        assert actual_arm == arm
        metadata = trainer.storage.verify_checkpoint(checkpoint)['metadata']
        assert metadata['update'] == bound['start_update' if training else 'end_update']
        if training:
            assert str(checkpoint) == bound['resume']
            assert trainer.sha(checkpoint / 'COMMIT.json') == bound['resume_commit_sha256']
        adapter = trainer.native.bridge.AdapterIdentity.from_document(dict(metadata['adapter'],path=str(checkpoint/'adapter')))
        binding = trainer.native.bridge.StageBinding(plan['cohort_id']+'_'+arm, trainer.native.bridge.ARMS[2],
            0,'training' if training else 'sealed_readout', adapter,False,not training,trainer.sha(stage/'BINDING.json'))
        proxy = SimpleNamespace(binding=lambda unused:binding,
            contract=SimpleNamespace(manifest=lambda unused:dict(recipe=trainer.previous.common.RECIPE)),
            lineage=SimpleNamespace(arm=trainer.native.bridge.ARMS[2]))
        return plan, prepared, metadata, adapter, binding, proxy

    context = dict(frozen.experience.__dict__, ROOT=stage, SLOTS=config['slots'], load_plan=load_plan)
    for name in ('train','readout'):
        original = getattr(frozen.experience,name)
        context[name] = FunctionType(original.__code__,context,name,original.__defaults__)
    return frozen, config, stage, bound, context


def readout_proof(trainer, previous, arm, segment, checkpoint):
    metadata = trainer.storage.verify_checkpoint(checkpoint)['metadata']
    proofs = {}
    for condition in ('ON','OFF'):
        path = previous/'fit'/arm/('segment%03d'%segment)/'readout'/condition/'COMPLETE.json'
        document = trainer.read(path)
        assert document['status'] == 'COMPLETE' and document['condition'] == condition
        assert document['capability_calls'] == 32 and document['base_and_adapter_unchanged'] is True
        assert document['checkpoint_state_sha256'] == metadata['adapter']['state_sha256']
        assert not document['parent_access'] and not document['training_ingestion']
        proofs[condition] = dict(path=str(path),sha256=trainer.sha(path))
    return proofs


def handoff(root, arm):
    frozen, config = configuration(root)
    trainer = frozen.trainer
    request = trainer.read(root / ('REQUEST_'+arm+'.json'))
    previous = Path(request['root'])
    expected = request['supervisor']
    assert expected['uid'] == os.getuid() and frozen.identity(expected['pid']) == expected
    assert trainer.sha(previous/'CONTINUATION.json') == request['continuation_sha256']
    assert trainer.sha(request['supervisor_source']) == request['supervisor_source_sha256']
    command = Path('/proc',str(expected['pid']),'cmdline').read_bytes().split(b'\0')
    assert str(previous).encode() in command and request['supervisor_source'].encode() in command
    descriptor = os.pidfd_open(expected['pid'])
    stopped = False
    released = False
    deadline = min(time.time()+900,config['hard_deadline_unix'])
    try:
        while time.time() < deadline:
            heartbeat = trainer.read(previous/('HEARTBEAT_'+arm+'.json'))
            if heartbeat.get('phase') != 'readout' or heartbeat.get('condition') != 'OFF':
                time.sleep(.25)
                continue
            assert frozen.identity(expected['pid']) == expected
            signal.pidfd_send_signal(descriptor,signal.SIGSTOP)
            stopped = True
            time.sleep(.03)
            assert Path('/proc',str(expected['pid']),'stat').read_text().rsplit(')',1)[1].split()[0] in ('T','t')
            current = trainer.read(previous/('HEARTBEAT_'+arm+'.json'))
            if current != heartbeat:
                signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                stopped = False
                continue
            segment = heartbeat['segment']
            child = heartbeat['identity']
            children_path = Path('/proc',str(expected['pid']),'task',str(expected['pid']),'children')
            children = children_path.read_text().split()
            if any(int(pid) != child['pid'] for pid in children):
                signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                stopped = False
                time.sleep(.25)
                continue
            launch = trainer.read(previous / ('%s_%d_readout_OFF_LAUNCH.json'%(arm,segment)))
            assert launch['identity'] == child and launch['resume'] == heartbeat['resume']
            while time.time() < deadline:
                native = Path('/proc',str(child['pid']))
                if native.exists():
                    assert frozen.identity(child['pid']) == child
                    if not completed_exit((native/'stat').read_text()):
                        time.sleep(.2)
                        continue
                else:
                    assert (previous/('%s_%d_PAIRED_COMPLETE.json'%(arm,segment))).exists()
                checkpoint = Path(heartbeat['resume'])
                proofs = readout_proof(trainer,previous,arm,segment,checkpoint)
                assert not (previous/('%s_%d_train_None_LAUNCH.json'%(arm,segment+1))).exists(), 'next_train_already_started'
                metadata = trainer.storage.verify_checkpoint(checkpoint)['metadata']
                assert metadata['update'] <= config['activation_update'], 'activation_boundary_already_passed'
                receipt = dict(status='SAFE_READOUT_COMPLETE_SUPERVISOR_RELEASE',arm=arm,physical=config['slots'][arm],
                    previous_root=str(previous),previous_supervisor=expected,completed_native=child,
                    previous_segment=segment,next_segment=segment+1,checkpoint=str(checkpoint),update=metadata['update'],
                    commit_sha256=trainer.sha(checkpoint/'COMMIT.json'),optimizer_sha256=trainer.sha(checkpoint/'optimizer.pt'),
                    rng_sha256=trainer.sha(checkpoint/'rank0.pt'),readouts=proofs,observed_unix=time.time(),
                    no_replay=True,optimizer_reset=False,campaign_sha256=trainer.sha(root/'CAMPAIGN.json'))
                trainer.write(root/('BOUNDARY_'+arm+'.json'),receipt)
                signal.pidfd_send_signal(descriptor,signal.SIGTERM)
                signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                stopped = False
                released = True
                for unused in range(100):
                    process = Path('/proc',str(expected['pid']),'stat')
                    if not process.exists() or process.read_text().rsplit(')',1)[1].split()[0] == 'Z':
                        break
                    time.sleep(.05)
                else:
                    raise RuntimeError('released_supervisor_not_exited')
                trainer.write(root/('RELEASED_'+arm+'.json'),dict(receipt,status='RELEASED',
                    boundary_sha256=trainer.sha(root/('BOUNDARY_'+arm+'.json'))))
                return
            raise TimeoutError('owned_OFF_readout_boundary_timeout')
        raise TimeoutError('no_safe_OFF_boundary')
    finally:
        if stopped and not released:
            signal.pidfd_send_signal(descriptor,signal.SIGCONT)
        os.close(descriptor)


def supervise(root,arm):
    import fcntl
    from gpu.orch_combined_l1_continual_run import scan
    frozen,config = configuration(root)
    trainer = frozen.trainer
    pre = trainer.read(root/'PRE_GPU.json')
    assert pre['cpu_passed'] and pre['builder_line'].startswith('[Builder]')
    assert pre['campaign_sha256'] == trainer.sha(root/'CAMPAIGN.json')
    release = trainer.read(root/('RELEASED_'+arm+'.json'))
    assert release['status']=='RELEASED' and release['arm']==arm
    assert release['campaign_sha256']==trainer.sha(root/'CAMPAIGN.json')
    lock = (root/(arm+'.lock')).open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (root/('START_'+arm+'.json')).exists()
    resume = Path(release['checkpoint'])
    for name,field in (('COMMIT.json','commit_sha256'),('optimizer.pt','optimizer_sha256'),('rank0.pt','rng_sha256')):
        assert trainer.sha(resume/name)==release[field]
    trainer.write(root/('START_'+arm+'.json'),dict(identity=frozen.identity(os.getpid()),release=release,observed_unix=time.time()))
    segment = release['next_segment']
    while time.time() < config['hard_deadline_unix']:
        frozen,config,stage,bound,context = stage_namespace(root,arm,segment,resume,create=True)
        for phase,condition in (('train',None),('readout','ON'),('readout','OFF')):
            while time.time() < config['hard_deadline_unix']:
                try:
                    snapshot = scan(config['slots'][arm],Path(config['service_identity']))
                except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
                    snapshot = dict(clear=False,scanner_euid=None,error_type=type(error).__name__)
                snapshot.pop('host',None)
                trainer.write(stage/('ADMISSION_%s_%s_%d.json'%(phase,condition,time.time_ns())),snapshot)
                if snapshot['clear']:
                    assert snapshot['scanner_euid']==0 and snapshot['gpu']['uuid']==config['uuid_by_index'][config['slots'][arm]]
                    break
                trainer.write(root/('HEARTBEAT_'+arm+'.json'),dict(phase='WAIT_OWNERSHIP',segment=segment,cohort=bound['cohort'],observed_unix=time.time()))
                time.sleep(2)
            else:
                return
            command = [sys.executable,'-B','-u',str(Path(__file__).resolve()),phase,'--root',str(root),
                       '--arm',arm,'--segment',str(segment),'--resume',str(resume)]
            if condition:
                command += ['--condition',condition]
            with (stage/('%s_%s.log'%(phase,condition))).open('x') as log:
                child = subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                    start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=config['uuid_by_index'][config['slots'][arm]],
                    HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
            expected = frozen.identity(child.pid)
            trainer.write(stage/('%s_%s_LAUNCH.json'%(phase,condition)),dict(identity=expected,resume=str(resume),binding_sha256=trainer.sha(stage/'BINDING.json')))
            while child.poll() is None:
                trainer.write(root/('HEARTBEAT_'+arm+'.json'),dict(identity=expected,phase=phase,condition=condition,
                    segment=segment,cohort=bound['cohort'],resume=str(resume),observed_unix=time.time()))
                if time.time() >= config['hard_deadline_unix']:
                    frozen.original.stop(child,expected,'ORIGINAL_LEASE_MARGIN')
                    return
                time.sleep(2)
            trainer.write(stage/('%s_%s_EXIT.json'%(phase,condition)),dict(returncode=child.returncode,observed_unix=time.time()))
            assert child.returncode==0,'failed_stage_preserved_no_replay'
            if phase=='train':
                complete = trainer.read(stage/'fit'/arm/('segment%03d'%segment)/'COMPLETE.json')
                resume = Path(complete['checkpoint'])
        proofs = readout_proof(trainer,stage,arm,segment,resume)
        trainer.write(stage/'PAIRED_COMPLETE.json',dict(checkpoint=str(resume),readouts=proofs,
            binding_sha256=trainer.sha(stage/'BINDING.json'),observed_unix=time.time()))
        segment += 1


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('check','handoff','supervise','handoff-run','train','readout'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--arm',choices=('FULL','CONTROL'))
    parser.add_argument('--segment',type=int)
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--condition',choices=('ON','OFF'))
    options=parser.parse_args()
    if options.action=='check':
        frozen,config=configuration(options.root)
        print(json.dumps(dict(status='CPU_PROVENANCE_PASS',activation_update=config['activation_update'],slots=config['slots'])))
    elif options.action in ('handoff','handoff-run'):
        handoff(options.root,options.arm)
        if options.action=='handoff-run':supervise(options.root,options.arm)
    elif options.action=='supervise':
        supervise(options.root,options.arm)
    else:
        frozen,config,stage,bound,context=stage_namespace(options.root,options.arm,options.segment,options.resume)
        if options.action=='train':context['train'](options.arm,options.segment,options.resume)
        else:context['readout'](options.arm,options.condition,options.segment,options.resume)
