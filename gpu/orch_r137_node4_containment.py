"""Node4 operator-only device containment and exact raw6 saved-boundary handoff."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import shutil
import socket
import stat
import subprocess
import time
from types import SimpleNamespace
import uuid

from gpu import orch_r125_continual_native as native
from gpu import orch_r133_retire_old_lanes as preservation
BASE = Path('/localhome/local-rohing')
PYTHON = BASE/'v2/venv/bin/python'
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
DEVICES = {
    3: 'GPU-4d0f10af-119f-10bb-a28f-f7b7703a3b14',
    6: 'GPU-06b31c8f-7a96-d812-23f3-df3444d95397',
    7: 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98',
}
ADAPTED_FROM_SHA256 = '85c4601506bbee8008b2738d83dd7d256b5923dfca2fc4afa719707dc4e0d743'


def require_host():
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA,
            'exact_node4_host_hash')

def require(condition, reason):
    native.require(condition, reason)


def ref(path):
    return preservation.ref(path)


def write(path, document):
    preservation.immutable(path, document)


def scan(config_path, output):
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(Path(__file__).resolve().parents[1]), str(PYTHON), '-B', '-m',
        'gpu.orch_r125_continual_guard', 'scan', '--config', str(config_path)]
    report = json.loads(subprocess.check_output(command, text=True, timeout=90))
    write(output, report)
    return report


def gpu_descriptors():
    result = []
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            target = os.readlink(descriptor)
            if not target.startswith('/dev/nvidia'):
                continue
            metadata = descriptor.stat()
            require(stat.S_ISCHR(metadata.st_mode), 'GPU_descriptor_character_device')
            result.append(dict(fd=int(descriptor.name), path=target,
                major=os.major(metadata.st_rdev), minor=os.minor(metadata.st_rdev)))
        except FileNotFoundError:
            continue
    return sorted(result, key=lambda entry: entry['fd'])


def nvml_discovery_probe():
    before = gpu_descriptors()
    import torch
    require(not torch.cuda.is_initialized(), 'probe_must_not_initialize_CUDA')
    after_import = gpu_descriptors()
    count = torch.cuda._device_count_nvml()
    require(not torch.cuda.is_initialized(), 'NVML_only_no_CUDA_fallback')
    return dict(schema='R136_NVML_CPU_DISCOVERY_PROBE_V1', pid=os.getpid(),
        observed_unix=time.time(), cvd=os.environ.get('CUDA_VISIBLE_DEVICES'),
        before=before, after_import=after_import, after_nvml=gpu_descriptors(),
        nvml_visible_count=count, torch_cuda_initialized=False,
        torch_version=torch.__version__, torch_cuda_source=ref(Path(torch.cuda.__file__)),
        cgroup=Path('/proc/self/cgroup').read_text(),
        diagnostic_only=True, admission_receipt=False, gpu_model_calls=0)


def device_containment_command(physical, minor, uid, gid, unit, source, command, lifetime):
    require(type(physical) is int and physical in DEVICES, 'explicit_NODE4_physical')
    require(type(minor) is int and 0 <= minor <= 7, 'verified_GPU_minor')
    require(type(uid) is int and uid > 0 and type(gid) is int and gid > 0, 'nonroot_probe_identity')
    require(re.fullmatch(r'orch-r136-(nvml|native)-[a-f0-9]{32}', unit), 'unique_probe_unit')
    source = Path(source)
    require(source.is_absolute() and '..' not in source.parts, 'absolute_probe_source')
    require(type(lifetime) is int and lifetime > 0, 'bounded_containment_lifetime')
    properties = dict(User=str(uid), Group=str(gid), NoNewPrivileges='yes',
        DevicePolicy='strict', CapabilityBoundingSet='', AmbientCapabilities='',
        ProtectControlGroups='yes', RuntimeMaxSec=str(lifetime), TimeoutStopSec='5',
        KillMode='control-group', WorkingDirectory=str(source))
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
        f'/dev/nvidia{minor} rw', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit='+unit,
        *['--property='+key+'='+value for key, value in properties.items()],
        '--property=DeviceAllow=', *['--property=DeviceAllow='+entry for entry in devices],
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'HOME='+str(BASE),
        'CUDA_VISIBLE_DEVICES='+DEVICES[physical], 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(source), 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
        'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1', 'TOKENIZERS_PARALLELISM=false', *command]


def containment_probe_command(physical, minor, uid, gid, unit, source):
    require(re.fullmatch(r'orch-r136-nvml-[a-f0-9]{32}', unit), 'unique_probe_unit')
    return device_containment_command(physical, minor, uid, gid, unit, source,
        [str(PYTHON), '-B', '-m', 'gpu.orch_r137_node4_containment', 'probe-nvml'], 30)


def device_minor(gpu_uuid):
    require(gpu_uuid in DEVICES.values(), 'known_NODE4_UUID')
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == gpu_uuid:
            matches.append(int(fields['Device Minor'].strip()))
    require(len(matches) == 1 and 0 <= matches[0] <= 7, 'one_kernel_UUID_minor_mapping')
    node = Path('/dev/nvidia'+str(matches[0]))
    metadata = node.lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
        and os.minor(metadata.st_rdev) == matches[0], 'real_bound_GPU_character_device')
    return matches[0]


def verify_device_containment(config, plan):
    policy = config['device_containment']
    require_host()
    require(os.getuid() == policy['uid'] > 0 and os.getgid() == policy['gid'] > 0, 'nonroot_contained_identity')
    require(Path('/proc/self/cgroup').read_text().strip() ==
        '0::/system.slice/'+policy['unit']+'.service', 'exact_contained_service')
    require(device_minor(plan['gpu_uuid']) == policy['minor'], 'unchanged_UUID_minor')
    require(not gpu_descriptors(), 'no_inherited_GPU_descriptors')
    denied = []
    for minor in range(8):
        if minor == policy['minor']:
            continue
        try:
            descriptor = os.open('/dev/nvidia'+str(minor), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            denied.append(minor)
        else:
            os.close(descriptor)
            raise ValueError('foreign_GPU_not_denied_before_native_start')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'one_GPU_contained_environment')
    return dict(policy=policy, denied_foreign_minors=denied,
        checked_unix=time.time(), pid=os.getpid(), existing_processes_modified=False)


def contained_native(config_path):
    from gpu import orch_r125_continual_guard as guard
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    config, plan = guard.validate(config_path)
    attempt = Path(config['attempt_dir'])
    proof = verify_device_containment(config, plan)
    write(attempt/'CONTAINMENT_VERIFIED.json', proof)
    admission = native.read(attempt/'ADMISSION.json')
    admitted = native.read(attempt/'ADMISSION_TIME.json')['verified_unix']
    require(admission['clear'] and admission['scanner_euid'] == 0 and not admission['blocking_reasons']
        and admission['gpu']['uuid'] == plan['gpu_uuid'] and 0 <= time.time()-admitted < 100,
        'fresh_global_admission_before_contained_native')
    remaining = int(plan['hard_end_unix']-time.time()-10)
    require(remaining > 10, 'time_for_native_load')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining)+'s', str(PYTHON),
        '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(config_path)]
    process = None
    try:
        with (attempt/'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            identity = preservation.identity(process.pid)
            publish_launch(attempt/'LAUNCH.json', dict(pid=process.pid,
                parent_start_ticks=identity['start_ticks'], started_unix=time.time(),
                admission_verified_unix=admitted, admission_sha256=native.sha(attempt/'ADMISSION.json'),
                guard_sha256=native.sha(config_path), command_sha256=native.digest(command),
                plan_sha256=config['plan_sha256'], gpu_uuid=plan['gpu_uuid'],
                hard_end_unix=plan['hard_end_unix'], no_retry=True,
                containment_sha256=native.sha(attempt/'CONTAINMENT_VERIFIED.json')))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            status = process.wait()
        write(attempt/'EXIT.json', dict(exit_code=status, finished_unix=time.time(), no_retry=True))
        require(status == 0, 'contained_native_failed_no_retry')
    except BaseException:
        reap_owned_child(process)
        raise


def contained_supervise(config_path):
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(config_path)
    require_host()
    attempt = Path(config['attempt_dir'])
    (attempt/'DISPATCH_ONCE').mkdir()
    report = scan(config_path, attempt/'ADMISSION.json')
    require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
        and report['gpu']['uuid'] == plan['gpu_uuid'], 'unchanged_global_exclusive_admission')
    write(attempt/'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    policy = config['device_containment']
    command = device_containment_command(plan['physical'], policy['minor'], policy['uid'],
        policy['gid'], policy['unit'], plan['source_root'], [str(PYTHON), '-B', '-m',
            'gpu.orch_r137_node4_containment', 'contained-native', '--config', str(config_path)],
        max(1, int(plan['hard_end_unix']-time.time())))
    write(attempt/'CONTAINED_COMMAND.json', dict(command=command, started_unix=time.time()))
    result = subprocess.run(command, check=False)
    write(attempt/'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
    require(result.returncode == 0, 'contained_service_failed_no_retry')


def same_life_plan(old_plan, source):
    plan = deepcopy(old_plan)
    plan['source_root'] = str(source)
    if plan.get('startup_context'):
        relative = Path(old_plan['startup_context']['path']).relative_to(old_plan['source_root'])
        plan['startup_context']['path'] = str(Path(source)/relative)
        require(native.sha(plan['startup_context']['path']) == old_plan['startup_context']['sha256'],
            'identical_startup_bytes')
    require(native.experiment_binding(plan) == native.experiment_binding(old_plan), 'same_life_experiment')
    return native.validate_plan(plan)


def stage_contained_resume(old_config_path, source, output, cpu_receipt):
    old_config_path, source, output, cpu_receipt = map(Path, (old_config_path, source, output, cpu_receipt))
    old_config = native.read(old_config_path)
    old_plan = native.read(old_config['plan_path'])
    require(native.sha(old_config['plan_path']) == old_config['plan_sha256'], 'old_bound_plan')
    require(type(old_plan['physical']) is int and old_plan['physical'] == 6
            and old_plan['gpu_uuid'] == DEVICES[6], 'first_NODE4_RAW6_handoff_only')
    for relative, checksum in old_config['source_pins'].items():
        require(native.sha(Path(old_plan['source_root'])/relative) == checksum, 'old_source_unchanged')
    cpu = native.read(cpu_receipt)
    actual = {str(path.relative_to(source)): native.sha(path) for path in source.rglob('*.py')}
    require(cpu['passed'] is True and cpu['source_pins'] == actual, 'tested_entire_new_source')
    changed = {relative for relative in set(actual) | set(old_config['source_pins'])
        if actual.get(relative) != old_config['source_pins'].get(relative)}
    require(changed <= {'gpu/orch_r137_node4_containment.py', 'tests/test_orch_r137_node4_containment.py',
                       'gpu/orch_r133_retire_old_lanes.py'}
            and 'gpu/orch_r133_retire_old_lanes.py' not in old_config['source_pins'],
        'operator_only_runtime_bytes_unchanged')
    require(source.is_absolute() and source != Path(old_plan['source_root']) and output.is_absolute(),
        'new_absolute_operator_source_and_attempt')
    plan = same_life_plan(old_plan, source)
    output.mkdir(parents=True, exist_ok=False)
    write(output/'PLAN.json', plan)
    allocation = dict(native.read(old_config['allocation_path']), plan_sha256=native.sha(output/'PLAN.json'),
        declared_unix=time.time(), checkpoint_resume=True, cpu_receipt_path=str(cpu_receipt),
        cpu_receipt_sha256=native.sha(cpu_receipt), current_CPU_gate_pushed=False,
        builder_entry='R136 same-life device containment; original published allocation, own dated CPU gate')
    write(output/'ALLOCATION.json', allocation)
    config = dict(old_config, plan_path=str(output/'PLAN.json'), plan_sha256=native.sha(output/'PLAN.json'),
        allocation_path=str(output/'ALLOCATION.json'), allocation_sha256=native.sha(output/'ALLOCATION.json'),
        attempt_dir=str(output), resume=True, source_pins=actual,
        device_containment=dict(minor=device_minor(plan['gpu_uuid']), uid=os.getuid(), gid=os.getgid(),
            unit='orch-r136-native-'+uuid.uuid4().hex))
    write(output/'GUARD.json', config)
    write(output/'SAME_LIFE.json', dict(old_config=ref(old_config_path), old_plan=ref(old_config['plan_path']),
        new_plan=ref(output/'PLAN.json'), new_source_pins_sha256=native.digest(actual),
        reset=False, lease_extended=False, runtime_changed=False, parent_untouched=True,
        changed_source_files=sorted(changed), cpu_receipt=ref(cpu_receipt)))
    return dict(guard_path=str(output/'GUARD.json'), plan_sha256=config['plan_sha256'])


def validate_handoff_processes(request, old_config, old_plan, launch):
    require(type(old_plan['physical']) is int and old_plan['physical'] == 6
            and old_plan['gpu_uuid'] == DEVICES[6], 'NODE4_RAW6_only_saved_handoff')
    require(type(request['wait_seconds']) is int and 1 <= request['wait_seconds'] <= 1200,
        'bounded_handoff_wait')
    path = request['old_config']['path']
    actor, timer, supervisor = (request[name] for name in ('actor', 'timer', 'supervisor'))
    prefix = [str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard']
    require(actor['argv'] == prefix+['native', '--config', path]
        and supervisor['argv'] == prefix+['supervise', '--config', path], 'exact_old_native_guard_pair')
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
        and len(timer['argv']) == 11 and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3])
        and timer['argv'][4:] == actor['argv'], 'exact_old_timeout_command')
    require(actor['parent'] == timer['pid'] and timer['parent'] == supervisor['pid']
        and timer['pid'] == launch['pid'] and timer['start_ticks'] == launch['parent_start_ticks'],
        'exact_owned_native_ancestry')
    require(all(process['uid'] == os.getuid() for process in (actor, timer, supervisor))
        and actor['cvd'] == timer['cvd'] == [DEVICES[6]] and supervisor['cvd'] == [''],
        'owned_single_device_processes')
    require(launch['guard_sha256'] == request['old_config']['sha256']
        and launch['plan_sha256'] == old_config['plan_sha256'], 'original_launch_binding')


def verify_stream_snapshot(snapshot, original, expected_sha256):
    from gpu.orch_r125_stream_journal import StreamJournal
    original_inbox = SimpleNamespace(inbox=Path(original)/'inbox')
    class SnapshotJournal(StreamJournal):
        def _inbox_event(self, message, path, source_sha256):
            return StreamJournal._inbox_event(original_inbox, message, path, source_sha256)
    with SnapshotJournal(snapshot, create=False) as journal:
        latest = journal.latest_checkpoint()
        require(latest is not None and latest['expected_sha256'] == expected_sha256,
            'full_journal_chain_verified_before_stop')
    return latest


def handoff_contained(request, output):
    from gpu import orch_r125_continual_guard as guard
    from gpu.orch_r131_saved_boundary_handoff import sleep_boundary, readout_started
    require_host()
    old_reference = request['old_config']
    require(native.sha(old_reference['path']) == old_reference['sha256'], 'unchanged_original_guard')
    old_config = native.read(old_reference['path'])
    require(native.sha(old_config['plan_path']) == old_config['plan_sha256'], 'unchanged_original_plan')
    old_plan = native.read(old_config['plan_path'])
    launch = native.read(Path(old_config['attempt_dir'])/'LAUNCH.json')
    validate_handoff_processes(request, old_config, old_plan, launch)
    config, plan = guard.validate(request['new_config'])
    verify_probe_receipt(request['device_probe'], config, plan)
    require(config['resume'] is True and plan == same_life_plan(old_plan, plan['source_root']),
        'operator_only_same_life_plan')
    same_life = native.read(Path(config['attempt_dir'])/'SAME_LIFE.json')
    cpu = same_life['cpu_receipt']
    require(native.sha(cpu['path']) == cpu['sha256'] and native.read(cpu['path'])['passed'] is True,
        'bound_handoff_CPU_receipt')
    require(request['gate']['cpu_passed'] is True and '[Builder]' in request['gate']['builder_line']
        and '2026-09-16' in request['gate']['builder_line'], 'dated_handoff_CPU_gate')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output/'REQUEST.json', request)
    root = Path(plan['root'])
    deadline = min(time.monotonic()+request['wait_seconds'],
        time.monotonic()+plan['hard_end_unix']-time.time()-120)
    pair = [(name, request[name]) for name in ('supervisor', 'timer', 'actor')]
    descriptors, paused = {}, []
    def interrupted(signum, frame):
        raise SystemExit('handoff_interrupted_resume_exact_paused_processes')
    handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGHUP)}
    try:
        for name, process in pair:
            preservation.same(process)
            descriptors[name] = os.pidfd_open(process['pid'])
            preservation.same(process)
        while time.monotonic() < deadline:
            boundary = sleep_boundary(root)
            if boundary is None or not readout_started(root, boundary['cycle'],
                    plan.get('readout_revision', 1), request['timer']['pid']):
                time.sleep(.5)
                continue
            for name, process in pair:
                paused.append((name, process))
                preservation.pause(process, descriptors[name])
            checked = sleep_boundary(root)
            if checked is None or checked['record_sha256'] != boundary['record_sha256']:
                for name, process in reversed(paused):
                    signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
                paused.clear()
                continue
            readout = root/'readouts'/native.readout_name(plan, boundary['cycle'])
            complete = readout/'COMPLETE.json'
            while time.monotonic() < deadline and not complete.exists():
                time.sleep(.5)
            require(complete.exists() and native.read(complete)['status'] == 'COMPLETE',
                'finished_fresh_readout_before_handoff')
            readout_pid = native.read(complete)['pid']
            while time.monotonic() < deadline:
                process_path = Path('/proc', str(readout_pid), 'stat')
                if not process_path.exists() or process_path.read_text().rsplit(')', 1)[1].split()[0] == 'Z':
                    break
                time.sleep(.1)
            else:
                raise ValueError('fresh_readout_process_not_exited')
            require(sleep_boundary(root) == boundary, 'saved_frontier_after_readout')
            stream = native.ContinualStream.restore(dict(state=boundary['state'], sha256=boundary['state_sha256']),
                expected_sha256=boundary['state_sha256'])
            native.verify_experiment_resume(plan, stream.experiment)
            checkpoint_path = root/'checkpoints'/f"sleep_{boundary['cycle']:06d}"/'COMMIT.json'
            checkpoint = native.read(checkpoint_path)
            native.NativeChild.verify_checkpoint(checkpoint)
            require(native.digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256
                and checkpoint.get('experiment') == stream.experiment
                and stream.deadline_unix == plan['hard_end_unix'], 'exact_saved_model_RNG_stream_and_wall')
            write(output/'BOUNDARY.json', dict(record=ref(boundary['path']),
                state_sha256=boundary['state_sha256'], checkpoint=ref(checkpoint_path),
                readout=ref(complete), cycle=boundary['cycle'], optimizer_steps=checkpoint['optimizer_steps']))
            saved = preservation.archive([root/'stream', root/'checkpoints', root/'readouts',
                old_reference['path'], old_config['plan_path'], old_config['lease_path'],
                Path(old_plan['source_root'])], output/'STATE.tar')
            require(sleep_boundary(root) == boundary, 'saved_frontier_after_archive')
            write(output/'PRESERVATION.json', dict(**saved, reset=False, optimizer_and_rng='EXACT_SAVED',
                same_root_and_inbox=True, parent_kept_running=True, observed_unix=time.time()))
            from gpu.orch_r125_stream_journal import StreamJournal
            shutil.copytree(root/'stream', output/'STREAM_VERIFY')
            verify_stream_snapshot(output/'STREAM_VERIFY', root/'stream', boundary['state_sha256'])
            require(sleep_boundary(root) == boundary, 'saved_frontier_before_stop')
            for name, process in reversed(pair):
                if preservation.alive(process):
                    preservation.same(process)
                    signal.pidfd_send_signal(descriptors[name], signal.SIGTERM)
                    signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
                    require(bool(select.select([descriptors[name]], [], [], 30)[0]), 'saved_owner_exit_no_KILL')
            paused.clear()
            write(output/'OLD_STOPPED.json', dict(old_actor=request['actor'], boundary=ref(output/'BOUNDARY.json'),
                preserved=ref(output/'PRESERVATION.json'), reset=False, stopped_unix=time.time()))
            with StreamJournal(root/'stream', create=False) as journal:
                latest = journal.latest_checkpoint()
                require(latest['expected_sha256'] == boundary['state_sha256'], 'same_authoritative_resume_state')
            command = [str(PYTHON), '-B', '-m', 'gpu.orch_r137_node4_containment',
                'contained-supervise', '--config', request['new_config']]
            with (output/'SUPERVISOR.log').open('x') as log:
                process = subprocess.Popen(command, cwd=plan['source_root'],
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=plan['source_root'],
                        PYTHONDONTWRITEBYTECODE='1'), stdin=subprocess.DEVNULL, stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True)
            receipt = dict(status='HANDOFF_DISPATCHED_NOT_LOADED', supervisor_pid=process.pid,
                command_sha256=native.digest(command), dispatched_unix=time.time(), reset=False,
                new_config=ref(request['new_config']), boundary=ref(output/'BOUNDARY.json'))
            write(output/'HANDOFF.json', receipt)
            return receipt
        write(output/'WAIT_EXPIRED.json', dict(status='NO_HANDOFF', finished_unix=time.time()))
    except BaseException as error:
        write(output/'ERROR.json', dict(error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        for name, process in reversed(paused):
            try:
                signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
            except ProcessLookupError:
                pass
        for descriptor in descriptors.values():
            os.close(descriptor)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


def probe_containment(config_path):
    config = native.read(config_path)
    plan = config['plan']
    require(type(plan['physical']) is int and plan['physical'] in DEVICES
            and plan['gpu_uuid'] == DEVICES[plan['physical']], 'owned_probe_device')
    proof = verify_device_containment(config, plan)
    observation = nvml_discovery_probe()
    require(observation['nvml_visible_count'] == 1, 'exactly_one_NVML_visible_device')
    allowed = {f"/dev/nvidia{config['device_containment']['minor']}", '/dev/nvidiactl', '/dev/nvidia-uvm'}
    require(all(item['path'] in allowed for item in observation['after_nvml']), 'no_foreign_NVML_descriptors')
    source = Path(__file__).resolve().parents[1]
    return dict(passed=True, config=ref(config_path), proof=proof, observation=observation,
                source_pins={str(path.relative_to(source)): native.sha(path) for path in source.rglob('*.py')})


def verify_probe_receipt(reference, config, plan):
    require(native.sha(reference['path']) == reference['sha256'], 'immutable_device_probe')
    result = native.read(reference['path'])
    require(result['passed'] is True and result['source_pins'] == config['source_pins'],
            'probe_same_source_closure')
    probe_ref = result['config']
    require(native.sha(probe_ref['path']) == probe_ref['sha256'], 'bound_probe_config')
    probe_config = native.read(probe_ref['path'])
    require(probe_config['plan'] == dict(physical=plan['physical'], gpu_uuid=plan['gpu_uuid']),
            'probe_same_device')
    policy = config['device_containment']
    require(all(result['proof']['policy'][key] == policy[key] for key in ('uid', 'gid', 'minor'))
            and result['proof']['denied_foreign_minors'] == [minor for minor in range(8) if minor != policy['minor']],
            'probe_all_foreign_denied')
    require(0 <= time.time()-result['proof']['checked_unix'] <= 3600
            and result['observation']['torch_cuda_initialized'] is False
            and result['observation']['nvml_visible_count'] == 1, 'recent_NVML_only_probe')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('probe-nvml', 'probe-containment', 'contained-native',
                                            'contained-supervise', 'handoff-contained'))
    parser.add_argument('--config', type=Path)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    if options.operation == 'probe-nvml':
        print(json.dumps(nvml_discovery_probe(), sort_keys=True))
    elif options.operation == 'probe-containment':
        print(json.dumps(probe_containment(options.config), sort_keys=True))
    elif options.operation == 'contained-native':
        contained_native(options.config)
    elif options.operation == 'contained-supervise':
        contained_supervise(options.config)
    else:
        print(json.dumps(handoff_contained(native.read(options.request), options.output), sort_keys=True))


if __name__ == '__main__':
    main()
