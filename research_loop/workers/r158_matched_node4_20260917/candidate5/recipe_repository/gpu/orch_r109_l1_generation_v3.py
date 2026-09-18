"""Safe immutable generation-only V3 continuation on the eight remaining lanes."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from types import FunctionType

try:
    from organism_v6 import orch_r109_l1_generation_policy as policy
except ImportError:
    import orch_r109_l1_generation_policy as policy


ORIGIN = Path('/localhome/local-rohing/orch_r109_l1_20260915')
ROOT = ORIGIN / 'generation_v3'
END = 1789491360
CUTOFF = END-300
LANES = {'node1':list(range(7)), 'node2':[4]}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def supplement_inventory():
    from gpu.orch_math_rich_source import verify_archive
    actual = {str(path.relative_to(ROOT/'source')):sha(path) for path in (ROOT/'source').rglob('*.py')}
    assert verify_archive(ROOT/'source.tar', ROOT/'source') == len(actual)
    return actual


def verify():
    from gpu import orch_r109_l1_run as original
    plan = read(ROOT/'PLAN.json')
    old = original.verify()
    assert sha(ORIGIN/'PLAN.json') == plan['original_plan_sha256']
    assert old['source_archive_sha256'] == plan['original_source_archive_sha256']
    assert plan['lifetime']['hard_deadline_unix'] == END and plan['lifetime']['native_deadline_unix'] == CUTOFF
    assert plan['lanes'] == LANES[plan['node']]
    assert sha(__file__) == plan['runner_sha256'] and sha(policy.__file__) == plan['policy_sha256']
    assert sha(ROOT/'source.tar') == plan['supplement_archive_sha256']
    assert supplement_inventory() == plan['supplement_python_files']
    receipt = read(ROOT/'PRE_GPU.json')
    assert receipt['cpu_passed'] is True and receipt['builder_line'].startswith('[Builder]')
    assert receipt['plan_sha256'] == sha(ROOT/'PLAN.json')
    return plan


def prepare(node):
    from gpu import orch_r109_l1_run as original
    old = original.verify()
    assert old['node'] == node and not (ROOT/'PLAN.json').exists()
    plan = dict(old, generation_version=policy.VERSION, lanes=LANES[node],
        original_plan_sha256=sha(ORIGIN/'PLAN.json'), original_source_archive_sha256=old['source_archive_sha256'],
        runner_sha256=sha(__file__), policy_sha256=sha(policy.__file__), supplement_archive_sha256=sha(ROOT/'source.tar'),
        supplement_python_files=supplement_inventory(),
        new_segment_call_allowance_per_lane=16384, call_ids_continue_old_counter=True,
        prior_call_allowance_unchanged=8192, per_call_output_cap=8192,
        two_call_opportunity_budget_max=16384, new_gpu_hours=0,
        generation_seed_unchanged=old['original_child_state'],
        measurement='PER_RESPONSE_FIRST_ANSWER_THEN_64_CHILD_TOKENS_4GRAM_NOVELTY_GE0.8_AND_FINAL_WITHIN_BUDGET_CAP_HITS_FAIL',
        prompted_opportunities_not_spontaneous=True, functional_admission=False, prepared_unix=time.time())
    original.write(ROOT/'PLAN.json',plan)
    print(json.dumps(dict(node=node,plan_sha256=sha(ROOT/'PLAN.json'),runner_sha256=plan['runner_sha256'],
        policy_sha256=plan['policy_sha256'],supplement_archive_sha256=plan['supplement_archive_sha256'],
        lanes=plan['lanes'],original_hard_end_unix=END,original_native_cutoff_unix=CUTOFF)))


def complete_boundary(directory):
    progress = read(directory/'PROGRESS.json')
    count = progress['calls']
    return (not (directory/f'INTENT_{count+1:06d}.json').exists()
        and (directory/f'CALL_{count:06d}.json').exists()
        and not list(directory.glob('FAILED_*.json'))), progress


def stopped(pid):
    fields = (Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
    return fields[0] in ('T','t')


def wait_stopped(pid):
    deadline = time.monotonic()+2
    while not stopped(pid):
        if time.monotonic() >= deadline:
            raise TimeoutError('owned_stop_ack_timeout')
        time.sleep(.0005)


def release(index):
    from gpu import orch_r109_l1_run as original
    from gpu.orch_r109_l1_ops import identity
    plan = verify()
    assert index in plan['lanes']
    launch = read(ORIGIN/f'generation_{index}_LAUNCH.json')
    expected = launch['identity']
    assert launch['module'] == 'gpu.orch_r109_l1_run' and launch['arguments'] == ['generate','--index',str(index)]
    assert launch['source_archive_sha256'] == plan['original_source_archive_sha256']
    assert identity(expected['pid']) == expected and expected['uid'] == os.getuid()
    descriptor = os.pidfd_open(expected['pid'])
    directory = ORIGIN/'generation'/f'gpu{index}'
    paused = False
    try:
        while time.time() < CUTOFF-600:
            assert identity(expected['pid']) == expected
            candidate,progress = complete_boundary(directory)
            if candidate:
                signal.pidfd_send_signal(descriptor,signal.SIGSTOP)
                paused = True
                wait_stopped(expected['pid'])
                candidate,after = complete_boundary(directory)
                if candidate and after == progress:
                    last = read(directory/f'CALL_{progress["calls"]:06d}.json')
                    episode = directory/f'EPISODE_{progress["batch"]:03d}_{progress["position"]:02d}.json'
                    assert last['family'] != 'route' or episode.exists()
                    calls = sorted(directory.glob('CALL_*.json'))
                    intents = sorted(directory.glob('INTENT_*.json'))
                    assert len(calls) == len(intents) == progress['calls']
                    original.write(ROOT/f'RELEASE_{index}.json',dict(identity=expected,index=index,
                        node=plan['node'],progress=progress,capture_hashes={path.name:sha(path) for path in calls},
                        original_launch_sha256=sha(ORIGIN/f'generation_{index}_LAUNCH.json'),
                        old_source_untouched=True,all_task_pair_episode_outputs_preserved=True,
                        stop_acknowledged_before_boundary_recheck=True,
                        original_deadline_unix=END,observed_unix=time.time()))
                    signal.pidfd_send_signal(descriptor,signal.SIGTERM)
                    signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                    paused = False
                    return
                signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                paused = False
            time.sleep(.0005)
        raise TimeoutError('no_safe_boundary_before_original_cutoff')
    finally:
        if paused:
            try:signal.pidfd_send_signal(descriptor,signal.SIGCONT)
            except ProcessLookupError:pass
        os.close(descriptor)


def messages(task,condition,previous=None):
    from organism_v6 import orch_rich_hot_node2_supply as supply
    result = supply.messages(task,'ORIGINAL_RICH')
    result[0] = dict(role='system',content=policy.guidance(condition))
    if task['family'] == 'math':
        result[-1]['content'] += '\nFinish with FINAL: and the numeric answer.'
    if previous is not None:
        result += [dict(role='assistant',content=previous),dict(role='user',content=policy.opportunity())]
    return result


def measurement(response,family,tokenizer,cap):
    ids = response['token_ids'][:-1] if response['terminal'] else response['token_ids']
    offset = policy.first_answer_end(response['raw'],family)
    marker = None
    alignment = None
    if offset is not None:
        encoded = tokenizer(response['raw'],add_special_tokens=False,return_offsets_mapping=True)
        alignment = encoded['input_ids'] == ids
        if alignment:
            marker = next((index+1 for index,span in enumerate(encoded['offset_mapping']) if span[1] >= offset),None)
    result = policy.measure(ids,marker,final=policy.final_present(response['raw'],family),terminal=response['terminal'],
        cap_hit=response['truncated'] or len(response['token_ids']) >= cap,total_generated=len(response['token_ids']),budget=cap)
    return dict(result,native_marker_alignment_verified=alignment,measurement_unit='SINGLE_NATIVE_RESPONSE',
        missing_code_fence_not_substituted_with_json_marker=True)


def generate(index):
    from gpu import orch_r109_l1_train as trainer
    from gpu.orch_rich_hot_node2_exhaustion_v3 import Engine
    from organism_v6 import orch_rich_hot_node2_floor98 as roster
    from organism_v6 import orch_rich_hot_node2_supply as environment
    plan = verify()
    assert index in plan['lanes'] and os.environ['CUDA_VISIBLE_DEVICES'] == plan['uuid_by_index'][index]
    condition = trainer.policy.CONDITIONS[trainer.policy.allocation(plan['node'],index)%len(trainer.policy.CONDITIONS)]
    checkpoint = ORIGIN/'input/checkpoint'
    commit = trainer.storage.verify_checkpoint(checkpoint)['metadata']
    adapter = trainer.native.bridge.AdapterIdentity.from_document(dict(commit['adapter'],path=str(checkpoint/'adapter')))
    assert adapter.state_sha256 == plan['generation_seed_unchanged']
    binding = trainer.native.bridge.StageBinding(f'R109_GEN_V3_{plan["node"]}_{index}',trainer.native.bridge.ARMS[1],
        0,'sealed_readout',adapter,False,True,sha(ROOT/'PLAN.json'))
    check = lambda label:trainer.previous.common.check_deadline(plan['lifetime'],label)
    loaded = trainer.native.load_stage(binding,model_dir=plan['model_dir'],device='cuda:0',gpu_uuid=plan['uuid_by_index'][index],
        context=trainer.native.StageContext(),check=check,engine_factory=Engine)
    directory = ROOT/f'gpu{index}'
    directory.mkdir(exist_ok=False)
    inherited = read(ROOT/f'RELEASE_{index}.json')['progress']
    start_calls = count = inherited['calls']
    batch,position = inherited['batch'],inherited['position']+2
    trainer.write(directory/'LOADED.json',dict(adapter=adapter.document(),condition=condition,process=loaded.process,
        inherited_call_count=start_calls,new_segment_allowance=16384,prompt_policy_sha256=plan['policy_sha256'],observed_unix=time.time()))
    document = read(ORIGIN/'TASKS.json')
    assert sha(ORIGIN/'TASKS.json') == read(ORIGIN/'GENERATION_READY.json')['tasks_sha256']
    while time.time() < CUTOFF and count-start_calls < 16384-32:
        if position >= roster.TASKS_PER_BATCH:
            batch,position = batch+1,index%2
        task = roster.task_at(document,batch%roster.MAX_BATCHES,position)
        task = dict(task,id=f'R109-V3-{plan["node"]}-{index}-B{batch:04d}-P{position:02d}',source_reuse=True)
        def call(stage,prefix):
            nonlocal count
            check('V3_native_call')
            assert count-start_calls < 16384
            cap = min(8192,32768-len(loaded.engine.prompt_tokens(prefix)))
            assert cap > 0
            count += 1
            row = dict(task_id=task['id'],source_task_id=task['source_task_id'],family=task['family'],stage=stage,
                condition=condition,source_label='R109_SELF_GENERATED_FUNCTIONAL',split='TRAIN',messages=prefix,
                source_archive_sha256=plan['supplement_archive_sha256'],original_environment_archive_sha256=plan['original_source_archive_sha256'],
                source_state_sha256=adapter.state_sha256,prompt_policy_sha256=plan['policy_sha256'],
                source_tasks_sha256=sha(ORIGIN/'TASKS.json'),started_unix=time.time(),max_new_tokens=cap,
                parent_calls=0,trainingAllowed=False,semantic_status='UNREVIEWED',cumulative_call=count,new_segment_call=count-start_calls)
            trainer.write(directory/f'INTENT_{count:06d}.json',row)
            try:
                response = loaded.engine.generate(prefix,max_new_tokens=cap)
                row.update(response=response,outcome=roster.outcome(task,response),finished_unix=time.time(),
                    descriptive_response_metrics=measurement(response,task['family'],loaded.engine.tokenizer,cap))
                trainer.write(directory/f'CALL_{count:06d}.json',row)
                return response
            except BaseException as failure:
                trainer.write(directory/f'FAILED_{count:06d}.json',dict(row,error_type=type(failure).__name__,finished_unix=time.time()))
                raise
        if task['family'] == 'route':
            world = task['payload'];runtime = environment.runtime(world['master'])
            collection = runtime['collect_world'](world,lambda prefix:call('exposure',prefix))
            runtime['replay_collection'](collection)
            store = {row['edge']['event']:row['event']['raw'] for row in collection['records'] if row['accepted']}
            episode = FunctionType(environment.route.episode.__code__,dict(environment.route.__dict__,GUIDANCE=policy.guidance(condition)),
                'episode',environment.route.episode.__defaults__)
            tasks = [task for ordinal,task in enumerate(runtime['build_tasks'](world)) if ordinal in (0,2)]
            episodes = [episode(world,task,lambda prefix:call('goal',prefix),store) for task in tasks]
            trainer.write(directory/f'EPISODE_{batch:04d}_{position:02d}.json',dict(task=task,collection=collection,episodes=episodes,
                semantic_status='UNREVIEWED',revisitation_not_assumed=True))
        else:
            response = call('draft',messages(task,condition))
            if condition != 'ORDINARY_CONTROL':
                call('optional_opportunity',messages(task,condition,response['raw']))
        trainer.write(directory/'PROGRESS.json',dict(calls=count,new_segment_calls=count-start_calls,inherited_calls=start_calls,
            batch=batch,position=position,finished_unix=time.time(),condition=condition,semantic_admissions=0))
        position += 2
    loaded.verify_unchanged()
    trainer.write(directory/'COMPLETE.json',dict(calls=count,new_segment_calls=count-start_calls,
        original_hard_end_unix=END,finished_unix=time.time()))


def supervise(index):
    from gpu import orch_r109_l1_run as original
    from gpu.orch_r109_l1_ops import identity
    plan = verify()
    assert index in plan['lanes']
    release(index)
    while time.time() < CUTOFF-600:
        scan = original.scan(plan['node'],index)
        original.write(ROOT/'admissions'/f'{index}_{time.time_ns()}.json',scan)
        if scan['clear']:
            assert scan['scanner_euid'] == 0 and scan['gpu']['uuid'] == plan['uuid_by_index'][index]
            break
        time.sleep(2)
    else:
        raise TimeoutError('original_admission_deadline')
    with (ROOT/f'GENERATOR_{index}.log').open('x') as log:
        child = subprocess.Popen([original.PYTHON,'-B','-u',str(Path(__file__)),'generate','--index',str(index)],
            cwd=ORIGIN/'source',stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,PYTHONPATH=str(Path(__file__).parent)+':'+str(ORIGIN/'source'),
                CUDA_VISIBLE_DEVICES=plan['uuid_by_index'][index],HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false'))
    expected = identity(child.pid)
    original.write(ROOT/f'LAUNCH_{index}.json',dict(identity=expected,index=index,node=plan['node'],started_unix=time.time(),
        source_archive_sha256=plan['supplement_archive_sha256'],hard_deadline_unix=END))
    try:
        while child.poll() is None:
            original.write(ROOT/f'HEARTBEAT_{index}.json',dict(identity=expected,index=index,
                phase='generation',observed_unix=time.time(),hard_deadline_unix=END))
            if time.time() >= END-45:
                original.stop(child,expected,'V3_FIXED_LIFETIME')
                break
            time.sleep(5)
        original.write(ROOT/f'EXIT_{index}.json',dict(identity=expected,returncode=child.wait(),observed_unix=time.time()))
        assert child.returncode == 0, 'V3_GENERATOR_NONZERO_EXIT'
    finally:
        original.stop(child,expected,'V3_FIXED_LIFETIME_SUPERVISOR_EXIT')


def observe():
    from gpu.orch_r109_l1_ops import identity
    plan = read(ROOT/'PLAN.json')
    report = dict(node=plan['node'],observed_unix=time.time(),hard_deadline_unix=END,
        plan_sha256=sha(ROOT/'PLAN.json'),policy_sha256=plan['policy_sha256'],lanes=[],native_samples=[],
        raw_output=False,semantic_admissions=0,descriptive_metrics_not_functional_admission=True)
    samples = []
    for index in plan['lanes']:
        lane = dict(index=index,phase='awaiting_safe_boundary',new_completed_calls=0)
        for name in ('RELEASE','LAUNCH','HEARTBEAT','EXIT','FAILURE'):
            path = ROOT/f'{name}_{index}.json'
            if path.exists():
                record = read(path)
                lane[name.lower()] = dict(path=str(path),sha256=sha(path),**{key:record[key] for key in
                    ('identity','observed_unix','returncode','error_type') if key in record})
                if name == 'RELEASE':lane['inherited_calls'] = record['progress']['calls']
                if name == 'LAUNCH':
                    try:
                        lane['alive'] = identity(record['identity']['pid']) == record['identity']
                    except FileNotFoundError:lane['alive'] = False
        directory = ROOT/f'gpu{index}'
        lane['phase'] = 'generation' if (directory/'LOADED.json').exists() else 'loading' if 'launch' in lane else lane['phase']
        if 'exit' in lane or 'failure' in lane:lane['phase'] = 'terminal'
        metrics = dict(denominator=0,persistence=0,cap_hits=0,missing_markers=0,alignment_failures=0)
        recent = 0
        for path in sorted(directory.glob('CALL_*.json')):
            row = read(path)
            value = row['descriptive_response_metrics']
            metrics['denominator'] += 1
            metrics['persistence'] += value['persistence']
            metrics['cap_hits'] += value['cap_hit']
            metrics['missing_markers'] += not value['marker_found']
            metrics['alignment_failures'] += value['native_marker_alignment_verified'] is False
            recent += row['finished_unix'] >= report['observed_unix']-3600
            samples.append(dict(index=index,path=str(path),sha256=sha(path),family=row['family'],stage=row['stage'],
                source_task_id=row['source_task_id'],source_label=row['source_label'],semantic_status=row['semantic_status'],
                finished_unix=row['finished_unix'],metrics=value))
        lane.update(metrics=metrics,new_completed_calls=metrics['denominator'],last3600_calls=recent,
            cumulative_completed_calls=lane.get('inherited_calls',0)+metrics['denominator'])
        report['lanes'].append(lane)
    report['native_samples'] = sorted(samples,key=lambda row:row['finished_unix'])[-6:]
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','supervise','generate','observe'])
    parser.add_argument('--node',choices=list(LANES))
    parser.add_argument('--index',type=int)
    options = parser.parse_args()
    if options.action == 'prepare':prepare(options.node)
    elif options.action == 'observe':observe()
    elif options.action == 'supervise':
        try:supervise(options.index)
        except BaseException as failure:
            from gpu import orch_r109_l1_run as original
            original.write(ROOT/f'FAILURE_{options.index}.json',dict(error_type=type(failure).__name__,observed_unix=time.time()))
            raise
    else:generate(options.index)
