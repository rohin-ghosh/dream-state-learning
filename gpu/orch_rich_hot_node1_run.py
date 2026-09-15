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
from gpu.orch_rich_hot_node3_run import Engine
from gpu import orch_rich_hot_node1_scan as scanner
from organism_v6 import orch_rich_hot_node1 as policy


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
    with (root / 'CALL_RESERVATIONS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        count = sum(1 for line in stream if line.strip())
        policy.require(count < policy.MAX_CALLS, 'global_call_cap_no_reset')
        result = dict(intent, global_call=count + 1)
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
        and config['num_hidden_layers'] == 28 and config['max_position_embeddings'] >= policy.CONTEXT,
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
    write(root / 'PREPARED.json', dict(status='PREPARED_NO_MODEL', native_calls=0, fits=0, updates=0,
        base_verification=base, adapter_state=policy.INITIAL_STATE, task_count=len(seen),
        prompts_checked=len(lengths), maximum_prompt_tokens=max(lengths), model_dir=MODEL,
        config_sha256=sha(Path(MODEL) / 'config.json'), host_sha256=policy.HOST_SHA256,
        devices=scanner.inventory(), source_sha256=sha(root / 'SOURCE_SHA256.json'),
        files={name: sha(root / name) for name in ('TASKS.json', 'PROTOCOL.json', 'PROVENANCE.json', 'gsm8k_train.jsonl')},
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
            runtime=engine.runtime, ready_unix=time.time(), fits=0, updates=0))
        roster = json.loads((root / 'TASKS.json').read_text())
        for batch in roster['batches']:
            check('next_frozen_batch')
            write(output / f'BATCH_{batch["batch"]:02d}_START.json', dict(batch=batch['batch'],
                batch_sha256=batch['sha256'], started_unix=time.time(), continuing_same_clock_and_ledger=True))
            for position, task in enumerate(batch['tasks']):
                if position % 2 != shard:
                    continue
                previous = None
                stages = ('source', 'own_second_pass') if condition in ('TWO_PASS', 'META_EVALUATE') else ('source',)
                for stage in stages:
                    check('call')
                    messages = policy.messages(task, condition, previous)
                    tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                        add_generation_prompt=True, return_dict=False)
                    if len(tokens) + policy.CAP > policy.CONTEXT:
                        context_failures += 1
                        write(output / f'CONTEXT_{batch["batch"]}_{position}_{stage}.json', dict(task_id=task['id'],
                            stage=stage, messages=messages, prompt_tokens=len(tokens), native_call=False,
                            status='CONTEXT_OVERFLOW_NO_TRUNCATION_NO_RETRY'))
                        break
                    intent = reserve(root, dict(index=index, condition=condition, batch=batch['batch'],
                        task_id=task['id'], stage=stage, started_unix=time.time(), max_new_tokens=policy.CAP,
                        prompt_tokens=len(tokens), messages=messages))
                    calls += 1
                    write(output / f'INTENT_{calls:05d}.json', intent)
                    try:
                        response = engine.generate(messages, max_new_tokens=policy.CAP)
                    except BaseException as error:
                        write(output / f'CALL_{calls:05d}_FAILED.json', dict(intent, status='NATIVE_FAILURE',
                            error_type=type(error).__name__, error=str(error), finished_unix=time.time(),
                            partial_native_tokens_unavailable=True))
                        raise
                    outcome = policy.outcome(task, response)
                    write(output / f'CALL_{calls:05d}.json', dict(intent, response=response, outcome=outcome,
                        finished_unix=time.time(), elapsed_seconds=time.time() - intent['started_unix'],
                        task=task, source_state=policy.INITIAL_STATE, trainingAllowed=False,
                        source_sha256=prepared['source_sha256'], tasks_sha256=prepared['files']['TASKS.json']))
                    previous = response['raw']
                    write(output / 'PROGRESS.json', dict(index=index, condition=condition, calls=calls,
                        task_id=task['id'], stage=stage, generated_tokens=outcome['content_tokens'],
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


def launch(root):
    scanner.host()
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    publication = json.loads((root / 'PUBLICATION.json').read_text())
    policy.require(publication['own_cpu_tests_passed'] and publication['dated_builder_publication'], 'own_pre_gpu_required')
    for name, expected in publication['files'].items():
        policy.require(sha(root / name) == expected, 'publication_drift:' + name)
    policy.require(not (root / 'LIFETIME.json').exists(), 'never_reset_lifetime')
    started = time.time()
    deadline = policy.deadline(started)
    write(root / 'LIFETIME.json', dict(started_unix=started, hard_deadline_unix=deadline,
        native_deadline_unix=deadline - 300, maximum_calls=policy.MAX_CALLS,
        maximum_assigned_gpu_hours=96, lease_end_unix=policy.LEASE_END,
        lease_margin_seconds=policy.LEASE_MARGIN, uuid_by_index=policy.UUIDS, minor_by_index=policy.MINORS))
    children, logs = [], []
    status = 'FAILED'
    try:
        for index in range(8):
            snapshot = scanner.scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / f'PRE_SCAN_{index}.json', snapshot)
            policy.require(snapshot['clear'], 'pre_scan_blocked:' + str(index))
        for index in range(8):
            snapshot = scanner.scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / f'ADMISSION_{index}.json', snapshot)
            policy.require(snapshot['clear'], 'immediate_admission_blocked:' + str(index))
            log = (root / f'shard{index}.log').open('x')
            logs.append(log)
            child = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_rich_hot_node1_run', 'run',
                '--root', str(root), '--index', str(index)], cwd=root / 'source',
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.UUIDS[index], PYTHONPATH=str(root / 'source'),
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                    TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'),
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            identity = scanner.process_identity(Path('/proc') / str(child.pid))
            children.append((child, identity))
            write(root / f'LAUNCH_{index}.json', dict(index=index, identity=identity,
                uuid=policy.UUIDS[index], minor=policy.MINORS[index], started_unix=time.time()))
        while any(child.poll() is None for child, identity in children):
            policy.require(time.time() < deadline - 180, 'hard_operational_deadline')
            time.sleep(5)
        status = 'COMPLETE' if all(child.returncode == 0 for child, identity in children) else 'SHARD_FAILURE'
    except BaseException as error:
        write(root / 'GUARD_FAILED.json', dict(error_type=type(error).__name__, error=str(error)))
        raise
    finally:
        for child, identity in children:
            if child.poll() is None:
                policy.require(scanner.process_identity(Path('/proc') / str(child.pid)) == identity, 'cleanup_identity_changed')
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    policy.require(scanner.process_identity(Path('/proc') / str(child.pid)) == identity, 'kill_identity_changed')
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=10)
        for log in logs:
            log.close()
        write(root / 'TERMINAL.json', dict(status=status, finished_unix=time.time(),
            exit_codes=[child.returncode for child, identity in children], assigned_gpu_hours=8 * (time.time() - started) / 3600))
        for index in range(8):
            write(root / f'RELEASE_{index}.json', scanner.scan(index, root / 'SERVICE_IDENTITY.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'launch', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=range(8))
    options = parser.parse_args()
    if options.phase == 'run':
        run(options.root, options.index)
    else:
        globals()[options.phase](options.root)
