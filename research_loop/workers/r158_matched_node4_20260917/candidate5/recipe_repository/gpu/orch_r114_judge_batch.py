"""Bounded, frozen14B blind annotation of already completed node-local readouts."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
from types import SimpleNamespace

from organism_v6 import orch_r114_shared_judge as judge


SOURCE_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path('/localhome/local-rohing/orch_r114_judge_20260915_attempt1')
CHILD_ROOT = Path('/localhome/local-rohing/orch_r110_guided_20260915_attempt1')
UUID = 'GPU-31583768-d90f-520c-51ed-5dac761526d0'
HOST_SHA = '6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'
REVISION = 'cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8'
MODEL_DIR = Path.home() / '.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots' / REVISION
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
MAX_SECONDS = 2700
MAX_NEW_TOKENS = 4096
CONTEXT_LIMIT = 16384
LEASE_END = datetime(2026, 9, 26, 23, 5, tzinfo=timezone.utc).timestamp()
require = judge.require


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def exact_host():
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_host')


def bind_scanner():
    from gpu import orch_r110_admission as scanner
    scanner.minor.pinned.policy = SimpleNamespace(DEVICES={4: UUID}, HOST_SHA=HOST_SHA,
        require=require, allocation=lambda index: require(index == 4, 'only_allocated_gpu4'))
    return scanner


def scanner_command(action):
    return ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + str(SOURCE_ROOT), 'python3', '-B', '-m', 'gpu.orch_r114_judge_batch', action]


def select_documents(child_root, cycles):
    cohort = read(child_root / 'COHORT.json')
    documents = []
    for cycle in cycles:
        directory = child_root / f'cycle{cycle}' / 'readout'
        complete = read(directory / 'COMPLETE.json')
        require(complete['status'] == 'COMPLETE' and complete['fresh_process'] is True
            and complete['parent_calls'] == 0, 'completed_parent_free_readout')
        tasks = {task['id']: task for task in cohort['held'][cycle - 1]}
        selected = []
        for path in sorted(directory.glob('CALL_*.json')):
            call = read(path)
            if call['task_id'] not in tasks:
                continue
            require(call['purpose'] == 'held' and 'response' in call and 'error_type' not in call,
                'actual_completed_held_call')
            document = dict(kind='held', task_text=tasks[call['task_id']]['question'],
                child_text=call['response']['raw'])
            request = judge.request(document)
            selected.append(dict(document=document, request=request,
                private_provenance=dict(cycle=cycle, task_id=call['task_id'],
                    source_path=str(path), source_sha256=sha(path),
                    complete_sha256=sha(directory / 'COMPLETE.json'))))
        require(len(selected) == 8 and len({row['private_provenance']['task_id'] for row in selected}) == 8,
            'eight_distinct_held_calls_per_cycle')
        documents.extend(selected)
    require(0 < len(documents) <= 32, 'bounded_judge_batch')
    return sorted(documents, key=lambda row: row['request']['input_sha256'])


def interpret(document, raw, cap_hit):
    if cap_hit:
        return dict(status='UNRESOLVED', reason='judge_output_cap', departures_and_returns=None, shifts=None)
    try:
        annotation = json.loads(raw)
        return dict(judge.validate_annotation(document, annotation), annotation=annotation)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        return dict(status='UNRESOLVED', reason='invalid_judge_annotation',
            departures_and_returns=None, shifts=None)


def prepare():
    exact_host()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_prepare')
    sources = read(ROOT / 'SOURCE_SHA256.json')
    for relative, expected in sources.items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'source_path')
        require(sha(SOURCE_ROOT / relative) == expected, 'immutable_source')
    cpu = read(ROOT / 'CPU_RESULT.json')
    require(cpu['passed'] is True and cpu['failed'] == 0, 'cpu_tests_passed')
    documents = select_documents(CHILD_ROOT, [1, 2])
    write(ROOT / 'DOCUMENTS.json', documents)
    shards = sorted(MODEL_DIR.glob('*.safetensors'))
    require(len(shards) == 8, 'eight_local_14b_shards')
    model_files = {path.name: sha(path) for path in sorted(MODEL_DIR.iterdir()) if path.is_file()}
    write(ROOT / 'MODEL_SHA256.json', model_files)
    write(ROOT / 'PLAN.json', dict(schema='R114_BLIND_JUDGE_BATCH_V1', physical=4, uuid=UUID,
        model=judge.MODEL, revision=REVISION, model_dir=str(MODEL_DIR),
        temperature=0, do_sample=False, max_new_tokens=MAX_NEW_TOKENS, context_limit=CONTEXT_LIMIT,
        max_seconds=MAX_SECONDS, lease_end_unix=LEASE_END, documents=len(documents),
        prompt_sha256=sha(judge.PROMPT_PATH), documents_sha256=sha(ROOT / 'DOCUMENTS.json'),
        source_manifest_sha256=sha(ROOT / 'SOURCE_SHA256.json'),
        model_manifest_sha256=sha(ROOT / 'MODEL_SHA256.json'), cpu_sha256=sha(ROOT / 'CPU_RESULT.json'),
        annotation_only=True, training_updates=0, parents=0, controls_not_inferred=True,
        legacy_r110_readouts_not_v4_dev_final=True, raw_node_only=True,
        prepared_unix=time.time()))


def launch():
    exact_host()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_dispatch')
    plan = read(ROOT / 'PLAN.json')
    require(read(ROOT / 'PUBLICATION.json')['plan_sha256'] == sha(ROOT / 'PLAN.json'), 'published_exact_plan')
    require(time.time() + MAX_SECONDS < LEASE_END - 21600, 'lease_margin')
    subprocess.run(scanner_command('service'), check=True, capture_output=True, timeout=90)
    report = json.loads(subprocess.run(scanner_command('scan'), check=True,
        capture_output=True, text=True, timeout=90).stdout)
    write(ROOT / 'ADMISSION.json', report)
    require(report['clear'] is True and report['scanner_euid'] == 0
        and report['gpu']['uuid'] == UUID and report['gpu']['index'] == 4
        and not report['blocking_reasons'], 'strict_allocated_device_admission')
    deadline = time.time() + plan['max_seconds']
    write(ROOT / 'LIFETIME.json', dict(started_unix=time.time(), deadline_unix=deadline,
        admission_sha256=sha(ROOT / 'ADMISSION.json')))
    command = ['timeout', '--signal=TERM', '--kill-after=10s', str(MAX_SECONDS) + 's',
        PYTHON, '-B', '-m', 'gpu.orch_r114_judge_batch', 'run']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=UUID, HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(SOURCE_ROOT))
    with (ROOT / 'native.log').open('x') as stream:
        process = subprocess.Popen(command, cwd=SOURCE_ROOT, env=environment,
            stdout=stream, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    write(ROOT / 'LAUNCH.json', dict(pid=process.pid, command=command,
        uuid=UUID, started_unix=time.time(), plan_sha256=sha(ROOT / 'PLAN.json')))
    print(json.dumps(dict(pid=process.pid, uuid=UUID, root=str(ROOT), status='DISPATCHED_NOT_YET_LOADED')))


def run():
    exact_host()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == UUID, 'allocated_uuid_only')
    (ROOT / 'RUN_ONCE').mkdir()
    deadline = read(ROOT / 'LIFETIME.json')['deadline_unix']
    started = time.time()
    completed = []

    def check(*unused):
        require(time.time() < deadline, 'judge_lifetime_exhausted')

    def interrupted(*unused):
        raise TimeoutError('owned_judge_interrupted')

    signal.signal(signal.SIGTERM, interrupted)
    try:
        for relative, expected in read(ROOT / 'SOURCE_SHA256.json').items():
            require(sha(SOURCE_ROOT / relative) == expected, 'immutable_native_source')
        plan = read(ROOT / 'PLAN.json')
        require(sha(ROOT / 'DOCUMENTS.json') == plan['documents_sha256']
            and sha(judge.PROMPT_PATH) == plan['prompt_sha256'], 'bound_native_inputs')
        require(sha(ROOT / 'SOURCE_SHA256.json') == plan['source_manifest_sha256']
            and sha(ROOT / 'MODEL_SHA256.json') == plan['model_manifest_sha256']
            and sha(ROOT / 'CPU_RESULT.json') == plan['cpu_sha256'], 'bound_native_manifests')
        require(read(ROOT / 'PUBLICATION.json')['plan_sha256'] == sha(ROOT / 'PLAN.json'),
            'published_native_plan')
        for name, expected in read(ROOT / 'MODEL_SHA256.json').items():
            require(Path(name).name == name and sha(MODEL_DIR / name) == expected, 'pinned_judge_weights')
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList
        require(torch.cuda.device_count() == 1, 'one_visible_judge_gpu')
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True, trust_remote_code=False)
        model = AutoModelForCausalLM.from_pretrained(MODEL_DIR, torch_dtype=torch.bfloat16,
            device_map={'': 0}, local_files_only=True, trust_remote_code=False, attn_implementation='sdpa')
        model.requires_grad_(False)
        model.eval()
        require(not any(parameter.requires_grad for parameter in model.parameters()), 'judge_frozen')
        versions = {name: parameter._version for name, parameter in model.named_parameters()}
        write(ROOT / 'LOADED.json', dict(pid=os.getpid(), loaded_unix=time.time(), uuid=UUID,
            model=judge.MODEL, revision=REVISION, trainable_parameters=0))

        class Deadline(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                check()
                return False

        for index, row in enumerate(read(ROOT / 'DOCUMENTS.json')):
            check()
            request = judge.request(row['document'])
            require(request == row['request'], 'bound_blind_request')
            inputs = tokenizer.apply_chat_template(request['messages'], tokenize=True,
                add_generation_prompt=True, return_tensors='pt', return_dict=True)
            inputs = {key: value.to('cuda:0') for key, value in inputs.items()}
            input_count = inputs['input_ids'].shape[1]
            require(input_count + MAX_NEW_TOKENS <= CONTEXT_LIMIT, 'no_silent_prompt_truncation')
            call_root = ROOT / f'call{index:03d}'
            write(call_root / 'REQUEST.json', request)
            call_started = time.time()
            with torch.inference_mode():
                output = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                    stopping_criteria=StoppingCriteriaList([Deadline()]),
                    pad_token_id=tokenizer.eos_token_id, use_cache=True)
            tokens = output[0, input_count:].tolist()
            raw = tokenizer.decode(tokens, skip_special_tokens=True)
            result = interpret(row['document'], raw, len(tokens) >= MAX_NEW_TOKENS)
            write(call_root / 'RESPONSE.json', dict(raw=raw, token_ids=tokens,
                prompt_tokens=input_count, started_unix=call_started, finished_unix=time.time(), result=result))
            completed.append(dict(call=index, input_sha256=request['input_sha256'],
                status=result['status'], response_sha256=sha(call_root / 'RESPONSE.json'),
                generated_tokens=len(tokens)))
            write(ROOT / 'progress' / f'{index:03d}.json', completed[-1])
        require(all(parameter._version == versions[name] for name, parameter in model.named_parameters()),
            'judge_parameters_unchanged')
        write(ROOT / 'COMPLETE.json', dict(status='COMPLETE', started_unix=started,
            finished_unix=time.time(), calls=completed, optimizer_updates=0, parent_calls=0,
            semantic_results_are_model_judgments=True, outcome_not_used=True))
    except BaseException as error:
        write(ROOT / 'FAILED.json', dict(status='FAILED', error_type=type(error).__name__,
            started_unix=started, finished_unix=time.time(), completed_calls=len(completed)))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'service', 'scan', 'launch', 'run'))
    action = parser.parse_args().action
    if action in ('service', 'scan'):
        exact_host()
        scanner = bind_scanner()
        if action == 'service':
            scanner.minor.pinned.service(ROOT / 'SERVICE_IDENTITY.json')
        else:
            print(json.dumps(scanner.scan(4, ROOT / 'SERVICE_IDENTITY.json')))
    else:
        globals()[action]()


if __name__ == '__main__':
    main()
