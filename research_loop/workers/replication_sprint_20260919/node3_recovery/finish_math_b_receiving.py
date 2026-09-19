"""Explicit CPU harness repair; retain failed logs and the unchanged staged runtime."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone


CONTROL = Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork/control_ws6_pending_math_b_20260919T142337Z')


def main():
    require = lambda condition, reason: condition or (_ for _ in ()).throw(ValueError(reason))
    require(os.uname().nodename == 'ipp2-ovx-p6-09' and os.getuid() == 2524
        and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'original_node_CPU_only')
    def checksum(path):
        value = hashlib.sha256()
        with Path(path).open('rb') as stream:
            while block := stream.read(4 * 1024 * 1024):
                value.update(block)
        return value.hexdigest()
    def write(path, value):
        with path.open('x') as output:
            json.dump(value, output, sort_keys=True, indent=2)
            output.flush()
            os.fsync(output.fileno())
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    def pin(path):
        return dict(path=str(path), sha256=checksum(path))
    old_failure = json.loads((CONTROL / 'STAGING_FAILED.json').read_bytes())
    require(old_failure['error'] == 'receiving_CPU_tests_failed_preserve_staging'
        and old_failure['native_or_GPU_launch_performed'] is False, 'only_explicit_receiving_harness_repair')
    original_guard = json.loads((CONTROL / 'ORIGINAL_GUARD.json').read_bytes())
    plan = json.loads((CONTROL / 'PLAN.json').read_bytes())
    source = Path(plan['source_root'])
    source_pins = {str(path.relative_to(source)): checksum(path) for path in source.rglob('*.py')}
    require(all(source_pins[name] == value for name,value in original_guard['source_pins'].items()),
        'unchanged_original_runtime_sources')
    require(len(source_pins) == 204, 'exact_198_original_plus_six_added_sources')
    sys.path.insert(0, str(source))
    import math_b_startup as startup
    from pending_sleep_contract import digest
    manifest = json.loads((CONTROL / 'STARTUP_MANIFEST.json').read_bytes())
    startup.validate_manifest(manifest, (CONTROL / 'PLAN.json').read_bytes())
    before = json.loads((CONTROL / 'STAGING_STARTED.json').read_bytes())
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(CONTROL / 'test_support') + ':' + str(source),
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(CONTROL / 'receiving_tests'),
        '-p', 'test_*.py', '-v']
    write(CONTROL / 'CPU_HARNESS_REPAIR.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        reason='python -m puts cwd ahead of PYTHONPATH; staged research_loop shadowed isolated test_support',
        prior_failure=pin(CONTROL / 'STAGING_FAILED.json'), prior_log=pin(CONTROL / 'RECEIVING_CPU.log'),
        old_cwd=str(source), corrected_cwd=str(CONTROL / 'test_support'),
        runtime_source_unchanged=True, source_pins_sha256=digest(source_pins), native_retry=False))
    log_path = CONTROL / 'RECEIVING_CPU_IMPORT_FIX.log'
    with log_path.open('xb') as log:
        result = subprocess.run(command, cwd=CONTROL / 'test_support', env=environment,
            stdout=log, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'corrected_CPU_harness_failed_preserve_evidence')
    require(source_pins == {str(path.relative_to(source)): checksum(path) for path in source.rglob('*.py')},
        'source_unchanged_after_receiving_CPU')
    raw = Path(original_guard['copy_raw'])
    head = json.loads((raw / 'stream/records' / f'{9555:020d}.json').read_bytes())
    require(head['sha256'] == '808f1e4b7fbca0f50c62eaffbdcd04fbdd601477250168d25a1d11aecba97785',
        'original_journal_head_unchanged')
    checkpoint_cpu = json.loads((CONTROL / 'ACTUAL_CHECKPOINT_CPU.json').read_bytes())
    require(checkpoint_cpu['optimizer_steps'] == 9740 and checkpoint_cpu['CUDA_initialized'] is False,
        'actual_saved_checkpoint_CPU_proof')
    additions = sorted(set(source_pins) - set(original_guard['source_pins']))
    cpu = dict(passed=True, utc=datetime.now(timezone.utc).isoformat(), interpreter=sys.executable,
        command=command, cwd=str(CONTROL / 'test_support'), log_sha256=checksum(log_path),
        source_pins=source_pins, source_pins_sha256=digest(source_pins),
        original_source_count=len(original_guard['source_pins']), added_source_files=additions,
        plan_sha256=checksum(CONTROL / 'PLAN.json'), startup_manifest=pin(CONTROL / 'STARTUP_MANIFEST.json'),
        checkpoint_cpu=pin(CONTROL / 'ACTUAL_CHECKPOINT_CPU.json'),
        harness_repair=pin(CONTROL / 'CPU_HARNESS_REPAIR.json'),
        original_state_or_journal_written=False, native_or_GPU_launch_performed=False,
        fresh_privileged_admission=False, main_published_scoped_builder_receipt_pending=True,
        initial_owner_available_bytes=before['actual_owner_available_bytes'],
        current_owner_available_bytes=os.statvfs(raw).f_bavail * os.statvfs(raw).f_frsize)
    write(CONTROL / 'RECEIVING_CPU.json', cpu)
    allocation = dict(builder_entry_logged=False, cpu_tests_passed=True, declared_unix=time.time(),
        plan_sha256=cpu['plan_sha256'], physical=2, gpu_uuid=plan['gpu_uuid'],
        cpu_receipt_path=str(CONTROL / 'RECEIVING_CPU.json'), cpu_receipt_sha256=checksum(CONTROL / 'RECEIVING_CPU.json'))
    write(CONTROL / 'ALLOCATION_CANDIDATE.json', allocation)
    guard = dict(original_guard, attempt_dir=str(CONTROL), plan_path=str(CONTROL / 'PLAN.json'),
        plan_sha256=cpu['plan_sha256'], source_pins=source_pins,
        allocation_path=str(CONTROL / 'ALLOCATION_CANDIDATE.json'),
        allocation_sha256=checksum(CONTROL / 'ALLOCATION_CANDIDATE.json'),
        pending_sleep_recovery=pin(CONTROL / 'STARTUP_MANIFEST.json'))
    write(CONTROL / 'GUARD_CANDIDATE.json', guard)
    candidate = json.loads((CONTROL / 'PENDING_SLEEP_CANDIDATE.json').read_bytes())
    receipt = dict(status='SOURCE_STAGED_RECEIVING_CPU_PASS_AFTER_EXPLICIT_HARNESS_FIX_NO_LAUNCH',
        utc=datetime.now(timezone.utc).isoformat(), source=str(source), control=str(CONTROL),
        source_pins=source_pins, source_pins_sha256=digest(source_pins),
        original_source_count=len(original_guard['source_pins']), added_source_files=additions,
        plan=pin(CONTROL / 'PLAN.json'), startup_manifest=pin(CONTROL / 'STARTUP_MANIFEST.json'),
        candidate_guard=pin(CONTROL / 'GUARD_CANDIDATE.json'), receiving_cpu=pin(CONTROL / 'RECEIVING_CPU.json'),
        candidate_sha256=candidate['sha256'], checkpoint_cpu=checkpoint_cpu,
        original_complete_sha256=manifest['selection']['complete_sha256'], original_head_sha256=head['sha256'],
        CPU_log_tail=log_path.read_text()[-1400:],
        admission_blocker='original guard requires source-bound Builder/allocation; candidate remains false',
        native_or_GPU_launch_performed=False, protected_parent_prerequisite_unchanged=True,
        owner_available_bytes=os.statvfs(raw).f_bavail * os.statvfs(raw).f_frsize)
    write(CONTROL / 'STAGED_READY_FOR_MAIN.json', receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
