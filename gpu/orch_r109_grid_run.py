"""Node-only finite resident BASE lives; readouts use fresh parent-free contexts."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from types import SimpleNamespace

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_rich_hot_a100_minor_scan as admission
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA
from gpu.orch_rich_hot_node3_base107_engine import Engine, assert_no_adapter
from organism_v6 import orch_r109_grid as policy


ROOT = Path('/localhome/local-rohing/orch_r109_grid_20260915_attempt1')
SOURCE = Path(__file__).resolve().parents[1]
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
MODEL = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
BUNDLE = '/tmp/astra_portable_37ec_20260914_attempt1'
require = policy.require


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_name(path.name+f'.{os.getpid()}.tmp')
    with temporary.open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary,path)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def validate(root, lane, ready=True):
    spec = policy.LANES[lane]
    require(root == ROOT and root.resolve() == root and admission.pinned.host_identity() == spec['host_sha256'], 'node_root_binding')
    require(policy.START_BOUND <= time.time() < policy.NATIVE_END
        and policy.HARD_END <= spec['lease_end']-21600, 'fixed_deadline_lease')
    for name, expected in read(root/'SOURCE_SHA256.json').items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts and sha(SOURCE/relative) == expected,
            'immutable_source_snapshot')
    if ready:
        document = read(root/'READY.json')
        require(document['lane'] == lane and document['allocation'] == spec
            and document['bounds'] == policy.bounds() and document['no_adapter'] is True
            and document['principles_sha256'] == policy.PRINCIPLES_SHA, 'ready_scope')
        for name, expected in document['inputs'].items():
            require(sha(root/name) == expected, 'ready_input_drift')
        publication = read(root/'PUBLICATION.json')
        require(publication['ready_sha256'] == sha(root/'READY.json')
            and publication['dated_builder_preGPU'] and publication['own_tests_passed'] is True,
            'dated_builder_receipt')
        return document


def bind(lane):
    spec = policy.LANES[lane]
    admission.pinned.policy = SimpleNamespace(DEVICES={spec['index']: spec['uuid']},
        HOST_SHA=spec['host_sha256'], require=require,
        allocation=lambda index: require(index == spec['index'], 'allocated_lane_only'))


def scan(root, lane):
    bind(lane)
    if os.geteuid() != 0:
        command = ['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH='+str(SOURCE),'python3','-B','-m','gpu.orch_r109_grid_run','scan','--lane',lane]
        return json.loads(subprocess.check_output(command, text=True, timeout=100))
    return admission.scan(policy.LANES[lane]['index'], root/'SERVICE_IDENTITY.json')


def prepare(root, lane):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not (root/'READY.json').exists(), 'CPU_only_once')
    validate(root, lane, ready=False)
    policy.principles()
    tests = read(root/'CPU_TESTS.json')
    require(tests['passed'] is True and tests['failed'] == 0 and tests['skipped'] == 0, 'actual_CPU_tests')
    base = portable.verify_base_files(BUNDLE, MODEL, expected_manifest_sha256=BUNDLE_SHA)
    require(base['expected_base_sha256'] == policy.BASE_SHA, 'fixed_base')
    tokenizer = portable.source.native.load_local_tokenizer(MODEL)
    cohort = policy.roster()
    lengths = []
    for groups in cohort.values():
        for group in groups:
            for spec in group:
                require(len(policy.shortest_solution(spec)) <= policy.MAX_STEPS, 'solvable_prospective_task')
                messages = policy.child_messages(spec, policy.initial(spec))
                lengths.append(len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                    return_dict=False)))
    require(max(lengths)+policy.OUTPUT_CAP < policy.CONTEXT, 'initial_uncropped_context')
    release = read(root/'PRIOR_RELEASE.json')
    for entry in release['evidence']:
        require(sha(entry['path']) == entry['sha256'], 'prior_release_evidence')
    require(release['lane'] == lane and release['no_refill_confirmed'] is True, 'owner_release')
    for pid in release['prior_pids']:
        require(not Path(f'/proc/{pid}').exists(), 'prior_process_not_released')
    write(root/'COHORT_PRIVATE.json', cohort)
    (root/'parent_queue').mkdir(exist_ok=True)
    document = dict(schema=policy.SCHEMA, lane=lane, allocation=policy.LANES[lane], bounds=policy.bounds(),
        base=base, model_dir=MODEL, bundle=BUNDLE, no_adapter=True, optimizer_updates=0,
        source_sha256=sha(root/'SOURCE_SHA256.json'), initial_prompt_tokens=lengths,
        inputs={name:sha(root/name) for name in ('COHORT_PRIVATE.json','CPU_TESTS.json','PRIOR_RELEASE.json',
            'SOURCE_SHA256.json')}, prepared_unix=time.time(), native_calls=0, parent_calls=0,
        no_control_added=True, no_L2_to_L1=True, no_retained_weight_learning_claim=True)
    document['principles_sha256'] = policy.PRINCIPLES_SHA
    write(root/'READY.json', document)
    return ref(root/'READY.json')


def spend(root, kind, detail):
    cap = policy.bounds()['native_per_lane' if kind == 'NATIVE' else 'parent_per_lane']
    require(kind in ('NATIVE','PARENT'), 'budget_kind')
    with (root/'LEDGER.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        number = sum(json.loads(line)['kind'] == kind for line in stream if line.strip())+1
        require(number <= cap and time.time() < policy.NATIVE_END, 'absolute_call_budget')
        record = dict(detail, kind=kind, number=number, reserved_unix=time.time())
        stream.write(json.dumps(record, sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
        return number


def parent(root, lane, payload, proposal_ref, check):
    number = spend(root, 'PARENT', dict(task_id=payload['task_id'], cadence=payload['cadence']))
    identifier = f'P{number:04d}'
    request = dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload),
        source_proposal=proposal_ref, ready_sha256=sha(root/'READY.json'))
    queue = root/'parent_queue'
    write(queue/(identifier+'.request.json'), request)
    response_path = queue/(identifier+'.response.json')
    until = min(time.time()+180, policy.NATIVE_END)
    while not response_path.exists():
        check('parent_wait'); require(time.time() < until, 'bounded_parent_transport_no_retry'); time.sleep(1)
    result = read(response_path)
    require(result['id'] == identifier and result['request_sha256'] == policy.digest(request)
        and result['status'] == 'COMPLETE' and result['actual_model'] == policy.STRONG, 'actual_bound_parent_response')
    intervention = policy.validate_parent(payload, result['plan'])
    archive = root/'parent_transcripts'/identifier
    require(result['archive_root'] == str(archive), 'own_parent_archive')
    for name, expected in result['files'].items():
        require(Path(name).name == name and sha(archive/name) == expected, 'parent_transcript_hash')
    from gpu.orch_route_parent_campaign_providers import parse_strong
    plan, model, usage = parse_strong(read(archive/'stdout.json'))
    require(plan == result['plan'] and model == policy.STRONG and bool(usage), 'actual_parent_source_parse')
    return dict(result, intervention_class=intervention, response_ref=ref(response_path))


def episode(spec, cadence, memory, counter, generate, ask, emit, style):
    state, history = policy.initial(spec), []
    proposals, interventions, triples = counter, 0, []
    while not state['done']:
        messages = policy.child_messages(spec, state, memory, history)
        proposal = generate(spec, 'proposal', messages)
        chosen = proposal
        if spec['split'] == 'TRAIN':
            proposals += 1
            if policy.intervene(cadence, proposals, state['steps']+1):
                payload = policy.parent_payload(spec, state, proposal['response']['raw'], history, memory,
                    cadence, style, proposals)
                response = ask(payload, proposal['reference'])
                interventions += 1
                if response['plan']['speak']:
                    chosen = generate(spec, 'continuation', policy.child_messages(spec, state, memory, history,
                        dict(proposal=proposal['response']['raw'], message=response['plan']['message'])))
                triple = dict(before_observation=policy.observation(spec, state), proposal=proposal['reference'],
                    intervention=response, continuation=chosen['reference'], no_continuation=not response['plan']['speak'],
                    functional_helpfulness='UNASSESSED', hidden_state_exported=False)
                triples.append(triple)
        before = policy.observation(spec, state)
        state, reward = policy.transition(spec, state, policy.parse_action(chosen['response']['raw']))
        history.append(dict(position=before['position'], action=reward['action'], event=reward['event'],
            reward=reward['reward'], own_trace=chosen['response']['raw']))
        if triples and triples[-1]['continuation'] == chosen['reference']:
            triples[-1].update(actual_transition=reward, after_observation=policy.observation(spec, state))
        emit(f'STEPS/{state["steps"]:02d}.json', dict(state=state, history=history, triples=triples))
    result = dict(task_id=spec['id'], split=spec['split'], success=state['success'], reward=state['total_reward'],
        steps=state['steps'], collisions=state['collisions'], invalid_actions=state['invalid_actions'],
        repeated_position_visits=sum(max(0,count-1) for count in state['visits'].values()),
        repetition_is_not_semantic_branching=True, proposals=proposals-counter,
        proposal_counter=proposals, parent_calls=interventions, triples=triples,
        final_state=state, history=history,
        optimizer_updates=0, retained_learning_claim=False)
    emit('EPISODE.json', result)
    return result


def metacognition(tasks, results, memory, cadence, style, counter, generate, ask, emit):
    require(len(tasks) == len(results) == 2 and all(task['split'] == 'TRAIN' for task in tasks), 'two_episodes_before_reflection')
    system = ('Discuss your thinking and learning process, not a worked solution. Examine effort allocation, '
        'self-perception, uncertainty, persistence versus strategy change, and what your own observations '
        'support. Identify behavior to add, stop or shift, and when that would be useful. '
        'No action, branch-count template, correctness claim or copied parent lesson is requested.')
    public = [dict(task_id=task['id'], actions=result['history'], final_observation=policy.observation(task,result['final_state']))
        for task,result in zip(tasks,results)]
    messages = [dict(role='system',content=system),dict(role='user',content=json.dumps(dict(
        earlier_own_reflections=memory, current_two_episodes=public)))]
    before = generate(tasks[-1], 'metacognitive_reflection', messages)
    payload = policy.parent_payload(tasks[-1], results[-1]['final_state'], before['response']['raw'],
        public, memory, cadence, style, counter, purpose='metacognition')
    response = ask(payload,before['reference'])
    conversation = messages+[dict(role='assistant',content=before['response']['raw']),
        dict(role='user',content='Parent perspective: '+response['plan']['message']+
            '\nContinue the metacognitive conversation in your own voice. Distill a usable account of how '
            'you allocate effort, notice your limits, and learn. Retain or revise earlier own reflections '
            'only where your actual experience supports it. No target answer or action is requested.')]
    after = generate(tasks[-1],'context_distillation',conversation)
    emit('METACOGNITIVE_TRIPLE.json',dict(before=before['reference'],intervention=response,
        continuation=after['reference'],functional_helpfulness='UNASSESSED',semantic_compiler=False,
        weight_updates=0, reflection_is_context_only=True))
    return (memory+[dict(task_id=tasks[-1]['id'],trace=after['response']['raw'],source=after['reference'])])[-2:]


def run(root, lane, cadence, cycle, phase, shared_engine=None):
    ready = validate(root, lane)
    spec = policy.LANES[lane]
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == spec['uuid'] and
        ('CUDA_VISIBLE_DEVICES='+spec['uuid']).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'), 'initial_uuid')
    require(cadence in policy.CADENCES and 1 <= cycle <= policy.CYCLES and phase in ('train','held'), 'phase_scope')
    output = root/cadence/f'cycle{cycle:02d}'/phase
    output.mkdir(parents=True, exist_ok=False)
    def check(label):
        require(time.time() < policy.NATIVE_END, 'native_deadline:'+label)
    def interrupted(signum, frame):
        raise TimeoutError('owned_process_deadline')
    signal.signal(signal.SIGTERM, interrupted)
    write(output/'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), lane=lane, cadence=cadence, phase=phase))
    engine = shared_engine
    try:
        tokenizer = engine.tokenizer if engine is not None else portable.source.native.load_local_tokenizer(ready['model_dir'])
        if engine is None:
            engine = Engine(ready['model_dir'], tokenizer, device='cuda:0', check=check)
        write(output/'LOADED.json', dict(pid=os.getpid(), loaded_unix=time.time(), base_sha256=engine.loaded_base_sha256,
            no_adapter=engine.no_adapter, runtime=engine.runtime, phase=phase, native_calls=0))
        def generate(task, purpose, messages):
            cap = policy.REFLECTION_CAP if purpose in ('metacognitive_reflection','context_distillation') else policy.OUTPUT_CAP
            prompt_tokens = len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))
            require(prompt_tokens+cap <= policy.CONTEXT, 'uncropped_prompt_and_budget')
            number = spend(root, 'NATIVE', dict(task_id=task['id'], split=task['split'], cadence=cadence,
                cycle=cycle, phase=phase, purpose=purpose))
            path = root/'calls'/f'N{number:05d}.json'
            call = dict(status='STARTED', task_id=task['id'], split=task['split'], purpose=purpose,
                messages=messages, started_unix=time.time(), base_sha256=policy.BASE_SHA, adapter=None)
            write(path, call)
            try:
                call['response'] = engine.generate(messages, max_new_tokens=cap)
                call['response'].update(input_truncated=False, requested_generation_cap=cap,
                    effective_generation_cap=cap, context_limit=policy.CONTEXT)
                call['status'] = 'COMPLETE'
            except BaseException as error:
                call.update(status='FAILED', error_type=type(error).__name__)
                raise
            finally:
                call['finished_unix'] = time.time(); write(path, call)
            return dict(response=call['response'], reference=ref(path))
        memory, counter = [], 0
        if phase == 'train' and cycle > 1:
            prior = read(root/cadence/f'cycle{cycle-1:02d}'/'train/COMPLETE.json')
            memory, counter = prior['memory'], prior['proposal_counter']
        results = []
        tasks = read(root/'COHORT_PRIVATE.json')['TRAIN' if phase == 'train' else 'HELD'][cycle-1]
        for position, task in enumerate(tasks, 1):
            result = episode(task, cadence, memory, counter, generate,
                lambda payload, reference: parent(root,lane,payload,reference,check),
                lambda name,value: write(output/f'episode{position}'/name,value), spec['style'])
            counter = result['proposal_counter']
            results.append(result)
        if phase == 'train':
            memory = metacognition(tasks,results,memory,cadence,spec['style'],counter,generate,
                lambda payload,reference: parent(root,lane,payload,reference,check),lambda name,value:write(output/name,value))
        engine.verify_base(); assert_no_adapter(engine.model)
        write(output/'COMPLETE.json', dict(status='COMPLETE', finished_unix=time.time(), pid=os.getpid(),
            results=[{key:value for key,value in result.items() if key not in ('triples','history','final_state')} for result in results],
            memory=memory, proposal_counter=counter, base_sha256=policy.BASE_SHA,
            no_adapter=True, optimizer_updates=0, held_parent_free=phase == 'held', fresh_process=shared_engine is None,
            fresh_messages=True, generation_KV_reused=False, r110_resident=shared_engine is not None))
    except BaseException as error:
        write(output/'FAILED.json', dict(status='FAILED', error_type=type(error).__name__, error=str(error),
            finished_unix=time.time(), no_retry=True, all_partial_evidence_preserved=True))
        raise


def resident(root, lane):
    ready = validate(root,lane)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == policy.LANES[lane]['uuid'], 'resident_uuid')
    def check(label): require(time.time() < policy.NATIVE_END, 'resident_deadline:'+label)
    tokenizer = portable.source.native.load_local_tokenizer(ready['model_dir'])
    engine = Engine(ready['model_dir'],tokenizer,device='cuda:0',check=check)
    write(root/'RESIDENT_LOADED.json',dict(pid=os.getpid(),loaded_unix=time.time(),base_sha256=engine.loaded_base_sha256,
        no_adapter=engine.no_adapter,admission_count=1))
    for cadence in policy.LANES[lane]['order']:
        for cycle in range(1,policy.CYCLES+1):
            run(root,lane,cadence,cycle,'train',shared_engine=engine)
            run(root,lane,cadence,cycle,'held',shared_engine=engine)
    engine.verify_base()


def guard(root, lane):
    validate(root,lane)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_guard')
    (root/'GUARD_ONCE').mkdir()
    try:
        validate(root,lane)
        admitted = False
        for attempt in range(90):
            require(time.time() < policy.NATIVE_END, 'admission_deadline')
            report = scan(root,lane)
            path = root/'admissions'/f'resident_{attempt:03d}.json'
            write(path,report)
            require(report['scanner_euid'] == 0, 'privileged_visibility')
            if report['clear']:
                require(not report['blocking_reasons'] and report['gpu']['uuid'] == policy.LANES[lane]['uuid'], 'exact_clear')
                admitted = True; break
            time.sleep(2)
        require(admitted,'bounded_strict_admission')
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES=policy.LANES[lane]['uuid'],
            PYTHONPATH=str(SOURCE), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
        seconds = int(policy.HARD_END-time.time()-5)
        require(seconds > 0,'hard_deadline')
        command = ['timeout','--signal=TERM','--kill-after=5s',str(seconds)+'s',PYTHON,'-B','-m',
            'gpu.orch_r109_grid_run','resident','--lane',lane]
        with (root/'resident.log').open('x') as log:
            child = subprocess.Popen(command,cwd=SOURCE,env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(root/'launches/resident.json',dict(pid=child.pid,admission=ref(path),launched_unix=time.time(),command=command))
        require(child.wait() == 0,'native_failure_no_retry')
        require(all(read(root/name/f'cycle{policy.CYCLES:02d}'/'held/COMPLETE.json')['status'] == 'COMPLETE'
            for name in policy.CADENCES),'phase_completion')
        write(root/'TERMINAL.json',dict(status='COMPLETE',finished_unix=time.time()))
    except BaseException as error:
        write(root/'TERMINAL.json',dict(status='FAILED',error_type=type(error).__name__,error=str(error),finished_unix=time.time()))
        raise
    finally:
        write(root/'FINAL_RELEASE.json',scan(root,lane))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode',choices=('prepare','scan','service','guard','run','resident'))
    parser.add_argument('--lane',choices=policy.LANES,required=True)
    parser.add_argument('--cadence',choices=policy.CADENCES)
    parser.add_argument('--cycle',type=int)
    parser.add_argument('--phase',choices=('train','held'))
    args = parser.parse_args()
    if args.mode == 'prepare': print(json.dumps(prepare(ROOT,args.lane)))
    elif args.mode == 'service': bind(args.lane); admission.pinned.service(ROOT/'SERVICE_IDENTITY.json')
    elif args.mode == 'scan': print(json.dumps(scan(ROOT,args.lane)))
    elif args.mode == 'guard': guard(ROOT,args.lane)
    elif args.mode == 'resident': resident(ROOT,args.lane)
    else: run(ROOT,args.lane,args.cadence,args.cycle,args.phase)
