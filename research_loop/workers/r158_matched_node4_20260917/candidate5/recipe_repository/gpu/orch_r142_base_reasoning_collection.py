"""R142 fresh PUBLIC TRAIN BASE-only permission versus direct-elicitation control."""

import argparse
import json
import os
from pathlib import Path
import signal
import time

from gpu import orch_r133_code_feedback_collection as frozen
from gpu import orch_r141_code_interface as interface


SCHEMA = 'R142_BASE_REASONING_COLLECTION_V1'
BASE_MODEL = 'BASE_NO_LORA'
MODELS = (BASE_MODEL,)
PROMPT_ARMS = ('PERMISSION_ONLY', 'DIRECTED_REASONING')
STEERING = {'PERMISSION_ONLY': 'permission_only', 'DIRECTED_REASONING': 'text_requested'}
DIRECTED_CUE = (
    'Before the final JSON, work through the task in your own words. '
    'If uncertainty or feedback gives you a reason to change your plan, '
    'explain what changes and why. Stop when you have enough evidence; '
    'do not pad the response.'
)
STAGES = frozen.STAGES
TASK_COUNT, CALL_CAP = frozen.TASK_COUNT, frozen.CALL_CAP
MAX_NEW_TOKENS, CONTEXT_LIMIT = frozen.MAX_NEW_TOKENS, frozen.CONTEXT_LIMIT
require, digest, sha, read, write = frozen.require, frozen.digest, frozen.sha, frozen.read, frozen.write
exclusions, build_tasks = frozen.exclusions, interface.build_tasks
parse_expression, evaluate, verify = frozen.parse_expression, frozen.evaluate, frozen.verify
execute_public = frozen.execute_public
FROZEN_SOURCE_SHA256 = dict(interface.FROZEN_SOURCE_SHA256, **{
    'gpu/orch_r141_code_interface.py': '4ec71fe6c1d92197329462d71526f0e2daa6cf1f271fb3aa136e415d7ffcb5d0',
    'gpu/orch_r141_code_interface_guard.py': '143e68abbc67094a7223bfa75dc1b64d0909b30a245d68f091dc2c7b9f378493',
    'tests/test_orch_r141_code_interface.py': '44d36aad88b2b529027992fc5c1357df2c002a4886f71249c85b5b4072b81bba',
    'tests/test_orch_r141_code_interface_guard.py': '0c203ed6aa23aa834e3f568050c8ce5c89f52b8bd3a99c9c351a02c56a463e06',
})
SOURCE_FILES = tuple(FROZEN_SOURCE_SHA256) + (
    'gpu/orch_r142_base_reasoning_collection.py', 'gpu/orch_r142_base_reasoning_guard.py',
    'tests/test_orch_r142_base_reasoning_collection.py', 'tests/test_orch_r142_base_reasoning_guard.py',
)


def source_hashes():
    repository = Path(__file__).resolve().parents[1]
    actual = {name: sha(repository / name) for name in SOURCE_FILES}
    require(all(actual[name] == expected for name, expected in FROZEN_SOURCE_SHA256.items()), 'exact_frozen_R136_R141_sources')
    return actual


def messages(task, prompt_arm, stage='draft', draft=None, feedback=None):
    require(prompt_arm in PROMPT_ARMS, 'declared_BASE_prompt_arm')
    result = interface.messages(task, stage, draft, feedback)
    if prompt_arm == 'DIRECTED_REASONING':
        result[0]['content'] += '\n' + DIRECTED_CUE
    return result


def contract():
    return dict(schema=SCHEMA, status='HASH_EXCLUDED_CPU_PREPARED', models=list(MODELS),
                prompt_arms=list(PROMPT_ARMS), effective_models={arm: BASE_MODEL for arm in PROMPT_ARMS},
                steering=dict(STEERING), directed_cue=DIRECTED_CUE,
                control='EXACT_CURRENT_R141', stages=list(STAGES), task_count=TASK_COUNT,
                native_call_cap=CALL_CAP, max_new_tokens=MAX_NEW_TOKENS, context_limit=CONTEXT_LIMIT,
                decoder=dict(do_sample=False, num_beams=1, repetition_penalty=1.0),
                external_calls=0, old_call_replay=False, automatic_admission=False, fit_updates=0,
                gpu_reserved=False, gpu_launched=False, four_way_benchmark=False, retention_claim=False)


def prepare(root, seed, inventory=None):
    root = Path(root)
    require(not root.exists(), 'new_CPU_preparation_directory_required')
    sources = source_hashes()
    tasks = build_tasks(seed, inventory)
    root.mkdir(parents=True, mode=0o700)
    write(root / 'TASKS.json', dict(schema=SCHEMA, tasks=tasks))
    write(root / 'EXCLUSIONS.json', inventory)
    plan = dict(contract(), generation_seed=seed, tasks_sha256=sha(root / 'TASKS.json'),
                exclusions_sha256=sha(root / 'EXCLUSIONS.json'), source_sha256=sources)
    write(root / 'PLAN.json', plan)
    return plan


def verified(root, require_launchable=False):
    root = Path(root)
    plan = read(root / 'PLAN.json')
    fixed = contract()
    require(set(plan) == set(fixed) | {'generation_seed', 'tasks_sha256', 'exclusions_sha256', 'source_sha256'}
            and digest({key: plan[key] for key in fixed}) == digest(fixed), 'exact_R142_BASE_prompt_contract')
    require(plan['source_sha256'] == source_hashes() and plan['tasks_sha256'] == sha(root / 'TASKS.json')
            and plan['exclusions_sha256'] == sha(root / 'EXCLUSIONS.json'), 'prepared_bytes_changed')
    document = read(root / 'TASKS.json')
    require(set(document) == {'schema', 'tasks'} and document['schema'] == SCHEMA, 'R142_task_envelope')
    tasks = document['tasks']
    require(digest(tasks) == digest(build_tasks(plan['generation_seed'], read(root / 'EXCLUSIONS.json'))), 'exact_fresh_generated_tasks')
    return plan, tasks


def run_episodes(root, tasks, generate, check=lambda label: None):
    root = Path(root)
    _, prepared = verified(root, require_launchable=True)
    require(digest(tasks) == digest(prepared), 'only_exact_fresh_R142_tasks')
    write(root / 'EPISODES_START.json', dict(schema=SCHEMA, prompt_arms=list(PROMPT_ARMS),
          effective_model=BASE_MODEL, retry_allowed=False, started_unix=time.time()))
    reserved, completed, results = 0, 0, []
    try:
        for position, task in enumerate(tasks):
            arms = PROMPT_ARMS if position % 2 == 0 else tuple(reversed(PROMPT_ARMS))
            forks = STAGES[1:] if position % 2 == 0 else tuple(reversed(STAGES[1:]))
            for prompt_arm in arms:
                directory = root / 'episodes' / task['id'] / prompt_arm
                responses, draft_hash = {}, None
                for stage in ('draft', *forks):
                    check('before_response')
                    draft = responses.get('draft', {}).get('raw')
                    feedback = execute_public(task, draft) if stage == 'interpreter_feedback' else None
                    prefix = messages(task, prompt_arm, stage, draft, feedback)
                    require(reserved < CALL_CAP, 'fixed_native_call_ceiling')
                    reserved += 1
                    intent = dict(schema=SCHEMA, task_id=task['id'], prompt_arm=prompt_arm,
                                  effective_model=BASE_MODEL, steering=STEERING[prompt_arm], stage=stage,
                                  reserved_call=reserved, messages=prefix, messages_sha256=digest(prefix),
                                  shared_draft_call_sha256=draft_hash,
                                  shared_draft_text_sha256=digest(draft) if draft is not None else None,
                                  max_new_tokens=MAX_NEW_TOKENS, started_unix=time.time())
                    write(directory / (stage + '.INTENT.json'), intent)
                    try:
                        response = generate(prefix, prompt_arm)
                    except BaseException as error:
                        write(directory / (stage + '.FAILURE.json'), dict(error=type(error).__name__ + ': ' + str(error),
                              prompt_arm=prompt_arm, effective_model=BASE_MODEL, reserved_call=reserved, retry_allowed=False))
                        raise
                    write(directory / (stage + '.CALL.json'), dict(intent, response=response, finished_unix=time.time()))
                    require(type(response) is dict and type(response.get('raw')) is str
                            and type(response.get('terminal')) is bool and type(response.get('truncated')) is bool,
                            'native_response_contract')
                    completed += 1
                    responses[stage] = response
                    if stage == 'draft':
                        draft_hash = sha(directory / 'draft.CALL.json')
                    write(directory / (stage + '.PUBLIC.json'), execute_public(task, response['raw']))
                    write(directory / (stage + '.VERIFY.json'), dict(success=verify(task, response['raw'])))
                    write(directory / (stage + '.MEASURE.json'), dict(schema=SCHEMA, prompt_arm=prompt_arm,
                          effective_model=BASE_MODEL, metrics=interface.response_metrics(task, response)))
                result = dict(task_id=task['id'], prompt_arm=prompt_arm, effective_model=BASE_MODEL,
                              steering=STEERING[prompt_arm], shared_draft_call_sha256=draft_hash,
                              forks={stage: interface.correction(task, responses['draft'], responses[stage]) for stage in STAGES[1:]})
                write(directory / 'COMPLETE.json', result)
                results.append(result)
        require(reserved == completed == CALL_CAP, 'exact_96_calls_on_completion')
    except BaseException as error:
        write(root / 'EPISODES_TERMINAL.json', dict(schema=SCHEMA, status='FAILED_NO_RETRY', reserved_calls=reserved,
              completed_calls=completed, error=type(error).__name__ + ': ' + str(error), retry_allowed=False))
        raise
    summary = dict(schema=SCHEMA, status='COMPLETE', reserved_calls=reserved, completed_calls=completed,
                   prompt_arms=list(PROMPT_ARMS), effective_model=BASE_MODEL, results=results,
                   rows_admitted=0, fit_updates=0, external_calls=0, retry_allowed=False,
                   retention_claim=False, four_way_benchmark=False)
    write(root / 'EPISODES_TERMINAL.json', summary)
    return summary


def require_base_disabled(model):
    modules = tuple(module for module in model.modules() if hasattr(module, 'lora_A') and hasattr(module, 'lora_B'))
    require(bool(modules) and all(module.disable_adapters is True for module in modules), 'BASE_adapter_must_remain_disabled')
    require(not any(parameter.requires_grad for parameter in model.parameters()), 'BASE_weights_must_remain_frozen')


def run_loaded(root, tasks, loaded, check):
    with frozen.readonly_model(loaded.engine.model, BASE_MODEL):
        require_base_disabled(loaded.engine.model)
        write(Path(root) / 'LOADED.json', dict(schema=SCHEMA, adapter=loaded.observed.document(), optimizer_count=0,
              runtime=loaded.engine.runtime, model_states=list(MODELS), prompt_arms=list(PROMPT_ARMS),
              effective_models={arm: BASE_MODEL for arm in PROMPT_ARMS}, steering=dict(STEERING),
              adapters_disabled_for_entire_collection=True))

        def generate(prefix, prompt_arm):
            require(prompt_arm in PROMPT_ARMS, 'declared_BASE_prompt_arm')
            check('generate')
            require_base_disabled(loaded.engine.model)
            require(len(loaded.engine.prompt_tokens(prefix)) + MAX_NEW_TOKENS <= CONTEXT_LIMIT, 'no_context_trim')
            try:
                return loaded.engine.generate(prefix, max_new_tokens=MAX_NEW_TOKENS)
            finally:
                require_base_disabled(loaded.engine.model)

        return run_episodes(root, tasks, generate, check)


def collect(root, authorization, *, expected_gpu_uuid):
    root = Path(root)
    _, tasks = verified(root, require_launchable=True)
    frozen.validate_authorization(root, authorization, time.time(), expected_gpu_uuid=expected_gpu_uuid)
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'fresh_process_no_existing_alarm')
    write(root / 'NATIVE_START.json', dict(schema=SCHEMA, authorization=authorization,
          effective_model=BASE_MODEL, prompt_arms=list(PROMPT_ARMS), started_unix=time.time(), retry_allowed=False))

    def check(label):
        require(time.time() < authorization['native_end_unix'], 'native_deadline:' + label)

    def deadline(signum, frame):
        raise TimeoutError('R142_hard_native_deadline')

    old_handler = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, authorization['native_end_unix'] - time.time())
    try:
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        from gpu import orch_guided_native as native
        from gpu.orch_rich_hot_node2_exhaustion_v3 import Engine
        from organism_v6 import orch_guided_bridge as bridge

        adapter = bridge.AdapterIdentity.from_document(authorization['adapter'])
        binding = bridge.StageBinding(root.name, bridge.ARMS[1], 0, 'collection', adapter,
                                      False, True, sha(root / 'PLAN.json'))
        loaded = native.load_stage(binding, model_dir=authorization['model_dir'], device='cuda:0',
                    gpu_uuid=authorization['gpu_uuid'], context=native.StageContext(), check=check, engine_factory=Engine)
        result = run_loaded(root, tasks, loaded, check)
        loaded.verify_unchanged()
        write(root / 'NATIVE_TERMINAL.json', dict(schema=SCHEMA, status='COMPLETE', weights_verified_unchanged=True,
              effective_model=BASE_MODEL, prompt_arms=list(PROMPT_ARMS), completed_calls=result['completed_calls']))
        return result
    except BaseException as error:
        write(root / 'NATIVE_TERMINAL.json', dict(schema=SCHEMA, status='FAILED_NO_RETRY',
              error=type(error).__name__ + ': ' + str(error), weights_verified_unchanged=False, retry_allowed=False))
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'verify'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--seed')
    parser.add_argument('--exclusions', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        require(args.exclusions is not None, 'Main_hash_only_exclusions_required')
        plan = prepare(args.root, args.seed, read(args.exclusions))
    else:
        plan, _ = verified(args.root)
    print(json.dumps(dict(status=plan['status'], prompt_arms=list(PROMPT_ARMS), effective_model=BASE_MODEL,
                          steering=STEERING, native_call_cap=CALL_CAP, gpu_launched=False, fit_updates=0), sort_keys=True))


if __name__ == '__main__':
    main()
