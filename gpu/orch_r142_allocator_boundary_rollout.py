"""Allocator-only ovx2 observer and original programmes-family boundary handoff."""

import argparse
from copy import deepcopy
import hashlib
import fcntl
import importlib
import json
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
from types import SimpleNamespace
import uuid


HOST = 'ipp2-ovx-p6-09'
BASE = Path('/localhome/local-rohing')
ALLOCATOR = 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True'
DEVICES = {
    0: 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939',
    1: 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821',
    2: 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1',
    3: 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e',
    4: 'GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4',
    7: 'GPU-319224de-e668-1822-d80b-4b24d15968ae',
}
NATIVE = 'gpu.orch_r125_continual_guard'
SCHEMA = 'R142_ALLOCATOR_READINESS_V1'
FAMILY = {3: 'brain_guided', 4: 'creative_free', 7: 'creative_select'}
PYTHON = BASE / 'v2/venv/bin/python'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def regular(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_canonical_path')
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), 'no_symlinks')
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


def scope(plan):
    physical = plan['physical']
    require(type(physical) is int and physical in DEVICES, 'ovx2_only_exclude5_6')
    require(plan['gpu_uuid'] == DEVICES[physical], 'unchanged_owned_UUID')
    for key in ('root', 'source_root'):
        path = regular(plan[key])
        require(path.is_relative_to(BASE), 'original_node3_root')
    return physical


def proposed_guard(config, attempt):
    attempt = regular(attempt)
    require(attempt != Path(config['attempt_dir']) and not attempt.exists(), 'new_attempt_only')
    proposed = deepcopy(config)
    proposed.update(attempt_dir=str(attempt), resume=True)
    require({key for key in proposed if proposed[key] != config.get(key)} <=
            {'attempt_dir', 'resume'}, 'original_bindings_unchanged')
    return proposed


def allocator_command(command):
    command = list(command)
    require(command.count('/usr/bin/env') == 1, 'one_contained_env')
    position = command.index('/usr/bin/env')
    require(command[position + 1:position + 2] == ['-i'], 'contained_clean_environment_required')
    require('systemd-run' in command[:position] and '--property=DevicePolicy=strict' in command[:position],
            'strict_containment_required')
    require(not any(value.startswith(('PYTORCH_CUDA_ALLOC_CONF=', 'PYTORCH_ALLOC_CONF='))
                    for value in command), 'no_existing_allocator_override')
    result = command[:position + 2] + [ALLOCATOR] + command[position + 2:]
    require(result[:position + 2] + result[position + 3:] == command, 'only_inner_env_addition')
    return result


def identity(pid):
    process = Path('/proc') / str(pid)
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[0] not in ('Z', 'T', 't', 'X'), 'native_not_active')
    args = (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    require(len(args) == 7 and args[1:6] == ['-B', '-m', NATIVE, 'native', '--config'],
            'exact_native_command')
    environment = (process / 'environ').read_bytes().split(b'\0')
    selected = [item.decode() for item in environment if item.startswith(
        (b'CUDA_VISIBLE_DEVICES=', b'PYTORCH_CUDA_ALLOC_CONF=', b'PYTORCH_ALLOC_CONF='))]
    return dict(pid=pid, start_ticks=fields[19], parent=int(fields[1]), group=int(fields[2]),
                argv=args, cwd=str((process / 'cwd').resolve()), environment=selected,
                uid=process.stat().st_uid)


def inventory():
    require(socket.gethostname() == HOST, 'exact_ovx2_host')
    lanes = {}
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            args = (process / 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
            if len(args) != 7 or args[1:6] != [b'-B', b'-m', NATIVE.encode(), b'native', b'--config']:
                continue
            path = regular(args[-1].decode())
            if any(name in str(path) for name in ('support_none', 'creative_none')):
                continue
            config = read(path)
            plan = read(config['plan_path'])
            physical = scope(plan)
            require(physical not in lanes, 'ambiguous_multiple_native_children')
            owned = identity(int(process.name))
            require(owned['cwd'] == plan['source_root'] and owned['uid'] == os.getuid(), 'original_native_source_owner')
            require('CUDA_VISIBLE_DEVICES=' + plan['gpu_uuid'] in owned['environment'], 'native_UUID_environment')
            require(sha(config['plan_path']) == config['plan_sha256'], 'original_plan_hash')
            require(sha(config['lease_path']) == config['lease_sha256'], 'original_lease_hash')
            require(sha(config['allocation_path']) == config['allocation_sha256'], 'original_allocation_hash')
            actual = {str(item.relative_to(plan['source_root'])): sha(item)
                      for item in Path(plan['source_root']).rglob('*.py')}
            require(actual == config['source_pins'], 'entire_original_source_closure')
            launch_path = Path(config['attempt_dir']) / 'LAUNCH.json'
            launch = read(launch_path)
            require(launch['pid'] == owned['parent'] and launch['guard_sha256'] == sha(path)
                    and launch['plan_sha256'] == config['plan_sha256'], 'original_launch_ancestry')
            require(identity(int(process.name)) == owned, 'identity_stable_during_inventory')
            lanes[physical] = dict(physical=physical, gpu_uuid=plan['gpu_uuid'], process=owned,
                guard_path=str(path), guard_sha256=sha(path), plan_path=config['plan_path'],
                plan_sha256=config['plan_sha256'], root=plan['root'], source_root=plan['source_root'],
                source_pins_sha256=digest(actual), lease_sha256=config['lease_sha256'],
                allocation_sha256=config['allocation_sha256'], launch_sha256=sha(launch_path),
                containment=config.get('device_containment'), launch_ready=False)
        except (FileNotFoundError, ProcessLookupError):
            continue
    return dict(schema=SCHEMA, host=HOST, observed_unix=time.time(), lanes=list(lanes.values()),
                missing_physical=sorted(set(DEVICES) - set(lanes)), excluded_physical=[5, 6],
                signal_count=0, launch_count=0, admission=False)


def journal_head(root):
    paths = sorted(path for path in (regular(root) / 'stream/records').glob('*.json')
                   if re.fullmatch(r'\d{20}\.json', path.name))
    require(paths, 'published_records_required')
    return paths[-1]


def boundary(lane):
    require(identity(lane['process']['pid']) == lane['process'], 'exact_inventory_identity')
    require(sha(lane['guard_path']) == lane['guard_sha256'], 'guard_unchanged')
    head = journal_head(lane['root'])
    head_file_sha256 = sha(head)
    record = read(head)
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
            'journal_head_hash')
    result = dict(physical=lane['physical'], observed_unix=time.time(), head=str(head),
                  head_sha256=record['sha256'], kind=record['kind'], launch_ready=False)
    if record['kind'] != 'SLEEP_COMPLETE':
        return dict(result, status='WAIT_NO_CLEAN_BOUNDARY')
    document = record['document']
    envelope = document['resume_state']
    state = envelope['state']
    require(envelope['sha256'] == digest(state), 'saved_state_hash')
    require(document['status'] == 'COMPLETE' and state['pending'] is None
            and state['sleep_frontier'] == len(state['rows']) and state['sleep_receipts']
            and state['sleep_receipts'][-1]['status'] == 'COMPLETE', 'no_abandoned_pending_work')
    checkpoint = document['checkpoint']
    checkpoint_root = regular(lane['root']) / 'checkpoints' / f"sleep_{document['cycle']:06d}"
    require(regular(checkpoint['optimizer_rng_path']) == checkpoint_root / 'optimizer_rng.pt'
            and regular(checkpoint['adapter_path']) == checkpoint_root / 'adapter', 'exact_saved_bundle_paths')
    require(read(checkpoint_root / 'COMMIT.json') == checkpoint, 'original_checkpoint_commit')
    require(checkpoint['experiment'] == state['experiment'], 'checkpoint_same_experiment')
    require(digest(checkpoint['checkpoint_sha256']) == state['model_state_sha256'], 'saved_model_binding')
    require(sha(checkpoint['optimizer_rng_path']) == checkpoint['checkpoint_sha256']['optimizer']
            == checkpoint['checkpoint_sha256']['rng'], 'AdamW_RNG_saved_bytes')
    files = {path.name: sha(path) for path in regular(checkpoint['adapter_path']).iterdir() if path.is_file()}
    require(files == checkpoint['adapter_files'] and digest(files) == checkpoint['checkpoint_sha256']['adapter'],
            'saved_adapter_bytes')
    if journal_head(lane['root']) != head or sha(head) != head_file_sha256:
        return dict(result, status='WAIT_MOVED_BOUNDARY')
    require(identity(lane['process']['pid']) == lane['process'], 'identity_after_boundary_hashing')
    return dict(result, status='OBSERVED_SAVED_BOUNDARY_NOT_ADMISSION', cycle=document['cycle'],
                state_sha256=envelope['sha256'], checkpoint_sha256=checkpoint['checkpoint_sha256'],
                optimizer_steps=checkpoint['optimizer_steps'], history_carry_preserved=True,
                full_journal_chain_verified=False, stopped_snapshot_verified=False,
                blocker='specialized_handoff_not_generalized; no_retirement_or_launch_authority_from_observation')


def observe(output, seconds, interval):
    require(type(seconds) is int and 1 <= seconds <= 600, 'bounded_observation_1_600_seconds')
    require(0.5 <= interval <= 30, 'bounded_poll_interval')
    output = regular(output)
    require(output.parent == BASE and output.name.startswith('orch_r142_allocator_ovx2_'), 'unique_operator_output_only')
    output.mkdir(exist_ok=False)
    state = inventory()
    write(output / 'INVENTORY.json', state)
    for lane in state['lanes']:
        proposed = proposed_guard(read(lane['guard_path']), output / f"physical{lane['physical']}_attempt1")
        write(output / f"GUARD_PROPOSAL_PHYSICAL{lane['physical']}.json", proposed)
    deadline = time.monotonic() + seconds
    samples = 0
    observed = set()
    while time.monotonic() < deadline:
        for lane in state['lanes']:
            try:
                sample = boundary(lane)
                if sample['status'] == 'OBSERVED_SAVED_BOUNDARY_NOT_ADMISSION':
                    observed.add(lane['physical'])
            except (ValueError, KeyError, OSError) as error:
                sample = dict(physical=lane['physical'], status='BLOCKED', error=str(error), launch_ready=False)
            write(output / f'SAMPLE_{samples:06d}.json', sample)
            samples += 1
        time.sleep(min(interval, max(0, deadline - time.monotonic())))
    result = dict(schema=SCHEMA, finished_unix=time.time(), samples=samples,
        boundary_observed_physical=sorted(observed), missing_physical=state['missing_physical'],
        status='OBSERVER_COMPLETE_NO_HANDOFF', signals=0, launches=0, launch_ready=False,
        required_gates=['root_specific_pidfd_handoff_CPU_tests', 'full_chain_and_stopped_boundary_verification',
            'fresh_privileged_admission', 'unchanged_UUID_actual_minor', 'all_seven_foreign_denials',
            'retirement_launch_LOADED_new_sleep_receipts'])
    write(output / 'COMPLETE.json', result)
    return result


def family_scope(plan):
    physical = scope(plan)
    require(physical in FAMILY, 'only_original_contained_programmes_3_4_7')
    root = BASE / f'orch_r133_node3_{FAMILY[physical]}_20260916_attempt1'
    require(plan['root'] == str(root / 'run1') and plan['source_root'] == str(root / 'source1'),
            'exact_programme_original_roots')
    require(not plan.get('preupdate_recovery') and not plan.get('authorized_wall_extension'),
            'no_recovery_or_wall_change')
    return physical


def originals(config_path):
    require(socket.gethostname() == HOST, 'exact_ovx2_host')
    config = read(config_path)
    plan = read(config['plan_path'])
    family_scope(plan)
    source = regular(plan['source_root'])
    sys.path.insert(0, str(source))
    modules = {}
    for label, name in (('guard', 'gpu.orch_r125_continual_guard'),
                        ('programmes', 'gpu.orch_r133_node3_programmes'),
                        ('native', NATIVE.replace('_guard', '_native')),
                        ('saved', 'gpu.orch_r131_saved_boundary_handoff')):
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve() == source / (name.replace('.', '/') + '.py'),
                'only_original_pinned_module_imports')
        modules[label] = module
    validated, original_plan = modules['guard'].validate(config_path)
    require(validated == config and original_plan == plan, 'exact_original_validation')
    return config, plan, SimpleNamespace(**modules)


def process_record(pid):
    process = Path('/proc') / str(pid)
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[0] not in ('Z', 'X'), 'owned_process_alive')
    return dict(pid=pid, start_ticks=fields[19], parent=int(fields[1]), group=int(fields[2]),
        uid=process.stat().st_uid, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        argv=(process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'),
        cwd=str((process / 'cwd').resolve()), cgroup=(process / 'cgroup').read_text().strip(),
        cvd=[part.decode().split('=', 1)[1] for part in (process / 'environ').read_bytes().split(b'\0')
             if part.startswith(b'CUDA_VISIBLE_DEVICES=')])


def process_pair(pid, config_path, config, plan):
    actor = process_record(pid)
    timer = process_record(actor['parent'])
    supervisor = process_record(timer['parent'])
    prefix = [str(PYTHON), '-B', '-m']
    require(actor['argv'] == prefix + [NATIVE, 'native', '--config', str(config_path)], 'original_native_argv')
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and len(timer['argv']) == 11 and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3])
            and timer['argv'][4:] == actor['argv'], 'original_timeout_argv')
    require(supervisor['argv'] == prefix + ['gpu.orch_r133_node3_programmes', 'contained-native',
            '--config', str(config_path)], 'original_programmes_supervisor_argv')
    launch = read(Path(config['attempt_dir']) / 'LAUNCH.json')
    require(launch['pid'] == timer['pid'] and launch['parent_start_ticks'] == timer['start_ticks']
            and launch['guard_sha256'] == sha(config_path) and launch['plan_sha256'] == config['plan_sha256'],
            'original_launch_identity_binding')
    policy = config['device_containment']
    for process in (actor, timer, supervisor):
        require(process['uid'] == os.getuid() == policy['uid'] and process['cwd'] == plan['source_root']
                and process['cvd'] == [plan['gpu_uuid']] and process['cgroup'] ==
                '0::/system.slice/' + policy['unit'] + '.service', 'exact_original_owned_cgroup')
    require(actor['group'] == timer['group'] == timer['pid'], 'native_owned_timeout_group')
    return dict(actor=actor, timer=timer, supervisor=supervisor)


def resume_config(config, attempt):
    proposed = proposed_guard(config, attempt)
    require('device_containment' in config, 'existing_containment_required')
    proposed['device_containment']['unit'] = 'orch-r133-node3-' + uuid.uuid4().hex
    original_policy = dict(config['device_containment'])
    restored_policy = dict(proposed['device_containment'], unit=original_policy['unit'])
    require(restored_policy == original_policy, 'no_foreign_device_policy_change')
    return proposed


def stage(config_path, pid, output, cpu_path):
    config_path, output, cpu_path = map(regular, (config_path, output, cpu_path))
    config, plan, original = originals(config_path)
    require(output.parent == BASE and output.name.startswith('orch_r142_allocator_ovx2_'),
            'unique_operator_attempt')
    cpu = read(cpu_path)
    require(cpu['passed'] is True and cpu['operator_sha256'] == sha(__file__)
            and cpu['tests_passed'] >= 16, 'own_exact_operator_CPU_gate')
    pair = process_pair(pid, config_path, config, plan)
    policy = config['device_containment']
    require(original.programmes.device_minor(plan['gpu_uuid']) == policy['minor'], 'unchanged_actual_minor')
    proposed = resume_config(config, output)
    output.mkdir(exist_ok=False)
    write(output / 'GUARD.json', proposed)
    original.guard.validate(output / 'GUARD.json')
    lifetime = int(plan['hard_end_unix'] - time.time())
    require(lifetime > 900, 'unchanged_lease_headroom')
    payload = [str(PYTHON), '-B', '-m', 'gpu.orch_r133_node3_programmes',
               'contained-native', '--config', str(output / 'GUARD.json')]
    baseline = original.programmes.containment_command(plan, proposed['device_containment'], payload, lifetime)
    changed = allocator_command(baseline)
    write(output / 'COMMAND_CPU.json', dict(original_contained_command=baseline, allocator_command=changed,
        command_sha256=digest(changed), payload_unchanged=True, inner_env_only=True,
        original_actor_argv=pair['actor']['argv'], original_source_pins_sha256=digest(config['source_pins'])))
    snapshot = output / 'STREAM_PRESTAGE'
    shutil.copytree(Path(plan['root']) / 'stream', snapshot)
    request = dict(schema='R142_PROGRAMMES_HANDOFF_V1', old_config=str(config_path), old_config_sha256=sha(config_path),
        new_config=str(output / 'GUARD.json'), new_config_sha256=sha(output / 'GUARD.json'),
        operator_path=str(Path(__file__).resolve()), operator_sha256=sha(__file__),
        cpu_path=str(cpu_path), cpu_sha256=sha(cpu_path), plan_sha256=config['plan_sha256'],
        physical=plan['physical'], gpu_uuid=plan['gpu_uuid'], processes=pair,
        stage_unix=time.time(), stage_native_alive=process_record(pid) == pair['actor'],
        training_source_changed=False, lease_changed=False, parent_touched=False)
    require(request['stage_native_alive'], 'live_original_preserved_through_setup')
    write(output / 'STAGED.json', request)
    return request


def verify_snapshot(snapshot, original_root, expected, original):
    module = importlib.import_module('gpu.orch_r125_stream_journal')
    source = Path(original.native.__file__).resolve().parents[1]
    require(Path(module.__file__).resolve() == source / 'gpu/orch_r125_stream_journal.py', 'original_journal_module')
    original_inbox = SimpleNamespace(inbox=Path(original_root) / 'stream/inbox')
    class SnapshotJournal(module.StreamJournal):
        def _inbox_event(self, message, path, source_sha256):
            return module.StreamJournal._inbox_event(original_inbox, message, path, source_sha256)
    with SnapshotJournal(snapshot, create=False) as journal:
        latest = journal.latest_checkpoint()
        require(latest is not None and latest['expected_sha256'] == expected, 'full_original_chain_saved_state')
    return latest


def saved_evidence(plan, saved, original):
    require(saved is not None, 'clean_saved_boundary_required')
    stream = original.native.ContinualStream.restore(
        dict(state=saved['state'], sha256=saved['state_sha256']), expected_sha256=saved['state_sha256'])
    original.native.verify_experiment_resume(plan, stream.experiment)
    commit = Path(plan['root']) / 'checkpoints' / f"sleep_{saved['cycle']:06d}" / 'COMMIT.json'
    checkpoint = read(commit)
    original.native.NativeChild.verify_checkpoint(checkpoint)
    require(digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256
            and checkpoint.get('experiment') == stream.experiment and stream.deadline_unix == plan['hard_end_unix'],
            'exact_adapter_AdamW_RNG_history_carry_wall')
    return dict(record_path=saved['path'], record_sha256=sha(saved['path']),
        state_sha256=saved['state_sha256'], checkpoint_path=str(commit), checkpoint_sha256=sha(commit),
        optimizer_steps=checkpoint['optimizer_steps'], adapter_state_sha256=checkpoint['adapter_state_sha256'],
        bundle_sha256=checkpoint['checkpoint_sha256'], cycle=saved['cycle'])


def pause_exact(expected, descriptor):
    require(process_record(expected['pid']) == expected, 'exact_identity_before_stop')
    signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        tasks = list((Path('/proc') / str(expected['pid']) / 'task').iterdir())
        if tasks and all((task / 'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't') for task in tasks):
            require(process_record(expected['pid']) == expected, 'exact_identity_after_stop')
            return
        time.sleep(.01)
    raise ValueError('bounded_all_threads_quiescence_failed')


def resume_paused(paused, descriptors):
    for name in reversed(paused):
        try:
            signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
        except ProcessLookupError:
            pass
    paused.clear()


def admission(report, plan):
    require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['gpu_uuid'] and report['gpu']['index'] == plan['physical'],
            'fresh_privileged_exact_UUID_physical_admission')


def admission_retry_eligible(prior):
    prior = regular(prior)
    require(not any((prior / name).exists() for name in
                    ('LAUNCH.json', 'CONTAINED_COMMAND.json', 'ADMISSION_TIME.json')),
            'readmit_only_before_any_native_dispatch')
    require(read(prior / 'RETIRED.json')['status'] == 'EXACT_OLD_PROCESSES_EXITED', 'exact_prior_retirement')
    require(read(prior / 'ADMISSION.json')['clear'] is False
            and (prior / 'SUPERVISOR_FAILED.json').exists(), 'preserved_admission_denial_required')
    require(read(prior / 'RETIRED.json')['boundary_sha256'] == sha(prior / 'BOUNDARY.json'),
            'prior_retirement_boundary_binding')


def readmit(prior, output, cpu_path):
    prior, output, cpu_path = map(regular, (prior, output, cpu_path))
    admission_retry_eligible(prior)
    previous = read(prior / 'STAGED.json')
    require(sha(prior / 'GUARD.json') == previous['new_config_sha256'], 'prior_staged_guard_unchanged')
    config, plan, original = originals(prior / 'GUARD.json')
    cpu = read(cpu_path)
    require(cpu['passed'] is True and cpu['tests_passed'] >= 22 and cpu['operator_sha256'] == sha(__file__),
            'readmit_tested_operator')
    require(output.parent == BASE and output.name.startswith('orch_r142_allocator_ovx2_'), 'unique_readmit_output')
    lock = os.open(BASE / 'orch_r142_allocator_ovx2_ROLLOUT.lock', os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        saved = original.saved.sleep_boundary(plan['root'])
        old_boundary = read(prior / 'BOUNDARY.json')
        require(saved is not None and saved['state_sha256'] == old_boundary['state_sha256']
                and sha(saved['path']) == old_boundary['record_sha256'], 'retired_boundary_still_exact_no_pending_work')
        evidence = saved_evidence(plan, saved, original)
        require(all(old_boundary[key] == value for key, value in evidence.items()), 'same_preserved_bundle')
        module = importlib.import_module('gpu.orch_r125_stream_journal')
        with module.StreamJournal(Path(plan['root']) / 'stream', create=False) as journal:
            require(journal.latest_checkpoint()['expected_sha256'] == saved['state_sha256'], 'unowned_exact_original_stream')
        proposed = resume_config(config, output)
        output.mkdir(exist_ok=False)
        write(output / 'GUARD.json', proposed)
        original.guard.validate(output / 'GUARD.json')
        request = dict(previous, new_config=str(output / 'GUARD.json'), new_config_sha256=sha(output / 'GUARD.json'),
            operator_path=str(Path(__file__).resolve()), operator_sha256=sha(__file__), cpu_path=str(cpu_path),
            cpu_sha256=sha(cpu_path), stage_native_alive=False, stage_unix=time.time(),
            no_native_previously_launched=True, prior_attempt=str(prior), prior_denial_sha256=sha(prior / 'ADMISSION.json'))
        write(output / 'STAGED.json', request)
        write(output / 'BOUNDARY.json', old_boundary)
        write(output / 'RETIRED.json', read(prior / 'RETIRED.json'))
        write(output / 'READMISSION_PROVENANCE.json', dict(prior=str(prior), original_denial_sha256=sha(prior / 'ADMISSION.json'),
            previous_retirement_sha256=sha(prior / 'RETIRED.json'), no_additional_signals=True,
            prior_attempt_preserved=True, policy_unchanged_except_unit=True, revalidated_unix=time.time()))
        command = [str(PYTHON), '-B', request['operator_path'], '--action', 'supervise', '--output', str(output)]
        with (output / 'SUPERVISOR.log').open('x') as log:
            successor = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=plan['source_root']))
        write(output / 'DISPATCHED.json', dict(supervisor_pid=successor.pid, command=command, dispatched_unix=time.time()))
        return monitor_success(output, evidence, Path(saved['path']).name,
                               on_loaded=lambda: fcntl.flock(lock, fcntl.LOCK_UN))
    finally:
        os.close(lock)


def supervise(output):
    output = regular(output)
    request = read(output / 'STAGED.json')
    require(sha(__file__) == request['operator_sha256'] and sha(output / 'GUARD.json') == request['new_config_sha256'],
            'staged_operator_and_guard_unchanged')
    config, plan, original = originals(output / 'GUARD.json')
    require(read(output / 'RETIRED.json')['status'] == 'EXACT_OLD_PROCESSES_EXITED', 'retirement_required')
    (output / 'DISPATCH_ONCE').mkdir()
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + plan['source_root'], str(PYTHON), '-B', '-m', NATIVE, 'scan',
        '--config', str(output / 'GUARD.json')]
    report = json.loads(subprocess.check_output(command, text=True, timeout=90, cwd=plan['source_root']))
    write(output / 'ADMISSION.json', report)
    admission(report, plan)
    require(original.programmes.device_minor(plan['gpu_uuid']) == config['device_containment']['minor'],
            'actual_minor_unchanged_before_dispatch')
    write(output / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    payload = [str(PYTHON), '-B', '-m', 'gpu.orch_r133_node3_programmes',
               'contained-native', '--config', str(output / 'GUARD.json')]
    baseline = original.programmes.containment_command(plan, config['device_containment'], payload,
        max(1, int(plan['hard_end_unix'] - time.time())))
    command = allocator_command(baseline)
    write(output / 'CONTAINED_COMMAND.json', dict(command=command, original_without_allocator=baseline,
        started_unix=time.time(), original_verify_containment_and_native=True))
    result = subprocess.run(command, check=False, cwd=plan['source_root'])
    write(output / 'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
    require(result.returncode == 0, 'original_contained_service_failed_no_retry')


def monitor_success(output, saved, old_head, seconds=1200, on_loaded=None):
    request = read(output / 'STAGED.json')
    config = read(output / 'GUARD.json')
    plan = read(config['plan_path'])
    require(sha(output / 'GUARD.json') == request['new_config_sha256'], 'monitor_staged_guard')
    deadline = time.monotonic() + seconds
    loaded_path = output / 'LOADED_RECEIPT.json'
    loaded = read(loaded_path) if loaded_path.exists() else None
    if loaded is not None:
        require(sha(loaded['record_path']) == loaded['record_sha256']
                and identity(loaded['actor']['pid']) == loaded['actor']
                and loaded['optimizer_steps'] == saved['optimizer_steps']
                and loaded['adapter_state_sha256'] == saved['adapter_state_sha256'], 'resume_monitor_verified_LOADED')
        if on_loaded is not None:
            on_loaded()
    while time.monotonic() < deadline:
        require(not (output / 'SUPERVISOR_FAILED.json').exists() and not (output / 'EXIT.json').exists(),
                'successor_failed_preserve_evidence')
        records = sorted((Path(plan['root']) / 'stream/records').glob('*.json'))
        for path in records:
            if not re.fullmatch(r'\d{20}\.json', path.name) or path.name <= old_head:
                continue
            record = read(path)
            document = record['document']
            require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
                    'new_receipt_journal_hash')
            if record['kind'] == 'LOADED' and loaded is None:
                require(document['resume'] is True and document['optimizer_steps'] == saved['optimizer_steps']
                        and document['adapter_sha256'] == saved['adapter_state_sha256'], 'exact_saved_LOADED')
                actor = identity(document['pid'])
                require(actor['argv'][-1] == str(output / 'GUARD.json') and ALLOCATOR in actor['environment']
                        and actor['cwd'] == plan['source_root'], 'allocator_in_actual_original_native')
                proof = read(output / 'CONTAINMENT_VERIFIED.json')
                require(len(proof['denied_devices']) == 7 and proof['policy'] == config['device_containment'],
                        'original_all_seven_denials_receipt')
                launch = read(output / 'LAUNCH.json')
                require(actor['parent'] == launch['pid'] and launch['guard_sha256'] == sha(output / 'GUARD.json'),
                        'new_launch_loaded_ancestry')
                loaded = dict(record_path=str(path), record_sha256=sha(path), actor=actor,
                    optimizer_steps=document['optimizer_steps'], adapter_state_sha256=document['adapter_sha256'],
                    containment_sha256=sha(output / 'CONTAINMENT_VERIFIED.json'), observed_unix=time.time())
                write(output / 'LOADED_RECEIPT.json', loaded)
                if on_loaded is not None:
                    on_loaded()
            if loaded and record['kind'] == 'SLEEP_COMPLETE' and document['cycle'] > saved['cycle']:
                require(document['status'] == 'COMPLETE', 'new_sleep_complete')
                result = dict(status='ALLOCATOR_RESUMED_AND_NEW_SLEEP', physical=request['physical'],
                    old_cycle=saved['cycle'], new_cycle=document['cycle'], loaded_sha256=sha(output / 'LOADED_RECEIPT.json'),
                    new_sleep_path=str(path), new_sleep_sha256=sha(path), finished_unix=time.time(),
                    plan_unchanged=sha(config['plan_path']) == request['plan_sha256'], training_changed=False)
                require(result['plan_unchanged'], 'same_plan_after_new_sleep')
                write(output / 'NEW_SLEEP_RECEIPT.json', result)
                return result
        time.sleep(2)
    write(output / 'MONITOR_TIMEOUT.json', dict(loaded=loaded is not None, finished_unix=time.time(), stopped=False))
    raise ValueError('bounded_loaded_new_sleep_monitor_expired_no_signal')


def handoff(output, wait_seconds=600):
    require(type(wait_seconds) is int and 1 <= wait_seconds <= 1200, 'bounded_handoff_wait')
    output = regular(output)
    request = read(output / 'STAGED.json')
    require(sha(__file__) == request['operator_sha256'] and sha(request['cpu_path']) == request['cpu_sha256']
            and sha(request['old_config']) == request['old_config_sha256']
            and sha(request['new_config']) == request['new_config_sha256'], 'all_staged_provenance_unchanged')
    config, plan, original = originals(request['old_config'])
    original.guard.validate(request['new_config'])
    require(process_pair(request['processes']['actor']['pid'], request['old_config'], config, plan)
            == request['processes'], 'exact_staged_original_processes')
    lock = os.open(BASE / 'orch_r142_allocator_ovx2_ROLLOUT.lock', os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    descriptors, paused = {}, []
    handlers = {}
    def interrupted(signum, frame):
        raise SystemExit('interrupted_restore_exact_paused_processes')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (output / 'HANDOFF_ONCE').mkdir()
        handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGHUP)}
        for name, process in request['processes'].items():
            require(process_record(process['pid']) == process, 'identity_before_pidfd_open')
            descriptors[name] = os.pidfd_open(process['pid'])
            require(process_record(process['pid']) == process, 'identity_after_pidfd_open')
        deadline = min(time.monotonic() + wait_seconds, time.monotonic() + plan['hard_end_unix'] - time.time() - 900)
        attempts = 0
        while time.monotonic() < deadline:
            saved = original.saved.sleep_boundary(plan['root'])
            if saved is None or not original.saved.readout_started(plan['root'], saved['cycle'],
                    plan.get('readout_revision', 1), request['processes']['timer']['pid']):
                time.sleep(.25)
                continue
            attempts += 1
            prepared = output / f'BOUNDARY_PREP_{attempts:04d}'
            prepared.mkdir()
            evidence = saved_evidence(plan, saved, original)
            shutil.copytree(Path(plan['root']) / 'stream', prepared / 'stream')
            try:
                verify_snapshot(prepared / 'stream', plan['root'], saved['state_sha256'], original)
            except (ValueError, FileNotFoundError):
                write(prepared / 'MOVED.json', dict(status='PREP_NOT_QUIESCENT_NO_SIGNAL'))
                continue
            shutil.copytree(Path(evidence['checkpoint_path']).parent, prepared / 'checkpoint')
            write(prepared / 'CPU_BOUNDARY.json', evidence)
            if original.saved.sleep_boundary(plan['root']) != saved:
                continue
            for name in ('supervisor', 'timer', 'actor'):
                paused.append(name)
                pause_exact(request['processes'][name], descriptors[name])
            if original.saved.sleep_boundary(plan['root']) != saved:
                resume_paused(paused, descriptors)
                continue
            complete = Path(plan['root']) / 'readouts' / original.native.readout_name(plan, saved['cycle']) / 'COMPLETE.json'
            readout_deadline = min(deadline, time.monotonic() + 180)
            while time.monotonic() < readout_deadline and not complete.exists():
                time.sleep(.1)
            require(complete.exists() and read(complete)['status'] == 'COMPLETE', 'readout_complete_before_retirement')
            readout_pid = read(complete)['pid']
            while time.monotonic() < readout_deadline:
                process = Path('/proc') / str(readout_pid) / 'stat'
                if not process.exists() or process.read_text().rsplit(') ', 1)[1].split()[0] == 'Z':
                    break
                time.sleep(.1)
            else:
                raise ValueError('readout_not_exited_restore_live_child')
            require(original.saved.sleep_boundary(plan['root']) == saved, 'quiescent_saved_frontier_unchanged')
            original_records = Path(plan['root']) / 'stream/records'
            copied_records = prepared / 'stream/records'
            require(sorted(path.name for path in original_records.iterdir()) ==
                    sorted(path.name for path in copied_records.iterdir()), 'no_unrecorded_pending_mutation')
            require(saved_evidence(plan, saved, original) == evidence, 'same_saved_bundle_after_quiescence')
            write(output / 'BOUNDARY.json', dict(**evidence, snapshot=str(prepared),
                full_chain_verified=True, all_threads_quiescent=True, readout_complete_sha256=sha(complete),
                original_raw_preserved=True, parent_untouched=True, saved_unix=time.time()))
            for name in ('actor', 'timer', 'supervisor'):
                process = request['processes'][name]
                require(process_record(process['pid']) == process, 'exact_identity_before_retirement')
                signal.pidfd_send_signal(descriptors[name], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
                require(bool(select.select([descriptors[name]], [], [], 20)[0]), 'exact_pidfd_exit_without_KILL')
            paused.clear()
            write(output / 'RETIRED.json', dict(status='EXACT_OLD_PROCESSES_EXITED',
                processes=request['processes'], boundary_sha256=sha(output / 'BOUNDARY.json'), retired_unix=time.time()))
            module = importlib.import_module('gpu.orch_r125_stream_journal')
            with module.StreamJournal(Path(plan['root']) / 'stream', create=False) as journal:
                require(journal.latest_checkpoint()['expected_sha256'] == saved['state_sha256'], 'released_original_writer_exact_state')
            command = [str(PYTHON), '-B', request['operator_path'], '--action', 'supervise', '--output', str(output)]
            with (output / 'SUPERVISOR.log').open('x') as log:
                successor = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=plan['source_root']))
            write(output / 'DISPATCHED.json', dict(supervisor_pid=successor.pid, command=command, dispatched_unix=time.time()))
            return monitor_success(output, evidence, Path(saved['path']).name,
                                   on_loaded=lambda: fcntl.flock(lock, fcntl.LOCK_UN))
        write(output / 'WAIT_EXPIRED.json', dict(status='NO_RETIREMENT', expired_unix=time.time()))
        return dict(status='NO_CLEAN_PREPARED_BOUNDARY', signals_restored=True)
    except BaseException as error:
        write(output / ('ERROR_' + str(time.time_ns()) + '.json'), dict(error=str(error), error_type=type(error).__name__,
            observed_unix=time.time(), retired=(output / 'RETIRED.json').exists()))
        raise
    finally:
        resume_paused(paused, descriptors)
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--action', choices=('observe', 'stage', 'handoff', 'supervise', 'monitor', 'readmit'), default='observe')
    parser.add_argument('--old-config', type=Path)
    parser.add_argument('--pid', type=int)
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--prior', type=Path)
    parser.add_argument('--seconds', type=int, default=120)
    parser.add_argument('--interval', type=float, default=2)
    arguments = parser.parse_args()
    if arguments.action == 'observe':
        result = observe(arguments.output, arguments.seconds, arguments.interval)
    elif arguments.action == 'stage':
        result = stage(arguments.old_config, arguments.pid, arguments.output, arguments.cpu)
    elif arguments.action == 'handoff':
        result = handoff(arguments.output, arguments.seconds)
    elif arguments.action == 'monitor':
        saved = read(arguments.output / 'BOUNDARY.json')
        write(arguments.output / 'MONITOR_CONTINUATION_STARTED.json', dict(pid=os.getpid(),
              operator_path=str(Path(__file__).resolve()), operator_sha256=sha(__file__), started_unix=time.time()))
        result = monitor_success(arguments.output, saved, Path(saved['record_path']).name)
    elif arguments.action == 'readmit':
        result = readmit(arguments.prior, arguments.output, arguments.cpu)
    else:
        try:
            result = supervise(arguments.output)
        except BaseException as error:
            write(arguments.output / 'SUPERVISOR_FAILED.json', dict(error=str(error), failed_unix=time.time()))
            raise
    print(json.dumps(result, sort_keys=True))
