"""Node3 exact-source target-policy inventory and staging; never signals or launches."""

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import time
import uuid

from gpu.orch_r144_target_patch import patch_source, without_sleep
from gpu.orch_r144_sleep_targets import POLICY


BASE = Path('/localhome/local-rohing')
HOST = 'ipp2-ovx-p6-09'
NATIVE = 'gpu/orch_r125_continual_native.py'
HELPER = 'gpu/orch_r144_sleep_targets.py'
DEVICES = {
    0: 'GPU-0ee6f753-c61e-e18a-8aea-acccd3042939',
    1: 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821',
    2: 'GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1',
    3: 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e',
    4: 'GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4',
    5: 'GPU-bc211959-642d-664b-3581-42a0dbe434e9',
    6: 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8',
    7: 'GPU-319224de-e668-1822-d80b-4b24d15968ae',
}
EXITED = {
    5: BASE / 'orch_r133_node3_creative_none_20260916_attempt1/control_r143_creative_none_20260916t1442z_attempt2/GUARD_CONTAINED.json',
    6: BASE / 'orch_r133_node3_support_none_20260916_attempt1/control_r142_support_20260916t1410z/GUARD_CONTAINED.json',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def closure(source):
    source = Path(source)
    require(source.is_absolute() and not any(path.is_symlink() for path in (source, *source.parents)),
            'canonical_source_root')
    paths = sorted(source.rglob('*'))
    require(not any(path.is_symlink() for path in paths), 'source_symlink_rejected')
    return {str(path.relative_to(source)): sha(path) for path in paths if path.suffix == '.py' and path.is_file()}


def process(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=pid, start_ticks=fields[19], parent=int(fields[1]), group=int(fields[2]),
        uid=directory.stat().st_uid, state=fields[0],
        argv=(directory / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'),
        cwd=str((directory / 'cwd').resolve()), cgroup=(directory / 'cgroup').read_text().strip(),
        environment=[part.decode() for part in (directory / 'environ').read_bytes().split(b'\0')
            if part.startswith((b'CUDA_VISIBLE_DEVICES=', b'PYTORCH_CUDA_ALLOC_CONF=', b'PYTORCH_ALLOC_CONF='))])


def discover():
    require(socket.gethostname() == HOST, 'node3_only')
    found = {}
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            if directory.stat().st_uid != os.getuid():
                continue
            args = (directory / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
            if len(args) != 7 or args[1:3] != ['-B', '-m'] or args[4:6] != ['native', '--config']:
                continue
            if args[3] not in ('gpu.orch_r125_continual_guard', 'gpu.orch_r142_support_recovery',
                               'gpu.orch_r143_creative_none_recovery'):
                continue
            config = read(args[6])
            plan = read(config['plan_path'])
            physical = plan['physical']
            require(physical in DEVICES and physical not in found, 'unique_node3_child')
            actor = process(int(directory.name))
            require(actor['state'] not in ('T', 't', 'Z', 'X'), 'preserve_active_child')
            found[physical] = (Path(args[6]), actor)
        except (FileNotFoundError, ProcessLookupError):
            continue
    return found


def inspect_lane(physical, config_path, actor):
    config, plan = read(config_path), read(read(config_path)['plan_path'])
    require(plan['physical'] == physical and plan['gpu_uuid'] == DEVICES[physical], 'exact_own_uuid')
    require(sha(config['plan_path']) == config['plan_sha256'], 'original_plan_pinned')
    for key in ('lease', 'allocation'):
        require(sha(config[key + '_path']) == config[key + '_sha256'], key + '_pinned')
    source = Path(plan['source_root'])
    require(source.is_relative_to(BASE) and Path(plan['root']).is_relative_to(BASE), 'node3_roots')
    pins = closure(source)
    require(pins == config['source_pins'], 'exact_original_source_closure')
    old = (source / NATIVE).read_text()
    patched = patch_source(old)
    before = without_sleep(ast.parse(old))
    require(before == without_sleep(ast.parse(patched)), 'non_sleep_ast_exact')
    actors = {}
    if actor:
        require(actor['cwd'] == str(source) and actor['uid'] == os.getuid(), 'actual_source_owner')
        require('CUDA_VISIBLE_DEVICES=' + plan['gpu_uuid'] in actor['environment'], 'actual_gpu_env')
        timer = process(actor['parent'])
        actors = dict(actor=actor, timer=timer, supervisor=process(timer['parent']))
        latest = process(actor['pid'])
        require(all(latest[key] == actor[key] for key in actor if key != 'state'), 'stable_process_identity')
    records = sorted(path for path in (Path(plan['root']) / 'stream/records').glob('*.json')
                     if re.fullmatch(r'\d{20}\.json', path.name))
    head = read(records[-1]) if records else {}
    attempt = Path(config['attempt_dir'])
    exit_receipt = read(attempt / 'EXIT.json') if (attempt / 'EXIT.json').exists() else None
    suffix = []
    if not actor:
        for path in reversed(records):
            record = read(path)
            document = record.get('document', {})
            suffix.append(dict(path=str(path), sha256=sha(path), kind=record.get('kind'),
                document_keys=sorted(document), metadata={key: document[key] for key in
                    ('cycle', 'optimizer_steps', 'optimizer_step', 'total_optimizer_steps',
                     'checkpoint', 'checkpoint_sha256', 'status', 'source_sha256', 'new_row_sha256',
                     'rehearsal_row_sha256', 'adapter_sha256', 'state_sha256') if key in document}))
            if record.get('kind') == 'SLEEP_COMPLETE':
                break
        suffix.reverse()
    return dict(physical=physical, gpu_uuid=plan['gpu_uuid'], minor=os.minor(os.stat('/dev/nvidia' + str(physical)).st_rdev),
        live=actor is not None, processes=actors, guard_path=str(config_path), guard_sha256=sha(config_path),
        plan_path=config['plan_path'], plan_sha256=config['plan_sha256'], root=plan['root'], source_root=str(source),
        lease_sha256=config['lease_sha256'], allocation_sha256=config['allocation_sha256'],
        source_pins=pins, python_files=len(pins), containment=config.get('device_containment'),
        old_native_sha256=sha(source / NATIVE), patched_native_sha256=sha_bytes(patched.encode()),
        non_sleep_ast_sha256=sha_bytes(before.encode()), exact_patch_supported=True,
        journal_head=dict(path=str(records[-1]) if records else None, kind=head.get('kind'),
            sha256=sha(records[-1]) if records else None), exit_receipt=exit_receipt,
        recovery_guard_keys=[key for key in config if 'r142' in key or 'r143' in key],
        exited_suffix_from_last_sleep=suffix, suffix_chain_replay_verified=False,
        boundary_proven=False, launch_ready=False)


def relocate_plan(plan, destination):
    proposed = deepcopy(plan)
    proposed['source_root'] = str(destination)
    if plan.get('startup_context'):
        relative = Path(plan['startup_context']['path']).relative_to(plan['source_root'])
        proposed['startup_context']['path'] = str(destination / relative)
    normalized = deepcopy(proposed)
    normalized['source_root'] = plan['source_root']
    if plan.get('startup_context'):
        normalized['startup_context']['path'] = plan['startup_context']['path']
    require(normalized == plan, 'plan_semantics_exact')
    return proposed


def stage_lane(lane, output, helper_path):
    source, destination = Path(lane['source_root']), output / 'source'
    config = read(lane['guard_path'])
    require(sha(lane['guard_path']) == lane['guard_sha256'], 'guard_unchanged')
    require(closure(source) == lane['source_pins'], 'source_unchanged_before_copy')
    require(HELPER not in lane['source_pins'], 'never_overwrite_existing_helper')
    output.mkdir()
    shutil.copytree(source, destination)
    require(closure(destination) == lane['source_pins'], 'copy_exact_before_patch')
    old = (destination / NATIVE).read_bytes()
    patched = patch_source(old.decode()).encode()
    require(sha_bytes(patched) == lane['patched_native_sha256'], 'exact_known_patch')
    native_path, helper_directory = destination / NATIVE, (destination / HELPER).parent
    native_mode, directory_mode = stat.S_IMODE(native_path.stat().st_mode), stat.S_IMODE(helper_directory.stat().st_mode)
    try:
        native_path.chmod(native_mode | stat.S_IWUSR)
        helper_directory.chmod(directory_mode | stat.S_IWUSR)
        native_path.write_bytes(patched)
        with (destination / HELPER).open('xb') as handle:
            handle.write(Path(helper_path).read_bytes())
        (destination / HELPER).chmod(native_mode)
    finally:
        native_path.chmod(native_mode)
        helper_directory.chmod(directory_mode)
    expected = dict(lane['source_pins'], **{NATIVE: sha_bytes(patched), HELPER: sha(helper_path)})
    require(closure(destination) == expected, 'only_native_plus_helper_changed')
    plan = relocate_plan(read(lane['plan_path']), destination)
    write(output / 'PROPOSED_PLAN.json', plan)
    proposed = deepcopy(config)
    proposed.update(plan_path=str(output / 'PROPOSED_PLAN.json'), plan_sha256=sha(output / 'PROPOSED_PLAN.json'),
                    source_pins=expected, resume=True, attempt_dir=str(output / 'NOT_DISPATCHED'))
    if 'device_containment' in proposed:
        proposed['device_containment']['unit'] = 'orch-r144-node3-' + uuid.uuid4().hex
    write(output / 'PROPOSED_GUARD.json', proposed)
    require(closure(source) == lane['source_pins'], 'original_source_untouched')
    result = dict(physical=lane['physical'], status='SOURCE_STAGED_NOT_LAUNCHABLE', policy=POLICY,
        old_source=str(source), new_source=str(destination), old_native_sha256=sha_bytes(old),
        new_native_sha256=sha_bytes(patched), helper_sha256=sha(helper_path),
        guard_path=str(output / 'PROPOSED_GUARD.json'), guard_sha256=sha(output / 'PROPOSED_GUARD.json'),
        plan_sha256=sha(output / 'PROPOSED_PLAN.json'), original_full_closure_preserved=True,
        non_sleep_ast_sha256=lane['non_sleep_ast_sha256'], effective_boundary=None,
        admission=False, launch_count=0, signal_count=0, raw_history_modified=False,
        recovery_entrypoint_replay_forbidden=bool(lane['recovery_guard_keys']))
    write(output / 'STAGED_SOURCE.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--helper', type=Path, required=True)
    args = parser.parse_args()
    require(args.output.is_absolute() and args.output.is_relative_to(BASE), 'new_node3_output')
    args.output.mkdir()
    found = discover()
    lanes, errors = [], []
    for physical in DEVICES:
        entry = found.get(physical) or ((EXITED[physical], None) if physical in EXITED else None)
        if not entry:
            errors.append(dict(physical=physical, error='no_live_child_or_explicit_last_guard'))
            continue
        try:
            lanes.append(inspect_lane(physical, *entry))
        except Exception as error:
            errors.append(dict(physical=physical, error=str(error), error_type=type(error).__name__))
    inventory = dict(host=HOST, observed_unix=time.time(), lanes=lanes, errors=errors,
        live_physical=sorted(found), signal_count=0, launch_count=0, policy=POLICY,
        gpu_process_inventory=subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,used_memory',
            '--format=csv,noheader'], text=True), operator_sha256=sha(__file__),
        patch_sha256=sha(Path(__file__).with_name('orch_r144_target_patch.py')), helper_sha256=sha(args.helper))
    write(args.output / 'INVENTORY.json', inventory)
    staged = []
    for lane in lanes:
        if not lane['live']:
            continue
        try:
            staged.append(stage_lane(lane, args.output / ('physical' + str(lane['physical'])), args.helper))
        except Exception as error:
            errors.append(dict(physical=lane['physical'], stage_error=str(error), error_type=type(error).__name__))
    summary = dict(observed_unix=time.time(), staged=staged, errors=errors,
        live_physical=sorted(found), launch_count=0, signal_count=0, policy=POLICY)
    write(args.output / 'SUMMARY.json', summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
