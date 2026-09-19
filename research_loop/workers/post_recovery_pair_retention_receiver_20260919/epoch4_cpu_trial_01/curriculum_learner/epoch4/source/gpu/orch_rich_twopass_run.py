"""Four bounded native shards, paired by one streamed child draft per task."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import astra_portable_actor_bundle as portable
from gpu.orch_math_rich_screen import mounted_adapter_parameters
from gpu.orch_math_rich_source import verify_archive
from organism_v6 import orch_rich_twopass as policy


BUNDLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
DEVICES = ('GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0', 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4',
           'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05', 'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733')
SECONDS = 7200
LEASE_END = int(datetime(2026, 9, 21, 8, 43, tzinfo=timezone.utc).timestamp())


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.{os.getpid()}.partial')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def process_start(pid):
    return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]


def reserve(root, position, stage, condition):
    key = f'{position:04d}_{condition}_{stage}'
    with (root / 'CALLS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        count = sum(1 for unused in stream)
        assert count < policy.MAX_CALLS, 'lifetime_call_cap'
        marker = root / 'reservations' / (key + '.json')
        marker.parent.mkdir(exist_ok=True)
        with marker.open('x') as reserved:
            json.dump(dict(index=count, key=key), reserved)
        stream.write(json.dumps(dict(index=count, position=position, stage=stage, condition=condition,
                                     reserved_unix=time.time(), pid=os.getpid())) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    return count


def scan(root, index):
    assert sha(root / 'scanner.py') == '6ed5c48c144dcf26dcb856798ab31d69e39bc66b6780211f2b10553972f8519b'
    assert sha(root / 'service_exceptions.json') == 'ed2c9111a50b09bdf20859d3395769945b79ce8ba1f5554ed7fe55b99cfd5117'
    with (root / 'service_exceptions.json').open() as services:
        completed = subprocess.run(['python3', str(root / 'scanner.py'), str(index), DEVICES[index]],
            stdin=services, capture_output=True, text=True, timeout=30,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
    result = json.loads(completed.stdout)
    result['scanner_exit_code'] = completed.returncode
    return result


class Engine(portable.source.Engine):
    def generate(self, messages, *, max_new_tokens):
        assert max_new_tokens in policy.CAPS.values()
        self.check('generation')
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
        assert 0 < len(tokens) <= policy.CONTEXT, 'context_overflow_no_truncation'
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            max_new_tokens=max_new_tokens, repetition_penalty=1.0,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs), generation_config=config)
        assert generated[0, :len(tokens)].tolist() == tokens, 'generated_prefix_changed'
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        text = self.tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False,
                                     clean_up_tokenization_spaces=False)
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail, raw=text,
                    terminal=terminal, truncated=not terminal and len(tail) == max_new_tokens)


def prepare(root, bundle, model_dir):
    assert sha(root / 'TASKS.json') == policy.TASKS_SHA
    document = read(root / 'TASKS.json')
    policy.validate_roster(document)
    provenance = read(root / 'DATA_PROVENANCE.json')
    assert provenance['tasks_sha256'] == policy.TASKS_SHA
    assert provenance['source_sha256'] == '17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465'
    assert provenance['excluded_distinct_ids'] == provenance['excluded_distinct_question_hashes'] == 1216
    verified_files = verify_archive(root / 'source.tar', root / 'source')
    manifest = portable.read_manifest(bundle, expected_manifest_sha256=BUNDLE_SHA)
    verification = portable.verify_base_files(bundle, model_dir, expected_manifest_sha256=BUNDLE_SHA)
    assert manifest['parent_state'] == portable.PARENT_STATE
    receipt = dict(status='CPU_PREPARED_NO_MODEL', created_utc=datetime.now(timezone.utc).isoformat(),
                   roster_sha256=policy.TASKS_SHA, provenance_sha256=sha(root / 'DATA_PROVENANCE.json'),
                   source_sha256=sha(root / 'source.tar'), source_verified_files=verified_files,
                   actor=portable.PARENT_STATE, bundle=str(bundle), bundle_sha256=BUNDLE_SHA,
                   model_dir=str(model_dir), base_verification=verification,
                   caps=policy.CAPS, context=policy.CONTEXT, calls=policy.MAX_CALLS,
                   fixed_tasks=256, targets_per_condition_max=512, fits=0, model_calls=0,
                   seconds=SECONDS, assigned_gpu_hours=8,
                   native_module_sha256=sha(Path(__file__)), policy_sha256=sha(Path(policy.__file__)))
    write(root / 'PREPARE.json', receipt)
    return receipt


def shard(root, shard_index):
    output = root / f'shard{shard_index}'
    output.mkdir(exist_ok=False)
    prepared, lifetime = read(root / 'PREPARE.json'), read(root / 'LIFETIME.json')
    assert sha(root / 'TASKS.json') == policy.TASKS_SHA
    verify_archive(root / 'source.tar', root / 'source')
    condition = 'BRANCH' if shard_index < 2 else 'CONTINUE'
    assert os.environ['CUDA_VISIBLE_DEVICES'] == DEVICES[shard_index]
    assert ('CUDA_VISIBLE_DEVICES=' + DEVICES[shard_index]).encode() in Path('/proc/self/environ').read_bytes().split(b'\0')
    tasks = read(root / 'TASKS.json')['tasks']
    calls = []
    binding = dict(shard=shard_index, condition=condition, pid=os.getpid(), start_ticks=process_start(os.getpid()),
                   uuid=DEVICES[shard_index], tasks_sha256=policy.TASKS_SHA, fits=0, updates=0,
                   started_unix=time.time(), deadline_unix=lifetime['deadline_unix'])
    write(output / 'REQUEST.json', binding)

    def check(label):
        if time.time() >= lifetime['deadline_unix']:
            raise TimeoutError('bounded_native_deadline:' + label)

    try:
        arguments = portable.read_bundle(prepared['bundle'], expected_manifest_sha256=BUNDLE_SHA,
            model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=DEVICES[shard_index])
        engine = Engine(arguments, portable.source.native.load_local_tokenizer(prepared['model_dir']), check=check)
        from organism_v6.pcfl_vertical_train import _state_hash
        parameters = mounted_adapter_parameters(engine.model)
        assert _state_hash(parameters) == portable.PARENT_STATE
        write(output / 'ACTOR_READY.json', dict(binding, actor_state=portable.PARENT_STATE, runtime=engine.runtime))

        def generate(position, stage, draft=None, final=None):
            check('before_reservation')
            task = tasks[position]
            label = 'SHARED' if stage == 'draft' else condition
            index = reserve(root, position, stage, label)
            messages, student = policy.prompt(task, stage, condition, draft, final)
            row = dict(position=position, task_id=task['id'], family=task['family'], stage=stage, condition=label,
                       status='RESERVED', index=index, max_new_tokens=policy.CAPS[stage], messages=messages,
                       student_prefix=student, started_unix=time.time(), actor_state=portable.PARENT_STATE)
            path = output / f'CALL_{index:04d}.json'
            write(path, row)
            try:
                response = engine.generate(messages, max_new_tokens=policy.CAPS[stage])
                row.update(policy.capture(task, stage, label, response, student,
                           policy.text_sha(draft) if draft is not None else None), status='OK')
            except Exception as error:
                row.update(status='ERROR', outcome_pass=False, candidate=False, admitted=False,
                           error_type=type(error).__name__, error=str(error))
            row['finished_unix'] = time.time()
            write(path, row)
            calls.append(index)
            if row['status'] == 'OK':
                try:
                    with (root / 'FIRST_NATIVE_CALL.json').open('x') as stream:
                        json.dump(dict(path=str(path), file_sha256=sha(path), utc=datetime.now(timezone.utc).isoformat(),
                                       index=index, shard=shard_index, stage=stage, actor_state=portable.PARENT_STATE), stream)
                except FileExistsError:
                    pass
            return row

        for position, task in enumerate(tasks):
            if position % 2 != shard_index % 2:
                continue
            check('task')
            draft_path = root / 'drafts' / f'{position:04d}.json'
            if shard_index < 2:
                draft = generate(position, 'draft')
                write(draft_path, draft)
            else:
                while not draft_path.exists():
                    check('shared_draft_wait')
                    time.sleep(.2)
                draft = read(draft_path)
            assert draft['task_id'] == task['id'] and draft['actor_state'] == portable.PARENT_STATE
            if draft['status'] != 'OK':
                write(output / f'TASK_{position:04d}.json', dict(position=position, task_id=task['id'],
                      final_status='SKIPPED_SHARED_DRAFT_ERROR', record_status='SKIPPED', fixed_denominator=256))
                continue
            assert policy.text_sha(draft['target']) == draft['target_sha256']
            final = generate(position, 'final', draft=draft['target'])
            record = generate(position, 'record', draft=draft['target'], final=final['target']) if policy.record_allowed(final) else None
            write(output / f'TASK_{position:04d}.json', dict(position=position, task_id=task['id'],
                  final_status=final['status'], record_status=record['status'] if record else 'SKIPPED_FINAL_NOT_CORRECT',
                  draft_sha256=draft['target_sha256'], final_index=final['index'],
                  record_index=record['index'] if record else None, fixed_denominator=256))
        engine.verify_base()
        assert _state_hash(parameters) == portable.PARENT_STATE
        write(output / 'RESULT.json', dict(binding, status='COMPLETE', attempts=len(calls),
              finished_unix=time.time(), actor_state=portable.PARENT_STATE, fixed_tasks=128))
    except BaseException as error:
        write(output / 'FAILED.json', dict(binding, attempts=len(calls), error_type=type(error).__name__, error=str(error)))
        raise


def launch(root):
    prepared = read(root / 'PREPARE.json')
    publication = read(root / 'PUBLICATION.json')
    assert publication['prepare_sha256'] == sha(root / 'PREPARE.json') and publication['cpu_tests_passed'] is True
    assert publication['source_sha256'] == prepared['source_sha256'] == sha(root / 'source.tar')
    assert sha(root / 'TASKS.json') == policy.TASKS_SHA
    assert time.time() + SECONDS < LEASE_END - 21600
    for index in range(4):
        snapshot = scan(root, index)
        write(root / f'PRE_GPU{index}.json', snapshot)
        assert snapshot['clear'] and snapshot['scanner_exit_code'] == 0, snapshot.get('unresolved')
    started = time.time()
    with (root / 'LIFETIME.json').open('x') as stream:
        json.dump(dict(started_unix=started, deadline_unix=started + SECONDS - 30,
                       hard_deadline_unix=started + SECONDS, gpu_hours_cap=8, call_cap=policy.MAX_CALLS), stream)
    children = []
    status = 'FAILED'
    try:
        for index, uuid in enumerate(DEVICES):
            log = (root / f'shard{index}.log').open('x')
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=uuid, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                               PYTHONDONTWRITEBYTECODE='1', CUDA_CACHE_PATH=str(root / 'cache' / str(index)))
            process = subprocess.Popen([sys.executable, '-m', 'gpu.orch_rich_twopass_run', 'shard',
                '--root', str(root), '--shard', str(index)], cwd=root / 'source', env=environment,
                stdout=log, stderr=subprocess.STDOUT)
            children.append((process, process_start(process.pid), log))
        while any(process.poll() is None for process, unused, log in children):
            if time.time() >= started + SECONDS - 5:
                raise TimeoutError('hard_native_lifetime')
            if any(process.poll() not in (None, 0) for process, unused, log in children):
                raise RuntimeError('native_shard_failed_no_retry')
            time.sleep(1)
        assert all(process.returncode == 0 for process, unused, log in children)
        status = 'COMPLETE'
    finally:
        for process, start, log in children:
            if process.poll() is None:
                assert process_start(process.pid) == start and Path(f'/proc/{process.pid}').stat().st_uid == os.getuid()
                process.send_signal(signal.SIGKILL)
                process.wait()
            log.close()
        ledger = root / 'CALLS.jsonl'
        write(root / 'TERMINAL.json', dict(status=status, started_unix=started, finished_unix=time.time(),
              attempted_calls=len(ledger.read_text().splitlines()) if ledger.exists() else 0,
              exits=[process.returncode for process, unused, log in children], fits=0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'launch', 'shard', 'scan'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--model-dir', type=Path)
    parser.add_argument('--shard', type=int, choices=range(4))
    options = parser.parse_args()
    root = options.root.resolve()
    assert root.parent == Path('/localhome/local-rohing') and root.name.startswith('orch_rich_twopass_')
    if options.phase == 'scan':
        print(json.dumps(scan(root, options.shard)))
    elif options.phase == 'prepare':
        print(json.dumps(prepare(root, options.bundle, options.model_dir), indent=2))
    elif options.phase == 'launch':
        launch(root)
    else:
        shard(root, options.shard)


if __name__ == '__main__':
    main()
