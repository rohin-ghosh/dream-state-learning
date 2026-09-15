"""R133 fresh PUBLIC TRAIN collection. CLI is CPU-only; Main owns native launch."""

import argparse
import ast
from contextlib import contextmanager, nullcontext
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import socket
import time

from gpu import orch_r119_public_feedback as public
from organism_v6 import orch_persist_code as ledger


SCHEMA = 'R133_PUBLIC_TRAIN_CODE_FEEDBACK_V1'
MODELS = ('FULL_FIXED18404', 'BASE_NO_LORA')
STAGES = ('draft', 'interpreter_feedback', 'neutral_review')
TASK_COUNT = 16
CALL_CAP = 96
MAX_NEW_TOKENS = 2048
CONTEXT_LIMIT = 32768
require, digest, sha, read, write = public.require, public.digest, public.sha, public.read, public.write
TASK_KEYS = {'kind', 'factor', 'offset', 'threshold', 'low', 'high', 'id', 'split',
             'spec', 'normalized_spec_sha256', 'public_input', 'verification_inputs'}
SOURCE_FILES = (
    'gpu/orch_r133_code_feedback_collection.py',
    'gpu/orch_r119_public_feedback.py', 'gpu/orch_r109_l1_public_feedback.py',
    'organism_v6/orch_persist_code.py', 'gpu/orch_guided_native.py',
    'organism_v6/orch_guided_bridge.py', 'gpu/orch_rich_hot_node2_exhaustion_v3.py',
    'gpu/astra_experienced_event_microloop.py', 'gpu/astra_pchain2_native.py',
    'organism_v6/pcfl_vertical_train.py', 'organism_v6/orch_rich_hot_node2_exhaustion_v3.py',
    'tests/test_orch_r133_code_feedback_collection.py',
)


def is_hash(value):
    return type(value) is str and len(value) == 64 and all(char in '0123456789abcdef' for char in value)


def host_sha256():
    return hashlib.sha256(socket.gethostname().encode('utf-8')).hexdigest()


def exclusions(document):
    require(set(document) == {'schema', 'normalization', 'attested_by', 'coverage',
                             'inventory_refs', 'spec_sha256', 'task_id_sha256', 'used_seed_sha256'}, 'hash_only_exclusions')
    require(document['schema'] == 'R133_HASH_ONLY_EXCLUSIONS_V1'
            and document['normalization'] == public.NORMALIZATION
            and document['attested_by'] == 'Main'
            and document['coverage'] == 'R119_LINEAGE_DECLARED_CODE_INVENTORIES', 'Main_bounded_exclusions_required')
    references = document['inventory_refs']
    require(type(references) is list and 0 < len(references) <= 16, 'bounded_inventory_refs_required')
    for reference in references:
        require(type(reference) is dict and set(reference) == {'ref', 'sha256'}
                and type(reference['ref']) is str and 0 < len(reference['ref']) <= 80
                and all(char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' for char in reference['ref'])
                and is_hash(reference['sha256']), 'non_sensitive_inventory_ref_and_hash_required')
    require(len({reference['ref'] for reference in references}) == len(references), 'unique_inventory_refs_required')
    for key in ('spec_sha256', 'task_id_sha256', 'used_seed_sha256'):
        require(type(document[key]) is list and all(is_hash(value) for value in document[key])
                and len(document[key]) == len(set(document[key])), 'unique_hashes_only:' + key)
    require(bool(document['spec_sha256']), 'empty_production_exclusions_forbidden')
    return {key: set(document[key]) for key in ('spec_sha256', 'task_id_sha256', 'used_seed_sha256')}


def build_tasks(seed, inventory=None):
    require(is_hash(seed), 'fresh_256_bit_hex_seed_required')
    forbidden = exclusions(inventory) if inventory is not None else {
        'spec_sha256': set(), 'task_id_sha256': set(), 'used_seed_sha256': set()}
    require(digest(seed) not in forbidden['used_seed_sha256'], 'generation_seed_already_used')
    generator = random.Random(int(seed, 16))
    occupied = set(forbidden['spec_sha256'])
    tasks = []
    for position in range(TASK_COUNT):
        for attempt in range(10000):
            task = dict(kind=position % 4, factor=generator.choice([-17, -13, -11, 11, 13, 17]),
                        offset=generator.randint(-91, 91), threshold=generator.randint(-70, 70),
                        low=-generator.randint(80, 160), high=generator.randint(80, 160))
            boundary = task['threshold']
            if task['kind'] == 3:
                task['threshold'] = task['factor'] * boundary + task['offset']
                if abs(task['threshold']) > 1000:
                    continue
            fingerprint = public.spec_hash(task)
            identity = f'R133_PUBLIC_TRAIN_{digest(seed)[:16]}_{fingerprint}'
            if fingerprint not in occupied and digest(identity) not in forbidden['task_id_sha256']:
                break
        else:
            raise ValueError('fresh_disjoint_pool_exhausted')
        occupied.add(fingerprint)
        probe = [boundary - 1, boundary, boundary, boundary + 1,
                 task['low'] - 1, task['high'] + 1, 0, 0]
        checks = random.Random(int(digest(['R133_CHECKS', seed, fingerprint]), 16))
        task.update(id=identity, split='TRAIN', spec=public.task_spec(task),
                    normalized_spec_sha256=fingerprint, public_input=probe,
                    verification_inputs=[[], [0], probe, [task['low'], task['low'], task['high']]]
                    + [[checks.randint(-250, 250) for element in range(12)] for case in range(16)])
        tasks.append(task)
    return tasks


def evaluate(expression, values):
    tree = ledger.validate_expression(expression)
    require(type(values) is list and len(values) <= 128
            and all(type(value) is int and abs(value) <= 1000000 for value in values), 'bounded_integer_input')

    def interpret(node):
        if type(node) is ast.Constant:
            return node.value
        if type(node) is ast.UnaryOp:
            return -node.operand.value
        if type(node) is ast.Name:
            require(node.id == 'values', 'helper_name_requires_call')
            return list(values)
        require(type(node) is ast.Call, 'helper_call_required')
        arguments = [interpret(argument) for argument in node.args]
        require(type(arguments[0]) is list and all(type(value) is int for value in arguments[0]),
                'helper_first_argument_requires_integer_list')
        require(all(type(value) is int for value in arguments[1:]), 'helper_scalar_arguments_require_integers')
        result = ledger.HELPERS[node.func.id](*arguments)
        integers = result if type(result) is list else [result]
        require(all(type(value) is int and value.bit_length() <= 256 for value in integers), 'integer_result_limit')
        return result

    result = interpret(tree.body)
    require(type(result) is int, 'task_must_return_integer')
    return result


def parse_expression(text):
    def no_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_JSON_key')
            result[key] = value
        return result

    require(type(text) is str and 0 < len(text) <= 131072, 'bounded_nonempty_response')
    lines = text.strip().splitlines()
    require(bool(lines), 'empty_child_response')
    action = json.loads(lines[-1], object_pairs_hook=no_duplicate_keys)
    require(type(action) is dict and set(action) == {'expression'}
            and type(action['expression']) is str, 'exact_expression_JSON_required')
    return action['expression']


def execute_public(task, text):
    receipt = dict(schema='R133_ACTUAL_PUBLIC_INTERPRETER_V1', source='ACTUAL_ATTEMPTED_EXPRESSION',
                   input=list(task['public_input']), hidden_tests_exposed=False,
                   parser_attempted=True, interpreter_started=False, draft_text_sha256=digest(text))
    try:
        expression = parse_expression(text)
        receipt['expression'] = expression
        ledger.validate_expression(expression)
        receipt['interpreter_started'] = True
        receipt['observed'] = evaluate(expression, task['public_input'])
    except (ValueError, TypeError, SyntaxError, RecursionError) as error:
        receipt['error'] = type(error).__name__ + ': ' + str(error)
    return receipt


def verify_expression(task, expression):
    try:
        return all(evaluate(expression, values) == public.expected(task, values)
                   for values in task['verification_inputs'])
    except (ValueError, TypeError, SyntaxError, RecursionError):
        return False


def verify(task, text):
    try:
        return verify_expression(task, parse_expression(text))
    except (ValueError, TypeError, SyntaxError, RecursionError):
        return False


def messages(task, stage='draft', draft=None, feedback=None):
    require(set(task) == TASK_KEYS and task['split'] == 'TRAIN'
            and task['spec'] == public.task_spec(task), 'only_generated_public_TRAIN_specification')
    require(stage in STAGES, 'declared_stage')
    result = [dict(role='system', content=public.CONTRACT),
              dict(role='user', content=task['spec'] + '\nOne public input is: '
                   + json.dumps(task['public_input']) + '. No expected output is supplied.')]
    if stage == 'draft':
        require(draft is None and feedback is None, 'fresh_draft_no_history')
        return result
    require(type(draft) is str, 'same_raw_draft_required')
    if stage == 'interpreter_feedback':
        actual = execute_public(task, draft)
        require(feedback == actual, 'no_fabricated_or_label_feedback')
        observation = 'Actual execution diagnostic/output for your attempted expression:\n' + json.dumps(actual, sort_keys=True)
    else:
        require(feedback is None, 'neutral_fork_no_execution_evidence')
        observation = 'No execution feedback or new observation is supplied. Do not invent observations.'
    result.extend([dict(role='assistant', content=draft), dict(role='user', content=observation
                   + '\nReview your own draft; revise or retain it. Finish with exactly one single-line expression JSON object.')])
    return result


def diagnostic_expression(text):
    try:
        return parse_expression(text)
    except (ValueError, TypeError, RecursionError):
        try:
            candidate = text.strip()
            if candidate.startswith('```') and candidate.endswith('```'):
                candidate = '\n'.join(candidate.splitlines()[1:-1])
            action = json.loads(candidate)
            return action['expression'] if type(action) is dict and type(action.get('expression')) is str else None
        except (ValueError, TypeError, RecursionError):
            return None


def correction(task, before, after):
    first, last = execute_public(task, before['raw']), execute_public(task, after['raw'])
    before_pass, after_pass = verify(task, before['raw']), verify(task, after['raw'])
    complete = all(response['terminal'] and not response['truncated'] for response in (before, after))
    recovered = diagnostic_expression(before['raw'])
    recovered_pass = recovered is not None and verify_expression(task, recovered)
    formatting_only = (not before_pass and after_pass and recovered_pass
                       and recovered == last.get('expression'))
    semantic = ('observed' in first and 'observed' in last and not before_pass and after_pass)
    return dict(before_success=before_pass, after_success=after_pass,
                complete_pair=complete, formatting_only_recovery=bool(complete and formatting_only),
                task_semantic_correction=bool(complete and semantic),
                interface_execution_recovery=bool(complete and 'error' in first and 'observed' in last),
                failed_to_passed=bool(complete and not before_pass and after_pass),
                unclassified_recovery=bool(complete and not before_pass and after_pass
                                           and not formatting_only and not semantic),
                rows_admitted=0, fit_updates=0, persistence_claim=False, metacognition_claim=False)


def source_hashes():
    repository = Path(__file__).resolve().parents[1]
    return {name: sha(repository / name) for name in SOURCE_FILES}


def prepare(root, seed, inventory=None):
    root = Path(root)
    require(not root.exists(), 'new_CPU_preparation_directory_required')
    tasks = build_tasks(seed, inventory)
    root.mkdir(parents=True, mode=0o700)
    write(root / 'TASKS.json', dict(schema=SCHEMA, tasks=tasks))
    write(root / 'EXCLUSIONS.json', inventory)
    plan = dict(schema=SCHEMA, generation_seed=seed, tasks_sha256=sha(root / 'TASKS.json'),
                exclusions_sha256=sha(root / 'EXCLUSIONS.json'), source_sha256=source_hashes(),
                status='HASH_EXCLUDED_CPU_PREPARED' if inventory is not None else 'PREVIEW_NOT_LAUNCHABLE',
                models=list(MODELS), stages=list(STAGES), task_count=TASK_COUNT, native_call_cap=CALL_CAP,
                max_new_tokens=MAX_NEW_TOKENS, context_limit=CONTEXT_LIMIT,
                decoder=dict(do_sample=False, num_beams=1, repetition_penalty=1.0),
                external_calls=0, old_call_replay=False, automatic_admission=False,
                fit_updates=0, gpu_reserved=False, gpu_launched=False)
    write(root / 'PLAN.json', plan)
    return plan


def verified(root, require_launchable=False):
    root = Path(root)
    plan = read(root / 'PLAN.json')
    require(plan['schema'] == SCHEMA and plan['tasks_sha256'] == sha(root / 'TASKS.json')
            and plan['exclusions_sha256'] == sha(root / 'EXCLUSIONS.json')
            and plan['source_sha256'] == source_hashes(), 'prepared_bytes_changed')
    inventory = read(root / 'EXCLUSIONS.json')
    tasks = read(root / 'TASKS.json')['tasks']
    require(tasks == build_tasks(plan['generation_seed'], inventory), 'exact_fresh_generated_tasks')
    require(plan['models'] == list(MODELS) and plan['stages'] == list(STAGES)
            and plan['task_count'] == TASK_COUNT and plan['native_call_cap'] == CALL_CAP
            and plan['max_new_tokens'] == MAX_NEW_TOKENS and plan['context_limit'] == CONTEXT_LIMIT
            and plan['decoder'] == dict(do_sample=False, num_beams=1, repetition_penalty=1.0)
            and plan['external_calls'] == 0 and plan['old_call_replay'] is False
            and plan['automatic_admission'] is False and plan['fit_updates'] == 0, 'frozen_collection_contract')
    if require_launchable:
        require(inventory is not None and plan['status'] == 'HASH_EXCLUDED_CPU_PREPARED', 'Main_exclusions_still_required')
    return plan, tasks


def run_episodes(root, tasks, generate, check=lambda label: None):
    root = Path(root)
    require(len(tasks) == TASK_COUNT and len({task['id'] for task in tasks}) == TASK_COUNT, 'fixed_16_unique_tasks')
    require(all(set(task) == TASK_KEYS and task['id'].startswith('R133_PUBLIC_TRAIN_')
                and '/' not in task['id'] and '\\' not in task['id'] for task in tasks), 'fresh_safe_task_ids')
    write(root / 'EPISODES_START.json', dict(schema=SCHEMA, retry_allowed=False, started_unix=time.time()))
    reserved, completed, results = 0, 0, []
    try:
        for position, task in enumerate(tasks):
            states = MODELS if position % 2 == 0 else tuple(reversed(MODELS))
            for model in states:
                directory = root / 'episodes' / task['id'] / model
                responses, draft_hash = {}, None
                forks = STAGES[1:] if position % 2 == 0 else tuple(reversed(STAGES[1:]))
                for stage in ('draft', *forks):
                    check('before_response')
                    draft = responses.get('draft', {}).get('raw')
                    feedback = execute_public(task, draft) if stage == 'interpreter_feedback' else None
                    prefix = messages(task, stage, draft, feedback)
                    require(reserved < CALL_CAP, 'fixed_native_call_ceiling')
                    reserved += 1
                    intent = dict(schema=SCHEMA, task_id=task['id'], model=model, stage=stage,
                                  reserved_call=reserved, messages=prefix, messages_sha256=digest(prefix),
                                  shared_draft_call_sha256=draft_hash,
                                  shared_draft_text_sha256=digest(draft) if draft is not None else None,
                                  max_new_tokens=MAX_NEW_TOKENS, started_unix=time.time())
                    write(directory / (stage + '.INTENT.json'), intent)
                    try:
                        response = generate(prefix, model)
                    except BaseException as error:
                        write(directory / (stage + '.FAILURE.json'), dict(error=type(error).__name__ + ': ' + str(error),
                              reserved_call=reserved, retry_allowed=False))
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
                result = dict(task_id=task['id'], model=model, shared_draft_call_sha256=draft_hash,
                              forks={stage: correction(task, responses['draft'], responses[stage]) for stage in STAGES[1:]})
                write(directory / 'COMPLETE.json', result)
                results.append(result)
        require(reserved == completed == CALL_CAP, 'exact_96_calls_on_completion')
    except BaseException as error:
        write(root / 'EPISODES_TERMINAL.json', dict(status='FAILED_NO_RETRY', reserved_calls=reserved,
              completed_calls=completed, error=type(error).__name__ + ': ' + str(error), retry_allowed=False))
        raise
    summary = dict(status='COMPLETE', reserved_calls=reserved, completed_calls=completed,
                   results=results, rows_admitted=0, fit_updates=0, external_calls=0, retry_allowed=False)
    write(root / 'EPISODES_TERMINAL.json', summary)
    return summary


@contextmanager
def readonly_model(model, state):
    require(state in MODELS, 'known_model_state')
    parameters = tuple(model.parameters())
    frozen_flags = tuple(parameter.requires_grad for parameter in parameters)
    require(not any(frozen_flags), 'all_weights_frozen')
    modules = tuple(module for module in model.modules() if hasattr(module, 'lora_A') and hasattr(module, 'lora_B'))
    require(bool(modules), 'actual_adapter_disable_state_required')
    previous_disabled = tuple(module.disable_adapters for module in modules)
    try:
        with model.disable_adapter() if state == 'BASE_NO_LORA' else nullcontext():
            require(all(module.disable_adapters is (state == 'BASE_NO_LORA') for module in modules),
                    'actual_adapter_disable_state_required')
            require(not any(parameter.requires_grad for parameter in model.parameters()), 'weights_became_trainable')
            try:
                yield
            finally:
                require(not any(parameter.requires_grad for parameter in model.parameters()), 'weights_became_trainable')
    finally:
        for parameter, frozen in zip(parameters, frozen_flags):
            if parameter.requires_grad is not frozen:
                parameter.requires_grad_(frozen)
        require(tuple(parameter.requires_grad for parameter in model.parameters()) == frozen_flags,
                'frozen_flags_not_restored')
        require(tuple(module.disable_adapters for module in modules) == previous_disabled,
                'adapter_enable_state_not_restored')


def validate_authorization(root, authorization, now, *, expected_gpu_uuid):
    require(set(authorization) == {'schema', 'approved_by', 'plan_sha256', 'r130_released',
            'allocation_confirmed', 'host_sha256', 'gpu_uuid', 'physical_index', 'node_local_root',
            'model_dir', 'checkpoint', 'adapter', 'native_end_unix', 'lease_end_unix'}, 'exact_Main_launch_metadata')
    require(authorization['schema'] == 'R133_MAIN_NATIVE_AUTHORIZATION_V1'
            and authorization['approved_by'] == 'Main' and authorization['r130_released'] is True
            and authorization['allocation_confirmed'] is True, 'Main_release_and_allocation_required')
    require(authorization['plan_sha256'] == sha(Path(root) / 'PLAN.json')
            and is_hash(authorization['host_sha256']) and authorization['host_sha256'] == host_sha256()
            and authorization['physical_index'] == 7
            and type(expected_gpu_uuid) is str and expected_gpu_uuid.startswith('GPU-')
            and authorization['gpu_uuid'] == expected_gpu_uuid
            and os.environ.get('CUDA_VISIBLE_DEVICES') == expected_gpu_uuid, 'exact_local_allocation_binding')
    require(now < authorization['native_end_unix'] < authorization['lease_end_unix'] - 120,
            'native_deadline_and_lease_margin_required')
    require(authorization['checkpoint'] == 18404 and authorization['adapter']['base_sha256'] == public.BASE_SHA,
            'fixed18404_and_frozen_Qwen_base_required')
    require(Path(authorization['node_local_root']).is_absolute(), 'absolute_node_local_root_required')
    local = Path(authorization['node_local_root']).resolve()
    repository = Path(__file__).resolve().parents[1]
    require(local.is_absolute() and Path(root).resolve().is_relative_to(local)
            and not Path(root).resolve().is_relative_to(repository), 'raw_artifacts_node_local_not_repo')
    for path in (authorization['model_dir'], authorization['adapter']['path']):
        require(Path(path).is_absolute() and Path(path).is_dir()
                and not Path(path).resolve().is_relative_to(Path(root).resolve()), 'read_only_weights_outside_output')


def collect(root, authorization, *, expected_gpu_uuid):
    """Main-only future entry point; not exposed by the CPU preparation CLI."""
    root = Path(root)
    plan, tasks = verified(root, require_launchable=True)
    validate_authorization(root, authorization, time.time(), expected_gpu_uuid=expected_gpu_uuid)
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'fresh_process_no_existing_alarm')
    write(root / 'NATIVE_START.json', dict(authorization=authorization, started_unix=time.time(), retry_allowed=False))

    def check(label):
        require(time.time() < authorization['native_end_unix'], 'native_deadline:' + label)

    def deadline(signum, frame):
        raise TimeoutError('R133_hard_native_deadline')

    old_handler = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, authorization['native_end_unix'] - time.time())
    loaded = None
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
        write(root / 'LOADED.json', dict(adapter=loaded.observed.document(), optimizer_count=0,
                                       runtime=loaded.engine.runtime, model_states=list(MODELS)))

        def generate(prefix, state):
            check('generate')
            require(len(loaded.engine.prompt_tokens(prefix)) + MAX_NEW_TOKENS <= CONTEXT_LIMIT, 'no_context_trim')
            with readonly_model(loaded.engine.model, state):
                return loaded.engine.generate(prefix, max_new_tokens=MAX_NEW_TOKENS)

        result = run_episodes(root, tasks, generate, check)
        loaded.verify_unchanged()
        write(root / 'NATIVE_TERMINAL.json', dict(status='COMPLETE', weights_verified_unchanged=True,
                                               completed_calls=result['completed_calls']))
        return result
    except BaseException as error:
        write(root / 'NATIVE_TERMINAL.json', dict(status='FAILED_NO_RETRY', error=type(error).__name__ + ': ' + str(error),
                                               weights_verified_unchanged=False, retry_allowed=False))
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
        plan = prepare(args.root, args.seed, read(args.exclusions) if args.exclusions else None)
    else:
        plan, tasks = verified(args.root)
    print(json.dumps(dict(status=plan['status'], tasks=TASK_COUNT, native_call_cap=CALL_CAP,
                         gpu_reserved=False, gpu_launched=False), sort_keys=True))


if __name__ == '__main__':
    main()
