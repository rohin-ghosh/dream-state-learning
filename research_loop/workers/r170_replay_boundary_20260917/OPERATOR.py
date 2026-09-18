"""One physical1 replay handoff using the pinned saved-boundary lifecycle."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
BASE = Path('/localhome/local-rohing')
OLD_SOURCE = BASE/'orch_r144_node3_targets_20260916t1515z_2/physical1/source'
OLD_GUARD = BASE/'orch_r144_node3_target_physical1_20260916t1545z_5/GUARD.json'
LIFE = BASE/'orch_r133_creative_reread_20260916_attempt1/run1'
STAGE = BASE/'orch_r170_creative_replay_20260917_attempt1'
NATIVE_PID = 1266769
NATIVE_TICKS = '28048014'
UUID = 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821'
FAMILY_SHA = '014e23e330db36f0ef6a8da23f75084a7685e7e0663a1e9540759dac7fc0da5c'
API_SHA = 'f128becb34d95b6875e4283baa49b3504e2c6c589e67b93e858e07c98f593e60'
NATIVE_SHA = 'cdb54252763472fd21ea12fd7694b208d968422c375dbf0647088cde736e6d48'
GUARD_SHA = '4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3'
REPLAY_PINS = {
    'gpu/orch_r168_targeted_replay.py': '4ff5a30e5602149bdde4d320c768fe23ef309070f88cff455e605080bf7c49b3',
    'gpu/orch_r168_targeted_replay_native.py': '12e512ba08be73a1881bc75c52f60458163aa929c5b0bc682814c9c0bf93e304',
    'gpu/orch_r168_targeted_replay_driver.py': '43295e6b98ebb10c7e99247e8b26720948b25556d5da13e34759c1f2d0088351',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and not path.is_symlink(), 'canonical_regular_metadata')
    require(path.is_file() and path.stat().st_size <= 16*1024*1024, 'bounded_metadata')
    return json.loads(path.read_bytes())


def bound(reference):
    require(set(reference) == {'path', 'sha256'}, 'exact_reference')
    require(sha(reference['path']) == reference['sha256'], 'bound_metadata_hash')
    return read(reference['path'])


def scope(plan):
    require(type(plan['physical']) is int and plan['physical'] == 1 and plan['gpu_uuid'] == UUID,
            'only_existing_creative_physical1')
    require(plan['root'] == str(LIFE) and plan['source_root'] == str(OLD_SOURCE), 'current_existing_life_source')
    require(not plan.get('preupdate_recovery') and not plan.get('authorized_wall_extension'),
            'no_recovery_or_wall_extension')
    return 1


def patched_guard(original, binding_ref):
    require(hashlib.sha256(original).hexdigest() == GUARD_SHA, 'exact_old_guard')
    require(set(binding_ref) == {'path', 'sha256'}, 'bound_driver_reference')
    call = b"    child.run(config['plan_path'], resume=config['resume'])\n"
    require(original.count(call) == 1, 'one_guard_entry_only')
    replacement = ("    __import__('gpu.orch_r168_targeted_replay_driver', fromlist=['run']).run("
        "child, config['plan_path'], resume=config['resume'], binding_ref="+repr(binding_ref)+')\n').encode()
    return original.replace(call, replacement, 1)


def verify_source(family, binding_path, old_config, old_plan, new_config, new_plan):
    helper = family['api']()
    scope(old_plan)
    require(Path(new_plan['source_root']) == STAGE/'physical1/source', 'one_staged_source')
    family['plan_delta'](old_plan, new_plan)
    family['guard_delta'](old_config, new_config)
    original, destination = Path(old_plan['source_root']), Path(new_plan['source_root'])
    stage = read(STAGE/'physical1/STAGED_SOURCE.json')
    require(sha(binding_path) == stage['guard_sha256'], 'source_binding_guard_hash')
    binding_ref = stage['driver_binding']
    driver_binding = bound(binding_ref)
    require(driver_binding['life_root'] == str(LIFE) and driver_binding['resume'] is True,
            'driver_existing_life_resume')
    require(driver_binding['plan_ref'] == dict(path=new_config['plan_path'], sha256=new_config['plan_sha256']),
            'driver_exact_new_plan')
    require(sha(original/'gpu/orch_r125_continual_native.py') == NATIVE_SHA, 'supported_actual_native')
    expected = dict(old_config['source_pins'])
    require(not set(REPLAY_PINS).intersection(expected), 'never_reinstall_arm')
    expected.update(REPLAY_PINS)
    guard_name = 'gpu/orch_r125_continual_guard.py'
    require((destination/guard_name).read_bytes() == patched_guard((original/guard_name).read_bytes(), binding_ref),
            'only_authorized_guard_entry_delta')
    expected[guard_name] = sha(destination/guard_name)
    require(new_config['source_pins'] == expected, 'exact_source_closure_delta')
    for name, checksum in expected.items():
        require(sha(destination/name) == checksum, 'staged_file_pin:'+name)
    require(read(new_config['allocation_path']) == dict(read(old_config['allocation_path']),
            plan_sha256=new_config['plan_sha256']), 'allocation_binding_only')
    for reference in (driver_binding['runtime_ref'], driver_binding['selection_ref'], driver_binding['main_go_ref']):
        bound(reference)
    selection = bound(driver_binding['selection_ref'])
    selected = selection['selected']
    require(len(selected) == 1 and selected[0]['segment'] == 118
        and selected[0]['source_sha256'] == '1d721f3be5a40bac051f0c132451d7bb1e6bec428eec63327b26f64432ae17d7'
        and selected[0]['row_sha256'] == '564f8a4f585ecc2eb4bfb16fb0efb390cf8014050fd761dadc93b4773ecd7e6d'
        and selected[0]['selection_kind'] == 'OBJECT_REPLAY' and selected[0]['extra_presentations'] == 4,
        'one_exact_own_row_four_extras')
    require(selection['target_cycle'] == selection['source_cycle']+1, 'one_immediate_next_sleep')


def family_namespace():
    source = HERE/'FAMILY.py'
    require(sha(source) == FAMILY_SHA and sha(HERE/'BOUNDARY_API.py') == API_SHA, 'pinned_saved_boundary_lifecycle')
    namespace = dict(__name__='r170_saved_boundary_family', __file__=str(Path(__file__).resolve()))
    exec(compile(source.read_bytes(), str(Path(__file__).resolve()), 'exec'), namespace)
    namespace['STAGED_SOURCE_ROOT'] = STAGE
    namespace['lane_scope'] = scope
    namespace['verify_source'] = lambda *args: verify_source(namespace, *args)
    original_modules = namespace['old_modules']
    original_saved = namespace['saved_evidence']
    original_validation = namespace['validate_new']

    def old_modules(config_path):
        require(Path(config_path) == OLD_GUARD, 'only_original_guard_path')
        config, plan, modules = original_modules(config_path)
        require(sha(config_path) == '8bbb6c007083884574b427b318ef3e466f26e514452b5ee5e7972801aca8ce9d',
                'exact_original_guard_config')
        require(sha(modules.native.__file__) == NATIVE_SHA, 'exact_original_native')
        return config, plan, modules

    def saved_evidence(plan, saved, original):
        stage = read(STAGE/'physical1/STAGED_SOURCE.json')
        binding = bound(stage['driver_binding'])
        selection = bound(binding['selection_ref'])
        require(saved is not None and saved['cycle'] == selection['source_cycle']
            and saved['state_sha256'] == selection['boundary_state_sha256']
            and saved['path'] == selection['boundary_ref']['path'], 'selected_exact_boundary_no_missed_cycle')
        return original_saved(plan, saved, original)

    def validate_new(config_path):
        result = original_validation(config_path)
        stage = read(STAGE/'physical1/STAGED_SOURCE.json')
        binding = bound(stage['driver_binding'])
        script = ('import json; from gpu import orch_r125_continual_native as native; '
            'from gpu import orch_r168_targeted_replay_driver as driver; '
            'driver._admit(native, '+repr(binding['plan_ref']['path'])+', True, '+repr(stage['driver_binding'])+'); '
            'print(json.dumps({"driver_admitted_CPU_only": True}))')
        output = subprocess.check_output([str(namespace['PYTHON']), '-B', '-c', script], text=True,
            timeout=90, cwd=result['source_root'], env=namespace['environment'](result['source_root']))
        require(json.loads(output) == dict(driver_admitted_CPU_only=True), 'actual_receiving_driver_preflight')
        result['driver_admitted_CPU_only'] = True
        return result

    namespace.update(old_modules=old_modules, saved_evidence=saved_evidence, validate_new=validate_new)
    return namespace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', choices=('stage', 'validate', 'handoff', 'supervise'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--seconds', type=int, default=600)
    args = parser.parse_args()
    namespace = family_namespace()
    if args.action == 'stage':
        require(namespace['api']().process_record(NATIVE_PID)['start_ticks'] == NATIVE_TICKS,
                'original_live_instance')
        result = namespace['stage'](1, args.output, args.cpu)
    elif args.action == 'validate':
        result = namespace['validate_new'](args.output)
    elif args.action == 'handoff':
        require(1 <= args.seconds <= 600, 'six_hundred_second_active_bound')
        result = namespace['handoff'](args.output, args.seconds)
    else:
        try:
            result = namespace['supervise'](args.output)
        except BaseException as error:
            namespace['api']().write(args.output/'SUPERVISOR_FAILED.json', dict(error_type=type(error).__name__,
                error=str(error), failed_unix=time.time(), no_retry=True))
            raise
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
