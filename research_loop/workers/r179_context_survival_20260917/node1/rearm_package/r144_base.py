"""Prospective target-only handoffs on A100/a40r; original admission retained."""

import argparse
import ast
from copy import deepcopy
import fcntl
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import random
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


BASE = Path('/localhome/local-rohing')
PYTHON = BASE/'v2/venv/bin/python'
GUARD = 'gpu.orch_r125_continual_guard'
POLICY = 'R144_SPECIAL_TOKEN_TARGET_EXCLUSION_V1'
PATCH_SHA = '3036dfd7b749f76d328f05330ef3b7afd664a0da599e80fc57d3e5d3e9876c1b'
HELPER_SHA = '8070e8047dd7d795df727204d2e79a2b2f7d906d88c095ac07777a8e566ed9a9'
LEGACY_NATIVE = {
    0: '163ac8d4711544dcbb479cbc747749513c455cde998035c3ecb8d2a6e5914565',
    1: '7626d13974a78c713b9e966093e285e1e8a4f194301dd8b69ec68cfcae656526',
    4: '7626d13974a78c713b9e966093e285e1e8a4f194301dd8b69ec68cfcae656526',
    5: '7626d13974a78c713b9e966093e285e1e8a4f194301dd8b69ec68cfcae656526',
}
LEGACY_STREAM_SHA = 'b603f8aee2ae465b3170903486a6a974810673fe37eb1c1d19e47a707e235fa2'
STRICT_MODULE = 'gpu.orch_r144_a40r4_strict'
STRICT_DONOR_SHA = '74cca3f1061f848da049b19e98797c5925e7646002c82147399b0c1131c4dcd2'
STRICT_CUSTODY_SHA = '0a9e370683bebeccdc96d0b344baf154513a37957674c0935c196e614c4920df'
HOSTS = dict(a100='6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8',
             a40r='e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b')
LANES = {
    'a100': {
        2: ('orch_r136_a100_teach_replay_20260916_attempt1', 'GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296'),
        3: ('orch_r136_a100_teach_perception_20260916_attempt1', 'GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8'),
        4: ('orch_r136_a100_teach_parenting_20260916_attempt1', 'GPU-31583768-d90f-520c-51ed-5dac761526d0'),
        5: ('orch_r136_a100_classroom_brain_20260916_attempt1', 'GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9'),
        6: ('orch_r136_a100_classroom_creative_20260916_attempt1', 'GPU-6de3930d-104a-f969-7d36-009271368dd1'),
        7: ('orch_r136_a100_classroom_support_20260916_attempt1', 'GPU-f0405a96-813d-7ac7-d641-3ec31d103037'),
    },
    'a40r': {
        0: ('orch_r132_kernel_child_20260916_attempt1', 'GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d'),
        1: ('orch_r136_raw_unparented_a40r1_20260916_attempt1', 'GPU-4b071167-a06a-773c-f947-60cb8c2f7512'),
        3: ('orch_r136_raw_parented_seed1_a40r3_20260916_attempt1', 'GPU-4d0f10af-119f-10bb-a28f-f7b7703a3b14'),
        4: ('orch_r136_kernel_parented_a40r4_20260916_attempt1', 'GPU-f83fb491-34ce-4176-5852-c94652151a9f'),
        5: ('orch_r136_kernel_unparented_a40r5_20260916_attempt1', 'GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30'),
        6: ('orch_r136_raw_unparented_reread_a40r6_20260916_attempt1', 'GPU-06b31c8f-7a96-d812-23f3-df3444d95397'),
        7: ('orch_r136_raw_unparented_none_a40r7_20260916_attempt1', 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98'),
    },
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def regular(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_path')
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), 'no_symlinks')
    return path


def read(path):
    return json.loads(regular(path).read_text())


def sha(path):
    value = hashlib.sha256()
    with regular(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def write(path, value):
    with regular(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def check_scope(node, config, plan, *, prospective=False):
    require(node in HOSTS and config['host_sha256'] == HOSTS[node], 'only_owned_node_hash')
    physical = plan['physical']
    require(type(physical) is int and physical in LANES[node], 'no_controls_or_unallocated_slots')
    name, gpu_uuid = LANES[node][physical]
    require(plan['root'] == str(BASE/name/'run1') and plan['gpu_uuid'] == gpu_uuid, 'exact_child_root_UUID')
    require(prospective or (node, physical) != ('a40r', 4) or kernel4_released(plan), 'Aquinas_kernel4_prospective_only')
    contained = 'device_containment' in config
    require(contained == (node == 'a100' or physical in (3, 6, 7)), 'original_topology_not_broadened')
    require(config['hard_end_unix'] == plan['hard_end_unix'], 'same_wall')
    return physical


def kernel4_released(plan):
    root = BASE/LANES['a40r'][4][0]
    if plan.get('source_root') != str(root/'source_r144_kernel4_20260916t1510z'):
        return False
    control = root/'control_r144_kernel4_20260916t1510z'
    release = control/'RECOVERY_COMPLETE_OBSERVED.json'
    return (release.exists() and sha(release) == 'cfbcbf82465679cdf63bab97cdbc645755a2230fa13332945e158151756d017e'
            and sha(control/'GUARD.json') == 'e119eb67d9986761a7d471f490676db7c8384efa78e69f69e2cd4b150b1bd1f9')


def original_entry_module(node, plan):
    if node == 'a40r' and plan['physical'] == 4 and kernel4_released(plan):
        return 'gpu.orch_r144_kernel4_recovery'
    return GUARD


def strict_kernel4_source(text):
    require(hashlib.sha256(text.encode()).hexdigest() == STRICT_DONOR_SHA, 'exact_original_R137_handler')
    tree = ast.parse(text)
    definitions = [node for node in tree.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'DEVICES' for target in node.targets)]
    require(len(definitions) == 1, 'one_original_device_scope')
    declaration = definitions[0]
    lines = text.splitlines(keepends=True)
    result = ''.join(lines[:declaration.lineno-1])+f"DEVICES = {{4: {LANES['a40r'][4][1]!r}}}\n"+''.join(lines[declaration.end_lineno:])
    result = result.replace("'gpu.orch_r137_node4_containment'", repr(STRICT_MODULE))
    after = ast.parse(result)
    for document in (tree, after):
        for node in document.body:
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'DEVICES' for target in node.targets):
                node.value = ast.Dict(keys=[], values=[])
        for node in ast.walk(document):
            if isinstance(node, ast.Constant) and node.value == STRICT_MODULE:
                node.value = 'gpu.orch_r137_node4_containment'
    require(ast.dump(tree) == ast.dump(after), 'only_scope_and_self_entrypoint_changed')
    compile(result, '<r144-kernel4-strict>', 'exec')
    return result


def add_strict_kernel4_files(source):
    donor = BASE/'orch_r144_target_rollout_a40r_20260916t1553z/lane3/source/gpu'
    wrapper = strict_kernel4_source((donor/'orch_r137_node4_containment.py').read_text()).encode()
    custody = donor/'orch_r133_retire_old_lanes.py'
    require(sha(custody) == STRICT_CUSTODY_SHA, 'exact_original_R137_custody_dependency')
    contents = {'gpu/orch_r144_a40r4_strict.py': wrapper,
                'gpu/orch_r133_retire_old_lanes.py': custody.read_bytes()}
    mode = stat.S_IMODE((source/'gpu').stat().st_mode)
    (source/'gpu').chmod(mode | stat.S_IWUSR)
    try:
        for name, content in contents.items():
            path = source/name
            if path.exists():
                require(path.read_bytes() == content, 'never_overwrite_existing_runtime_dependency')
            else:
                with path.open('xb') as stream:
                    stream.write(content)
    finally:
        (source/'gpu').chmod(mode)
    return {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}


def current_node(node):
    require(node in HOSTS and hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOSTS[node],
            'actual_owned_node')


def module_from_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inventory_files(source):
    source = regular(source)
    result = {}
    for path in source.rglob('*'):
        require(not path.is_symlink(), 'immutable_source_no_symlinks')
        if path.is_file():
            result[str(path.relative_to(source))] = sha(path)
    return result


def verify_resume_entrypoint(source):
    source = regular(source)
    guard_tree = ast.parse((source/'gpu/orch_r125_continual_guard.py').read_text())
    native_tree = ast.parse((source/'gpu/orch_r125_continual_native.py').read_text())
    entry = [node for node in guard_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'native_entry']
    runs = [node for node in native_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run']
    require(len(entry) == len(runs) == 1, 'ordinary_native_entrypoints_required')
    expected = ast.parse("child.run(config['plan_path'], resume=config['resume'])").body[0]
    require(ast.dump(entry[0].body[-1]) == ast.dump(expected), 'refuse_one_shot_guard_entrypoint')
    assignments = [node for node in ast.walk(runs[0]) if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'recovering' for target in node.targets)]
    pending = ast.parse("isinstance(stream.pending, str) and stream.pending.startswith('sleep:') "
                        "and isinstance(plan.get('preupdate_recovery'), dict)", mode='eval').body
    require(len(assignments) == 2 and isinstance(assignments[0].value, ast.Constant)
            and assignments[0].value.value is False and ast.dump(assignments[1].value) == ast.dump(pending),
            'recovery_only_for_pending_sleep_never_saved_boundary')
    guarded = [node for node in ast.walk(runs[0]) if isinstance(node, ast.If)
               and isinstance(node.test, ast.Name) and node.test.id == 'recovering']
    require(len(guarded) == 2, 'known_recovery_and_finish_sleep_branches')
    protected = {id(node) for branch in guarded for node in ast.walk(branch)}
    calls = [node for node in ast.walk(runs[0]) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == 'recover_rng']
    require(len(calls) == 1 and id(calls[0]) in protected, 'refuse_unconditional_one_shot_recovery')
    return dict(entrypoint=GUARD+' native', resume=True, pending_required_for_recovery=True,
                stale_suffix_replay=False, recovery_artifacts_preserved=True)


def originals(config_path):
    config = read(config_path)
    plan = read(config['plan_path'])
    source = regular(plan['source_root'])
    sys.path.insert(0, str(source))
    modules = {}
    for label, name in [('guard', GUARD), ('native', 'gpu.orch_r125_continual_native'),
                        ('journal', 'gpu.orch_r125_stream_journal')]:
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve() == source/(name.replace('.', '/')+'.py'), 'fresh_original_imports')
        modules[label] = module
    require(modules['guard'].validate(config_path) == (config, plan), 'original_full_guard_validation')
    return config, plan, SimpleNamespace(**modules)


def actual_device(plan):
    inventory = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid', '--format=csv,noheader,nounits'], text=True)
    physicals = dict((int(index.strip()), gpu_uuid.strip()) for index, gpu_uuid in
                     (line.split(',') for line in inventory.splitlines()))
    require(physicals[plan['physical']] == plan['gpu_uuid'], 'actual_physical_UUID')
    minors = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == plan['gpu_uuid']:
            minors.append(int(fields['Device Minor'].strip()))
    require(len(minors) == 1, 'one_actual_UUID_minor')
    path = Path('/dev')/f'nvidia{minors[0]}'
    metadata = path.lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
            and os.minor(metadata.st_rdev) == minors[0], 'actual_kernel_device_not_index_assumption')
    return dict(physical=plan['physical'], gpu_uuid=plan['gpu_uuid'], minor=minors[0], device_path=str(path))


def identity(pid):
    process = Path('/proc')/str(pid)
    fields = (process/'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[0] not in ('Z', 'X'), 'owned_process_alive')
    environment = (process/'environ').read_bytes().split(b'\0')
    return dict(pid=pid, start_ticks=fields[19], parent=int(fields[1]), group=int(fields[2]),
        uid=process.stat().st_uid, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        argv=(process/'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'),
        cwd=str((process/'cwd').resolve()), cgroup=(process/'cgroup').read_text().strip(),
        environment=[part.decode() for part in environment if part.startswith(
            (b'CUDA_VISIBLE_DEVICES=', b'PYTORCH_CUDA_ALLOC_CONF=', b'PYTORCH_ALLOC_CONF='))])


def launcher(node, config):
    if 'device_containment' not in config:
        return dict(module=GUARD, supervisor='supervise', inner='supervise')
    module = 'gpu.orch_r136_node1_launcher' if node == 'a100' else 'gpu.orch_r137_node4_containment'
    return dict(module=module, supervisor='contained-supervise', inner='contained-native')


def validate_pair(pair, node, config_path, config, plan, launch):
    actor, timer, supervisor = (pair[name] for name in ('actor', 'timer', 'supervisor'))
    prior_module = original_entry_module(node, plan)
    expected = [str(PYTHON), '-B', '-m', prior_module, 'native', '--config', str(config_path)]
    require(actor['argv'] == expected and timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3]) and timer['argv'][4:] == expected, 'original_native_timer')
    handler = launcher(node, config)
    prior_supervisor = prior_module if prior_module != GUARD else handler['module']
    require(supervisor['argv'] == [str(PYTHON), '-B', '-m', prior_supervisor, handler['inner'],
            '--config', str(config_path)], 'original_node_supervisor')
    require(actor['parent'] == timer['pid'] and timer['parent'] == supervisor['pid']
            and actor['group'] == timer['group'] == timer['pid'], 'exact_process_ancestry')
    require(launch['pid'] == timer['pid'] and launch['parent_start_ticks'] == timer['start_ticks']
            and launch['guard_sha256'] == sha(config_path) and launch['plan_sha256'] == config['plan_sha256']
            and launch['gpu_uuid'] == plan['gpu_uuid'], 'original_launch_identity_binding')
    for name, process in pair.items():
        require(process['uid'] == os.getuid() and process['boot_id'] == actor['boot_id']
                and process['cgroup'] == actor['cgroup'], 'owned_same_cgroup_processes')
        require(process['cwd'] == plan['source_root'] or (name == 'supervisor'
                and handler['module'] == GUARD and process['cwd'] == str(BASE)), 'original_process_cwd')
        expected_uuid = '' if name == 'supervisor' and handler['module'] == GUARD else plan['gpu_uuid']
        require(process['environment'] == ['CUDA_VISIBLE_DEVICES='+expected_uuid], 'unchanged_original_environment')
    if 'device_containment' in config:
        require(actor['cgroup'] == '0::/system.slice/'+config['device_containment']['unit']+'.service',
                'bound_original_containment_unit')


def process_pair(pid, node, config_path, config, plan):
    actor = identity(pid)
    timer = identity(actor['parent'])
    pair = dict(actor=actor, timer=timer, supervisor=identity(timer['parent']))
    validate_pair(pair, node, config_path, config, plan, read(Path(config['attempt_dir'])/'LAUNCH.json'))
    return pair


def relocated_plan(plan, source):
    proposed = deepcopy(plan)
    proposed['source_root'] = str(source)
    if plan.get('startup_context'):
        relative = regular(plan['startup_context']['path']).relative_to(regular(plan['source_root']))
        require(sha(source/relative) == plan['startup_context']['sha256'], 'unchanged_startup_bytes')
        proposed['startup_context']['path'] = str(source/relative)
    normalized = deepcopy(proposed)
    normalized['source_root'] = plan['source_root']
    if plan.get('startup_context'):
        normalized['startup_context']['path'] = plan['startup_context']['path']
    require(normalized == plan, 'only_source_and_startup_relocation')
    require('authorized_wall_extension' not in plan, 'unsupported_one_shot_wall_topology')
    return proposed


def stage(node, config_path, pid, output, cpu_path, patch_path, helper_path):
    current_node(node)
    config_path, output, cpu_path, patch_path, helper_path = map(regular,
        (config_path, output, cpu_path, patch_path, helper_path))
    config, plan, original = originals(config_path)
    physical = check_scope(node, config, plan, prospective=True)
    reserved = (node, physical) == ('a40r', 4) and not kernel4_released(plan)
    require(output.is_relative_to(BASE) and output.parent.name.startswith('orch_r144_target_rollout_'+node+'_')
            and not output.exists(), 'unique_owned_stage')
    require(sha(patch_path) == PATCH_SHA and sha(helper_path) == HELPER_SHA, 'exact_Main_patch_helper_bytes')
    cpu = read(cpu_path)
    require(cpu['status'] == 'PASS' and cpu['operator_sha256'] == sha(Path(__file__).absolute())
            and cpu['patch_sha256'] == PATCH_SHA and cpu['helper_sha256'] == HELPER_SHA, 'own_bound_CPU_gate')
    pair = None if reserved else process_pair(pid, node, config_path, config, plan)
    device = actual_device(plan)
    if 'device_containment' in config:
        require(config['device_containment']['minor'] == device['minor'], 'original_actual_minor_preserved')
    old_source = regular(plan['source_root'])
    entrypoint = verify_resume_entrypoint(old_source)
    before = inventory_files(old_source)
    utility = module_from_file('r144_frozen_patch', patch_path)
    patched = utility.patch_source((old_source/'gpu/orch_r125_continual_native.py').read_bytes().decode('utf-8'))
    output.mkdir()
    source, control = output/'source', output/'control'
    shutil.copytree(old_source, source)
    native_path = source/'gpu/orch_r125_continual_native.py'
    native_mode = stat.S_IMODE(native_path.stat().st_mode)
    native_path.chmod(native_mode | stat.S_IWUSR)
    try:
        native_path.write_bytes(patched.encode('utf-8'))
    finally:
        native_path.chmod(native_mode)
    require(not (source/'gpu/orch_r144_sleep_targets.py').exists(), 'new_helper_only')
    directory_mode = stat.S_IMODE((source/'gpu').stat().st_mode)
    (source/'gpu').chmod(directory_mode | stat.S_IWUSR)
    try:
        shutil.copyfile(helper_path, source/'gpu/orch_r144_sleep_targets.py')
    finally:
        (source/'gpu').chmod(directory_mode)
    strict = node == 'a40r' and physical == 4 and not reserved
    strict_files = add_strict_kernel4_files(source) if strict else {}
    after = inventory_files(source)
    expected = dict(before, **{'gpu/orch_r125_continual_native.py': sha(native_path),
                             'gpu/orch_r144_sleep_targets.py': HELPER_SHA})
    expected.update(strict_files)
    require(after == expected and inventory_files(old_source) == before, 'all_other_frozen_bytes_preserved')
    write(output/'SOURCE_PROOF.json', dict(old_source=str(old_source), old_inventory=before,
        new_source=str(source), new_inventory=after, patch_sha256=PATCH_SHA, helper_sha256=HELPER_SHA,
        only_changed_existing_file='gpu/orch_r125_continual_native.py', added_files=sorted(set(after)-set(before)),
        authorized_strict_kernel4=strict, strict_donor_sha256=STRICT_DONOR_SHA if strict else None,
        only_native_sleep_AST_changed=True))
    staged = dict(node=node, physical=physical, old_config=str(config_path), old_config_sha256=sha(config_path),
        old_plan=plan, old_plan_sha256=config['plan_sha256'], source_root=str(source),
        source_proof_sha256=sha(output/'SOURCE_PROOF.json'), processes=pair, device=device,
        policy=POLICY, operator_path=str(Path(__file__).absolute()), operator_sha256=sha(Path(__file__).absolute()),
        cpu_path=str(cpu_path), cpu_sha256=sha(cpu_path), handler=launcher(node, config),
        status='RESERVED_AQUINAS_PROSPECTIVE_ONLY' if reserved else 'STAGED_NOT_APPLIED', staged_unix=time.time())
    if not reserved:
        control.mkdir()
        proposed = relocated_plan(plan, source)
        write(control/'PLAN.json', proposed)
        allocation = read(config['allocation_path'])
        require(allocation['plan_sha256'] == config['plan_sha256'], 'original_allocation')
        allocation.update(plan_sha256=sha(control/'PLAN.json'), r144_cpu_sha256=sha(cpu_path), r144_policy=POLICY)
        write(control/'ALLOCATION.json', allocation)
        updated = deepcopy(config)
        updated.update(attempt_dir=str(control), resume=True, plan_path=str(control/'PLAN.json'),
            plan_sha256=sha(control/'PLAN.json'), allocation_path=str(control/'ALLOCATION.json'),
            allocation_sha256=sha(control/'ALLOCATION.json'),
            source_pins={name: value for name, value in after.items() if name.endswith('.py')})
        if 'device_containment' in updated:
            updated['device_containment']['unit'] = 'orch-r136-native-'+uuid.uuid4().hex
        if strict:
            updated['device_containment'] = dict(minor=device['minor'], uid=os.getuid(), gid=os.getgid(),
                                                unit='orch-r136-native-'+uuid.uuid4().hex)
            staged['handler'] = dict(module=STRICT_MODULE, supervisor='contained-supervise', inner='contained-native')
        write(control/'GUARD.json', updated)
        command = [str(PYTHON), '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
                   str(control/'GUARD.json')]
        subprocess.run(command, cwd=source, env=dict(os.environ, PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES='',
            PYTHONDONTWRITEBYTECODE='1'), check=True, timeout=90)
        if strict:
            command = [str(PYTHON), '-B', '-c', 'import '+STRICT_MODULE+' as handler; '
                'assert set(handler.DEVICES) == {4}; '
                'assert callable(handler.contained_supervise) and callable(handler.verify_device_containment)']
            subprocess.run(command, cwd=source, env=dict(os.environ, PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES='',
                PYTHONDONTWRITEBYTECODE='1'), check=True, timeout=90)
        write(control/'RUNTIME_POLICY.json', dict(policy=POLICY, native_sha256=sha(native_path), helper_sha256=HELPER_SHA,
            patch_sha256=PATCH_SHA, old_plan_sha256=config['plan_sha256'], plan_sha256=updated['plan_sha256'],
            source_proof_sha256=sha(output/'SOURCE_PROOF.json'), raw_history_modified=False,
            targets_only=True, nonmatching_errors_fatal=True, original_launcher=staged['handler']))
        staged.update(new_config=str(control/'GUARD.json'), new_config_sha256=sha(control/'GUARD.json'))
        require(process_pair(pid, node, config_path, config, plan) == pair, 'staging_preserved_live_processes')
    staged['operator_path'] = str(Path(__file__).absolute())
    write(output/'STAGED.json', staged)
    write(output/'RESUME_ENTRYPOINT.json', entrypoint)
    return dict(status=staged['status'], node=node, physical=physical, stage=str(output),
                source_proof_sha256=staged['source_proof_sha256'])


def records(root):
    return sorted(path for path in (Path(root)/'stream/records').iterdir() if re.fullmatch(r'\d{20}\.json', path.name))


def sleep_boundary(root):
    paths = records(root)
    require(paths, 'journal_required')
    record = read(paths[-1])
    if record['kind'] != 'SLEEP_COMPLETE':
        return None
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}), 'boundary_record_hash')
    document = record['document']
    envelope = document['resume_state']
    state = envelope['state']
    require(document['status'] == 'COMPLETE' and envelope['sha256'] == digest(state)
            and state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
            and state['sleep_receipts'][-1]['status'] == 'COMPLETE', 'exact_saved_no_pending_boundary')
    return dict(path=str(paths[-1]), record_sha256=record['sha256'], state_sha256=envelope['sha256'],
                state=state, cycle=document['cycle'])


def readout_drained(plan, saved, actor_pid, plan_path, native):
    name = native.readout_name(plan, saved['cycle'])
    root = Path(plan['root'])/'readouts'
    dispatch, complete, failed = root/(name+'_DISPATCH.json'), root/name/'COMPLETE.json', root/(name+'_FAILED.json')
    if not dispatch.exists() or not complete.exists() or failed.exists():
        return False
    metadata = read(dispatch)
    require(metadata['resident_pid'] == actor_pid and metadata['cycle'] == saved['cycle']
            and metadata['checkpoint_sha256'] == sha(Path(plan['root'])/'checkpoints'/f"sleep_{saved['cycle']:06d}"/'COMMIT.json'),
            'exact_readout_checkpoint_dispatch')
    children = (Path('/proc')/str(actor_pid)/'task'/str(actor_pid)/'children').read_text().split()
    for child_pid in children:
        try:
            fields = (Path('/proc')/child_pid/'stat').read_text().rsplit(') ', 1)[1].split()
            if fields[0] not in ('Z', 'X'):
                return False
        except FileNotFoundError:
            pass
    return dict(dispatch_sha256=sha(dispatch), completion_marker_mtime=complete.stat().st_mtime,
                completion_contents_read=False, active_child_processes=0)


def checkpoint_contract(plan, native):
    if hasattr(native, 'verify_experiment_resume'):
        return 'EXPLICIT_EXPERIMENT'
    physical = plan['physical']
    require(physical in LEGACY_NATIVE and plan['root'] == str(BASE/LANES['a40r'][physical][0]/'run1')
        and plan['gpu_uuid'] == LANES['a40r'][physical][1], 'only_exact_legacy_children')
    source = Path(plan['source_root'])
    require(sha(source/'gpu/orch_r125_continual_native.py') == LEGACY_NATIVE[physical]
        and sha(source/'organism_v6/orch_r125_continual_stream.py') == LEGACY_STREAM_SHA,
        'exact_legacy_native_stream_contract_no_generic_skip')
    return 'PINNED_LEGACY_FIXED_RANK8'


def verify_saved_schema(contract, plan, state, checkpoint, payload):
    if contract == 'EXPLICIT_EXPERIMENT':
        require(state.get('experiment') == checkpoint.get('experiment') == payload.get('experiment'),
                'saved_experiment_triplet')
        return
    require(contract == 'PINNED_LEGACY_FIXED_RANK8', 'known_saved_contract')
    require(all('experiment' not in value for value in (state, checkpoint, payload)), 'legacy_no_invented_experiment')
    require(set(checkpoint) == {'adapter_files','adapter_path','adapter_state_sha256','base_sha256',
        'checkpoint_sha256','created_unix','optimizer_rng_path','optimizer_steps','schema'}
        and set(payload) == {'optimizer','parameter_names','optimizer_steps','cpu_rng','cuda_rng','python_rng'},
        'exact_legacy_checkpoint_optimizer_schema')
    expected = (dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
        birth_prompt=plan['birth_prompt']) if plan.get('presentation_version') else None)
    require(state['presentation'] == expected and state['context_limit'] == plan['context_limit']
        and state['segment_tokens'] == plan['segment_tokens'] and state['segments_per_sleep'] == plan['segments_per_sleep']
        and state['pending'] is None and state['sleep_frontier'] == len(state['rows']),
        'unchanged_legacy_history_context_recipe_boundary')


def saved_evidence(plan, saved, original):
    envelope = dict(state=saved['state'], sha256=saved['state_sha256'])
    stream = original.native.ContinualStream.restore(envelope, expected_sha256=saved['state_sha256'])
    contract = checkpoint_contract(plan, original.native)
    if contract == 'EXPLICIT_EXPERIMENT':
        original.native.verify_experiment_resume(plan, stream.experiment)
    commit_path = Path(plan['root'])/'checkpoints'/f"sleep_{saved['cycle']:06d}"/'COMMIT.json'
    checkpoint = read(commit_path)
    original.native.NativeChild.verify_checkpoint(checkpoint)
    require(digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256
            and checkpoint.get('experiment') == getattr(stream, 'experiment', None) and stream.deadline_unix == plan['hard_end_unix'],
            'exact_adapter_optimizer_RNG_history_carry_wall')
    import torch
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    verify_saved_schema(contract, plan, saved['state'], checkpoint, payload)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] > 0 and payload['parameter_names']
            and payload['optimizer']['state'] and payload['optimizer']['param_groups'], 'full_AdamW_not_reset')
    require(payload.get('experiment') == checkpoint.get('experiment') and len(payload['cuda_rng']) == 1
            and payload['cpu_rng'].device.type == 'cpu' and payload['cuda_rng'][0].device.type == 'cpu', 'saved_RNG_experiment')
    torch.Generator(device='cpu').set_state(payload['cpu_rng'])
    random.Random().setstate(payload['python_rng'])
    require(not torch.cuda.is_initialized(), 'provenance_CPU_only')
    return dict(record_path=saved['path'], record_sha256=saved['record_sha256'], state_sha256=saved['state_sha256'],
        checkpoint_path=str(commit_path), checkpoint_sha256=sha(commit_path), cycle=saved['cycle'],
        optimizer_steps=checkpoint['optimizer_steps'], adapter_state_sha256=checkpoint['adapter_state_sha256'],
        bundle_sha256=checkpoint['checkpoint_sha256'], full_AdamW_Python_CPU_CUDA_RNG=True)


def verify_snapshot(snapshot, original_root, expected, original):
    inbox = SimpleNamespace(inbox=Path(original_root)/'stream/inbox')
    class SnapshotJournal(original.journal.StreamJournal):
        def _inbox_event(self, message, path, source_sha256):
            return original.journal.StreamJournal._inbox_event(inbox, message, path, source_sha256)
    with SnapshotJournal(snapshot, create=False) as journal:
        require(journal.latest_checkpoint()['expected_sha256'] == expected, 'full_original_journal_snapshot_chain')


def pause_exact(expected, descriptor):
    require(identity(expected['pid']) == expected, 'identity_before_pause')
    signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
    deadline = time.monotonic()+10
    while time.monotonic() < deadline:
        tasks = list((Path('/proc')/str(expected['pid'])/'task').iterdir())
        if tasks and all((task/'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't') for task in tasks):
            require(identity(expected['pid']) == expected, 'identity_after_pause')
            return
        time.sleep(.01)
    raise ValueError('all_threads_quiescent_timeout')


def resume_paused(paused, descriptors):
    for name in reversed(paused):
        try:
            signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
        except ProcessLookupError:
            pass
    paused.clear()


def launch_command(request):
    handler = request['handler']
    return [str(PYTHON), '-B', '-m', handler['module'], handler['supervisor'], '--config', request['new_config']]


def validate_node_dependency(request, hold, report, admission_sha, launched, released):
    require(request['node'] == 'a40r' and request['physical'] == 4 and released,
            'only_released_kernel4_dependency')
    require(Path(hold['stage']).name == 'lane3' and report['clear'] is False and report['scanner_euid'] == 0
        and report['blocking_reasons'] == ['open_device_pid:1753623']
        and admission_sha == '81412f3372fbb301a931bbb844d8565d7d10bbdf232a606bc31ea8d2efd83969'
        and not launched, 'only_exact_preload_foreign_holder_dependency')


def monitor(output, request, saved, seconds=600):
    control = output/'control'
    deadline = time.monotonic()+seconds
    loaded = None
    old_index = int(Path(saved['record_path']).name.split('.')[0])
    while time.monotonic() < deadline:
        require(not any((control/name).exists() for name in ('FAILED.json', 'EXIT.json', 'SERVICE_EXIT.json')),
                'successor_exited_preserve_no_retry')
        for path in records(request['old_plan']['root']):
            if int(path.name.split('.')[0]) <= old_index:
                continue
            record = read(path)
            document = record['document']
            if record['kind'] == 'LOADED' and loaded is None:
                require(document['resume'] is True and document['optimizer_steps'] == saved['optimizer_steps']
                        and document['adapter_sha256'] == saved['adapter_state_sha256'], 'exact_saved_successor_LOADED')
                actor = identity(document['pid'])
                require(actor['argv'] == [str(PYTHON), '-B', '-m', GUARD, 'native', '--config', request['new_config']]
                        and actor['cwd'] == request['source_root']
                        and actor['environment'] == request['processes']['actor']['environment'], 'actual_same_environment_new_source')
                admission = read(control/'ADMISSION.json')
                require(admission['scanner_euid'] == 0 and admission['clear'] and not admission['blocking_reasons']
                        and admission['gpu']['uuid'] == request['old_plan']['gpu_uuid'], 'original_privileged_admission')
                if request['handler']['module'] != GUARD:
                    containment = read(control/'CONTAINMENT_VERIFIED.json')
                    denied = containment.get('denied_foreign_minors', containment.get('denied_devices'))
                    require(isinstance(denied, list) and len(denied) == 7
                            and containment['policy']['minor'] == request['device']['minor'], 'original_seven_foreign_denials')
                proof = read(output/'SOURCE_PROOF.json')
                require(sha(Path(request['source_root'])/'gpu/orch_r125_continual_native.py') ==
                        proof['new_inventory']['gpu/orch_r125_continual_native.py']
                        and sha(Path(request['source_root'])/'gpu/orch_r144_sleep_targets.py') == HELPER_SHA,
                        'actual_patched_runtime_files')
                loaded = dict(status='TARGET_POLICY_APPLIED_EXACT_SAVED_LOADED', policy=POLICY, actor=actor,
                    record_index=record['index'], record_sha256=record['sha256'], saved=saved, observed_unix=time.time())
                write(output/'LOADED_RECEIPT.json', loaded)
            if loaded and record['kind'] == 'COMMITTED':
                state = document['state']
                require(state['sha256'] == digest(state['state']) and state['state']['pending'] is None
                        and state['state']['model_state_sha256'] == digest(saved['bundle_sha256']), 'new_commit_saved_model')
                before = read(saved['record_path'])['document']['resume_state']['state']
                require(state['state']['rows'][:len(before['rows'])] == before['rows'], 'all_prior_rows_preserved')
                receipt = dict(status='APPLIED_AND_NEW_GENERATION_COMMITTED', node=request['node'], physical=request['physical'],
                    policy=POLICY, actor_pid=loaded['actor']['pid'], saved_cycle=saved['cycle'], optimizer_steps=saved['optimizer_steps'],
                    loaded_sha256=sha(output/'LOADED_RECEIPT.json'), first_commit_index=record['index'],
                    first_commit_sha256=record['sha256'], original_rows_preserved=True, observed_unix=time.time())
                write(output/'HANDOFF_COMPLETE.json', receipt)
                return receipt
        time.sleep(1)
    require(loaded is not None, 'no_loaded_receipt_within_bound')
    write(output/'MONITOR_TIMEOUT.json', dict(status='LOADED_NEW_COMMIT_NOT_OBSERVED', observed_unix=time.time()))
    return loaded


def handoff(output, wait_seconds=1800):
    output = regular(output)
    request = read(output/'STAGED.json')
    current_node(request['node'])
    config, plan, original = originals(request['old_config'])
    check_scope(request['node'], config, plan)
    checkpoint_contract(plan, original.native)
    require(request['status'] == 'STAGED_NOT_APPLIED' and not (output/'RETIRED.json').exists(), 'one_shot_live_handoff')
    require(sha(Path(__file__).absolute()) == request['operator_sha256']
            and sha(request['old_config']) == request['old_config_sha256']
            and sha(request['new_config']) == request['new_config_sha256']
            and sha(request['cpu_path']) == request['cpu_sha256'], 'bound_stage_operator_CPU_configs')
    proof = read(output/'SOURCE_PROOF.json')
    require(verify_resume_entrypoint(request['source_root']) == read(output/'RESUME_ENTRYPOINT.json'),
            'ordinary_saved_resume_reverified_before_retirement')
    require(sha(output/'SOURCE_PROOF.json') == request['source_proof_sha256']
            and inventory_files(proof['old_source']) == proof['old_inventory']
            and inventory_files(proof['new_source']) == proof['new_inventory'], 'immutable_source_provenance_before_signal')
    require(process_pair(request['processes']['actor']['pid'], request['node'], request['old_config'], config, plan)
            == request['processes'], 'same_owned_processes_before_wait')
    require(actual_device(plan) == request['device'], 'same_actual_UUID_minor')
    require(0 < wait_seconds <= 7200, 'bounded_wait')
    lock = os.open(output.parent/'NODE_HANDOFF.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    descriptors, paused = {}, []
    handlers = {}
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        hold_path = output.parent/'NODE_UNRESOLVED.json'
        if hold_path.exists():
            held = output.parent/'lane3'
            hold = read(hold_path)
            require(hold['stage'] == str(held), 'prior_node_handoff_unresolved')
            denial = held/'control/ADMISSION.json'
            validate_node_dependency(request, hold, read(denial), sha(denial),
                any((held/'control'/name).exists() for name in ('LAUNCH.json','NATIVE.log','CONTAINMENT_VERIFIED.json')),
                kernel4_released(plan))
            process = Path('/proc')/str(read(held/'DISPATCHED.json')['supervisor_pid'])/'stat'
            require(not process.exists() or process.read_text().rsplit(') ', 1)[1].split()[0] in ('Z','X'),
                    'held_lane_has_no_active_launcher')
            write(output/'DEPENDENCY_ONLY.json', dict(hold_sha256=sha(hold_path), denial_sha256=sha(denial),
                prior_lane_remains_held=True, no_admission_exception=True, observed_unix=time.time()))
        for name, process in request['processes'].items():
            descriptors[name] = os.pidfd_open(process['pid'])
        for signum in (signal.SIGINT, signal.SIGTERM):
            handlers[signum] = signal.signal(signum, lambda number, frame: (_ for _ in ()).throw(InterruptedError('operator_cancelled')))
        deadline = min(time.monotonic()+wait_seconds, time.monotonic()+plan['hard_end_unix']-time.time()-600)
        while time.monotonic() < deadline:
            saved = sleep_boundary(plan['root'])
            if saved is None:
                time.sleep(.2)
                continue
            drained = readout_drained(plan, saved, request['processes']['actor']['pid'], config['plan_path'], original.native)
            if not drained:
                time.sleep(.2)
                continue
            for name in ('supervisor', 'timer', 'actor'):
                paused.append(name)
                pause_exact(request['processes'][name], descriptors[name])
            if sleep_boundary(plan['root']) != saved:
                resume_paused(paused, descriptors)
                continue
            require(readout_drained(plan, saved, request['processes']['actor']['pid'], config['plan_path'], original.native),
                    'readout_drained_after_quiescence')
            evidence = saved_evidence(plan, saved, original)
            snapshot = output/('snapshot_'+str(time.time_ns()))
            shutil.copytree(Path(plan['root'])/'stream', snapshot)
            verify_snapshot(snapshot, plan['root'], saved['state_sha256'], original)
            require(sleep_boundary(plan['root']) == saved and saved_evidence(plan, saved, original) == evidence,
                    'unchanged_saved_state_after_snapshot')
            write(output/'BOUNDARY.json', dict(saved=evidence, readout=drained, snapshot=str(snapshot),
                all_threads_quiescent=True, original_history_carry_preserved=True, observed_unix=time.time()))
            write(output/'RETIREMENT_STARTED.json', dict(boundary_sha256=sha(output/'BOUNDARY.json'), started_unix=time.time()))
            for name in ('actor', 'timer', 'supervisor'):
                require(identity(request['processes'][name]['pid']) == request['processes'][name], 'identity_before_retirement')
                signal.pidfd_send_signal(descriptors[name], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
                require(bool(select.select([descriptors[name]], [], [], 30)[0]), 'exact_pidfd_exit_without_KILL')
            paused.clear()
            write(output/'RETIRED.json', dict(status='OLD_OWNED_PROCESSES_EXITED', processes=request['processes'],
                boundary_sha256=sha(output/'BOUNDARY.json'), retired_unix=time.time()))
            with original.journal.StreamJournal(Path(plan['root'])/'stream', create=False) as journal:
                require(journal.latest_checkpoint()['expected_sha256'] == saved['state_sha256'], 'released_original_writer_exact_state')
            command = launch_command(request)
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=request['source_root'], PYTHONDONTWRITEBYTECODE='1')
            require(not any(key in environment for key in ('PYTORCH_CUDA_ALLOC_CONF', 'PYTORCH_ALLOC_CONF')),
                    'no_new_allocator_runtime_change')
            with (output/'control/SUPERVISOR.log').open('x') as log:
                process = subprocess.Popen(command, cwd=request['source_root'], env=environment,
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            write(output/'DISPATCHED.json', dict(supervisor_pid=process.pid, command=command, started_unix=time.time()))
            return monitor(output, request, evidence)
        write(output/('WAIT_EXPIRED_'+str(time.time_ns())+'.json'), dict(status='NO_RETIREMENT', expired_unix=time.time()))
        return dict(status='NO_CLEAN_DRAINED_BOUNDARY', physical=request['physical'])
    except BaseException as error:
        write(output/('ERROR_'+str(time.time_ns())+'.json'), dict(error_type=type(error).__name__, error=str(error),
            retired=(output/'RETIRED.json').exists(), observed_unix=time.time()))
        if (output/'RETIREMENT_STARTED.json').exists() and not (output/'LOADED_RECEIPT.json').exists():
            marker = output.parent/'NODE_UNRESOLVED.json'
            if marker.exists():
                marker = output.parent/('SECONDARY_NODE_UNRESOLVED_'+str(time.time_ns())+'.json')
            write(marker, dict(stage=str(output), error=str(error), no_further_handoffs=True))
        raise
    finally:
        resume_paused(paused, descriptors)
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='action', required=True)
    staging = subparsers.add_parser('stage')
    staging.add_argument('--node', choices=tuple(HOSTS), required=True)
    staging.add_argument('--pid', type=int, required=True)
    for name in ('config-path', 'output', 'cpu-path', 'patch-path', 'helper-path'):
        staging.add_argument('--'+name, type=Path, required=True)
    handing = subparsers.add_parser('handoff')
    handing.add_argument('--output', type=Path, required=True)
    handing.add_argument('--wait-seconds', type=int, default=1800)
    arguments = vars(parser.parse_args())
    action = arguments.pop('action')
    print(json.dumps(stage(**arguments) if action == 'stage' else handoff(**arguments), indent=2))


if __name__ == '__main__':
    main()
