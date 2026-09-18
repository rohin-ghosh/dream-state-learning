"""R110 continuation from preserved C8 captures, without replay or weight reset."""

import json
import os
from pathlib import Path
import time

from gpu import orch_math_feedback_uptake_r108_run as reuse
from gpu import orch_math_feedback_uptake_stopped as reflection
from gpu import orch_math_pipeline_l2_parent_strong as provider
from organism_v6 import orch_math_feedback_uptake_r110 as policy


common = reuse.common
require = policy.require


def parent(root, output, index, cycle, segment, task, records, deadline, previous_teacher=''):
    payload = policy.parent_payload(index, cycle, segment, task, records)
    identifier = f'GUIDED_SLEEP_C{cycle:03d}_T{segment:03d}'
    reuse.driver.seam.legacy.spend(root, 'PARENT', policy.PARENT_CAPS[index], dict(cycle=cycle, segment=segment))
    queue = root / 'r110_parent_queue'
    path = queue / f'{identifier}.request.json'
    require(not path.exists(), 'parent_once_no_retry')
    common.write(path, dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload),
        ready_sha256=common.sha(root / 'READY.json')))
    response = queue / f'{identifier}.response.json'
    until = min(time.time() + 300, deadline)
    while not response.exists() and time.time() < until:
        time.sleep(2)
    if not response.exists():
        common.write(output / f'PARENT_T{segment:03d}.json', dict(status='MISSING',
            error='parent_timeout_no_retry', segment=segment, request_sha256=common.sha(path)))
        return previous_teacher, None
    result = common.read(response)
    require(result['request_sha256'] == common.sha(path), 'real_bound_parent_request')
    directory = Path(result['archive']['remote_root'])
    require(directory == root.parent / 'parent_transcripts' / root.name / identifier, 'native_parent_custody')
    for name, digest in result['archive']['files'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'safe_parent_file')
        require(common.sha(directory / name) == digest, 'native_parent_hash')
    if result['status'] != 'COMPLETE':
        require(result['status'] in ('FAILED', 'MISSING'), 'known_missing_delivery')
        common.write(output / f'PARENT_T{segment:03d}.json', dict(status='MISSING',
            source_status=result['status'], error=result.get('error'), segment=segment,
            path=str(response), sha256=common.sha(response), archive=result['archive']))
        return previous_teacher, None
    envelope = common.read(directory / 'RAW_RESPONSE.json')
    plan = provider.parse(envelope, [task['id']])
    require(plan == result['plan'] == common.read(directory / 'PLAN.json'), 'exact_plan_join')
    teacher = policy.validate_plan(plan, task['id'])
    binding = dict(path=str(response), sha256=common.sha(response), archive=result['archive'],
        actual_model=envelope['model'], segment=segment, task_id=task['id'],
        child_source_record_sha256=policy.digest(records[-1]),
        configured_classes=list(policy.CLASSES), actual_class='UNKNOWN_AUTHOR_REVIEW')
    common.write(output / f'PARENT_T{segment:03d}.json', binding)
    common.write(root / 'R119_LEASE_V3' / 'LATEST_PARENT.json', dict(binding, finished_unix=time.time()))
    return teacher, binding


def run(root, index, cycle, phase, engine_class, validate, continuation):
    prepared = validate(root.parent)
    ready = common.read(root / 'READY.json')
    plan = common.read(root / 'R119_LEASE_V3' / 'PLAN.json')
    lifetime = plan['clock']
    require(os.environ['CUDA_VISIBLE_DEVICES'] == policy.DEVICES[index], 'uuid_cvd')
    require(('CUDA_VISIBLE_DEVICES=' + policy.DEVICES[index]).encode() in
        Path('/proc/self/environ').read_bytes().split(b'\0'), 'initial_cvd')
    require(common.sha(root / 'COHORT.json') == ready['cohort_sha256'], 'frozen_cohort')
    require(1 <= cycle <= policy.CYCLES and phase in ('experience', 'readout'), 'phase_bounds')
    output = root / 'R119_LEASE_V3' / f'cycle{cycle}' / phase
    output.mkdir(parents=True, exist_ok=False)
    process = reuse.driver.seam.native.process_identity()
    request = dict(cycle=cycle, phase=phase, index=index, process=process,
        started_unix=time.time(), adapter=None, optimizer=None, weight_writes=0,
        thought_definition='one_completed_generated_TRAIN_segment_including_metacognition', hidden_cot_count=False)
    common.write(output / 'REQUEST.json', request)
    common.write(output / 'DENOMINATORS.json', dict(planned_native=8,
        originals=2 if phase == 'experience' else 0, checks=2 if phase == 'experience' else 0,
        reflections=2 if phase == 'experience' else 0, metacognition_dialogue=2 if phase == 'experience' else 0, held=8 if phase == 'readout' else 0,
        failures_and_unattempted_included=True))
    engine = None
    def check(label):
        require(time.time() < lifetime['native_deadline_unix'], 'fixed_deadline:' + label)
    resuming = cycle == plan['next_cycle'] and phase == plan['next_phase']
    initial_context = resuming or (plan['next_phase'] == 'readout' and
        cycle == plan['next_cycle'] + 1 and phase == 'experience')
    if initial_context:
        state = common.read(root / 'R119_LEASE_V3' / 'INITIAL_STATE.json')
        incoming_memory = (common.read(root / 'R119_LEASE_V3' / 'INCOMING_MEMORY.json')
            if resuming else state['memory'])
    else:
        prior = root / 'R119_LEASE_V3' / f'cycle{cycle if phase == "readout" else cycle - 1}' / 'experience'
        complete = common.read(prior / 'COMPLETE.json')
        require(complete['status'] == 'COMPLETE' and complete['process'] == list(process), 'resident_same_process_continuity')
        require(common.sha(prior / 'STATE.json') == complete['state_sha256'], 'context_continuity')
        state = common.read(prior / 'STATE.json')
        incoming_memory = state['memory']
    preserved = plan['completed_prefix'] if resuming else 0
    common.write(output / 'CONTINUATION.json', dict(plan_sha256=continuation,
        preserved_child_calls=preserved, process_restart_explicit=True, no_model_calls_replayed=True))
    common.write(output / 'CONTEXT_CONDITION.json', dict(parent_free=phase == 'readout',
        own_train_memory=state['memory'] is not None, frozen_weights=True,
        teacher_removed_from_readout=True, full_history_archived=True,
        working_context='own_context_distillation_plus_current_episode_with_prior_context_preserved_in_boundary_archive',
        no_unbounded_context_or_weight_retention_claim=True))
    def generate(task, purpose, records=()):
        teacher = state['teacher'] if phase == 'experience' else ''
        messages = reflection.TaggedMessages(policy.messages(task, records, purpose, teacher, state['memory']), purpose)
        tokens = len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))
        teacher_tokens = len(tokenizer.encode(teacher, add_special_tokens=False)) if teacher else 0
        requested = policy.DISTILLATION_CAPS[index] if task.get('context_distillation') else policy.base.CAPS[purpose]
        require(0 < tokens < 16384 and teacher_tokens <= 1024, 'uncropped_context_and_guidance')
        cap = min(requested, 16384 - tokens)
        check('reserve')
        number = reuse.driver.seam.legacy.spend(root, 'NATIVE', policy.NATIVE_CAP,
            dict(cycle=cycle, purpose=purpose, task_id=task['id']))
        path = output / f'CALL_{number:04d}.json'
        call = dict(task_id=task['id'], purpose=purpose, messages=list(messages),
            started_unix=time.time(), process=process, requested_cap=requested,
            effective_cap=cap, parent_present=bool(teacher), updates=0)
        common.write(path, call)
        try:
            call['response'] = engine.generate(messages, max_new_tokens=cap)
            call['outcome'] = (dict(status='NOT_SCORED_METACOGNITION', correct=False) if task.get('context_distillation')
                else policy.base.history.source.judge(task, call['response']))
            call['context_distillation'] = bool(task.get('context_distillation'))
        except BaseException as error:
            call['error'] = dict(type=type(error).__name__, message=str(error))
            raise
        finally:
            call['finished_unix'] = time.time()
            common.write(path, call)
        latest = dict(path=str(path), sha256=common.sha(path), purpose=purpose,
            task_id=task['id'], tokens=len(call['response']['token_ids']), finished_unix=call['finished_unix'])
        common.write(output / 'LATEST_RESPONSE.json', latest)
        common.write(root / 'R119_LEASE_V3' / 'LATEST_RESPONSE.json', latest)
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
            records = common.read(root / 'R119_LEASE_V3' / 'INITIAL_EPISODES.json') if resuming else {}
            for task in cohort['train'][cycle - 1]:
                existing_count = len(records.setdefault(task['id'], []))
                for position, purpose in enumerate(('experience', 'check', 'revision')):
                    if position < existing_count:
                        continue
                    try:
                        response = generate(task, purpose, records[task['id']])
                        record = policy.record(task, purpose, response)
                    except Exception as error:
                        records[task['id']].append(policy.record(task, purpose,
                            error=dict(type=type(error).__name__, message=str(error))))
                        common.write(output / 'EPISODES.json', records)
                        raise
                    records[task['id']].append(record)
                    common.write(output / 'EPISODES.json', records)
                    state['completed_train_segments'] += 1
                    if policy.due(index, state['completed_train_segments']):
                        state['teacher'], state['pending'] = parent(root, output, index, cycle,
                            state['completed_train_segments'], task, records[task['id']], lifetime['native_deadline_unix'], state['teacher'])
                    if purpose == 'revision':
                        state['memory'] = dict(task_id=task['id'], question=task['question'], trace=response['raw'],
                            source_record_sha256=policy.digest(record), outcome=record['outcome'],
                            original_outcome=records[task['id']][0]['outcome'])
                    common.write(output / 'STATE.json', state)
            sources = [dict(task_id=task['id'], question=task['question'],
                trace=records[task['id']][-1]['response']['raw'],
                source_record_sha256=policy.digest(records[task['id']][-1]),
                outcome=records[task['id']][-1]['outcome'], original_outcome=records[task['id']][0]['outcome'])
                for task in cohort['train'][cycle - 1]]
            context = dict(previous_own_context=incoming_memory, current_own_reflections=sources,
                context_is_sourced_history_not_verified_facts=True)
            dialogue_task = dict(id=f'R110_DISTILL_TRAIN_C{cycle}', split='TRAIN', context_distillation=True,
                question='We are about to leave this context. Discuss importance, context retention, self-perception and your own learning process, not the task answer. Sourced history:\n' + json.dumps(context, sort_keys=True))
            dialogue_records = common.read(root / 'R119_LEASE_V3' / 'INITIAL_DIALOGUE.json') if resuming else []
            for turn in range(len(dialogue_records) + 1, 3):
                try:
                    response = generate(dialogue_task, 'revision', dialogue_records)
                    event = policy.record(dialogue_task, 'revision', response)
                except Exception as error:
                    dialogue_records.append(policy.record(dialogue_task, 'revision', error=dict(type=type(error).__name__, message=str(error))))
                    common.write(output / 'METACOGNITION_DIALOGUE.json', dialogue_records)
                    raise
                dialogue_records.append(event)
                common.write(output / 'METACOGNITION_DIALOGUE.json', dialogue_records)
                state['completed_train_segments'] += 1
                if policy.due(index, state['completed_train_segments']):
                    state['teacher'], state['pending'] = parent(root, output, index, cycle,
                        state['completed_train_segments'], dialogue_task, dialogue_records, lifetime['native_deadline_unix'], state['teacher'])
                state['memory'] = dict(task_id=dialogue_task['id'], question='Prior own metacognition/context distillation; not certified facts.',
                    trace=response['raw'], source_record_sha256=policy.digest(event), outcome=event['outcome'], original_outcome=event['outcome'])
                common.write(output / 'STATE.json', state)
            common.write(output / 'REFLECTION_BOUNDARY.json', dict(pure_dialogue_complete=True,
                dialogue_sha256=common.sha(output / 'METACOGNITION_DIALOGUE.json'), prior_context_sha256=policy.digest(incoming_memory),
                retained_history_sha256=policy.digest(context), compiler='RAW_SOURCE_SERIALIZATION_ONLY', weight_writes=0,
                metacognition_not_scored=True, finished_unix=time.time()))
            result = dict(child_calls=8, new_child_calls=8 - preserved,
                preserved_child_calls=preserved, completed_episodes=2, reflection_boundary=True,
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
