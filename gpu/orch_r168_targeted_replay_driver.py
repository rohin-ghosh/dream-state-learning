"""Bound receiving entry for one creative_reread targeted replay sleep."""

from copy import deepcopy
import hashlib
import importlib
import sys
import time
import types

from gpu import orch_r168_targeted_replay_native as integration


replay = integration.replay
LIFE_ROOT = '/localhome/local-rohing/orch_r133_creative_reread_20260916_attempt1/run1'
INTEGRATION_SHA256 = '12e512ba08be73a1881bc75c52f60458163aa929c5b0bc682814c9c0bf93e304'
GUARD_SHA256 = '4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3'
BINDING_SCHEMA = 'R168_NATIVE_DRIVER_BINDING_V1'
GUARD_CALL = "    child.run(config['plan_path'], resume=config['resume'])"


def patch_guard(source, binding_ref):
    replay.require(type(source) is bytes and hashlib.sha256(source).hexdigest() == GUARD_SHA256,
                   'exact_original_guard_source')
    replay.reference_fields(binding_ref)
    original = (GUARD_CALL + '\n').encode()
    replay.require(source.count(original) == 1, 'unique_original_guard_run_call')
    replacement = ("    __import__('gpu.orch_r168_targeted_replay_driver', fromlist=['run']).run("
        "child, config['plan_path'], resume=config['resume'], binding_ref="
        + repr(deepcopy(binding_ref)) + ')\n').encode()
    staged = source.replace(original, replacement, 1)
    compile(staged, '<staged_r168_guard>', 'exec')
    return staged


def _admit(native_module, plan_path, resume, binding_ref):
    binding = replay.read_bound(binding_ref)
    replay.require(type(binding) is dict and set(binding) == {
        'schema', 'life_root', 'life_role', 'resume', 'plan_ref', 'runtime_ref',
        'selection_ref', 'main_go_ref', 'approved_intake_sha256', 'native_sha256',
        'integration_sha256', 'arm_sha256', 'driver_sha256'}, 'exact_driver_binding')
    replay.require(binding['schema'] == BINDING_SCHEMA and binding['life_root'] == LIFE_ROOT
        and binding['life_role'] == replay.ROLE and resume is True and binding['resume'] is True,
        'only_bound_parented_creative_reread_resume')
    replay.require(binding['native_sha256'] == integration.NATIVE_SHA256
        and binding['integration_sha256'] == INTEGRATION_SHA256
        and binding['arm_sha256'] == integration.ARM_SHA256, 'fixed_driver_source_contract')
    integration._source_bytes(sys.modules[__name__], binding['driver_sha256'])
    integration._source_bytes(integration, INTEGRATION_SHA256)
    integration._source_bytes(replay, integration.ARM_SHA256)
    raw = integration._source_bytes(native_module, integration.NATIVE_SHA256)
    original = native_module.run
    expected = integration._code(compile(raw, native_module.__file__, 'exec'), 'run')
    replay.require(original.__code__ == expected and original.__globals__ is native_module.__dict__
        and original.__closure__ is None and original.__defaults__ is None
        and original.__kwdefaults__ == {'resume': False}, 'exact_native_run_method')
    plan_ref = binding['plan_ref']
    replay.require(replay.canonical(plan_path) == replay.reference_fields(plan_ref), 'exact_run_plan_path')
    plan = replay.read_bound(plan_ref)
    replay.require(plan['root'] == LIFE_ROOT and plan['presleep_variant'] == 'reread_select'
        and plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 1
        and plan['anchor_lambda'] == 0.25 and plan.get('preupdate_recovery') is None,
        'exact_replay_plan_no_pending_recovery')
    source_root = replay.canonical(plan['source_root'])
    for reference in (binding_ref, plan_ref, binding['runtime_ref'], binding['selection_ref'],
                      binding['main_go_ref']):
        replay.require(not replay.reference_fields(reference).is_relative_to(source_root),
                       'external_binding_metadata_outside_source')
    selection = replay.read_bound(binding['selection_ref'])
    replay.require(selection['life_root'] == LIFE_ROOT and selection['life_role'] == replay.ROLE
        and selection['plan_sha256'] == plan_ref['sha256']
        and selection['runtime_sha256'] == binding['runtime_ref']['sha256'],
        'exact_own_selection_before_boundary_reads')
    selected = selection['selected']
    replay.require(len(selected) == 1 and selected[0]['source_sha256'] == integration.SOURCE_SHA256
        and selected[0]['row_sha256'] == integration.ROW_SHA256
        and selected[0]['selection_kind'] == 'OBJECT_REPLAY'
        and selected[0]['extra_presentations'] == 4, 'one_original_object_four_extras')
    runtime = replay.read_bound(binding['runtime_ref'])
    replay.require(set(runtime) == {'schema', 'native_sha256', 'arm_sha256',
        'integration_sha256', 'dependencies'} and runtime['schema'] == 'R168_NATIVE_SLEEP_RUNTIME_V1'
        and runtime['native_sha256'] == integration.NATIVE_SHA256
        and runtime['integration_sha256'] == INTEGRATION_SHA256
        and runtime['arm_sha256'] == integration.ARM_SHA256
        and set(runtime['dependencies']) == set(integration.DEPENDENCIES), 'exact_driver_runtime')
    for name in integration.DEPENDENCIES:
        integration._source_bytes(importlib.import_module(name), runtime['dependencies'][name])
    replay.validate_go(replay.read_bound(binding['main_go_ref']), binding['selection_ref'], selection,
                       binding['approved_intake_sha256'], time.time())
    arm = replay.SingleSleepArm(binding['selection_ref'], binding['main_go_ref'],
                               approved_intake_sha256=binding['approved_intake_sha256'])
    return binding, arm


def run(native_module, plan_path, *, resume=False, binding_ref=None):
    if binding_ref is None:
        return native_module.run(plan_path, resume=resume)
    binding, arm = _admit(native_module, plan_path, resume, deepcopy(binding_ref))
    bridge = None

    def finish_sleep(child, stream, journal, anchors, root, cycle):
        nonlocal bridge
        if bridge is None:
            bridge = integration.NativeReplaySleep(native_module, child, arm=arm,
                plan_ref=binding['plan_ref'], runtime_ref=binding['runtime_ref'])
        replay.require(bridge.child is child, 'one_actual_child_per_native_run')
        return bridge.finish_sleep(stream, journal, anchors, root, cycle)

    original = native_module.run
    private_globals = dict(original.__globals__, finish_sleep=finish_sleep)
    isolated = types.FunctionType(original.__code__, private_globals, original.__name__,
                                  original.__defaults__, original.__closure__)
    isolated.__kwdefaults__ = deepcopy(original.__kwdefaults__)
    return isolated(plan_path, resume=resume)
