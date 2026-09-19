"""Unique-source staging and CPU-only receiving proof; never dispatch a native."""

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import types


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork')
OLD_CONTROL = ROOT / 'control_r233_recovery_20260918_policy_lease_ceiling'
PLAN_SHA256 = '95f1ae5ac9a725c4389cb009b5a85280575ad5e69c21d8f84d36883c0c436777'
GUARD_SHA256 = '9cb1f895c32954733a46e2acec941b7e6c23c905931958721b141bcc7dcf6282'
COMPLETE_SHA256 = '0ef904c4c9e50c866c11f30e8d20d14ecc76d128d7bc013ca6ee15301272cae2'
HEAD_SHA256 = '808f1e4b7fbca0f50c62eaffbdcd04fbdd601477250168d25a1d11aecba97785'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checksum(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as source:
        while block := source.read(4 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def write_bytes(path, raw):
    with path.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_json(path, value):
    write_bytes(path, json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def pin(path):
    return dict(path=str(path), sha256=checksum(path))


def main():
    payload = json.loads(sys.stdin.readline())
    require(os.uname().nodename == 'ipp2-ovx-p6-09' and os.getuid() == 2524,
        'original_node3_and_owner')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not payload['gpu_launch_authorized'],
        'CPU_staging_only')
    require(checksum(OLD_CONTROL / 'PLAN.json') == PLAN_SHA256
        and checksum(OLD_CONTROL / 'GUARD.json') == GUARD_SHA256, 'unchanged_original_plan_and_guard')
    original_bytes = (OLD_CONTROL / 'PLAN.json').read_bytes()
    original = json.loads(original_bytes)
    guard = json.loads((OLD_CONTROL / 'GUARD.json').read_bytes())
    active = json.loads((ROOT / 'ACTIVE_RUNTIME.json').read_bytes())
    require(active['control'] == str(OLD_CONTROL) and active['source'] == original['source_root'],
        'original_active_binding_unchanged')
    require(original['physical'] == 2 and original['gpu_uuid'] == 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1'
        and time.time() < original['hard_end_unix'] == 1790272800 < original['lease_end_unix'],
        'original_device_wall_and_lease_unexpired')
    require(checksum(guard['lease_path']) == guard['lease_sha256'], 'original_lease_bytes')
    compute = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,process_name',
        '--format=csv,noheader'], check=True, capture_output=True, text=True).stdout
    require(original['gpu_uuid'] not in compute, 'no_healthy_native_on_original_GPU2')
    available = os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize
    source = Path(original['source_root'])
    source_files = [path for path in source.rglob('*') if path.is_file()]
    require(not any(path.is_symlink() for path in source.rglob('*')), 'no_source_copy_redirection')
    source_bytes = sum(path.stat().st_size for path in source_files)
    payload_bytes = sum(len(base64.b64decode(entry['content'])) for entry in payload['files'])
    needed = source_bytes + payload_bytes + 2 * 242700000 + 2 * 1024**3
    require(source_bytes < 100 * 1024**2 and available >= needed, 'measured_staging_checkpoint_and_safety_headroom')
    for relative, expected in guard['source_pins'].items():
        require(checksum(source / relative) == expected, 'original_source_pin_changed:' + relative)
    raw = Path(guard['copy_raw'])
    records = raw / 'stream' / 'records'
    names = sorted(path.name for path in records.iterdir() if re.fullmatch(r'\d{20}\.json', path.name))
    require(len(names) == 9556 and names[-1] == f'{9555:020d}.json', 'unchanged_complete_record_frontier')
    require(not any(path.name.endswith('.partial') for path in records.iterdir()), 'preserve_partial_artifact_do_not_skip')
    require(all((records / name.replace('.json', '.intent.json')).is_file() for name in names),
        'all_original_intents_present')
    complete = json.loads((records / f'{9476:020d}.json').read_bytes())
    pending = json.loads((records / f'{9505:020d}.json').read_bytes())
    suffix = [json.loads((records / f'{index:020d}.json').read_bytes()) for index in range(9506, 9556)]
    require(complete['sha256'] == COMPLETE_SHA256 and suffix[-1]['sha256'] == HEAD_SHA256,
        'same_COMPLETE_and_interrupted_head')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    staged_source = ROOT / ('source_ws6_pending_math_b_' + stamp)
    control = ROOT / ('control_ws6_pending_math_b_' + stamp)
    require(not staged_source.exists() and not control.exists(), 'unique_staging_only')
    control.mkdir()
    write_json(control / 'STAGING_STARTED.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        original_plan_sha256=PLAN_SHA256, original_guard_sha256=GUARD_SHA256,
        source=str(staged_source), control=str(control), measured_source_bytes=source_bytes,
        payload_bytes=payload_bytes, required_owner_headroom_bytes=needed, actual_owner_available_bytes=available,
        checkpoint_budget_bytes=2 * 242700000, safety_bytes=2 * 1024**3,
        compute_apps_before=compute, native_or_GPU_launch_authorized=False))
    print(json.dumps(dict(status='STAGING_STARTED', source=str(staged_source), control=str(control))), flush=True)
    try:
        shutil.copytree(source, staged_source, copy_function=shutil.copy2)
        for entry in payload['files']:
            content = base64.b64decode(entry['content'])
            require(hashlib.sha256(content).hexdigest() == entry['sha256'], 'payload_bytes_changed')
            base = staged_source if entry['surface'] == 'source' else control
            relative = Path(entry['path'])
            require(not relative.is_absolute() and '..' not in relative.parts, 'scoped_staging_path')
            target = base / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            write_bytes(target, content)
        source_pins = {str(path.relative_to(staged_source)): checksum(path)
            for path in staged_source.rglob('*.py')}
        require(all(source_pins[name] == expected for name, expected in guard['source_pins'].items()),
            'every_original_source_pin_preserved')
        additions = sorted(set(source_pins) - set(guard['source_pins']))
        require(set(additions) == {entry['path'] for entry in payload['files'] if entry['surface'] == 'source'},
            'only_six_reviewed_source_additions')
        write_bytes(control / 'ORIGINAL_PLAN.json', original_bytes)
        write_bytes(control / 'ORIGINAL_GUARD.json', (OLD_CONTROL / 'GUARD.json').read_bytes())
        write_bytes(control / 'ORIGINAL_EXIT.json', (OLD_CONTROL / 'EXIT.json').read_bytes())
        execution = dict(original, source_root=str(staged_source))
        write_json(control / 'PLAN.json', execution)
        sys.path.insert(0, str(staged_source))
        import math_b_runtime_candidate as kernel
        import math_b_startup as startup
        candidate = kernel.prepare_candidate(complete, pending, suffix,
            plan_bytes=original_bytes, expected_plan_sha256=PLAN_SHA256)
        write_json(control / 'PENDING_SLEEP_CANDIDATE.json', candidate)
        journal_id = json.loads((raw / 'stream' / 'JOURNAL.json').read_bytes())['journal_id']
        selection = dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=str(Path(original['root']) / 'stream'),
            journal_id=journal_id, complete_index=9476, complete_sha256=COMPLETE_SHA256,
            life_id='R213_NEW_MATH_B', max_tail_records=2048, max_tail_bytes=128 * 1024**2,
            sidecars=[dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)],
            persist_complete_anchors=True)
        manifest = dict(schema=startup.SCHEMA, life='r213_math_b_fork',
            original_plan=pin(control / 'ORIGINAL_PLAN.json'), staged_source_root=str(staged_source),
            execution_plan_sha256=checksum(control / 'PLAN.json'),
            candidate=pin(control / 'PENDING_SLEEP_CANDIDATE.json'), selection=selection)
        write_json(control / 'STARTUP_MANIFEST.json', manifest)
        startup.validate_manifest(manifest, (control / 'PLAN.json').read_bytes())
        checkpoint = complete['document']['checkpoint']
        checkpoint_root = raw / 'checkpoints' / 'sleep_000192'
        require(json.loads((checkpoint_root / 'COMMIT.json').read_bytes()) == checkpoint,
            'actual_committed_checkpoint_matches_original_COMPLETE')
        for name, expected in checkpoint['adapter_files'].items():
            require(checksum(checkpoint_root / 'adapter' / name) == expected, 'actual_adapter_file_hash')
        require(checksum(checkpoint_root / 'optimizer_rng.pt') == checkpoint['checkpoint_sha256']['optimizer']
            == checkpoint['checkpoint_sha256']['rng'], 'actual_optimizer_RNG_file_hash')
        import torch
        require(not torch.cuda.is_initialized(), 'no_GPU_initialization_during_CPU_receiving')
        saved = torch.load(checkpoint_root / 'optimizer_rng.pt', map_location='cpu', weights_only=False)
        require(saved['optimizer_steps'] == 9740 and saved.get('experiment') == checkpoint.get('experiment')
            and len(saved['optimizer']['state']) > 0 and len(saved['parameter_names']) > 0,
            'durable_optimizer_state_really_deserializes')
        require(saved['cpu_rng'].dtype == torch.uint8 and saved['cpu_rng'].numel() > 0
            and len(saved['cuda_rng']) > 0 and all(value.dtype == torch.uint8 and value.numel() > 0
                and value.device.type == 'cpu' for value in saved['cuda_rng'])
            and isinstance(saved['python_rng'], tuple), 'saved_RNG_payload_present_on_CPU')
        tensor_receipt = dict(torch_version=torch.__version__, optimizer_steps=saved['optimizer_steps'],
            optimizer_parameter_states=len(saved['optimizer']['state']), parameter_names=len(saved['parameter_names']),
            cpu_rng_bytes=saved['cpu_rng'].numel(), saved_cuda_rng_count=len(saved['cuda_rng']),
            deserialized_on='CPU', post_generation_or_unsaved_update_RNG_claimed=False,
            model_loaded=False, CUDA_initialized=torch.cuda.is_initialized())
        write_json(control / 'ACTUAL_CHECKPOINT_CPU.json', tensor_receipt)
        del saved
        tests = control / 'receiving_tests'
        for relative in payload['test_source_evidence']:
            target = tests / 'source_evidence' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(staged_source / relative, target)
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
            PYTHONPATH=str(control / 'test_support') + ':' + str(staged_source),
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
        command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(tests), '-p', 'test_*.py', '-v']
        with (control / 'RECEIVING_CPU.log').open('xb') as log:
            result = subprocess.run(command, cwd=control / 'test_support', env=environment, stdout=log,
                stderr=subprocess.STDOUT, timeout=180)
        require(result.returncode == 0, 'receiving_CPU_tests_failed_preserve_staging')
        require(source_pins == {str(path.relative_to(staged_source)): checksum(path)
            for path in staged_source.rglob('*.py')}, 'source_closure_unchanged_after_receiving_tests')
        require(checksum(OLD_CONTROL / 'PLAN.json') == PLAN_SHA256
            and checksum(OLD_CONTROL / 'GUARD.json') == GUARD_SHA256
            and json.loads((records / f'{9555:020d}.json').read_bytes())['sha256'] == HEAD_SHA256,
            'original_plan_guard_and_frontier_unchanged')
        cpu = dict(passed=True, utc=datetime.now(timezone.utc).isoformat(), interpreter=sys.executable,
            command=command, log_sha256=checksum(control / 'RECEIVING_CPU.log'), source_pins=source_pins,
            source_pins_sha256=kernel.digest(source_pins), original_source_count=len(guard['source_pins']),
            added_source_files=additions, plan_sha256=checksum(control / 'PLAN.json'),
            startup_manifest=pin(control / 'STARTUP_MANIFEST.json'), checkpoint_cpu=pin(control / 'ACTUAL_CHECKPOINT_CPU.json'),
            native_or_GPU_launch_performed=False, original_state_or_journal_written=False,
            fresh_privileged_admission=False, main_published_scoped_builder_receipt_pending=True,
            initial_owner_available_bytes=available,
            current_owner_available_bytes=os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize)
        write_json(control / 'RECEIVING_CPU.json', cpu)
        allocation = dict(builder_entry_logged=False, cpu_tests_passed=True, declared_unix=time.time(),
            plan_sha256=cpu['plan_sha256'], physical=2, gpu_uuid=original['gpu_uuid'],
            cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=checksum(control / 'RECEIVING_CPU.json'))
        write_json(control / 'ALLOCATION_CANDIDATE.json', allocation)
        candidate_guard = dict(guard, attempt_dir=str(control), plan_path=str(control / 'PLAN.json'),
            plan_sha256=cpu['plan_sha256'], source_pins=source_pins,
            allocation_path=str(control / 'ALLOCATION_CANDIDATE.json'),
            allocation_sha256=checksum(control / 'ALLOCATION_CANDIDATE.json'),
            pending_sleep_recovery=pin(control / 'STARTUP_MANIFEST.json'))
        write_json(control / 'GUARD_CANDIDATE.json', candidate_guard)
        receipt = dict(status='SOURCE_STAGED_ACTUAL_CHECKPOINT_CPU_AND_RECEIVING_TESTS_PASS_NO_LAUNCH',
            utc=datetime.now(timezone.utc).isoformat(), source=str(staged_source), control=str(control),
            source_pins=source_pins, source_pins_sha256=kernel.digest(source_pins),
            original_source_count=len(guard['source_pins']), added_source_files=additions,
            plan=pin(control / 'PLAN.json'), startup_manifest=pin(control / 'STARTUP_MANIFEST.json'),
            candidate_guard=pin(control / 'GUARD_CANDIDATE.json'), receiving_cpu=pin(control / 'RECEIVING_CPU.json'),
            checkpoint_cpu=tensor_receipt, candidate_sha256=candidate['sha256'],
            original_head_sha256=HEAD_SHA256, original_complete_sha256=COMPLETE_SHA256,
            CPU_log_tail=(control / 'RECEIVING_CPU.log').read_text()[-1200:],
            admission_blocker='original guard requires published source-bound Builder/allocation; candidate remains false',
            native_or_GPU_launch_performed=False, original_owner_available_bytes=available,
            owner_available_bytes=os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize,
            seven_native_parent_prerequisite_unchanged=True)
        write_json(control / 'STAGED_READY_FOR_MAIN.json', receipt)
        print(json.dumps(receipt, sort_keys=True), flush=True)
    except BaseException as error:
        write_json(control / 'STAGING_FAILED.json', dict(error_type=type(error).__name__, error=str(error),
            utc=datetime.now(timezone.utc).isoformat(), no_automatic_retry=True,
            original_state_preserved=True, partial_staging_preserved=True, native_or_GPU_launch_performed=False))
        raise


if __name__ == '__main__':
    main()
