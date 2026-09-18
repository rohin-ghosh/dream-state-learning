"""Fresh, common-cohort transfer evaluation of the historical canonical learners."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


SCHEMA = 'R127_CANONICAL_FRESH_TRANSFER_V1'
PREFIX = 'ORCH-ROUTE-PARENT-20260915-R127-TRANSFER-'
CYCLES = (2, 4, 6)
CONDITIONS = ('SEED',) + tuple(f'{arm}_C{cycle}' for arm in ('GUIDED', 'UNPARENTED') for cycle in CYCLES)
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
SEED = 'd13fabd566e04926f45aa66ee0a30ff7dc88d411430ab3e1fe15dfffeb2fd27f'
WORLDS = 16
CAP = 512
SOURCE_CALLS = WORLDS * 8
CONDITION_CALLS = WORLDS * 2 * 6
TOTAL_CALLS = SOURCE_CALLS + len(CONDITIONS) * CONDITION_CALLS
HISTORICAL_RUNTIME = ('gpu/orch_guided_native.py', 'gpu/orch_route_parent_campaign_run.py',
    'organism_v6/orch_l2_guided.py', 'organism_v6/orch_full_rich.py',
    'organism_v6/orch_replication.py', 'organism_v6/experienced_event_two_hop.py')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def checked(reference):
    require(sha(reference['path']) == reference['sha256'], 'bound_input_hash')
    return read(reference['path'])


def identifiers(value):
    return set(re.findall(r'\b[NEPR]_[A-Za-z0-9_]+\b', json.dumps(value, sort_keys=True)))


def fresh_cohort(exclusions):
    from organism_v6 import orch_route_parent_campaign as policy
    from organism_v6 import orch_full_rich as rich
    seen = set(exclusions)
    worlds, tasks = [], []
    for index in range(WORLDS):
        master = PREFIX + f'W{index:02d}'
        world = policy.runtime(master)['build_world'](master)
        actual = identifiers(world)
        require(actual and not actual.intersection(seen), 'fresh_namespace_collision')
        seen.update(actual)
        worlds.append(world)
        for ordinal, task in enumerate(policy.shared.tasks(world)):
            messages = [dict(role='system', content=rich.SYSTEM),
                        dict(role='user', content=rich.readout.display(task['node'], task, list(task['ports'])))]
            tasks.append(dict(task_id=f'W{index:02d}_T{ordinal}', world_id=master,
                world_index=index, task=task, task_sha256=digest(task),
                initial_prompt_sha256=digest(messages), split='DEV_DIAGNOSTIC', trainingAllowed=False))
    require(len(tasks) == WORLDS * 2, 'two_tasks_per_world')
    return dict(schema=SCHEMA, worlds=worlds, tasks=tasks, exclusions_sha256=digest(sorted(exclusions)),
        parent_input_allowed=False, final_tasks_used=False, trainingAllowed=False)


def export(canonical_root, output):
    canonical_root, output = Path(canonical_root).resolve(), Path(output).resolve()
    require(not output.exists() and not output.is_relative_to(canonical_root), 'new_export_only')
    prepared = read(canonical_root / 'PREPARE.json')
    initial = prepared['initial']
    require(initial['state_sha256'] == SEED and initial['base_sha256'] == BASE, 'canonical_seed_identity')
    prior_cohort = read(canonical_root / 'COHORT.json')
    require(prepared['inputs']['COHORT.json'] == sha(canonical_root / 'COHORT.json'), 'original_cohort_binding')
    exclusion_inputs = []
    excluded = identifiers(prior_cohort)
    for name in ('COHORT.json', 'LEGACY_READOUT.json', 'LEGACY_MATERIAL.json'):
        source = canonical_root / name
        require(source.exists() and prepared['inputs'][name] == sha(source), 'original_exclusion_input')
        excluded.update(identifiers(read(source)))
        exclusion_inputs.append(ref(source))
    cohort = fresh_cohort(excluded)
    output.mkdir(parents=True)
    write(output / 'COHORT.json', cohort)
    conditions = {'SEED': dict(arm='SEED', cycle=0, updates=0, adapter=initial)}
    history = {}
    for arm in ('GUIDED', 'UNPARENTED'):
        previous, total, receipts = initial, 0, []
        for cycle in range(1, max(CYCLES) + 1):
            path = canonical_root / arm / f'cycle{cycle}/sleep/COMPLETE.json'
            complete = read(path)
            require(complete['arm'] == arm and complete['cycle'] == cycle
                    and complete['phase'] == 'sleep' and complete['status'] == 'COMPLETE', 'actual_completed_sleep')
            require(complete['input_adapter'] == previous, 'consecutive_same_child_lineage')
            require(complete['output_adapter']['base_sha256'] == BASE, 'same_frozen_base')
            total += complete['updates']
            previous = complete['output_adapter']
            target = output / 'history' / arm / f'C{cycle}.json'
            write(target, complete)
            receipts.append(dict(origin=ref(path), copied=str(target.relative_to(output)), updates=complete['updates']))
            if cycle in CYCLES:
                conditions[f'{arm}_C{cycle}'] = dict(arm=arm, cycle=cycle, updates=total,
                    adapter=previous, original_sleep=ref(path))
        history[arm] = receipts
    for name, item in conditions.items():
        folder = output / 'conditions' / name / 'adapter'
        folder.mkdir(parents=True)
        for filename, expected in item['adapter']['files']:
            require(Path(filename).name == filename, 'flat_adapter_files')
            source = Path(item['adapter']['path']) / filename
            require(sha(source) == expected, 'original_adapter_hash')
            shutil.copy2(source, folder / filename)
            require(sha(folder / filename) == expected, 'copied_adapter_hash')
        item['original_adapter_path'] = item['adapter']['path']
        item['adapter'] = dict(item['adapter'], path=str(folder.relative_to(output)))
    files = {str(path.relative_to(output)): sha(path) for path in output.rglob('*') if path.is_file()}
    write(output / 'EXPORT.json', dict(schema=SCHEMA, conditions=conditions, history=history,
        files=files, exclusions=exclusion_inputs, original_prepare=ref(canonical_root / 'PREPARE.json'),
        original_source_files=prepared['source_files'], cohort_sha256=sha(output / 'COHORT.json'),
        selection='FIXED_C2_C4_C6_NOT_SELECTED_ON_TRANSFER_OUTCOMES', created_unix=time.time()))


def validate(plan_path):
    plan = read(plan_path)
    require(plan['schema'] == SCHEMA and plan['wrapper'] == 'ovx' and plan['physical'] == 7, 'owned_assay_device')
    require(plan['parent_calls'] == plan['optimizer_steps'] == plan['training_rows'] == 0, 'evaluation_only')
    require(plan['max_native_calls'] == TOTAL_CALLS and plan['response_cap'] == CAP, 'fixed_call_budget')
    require(time.time() < plan['hard_end_unix'] <= plan['lease_end_unix'] - 21600
            and plan['hard_end_unix'] - plan['created_unix'] <= 10800, 'bounded_lease_wall')
    require(sha(plan['service_identity']) == plan['service_identity_sha256'], 'service_identity_binding')
    for path, expected in plan['source_files'].items():
        require(sha(path) == expected, 'frozen_source_file')
    bundle = Path(plan['bundle'])
    require(sha(bundle / 'EXPORT.json') == plan['export_sha256'], 'export_binding')
    exported = read(bundle / 'EXPORT.json')
    require(set(exported['conditions']) == set(CONDITIONS), 'all_fixed_checkpoints')
    for name in HISTORICAL_RUNTIME:
        require(sha(Path(plan['source_root']) / name) == exported['original_source_files'][name],
                'historical_runtime_contract:' + name)
    for name, expected in exported['files'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'relative_export_file')
        require(sha(bundle / name) == expected, 'frozen_export_file')
    cohort = read(bundle / 'COHORT.json')
    require(len(cohort['worlds']) == WORLDS and len(cohort['tasks']) == WORLDS * 2
            and not cohort['trainingAllowed'] and not cohort['final_tasks_used'], 'fixed_unexposed_cohort')
    return plan, exported, cohort


def reserve(root, condition, messages):
    with (root / 'BUDGET.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        folder = root / 'claims'
        folder.mkdir(exist_ok=True)
        claims = sorted(folder.glob('CALL_*.json'))
        require(len(claims) < TOTAL_CALLS, 'total_budget_exhausted')
        require([path.name for path in claims] == [f'CALL_{index:05d}.json' for index in range(1, len(claims)+1)],
                'contiguous_charged_history')
        own = sum(read(path)['condition'] == condition for path in claims)
        limit = SOURCE_CALLS if condition == 'SOURCE' else CONDITION_CALLS
        require(own < limit, 'condition_budget_exhausted')
        path = folder / f'CALL_{len(claims)+1:05d}.json'
        write(path, dict(condition=condition, messages_sha256=digest(messages), cap=CAP,
            trainingAllowed=False, reserved_unix=time.time(), no_retry=True))
        return path


def stage(plan_path, condition):
    from gpu import orch_guided_native as native
    from gpu import orch_route_parent_campaign_run as run
    plan, exported, cohort = validate(plan_path)
    require(condition in ('SOURCE',) + CONDITIONS, 'planned_condition')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['uuid'], 'single_exact_device')
    require(os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_model')
    root = Path(plan['output'])
    output = root / condition
    output.mkdir(exist_ok=False)
    identity_data = exported['conditions']['SEED' if condition == 'SOURCE' else condition]['adapter']
    identity = native.bridge.AdapterIdentity.from_document(dict(identity_data,
        path=str(Path(plan['bundle']) / identity_data['path'])))
    require(identity.base_sha256 == BASE, 'exact_frozen_base')
    binding = native.bridge.StageBinding(root.name + '_' + condition, native.bridge.ARMS[0], 0,
        'sealed_readout', identity, False, True, sha(plan_path))
    write(output / 'BINDING.json', asdict(binding))
    def check(label):
        require(time.time() < plan['hard_end_unix'], 'lease_or_assay_wall:' + str(label))
    loaded = native.load_stage(binding, model_dir=plan['model_dir'], device='cuda:0', gpu_uuid=plan['uuid'],
        context=native.StageContext(), check=check, engine_factory=run.Engine)
    require(loaded.optimizer is None and loaded.observed == identity, 'read_only_actual_checkpoint')
    write(output / 'LOADED.json', dict(process=loaded.process, adapter=loaded.observed.document(),
        condition=condition, parent_free=True, fresh_process=True, optimizer_steps=0, loaded_unix=time.time()))
    def generate(messages):
        check('generate')
        claim = reserve(root, condition, messages)
        result = dict(condition=condition, messages=deepcopy(messages), claim=ref(claim), started_unix=time.time())
        try:
            result['response'] = loaded.engine.generate(messages, max_new_tokens=CAP)
            require(result['response']['messages'] == messages, 'capture_prompt_binding')
            result['status'] = 'COMPLETE'
            return result['response']
        except BaseException as error:
            result.update(status='FAILED', error_type=type(error).__name__)
            raise
        finally:
            result['finished_unix'] = time.time()
            write(output / 'calls' / claim.name, result)
    if condition == 'SOURCE':
        collections, store = [], {}
        for index, world in enumerate(cohort['worlds']):
            runtime = run.policy.runtime(world['master'])
            collection = runtime['collect_world'](world, generate)
            runtime['replay_collection'](collection)
            write(output / f'WORLD_{index:02d}.json', collection)
            collections.append(collection)
            for record in collection['records']:
                if record['accepted']:
                    store[record['edge']['event']] = record['event']['raw']
        write(output / 'STORE.json', dict(store=store, source_store_sha256=digest(store),
            worlds=WORLDS, accepted_events=len(store), offered_events=WORLDS*4,
            complete_worlds=sum(item['ready'] for item in collections),
            trainingAllowed=False, policy='COMMON_INITIAL_CHILD_RAW_EVENTS_NO_FABRICATION_OR_FILTERING'))
        episodes = []
    else:
        require((root / 'SOURCE/COMPLETE.json').exists(), 'completed_shared_source_required')
        source_complete = read(root / 'SOURCE/COMPLETE.json')
        source = checked(source_complete['store'])
        episodes = []
        for row in cohort['tasks']:
            world = cohort['worlds'][row['world_index']]
            record = run.guided.episode(world, row['task'], generate, source['store'], parent=None, rich_contract=False)
            require(record['task'] == row['task'] and not record['parent_messages'], 'parent_free_exact_task')
            require(not record['captures'] or digest(record['captures'][0]['messages']) == row['initial_prompt_sha256'],
                    'same_initial_prompt_all_checkpoints')
            record.update(condition=condition, world_id=row['world_id'], task_id=row['task_id'],
                task_sha256=row['task_sha256'], checkpoint_state_sha256=identity.state_sha256,
                initial_prompt_sha256=row['initial_prompt_sha256'], source_store_sha256=source['source_store_sha256'],
                trainingAllowed=False, split='DEV_DIAGNOSTIC')
            path = output / f'EPISODE_{len(episodes):02d}.json'
            write(path, record)
            episodes.append(ref(path))
    loaded.verify_unchanged()
    calls = [ref(path) for path in sorted((output / 'calls').glob('CALL_*.json'))]
    write(output / 'COMPLETE.json', dict(status='COMPLETE', condition=condition, episodes=episodes, calls=calls,
        store=ref(output / 'STORE.json') if condition == 'SOURCE' else source_complete['store'],
        adapter=loaded.observed.document(), parent_calls=0, optimizer_steps=0, training_rows=0,
        unchanged=True, finished_unix=time.time(), semantic_improvement='UNPROVEN'))


def supervise(plan_path):
    from gpu.orch_rich_hot_node2_scan import scan
    plan, unused_export, unused_cohort = validate(plan_path)
    root = Path(plan['output'])
    root.mkdir(exist_ok=False)
    write(root / 'START.json', dict(pid=os.getpid(), plan=ref(plan_path), started_unix=time.time()))
    results = []
    for condition in ('SOURCE',) + CONDITIONS:
        if condition != 'SOURCE' and not (root / 'SOURCE/COMPLETE.json').exists():
            break
        while time.time() < plan['hard_end_unix']:
            try:
                report = scan(7, Path(plan['service_identity']))
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                report = dict(clear=False, error_type=type(error).__name__)
            report.pop('host', None)
            write(root / 'admissions' / f'{condition}_{time.time_ns()}.json', report)
            if report['clear']:
                require(report['scanner_euid'] == 0 and report['gpu']['uuid'] == plan['uuid'], 'privileged_exact_UUID')
                break
            time.sleep(2)
        else:
            break
        environment = {key: value for key, value in os.environ.items() if not key.startswith(('PARENT_', 'CLAUDE_'))}
        environment.update(CUDA_VISIBLE_DEVICES=plan['uuid'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
            PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=plan['source_root'])
        with (root / f'{condition}.log').open('x') as stream:
            process = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_r127_route_transfer', 'stage',
                '--plan', str(plan_path), '--condition', condition], env=environment,
                stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            write(root / f'{condition}_LAUNCH.json', dict(pid=process.pid, started_unix=time.time(), condition=condition))
            try:
                process.wait(timeout=max(1, plan['hard_end_unix'] - time.time()))
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        outcome = dict(condition=condition, returncode=process.returncode,
            complete=(root / condition / 'COMPLETE.json').exists(), finished_unix=time.time(), no_retry=True)
        write(root / f'{condition}_EXIT.json', outcome)
        results.append(outcome)
    write(root / 'TERMINAL.json', dict(status='COMPLETE' if len(results) == len(CONDITIONS)+1
        and all(item['complete'] and item['returncode'] == 0 for item in results) else 'INCOMPLETE',
        results=results, parent_calls=0, optimizer_steps=0, training_rows=0, finished_unix=time.time()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('export', 'validate', 'stage', 'supervise'))
    parser.add_argument('--canonical-root', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--condition', choices=('SOURCE',) + CONDITIONS)
    args = parser.parse_args()
    if args.action == 'export':
        export(args.canonical_root, args.output)
    elif args.action == 'validate':
        validate(args.plan)
        print('CPU_METADATA_VALID_NO_GPU_CALLS')
    elif args.action == 'stage':
        stage(args.plan, args.condition)
    else:
        supervise(args.plan)


if __name__ == '__main__':
    main()
