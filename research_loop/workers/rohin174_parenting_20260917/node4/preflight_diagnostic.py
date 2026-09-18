"""Expose rejected original scanner samples, never grant readiness or admission."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from types import FunctionType


HELPER_SHA = '0fdbd4da086efac21d297874d7a61ee6d73e6515fafa0d02a56bd35fcd441bcf'
BUNDLE = Path('/localhome/local-rohing/orch_r179_node4_r181_20260917t2150z')
DRIFT = re.compile(r'(process_identity_drift|minor_scan_identity_changed|minor_scan_process_drift):([0-9]+)\Z')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def explain(report, observations, helper):
    annotated = helper.annotate(report, observations)
    require({key: value for key, value in annotated.items() if key != 'r179_preflight_evidence'} == report,
        'original_report_all_fields_unchanged')
    eligible = set(annotated['r179_preflight_evidence']['eligible_non_gpu_argv_only_pids'])
    processes = {process['pid']: process for process in report['processes']}
    rejected = {}
    for reason in report['blocking_reasons']:
        match = DRIFT.fullmatch(reason)
        if match is None or int(match[2]) in eligible:
            continue
        pid = int(match[2])
        samples = observations.get(pid, [])
        process = processes.get(pid)
        failures = []
        if len(samples) < 3:
            failures.append('fewer_than_three_original_samples')
        if process is None:
            failures.append('no_original_process_entry')
        if samples:
            first = samples[0]
            for key in helper.KERNEL_KEYS + ('executable_identity',):
                if key not in first or any(sample.get(key) != first.get(key) for sample in samples):
                    failures.append('missing_or_changed_' + key)
            if any(sample.get('visibility_complete') is not True for sample in samples):
                failures.append('incomplete_original_visibility')
            if any(sample.get('target_open') is not False for sample in samples):
                failures.append('target_fd_not_proven_absent')
            if any(sample.get('cvd') not in (None, '', '-1') for sample in samples):
                failures.append('nonempty_CVD')
            if len({sample.get('command_sha256') for sample in samples}) < 2:
                failures.append('no_observed_argv_change')
            if process and any(process.get('pinned_identity', {}).get(key) != first.get(key)
                               for key in helper.KERNEL_KEYS):
                failures.append('original_pinned_identity_mismatch')
        if any(entry['pid'] == pid for entry in report['compute_processes']):
            failures.append('compute_entry_on_any_GPU')
        rejected[str(pid)] = dict(original_process=deepcopy(process), original_samples=deepcopy(samples),
            original_sample_count=len(samples), diagnostic_failure_reasons=failures,
            eligible_for_exception=False)
    return dict(schema='NODE4_ORIGINAL_PREFLIGHT_REJECTION_DIAGNOSTIC_V1',
        original_annotated_report=annotated, rejected_process_evidence=rejected,
        acceptance_changed=False, admission_receipt=False, native_signals=0,
        scope='DIAGNOSTIC_ONLY_NOT_USED_BY_HANDOFF')


def scan(physical):
    require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'privileged_CPU_only')
    require(type(physical) is int and physical in (0, 1), 'blocked_NODE4_0_1_only')
    lane = BUNDLE / f'lane{physical}'
    stage = json.loads((lane / 'STAGED.json').read_text())
    source = lane / 'source'
    config = lane / 'control/GUARD.json'
    require(stage['physical'] == physical and stage['source_root'] == str(source)
        and stage['new_config_sha256'] == digest(config), 'exact_existing_staged_guard')
    path = source / 'gpu/orch_r179_busy_preflight.py'
    require(digest(path) == HELPER_SHA, 'unchanged_Main_helper')
    sys.path.insert(0, str(source))
    from gpu import orch_r179_busy_preflight as helper
    require(Path(helper.__file__).resolve() == path, 'actual_source_import')
    captured = []

    def capture(report, observations):
        result = explain(report, observations, helper)
        captured.append(result)
        return result['original_annotated_report']

    namespace = dict(helper.scan.__globals__, annotate=capture)
    copied_scan = FunctionType(helper.scan.__code__, namespace, helper.scan.__name__, helper.scan.__defaults__)
    report = copied_scan(config)
    require(len(captured) == 1 and report == captured[0]['original_annotated_report'], 'single_original_scan')
    return dict(captured[0], physical=physical, helper_sha256=HELPER_SHA, source=str(source),
        diagnostic_sha256=digest(__file__), guard_sha256=digest(config))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physical', type=int, choices=(0, 1), required=True)
    arguments = parser.parse_args()
    print(json.dumps(scan(arguments.physical), sort_keys=True, allow_nan=False))
