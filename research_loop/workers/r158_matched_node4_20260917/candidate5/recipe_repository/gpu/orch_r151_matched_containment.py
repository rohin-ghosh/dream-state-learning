"""CPU-preparable node5 matched supervision; execution requires an external bound Main GO."""

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from types import ModuleType


HOST = '[REDACTED_HOST]'
HOST_SHA256 = hashlib.sha256(HOST.encode()).hexdigest()
BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
DEVICES = {
    0: 'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a',
    3: 'GPU-d23c9369-39cf-51fd-833e-13292f173006',
    4: 'GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d',
}
SCOPE = 'R151_NODE5_MATCHED_INITIALIZE_RUN_0_3_4'
MODULE = 'gpu.orch_r151_matched_containment'
GUARD = 'gpu/orch_r125_continual_guard.py'
ORIGINAL_GUARD_SHA256 = '4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3'
R150_PARENT_GUARD_SHA256 = '25d2a56c860f8e3ca7d479a20f391c13644829d6996c134d9b73b4b17d26c015'
R151_GUARD_SHA256 = 'c1358b5b478b7be8fbfde1beab43f0b7ca60db6ee019b5a7085a81844977bc85'
STAGING_PATCHER = 'gpu/orch_r151_matched_stage.py'
MEMORY_PROBE = 'gpu/orch_r151_memory_probe.py'
EXISTING_LEASE_SHA256 = '12e187a3237d6c167d91c4abaae9e6ef671e096d827c9ed68a662aa465d51049'
CAPSULE_SHA256 = '29e2d77dfe21a6c1b37861f52c00d2eeb858c67b60f054ab6e2d2238cc135c95'
OLD_DEVICES = "DEVICES = {2: 'GPU-d62ba12e-ff08-9e5e-ba35-14c723f6e05b', 6: 'GPU-67a989f7-2660-a76b-40e8-3619b9fa2987'}"
PINNED_SCANNER = {
    'gpu/orch_r111_route_admission.py': 'c79f08d18eb2dd989b13555b90ad289d98937c8662b9c01cc1899d80429228b1',
    'gpu/orch_rich_hot_a100_minor_scan.py': 'f7136608f4b3fca051b3852a006abf86b704dbf1cfe882f6b8c3b43704ec387e',
    'gpu/orch_rich_hot_a100_scan.py': '9902c38ecadeaa06bc02abf184f6a04025a289868f809b63aace5148cd95575e',
    'gpu/orch_r110_admission.py': '91027037bf98aa391afe5d89da9814502da57d6b15ad16574b2a7cdef9976c3f',
    'gpu/orch_math_replication_guard.py': '389521b8a291292c386fd874faa40ff8767b38da8e088985f6f6659e5f971ac2',
    'organism_v6/orch_rich_hot_a100.py': 'aececd1a8e00bca76b658fada7f23d770c87f9ab17bb3be8b1f4c094b556eb38',
}
ALLOCATOR = 'expandable_segments:True'
CGROUP_ROOT = Path('/sys/fs/cgroup')
BOOT_ID = Path('/proc/sys/kernel/random/boot_id')
SYSTEMD_PROPERTIES = (
    'Id', 'LoadState', 'ActiveState', 'SubState', 'InvocationID', 'ControlGroup',
    'MainPID', 'Result', 'ExecMainCode', 'ExecMainStatus', 'DevicePolicy',
    'NoNewPrivileges', 'CapabilityBoundingSet', 'AmbientCapabilities',
    'ProtectControlGroups', 'KillMode', 'User', 'Group',
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_once(path, document):
    path = Path(path)
    temporary = path.with_name(path.name + '.pending')
    with temporary.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path)
    temporary.unlink()
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def fail_receipt(attempt, error, stage, filename='FAILED.json'):
    receipt = dict(status='FAILED', stage=stage, error_type=type(error).__name__,
                   error=str(error), finished_unix=time.time(), no_retry=True)
    try:
        write_once(Path(attempt) / filename, receipt)
    except BaseException as receipt_error:
        receipt['receipt_error'] = type(receipt_error).__name__ + ': ' + str(receipt_error)
    print(json.dumps(receipt, sort_keys=True), file=sys.stderr, flush=True)


def new_unit(receipt_dir):
    return 'orch-r136-native-' + digest(str(canonical(receipt_dir)).encode())[:32]


def render_capsule(original):
    """Pure bytes API: change only the pinned successful capsule's DEVICES binding."""
    require(type(original) is bytes and digest(original) == CAPSULE_SHA256, 'original_capsule_bytes')
    source = original.decode('utf-8')
    require(source.count(OLD_DEVICES) == 1, 'single_capsule_device_binding')
    return source.replace(OLD_DEVICES, 'DEVICES = ' + repr(DEVICES), 1).encode('utf-8')


def render_guard(original):
    """Pure bytes API: Main's exact R151 initializer derivative, not the R150 parent."""
    require(type(original) is bytes and digest(original) == ORIGINAL_GUARD_SHA256, 'original_guard_bytes')
    from gpu.orch_r150_guard_patch import patch_source
    from gpu.orch_r151_matched_stage import patch_guard, revert_guard
    parent = patch_source(original.decode('utf-8')).encode('utf-8')
    require(digest(parent) == R150_PARENT_GUARD_SHA256, 'exact_R150_parent_guard_bytes')
    result = patch_guard(original.decode('utf-8')).encode('utf-8')
    require(revert_guard(result.decode('utf-8')).encode('utf-8') == original, 'exact_R151_guard_reversal')
    require(digest(result) == R151_GUARD_SHA256, 'Main_supplied_final_R151_guard_bytes')
    return result


def verify_guard_derivation(source, source_pins, gate):
    expected = dict(status='PASS', original_guard_sha256=ORIGINAL_GUARD_SHA256,
                    r150_parent_guard_sha256=R150_PARENT_GUARD_SHA256,
                    guard_sha256=source_pins[GUARD], patcher_sha256=source_pins[STAGING_PATCHER],
                    memory_probe_sha256=source_pins[MEMORY_PROBE],
                    initialize_callback='gpu.orch_r151_memory_probe.initial_capacity',
                    original_checks_preserved=True, run_dispatch_unchanged=True)
    require(gate['guard_derivation'] == expected, 'exact_Main_CPU_reviewed_guard_derivation')
    require(expected['guard_sha256'] != R150_PARENT_GUARD_SHA256, 'R150_parent_is_not_R151_final_guard')
    from gpu import orch_r151_matched_stage as staging
    require(Path(staging.__file__).resolve() == source / STAGING_PATCHER, 'bound_staging_patcher_location')
    data = (source / GUARD).read_bytes()
    original = staging.revert_guard(data.decode('utf-8')).encode('utf-8')
    require(render_guard(original) == data, 'exact_fixed_initializer_guard_derivation')


def verify_budget(config, plan):
    budget = read(reference(config, 'lease'))
    require(budget['schema'] == 'R151_EXISTING_NODE5_COHORT_BUDGET_V1'
            and budget['physical_devices'] == [0, 3, 4] and budget['host_sha256'] == HOST_SHA256,
            'new_scope_specific_node5_budget')
    require(budget['lease_extended'] is False and budget['existing_life_wall_changed'] is False
            and budget['safety_margin_seconds'] == 600, 'no_lease_or_existing_life_extension')
    prior_ref = budget['derived_from']
    require(prior_ref['sha256'] == EXISTING_LEASE_SHA256
            and sha(canonical(prior_ref['path'])) == EXISTING_LEASE_SHA256, 'actual_generic_R131_lease_bytes')
    prior = read(prior_ref['path'])
    require(plan['lease_end_unix'] == budget['lease_end_unix'] == prior['lease_end_unix']
            and plan['hard_end_unix'] <= budget['hard_end_unix'] <= prior['hard_end_unix']
            and budget['hard_end_unix'] <= budget['lease_end_unix'] - 600, 'existing_generic_lease_ceiling')


def load_capsule(path):
    data = Path(path).read_bytes()
    expected_binding = 'DEVICES = ' + repr(DEVICES)
    require(data.decode('utf-8').count(expected_binding) == 1, 'new_capsule_device_binding')
    original = data.decode('utf-8').replace(expected_binding, OLD_DEVICES, 1).encode('utf-8')
    require(render_capsule(original) == data, 'unchanged_successful_capsule_functions')
    module = ModuleType('r151_node5_capsule')
    exec(compile(data, str(path), 'exec'), module.__dict__)
    return module


def canonical(path):
    result = Path(path)
    require(result.is_absolute() and result == result.resolve(), 'canonical_absolute_path')
    return result


def reference(config, name):
    path = canonical(config[name + '_path'])
    require(sha(path) == config[name + '_sha256'], 'bound_reference:' + name)
    return path


def source_inventory(source):
    files = {}
    for path in source.rglob('*'):
        require(not path.is_symlink(), 'no_source_symlinks')
        if path.is_file():
            files[str(path.relative_to(source))] = sha(path)
        else:
            require(path.is_dir(), 'ordinary_source_files_only')
    return files


def go_binding(config, plan, config_sha256):
    """Return required Main GO bindings, not a GO or an authorization."""
    return dict(
        requested_scope=SCOPE, config_sha256=config_sha256,
        plan_sha256=config['plan_sha256'], lease_sha256=config['lease_sha256'],
        allocation_sha256=config['allocation_sha256'],
        source_manifest_sha256=config['source_manifest_sha256'],
        cpu_gate_sha256=config['cpu_gate_sha256'], intake_sha256=config['intake_sha256'],
        matched_cohort_sha256=config['matched_cohort_sha256'],
        host_sha256=HOST_SHA256, boot_id=config['boot_id'], allowed_physical=[0, 3, 4],
        physical=plan['physical'], gpu_uuid=plan['gpu_uuid'], phase=config['phase'],
        matched_arm=config['matched_arm'], resume=config['resume'],
        device_containment=config['device_containment'], attempt_dir=config['attempt_dir'],
        hard_end_unix=config['hard_end_unix'],
    )


def validate_go(config, plan, config_sha256, main_go_path, main_go_sha256):
    require(sha(canonical(main_go_path)) == main_go_sha256, 'externally_bound_main_GO_bytes')
    document = read(main_go_path)
    require(document['schema'] == 'R151_MAIN_GO_V1' and document['decision'] == 'GO'
            and document['issuer'] == 'Main', 'explicit_main_GO')
    require(document['binding'] == go_binding(config, plan, config_sha256), 'exact_main_GO_scope')
    require(document['not_before_unix'] <= time.time() < document['expires_unix']
            <= config['hard_end_unix'], 'live_bounded_main_GO')


def validate(config_path, attempt, main_go_path, main_go_sha256):
    config_path, attempt = canonical(config_path), canonical(attempt)
    config = read(config_path)
    require(socket.gethostname() == HOST and config['host_sha256'] == HOST_SHA256, 'exact_node5_host')
    require(BOOT_ID.read_text().strip() == config['boot_id'], 'same_node5_boot')
    require(config['requested_scope'] == SCOPE, 'explicit_requested_scope')
    plan = read(reference(config, 'plan'))
    require(type(plan['physical']) is int and plan['physical'] in DEVICES
            and plan['gpu_uuid'] == DEVICES[plan['physical']], 'only_node5_physical_0_3_4')
    require(config['phase'] in ('initialize', 'run') and type(config['resume']) is bool,
            'explicit_phase_and_resume')
    require(config['matched_arm'] == plan['matched_arm']
            and config['matched_cohort_sha256'] == plan['matched_cohort']['sha256'], 'phase_arm_cohort_binding')
    require(config['phase'] != 'initialize' or
            (config['matched_arm'] == 'parented_learning' and config['resume'] is False), 'fresh_designated_initializer')
    require(plan.get('initialization_validation_schema') == 'R151_MATCHED_INITIAL_CAPACITY_V1',
            'capacity_validated_common_initial_state_required')
    validate_go(config, plan, sha(config_path), main_go_path, main_go_sha256)
    source = canonical(plan['source_root'])
    require(source == Path(__file__).resolve().parents[1], 'supervisor_in_new_frozen_source')
    require(attempt == canonical(config['attempt_dir']), 'explicit_receipt_destination')
    cohort_ref = plan['matched_cohort']
    require(sha(canonical(cohort_ref['path'])) == cohort_ref['sha256'], 'cohort_bytes')
    cohort = read(cohort_ref['path'])
    outputs = [canonical(plan['root']), canonical(cohort['initial_directory']), attempt]
    require(all(not left.is_relative_to(right) and not right.is_relative_to(left)
                for left in outputs for right in [source]), 'source_outputs_disjoint')
    require(all(not left.is_relative_to(right) for left in outputs for right in outputs
                if left != right) and len(set(outputs)) == len(outputs), 'receipts_readouts_initial_disjoint')
    for name in ('plan', 'lease', 'allocation', 'source_manifest', 'cpu_gate', 'intake'):
        path = reference(config, name)
        require(not path.is_relative_to(attempt), 'immutable_inputs_outside_attempt')
    verify_budget(config, plan)
    manifest = read(reference(config, 'source_manifest'))
    require(not reference(config, 'source_manifest').is_relative_to(source), 'manifest_outside_source')
    require(manifest['files'] == source_inventory(source), 'entire_source_manifest_bytes')
    require(config['source_pins'] == {name: value for name, value in manifest['files'].items()
                                    if name.endswith('.py')}, 'full_python_closure')
    for name, expected in PINNED_SCANNER.items():
        require(config['source_pins'].get(name) == expected, 'unchanged_guard_scanner:' + name)
    capsule_path = reference(config, 'capsule')
    require(capsule_path.is_relative_to(source), 'new_capsule_inside_new_source')
    capsule = load_capsule(capsule_path)
    policy = config['device_containment']
    require(set(policy) == {'uid', 'gid', 'minor', 'unit'}
            and type(policy['uid']) is type(policy['gid']) is int and policy['uid'] == policy['gid'] == 2524,
            'known_node5_nonroot_identity')
    require(type(policy['minor']) is int and policy['minor'] == capsule.device_minor(plan['gpu_uuid']),
            'live_kernel_UUID_minor_binding')
    require(policy['unit'] == new_unit(attempt), 'unique_attempt_bound_native_unit')
    require(config['allocator'] == ALLOCATOR, 'expandable_allocator_required')
    gate = read(reference(config, 'cpu_gate'))
    require(gate['status'] == 'PASS' and gate['source_manifest_sha256'] == config['source_manifest_sha256']
            and gate['matched_cohort_sha256'] == config['matched_cohort_sha256'], 'source_bound_CPU_gate')
    verify_guard_derivation(source, config['source_pins'], gate)
    guard = importlib.import_module('gpu.orch_r125_continual_guard')
    require(Path(guard.__file__).resolve() == source / GUARD, 'loaded_guard_from_frozen_source')
    checked_config, checked_plan = guard.validate(config_path)
    require(checked_config == config and checked_plan == plan, 'original_guard_validation_retained')
    require(config['hard_end_unix'] - time.time() > 20, 'time_for_bounded_startup')
    return config, plan, capsule, guard


def clean_environment(source, gpu_uuid=''):
    return dict(PATH='/usr/bin:/bin', HOME=str(BASE), CUDA_VISIBLE_DEVICES=gpu_uuid,
                PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(source), HF_HUB_OFFLINE='1',
                TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                TOKENIZERS_PARALLELISM='false', PYTORCH_CUDA_ALLOC_CONF=ALLOCATOR)


def check_admission(report, config, plan, verified_unix):
    require(report['scanner_euid'] == 0 and report['clear'] is True and not report['blocking_reasons'],
            'fresh_exclusive_admission')
    require(report['gpu']['uuid'] == plan['gpu_uuid'] and report['host_sha256'] == HOST_SHA256
            and report['device_minor'] == config['device_containment']['minor'], 'admission_host_UUID_minor')
    require(0 <= time.time() - verified_unix <= 120, 'admission_120s_freshness')


def systemd_state(unit):
    result = subprocess.run(['/usr/bin/systemctl', 'show', unit + '.service',
                             '--property=' + ','.join(SYSTEMD_PROPERTIES)],
                            env=clean_environment(''), text=True, capture_output=True, timeout=10)
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    require(fields.get('LoadState') == 'not-found' or result.returncode == 0, 'readable_systemd_state')
    require(fields.get('Id') == unit + '.service', 'exact_systemd_unit')
    return fields


def cgroup_path(unit):
    require(re.fullmatch(r'orch-r136-native-[a-f0-9]{32}', unit), 'bound_unit_name')
    return CGROUP_ROOT / 'system.slice' / (unit + '.service')


def inode(path):
    metadata = path.stat()
    return [metadata.st_dev, metadata.st_ino]


def start_ticks(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]


def observe_service(config, started):
    policy = config['device_containment']
    unit = policy['unit']
    path = cgroup_path(unit)
    state = systemd_state(unit)
    require(state['ActiveState'] == 'active' and state['ControlGroup'] == '/system.slice/' + unit + '.service',
            'actual_active_bound_service')
    require(state['InvocationID'] == started['invocation_id']
            and re.fullmatch('[a-f0-9]{32}', state['InvocationID']), 'observed_service_invocation')
    require(int(state['MainPID']) == started['pid'], 'observed_service_main_pid')
    require(start_ticks(started['pid']) == started['start_ticks'], 'observed_service_start_ticks')
    expected = dict(DevicePolicy='strict', NoNewPrivileges='yes', CapabilityBoundingSet='',
                    AmbientCapabilities='', ProtectControlGroups='yes', KillMode='control-group',
                    User='2524', Group='2524')
    require(all(state[key] == value for key, value in expected.items()), 'observed_strict_properties')
    require(BOOT_ID.read_text().strip() == config['boot_id'] == started['boot_id'], 'observed_same_boot')
    require(inode(path) == started['cgroup_inode'], 'observed_same_cgroup_inode')
    require(str(started['pid']) in (path / 'cgroup.procs').read_text().split(), 'actual_cgroup_membership')
    return dict(unit=unit, cgroup='/system.slice/' + unit + '.service', cgroup_inode=inode(path),
                parent_inode=inode(path.parent), invocation_id=state['InvocationID'],
                boot_id=config['boot_id'], pid=started['pid'], start_ticks=started['start_ticks'],
                state=state, checked_unix=time.time())


def verify_service_exit(observed):
    """External read-only proof; return codes never establish cgroup emptiness."""
    require(BOOT_ID.read_text().strip() == observed['boot_id'], 'exit_same_boot')
    path = cgroup_path(observed['unit'])
    require(inode(path.parent) == observed['parent_inode'], 'same_visible_cgroup_parent')
    state = systemd_state(observed['unit'])
    require(state['ActiveState'] in ('inactive', 'failed'), 'service_reached_terminal_state')
    require(state.get('InvocationID') in ('', observed['invocation_id']), 'no_unit_reuse')
    require(state.get('ControlGroup') in ('', observed['cgroup']), 'no_cgroup_rebinding')
    if path.exists():
        require(not path.is_symlink() and inode(path) == observed['cgroup_inode'], 'same_exit_cgroup_inode')
        events = dict(line.split() for line in (path / 'cgroup.events').read_text().splitlines())
        members = {str(child.relative_to(path)): child.read_text().split()
                   for child in [path / 'cgroup.procs', *path.glob('**/cgroup.procs')]}
        require(events['populated'] == '0' and all(not values for values in members.values()),
                'verified_hierarchical_cgroup_empty')
        evidence = dict(kind='present_empty', events=events, members=members)
    else:
        require(path.name not in os.listdir(path.parent), 'verified_cgroup_removed_from_visible_parent')
        evidence = dict(kind='removed_after_bound_observation', parent_inode=inode(path.parent))
    return dict(status='SERVICE_EXIT_VERIFIED', cgroup_empty_verified=True, observed=observed,
                terminal_state=state, evidence=evidence, checked_unix=time.time(),
                readout_cleanup_adopted=False, evaluation_success_claimed=False)


def invocation_arguments(action, config_path, attempt, main_go_path, main_go_sha256):
    return [str(PYTHON), '-B', '-m', MODULE, action, '--config', str(config_path),
            '--receipt-dir', str(attempt), '--main-go', str(main_go_path), '--main-go-sha256', main_go_sha256]


def supervise(config_path, *, receipt_dir, main_go_path, main_go_sha256):
    """One attempt, no retries. Main must supply pre-staged immutable inputs and a bound GO."""
    attempt = Path(receipt_dir)
    process = None
    observed = None
    stage = 'CREATE_ATTEMPT'
    created = False
    try:
        canonical(attempt)
        require(not attempt.is_relative_to(Path(__file__).resolve().parents[1]), 'receipts_outside_source')
        attempt.mkdir(mode=0o700)
        created = True
        write_once(attempt / 'STARTUP.json', dict(status='STARTING', started_unix=time.time(),
                   config_path=str(config_path), main_go_path=str(main_go_path), main_go_sha256=main_go_sha256))
        stage = 'VALIDATE'
        config, plan, capsule, _ = validate(config_path, attempt, main_go_path, main_go_sha256)
        require(os.getuid() == os.getgid() == 2524, 'unprivileged_node5_supervisor')
        unit = config['device_containment']['unit']
        require(systemd_state(unit)['LoadState'] == 'not-found' and not cgroup_path(unit).exists(),
                'never_reuse_service_or_cgroup')
        (attempt / 'DISPATCH_ONCE').mkdir()
        write_once(attempt / 'BINDING.json', go_binding(config, plan, sha(config_path)))
        stage = 'ADMISSION'
        environment = clean_environment(plan['source_root'])
        command = ['sudo', '-n', '/usr/bin/env', '-i',
                   *[key + '=' + value for key, value in environment.items()], str(PYTHON), '-B', '-m',
                   'gpu.orch_r125_continual_guard', 'scan', '--config', str(config_path)]
        scan_started = time.time()
        try:
            with (attempt / 'SCAN.stderr').open('x') as scan_log:
                result = subprocess.run(command, env=environment, text=True, stdout=subprocess.PIPE,
                                        stderr=scan_log, timeout=min(100, int(config['hard_end_unix'] - time.time() - 10)))
        except subprocess.TimeoutExpired as error:
            output = error.stdout or b''
            with (attempt / 'SCAN.stdout').open('xb') as scan_output:
                scan_output.write(output.encode() if isinstance(output, str) else output)
            raise
        with (attempt / 'SCAN.stdout').open('x') as scan_output:
            scan_output.write(result.stdout)
        require(result.returncode == 0, 'privileged_admission_failed')
        report = json.loads(result.stdout)
        write_once(attempt / 'ADMISSION.json', report)
        check_admission(report, config, plan, scan_started)
        write_once(attempt / 'ADMISSION_CLOCK.json', dict(verified_unix=scan_started,
                   finished_unix=time.time(), admission_sha256=sha(attempt / 'ADMISSION.json')))
        validate_go(config, plan, sha(config_path), main_go_path, main_go_sha256)
        stage = 'SERVICE'
        policy = config['device_containment']
        lifetime = int(config['hard_end_unix'] - time.time() - 10)
        require(lifetime > 10, 'remaining_service_wall')
        command = capsule.device_containment_command(plan['physical'], policy['minor'], policy['uid'],
                  policy['gid'], unit, plan['source_root'], ['PYTORCH_CUDA_ALLOC_CONF=' + ALLOCATOR,
                  *invocation_arguments('contained', config_path, attempt, main_go_path, main_go_sha256)], lifetime)
        with (attempt / 'SERVICE.log').open('x') as log:
            process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL, stdout=log,
                                       stderr=subprocess.STDOUT, close_fds=True)
            service_deadline = time.monotonic() + lifetime + 30
            while process.poll() is None:
                require(time.monotonic() < service_deadline, 'bounded_supervisor_service_wait')
                if observed is None and (attempt / 'SERVICE_STARTED.json').exists():
                    observed = observe_service(config, read(attempt / 'SERVICE_STARTED.json'))
                    write_once(attempt / 'SERVICE_OBSERVED.json', observed)
                time.sleep(0.1)
            status = process.wait()
        stage = 'EXIT_PROOF'
        require(observed is not None, 'service_identity_not_observed_no_emptiness_claim')
        lifecycle = verify_service_exit(observed)
        lifecycle['service_returncode'] = status
        lifecycle['binding_sha256'] = sha(attempt / 'BINDING.json')
        write_once(attempt / 'LIFECYCLE.json', lifecycle)
        require(status == 0 and (attempt / 'NATIVE_EXIT.json').exists()
                and read(attempt / 'NATIVE_EXIT.json')['exit_code'] == 0, 'native_failed_preserve_no_retry')
        write_once(attempt / 'EXIT.json', dict(status='COMPLETE', exit_code=0, finished_unix=time.time(),
                   lifecycle_sha256=sha(attempt / 'LIFECYCLE.json'), no_retry=True))
        return lifecycle
    except BaseException as error:
        if created and not (attempt / 'LIFECYCLE.json').exists():
            lifecycle = dict(status='NOT_STARTED' if process is None else 'UNVERIFIED',
                             cgroup_empty_verified=None, observed=observed, no_retry=True,
                             binding_sha256=sha(attempt / 'BINDING.json')
                             if (attempt / 'BINDING.json').exists() else None)
            try:
                if observed is not None:
                    lifecycle = verify_service_exit(observed)
                    lifecycle['binding_sha256'] = sha(attempt / 'BINDING.json')
                write_once(attempt / 'LIFECYCLE.json', lifecycle)
            except BaseException as lifecycle_error:
                fail_receipt(attempt, lifecycle_error, 'EXIT_PROOF', 'LIFECYCLE_FAILED.json')
        fail_receipt(attempt if created else '/nonexistent-r151-receipt-destination', error, stage)
        raise


def contained(config_path, *, receipt_dir, main_go_path, main_go_sha256):
    attempt = Path(receipt_dir)
    process = None
    try:
        config, plan, capsule, guard = validate(config_path, attempt, main_go_path, main_go_sha256)
        containment = capsule.verify_device_containment(config, plan)
        require(os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == ALLOCATOR, 'contained_expandable_allocator')
        write_once(attempt / 'CONTAINMENT_VERIFIED.json', containment)
        unit = config['device_containment']['unit']
        invocation = os.environ.get('INVOCATION_ID')
        if not invocation:
            invocation = systemd_state(unit)['InvocationID']
        started = dict(pid=os.getpid(), start_ticks=start_ticks(os.getpid()),
                       invocation_id=invocation, boot_id=config['boot_id'],
                       cgroup_inode=inode(cgroup_path(unit)), started_unix=time.time())
        write_once(attempt / 'SERVICE_STARTED.json', started)
        deadline = min(time.monotonic() + 10, time.monotonic() + config['hard_end_unix'] - time.time() - 10)
        while not (attempt / 'SERVICE_OBSERVED.json').exists():
            require(time.monotonic() < deadline, 'external_service_observation_timeout')
            time.sleep(0.05)
        observed = read(attempt / 'SERVICE_OBSERVED.json')
        require(observed['invocation_id'] == invocation and observed['cgroup_inode'] == started['cgroup_inode'],
                'external_observation_binding')
        clock = read(attempt / 'ADMISSION_CLOCK.json')
        require(sha(attempt / 'ADMISSION.json') == clock['admission_sha256'], 'admission_receipt_bytes')
        check_admission(read(attempt / 'ADMISSION.json'), config, plan, clock['verified_unix'])
        remaining = int(config['hard_end_unix'] - time.time() - 15)
        require(remaining > 5, 'bounded_native_timeout')
        command = ['/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's',
                   *invocation_arguments('native', config_path, attempt, main_go_path, main_go_sha256)]
        with (attempt / 'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], env=clean_environment(
                       plan['source_root'], plan['gpu_uuid']), stdin=subprocess.PIPE, stdout=log,
                       stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
            ticks = start_ticks(process.pid)
            guard.publish_launch(attempt / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=ticks,
                started_unix=time.time(), admission_verified_unix=clock['verified_unix'],
                admission_sha256=clock['admission_sha256'], guard_sha256=sha(config_path),
                command_sha256=digest(json.dumps(command, sort_keys=True, separators=(',', ':')).encode()),
                plan_sha256=config['plan_sha256'], gpu_uuid=plan['gpu_uuid'], hard_end_unix=plan['hard_end_unix'],
                unit=unit, invocation_id=invocation, cgroup=observed['cgroup'], no_retry=True))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            status = process.wait()
        write_once(attempt / 'NATIVE_EXIT.json', dict(exit_code=status, finished_unix=time.time(),
                   cgroup_empty_verified=None, no_retry=True))
        require(status == 0, 'native_failed_preserve_no_retry')
    except BaseException as error:
        fail_receipt(attempt, error, 'CONTAINED', 'CONTAINED_FAILED.json')
        raise


def native(config_path, *, receipt_dir, main_go_path, main_go_sha256):
    try:
        config, plan, capsule, guard = validate(config_path, receipt_dir, main_go_path, main_go_sha256)
        capsule.verify_device_containment(config, plan)
        require(os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == ALLOCATOR
                and 'PYTORCH_ALLOC_CONF' not in os.environ, 'native_expandable_allocator')
        write_once(Path(receipt_dir) / 'PRE_NATIVE.json', dict(status='ENTERING_GUARD', pid=os.getpid(),
                   checked_unix=time.time(), model_loaded_claimed=False))
        guard.native_entry(config_path)
    except BaseException as error:
        fail_receipt(receipt_dir, error, 'NATIVE', 'NATIVE_FAILED.json')
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('supervise', 'contained', 'native'))
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--receipt-dir', type=Path, required=True)
    parser.add_argument('--main-go', type=Path, required=True)
    parser.add_argument('--main-go-sha256', required=True)
    args = parser.parse_args()
    globals()[args.action](args.config, receipt_dir=args.receipt_dir, main_go_path=args.main_go,
                           main_go_sha256=args.main_go_sha256)


if __name__ == '__main__':
    main()
