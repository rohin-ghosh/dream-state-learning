"""Eight native generators, frozen next batches, one shared lease-bound clock."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import astra_portable_actor_bundle as portable
from gpu.orch_math_replication_guard import verify_sources
from gpu.orch_math_rich_screen import mounted_adapter_parameters
from gpu.orch_rich_hot_node1_exhaustion_engine import Engine
from gpu import orch_rich_hot_node1_scan as scanner
from organism_v6 import orch_rich_hot_node1_exhaustion as policy


PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
MODEL = '/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'
BUNDLE = '/tmp/astra_portable_37ec_20260914_attempt1'
BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def reserve(root, intent):
    continuation = json.loads((root / 'CONTINUATION.json').read_text())
    ledger_root = Path(continuation['original_root'])
    with (ledger_root / 'CALL_RESERVATIONS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        count = sum(1 for line in stream if line.strip())
        policy.require(count < policy.MAX_CALLS, 'global_call_cap_no_reset')
        result = dict(intent, global_call=count + 1, phase_version=policy.VERSION)
        stream.write(json.dumps(result, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    return result


def prepare(root):
    scanner.host()
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_only')
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    policy.require(json.loads((root / 'PROTOCOL.json').read_text()) == policy.protocol(), 'frozen_protocol_drift')
    config = json.loads((Path(MODEL) / 'config.json').read_text())
    policy.require(config['model_type'] == 'qwen2' and config['hidden_size'] == 3584
        and config['num_hidden_layers'] == 28 and config['max_position_embeddings'] >= policy.CONTEXT
        and config.get('rope_scaling') is None,
        'exact_7b_context_configuration')
    manifest = portable.read_manifest(BUNDLE, expected_manifest_sha256=BUNDLE_SHA)
    policy.require(manifest['parent_state'] == policy.INITIAL_STATE, 'original37ec_required')
    base = portable.verify_base_files(BUNDLE, MODEL, expected_manifest_sha256=BUNDLE_SHA)
    tokenizer = portable.source.native.load_local_tokenizer(MODEL)
    source = root / 'gsm8k_train.jsonl'
    policy.require(sha(source) == policy.SOURCE_SHA, 'cached_source_hash')
    records = [json.loads(line) for line in source.read_text().splitlines()]
    roster = json.loads((root / 'TASKS.json').read_text())
    seen, lengths = set(), []
    for batch in roster['batches']:
        for task in batch['tasks']:
            policy.require(task['id'] not in seen and task['id'] not in roster['excluded_ids']
                and task['question_sha256'] not in roster['excluded_question_hashes'], 'task_overlap_or_held')
            seen.add(task['id'])
            record = records[int(task['id'].rsplit('-', 1)[1])]
            policy.require(record['question'].strip() == task['question'] and
                policy.source.original.number(record['answer'].rsplit('####', 1)[1]) == policy.source.original.number(task['gold']),
                'cached_train_question_gold_join')
            for condition in policy.CONDITIONS:
                tokens = tokenizer.apply_chat_template(policy.messages(task, condition), tokenize=True,
                    add_generation_prompt=True, return_dict=False)
                policy.require(0 < len(tokens) <= policy.CONTEXT - policy.CAP, 'source_context_overflow')
                lengths.append(len(tokens))
    second_pass_probes = []
    previous_root = Path(json.loads((root / 'CONTINUATION.json').read_text())['previous_phase_root'])
    for index, condition in ((4, 'TWO_PASS'), (6, 'META_EVALUATE')):
        first = json.loads((previous_root / f'shard{index}/CALL_00001.json').read_text())
        probe = policy.messages(first['task'], condition, first['response']['raw'])
        encoded = tokenizer.apply_chat_template(probe, tokenize=True, add_generation_prompt=True, return_dict=False)
        cap = policy.token_budget(len(encoded))
        policy.require(len(encoded) + cap <= policy.CONTEXT, 'native_second_pass_context')
        second_pass_probes.append(dict(index=index, prompt_tokens=len(encoded), cap=cap,
            own_source_sha256=sha(previous_root / f'shard{index}/CALL_00001.json')))
    write(root / 'PREPARED.json', dict(status='PREPARED_NO_MODEL', native_calls=0, fits=0, updates=0,
        base_verification=base, adapter_state=policy.INITIAL_STATE, task_count=len(seen),
        prompts_checked=len(lengths), maximum_prompt_tokens=max(lengths), model_dir=MODEL,
        config_sha256=sha(Path(MODEL) / 'config.json'), max_position_embeddings=config['max_position_embeddings'], rope_scaling=config.get('rope_scaling'), requested_output_cap=policy.CAP, requested_context=policy.CONTEXT, host_sha256=policy.HOST_SHA256,
        devices=scanner.inventory(), source_sha256=sha(root / 'SOURCE_SHA256.json'),
        files={name: sha(root / name) for name in ('TASKS.json', 'PROTOCOL.json', 'PROVENANCE.json', 'gsm8k_train.jsonl')},
        second_pass_native_encoding_probes=second_pass_probes,
        finished_utc=datetime.now(timezone.utc).isoformat()))


def run(root, index):
    scanner.host()
    condition, shard = policy.allocation(index)
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == policy.UUIDS[index], 'exact_uuid_required')
    policy.require(('CUDA_VISIBLE_DEVICES=' + policy.UUIDS[index]).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'), 'proc_cvd_required')
    prepared = json.loads((root / 'PREPARED.json').read_text())
    for name, expected in prepared['files'].items():
        policy.require(sha(root / name) == expected, 'input_drift:' + name)
    lifetime = json.loads((root / 'LIFETIME.json').read_text())
    continuation = json.loads((root / 'CONTINUATION.json').read_text())
    original_root = Path(continuation['original_root'])
    policy.require(sha(original_root / 'LIFETIME.json') == continuation['original_lifetime_sha256'] == sha(root / 'LIFETIME.json'), 'inherited_lifetime_drift')
    checkpoint = json.loads((root / f'CHECKPOINT_{index}.json').read_text())
    launch_receipt = json.loads((root / f'LAUNCH_{index}.json').read_text())
    policy.require(sha(root / f'CHECKPOINT_{index}.json') == launch_receipt['checkpoint_sha256'], 'checkpoint_changed_after_launch')
    policy.require(checkpoint['original_root'] == continuation['previous_phase_root'], 'checkpoint_source_root_mismatch')
    for relative, expected in checkpoint['files'].items():
        policy.require(sha(Path(continuation['previous_phase_root']) / relative) == expected, 'preserved_v1_call_drift')
    policy.require(checkpoint['original_tasks_sha256'] == sha(root / 'TASKS.json'), 'same_frozen_cohort_required')
    policy.require(checkpoint['unfinished_calls'] == [] and checkpoint['pending_source_second_pass_pairs'] == [], 'complete_v1_task_boundary_required')
    completed_v1 = set(checkpoint['completed_tasks'])
    output = root / f'shard{index}'
    output.mkdir(exist_ok=False)
    calls, completed, context_failures = 0, 0, 0

    def check(label):
        policy.require(time.time() < lifetime['native_deadline_unix'], 'operational_deadline:' + label)

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    try:
        check('load')
        portable.verify_base_files(BUNDLE, MODEL, expected_manifest_sha256=BUNDLE_SHA)
        arguments = portable.read_bundle(BUNDLE, expected_manifest_sha256=BUNDLE_SHA,
            model_dir=MODEL, device='cuda:0', gpu_uuid=policy.UUIDS[index])
        engine = Engine(arguments, portable.source.native.load_local_tokenizer(MODEL), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash
        parameters = mounted_adapter_parameters(engine.model)
        policy.require(_state_hash(parameters) == policy.INITIAL_STATE, 'loaded_adapter_state_mismatch')
        write(output / 'ACTOR_READY.json', dict(index=index, pid=os.getpid(), uuid=policy.UUIDS[index],
            kernel_minor=policy.MINORS[index], all_parameters_frozen=True, adapter_state=policy.INITIAL_STATE,
            runtime=engine.runtime, ready_unix=time.time(), fits=0, updates=0, phase_version=policy.VERSION, reused_completed_v1_tasks=len(completed_v1)))
        roster = json.loads((root / 'TASKS.json').read_text())
        for batch in roster['batches']:
            check('next_frozen_batch')
            write(output / f'BATCH_{batch["batch"]:02d}_START.json', dict(batch=batch['batch'],
                batch_sha256=batch['sha256'], started_unix=time.time(), continuing_same_clock_and_ledger=True))
            for position, task in enumerate(batch['tasks']):
                if position % 2 != shard or task['id'] in completed_v1:
                    continue
                previous = None
                stages = ('source', 'own_second_pass') if condition in ('TWO_PASS', 'META_EVALUATE') else ('source',)
                for stage in stages:
                    check('call')
                    messages = policy.messages(task, condition, previous)
                    tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                        add_generation_prompt=True, return_dict=False)
                    if len(tokens) >= policy.CONTEXT:
                        context_failures += 1
                        write(output / f'CONTEXT_{batch["batch"]}_{position}_{stage}.json', dict(task_id=task['id'],
                            stage=stage, messages=messages, prompt_tokens=len(tokens), native_call=False,
                            status='CONTEXT_OVERFLOW_NO_TRUNCATION_NO_RETRY'))
                        break
                    call_cap = policy.token_budget(len(tokens))
                    intent = reserve(root, dict(index=index, condition=condition, arm=policy.arm(condition), batch=batch['batch'],
                        task_id=task['id'], stage=stage, checkpoint_sha256=sha(root / f'CHECKPOINT_{index}.json'), started_unix=time.time(), max_new_tokens=call_cap,
                        prompt_tokens=len(tokens), messages=messages))
                    calls += 1
                    write(output / f'INTENT_{calls:05d}.json', intent)
                    try:
                        response = engine.generate(messages, max_new_tokens=call_cap)
                    except BaseException as error:
                        write(output / f'CALL_{calls:05d}_FAILED.json', dict(intent, status='NATIVE_FAILURE',
                            error_type=type(error).__name__, error=str(error), finished_unix=time.time(),
                            partial_native_tokens_unavailable=True))
                        raise
                    outcome = policy.outcome(task, response)
                    write(output / f'CALL_{calls:05d}.json', dict(intent, response=response, outcome=outcome,
                        approach_assessment=policy.assess(response),
                        finished_unix=time.time(), elapsed_seconds=time.time() - intent['started_unix'],
                        task=task, source_state=policy.INITIAL_STATE, trainingAllowed=False,
                        source_sha256=prepared['source_sha256'], tasks_sha256=prepared['files']['TASKS.json']))
                    previous = response['raw']
                    write(output / 'PROGRESS.json', dict(index=index, condition=condition, calls=calls,
                        task_id=task['id'], stage=stage, arm=policy.arm(condition), max_new_tokens=call_cap, phase_version=policy.VERSION, generated_tokens=outcome['content_tokens'],
                        category=outcome['category'], batch=batch['batch'], updated_unix=time.time()))
                completed += 1
            write(output / f'BATCH_{batch["batch"]:02d}_COMPLETE.json', dict(batch=batch['batch'],
                completed_tasks_cumulative=completed, calls=calls, finished_unix=time.time()))
        engine.verify_base()
        policy.require(_state_hash(parameters) == policy.INITIAL_STATE, 'frozen_adapter_changed')
        write(output / 'RESULT.json', dict(status='COMPLETE_FROZEN_QUEUE', calls=calls, completed_tasks=completed,
            context_failures=context_failures, finished_unix=time.time(), frozen_base_unchanged=True,
            adapter_state=policy.INITIAL_STATE, fits=0, updates=0))
    except BaseException as error:
        write(output / 'FAILED.json', dict(status='FAILED_OR_DEADLINE', error_type=type(error).__name__,
            error=str(error), calls=calls, completed_tasks=completed, finished_unix=time.time()))
        raise



def supervise(root, index):
    scanner.host()
    policy.allocation(index)
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    publication = json.loads((root / 'PUBLICATION.json').read_text())
    policy.require(publication['own_cpu_tests_passed'] and publication['dated_builder_publication'], 'published_v2_pre_gpu_required')
    for name, expected in publication['files'].items():
        policy.require(sha(root / name) == expected, 'publication_drift:' + name)
    checkpoint = json.loads((root / f'CHECKPOINT_{index}.json').read_text())
    policy.require(checkpoint['unfinished_calls'] == [] and checkpoint['pending_source_second_pass_pairs'] == [], 'no_incomplete_v1_pair')
    for attempt in range(12):
        snapshot = scanner.scan(index, root / 'SERVICE_IDENTITY.json')
        write(root / f'ADMISSION_{index}_{attempt:02d}.json', snapshot)
        if snapshot['clear']:
            break
        time.sleep(3)
    policy.require(snapshot['clear'], 'fresh_admission_required')
    lifetime = json.loads((root / 'LIFETIME.json').read_text())
    policy.require(time.time() < lifetime['native_deadline_unix'], 'inherited_deadline')
    with (root / f'shard{index}.log').open('x') as log:
        child = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_rich_hot_node1_exhaustion_run', 'run', '--root', str(root), '--index', str(index)],
            cwd=root / 'source', env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.UUIDS[index],
                PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'),
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        identity = scanner.process_identity(Path('/proc') / str(child.pid))
        write(root / f'LAUNCH_{index}.json', dict(index=index, identity=identity, uuid=policy.UUIDS[index],
            phase_version=policy.VERSION, checkpoint_sha256=sha(root / f'CHECKPOINT_{index}.json'), started_unix=time.time()))
        try:
            while child.poll() is None and time.time() < lifetime['hard_deadline_unix'] - 180:
                time.sleep(2)
        finally:
            if child.poll() is None:
                policy.require(scanner.process_identity(Path('/proc') / str(child.pid)) == identity, 'owned_cleanup_identity')
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    policy.require(scanner.process_identity(Path('/proc') / str(child.pid)) == identity, 'owned_kill_identity')
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=10)
            write(root / f'RELEASE_{index}.json', scanner.scan(index, root / 'SERVICE_IDENTITY.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run', 'supervise'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=range(8))
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    else:
        globals()[options.phase](options.root, options.index)
