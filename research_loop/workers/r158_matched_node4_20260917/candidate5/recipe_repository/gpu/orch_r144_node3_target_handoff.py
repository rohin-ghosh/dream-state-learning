"""Target-only handoffs for six inventoried healthy node3 child topologies."""

import argparse
from copy import deepcopy
import fcntl
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid


API_SHA = 'f128becb34d95b6875e4283baa49b3504e2c6c589e67b93e858e07c98f593e60'
PATCH_SHA = '3036dfd7b749f76d328f05330ef3b7afd664a0da599e80fc57d3e5d3e9876c1b'
HELPER_SHA = '8070e8047dd7d795df727204d2e79a2b2f7d906d88c095ac07777a8e566ed9a9'
POLICY = 'R144_SPECIAL_TOKEN_TARGET_EXCLUSION_V1'
BASE = Path('/localhome/local-rohing')
STAGED_SOURCE_ROOT = BASE / 'orch_r144_node3_targets_20260916t1515z_2'
PYTHON = BASE / 'v2/venv/bin/python'
GUARD_MODULE = 'gpu.orch_r125_continual_guard'
PROGRAMMES_MODULE = 'gpu.orch_r133_node3_programmes'
CREATIVE_MODULE = 'gpu.orch_r133_node3_handoff'
OTHER_ROOTS = {
    0: ('orch_r133_support_free_20260916_attempt1', 'source1'),
    1: ('orch_r133_creative_reread_20260916_attempt1', 'OP/source2'),
    2: ('orch_r133_brain_free_20260916_attempt1', 'source1'),
}
OTHER_UUIDS = {
    0: 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939',
    1: 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821',
    2: 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def api():
    import hashlib
    path = Path(__file__).with_name('BOUNDARY_API.py')
    require(hashlib.sha256(path.read_bytes()).hexdigest() == API_SHA, 'immutable_boundary_API')
    return load_file('r144_pinned_boundary_api', path)


def plan_delta(old, new):
    normalized = deepcopy(new)
    require(new['source_root'] != old['source_root'], 'new_source_namespace')
    normalized['source_root'] = old['source_root']
    if old.get('startup_context'):
        relative = Path(old['startup_context']['path']).relative_to(old['source_root'])
        require(new['startup_context']['path'] == str(Path(new['source_root']) / relative), 'startup_relocation_only')
        normalized['startup_context']['path'] = old['startup_context']['path']
    require(normalized == old, 'all_training_and_plan_semantics_unchanged')


def guard_delta(old, new):
    normalized = deepcopy(new)
    changes = {'plan_path', 'plan_sha256', 'source_pins', 'attempt_dir', 'resume',
               'allocation_path', 'allocation_sha256'}
    for key in changes:
        normalized[key] = old[key]
    require(new['resume'] is True and new['attempt_dir'] != old['attempt_dir'], 'fresh_resume_attempt')
    if 'device_containment' in old:
        require(new['device_containment']['unit'] != old['device_containment']['unit'], 'fresh_unique_unit')
        normalized['device_containment']['unit'] = old['device_containment']['unit']
    else:
        policy = normalized.pop('device_containment')
        require(set(policy) == {'uid', 'gid', 'minor', 'unit'}
                and type(policy['uid']) is int and policy['uid'] > 0
                and type(policy['gid']) is int and policy['gid'] > 0
                and type(policy['minor']) is int and policy['minor'] in (0, 2)
                and re.fullmatch(r'orch-r144-native-[0-9a-f]{32}', policy['unit']), 'strict_direct_lane_policy_only')
    require(normalized == old, 'only_authorized_guard_delta')


def lane_scope(plan):
    physical = plan['physical']
    require(type(physical) is int and physical in (0, 1, 2, 3, 4, 7), 'healthy_six_only_exclude5_6')
    if physical in (3, 4, 7):
        return api().family_scope(plan)
    namespace, source_suffix = OTHER_ROOTS[physical]
    require(plan['gpu_uuid'] == OTHER_UUIDS[physical] and plan['root'] == str(BASE / namespace / 'run1')
            and plan['source_root'] == str(BASE / namespace / source_suffix), 'exact_inventoried_legacy_roots')
    require(not plan.get('preupdate_recovery') and not plan.get('authorized_wall_extension'), 'no_recovery_or_wall_change')
    return physical


def old_modules(config_path):
    helper = api()
    config = helper.read(config_path)
    plan = helper.read(config['plan_path'])
    lane_scope(plan)
    if plan['physical'] in (3, 4, 7):
        return helper.originals(config_path)
    require(socket.gethostname() == helper.HOST, 'exact_node3_host')
    source = Path(plan['source_root'])
    sys.path.insert(0, str(source))
    modules = {}
    for label, name in (('guard', GUARD_MODULE), ('native', 'gpu.orch_r125_continual_native'),
                        ('saved', 'gpu.orch_r131_saved_boundary_handoff')):
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve() == source / (name.replace('.', '/') + '.py'), 'original_module_identity')
        modules[label] = module
    modules['guard'].validate(config_path)
    return config, plan, SimpleNamespace(**modules)


def old_processes(pid, config_path, config, plan):
    helper = api()
    physical = lane_scope(plan)
    if physical in (3, 4, 7):
        return helper.process_pair(pid, config_path, config, plan)
    actor = helper.process_record(pid)
    timer = helper.process_record(actor['parent'])
    supervisor = helper.process_record(timer['parent'])
    prefix = [str(PYTHON), '-B', '-m']
    require(actor['argv'] == prefix + [GUARD_MODULE, 'native', '--config', str(config_path)], 'original_native_argv')
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and len(timer['argv']) == 11 and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3])
            and timer['argv'][4:] == actor['argv'], 'original_timeout_argv')
    wrapper, action = (CREATIVE_MODULE, 'contained-native') if physical == 1 else (GUARD_MODULE, 'supervise')
    require(supervisor['argv'] == prefix + [wrapper, action, '--config', str(config_path)], 'exact_legacy_supervisor')
    require(actor['group'] == timer['group'] == timer['pid'] and supervisor['group'] == supervisor['pid']
            and supervisor['parent'] == 1, 'exact_owned_groups')
    for process in (actor, timer, supervisor):
        require(process['uid'] == os.getuid() and process['cwd'] == plan['source_root'], 'same_owned_source')
    require(actor['cvd'] == timer['cvd'] == [plan['gpu_uuid']], 'native_timeout_uuid')
    if physical == 1:
        require(supervisor['cvd'] == [plan['gpu_uuid']], 'creative_contained_supervisor_uuid')
        cgroup = '0::/system.slice/' + config['device_containment']['unit'] + '.service'
    else:
        require('device_containment' not in config and supervisor['cvd'] == [''], 'original_direct_CPU_supervisor')
        cgroup = actor['cgroup']
        require(re.fullmatch(r'0::/user.slice/user-2524.slice/session-[0-9]+.scope', cgroup), 'original_user_session')
    require(actor['cgroup'] == timer['cgroup'] == supervisor['cgroup'] == cgroup, 'same_original_cgroup')
    launch = helper.read(Path(config['attempt_dir']) / 'LAUNCH.json')
    require(launch['pid'] == timer['pid'] and launch['parent_start_ticks'] == timer['start_ticks']
            and launch['guard_sha256'] == helper.sha(config_path) and launch['plan_sha256'] == config['plan_sha256'],
            'original_launch_identity')
    return dict(actor=actor, timer=timer, supervisor=supervisor)


def direct_minor(plan):
    require(type(plan['physical']) is int and plan['physical'] in (0, 2)
            and plan['gpu_uuid'] == OTHER_UUIDS[plan['physical']], 'explicit_direct_0_2_uuid')
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == plan['gpu_uuid']:
            matches.append(int(fields['Device Minor'].strip()))
    require(matches == [plan['physical']], 'unchanged_inventory_actual_minor')
    metadata = Path('/dev/nvidia' + str(matches[0])).lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
            and os.minor(metadata.st_rdev) == matches[0], 'actual_GPU_character_device')
    return matches[0]


def direct_command(plan, policy, command, lifetime):
    require(type(plan['physical']) is int and plan['physical'] in (0, 2)
            and plan['gpu_uuid'] == OTHER_UUIDS[plan['physical']], 'explicit_direct_0_2_uuid')
    require(set(policy) == {'minor', 'uid', 'gid', 'unit'} and type(policy['minor']) is int
            and policy['minor'] == plan['physical'] and type(policy['uid']) is int and policy['uid'] > 0
            and type(policy['gid']) is int and policy['gid'] > 0
            and re.fullmatch(r'orch-r144-native-[0-9a-f]{32}', policy['unit']), 'exact_strict_direct_policy')
    require(type(lifetime) is int and lifetime > 0, 'bounded_service_lifetime')
    source = Path(plan['source_root'])
    require(source.is_absolute() and '..' not in source.parts, 'canonical_source')
    properties = dict(User=str(policy['uid']), Group=str(policy['gid']), NoNewPrivileges='yes',
        DevicePolicy='strict', CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes',
        RuntimeMaxSec=str(lifetime), TimeoutStopSec='5', KillMode='control-group', WorkingDirectory=str(source))
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
               f"/dev/nvidia{policy['minor']} rw", '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + policy['unit'],
        *['--property=' + key + '=' + value for key, value in properties.items()], '--property=DeviceAllow=',
        *['--property=DeviceAllow=' + device for device in devices], '/usr/bin/env', '-i',
        'PATH=/usr/bin:/bin', 'HOME=' + str(BASE), 'CUDA_VISIBLE_DEVICES=' + plan['gpu_uuid'],
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(source), 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
        'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1', 'TOKENIZERS_PARALLELISM=false', *command]


def contained_command(plan, config, original, config_path, lifetime):
    if plan['physical'] in (0, 2):
        payload = [str(PYTHON), '-B', str(Path(__file__).resolve()), '--action', 'contained', '--output', str(config_path.parent)]
        return direct_command(plan, config['device_containment'], payload, lifetime)
    wrapper = CREATIVE_MODULE if plan['physical'] == 1 else PROGRAMMES_MODULE
    payload = [str(PYTHON), '-B', '-m', wrapper, 'contained-native', '--config', str(config_path)]
    if plan['physical'] == 1:
        policy = config['device_containment']
        return original.programmes.device_containment_command(1, policy['minor'], policy['uid'], policy['gid'],
            policy['unit'], plan['source_root'], payload, lifetime)
    return original.programmes.containment_command(plan, config['device_containment'], payload, lifetime)


def verify_source(binding, old_config, old_plan, new_config, new_plan):
    helper = api()
    physical = lane_scope(old_plan)
    require(Path(new_plan['source_root']) == STAGED_SOURCE_ROOT / ('physical' + str(physical)) / 'source',
            'exact_inventoried_new_source')
    plan_delta(old_plan, new_plan)
    guard_delta(old_config, new_config)
    original = Path(old_plan['source_root'])
    destination = Path(new_plan['source_root'])
    patch_path = Path(__file__).with_name('TARGET_PATCH.py')
    require(helper.sha(patch_path) == PATCH_SHA, 'Main_exact_patch_utility')
    patcher = load_file('r144_main_pinned_patch', patch_path)
    native = 'gpu/orch_r125_continual_native.py'
    targets = 'gpu/orch_r144_sleep_targets.py'
    expected = dict(old_config['source_pins'])
    require(targets not in expected, 'never_repatch')
    require((destination / native).read_text() == patcher.patch_source((original / native).read_text()),
            'exact_target_only_native_bytes')
    require(helper.sha(destination / targets) == HELPER_SHA, 'Main_exact_runtime_policy')
    expected[native], expected[targets] = helper.sha(destination / native), HELPER_SHA
    require(new_config['source_pins'] == expected, 'only_native_and_helper_source_delta')
    allocation = helper.read(new_config['allocation_path'])
    original_allocation = helper.read(old_config['allocation_path'])
    require(allocation == dict(original_allocation, plan_sha256=new_config['plan_sha256']),
            'allocation_binding_only_no_lease_or_recipe_change')
    require(helper.sha(binding) == helper.read(Path(binding).parent / 'STAGED_SOURCE.json')['guard_sha256'],
            'source_stage_guard_binding')


def environment(source):
    return dict(os.environ, PYTHONPATH=source, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')


def new_modules(config_path):
    helper = api()
    config = helper.read(config_path)
    plan = helper.read(config['plan_path'])
    source = Path(plan['source_root'])
    modules = {}
    names = [('guard', GUARD_MODULE), ('native', 'gpu.orch_r125_continual_native')]
    if plan['physical'] not in (0, 2):
        names.append(('programmes', CREATIVE_MODULE if plan['physical'] == 1 else PROGRAMMES_MODULE))
    for label, name in names:
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve() == source / (name.replace('.', '/') + '.py'),
                'new_source_module_identity')
        modules[label] = module
    modules['guard'].validate(config_path)
    return config, plan, SimpleNamespace(**modules)


def validate_new(config_path):
    helper = api()
    config, plan, modules = new_modules(config_path)
    command = contained_command(plan, config, modules, config_path, 60)
    actual = helper.allocator_command(command)
    return dict(status='PASS', guard_sha256=helper.sha(config_path), source_root=plan['source_root'],
                plan_sha256=helper.sha(config['plan_path']), dry_command=actual, no_GPU_launch=True)


def validate_fresh(config_path, source):
    command = [str(PYTHON), '-B', str(Path(__file__).resolve()), '--action', 'validate', '--output', str(config_path)]
    return json.loads(subprocess.check_output(command, text=True, timeout=90, cwd=source, env=environment(source)))


def stage(physical, output, cpu_path):
    helper = api()
    require(type(physical) is int and physical in (0, 1, 2, 3, 4, 7), 'healthy_six_only_exclude5_6')
    output = helper.regular(output)
    require(output.is_relative_to(BASE) and not output.exists(), 'unique_operator_control')
    cpu = helper.read(cpu_path)
    require(cpu['status'] == 'PASS' and cpu['operator_sha256'] == helper.sha(__file__)
            and cpu['api_sha256'] == API_SHA and cpu['patch_sha256'] == PATCH_SHA
            and cpu['helper_sha256'] == HELPER_SHA, 'tested_exact_operator_and_Main_patch')
    inventory = helper.read(STAGED_SOURCE_ROOT / 'INVENTORY.json')
    lane = next(row for row in inventory['lanes'] if row['physical'] == physical)
    require(lane['live'] is True, 'healthy_lane_only')
    old_config, old_plan, original = old_modules(lane['guard_path'])
    require(helper.sha(lane['guard_path']) == lane['guard_sha256'], 'inventory_guard_unchanged')
    original.guard.validate(lane['guard_path'])
    processes = old_processes(lane['processes']['actor']['pid'], lane['guard_path'], old_config, old_plan)
    require(all(processes[name]['pid'] == lane['processes'][name]['pid']
                and processes[name]['start_ticks'] == lane['processes'][name]['start_ticks']
                and processes[name]['cgroup'] == lane['processes'][name]['cgroup'] for name in processes),
            'inventoried_topology_unchanged')
    source_stage = STAGED_SOURCE_ROOT / ('physical' + str(physical))
    binding = source_stage / 'PROPOSED_GUARD.json'
    staged = helper.read(source_stage / 'STAGED_SOURCE.json')
    require(helper.sha(binding) == staged['guard_sha256'], 'exact_staged_guard')
    proposed = helper.read(binding)
    output.mkdir()
    allocation = dict(helper.read(old_config['allocation_path']), plan_sha256=proposed['plan_sha256'])
    helper.write(output / 'ALLOCATION.json', allocation)
    if physical in (0, 2):
        new_config = helper.proposed_guard(old_config, output / 'runtime')
        new_config['device_containment'] = dict(uid=os.getuid(), gid=os.getgid(), minor=direct_minor(old_plan),
            unit='orch-r144-native-' + uuid.uuid4().hex)
    else:
        new_config = helper.resume_config(old_config, output / 'runtime')
        if physical == 1:
            new_config['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    new_config.update(attempt_dir=str(output), plan_path=proposed['plan_path'], plan_sha256=proposed['plan_sha256'],
        source_pins=proposed['source_pins'], allocation_path=str(output / 'ALLOCATION.json'),
        allocation_sha256=helper.sha(output / 'ALLOCATION.json'))
    helper.write(output / 'GUARD.json', new_config)
    new_plan = helper.read(new_config['plan_path'])
    verify_source(binding, old_config, old_plan, new_config, new_plan)
    validation = validate_fresh(output / 'GUARD.json', new_plan['source_root'])
    require(validation['status'] == 'PASS', 'CPU_new_frozen_guard_and_wrapper')
    helper.write(output / 'VALIDATED_NEW_SOURCE.json', validation)
    candidates = sorted(path for path in (Path(old_plan['root']) / 'stream/records').glob('*.json')
                        if re.fullmatch(r'\d{20}\.json', path.name))
    for path in reversed(candidates):
        record = helper.read(path)
        if record['kind'] != 'SLEEP_COMPLETE':
            continue
        require(record['sha256'] == helper.digest({key: value for key, value in record.items() if key != 'sha256'}),
                'historical_probe_record_hash')
        envelope = record['document']['resume_state']
        saved = dict(path=str(path), state=envelope['state'], state_sha256=envelope['sha256'],
                     cycle=record['document']['cycle'])
        probe = saved_evidence(old_plan, saved, original)
        helper.write(output / 'CPU_SAVED_PROTOCOL.json', dict(evidence=probe, historical_only=True,
            current_clean_boundary_inferred=False, signals_sent=0, observed_unix=time.time()))
        break
    else:
        raise ValueError('prior_saved_protocol_required_for_staging')
    request = dict(physical=physical, policy=POLICY, old_config=lane['guard_path'],
        old_config_sha256=lane['guard_sha256'], new_config=str(output / 'GUARD.json'),
        new_config_sha256=helper.sha(output / 'GUARD.json'), processes=processes,
        old_plan_sha256=old_config['plan_sha256'], plan_sha256=new_config['plan_sha256'],
        old_source=old_plan['source_root'], new_source=new_plan['source_root'], source_binding=str(binding),
        cpu_path=str(cpu_path), cpu_sha256=helper.sha(cpu_path), operator_path=str(Path(__file__).resolve()),
        operator_sha256=helper.sha(__file__), staged_unix=time.time(), signals_sent=0)
    helper.write(output / 'STAGED.json', request)
    return request


def supervise(output):
    helper = api()
    request = helper.read(output / 'STAGED.json')
    require(helper.sha(__file__) == request['operator_sha256']
            and helper.sha(output / 'GUARD.json') == request['new_config_sha256'], 'bound_dispatch_operator')
    config, plan, original = new_modules(output / 'GUARD.json')
    require(helper.read(output / 'RETIRED.json')['status'] == 'EXACT_OLD_PROCESSES_EXITED', 'exact_retirement_required')
    (output / 'DISPATCH_ONCE').mkdir()
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + plan['source_root'], str(PYTHON), '-B', '-m', GUARD_MODULE,
        'scan', '--config', str(output / 'GUARD.json')]
    report = json.loads(subprocess.check_output(command, text=True, timeout=90, cwd=plan['source_root']))
    helper.write(output / 'ADMISSION.json', report)
    helper.admission(report, plan)
    minor = direct_minor(plan) if plan['physical'] in (0, 2) else original.programmes.device_minor(plan['gpu_uuid'])
    require(minor == config['device_containment']['minor'],
            'actual_minor_unchanged_before_dispatch')
    helper.write(output / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    baseline = contained_command(plan, config, original, output / 'GUARD.json', max(1, int(plan['hard_end_unix'] - time.time())))
    command = helper.allocator_command(baseline)
    helper.write(output / 'CONTAINED_COMMAND.json', dict(command=command, original_without_allocator=baseline,
        started_unix=time.time(), original_verify_containment_and_native=True))
    result = subprocess.run(command, check=False, cwd=plan['source_root'])
    helper.write(output / 'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
    require(result.returncode == 0, 'original_contained_service_failed_no_retry')


def contained(output):
    helper = api()
    request = helper.read(output / 'STAGED.json')
    require(helper.sha(__file__) == request['operator_sha256']
            and helper.sha(output / 'GUARD.json') == request['new_config_sha256'], 'bound_contained_operator')
    config, plan, original = new_modules(output / 'GUARD.json')
    require(socket.gethostname() == helper.HOST and plan['physical'] in (0, 2), 'own_direct_node3_only')
    policy = config['device_containment']
    require(os.getuid() == policy['uid'] > 0 and os.getgid() == policy['gid'] > 0, 'nonroot_service')
    require(Path('/proc/self/cgroup').read_text().strip() == '0::/system.slice/' + policy['unit'] + '.service',
            'exact_contained_service')
    require(direct_minor(plan) == policy['minor'], 'unchanged_actual_minor')
    for path in Path('/proc/self/fd').iterdir():
        try:
            require(not os.readlink(path).startswith('/dev/nvidia'), 'no_inherited_GPU_descriptors')
        except FileNotFoundError:
            pass
    denied = []
    for minor in range(8):
        if minor == policy['minor']:
            continue
        try:
            descriptor = os.open('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            denied.append(minor)
        else:
            os.close(descriptor)
            raise ValueError('foreign_GPU_not_denied')
    require(denied == [minor for minor in range(8) if minor != policy['minor']], 'all_seven_foreign_denials')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid']
            and os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == 'expandable_segments:True', 'actual_GPU_allocator_environment')
    helper.write(output / 'CONTAINMENT_VERIFIED.json', dict(policy=policy, denied_foreign_minors=denied,
        checked_unix=time.time(), pid=os.getpid()))
    report = helper.read(output / 'ADMISSION.json')
    helper.admission(report, plan)
    admitted = helper.read(output / 'ADMISSION_TIME.json')['verified_unix']
    require(0 <= time.time() - admitted < 100, 'fresh_admission_inside_containment')
    remaining = int(plan['hard_end_unix'] - time.time() - 10)
    require(remaining > 10, 'bounded_native_lifetime')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's', str(PYTHON),
               '-B', '-m', GUARD_MODULE, 'native', '--config', str(output / 'GUARD.json')]
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    process = None
    try:
        with (output / 'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            publish_launch(output / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=ticks,
                started_unix=time.time(), admission_verified_unix=admitted,
                admission_sha256=helper.sha(output / 'ADMISSION.json'), guard_sha256=helper.sha(output / 'GUARD.json'),
                command_sha256=helper.digest(command), plan_sha256=config['plan_sha256'], gpu_uuid=plan['gpu_uuid'],
                hard_end_unix=plan['hard_end_unix'], no_retry=True,
                containment_sha256=helper.sha(output / 'CONTAINMENT_VERIFIED.json')))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            status = process.wait()
        helper.write(output / 'EXIT.json', dict(exit_code=status, finished_unix=time.time(), no_retry=True))
        require(status == 0, 'native_failed_preserve_no_retry')
    except BaseException:
        reap_owned_child(process)
        raise


def monitor(output, saved, unlock):
    helper = api()
    request = helper.read(output / 'STAGED.json')
    config = helper.read(output / 'GUARD.json')
    plan = helper.read(config['plan_path'])
    deadline = time.monotonic() + 1200
    old_head = Path(saved['record_path']).name
    loaded, target = None, None
    while time.monotonic() < deadline:
        require(not any((output / name).exists() for name in ('SUPERVISOR_FAILED.json', 'EXIT.json', 'SERVICE_EXIT.json')),
                'successor_failed_preserve_evidence')
        for path in sorted((Path(plan['root']) / 'stream/records').glob('*.json')):
            if not re.fullmatch(r'\d{20}\.json', path.name) or path.name <= old_head:
                continue
            record = helper.read(path)
            document = record['document']
            require(record['sha256'] == helper.digest({key: value for key, value in record.items() if key != 'sha256'}),
                    'new_journal_receipt_hash')
            if record['kind'] == 'LOADED' and loaded is None:
                require(document['resume'] is True and document['optimizer_steps'] == saved['optimizer_steps']
                        and document['adapter_sha256'] == saved['adapter_state_sha256'], 'exact_saved_LOADED')
                actor = helper.identity(document['pid'])
                require(actor['argv'][-1] == str(output / 'GUARD.json') and helper.ALLOCATOR in actor['environment']
                        and actor['cwd'] == plan['source_root'], 'new_source_actual_native_allocator')
                proof = helper.read(output / 'CONTAINMENT_VERIFIED.json')
                denied = proof.get('denied_foreign_minors')
                if denied is None:
                    denied = [int(name.removeprefix('nvidia')) for name in proof['denied_devices']]
                require(sorted(denied) == [minor for minor in range(8) if minor != config['device_containment']['minor']]
                        and proof['policy'] == config['device_containment'],
                        'all_seven_original_foreign_denials')
                launch = helper.read(output / 'LAUNCH.json')
                require(actor['parent'] == launch['pid'] and launch['guard_sha256'] == helper.sha(output / 'GUARD.json'),
                        'new_native_launch_binding')
                loaded = dict(record_path=str(path), record_sha256=helper.sha(path), actor=actor,
                    optimizer_steps=document['optimizer_steps'], adapter_state_sha256=document['adapter_sha256'],
                    policy=POLICY, effective_next_cycle=saved['cycle'] + 1, observed_unix=time.time())
                helper.write(output / 'LOADED_RECEIPT.json', loaded)
                unlock()
            if loaded and record['kind'] == 'TARGET_ELIGIBILITY' and target is None:
                require(document['runtime_policy'] == POLICY and document['raw_modified'] is False,
                        'runtime_policy_and_raw_preservation_receipt')
                target = dict(record_path=str(path), record_sha256=helper.sha(path), document=document,
                              observed_unix=time.time(), effective_cycle=saved['cycle'] + 1)
                helper.write(output / 'TARGET_POLICY_RECEIPT.json', target)
            if loaded and target and record['kind'] == 'SLEEP_COMPLETE' and document['cycle'] == saved['cycle'] + 1:
                require(document['status'] == 'COMPLETE', 'new_sleep_complete')
                result = dict(status='TARGET_POLICY_NEW_SLEEP_COMPLETE', physical=request['physical'],
                    old_cycle=saved['cycle'], new_cycle=document['cycle'], record_path=str(path),
                    record_sha256=helper.sha(path), loaded_sha256=helper.sha(output / 'LOADED_RECEIPT.json'),
                    policy_receipt_sha256=helper.sha(output / 'TARGET_POLICY_RECEIPT.json'), observed_unix=time.time())
                helper.write(output / 'NEW_SLEEP_RECEIPT.json', result)
                return result
        time.sleep(2)
    helper.write(output / 'MONITOR_TIMEOUT.json', dict(loaded=loaded is not None, policy_observed=target is not None,
        observed_unix=time.time(), child_stopped=False))
    return dict(status='BOUNDED_OBSERVATION_EXPIRED_NO_SIGNAL')


def claim_boundary(lock):
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return False
    return True


def verify_legacy_state(plan, state, checkpoint):
    require(type(plan['physical']) is int and plan['physical'] in (0, 2), 'legacy_0_2_only')
    require(plan['seed'] == 0 and plan.get('presleep_variant') is None
            and 'experiment' not in state and 'experiment' not in checkpoint, 'exact_pre_experiment_protocol')
    require(state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
            and state['sleep_receipts'] and state['sleep_receipts'][-1]['status'] == 'COMPLETE', 'legacy_clean_saved_frontier')
    for key in ('context_limit', 'segment_tokens', 'segments_per_sleep'):
        require(state[key] == plan[key], 'legacy_unchanged_schedule:' + key)
    require(state['deadline_unix'] == plan['hard_end_unix'], 'legacy_original_wall')
    require(state['history']['system_prompt'] == plan['system_prompt']
            and state['history']['birth_prompt'] == plan['birth_prompt'], 'legacy_exact_history_prompts')
    require(state['presentation'] == dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
            birth_prompt=plan['birth_prompt']), 'legacy_exact_presentation')


def saved_evidence(plan, saved, original):
    helper = api()
    if plan['physical'] not in (0, 2):
        return helper.saved_evidence(plan, saved, original)
    lane_scope(plan)
    require(helper.sha(original.native.__file__) == '7626d13974a78c713b9e966093e285e1e8a4f194301dd8b69ec68cfcae656526',
            'exact_inventoried_legacy_native')
    original.native.validate_plan(plan)
    require(saved is not None, 'clean_saved_boundary_required')
    stream = original.native.ContinualStream.restore(dict(state=saved['state'], sha256=saved['state_sha256']),
        expected_sha256=saved['state_sha256'])
    commit = Path(plan['root']) / 'checkpoints' / f"sleep_{saved['cycle']:06d}" / 'COMMIT.json'
    checkpoint = helper.read(commit)
    verify_legacy_state(plan, saved['state'], checkpoint)
    original.native.NativeChild.verify_checkpoint(checkpoint)
    require(helper.digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256
            and stream.deadline_unix == plan['hard_end_unix'], 'legacy_exact_adapter_AdamW_RNG_history_carry_wall')
    return dict(record_path=saved['path'], record_sha256=helper.sha(saved['path']), state_sha256=saved['state_sha256'],
        checkpoint_path=str(commit), checkpoint_sha256=helper.sha(commit), optimizer_steps=checkpoint['optimizer_steps'],
        adapter_state_sha256=checkpoint['adapter_state_sha256'], bundle_sha256=checkpoint['checkpoint_sha256'],
        cycle=saved['cycle'], protocol='EXACT_PINNED_PRE_EXPERIMENT_0_2')


def readmission_guard(config, plan, output):
    result = deepcopy(config)
    require(str(output) != config['attempt_dir'] and result['resume'] is True, 'new_resume_attempt_only')
    result['attempt_dir'] = str(output)
    prefix = 'orch-r144-native-' if plan['physical'] in (0, 2) else (
        'orch-r136-native-' if plan['physical'] == 1 else 'orch-r133-node3-')
    result['device_containment']['unit'] = prefix + uuid.uuid4().hex
    normalized = deepcopy(result)
    normalized['attempt_dir'] = config['attempt_dir']
    normalized['device_containment']['unit'] = config['device_containment']['unit']
    require(normalized == config, 'readmission_no_source_plan_policy_change')
    return result


def readmit(prior, output, cpu_path):
    helper = api()
    prior, output, cpu_path = map(helper.regular, (prior, output, cpu_path))
    helper.admission_retry_eligible(prior)
    require(output.parent == BASE and output.name.startswith('orch_r144_node3_target_') and not output.exists(),
            'unique_node3_readmission_control')
    previous = helper.read(prior / 'STAGED.json')
    require(helper.sha(prior / 'GUARD.json') == previous['new_config_sha256']
            and helper.sha(previous['old_config']) == previous['old_config_sha256'], 'prior_staged_bindings')
    old_config, old_plan, original = old_modules(previous['old_config'])
    config = helper.read(prior / 'GUARD.json')
    plan = helper.read(config['plan_path'])
    cpu = helper.read(cpu_path)
    require(cpu['status'] == 'PASS' and cpu['operator_sha256'] == helper.sha(__file__)
            and cpu['api_sha256'] == API_SHA and cpu['patch_sha256'] == PATCH_SHA
            and cpu['helper_sha256'] == HELPER_SHA, 'readmission_tested_exact_operator')
    lock = os.open(BASE / 'orch_r142_allocator_ovx2_ROLLOUT.lock', os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        require(claim_boundary(lock), 'other_handoff_owns_lock_no_dispatch')
        saved = original.saved.sleep_boundary(old_plan['root'])
        boundary = helper.read(prior / 'BOUNDARY.json')
        require(saved is not None and saved['state_sha256'] == boundary['state_sha256']
                and helper.sha(saved['path']) == boundary['record_sha256'], 'unchanged_retired_boundary_no_pending_work')
        evidence = saved_evidence(old_plan, saved, original)
        require(all(boundary[key] == value for key, value in evidence.items()), 'same_preserved_bundle')
        module = importlib.import_module('gpu.orch_r125_stream_journal')
        with module.StreamJournal(Path(old_plan['root']) / 'stream', create=False) as journal:
            require(journal.latest_checkpoint()['expected_sha256'] == saved['state_sha256'], 'unowned_exact_original_stream')
        proposed = readmission_guard(config, plan, output)
        output.mkdir()
        helper.write(output / 'GUARD.json', proposed)
        verify_source(previous['source_binding'], old_config, old_plan, proposed, plan)
        validation = validate_fresh(output / 'GUARD.json', plan['source_root'])
        helper.write(output / 'VALIDATED_NEW_SOURCE.json', validation)
        request = dict(previous, new_config=str(output / 'GUARD.json'), new_config_sha256=helper.sha(output / 'GUARD.json'),
            operator_path=str(Path(__file__).resolve()), operator_sha256=helper.sha(__file__),
            cpu_path=str(cpu_path), cpu_sha256=helper.sha(cpu_path), stage_native_alive=False,
            prior_attempt=str(prior), prior_denial_sha256=helper.sha(prior / 'ADMISSION.json'), staged_unix=time.time())
        helper.write(output / 'STAGED.json', request)
        helper.write(output / 'BOUNDARY.json', boundary)
        helper.write(output / 'RETIRED.json', helper.read(prior / 'RETIRED.json'))
        helper.write(output / 'READMISSION_PROVENANCE.json', dict(prior=str(prior),
            prior_denial_sha256=helper.sha(prior / 'ADMISSION.json'), retirement_sha256=helper.sha(prior / 'RETIRED.json'),
            no_additional_signals=True, no_native_previously_dispatched=True, no_policy_waivers=True,
            original_full_chain_and_bundle_verified=True, observed_unix=time.time()))
        command = [str(PYTHON), '-B', request['operator_path'], '--action', 'supervise', '--output', str(output)]
        with (output / 'SUPERVISOR.log').open('x') as log:
            successor = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=environment(plan['source_root']))
        helper.write(output / 'DISPATCHED.json', dict(supervisor_pid=successor.pid, command=command, dispatched_unix=time.time()))
        return monitor(output, evidence, lambda: fcntl.flock(lock, fcntl.LOCK_UN))
    except BaseException as error:
        if output.exists():
            helper.write(output / ('ERROR_' + str(time.time_ns()) + '.json'), dict(error=str(error),
                error_type=type(error).__name__, observed_unix=time.time(), no_additional_signals=True))
        raise
    finally:
        os.close(lock)


def handoff(output, seconds):
    helper = api()
    require(type(seconds) is int and 1 <= seconds <= 1200, 'bounded_boundary_wait')
    request = helper.read(output / 'STAGED.json')
    require(helper.sha(__file__) == request['operator_sha256'] and helper.sha(request['cpu_path']) == request['cpu_sha256']
        and helper.sha(request['old_config']) == request['old_config_sha256']
        and helper.sha(output / 'GUARD.json') == request['new_config_sha256'], 'staged_provenance_unchanged')
    config, plan, original = old_modules(request['old_config'])
    new_config = helper.read(output / 'GUARD.json')
    new_plan = helper.read(new_config['plan_path'])
    verify_source(request['source_binding'], config, plan, new_config, new_plan)
    validate_fresh(output / 'GUARD.json', new_plan['source_root'])
    require(old_processes(request['processes']['actor']['pid'], request['old_config'], config, plan)
            == request['processes'], 'exact_staged_original_processes')
    lock = os.open(BASE / 'orch_r142_allocator_ovx2_ROLLOUT.lock', os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    descriptors, paused, handlers = {}, [], {}
    def interrupted(signum, frame):
        raise SystemExit('interrupted_restore_exact_paused_processes')
    try:
        (output / 'HANDOFF_ONCE').mkdir()
        handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGHUP)}
        for name, process in request['processes'].items():
            require(helper.process_record(process['pid']) == process, 'identity_before_pidfd')
            descriptors[name] = os.pidfd_open(process['pid'])
            require(helper.process_record(process['pid']) == process, 'identity_after_pidfd')
        deadline = min(time.monotonic() + seconds, time.monotonic() + plan['hard_end_unix'] - time.time() - 900)
        attempts = 0
        while time.monotonic() < deadline:
            saved = original.saved.sleep_boundary(plan['root'])
            if saved is None or not original.saved.readout_started(plan['root'], saved['cycle'],
                    plan.get('readout_revision', 1), request['processes']['timer']['pid']):
                time.sleep(.25)
                continue
            if not claim_boundary(lock):
                time.sleep(.25)
                continue
            attempts += 1
            prepared = output / f'BOUNDARY_PREP_{attempts:04d}'
            prepared.mkdir()
            evidence = saved_evidence(plan, saved, original)
            shutil.copytree(Path(plan['root']) / 'stream', prepared / 'stream')
            try:
                helper.verify_snapshot(prepared / 'stream', plan['root'], saved['state_sha256'], original)
            except (ValueError, FileNotFoundError):
                helper.write(prepared / 'MOVED.json', dict(status='PREP_MOVED_NO_SIGNAL'))
                fcntl.flock(lock, fcntl.LOCK_UN)
                continue
            shutil.copytree(Path(evidence['checkpoint_path']).parent, prepared / 'checkpoint')
            helper.write(prepared / 'CPU_BOUNDARY.json', evidence)
            if original.saved.sleep_boundary(plan['root']) != saved:
                fcntl.flock(lock, fcntl.LOCK_UN)
                continue
            for name in ('supervisor', 'timer', 'actor'):
                paused.append(name)
                helper.pause_exact(request['processes'][name], descriptors[name])
            if original.saved.sleep_boundary(plan['root']) != saved:
                helper.resume_paused(paused, descriptors)
                fcntl.flock(lock, fcntl.LOCK_UN)
                continue
            complete = Path(plan['root']) / 'readouts' / original.native.readout_name(plan, saved['cycle']) / 'COMPLETE.json'
            readout_deadline = min(deadline, time.monotonic() + 180)
            while time.monotonic() < readout_deadline and not complete.exists():
                time.sleep(.1)
            require(complete.exists() and helper.read(complete)['status'] == 'COMPLETE', 'readout_complete_before_retirement')
            readout_pid = helper.read(complete)['pid']
            while time.monotonic() < readout_deadline:
                status = Path('/proc') / str(readout_pid) / 'stat'
                if not status.exists() or status.read_text().rsplit(') ', 1)[1].split()[0] == 'Z':
                    break
                time.sleep(.1)
            else:
                raise ValueError('readout_not_exited_restore_live_child')
            require(original.saved.sleep_boundary(plan['root']) == saved, 'saved_frontier_unchanged')
            require(sorted(path.name for path in (Path(plan['root']) / 'stream/records').iterdir()) ==
                    sorted(path.name for path in (prepared / 'stream/records').iterdir()), 'no_pending_mutation')
            require(saved_evidence(plan, saved, original) == evidence, 'exact_bundle_after_quiescence')
            helper.write(output / 'BOUNDARY.json', dict(**evidence, full_chain_verified=True,
                all_threads_quiescent=True, snapshot=str(prepared), readout_complete_sha256=helper.sha(complete),
                original_raw_preserved=True, saved_unix=time.time()))
            for name in ('actor', 'timer', 'supervisor'):
                process = request['processes'][name]
                require(helper.process_record(process['pid']) == process, 'exact_identity_before_retirement')
                signal.pidfd_send_signal(descriptors[name], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
                require(bool(select.select([descriptors[name]], [], [], 20)[0]), 'exact_pidfd_exit_without_KILL')
            paused.clear()
            helper.write(output / 'RETIRED.json', dict(status='EXACT_OLD_PROCESSES_EXITED',
                processes=request['processes'], boundary_sha256=helper.sha(output / 'BOUNDARY.json'), retired_unix=time.time()))
            module = importlib.import_module('gpu.orch_r125_stream_journal')
            with module.StreamJournal(Path(plan['root']) / 'stream', create=False) as journal:
                require(journal.latest_checkpoint()['expected_sha256'] == saved['state_sha256'], 'released_writer_exact_state')
            command = [str(PYTHON), '-B', request['operator_path'], '--action', 'supervise', '--output', str(output)]
            with (output / 'SUPERVISOR.log').open('x') as log:
                successor = subprocess.Popen(command, cwd=new_plan['source_root'], stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=environment(new_plan['source_root']))
            helper.write(output / 'DISPATCHED.json', dict(supervisor_pid=successor.pid, command=command, dispatched_unix=time.time()))
            return monitor(output, evidence, lambda: fcntl.flock(lock, fcntl.LOCK_UN))
        helper.write(output / 'WAIT_EXPIRED.json', dict(status='NO_RETIREMENT', observed_unix=time.time()))
        return dict(status='NO_CLEAN_PREPARED_BOUNDARY')
    except BaseException as error:
        helper.write(output / ('ERROR_' + str(time.time_ns()) + '.json'), dict(error=str(error),
            error_type=type(error).__name__, observed_unix=time.time(), retired=(output / 'RETIRED.json').exists()))
        raise
    finally:
        helper.resume_paused(paused, descriptors)
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=('stage', 'validate', 'handoff', 'supervise', 'contained', 'readmit'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--physical', type=int)
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--prior', type=Path)
    parser.add_argument('--seconds', type=int, default=1200)
    args = parser.parse_args()
    if args.action == 'stage':
        result = stage(args.physical, args.output, args.cpu)
    elif args.action == 'validate':
        result = validate_new(args.output)
    elif args.action == 'handoff':
        result = handoff(args.output, args.seconds)
    elif args.action == 'contained':
        result = contained(args.output)
    elif args.action == 'readmit':
        result = readmit(args.prior, args.output, args.cpu)
    else:
        try:
            result = supervise(args.output)
        except BaseException as error:
            api().write(args.output / 'SUPERVISOR_FAILED.json', dict(error=str(error), error_type=type(error).__name__,
                        failed_unix=time.time(), no_retry=True))
            raise
    print(json.dumps(result, sort_keys=True))
