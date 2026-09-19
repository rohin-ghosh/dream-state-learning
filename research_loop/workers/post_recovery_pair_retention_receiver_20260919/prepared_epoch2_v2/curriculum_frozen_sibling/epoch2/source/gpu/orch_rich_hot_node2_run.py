"""Eight finite high-budget generation shards, original37ec, no fitting/review."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu.orch_l2_budget_readout_run import LEASE_END, PYTHON, stop_owned
from gpu.orch_l2_budget_readout_scan import HOST, identity as process_identity
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA, read, sha, write
from gpu.orch_math_rich_source import verify_archive
from gpu.orch_rich_hot_node2_scan import scan
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_rich_hot_node2 as policy


ROOT = Path('/localhome/local-rohing/orch_rich_hot_node2_20260915_attempt1')


class Engine(portable.source.Engine):
    def generate(self, messages, *, max_new_tokens=8192):
        policy.require(max_new_tokens == policy.CAP, 'fixed_8192_cap')
        self.check('generation')
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
        policy.require(0 < len(tokens) and len(tokens) + max_new_tokens <= policy.CONTEXT, 'context_overflow_no_cropping')
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            max_new_tokens=max_new_tokens, repetition_penalty=1.0, eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs), generation_config=config)
        policy.require(generated[0, :len(tokens)].tolist() == tokens, 'generation_prefix_changed')
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        raw = self.tokenizer.decode(tail[:-1] if terminal else tail, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail, raw=raw, terminal=terminal,
                    truncated=not terminal and len(tail) == max_new_tokens, max_new_tokens=max_new_tokens, context=policy.CONTEXT)


def validate(root):
    policy.require(root == ROOT and socket.gethostname() == HOST, 'exact_native_root_host')
    prepared = read(root / 'PREPARE.json')
    policy.require(sha(root / 'source.tar') == prepared['source_sha256'], 'source_archive_drift')
    policy.require(verify_archive(root / 'source.tar', root / 'source') == prepared['source_files'], 'source_drift')
    policy.require(all(sha(root / name) == digest for name, digest in prepared['files'].items()), 'frozen_input_drift')
    return prepared


def prepare(root):
    from safetensors.torch import load_file
    from transformers import AutoConfig

    policy.require(root == ROOT and socket.gethostname() == HOST and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_only')
    policy.require(not (root / 'PREPARE.json').exists(), 'prepare_once')
    prior = read(Path('/localhome/local-rohing/orch_l2_rich_math_20260915_attempt1/LANE_PREPARE.json'))
    bundle = '/tmp/astra_portable_37ec_20260914_attempt1'
    base = portable.verify_base_files(bundle, prior['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    identity = bridge.AdapterIdentity.from_document(read(root / 'INITIAL.json'))
    policy.require(identity.state_sha256 == policy.INITIAL_STATE, 'original37ec_required')
    tensors = load_file(str(Path(identity.path) / 'adapter_model.safetensors'), device='cpu')
    mounted = {name.replace('.lora_A.', '.lora_A.default.').replace('.lora_B.', '.lora_B.default.'): value for name, value in tensors.items()}
    policy.require(native.state_hash(mounted) == identity.state_sha256, 'saved_tensor_hash_mismatch')
    configuration = AutoConfig.from_pretrained(prior['model_dir'], local_files_only=True, trust_remote_code=False)
    policy.require(configuration.max_position_embeddings >= policy.CONTEXT, 'model_context_unsupported')
    tasks, provenance = read(root / 'TASKS.json'), read(root / 'DATA_PROVENANCE.json')
    policy.require(provenance['source_sha256'] == policy.SOURCE_SHA and sha(root / 'gsm8k_train.jsonl') == policy.SOURCE_SHA, 'cached_source_mismatch')
    records = [json.loads(line) for line in (root / 'gsm8k_train.jsonl').read_text().splitlines()]
    policy.require(tasks == policy.roster(records, set(tasks['excluded_ids']), set(tasks['excluded_question_hashes'])), 'prospective_cohort_drift')
    tokenizer = native.source.native.load_local_tokenizer(prior['model_dir'])
    counts = [len(tokenizer.apply_chat_template(policy.messages(task, condition), tokenize=True, add_generation_prompt=True,
                return_dict=False)) for task in tasks['tasks'] for condition in policy.CONDITIONS]
    policy.require(max(counts) + policy.CAP <= policy.CONTEXT, 'initial_prompt_context_overflow')
    names = ['TASKS.json', 'DATA_PROVENANCE.json', 'INITIAL.json', 'PROTOCOL.md', 'SERVICE_IDENTITY.json', 'gsm8k_train.jsonl']
    write(root / 'PREPARE.json', dict(status='CPU_READY_NO_MODEL', model_dir=prior['model_dir'], bundle=bundle,
        identity=identity.document(), base=base, model_max_position_embeddings=configuration.max_position_embeddings,
        source_sha256=sha(root / 'source.tar'), source_files=verify_archive(root / 'source.tar', root / 'source'),
        files={name: sha(root / name) for name in names}, prompt_tokens_range=[min(counts), max(counts)],
        tasks_per_condition=len(tasks['tasks']), maximum_calls=tasks['max_calls'], fits=0, parent_calls=0,
        prepared_unix=time.time()))
    print(json.dumps(dict(prepare_sha256=sha(root / 'PREPARE.json'), tasks=len(tasks['tasks']), context=configuration.max_position_embeddings)))


def reserve(root, shard, task, stage, messages, deadline):
    policy.require(time.time() < deadline, 'original_deadline_no_reset')
    key = f"{shard}_{task['id']}_{stage}"
    with (root / 'CALLS.jsonl').open('a+') as ledger:
        fcntl.flock(ledger, fcntl.LOCK_EX)
        ledger.seek(0)
        count = sum(1 for line in ledger)
        policy.require(count < read(root / 'TASKS.json')['max_calls'], 'global_call_cap')
        row = dict(index=count, shard=shard, task_id=task['id'], stage=stage, messages=messages,
                   reserved_unix=time.time(), max_new_tokens=policy.CAP)
        with (root / 'reservations' / (key + '.json')).open('x') as marker:
            json.dump(row, marker)
            marker.flush()
            os.fsync(marker.fileno())
        ledger.seek(0, 2)
        ledger.write(json.dumps(row) + '\n')
        ledger.flush()
        os.fsync(ledger.fileno())
    return row


def run(root, shard):
    prepared = validate(root)
    lifetime = read(root / 'LIFETIME.json')
    uuid, condition = policy.UUIDS[shard], policy.CONDITIONS[shard // 2]
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == uuid, 'exact_uuid_only')
    output = root / f'shard{shard}'
    output.mkdir(exist_ok=False)
    loaded, status, completed = None, 'FAILED', 0

    def check(label):
        policy.require(time.time() < lifetime['native_deadline_unix'], 'finite_guardian:' + label)

    try:
        check('load')
        identity = bridge.AdapterIdentity.from_document(prepared['identity'])
        binding = bridge.StageBinding(root.name + f'_{shard}', bridge.ARMS[1], 0, 'sealed_readout', identity,
                                      False, True, sha(root / 'PREPARE.json'))
        loaded = native.load_stage(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
                                   context=native.StageContext(), check=check, engine_factory=Engine)
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
                                          uuid=uuid, condition=condition, max_new_tokens=policy.CAP, context=policy.CONTEXT))
        for position, task in enumerate(read(root / 'TASKS.json')['tasks']):
            if position % 2 != shard % 2:
                continue
            previous = None
            stages = ('draft', 'final') if condition in ('TWO_PASS', 'META_EVALUATE') else ('final',)
            for stage in stages:
                check('next_task')
                messages = policy.messages(task, condition, previous)
                row = reserve(root, shard, task, stage, messages, lifetime['native_deadline_unix'])
                row.update(condition=condition, task_position=position, gold=task['gold'], trainingAllowed=False)
                try:
                    response = loaded.engine.generate(messages, max_new_tokens=policy.CAP)
                    row.update(response=response, outcome=policy.outcome(task, response))
                    previous = response['raw']
                    completed += 1
                except Exception as error:
                    row['error'] = dict(type=type(error).__name__, message=str(error))
                finally:
                    row['finished_unix'] = time.time()
                    write(output / f"{task['id']}_{stage}.json", row)
                if 'error' in row:
                    break
        status = 'COMPLETE'
    except BaseException as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        if loaded is not None:
            try:
                after = loaded.verify_unchanged()
                portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
                write(output / 'AFTER.json', dict(observed=after.document(), unchanged=True, process=loaded.process))
            except BaseException as error:
                status = 'IDENTITY_FAILED'
                write(output / 'AFTER_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        write(output / 'TERMINAL.json', dict(status=status, completed_calls=completed, condition=condition,
            finished_unix=time.time(), fits=0, parent_calls=0, admitted_rows=0))


def launch(root):
    prepared = validate(root)
    ready = read(root / 'READY.json')
    policy.require(ready['prepare_sha256'] == sha(root / 'PREPARE.json') and ready['cpu_tests_passed'], 'cpu_readiness_required')
    policy.require(ready['builder_receipt_sha256'] == sha(root / 'BUILDER_RECEIPT.md'), 'builder_publication_required')
    lock = (root / 'NODE2_ALL8_ADMISSION.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.time()
    policy.require(started + policy.SECONDS < LEASE_END - 21600, 'lease_end_minus6h_guard')
    lifetime = dict(started_unix=started, native_deadline_unix=started + policy.SECONDS - 300,
        hard_deadline_unix=started + policy.SECONDS, assigned_gpu_hours_ceiling=128,
        max_calls=prepared['maximum_calls'], ready_sha256=sha(root / 'READY.json'))
    with (root / 'LIFETIME.json').open('x') as stream:
        json.dump(lifetime, stream, indent=2)
    with (root / 'NODE2_ALL8_LEASE_CLAIM.json').open('x') as stream:
        json.dump(dict(node=HOST, devices=policy.DEVICES, identity=process_identity(Path('/proc') / str(os.getpid())),
                       lifetime=lifetime, authority='Direct user90-93/Main allocation; own atomic claim plus full device admission'), stream, indent=2)
    (root / 'reservations').mkdir(exist_ok=False)
    children, logs, status = {}, [], 'FAILED'

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for shard in range(8):
            report = scan(shard, root / 'SERVICE_IDENTITY.json')
            write(root / f'ADMISSION_{shard}.json', report)
            policy.require(report['clear'] and report['scanner_euid'] == 0, 'full_admission_failed')
            log = (root / f'shard{shard}.log').open('x')
            logs.append(log)
            child = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_rich_hot_node2_run', 'run', '--root', str(root), '--shard', str(shard)],
                cwd=root / 'source', start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.UUIDS[shard],
                    PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                    MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'), stdout=log, stderr=subprocess.STDOUT)
            identity = process_identity(Path('/proc') / str(child.pid))
            children[shard] = (child, identity)
            write(root / f'LAUNCH_{shard}.json', dict(identity=identity, uuid=policy.UUIDS[shard], started_unix=time.time()))
        while any(child.poll() is None for child, identity in children.values()):
            policy.require(time.time() < lifetime['hard_deadline_unix'] - 240, '16hour_hard_guard')
            time.sleep(5)
        status = 'COMPLETE' if all(child.returncode == 0 for child, identity in children.values()) else 'NATIVE_FAILURE'
    except BaseException as error:
        write(root / 'GUARD_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        for child, identity in children.values():
            stop_owned(child, identity)
        for log in logs:
            log.close()
        releases = {}
        for shard in range(8):
            try:
                report = scan(shard, root / 'SERVICE_IDENTITY.json', timeout_seconds=20)
                write(root / f'RELEASE_{shard}.json', report)
                releases[str(shard)] = report['clear']
            except Exception as error:
                releases[str(shard)] = False
                write(root / f'RELEASE_{shard}.json', dict(clear=False, error=str(error)))
        write(root / 'TERMINAL.json', dict(status=status, finished_unix=time.time(), releases=releases,
            assigned_gpu_hours=8 * (time.time() - started) / 3600, lifetime=lifetime))
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run', 'launch'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--shard', type=int, choices=range(8))
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    elif options.phase == 'run':
        run(options.root, options.shard)
    else:
        launch(options.root)
