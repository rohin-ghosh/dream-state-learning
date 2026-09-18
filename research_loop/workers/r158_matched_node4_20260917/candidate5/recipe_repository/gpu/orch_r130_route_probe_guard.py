"""Bounded fresh-process R130 supervision on the released node5 slot."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import orch_r130_route_evidence_probe as probe


UUID = 'GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b'


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def validate_scope(plan):
    probe.require(plan['gpu_uuid'] == UUID and plan['physical'] == 7
        and plan['wrapper'] == 'ovx3', 'only_released_node5_slot7')
    probe.require(plan['hard_end_unix'] < plan['next_reserved_unix'] - 600,
        'release_before_existing_timer')
    probe.require(plan['hard_end_unix'] - plan['created_unix'] <= 3600,
        'bounded_diagnostic_duration')
    probe.require(plan['max_native_calls'] == probe.TOTAL_CALLS, 'fixed_96_call_limit')


def scan(plan_path):
    plan, _, _ = probe.validate_plan(plan_path)
    validate_scope(plan)
    probe.require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
        'privileged_cpu_scan')
    from gpu import orch_rich_hot_a100_minor_scan as minor
    from gpu import orch_r111_route_admission as admission

    def allocation(index):
        probe.require(index == 7, 'exact_owned_index')

    minor.pinned.policy = SimpleNamespace(HOST_SHA=plan['host_sha256'],
        DEVICES={7: UUID}, require=probe.require, allocation=allocation)
    service = Path(plan['output']) / 'SERVICE_IDENTITY.json'
    if not service.exists():
        minor.pinned.service(service)
    return admission.scan(7, service)


def supervise(plan_path):
    plan, _, _ = probe.validate_plan(plan_path)
    validate_scope(plan)
    output = Path(plan['output'])
    output.mkdir(parents=True, exist_ok=True)
    (output / 'DISPATCH_ONCE').mkdir()
    publication = probe.read(output / 'PUBLICATION.json')
    probe.require(publication['plan_sha256'] == probe.sha(plan_path)
        and publication['allocation_sha256'] == probe.sha(output / 'ALLOCATION.md')
        and publication['dated_builder_publication'] is True, 'published_before_gpu')
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=plan['source_root'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
    completed = []
    try:
        for condition in probe.CONDITIONS:
            scan_command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
                'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + plan['source_root'],
                sys.executable, '-B', str(Path(__file__).resolve()),
                'scan', '--plan', str(plan_path)]
            report = json.loads(subprocess.check_output(scan_command, text=True, timeout=100))
            write(output / (condition + '_ADMISSION.json'), report)
            probe.require(report['clear'] and report['scanner_euid'] == 0
                and not report['blocking_reasons'], 'fresh_exclusive_admission')
            remaining = int(plan['hard_end_unix'] - time.time() - 10)
            probe.require(remaining > 10, 'remaining_native_wall')
            command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's',
                sys.executable, '-B', '-m', 'gpu.orch_r130_route_evidence_probe', 'stage',
                '--plan', str(plan_path), '--condition', condition]
            with (output / (condition + '.log')).open('x') as log:
                process = subprocess.Popen(command, cwd=plan['source_root'],
                    env=dict(environment, CUDA_VISIBLE_DEVICES=UUID), stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                write(output / (condition + '_LAUNCH.json'), dict(pid=process.pid,
                    command_sha256=hashlib.sha256(json.dumps(command).encode()).hexdigest(),
                    started_unix=time.time(), hard_end_unix=plan['hard_end_unix']))
                exit_code = process.wait()
            write(output / (condition + '_EXIT.json'), dict(exit_code=exit_code,
                finished_unix=time.time(), no_retry=True))
            probe.require(exit_code == 0 and (output / condition / 'COMPLETE.json').exists(),
                'condition_must_complete_no_retry')
            completed.append(condition)
        write(output / 'SUPERVISOR_COMPLETE.json', dict(status='COMPLETE',
            conditions=completed, finished_unix=time.time(), optimizer_steps=0, parent_calls=0))
    except BaseException as error:
        write(output / 'SUPERVISOR_FAILED.json', dict(status='FAILED',
            conditions_completed=completed, error_type=type(error).__name__,
            error=str(error), finished_unix=time.time(), no_retry=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('scan', 'supervise'))
    parser.add_argument('--plan', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.action == 'scan':
        print(json.dumps(scan(arguments.plan), sort_keys=True))
    else:
        supervise(arguments.plan)
