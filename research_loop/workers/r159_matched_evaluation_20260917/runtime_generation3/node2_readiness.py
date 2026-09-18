import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time


OLD = Path('/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1')
NEW = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
RUNTIME = NEW / 'preparation/runtime_generation2'
EXPECTED_CONTROLLER = dict(boot_id='8ff7b0dc-fbdf-4945-9044-3dffe94b5407',
    pid=1688939, start_ticks='84709817', uid=2524)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def main():
    assert socket.gethostname() == '[REDACTED_HOST]'
    started = time.time()
    manifest_path = RUNTIME / 'SOURCE_MANIFEST.json'
    assert sha(manifest_path) == 'a7f09b623ea9d270f9af70de38b299c2c80f516eae4bbafbab9ba0822f1d0200'
    manifest = read(manifest_path)
    mismatches = [name for name, expected in manifest['sources'].items()
                  if sha(RUNTIME / 'source' / name) != expected]
    assert not mismatches
    sys.path.insert(0, str(RUNTIME / 'source'))
    from gpu import orch_r130_benchmark_sidecar as sidecar
    from gpu import orch_r159_matched_evaluation as evaluator
    scheduler_path = OLD / 'SCHEDULER_R158_20260917T0416Z.json'
    scheduler = read(scheduler_path)
    plan = read(scheduler['template_plan_path'])
    terminal_path = OLD / 'successor_phase_r158_20260917t0416z/COMPLETE.json'
    terminal = read(terminal_path)
    try:
        current = sidecar.identity(EXPECTED_CONTROLLER['pid'])
    except (FileNotFoundError, ProcessLookupError):
        current = None
    service = read(scheduler['service_path'])
    try:
        service_current = sidecar.identity(service['pid'])
    except (FileNotFoundError, ProcessLookupError):
        service_current = None
    result = dict(schema='R159_NODE2_READONLY_READINESS_V1', started_unix=started,
        hostname=socket.gethostname(), source_manifest=reference(manifest_path),
        source_files_verified=len(manifest['sources']), source_mismatches=mismatches,
        old_scheduler=reference(scheduler_path), old_terminal=reference(terminal_path),
        old_terminal_status=terminal['status'], old_terminal_identity=EXPECTED_CONTROLLER,
        current_controller_identity=current, old_controller_same_identity_alive=current == EXPECTED_CONTROLLER,
        old_caps=dict(total_calls=4800, phase_jobs=58),
        terminal_counts={key: terminal[key] for key in ('completed_checkpoint_count',
            'reserved_checkpoint_count', 'phase_charged', 'remaining_jobs',
            'remaining_total_call_budget', 'own_admitted') if key in terminal},
        python=scheduler['python'], python_sha256=sha(scheduler['python']),
        python_resolved=str(Path(scheduler['python']).resolve()),
        python_executable=os.access(scheduler['python'], os.X_OK),
        model_dir=plan['model_dir'], model_dir_exists=Path(plan['model_dir']).is_dir(),
        service=reference(scheduler['service_path']), service_expected_sha256=scheduler['service_sha256'],
        service_identity_matches=service_current == {key: service[key] for key in ('pid', 'uid', 'boot_id', 'start_ticks')},
        existing_lease_end_unix=scheduler['lease_end_unix'], proposed_hard_end_unix=1789632000,
        source_read_end_unix=1789632000,
        six_hour_margin_satisfied=1789632000 <= scheduler['lease_end_unix']-21600,
        latest_dispatch_strictly_before_unix=1789632000-3615,
        new_ledger=evaluator.ledger_status(NEW, evaluator.ORIGINAL_PLAN_SHA256), devices={})
    locks = Path('/proc/locks').read_text().splitlines()
    for physical in (0, 1):
        path = OLD / f'physical{physical}.lock'
        metadata = dict(path=str(path), exists=path.exists(), lock_acquired=False)
        if path.exists():
            info = path.stat()
            matched = []
            for line in locks:
                parts = line.split()
                for token in parts:
                    fields = token.split(':')
                    if len(fields) == 3:
                        try:
                            if (int(fields[0], 16), int(fields[1], 16), int(fields[2])) == (
                                    os.major(info.st_dev), os.minor(info.st_dev), info.st_ino):
                                matched.append(line)
                        except ValueError:
                            pass
            metadata.update(inode=info.st_ino, kernel_lock_entries=matched)
        try:
            report = sidecar.scan(dict(physical=physical, gpu_uuid=sidecar.DEVICES[physical],
                service_path=scheduler['service_path']))
            scan = dict(clear=report['clear'], blocking_reasons=report['blocking_reasons'],
                scanner_euid=report['scanner_euid'], gpu_uuid=report['gpu']['uuid'],
                report_sha256=hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest())
        except Exception as error:
            scan = dict(clear=False, error_type=type(error).__name__, details_not_returned=True)
        result['devices'][str(physical)] = dict(gpu_uuid=sidecar.DEVICES[physical], lock=metadata, scan=scan)
    result.update(observed_unix=time.time(), source_written=False, gpu_model_calls=0,
        enrollment=False, benchmark_contents_read=False)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
