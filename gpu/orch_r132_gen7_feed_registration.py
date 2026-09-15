"""Explicit gen7-only feed registration and immutable paired C4 continuation."""

import argparse
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
import time
from types import FunctionType


GEN7 = Path('/localhome/local-rohing/orch_r119_l1_gen7_post_r127_20260915_attempt1')
REGISTRATION = 'R132_GEN7_CONTINUING_SELF_TRAIN_FULL15460'
CANDIDATES = {
    'gsm8k-train-6309': (23244,'72b2d93d328ab07922ad4f1eabf14cc5d81e50788739ded97a46f5d25ee666d7'),
    'gsm8k-train-4034': (23268,'ac9b3a30eaf41f220320a03e1c17ebcd868f499c4f7ceb10a16b753a1257dc38'),
    'gsm8k-train-3632': (23292,'b5dab15a93e59e2851a48f587699698d7d5ec12422188bdc2f582acc50d2ac69'),
}


def load(root, name):
    spec=importlib.util.spec_from_file_location(name,root/(name+'.py'))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_exact(source, replacements):
    for before,after in replacements.items():
        assert source.count(before)==1, 'unknown_frozen_seam:'+before
        source=source.replace(before,after)
    return source


def publication_source(source):
    return replace_exact(source,{
        "len(previous_rows) == 19, 'exact_old19'":"len(previous_rows) == 22, 'exact_parent22'",
        "cohort_id='R119_EXPERIENCE_C3_B003'":"cohort_id='R132_GEN7_EXPERIENCE_C4_B004'",
        'batch_number=3':'batch_number=4',
        'old19_digest=':'parent22_digest=',
        'old19_encoded_digest=':'parent22_encoded_digest=',
    })


def candidate_binding(registration, review, row):
    assert Path(registration['root'])==GEN7, 'only_verified_continuing_gen7_root'
    assert registration['source_registration_id']==REGISTRATION
    count,expected=CANDIDATES[review['source_task_id']]
    assert review['path']=='segment0000/gpu7/CALL_%06d.json'%count, 'exact_candidate_capture'
    assert review['call_sha256']==expected and row['cumulative_call']==count
    assert row['source_task_id']==review['source_task_id']
    assert count>21259 and row['new_segment_call']==count-15842, 'original_cursor_accounting'


def cohort_for(update, activation_update):
    assert type(update) is int and type(activation_update) is int
    assert update>=17764 and (update-15460)%128==0
    assert activation_update>17764 and (activation_update-15460)%128==0
    return 'C3' if update<activation_update else 'R132_C4'


def verify_sources(root, helper):
    document=helper.read(root/'R132_SOURCE_PINS.json')
    for name,expected in document.items():
        assert Path(name).name==name and helper.sha(root/name)==expected, 'frozen_source_closure'
    assert helper.sha(__file__)==document[Path(__file__).name]


def publication_context(root):
    original=load(root,'orch_r119_l1_c3_feed')
    verify_sources(root,original)
    context=dict(original.__dict__,__file__=str(Path(__file__).resolve()),REGISTRATION=REGISTRATION)
    verify=FunctionType(original.verify.__code__,context,'verify',original.verify.__defaults__)
    original_gate=FunctionType(original.source_gate.__code__,context,'source_gate',original.source_gate.__defaults__)

    def registered_verify(folder):
        manifest,registration,parent=verify(folder)
        assert Path(registration['root'])==GEN7
        custody=original.read(GEN7/'CURSOR_RESUME.json')
        assert custody['progress']['calls']==21259 and custody['progress']['inherited_calls']==15842
        assert original.read(GEN7/'ASSAY_RELEASED.json')['status']=='RELEASED'
        assert original.read(GEN7/'START.json')['prior_cursor']==custody['progress']
        assert original.read(GEN7/'segment0000/LAUNCH.json')['first_new_call']==21260
        assert original.sha(GEN7/'FORKS.json')==registration['forks_sha256']
        required={str(GEN7/name) for name in ('CURSOR_RESUME.json','ASSAY_RELEASED.json','START.json',
            'segment0000/LAUNCH.json','FORKS.json','SOURCE_PINS.json','orch_r119_l1_gen7_post_r127.py')}
        assert required.issubset(manifest['native_pins']), 'actual_custody_pins_required'
        assert original.read(parent/'PLAN.json')['cohort_id']=='R119_EXPERIENCE_C3_B003'
        ready=original.read(folder/'PRE_PUBLICATION.json')
        assert ready['cpu_passed'] and ready['builder_line'].startswith('[Builder]')
        assert ready['manifest_sha256']==original.sha(folder/'MANIFEST.json')
        return manifest,registration,parent

    def registered_gate(registration,review,row,task):
        candidate_binding(registration,review,row)
        original_gate(registration,review,row,task)

    context.update(verify=registered_verify,source_gate=registered_gate)
    exec(compile(publication_source(inspect.getsource(original.prepare)),__file__,'exec'),context)
    return context


def handoff_source(source, modernize):
    return replace_exact(modernize(source),{
        "assert cohort_for(metadata['update'], config['activation_update']) == 'C3', 'existing_C3_continuation_only'":
            "assert metadata['update'] <= config['activation_update'], 'common_future_boundary_already_passed'",
    })


def consumer_context(root):
    original=load(root,'orch_r119_l1_c3_consumer')
    frozen=original.dependencies(root)
    verify_sources(root,frozen.trainer)
    modern=load(root,'orch_r119_l1_c3_scanned_resume')
    context=dict(original.__dict__,__file__=str(Path(__file__).resolve()),cohort_for=cohort_for)
    configuration=FunctionType(original.configuration.__code__,context,'configuration',original.configuration.__defaults__)

    def bound_configuration(folder):
        dependency,config=configuration(folder)
        assert config['experiment']=='R132_GEN7_C4' and set(config['cohorts'])=={'C3','R132_C4'}
        assert config['activation_update']==config['global_feed_boundary'], 'one_GLOBAL_boundary'
        old=dependency.trainer.read(Path(config['cohorts']['C3']['path'])/'PREPARED.json')
        new=dependency.trainer.read(Path(config['cohorts']['R132_C4']['path'])/'PREPARED.json')
        assert old['counts']['eligible']==22 and 22<new['counts']['eligible']<=25
        assert old['fixed32_suite_sha256']==new['fixed32_suite_sha256']
        assert old['held_behavior_sha256']==new['held_behavior_sha256']
        assert config['slots']=={'FULL':0,'CONTROL':1}
        return dependency,config

    context['configuration']=bound_configuration
    for name in ('stage_namespace','supervise'):
        context[name]=FunctionType(getattr(original,name).__code__,context,name,getattr(original,name).__defaults__)
    exec(compile(handoff_source(inspect.getsource(original.handoff),modern.modern_handoff_source),__file__,'exec'),context)
    return context


def activate(root, arm):
    context=consumer_context(root)
    frozen,config=context['configuration'](root)
    receipt=frozen.trainer.read(root/'PRE_GPU.json')
    assert receipt['cpu_passed'] and receipt['builder_line'].startswith('[Builder]')
    assert receipt['main_notice_sent_before_activation'] is True
    assert receipt['campaign_sha256']==frozen.trainer.sha(root/'CAMPAIGN.json')
    context['handoff'](root,arm)
    from gpu import orch_combined_l1_continual_run as admission
    enrichment=load(root,'orch_r119_l1_c3_scan')
    admission.scan=lambda index,service:enrichment.scan_process(root,index,service)
    context['supervise'](root,arm)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('check-feed','prepare','check-consumer','activate','train','readout'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--arm',choices=('FULL','CONTROL'))
    parser.add_argument('--segment',type=int)
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--condition',choices=('ON','OFF'))
    options=parser.parse_args()
    if options.action in ('check-feed','prepare'):
        context=publication_context(options.root)
        if options.action=='prepare':
            context['prepare'](options.root)
        else:
            context['verify'](options.root)
            print(json.dumps(dict(status='CPU_PROVENANCE_PASS',registration=REGISTRATION,max_reviews=3)))
    elif options.action=='check-consumer':
        context=consumer_context(options.root)
        frozen,config=context['configuration'](options.root)
        print(json.dumps(dict(status='CPU_PROVENANCE_PASS',global_boundary=config['activation_update'],slots=config['slots'])))
    elif options.action=='activate':
        activate(options.root,options.arm)
    else:
        context=consumer_context(options.root)
        frozen,config,stage,bound,native=context['stage_namespace'](options.root,options.arm,options.segment,options.resume)
        if options.action=='train':native['train'](options.arm,options.segment,options.resume)
        else:native['readout'](options.arm,options.condition,options.segment,options.resume)


if __name__=='__main__':
    main()
