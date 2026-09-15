"""Read-only, matched public-context probes of consecutive route checkpoints."""

import argparse
from contextlib import nullcontext
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


SCHEMA = 'R124_ROUTE_MATCHED_PUBLIC_PROBE_V1'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
MINIMAL = 'Use the public task and available records. End with READ EVENT <listedaddress> or ROUTE <listedport>.'
EXPLANATION = (
    'Briefly explain which available observations inform your next action and what remains unknown. '
    'Use only observations actually supplied; do not invent a record or a result. '
    'Then end with READ EVENT <listedaddress> or ROUTE <listedport>.'
)
CONDITIONS = ('BEFORE', 'AFTER', 'AFTER_LORA_OFF')
CAP = 512
BATCH = 4


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def reference(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def select_checkpoints(root):
    candidates = []
    for path in Path(root).glob('cycle_*/checkpoint/CHECKPOINT.json'):
        document = read(path)
        sleep_path = path.parent.parent / 'SLEEP.json'
        if document.get('complete') is not True or not sleep_path.is_file():
            continue
        sleep = read(sleep_path)
        require(sleep['checkpoint_sha256'] == sha(path), 'saved_sleep_checkpoint_binding')
        require(document['adapter']['base_sha256'] == BASE_SHA, 'frozen_base_identity')
        candidates.append((document['cycle'], path, document))
    candidates.sort(key=lambda item: item[0])
    require(len(candidates) >= 2, 'two_durable_checkpoints_required')
    before, after = candidates[-2:]
    require(after[0] == before[0] + 1, 'consecutive_cycles_required')
    require(after[2]['sleeps'] == before[2]['sleeps'] + 1, 'exactly_one_sleep_difference')
    require(after[2]['saved_unix'] > before[2]['saved_unix'], 'checkpoint_time_order')
    return {'BEFORE': before[1], 'AFTER': after[1]}


def public_prompts(cohort, display):
    held = cohort['held']
    require(len(held) == 8 and len({entry['id'] for entry in held}) == 8, 'eight_unique_DEV_tasks')
    require(not ({entry['id'] for entry in held} & {entry['id'] for entry in cohort['train']}),
            'DEV_TRAIN_ids_disjoint')
    result = []
    for entry in held:
        task = entry['task']
        require(bool(task['events']), 'public_record_address_required')
        address = task['events'][0]
        require(address in cohort['store'], 'actual_public_record_required')
        initial = display(task['node'], task, list(task['ports']))
        contexts = {
            'INITIAL': initial,
            'PUBLIC_RECORD': initial + '\n\nA public observation is supplied below.\n'
                + 'READ EVENT ' + address + '\nMEMORY RESULT\n' + cohort['store'][address],
        }
        for context, observation in contexts.items():
            for style, policy in [('MINIMAL', MINIMAL), ('EXPLANATION_REQUESTED', EXPLANATION)]:
                messages = [dict(role='system', content=policy), dict(role='user', content=observation)]
                result.append(dict(id=f'{entry["id"]}:{context}:{style}', task_id=entry['id'],
                    context=context, style=style, messages=messages, messages_sha256=digest(messages),
                    split='DEV_DIAGNOSTIC', trainingAllowed=False, parent_present=False,
                    carried_context=False, public_record_selection='FIRST_LISTED_NOT_SCORE_SELECTED'))
    return result


def export_bundle(branch, root, output):
    from organism_v6 import orch_full_rich as gym
    root, output = Path(root).resolve(), Path(output).resolve()
    require(branch in ('F1', 'A1'), 'route_branch_only')
    require(not output.exists(), 'new_export_namespace_no_overwrite')
    plan = read(root / 'R121_INDEPENDENT_PLAN_V2.json')
    require(plan['branch'] == branch, 'actual_branch_binding')
    require(sha(root / 'COHORT.json') == plan['cohort_sha256'], 'frozen_cohort')
    selected = select_checkpoints(root)
    prompts = public_prompts(read(root / 'COHORT.json'), gym.readout.display)
    output.mkdir(parents=True, mode=0o700)
    write(output / 'PROMPTS.json', prompts)
    snapshots = {}
    for condition, path in selected.items():
        document = read(path)
        target = output / condition
        target.mkdir()
        shutil.copy2(path, target / 'CHECKPOINT.json')
        (target / 'adapter').mkdir()
        for name, expected in document['adapter']['files']:
            require(Path(name).name == name, 'flat_adapter_files_only')
            source = Path(document['adapter']['path']) / name
            require(sha(source) == expected, 'original_adapter_file_hash')
            shutil.copy2(source, target / 'adapter' / name)
            require(sha(target / 'adapter' / name) == expected, 'copied_adapter_file_hash')
        require(sha(path) == sha(target / 'CHECKPOINT.json'), 'checkpoint_copy_hash')
        snapshots[condition] = dict(origin=reference(path), cycle=document['cycle'],
            sleeps=document['sleeps'], saved_unix=document['saved_unix'],
            adapter_state_sha256=document['adapter']['state_sha256'])
    files = {str(path.relative_to(output)): sha(path) for path in output.rglob('*') if path.is_file()}
    write(output / 'EXPORT.json', dict(schema=SCHEMA, branch=branch, created_unix=time.time(),
        source_root=str(root), source_plan=reference(root / 'R121_INDEPENDENT_PLAN_V2.json'),
        source_cohort=reference(root / 'COHORT.json'), checkpoints=snapshots, files=files,
        prompts_sha256=sha(output / 'PROMPTS.json'), conditions=list(CONDITIONS),
        max_native_calls=96, response_cap=CAP, batch_size=BATCH, parent_calls=0, optimizer_steps=0,
        new_diagnostic_not_historical_readout_retry=True, outcome_or_checkpoint_selection=False,
        final_read=False, raw_text_retained=True))
    return reference(output / 'EXPORT.json')


def verify_bundle(bundle):
    bundle = Path(bundle)
    document = read(bundle / 'EXPORT.json')
    require(document['schema'] == SCHEMA and document['branch'] in ('F1', 'A1'), 'exact_export_schema')
    require(document['conditions'] == list(CONDITIONS) and document['max_native_calls'] == 96,
            'fixed_call_budget')
    require(document['parent_calls'] == document['optimizer_steps'] == 0 and not document['final_read'],
            'evaluation_only')
    for relative, expected in document['files'].items():
        path = Path(relative)
        require(not path.is_absolute() and '..' not in path.parts, 'bundle_relative_files')
        require(sha(bundle / path) == expected, 'immutable_bundle_file')
    prompts = read(bundle / 'PROMPTS.json')
    require(len(prompts) == 32 and len({row['id'] for row in prompts}) == 32, 'thirty_two_fixed_prompts')
    for row in prompts:
        require(row['messages_sha256'] == digest(row['messages']), 'actual_prompt_hash')
        require([entry['role'] for entry in row['messages']] == ['system', 'user'], 'empty_actor_context')
        require(row['split'] == 'DEV_DIAGNOSTIC' and row['trainingAllowed'] is False
                and row['parent_present'] is False and row['carried_context'] is False, 'visibility_contract')
    return document, prompts


def metrics(response, tokenizer):
    raw = response['raw']
    lines = raw.rstrip().splitlines()
    action = lines[-1] if lines and re.fullmatch(r'(READ EVENT|ROUTE) \S+', lines[-1]) else None
    rationale = '\n'.join(lines[:-1]) if action else raw
    words = raw.split()
    grams = list(zip(words, words[1:], words[2:], words[3:]))
    return dict(generated_tokens=len(response['token_ids']), raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        rationale_tokens=len(tokenizer.encode(rationale, add_special_tokens=False)),
        valid_final_action=action is not None, action=action,
        terminal=response['terminal'], truncated=response['truncated'],
        repeated_fourgram_fraction=(len(grams) - len(set(grams))) / len(grams) if grams else 0.0,
        semantic_coherence='UNJUDGED', retained_improvement='UNPROVEN')


def finalize_readonly(loaded):
    require(loaded.binding.phase == 'sealed_readout' and loaded.optimizer is None,
            'readout_only_gradient_flag_restore')
    loaded.engine.model.requires_grad_(False)
    return loaded.verify_unchanged()


def verify_plan(path):
    plan = read(path)
    require(plan['schema'] == SCHEMA and plan['wrapper'] == 'ovx' and plan['physical'] == 7,
            'declared_evaluator_allocation')
    require(plan['hard_end_unix'] <= plan['lease_end_unix'] - 21600, 'lease_margin')
    require(time.time() < plan['hard_end_unix'], 'assay_wall')
    require(plan['max_native_calls'] == 192 and plan['parent_calls'] == plan['optimizer_steps'] == 0,
            'evaluation_budget')
    require(set(plan['bundles']) == {'F1', 'A1'}, 'both_route_branches_required')
    require(sha(plan['service_identity']) == plan['service_identity_sha256'], 'pinned_service_identity')
    for source, expected in plan['source_files'].items():
        require(sha(source) == expected, 'frozen_source')
    for branch, item in plan['bundles'].items():
        require(sha(Path(item['root']) / 'EXPORT.json') == item['sha256'], 'export_manifest_hash')
        document, unused = verify_bundle(item['root'])
        require(document['branch'] == branch, 'branch_export_binding')
    return plan


def evaluate(plan_path, branch, condition):
    from gpu import orch_guided_native as native
    from gpu import orch_r121_route_independent as route
    plan = verify_plan(plan_path)
    require(condition in CONDITIONS and branch in plan['bundles'], 'planned_condition')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['uuid'], 'exact_single_GPU')
    bundle = Path(plan['bundles'][branch]['root'])
    export, prompts = verify_bundle(bundle)
    source_condition = 'AFTER' if condition == 'AFTER_LORA_OFF' else condition
    checkpoint = read(bundle / source_condition / 'CHECKPOINT.json')
    identity_document = dict(checkpoint['adapter'], path=str(bundle / source_condition / 'adapter'))
    identity = native.bridge.AdapterIdentity.from_document(identity_document)
    require(identity.base_sha256 == BASE_SHA, 'frozen_Qwen_base')
    output = Path(plan['output']) / branch / condition
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    write(output / 'RESERVATIONS.json', dict(calls=[dict(id=row['id'], messages_sha256=row['messages_sha256'],
        cap=CAP, reserved_unix=time.time(), trainingAllowed=False) for row in prompts],
        count=32, provider_calls=0, optimizer_steps=0, no_retry=True))
    deadline = min(plan['hard_end_unix'], time.time() + 1200)

    def check(label):
        require(time.time() < deadline, 'readout_deadline:' + str(label))

    binding = native.bridge.StageBinding(f'R124_{branch}_{condition}', native.bridge.ARMS[0],
        0, 'sealed_readout', identity, False, True, export['prompts_sha256'])
    loaded = native.load_stage(binding, model_dir=plan['model_dir'], device='cuda:0', gpu_uuid=plan['uuid'],
        context=native.StageContext(), check=check, predecessor_processes=(tuple(checkpoint['source_process']),))
    engine = loaded.engine
    write(output / 'LOADED.json', dict(process=loaded.process, adapter=identity.document(),
        original_checkpoint=export['checkpoints'][source_condition], condition=condition,
        parent_free=True, fresh_process=True, context_free=True, loaded_unix=time.time()))
    responses = []
    context = engine.model.disable_adapter() if condition == 'AFTER_LORA_OFF' else nullcontext()
    with context:
        for offset in range(0, len(prompts), BATCH):
            check('batch')
            batch = prompts[offset:offset + BATCH]
            generated = route.generate_batch(engine, [row['messages'] for row in batch], CAP)
            require(len(generated) == len(batch), 'complete_batch_shape')
            for row, response in zip(batch, generated):
                require(response['messages'] == row['messages'], 'unchanged_full_prompt')
                item = dict(id=row['id'], task_id=row['task_id'], context=row['context'], style=row['style'],
                    messages_sha256=row['messages_sha256'], response=response, condition=condition,
                    metrics=metrics(response, engine.tokenizer), completed_unix=time.time(),
                    status='COMPLETE', trainingAllowed=False, parent_free=True)
                path = output / 'calls' / f'{len(responses):03d}.json'
                write(path, item)
                responses.append(dict(path=str(path), sha256=sha(path), id=row['id'], metrics=item['metrics']))
    finalize_readonly(loaded)
    write(output / 'COMPLETE.json', dict(condition=condition, calls=responses, native_calls=32,
        parent_calls=0, optimizer_steps=0, prompts_sha256=export['prompts_sha256'],
        base_adapter_unchanged=True, finished_unix=time.time(), semantic_improvement='UNPROVEN'))


def supervise(plan_path):
    from gpu.orch_rich_hot_node2_scan import scan
    plan = verify_plan(plan_path)
    root = Path(plan['output'])
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    with (root / 'OWNER.lock').open('x') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(root / 'START.json', dict(pid=os.getpid(), plan=reference(plan_path), started_unix=time.time()))
        for branch in sorted(plan['bundles']):
            for condition in CONDITIONS:
                while True:
                    verify_plan(plan_path)
                    snapshot = scan(7, Path(plan['service_identity']))
                    snapshot.pop('host', None)
                    write(root / 'admissions' / f'{branch}_{condition}_{time.time_ns()}.json', snapshot)
                    if snapshot['clear']:
                        require(snapshot['scanner_euid'] == 0 and snapshot['gpu']['uuid'] == plan['uuid'],
                                'strict_privileged_exact_UUID')
                        break
                    time.sleep(2)
                environment = {key: value for key, value in os.environ.items()
                               if not key.startswith(('PARENT_', 'CLAUDE_'))}
                environment.update(CUDA_VISIBLE_DEVICES=plan['uuid'], HF_HUB_OFFLINE='1',
                    TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
                command = [sys.executable, '-B', '-m', 'gpu.orch_r124_route_behavior_probe', 'evaluate',
                    '--plan', str(plan_path), '--branch', branch, '--condition', condition]
                with (root / f'{branch}_{condition}.log').open('x') as stream:
                    process = subprocess.Popen(command, env=environment, stdout=stream, stderr=subprocess.STDOUT,
                                               stdin=subprocess.DEVNULL, start_new_session=True)
                    write(root / f'{branch}_{condition}_LAUNCH.json', dict(pid=process.pid,
                        started_unix=time.time(), fresh_process=True, condition=condition))
                    try:
                        process.wait(timeout=max(1, min(1230, plan['hard_end_unix'] - time.time())))
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                write(root / f'{branch}_{condition}_EXIT.json', dict(returncode=process.returncode,
                    finished_unix=time.time(), no_retry=True))
        write(root / 'TERMINAL.json', dict(status='ASSAY_ATTEMPTS_FINISHED', finished_unix=time.time(),
            semantic_improvement='UNPROVEN', parent_calls=0, optimizer_steps=0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('export', 'evaluate', 'supervise'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--branch', choices=('F1', 'A1'))
    parser.add_argument('--condition', choices=CONDITIONS)
    args = parser.parse_args()
    if args.action == 'export':
        print(json.dumps(export_bundle(args.branch, args.root, args.output)))
    elif args.action == 'evaluate':
        evaluate(args.plan, args.branch, args.condition)
    else:
        supervise(args.plan)


if __name__ == '__main__':
    main()
