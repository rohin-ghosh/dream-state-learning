"""Stage combined target-policy sources only after both recovery continuations."""

import ast
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import time


BASE = Path('/localhome/local-rohing')
CONTROLS = {
    5: BASE / 'orch_r133_node3_creative_none_20260916_attempt1/control_r145_20260916t1611z_5c',
    6: BASE / 'orch_r133_node3_support_none_20260916_attempt1/control_r145_20260916t1611z_6b_readmit1_readmit2_readmit3',
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(directory):
    operator = load(directory / 'OPERATOR.py', 'r145_target_operator')
    helper = operator.api()
    patcher = load(directory / 'TARGET_PATCH.py', 'r145_main_target_patch')
    helper_path = directory / 'TARGET_HELPER.py'
    operator.require(helper.sha(directory / 'TARGET_PATCH.py') == operator.PATCH_SHA
                     and helper.sha(helper_path) == operator.HELPER_SHA, 'exact_Main_policy_and_patch')
    root = operator.STAGED_SOURCE_ROOT
    operator.require(not root.exists(), 'never_overwrite_combined_stage')
    proofs = []
    for physical, control in CONTROLS.items():
        path = control / 'RECOVERY_CONTINUATION_VERIFIED.json'
        proof = helper.read(path)
        operator.require(proof['physical'] == physical
            and proof['status'] == 'DURABLE_REPLACEMENT_LOADED_TRAIN_CONTINUATION_VERIFIED'
            and proof['optimizer_steps'] == {5: 816, 6: 630}[physical]
            and proof['r144_target_policy_applied'] is False, 'both_recoveries_completed_first')
        proofs.append(dict(path=str(path), sha256=helper.sha(path)))
    root.mkdir()
    lanes = []
    for physical, control in CONTROLS.items():
        config_path = control / 'GUARD_CONTAINED.json'
        config = helper.read(config_path)
        plan = helper.read(config['plan_path'])
        operator.lane_scope(plan)
        proof = helper.read(control / 'RECOVERY_CONTINUATION_VERIFIED.json')
        processes = operator.old_processes(proof['native_pid'], config_path, config, plan)
        source = Path(plan['source_root'])
        pins = {str(path.relative_to(source)): helper.sha(path) for path in source.rglob('*.py')}
        operator.require(pins == config['source_pins'], 'unchanged_live_capacity_source_closure')
        output = root / ('physical' + str(physical))
        output.mkdir()
        destination = output / 'source'
        shutil.copytree(source, destination)
        native = destination / 'gpu/orch_r125_continual_native.py'
        before = native.read_text()
        patched = patcher.patch_source(before)
        operator.require(patched.count('r145_capacity.prepare_sleep(') == 1
            and patched.count("if label.startswith('ANCHOR:'):") == before.count("if label.startswith('ANCHOR:'):") > 0
            and patched.count("logits_to_keep=window['logits_to_keep']") == 1,
            'capacity_guard_and_child_only_forward_retained')
        mode = stat.S_IMODE(native.stat().st_mode)
        directory_mode = stat.S_IMODE(native.parent.stat().st_mode)
        try:
            native.chmod(mode | stat.S_IWUSR)
            native.parent.chmod(directory_mode | stat.S_IWUSR)
            native.write_text(patched)
            target = native.with_name('orch_r144_sleep_targets.py')
            with target.open('xb') as handle:
                handle.write(helper_path.read_bytes())
            target.chmod(mode)
        finally:
            native.chmod(mode)
            native.parent.chmod(directory_mode)
        proposed_plan = deepcopy(plan)
        proposed_plan['source_root'] = str(destination)
        if 'startup_context' in plan:
            relative = Path(plan['startup_context']['path']).relative_to(source)
            proposed_plan['startup_context']['path'] = str(destination / relative)
        operator.plan_delta(plan, proposed_plan)
        expected = dict(pins)
        expected['gpu/orch_r125_continual_native.py'] = helper.sha(native)
        expected['gpu/orch_r144_sleep_targets.py'] = operator.HELPER_SHA
        actual = {str(path.relative_to(destination)): helper.sha(path) for path in destination.rglob('*.py')}
        operator.require(actual == expected, 'only_sleep_native_and_target_helper_change')
        helper.write(output / 'PROPOSED_PLAN.json', proposed_plan)
        proposed = deepcopy(config)
        proposed.update(plan_path=str(output / 'PROPOSED_PLAN.json'), plan_sha256=helper.sha(output / 'PROPOSED_PLAN.json'),
                        source_pins=expected, resume=True, attempt_dir=str(output / 'NOT_DISPATCHED'))
        for key in ('r145_manifest', 'r145_acknowledgment'):
            proposed.pop(key)
        helper.write(output / 'PROPOSED_GUARD.json', proposed)
        helper.write(output / 'STAGED_SOURCE.json', dict(physical=physical, old_source=str(source), new_source=str(destination),
            guard_sha256=helper.sha(output / 'PROPOSED_GUARD.json'), old_native_sha256=pins['gpu/orch_r125_continual_native.py'],
            new_native_sha256=helper.sha(native), helper_sha256=operator.HELPER_SHA, policy=operator.POLICY,
            non_sleep_ast_preserved=patcher.without_sleep(ast.parse(before)) == patcher.without_sleep(ast.parse(patched)),
            recovery_entrypoint_replay_forbidden=True, admission=False, signals_sent=0, launch_count=0))
        lanes.append(dict(physical=physical, live=True, processes=processes, guard_path=str(config_path),
                          guard_sha256=helper.sha(config_path), source_root=str(source)))
    helper.write(root / 'INVENTORY.json', dict(lanes=lanes, both_recoveries_verified=True,
        recovery_continuations=proofs, created_unix=time.time(), prospective_only=True))
    print(json.dumps(dict(status='COMBINED_SOURCES_STAGED_NO_RETIREMENT', root=str(root)), sort_keys=True))


if __name__ == '__main__':
    prepare(Path(__file__).resolve().parent)
