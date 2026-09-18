"""CPU-only staging and explicit one-shot launch for the exact R145 owned lanes."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from gpu import orch_r145_node3_capacity_recovery as capacity
from gpu import orch_r145_node3_pending_recovery as pending
from gpu import orch_r145_node3_admitted_recovery as admitted


OWNED = ('orch_r145_node3_capacity_recovery.py', 'orch_r145_node3_pending_recovery.py',
         'orch_r145_node3_admitted_recovery.py', 'orch_r145_node3_stage_recovery.py')
TESTS = ('test_orch_r145_node3_capacity_recovery.py', 'test_orch_r145_node3_pending_recovery.py',
         'test_orch_r145_node3_admitted_recovery.py')
require = capacity.require


def reference(path):
    return dict(path=str(Path(path).absolute()), sha256=capacity.file_sha(path))


def unchanged_plan(original, source):
    plan = deepcopy(original)
    plan['source_root'] = str(source)
    if 'startup_context' in plan:
        relative = Path(original['startup_context']['path']).relative_to(original['source_root'])
        plan['startup_context']['path'] = str(source / relative)
    capacity.owned_plan(plan)
    return plan


def old_process_absent(control):
    launch = json.loads((control / 'LAUNCH.json').read_text())
    stat = Path('/proc', str(launch['pid']), 'stat')
    if stat.exists():
        require(stat.read_text().rsplit(')', 1)[1].split()[19] != launch['parent_start_ticks'],
                'original_timeout_identity_still_present')
    source_tokens = ('gpu.orch_r142_support_recovery', 'gpu.orch_r143_creative_none_recovery')
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            arguments = (directory / 'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        if str(control / 'GUARD_CONTAINED.json').encode() in arguments:
            require(not any(token.encode() in arguments for token in source_tokens), 'original_recovery_actor_still_present')


def stage(physical, package, tag):
    require(physical in capacity.LANES and tag.replace('_', '').isalnum(), 'owned_lane_safe_unique_tag')
    package = Path(package).absolute()
    lane = pending.load_lane(physical, package / 'EXITED_5_6_SUMMARY.json', package / 'INVENTORY.json')
    store = pending.LocalCaptureStore(pending.ORIGIN)
    inventory = lane.inventory
    original_source = Path(inventory['source_root'])
    original_control = Path(inventory['guard_path']).parent
    old_process_absent(original_control)
    original_command = json.loads((original_control / 'CONTAINED_COMMAND.json').read_text())['command']
    interpreter = original_command[original_command.index('-B') - 1]
    require(os.path.samefile(sys.executable, interpreter), 'original_python_interpreter_binary')
    require(capacity.installed_runtime_pins() == json.loads((package / 'gpu' / capacity.RUNTIME_FILENAME).read_text()),
            'staging_actual_installed_runtime_no_skip_substitute')
    original_guard = json.loads(store.raw(inventory['guard_path'], inventory['guard_sha256']))
    original_plan = json.loads(store.raw(inventory['plan_path'], inventory['plan_sha256']))
    pending.verify_saved_files(lane, store)
    failure = [reference(original_control / name) for name in ('EXIT.json', 'NATIVE.log', 'LAUNCH.json', 'GUARD_CONTAINED.json', 'PLAN.json', 'CONTAINED_COMMAND.json')]
    require(json.loads((original_control / 'EXIT.json').read_text()) == inventory['exit_receipt'], 'same_original_failed_exit')
    log = (original_control / 'NATIVE.log').read_text()
    require('torch.OutOfMemoryError: CUDA out of memory.' in log and 'backward()' in log, 'original_capacity_failure')
    source = lane.root.parent / ('source_r145_' + tag)
    control = lane.root.parent / ('control_r145_' + tag)
    require(not source.exists() and not control.exists(), 'new_source_control_no_retry_or_overwrite')
    shutil.copytree(original_source, source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for path in (source, *source.rglob('*')):
        require(not path.is_symlink(), 'no_frozen_source_symlinks')
        path.chmod(path.stat().st_mode | 0o200)
    control.mkdir()
    for name in OWNED:
        shutil.copyfile(package / 'gpu' / name, source / 'gpu' / name)
    for name in TESTS:
        shutil.copyfile(package / 'tests' / name, source / 'tests' / name)
    helper = package / 'gpu' / 'orch_r145_suffix_loss.py'
    require(capacity.file_sha(helper) == 'd5e69655fd30f3317d114bd4aab2025024fdfb1521664b536d54ad61069bf026',
            'unchanged_Main_helper_test_dependency')
    shutil.copyfile(helper, source / 'gpu' / helper.name)
    captures = Path('research_loop/workers/r144_node3_targets_20260916t1515z_operator2')
    (source / captures).mkdir(parents=True, exist_ok=True)
    for name in ('EXITED_5_6_SUMMARY.json', 'INVENTORY.json'):
        shutil.copyfile(package / name, source / captures / name)
    runtime = package / 'gpu' / capacity.RUNTIME_FILENAME
    require(capacity.file_sha(runtime) == admitted.RUNTIME_SHA, 'Main_runtime_bytes')
    shutil.copyfile(runtime, source / 'gpu' / capacity.RUNTIME_FILENAME)
    native = source / 'gpu' / 'orch_r125_continual_native.py'
    native.write_text(capacity.patch_source(native.read_text(), admitted.RUNTIME_SHA))
    plan = unchanged_plan(original_plan, source)
    pending.verify_source_and_plan(lane, store, plan)
    from gpu.orch_r125_stream_journal import StreamJournal
    with StreamJournal(lane.root / 'stream', create=False) as journal:
        state, records = pending.scan_records(journal)
        require(len(records) == lane.spec['end'], 'unchanged_original_journal_count')
        for item in lane.summary['suffix']:
            require(json.loads(store.raw(item['path'], item['sha256'])) == records[int(Path(item['path']).stem)],
                    'same_original_raw_suffix')
    source_pins = {str(path.relative_to(source)): capacity.file_sha(path) for path in source.rglob('*.py')}
    owned_pins = {name: capacity.file_sha(source / 'gpu' / name) for name in OWNED}
    test_environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                            PYTHONPATH=str(source), R145_ORIGINAL_NATIVE=str(original_source / 'gpu/orch_r125_continual_native.py'))
    with (control / 'CPU_INTEGRATION.log').open('x') as output:
        result = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v',
            *['tests.' + Path(name).stem for name in TESTS]], cwd=source, env=test_environment,
            stdout=output, stderr=subprocess.STDOUT, timeout=90)
    require(result.returncode == 0, 'scoped_remote_CPU_tests_pass')
    capacity.save_once(control / 'CPU_GATE.json', dict(status='PASS', source_pins=source_pins, owned_pins=owned_pins,
        test_log=reference(control / 'CPU_INTEGRATION.log'), actual_GPU_validated=False, created_unix=time.time()))
    capacity.save_once(control / 'PLAN.json', plan)
    allocation = json.loads(Path(original_guard['allocation_path']).read_text())
    allocation.update(plan_sha256=capacity.file_sha(control / 'PLAN.json'), declared_unix=time.time(),
                      cpu_tests_passed=True, builder_entry_pushed=True)
    capacity.save_once(control / 'ALLOCATION.json', allocation)
    policy = deepcopy(original_guard['device_containment'])
    require(policy['minor'] == physical and policy['uid'] == os.getuid() and policy['gid'] == os.getgid(), 'same_service_identity')
    policy['unit'] = 'orch-r133-node3-' + uuid.uuid4().hex
    recovery_output = lane.root / 'recoveries' / ('r145-' + tag)
    manifest = dict(schema=admitted.SCHEMA, physical=physical, plan_sha256=capacity.file_sha(control / 'PLAN.json'),
        source_pins=source_pins, owned_pins=owned_pins, runtime=reference(source / 'gpu' / capacity.RUNTIME_FILENAME),
        stack_cpu=reference(package / 'CPU_STACK.log'), cpu_gate=reference(control / 'CPU_GATE.json'),
        summary=reference(package / 'EXITED_5_6_SUMMARY.json'), inventory=reference(package / 'INVENTORY.json'),
        capture_binding=lane.binding, failure_evidence=failure, recovery_output=str(recovery_output),
        broad_R144_guard_patch=False, actual_GPU_validated=False)
    capacity.save_once(control / 'MANIFEST.json', manifest)
    config = deepcopy(original_guard)
    for key in ('r142_manifest', 'r142_acknowledgment', 'r143_manifest', 'r143_acknowledgment'):
        config.pop(key, None)
    config.update(plan_path=str(control / 'PLAN.json'), plan_sha256=capacity.file_sha(control / 'PLAN.json'),
        source_pins=source_pins, attempt_dir=str(control), resume=True, device_containment=policy,
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=capacity.file_sha(control / 'ALLOCATION.json'),
        r145_manifest=reference(control / 'MANIFEST.json'))
    capacity.save_once(control / 'CONFIG_PENDING_ACK.json', config)
    admitted.verify_manifest(config, plan, acknowledge=False)
    capacity.save_once(control / 'RELEASE.json', dict(status='RELEASED', physical=physical, uuid=plan['gpu_uuid'],
        original_failed_exit=inventory['exit_receipt'], original_process_absent=True, signals_sent=0, observed_unix=time.time()))
    result = dict(status='STAGED_REQUIRES_EXACT_ACK', physical=physical, control=str(control), source=str(source),
                  manifest=reference(control / 'MANIFEST.json'), recovery_output=str(recovery_output))
    capacity.save_once(control / 'STAGED.json', result)
    for path in (*source.rglob('*'), source):
        path.chmod(path.stat().st_mode & ~0o222)
    print(json.dumps(result, sort_keys=True), flush=True)


def launch(control, acknowledgment):
    control = Path(control).absolute()
    config = json.loads((control / 'CONFIG_PENDING_ACK.json').read_text())
    plan = json.loads(Path(config['plan_path']).read_text())
    capacity.owned_plan(plan)
    require(control == Path(config['attempt_dir']) and control.parent == Path(plan['root']).parent
            and control.name.startswith('control_r145_'), 'exact_owned_control')
    require(not (control / 'DISPATCH_ONCE').exists() and not (control / 'LAUNCH_REQUESTED.json').exists(), 'one_launch_only')
    config['r145_acknowledgment'] = reference(acknowledgment)
    admitted.verify_manifest(config, plan)
    capacity.save_once(control / 'GUARD_CONTAINED.json', config)
    capacity.save_once(control / 'LAUNCH_REQUESTED.json', dict(requested_unix=time.time(), retry_allowed=False))
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=plan['source_root'])
    command = [sys.executable, '-B', '-m', admitted.MODULE, 'supervise', '--config', str(control / 'GUARD_CONTAINED.json'),
               '--release', str(control / 'RELEASE.json')]
    with (control / 'SUPERVISOR.log').open('x') as output:
        process = subprocess.Popen(command, cwd=plan['source_root'], env=environment,
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    result = dict(pid=process.pid, command=command, requested_unix=time.time(), loaded=False)
    capacity.save_once(control / 'SUPERVISOR_REQUEST.json', result)
    print(json.dumps(result, sort_keys=True), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    staging = commands.add_parser('stage')
    staging.add_argument('--physical', type=int, choices=(5, 6), required=True)
    staging.add_argument('--package', type=Path, required=True)
    staging.add_argument('--tag', required=True)
    launching = commands.add_parser('launch')
    launching.add_argument('--control', type=Path, required=True)
    launching.add_argument('--acknowledgment', type=Path, required=True)
    arguments = vars(parser.parse_args())
    action = arguments.pop('action')
    (stage if action == 'stage' else launch)(**arguments)


if __name__ == '__main__':
    main()
