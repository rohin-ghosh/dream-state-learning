"""Fresh original scan after a proven before-native A40R7 identity denial."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from gpu import orch_r145_a40r7_recovery as recovery


def reference(path):
    return dict(path=str(Path(path).absolute()), sha256=recovery.sha(path))


def validate_denial(control, config):
    control = Path(control)
    recovery.require(str(control) == config['attempt_dir'], 'exact_denied_control')
    for name in ('CONTAINED_COMMAND.json', 'CONTAINMENT_VERIFIED.json', 'LAUNCH.json', 'NATIVE.log',
                 'EXIT.json', 'SERVICE_EXIT.json', 'ADMISSION_TIME.json'):
        recovery.require(not (control / name).exists(), 'no_possible_native_dispatch')
    recovery.require(not recovery.RECOVERY.exists(), 'no_started_recovery_or_OOM_retry')
    log = (control / 'SUPERVISOR.log').read_text()
    recovery.require(log.rstrip().endswith('ValueError: unchanged_global_exclusive_admission'),
                     'only_original_pre_native_admission_error')
    report = json.loads((control / 'ADMISSION.json').read_text())
    reasons = report['blocking_reasons']
    recovery.require(report['clear'] is False and report['scanner_euid'] == 0 and reasons
        and all(reason.startswith('process_identity_drift:') and reason.split(':')[1].isdigit() for reason in reasons),
        'only_identity_drift_not_foreign_device_or_policy_denial')
    supervisor = json.loads((control / 'SUPERVISOR_DISPATCH.json').read_text())
    recovery.require(not Path('/proc', str(supervisor['pid'])).exists(), 'previous_supervisor_exited')
    return report


def revised_config(config, destination, unit):
    result = deepcopy(config)
    result['attempt_dir'] = str(destination)
    result['device_containment']['unit'] = unit
    normalized = deepcopy(result)
    normalized['attempt_dir'] = config['attempt_dir']
    normalized['device_containment']['unit'] = config['device_containment']['unit']
    recovery.require(normalized == config, 'only_attempt_directory_and_unit_change')
    return result


def readmit(control, destination, cpu_gate):
    from gpu import orch_r125_continual_guard as guard
    control, destination = Path(control).absolute(), Path(destination).absolute()
    recovery.require(control.parent == recovery.BASE and destination.parent == recovery.BASE
        and control.name.startswith('control_r145_a40r7_')
        and destination.name.startswith(control.name + '_readmit') and not destination.exists(),
        'new_owned_same_life_control_only')
    config, plan = guard.validate(control / 'GUARD.json')
    recovery.require(plan['physical'] == 7 and plan['gpu_uuid'] == recovery.GPU_UUID
        and plan['root'] == str(recovery.ROOT) and config['resume'] is True, 'original_owned_restore')
    manifest = json.loads(recovery.raw(config['r145_a40r7_manifest']['path']))
    recovery.verify_manifest(manifest, config['r145_a40r7_acknowledgment'])
    report = validate_denial(control, config)
    gate = json.loads(recovery.raw(cpu_gate))
    recovery.require(gate['status'] == 'PASS' and gate['module_sha256'] == recovery.sha(Path(__file__).absolute()),
        'own_readmission_tests_bound')
    recovery.require(recovery.sha(gate['log']['path']) == gate['log']['sha256'], 'readmission_test_log_binding')
    recovery.pinned_evidence()
    recovery.verify_original_absent()
    recovery.verify_topology()
    destination.mkdir()
    revised = revised_config(config, destination, 'orch-r136-native-' + uuid.uuid4().hex)
    recovery.save(destination / 'GUARD.json', revised)
    guard.validate(destination / 'GUARD.json')
    binding = dict(original_guard=reference(control / 'GUARD.json'), original_admission=reference(control / 'ADMISSION.json'),
        original_failure_log=reference(control / 'SUPERVISOR.log'), CPU_gate=reference(cpu_gate),
        denial_reasons=report['blocking_reasons'], same_frozen_source=True, same_manifest_and_ACK=True,
        same_saved_checkpoint=True, original_scanner_unchanged=True, observed_unix=time.time())
    recovery.save(destination / 'READMISSION_BINDING.json', binding)
    command = [sys.executable, '-B', '-m', 'gpu.orch_r145_a40r7_recovery', 'contained-supervise',
               '--config', str(destination / 'GUARD.json')]
    time.sleep(2)
    with (destination / 'SUPERVISOR.log').open('x') as log:
        process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=plan['source_root']))
    receipt = dict(status='READMISSION_SUPERVISOR_DISPATCHED_NOT_NATIVE_LOADED', pid=process.pid,
        command=command, guard=reference(destination / 'GUARD.json'), started_unix=time.time())
    recovery.save(destination / 'SUPERVISOR_DISPATCH.json', receipt)
    print(json.dumps(receipt, indent=2), flush=True)
    time.sleep(20)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--cpu-gate', type=Path, required=True)
    readmit(**vars(parser.parse_args()))
