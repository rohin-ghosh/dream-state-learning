"""Explicitly gated, no-retry R153 native execution using the original R125 scan.

No historical R137 host/device table is reused. The generic R136 envelope is
followed by cgroup, kernel UUID/minor and foreign-device denial verification.
Only Main's exact promoted config can reach the original native guard handshake.
"""

import argparse
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import time

from gpu.orch_r153_community_launch import (
    DEFAULT_PROFILE, NODE5_PROFILE, NODE5_HOST_SHA256, NODE5_WALL, NODE5_LEASE_END,
    absolute, assigned_agents, containment_command, digest, encoded, native, read_bytes,
    require, unlinked, validate_capacity_release, validate_launch_gate, write_new,
)


def validate_promotion(config_path):
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(config_path)
    gate_raw = read_bytes(config['r153_main_gate_path'])
    require(digest(gate_raw) == config['r153_main_gate_sha256'], 'immutable_Main_gate')
    gate = json.loads(gate_raw)
    agent = config['r153_agent']
    assigned = assigned_agents(agent)
    validate_launch_gate(gate, agent, config['plan_sha256'], config['r153_manifest_sha256'], time.time())
    require(gate['agent_id'] == agent['id'] and config['resume'] is False
            and gate['expires_unix'] <= plan['hard_end_unix'], 'new_life_gate_no_resume')
    require(agent['node'] == assigned[agent['id']][1] and agent['physical'] == assigned[agent['id']][2]
            and agent['retiree'] == assigned[agent['id']][3]
            and plan.get('community_profile', DEFAULT_PROFILE) == agent.get('profile', DEFAULT_PROFILE)
            and plan.get('community_agent_id', agent['id']) == agent['id']
            and plan['physical'] == agent['physical'] and plan['gpu_uuid'] == agent['gpu_uuid']
            and plan['root'] == str(Path(agent['destination']) / 'life')
            and plan['source_root'] == str(Path(agent['destination']) / 'source'), 'exact_plan_agent_slot_binding')
    release_kind = 'capacity_release' if agent.get('profile') == NODE5_PROFILE else 'retirement'
    require(config.get('r153_release_kind', 'retirement') == release_kind
            and digest(read_bytes(config['r153_retirement_path'])) == config['r153_retirement_sha256']
            == gate[release_kind]['sha256'], 'preserved_exact_retirement_evidence')
    if release_kind == 'capacity_release':
        release = json.loads(read_bytes(config['r153_retirement_path']))
        validate_capacity_release(release, release['lease'])
        require(release['lease']['sha256'] == config['lease_sha256']
                and config['host_sha256'] == NODE5_HOST_SHA256 and plan['hard_end_unix'] == NODE5_WALL
                and plan['lease_end_unix'] == NODE5_LEASE_END, 'capacity_release_exact_node5_lease')
    source = absolute(plan['source_root'])
    actual = {path.relative_to(source).as_posix(): digest(read_bytes(path))
              for path in source.rglob('*') if path.is_file()}
    require(actual == config['r153_source_files'], 'entire_deployed_source_and_runtime_assets')
    for path in (source, *source.rglob('*')):
        require(not path.is_symlink() and path.stat().st_mode & 0o222 == 0, 'immutable_deployed_source')
    community = json.loads(read_bytes(Path(plan['root']).parent / 'config/COMMUNITY.json'))
    require(digest(read_bytes(Path(plan['root']).parent / 'config/COMMUNITY.json'))
            == agent['files']['config/COMMUNITY.json'], 'immutable_community_binding')
    require(community['parent']['speaker'] == 'Astra' and community['parent']['cadence_responses'] == 3,
            'Astra_only_cadence3_before_execution')
    return config, plan


def supervise(config_path):
    """Run one explicitly promoted life using the existing privileged guard scan."""
    config, plan = validate_promotion(config_path)
    root = unlinked(plan['root'])
    if root.exists():
        require(root.is_dir() and {path.name for path in root.iterdir()} <= {'workspace'}, 'new_root_no_saved_state')
        require(root.stat().st_mode & 0o077 == 0, 'private_new_life_root')
    else:
        root.mkdir(mode=0o700)
    attempt = unlinked(config['attempt_dir'])
    attempt.mkdir(mode=0o700, exist_ok=False)
    (attempt / 'DISPATCH_ONCE').mkdir()
    python = config['r153_agent']['python']
    scan = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH=' + plan['source_root'], python, '-B', '-m',
            'gpu.orch_r125_continual_guard', 'scan', '--config', str(config_path)]
    report = json.loads(subprocess.check_output(scan, text=True, timeout=90))
    write_new(attempt / 'ADMISSION.json', encoded(report))
    require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['gpu_uuid'], 'fresh_global_exclusive_admission')
    write_new(attempt / 'ADMISSION_TIME.json', encoded(dict(verified_unix=time.time())))
    validate_promotion(config_path)
    command = containment_command(plan, config['device_containment'], python,
        ['-m', 'gpu.orch_r153_community_runtime', 'contained-native', '--config', str(config_path)])
    write_new(attempt / 'CONTAINED_COMMAND.json', encoded(dict(command=command, started_unix=time.time())))
    result = subprocess.run(command, check=False)
    write_new(attempt / 'SERVICE_EXIT.json', encoded(dict(returncode=result.returncode,
                                                        finished_unix=time.time(), no_retry=True)))
    require(result.returncode == 0, 'contained_service_failed_no_retry')
    return dict(returncode=result.returncode, attempt_dir=str(attempt))


def verify_containment(config, plan):
    from gpu.orch_r137_node4_containment import gpu_descriptors
    policy = config['device_containment']
    require(digest(socket.gethostname().encode()) == config['host_sha256'], 'exact_node_host')
    require(os.getuid() == policy['uid'] > 0 and os.getgid() == policy['gid'] > 0, 'nonroot_contained_identity')
    require(Path('/proc/self/cgroup').read_text().strip() == '0::/system.slice/' + policy['unit'] + '.service',
            'exact_contained_service')
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == plan['gpu_uuid']:
            matches.append(int(fields['Device Minor'].strip()))
    require(matches == [policy['minor']], 'kernel_UUID_minor_mapping')
    metadata = Path('/dev/nvidia' + str(policy['minor'])).lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
            and os.minor(metadata.st_rdev) == policy['minor'], 'bound_GPU_character_device')
    require(not gpu_descriptors(), 'no_inherited_GPU_descriptors')
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
            raise ValueError('foreign_GPU_not_denied_before_native_start')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid']
            and os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == 'expandable_segments:True'
            and 'PYTORCH_ALLOC_CONF' not in os.environ, 'single_GPU_allocator_environment')
    return dict(policy=policy, denied_foreign_minors=denied, checked_unix=time.time(), pid=os.getpid())


def contained_native(config_path):
    from gpu import orch_r133_retire_old_lanes as preservation
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    config, plan = validate_promotion(config_path)
    attempt = Path(config['attempt_dir'])
    proof = verify_containment(config, plan)
    write_new(attempt / 'CONTAINMENT_VERIFIED.json', encoded(proof))
    report = json.loads(read_bytes(attempt / 'ADMISSION.json'))
    admitted = json.loads(read_bytes(attempt / 'ADMISSION_TIME.json'))['verified_unix']
    require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['gpu_uuid'] and 0 <= time.time() - admitted < 100,
            'fresh_admission_before_native_start')
    remaining = int(plan['hard_end_unix'] - time.time() - 10)
    require(remaining > 10, 'time_for_native_load')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's',
               config['r153_agent']['python'], '-B', '-m', 'gpu.orch_r125_continual_guard',
               'native', '--config', str(config_path)]
    process = None
    try:
        with (attempt / 'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            identity = preservation.identity(process.pid)
            publish_launch(attempt / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=identity['start_ticks'],
                started_unix=time.time(), admission_verified_unix=admitted,
                admission_sha256=digest(read_bytes(attempt / 'ADMISSION.json')),
                guard_sha256=digest(read_bytes(config_path)), command_sha256=native.digest(command),
                plan_sha256=config['plan_sha256'], gpu_uuid=plan['gpu_uuid'], hard_end_unix=plan['hard_end_unix'],
                no_retry=True, containment_sha256=digest(read_bytes(attempt / 'CONTAINMENT_VERIFIED.json'))))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            status = process.wait()
        write_new(attempt / 'EXIT.json', encoded(dict(exit_code=status, finished_unix=time.time(), no_retry=True)))
        require(status == 0, 'contained_native_failed_no_retry')
    except BaseException:
        reap_owned_child(process)
        raise



def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('supervise', 'contained-native'))
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == 'supervise':
        print(json.dumps(supervise(args.config), sort_keys=True))
    else:
        contained_native(args.config)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
