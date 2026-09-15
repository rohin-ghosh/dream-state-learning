"""Immutable, bounded, read-only original37ec generation on allocated A100s."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu.orch_math_rich_source import verify_archive
from gpu.orch_rich_hot_a100_scan import host_identity, identity, scan, sha
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_rich_hot_a100 as policy


ROOT = Path('/localhome/local-rohing/orch_rich_hot_a100_20260915_attempt1')
PILOT = Path('/localhome/local-rohing/orch_l2_rich_math_20260915_attempt1')
TRANSFER = Path('/localhome/local-rohing/orch_l1_bootstrap_transfer_20260915_attempt1')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
LEASE_END = 1790463900
BUNDLE_SHA = policy.intensity.BUNDLE_SHA


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + f'.{os.getpid()}.partial')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
    temporary.replace(path)


def exclusive(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


class Engine(portable.source.Engine):
    def generate(self, messages, *, max_new_tokens=policy.CAP):
        policy.require(max_new_tokens == policy.CAP, '8192_top_cap_required')
        self.check('generation')
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                    return_dict=False, truncation=False, padding=False)
        cap = policy.budget(len(tokens))
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            max_new_tokens=cap, min_new_tokens=0, repetition_penalty=1.0,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                                            generation_config=config)
        policy.require(generated[0, :len(tokens)].tolist() == tokens, 'generation_prefix_changed')
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        raw = self.tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False,
                                    clean_up_tokenization_spaces=False)
        return dict(raw=raw, token_ids=tail, prompt_tokens=len(tokens), terminal=terminal,
                    truncated=not terminal and len(tail) == cap, max_new_tokens=cap, context=policy.CONTEXT)


def validate(root):
    policy.require(root == ROOT and not root.is_symlink() and host_identity() == policy.HOST_SHA, 'exact_root_host')
    prepared = read(root / 'PREPARE.json')
    policy.require(sha(root / 'source.tar') == prepared['source_sha256'], 'archive_drift')
    policy.require(verify_archive(root / 'source.tar', root / 'source') == prepared['source_files'], 'source_drift')
    policy.require(all(sha(root / name) == digest for name, digest in prepared['files'].items()), 'input_drift')
    policy.require(sha(PILOT / 'PREPARE.json') == prepared['pilot_prepare_sha256'], 'pilot_drift')
    return prepared


def prepare(root):
    from safetensors.torch import load_file
    from transformers import AutoConfig

    policy.require(root == ROOT and host_identity() == policy.HOST_SHA and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
                   'cpu_only_exact_host_root')
    policy.require(not (root / 'PREPARE.json').exists(), 'prepare_once')
    prior = read(PILOT / 'PREPARE.json')
    manifest = portable.read_manifest(prior['bundle'], expected_manifest_sha256=BUNDLE_SHA)
    base = portable.verify_base_files(prior['bundle'], prior['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    initial = bridge.AdapterIdentity.from_document(prior['initial'])
    initial.verify()
    policy.require(initial.state_sha256 == portable.PARENT_STATE and initial.base_sha256 == manifest['expected_base_sha256'],
                   'original37ec_frozen_base_required')
    tensors = load_file(str(Path(initial.path) / 'adapter_model.safetensors'), device='cpu')
    mounted = {name.replace('.lora_A.', '.lora_A.default.').replace('.lora_B.', '.lora_B.default.'): value
               for name, value in tensors.items()}
    policy.require(native.state_hash(mounted) == portable.PARENT_STATE, 'saved_tensor_hash')
    config = AutoConfig.from_pretrained(prior['model_dir'], local_files_only=True, trust_remote_code=False)
    policy.require(config.max_position_embeddings >= policy.CONTEXT, 'native_context_unsupported')
    tasks = read(root / 'TASKS.json')
    policy.intensity.validate(tasks)
    policy.require(sha(root / 'TASKS.json') == policy.intensity.TASKS_SHA and
                   sha(root / 'gsm8k_train.jsonl') == policy.SOURCE_SHA, 'cached_train_source')
    records = [json.loads(line) for line in (root / 'gsm8k_train.jsonl').read_text().splitlines()]
    policy.require(not set(manifest['old_ids']) & {task['id'] for task in tasks['tasks']}, 'old_id_overlap')
    tokenizer = native.source.native.load_local_tokenizer(prior['model_dir'])
    counts = []
    for task in tasks['tasks']:
        record = records[int(task['id'].rsplit('-', 1)[1])]
        policy.require(record['question'].strip() == task['question'] and
                       policy.original.number(record['answer'].rsplit('####', 1)[1]) == policy.original.number(task['gold']),
                       'source_question_gold_mismatch')
        for strategy in ('ORIGINAL_RICH', 'LIGHT_BRANCH', 'SELF_EVALUATE'):
            for previous in (None, 'I checked the quantities.\nFINAL: 1'):
                messages = policy.messages(task, strategy, previous)
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                       return_dict=False, truncation=False, padding=False)
                policy.require(tokens == tokenizer.encode(text, add_special_tokens=False), 'exact_encoder_mismatch')
                policy.require(tokenizer.decode(tokens, skip_special_tokens=False,
                               clean_up_tokenization_spaces=False) == text, 'encoder_roundtrip')
                policy.require(policy.budget(len(tokens)) == policy.CAP, 'initial_probe_context')
                counts.append(len(tokens))
    policy.require(tokenizer.encode(tokenizer.eos_token, add_special_tokens=False) == [tokenizer.eos_token_id], 'exact_eos')
    names = ('TASKS.json', 'DATA_PROVENANCE.json', 'gsm8k_train.jsonl', 'PROTOCOL.md', 'DIRECTIVE.txt',
             'SERVICE_IDENTITY.json', 'SOURCE_INVENTORY.json', 'CPU_TESTS.txt')
    prepared = dict(status='CPU_PREPARED_NO_MODEL', initial=initial.document(), model_dir=prior['model_dir'],
        bundle=prior['bundle'], base_verification=base, pilot_prepare_sha256=sha(PILOT / 'PREPARE.json'),
        source_sha256=sha(root / 'source.tar'), source_files=verify_archive(root / 'source.tar', root / 'source'),
        files={name: sha(root / name) for name in names}, max_position_embeddings=config.max_position_embeddings,
        exact_encoder_cases=len(counts), prompt_tokens_range=[min(counts), max(counts)], native_calls=0,
        model_loads=0, fits=0, prepared_unix=time.time(), host_sha256=host_identity())
    exclusive(root / 'PREPARE.json', prepared)
    print(json.dumps(dict(status=prepared['status'], prepare_sha256=sha(root / 'PREPARE.json'),
                         encoder_cases=len(counts), context=config.max_position_embeddings)))


def handoff(root, index):
    if index not in (2, 3, 7) or not (root / 'HANDOFF_REQUEST.json').exists():
        return False
    request = read(root / 'HANDOFF_REQUEST.json')
    path = Path(request['child_ready_path'])
    policy.require(path.is_absolute() and path.is_file() and sha(path) == request['child_ready_sha256'],
                   'exact_relayed_child_ready_required')
    return True


def run(root, index):
    prepared = validate(root)
    lifetime = read(root / 'LIFETIME.json')
    strategy, shard = policy.allocation(index)
    uuid = policy.DEVICES[index]
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == uuid and
        ('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'), 'exact_cvd')
    output = root / f'gpu{index}'
    output.mkdir(exist_ok=False)
    stopping = []
    signal.signal(signal.SIGTERM, lambda signum, frame: stopping.append(signum))
    loaded, calls, status = None, 0, 'FAILED'

    def check(label):
        policy.require(time.time() < lifetime['native_deadline_unix'], 'fixed_deadline:' + label)

    try:
        check('load')
        portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
        initial = bridge.AdapterIdentity.from_document(prepared['initial'])
        binding = bridge.StageBinding(root.name, bridge.ARMS[1], 0, 'sealed_readout', initial,
                                      False, True, sha(root / 'PREPARE.json'))
        loaded = native.load_stage(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
                                  context=native.StageContext(), check=check, engine_factory=Engine)
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
              uuid=uuid, physical_index=index, strategy=strategy, native_calls=0, loaded_unix=time.time()))
        tasks = read(root / 'TASKS.json')['tasks']
        for position, task in enumerate(tasks):
            previous = None
            for stage in ('source', 'reconsider' if strategy == 'SELF_EVALUATE' else 'new_record'):
                if stopping or handoff(root, index):
                    status = 'CHECKPOINT_HANDOFF'
                    break
                check('reserve')
                policy.require(calls < policy.MAX_CALLS, 'fixed_gpu_call_limit')
                messages = policy.messages(task, strategy, previous)
                row = dict(task_id=task['id'], gold=task['gold'], family=task['family'], strategy=strategy,
                           stage=stage, position=position, messages=messages, started_unix=time.time(),
                           trainingAllowed=False, admitted=False, semantic_status='UNREVIEWED')
                exclusive(output / f'INTENT_{calls:04d}.json', row)
                call_index = calls
                calls += 1
                try:
                    row['response'] = loaded.engine.generate(messages)
                    row['outcome'] = policy.outcome(task, row['response'])
                except BaseException as error:
                    row['error'] = dict(type=type(error).__name__, message=str(error))
                    raise
                finally:
                    row['finished_unix'] = time.time()
                    write(output / f'CALL_{call_index:04d}.json', row)
                write(output / 'CHECKPOINT.json', dict(calls=calls, last_call=call_index, finished_unix=time.time()))
                previous = row['response']['raw']
                if stage == 'source' and not policy.followup_allowed(strategy, row['outcome']):
                    write(output / f'SKIPPED_{position:03d}.json', dict(task_id=task['id'], reason='source_numeric_FINAL_failed'))
                    break
            if status == 'CHECKPOINT_HANDOFF':
                break
        if status != 'CHECKPOINT_HANDOFF':
            status = 'COMPLETE'
    except BaseException as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        if loaded is not None:
            try:
                observed = loaded.verify_unchanged()
                portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
                write(output / 'AFTER.json', dict(observed=observed.document(), unchanged=True))
            except BaseException as error:
                status = 'IDENTITY_FAILED'
                write(output / 'AFTER_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        write(output / 'TERMINAL.json', dict(status=status, reserved_calls=calls, fits=0, parent_calls=0,
              semantic_reviews=0, admitted_rows=0, denominator=256, finished_unix=time.time()))
    policy.require(status in ('COMPLETE', 'CHECKPOINT_HANDOFF'), 'native_terminal_failure')


def transfer_release():
    terminal = read(TRANSFER / 'TERMINAL.json')
    policy.require(terminal['status'] == 'COMPLETE' and terminal['reserved_calls'] == 96 and
                   terminal['all_states_verified'] and all(terminal['releases'].values()), 'formal_transfer_release_required')
    receipts = {}
    for arm in ('FULL', 'OFF', 'ORIGINAL37EC'):
        path = TRANSFER / f'RELEASE_{arm}.json'
        report = read(path)
        policy.require(report['clear'] and report['scanner_euid'] == 0, 'transfer_privileged_release')
        receipts[str(path)] = sha(path)
    return dict(terminal_sha256=sha(TRANSFER / 'TERMINAL.json'), releases=receipts)


def stop_owned(child, expected):
    if child.poll() is not None:
        return
    descriptor = os.pidfd_open(child.pid)
    try:
        policy.require(identity(Path('/proc') / str(child.pid)) == expected and expected['uid'] == os.getuid(),
                       'owned_exact_pid_required')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        try:
            child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            policy.require(identity(Path('/proc') / str(child.pid)) == expected, 'pid_changed')
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            child.wait(timeout=20)
    finally:
        os.close(descriptor)


def launch(root):
    validate(root)
    ready = read(root / 'READY.json')
    policy.require(ready['prepare_sha256'] == sha(root / 'PREPARE.json') and ready['cpu_tests_passed'] and
                   ready['builder_receipt_sha256'] == sha(root / 'BUILDER_RECEIPT.md'), 'published_pregpu_required')
    lock = (root / 'GUARD.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lifetime = policy.lease_deadline(time.time(), LEASE_END)
    exclusive(root / 'LIFETIME.json', lifetime)
    exclusive(root / 'GUARD_IDENTITY.json', identity(Path('/proc') / str(os.getpid())))
    children, logs, released = {}, [], {}
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(SystemExit(128 + signum)))
    try:
        for index in (4, 5, 6):
            if index in (4, 5, 6):
                write(root / f'TRANSFER_RELEASE_{index}.json', transfer_release())
            report = scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / f'ADMISSION_{index}.json', report)
            policy.require(report['clear'] and report['scanner_euid'] == 0, 'privileged_admission_failed')
            if handoff(root, index):
                released[index] = True
                write(root / f'RELEASE_{index}.json', report)
                continue
            log = (root / f'gpu{index}.log').open('x')
            logs.append(log)
            child = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_rich_hot_a100_run', 'run', '--root', str(root),
                '--index', str(index)], cwd=root / 'source', start_new_session=True,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.DEVICES[index], PYTHONPATH=str(root / 'source'),
                         HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
                         OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'),
                stdout=log, stderr=subprocess.STDOUT)
            pinned = identity(Path('/proc') / str(child.pid))
            children[index] = (child, pinned)
            exclusive(root / f'LAUNCH_{index}.json', dict(identity=pinned, uuid=policy.DEVICES[index],
                      launched_unix=time.time(), ready_sha256=sha(root / 'READY.json')))
        while any(child.poll() is None for child, pinned in children.values()):
            policy.require(time.time() < lifetime['hard_deadline_unix'] - 240, '12hour_guard')
            for index, (child, pinned) in children.items():
                if child.poll() is not None and index not in released:
                    report = scan(index, root / 'SERVICE_IDENTITY.json')
                    write(root / f'RELEASE_{index}.json', report)
                    released[index] = report['clear']
            time.sleep(3)
    except BaseException as error:
        write(root / 'GUARD_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        for child, pinned in children.values():
            stop_owned(child, pinned)
        for log in logs:
            log.close()
        for index in children:
            if index not in released:
                report = scan(index, root / 'SERVICE_IDENTITY.json')
                write(root / f'RELEASE_{index}.json', report)
                released[index] = report['clear']
        write(root / 'TERMINAL.json', dict(returncodes={index: child.returncode for index, (child, _) in children.items()},
              releases=released, finished_unix=time.time(), lifetime=lifetime))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'launch', 'run'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--index', type=int)
    options = parser.parse_args()
    if options.phase == 'run':
        run(options.root, options.index)
    else:
        globals()[options.phase](options.root)
