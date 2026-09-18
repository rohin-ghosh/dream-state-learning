"""Bounded allocator-only handoffs for the two existing node5 continual lives."""

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


HOST = '[REDACTED_HOST]'
BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
GUARD = 'gpu.orch_r125_continual_guard'
ALLOCATOR_KEY = 'PYTORCH_CUDA_ALLOC_CONF'
ALLOCATOR_VALUE = 'expandable_segments:True'
GUARD_SHA = '4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3'
NATIVE_SHA = '7626d13974a78c713b9e966093e285e1e8a4f194301dd8b69ec68cfcae656526'
TARGET_POLICY = 'R144_SPECIAL_TOKEN_TARGET_EXCLUSION_V1'
LANES = {
    2: ('orch_r125_continual_20260916_attempt1', 'source_v5',
        'GPU-d62ba12e-ff08-9e5e-ba35-14c723f6e05b'),
    6: ('orch_r127_pilot_20260916_attempt1', 'source2',
        'GPU-67a989f7-2660-a76b-40e8-3619b9fa2987'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def regular(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_path')
    require(not any(part.is_symlink() for part in (path, *path.parents)), 'no_symlinks')
    return path


def read(path):
    return json.loads(regular(path).read_text())


def sha(path):
    result = hashlib.sha256()
    with regular(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def write(path, value):
    with regular(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def scope(config, plan):
    physical = plan['physical']
    require(type(physical) is int and physical in LANES, 'only_original_node5_2_6')
    programme, source, gpu_uuid = LANES[physical]
    require(plan['root'] == str(BASE / programme / 'run1')
            and plan['source_root'] == str(BASE / programme / source)
            and plan['gpu_uuid'] == gpu_uuid, 'exact_original_life_source_UUID')
    require('device_containment' not in config, 'original_guard_topology_only')
    require(plan['hard_end_unix'] == config['hard_end_unix'] == 1789617240.0
            and plan['lease_end_unix'] == config['next_reserved_unix'] == 1789617840.0,
            'original_wall_lease_reservation')
    require(config['source_pins']['gpu/orch_r125_continual_guard.py'] == GUARD_SHA,
            'original_inherited_environment_guard')
    return physical


def prospective_scope(config, plan):
    if plan['physical'] != 7:
        return scope(config, plan)
    require(type(plan['physical']) is int and plan['root'] ==
            str(BASE / 'orch_r136_repo_reader_20260916_attempt1/run1')
            and plan['source_root'] == str(BASE / 'orch_r136_repo_reader_20260916_attempt1/source1')
            and plan['gpu_uuid'] == 'GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b', 'exact_node5_repo_reader_only')
    require('device_containment' not in config and config['source_pins']['gpu/orch_r125_continual_guard.py'] == GUARD_SHA,
            'original_repo_reader_guard_topology')
    require(plan['hard_end_unix'] == config['hard_end_unix'] == 1789596240.0
            and plan['lease_end_unix'] == config['next_reserved_unix'] == 1789617840.0,
            'repo_reader_original_wall_lease')
    return 7


def originals(config_path, prospective=False):
    require(socket.gethostname() == HOST, 'exact_node5_host')
    config = read(config_path)
    plan = read(config['plan_path'])
    (prospective_scope if prospective else scope)(config, plan)
    source = regular(plan['source_root'])
    sys.path.insert(0, str(source))
    modules = {}
    for label, name in (('guard', GUARD), ('native', 'gpu.orch_r125_continual_native'),
                        ('journal', 'gpu.orch_r125_stream_journal')):
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve() == source / (name.replace('.', '/') + '.py'),
                'original_module_location')
        modules[label] = module
    require(modules['guard'].validate(config_path) == (config, plan), 'original_provenance_validation')
    return config, plan, SimpleNamespace(**modules)


def resume_config(config, output):
    output = regular(output)
    require(not output.exists() and str(output) != config['attempt_dir'], 'unique_new_attempt')
    proposed = deepcopy(config)
    proposed.update(attempt_dir=str(output), resume=True)
    require({key for key in proposed if proposed[key] != config.get(key)} <=
            {'attempt_dir', 'resume'}, 'original_config_bindings_preserved')
    return proposed


def allocator_environment(environment):
    require(not any(key in environment for key in (ALLOCATOR_KEY, 'PYTORCH_ALLOC_CONF')),
            'no_existing_allocator_override')
    return dict(environment, **{ALLOCATOR_KEY: ALLOCATOR_VALUE})


def consumed_authorization_plan(plan, plan_sha256, records, current_deadline):
    authorization = plan.get('authorized_wall_extension')
    require(isinstance(authorization, dict), 'original_one_shot_authorization_required')
    matches = [record for record in records if record['kind'] == 'WALL_EXTENDED'
               and record['document']['authorization'] == authorization
               and record['document']['plan_sha256'] == plan_sha256]
    require(len(matches) == 1, 'one_exact_already_applied_authorization')
    record = matches[0]
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
            'applied_authorization_record_hash')
    envelope = record['document']['state']
    require(envelope['sha256'] == digest(envelope['state'])
            and envelope['state']['deadline_unix'] == authorization['new_deadline_unix']
            == current_deadline == plan['hard_end_unix']
            and authorization['lease_end_unix'] == plan['lease_end_unix'], 'authorization_already_in_current_state')
    proposed = deepcopy(plan)
    del proposed['authorized_wall_extension']
    require(dict(proposed, authorized_wall_extension=authorization) == plan, 'only_consumed_directive_removed')
    return proposed, dict(record_index=record['index'], record_sha256=record['sha256'],
        authorization=authorization, deadline_changed=False, training_changed=False,
        reason='omit_proven_consumed_one_shot_on_ordinary_resume')


def write_resume_guard(config, plan, output):
    proposed = resume_config(config, output)
    records = [read(path) for path in record_paths(plan['root'])]
    states = [record['document']['resume_state']['state'] for record in records if record['kind'] == 'SLEEP_COMPLETE']
    require(states, 'saved_state_before_derived_resume_config')
    resume_plan, proof = consumed_authorization_plan(plan, config['plan_sha256'], records,
                                                   states[-1]['deadline_unix'])
    output.mkdir(exist_ok=False)
    write(output / 'PLAN.json', resume_plan)
    allocation = read(config['allocation_path'])
    require(allocation['plan_sha256'] == config['plan_sha256'], 'original_allocation_binding')
    derived_allocation = dict(allocation, plan_sha256=sha(output / 'PLAN.json'))
    write(output / 'ALLOCATION.json', derived_allocation)
    proposed.update(plan_path=str(output / 'PLAN.json'), plan_sha256=sha(output / 'PLAN.json'),
        allocation_path=str(output / 'ALLOCATION.json'), allocation_sha256=sha(output / 'ALLOCATION.json'))
    write(output / 'GUARD.json', proposed)
    write(output / 'CONSUMED_AUTHORIZATION.json', dict(**proof, original_plan_path=config['plan_path'],
        original_plan_sha256=config['plan_sha256'], resume_plan_sha256=proposed['plan_sha256'],
        original_allocation_sha256=config['allocation_sha256'],
        allocation_delta_keys=['plan_sha256'], source_and_lease_bytes_unchanged=True))
    return proposed


def identity(pid):
    process = Path('/proc') / str(pid)
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[0] not in ('Z', 'X'), 'owned_process_alive')
    environment = (process / 'environ').read_bytes().split(b'\0')
    return dict(pid=pid, start_ticks=fields[19], parent=int(fields[1]), group=int(fields[2]),
        uid=process.stat().st_uid, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        argv=(process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'),
        cwd=str((process / 'cwd').resolve()), cgroup=(process / 'cgroup').read_text().strip(),
        environment=[part.decode() for part in environment if part.startswith(
            (b'CUDA_VISIBLE_DEVICES=', b'PYTORCH_CUDA_ALLOC_CONF=', b'PYTORCH_ALLOC_CONF='))])


def validate_pair(pair, config_path, config, plan, launch, guard_sha, allow_allocator=False):
    actor, timer, supervisor = (pair[name] for name in ('actor', 'timer', 'supervisor'))
    prefix = [str(PYTHON), '-B', '-m', GUARD]
    require(actor['argv'] == prefix + ['native', '--config', str(config_path)], 'original_actor_argv')
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and len(timer['argv']) == 11 and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3])
            and timer['argv'][4:] == actor['argv'], 'original_timer_argv')
    require(supervisor['argv'] == prefix + ['supervise', '--config', str(config_path)],
            'original_supervisor_argv')
    require(actor['parent'] == timer['pid'] and timer['parent'] == supervisor['pid']
            and actor['group'] == timer['group'] == timer['pid'], 'exact_ancestry')
    require(launch['pid'] == timer['pid'] and launch['parent_start_ticks'] == timer['start_ticks']
            and launch['guard_sha256'] == guard_sha and launch['plan_sha256'] == config['plan_sha256']
            and launch['gpu_uuid'] == plan['gpu_uuid'], 'original_launch_binding')
    for name, process in pair.items():
        cvd = '' if name == 'supervisor' else plan['gpu_uuid']
        expected_environment = ['CUDA_VISIBLE_DEVICES=' + cvd]
        if allow_allocator and ALLOCATOR_KEY + '=' + ALLOCATOR_VALUE in actor['environment']:
            expected_environment.append(ALLOCATOR_KEY + '=' + ALLOCATOR_VALUE)
        require(process['uid'] == os.getuid() and process['cwd'] == plan['source_root']
                and sorted(process['environment']) == sorted(expected_environment)
                and process['cgroup'] == actor['cgroup'] and process['boot_id'] == actor['boot_id'],
                'original_owned_process_environment')


def process_pair(pid, config_path, config, plan, allow_allocator=False):
    actor = identity(pid)
    timer = identity(actor['parent'])
    pair = dict(actor=actor, timer=timer, supervisor=identity(timer['parent']))
    validate_pair(pair, config_path, config, plan, read(Path(config['attempt_dir']) / 'LAUNCH.json'),
                  sha(config_path), allow_allocator=allow_allocator)
    return pair


def device(plan):
    output = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid', '--format=csv,noheader'], text=True)
    actual = dict((int(index.strip()), gpu_uuid.strip()) for index, gpu_uuid in
                  (line.split(',') for line in output.splitlines()))
    require(actual[plan['physical']] == plan['gpu_uuid'], 'actual_original_GPU_UUID')
    node = Path('/dev') / ('nvidia' + str(plan['physical']))
    metadata = node.stat()
    require(stat.S_ISCHR(metadata.st_mode) and os.minor(metadata.st_rdev) == plan['physical'],
            'original_physical_device_minor')
    return dict(path=str(node), major=os.major(metadata.st_rdev), minor=os.minor(metadata.st_rdev),
                gpu_uuid=plan['gpu_uuid'])


def record_paths(root):
    return sorted(path for path in (Path(root) / 'stream/records').iterdir()
                  if re.fullmatch(r'\d{20}\.json', path.name))


def sleep_boundary(root):
    paths = record_paths(root)
    require(paths, 'published_journal_required')
    record = read(paths[-1])
    if record['kind'] != 'SLEEP_COMPLETE':
        return None
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
            'boundary_hash')
    document = record['document']
    envelope = document['resume_state']
    state = envelope['state']
    require(envelope['sha256'] == digest(state) and document['status'] == 'COMPLETE'
            and state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
            and state['sleep_receipts'] and state['sleep_receipts'][-1]['status'] == 'COMPLETE',
            'no_pending_work_exact_sleep_boundary')
    return dict(path=str(paths[-1]), record_sha256=record['sha256'], state_sha256=envelope['sha256'],
                state=state, cycle=document['cycle'])


def saved_evidence(plan, saved, original):
    require(saved is not None, 'saved_boundary_required')
    state = saved['state']
    stream = original.native.ContinualStream.restore(dict(state=state, sha256=saved['state_sha256']),
                                                    expected_sha256=saved['state_sha256'])
    commit = Path(plan['root']) / 'checkpoints' / f"sleep_{saved['cycle']:06d}" / 'COMMIT.json'
    checkpoint = read(commit)
    original.native.NativeChild.verify_checkpoint(checkpoint)
    require(digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256
            and stream.deadline_unix == plan['hard_end_unix'], 'exact_saved_bundle_and_wall')
    import torch
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] > 0
            and payload['parameter_names'] and payload['optimizer']['state']
            and payload['optimizer']['param_groups'], 'full_saved_AdamW_not_reset')
    require(payload['cpu_rng'].device.type == 'cpu' and len(payload['cuda_rng']) == 1
            and payload['cuda_rng'][0].device.type == 'cpu' and payload['cuda_rng'][0].numel() > 0,
            'saved_CPU_CUDA_RNG_payload')
    torch.Generator(device='cpu').set_state(payload['cpu_rng'])
    random.Random().setstate(payload['python_rng'])
    require(not torch.cuda.is_initialized(), 'CPU_only_provenance')
    return dict(record_path=saved['path'], record_sha256=sha(saved['path']), state_sha256=saved['state_sha256'],
        checkpoint_path=str(commit), checkpoint_file_sha256=sha(commit), cycle=saved['cycle'],
        optimizer_steps=checkpoint['optimizer_steps'], adapter_state_sha256=checkpoint['adapter_state_sha256'],
        bundle_sha256=checkpoint['checkpoint_sha256'], rows=len(state['rows']), pending=None,
        full_AdamW_Python_CPU_CUDA_RNG=True, history_carry_state_sha256=saved['state_sha256'])


def verify_snapshot(snapshot, original_root, expected, original):
    original_inbox = SimpleNamespace(inbox=Path(original_root) / 'stream/inbox')
    class SnapshotJournal(original.journal.StreamJournal):
        def _inbox_event(self, message, path, source_sha256):
            return original.journal.StreamJournal._inbox_event(original_inbox, message, path, source_sha256)
    with SnapshotJournal(snapshot, create=False) as journal:
        latest = journal.latest_checkpoint()
        require(latest is not None and latest['expected_sha256'] == expected, 'full_original_journal_chain')


def readout_status(plan, saved, actor_pid, original):
    name = original.native.readout_name(plan, saved['cycle'])
    root = Path(plan['root']) / 'readouts'
    dispatch = root / (name + '_DISPATCH.json')
    complete = root / name / 'COMPLETE.json'
    failed = root / (name + '_FAILED.json')
    if not dispatch.exists():
        return None
    document = read(dispatch)
    require(document['resident_pid'] == actor_pid and document['cycle'] == saved['cycle']
            and document['checkpoint_sha256'] == sha(Path(plan['root']) / 'checkpoints' /
                 f"sleep_{saved['cycle']:06d}" / 'COMMIT.json'), 'exact_readout_dispatch')
    require(not failed.exists(), 'readout_failed_no_retirement')
    actor = Path('/proc') / str(actor_pid)
    children = actor.joinpath('task', str(actor_pid), 'children').read_text().split()
    active = []
    for child_pid in children:
        child = Path('/proc') / child_pid
        try:
            fields = child.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
            if fields[0] == 'Z':
                continue
            process = identity(int(child_pid))
        except FileNotFoundError:
            continue
        expected = [str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_readout', '--plan',
                    plan['_plan_path'], '--checkpoint', str(Path(plan['root']) / 'checkpoints' /
                    f"sleep_{saved['cycle']:06d}" / 'COMMIT.json'), '--output', str(root / name)]
        require(process['argv'] == expected and process['group'] == process['pid'],
                'only_independent_original_readout_child')
        active.append(process['pid'])
    return dict(dispatch_sha256=sha(dispatch), complete_marker=complete.exists(), active_pids=active,
                held_contents_read=False)


def pause_exact(expected, descriptor):
    require(identity(expected['pid']) == expected, 'identity_before_pause')
    signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        tasks = list((Path('/proc') / str(expected['pid']) / 'task').iterdir())
        if tasks and all((task / 'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't') for task in tasks):
            require(identity(expected['pid']) == expected, 'identity_after_pause')
            return
        time.sleep(.01)
    raise ValueError('all_threads_pause_timeout')


def resume_paused(paused, descriptors):
    for name in reversed(paused):
        try:
            signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
        except ProcessLookupError:
            pass
    paused.clear()


def stage(config_path, pid, output, cpu_path):
    config_path, output, cpu_path = map(regular, (config_path, output, cpu_path))
    config, plan, original = originals(config_path)
    require(output.parent == BASE and output.name.startswith('orch_r143_node5_allocator_'), 'own_unique_output')
    cpu = read(cpu_path)
    require(cpu['passed'] is True and cpu['tests_passed'] >= 15 and cpu['operator_sha256'] == sha(__file__),
            'own_bound_CPU_tests')
    allocator_environment(os.environ)
    pair = process_pair(pid, config_path, config, plan)
    actual_device = device(plan)
    subprocess.run(['sudo', '-n', 'true'], check=True, timeout=10)
    proposed = write_resume_guard(config, plan, output)
    original.guard.validate(output / 'GUARD.json')
    require(time.time() + 900 < plan['hard_end_unix'], 'original_wall_headroom')
    require(process_pair(pid, config_path, config, plan) == pair, 'setup_preserves_live_children')
    request = dict(old_config=str(config_path), old_config_sha256=sha(config_path),
        new_config=str(output / 'GUARD.json'), new_config_sha256=sha(output / 'GUARD.json'),
        plan_sha256=config['plan_sha256'], source_pins_sha256=digest(config['source_pins']),
        processes=pair, device=actual_device, operator_path=str(Path(__file__).resolve()),
        operator_sha256=sha(__file__), cpu_path=str(cpu_path), cpu_sha256=sha(cpu_path),
        physical=plan['physical'], staged_unix=time.time(), applied=False,
        original_supervise_unmodified=True, topology='inherited_environment_no_env_i',
        allocator={ALLOCATOR_KEY: ALLOCATOR_VALUE}, parent_changed=False, lease_changed=False)
    request['consumed_authorization_sha256'] = sha(output / 'CONSUMED_AUTHORIZATION.json')
    write(output / 'STAGED.json', request)
    return request


def patch_frozen_native(source, patcher):
    require(hashlib.sha256(source.encode()).hexdigest() == NATIVE_SHA, 'exact_node5_frozen_native_bytes')
    patched = patcher.patch_source(source)
    before, after = ast.parse(source), ast.parse(patched)
    require(patcher.without_sleep(before) == patcher.without_sleep(after), 'all_non_sleep_AST_unchanged')
    encoders = []
    for tree, text in ((before, source), (after, patched)):
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'encode_own']
        require(len(nodes) == 1, 'one_original_encoder')
        encoders.append(ast.get_source_segment(text, nodes[0]))
    require(encoders[0] == encoders[1], 'original_encoder_exact_bytes_preserved')
    return patched


def validate_new_guard(config_path):
    config = read(config_path)
    plan = read(config['plan_path'])
    command = [str(PYTHON), '-B', '-c',
        'import sys; from gpu.orch_r125_continual_guard import validate; validate(sys.argv[1]); print("ORIGINAL_GUARD_VALIDATED")',
        str(config_path)]
    result = subprocess.check_output(command, cwd=plan['source_root'], text=True, timeout=60,
        env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=plan['source_root']))
    require(result.strip() == 'ORIGINAL_GUARD_VALIDATED', 'isolated_original_guard_validation')


def relocate_startup(plan, source):
    proposed = deepcopy(plan)
    proposed['source_root'] = str(source)
    startup = plan.get('startup_context')
    if startup is None:
        return proposed, None
    original_path = regular(startup['path'])
    original_source = regular(plan['source_root'])
    require(original_path.is_relative_to(original_source), 'startup_inside_original_source')
    copied_path = regular(Path(source) / original_path.relative_to(original_source))
    require(sha(original_path) == sha(copied_path) == startup['sha256']
            and copied_path.read_text() == plan['birth_prompt'], 'startup_bytes_and_rendered_prompt_unchanged')
    proposed['startup_context']['path'] = str(copied_path)
    return proposed, dict(original_path=str(original_path), copied_path=str(copied_path),
                          sha256=startup['sha256'], prompt_bytes_unchanged=True)


def stage_prospective(config_path, pid, output, cpu_path, helper_path, patcher_path):
    config_path, output, cpu_path, helper_path, patcher_path = map(
        regular, (config_path, output, cpu_path, helper_path, patcher_path))
    config, plan, original = originals(config_path, prospective=True)
    require(output.parent == BASE and output.name.startswith('orch_r143_node5_target_allocator_')
            and not output.exists(), 'own_new_prospective_artifacts')
    cpu = read(cpu_path)
    require(cpu['passed'] is True and cpu['tests_passed'] >= 32 and cpu['operator_sha256'] == sha(__file__)
            and cpu['helper_sha256'] == sha(helper_path) and cpu['patcher_sha256'] == sha(patcher_path),
            'prospective_CPU_and_Main_input_bindings')
    pair = process_pair(pid, config_path, config, plan, allow_allocator=True)
    if plan['physical'] == 7:
        require(not any(value.startswith(('PYTORCH_CUDA_ALLOC_CONF=', 'PYTORCH_ALLOC_CONF='))
                        for process in pair.values() for value in process['environment']),
                'repo_reader_target_only_preserves_allocator_environment')
    actual_device = device(plan)
    spec = importlib.util.spec_from_file_location('r143_bound_Main_patcher', patcher_path)
    patcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(patcher)
    frozen = Path(plan['source_root']) / 'gpu/orch_r125_continual_native.py'
    patched = patch_frozen_native(frozen.read_text(), patcher)
    output.mkdir(exist_ok=False)
    source = output / 'source'
    shutil.copytree(plan['source_root'], source)
    require(sha(source / 'gpu/orch_r125_continual_native.py') == NATIVE_SHA, 'copied_frozen_native_exact')
    (source / 'gpu/orch_r125_continual_native.py').write_text(patched)
    helper_target = source / 'gpu/orch_r144_sleep_targets.py'
    require(not helper_target.exists(), 'new_helper_only')
    shutil.copyfile(helper_path, helper_target)
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    old_pins = config['source_pins']
    require(set(pins) - set(old_pins) == {'gpu/orch_r144_sleep_targets.py'}
            and set(old_pins) - set(pins) == set()
            and {name for name in old_pins if old_pins[name] != pins[name]} == {'gpu/orch_r125_continual_native.py'},
            'only_frozen_sleep_patch_plus_helper')
    records = [read(path) for path in record_paths(plan['root'])]
    if plan.get('authorized_wall_extension') is not None:
        states = [record['document']['resume_state']['state'] for record in records if record['kind'] == 'SLEEP_COMPLETE']
        resume_plan, consumed = consumed_authorization_plan(plan, config['plan_sha256'], records,
                                                          states[-1]['deadline_unix'])
    else:
        resume_plan = deepcopy(plan)
        consumed = dict(reason='ordinary_resume_without_one_shot_directive', deadline_changed=False)
    resume_plan, startup_proof = relocate_startup(resume_plan, source)
    require({key for key in set(plan) | set(resume_plan) if plan.get(key) != resume_plan.get(key)} <=
            {'source_root', 'authorized_wall_extension', 'startup_context'}, 'frozen_recipe_visibility_wall_preserved')
    write(output / 'PLAN.json', resume_plan)
    allocation = read(config['allocation_path'])
    require(allocation['plan_sha256'] == config['plan_sha256'], 'existing_allocation_for_same_life')
    write(output / 'ALLOCATION.json', dict(allocation, plan_sha256=sha(output / 'PLAN.json')))
    proposed = deepcopy(config)
    proposed.update(attempt_dir=str(output), resume=True, source_pins=pins,
        plan_path=str(output / 'PLAN.json'), plan_sha256=sha(output / 'PLAN.json'),
        allocation_path=str(output / 'ALLOCATION.json'), allocation_sha256=sha(output / 'ALLOCATION.json'))
    write(output / 'GUARD.json', proposed)
    validate_new_guard(output / 'GUARD.json')
    original.guard.validate(config_path)
    require(process_pair(pid, config_path, config, plan, allow_allocator=True) == pair,
            'original_child_kept_active_during_prospective_staging')
    proof = dict(policy=TARGET_POLICY, old_source_root=plan['source_root'], new_source_root=str(source),
        old_source_pins_sha256=digest(old_pins), new_source_pins_sha256=digest(pins),
        old_native_sha256=NATIVE_SHA, new_native_sha256=pins['gpu/orch_r125_continual_native.py'],
        helper_sha256=sha(helper_path), patcher_sha256=sha(patcher_path),
        patch_api='patch_source(source:str)->str', non_sleep_AST_unchanged=True,
        encoder_bytes_unchanged=True, recipe_visibility_deadline_unchanged=True,
        allocator_requested=plan['physical'] in (2, 6),
        startup_path_relocation=startup_proof,
        consumed_authorization=consumed, old_plan_sha256=config['plan_sha256'], new_plan_sha256=proposed['plan_sha256'])
    write(output / 'PROSPECTIVE_SOURCE_RECIPE.json', proof)
    request = dict(old_config=str(config_path), old_config_sha256=sha(config_path),
        new_config=str(output / 'GUARD.json'), new_config_sha256=sha(output / 'GUARD.json'),
        plan_sha256=config['plan_sha256'], processes=pair, device=actual_device,
        operator_path=str(Path(__file__).resolve()), operator_sha256=sha(__file__),
        cpu_path=str(cpu_path), cpu_sha256=sha(cpu_path), physical=plan['physical'],
        stage_unix=time.time(), applied=False, prospective_policy=TARGET_POLICY,
        source_recipe_sha256=sha(output / 'PROSPECTIVE_SOURCE_RECIPE.json'))
    write(output / 'STAGED.json', request)
    return request


def try_ready_lock(descriptor):
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def peers_safe(outputs, current):
    for output in outputs:
        output = regular(output)
        if output == current:
            continue
        if any((output / name).exists() for name in ('FAILED.json', 'EXIT.json', 'MONITOR_EXPIRED.json')):
            return False
        if list(output.glob('ERROR_*.json')):
            return False
        started = any((output / name).exists() for name in (
            'QUIESCENCE_STARTED.json', 'BOUNDARY.json', 'RETIRED.json', 'DISPATCHED.json'))
        if started:
            if not (output / 'LOADED_RECEIPT.json').exists():
                return False
            loaded = read(output / 'LOADED_RECEIPT.json')
            if identity(loaded['actor']['pid']) != loaded['actor']:
                return False
    return True


def validate_peer_controls(outputs, current):
    if not outputs:
        return
    require(len(outputs) == len(set(map(str, outputs))) == 3 and current in outputs,
            'exact_three_distinct_peer_controls')
    physicals = []
    for output in outputs:
        request = read(regular(output) / 'STAGED.json')
        require(request['operator_sha256'] == sha(__file__)
                and request['prospective_policy'] == TARGET_POLICY
                and request['new_config_sha256'] == sha(request['new_config'])
                and request['source_recipe_sha256'] == sha(regular(output) / 'PROSPECTIVE_SOURCE_RECIPE.json')
                and request['cpu_sha256'] == sha(request['cpu_path']), 'bound_peer_provenance')
        physicals.append(request['physical'])
    require(sorted(physicals) == [2, 6, 7], 'only_three_node5_continual_peers')


def predecessor_no_action(controls, stopped_path):
    stopped = read(stopped_path)
    require(stopped.get('automatic_retry') is False, 'predecessor_terminal_no_retry')
    for control in controls:
        control = regular(control)
        require(not any((control / name).exists() for name in (
            'BOUNDARY.json', 'RETIRED.json', 'DISPATCHED.json', 'LOADED_RECEIPT.json', 'COMPLETE.json')),
            'predecessor_action_started_no_takeover')
        require(not list(control.glob('ERROR_*.json')), 'predecessor_error_requires_diagnosis')
    expired = read(regular(controls[0]) / 'WAIT_EXPIRED.json')
    require(expired['status'] == 'NO_CLEAN_BOUNDARY_NO_RETIREMENT', 'predecessor_clean_wait_expiry')
    return dict(status='EXPIRED_WITHOUT_RETIREMENT', stopped_sha256=sha(stopped_path),
                expired_sha256=sha(regular(controls[0]) / 'WAIT_EXPIRED.json'))


def monitor(output, saved, plan, original, seconds=600, on_loaded=None):
    loaded = None
    deadline = min(time.monotonic() + seconds, time.monotonic() + plan['hard_end_unix'] - time.time() - 60)
    while time.monotonic() < deadline:
        require(not any((output / name).exists() for name in ('FAILED.json', 'EXIT.json')),
                'original_successor_failed_no_retry')
        for path in record_paths(plan['root']):
            if path.name <= Path(saved['record_path']).name:
                continue
            record = read(path)
            document = record['document']
            if record['kind'] == 'LOADED' and loaded is None:
                require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
                        'loaded_journal_hash')
                require(document['resume'] is True and document['optimizer_steps'] == saved['optimizer_steps']
                        and document['adapter_sha256'] == saved['adapter_state_sha256'], 'exact_saved_LOADED')
                actor = identity(document['pid'])
                require(actor['argv'][-1] == str(output / 'GUARD.json') and actor['cwd'] == plan['source_root']
                        and 'CUDA_VISIBLE_DEVICES=' + plan['gpu_uuid'] in actor['environment'], 'actual_allocator_and_UUID')
                if plan['physical'] in (2, 6):
                    require(ALLOCATOR_KEY + '=' + ALLOCATOR_VALUE in actor['environment'], 'actual_allocator_present')
                else:
                    require(not any(value.startswith(('PYTORCH_CUDA_ALLOC_CONF=', 'PYTORCH_ALLOC_CONF='))
                                    for value in actor['environment']), 'repo_reader_allocator_unchanged')
                admission = read(output / 'ADMISSION.json')
                require(admission['scanner_euid'] == 0 and admission['clear'] and not admission['blocking_reasons']
                        and admission['gpu']['uuid'] == plan['gpu_uuid'], 'original_privileged_admission_passed')
                loaded = dict(status=('ALLOCATOR_APPLIED_EXACT_SAVED_LOADED' if plan['physical'] in (2, 6)
                                      else 'TARGET_POLICY_EXACT_SAVED_LOADED'), actor=actor,
                    record_sha256=record['sha256'], record_index=record['index'],
                    optimizer_steps=document['optimizer_steps'], saved=saved, observed_unix=time.time())
                write(output / 'LOADED_RECEIPT.json', loaded)
                if on_loaded is not None:
                    on_loaded()
            if loaded and record['kind'] == 'COMMITTED':
                state = document['state']
                require(state['sha256'] == digest(state['state']) and state['state']['pending'] is None,
                        'first_new_commit_valid_state')
                boundary_state = read(saved['record_path'])['document']['resume_state']['state']
                require(state['state']['rows'][:saved['rows']] == boundary_state['rows']
                        and len(state['state']['rows']) == saved['rows'] + 1, 'old_rows_preserved_one_new_commit')
                result = dict(status=('ALLOCATOR_APPLIED_LOADED_AND_NEW_COMMIT' if plan['physical'] in (2, 6)
                                      else 'TARGET_POLICY_LOADED_AND_NEW_COMMIT'), physical=plan['physical'],
                    loaded_receipt_sha256=sha(output / 'LOADED_RECEIPT.json'), committed_index=record['index'],
                    committed_sha256=record['sha256'], old_rows_preserved=True, completed_unix=time.time())
                write(output / 'COMPLETE.json', result)
                return result
        time.sleep(2)
    result = dict(status='LOADED_ONLY' if loaded else 'DISPATCHED_NOT_YET_LOADED', observed_unix=time.time())
    write(output / 'MONITOR_EXPIRED.json', result)
    return result


def handoff(output, seconds, peer_outputs=()):
    require(type(seconds) is int and 1 <= seconds <= 1200, 'bounded_observer')
    output = regular(output)
    validate_peer_controls(peer_outputs, output)
    request = read(output / 'STAGED.json')
    require(sha(__file__) == request['operator_sha256'] and sha(request['cpu_path']) == request['cpu_sha256']
            and sha(request['old_config']) == request['old_config_sha256']
            and sha(request['new_config']) == request['new_config_sha256'], 'unchanged_staged_provenance')
    config, plan, original = originals(request['old_config'], prospective=bool(request.get('prospective_policy')))
    if request.get('prospective_policy'):
        require(request['prospective_policy'] == TARGET_POLICY
                and sha(output / 'PROSPECTIVE_SOURCE_RECIPE.json') == request['source_recipe_sha256'],
                'bound_prospective_source_recipe')
        validate_new_guard(request['new_config'])
    else:
        original.guard.validate(request['new_config'])
    plan = dict(plan, _plan_path=config['plan_path'])
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=plan['source_root'])
    if plan['physical'] in (2, 6):
        environment = allocator_environment(environment)
    else:
        require(not any(key in environment for key in (ALLOCATOR_KEY, 'PYTORCH_ALLOC_CONF')),
                'repo_reader_no_new_allocator')
    require(process_pair(request['processes']['actor']['pid'], request['old_config'], config, plan,
                         allow_allocator=bool(request.get('prospective_policy')))
            == request['processes'], 'same_original_processes')
    lock = os.open(BASE / 'orch_r143_node5_allocator_ROLLOUT.lock',
                   os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    descriptors, paused, handlers = {}, [], {}
    lock_held = False
    def release_lock():
        nonlocal lock_held
        if lock_held:
            fcntl.flock(lock, fcntl.LOCK_UN)
            lock_held = False
    def interrupted(signum, frame):
        raise SystemExit('interrupted_restore_paused_processes')
    try:
        (output / 'HANDOFF_ONCE').mkdir()
        handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGHUP)}
        for name, process in request['processes'].items():
            descriptors[name] = os.pidfd_open(process['pid'])
            require(identity(process['pid']) == process, 'pidfd_exact_identity')
        deadline = min(time.monotonic() + seconds, time.monotonic() + plan['hard_end_unix'] - time.time() - 300)
        write(output / 'OBSERVER_ARMED.json', dict(armed_unix=time.time(), seconds=seconds, children_running=True,
            ready_first=True, lock_held_during_wait=False, peers=[str(path) for path in peer_outputs]))
        cached_boundary = None
        while time.monotonic() < deadline:
            saved = sleep_boundary(plan['root'])
            if saved is None:
                time.sleep(1)
                continue
            status = readout_status(plan, saved, request['processes']['actor']['pid'], original)
            if status is None or not (status['complete_marker'] or status['active_pids']):
                time.sleep(.2)
                continue
            if cached_boundary != saved:
                prepared = output / ('BOUNDARY_PREP_' + str(time.time_ns()))
                shutil.copytree(Path(plan['root']) / 'stream', prepared)
                if sleep_boundary(plan['root']) != saved:
                    continue
                evidence = saved_evidence(plan, saved, original)
                verify_snapshot(prepared, plan['root'], saved['state_sha256'], original)
                cached_boundary = saved
            if sleep_boundary(plan['root']) != saved:
                continue
            if not try_ready_lock(lock):
                time.sleep(.2)
                continue
            lock_held = True
            if not peers_safe(peer_outputs, output):
                release_lock()
                time.sleep(.2)
                continue
            if sleep_boundary(plan['root']) != saved:
                release_lock()
                continue
            require(device(plan) == request['device'], 'unchanged_device_before_boundary_pause')
            write(output / 'QUIESCENCE_STARTED.json', dict(started_unix=time.time(),
                state_sha256=saved['state_sha256'], peer_outputs=[str(path) for path in peer_outputs]))
            for name in ('supervisor', 'timer', 'actor'):
                paused.append(name)
                pause_exact(request['processes'][name], descriptors[name])
            if sleep_boundary(plan['root']) != saved:
                resume_paused(paused, descriptors)
                raise ValueError('boundary_advanced_before_pause_live_child_restored')
            readout_deadline = min(deadline, time.monotonic() + 180)
            while time.monotonic() < readout_deadline:
                status = readout_status(plan, saved, request['processes']['actor']['pid'], original)
                if status and status['complete_marker'] and not status['active_pids']:
                    break
                time.sleep(.2)
            else:
                raise ValueError('readout_not_complete_restore_live_child')
            require(sleep_boundary(plan['root']) == saved, 'quiescent_boundary_unchanged')
            require(sorted(path.name for path in (Path(plan['root']) / 'stream/records').iterdir()) ==
                    sorted(path.name for path in (prepared / 'records').iterdir()), 'no_pending_record_intents')
            require(saved_evidence(plan, saved, original) == evidence, 'same_full_bundle_after_quiescence')
            if request.get('prospective_policy'):
                validate_new_guard(request['new_config'])
            else:
                original.guard.validate(request['new_config'])
            write(output / 'BOUNDARY.json', dict(**evidence, snapshot=str(prepared), readout=status,
                full_chain_verified=True, all_threads_quiescent=True, parent_untouched=True,
                prospective_source_recipe_sha256=request.get('source_recipe_sha256'), saved_unix=time.time()))
            for name in ('actor', 'timer', 'supervisor'):
                require(identity(request['processes'][name]['pid']) == request['processes'][name], 'identity_before_retirement')
                signal.pidfd_send_signal(descriptors[name], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
                require(bool(select.select([descriptors[name]], [], [], 20)[0]), 'exact_exit_without_KILL')
            paused.clear()
            write(output / 'RETIRED.json', dict(status='EXACT_OLD_PROCESSES_EXITED',
                processes=request['processes'], boundary_sha256=sha(output / 'BOUNDARY.json'), retired_unix=time.time()))
            command = [str(PYTHON), '-B', '-m', GUARD, 'supervise', '--config', request['new_config']]
            successor_plan = read(read(request['new_config'])['plan_path'])
            environment['PYTHONPATH'] = successor_plan['source_root']
            with (output / 'SUPERVISOR.log').open('x') as log:
                successor = subprocess.Popen(command, cwd=successor_plan['source_root'], env=environment,
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            write(output / 'DISPATCHED.json', dict(supervisor_pid=successor.pid, command=command,
                allocator={ALLOCATOR_KEY: ALLOCATOR_VALUE} if plan['physical'] in (2, 6) else {},
                original_supervise=True, dispatched_unix=time.time()))
            return monitor(output, evidence, successor_plan, original, on_loaded=release_lock)
        result = dict(status='NO_CLEAN_BOUNDARY_NO_RETIREMENT', expired_unix=time.time())
        write(output / 'WAIT_EXPIRED.json', result)
        return result
    except BaseException as error:
        write(output / ('ERROR_' + str(time.time_ns()) + '.json'), dict(error=str(error),
            error_type=type(error).__name__, retired=(output / 'RETIRED.json').exists(), observed_unix=time.time()))
        raise
    finally:
        resume_paused(paused, descriptors)
        release_lock()
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


def resume_retired(retired_output, output, cpu_path):
    retired_output, output, cpu_path = map(regular, (retired_output, output, cpu_path))
    require(output.parent == BASE and output.name.startswith('orch_r143_node5_allocator_'), 'own_unique_output')
    request = read(retired_output / 'STAGED.json')
    retired = read(retired_output / 'RETIRED.json')
    require(retired['status'] == 'EXACT_OLD_PROCESSES_EXITED'
            and retired['boundary_sha256'] == sha(retired_output / 'BOUNDARY.json'), 'proven_prior_retirement')
    require(read(retired_output / 'EXIT.json')['exit_code'] == 1
            and not (retired_output / 'LOADED_RECEIPT.json').exists()
            and 'ValueError: wall_extension_exact_prior_binding' in (retired_output / 'NATIVE.log').read_text(),
            'only_diagnosed_preload_consumed_authorization_failure')
    cpu = read(cpu_path)
    require(cpu['passed'] is True and cpu['tests_passed'] >= 28 and cpu['operator_sha256'] == sha(__file__),
            'repaired_operator_CPU_gate')
    config, plan, original = originals(request['old_config'])
    environment = allocator_environment(dict(os.environ, CUDA_VISIBLE_DEVICES='',
        PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=plan['source_root']))
    lock = os.open(BASE / 'orch_r143_node5_allocator_ROLLOUT.lock',
                   os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for process in retired['processes'].values():
            require(not (Path('/proc') / str(process['pid'])).exists(), 'old_retired_processes_absent')
        require(not (Path('/proc') / str(read(retired_output / 'LAUNCH.json')['pid'])).exists(),
                'failed_successor_timeout_absent')
        saved = sleep_boundary(plan['root'])
        previous = read(retired_output / 'BOUNDARY.json')
        require(saved is not None and saved['state_sha256'] == previous['state_sha256']
                and sha(saved['path']) == previous['record_sha256'], 'no_work_since_exact_retired_boundary')
        evidence = saved_evidence(plan, saved, original)
        require(all(evidence[key] == previous[key] for key in evidence), 'same_retired_adapter_AdamW_RNG_history')
        require(device(plan) == request['device'], 'same_retired_GPU_minor')
        write_resume_guard(config, plan, output)
        original.guard.validate(output / 'GUARD.json')
        snapshot = output / 'BOUNDARY_SNAPSHOT'
        shutil.copytree(Path(plan['root']) / 'stream', snapshot)
        verify_snapshot(snapshot, plan['root'], saved['state_sha256'], original)
        require(sleep_boundary(plan['root']) == saved, 'exact_boundary_before_restore')
        write(output / 'BOUNDARY.json', dict(**evidence, snapshot=str(snapshot), full_chain_verified=True,
            previous_retired_output=str(retired_output), no_reset=True, saved_unix=time.time()))
        write(output / 'CPU_GATE_BINDING.json', dict(cpu_sha256=sha(cpu_path), operator_sha256=sha(__file__)))
        command = [str(PYTHON), '-B', '-m', GUARD, 'supervise', '--config', str(output / 'GUARD.json')]
        with (output / 'SUPERVISOR.log').open('x') as log:
            successor = subprocess.Popen(command, cwd=plan['source_root'], env=environment,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(output / 'DISPATCHED.json', dict(supervisor_pid=successor.pid, command=command,
            allocator={ALLOCATOR_KEY: ALLOCATOR_VALUE}, original_supervise=True, dispatched_unix=time.time()))
        return monitor(output, evidence, plan, original)
    finally:
        os.close(lock)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'handoff', 'resume-retired', 'stage-prospective'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--old-config', type=Path)
    parser.add_argument('--pid', type=int)
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--retired-output', type=Path)
    parser.add_argument('--helper', type=Path)
    parser.add_argument('--patcher', type=Path)
    parser.add_argument('--seconds', type=int, default=600)
    parser.add_argument('--peer-output', type=Path, action='append', default=[])
    arguments = parser.parse_args()
    if arguments.action == 'stage':
        result = stage(arguments.old_config, arguments.pid, arguments.output, arguments.cpu)
    elif arguments.action == 'handoff':
        result = handoff(arguments.output, arguments.seconds, arguments.peer_output)
    elif arguments.action == 'resume-retired':
        result = resume_retired(arguments.retired_output, arguments.output, arguments.cpu)
    else:
        result = stage_prospective(arguments.old_config, arguments.pid, arguments.output, arguments.cpu,
                                   arguments.helper, arguments.patcher)
    print(json.dumps(result, sort_keys=True))
