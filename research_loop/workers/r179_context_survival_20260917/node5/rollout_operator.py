"""R179 NODE5 one-shot source-only handoff using unchanged native GPU guards."""

import argparse
import ast
import base64
from copy import deepcopy
import fcntl
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid


BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
POLICY_SHA = 'b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b'
SCOPE_SHA = '85441db890036947f6bc242e66ef15db750a683d73fe02d06778ebe996d4fb54'
NATIVE = 'gpu/orch_r125_continual_native.py'
POLICY = 'gpu/orch_r179_context_survival.py'
LABELS = {'C1': 0, 'C2': 1, 'run1': 2, 'C3': 3, 'C4': 4, 'C5': 5, 'pilot': 6, 'repo_reader': 7}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    Path(path).chmod(0o444)


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def environment(source):
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(source),
                HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                TOKENIZERS_PARALLELISM='false')


def load_saved(source):
    sys.path.insert(0, str(source))
    if not (source / 'gpu/orch_r157_community_wall_extension.py').exists():
        return load_auxiliary('saved_primitives.py')
    module = importlib.import_module('gpu.orch_r157_community_wall_extension')
    require(Path(module.__file__).resolve() == source / 'gpu/orch_r157_community_wall_extension.py',
            'exact_saved_primitive_source')
    return module


def load_auxiliary(name):
    path = Path(__file__).resolve().parent / name
    spec = importlib.util.spec_from_file_location('_r179_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unchanged_containment_check(config, plan):
    if plan.get('physical') in (2, 6):
        return unchanged_protected_containment_check(config, plan)
    path = Path(__file__).resolve().parent / 'containment_primitives.py'
    tree = ast.parse(path.read_bytes())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'verify_containment']
    require(len(functions) == 1, 'one_exact_saved_containment_function')
    namespace = dict(os=os, Path=Path, socket=socket, stat=stat, time=time, require=require,
                     digest=lambda raw: hashlib.sha256(raw).hexdigest())
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['verify_containment'](config, plan)


def unchanged_protected_containment_check(config, plan):
    path = Path(__file__).resolve().parent / 'protected_primitives.py'
    tree = ast.parse(path.read_bytes())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'contained']
    require(len(functions) == 1, 'one_exact_saved_protected_containment_function')
    function = functions[0]
    require(ast.unparse(function.body[0]) == "config, plan, unused_guard = modules(output / 'GUARD.json')",
            'protected_containment_config_load_prefix')
    receipts = [position for position, statement in enumerate(function.body)
                if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Name) and statement.value.func.id == 'write'
                and ast.unparse(statement.value.args[0]) == "output / 'CONTAINMENT_VERIFIED.json'"]
    require(len(receipts) == 1 and receipts[0] > 1, 'one_protected_prelaunch_containment_receipt')
    boundary = receipts[0]
    verifier = ast.parse('def verify_containment(config, plan):\n    pass\n').body[0]
    verifier.body = function.body[1:boundary] + [ast.Return(value=function.body[boundary].value.args[1])]
    namespace = dict(os=os, Path=Path, stat=stat, require=require)
    module = ast.fix_missing_locations(ast.Module(body=[verifier], type_ignores=[]))
    exec(compile(module, str(path), 'exec'), namespace)
    return namespace['verify_containment'](config, plan)


def authority(output):
    require(socket.gethostname() == '[REDACTED_HOST]' and os.getuid() == os.getgid() == 2524,
            'exact_node5_owner')
    require(sha(output / 'BUILDER_SCOPE.json') == SCOPE_SHA, 'exact_Main_builder_scope')
    scope = read(output / 'BUILDER_SCOPE.json')
    require(scope['policy']['sha256'] == POLICY_SHA == sha(output / 'policy.py'), 'exact_Main_policy')
    require(sha(output / 'MAIN_TESTS.py') == scope['tests']['sha256']
            and sha(output / 'CPU_MAIN.log') == scope['cpu']['sha256'], 'bound_Main_tests_and_CPU')
    require(output.parent == BASE and output.name.startswith('orch_r179_context_'), 'own_new_remote_root')
    request = read(output / 'INPUT.json')
    require(request['label'] in LABELS and request['physical'] == LABELS[request['label']], 'assigned_slot')
    return request


def namespace_matches(request):
    logical = Path(request['logical_root']).stat()
    stored = Path(request['storage_root']).stat()
    return (logical.st_dev, logical.st_ino) == (stored.st_dev, stored.st_ino)


def namespace_command(request, command):
    require(request['label'] == 'repo_reader' and request['physical'] == 7, 'reader_namespace_only')
    process_id = request['identity']['pid']
    fields = Path('/proc', str(process_id), 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[19] == request['identity']['start_ticks'], 'registered_namespace_owner')
    return ['sudo', '-n', 'nsenter', '--target', str(process_id), '--mount', '--',
            '/usr/bin/setpriv', '--reuid=2524', '--regid=2524', '--clear-groups', *command]


def owner_pair(saved, request, config, plan):
    actor = saved.identity(request['identity']['pid'])
    require(actor['start_ticks'] == request['identity']['start_ticks']
            and actor['uid'] == request['identity']['uid'] == 2524, 'current_registered_owner')
    timer = saved.identity(actor['parent'])
    supervisor = saved.identity(timer['parent'])
    command = [str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', request['config_ref']['path']]
    timeout_prefix = (['timeout', '--foreground', '--signal=TERM'] if request['label'] == 'repo_reader'
                      else ['timeout', '--signal=TERM', '--kill-after=5s'])
    require(actor['argv'] == command and timer['argv'][:3] == timeout_prefix
            and timer['argv'][4:] == command and timer['argv'][3].endswith('s'), 'exact_native_timeout_pair')
    launch = read(Path(config['attempt_dir']) / 'LAUNCH.json')
    require(launch['pid'] == timer['pid'] and launch['parent_start_ticks'] == timer['start_ticks']
            and launch['guard_sha256'] == request['config_ref']['sha256']
            and launch['plan_sha256'] == request['plan_ref']['sha256'], 'original_LAUNCH_binding')
    pair = dict(actor=actor, timer=timer, supervisor=supervisor)
    for process in pair.values():
        require(process['uid'] == 2524 and process['cwd'] == plan['source_root']
                and process['boot_id'] == actor['boot_id'] and process['cgroup'] ==
                '0::/system.slice/' + config['device_containment']['unit'] + '.service', 'owned_confined_process_tree')
    require(actor['group'] == timer['group'] == timer['pid'], 'owned_timeout_group')
    return pair


def parse_properties(raw):
    values = {}
    for line in raw.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            if key == 'DeviceAllow' and key in values:
                values[key] += '\n' + value
            else:
                require(key not in values, 'unique_scalar_systemd_property')
                values[key] = value
    return values


def device_preflight(config, plan):
    properties = ('User', 'Group', 'DevicePolicy', 'DeviceAllow', 'NoNewPrivileges',
                  'ProtectControlGroups', 'CapabilityBoundingSet', 'AmbientCapabilities',
                  'BindPaths', 'KillMode', 'SendSIGKILL')
    command = ['sudo', '-n', 'systemctl', 'show', config['device_containment']['unit'] + '.service']
    for name in properties:
        command.extend(['-p', name])
    raw = subprocess.check_output(command, text=True, timeout=20)
    values = parse_properties(raw)
    require(values['DevicePolicy'] == 'strict' and values['NoNewPrivileges'] == 'yes'
            and values['ProtectControlGroups'] == 'yes' and not values['CapabilityBoundingSet']
            and not values['AmbientCapabilities'], 'existing_strict_device_confinement')
    require(values['User'] in ('2524', 'local-rohing') and values['Group'] in ('2524', 'local-rohing'),
            'existing_nonroot_service_identity')
    minor = config['device_containment']['minor']
    require(minor == plan['physical'] and '/dev/nvidia' + str(minor) + ' ' in values['DeviceAllow'],
            'allocated_device_allowlist')
    require(all('/dev/nvidia' + str(other) + ' ' not in values['DeviceAllow'] for other in range(8) if other != minor),
            'foreign_device_not_allowed')
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == plan['gpu_uuid']:
            matches.append(int(fields['Device Minor'].strip()))
    require(matches == [minor], 'kernel_GPU_UUID_minor')
    return dict(checked_unix=time.time(), properties=values, physical=minor, gpu_uuid=plan['gpu_uuid'],
                existing_owner_occupied=True, clear_GPU_admission='POST_RETIREMENT_ORIGINAL_GUARD_SCAN')


def old_inputs(output):
    request = authority(output)
    require(sha(request['config_ref']['path']) == request['config_ref']['sha256']
            and sha(request['plan_ref']['path']) == request['plan_ref']['sha256'], 'unchanged_original_control')
    config, plan = read(request['config_ref']['path']), read(request['plan_ref']['path'])
    require(plan['root'] == request['logical_root'] and plan['source_root'] == request['plan']['source_root']
            and plan['physical'] == request['physical'] and plan['gpu_uuid'] == request['plan']['gpu_uuid'],
            'same_life_device_source')
    if request['storage_root'] != plan['root']:
        require(request['label'] == 'repo_reader' and namespace_matches(request), 'exact_recovered_root_not_archival')
    return request, config, plan


def cpu_proof(output, boundary, name):
    path = output / (name + '_BOUNDARY.json')
    write(path, boundary)
    command = [str(PYTHON), '-B', str(output / 'cpu_actual.py'), '--source', str(output / 'source'),
               '--original', read(output / 'INPUT.json')['plan']['source_root'],
               '--plan', str(output / 'PLAN.json'), '--boundary', str(path)]
    completed = subprocess.run(command, env=environment(output / 'source'), cwd=output / 'source',
                               text=True, capture_output=True, timeout=180)
    (output / (name + '_CPU.log')).write_text(completed.stdout + completed.stderr)
    require(completed.returncode == 0, 'receiving_actual_source_CPU_failed_' + name)
    proof = json.loads(completed.stdout)
    require(proof['status'] == 'PASS' and proof['cuda_initialized'] is False, 'actual_CPU_proof')
    write(output / (name + '_CPU.json'), proof)
    return proof


def latest_saved(saved, root):
    probe = importlib.import_module('stage_node5')
    paths = sorted(path for path in (root / 'stream/records').glob('*.json') if path.stem.isdigit())
    for path in reversed(paths[-256:]):
        if probe.tail_metadata(path)['kind'] == 'SLEEP_COMPLETE':
            record = read(path)
            require(record['sha256'] == saved.digest({key: value for key, value in record.items() if key != 'sha256'}),
                    'saved_journal_record_hash')
            return dict(record=record, reference=reference(path), cycle=record['document']['cycle'],
                        index=record['index'], state_sha256=record['document']['resume_state']['sha256'])
    raise ValueError('no_saved_boundary_in_bounded_window')


def remove_consumed_wall(saved, plan, successor):
    if 'authorized_wall_extension' not in plan:
        return None
    probe = importlib.import_module('stage_node5')
    extension = plan['authorized_wall_extension']
    require(extension['new_deadline_unix'] == plan['hard_end_unix'], 'only_applied_wall_directive')
    paths = sorted(path for path in (Path(plan['root']) / 'stream/records').glob('*.json') if path.stem.isdigit())
    require(len(paths) <= 20000, 'bounded_wall_metadata_search')
    for path in reversed(paths):
        if probe.tail_metadata(path)['kind'] != 'WALL_EXTENDED':
            continue
        record = read(path)
        require(record['sha256'] == saved.digest({key: value for key, value in record.items() if key != 'sha256'}),
                'recorded_wall_hash')
        if record['document']['authorization'] == extension:
            successor.pop('authorized_wall_extension')
            return reference(path)
    raise ValueError('consumed_wall_not_proven_no_removal')


def successor_unit_name(output, physical):
    if physical == 7:
        return 'orch-r136-native-' + uuid.uuid4().hex
    return output.name.replace('_', '-')


def command_preflight(saved, config, plan, output):
    command = strict_command(saved, config, plan, output)
    suffix = [str(PYTHON), '-B', str(output / 'rollout_operator.py'), 'contained', '--output', str(output)]
    require(command[-len(suffix):] == suffix, 'exact_successor_entrypoint_preflight')
    return dict(command=command, constructed_unix=time.time(), launched=False, model_loaded=False)


def stage(output):
    request, config, plan = old_inputs(output)
    tests = subprocess.run([str(PYTHON), '-B', '-m', 'unittest', 'discover', '-s', str(output),
        '-p', 'test_*.py', '-v'], env=environment(output), text=True, capture_output=True, timeout=60)
    (output / 'OPERATOR_CPU.log').write_text(tests.stdout + tests.stderr)
    require(tests.returncode == 0, 'receiving_operator_CPU_tests')
    original = Path(plan['source_root'])
    saved = load_saved(original)
    pair = owner_pair(saved, request, config, plan)
    if request['label'] in ('C2', 'C5'):
        controller = load_auxiliary('controller_transfer.py')
        binding = controller.inspect_holder(request['label'], config, pair)
        write(output / 'CONTROLLER_BINDING.json', binding)
        write(output / 'CONTROLLER_PREFLIGHT.json', dict(status='PASS',
            binding=reference(output / 'CONTROLLER_BINDING.json'),
            helper=reference(output / 'controller_transfer.py'), source_proof=binding['source_proof'],
            receiving_operator_cpu=reference(output / 'OPERATOR_CPU.log'), signals_sent=0,
            genuine_legacy_flock_verified=True, model_loaded=False, checked_unix=time.time()))
    device = device_preflight(config, plan)
    if request['label'] == 'repo_reader':
        require(device['properties']['KillMode'] == 'process' and device['properties']['SendSIGKILL'] == 'no'
                and device['properties']['BindPaths'] == request['storage_root'] + ':' + plan['root'] + ':rbind',
                'existing_reader_mount_and_termination_policy')
        script = Path(pair['supervisor']['argv'][2])
        require(script.is_absolute() and script.name == 'orch_r157_repo_reader_wall.py', 'actual_reader_supervisor')
        capsule = script.parent / 'CONFINEMENT_API.py'
        require(sha(capsule) == '29e2d77dfe21a6c1b37861f52c00d2eeb858c67b60f054ab6e2d2238cc135c95',
                'actual_reader_confinement_capsule')
        shutil.copyfile(capsule, output / 'reader_capsule.py')
        (output / 'reader_capsule.py').chmod(0o444)
    original_files = saved.files(original)
    require(POLICY not in original_files, 'not_already_R179')
    require(shutil.disk_usage(BASE).free > 2 * 1024 ** 3, 'receiving_disk_headroom')
    source = output / 'source'
    shutil.copytree(original, source)
    for path in (source, source / 'gpu'):
        path.chmod(0o755)
    shutil.copyfile(output / 'policy.py', source / POLICY)
    spec = importlib.util.spec_from_file_location('r179_exact_policy', source / POLICY)
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    native = source / NATIVE
    native.chmod(0o644)
    native.write_text(policy.patch_native((original / NATIVE).read_text()))
    inventory = saved.files(source)
    require(set(inventory) == set(original_files) | {POLICY}
            and all(inventory[name] == value for name, value in original_files.items() if name != NATIVE),
            'only_native_compaction_and_policy_added')
    successor_plan = deepcopy(plan)
    successor_plan['source_root'] = str(source)
    if plan.get('startup_context'):
        relative = Path(plan['startup_context']['path']).relative_to(original)
        successor_plan['startup_context']['path'] = str(source / relative)
    consumed_wall = remove_consumed_wall(saved, plan, successor_plan)
    require(plan.get('preupdate_recovery') is None, 'no_unsaved_recovery')
    write(output / 'PLAN.json', successor_plan)
    proof = cpu_proof(output, latest_saved(saved, Path(plan['root'])), 'STAGE')
    saved.freeze(source)
    write(output / 'SOURCE_MANIFEST.json', dict(original_files=original_files, source_files=inventory,
        policy_sha256=POLICY_SHA, source_root=str(source), original_source_root=str(original)))
    allocation = read(config['allocation_path'])
    allocation.update(plan_sha256=sha(output / 'PLAN.json'), declared_unix=time.time(),
                      cpu_tests_passed=True, builder_entry_pushed=True,
                      r179_cpu=reference(output / 'STAGE_CPU.json'), r179_scope=reference(output / 'BUILDER_SCOPE.json'))
    write(output / 'ALLOCATION.json', allocation)
    successor_config = deepcopy(config)
    successor_config.update(plan_path=str(output / 'PLAN.json'), plan_sha256=sha(output / 'PLAN.json'),
        source_pins={name: value for name, value in inventory.items() if name.endswith('.py')},
        allocation_path=str(output / 'ALLOCATION.json'), allocation_sha256=sha(output / 'ALLOCATION.json'),
        attempt_dir=str(output / 'attempt'), resume=True)
    successor_config['device_containment']['unit'] = successor_unit_name(output, plan['physical'])
    write(output / 'GUARD.json', successor_config)
    write(output / 'COMMAND_PREFLIGHT.json', command_preflight(saved, successor_config, successor_plan, output))
    command = [str(PYTHON), '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
               str(output / 'GUARD.json')]
    subprocess.run(command, env=environment(source), cwd=source, check=True, timeout=60)
    require(saved.files(original) == original_files and saved.files(source) == inventory, 'source_still_exact')
    write(output / 'READY.json', dict(status='ACTUAL_SOURCE_CPU_READY_NOT_STOPPED', pair=pair,
        config=reference(output / 'GUARD.json'), plan=reference(output / 'PLAN.json'),
        source_manifest=reference(output / 'SOURCE_MANIFEST.json'), cpu=reference(output / 'STAGE_CPU.json'),
        operator_cpu=reference(output / 'OPERATOR_CPU.log'),
        command_preflight=reference(output / 'COMMAND_PREFLIGHT.json'),
        auxiliary_files={name: sha(output / name) for name in ('cpu_actual.py', 'stage_node5.py',
            'saved_primitives.py', 'protected_primitives.py', 'containment_primitives.py', 'reader_capsule.py',
            'controller_transfer.py', 'CONTROLLER_BINDING.json', 'CONTROLLER_PREFLIGHT.json')
            if (output / name).exists()},
        consumed_wall_record=consumed_wall,
        device_preflight=device, authority=reference(output / 'BUILDER_SCOPE.json'),
        operator=reference(output / 'rollout_operator.py'), proof_steps=proof['optimizer_steps'],
        unchanged_walls=True, unchanged_invitations=True, stopped=False, staged_unix=time.time()))
    return reference(output / 'READY.json')


def validate_successor(output):
    request = authority(output)
    if request['storage_root'] != request['logical_root']:
        require(namespace_matches(request), 'same_reader_namespace_on_every_entry')
    ready = read(output / 'READY.json')
    require(sha(output / 'rollout_operator.py') == ready['operator']['sha256'], 'bound_operator_bytes')
    require(all(sha(output / name) == checksum for name, checksum in ready.get('auxiliary_files', {}).items()),
            'bound_CPU_and_saved_helpers')
    require(sha(output / 'GUARD.json') == ready['config']['sha256']
            and sha(output / 'PLAN.json') == ready['plan']['sha256'], 'bound_successor_control')
    saved = load_saved(output / 'source')
    manifest = read(output / 'SOURCE_MANIFEST.json')
    require(saved.files(output / 'source') == manifest['source_files'], 'immutable_actual_successor')
    from gpu.orch_r125_continual_guard import validate
    config, plan = validate(output / 'GUARD.json')
    require(plan['hard_end_unix'] == read(read(output / 'INPUT.json')['plan_ref']['path'])['hard_end_unix'],
            'unchanged_wall')
    return saved, config, plan


def execute(output, seconds, controller_go=None, controller_go_sha256=None):
    saved, config, plan = validate_successor(output)
    request, old_config, old_plan = old_inputs(output)
    ready = read(output / 'READY.json')
    pair = ready['pair']
    require(owner_pair(saved, request, old_config, old_plan) == pair, 'exact_ready_process_tree')
    controller = load_auxiliary('controller_transfer.py') if request['label'] in ('C2', 'C5') else None
    if controller:
        controller_authority = controller.authorize(output, controller_go, controller_go_sha256)
        controller_binding = read(output / 'CONTROLLER_BINDING.json')
        controller.verify_binding(controller_binding, old_config, pair)
        controller.no_previous_stop(output, controller_binding)
    lock = os.open(BASE / ('orch_r157_' + request['label'] + '_HANDOFF.lock'),
                   (0 if controller else os.O_CREAT) | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    descriptors = {}
    try:
        if controller:
            controller.verify_descriptor(lock, controller_binding)
        else:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (output / 'EXECUTE_ONCE').mkdir()
        for role, process in pair.items():
            saved.same(process)
            descriptors[role] = os.pidfd_open(process['pid'])
            saved.same(process)
        deadline = min(time.monotonic() + seconds, time.monotonic() + plan['hard_end_unix'] - time.time() - 600)
        while time.monotonic() < deadline:
            if controller:
                controller.verify_binding(controller_binding, old_config, pair)
            for process in pair.values():
                saved.same(process)
            boundary = saved.saved_boundary(plan['root'])
            metadata = saved.readout(plan['root'], old_config, old_plan, boundary, pair['actor']) if boundary else None
            if boundary is not None and metadata is not None:
                proof = cpu_proof(output, boundary, 'ACTUAL_' + str(boundary['index']))
                if saved.saved_boundary(plan['root']) == boundary:
                    break
            time.sleep(0.25)
        else:
            raise TimeoutError('boundary_wait_expired_original_left_running')
        saved.check_children(pair, metadata['identity']['pid'] if metadata['identity'] else None)
        validate_successor(output)
        device_preflight(old_config, old_plan)
        if controller:
            controller_authority = controller.authorize(output, controller_go, controller_go_sha256)
            controller.verify_binding(controller_binding, old_config, pair)
        with saved.pause_watchdog(descriptors['actor'], 480) as pause_deadline:
            saved.pause_exact(pair['actor'], descriptors['actor'])
            require(saved.saved_boundary(plan['root']) == boundary, 'no_boundary_race_after_pause')
            completion = saved.wait_readout(metadata, pause_deadline - 180)
            saved.check_children(pair)
            write(output / 'ACTUAL_BOUNDARY_READY.json', dict(boundary=boundary['reference'],
                state_sha256=boundary['state_sha256'], cycle=boundary['cycle'], proof=proof,
                ready=reference(output / 'READY.json'), readout_completion=completion,
                adapter_optimizer_RNG_history_exact=True, ready_before_termination=True))
            require(saved.saved_boundary(plan['root']) == boundary and time.monotonic() + 120 < pause_deadline,
                    'same_saved_boundary_before_termination')
            if controller:
                controller_authority = controller.authorize(output, controller_go, controller_go_sha256)

                def verify_native_boundary():
                    require(owner_pair(saved, request, old_config, old_plan) == pair,
                            'native_timer_supervisor_unchanged_during_controller_transfer')
                    require(saved.saved_boundary(plan['root']) == boundary and time.monotonic() + 120 < pause_deadline,
                            'same_saved_boundary_and_watchdog_budget_during_controller_transfer')
                    validate_successor(output)

                controller.transfer(output, controller_binding, lock, old_config, pair,
                                    verify_native_boundary, controller_authority)
                controller.authorize(output, controller_go, controller_go_sha256)
            write(output / 'TERMINATION_INTENT.json', dict(pair=pair, authority=reference(output / 'BUILDER_SCOPE.json'),
                  boundary_ready=reference(output / 'ACTUAL_BOUNDARY_READY.json'), no_retry=True))
            signal.pidfd_send_signal(descriptors['actor'], signal.SIGTERM)
            signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
            for role in ('actor', 'timer', 'supervisor'):
                require(bool(select.select([descriptors[role]], [], [], 30)[0]), 'owned_exit_' + role)
            require(saved.saved_boundary(plan['root']) == boundary, 'no_unsaved_suffix_after_exit')
            write(output / 'OWNER_RETIRED.json', dict(pair=pair, boundary_ready=reference(output / 'ACTUAL_BOUNDARY_READY.json'),
                reset=False, stopped_unix=time.time()))
        supervise(output)
    except BaseException as error:
        write(output / 'EXECUTION_FAILED.json', dict(error_type=type(error).__name__, reason=str(error),
            terminated=(output / 'TERMINATION_INTENT.json').exists(), retired=(output / 'OWNER_RETIRED.json').exists(),
            controller_stop_intent=(output / 'CONTROLLER_STOP_INTENT.json').exists(),
            controller_exited=(output / 'CONTROLLER_EXITED.json').exists(),
            controller_lock_acquired=(output / 'CONTROLLER_LOCK_ACQUIRED.json').exists(),
            automatic_retry=False, recorded_unix=time.time()))
        raise
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)


def supervise(output):
    saved, config, plan = validate_successor(output)
    require((output / 'OWNER_RETIRED.json').exists(), 'recorded_exact_owner_retirement')
    for process in read(output / 'READY.json')['pair'].values():
        require(not Path('/proc', str(process['pid'])).exists(), 'old_owner_absent')
    attempt = output / 'attempt'
    attempt.mkdir(mode=0o700)
    (attempt / 'DISPATCH_ONCE').mkdir()
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + plan['source_root'], str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard',
        'scan', '--config', str(output / 'GUARD.json')]
    report = json.loads(subprocess.check_output(command, cwd=plan['source_root'], text=True, timeout=100))
    write(attempt / 'ADMISSION.json', report)
    require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['gpu_uuid'], 'original_privileged_clear_admission')
    write(attempt / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    command = strict_command(saved, config, plan, output)
    write(attempt / 'CONTAINED_COMMAND.json', dict(command=command, started_unix=time.time()))
    result = subprocess.run(command, check=False)
    write(attempt / 'SERVICE_EXIT.json', dict(returncode=result.returncode, no_retry=True))
    require(result.returncode == 0, 'contained_service_failed')


def strict_command(saved, config, plan, output):
    if plan.get('physical') == 7:
        request = read(output / 'INPUT.json')
        capsule = load_auxiliary('reader_capsule.py')
        capsule.DEVICES = {7: plan['gpu_uuid']}
        require(request['label'] == 'repo_reader' and config['device_containment']['minor'] == 7
                and config['device_containment']['uid'] == config['device_containment']['gid'] == 2524,
                'exact_reader_slot')
        payload = [str(PYTHON), '-B', str(output / 'rollout_operator.py'), 'contained', '--output', str(output)]
        command = capsule.device_containment_command(7, 7, 2524, 2524, config['device_containment']['unit'],
            Path(plan['source_root']), payload, int(plan['hard_end_unix'] - time.time()))
        command = [value.replace('KillMode=control-group', 'KillMode=process') for value in command]
        position = command.index('/usr/bin/env')
        command[position:position] = ['--property=SendSIGKILL=no',
            '--property=BindPaths=' + request['storage_root'] + ':' + request['logical_root']]
        command.insert(command.index('/usr/bin/env') + 2, 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')
        return command
    if plan.get('physical') in (2, 6):
        protected = load_auxiliary('protected_primitives.py')
        require(plan['hard_end_unix'] == protected.NEW_WALL and plan['lease_end_unix'] == protected.RESOURCE_CEILING
                and plan['gpu_uuid'] == protected.LANES[plan['physical']][1]
                and config['device_containment']['minor'] == plan['physical'], 'exact_protected_GPU_and_wall')
        command = protected.contained_command(config, plan, output / 'rollout_operator.py', output)
        suffix = ['--action', 'contained', '--output', str(output)]
        require(command[-4:] == suffix, 'exact_protected_entrypoint')
        return command[:-4] + ['contained', '--output', str(output)]
    copied = deepcopy(config)
    copied['r157_config_path'] = str(output / 'GUARD.json')
    command = saved.containment_command(copied, plan)
    expected = [str(PYTHON), '-B', '-m', saved.MODULE, 'contained-native', '--config', str(output / 'GUARD.json')]
    require(command[-len(expected):] == expected, 'unchanged_containment_command_prefix')
    return command[:-len(expected)] + [str(PYTHON), '-B', str(output / 'rollout_operator.py'), 'contained', '--output', str(output)]


def contained(output):
    saved, config, plan = validate_successor(output)
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    attempt = output / 'attempt'
    if plan['physical'] == 7:
        capsule = load_auxiliary('reader_capsule.py')
        capsule.DEVICES = {7: plan['gpu_uuid']}
        containment = capsule.verify_device_containment(config, plan)
    else:
        containment = unchanged_containment_check(config, plan)
    write(attempt / 'CONTAINMENT_VERIFIED.json', containment)
    report = read(attempt / 'ADMISSION.json')
    admitted = read(attempt / 'ADMISSION_TIME.json')['verified_unix']
    require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['gpu_uuid'] and 0 <= time.time() - admitted < 100,
            'fresh_original_admission_before_native')
    remaining = int(plan['hard_end_unix'] - time.time() - 10)
    require(remaining > 10, 'remaining_original_wall')
    timeout_prefix = (['timeout', '--foreground', '--signal=TERM'] if plan['physical'] == 7
                      else ['timeout', '--signal=TERM', '--kill-after=5s'])
    command = [*timeout_prefix, str(remaining) + 's', str(PYTHON),
               '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(output / 'GUARD.json')]
    process = None
    try:
        with (attempt / 'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            timer = saved.identity(process.pid)
            publish_launch(attempt / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=timer['start_ticks'],
                started_unix=time.time(), admission_verified_unix=admitted,
                admission_sha256=sha(attempt / 'ADMISSION.json'), guard_sha256=sha(output / 'GUARD.json'),
                plan_sha256=config['plan_sha256'], gpu_uuid=plan['gpu_uuid'], command_sha256=saved.digest(command),
                hard_end_unix=plan['hard_end_unix'], no_retry=True))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            result = process.wait()
        write(attempt / 'NATIVE_EXIT.json', dict(returncode=result, no_retry=True))
        require(result == 0, 'native_successor_failed')
    except BaseException:
        reap_owned_child(process)
        raise


def bootstrap():
    package = json.load(sys.stdin)
    output = Path(package['output'])
    require(output.parent == BASE and output.name.startswith('orch_r179_context_') and not output.exists(),
            'fresh_owned_remote_output')
    output.mkdir(mode=0o700)
    for name, encoded in package['files'].items():
        require(Path(name).name == name, 'flat_package_file')
        path = output / name
        path.write_bytes(base64.b64decode(encoded, validate=True))
        path.chmod(0o444)
    request = authority(output)
    command = [str(PYTHON), '-B', str(output / 'rollout_operator.py'), 'stage', '--output', str(output)]
    if request['storage_root'] != request['logical_root'] and not namespace_matches(request):
        command = namespace_command(request, ['/usr/bin/env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1', *command])
    finished = subprocess.run(command,
        env=environment(output), text=True, capture_output=True, timeout=300)
    (output / 'STAGING.log').write_text(finished.stdout + finished.stderr)
    print(json.dumps(dict(output=str(output), stage_returncode=finished.returncode,
        ready=reference(output / 'READY.json') if (output / 'READY.json').exists() else None)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('bootstrap', 'stage', 'execute', 'contained', 'start'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seconds', type=int, default=1800)
    parser.add_argument('--controller-go', type=Path)
    parser.add_argument('--controller-go-sha256')
    arguments = parser.parse_args()
    if arguments.action == 'bootstrap':
        bootstrap()
    elif arguments.action == 'stage':
        print(json.dumps(stage(arguments.output), sort_keys=True))
    elif arguments.action == 'execute':
        execute(arguments.output, arguments.seconds, arguments.controller_go, arguments.controller_go_sha256)
    elif arguments.action == 'contained':
        contained(arguments.output)
    else:
        request = authority(arguments.output)
        if request['storage_root'] != request['logical_root'] and not namespace_matches(request):
            command = [str(PYTHON), '-B', str(arguments.output / 'rollout_operator.py'), 'start',
                       '--output', str(arguments.output), '--seconds', str(arguments.seconds)]
            command = namespace_command(request, ['/usr/bin/env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1', *command])
            print(subprocess.check_output(command, text=True, timeout=30).strip())
            return
        saved, config, plan = validate_successor(arguments.output)
        extra = []
        if request['label'] in ('C2', 'C5'):
            controller = load_auxiliary('controller_transfer.py')
            controller.authorize(arguments.output, arguments.controller_go, arguments.controller_go_sha256)
            extra = ['--controller-go', str(arguments.controller_go), '--controller-go-sha256', arguments.controller_go_sha256]
        with (arguments.output / 'OPERATOR.log').open('x') as log:
            process = subprocess.Popen([str(PYTHON), '-B', str(arguments.output / 'rollout_operator.py'), 'execute',
                '--output', str(arguments.output), '--seconds', str(arguments.seconds), *extra],
                env=environment(arguments.output / 'source'), cwd=arguments.output / 'source',
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        receipt = dict(status='BOUNDED_HANDOFF_OPERATOR_STARTED', identity=saved.identity(process.pid),
                       ready=reference(arguments.output / 'READY.json'), max_wait_seconds=arguments.seconds)
        write(arguments.output / 'OPERATOR_STARTED.json', receipt)
        print(json.dumps(dict(pid=process.pid, receipt=reference(arguments.output / 'OPERATOR_STARTED.json'))))


if __name__ == '__main__':
    main()
