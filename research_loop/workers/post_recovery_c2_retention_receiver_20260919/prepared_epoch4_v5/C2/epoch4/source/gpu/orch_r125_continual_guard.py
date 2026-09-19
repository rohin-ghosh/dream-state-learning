"""One-shot privileged GPU admission for a bound native continuity run."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import orch_r125_continual_native as child
from gpu.orch_r133_code_feedback_guard import await_startup, publish_launch, reap_owned_child


def validate(config_path):
    config = child.read(config_path)
    child.require(config['schema'] == 'R125_CONTINUAL_GUARD_V1', 'guard_schema')
    child.require(child.sha(config['plan_path']) == config['plan_sha256'], 'guard_plan_bytes')
    plan = child.validate_plan(child.read(config['plan_path']))
    source = Path(plan['source_root']).resolve()
    child.require(source == Path(__file__).resolve().parents[1], 'frozen_source_location')
    actual = {str(path.relative_to(source)):child.sha(path) for path in source.rglob('*.py')}
    child.require(actual == config['source_pins'], 'entire_python_source_closure')
    child.require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == config['host_sha256'], 'hashed_node_binding')
    child.require(config['hard_end_unix'] == plan['hard_end_unix'], 'one_bound_wall')
    child.require(child.sha(config['lease_path']) == config['lease_sha256'], 'lease_receipt_bytes')
    lease = child.read(config['lease_path'])
    child.require(plan['lease_end_unix'] == lease['lease_end_unix']
        and plan['hard_end_unix'] <= lease['hard_end_unix'], 'existing_lease_margin_preserved')
    child.require(plan['hard_end_unix'] <= config['next_reserved_unix']-120, 'preserve_next_reservation')
    allocation = child.read(config['allocation_path'])
    child.require(child.sha(config['allocation_path']) == config['allocation_sha256']
        and allocation['plan_sha256'] == config['plan_sha256'] and allocation['cpu_tests_passed'] is True
        and allocation['gpu_uuid'] == plan['gpu_uuid'] and allocation['physical'] == plan['physical']
        and allocation['builder_entry_logged'] is True
        and child.sha(allocation['cpu_receipt_path']) == allocation['cpu_receipt_sha256']
        and child.read(allocation['cpu_receipt_path'])['passed'] is True, 'posted_allocation_and_CPU_provenance')
    child.require(time.time()-allocation['declared_unix'] >= 0, 'allocation_not_future')
    attempt = Path(config['attempt_dir'])
    child.require(attempt.is_absolute() and not attempt.resolve().is_relative_to(source), 'attempt_outside_source')
    return config, plan


def scan(config_path):
    config, plan = validate(config_path)
    child.require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'privileged_CPU_scan')
    from gpu import orch_rich_hot_a100_minor_scan as minor
    from gpu import orch_r111_route_admission as admission
    def allocation(index):
        child.require(index == plan['physical'], 'only_allocated_device')
    minor.pinned.policy = SimpleNamespace(HOST_SHA=config['host_sha256'],
        DEVICES={plan['physical']:plan['gpu_uuid']}, require=child.require, allocation=allocation)
    service = Path(config['attempt_dir'])/'SERVICE_IDENTITY.json'
    if not service.exists():
        minor.pinned.service(service)
    return admission.scan(plan['physical'], service)


def native_entry(config_path):
    config, plan = validate(config_path)
    await_startup(config, sys.stdin)
    attempt = Path(config['attempt_dir'])
    launch = child.read(attempt/'LAUNCH.json')
    child.require((attempt/'DISPATCH_ONCE').is_dir() and launch['pid'] == os.getppid(), 'actual_timeout_parent')
    ticks = Path('/proc',str(os.getppid()),'stat').read_text().rsplit(')',1)[1].split()[19]
    child.require(ticks == launch['parent_start_ticks'] and launch['guard_sha256'] == child.sha(config_path),
                  'launch_process_and_config_binding')
    report = child.read(attempt/'ADMISSION.json')
    child.require(child.sha(attempt/'ADMISSION.json') == launch['admission_sha256']
        and report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons']
        and report['gpu']['uuid'] == plan['gpu_uuid']
        and 0 <= time.time()-launch['admission_verified_unix'] <= 120, 'fresh_clear_admission')
    child.require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'native_GPU_binding')
    os.environ['R125_ADMISSION_PLAN_SHA256'] = config['plan_sha256']
    from gpu.c2_prefix_authority import admitted_prefix
    with admitted_prefix(config, plan, guard_path=config_path):
        child.run(config['plan_path'], resume=config['resume'])


def supervise(config_path):
    config, plan = validate(config_path)
    attempt = Path(config['attempt_dir'])
    (attempt/'DISPATCH_ONCE').mkdir()
    process = None
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=plan['source_root'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false')
    try:
        command = ['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH='+plan['source_root'],sys.executable,'-B','-m','gpu.orch_r125_continual_guard',
            'scan','--config',str(config_path)]
        bound = child.read(attempt/'PRE_SERVICE_ADMISSION.json')
        child.require(bound['guard_sha256'] == child.sha(config_path)
            and 0 <= time.time()-bound['verified_unix'] <= 120, 'fresh_bound_privileged_preservice_scan')
        report = bound['report']
        child.write_once(attempt/'ADMISSION.json', report)
        child.require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons'],
                      'fresh_exclusive_admission')
        admitted = time.time()
        remaining = int(plan['hard_end_unix']-time.time()-10)
        child.require(remaining > 10, 'time_for_native_load')
        command = ['timeout','--signal=TERM','--kill-after=5s',str(remaining)+'s',sys.executable,
            '-B','-m','gpu.orch_r125_continual_guard','native','--config',str(config_path)]
        with (attempt/'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'],
                env=dict(environment, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']), stdin=subprocess.PIPE,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            ticks = Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
            publish_launch(attempt/'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=ticks,
                started_unix=time.time(), admission_verified_unix=admitted,
                admission_sha256=child.sha(attempt/'ADMISSION.json'), guard_sha256=child.sha(config_path),
                command_sha256=child.digest(command), plan_sha256=config['plan_sha256'],
                gpu_uuid=plan['gpu_uuid'], hard_end_unix=plan['hard_end_unix'], no_retry=True))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            status = process.wait()
        child.write_once(attempt/'EXIT.json', dict(exit_code=status, finished_unix=time.time(), no_retry=True))
        child.require(status == 0, 'native_failed_preserve_no_retry')
    except BaseException as error:
        reap_owned_child(process)
        child.write_once(attempt/'FAILED.json', dict(error_type=type(error).__name__, error=str(error),
            finished_unix=time.time(), no_retry=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('scan','supervise','native'))
    parser.add_argument('--config', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.action == 'scan':
        print(json.dumps(scan(arguments.config), sort_keys=True))
    elif arguments.action == 'native':
        native_entry(arguments.config)
    else:
        supervise(arguments.config)
