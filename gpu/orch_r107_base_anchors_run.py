"""Finite genuine-BASE TRAIN anchors on assigned A1000; raw remains node-local."""

import argparse
from collections import Counter
import hashlib
import math
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r107_capability_base as common
from gpu import orch_r107_continual_capability_run as ownership
from gpu import orch_r107_continual_capability_admit as rescan
from gpu.orch_rich_intensity_screen import Engine
from organism_v6 import orch_combined_l1_base as base
from organism_v6 import orch_r107_base_anchors as policy


SOURCE_ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = Path('/localhome/local-rohing/orch_r107_continual_capability_20260915_attempt1')
GPU_UUID = ownership.GPU_UUID
REQUIRED_SOURCES = (
    'organism_v6/orch_r107_base_anchors.py', 'gpu/orch_r107_base_anchors_run.py',
    'tests/test_orch_r107_base_anchors.py', 'organism_v6/orch_code_bounded.py',
    'organism_v6/orch_r107_capability.py', 'organism_v6/orch_combined_l1_base.py',
    'gpu/orch_r107_capability_base.py', 'gpu/orch_r107_continual_capability_run.py',
    'gpu/orch_r107_continual_capability_admit.py', 'gpu/orch_rich_intensity_screen.py',
    'gpu/astra_experienced_event_microloop.py', 'gpu/orch_rich_hot_a100_minor_scan.py',
    'gpu/orch_rich_hot_a100_scan.py', 'gpu/orch_combined_l1_continual_run.py',
)
read, sha, write = ownership.read, ownership.sha, ownership.write


def require_host():
    policy.require(ownership.host_identity() == ownership.continual.combined.HOST_SHA, 'pinned_host_required')


def validate(plan, now):
    policy.require(plan['schema'] == policy.SCHEMA and plan['base_sha256'] == policy.BASE_SHA
        and plan['adapter'] is None, 'genuine_base_only')
    policy.require(plan['gpu_uuid'] == GPU_UUID and plan['physical_index'] == 0, 'allocated_a1000_only')
    for name, value in (('call_cap', 64), ('max_new_tokens', 512), ('training_updates', 0), ('parent_calls', 0)):
        policy.require(type(plan[name]) is int and plan[name] == value, 'fixed_' + name)
    policy.require(plan['parent_access'] is False and plan['automatic_fit'] is False, 'no_parent_or_auto_fit')
    policy.require(plan['lifetime_started_unix'] <= now < plan['native_deadline_unix'] < plan['hard_deadline_unix']
        <= plan['lease_end_unix'] - 21600 and plan['hard_deadline_unix'] - plan['lifetime_started_unix'] <= 1800
        and plan['gpu_hours_cap'] == 0.5, 'single_bounded_lifetime')
    policy.require(plan['suite_sha256'] == policy.digest(policy.tasks()) and
        plan['exclusions'] == policy.exclusions(policy.tasks()), 'fixed_train_cohort_exclusions')
    policy.require(set(REQUIRED_SOURCES) <= set(plan['sources']), 'bound_runtime_sources')
    for relative, expected in plan['sources'].items():
        path = Path(relative)
        policy.require(not path.is_absolute() and '..' not in path.parts
            and (SOURCE_ROOT / path).resolve().is_relative_to(SOURCE_ROOT), 'source_path_escape')
        policy.require(sha(SOURCE_ROOT / path) == expected, 'source_hash_drift')
    return plan


def encoded(tokenizer, context):
    rows = []
    for task in policy.tasks():
        tokens = tokenizer.apply_chat_template(policy.messages(task), tokenize=True,
            add_generation_prompt=True, return_dict=False)
        policy.require(0 < len(tokens) <= 4096 and len(tokens) + 512 <= context, 'untruncated_context_required')
        rows.append(dict(task_id=task['id'], prompt_tokens=len(tokens), encoded_sha256=policy.digest(tokens)))
    return rows


def prepare(root, cpu_log):
    require_host()
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not (root/'PLAN.json').exists(), 'fresh_cpu_prepare')
    policy.require(Path(cpu_log).is_file() and 'passed' in Path(cpu_log).read_text(), 'cpu_tests_required')
    previous = read(PREDECESSOR/'PLAN.json')
    metadata, context = common.metadata(previous['model_dir'])
    tokenizer = common.native.source.native.load_local_tokenizer(previous['model_dir'])
    tokenization = encoded(tokenizer, context)
    suite = policy.tasks()
    exclusions = policy.exclusions(suite)
    started = time.time()
    plan = dict(schema=policy.SCHEMA, base_sha256=policy.BASE_SHA, adapter=None,
        model_dir=previous['model_dir'], physical_index=0, gpu_uuid=GPU_UUID,
        call_cap=64, max_new_tokens=512, training_updates=0, parent_calls=0,
        parent_access=False, automatic_fit=False, suite_sha256=policy.digest(suite), exclusions=exclusions,
        lifetime_started_unix=started, native_deadline_unix=started + 1740,
        hard_deadline_unix=started + 1800, lease_end_unix=ownership.continual.LEASE_END, gpu_hours_cap=0.5,
        sources={str(path.relative_to(SOURCE_ROOT)): sha(path) for folder in ('gpu','organism_v6','tests')
                 for path in sorted((SOURCE_ROOT/folder).rglob('*.py'))})
    validate(plan, time.time())
    write(root/'PLAN.json', plan)
    write(root/'TASKS_PRIVATE.json', suite)
    write(root/'RESERVATIONS.json', dict(call_cap=64, retries=0, plan_sha256=sha(root/'PLAN.json'),
        cells=[dict(position=position, task_id=task['id'], family=task['family'], prompt_sha256=task['prompt_sha256'],
                    content_sha256=task['content_sha256'], max_new_tokens=512) for position,task in enumerate(suite)]))
    ready = dict(status='PASS', plan_sha256=sha(root/'PLAN.json'), suite_sha256=plan['suite_sha256'],
        reservations_sha256=sha(root/'RESERVATIONS.json'), task_file_sha256=sha(root/'TASKS_PRIVATE.json'),
        cpu_log_sha256=sha(cpu_log), tokenization=tokenization, model_metadata=metadata, context=context,
        encoded_tasks=64, native_calls=0, parent_calls=0, training_updates=0, prepared_unix=time.time())
    write(root/'READY.json', ready)
    return ready


def ready_check(root, plan):
    ready, publication = read(root/'READY.json'), read(root/'PUBLICATION.json')
    policy.require(ready['status'] == 'PASS' and ready['plan_sha256'] == sha(root/'PLAN.json')
        and publication['ready_sha256'] == sha(root/'READY.json') and publication['own_cpu_tests_passed'] is True
        and publication['dated_builder_publication'] and publication['board_allocation'], 'bound_publication_required')
    policy.require(ready['reservations_sha256'] == sha(root/'RESERVATIONS.json')
        and ready['task_file_sha256'] == sha(root/'TASKS_PRIVATE.json'), 'fixed_call_and_task_inventory')
    metadata, context = common.metadata(plan['model_dir'])
    policy.require(metadata == ready['model_metadata'] and context == ready['context'], 'frozen_metadata_drift')
    return ready


def natural_release():
    policy.require((PREDECESSOR/'readout/COMPLETE.json').is_file(), 'predecessor_natural_completion_required')
    process = read(PREDECESSOR/'readout/REQUEST.json')['process']
    path = Path('/proc')/str(process[1])/'stat'
    if path.exists():
        policy.require(path.read_text().rsplit(')',1)[1].split()[19] != str(process[2]), 'predecessor_process_still_alive')


def launch(root):
    require_host()
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_guard_cvd_empty')
    plan = validate(read(root/'PLAN.json'), time.time())
    ready_check(root, plan)
    natural_release()
    (root/'LAUNCH_ONCE').mkdir(exist_ok=False)
    cutoff = min(time.time()+60, plan['native_deadline_unix'])
    report = None
    for attempt in range(30):
        policy.require(time.time() < cutoff, 'admission_window_exhausted')
        report = ownership.continual.scan(0, ownership.continual.ROOT/'SERVICE_IDENTITY.json')
        write(root/'ADMISSIONS'/f'{attempt:03d}.json', report)
        if report['clear'] is True:
            ownership.validate_scan(report, time.time())
            break
        policy.require(rescan.transient(report), 'blocked_gpu_no_waiver')
        time.sleep(1)
    policy.require(report is not None and report['clear'] is True, 'strict_clear_required')
    write(root/'ADMISSION.json', dict(plan_sha256=sha(root/'PLAN.json'), snapshot=report))
    seconds = math.floor(plan['hard_deadline_unix'] - time.time() - 5)
    policy.require(seconds > 0, 'lifetime_exhausted')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(SOURCE_ROOT))
    command = ['timeout','--signal=TERM','--kill-after=5s',str(seconds)+'s', ownership.continual.PYTHON,
               '-B','-m','gpu.orch_r107_base_anchors_run','run','--root',str(root)]
    with (root/'native.log').open('x') as log:
        child = subprocess.Popen(command,cwd=SOURCE_ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    receipt = dict(status='LAUNCHED', timeout_identity=ownership.continual.minor_scan.pinned.identity(Path('/proc')/str(child.pid)),
        admission_sha256=sha(root/'ADMISSION.json'), plan_sha256=sha(root/'PLAN.json'), launched_unix=time.time(),
        hard_deadline_unix=plan['hard_deadline_unix'], call_cap=64, parent_calls=0, training_updates=0)
    write(root/'LAUNCH.json',receipt)
    return receipt


def publish_anchors(root, calls, verified):
    suite, anchors, summaries = policy.tasks(), [], []
    for position, task in enumerate(suite):
        summary = dict(position=position,task_id=task['id'],family=task['family'],status='MISSING',
                       verified_anchor=False,category='missing',generated_tokens=0,content_tokens=0)
        if position < len(calls):
            call = calls[position]
            path = root/'readout'/f'CALL_{position:03d}.json'
            summary.update(status=call['status'],call_sha256=sha(path),call_path=str(path))
            if 'outcome' in call:
                summary.update(call['outcome'])
            if call['status'] != 'COMPLETE':
                summary.update(verified_anchor=False, category='execution_error')
            if verified and summary['verified_anchor']:
                anchors.append(dict(task_id=task['id'],family=task['family'],split='TRAIN',cohort=policy.COHORT,
                    label='ORDINARY_COMPETENT_BASE_TRAIN_ANCHOR',admitted_as_anchor=True,trainingAllowed=False,
                    fit_ready=False,automatic_fit=False,semantic_richness='NOT_CLAIMED',
                    messages=policy.messages(task)+[dict(role='assistant',content=call['response']['raw'])],
                    target=call['response']['raw'],target_sha256=hashlib.sha256(call['response']['raw'].encode()).hexdigest(),
                    task_content_sha256=task['content_sha256'],prompt_sha256=task['prompt_sha256'],
                    runtime_prefix=str(root),source_actor=dict(base_sha256=policy.BASE_SHA,adapter=None,
                        generator_sha256=sha(__file__),policy_sha256=sha(policy.__file__)),
                    call_path=str(path),call_sha256=sha(path),machine_outcome=call['outcome']['machine']))
        summaries.append(summary)
    write(root/'ANCHOR_ROWS.json',anchors)
    counts = Counter(row['family'] for row in anchors)
    result = dict(schema=policy.SCHEMA,status='VERIFIED_ANCHOR_MANIFEST_READY' if verified else 'WITHHELD_UNVERIFIED_EXECUTION',
        source_kind='GENUINE_BASE_ORDINARY_TRAIN_ANCHORS',runtime_prefix=str(root),base_sha256=policy.BASE_SHA,adapter=None,
        suite_sha256=policy.digest(suite),plan_sha256=sha(root/'PLAN.json'),before_after_verified=verified,
        anchors_path=str(root/'ANCHOR_ROWS.json'),anchors_sha256=sha(root/'ANCHOR_ROWS.json'),
        reserved_calls=len(calls),completed_calls=sum(row['status']=='COMPLETE' for row in calls),
        verified_anchors=len(anchors),families={family:dict(expected_tasks=16,verified_anchors=counts[family],
            target_minimum=4,shortfall=max(0,4-counts[family])) for family in policy.FAMILIES},
        rows=summaries,automatic_fit=False,trainingAllowed=False,fit_ready=False,
        parent_calls=0,training_updates=0,teacher_targets=False,l2=False,held=False,
        selector_handoff='Hubble: separate source registration required; only this verified manifest, never capability outputs.',
        finished_unix=time.time())
    write(root/'ANCHOR_MANIFEST.json',result)
    return result


def run(root):
    require_host()
    plan = validate(read(root/'PLAN.json'),time.time())
    ready = ready_check(root,plan)
    admission = read(root/'ADMISSION.json')
    policy.require(admission['plan_sha256']==sha(root/'PLAN.json'),'admission_plan_drift')
    ownership.validate_scan(admission['snapshot'],time.time())
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES')==GPU_UUID and
        os.environ.get('HF_HUB_OFFLINE')==os.environ.get('TRANSFORMERS_OFFLINE')=='1','offline_uuid_environment')
    tokenizer=common.native.source.native.load_local_tokenizer(plan['model_dir'])
    policy.require(encoded(tokenizer,ready['context'])==ready['tokenization'],'encoded_prompt_drift')
    output=root/'readout'
    output.mkdir(exist_ok=False)
    write(output/'REQUEST.json',dict(plan_sha256=sha(root/'PLAN.json'),process=common.native.process_identity(),
        started_unix=time.time(),base_sha256=policy.BASE_SHA,adapter=None,parent_calls=0,training_updates=0))
    calls,engine,failure=[],None,None
    before,after,finalizing=False,False,False
    def check(label):
        deadline=plan['hard_deadline_unix'] if finalizing and label=='base_hash' else plan['native_deadline_unix']
        if time.time()>=deadline:
            raise TimeoutError('fixed_anchor_deadline:'+label)
    try:
        check('load')
        engine=Engine(base.options(plan['model_dir'],GPU_UUID),tokenizer,check=check)
        write(output/'BEFORE.json',common.verify_frozen(engine))
        before=True
        for position,task in enumerate(policy.tasks()):
            check('reserve')
            base.verify_no_adapter(engine.model.named_parameters(),getattr(engine.model,'peft_config',None))
            call=dict(position=position,task_id=task['id'],family=task['family'],messages=policy.messages(task),
                status='RESERVED',started_unix=time.time(),max_new_tokens=512,base_sha256=policy.BASE_SHA,adapter=None)
            path=output/f'CALL_{position:03d}.json'
            write(path,call)
            calls.append(call)
            try:
                check('dispatch')
                call['response']=engine.generate(call['messages'],max_new_tokens=512)
                call['outcome']=policy.outcome(task,call['response'],tokenizer.eos_token_id)
                policy.require(call['response']['prompt_tokens']==ready['tokenization'][position]['prompt_tokens'],'native_prompt_drift')
                call['status']='COMPLETE'
            except BaseException as error:
                call.update(status='FAILED',error_type=type(error).__name__)
                raise
            finally:
                call['finished_unix']=time.time()
                write(path,call)
    except BaseException as error:
        failure=error
    finally:
        finalizing=True
        try:
            policy.require(engine is not None,'engine_not_loaded')
            evidence=common.verify_frozen(engine)
            policy.require(common.metadata(plan['model_dir'])[0]==ready['model_metadata'],'metadata_drift_after')
            write(output/'AFTER.json',dict(evidence,status='PASS',finished_unix=time.time()))
            after=True
        except BaseException as error:
            write(output/'AFTER.json',dict(status='FAILED',error_type=type(error).__name__))
            failure=failure or error
        result=publish_anchors(root,calls,before and after and failure is None and len(calls)==64)
        write(output/('FAILED.json' if failure else 'COMPLETE.json'),dict(status='FAILED' if failure else 'COMPLETE',
            calls=len(calls),error_type=type(failure).__name__ if failure else None,
            manifest_sha256=sha(root/'ANCHOR_MANIFEST.json'),finished_unix=time.time()))
    if failure:
        raise failure
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('prepare','launch','run'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--cpu-log',type=Path)
    arguments=parser.parse_args()
    result=prepare(arguments.root,arguments.cpu_log) if arguments.phase=='prepare' else globals()[arguments.phase](arguments.root)
    print(ownership.json.dumps({key:value for key,value in result.items() if key not in ('rows','tokenization')},sort_keys=True))
