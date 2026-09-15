"""Sequential frozen BASE contextual cycles; private parents never see readouts."""

import os
from pathlib import Path
import time

from gpu import orch_math_feedback_uptake_r108_run as reuse
from gpu import orch_math_feedback_uptake_stopped as reflection
from gpu import orch_math_pipeline_l2_parent_strong as provider
from organism_v6 import orch_math_feedback_uptake_r109 as policy


common = reuse.common
require = policy.require


def parent(root, output, index, cycle, segment, task, records, deadline):
    payload = policy.parent_payload(index, cycle, segment, task, records)
    identifier = f'GUIDED_SLEEP_C{cycle:03d}_T{segment:03d}'
    reuse.driver.seam.legacy.spend(root, 'PARENT', policy.PARENT_CAPS[index], dict(cycle=cycle, segment=segment))
    queue = root / 'r109_parent_queue'
    path = queue / f'{identifier}.request.json'
    require(not path.exists(), 'parent_once_no_retry')
    common.write(path, dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload),
        ready_sha256=common.sha(root / 'READY.json')))
    response = queue / f'{identifier}.response.json'
    until = min(time.time() + 300, deadline)
    while not response.exists():
        require(time.time() < until, 'parent_timeout_no_retry')
        time.sleep(2)
    result = common.read(response)
    require(result['status'] == 'COMPLETE' and result['request_sha256'] == common.sha(path), 'real_bound_parent')
    directory = Path(result['archive']['remote_root'])
    require(directory == root.parent / 'parent_transcripts' / root.name / identifier, 'native_parent_custody')
    for name, digest in result['archive']['files'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'safe_parent_file')
        require(common.sha(directory / name) == digest, 'native_parent_hash')
    envelope = common.read(directory / 'RAW_RESPONSE.json')
    plan = provider.parse(envelope, [task['id']])
    require(plan == result['plan'] == common.read(directory / 'PLAN.json'), 'exact_plan_join')
    teacher = policy.validate_plan(plan, task['id'])
    binding = dict(path=str(response), sha256=common.sha(response), archive=result['archive'],
        actual_model=envelope['model'], segment=segment, task_id=task['id'],
        child_source_record_sha256=policy.digest(records[-1]),
        configured_classes=list(policy.CLASSES), actual_class='UNKNOWN_AUTHOR_REVIEW')
    common.write(output / f'PARENT_T{segment:03d}.json', binding)
    common.write(root / 'LATEST_PARENT.json', dict(binding, finished_unix=time.time()))
    return teacher, binding


def run(root, index, cycle, phase, engine_class, validate):
    prepared = validate(root.parent)
    ready = common.read(root / 'READY.json')
    lifetime = common.read(root / 'ACTIVATION.json')
    require(os.environ['CUDA_VISIBLE_DEVICES'] == policy.DEVICES[index], 'uuid_cvd')
    require(('CUDA_VISIBLE_DEVICES=' + policy.DEVICES[index]).encode() in
        Path('/proc/self/environ').read_bytes().split(b'\0'), 'initial_cvd')
    require(common.sha(root / 'COHORT.json') == ready['cohort_sha256'], 'frozen_cohort')
    require(1 <= cycle <= policy.CYCLES and phase in ('experience', 'readout'), 'phase_bounds')
    output = root / f'cycle{cycle}' / phase
    output.mkdir(parents=True, exist_ok=False)
    process = reuse.driver.seam.native.process_identity()
    request = dict(cycle=cycle, phase=phase, index=index, process=process,
        started_unix=time.time(), adapter=None, optimizer=None, weight_writes=0,
        thought_definition='one_completed_generated_TRAIN_segment', hidden_cot_count=False)
    common.write(output / 'REQUEST.json', request)
    common.write(output / 'DENOMINATORS.json', dict(planned_native=6 if phase == 'experience' else 8,
        originals=2 if phase == 'experience' else 0, checks=2 if phase == 'experience' else 0,
        reflections=2 if phase == 'experience' else 0, held=8 if phase == 'readout' else 0,
        failures_and_unattempted_included=True))
    engine = None
    def check(label):
        require(time.time() < lifetime['native_deadline_unix'], 'fixed_deadline:' + label)
    state = dict(memory=None, teacher='', pending=None, completed_train_segments=0)
    if phase == 'readout' or cycle > 1:
        prior = root / f'cycle{cycle if phase == "readout" else cycle - 1}' / 'experience'
        complete = common.read(prior / 'COMPLETE.json')
        require(complete['status'] == 'COMPLETE' and complete['process'] != list(process), 'fresh_prior_complete')
        require(common.sha(prior / 'STATE.json') == complete['state_sha256'], 'context_continuity')
        state = common.read(prior / 'STATE.json')
    common.write(output / 'CONTEXT_CONDITION.json', dict(parent_free=phase == 'readout',
        own_train_memory=state['memory'] is not None, frozen_weights=True,
        teacher_removed_from_readout=True, full_history_archived=True,
        working_context='most_recent_sourced_own_reflection_plus_current_episode',
        no_unbounded_context_or_weight_retention_claim=True))
    def generate(task, purpose, records=()):
        teacher = state['teacher'] if phase == 'experience' else ''
        messages = reflection.TaggedMessages(policy.messages(task, records, purpose, teacher, state['memory']), purpose)
        tokens = len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))
        teacher_tokens = len(tokenizer.encode(teacher, add_special_tokens=False)) if teacher else 0
        cap = policy.base.generation_cap(purpose, tokens, teacher_tokens)
        check('reserve')
        number = reuse.driver.seam.legacy.spend(root, 'NATIVE', policy.NATIVE_CAP,
            dict(cycle=cycle, purpose=purpose, task_id=task['id']))
        path = output / f'CALL_{number:04d}.json'
        call = dict(task_id=task['id'], purpose=purpose, messages=list(messages),
            started_unix=time.time(), process=process, requested_cap=policy.base.CAPS[purpose],
            effective_cap=cap, parent_present=bool(teacher), updates=0)
        common.write(path, call)
        try:
            call['response'] = engine.generate(messages, max_new_tokens=cap)
            call['outcome'] = policy.base.history.source.judge(task, call['response'])
        except BaseException as error:
            call['error'] = dict(type=type(error).__name__, message=str(error))
            raise
        finally:
            call['finished_unix'] = time.time()
            common.write(path, call)
        latest = dict(path=str(path), sha256=common.sha(path), purpose=purpose,
            task_id=task['id'], tokens=len(call['response']['token_ids']), finished_unix=call['finished_unix'])
        common.write(output / 'LATEST_RESPONSE.json', latest)
        common.write(root / 'LATEST_RESPONSE.json', latest)
        if phase == 'experience' and state['pending']:
            common.write(output / f'TRIPLE_{number:04d}.json', dict(child_state=state['pending']['child_source_record_sha256'],
                parent_intervention=state['pending'], subsequent_behavior=latest,
                semantic_behavior_change='UNKNOWN_AUTHOR_REVIEW', helpfulness='UNKNOWN_AUTHOR_REVIEW',
                outcome=call['outcome'], causal_claim=False))
            state['pending'] = None
        return call['response']
    try:
        before = reuse.driver.seam.portable.verify_base_files(prepared['bundle'], prepared['model_dir'],
            expected_manifest_sha256=reuse.node_limits.BUNDLE_SHA)
        require(before['expected_base_sha256'] == policy.base.BASE_SHA, 'actual_base_files')
        tokenizer = reuse.driver.seam.native.source.native.load_local_tokenizer(prepared['model_dir'])
        engine = reflection.engine_class(engine_class)(prepared['model_dir'], tokenizer, device='cuda:0', check=check)
        count = policy.base.verify_no_adapter(engine.model)
        common.write(output / 'LOADED.json', dict(request, loaded_unix=time.time(), parameters=count,
            base_sha256=policy.base.BASE_SHA, no_adapter=True, no_optimizer=True, all_parameters_frozen=True))
        cohort = common.read(root / 'COHORT.json')
        if phase == 'experience':
            records = {}
            for task in cohort['train'][cycle - 1]:
                records[task['id']] = []
                for purpose in ('experience', 'check', 'revision'):
                    try:
                        response = generate(task, purpose, records[task['id']])
                        record = policy.base.history.record(task, purpose, response)
                    except Exception as error:
                        records[task['id']].append(policy.base.history.record(task, purpose,
                            error=dict(type=type(error).__name__, message=str(error))))
                        common.write(output / 'EPISODES.json', records)
                        raise
                    records[task['id']].append(record)
                    common.write(output / 'EPISODES.json', records)
                    state['completed_train_segments'] += 1
                    if policy.due(index, state['completed_train_segments']):
                        state['teacher'], state['pending'] = parent(root, output, index, cycle,
                            state['completed_train_segments'], task, records[task['id']], lifetime['native_deadline_unix'])
                    if purpose == 'revision':
                        state['memory'] = dict(task_id=task['id'], question=task['question'], trace=response['raw'],
                            source_record_sha256=policy.digest(record), outcome=record['outcome'],
                            original_outcome=records[task['id']][0]['outcome'])
                    common.write(output / 'STATE.json', state)
            result = dict(child_calls=6, completed_episodes=2, reflection_boundary=True,
                state_sha256=common.sha(output / 'STATE.json'), all_experience_archived=True,
                negative_outcomes_retained=True, sleep_weight_writes=0)
        else:
            for task in cohort['held'][cycle - 1]:
                generate(task, 'held')
            result = dict(child_calls=8, parent_free=True, no_held_to_parent=True)
        engine.verify_base()
        policy.base.verify_no_adapter(engine.model)
        reuse.driver.seam.portable.verify_base_files(prepared['bundle'], prepared['model_dir'],
            expected_manifest_sha256=reuse.node_limits.BUNDLE_SHA)
        common.write(output / 'AFTER.json', dict(actual_mounted_base_verified=True,
            base_sha256=policy.base.BASE_SHA, adapter=None, optimizer=None, process=process, finished_unix=time.time()))
        common.write(output / 'COMPLETE.json', dict(request, status='COMPLETE', finished_unix=time.time(), **result))
    except BaseException as error:
        common.write(output / 'FAILED.json', dict(request, type=type(error).__name__,
            error=str(error), finished_unix=time.time(), no_retry=True))
        if engine is not None:
            try:
                engine.verify_base()
                policy.base.verify_no_adapter(engine.model)
                common.write(output / 'FAILED_AFTER.json', dict(verified=True, process=process))
            except BaseException as failure:
                common.write(output / 'FAILED_AFTER.json', dict(verified=False, error=str(failure)))
        raise
