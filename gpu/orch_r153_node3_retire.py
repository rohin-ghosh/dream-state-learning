"""Rohin147: saved-boundary retirement of node3 creative5/support6 only."""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import signal
import socket
import subprocess
import sys
import time


API_SHA = 'f128becb34d95b6875e4283baa49b3504e2c6c589e67b93e858e07c98f593e60'
HOST = 'ipp2-ovx-p6-09'
BOOT = '589725e3-0bcb-4427-83b3-8ead5cbc1e9a'
BASE = Path('/localhome/local-rohing')
SOURCE_BASE = BASE / 'orch_r145_combined_targets_20260916t1645z_2'
AUTHORITY = 'Rohin147_CONFIRMED_RETIRE_NODE3_CREATIVE5_SUPPORT6_ONLY'
TARGETS = {
    5: dict(name='creative_none', pid=1679411, ticks='28446643',
            uuid='GPU-bc211959-642d-664b-3581-42a0dbe434e9',
            control='orch_r144_node3_target_r145_5_20260916t1650z',
            guard_sha='507ab15980d3566a938b5b7a0707423d56668b1e1d9a445f57d23d72eeba7687'),
    6: dict(name='support_none', pid=1657354, ticks='28425143',
            uuid='GPU-1a83d900-1e95-c7b4-9b12-8117399697f8',
            control='orch_r144_node3_target_r145_6_20260916t1650z_readmit1',
            guard_sha='97feb3141fabd0833486de68d47090f0fa3f33a37a1ef270b8509ff6c387e9be'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def scope(plan):
    physical = plan['physical']
    require(type(physical) is int and physical in TARGETS, 'only_named_node3_5_6')
    target = TARGETS[physical]
    require(plan['root'] == str(BASE / f"orch_r133_node3_{target['name']}_20260916_attempt1/run1")
            and plan['source_root'] == str(SOURCE_BASE / f'physical{physical}/source')
            and plan['gpu_uuid'] == target['uuid'], 'exact_named_root_source_UUID')
    return physical


def load_api(path):
    require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == API_SHA, 'pinned_proven_boundary_API')
    spec = importlib.util.spec_from_file_location('r153_boundary_api', path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.family_scope = scope
    return helper


def reference(helper, path):
    return dict(path=str(Path(path).absolute()), sha256=helper.sha(path))


def host_check():
    require(socket.gethostname() == HOST and os.getuid() == 2524, 'exact_node3_owner')
    require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == BOOT, 'exact_node3_boot')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_operator_no_GPU_environment')


def same_pair(helper, pair):
    for identity in pair.values():
        require(helper.process_record(identity['pid']) == identity, 'bound_process_identity_changed')


def children(pid):
    result = set()
    for task in (Path('/proc') / str(pid) / 'task').iterdir():
        result.update(int(value) for value in (task / 'children').read_text().split())
    return result


def validate_children(pair, readout_pid=None):
    require(children(pair['timer']['pid']) == {pair['actor']['pid']}, 'timer_has_only_named_native')
    require(children(pair['supervisor']['pid']) == {pair['timer']['pid']}, 'supervisor_has_only_named_timer')
    allowed = set() if readout_pid is None else {readout_pid}
    require(children(pair['actor']['pid']) <= allowed, 'no_foreign_or_unbound_native_child')


def gpu_metadata(physical):
    target = TARGETS[physical]
    query = subprocess.run(['nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu',
                            '--format=csv,noheader,nounits'], text=True, capture_output=True, check=True, timeout=10)
    rows = [line.split(',') for line in query.stdout.splitlines() if line.strip()]
    selected = [row for row in rows if int(row[0].strip()) == physical]
    require(len(selected) == 1 and selected[0][1].strip() == target['uuid'], 'unchanged_physical_UUID_mapping')
    apps = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'],
                          text=True, capture_output=True, check=True, timeout=10)
    pids = [int(line.split(',')[1].strip()) for line in apps.stdout.splitlines()
            if line.split(',')[0].strip() == target['uuid']]
    return dict(physical=physical, uuid=target['uuid'], compute_pids=pids,
                memory_used_MiB=int(selected[0][2].strip()), utilization_percent=int(selected[0][3].strip()),
                observed_unix=time.time())


def resume_command(helper, output, api_path):
    code = (
        'import hashlib,importlib.util,json,pathlib;'
        f'output=pathlib.Path({str(output)!r});'
        'ack=json.loads((output/"RESUME_MAIN_ACK.json").read_bytes());'
        'assert ack.get("approved") is True and ack.get("action")=="RESUME_R153_SAME_LIFE";'
        'assert ack.get("retirement_sha256")==hashlib.sha256((output/"RETIRED.json").read_bytes()).hexdigest();'
        f'api_path=pathlib.Path({str(api_path)!r});'
        f'assert hashlib.sha256(api_path.read_bytes()).hexdigest()=={API_SHA!r};'
        'spec=importlib.util.spec_from_file_location("r153_resume_api",api_path);'
        'api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api);'
        'from gpu import orch_r133_node3_programmes as programmes;'
        'original=programmes.containment_command;'
        'programmes.containment_command=lambda *args,**kwargs:api.allocator_command(original(*args,**kwargs));'
        'programmes.supervise(output/"resume/GUARD.json",output/"RELEASED.json")'
    )
    return [str(helper.PYTHON), '-B', '-c', code]


def prepare(helper, physical, output, cpu_path, authority):
    host_check()
    require(authority == AUTHORITY and type(physical) is int and physical in TARGETS, 'exact_retirement_authority')
    output = helper.regular(output)
    require(output.parent == BASE and output.name.startswith('orch_r153_node3_retire_')
            and not output.exists(), 'fresh_owned_operator_directory')
    gate = helper.read(cpu_path)
    require(gate['status'] == 'PASS' and gate['module_sha256'] == helper.sha(__file__)
            and gate['api_sha256'] == API_SHA and helper.sha(gate['log']['path']) == gate['log']['sha256'],
            'actual_CPU_gate_bound_before_actions')
    target = TARGETS[physical]
    config_path = BASE / target['control'] / 'GUARD.json'
    require(helper.sha(config_path) == target['guard_sha'], 'original_live_guard_bytes')
    config, plan, original = helper.originals(config_path)
    require(scope(plan) == physical and plan['hard_end_unix'] - time.time() > 900, 'owned_lane_and_lease_headroom')
    pair = helper.process_pair(target['pid'], config_path, config, plan)
    require(pair['actor']['start_ticks'] == target['ticks'], 'actual_native_start_ticks')
    validate_children(pair)
    same_pair(helper, pair)
    output.mkdir(mode=0o700)
    resume = helper.resume_config(config, output / 'resume')
    (output / 'resume').mkdir(mode=0o700)
    helper.write(output / 'resume/GUARD.json', resume)
    original.guard.validate(output / 'resume/GUARD.json')
    request = dict(schema='R153_NODE3_RETIRE_V1', authority=authority, physical=physical,
        root=plan['root'], config=reference(helper, config_path), plan=reference(helper, config['plan_path']),
        source_pins=config['source_pins'], source_root=plan['source_root'], pair=pair,
        operator_sha256=helper.sha(__file__), api_sha256=API_SHA, cpu=reference(helper, cpu_path),
        resume_config=reference(helper, output / 'resume/GUARD.json'),
        resume_status='PREPARED_NOT_LAUNCHED_REQUIRES_NEW_AUTHORIZATION_AND_FRESH_ADMISSION',
        resume_command=resume_command(helper, output, Path(helper.__file__).absolute()),
        resume_environment=dict(PYTHONPATH=plan['source_root'], CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
        created_unix=time.time(), launch_authorized=False, training_source_changed=False)
    helper.write(output / 'REQUEST.json', request)
    return dict(status='PREPARED_NO_SIGNAL', physical=physical, output=str(output), actor=target['pid'])


def watchdog(actor_fd, pipe_fd, seconds):
    ready = select.select([pipe_fd], [], [], seconds)[0]
    if ready and os.read(pipe_fd, 1) == b'D':
        return
    try:
        signal.pidfd_send_signal(actor_fd, signal.SIGCONT)
    except ProcessLookupError:
        pass


@contextmanager
def pause_guard(actor_fd, seconds):
    reader, writer = os.pipe()
    process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).absolute()), 'watchdog',
        '--actor-fd', str(actor_fd), '--pipe-fd', str(reader), '--seconds', str(seconds)],
        pass_fds=(actor_fd, reader), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, start_new_session=True)
    os.close(reader)
    try:
        yield time.monotonic() + seconds
    finally:
        try:
            os.write(writer, b'D')
        except BrokenPipeError:
            pass
        os.close(writer)
        process.wait(timeout=5)


def retire_actor(helper, pair, descriptors, deadline):
    require(time.monotonic() + 25 < deadline, 'pause_budget_before_irreversible_exit')
    same_pair(helper, pair)
    signal.pidfd_send_signal(descriptors['actor'], signal.SIGTERM)
    signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
    require(bool(select.select([descriptors['actor']], [], [], 20)[0]), 'native_exit_without_force_kill')
    for name in ('timer', 'supervisor'):
        require(bool(select.select([descriptors[name]], [], [], 20)[0]), 'natural_' + name + '_exit_required')


def readout_metadata(helper, plan, config, saved, original, pair):
    directory = Path(plan['root']) / 'readouts' / original.native.readout_name(plan, saved['cycle'])
    request_path = directory / 'REQUEST.json'
    request = helper.read(request_path)
    checkpoint_path = Path(plan['root']) / 'checkpoints' / f"sleep_{saved['cycle']:06d}/COMMIT.json"
    require(request['plan_sha256'] == config['plan_sha256'] and request['plan_path'] == config['plan_path']
            and request['checkpoint_path'] == str(checkpoint_path)
            and request['checkpoint_commit_sha256'] == helper.sha(checkpoint_path)
            and request['gpu_uuid'] == plan['gpu_uuid'] and request['ppid'] == pair['actor']['pid'],
            'readout_exact_native_plan_checkpoint')
    pid = request['pid']
    status = Path('/proc') / str(pid) / 'stat'
    identity = None
    descriptor = None
    if status.exists() and status.read_text().rsplit(')', 1)[1].split()[0] not in ('Z', 'X'):
        identity = helper.process_record(pid)
        expected = [str(helper.PYTHON), '-B', '-m', 'gpu.orch_r125_continual_readout',
                    '--plan', config['plan_path'], '--checkpoint', str(checkpoint_path), '--output', str(directory)]
        require(identity['argv'] == expected and identity['cwd'] == plan['source_root']
                and identity['uid'] == pair['actor']['uid'] and identity['parent'] == pair['actor']['pid']
                and identity['group'] == pid and identity['group'] != pair['timer']['group'],
                'readout_independent_exact_identity')
        descriptor = os.pidfd_open(pid)
        require(helper.process_record(pid) == identity, 'readout_identity_after_pidfd')
    return dict(pid=pid, descriptor=descriptor, identity=identity, directory=directory,
                request_sha256=helper.sha(request_path), checkpoint_commit_sha256=request['checkpoint_commit_sha256'])


def finish_readout(helper, readout, deadline):
    complete = readout['directory'] / 'COMPLETE.json'
    while time.monotonic() + 30 < deadline:
        exited = (bool(select.select([readout['descriptor']], [], [], 0)[0])
                  if readout['descriptor'] is not None else True)
        if complete.is_file() and exited:
            metadata = helper.read(complete)
            require(metadata['status'] == 'COMPLETE' and metadata['pid'] == readout['pid']
                    and metadata['checkpoint_commit_sha256'] == readout['checkpoint_commit_sha256'],
                    'successful_matching_readout_metadata_only')
            return dict(pid=readout['pid'], request_sha256=readout['request_sha256'],
                        complete_sha256=helper.sha(complete), finished_unix=metadata['finished_unix'])
        time.sleep(.1)
    raise TimeoutError('readout_not_completed_restore_live_native')


def retire(helper, output, seconds, authority):
    host_check()
    require(authority == AUTHORITY and type(seconds) is int and 1 <= seconds <= 5400, 'bounded_authorized_wait')
    request = helper.read(output / 'REQUEST.json')
    require(request['authority'] == authority and request['operator_sha256'] == helper.sha(__file__)
            and helper.sha(request['cpu']['path']) == request['cpu']['sha256']
            and helper.sha(request['config']['path']) == request['config']['sha256'], 'unchanged_prepared_bindings')
    config, plan, original = helper.originals(request['config']['path'])
    physical = scope(plan)
    require(physical == request['physical'] and config['source_pins'] == request['source_pins'], 'same_scope_and_source')
    pair = helper.process_pair(TARGETS[physical]['pid'], request['config']['path'], config, plan)
    require(pair == request['pair'], 'exact_prepared_native_timer_supervisor')
    descriptors = {}
    paused = []
    lock = os.open(BASE / 'orch_r142_allocator_ovx2_ROLLOUT.lock',
                   os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    handlers = {}
    def interrupted(signum, frame):
        raise SystemExit('operator_interrupted_restore_owned_pause')
    try:
        (output / 'RETIRE_ONCE').mkdir()
        for signum in (signal.SIGTERM, signal.SIGHUP):
            handlers[signum] = signal.signal(signum, interrupted)
        for name, identity in pair.items():
            require(helper.process_record(identity['pid']) == identity, 'identity_before_pidfd')
            descriptors[name] = os.pidfd_open(identity['pid'])
            require(helper.process_record(identity['pid']) == identity, 'identity_after_pidfd')
        deadline = min(time.monotonic() + seconds, time.monotonic() + plan['hard_end_unix'] - time.time() - 900)
        helper.write(output / 'ARMED.json', dict(physical=physical, pair=pair, armed_unix=time.time(),
            operator_pid=os.getpid(), signals_sent=0, launch_authorized=False))
        attempts = 0
        while time.monotonic() < deadline:
            same_pair(helper, pair)
            saved = original.saved.sleep_boundary(plan['root'])
            if saved is None or not original.saved.readout_started(plan['root'], saved['cycle'],
                    plan.get('readout_revision', 1), pair['timer']['pid']):
                time.sleep(.25)
                continue
            attempts += 1
            prepared = output / f'BOUNDARY_PREP_{attempts:04d}'
            prepared.mkdir(mode=0o700)
            evidence = helper.saved_evidence(plan, saved, original)
            shutil.copytree(Path(plan['root']) / 'stream', prepared / 'stream')
            try:
                helper.verify_snapshot(prepared / 'stream', plan['root'], saved['state_sha256'], original)
            except (ValueError, FileNotFoundError):
                helper.write(prepared / 'MOVED.json', dict(status='SNAPSHOT_MOVED_NO_SIGNAL'))
                continue
            shutil.copytree(Path(evidence['checkpoint_path']).parent, prepared / 'checkpoint')
            for path in (prepared / 'checkpoint').rglob('*'):
                if path.is_file():
                    relative = path.relative_to(prepared / 'checkpoint')
                    require(helper.sha(path) == helper.sha(Path(evidence['checkpoint_path']).parent / relative),
                            'copied_checkpoint_exact_bytes')
            helper.write(prepared / 'CPU_BOUNDARY.json', evidence)
            if original.saved.sleep_boundary(plan['root']) != saved:
                continue
            readout = readout_metadata(helper, plan, config, saved, original, pair)
            try:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    time.sleep(.25)
                    continue
                same_pair(helper, pair)
                validate_children(pair, readout['pid'])
                if original.saved.sleep_boundary(plan['root']) != saved:
                    continue
                with pause_guard(descriptors['actor'], 180) as pause_deadline:
                    paused.append('actor')
                    try:
                        helper.pause_exact(pair['actor'], descriptors['actor'])
                        require(original.saved.sleep_boundary(plan['root']) == saved, 'boundary_still_saved_after_pause')
                        completed = finish_readout(helper, readout, min(deadline, pause_deadline))
                        validate_children(pair, readout['pid'])
                        require(original.saved.sleep_boundary(plan['root']) == saved, 'no_new_generation_or_update')
                        require(sorted(path.name for path in (Path(plan['root']) / 'stream/records').iterdir()) ==
                                sorted(path.name for path in (prepared / 'stream/records').iterdir()), 'no_pending_journal_tail')
                        helper.write(output / 'BOUNDARY.json', dict(**evidence, snapshot=str(prepared),
                            readout=completed, full_chain_verified=True, all_native_threads_quiescent=True,
                            original_files_preserved=True, parent_untouched=True, observed_unix=time.time()))
                        retire_actor(helper, pair, descriptors, min(deadline, pause_deadline))
                        paused.clear()
                    finally:
                        helper.resume_paused(paused, descriptors)
                helper.write(output / 'RETIRED.json', dict(status='EXACT_NATIVE_EXITED_PARENTS_EXITED_NATURALLY',
                    physical=physical, pair=pair, signaled_roles=['actor'], signals=['SIGSTOP','SIGTERM','SIGCONT'],
                    boundary_sha256=helper.sha(output / 'BOUNDARY.json'), retired_unix=time.time(), no_force_kill=True))
                break
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
                if readout['descriptor'] is not None:
                    os.close(readout['descriptor'])
        else:
            helper.write(output / 'WAIT_EXPIRED.json', dict(status='NO_RETIREMENT', observed_unix=time.time()))
            return dict(status='NO_SAVED_BOUNDARY_WITHIN_WAIT', physical=physical)
        require(original.saved.sleep_boundary(plan['root']) == saved, 'postexit_saved_frontier_unchanged')
        require(helper.saved_evidence(plan, saved, original) == evidence, 'postexit_exact_saved_bundle')
        module = sys.modules['gpu.orch_r125_stream_journal']
        with module.StreamJournal(Path(plan['root']) / 'stream', create=False) as journal:
            require(journal.latest_checkpoint()['expected_sha256'] == saved['state_sha256'], 'released_writer_exact_context')
        metadata = gpu_metadata(physical)
        require(not metadata['compute_pids'], 'target_GPU_has_no_compute_processes')
        helper.write(output / 'RELEASED.json', dict(status='RELEASED', physical=physical, uuid=plan['gpu_uuid'],
            free_GPU_proof=metadata, boundary_sha256=helper.sha(output / 'BOUNDARY.json'),
            resume_status=request['resume_status'], launch_authorized=False, observed_unix=time.time()))
        return dict(status='RELEASED', physical=physical, cycle=evidence['cycle'], optimizer_steps=evidence['optimizer_steps'],
                    output=str(output), free_GPU_proof=metadata, resume_status=request['resume_status'])
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'retire', 'watchdog'))
    parser.add_argument('--api', type=Path)
    parser.add_argument('--physical', type=int)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--authority')
    parser.add_argument('--seconds', type=int, default=5400)
    parser.add_argument('--actor-fd', type=int)
    parser.add_argument('--pipe-fd', type=int)
    arguments = parser.parse_args()
    if arguments.action == 'watchdog':
        watchdog(arguments.actor_fd, arguments.pipe_fd, arguments.seconds)
        return
    helper = load_api(arguments.api)
    if arguments.action == 'prepare':
        result = prepare(helper, arguments.physical, arguments.output, arguments.cpu, arguments.authority)
    else:
        result = retire(helper, arguments.output, arguments.seconds, arguments.authority)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
