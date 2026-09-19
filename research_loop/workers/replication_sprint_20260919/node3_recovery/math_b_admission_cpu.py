"""Bind the exact published Builder entry and run original CPU-only admission checks."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


CONTROL = Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork/control_ws6_pending_math_b_20260919T142337Z')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def main(publication):
    require(os.uname().nodename == 'ipp2-ovx-p6-09' and os.getuid() == os.getgid() == 2524,
        'original_node_and_owner')
    require(publication['git_commit'] == '4813989c2e26fb3f3bfd72f0db4f6857187b6ed8'
        and publication['entry'].startswith('[Builder] 2026-09-19T14:31Z'), 'exact_authorized_publication')
    require(hashlib.sha256(publication['entry'].encode()).hexdigest() == publication['entry_sha256'],
        'published_entry_exact_bytes')

    def pin(path):
        return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def write(name, document):
        path = CONTROL / name
        with path.open('x') as output:
            json.dump(document, output, sort_keys=True, indent=2)
            output.flush()
            os.fsync(output.fileno())
        descriptor = os.open(CONTROL, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return pin(path)

    started = dict(utc=datetime.now(timezone.utc).isoformat(), pid=os.getpid(),
        native_launch_performed=False, known_native_startup_blocker='authorized128MiB_tail_limit_too_small',
        action='original_confinement_probe_and_privileged_scan_only_no_dispatch')
    write('BUILDER1431_CPU_ADMISSION_STARTED.json', started)
    try:
        compute = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,process_name',
            '--format=csv,noheader'], capture_output=True, text=True, check=True, timeout=20)
        require(not compute.stdout.strip(), 'compute_present_stop_no_healthy_native_signal')
        process_facts = []
        for process in Path('/proc').iterdir():
            if not process.name.isdigit() or int(process.name) in (os.getpid(), os.getppid()):
                continue
            try:
                if process.stat().st_uid != os.getuid():
                    continue
                arguments = (process / 'cmdline').read_bytes().decode(errors='replace').split('\0')
                if any(argument in ('native', 'child', 'dispatch') for argument in arguments):
                    process_facts.append(dict(pid=int(process.name),
                        start_ticks=(process / 'stat').read_text().rsplit(')', 1)[1].split()[19],
                        argv=arguments))
            except FileNotFoundError:
                pass
        require(not process_facts, 'native_wrapper_present_stop_without_signalling')
        plan = json.loads((CONTROL / 'PLAN.json').read_bytes())
        source = Path(plan['source_root'])
        require(plan['hard_end_unix'] == 1790272800 and time.time() < plan['hard_end_unix']
            and plan['physical'] == 2 and plan['gpu_uuid'] == 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1',
            'same_original_GPU_and_remaining_wall')
        candidate = json.loads((CONTROL / 'GUARD_CANDIDATE.json').read_bytes())
        allocation = json.loads((CONTROL / 'ALLOCATION_CANDIDATE.json').read_bytes())
        for bound in (candidate['plan_sha256'], candidate['pending_sleep_recovery']['sha256'],
                allocation['cpu_receipt_sha256']):
            require(bound in publication['entry'], 'published_binding_missing')
        sys.path.insert(0, str(source))
        from pending_sleep_contract import digest
        require(digest(candidate['source_pins']) in publication['entry'], 'published_source_closure')
        publication_pin = write('BUILDER1431_PUBLICATION.json', publication)
        allocation.update(builder_entry_logged=True, builder_publication=publication_pin)
        allocation_pin = write('ALLOCATION_BUILDER1431.json', allocation)
        final_guard = dict(candidate, allocation_path=allocation_pin['path'],
            allocation_sha256=allocation_pin['sha256'])
        guard_pin = write('GUARD_BUILDER1431.json', final_guard)
        from gpu import orch_r125_continual_guard as guard
        from gpu import r205_runtime as runtime
        from gpu.r226_math_runtime import bounded_runtime
        validated_guard, validated_plan = guard.validate(Path(guard_pin['path']))
        require(validated_guard == final_guard and validated_plan == plan, 'original_guard_validation')
        runtime.MODULE = 'gpu.ws6_math_b_pending_entry'
        command = bounded_runtime(runtime.contained_command(Path(guard_pin['path']), 'probe'),
            plan['hard_end_unix'], time.time())
        require('probe' in command and 'dispatch' not in command and 'native' not in command,
            'probe_only_no_native_command')
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
            PYTHONPATH=str(source), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        with (CONTROL / 'BUILDER1431_PROBE.log').open('xb') as output:
            probe = subprocess.run(command, cwd=source, env=environment, stdout=output,
                stderr=subprocess.STDOUT, timeout=110)
        require(probe.returncode == 0, 'actual_original_confinement_probe_failed')
        proof = json.loads((CONTROL / 'CONFINEMENT_CPU.json').read_bytes())
        require(proof['model_calls'] == 0 and proof['physical'] == 2
            and sorted(proof['denied_foreign_minors']) == [0, 1, 3, 4, 5, 6, 7], 'actual_strict_GPU2_confinement')
        scan_command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + str(source), sys.executable, '-B', '-m', 'gpu.ws6_math_b_pending_entry',
            'scan', '--config', guard_pin['path']]
        with (CONTROL / 'BUILDER1431_SCAN.stderr').open('xb') as errors:
            scan = subprocess.run(scan_command, cwd=source, env=environment, capture_output=False,
                stdout=subprocess.PIPE, stderr=errors, timeout=110)
        with (CONTROL / 'BUILDER1431_SCAN.stdout').open('xb') as output:
            output.write(scan.stdout)
            output.flush()
            os.fsync(output.fileno())
        require(scan.returncode == 0, 'original_privileged_scan_failed')
        report = json.loads(scan.stdout)
        report_pin = write('BUILDER1431_ADMISSION_REPORT.json', report)
        require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons'],
            'original_privileged_admission_not_clear')
        receipt = dict(utc=datetime.now(timezone.utc).isoformat(),
            status='EXACT_BUILDER1431_ORIGINAL_CPU_CONFINEMENT_AND_PRIVILEGED_SCAN_PASS_NO_NATIVE',
            guard=guard_pin, allocation=allocation_pin, publication=publication_pin,
            confinement_cpu=pin(CONTROL / 'CONFINEMENT_CPU.json'), admission_report=report_pin,
            model_calls=0, native_launch_performed=False,
            known_native_startup_blocker='authorized128MiB_manifest_needs_exact512MiB_amendment',
            fresh_scan_required_again_before_actual_launch=True,
            owner_available_bytes=os.statvfs(CONTROL).f_bavail * os.statvfs(CONTROL).f_frsize)
        write('BUILDER1431_CPU_ADMISSION_VERIFIED.json', receipt)
        print(json.dumps(receipt, sort_keys=True), flush=True)
    except BaseException as error:
        receipt = dict(utc=datetime.now(timezone.utc).isoformat(), status='CPU_ADMISSION_FAILED_NO_BYPASS',
            error_type=type(error).__name__, error=str(error), native_launch_performed=False,
            automatic_retry=False, original_failures_preserved=True)
        write('BUILDER1431_CPU_ADMISSION_FAILED.json', receipt)
        print(json.dumps(receipt, sort_keys=True), flush=True)
        raise
