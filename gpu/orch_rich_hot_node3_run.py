"""Isolated top-budget native generation and identity-bound six-GPU guardian."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_rich_intensity_guard as ownership
from gpu.orch_math_replication_guard import verify_sources
from gpu.orch_math_rich_screen import mounted_adapter_parameters, write
from organism_v6 import orch_rich_hot_node3 as policy
from organism_v6 import orch_rich_intensity as prior


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind_host():
    if hashlib.sha256(socket.gethostname().encode()).hexdigest() != policy.HOST_SHA256:
        raise ValueError('node3_hashed_host_binding_mismatch')


def reserve(root, intent):
    with (root / 'CALL_RESERVATIONS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        count = sum(1 for line in stream if line.strip())
        if count >= policy.MAX_CALLS:
            raise RuntimeError('global_2048_call_cap')
        reservation = dict(intent, global_call=count + 1)
        stream.write(json.dumps(reservation, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
        return reservation


class Engine(portable.source.Engine):
    def generate(self, messages, *, max_new_tokens):
        self.check('generation')
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True,
            add_generation_prompt=True, return_dict=False)
        policy.context_check(len(tokens), max_new_tokens)
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1,
            use_cache=True, max_new_tokens=max_new_tokens, repetition_penalty=1.0,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                generation_config=config)
        assert generated[0, :len(tokens)].tolist() == tokens
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        text = self.tokenizer.decode(tail[:-1] if terminal else tail,
            skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail,
            raw=text, terminal=terminal, truncated=not terminal and len(tail) == max_new_tokens)


def prepare(root):
    bind_host()
    assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    assert sha(root / 'TASKS.json') == policy.TASKS_SHA
    document = json.loads((root / 'TASKS.json').read_text())
    prior.validate(document)
    assert json.loads((root / 'PROTOCOL.json').read_text()) == policy.protocol()
    config_path = Path(ownership.existing.MODEL) / 'config.json'
    config = json.loads(config_path.read_text())
    policy.model_config_check(config)
    manifest = portable.read_manifest(ownership.existing.BUNDLE,
        expected_manifest_sha256=policy.BUNDLE_SHA)
    assert manifest['parent_state'] == portable.PARENT_STATE
    base = portable.verify_base_files(ownership.existing.BUNDLE, ownership.existing.MODEL,
        expected_manifest_sha256=policy.BUNDLE_SHA)
    tokenizer = portable.source.native.load_local_tokenizer(ownership.existing.MODEL)
    lengths = []
    for condition in policy.CONDITIONS:
        for task in document['tasks']:
            messages, _ = policy.prompt(task, condition, 'rich')
            encoded = tokenizer.apply_chat_template(messages, tokenize=True,
                add_generation_prompt=True, return_dict=False)
            policy.context_check(len(encoded))
            lengths.append(len(encoded))
    write(root / 'PREPARED.json', dict(status='PREPARED_NO_MODEL', native_calls=0,
        fits=0, updates=0, base_verification=base, adapter_state=portable.PARENT_STATE,
        host_sha256=policy.HOST_SHA256, config_sha256=sha(config_path),
        max_position_embeddings=config['max_position_embeddings'],
        maximum_source_prompt_tokens=max(lengths), source_prompts_checked=len(lengths),
        tasks_sha256=sha(root / 'TASKS.json'), protocol_sha256=sha(root / 'PROTOCOL.json'),
        source_sha256=sha(root / 'SOURCE_SHA256.json'), finished_unix=time.time()))


def screen(root, index):
    bind_host()
    condition, shard = policy.allocation(index)
    uuid = ownership.DEVICES[index]
    assert os.environ['CUDA_VISIBLE_DEVICES'] == uuid
    assert ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    assert os.environ['HF_HUB_OFFLINE'] == os.environ['TRANSFORMERS_OFFLINE'] == '1'
    start = json.loads((root / 'run/START.json').read_text())
    output = root / 'run' / f'shard{index}'
    output.mkdir(exist_ok=False)
    binding = dict(started_unix=time.time(), pid=os.getpid(), condition=condition,
        physical_index=index, gpu_uuid=uuid, host_sha256=policy.HOST_SHA256,
        tasks_sha256=policy.TASKS_SHA, protocol_sha256=sha(root / 'PROTOCOL.json'),
        source_sha256=sha(root / 'SOURCE_SHA256.json'), fits=0, updates=0,
        trainingAllowed=False, fit_ready=False, native_deadline_unix=start['native_deadline_unix'])
    write(output / 'REQUEST.json', binding)
    calls, failures = 0, 0
    recovery = json.loads((root / 'RECOVERY.json').read_text()) if (root / 'RECOVERY.json').exists() else None
    budget_root = Path(recovery['original_root']) if recovery else root

    def check(label):
        if time.time() >= start['native_deadline_unix']:
            raise TimeoutError('common_12h_deadline:' + label)

    try:
        assert sha(root / 'TASKS.json') == policy.TASKS_SHA
        document = json.loads((root / 'TASKS.json').read_text())
        prior.validate(document)
        config = json.loads((Path(ownership.existing.MODEL) / 'config.json').read_text())
        policy.model_config_check(config)
        portable.verify_base_files(ownership.existing.BUNDLE, ownership.existing.MODEL,
            expected_manifest_sha256=policy.BUNDLE_SHA)
        arguments = portable.read_bundle(ownership.existing.BUNDLE,
            expected_manifest_sha256=policy.BUNDLE_SHA, model_dir=ownership.existing.MODEL,
            device='cuda:0', gpu_uuid=uuid)
        engine = Engine(arguments, portable.source.native.load_local_tokenizer(arguments.model_dir), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash
        parameters = mounted_adapter_parameters(engine.model)
        assert _state_hash(parameters) == portable.PARENT_STATE
        assert not any(parameter.requires_grad for parameter in engine.model.parameters())
        write(output / 'ACTOR_READY.json', dict(binding, ready_unix=time.time(),
            runtime=engine.runtime, adapter_state=portable.PARENT_STATE, all_parameters_frozen=True))

        def generate(task, kind, previous=None):
            nonlocal calls, failures
            check('call')
            messages, student = policy.prompt(task, condition, kind, previous)
            encoded = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                add_generation_prompt=True, return_dict=False)
            try:
                policy.context_check(len(encoded))
            except ValueError as error:
                failures += 1
                write(output / f'{task["id"]}_{kind}_CONTEXT_FAILURE.json', dict(
                    task_id=task['id'], kind=kind, messages=messages, prompt_tokens=len(encoded),
                    error=str(error), native_call=False, no_truncation=True, time_unix=time.time()))
                return None
            intent = dict(task_id=task['id'], kind=kind, condition=condition,
                physical_index=index, started_unix=time.time(), prompt_tokens=len(encoded),
                max_new_tokens=policy.MAX_NEW_TOKENS, messages=messages,
                previous_sha256=hashlib.sha256(previous.encode()).hexdigest() if previous is not None else None)
            reservation = reserve(budget_root, intent)
            calls += 1
            write(output / f'INTENT_{calls:04d}.json', reservation)
            try:
                result = engine.generate(messages, max_new_tokens=policy.MAX_NEW_TOKENS)
            except BaseException as error:
                write(output / f'CALL_{calls:04d}_FAILED.json', dict(reservation,
                    status='NATIVE_FAILURE', error_type=type(error).__name__,
                    error=str(error), finished_unix=time.time(), partial_tokens_unavailable=True))
                raise
            row = policy.capture(task, kind, result, student)
            row.update(condition=condition, physical_index=index, global_call=reservation['global_call'],
                generation_messages=messages, max_new_tokens=policy.MAX_NEW_TOKENS,
                started_unix=intent['started_unix'], finished_unix=time.time(),
                elapsed_seconds=time.time() - intent['started_unix'],
                previous_sha256=intent['previous_sha256'], actor_state=portable.PARENT_STATE,
                tasks_sha256=policy.TASKS_SHA)
            write(output / f'CALL_{calls:04d}.json', row)
            write(output / 'PROGRESS.json', dict(binding, calls=calls, failures=failures,
                last_task_id=task['id'], last_kind=kind, last_generated_tokens=row['generated_tokens'],
                last_outcome_pass=row['outcome_pass'], updated_unix=time.time()))
            return row

        completed = 0
        for position, task in enumerate(document['tasks']):
            if position % 2 != shard:
                continue
            if recovery and completed == 0:
                saved = recovery['saved_sources'][str(index)]
                assert sha(saved['path']) == saved['sha256']
                rich = json.loads(Path(saved['path']).read_text())
                assert rich['task_id'] == task['id'] and rich['kind'] == 'rich'
                assert rich['condition'] == condition and rich['physical_index'] == index
                assert rich['actor_state'] == portable.PARENT_STATE
                assert rich['tasks_sha256'] == policy.TASKS_SHA
                assert rich['generation_messages'] == policy.prompt(task, condition, 'rich')[0]
                assert rich['target_sha256'] == hashlib.sha256(rich['target'].encode()).hexdigest()
                write(output / 'REUSED_SOURCE.json', dict(saved, task_id=task['id'],
                    global_call=rich['global_call'], regenerated=False))
            else:
                rich = generate(task, 'rich')
            kind = policy.followup(condition, rich['outcome_pass']) if rich is not None else None
            if kind is not None:
                generate(task, kind, rich['target'])
            else:
                write(output / f'{task["id"]}_SKIPPED.json', dict(task_id=task['id'],
                    reason='source_failed_oracle_or_context', skipped='new_record', condition=condition))
            completed += 1
        engine.verify_base()
        assert _state_hash(parameters) == portable.PARENT_STATE
        write(output / 'RESULT.json', dict(binding, status='COMPLETE', model_calls=calls,
            context_failures=failures, completed_tasks=completed, denominator=128,
            reused_source_calls=1 if recovery else 0,
            finished_unix=time.time(), adapter_state=portable.PARENT_STATE, frozen_base_unchanged=True))
    except BaseException as error:
        write(output / 'FAILED.json', dict(binding, status='FAILED', reserved_calls=calls,
            error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise


def launch(root):
    bind_host()
    assert os.geteuid() != 0
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    publication = json.loads((root / 'PUBLICATION.json').read_text())
    assert publication['own_cpu_tests_passed'] and publication['dated_builder_publication']
    for relative, expected in publication['files'].items():
        assert sha(root / relative) == expected, relative
    prepared = json.loads((root / 'PREPARED.json').read_text())
    assert prepared['status'] == 'PREPARED_NO_MODEL' and prepared['base_verification']['verified']
    assert prepared['tasks_sha256'] == policy.TASKS_SHA
    assert json.loads((root / 'PROTOCOL.json').read_text()) == policy.protocol()
    output = root / 'run'
    output.mkdir(exist_ok=False)
    started = time.time()
    deadline = started + policy.MAX_SECONDS
    indices = list(ownership.DEVICES)
    allocation_started = started
    if (root / 'RECOVERY.json').exists():
        recovery = json.loads((root / 'RECOVERY.json').read_text())
        original_start = Path(recovery['original_root']) / 'run/START.json'
        assert sha(original_start) == recovery['original_start_sha256']
        original = json.loads(original_start.read_text())
        deadline = original['hard_deadline_unix']
        allocation_started = original['started_unix']
        indices = recovery['indices']
        assert indices == [0, 1, 2, 3]
        for saved in recovery['saved_sources'].values():
            assert sha(saved['path']) == saved['sha256']
        assert time.time() < original['native_deadline_unix'] - 60
    assert deadline < ownership.existing.LEASE_CUTOFF - 6 * 3600
    write(output / 'START.json', dict(started_unix=started, hard_deadline_unix=deadline,
        native_deadline_unix=deadline - 300, assigned_gpus={index: ownership.DEVICES[index] for index in indices},
        original_allocation_started_unix=allocation_started,
        max_calls=policy.MAX_CALLS, assigned_gpu_hours_ceiling=72, fits=0, updates=0,
        lease_cutoff_unix=ownership.existing.LEASE_CUTOFF, host_sha256=policy.HOST_SHA256,
        publication=publication))
    children, logs = [], []
    status = 'FAILED'
    try:
        for index in indices:
            snapshot = ownership.scan(index, root / 'SERVICE_IDENTITY.json')
            write(output / f'PRE_SCAN_{index}.json', snapshot)
            if not snapshot['clear']:
                raise RuntimeError('ownership_scan_blocked:' + str(index) + ':' + str(snapshot['blocking_reasons']))
        for index in indices:
            uuid = ownership.DEVICES[index]
            snapshot = ownership.scan(index, root / 'SERVICE_IDENTITY.json')
            write(output / f'ADMISSION_{index}.json', snapshot)
            if not snapshot['clear']:
                raise RuntimeError('immediate_admission_blocked:' + str(index))
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=uuid, PYTHONPATH=str(root / 'source'),
                HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1')
            log = (output / f'shard{index}.log').open('x')
            logs.append(log)
            child = subprocess.Popen([ownership.existing.PYTHON, '-B', '-m',
                'gpu.orch_rich_hot_node3_run', 'screen', '--root', str(root), '--index', str(index)],
                env=environment, cwd=root / 'source', stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True)
            children.append(child)
            write(output / f'LAUNCH_{index}.json', dict(pid=child.pid, index=index, uuid=uuid,
                condition=policy.allocation(index)[0], started_unix=time.time()))
        while any(child.poll() is None for child in children):
            if time.time() >= deadline - 180:
                raise TimeoutError('common_12h_deadline')
            time.sleep(5)
        status = 'COMPLETE' if all(child.returncode == 0 for child in children) else 'SHARD_FAILURE'
    except BaseException as error:
        write(output / 'GUARD_FAILED.json', dict(error_type=type(error).__name__, error=str(error)))
        raise
    finally:
        for child in children:
            ownership.existing.stop_owned(child)
        for log in logs:
            log.close()
        write(output / 'RESULT.json', dict(status=status, exit_codes=[child.returncode for child in children],
            finished_unix=time.time(), assigned_gpu_hours=len(indices) * (time.time() - started) / 3600,
            global_assigned_gpu_hours=6 * (time.time() - allocation_started) / 3600))
        for index in indices:
            write(output / f'RELEASE_{index}.json', ownership.scan(index, root / 'SERVICE_IDENTITY.json'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'launch', 'screen'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--index', type=int, choices=range(6))
    options = parser.parse_args()
    if options.phase == 'screen':
        screen(options.root, options.index)
    else:
        globals()[options.phase](options.root)


if __name__ == '__main__':
    main()
