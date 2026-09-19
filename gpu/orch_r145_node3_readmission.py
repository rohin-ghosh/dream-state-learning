"""Fresh original admission after an exact before-native identity-drift denial."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import time
import uuid

from gpu import orch_r145_node3_admitted_recovery as admitted
from gpu import orch_r145_node3_capacity_recovery as capacity
from gpu import orch_r145_node3_stage_recovery as staging


def validate_denial(control, config, manifest):
    control = Path(control)
    capacity.require(control == Path(config['attempt_dir']), 'exact_denied_control')
    for name in ('CONTAINED_COMMAND.json', 'CONTAINMENT_VERIFIED.json', 'LAUNCH.json', 'NATIVE.log', 'EXIT.json'):
        capacity.require(not (control / name).exists(), 'never_readmit_after_possible_native_dispatch')
    capacity.require(not Path(manifest['recovery_output']).exists(), 'never_readmit_after_recovery_started')
    failure = json.loads((control / 'FAILED.json').read_text())
    capacity.require(failure['error'] == 'unchanged_global_exclusive_admission', 'only_original_admission_failure')
    report = json.loads((control / 'ADMISSION.json').read_text())
    reasons = report['blocking_reasons']
    capacity.require(report['clear'] is False and report['scanner_euid'] == 0 and reasons
        and all(reason.startswith('process_identity_drift:') and reason.split(':')[1].isdigit() for reason in reasons),
        'only_transient_identity_denial_never_foreign_device_blockers')
    request = json.loads((control / 'SUPERVISOR_REQUEST.json').read_text())
    capacity.require(not Path('/proc', str(request['pid'])).exists(), 'previous_supervisor_must_exit')
    return report


def readmit(control, destination, cpu_gate):
    control, destination = Path(control).absolute(), Path(destination).absolute()
    config = json.loads((control / 'GUARD_CONTAINED.json').read_text())
    plan = json.loads(Path(config['plan_path']).read_text())
    manifest = admitted.verify_manifest(config, plan)
    report = validate_denial(control, config, manifest)
    gate = json.loads(Path(cpu_gate).read_text())
    capacity.require(gate['status'] == 'PASS' and gate['module_sha256'] == capacity.file_sha(__file__), 'same_readmission_CPU_gate')
    capacity.require(destination.parent == control.parent and destination.name.startswith(control.name + '_readmit')
                     and not destination.exists(), 'new_same_lane_readmission_control')
    destination.mkdir()
    revised = deepcopy(config)
    revised['attempt_dir'] = str(destination)
    revised['device_containment']['unit'] = 'orch-r133-node3-' + uuid.uuid4().hex
    capacity.save_once(destination / 'CONFIG_PENDING_ACK.json', revised)
    capacity.save_once(destination / 'RELEASE.json', json.loads((control / 'RELEASE.json').read_text()))
    capacity.save_once(destination / 'READMISSION_BINDING.json', dict(original_control=str(control),
        original_admission=staging.reference(control / 'ADMISSION.json'), original_failure=staging.reference(control / 'FAILED.json'),
        cpu_gate=staging.reference(cpu_gate), denial_reasons=report['blocking_reasons'],
        same_frozen_source=True, same_manifest=True, scanner_policy_changed=False, observed_unix=time.time()))
    staging.launch(destination, config['r145_acknowledgment']['path'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--cpu-gate', type=Path, required=True)
    readmit(**vars(parser.parse_args()))
