"""Queue mixed supply after exact original terminals; inherit the original clock."""

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
from gpu import orch_rich_hot_node2_export as exporter
from gpu.orch_l2_budget_readout_run import LEASE_END, PYTHON, stop_owned
from gpu.orch_l2_budget_readout_scan import HOST, identity as process_identity
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA, read, sha
from gpu.orch_math_rich_source import verify_archive
from gpu.orch_rich_hot_node2_run import Engine, ROOT as ORIGINAL
from gpu.orch_rich_hot_node2_scan import scan
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_rich_hot_node2 as hot
from organism_v6 import orch_rich_hot_node2_supply as policy


ROOT = Path('/localhome/local-rohing/orch_rich_hot_node2_continue_20260915_attempt1')


class BudgetEnd(BaseException):
    pass


def write(path, value):
    exporter.durable(path, exporter.wire(value))


def original_terminal(original):
    if not (original / 'TERMINAL.json').exists():
        return False
    terminal = read(original / 'TERMINAL.json')
    hot.require(terminal['status'] == 'COMPLETE' and set(terminal['releases']) == {str(index) for index in range(8)}
                and all(value is True for value in terminal['releases'].values()), 'original_not_safely_released')
    for shard in range(8):
        launch = read(original / f'LAUNCH_{shard}.json')['identity']
        hot.require(not (Path('/proc') / str(launch['pid'])).exists(), 'original_pid_still_present')
        hot.require(read(original / f'shard{shard}/TERMINAL.json')['status'] == 'COMPLETE', 'original_shard_incomplete')
        hot.require(read(original / f'shard{shard}/AFTER.json')['unchanged'] is True, 'original_state_not_verified')
    for path in (original / 'reservations').glob('*.json'):
        row = read(path)
        capture = original / f"shard{row['shard']}" / f"{row['task_id']}_{row['stage']}.json"
        hot.require(capture.is_file() and read(capture)['index'] == row['index'], 'unresolved_original_reservation')
    return True


def validate(root):
    hot.require(root == ROOT and socket.gethostname() == HOST, 'exact_continuation_host_root')
    prepared = read(root / 'PREPARE.json')
    hot.require(sha(root / 'source.tar') == prepared['source_sha256'], 'continuation_source_archive_drift')
    hot.require(verify_archive(root / 'source.tar', root / 'source') == prepared['source_files'], 'continuation_source_drift')
    hot.require(all(sha(root / name) == digest for name, digest in prepared['files'].items()), 'continuation_input_drift')
    hot.require(sha(ORIGINAL / 'LIFETIME.json') == prepared['original_lifetime_sha256'], 'original_clock_changed')
    hot.require(sha(ORIGINAL / 'PREPARE.json') == prepared['original_prepare_sha256'], 'original_prepare_changed')
    return prepared


def prepare(root):
    hot.require(root == ROOT and socket.gethostname() == HOST and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'native_cpu_only')
    prior = read(ORIGINAL / 'PREPARE.json')
    hot.require(sha(ORIGINAL / 'source.tar') == prior['source_sha256'], 'original_source_drift')
    verify_archive(ORIGINAL / 'source.tar', ORIGINAL / 'source')
    hot.require(read(root / 'LIFETIME.json') == read(ORIGINAL / 'LIFETIME.json'), 'inherit_clock_exactly')
    hot.require(sha(root / 'gsm8k_train.jsonl') == hot.SOURCE_SHA, 'cached_source_identity')
    records = [json.loads(line) for line in (root / 'gsm8k_train.jsonl').read_text().splitlines()]
    hot.require(read(root / 'TASKS.json') == policy.cohort(records, read(ORIGINAL / 'TASKS.json')), 'prospective_cohort_mismatch')
    portable.verify_base_files(prior['bundle'], prior['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    hot.require(prior['identity']['state_sha256'] == hot.INITIAL_STATE, 'frozen37ec_only')
    from safetensors.torch import load_file
    tensors = load_file(str(Path(prior['identity']['path']) / 'adapter_model.safetensors'), device='cpu')
    mounted = {name.replace('.lora_A.', '.lora_A.default.').replace('.lora_B.', '.lora_B.default.'): value for name, value in tensors.items()}
    hot.require(native.state_hash(mounted) == hot.INITIAL_STATE, 'input_tensor_hash')
    config = read(Path(prior['model_dir']) / 'config.json')
    hot.require(config['max_position_embeddings'] >= hot.CONTEXT, 'native_context_support')
    tokenizer = native.source.native.load_local_tokenizer(prior['model_dir'])
    document = read(root / 'TASKS.json')
    messages = [policy.messages(dict(family=family, payload=task), condition)
                for family, tasks in (('math', document['math']['tasks']), ('code', document['code']))
                for task in tasks for condition in hot.CONDITIONS]
    lengths = [len(tokenizer.apply_chat_template(message, tokenize=True, add_generation_prompt=True, return_dict=False)) for message in messages]
    hot.require(max(lengths) + hot.CAP <= hot.CONTEXT, 'initial_context_fit')
    names = ('TASKS.json', 'INITIAL.json', 'DATA_PROVENANCE.json', 'PROTOCOL.md',
             'LIFETIME.json', 'SERVICE_IDENTITY.json', 'gsm8k_train.jsonl')
    write(root / 'PREPARE.json', dict(identity=prior['identity'], model_dir=prior['model_dir'], bundle=prior['bundle'],
          original_lifetime_sha256=sha(ORIGINAL / 'LIFETIME.json'), original_prepare_sha256=sha(ORIGINAL / 'PREPARE.json'),
          source_sha256=sha(root / 'source.tar'), source_files=verify_archive(root / 'source.tar', root / 'source'),
          files={name: sha(root / name) for name in names}, additional_max_calls=policy.MAX_CALLS,
          original_max_calls=prior['maximum_calls'], max_new_tokens=hot.CAP, context=hot.CONTEXT,
          prompt_range=[min(lengths), max(lengths)], prepared_unix=time.time(), cpu_only=True))


def reserve(root, shard, task, stage, messages, deadline):
    if time.time() >= deadline or (root / 'STOP_AFTER_CALL.json').exists():
        raise BudgetEnd('original_deadline_or_owned_stop')
    with (root / 'CALLS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        markers = list((root / 'reservations').glob('*.json'))
        if len(markers) >= policy.MAX_CALLS or sum(path.name.startswith(str(shard) + '_') for path in markers) >= policy.CALLS_PER_SHARD:
            raise BudgetEnd('fixed_additional_call_cap')
        row = dict(index=len(markers), shard=shard, task_id=task['id'], family=task['family'], stage=stage,
                   messages=messages, max_new_tokens=hot.CAP, context=hot.CONTEXT,
                   condition=hot.CONDITIONS[shard // 2], source_task_id=task['source_task_id'],
                   repeated_train_source=task['repeated_train_source'], reserved_unix=time.time(), trainingAllowed=False)
        write(root / 'reservations' / f'{shard}_{task["id"]}_{stage}.json', row)
        stream.seek(0, 2)
        stream.write(json.dumps({name: value for name, value in row.items() if name != 'messages'}) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    return row


def run(root, shard):
    prepared = validate(root)
    hot.require(os.environ.get('CUDA_VISIBLE_DEVICES') == hot.UUIDS[shard], 'exact_uuid')
    lifetime, document = read(root / 'LIFETIME.json'), read(root / 'TASKS.json')
    output = root / f'shard{shard}'
    output.mkdir(exist_ok=False)
    (output / 'evidence').mkdir()
    condition = hot.CONDITIONS[shard // 2]
    loaded, status, completed = None, 'FAILED', 0

    def check(label):
        if time.time() >= lifetime['native_deadline_unix']:
            raise BudgetEnd('inherited_deadline:' + label)

    try:
        identity = bridge.AdapterIdentity.from_document(prepared['identity'])
        binding = bridge.StageBinding(root.name + f'_{shard}', bridge.ARMS[1], 0, 'sealed_readout',
                                      identity, False, True, sha(root / 'PREPARE.json'))
        loaded = native.load_stage(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=hot.UUIDS[shard],
                                   context=native.StageContext(), check=check, engine_factory=Engine)
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
                                          uuid=hot.UUIDS[shard], condition=condition))
        for batch in range(policy.MAX_BATCHES):
            for position in range(policy.TASKS_PER_BATCH):
                if position % 2 != shard % 2:
                    continue
                task, stage_counts = policy.task_at(document, batch, position), {}

                def generate(stage, messages):
                    nonlocal completed
                    number = stage_counts.get(stage, 0)
                    stage_counts[stage] = number + 1
                    stage = f'{stage}_{number}'
                    row = reserve(root, shard, task, stage, messages, lifetime['native_deadline_unix'])
                    try:
                        response = loaded.engine.generate(messages, max_new_tokens=hot.CAP)
                        row.update(response=response, outcome=policy.outcome(task, response))
                        completed += 1
                        return response
                    except BaseException as error:
                        row['error'] = dict(type=type(error).__name__, message=str(error))
                        raise
                    finally:
                        row['finished_unix'] = time.time()
                        write(output / f'{task["id"]}_{stage}.json', row)

                try:
                    if task['family'] == 'route':
                        evidence = policy.route_task(task, condition, generate)
                    else:
                        previous = generate('draft' if condition in ('TWO_PASS', 'META_EVALUATE') else 'final',
                                            policy.messages(task, condition))
                        if condition in ('TWO_PASS', 'META_EVALUATE'):
                            generate('final', policy.messages(task, condition, previous['raw']))
                        evidence = dict(status='TASK_CALLS_COMPLETE')
                    write(output / 'evidence' / f'{task["id"]}.json', dict(task=task, evidence=evidence))
                except Exception as error:
                    write(output / 'evidence' / f'{task["id"]}.json', dict(task=task, error=dict(type=type(error).__name__, message=str(error))))
            after = loaded.verify_unchanged()
            write(output / 'evidence' / f'BATCH_{batch:03d}_CHECKPOINT.json',
                  dict(batch=batch, observed=after.document(), unchanged=True, completed_calls=completed))
        status = 'FINITE_POOL_COMPLETE'
    except BudgetEnd as error:
        status = 'BOUNDED_STOP'
        write(output / 'BOUND.json', dict(reason=str(error), observed_unix=time.time()))
    except BaseException as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        if loaded is not None:
            try:
                after = loaded.verify_unchanged()
                portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
                write(output / 'AFTER.json', dict(observed=after.document(), unchanged=True))
            except BaseException as error:
                status = 'IDENTITY_FAILED'
                write(output / 'AFTER_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        write(output / 'TERMINAL.json', dict(status=status, completed_calls=completed, finished_unix=time.time(),
                                            fits=0, parent_calls=0, admitted_rows=0))


def watch(root):
    prepared = validate(root)
    ready = read(root / 'READY.json')
    hot.require(ready['cpu_tests_passed'] and ready['prepare_sha256'] == sha(root / 'PREPARE.json')
                and ready['builder_receipt_sha256'] == sha(root / 'BUILDER_RECEIPT.md'), 'bound_builder_gate')
    lifetime = read(root / 'LIFETIME.json')
    hot.require(lifetime['hard_deadline_unix'] < LEASE_END - 21600, 'lease_margin')
    write(root / 'WATCH_IDENTITY.json', dict(identity=process_identity(Path('/proc') / str(os.getpid())),
                                            ready_sha256=sha(root / 'READY.json'), queued_unix=time.time()))
    while not original_terminal(ORIGINAL):
        if time.time() >= lifetime['native_deadline_unix'] - 600 or (root / 'STOP_AFTER_CALL.json').exists():
            write(root / 'QUEUE_TERMINAL.json', dict(status='DEADLINE_OR_STOP_WITHOUT_LAUNCH', observed_unix=time.time()))
            return
        time.sleep(30)
    lock = (ORIGINAL / 'NODE2_ALL8_ADMISSION.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    children, logs = {}, []
    status = 'FAILED'

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        validate(root)
        hot.require(time.time() < lifetime['native_deadline_unix'] - 600, 'no_late_new_load')
        write(root / 'LEASE_CLAIM.json', dict(identity=process_identity(Path('/proc') / str(os.getpid())),
            original_lifetime_sha256=prepared['original_lifetime_sha256'], devices=hot.DEVICES,
            authority='Rohin96 continuous richness; prospective additional65536calls within original16h/128GPUh'))
        (root / 'reservations').mkdir(exist_ok=False)
        for shard in range(8):
            report = scan(shard, root / 'SERVICE_IDENTITY.json')
            write(root / f'ADMISSION_{shard}.json', report)
            hot.require(report['clear'] and report['scanner_euid'] == 0, 'fresh_full_admission_failed')
            log = (root / f'shard{shard}.log').open('x')
            logs.append(log)
            child = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_rich_hot_node2_continue', 'run', '--root', str(root), '--shard', str(shard)],
                cwd=root / 'source', start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=hot.UUIDS[shard],
                    PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'),
                stdout=log, stderr=subprocess.STDOUT)
            identity = process_identity(Path('/proc') / str(child.pid))
            children[shard] = child, identity
            write(root / f'LAUNCH_{shard}.json', dict(identity=identity, uuid=hot.UUIDS[shard], started_unix=time.time()))
        while any(child.poll() is None for child, identity in children.values()):
            if time.time() >= lifetime['hard_deadline_unix'] - 240:
                status = 'INHERITED_HARD_GUARD'
                break
            time.sleep(10)
        else:
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
        write(root / 'TERMINAL.json', dict(status=status, releases=releases, finished_unix=time.time(), lifetime=lifetime))
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'watch', 'run'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--shard', type=int, choices=range(8))
    options = parser.parse_args()
    globals()[options.phase](options.root, options.shard) if options.phase == 'run' else globals()[options.phase](options.root)
