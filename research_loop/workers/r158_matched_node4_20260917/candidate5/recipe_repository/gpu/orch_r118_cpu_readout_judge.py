"""CPU-only blind annotation of completed route DEV trajectories, never training."""

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import time

from organism_v6 import orch_r114_shared_judge as judge


REVISION = 'cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8'
MAX_NEW_TOKENS = 4096
CONTEXT_LIMIT = 16384
MAX_SECONDS = 3600
CALL_SECONDS = 300
require = judge.require


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def collect(root, cycles):
    root = Path(root).resolve(strict=True)
    require(cycles and len(cycles) <= 8 and len(set(cycles)) == len(cycles), 'bounded_unique_cycles')
    require(all(type(cycle) is int and cycle >= 0 for cycle in cycles), 'nonnegative_cycles')
    cohort = read(root / 'COHORT.json')
    expected_ids = [entry['id'] for entry in cohort['held']]
    require(len(expected_ids) == len(set(expected_ids)) == 8, 'eight_fixed_DEV_tasks')
    documents = []
    for cycle in cycles:
        directory = root / f'readout_{cycle:04d}'
        complete = read(directory / 'COMPLETE.json')
        launch = read(directory / 'LAUNCH.json')
        loaded = read(directory / 'LOADED.json')
        process = read(directory / 'PROCESS_RESULT.json')
        require(complete.get('fresh_process') is True and complete.get('context_free') is True
                and complete.get('parent_calls') == 0 and complete.get('held_tasks') == 8,
                'completed_fresh_parent_free_DEV')
        require(launch.get('parent_free') is True and loaded.get('parent_free') is True
                and process.get('status') == 'COMPLETE', 'readout_process_completed')
        checkpoint = Path(launch['checkpoint'])
        require(checkpoint.is_relative_to(root) and sha(checkpoint) == loaded['checkpoint_sha256'],
                'exact_saved_checkpoint')
        held = read(directory / 'HELD.json')
        require(held.get('scope') == 'dev' and held.get('selection') is False
                and held['ids'] == expected_ids and len(held['cached_responses']) == 8,
                'fixed_DEV_only_no_FINAL')
        captures = defaultdict(list)
        for path in sorted(directory.glob('CALL_*.json')):
            call = read(path)
            if call.get('task_id') not in expected_ids or call.get('condition') != 'LORA_ON':
                continue
            require(call.get('status') == 'COMPLETE' and call.get('parent_free') is True,
                    'actual_completed_parent_free_capture')
            captures[(call['task_id'], judge.previous.digest(call['response']))].append(path)
        for task_id, responses in zip(expected_ids, held['cached_responses']):
            require(responses, 'no_missing_task_outputs')
            sources = []
            for response in responses:
                require(isinstance(response['raw'], str) and isinstance(response['token_ids'], list)
                        and all(type(token) is int for token in response['token_ids']), 'native_output_required')
                require(response.get('full_prompt_prefix_verified') is True
                        and response.get('input_truncated') is False, 'complete_causal_prefix')
                matches = captures[(task_id, judge.previous.digest(response))]
                require(matches, 'cached_text_must_match_native_capture')
                path = matches.pop(0)
                sources.append(dict(path=str(path), sha256=sha(path)))
            visible = [message['content'] for message in responses[-1]['messages']
                       if message['role'] in ('user', 'tool')]
            require(visible and all(isinstance(text, str) for text in visible), 'public_context_required')
            document = dict(kind='held', task_text='\n\n'.join(visible),
                            child_text='\n\n'.join(response['raw'] for response in responses))
            request = judge.request(document)
            documents.append(dict(document=document, request=request, private_provenance=dict(
                cycle=cycle, task_id=task_id, sources=sources,
                held_path=str(directory / 'HELD.json'), held_sha256=sha(directory / 'HELD.json'),
                checkpoint_sha256=loaded['checkpoint_sha256'],
                complete_sha256=sha(directory / 'COMPLETE.json'),
                child_token_ids=sum(len(response['token_ids']) for response in responses),
                native_calls=len(responses), child_output_truncated=any(response['truncated'] for response in responses),
                parent_free=True, training_buffer=False)))
    return sorted(documents, key=lambda item: item['request']['input_sha256'])


def interpret(document, raw, terminated):
    if not terminated:
        return dict(status='UNRESOLVED', reason='judge_output_bound', departures_and_returns=None, shifts=None)
    try:
        annotation = json.loads(raw)
        return dict(judge.validate_annotation(document, annotation), annotation=annotation)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        return dict(status='UNRESOLVED', reason='invalid_judge_annotation', departures_and_returns=None, shifts=None)


def cpu_environment():
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'explicitly_no_visible_GPU')


def prepare(root, child_root, cycles, model_dir, source_manifest):
    cpu_environment()
    root, model_dir = Path(root), Path(model_dir).resolve(strict=True)
    require(model_dir.name == REVISION, 'pinned_14B_revision')
    source_manifest = Path(source_manifest).resolve(strict=True)
    source_root = Path(__file__).resolve().parents[1]
    for relative, expected in read(source_manifest).items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'source_relative_path')
        require(sha(source_root / relative) == expected, 'frozen_source_hash')
    documents = collect(child_root, cycles)
    weights = sorted(model_dir.glob('*.safetensors'))
    require(len(weights) == 8, 'eight_pinned_model_shards')
    model_manifest = {path.name: sha(path) for path in sorted(model_dir.iterdir()) if path.is_file()}
    write(root / 'DOCUMENTS.json', documents)
    write(root / 'MODEL_SHA256.json', model_manifest)
    write(root / 'PLAN.json', dict(schema='R118_CPU_DEV_JUDGE_V1', device='cpu', dtype='bfloat16',
        model=judge.MODEL, revision=REVISION, model_dir=str(model_dir), threads=16,
        prompt_sha256=sha(judge.PROMPT_PATH), documents_sha256=sha(root / 'DOCUMENTS.json'),
        model_manifest_sha256=sha(root / 'MODEL_SHA256.json'), source_root=str(source_root),
        source_manifest=str(source_manifest), source_manifest_sha256=sha(source_manifest),
        cycles=list(cycles), documents=len(documents), max_new_tokens=MAX_NEW_TOKENS,
        max_seconds=MAX_SECONDS, call_seconds=CALL_SECONDS, context_limit=CONTEXT_LIMIT,
        temperature=0, do_sample=False, annotation_only=True, parent_calls=0, optimizer_updates=0,
        device_comparability='CPU_bfloat16_not_assumed_identical_to_prior_GPU_judgments',
        exploratory_DEV_not_FINAL=True, held_composition_not_obstacle_persistence=True))


def run(root):
    cpu_environment()
    root = Path(root)
    started = time.time()
    require(not (root / 'STARTED.json').exists(), 'no_automatic_annotation_replay')
    plan = read(root / 'PLAN.json')
    require(read(root / 'PUBLICATION.json')['plan_sha256'] == sha(root / 'PLAN.json'), 'published_scope')
    for name, field in (('DOCUMENTS.json', 'documents_sha256'), ('MODEL_SHA256.json', 'model_manifest_sha256')):
        require(sha(root / name) == plan[field], 'bound_inputs')
    require(sha(judge.PROMPT_PATH) == plan['prompt_sha256'], 'fixed_judge_prompt')
    require(sha(plan['source_manifest']) == plan['source_manifest_sha256'], 'source_manifest_binding')
    for relative, expected in read(plan['source_manifest']).items():
        require(sha(Path(plan['source_root']) / relative) == expected, 'frozen_source_hash')
    model_dir = Path(plan['model_dir'])
    for name, expected in read(root / 'MODEL_SHA256.json').items():
        require(Path(name).name == name and sha(model_dir / name) == expected, 'pinned_model_file')
    write(root / 'STARTED.json', dict(pid=os.getpid(), started_unix=started, device='cpu'))
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList
    torch.set_num_threads(plan['threads'])
    torch.set_num_interop_threads(1)
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.bfloat16,
        device_map={'': 'cpu'}, local_files_only=True, trust_remote_code=False, attn_implementation='sdpa')
    model.requires_grad_(False)
    model.eval()
    require(all(parameter.device.type == 'cpu' and not parameter.requires_grad
                for parameter in model.parameters()) and not torch.cuda.is_initialized(), 'CPU_frozen_no_CUDA')
    versions = {name: parameter._version for name, parameter in model.named_parameters()}
    write(root / 'LOADED.json', dict(pid=os.getpid(), loaded_unix=time.time(), device='cpu',
        cuda_initialized=False, trainable_parameters=0, threads=torch.get_num_threads()))
    documents = read(root / 'DOCUMENTS.json')
    deadline = started + plan['max_seconds']
    completed = []
    for index, item in enumerate(documents):
        if time.time() >= deadline:
            break
        request = judge.request(item['document'])
        require(request == item['request'], 'blind_request_unchanged')
        inputs = tokenizer.apply_chat_template(request['messages'], tokenize=True,
            add_generation_prompt=True, return_tensors='pt', return_dict=True)
        input_count = inputs['input_ids'].shape[1]
        call_root = root / f'call_{index:04d}'
        write(call_root / 'REQUEST.json', request)
        call_started = time.time()
        raw, tokens = '', []
        if input_count + plan['max_new_tokens'] > plan['context_limit']:
            result = dict(status='UNRESOLVED', reason='input_context_bound', departures_and_returns=None, shifts=None)
        else:
            call_deadline = min(deadline, call_started + plan['call_seconds'])

            class Deadline(StoppingCriteria):
                def __call__(self, input_ids, scores, **kwargs):
                    return time.time() >= call_deadline

            with torch.inference_mode():
                output = model.generate(**inputs, max_new_tokens=plan['max_new_tokens'], do_sample=False,
                    stopping_criteria=StoppingCriteriaList([Deadline()]),
                    pad_token_id=tokenizer.eos_token_id, use_cache=True)
            tokens = output[0, input_count:].tolist()
            raw = tokenizer.decode(tokens, skip_special_tokens=True)
            eos = model.generation_config.eos_token_id
            eos = eos if isinstance(eos, list) else [eos]
            result = interpret(item['document'], raw, bool(tokens) and tokens[-1] in eos)
        write(call_root / 'RESPONSE.json', dict(raw=raw, token_ids=tokens, input_tokens=input_count,
            started_unix=call_started, finished_unix=time.time(), result=result))
        receipt = dict(index=index, input_sha256=request['input_sha256'], status=result['status'],
            response_path=str(call_root / 'RESPONSE.json'), response_sha256=sha(call_root / 'RESPONSE.json'))
        completed.append(receipt)
        write(root / 'progress' / f'{index:04d}.json', receipt)
    require(all(parameter._version == versions[name] for name, parameter in model.named_parameters()),
            'judge_weights_unchanged')
    write(root / 'TERMINAL.json', dict(status='COMPLETE' if len(completed) == len(documents) else 'WALL_BOUND',
        started_unix=started, finished_unix=time.time(), attempted=len(completed), expected=len(documents),
        complete_annotations=sum(item['status'] == 'COMPLETE' for item in completed),
        unresolved_annotations=sum(item['status'] == 'UNRESOLVED' for item in completed),
        unattempted=len(documents)-len(completed), optimizer_updates=0, parent_calls=0,
        semantic_labels_are_model_judgments=True, retained_learning_not_established=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--child-root', type=Path)
    parser.add_argument('--model-dir', type=Path)
    parser.add_argument('--source-manifest', type=Path)
    parser.add_argument('--cycles', type=int, nargs='+')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.root, args.child_root, args.cycles, args.model_dir, args.source_manifest)
    else:
        run(args.root)


if __name__ == '__main__':
    main()
