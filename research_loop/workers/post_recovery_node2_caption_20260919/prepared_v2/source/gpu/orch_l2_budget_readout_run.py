"""Four fresh read-only states, fixed 320 calls, one global 60-minute lifetime."""

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

from gpu import astra_goal_quality_train as old
from gpu import astra_portable_actor_bundle as portable
from gpu import orch_guided_native as native
from gpu.orch_l2_budget_readout_scan import HOST, identity as process_identity, scan
from gpu.orch_l2_rich_math_bootstrap import BUNDLE_SHA, read, sha, write
from gpu.orch_math_rich_source import verify_archive
from gpu.orch_rich_twopass_run import Engine
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_l2_budget_readout as policy


ROOT = Path('/localhome/local-rohing/orch_l2_budget_readout_20260915_attempt1')
PILOT = Path('/localhome/local-rohing/orch_l2_rich_math_20260915_attempt1')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
LEASE_END = datetime(2026, 9, 21, 8, 43, tzinfo=timezone.utc).timestamp()
RECEIPTS = dict(GUIDED_SLEEP='GUIDED_SLEEP/cycle3/sleep/COMPLETE.json',
    GUIDED_FROZEN='FULL/COMPLETE.json', UNPARENTED_SLEEP='UNPARENTED_SLEEP/cycle3/sleep/COMPLETE.json',
    BOOTSTRAP_OFF='OFF/COMPLETE.json')


def call_plan(cohort, legacy):
    calls = []
    for task, budgets in zip(cohort['tasks'], cohort['budget_order']):
        for budget in budgets:
            calls.append(dict(kind='math', task_id=task['id'], max_new_tokens=budget,
                              messages=[dict(role='user', content=task['question'])]))
    policy.require(len(legacy['old_bank']) == len(legacy['old_episodes']) == 16, 'full_legacy_memory_required')
    for view in (0, 8):
        for fact in legacy['old_bank']:
            calls.append(dict(kind='retention', view=view, event=fact['event'], max_new_tokens=512,
                              messages=old.memory.memory_messages(fact['event'], view)))
    policy.require(len(legacy['held']['cases']) == 16, 'full_legacy_audit_required')
    for case in legacy['held']['cases']:
        calls.append(dict(kind='audit', case_sha256=case['case_sha256'], max_new_tokens=512,
                          messages=old.memory.audit._messages(case, coached=False)))
    policy.require(len(calls) == policy.CALLS_PER_ARM, 'exact_80_calls_required')
    return [dict(position=position, **row) for position, row in enumerate(calls)]


def validate_inputs(root):
    policy.require(root == ROOT and socket.gethostname() == HOST and not root.is_symlink(), 'native_root_binding')
    prepared = read(root / 'PREPARE.json')
    policy.require(sha(root / 'source.tar') == prepared['source_sha256'], 'source_archive_changed')
    policy.require(verify_archive(root / 'source.tar', root / 'source') == prepared['source_files'], 'source_file_count_changed')
    policy.require(all(sha(root / name) == digest for name, digest in prepared['files'].items()), 'frozen_input_changed')
    policy.require(all(sha(Path(name)) == digest for name, digest in prepared['pilot_files'].items()), 'original_evidence_changed')
    return prepared


def prepare(root):
    from safetensors.torch import load_file

    policy.require(root == ROOT and socket.gethostname() == HOST and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_node2_prepare_only')
    policy.require(not (root / 'PREPARE.json').exists(), 'prepare_once_only')
    cohort, legacy = read(root / 'COHORT.json'), read(root / 'LEGACY_READOUT.json')
    policy.require(cohort == policy.cohort(read(PILOT / 'COHORT.json')), 'new_cohort_changed')
    policy.require(legacy == read(PILOT / 'LEGACY_READOUT.json'), 'legacy_readout_changed')
    order = call_plan(cohort, legacy)
    policy.require(order == read(root / 'ORDER.json'), 'frozen_call_order_changed')
    prior = read(PILOT / 'LANE_PREPARE.json')
    bundle = '/tmp/astra_portable_37ec_20260914_attempt1'
    base = portable.verify_base_files(bundle, prior['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
    identities, original_identities, pilot_files = {}, {}, {}
    for arm, relative in RECEIPTS.items():
        receipt_path = PILOT / relative
        receipt = read(receipt_path)
        policy.require(receipt['status'] == 'COMPLETE', 'incomplete_input_checkpoint')
        original = bridge.AdapterIdentity.from_document(receipt['output_adapter'])
        policy.require(original.state_sha256 == policy.STATES[arm] and original.base_sha256 == policy.BASE_SHA, 'checkpoint_state_mismatch')
        document = dict(original.document(), path=str(root / 'inputs' / arm / 'adapter'))
        copied = bridge.AdapterIdentity.from_document(document)
        parameters = load_file(str(Path(copied.path) / 'adapter_model.safetensors'), device='cpu')
        mounted = {name.replace('.lora_A.', '.lora_A.default.').replace('.lora_B.', '.lora_B.default.'): tensor
                   for name, tensor in parameters.items()}
        policy.require(native.state_hash(mounted) == copied.state_sha256, 'saved_tensor_identity_mismatch')
        identities[arm], original_identities[arm] = document, original.document()
        pilot_files[str(receipt_path)] = sha(receipt_path)
        for name, digest in original.files:
            pilot_files[str(Path(original.path) / name)] = digest
    tokenizer = native.source.native.load_local_tokenizer(prior['model_dir'])
    token_counts = [len(tokenizer.apply_chat_template(row['messages'], tokenize=True, add_generation_prompt=True,
        return_dict=False)) for row in order]
    policy.require(all(0 < count + row['max_new_tokens'] <= policy.CONTEXT for count, row in zip(token_counts, order)), 'context_envelope_exceeded')
    files = ['COHORT.json', 'ORDER.json', 'LEGACY_READOUT.json', 'PROTOCOL.md', 'SERVICE_IDENTITY.json']
    files += [str(path.relative_to(root)) for path in sorted((root / 'inputs').rglob('*')) if path.is_file()]
    for name in ('COHORT.json', 'LEGACY_READOUT.json', 'LANE_PREPARE.json', 'PILOT_TERMINAL.json'):
        pilot_files[str(PILOT / name)] = sha(PILOT / name)
    prepared = dict(status='CPU_PREPARED_NO_MODEL', prepared_unix=time.time(), model_dir=prior['model_dir'],
        bundle=bundle, base_verification=base, identities=identities, original_identities=original_identities,
        source_sha256=sha(root / 'source.tar'), source_files=verify_archive(root / 'source.tar', root / 'source'),
        files={name: sha(root / name) for name in files}, pilot_files=pilot_files,
        prompt_token_counts=token_counts, total_calls=320, math_calls=128, retention_calls=192,
        parent_calls=0, fits=0, checkpoint_tensor_hashes_verified=True)
    write(root / 'PREPARE.json', prepared)
    print(json.dumps(dict(status=prepared['status'], prepare_sha256=sha(root / 'PREPARE.json'),
        source_sha256=prepared['source_sha256'], prompt_tokens_range=[min(token_counts), max(token_counts)])))


def reserve(root, arm, planned, now, deadline):
    policy.require(now < deadline, 'global_deadline_before_dispatch')
    policy.require(arm in policy.ARMS and 0 <= planned['position'] < policy.CALLS_PER_ARM, 'invalid_planned_call')
    marker = root / 'reservations' / f"{arm}_{planned['position']:02d}.json"
    with (root / 'CALLS.jsonl').open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        count = sum(1 for line in stream)
        policy.require(count < policy.MAX_CALLS, 'global_320_call_cap')
        row = dict(planned, arm=arm, global_index=count, reserved_unix=now)
        with marker.open('x') as receipt:
            json.dump(row, receipt, sort_keys=True)
            receipt.flush()
            os.fsync(receipt.fileno())
        stream.seek(0, 2)
        stream.write(json.dumps(row, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    return row


def run(root, arm):
    prepared = validate_inputs(root)
    lifetime = read(root / 'LIFETIME.json')
    uuid = policy.DEVICES[arm][1]
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == uuid, 'exact_uuid_required')
    policy.require(('CUDA_VISIBLE_DEVICES=' + uuid).encode() in Path('/proc/self/environ').read_bytes().split(b'\0'), 'exec_uuid_required')
    output = root / arm
    output.mkdir(exist_ok=False)
    order, cohort, legacy = (read(root / name) for name in ('ORDER.json', 'COHORT.json', 'LEGACY_READOUT.json'))
    loaded, position, status = None, 0, 'FAILED'

    def check(label):
        policy.require(time.time() < lifetime['native_deadline_unix'], 'global_lifetime_expired:' + label)

    def generate(messages, **metadata):
        nonlocal position
        check('generation')
        policy.require(position < len(order), 'extra_call_forbidden')
        planned = order[position]
        policy.require(messages == planned['messages'], 'prompt_or_order_changed')
        tokens = loaded.engine.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
        policy.require(len(tokens) + planned['max_new_tokens'] <= policy.CONTEXT, 'context_overflow_no_cropping')
        row = reserve(root, arm, planned, time.time(), lifetime['native_deadline_unix'])
        position += 1
        try:
            row['response'] = loaded.engine.generate(messages, max_new_tokens=planned['max_new_tokens'])
            if planned['kind'] == 'math':
                task = next(task for task in cohort['tasks'] if task['id'] == planned['task_id'])
                row['score'] = policy.score(task, row['response'])
            return row['response']
        except Exception as error:
            row['error'] = dict(type=type(error).__name__, message=str(error))
            raise
        finally:
            row['finished_unix'] = time.time()
            write(output / f"CALL_{planned['position']:02d}.json", row)

    try:
        check('load')
        portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
        identity = bridge.AdapterIdentity.from_document(prepared['identities'][arm])
        binding = bridge.StageBinding(root.name, bridge.ARMS[1], 0, 'sealed_readout', identity,
                                      False, True, sha(root / 'PREPARE.json'))
        loaded = native.load_stage(binding, model_dir=prepared['model_dir'], device='cuda:0', gpu_uuid=uuid,
                                   context=native.StageContext(), check=check, engine_factory=Engine)
        write(output / 'LOADED.json', dict(observed=loaded.observed.document(), process=loaded.process,
                                          uuid=uuid, physical_index=policy.DEVICES[arm][0]))
        for planned in order[:32]:
            generate(planned['messages'])
        events = [dict(event=fact['event'], raw=episode['event']['raw'])
                  for fact, episode in zip(legacy['old_bank'], legacy['old_episodes'])]
        retention = old.memory.recall(events, generate, output, 'OLD')
        audit = old.memory.audit.collect_cases(legacy['held'], generate, coached=False)
        write(output / 'LEGACY_AUDIT.json', audit)
        policy.require(position == policy.CALLS_PER_ARM and audit['model_calls'] == 16, 'all_80_calls_required')
        write(output / 'RETENTION.json', dict(memory=retention, audit=audit['summary'], calls=48, max_new_tokens=512))
        status = 'COMPLETE'
    except BaseException as error:
        write(output / 'FAILED.json', dict(type=type(error).__name__, message=str(error), finished_unix=time.time()))
        raise
    finally:
        if loaded is not None:
            try:
                observed = loaded.verify_unchanged()
                portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=BUNDLE_SHA)
                validate_inputs(root)
                write(output / 'AFTER.json', dict(observed=observed.document(), process=loaded.process,
                                                unchanged=True, finished_unix=time.time()))
            except BaseException as error:
                status = 'IDENTITY_VERIFICATION_FAILED'
                write(output / 'AFTER_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        write(output / 'TERMINAL.json', dict(status=status, reserved_calls=position, finished_unix=time.time(),
                                            math_denominator_per_budget=16, retention_calls_expected=48, fits=0, parent_calls=0))
    policy.require(status == 'COMPLETE', 'state_not_complete')


def stop_owned(child, identity):
    if child.poll() is not None:
        return
    policy.require(process_identity(Path('/proc') / str(child.pid)) == identity and identity['uid'] == os.getuid(), 'stop_identity_mismatch')
    child.send_signal(signal.SIGTERM)
    try:
        child.wait(timeout=8)
    except subprocess.TimeoutExpired:
        policy.require(process_identity(Path('/proc') / str(child.pid)) == identity, 'kill_identity_mismatch')
        child.send_signal(signal.SIGKILL)
        child.wait(timeout=5)


def reduce(root):
    records = [read(path) for arm in policy.ARMS for path in sorted((root / arm).glob('CALL_*.json'))]
    return dict(records=len(records), math_records=sum(row['kind'] == 'math' for row in records),
        retention_records=sum(row['kind'] != 'math' for row in records), comparisons=policy.summarize(records),
        errors=sum('error' in row for row in records), fits=0, parent_calls=0)


def launch(root):
    validate_inputs(root)
    ready = read(root / 'READY.json')
    policy.require(ready['prepare_sha256'] == sha(root / 'PREPARE.json') and ready['cpu_tests_passed'], 'readiness_mismatch')
    policy.require(ready['cpu_test_log_sha256'] == sha(root / 'CPU_TESTS.log'), 'cpu_test_log_mismatch')
    policy.require(ready['builder_receipt_sha256'] == sha(root / 'BUILDER_RECEIPT.md'), 'builder_log_receipt_binding_required')
    started = time.time()
    policy.require(started + policy.SECONDS < LEASE_END - 21600, 'lease_margin_violation')
    lifetime = dict(started_unix=started, hard_deadline_unix=started + policy.SECONDS,
        native_deadline_unix=started + policy.SECONDS - 180, max_calls=320, assigned_gpu_hours_ceiling=4,
        builder_receipt_sha256=ready['builder_receipt_sha256'], ready_sha256=sha(root / 'READY.json'))
    with (root / 'LIFETIME.json').open('x') as stream:
        json.dump(lifetime, stream, indent=2)
    (root / 'reservations').mkdir(exist_ok=False)
    children, logs, status = {}, [], 'FAILED'

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for arm, (index, uuid) in policy.DEVICES.items():
            admission = scan(index, root / 'SERVICE_IDENTITY.json')
            write(root / f'ADMISSION_{arm}.json', admission)
            policy.require(admission['clear'] and admission['scanner_euid'] == 0, 'full_proc_admission_failed:' + arm)
            log = (root / f'{arm}.log').open('x')
            logs.append(log)
            child = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_l2_budget_readout_run', 'run', '--root', str(root), '--arm', arm],
                cwd=root / 'source', start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=uuid,
                    PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                    MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'),
                stdout=log, stderr=subprocess.STDOUT)
            identity = process_identity(Path('/proc') / str(child.pid))
            children[arm] = (child, identity)
            write(root / f'LAUNCH_{arm}.json', dict(identity=identity, uuid=uuid, started_unix=time.time()))
        while any(child.poll() is None for child, identity in children.values()):
            policy.require(time.time() < lifetime['hard_deadline_unix'] - 120, 'global_60minute_guardian')
            time.sleep(2)
        status = 'COMPLETE' if all(child.returncode == 0 for child, identity in children.values()) else 'NATIVE_FAILURE'
    except BaseException as error:
        write(root / 'GUARD_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        for child, identity in children.values():
            stop_owned(child, identity)
        for log in logs:
            log.close()
        write(root / 'SUMMARY.json', reduce(root))
        releases = {}
        for arm, (index, uuid) in policy.DEVICES.items():
            try:
                remaining = lifetime['hard_deadline_unix'] - time.time() - 2
                policy.require(remaining > 1, 'release_budget_expired')
                report = scan(index, root / 'SERVICE_IDENTITY.json', timeout_seconds=min(20, remaining / (4 - len(releases))))
                write(root / f'RELEASE_{arm}.json', report)
                releases[arm] = report['clear']
            except Exception as error:
                releases[arm] = False
                write(root / f'RELEASE_{arm}.json', dict(clear=False, error=str(error)))
        write(root / 'TERMINAL.json', dict(status=status, finished_unix=time.time(), releases=releases,
            assigned_gpu_hours=4 * (time.time() - started) / 3600, lifetime=lifetime))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run', 'launch', 'reduce'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--arm', choices=policy.ARMS)
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    elif options.phase == 'run':
        run(options.root, options.arm)
    elif options.phase == 'launch':
        launch(options.root)
    else:
        print(json.dumps(reduce(options.root), indent=2))
