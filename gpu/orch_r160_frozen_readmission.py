"""One explicitly authorized pre-native readmission of the R158 frozen arm."""

import argparse
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import socket
import sys
import time


BASE = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5')
SOURCE = BASE / 'source'
HOST = 'a4u8g-0105'
ARM = 'parented_frozen'
UUID = 'GPU-06b31c8f-7a96-d812-23f3-df3444d95397'
OLD_CONFIG = BASE / 'control/run-parented_frozen/GUARD.json'
OLD_ATTEMPT = BASE / 'attempts/run-parented_frozen-attempt1'
CONTROL = BASE / 'control/run-parented_frozen-r160-readmission'
ATTEMPT = BASE / 'attempts/run-parented_frozen-attempt2'
MARKER = BASE / 'control/PHASE_ONCE_R160_run_parented_frozen'
OLD_MARKER = BASE / 'control/PHASE_ONCE_run_parented_frozen'
PINS = {
    'config': (OLD_CONFIG, 'c49fc41bf226d223a2ad8825da6141183f0f03f2c4a042bdb97e9804f70b2945'),
    'admission': (OLD_ATTEMPT / 'ADMISSION.json', 'dce5e8adcaf6402a2f77d58fc3055def46e710e0c2658c9aa448565b5f491274'),
    'failure': (OLD_ATTEMPT / 'FAILED.json', '90082b2554ea4c82f8390fd6971a44a415f4741a8b34985b7d8ac137f281a297'),
    'lifecycle': (OLD_ATTEMPT / 'LIFECYCLE.json', '9ad0393f06dca9a9205c8931c1f3ab9b3dcce99620529afbd9d483f493aac975'),
}
RUNTIME_SHA = '4e21fe3b72f823b9b26ba2edd08e8442ac68c3ea0fe3cdfea1590a2a5cd085d7'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def regular(path):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve()
            and not any(part.is_symlink() for part in (path, *path.parents)) and path.is_file(),
            'canonical_regular_input')
    return path


def sha(path):
    return hashlib.sha256(regular(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(regular(path).read_bytes())


def reference(path):
    return dict(path=str(regular(path)), sha256=sha(path))


def bound(reference):
    require(set(reference) == {'path', 'sha256'} and sha(reference['path']) == reference['sha256'],
            'bound_receipt_bytes')
    return read(reference['path'])


def runtime():
    require(socket.gethostname() == HOST and os.getuid() == os.getgid() == 2524
            and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'node4_unprivileged_CPU_operator')
    require(sha(SOURCE / 'gpu/orch_r158_matched_node4.py') == RUNTIME_SHA, 'exact_frozen_R158_runtime')
    sys.path.insert(0, str(SOURCE))
    module = importlib.import_module('gpu.orch_r158_matched_node4')
    require(Path(module.__file__).resolve() == SOURCE / 'gpu/orch_r158_matched_node4.py',
            'runtime_loaded_only_from_frozen_source')
    return module


def validate_old(module):
    documents = {name: bound(dict(path=str(path), sha256=checksum)) for name, (path, checksum) in PINS.items()}
    config, admission, failure, lifecycle = (documents[name] for name in ('config', 'admission', 'failure', 'lifecycle'))
    plan = bound(dict(path=config['plan_path'], sha256=config['plan_sha256']))
    require(config['phase'] == 'run' and config['matched_arm'] == plan['matched_arm'] == ARM
            and config['resume'] is False and plan['physical'] == 6 and plan['gpu_uuid'] == UUID
            and plan['root'] == str(BASE / ARM) and plan['source_root'] == str(SOURCE)
            and config['attempt_dir'] == str(OLD_ATTEMPT), 'only_original_frozen_slot6_run')
    require(failure['stage'] == 'ADMISSION' and failure['error'] == 'fresh_exclusive_admission'
            and failure['status'] == 'FAILED' and failure['no_retry'] is True
            and lifecycle['status'] == 'NOT_STARTED' and lifecycle['observed'] is None
            and lifecycle['cgroup_empty_verified'] is None, 'exact_pre_native_refusal')
    require(admission['clear'] is False and admission['scanner_euid'] == 0
            and admission['gpu']['uuid'] == UUID and admission['gpu']['memory_used_mib'] == 0
            and admission['blocking_reasons'] == ['minor_scan_identity_changed:530040',
                'minor_scan_process_drift:530040', 'process_identity_drift:530215'], 'original_full_refusal_preserved')
    require(OLD_MARKER.is_dir() and not OLD_MARKER.is_symlink(), 'original_phase_marker_retained')
    require(not (BASE / ARM).exists() and not (BASE / ARM).is_symlink(), 'frozen_life_never_born')
    require(all(not (OLD_ATTEMPT / name).exists() and not (OLD_ATTEMPT / name).is_symlink()
                for name in ('LAUNCH.json', 'PRE_NATIVE.json', 'SERVICE_STARTED.json', 'NATIVE.log', 'NATIVE_EXIT.json')),
            'no_original_native_or_service_start')
    module.verify_cpu(config['r158_cpu']['path'], SOURCE)
    module.verify_repairs(config['r158_repairs']['path'], SOURCE, require_freeze=True)
    require(module.inventory(SOURCE) == read(config['source_manifest_path'])['files'], 'unchanged_frozen_inventory')
    require(all(path.stat().st_mode & 0o222 == 0 and not path.is_symlink()
                for path in (SOURCE, *SOURCE.rglob('*'))), 'frozen_source_permissions')
    return config, plan


def verify_cpu(path):
    receipt = read(path)
    require(receipt['status'] == 'PASS' and receipt['exit_code'] == 0
            and type(receipt['passed']) is int and receipt['passed'] > 0
            and receipt['operator_sha256'] == sha(Path(__file__).resolve()), 'actual_external_operator_CPU_gate')
    require(receipt['logs'], 'actual_CPU_logs')
    for log in receipt['logs']:
        require(sha(log['path']) == log['sha256'], 'CPU_log_bytes')
    return receipt


def derive_config(original, allocation, engine):
    config = deepcopy(original)
    config.update(attempt_dir=str(ATTEMPT), allocation_path=allocation['path'], allocation_sha256=allocation['sha256'])
    config['device_containment']['unit'] = engine.new_unit(ATTEMPT)
    return config


def prepare(cpu_path):
    module = runtime()
    original, plan = validate_old(module)
    verify_cpu(cpu_path)
    require(not ATTEMPT.exists() and not ATTEMPT.is_symlink() and not MARKER.exists(), 'new_attempt2_only')
    engine = module.engine()
    CONTROL.mkdir(mode=0o700, exist_ok=False)
    provenance = dict(schema='R160_FROZEN_PRE_NATIVE_READMISSION_V1', operator=reference(Path(__file__).resolve()),
        cpu=reference(cpu_path), previous={name: dict(path=str(path), sha256=checksum)
            for name, (path, checksum) in PINS.items()}, old_marker=str(OLD_MARKER), new_marker=str(MARKER),
        original_reports_unchanged=True, original_reasons_ignored=False, fresh_full_admission_required=True,
        native_retry=False, initialized=reference(BASE / 'common_initial/INITIALIZED.json'),
        commit=reference(BASE / 'common_initial/COMMIT.json'),
        lifecycle=reference(BASE / 'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json'))
    module.write(CONTROL / 'PROVENANCE.json', provenance)
    original_allocation = bound(dict(path=original['allocation_path'], sha256=original['allocation_sha256']))
    allocation = dict(original_allocation, declared_unix=time.time(),
                      r160_readmission=reference(CONTROL / 'PROVENANCE.json'))
    module.write(CONTROL / 'ALLOCATION.json', allocation)
    config = derive_config(original, reference(CONTROL / 'ALLOCATION.json'), engine)
    module.write(CONTROL / 'GUARD.json', config)
    guard = importlib.import_module('gpu.orch_r125_continual_guard')
    require(Path(guard.__file__).resolve() == SOURCE / 'gpu/orch_r125_continual_guard.py', 'original_guard_location')
    require(guard.validate(CONTROL / 'GUARD.json') == (config, plan), 'original_guard_accepts_exact_config_changes')
    result = dict(status='CPU_PREPARED_NO_GO_NO_GPU', config=reference(CONTROL / 'GUARD.json'),
        receipt_dir=str(ATTEMPT), provenance=reference(CONTROL / 'PROVENANCE.json'),
        required_GO_binding=engine.go_binding(config, plan, sha(CONTROL / 'GUARD.json')),
        initialization={name: provenance[name] for name in ('initialized', 'commit', 'lifecycle')},
        required_GO_readmission_path=str(CONTROL / 'PREPARED_READMISSION.json'), GPU_calls=0)
    module.write(CONTROL / 'PREPARED_READMISSION.json', result)
    return result


@contextmanager
def exclusive():
    lock = os.open(BASE.parent / '.orch_r158_node4_device_6.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not MARKER.is_symlink(), 'new_marker_not_symlink')
        MARKER.mkdir(mode=0o700, exist_ok=False)
        yield
    finally:
        os.close(lock)


def supervise(go_path, go_sha256):
    module = runtime()
    original, plan = validate_old(module)
    prepared = read(CONTROL / 'PREPARED_READMISSION.json')
    provenance = bound(prepared['provenance'])
    require(provenance['operator'] == reference(Path(__file__).resolve()), 'exact_prepared_external_operator')
    verify_cpu(provenance['cpu']['path'])
    bound(provenance['cpu'])
    config = bound(prepared['config'])
    allocation = bound(dict(path=config['allocation_path'], sha256=config['allocation_sha256']))
    require(allocation['r160_readmission'] == prepared['provenance'], 'allocation_binds_readmission')
    original_allocation = bound(dict(path=original['allocation_path'], sha256=original['allocation_sha256']))
    require(allocation == dict(original_allocation, declared_unix=allocation['declared_unix'],
                               r160_readmission=prepared['provenance'])
            and allocation['declared_unix'] <= time.time(), 'original_allocation_only_provenance_updated')
    require(config == derive_config(original, reference(CONTROL / 'ALLOCATION.json'), module.engine()),
            'only_allocation_attempt_unit_changes')
    go = bound(dict(path=str(go_path), sha256=go_sha256))
    require(go.get('readmission') == reference(CONTROL / 'PREPARED_READMISSION.json'), 'Main_bound_readmission')
    engine = module.engine()
    engine.validate(CONTROL / 'GUARD.json', ATTEMPT, go_path, go_sha256)
    module.validate_extra(CONTROL / 'GUARD.json', go_path)
    with exclusive():
        validate_old(module)
        require(not ATTEMPT.exists() and not ATTEMPT.is_symlink(), 'never_reuse_attempt2')
        return engine.supervise(CONTROL / 'GUARD.json', receipt_dir=ATTEMPT,
                                main_go_path=go_path, main_go_sha256=go_sha256)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    preparing = commands.add_parser('prepare')
    preparing.add_argument('--cpu', type=Path, required=True)
    running = commands.add_parser('supervise')
    running.add_argument('--main-go', type=Path, required=True)
    running.add_argument('--main-go-sha256', required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        print(json.dumps(prepare(args.cpu), sort_keys=True))
    else:
        supervise(args.main_go, args.main_go_sha256)


if __name__ == '__main__':
    main()
