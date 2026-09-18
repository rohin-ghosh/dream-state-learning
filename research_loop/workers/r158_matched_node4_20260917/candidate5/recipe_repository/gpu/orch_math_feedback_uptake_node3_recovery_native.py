"""New BASE context-continuation source; only own reflections receive a lexical guard."""

from types import SimpleNamespace
from gpu import orch_math_feedback_uptake_stopped as integration
from gpu import orch_math_feedback_uptake_response_contract as response_contract
import os
from pathlib import Path
import time

from gpu import orch_math_pipeline_l2_r104_native as seam
from gpu import orch_math_pipeline_l2_run as common
from organism_v6 import orch_math_feedback_uptake_base as original_policy
policy = SimpleNamespace(**vars(original_policy))
policy.NATIVE_CAP = 14
policy.PARENT_CAP = 2


def run(root, cycle, phase):
    prepared = common.validate(root.parent)
    ready = common.read(root / 'READY.json')
    lifetime = common.read(root / 'ACTIVATION.json')
    policy.require(os.environ['CUDA_VISIBLE_DEVICES'] == policy.UUID, 'exact_uuid_cvd')
    policy.require(('CUDA_VISIBLE_DEVICES=' + policy.UUID).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'), 'initial_native_cvd')
    for path, digest in ready['source_files'].items():
        policy.require(common.sha(Path(path)) == digest, 'source_binding')
    for path, digest in ready['files'].items():
        policy.require(common.sha(root / path) == digest, 'input_binding')
    output = root / f'cycle{cycle}' / phase
    output.mkdir(parents=True, exist_ok=False)
    request = dict(cycle=cycle, phase=phase, process=seam.native.process_identity(), started_unix=time.time(),
        adapter=None, optimizer=None, training_updates=0, base_sha256=policy.BASE_SHA, uuid=policy.UUID)
    common.write(output / 'REQUEST.json', request)
    common.write(output / 'DENOMINATORS.json', dict(original=2 if phase == 'experience' else 0,
        checks=2 if phase == 'experience' else 0, own_reflections=2 if phase == 'experience' else 0,
        parents=2 if phase == 'experience' else 0, held=8 if phase == 'readout' else 0,
        failures_and_unattempted_included=True))
    engine = None

    def check(label):
        policy.require(time.time() < lifetime['native_deadline_unix'], 'original_and_segment_deadline:' + label)

    try:
        before = seam.portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=seam.BUNDLE_SHA)
        policy.require(before['expected_base_sha256'] == policy.BASE_SHA, 'actual_base_files')
        tokenizer = seam.native.source.native.load_local_tokenizer(prepared['model_dir'])
        engine = integration.engine_class(seam.Engine)(policy.options(prepared['model_dir']), tokenizer, check=check)
        count = policy.verify_no_adapter(engine.model)
        common.write(output / 'LOADED.json', dict(request, loaded_unix=time.time(), parameters=count,
            base_verified=True, no_peft=True, no_lora=True, all_parameters_frozen=True, runtime=engine.runtime))
        memory = common.read(root / 'PREVIOUS_CARRY.json')
        if phase == 'readout' or cycle > 1:
            prior = root / f'cycle{cycle if phase == "readout" else cycle - 1}' / 'experience'
            complete = common.read(prior / 'COMPLETE.json')
            policy.require(complete['status'] == 'COMPLETE' and common.sha(prior / 'CARRY.json') == complete['carry_sha256'], 'actual_own_context_carry')
            policy.require(complete['process'] != list(seam.native.process_identity()), 'fresh_process_required')
            memory = common.read(prior / 'CARRY.json')
        common.write(output / 'CONTEXT_CONDITION.json', dict(parent_free=phase == 'readout', own_train_memory=memory is not None,
            weight_learning=False, memory_sha256=policy.digest(memory), no_weight_retention_claim=True))

        def generate(task, purpose, records=(), teacher=''):
            messages = integration.TaggedMessages(policy.messages(task, records, purpose, teacher, memory), purpose)
            prompt_tokens = len(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False))
            cap = policy.generation_cap(purpose, prompt_tokens, len(tokenizer.encode(teacher, add_special_tokens=False)) if teacher else 0)
            if cycle == 1 and phase == 'experience' and purpose == 'experience':
                historical = common.read(root / 'HISTORICAL_FIRST_CALL.json')
                if task['id'] == historical['task_id']:
                    policy.require(messages == historical['messages'] and cap == historical['effective_cap'], 'exact_historical_prompt_cap')
                    imported = dict(historical, historical_import=True, newly_generated=False,
                        original_call_sha256=common.sha(root / 'HISTORICAL_FIRST_CALL.json'))
                    imported['response'] = response_contract.canonical_response(historical['response'], messages,
                        tokenizer, cap, common.read(root / 'RECOVERY.json')['original_engine_sha256'])
                    path = output / 'CALL_000.json'
                    policy.require(not path.exists(), 'historical_import_once')
                    common.write(path, imported)
                    common.write(output / 'HISTORICAL_IMPORT.json', dict(original_sha256=imported['original_call_sha256'],
                        original_process=historical['process'], import_process=seam.native.process_identity(),
                        imported_unix=time.time(), native_calls_added=0, raw_and_tokens_unchanged=True))
                    return imported['response']
            check('reserve')
            number = seam.legacy.spend(root, 'NATIVE', policy.NATIVE_CAP, dict(cycle=cycle, purpose=purpose, task_id=task['id']))
            path = output / f'CALL_{number:03d}.json'
            call = dict(task_id=task['id'], purpose=purpose, messages=messages, requested_cap=policy.CAPS[purpose], effective_cap=cap,
                started_unix=time.time(), process=seam.native.process_identity(), parent_present=bool(teacher), updates=0)
            common.write(path, call)
            try:
                call['response'] = engine.generate(messages, max_new_tokens=cap)
            except BaseException as error:
                call['error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                call['finished_unix'] = time.time()
                common.write(path, call)
            common.write(output / 'LATEST_RESPONSE.json', dict(purpose=purpose, task_id=task['id'],
                path=str(path), sha256=common.sha(path), tokens=len(call['response']['token_ids']), finished_unix=call['finished_unix']))
            return call['response']

        cohort = common.read(root / 'COHORT.json')
        if phase == 'experience':
            tasks = cohort['train'][cycle - 1]
            records = {task['id']: [] for task in tasks}
            for task in tasks:
                records[task['id']].append(policy.history.record(task, 'experience', generate(task, 'experience')))
                common.write(output / 'EPISODES.json', records)
            for round_number, purpose in ((1, 'check'), (2, 'revision')):
                previous = [dict(task_id=memory['task_id'], trace=memory['trace'], source_record_sha256=memory['source_record_sha256'])] if memory else []
                payload = policy.parent_payload(tasks, records, cycle, round_number, previous)
                identifier = f'GUIDED_SLEEP_C{cycle}_P{round_number}'
                check('parent_reserve')
                seam.legacy.spend(root, 'PARENT', policy.PARENT_CAP, dict(cycle=cycle, round=round_number))
                queue = root / 'base_parent_queue_r107'
                path = queue / (identifier + '.request.json')
                policy.require(not path.exists(), 'parent_once_only')
                common.write(path, dict(id=identifier, payload=payload, payload_sha256=policy.digest(payload), ready_sha256=common.sha(root / 'READY.json')))
                until = min(time.time() + 300, lifetime['native_deadline_unix'])
                response_path = queue / (identifier + '.response.json')
                while not response_path.exists():
                    check('parent_wait')
                    policy.require(time.time() < until, 'parent_timeout_no_retry')
                    time.sleep(2)
                result = common.read(response_path)
                policy.require(result['status'] == 'COMPLETE' and result['request_sha256'] == common.sha(path), 'bound_real_parent_response')
                archive = result['archive']
                directory = Path(archive['remote_root'])
                policy.require(directory.is_relative_to(root.parent / 'parent_transcripts' / root.name), 'own_parent_lineage')
                for name, digest in archive['files'].items():
                    policy.require('..' not in Path(name).parts and not Path(name).is_absolute(), 'safe_transcript_path')
                    policy.require(common.sha(directory / name) == digest, 'native_transcript_hash')
                envelope = common.read(directory / 'RAW_RESPONSE.json')
                plan = policy.verified_plan(envelope, tasks)
                policy.require(plan == result['plan'] == common.read(directory / 'PLAN.json'), 'exact_native_parent_plan_join')
                common.write(output / f'PARENT_{round_number}.json', result)
                for task_id in plan['order']:
                    task = next(task for task in tasks if task['id'] == task_id)
                    teacher = plan['guidance'] + '\n' + plan['episode_guidance'][task_id]
                    response = generate(task, purpose, records[task_id], teacher)
                    records[task_id].append(policy.history.record(task, purpose, response))
                    common.write(output / 'EPISODES.json', records)
            final_task = tasks[-1]
            final = records[final_task['id']][-1]
            common.write(output / 'CARRY.json', dict(task_id=final_task['id'], question=final_task['question'],
                trace=final['response']['raw'], source_record_sha256=policy.digest(final),
                outcome=final['outcome'], original_outcome=records[final_task['id']][0]['outcome']))
            result = dict(child_calls=6, parent_calls=2, carry_sha256=common.sha(output / 'CARRY.json'),
                reflection_boundary=True, sleep_weight_writes=0, all_experience_retained=True)
        else:
            for task in cohort['held'][cycle - 1]:
                generate(task, 'held')
            result = dict(child_calls=8, parent_calls=0, parent_free=True, own_context_conditioned=True,
                primary_readout='author_environment_absorption_questions_integration_strategy_novel_thought_per_child_token',
                outcome_selection=False, no_automatic_semantic_labels=True)
        engine.verify_base()
        policy.verify_no_adapter(engine.model)
        seam.portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=seam.BUNDLE_SHA)
        common.write(output / 'AFTER.json', dict(base_sha256=policy.BASE_SHA, adapter=None, optimizer=None,
            actual_mounted_base_verified=True, all_parameters_frozen=True, process=seam.native.process_identity(), finished_unix=time.time()))
        common.write(output / 'COMPLETE.json', dict(request, status='COMPLETE', finished_unix=time.time(), **result))
    except BaseException as error:
        if engine is not None:
            try:
                engine.verify_base()
                policy.verify_no_adapter(engine.model)
                common.write(output / 'FAILED_AFTER.json', dict(actual_mounted_base_verified=True, adapter=None, training_updates=0))
            except BaseException as verification_error:
                common.write(output / 'FAILED_AFTER.json', dict(verified=False, error=str(verification_error)))
        common.write(output / 'FAILED.json', dict(request, type=type(error).__name__, error=str(error), finished_unix=time.time(), no_retry=True))
        raise
