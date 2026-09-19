"""R119 isolated public-feedback collection; no optimizer, admission or fit.

CPU preparation: prepare --request /node/request.json --root /node/new-root
Main-owned launch after allocation/release/CPU receipts: guard --root /node/new-root
Requests pin allocation, seed, exclusions and source_files by SHA256. The sealed
exclusion inventory is metadata supplied by Main, never a path to FINAL content.
CONFIRM reservations contain IDs and normalized hashes, not prompts or examples.
"""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time

from gpu import orch_r109_l1_public_feedback as pilot
from organism_v6 import orch_persist_code as ledger


SOURCE = 'R119_SELF_PUBLIC_FEEDBACK_EXACT_CONTRACT_V1'
NORMALIZATION = 'R119_LEDGER_FUNCTIONAL_SPEC_V1'
BRANCHES = ('CHILD_PUBLIC_FEEDBACK', 'CHILD_NO_FEEDBACK', 'BASE_PUBLIC_FEEDBACK', 'BASE_NO_FEEDBACK')
MODELS = ('CHILD', 'BASE')
COUNTS = {'TRAIN': 16, 'DEV': 8, 'CONFIRM': 8}
RESPONSE_CAPS = {'TRAIN': 160, 'DEV': 80}
SEED_STATE = '5744cb66d7dcbee79150d5f67c7221177edd898ba78a5659e64b5a81ef55156d'
OPTIMIZER_SHA = 'f05ea93f7326f14764085ee481aedd9d6aca2cfaaabb70f6849b44f30f6e4c51'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
NATIVE_END = 1789495200
EXTERNAL_END = 1789495380
DECODER = {'do_sample': False, 'num_beams': 1, 'repetition_penalty': 1.0}
PUBLIC_KEYS = {'schema', 'source', 'input', 'expression', 'observed', 'error',
               'hidden_tests_exposed', 'probe_attempted', 'interpreter_started'}
CONTRACT = (
    'You may reason, revisit a consequential uncertainty, and allocate your remaining '
    'budget as useful. Reasoning before the final action is permitted; no prescribed '
    'headings, minimum length or required revisitation. Do not invent observations. '
    'The FINAL LINE must be exactly a single-line JSON object with exactly the key '
    '"expression" and a string value: {"expression":"..."}. The ellipsis is a '
    'placeholder, not code to submit. No extra keys or code fence on the final line. '
    'The ONLY input identifier is values, bound to the complete integer input list. '
    'Do not use xs, TRAIN, train or a literal input list in the expression. '
    'Helper signatures (items denotes an argument, NOT an available identifier): '
    'ge(items, threshold): list of integers >= threshold, preserving order and duplicates; '
    'affine(items, factor, offset): list with each integer mapped to factor*x+offset; '
    'clip(items, low, high): list with each integer clamped inclusively to [low, high], low<=high; '
    'unique(items): list removing duplicates, preserving first occurrence; '
    'sum(items): integer sum, including 0 for an empty list; '
    'len(items): integer length, including 0 for an empty list. '
    'Allowed syntax: nested positional calls to these six helpers, values, integer '
    'constants of absolute value <=1000 and a minus sign on integer constants. '
    'No other identifiers, functions, keyword arguments, arithmetic operators, '
    'comparisons, comprehensions, indexing, attributes, literal lists or lambdas. '
    'At most500 expression characters and100 AST nodes. Return an integer for any '
    'input list, not a constant answer for the one public probe. '
    'The response budget is a limit, not a target; finish within it.'
)
require, read, sha, write = pilot.require, pilot.read, pilot.sha, pilot.write


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def normalized_spec(task):
    kind, factor, offset = task['kind'], task['factor'], task['offset']
    require(kind in range(4) and factor != 0, 'supported_nondegenerate_task')
    if kind in (0, 2):
        body = ['filtered_affine_sum', kind == 2, task['threshold'], factor, offset]
    elif kind == 1:
        body = ['affine_clamp_distinct_sum', factor, offset, task['low'], task['high']]
    else:
        difference = task['threshold'] - offset
        cutoff = -((-difference) // factor) if factor > 0 else difference // factor
        low, high = task['low'], task['high']
        if factor > 0:
            body = ['count_all'] if cutoff <= low else ['count_none'] if cutoff > high else ['count_ge', cutoff]
        else:
            body = ['count_none'] if cutoff < low else ['count_all'] if cutoff >= high else ['count_le', cutoff]
    return {'normalization': NORMALIZATION, 'function': body}


def spec_hash(task):
    return digest(normalized_spec(task))


def exclusion_hashes(inventory):
    require(inventory['schema'] == 'R119_SEALED_SPEC_HASHES_V1'
            and inventory['normalization'] == NORMALIZATION
            and inventory['attested_by'] == 'Main'
            and inventory['coverage'] == 'ALL_SEALED_NAMESPACES', 'sealed_metadata_coverage_required')
    namespaces = inventory['namespaces']
    require(isinstance(namespaces, dict) and namespaces, 'sealed_namespace_inventory_required')
    result = set()
    for namespace, hashes in namespaces.items():
        require(isinstance(namespace, str) and namespace and isinstance(hashes, list), 'namespace_hash_list')
        for value in hashes:
            require(isinstance(value, str) and len(value) == 64
                    and all(char in '0123456789abcdef' for char in value), 'normalized_sha256_only')
            result.add(value)
    return result


def task_spec(task):
    threshold, factor, offset = task['threshold'], task['factor'], task['offset']
    low, high = task['low'], task['high']
    return (
        f'Keep original values >= {threshold}; map each to {factor}*x+({offset}); sum the mapped values.',
        f'Map all values to {factor}*x+({offset}); clamp to [{low},{high}]; remove duplicates after clamping; sum.',
        f'Remove duplicate original values; keep values >= {threshold}; map to {factor}*x+({offset}); sum.',
        f'Clamp all values to [{low},{high}]; map to {factor}*x+({offset}); count mapped values >= {threshold}. Duplicates count separately.',
    )[task['kind']]


def build_tasks(seed, inventory):
    forbidden = exclusion_hashes(inventory) | {spec_hash(task) for task in ledger.build_tasks(count=64)}
    generator = random.Random(seed)
    tasks, reservations, occupied = [], [], set(forbidden)
    for split, count in COUNTS.items():
        for position in range(count):
            for attempt in range(10000):
                task = dict(kind=position % 4, factor=generator.choice([-7, -5, 5, 7]),
                            offset=generator.randint(-43, 43), low=-generator.randint(40, 100),
                            high=generator.randint(40, 100), threshold=generator.choice([-1, 1]) * generator.randint(20, 35))
                if task['kind'] == 3:
                    task['threshold'] = task['factor'] * task['threshold'] + task['offset']
                fingerprint = spec_hash(task)
                if fingerprint not in occupied:
                    break
            else:
                raise ValueError('disjoint_parameter_pool_exhausted')
            occupied.add(fingerprint)
            identity = f'R119_PUBLIC_{split}_{position:03d}_{fingerprint[:12]}'
            if split == 'CONFIRM':
                reservations.append({'id': identity, 'normalized_spec_sha256': fingerprint})
                continue
            boundary = normalized_spec(task)['function'][-1] if task['kind'] == 3 else task['threshold']
            task.update(id=identity, split=split, spec=task_spec(task), normalized_spec_sha256=fingerprint,
                        public_input=[boundary - 1, boundary, boundary + 1, task['low'] - 1, task['high'] + 1, 0, 0])
            probes = random.Random(int(fingerprint[:16], 16))
            task['verification_inputs'] = [[], [0], task['public_input'], [task['low'], task['low'], task['high']]]
            task['verification_inputs'] += [[probes.randint(-150, 150) for element in range(12)] for case in range(12)]
            tasks.append(task)
    return dict(schema=SOURCE, normalization=NORMALIZATION, generation_seed=seed,
                exclusions_sha256=digest(inventory), tasks=tasks, confirm_reservations=reservations,
                original64_spec_hashes=sorted({spec_hash(task) for task in ledger.build_tasks(count=64)}))


def expected(task, values):
    current = list(values)
    if task['kind'] == 2:
        current = list(dict.fromkeys(current))
    if task['kind'] in (0, 2):
        return sum(task['factor'] * value + task['offset'] for value in current if value >= task['threshold'])
    if task['kind'] == 1:
        current = [min(task['high'], max(task['low'], task['factor'] * value + task['offset'])) for value in current]
        return sum(dict.fromkeys(current))
    count = 0
    for value in current:
        clamped = min(task['high'], max(task['low'], value))
        if task['factor'] * clamped + task['offset'] >= task['threshold']:
            count += 1
    return count


def parse_action(text):
    action, reasoning = ledger.parse_action(text)
    require(set(action) == {'expression'}, 'expression_action_required_not_record')
    return action['expression']


def execute_public(task, text):
    result = dict(schema='R119_PUBLIC_INTERPRETER_V1', source='ACTUAL_PUBLIC_INPUT_INTERPRETER',
                  input=task['public_input'], hidden_tests_exposed=False, probe_attempted=True,
                  interpreter_started=False)
    try:
        expression = parse_action(text)
        result['expression'] = expression
        ledger.validate_expression(expression)
        result['interpreter_started'] = True
        result['observed'] = ledger.evaluate(expression, task['public_input'])
    except (ValueError, TypeError, SyntaxError, KeyError) as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
    return result


def verify(task, text):
    passed = 0
    try:
        expression = parse_action(text)
        for values in task['verification_inputs']:
            if ledger.evaluate(expression, values) != expected(task, values):
                return dict(success=False, passed=passed, total=len(task['verification_inputs']), reason='output_mismatch')
            passed += 1
        return dict(success=True, passed=passed, total=passed)
    except (ValueError, TypeError, SyntaxError, KeyError) as error:
        return dict(success=False, passed=passed, total=len(task['verification_inputs']), reason=type(error).__name__ + ': ' + str(error))


def messages(task, branch, history=()):
    require(task['split'] in ('TRAIN', 'DEV') and branch in BRANCHES and len(history) <= 2, 'declared_roles_and_two_revisions')
    result = [dict(role='system', content=CONTRACT), dict(role='user', content=task['spec'] +
              '\nOne public input is: ' + json.dumps(task['public_input']) + '. No expected output is supplied.')]
    for turn in history:
        if branch.endswith('_NO_FEEDBACK'):
            text = 'No execution feedback or new observation is supplied. You may revise or retain your answer. Do not invent observations.'
        else:
            feedback = turn['public']
            require(set(feedback) <= PUBLIC_KEYS and feedback == execute_public(task, turn['raw']), 'actual_interpreter_whitelist_no_gold_or_fabrication')
            text = 'Actual public-input interpreter diagnostic/output:\n' + json.dumps(feedback, sort_keys=True)
            text += '\nUse only this observation and the original public specification to revise or retain your answer.'
        result.extend([dict(role='assistant', content=turn['raw']), dict(role='user', content=text +
                       '\nUseful reasoning may precede the final line. Finish with a single-line '
                       '{"expression":"..."} object; values is the only input identifier.')])
    return result


def issues(text):
    result = dict(contract=False, ast=False, unknown=set(), arity=0, unsupported=0, values_used=False)
    try:
        expression = parse_action(text)
        result['contract'] = True
        tree = ast.parse(expression, mode='eval')
        result['ast'] = True
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == 'values':
                result['values_used'] = True
            if isinstance(node, ast.Name) and node.id not in {'values', *ledger.HELPERS}:
                result['unknown'].add(node.id)
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in ledger.ARITY:
                    result['unsupported'] += 1
                elif len(node.args) != ledger.ARITY[node.func.id] or node.keywords:
                    result['arity'] += 1
            if type(node) not in (ast.Expression, ast.Call, ast.Name, ast.Load, ast.Constant, ast.UnaryOp, ast.USub):
                result['unsupported'] += 1
    except (ValueError, TypeError, SyntaxError):
        pass
    return result


def correction(task, branch, before, after):
    initial, final = issues(before['raw']), issues(after['raw'])
    tags = []
    if not initial['contract'] and final['contract']:
        tags.append('OUTPUT_CONTRACT_REPAIRED')
    if initial['ast'] and final['ast']:
        if initial['unknown'] and not final['unknown'] and final['values_used']:
            tags.append('INPUT_IDENTIFIER_REPAIRED')
        if initial['arity'] and not final['arity']:
            tags.append('HELPER_ARITY_REPAIRED')
        if initial['unsupported'] and not final['unsupported']:
            tags.append('UNSUPPORTED_SYNTAX_REMOVED')
    public_before, public_after = execute_public(task, before['raw']), execute_public(task, after['raw'])
    if 'error' in public_before and 'observed' in public_after:
        tags.append('PUBLIC_EXECUTION_ERROR_RESOLVED')
    checked_before, checked_after = verify(task, before['raw']), verify(task, after['raw'])
    passed = checked_before['success'] is False and checked_after['success'] is True
    if passed:
        tags.append('TASK_CHECK_FAILED_TO_PASSED')
    terminal = all(turn['terminal'] and not turn['truncated'] for turn in (before, after))
    changed = before['raw'] != after['raw']
    eligible = task['split'] == 'TRAIN' and branch in ('CHILD_PUBLIC_FEEDBACK', 'CHILD_NO_FEEDBACK')
    return dict(semantic_tags=tags, before_success=checked_before['success'], after_success=checked_after['success'],
                verified_failed_to_passed=bool(passed and changed and terminal),
                potential_child_only_row=bool(eligible and changed and terminal and tags and final['values_used']),
                public_output_changed_unverified=('observed' in public_before and 'observed' in public_after
                                                  and public_before['observed'] != public_after['observed']),
                cap_hit_or_incomplete=not terminal, split=task['split'], branch=branch,
                source_label=SOURCE, human_review_required=True, semantic_review='PENDING',
                functional_admission=False, rows_admitted=0, fit_updates=0,
                metacognition_claim=False, causal_feedback_claim=False)


def validate_plan(plan, allocation, now):
    require(all(plan[key] == allocation[key] for key in ('source_label', 'root', 'physical', 'uuid', 'counts',
                'max_responses', 'max_new_tokens', 'context_limit', 'native_end_unix', 'external_end_unix',
                'lease_end_unix', 'lease_margin_seconds', 'revisions', 'decoder', 'response_caps')), 'exact_Main_allocation_no_quota_reset')
    require(allocation['approved_by'] == 'Main' and allocation['status'] == 'APPROVED', 'explicit_new_allocation_required')
    require(plan['source_label'] == SOURCE and plan['counts'] == COUNTS and plan['revisions'] == 2, 'exact_R119_shape')
    require(plan['physical'] == 7 and plan['uuid'] == pilot.UUID, 'only_newly_allocated_node2_physical7')
    require(plan['max_responses'] == 240 and plan['response_caps'] == RESPONSE_CAPS
            and plan['max_new_tokens'] == 2048 and plan['context_limit'] == 16384,
            '240_unique_responses_shared_drafts_2048_token_16384_context_caps')
    require(plan['native_end_unix'] == NATIVE_END and plan['external_end_unix'] == EXTERNAL_END
            and now < NATIVE_END < EXTERNAL_END <= plan['lease_end_unix'] - plan['lease_margin_seconds']
            and plan['lease_margin_seconds'] > 0, 'fixed_new_bounds_with_actual_lease_margin')
    require(plan['decoder'] == DECODER and plan['fit_allowed'] is False and plan['parents'] == 0, 'collection_only_same_decoder')
    require(Path(plan['root']).is_absolute() and Path(plan['root']).is_relative_to('/localhome/local-rohing'), 'raw_node_local_only')


def pinned(reference):
    require(sha(reference['path']) == reference['sha256'], 'pinned_input_hash')
    return read(reference['path'])


def verify_sources(files):
    root = Path(__file__).resolve().parents[1]
    required = {Path(__file__).resolve(), Path(pilot.__file__).resolve(), Path(ledger.__file__).resolve()}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.suffix == '.py' and any(path.is_relative_to(root / folder) for folder in ('gpu', 'organism_v6')):
                required.add(path)
    require(all(files.get(str(path)) == sha(path) for path in required), 'loaded_runtime_source_closure_pinned')
    for path, fingerprint in files.items():
        require(sha(path) == fingerprint, 'frozen_source_closure')


def validate_seed(seed, optimizer_file):
    require(seed['adapter']['state_sha256'] == SEED_STATE and seed['adapter']['base_sha256'] == BASE_SHA
            and seed['optimizer_sha256'] == OPTIMIZER_SHA, 'exact_frozen_C2_FULL15332_base_seed')
    require(Path(seed['checkpoint']).name == '000015332', 'seed_update_15332')
    require(sha(optimizer_file) == OPTIMIZER_SHA, 'original_optimizer_provenance_not_loaded')


def prepare(request, root):
    require(not root.exists(), 'new_immutable_root_only')
    allocation, seed, exclusions = (pinned(request[key]) for key in ('allocation', 'seed', 'exclusions'))
    plan = dict(request['plan'], root=str(root), allocation=request['allocation'], seed=request['seed'], exclusions=request['exclusions'])
    validate_plan(plan, allocation, time.time())
    validate_seed(seed, request['optimizer_file'])
    plan.update(optimizer_file=request['optimizer_file'], source_files=request['source_files'])
    verify_sources(plan['source_files'])
    tasks = build_tasks(request['generation_seed'], exclusions)
    root.mkdir(parents=True)
    write(root / 'TASKS.json', tasks)
    plan['tasks_sha256'] = sha(root / 'TASKS.json')
    write(root / 'PLAN.json', plan)
    write(root / 'PREPARED.json', dict(plan_sha256=sha(root / 'PLAN.json'), counts=COUNTS, max_responses=240,
                                      confirm_reservations=tasks['confirm_reservations'], status='NOT_LAUNCHED'))


def verified(root):
    plan = read(root / 'PLAN.json')
    validate_plan(plan, pinned(plan['allocation']), time.time())
    require(Path(plan['root']).resolve() == root.resolve(), 'exact_root')
    require(sha(root / 'TASKS.json') == plan['tasks_sha256'], 'immutable_task_manifest')
    tasks = read(root / 'TASKS.json')
    require(tasks == build_tasks(tasks['generation_seed'], pinned(plan['exclusions'])), 'rederived_disjoint_tasks')
    seed = pinned(plan['seed'])
    validate_seed(seed, plan['optimizer_file'])
    verify_sources(plan['source_files'])
    return plan, seed, tasks


def run_episodes(root, plan, tasks, generate, clock=time.time):
    reserved = 0
    split_reserved = {'TRAIN': 0, 'DEV': 0}
    cap_hits = 0
    incomplete = 0
    generated_tokens = 0
    summaries = []

    def call(task, model, branch, folder, stage, history):
        nonlocal reserved, cap_hits, incomplete, generated_tokens
        require(clock() < plan['native_end_unix'] and reserved < plan['max_responses']
                and split_reserved[task['split']] < plan['response_caps'][task['split']], 'fixed_bound_no_retry')
        prefix = messages(task, branch, history)
        intent = dict(source_label=SOURCE, task_id=task['id'], split=task['split'], model=model,
                      branch='SHARED_DRAFT' if stage == 'draft' else branch, stage=stage,
                      stage_role='TRAIN_FEEDBACK_MINING' if task['split'] == 'TRAIN' else 'DEV_PARENT_FREE_FEEDBACK_UPTAKE_READOUT',
                      normalized_spec_sha256=task['normalized_spec_sha256'], messages=prefix,
                      reserved_response=reserved + 1, max_new_tokens=plan['max_new_tokens'], context_limit=plan['context_limit'],
                      seed_state_sha256=SEED_STATE, decoder=DECODER, parents=0, optimizer_count=0,
                      task_manifest_sha256=digest(tasks), source_manifest_sha256=digest(plan.get('source_files', {})),
                      trainingAllowed=False, time_unix=clock())
        write(folder / (stage + '.INTENT.json'), intent)
        reserved += 1
        split_reserved[task['split']] += 1
        response = generate(prefix, model)
        call_path = folder / (stage + '.CALL.json')
        write(call_path, dict(intent, response=response))
        public = execute_public(task, response['raw'])
        write(folder / (stage + '.PUBLIC.json'), public)
        write(folder / (stage + '.VERIFY.json'), verify(task, response['raw']))
        cap_hits += int(response['truncated'])
        incomplete += int(not response['terminal'])
        generated_tokens += len(response.get('token_ids', []))
        return dict(raw=response['raw'], public=public, terminal=response['terminal'], truncated=response['truncated'],
                    call=dict(path=str(call_path), sha256=sha(call_path)))

    for task in tasks['tasks']:
        for model in MODELS:
            model_folder = root / 'episodes' / task['id'] / model
            model_folder.mkdir(parents=True, exist_ok=False)
            draft = call(task, model, model + '_PUBLIC_FEEDBACK', model_folder, 'draft', [])
            for branch in (model + '_PUBLIC_FEEDBACK', model + '_NO_FEEDBACK'):
                folder = model_folder / branch
                folder.mkdir(exist_ok=False)
                write(folder / 'SHARED_DRAFT.json', dict(draft['call'], reference_only_not_new_response=True))
                history, changes = [draft], []
                for stage in ('revision1', 'revision2'):
                    current = call(task, model, branch, folder, stage, history)
                    change = correction(task, branch, history[-1], current)
                    change['source_calls'] = dict(before=history[-1]['call'], after=current['call'])
                    changes.append(change)
                    history.append(current)
                complete = dict(task_id=task['id'], split=task['split'], branch=branch, revisions=changes,
                                shared_draft=draft['call'], unique_responses_owned=2, response_references=3,
                                cap_hits_including_shared_draft=sum(turn['truncated'] for turn in history),
                                candidate_stage='REVIEW_ONLY_NOT_INGESTION', all_raw_retained=True)
                write(folder / 'COMPLETE.json', complete)
                summaries.append(complete)
    return dict(status='COMPLETE', responses_reserved=reserved, completed_episodes=len(summaries), results=summaries,
                split_responses_reserved=split_reserved, unique_draft_calls=len(tasks['tasks']) * len(MODELS),
                unique_cap_hits=cap_hits, unique_incomplete_responses=incomplete, generated_tokens=generated_tokens,
                optimizer_steps=0, rows_admitted=0, retry_allowed=False, confirm_calls=0, time_unix=clock())


def collect(root):
    from gpu import orch_guided_native as native
    from gpu.orch_r107_capability_run import readonly_condition
    from gpu.orch_rich_hot_node2_exhaustion_v3 import Engine
    from organism_v6 import orch_guided_bridge as bridge

    plan, seed, tasks = verified(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['uuid'], 'exact_single_GPU')
    require(read(root / 'ADMISSION.json')['clear'] is True and (root / 'GUARD_START.json').exists(), 'guard_admission_required')
    write(root / 'NATIVE_START.json', dict(identity=pilot.identity(), plan_sha256=sha(root / 'PLAN.json')))
    adapter = bridge.AdapterIdentity.from_document(seed['adapter'])
    binding = bridge.StageBinding(root.name, bridge.ARMS[1], 0, 'sealed_readout', adapter, False, True, sha(root / 'PLAN.json'))

    def check(label):
        require(time.time() < plan['native_end_unix'], 'native_deadline:' + label)

    try:
        loaded = native.load_stage(binding, model_dir=plan['model_dir'], device='cuda:0', gpu_uuid=plan['uuid'],
                                   context=native.StageContext(), check=check, engine_factory=Engine)
        write(root / 'LOADED.json', dict(identity=pilot.identity(), adapter=loaded.observed.document(), optimizer_count=0,
                                       optimizer_sha256=OPTIMIZER_SHA, time_unix=time.time()))

        def generate(prefix, model):
            require(len(loaded.engine.prompt_tokens(prefix)) + plan['max_new_tokens'] <= plan['context_limit'], 'no_context_trim_or_budget_shrink')
            condition = 'LORA_OFF' if model == 'BASE' else 'LORA_ON'
            with readonly_condition(loaded.engine.model, condition):
                return loaded.engine.generate(prefix, max_new_tokens=plan['max_new_tokens'])

        result = run_episodes(root, plan, tasks, generate)
        loaded.verify_unchanged()
        require(sha(plan['optimizer_file']) == OPTIMIZER_SHA, 'original_optimizer_unchanged')
    except BaseException as error:
        write(root / 'TERMINAL.json', dict(status='FAILED_OR_BOUNDED_STOP', error=type(error).__name__ + ': ' + str(error),
                                          responses_reserved=len(list((root / 'episodes').rglob('*.INTENT.json'))),
                                          optimizer_steps=0, rows_admitted=0, retry_allowed=False, time_unix=time.time()))
        raise
    write(root / 'TERMINAL.json', result)


def guard(root):
    from gpu.orch_rich_hot_node2_scan import scan

    plan, seed, tasks = verified(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES', '') == '', 'CPU_guard_CVD_empty')
    ready, release = read(root / 'PRE_GPU.json'), read(root / 'RELEASE.json')
    require(ready['cpu_passed'] is True and ready['plan_sha256'] == sha(root / 'PLAN.json')
            and ready['release_sha256'] == sha(root / 'RELEASE.json'), 'dated_builder_CPU_release_receipt')
    require(release['status'] == 'RELEASED' and sha(release['terminal']['path']) == release['terminal']['sha256'], 'verified_R109_natural_release')
    require(all(not Path('/proc', str(pid)).exists() for pid in release['old_group_pids']), 'old_owned_processes_absent')
    write(root / 'GUARD_START.json', dict(identity=pilot.identity(), plan_sha256=sha(root / 'PLAN.json')))
    admission = scan(plan['physical'], Path(plan['service_identity']))
    admission.pop('host', None)
    write(root / 'ADMISSION.json', admission)
    require(admission['clear'] and admission['scanner_euid'] == 0 and admission['gpu']['uuid'] == plan['uuid'], 'strict_fresh_ownership')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                       OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1')
    with (root / 'NATIVE.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), 'collect', '--root', str(root)],
                                 env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        identity = pilot.identity(child.pid)
        write(root / 'LAUNCH.json', dict(identity=identity, native_end_unix=plan['native_end_unix'], external_end_unix=plan['external_end_unix']))
        try:
            child.wait(timeout=max(.001, plan['native_end_unix'] - time.time()))
        except subprocess.TimeoutExpired:
            require(pilot.identity(child.pid) == identity, 'exact_owned_native_identity')
            write(root / 'CUTOFF.json', dict(identity=identity, time_unix=time.time()))
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=max(.001, min(15, plan['external_end_unix'] - time.time())))
            except subprocess.TimeoutExpired:
                require(pilot.identity(child.pid) == identity, 'exact_owned_kill_identity')
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=max(.001, plan['external_end_unix'] - time.time()))
    write(root / 'GUARD_TERMINAL.json', dict(returncode=child.returncode, identity=identity, time_unix=time.time(), retry_allowed=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'guard', 'collect'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--request', type=Path)
    options = parser.parse_args()
    if options.action == 'prepare':
        require(options.request is not None, 'request_required')
        prepare(read(options.request), options.root)
    else:
        (guard if options.action == 'guard' else collect)(options.root)
