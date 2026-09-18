"""Exact renewed5/6 entrypoint relocation through the original admission chain."""

import argparse
import ast
from copy import deepcopy
import hashlib
import inspect
import json
import os
from pathlib import Path
import time

from gpu import orch_r145_node3_capacity_recovery as capacity
from gpu import orch_r145_node3_pending_recovery as pending


SCHEMA = 'R145_NODE3_ADMITTED_RECOVERY_V1'
MODULE = 'gpu.orch_r145_node3_admitted_recovery'
RUNTIME_SHA = 'c66a91b631937236d614095c07785f90242e4d476c45b7fa8fe5d65a8f277d2d'
STACK_SHA = '4b61ce130a590d8501cb0c66006bae28dfea0ded3675a77985bbb6349d2fc120'
require = capacity.require


def raw_reference(reference):
    require(set(reference) == {'path', 'sha256'}, 'exact_file_reference')
    path = Path(reference['path'])
    require(path.is_absolute() and '..' not in path.parts
            and not any(part.is_symlink() for part in (path, *path.parents)), 'canonical_reference')
    require(capacity.file_sha(path) == reference['sha256'], 'exact_reference_bytes:' + str(path))
    return path.read_bytes()


def lane_from_manifest(manifest):
    return pending.load_lane(manifest['physical'], manifest['summary']['path'], manifest['inventory']['path'])


def verify_manifest(config, plan, *, acknowledge=True):
    capacity.owned_plan(plan)
    manifest = json.loads(raw_reference(config['r145_manifest']))
    require(manifest['schema'] == SCHEMA and manifest['physical'] == plan['physical']
            and manifest['plan_sha256'] == config['plan_sha256']
            and manifest['source_pins'] == config['source_pins'], 'manifest_plan_source_binding')
    source = Path(plan['source_root'])
    for name, expected in manifest['owned_pins'].items():
        require(Path(name).name == name and capacity.file_sha(source / 'gpu' / name) == expected,
                'owned_integration_source_pin')
    require(manifest['runtime']['sha256'] == RUNTIME_SHA
            and manifest['runtime']['path'] == str(source / 'gpu' / capacity.RUNTIME_FILENAME), 'exact_Main_runtime_pin')
    raw_reference(manifest['runtime'])
    require(manifest['stack_cpu']['sha256'] == STACK_SHA, 'actual_CPU_stack_pin')
    raw_reference(manifest['stack_cpu'])
    gate = json.loads(raw_reference(manifest['cpu_gate']))
    require(gate['status'] == 'PASS' and gate['source_pins'] == config['source_pins']
            and gate['owned_pins'] == manifest['owned_pins'], 'same_source_CPU_gate')
    raw_reference(manifest['summary'])
    raw_reference(manifest['inventory'])
    lane = lane_from_manifest(manifest)
    store = pending.LocalCaptureStore(pending.ORIGIN)
    pending.verify_source_and_plan(lane, store, plan)
    pending.verify_saved_files(lane, store)
    require(manifest['capture_binding'] == lane.binding
            and Path(manifest['recovery_output']).parent == lane.root / 'recoveries'
            and Path(manifest['recovery_output']).name.startswith('r145-'), 'same_life_recovery_output')
    for reference in manifest['failure_evidence']:
        raw_reference(reference)
    if acknowledge:
        acknowledgment = json.loads(raw_reference(config['r145_acknowledgment']))
        require(acknowledgment.get('author') == 'Main' and acknowledgment.get('approved') is True
                and acknowledgment.get('manifest_sha256') == config['r145_manifest']['sha256'],
                'Main_acknowledges_exact_manifest_file_bytes')
    return manifest


def allocator_command(command, plan, policy):
    capacity.owned_plan(plan)
    command = list(command)
    require(policy['minor'] == plan['physical'] and command.count('/usr/bin/env') == 1,
            'exact_owned_minor_and_clean_environment')
    position = command.index('/usr/bin/env')
    require(command[position + 1] == '-i' and '--property=DevicePolicy=strict' in command[:position],
            'original_strict_containment')
    devices = [item for item in command[:position] if item.startswith('--property=DeviceAllow=/dev/nvidia')]
    require(sorted(devices) == sorted(['--property=DeviceAllow=/dev/nvidia' + str(plan['physical']) + ' rw',
            '--property=DeviceAllow=/dev/nvidiactl rw', '--property=DeviceAllow=/dev/nvidia-uvm rw']),
            'only_target_plus_control_devices')
    require('CUDA_VISIBLE_DEVICES=' + plan['gpu_uuid'] in command[position + 2:]
            and not any(item.startswith(('PYTORCH_CUDA_ALLOC_CONF=', 'PYTORCH_ALLOC_CONF=')) for item in command),
            'original_UUID_no_conflicting_allocator')
    command.insert(position + 2, 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')
    return command


def relocated_source(source, action):
    require(action in ('supervise', 'contained_native'), 'original_launch_functions_only')
    before = 'gpu.orch_r133_node3_programmes' if action == 'supervise' else 'gpu.orch_r125_continual_guard'
    require(source.count(repr(before)) == 1, 'one_exact_entrypoint_literal')
    modified = source.replace(repr(before), repr(MODULE))
    tree = ast.parse(modified)
    replacements = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == MODULE:
            node.value = before
            replacements += 1
    require(replacements == 1 and ast.dump(tree) == ast.dump(ast.parse(source)), 'only_entrypoint_relocated')
    return modified


def adapted_node_function(action):
    from gpu import orch_r133_node3_programmes as programmes
    require(capacity.file_sha(programmes.__file__) == capacity.LAUNCHER_SHA, 'original_launcher_bytes')
    function = getattr(programmes, action)
    modified = relocated_source(inspect.getsource(function), action)
    namespace = dict(function.__globals__)
    if action == 'supervise':
        def contained_command(plan, policy, command, lifetime):
            capacity.owned_plan(plan)
            require(programmes.device_minor(plan['gpu_uuid']) == policy['minor'] == plan['physical'],
                    'actual_UUID_kernel_minor')
            return allocator_command(programmes.containment_command(plan, policy, command, lifetime), plan, policy)
        namespace['containment_command'] = contained_command
    exec(compile(modified, __file__ + ':' + action, 'exec'), namespace)
    return namespace[action]


def admitted_probe(child, stream, anchors, output):
    from gpu import orch_r125_continual_native as native
    rows = stream.pending_rows() + stream.rows[:stream.sleep_frontier]
    encoded = {row['source_sha256']: native.encode_own(row, child.tokenizer, child.plan['context_limit']) for row in rows}
    return capacity.bounded_train_probe(child, encoded, anchors, RUNTIME_SHA, output)


def recover_admitted_sleep(plan_path, manifest):
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r107_base_anchors_inventory import build_inventory
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream, verify_experiment_resume
    plan = native.validate_plan(native.read(plan_path))
    capacity.owned_plan(plan)
    require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == capacity.file_sha(plan_path), 'original_admitted_plan')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid']
            and os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == 'expandable_segments:True'
            and 'PYTORCH_ALLOC_CONF' not in os.environ, 'premodel_allocator_and_UUID')
    lane = lane_from_manifest(manifest)
    store = pending.LocalCaptureStore(pending.ORIGIN)
    pending.verify_source_and_plan(lane, store, plan)
    checkpoint = pending.verify_saved_files(lane, store)
    require(capacity.installed_runtime_pins() == json.loads(raw_reference(manifest['runtime'])),
            'fresh_admitted_installed_runtime_pin')
    with StreamJournal(lane.root / 'stream', create=False) as journal:
        state = journal.latest_checkpoint()
        stream = ContinualStream.restore(state['document'], expected_sha256=state['expected_sha256'])
        verify_experiment_resume(plan, stream.experiment)
        require(checkpoint.get('experiment') == stream.experiment, 'saved_stream_experiment')
        child = native.NativeChild(plan, checkpoint)
        child.r145_admitted_plan_sha256 = capacity.file_sha(plan_path)
        anchors, anchor_receipt = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
        output = Path(manifest['recovery_output'])
        recovery = pending.PendingRecovery(lane, store, child, stream, journal, output)
        recovery.prepare_and_probe(anchors, lambda loaded, restored, inventory:
            admitted_probe(loaded, restored, inventory, output))
        capacity.save_once(output / 'ANCHOR_INVENTORY.json', anchor_receipt)
        recovery.replay()
        return recovery.recompute(anchors)


def entrypoint():
    from gpu import orch_r125_continual_guard as guard
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('supervise', 'contained-native', 'native'))
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--release', type=Path)
    arguments = parser.parse_args()
    config, plan = guard.validate(arguments.config)
    manifest = verify_manifest(config, plan)
    require(config['resume'] is True, 'never_fresh_initialization')
    if arguments.action == 'supervise':
        require(arguments.release is not None, 'original_release_required')
        adapted_node_function('supervise')(arguments.config, arguments.release)
    elif arguments.action == 'contained-native':
        adapted_node_function('contained_native')(arguments.config)
    else:
        original_run = guard.child.run

        def recovered_run(plan_path, *, resume=False):
            require(resume is True, 'same_life_resume_only')
            recover_admitted_sleep(plan_path, manifest)
            import gc
            import torch
            gc.collect()
            torch.cuda.empty_cache()
            guard.child.run = original_run
            original_run(plan_path, resume=True)

        guard.child.run = recovered_run
        guard.native_entry(arguments.config)


if __name__ == '__main__':
    entrypoint()
