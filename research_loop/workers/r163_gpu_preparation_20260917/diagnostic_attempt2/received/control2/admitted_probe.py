"""Explicit-GO, one-shot node3 physical5 numerical validation wrapper."""

import argparse
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r163_numerical_diagnostic_20260917_attempt2')
SOURCE = ROOT / 'selected_source'
CONFIG = ROOT / 'control2/GUARD.json'
MANIFEST = ROOT / 'control2/SOURCE_PINS.json'
ATTEMPT = ROOT / 'attempt1'
UUID = 'GPU-bc211959-642d-664b-3581-42a0dbe434e9'
NATIVE_SHA = 'bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve()
            and not any(part.is_symlink() for part in (path, *path.parents)), 'canonical_file')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def binding(config):
    return dict(config=ref(CONFIG), plan=ref(Path(config['plan_path'])),
                manifest=ref(MANIFEST), operator=ref(Path(__file__).resolve()),
                lease=ref(Path(config['lease_path'])), physical=5, gpu_uuid=UUID,
                attempt_dir=str(ATTEMPT), hard_end_unix=config['hard_end_unix'])


def validate_go(go, expected, now):
    require(go.get('schema') == 'R163_NODE3_NUMERICAL_GO_V1'
            and go.get('issuer') == 'Main' and go.get('decision') == 'GO', 'explicit_Main_GO')
    require(go.get('binding') == expected, 'exact_GO_binding')
    require(go['not_before_unix'] <= now < go['expires_unix'] <= expected['hard_end_unix'], 'fresh_GO')
    require(now < expected['hard_end_unix'] <= now + 1800
            and expected['hard_end_unix'] + 21600 <= 1789668000, 'thirty_minutes_and_six_hour_margin')


def validate_admission(report):
    require(report['scanner_euid'] == 0 and report['clear'] is True
            and report['blocking_reasons'] == [] and report['gpu']['uuid'] == UUID
            and report['gpu']['index'] == 5 and report['device_minor'] == 5,
            'unchanged_fresh_physical5_admission')


def validate(go_path, go_sha256, action):
    require(socket.gethostname() == '[REDACTED_HOST]' and os.getuid() == os.getgid() == 2524,
            'exact_node3_nonroot_operator')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == ('' if action == 'supervise' else UUID),
            'correct_operator_GPU_visibility')
    require(sha(go_path) == go_sha256, 'exact_GO_bytes')
    require(sha(SOURCE / 'gpu/orch_r125_continual_native.py') == NATIVE_SHA, 'exact_candidate5_native')
    sys.path.insert(0, str(SOURCE))
    guard = importlib.import_module('gpu.orch_r125_continual_guard')
    node3 = importlib.import_module('gpu.orch_r133_node3_programmes')
    driver = importlib.import_module('gpu.orch_r163_probe_driver')
    for module in (guard, node3, driver):
        require(Path(module.__file__).resolve().parent == SOURCE / 'gpu', 'selected_source_only')
    config, plan = guard.validate(CONFIG)
    require(plan['physical'] == 5 and plan['gpu_uuid'] == UUID and plan['seed'] == 0
            and plan.get('r163_validation_only') is True and plan['source_root'] == str(SOURCE)
            and plan['root'] == str(ROOT / 'validation_run1') and config['resume'] is False
            and config['attempt_dir'] == str(ATTEMPT), 'fresh_validation_only_scope')
    require(config['device_containment']['minor'] == 5
            and config['device_containment']['uid'] == config['device_containment']['gid'] == 2524,
            'physical5_only_device_policy')
    require(not any(key in plan for key in ('initialization_source', 'preupdate_recovery', 'matched_cohort')),
            'no_original_checkpoint_or_cohort')
    manifest = read(MANIFEST)
    driver.verify_sources(manifest)
    require(manifest['files'].get(str(Path(__file__).resolve())) == sha(Path(__file__).resolve()),
            'operator_in_selected_manifest')
    require(all(Path(path).stat().st_mode & 0o222 == 0 for path in manifest['files']), 'immutable_code')
    driver.verify_imports(manifest)
    validate_go(read(go_path), binding(config), time.time())
    require(not Path(plan['root']).exists(), 'no_existing_validation_root')
    return config, plan, node3, driver


def supervise(go_path, go_sha256):
    config, plan, node3, driver = validate(go_path, go_sha256, 'supervise')
    descriptor = os.open(ROOT.parent / '.orch_r163_node3_physical5.lock',
                         os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ATTEMPT.mkdir(mode=0o700, exist_ok=False)
        write(ATTEMPT / 'DISPATCH_ONCE.json', dict(binding=binding(config), go=ref(go_path), no_retry=True))
        try:
            scan_command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                            'PYTHONPATH=' + str(SOURCE), sys.executable, '-B', '-m',
                            'gpu.orch_r125_continual_guard', 'scan', '--config', str(CONFIG)]
            scanned = subprocess.run(scan_command, capture_output=True, text=True, timeout=100, check=False)
            write(ATTEMPT / 'SCAN_PROCESS.json', dict(returncode=scanned.returncode,
                  stdout=scanned.stdout, stderr=scanned.stderr, finished_unix=time.time()))
            require(scanned.returncode == 0, 'scanner_process_failed')
            report = json.loads(scanned.stdout)
            write(ATTEMPT / 'ADMISSION.json', report)
            validate_admission(report)
            write(ATTEMPT / 'ADMISSION_TIME.json', dict(verified_unix=time.time(),
                  report=ref(ATTEMPT / 'ADMISSION.json'), binding=binding(config)))
            remaining = int(plan['hard_end_unix'] - time.time())
            require(0 < remaining <= 1800, 'remaining_probe_window')
            command = node3.containment_command(plan, config['device_containment'],
                [sys.executable, '-B', str(Path(__file__).resolve()), 'native',
                 '--main-go', str(go_path), '--main-go-sha256', go_sha256], remaining)
            write(ATTEMPT / 'CONTAINED_COMMAND.json', dict(command=command, started_unix=time.time()))
            with (ATTEMPT / 'SERVICE.log').open('x') as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
            write(ATTEMPT / 'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
            require(result.returncode == 0, 'contained_probe_failed_no_retry')
        except BaseException as error:
            write(ATTEMPT / 'FAILED.json', dict(error_type=type(error).__name__, error=str(error),
                  failed_unix=time.time(), no_retry=True))
            raise
    finally:
        os.close(descriptor)


def native(go_path, go_sha256):
    config, plan, node3, driver = validate(go_path, go_sha256, 'native')
    require((ATTEMPT / 'DISPATCH_ONCE.json').is_file(), 'supervisor_dispatch_required')
    receipt = read(ATTEMPT / 'ADMISSION_TIME.json')
    require(receipt['binding'] == binding(config)
            and receipt['report'] == ref(ATTEMPT / 'ADMISSION.json')
            and 0 <= time.time() - receipt['verified_unix'] <= 120, 'fresh_bound_admission_receipt')
    validate_admission(read(ATTEMPT / 'ADMISSION.json'))
    proof = node3.verify_containment(config, plan)
    write(ATTEMPT / 'CONTAINMENT_VERIFIED.json', proof)
    write(ATTEMPT / 'PRE_NATIVE.json', dict(pid=os.getpid(), observed_unix=time.time(),
          model_loaded_claimed=False, go=ref(go_path), binding=binding(config)))
    result = driver.main(['--plan', config['plan_path'], '--plan-sha256', config['plan_sha256'],
                          '--manifest', str(MANIFEST), '--manifest-sha256', sha(MANIFEST)])
    write(ATTEMPT / 'DRIVER_EXIT.json', dict(returncode=result, finished_unix=time.time()))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('supervise', 'native'))
    parser.add_argument('--main-go', type=Path, required=True)
    parser.add_argument('--main-go-sha256', required=True)
    args = parser.parse_args()
    return supervise(args.main_go, args.main_go_sha256) if args.action == 'supervise' else native(args.main_go, args.main_go_sha256)


if __name__ == '__main__':
    raise SystemExit(main())
