"""Expose unchanged scanner evidence for busy-owner preflight, never admission."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from types import FunctionType

from gpu import orch_r110_admission as original
from gpu import orch_r111_route_admission as route
from gpu import orch_r125_continual_guard as guard


SCHEMA = 'R179_BUSY_PREFLIGHT_EVIDENCE_ONLY_V1'
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
ROOTS = {
    0: '/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/run1',
    1: '/localhome/local-rohing/orch_r136_raw_unparented_a40r1_20260916_attempt1/run1',
    3: '/localhome/local-rohing/orch_r136_raw_parented_seed1_a40r3_20260916_attempt1/run1',
    4: '/localhome/local-rohing/orch_r136_kernel_parented_a40r4_20260916_attempt1/run1',
}
KERNEL_KEYS = ('pid', 'uid', 'start_ticks', 'boot_id')


def classify_argv_only(report, observations):
    if report.get('scanner_euid') != 0:
        return []
    processes = {entry['pid']: entry for entry in report['processes']}
    computing = {entry['pid'] for entry in report['compute_processes']}
    accepted = []
    for pid, samples in observations.items():
        process = processes.get(pid)
        if not process or len(samples) < 3 or pid in computing:
            continue
        if process.get('target_device_open') is not False or process.get('cvd') not in (None, '', '-1'):
            continue
        first = samples[0]
        keys = KERNEL_KEYS + ('executable_identity',)
        if any(key not in first for key in keys) or first['pid'] != pid:
            continue
        if any(sample.get('visibility_complete') is not True or sample.get('target_open') is not False
               or sample.get('cvd') not in (None, '', '-1')
               or any(sample.get(key) != first[key] for key in keys) for sample in samples):
            continue
        if any(process.get(key) != first[key] for key in ('uid', 'start_ticks')):
            continue
        if any(process.get('pinned_identity', {}).get(key) != first[key] for key in KERNEL_KEYS):
            continue
        if any(not isinstance(sample.get('command_sha256'), str) for sample in samples):
            continue
        if len({sample['command_sha256'] for sample in samples}) < 2:
            continue
        accepted.append(pid)
    return sorted(accepted)


def annotate(report, observations):
    result = deepcopy(report)
    eligible = classify_argv_only(report, observations)
    canonical = json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    result['r179_preflight_evidence'] = dict(schema=SCHEMA,
        original_report_sha256=hashlib.sha256(canonical).hexdigest(),
        eligible_non_gpu_argv_only_pids=eligible,
        observations={str(pid): deepcopy(observations[pid]) for pid in eligible},
        original_clear_and_blockers_unchanged=True, admission_receipt=False,
        scope='PRE_RETIREMENT_KNOWN_OWNER_PREFLIGHT_ONLY_FINAL_SCAN_UNCHANGED')
    return result


def scan(config_path):
    if os.geteuid() != 0 or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('privileged_CPU_only_preflight')
    config, plan = guard.validate(config_path)
    if config['host_sha256'] != HOST_SHA or plan['physical'] not in ROOTS \
            or plan['root'] != ROOTS[plan['physical']]:
        raise ValueError('exact_R179_node4_preflight_scope')
    old_scan = route.scan

    def capture(report, observations):
        return annotate(route.reconcile(report, observations), observations)

    def observed_scan(index, service_path):
        namespace = dict(original.scan.__globals__, reconcile=capture)
        observed = FunctionType(original.scan.__code__, namespace, 'scan', original.scan.__defaults__)
        return observed(index, service_path)

    route.scan = observed_scan
    try:
        return guard.scan(config_path)
    finally:
        route.scan = old_scan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(scan(args.config), sort_keys=True))


if __name__ == '__main__':
    main()
