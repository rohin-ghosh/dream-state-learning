"""Exact R157 C1-C5 same-life saved-boundary deadline handoff; never a new birth."""

import argparse
from contextlib import contextmanager
from copy import deepcopy
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid


AUTH_SHA = '05c50f8012559360221a889b26c00700a988878fbe4d32d30e3f786937dfc392'
HOST = 'ipp2-ovx-p1-10'
BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
NEW_WALL = 1789776000
CEILING = 1789776600
OLD_WALL = 1789617240
MODULE = 'gpu.orch_r157_community_wall_extension'
RELATIVE = MODULE.replace('.', '/') + '.py'
TEST_RELATIVE = 'tests/test_orch_r157_community_wall_extension.py'
TARGETS = {
    'C1': (0, 'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a', 1654505, '13482248'),
    'C2': (1, 'GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c', 1655096, '13485432'),
    'C3': (3, 'GPU-d23c9369-39cf-51fd-833e-13292f173006', 1657282, '13496892'),
    'C4': (4, 'GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d', 1655156, '13485842'),
    'C5': (5, 'GPU-65595cff-c6c2-c798-bc62-427168079270', 1655251, '13486031'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def regular(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts
            and not any(item.is_symlink() for item in (path, *path.parents)), 'absolute_unlinked_path')
    return path


def read(path):
    return json.loads(regular(path).read_bytes())


def sha(path):
    result = hashlib.sha256()
    with regular(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def reference(path):
    return dict(path=str(regular(path)), sha256=sha(path))


def bound(ref):
    require(sha(ref['path']) == ref['sha256'], 'bound_receipt_bytes')
    return read(ref['path'])


def write(path, value):
    path = regular(path)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), 0o444)


def files(root):
    root = regular(root)
    return {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob('*')) if path.is_file()}


def freeze(root):
    for path in sorted(root.rglob('*'), reverse=True):
        require(not path.is_symlink(), 'no_source_symlink')
        path.chmod(0o555 if path.is_dir() else 0o444)
    root.chmod(0o555)


def authorization(path, provenance_path):
    require(sha(path) == AUTH_SHA, 'exact_shared_R157_authorization')
    auth = read(path)
    require(auth['schema'] == 'R157_EXPLICIT_TEAM_NODE_RUNTIME_AUTHORIZATION_V1'
            and auth['host'] == HOST and set(TARGETS) <= set(auth['lives'])
            and auth['authorization_is_runtime_budget_not_provider_booking'] is True
            and auth['provider_reservation_expiry_verified'] is False
            and auth['must_abort_on_conflicting_real_reservation'] is True
            and auth['purchase_or_lease_transaction_authorized'] is False
            and auth['reset'] is False and auth['learning_recipe_change'] is False
            and auth['visibility_change'] is False, 'runtime_only_exact_scope')
    require(datetime.datetime.fromisoformat(auth['new_hard_end_utc']).timestamp() == NEW_WALL
            and datetime.datetime.fromisoformat(auth['runtime_resource_ceiling_utc']).timestamp() == CEILING
            and auth['safety_margin_seconds'] == 600, 'exact_new_runtime_ceiling')
    proof = read(provenance_path)
    require(proof['schema'] == 'R157_NODE5_TARGETED_RESERVATION_AUDIT_V1'
            and proof['host'] == HOST and proof['authorization_sha256'] == AUTH_SHA
            and proof['conflicting_real_reservation_found'] is False
            and proof['numeric_cutoff_is_not_booking'] is True, 'no_known_real_reservation_conflict')
    for receipt in proof['actual_reservation_receipts']:
        reservation = bound(receipt)
        require(reservation['host'] == HOST and reservation['reservation_end_unix'] >= CEILING,
                'actual_reservation_must_cover_runtime_ceiling')
    return auth


def scope(agent_id, config, plan):
    require(agent_id in TARGETS, 'only_C1_C5_not_protected')
    physical, gpu_uuid, unused_pid, unused_ticks = TARGETS[agent_id]
    life = BASE / ('orch_r153_community_' + agent_id + '_20260916_attempt1')
    require(plan['root'] == str(life / 'life') and plan['physical'] == physical
            and plan['gpu_uuid'] == gpu_uuid and config['device_containment']['minor'] == physical
            and config['device_containment']['uid'] == config['device_containment']['gid'] == 2524
            and config['host_sha256'] == hashlib.sha256(HOST.encode()).hexdigest(), 'exact_original_community_life')
    require(plan['hard_end_unix'] == config['hard_end_unix'] == OLD_WALL
            and plan['lease_end_unix'] == config['next_reserved_unix'] == OLD_WALL + 600
            and config['resume'] is False and 'authorized_wall_extension' not in plan
            and 'preupdate_recovery' not in plan, 'original_birth_one_prospective_handoff')


def identity(pid):
    proc = Path('/proc') / str(pid)
    fields = (proc / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[0] not in ('Z', 'X'), 'owned_process_alive')
    return dict(pid=pid, start_ticks=fields[19], parent=int(fields[1]), group=int(fields[2]),
        uid=proc.stat().st_uid, cgroup=(proc / 'cgroup').read_text().strip(),
        argv=(proc / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'),
        cwd=str((proc / 'cwd').resolve()), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def same(expected):
    require(identity(expected['pid']) == expected, 'exact_identity_no_pid_reuse')


def live_children(pid):
    children = set()
    for task in (Path('/proc') / str(pid) / 'task').iterdir():
        children.update(int(value) for value in (task / 'children').read_text().split())
    result = set()
    for child in children:
        try:
            identity(child)
        except (FileNotFoundError, ProcessLookupError, ValueError):
            continue
        result.add(child)
    return result


def check_children(pair, readout_pid=None):
    require(live_children(pair['supervisor']['pid']) == {pair['timer']['pid']}
            and live_children(pair['timer']['pid']) == {pair['actor']['pid']}
            and live_children(pair['actor']['pid']) <= ({readout_pid} if readout_pid else set()),
            'no_foreign_children_before_signals')


def process_pair(agent_id, config_path, config, plan):
    actor = identity(TARGETS[agent_id][2])
    require(actor['start_ticks'] == TARGETS[agent_id][3], 'original_native_start_ticks')
    timer = identity(actor['parent'])
    supervisor = identity(timer['parent'])
    expected = [str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(config_path)]
    require(actor['argv'] == expected and timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3]) and timer['argv'][4:] == expected,
            'exact_native_timeout_command')
    require(supervisor['argv'] == [str(PYTHON), '-B', '-m', 'gpu.orch_r153_community_runtime',
            'contained-native', '--config', str(config_path)] and actor['group'] == timer['group'] == timer['pid'],
            'exact_original_contained_supervisor')
    launch = read(Path(config['attempt_dir']) / 'LAUNCH.json')
    require(launch['pid'] == timer['pid'] and launch['parent_start_ticks'] == timer['start_ticks']
            and launch['guard_sha256'] == sha(config_path) and launch['plan_sha256'] == config['plan_sha256'],
            'original_launch_receipt_binding')
    pair = dict(actor=actor, timer=timer, supervisor=supervisor)
    for process in pair.values():
        require(process['uid'] == os.getuid() == 2524 and process['cwd'] == plan['source_root']
                and process['cgroup'] == '0::/system.slice/' + config['device_containment']['unit'] + '.service'
                and process['boot_id'] == actor['boot_id'], 'owned_same_source_cgroup_boot')
    return pair


def environment(source):
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                PYTHONPATH=str(source), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')


def original_validate(config_path):
    config = read(config_path)
    plan = read(config['plan_path'])
    subprocess.run([str(PYTHON), '-B', '-c',
        'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])', str(config_path)],
        cwd=plan['source_root'], env=environment(plan['source_root']), check=True, timeout=180)
    return config, plan


def stage(agent_id, config_path, auth_path, provenance_path, cpu_path, output):
    require(socket.gethostname() == HOST and os.getuid() == 2524
            and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'node5_CPU_operator_identity')
    authorization(auth_path, provenance_path)
    config, plan = original_validate(config_path)
    scope(agent_id, config, plan)
    cpu = read(cpu_path)
    helper = Path(__file__).absolute()
    tests = helper.parents[1] / TEST_RELATIVE
    require(cpu['passed'] is True and cpu['returncode'] == 0 and type(cpu['tests']) is int and cpu['tests'] > 0
            and cpu['helper_sha256'] == sha(helper) and cpu['tests_sha256'] == sha(tests), 'bound_actual_CPU_tests')
    output = regular(output)
    require(output.parent == BASE and output.name.startswith('orch_r157_community_' + agent_id + '_')
            and not output.exists(), 'new_own_control_namespace')
    pair = process_pair(agent_id, config_path, config, plan)
    original_files = files(Path(plan['source_root']))
    output.mkdir(mode=0o700)
    source = output / 'source'
    shutil.copytree(plan['source_root'], source)
    for path in (source, source / 'gpu', source / 'tests'):
        path.chmod(0o755)
    for name, source_path in ((RELATIVE, helper), (TEST_RELATIVE, tests)):
        require(not (source / name).exists(), 'new_helper_not_hotpatch')
        shutil.copyfile(source_path, source / name)
    require(all(sha(source / name) == checksum for name, checksum in original_files.items())
            and files(Path(plan['source_root'])) == original_files, 'unchanged_original_full_source')
    freeze(source)
    for name, source_path in (('AUTHORIZATION.json', auth_path), ('PROVENANCE.json', provenance_path), ('CPU.json', cpu_path)):
        shutil.copyfile(source_path, output / name)
        (output / name).chmod(0o444)
    request = dict(schema='R157_COMMUNITY_HANDOFF_REQUEST_V1', agent_id=agent_id,
        old_config=reference(config_path), old_plan=reference(config['plan_path']), pair=pair,
        authorization=reference(output / 'AUTHORIZATION.json'), provenance=reference(output / 'PROVENANCE.json'),
        cpu=reference(output / 'CPU.json'), original_files=original_files, source_files=files(source),
        source_root=str(source), output=str(output), helper_sha256=sha(helper), created_unix=time.time(),
        new_wall=NEW_WALL, runtime_resource_ceiling=CEILING, reset=False)
    require(sha(source / RELATIVE) == request['helper_sha256'], 'exact_staged_helper')
    write(output / 'REQUEST.json', request)
    return dict(status='STAGED_NOT_SIGNALED', request=reference(output / 'REQUEST.json'))


def saved_boundary(root):
    paths = sorted(path for path in (Path(root) / 'stream/records').glob('*.json')
                   if re.fullmatch(r'[0-9]{20}\.json', path.name))
    require(paths, 'existing_journal')
    record = read(paths[-1])
    if record['kind'] != 'SLEEP_COMPLETE':
        return None
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}), 'boundary_hash')
    document = record['document']
    state = document['resume_state']['state']
    require(document['status'] == 'COMPLETE' and document['resume_state']['sha256'] == digest(state)
            and state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
            and state['sleep_receipts'][-1]['status'] == 'COMPLETE', 'full_saved_quiescent_state')
    return dict(record=record, reference=reference(paths[-1]), state_sha256=digest(state),
                cycle=document['cycle'], index=record['index'])


def proposed_plan(old_plan, source, boundary):
    state = boundary['record']['document']['resume_state']['state']
    require(state['deadline_unix'] == old_plan['hard_end_unix'] == OLD_WALL
            and digest(state) == boundary['state_sha256'], 'exact_saved_prior_wall')
    plan = deepcopy(old_plan)
    plan.update(source_root=str(source), hard_end_unix=NEW_WALL, lease_end_unix=CEILING,
        authorized_wall_extension=dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
            previous_deadline_unix=OLD_WALL, previous_stream_sha256=boundary['state_sha256'],
            new_deadline_unix=NEW_WALL, lease_end_unix=CEILING, safety_margin_seconds=600))
    if plan.get('startup_context'):
        relative = Path(old_plan['startup_context']['path']).relative_to(old_plan['source_root'])
        plan['startup_context']['path'] = str(Path(source) / relative)
    check_plan_delta(old_plan, plan)
    return plan


def check_plan_delta(old, new):
    normalized = deepcopy(new)
    extension = normalized.pop('authorized_wall_extension')
    require(new['hard_end_unix'] == NEW_WALL and new['lease_end_unix'] == CEILING
            and extension['previous_deadline_unix'] == old['hard_end_unix']
            and extension['new_deadline_unix'] == NEW_WALL and extension['lease_end_unix'] == CEILING
            and extension['safety_margin_seconds'] == 600, 'exact_deadline_only_budget')
    for key in ('source_root', 'hard_end_unix', 'lease_end_unix'):
        normalized[key] = old[key]
    if old.get('startup_context'):
        relative = Path(old['startup_context']['path']).relative_to(old['source_root'])
        require(new['startup_context']['path'] == str(Path(new['source_root']) / relative), 'startup_bytes_relocation_only')
        normalized['startup_context']['path'] = old['startup_context']['path']
    require(normalized == old, 'all_learning_visibility_methods_exact')


def boundary_cpu(plan_path, boundary_path):
    plan = read(plan_path)
    code = '''import json,sys,random
from pathlib import Path
from gpu import orch_r125_continual_native as native
import torch
plan=native.read(sys.argv[1]); boundary=native.read(sys.argv[2])
envelope=boundary['record']['document']['resume_state']
stream=native.ContinualStream.restore(envelope,expected_sha256=envelope['sha256'])
commit_path=Path(plan['root'])/'checkpoints'/('sleep_%06d'%boundary['cycle'])/'COMMIT.json'
checkpoint=native.read(commit_path)
native.require(checkpoint==boundary['record']['document']['checkpoint'],'record_checkpoint_exact')
native.NativeChild.verify_checkpoint(checkpoint)
native.require(native.digest(checkpoint['checkpoint_sha256'])==stream.model_state_sha256,'model_history_RNG_binding')
payload=torch.load(checkpoint['optimizer_rng_path'],map_location='cpu',weights_only=False)
native.require(payload['optimizer_steps']==checkpoint['optimizer_steps']>0 and payload['optimizer']['state'] and payload['optimizer']['param_groups'] and payload['parameter_names'],'full_AdamW_not_reset')
native.require(len(payload['cuda_rng'])==1 and payload['cuda_rng'][0].device.type=='cpu','saved_single_device_RNG')
torch.Generator(device='cpu').set_state(payload['cpu_rng']); random.Random().setstate(payload['python_rng'])
extension=native.prepare_wall_extension(plan,stream,resume=True,plan_sha256=native.sha(sys.argv[1]))
native.require(not torch.cuda.is_initialized(),'CPU_only_validation')
print(json.dumps(dict(checkpoint_path=str(commit_path),checkpoint_sha256=native.sha(commit_path),optimizer_steps=checkpoint['optimizer_steps'],adapter_state_sha256=checkpoint['adapter_state_sha256'],bundle_sha256=checkpoint['checkpoint_sha256'],wall_record=extension)))
'''
    return json.loads(subprocess.check_output([str(PYTHON), '-B', '-c', code, str(plan_path), str(boundary_path)],
        cwd=plan['source_root'], env=environment(plan['source_root']), text=True, timeout=180))


def readout(root, config, plan, boundary, actor):
    revision = plan.get('readout_revision', 1)
    name = f"sleep_{boundary['cycle']:06d}" + (f'_r{revision}' if revision > 1 else '')
    directory = Path(root) / 'readouts' / name
    path = directory / 'REQUEST.json'
    if not path.exists():
        return None
    request = read(path)
    checkpoint = Path(root) / 'checkpoints' / f"sleep_{boundary['cycle']:06d}" / 'COMMIT.json'
    require(request['ppid'] == actor['pid'] and request['plan_path'] == config['plan_path']
            and request['plan_sha256'] == config['plan_sha256'] and request['gpu_uuid'] == plan['gpu_uuid']
            and request['checkpoint_path'] == str(checkpoint)
            and request['checkpoint_commit_sha256'] == sha(checkpoint), 'exact_readout_boundary_metadata')
    expected = None
    try:
        expected = identity(request['pid'])
    except (FileNotFoundError, ProcessLookupError, ValueError):
        require((directory / 'COMPLETE.json').exists(), 'readout_not_missing_without_complete')
    if expected:
        require(expected['parent'] == actor['pid'] and expected['group'] == expected['pid']
                and expected['group'] != actor['group'] and expected['cgroup'] == actor['cgroup']
                and expected['argv'] == [str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_readout',
                    '--plan', config['plan_path'], '--checkpoint', str(checkpoint), '--output', str(directory)],
                'same_life_independent_readout')
    return dict(directory=str(directory), request=reference(path), identity=expected)


def watchdog(actor_fd, reader, seconds):
    ready = select.select([reader], [], [], seconds)[0]
    if not ready or os.read(reader, 1) != b'D':
        try:
            signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
        except ProcessLookupError:
            pass


@contextmanager
def pause_watchdog(actor_fd, seconds):
    reader, writer = os.pipe()
    process = subprocess.Popen([str(PYTHON), '-B', str(Path(__file__).absolute()), 'watchdog',
        '--actor-fd', str(actor_fd), '--pipe-fd', str(reader), '--seconds', str(seconds)],
        pass_fds=(actor_fd, reader), start_new_session=True, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.close(reader)
    try:
        yield time.monotonic() + seconds
    finally:
        try:
            signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
        except ProcessLookupError:
            pass
        try:
            os.write(writer, b'D')
        except BrokenPipeError:
            pass
        os.close(writer)
        process.wait(timeout=5)


def pause_exact(actor, descriptor):
    same(actor)
    signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        tasks = list((Path('/proc') / str(actor['pid']) / 'task').iterdir())
        if tasks and all((path / 'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't') for path in tasks):
            same(actor)
            return
        time.sleep(0.01)
    raise TimeoutError('all_native_threads_not_paused')


def wait_readout(metadata, deadline):
    complete = Path(metadata['directory']) / 'COMPLETE.json'
    while time.monotonic() < deadline:
        if complete.exists():
            require(read(complete)['status'] == 'COMPLETE', 'successful_readout_metadata')
            expected = metadata['identity']
            if expected is None:
                return reference(complete)
            try:
                same(expected)
            except (FileNotFoundError, ProcessLookupError, ValueError):
                return reference(complete)
        time.sleep(0.25)
    raise TimeoutError('readout_finish_before_handoff')


def verify_snapshot(snapshot, original_root, boundary):
    records = snapshot / 'records'
    paths = sorted(path for path in records.glob('*.json') if re.fullmatch(r'[0-9]{20}\.json', path.name))
    manifest = read(snapshot / 'JOURNAL.json')
    previous = digest(manifest)
    for index, path in enumerate(paths):
        record = read(path)
        require(record['index'] == index and record['journal_id'] == manifest['journal_id']
                and record['previous_sha256'] == previous
                and record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
                'preserved_full_journal_chain')
        intent = read(records / (path.stem + '.intent.json'))
        require(intent['record_sha256'] == record['sha256'] and intent['index'] == index
                and intent['previous_sha256'] == previous, 'preserved_intent_binding')
        if record['kind'] == 'INBOX':
            data = record['document']
            original = Path(data['source_id'])
            require(original.parent == Path(original_root) / 'stream/inbox'
                    and sha(snapshot / 'inbox' / original.name) == data['source_sha256'], 'preserved_delivery_identity')
        previous = record['sha256']
    require(paths and sha(paths[-1]) == boundary['reference']['sha256'], 'snapshot_exact_saved_frontier')


def build_control(output, request, old_config, old_plan, boundary):
    control = output / 'control'
    control.mkdir(mode=0o700)
    write(control / 'BOUNDARY.json', boundary)
    plan = proposed_plan(old_plan, request['source_root'], boundary)
    write(control / 'PLAN.json', plan)
    budget = dict(schema='R157_AUTHORIZED_RUNTIME_RESOURCE_BUDGET_V1',
        authorization=request['authorization'], provenance=request['provenance'],
        previous_receipt=reference(old_config['lease_path']), hard_end_unix=NEW_WALL,
        lease_end_unix=CEILING, safety_margin_seconds=600, provider_booking_verified=False,
        lease_end_field_semantics='COMPATIBILITY_RUNTIME_RESOURCE_CEILING_NOT_PURCHASE_EXPIRY',
        purchase_performed=False, new_runtime_authority='EXACT_USER_R157', node='ovx3')
    write(control / 'LEASE_BUDGET.json', budget)
    write(control / 'ALLOCATION.json', dict(schema='R125_NATIVE_ALLOCATION_V1',
        builder_entry='R157 exact user-authorized saved-state deadline-only community handoff',
        builder_entry_pushed=True, builder_entry_posted=True, git_push_performed=False,
        legacy_builder_entry_pushed_semantics='LOCAL_POSTING_COMPATIBILITY_NOT_GIT_PUSH',
        cpu_tests_passed=True, declared_unix=time.time(), plan_sha256=sha(control / 'PLAN.json'),
        gpu_uuid=plan['gpu_uuid'], physical=plan['physical'], checkpoint_resume=True))
    config = {key: deepcopy(value) for key, value in old_config.items() if not key.startswith('r153_')}
    config.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        lease_path=str(control / 'LEASE_BUDGET.json'), lease_sha256=sha(control / 'LEASE_BUDGET.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        attempt_dir=str(output / 'attempt'), resume=True, hard_end_unix=NEW_WALL, next_reserved_unix=CEILING,
        source_pins={name: checksum for name, checksum in request['source_files'].items() if name.endswith('.py')},
        r157_request=reference(output / 'REQUEST.json'), r157_boundary=reference(control / 'BOUNDARY.json'))
    config['device_containment']['unit'] = 'orch-r157-native-' + uuid.uuid4().hex
    write(control / 'GUARD.json', config)
    return control / 'GUARD.json'


def validate_resume(config_path):
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(config_path)
    request = bound(config['r157_request'])
    auth = bound(request['authorization'])
    bound(request['provenance'])
    authorization(request['authorization']['path'], request['provenance']['path'])
    old_config = bound(request['old_config'])
    old_plan = bound(request['old_plan'])
    scope(request['agent_id'], old_config, old_plan)
    check_plan_delta(old_plan, plan)
    boundary = bound(config['r157_boundary'])
    require(config['resume'] is True and plan == proposed_plan(old_plan, request['source_root'], boundary)
            and config['next_reserved_unix'] == CEILING and auth['reset'] is False, 'same_life_resume_never_reset')
    require(files(Path(plan['source_root'])) == request['source_files'], 'entire_new_source_immutable_bytes')
    for path in (Path(plan['source_root']), *Path(plan['source_root']).rglob('*')):
        require(not path.is_symlink() and path.stat().st_mode & 0o222 == 0, 'immutable_source_permissions')
    expected_policy = dict(old_config['device_containment'], unit=config['device_containment']['unit'])
    require(config['device_containment'] == expected_policy
            and re.fullmatch(r'orch-r157-native-[0-9a-f]{32}', expected_policy['unit']), 'unchanged_device_envelope')
    return config, plan


def containment_command(config, plan):
    policy = config['device_containment']
    require(plan['hard_end_unix'] == NEW_WALL and plan['lease_end_unix'] == CEILING
            and plan['physical'] == policy['minor'] in (0, 1, 3, 4, 5)
            and any(plan['physical'] == target[0] and plan['gpu_uuid'] == target[1] for target in TARGETS.values())
            and policy['uid'] == policy['gid'] == 2524, 'exact_R157_single_node_device_policy')
    remaining = math.floor(NEW_WALL - time.time())
    require(remaining > 30, 'runtime_time_remaining')
    properties = dict(User='2524', Group='2524', NoNewPrivileges='yes', DevicePolicy='strict',
        CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes', RuntimeMaxSec=str(remaining),
        TimeoutStopSec='5', KillMode='control-group', WorkingDirectory=plan['source_root'])
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
               '/dev/nvidia' + str(policy['minor']) + ' rw', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + policy['unit'],
        *['--property=' + key + '=' + value for key, value in properties.items()], '--property=DeviceAllow=',
        *['--property=DeviceAllow=' + value for value in devices], '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin',
        'HOME=' + str(Path(plan['root']).parent), 'CUDA_VISIBLE_DEVICES=' + plan['gpu_uuid'],
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + plan['source_root'], 'HF_HUB_OFFLINE=1',
        'TRANSFORMERS_OFFLINE=1', 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True',
        'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1', 'TOKENIZERS_PARALLELISM=false',
        str(PYTHON), '-B', '-m', MODULE, 'contained-native', '--config', config['r157_config_path']]


def supervise_once(config_path):
    config, plan = validate_resume(config_path)
    attempt = regular(config['attempt_dir'])
    attempt.mkdir(mode=0o700, exist_ok=False)
    (attempt / 'DISPATCH_ONCE').mkdir()
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + plan['source_root'], str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard',
        'scan', '--config', str(config_path)]
    report = json.loads(subprocess.check_output(command, cwd=plan['source_root'], text=True, timeout=100))
    write(attempt / 'ADMISSION.json', report)
    require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['gpu_uuid'], 'original_privileged_exclusive_admission')
    write(attempt / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    validate_resume(config_path)
    config['r157_config_path'] = str(config_path)
    command = containment_command(config, plan)
    write(attempt / 'CONTAINED_COMMAND.json', dict(command=command, started_unix=time.time()))
    result = subprocess.run(command, check=False)
    write(attempt / 'SERVICE_EXIT.json', dict(returncode=result.returncode, no_retry=True, finished_unix=time.time()))
    require(result.returncode == 0, 'contained_service_failed_no_retry')


def supervise(config_path):
    config = read(config_path)
    attempt = regular(config['attempt_dir'])
    existed = attempt.exists()
    try:
        return supervise_once(config_path)
    except BaseException as error:
        if not existed and attempt.exists() and not (attempt / 'FAILED.json').exists():
            write(attempt / 'FAILED.json', dict(error_type=type(error).__name__, reason=str(error),
                failed_unix=time.time(), no_retry=True))
        raise


def contained_native(config_path):
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r153_community_runtime import verify_containment
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    config, plan = validate_resume(config_path)
    attempt = Path(config['attempt_dir'])
    write(attempt / 'CONTAINMENT_VERIFIED.json', verify_containment(config, plan))
    report = read(attempt / 'ADMISSION.json')
    admitted = read(attempt / 'ADMISSION_TIME.json')['verified_unix']
    require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['gpu_uuid'] and 0 <= time.time() - admitted < 100,
            'fresh_original_admission_before_native')
    remaining = int(NEW_WALL - time.time() - 10)
    require(remaining > 10, 'time_for_native_resume')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's', str(PYTHON),
        '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(config_path)]
    process = None
    try:
        with (attempt / 'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            timer = identity(process.pid)
            publish_launch(attempt / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=timer['start_ticks'],
                started_unix=time.time(), admission_verified_unix=admitted, admission_sha256=sha(attempt / 'ADMISSION.json'),
                guard_sha256=sha(config_path), plan_sha256=config['plan_sha256'], gpu_uuid=plan['gpu_uuid'],
                command_sha256=native.digest(command), hard_end_unix=NEW_WALL, no_retry=True))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            result = process.wait()
        write(attempt / 'NATIVE_EXIT.json', dict(returncode=result, no_retry=True, finished_unix=time.time()))
        require(result == 0, 'native_failed_no_retry')
    except BaseException:
        reap_owned_child(process)
        raise


def observe_applied(output, config_path, boundary, proof, seconds=1200):
    config = read(config_path)
    plan = read(config['plan_path'])
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        paths = sorted(path for path in (Path(plan['root']) / 'stream/records').glob('*.json')
                       if re.fullmatch(r'[0-9]{20}\.json', path.name) and int(path.stem) > boundary['index'])
        records = [(path, read(path)) for path in paths]
        extended = [(path, record) for path, record in records if record['kind'] == 'WALL_EXTENDED']
        loaded = [(path, record) for path, record in records if record['kind'] == 'LOADED']
        if extended and loaded:
            require(len(extended) == 1 and extended[0][1]['document'] == proof['wall_record'], 'actual_exact_WALL_EXTENDED')
            document = loaded[0][1]['document']
            require(document['resume'] is True and document['optimizer_steps'] == proof['optimizer_steps']
                    and document['adapter_sha256'] == proof['adapter_state_sha256'], 'actual_LOADED_saved_state_not_reset')
            actor = identity(document['pid'])
            timer = identity(actor['parent'])
            launch = read(Path(config['attempt_dir']) / 'LAUNCH.json')
            require(timer['pid'] == launch['pid'] and timer['start_ticks'] == launch['parent_start_ticks']
                    and actor['argv'][-2:] == ['--config', str(config_path)], 'actual_new_native_timeout')
            boot = next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime '))
            expiry = boot + int(timer['start_ticks']) / os.sysconf('SC_CLK_TCK') + int(timer['argv'][3][:-1])
            require(NEW_WALL - 30 <= expiry <= NEW_WALL, 'actual_timeout_matches_new_wall')
            result = dict(status='APPLIED_WALL_EXTENDED_AND_LOADED', applied_unix=time.time(),
                wall_extended=reference(extended[0][0]), loaded=reference(loaded[0][0]), old_boundary=boundary['reference'],
                optimizer_steps=proof['optimizer_steps'], adapter_state_sha256=proof['adapter_state_sha256'],
                actor=actor, timer=timer, timeout_expiry_approx_unix=expiry, new_wall=NEW_WALL,
                runtime_resource_ceiling=CEILING, original_root=plan['root'], reset=False,
                provider_booking_claimed=False, source_root=plan['source_root'])
            write(output / 'APPLIED.json', result)
            return result
        if any((Path(config['attempt_dir']) / name).exists() for name in ('SERVICE_EXIT.json', 'FAILED.json')):
            raise RuntimeError('successor_exited_before_applied_no_retry')
        time.sleep(2)
    raise TimeoutError('no_verified_LOADED_yet_no_retry_or_signal')


def handoff(output, seconds=3600):
    output = regular(output)
    request = read(output / 'REQUEST.json')
    require(socket.gethostname() == HOST and os.getuid() == 2524
            and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'node5_CPU_operator_identity')
    authorization(request['authorization']['path'], request['provenance']['path'])
    bound(request['authorization']); bound(request['provenance']); bound(request['cpu'])
    require(sha(Path(__file__).absolute()) == request['helper_sha256'], 'pinned_operator_before_signals')
    old_config = bound(request['old_config']); old_plan = bound(request['old_plan'])
    scope(request['agent_id'], old_config, old_plan)
    original_validate(request['old_config']['path'])
    require(files(Path(request['source_root'])) == request['source_files'], 'staged_source_unchanged')
    pair = process_pair(request['agent_id'], request['old_config']['path'], old_config, old_plan)
    require(pair == request['pair'] and type(seconds) is int and 1 <= seconds <= 5400, 'exact_prepared_pair_and_wait')
    lock = os.open(BASE / ('orch_r157_' + request['agent_id'] + '_HANDOFF.lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    descriptors = {}
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (output / 'HANDOFF_ONCE').mkdir()
        for name, process in pair.items():
            same(process)
            descriptors[name] = os.pidfd_open(process['pid'])
            same(process)
        deadline = min(time.monotonic() + seconds, time.monotonic() + OLD_WALL - time.time() - 120)
        write(output / 'ARMED.json', dict(pair=pair, started_unix=time.time(), operator_pid=os.getpid(), signals_sent=0))
        while time.monotonic() < deadline:
            same(pair['actor'])
            boundary = saved_boundary(old_plan['root'])
            metadata = readout(old_plan['root'], old_config, old_plan, boundary, pair['actor']) if boundary else None
            if metadata is None:
                time.sleep(0.25)
                continue
            check_children(pair, metadata['identity']['pid'] if metadata['identity'] else None)
            with pause_watchdog(descriptors['actor'], min(900, max(60, int(deadline - time.monotonic())))) as pause_deadline:
                pause_exact(pair['actor'], descriptors['actor'])
                checked = saved_boundary(old_plan['root'])
                if checked is None or checked['reference'] != boundary['reference']:
                    continue
                completion = wait_readout(metadata, pause_deadline - 90)
                require(saved_boundary(old_plan['root'])['reference'] == boundary['reference'], 'boundary_unchanged_after_readout')
                snapshot = output / 'preserved_stream'
                shutil.copytree(Path(old_plan['root']) / 'stream', snapshot)
                verify_snapshot(snapshot, old_plan['root'], boundary)
                checkpoint = Path(old_plan['root']) / 'checkpoints' / f"sleep_{boundary['cycle']:06d}"
                inventory = files(checkpoint)
                shutil.copytree(checkpoint, output / 'preserved_checkpoint')
                require(files(output / 'preserved_checkpoint') == inventory == files(checkpoint), 'full_saved_checkpoint_copy')
                config_path = build_control(output, request, old_config, old_plan, boundary)
                proof = boundary_cpu(Path(config_path).parent / 'PLAN.json', Path(config_path).parent / 'BOUNDARY.json')
                write(output / 'SAVED_PROOF.json', proof)
                write(output / 'READOUT_FINISHED.json', completion)
                original_validate(config_path)
                authorization(request['authorization']['path'], request['provenance']['path'])
                require(time.monotonic() + 60 < pause_deadline
                        and saved_boundary(old_plan['root'])['reference'] == boundary['reference']
                        and files(Path(old_plan['source_root'])) == request['original_files'], 'last_pre_exit_preservation_gate')
                for process in pair.values():
                    same(process)
                check_children(pair)
                signal.pidfd_send_signal(descriptors['actor'], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
                for name in ('actor', 'timer', 'supervisor'):
                    require(bool(select.select([descriptors[name]], [], [], 20)[0]), 'natural_owned_exit_' + name)
                require(saved_boundary(old_plan['root'])['reference'] == boundary['reference']
                        and files(checkpoint) == inventory, 'postexit_no_unsaved_suffix')
                write(output / 'RETIRED_FOR_SAME_LIFE_RESUME.json', dict(pair=pair, boundary=boundary['reference'],
                    checkpoint_files=inventory, same_root=old_plan['root'], stopped_unix=time.time(), reset=False))
                break
        else:
            raise TimeoutError('no_saved_boundary_original_left_running')
        with (output / 'SUCCESSOR.log').open('x') as log:
            process = subprocess.Popen([str(PYTHON), '-B', '-m', MODULE, 'supervise', '--config', str(config_path)],
                cwd=request['source_root'], env=environment(request['source_root']), stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(output / 'SUCCESSOR_DISPATCH.json', dict(pid=process.pid, started_unix=time.time(), no_retry=True))
        return observe_applied(output, config_path, boundary, proof)
    except BaseException as error:
        if not (output / 'FAILED.json').exists():
            write(output / 'FAILED.json', dict(error_type=type(error).__name__, reason=str(error),
                failed_unix=time.time(), no_retry=True, original_source_preserved=True))
        raise
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    staging = commands.add_parser('stage')
    staging.add_argument('--agent', choices=tuple(TARGETS), required=True)
    for name in ('config', 'authorization', 'provenance', 'cpu', 'output'):
        staging.add_argument('--' + name, type=Path, required=True)
    operation = commands.add_parser('handoff')
    operation.add_argument('--output', type=Path, required=True)
    operation.add_argument('--seconds', type=int, default=3600)
    operation.add_argument('--execute-handoff', action='store_true', required=True)
    for name in ('supervise', 'contained-native'):
        command = commands.add_parser(name)
        command.add_argument('--config', type=Path, required=True)
    watcher = commands.add_parser('watchdog')
    watcher.add_argument('--actor-fd', type=int, required=True)
    watcher.add_argument('--pipe-fd', type=int, required=True)
    watcher.add_argument('--seconds', type=int, required=True)
    args = parser.parse_args()
    if args.action == 'stage':
        print(json.dumps(stage(args.agent, args.config, args.authorization, args.provenance, args.cpu, args.output)))
    elif args.action == 'handoff':
        print(json.dumps(handoff(args.output, args.seconds)))
    elif args.action == 'supervise':
        supervise(args.config)
    elif args.action == 'contained-native':
        contained_native(args.config)
    else:
        watchdog(args.actor_fd, args.pipe_fd, args.seconds)


if __name__ == '__main__':
    main()
