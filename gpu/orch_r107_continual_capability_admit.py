"""Nonmaterial pre-dispatch scanner recovery; original plan/source remain frozen.

Only eligible after a recorded process-identity scan race with zero dispatched
calls. Preserve the failed full scan, repeat full privileged scans for <=60s,
and launch only on strict CLEAR within the original absolute deadlines.
"""

import argparse
import math
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_r107_continual_capability_run as run


def transient(report):
    reasons = report['blocking_reasons']
    return bool(reasons) and report['scanner_euid'] == 0 and report['gpu']['memory_used_mib'] == 0 \
        and report['gpu']['utilization_percent'] == 0 \
        and not any(row['gpu_uuid'] == run.GPU_UUID for row in report['compute_processes']) \
        and all(reason.startswith(('process_identity_drift:', 'minor_scan_identity_changed:',
                                   'minor_scan_process_drift:')) for reason in reasons)


def eligible(root):
    run.require((root / 'LAUNCH_ONCE').is_dir() and not (root / 'LAUNCH.json').exists()
                and not (root / 'readout').exists(), 'zero_dispatch_scan_failure_only')
    run.require(transient(run.read(root / 'FULL_SCAN.json')), 'preserved_transient_scan_required')


def recover(root, publication_path):
    run.require(run.host_identity() == run.continual.combined.HOST_SHA and os.environ.get('CUDA_VISIBLE_DEVICES') == '',
                'exact_cpu_a100_recovery')
    plan = run.validate(run.read(root / 'PLAN.json'), time.time())
    run.validate_ready(root, plan)
    eligible(root)
    publication = run.read(publication_path)
    run.require(publication['source_sha256'] == run.sha(__file__)
                and publication['original_plan_sha256'] == run.sha(root / 'PLAN.json')
                and publication['failed_scan_sha256'] == run.sha(root / 'FULL_SCAN.json')
                and publication['own_cpu_tests_passed'] is True and publication['dated_builder_publication'],
                'bound_recovery_publication_required')
    recovery = root / 'ADMISSION_RECOVERY'
    recovery.mkdir(exist_ok=False)
    cutoff = min(time.time() + 60, plan['native_deadline_unix'])
    report = None
    for attempt in range(30):
        run.require(time.time() < cutoff, 'bounded_scan_recovery_exhausted')
        report = run.continual.scan(0, run.continual.ROOT / 'SERVICE_IDENTITY.json')
        run.write(recovery / f'SCAN_{attempt:03d}.json', report)
        if report['clear'] is True:
            run.validate_scan(report, time.time())
            break
        run.require(transient(report), 'actual_ownership_or_memory_block_no_waiver')
        time.sleep(1)
    run.require(report is not None and report['clear'] is True, 'strict_clear_required')
    eligible(root)
    run.validate(plan, time.time())
    run.write(root / 'ADMISSION.json', dict(clear=True, uuid=run.GPU_UUID, observed_unix=time.time(),
        plan_sha256=run.sha(root / 'PLAN.json'), snapshot=report,
        preserved_failed_scan_sha256=run.sha(root / 'FULL_SCAN.json'),
        recovery_publication_sha256=run.sha(publication_path)))
    seconds = math.floor(plan['hard_deadline_unix'] - time.time() - 5)
    run.require(seconds > 0, 'original_lifetime_exhausted')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=run.GPU_UUID, HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(run.SOURCE_ROOT))
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(seconds) + 's',
        run.continual.PYTHON, '-B', '-m', 'gpu.orch_r107_continual_capability_run', 'run', '--root', str(root)]
    with (root / 'native.log').open('x') as log:
        child = subprocess.Popen(command, cwd=run.SOURCE_ROOT, env=environment, stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True)
    identity = run.continual.minor_scan.pinned.identity(Path('/proc') / str(child.pid))
    receipt = dict(status='LAUNCHED', timeout_identity=identity, command=command,
        admission_sha256=run.sha(root / 'ADMISSION.json'), plan_sha256=run.sha(root / 'PLAN.json'),
        hard_deadline_unix=plan['hard_deadline_unix'], calls_cap=64, base_calls=0,
        launched_unix=time.time(), original_scan_preserved=True,
        recovery_source_sha256=run.sha(__file__))
    run.write(root / 'LAUNCH.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--publication', type=Path, required=True)
    arguments = parser.parse_args()
    print(run.json.dumps(recover(arguments.root, arguments.publication), sort_keys=True))
