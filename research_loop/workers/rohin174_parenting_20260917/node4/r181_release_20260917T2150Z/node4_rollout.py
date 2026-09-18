"""R179 four-life NODE4 actual-source staging and exact saved-boundary handoff."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import select
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid


POLICY_SHA = 'b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b'
HELPERS_SHA = '6e4d91c9581d952924ae269d7f4831fc9840c741805ebcddf2f2c78e8d356270'
BASE = Path('/localhome/local-rohing')
PREFIX = BASE / 'orch_r144_target_rollout_a40r_suffix_20260916t1643z'
NATIVE = 'gpu/orch_r125_continual_native.py'
POLICY = 'gpu/orch_r179_context_survival.py'
LEGACY = 'gpu/orch_r179_node4_legacy_containment.py'
LEGACY_SHA = 'b5385da9892dff75884b67f6fbf286a1c67fd1d658cd67cb3ab02c37943ca5c7'
LEGACY_TEST_SHA = '3bbb473f82bde48bbeddbad7d54c44d18a8235067020d06902b49f5d96372f7a'
PREFLIGHT = 'gpu/orch_r179_busy_preflight.py'
PREFLIGHT_SHA = '0fdbd4da086efac21d297874d7a61ee6d73e6515fafa0d02a56bd35fcd441bcf'
PREFLIGHT_TEST_SHA = '8ab4dbec3db1dfbba19f3ce4a7d780853d96c8e559bf375bdf450c6c6e286078'
DRIFT_PREFIXES = ('process_identity_drift', 'minor_scan_identity_changed', 'minor_scan_process_drift')
MAX_BOUNDARY_WAIT_SECONDS = 5400
ALLOWLIST = {
    0: ('kernel0', 'orch_r132_kernel_child_20260916_attempt1', 2709461, '14646722',
        'ebc23f30800d0ea508477c853fe656875e1a0233ec691e7a4c88e33e3775cfe7', 'readmission2/control'),
    1: ('raw_unparented', 'orch_r136_raw_unparented_a40r1_20260916_attempt1', 2753950, '14677789',
        'd3cbd3b0053f0c7c5d3d8e36e37c52954bdb39a40fc4346e4e6d3ab4bf5a2ad1', 'control'),
    3: ('raw_parented', 'orch_r136_raw_parented_seed1_a40r3_20260916_attempt1', 2941297, '14809147',
        'bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6', 'control'),
    4: ('kernel_parented', 'orch_r136_kernel_parented_a40r4_20260916_attempt1', 3496993, '15201156',
        'd3cbd3b0053f0c7c5d3d8e36e37c52954bdb39a40fc4346e4e6d3ab4bf5a2ad1', 'readmission1/control'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def helper_module(bundle):
    path = bundle / 'r144_helpers.py'
    require(hashlib.sha256(path.read_bytes()).hexdigest() == HELPERS_SHA, 'pinned_readonly_R144_primitives')
    spec = importlib.util.spec_from_file_location('r179_node4_r144_primitives', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def handler(physical, config):
    require(physical in ALLOWLIST and 'device_containment' in config, 'preserve_current_strict_confinement')
    module = ('gpu.orch_r179_node4_legacy_containment' if physical in (0, 1) else
        'gpu.orch_r144_a40r4_strict' if physical == 4 else 'gpu.orch_r137_node4_containment')
    return dict(module=module, supervisor='contained-supervise', inner='contained-native')


def legacy_authority(bundle, helpers):
    scope = helpers.read(bundle / 'NODE4_LEGACY_ADDENDUM.json')
    require(scope['schema'] == 'R179_NODE4_LEGACY_CONTAINMENT_ADDENDUM_V1'
            and scope['added_module'] == dict(path=LEGACY, sha256=LEGACY_SHA)
            and scope['tests']['sha256'] == LEGACY_TEST_SHA
            and scope['cpu']['passed'] == 35 and scope['cpu']['subtests_passed'] == 63, 'exact_Main_legacy_addendum')
    require(helpers.sha(bundle / 'legacy_containment.py') == LEGACY_SHA
            and helpers.sha(bundle / 'legacy_tests.py') == LEGACY_TEST_SHA
            and helpers.sha(bundle / 'CPU_LEGACY_CONTAINMENT_1.log') == scope['cpu']['sha256'], 'bound_legacy_module_tests_CPU')
    return helpers.sha(bundle / 'NODE4_LEGACY_ADDENDUM.json')


def legacy_runtime_environment(actor):
    parts = (Path('/proc') / str(actor['pid']) / 'environ').read_bytes().split(b'\0')
    environment = dict(part.decode().split('=', 1) for part in parts if b'=' in part)
    require(not any(name in environment for name in ('PYTORCH_CUDA_ALLOC_CONF', 'PYTORCH_ALLOC_CONF', 'CUDA_DEVICE_ORDER')),
            'no_original_allocator_or_device_order_override')
    require(environment.get('OMP_NUM_THREADS') == environment.get('MKL_NUM_THREADS') == '1'
            and environment.get('TOKENIZERS_PARALLELISM') == 'false', 'original_thread_tokenizer_environment_preserved')
    return dict(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', allocator_override=False)


def preflight_authority(bundle, helpers):
    scope = helpers.read(bundle / 'NODE4_PREFLIGHT_ADDENDUM.json')
    require(scope['schema'] == 'R179_NODE4_PREFLIGHT_EVIDENCE_ADDENDUM_V1'
            and scope['module'] == dict(path=PREFLIGHT, sha256=PREFLIGHT_SHA)
            and scope['tests']['sha256'] == PREFLIGHT_TEST_SHA
            and scope['cpu']['passed'] == 42 and scope['cpu']['subtests_passed'] == 50, 'exact_Main_preflight_addendum')
    require(helpers.sha(bundle / 'busy_preflight.py') == PREFLIGHT_SHA
            and helpers.sha(bundle / 'preflight_tests.py') == PREFLIGHT_TEST_SHA
            and helpers.sha(bundle / 'CPU_PREFLIGHT_1.log') == scope['cpu']['sha256'], 'bound_preflight_module_tests_CPU')
    return helpers.sha(bundle / 'NODE4_PREFLIGHT_ADDENDUM.json')


def selected(physical, helpers):
    require(physical in ALLOWLIST, 'only_four_current_learning_lives')
    helpers.current_node('a40r')
    current = helpers.read(Path(__file__).parent / 'CURRENT.json')[str(physical)]
    config_path = Path(current['guard_path'])
    config, plan, original = helpers.originals(config_path)
    require(plan['root'] == current['root'] and plan['physical'] == physical
        and plan['gpu_uuid'] == helpers.LANES['a40r'][physical][1], 'exact_current_life_UUID')
    require(helpers.sha(config_path) == current['guard_sha256']
        and helpers.sha(Path(plan['source_root']) / NATIVE) == current['source_sha256'], 'exact_current_guard_and_native')
    require(plan['hard_end_unix'] == config['hard_end_unix'] == 1789754400, 'unchanged_original_wall')
    actor = helpers.identity(current['actor']['pid'])
    require(actor['start_ticks'] == current['actor']['start_ticks'], 'current_exact_PID_start_ticks')
    timer = helpers.identity(actor['parent'])
    pair = dict(actor=actor, timer=timer, supervisor=helpers.identity(timer['parent']))
    launch = helpers.read(Path(config['attempt_dir']) / 'LAUNCH.json')
    validate_pair(pair, config_path, config, plan, launch, helpers)
    return config_path, config, plan, original, pair


def validate_pair(pair, config_path, config, plan, launch, helpers):
    actor, timer, supervisor = (pair[name] for name in ('actor', 'timer', 'supervisor'))
    launch_handler = handler(plan['physical'], config)
    expected = [str(helpers.PYTHON), '-B', '-m', helpers.GUARD, 'native', '--config', str(config_path)]
    require(actor['argv'] == expected and timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3]) and timer['argv'][4:] == expected,
            'exact_guarded_actor_and_timeout')
    require(supervisor['argv'] == [str(helpers.PYTHON), '-B', '-m', launch_handler['module'],
            launch_handler['inner'], '--config', str(config_path)], 'exact_existing_supervisor')
    require(actor['parent'] == timer['pid'] and timer['parent'] == supervisor['pid']
            and actor['group'] == timer['group'] == timer['pid'], 'exact_owned_ancestry')
    require(launch['pid'] == timer['pid'] and str(launch['parent_start_ticks']) == timer['start_ticks']
            and launch['guard_sha256'] == helpers.sha(config_path) and launch['plan_sha256'] == config['plan_sha256']
            and launch['gpu_uuid'] == plan['gpu_uuid'], 'original_LAUNCH_binding')
    for name, process in pair.items():
        require(process['uid'] == os.getuid() and process['boot_id'] == actor['boot_id']
                and process['cgroup'] == actor['cgroup'], 'same_owned_cgroup_and_boot')
        require(process['cwd'] == plan['source_root'] or (name == 'supervisor'
                and launch_handler['module'] == helpers.GUARD and process['cwd'] == str(BASE)), 'same_original_cwd')
        visible = '' if name == 'supervisor' and launch_handler['module'] == helpers.GUARD else plan['gpu_uuid']
        require(process['environment'] == ['CUDA_VISIBLE_DEVICES=' + visible], 'same_UUID_no_allocator_changes')
    if 'device_containment' in config:
        require(actor['cgroup'] == '0::/system.slice/' + config['device_containment']['unit'] + '.service',
                'existing_strict_cgroup_bound')


def cpu_command(source, command, log, timeout=120):
    with log.open('x') as output:
        result = subprocess.run(command, cwd=source, env=dict(os.environ, PYTHONPATH=str(source),
            CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'),
            stdout=output, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    require(result.returncode == 0, 'receiving_CPU_failed:' + str(log))


def stage(bundle, output, physical):
    helpers = helper_module(bundle)
    require(helpers.sha(bundle / 'policy.py') == POLICY_SHA, 'exact_Main_policy')
    authority = helpers.read(bundle / 'BUILDER_SCOPE.json')
    require(authority['policy']['sha256'] == POLICY_SHA and authority['cpu']['passed'] == 108
            and authority['cpu']['subtests_passed'] == 145, 'existing_Main_READY_GO')
    config_path, config, plan, original, pair = selected(physical, helpers)
    preflight_addendum_sha = preflight_authority(bundle, helpers)
    legacy = physical in (0, 1)
    addendum_sha = legacy_authority(bundle, helpers) if legacy else None
    runtime_environment = legacy_runtime_environment(pair['actor']) if legacy else None
    require(output.parent == bundle and output.name == f'lane{physical}' and not output.exists(), 'fresh_bounded_stage')
    device = helpers.actual_device(plan)
    if 'device_containment' in config:
        require(device['minor'] == config['device_containment']['minor'], 'unchanged_actual_device_minor')
    before = helpers.inventory_files(plan['source_root'])
    entry = helpers.verify_resume_entrypoint(plan['source_root'])
    output.mkdir()
    source, control = output / 'source', output / 'control'
    shutil.copytree(plan['source_root'], source)
    module = helpers.module_from_file('r181_exact_delta', bundle / 'r181_native_delta.py')
    patched = module.patch_native((source / NATIVE).read_text(), (bundle / 'MAIN_NATIVE.py').read_text())
    mode = stat.S_IMODE((source / NATIVE).stat().st_mode)
    (source / NATIVE).chmod(mode | stat.S_IWUSR)
    (source / NATIVE).write_text(patched)
    (source / NATIVE).chmod(mode)
    require(helpers.sha(source / POLICY) == POLICY_SHA and helpers.sha(source / PREFLIGHT) == PREFLIGHT_SHA, 'existing_R179_and_preflight_unchanged')
    if legacy:
        require(helpers.sha(source / LEGACY) == LEGACY_SHA, 'existing_legacy_confinement_unchanged')
    after = helpers.inventory_files(source)
    expected = dict(before, **{NATIVE: helpers.sha(source / NATIVE), POLICY: POLICY_SHA, PREFLIGHT: PREFLIGHT_SHA})
    if legacy:
        expected[LEGACY] = LEGACY_SHA
    require(after == expected
            and helpers.inventory_files(plan['source_root']) == before, 'only_authorized_successor_source_delta')
    helpers.write(output / 'SOURCE_PROOF.json', dict(old_source=plan['source_root'], old_inventory=before,
        new_source=str(source), new_inventory=after, policy_sha256=POLICY_SHA, unchanged_other_bytes=True,
        legacy_addendum_sha256=addendum_sha, legacy_module_sha256=LEGACY_SHA if legacy else None,
        preflight_addendum_sha256=preflight_addendum_sha, preflight_module_sha256=PREFLIGHT_SHA))
    control.mkdir()
    proposed = helpers.relocated_plan(plan, source)
    proposed['rehearsal_presentations'] = 0
    helpers.write(control / 'PLAN.json', proposed)
    cpu_command(source, [str(helpers.PYTHON), '-B', str(bundle / 'cpu_actual.py'), '--source', str(source),
        '--predecessor', plan['source_root'], '--plan', str(control / 'PLAN.json')], output / 'CPU_POLICY.log')
    cpu = helpers.read(output / 'CPU_POLICY.log')
    require(cpu['status'] == 'PASS' and cpu['cases'] == 8, 'actual_source_eight_integration_cases')
    cpu_command(source, [str(helpers.PYTHON), '-B', '-m', 'unittest',
        'tests.test_orch_r124_train_history', 'tests.test_orch_r125_continual_stream',
        'tests.test_orch_r125_stream_journal'], output / 'CPU_FROZEN.log')
    cpu_command(source, [str(helpers.PYTHON), '-B', str(bundle / 'preflight_tests.py'), '-v'], output / 'CPU_PREFLIGHT.log')
    cpu_command(source, [str(helpers.PYTHON), '-B', '-c',
        'from gpu import orch_r179_busy_preflight as module; from pathlib import Path; '
        'assert Path(module.__file__).resolve() == Path.cwd()/"gpu/orch_r179_busy_preflight.py"'],
        output / 'CPU_PREFLIGHT_IMPORT.log')
    if legacy:
        cpu_command(source, [str(helpers.PYTHON), '-B', str(bundle / 'legacy_tests.py'), '-v'], output / 'CPU_LEGACY.log')
        cpu_command(source, [str(helpers.PYTHON), '-B', '-c',
            'from gpu import orch_r179_node4_legacy_containment as module; from pathlib import Path; '
            'import tempfile; '
            'assert Path(module.__file__).resolve() == Path.cwd()/"gpu/orch_r179_node4_legacy_containment.py"; '
            'directory=tempfile.TemporaryDirectory(); module.write(Path(directory.name)/"proof.json", {"CPU":True}); '
            'directory.cleanup()'], output / 'CPU_LEGACY_WRITER.log')
    allocation = helpers.read(config['allocation_path'])
    require(allocation['plan_sha256'] == config['plan_sha256'], 'original_posted_allocation_binding')
    allocation.update(plan_sha256=helpers.sha(control / 'PLAN.json'), r179_policy_sha256=POLICY_SHA,
        r179_cpu_sha256=helpers.sha(output / 'CPU_POLICY.log'), r179_original_allocation_sha256=config['allocation_sha256'])
    helpers.write(control / 'ALLOCATION.json', allocation)
    updated = deepcopy(config)
    updated.update(attempt_dir=str(control), resume=True, plan_path=str(control / 'PLAN.json'),
        plan_sha256=helpers.sha(control / 'PLAN.json'), allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=helpers.sha(control / 'ALLOCATION.json'),
        source_pins={name: value for name, value in after.items() if name.endswith('.py')})
    if 'device_containment' in updated:
        updated['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    elif legacy:
        updated['device_containment'] = dict(minor=device['minor'], uid=os.getuid(), gid=os.getgid(),
            unit='orch-r136-native-' + uuid.uuid4().hex)
    helpers.write(control / 'GUARD.json', updated)
    cpu_command(source, [str(helpers.PYTHON), '-B', '-c',
        'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], output / 'CPU_GUARD.log')
    launch_handler = handler(physical, config)
    if legacy:
        launch_handler = dict(module='gpu.orch_r179_node4_legacy_containment',
            supervisor='contained-supervise', inner='contained-native')
    if 'device_containment' in updated:
        probe = deepcopy(updated)
        probe['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
        helpers.write(output / 'PROBE_GUARD.json', probe)
        code = ('import importlib,json,sys; from pathlib import Path; '
            'config=json.loads(Path(sys.argv[1]).read_text()); plan=json.loads(Path(config["plan_path"]).read_text()); '
            'module=importlib.import_module(sys.argv[2]); print(json.dumps(module.verify_device_containment(config,plan)))')
        containment = (helpers.module_from_file('r179_legacy_constructor', bundle / 'legacy_containment.py')
            if legacy else importlib.import_module(launch_handler['module']))
        policy = probe['device_containment']
        probe_command = ([str(helpers.PYTHON), '-B', '-m', launch_handler['module'], 'probe',
            '--config', str(output / 'PROBE_GUARD.json')] if legacy else
            [str(helpers.PYTHON), '-B', '-c', code, str(output / 'PROBE_GUARD.json'), launch_handler['module']])
        command = containment.device_containment_command(physical, policy['minor'], policy['uid'], policy['gid'],
            policy['unit'], str(source), probe_command, 45)
        cpu_command(source, command, output / 'DEVICE_PROBE.json', timeout=60)
        proof = helpers.read(output / 'DEVICE_PROBE.json')
        require(len(proof.get('denied_foreign_minors', proof.get('denied_devices', []))) == 7,
                'receiving_device_seven_foreign_denials')
    require({name: helpers.identity(value['pid']) for name, value in pair.items()} == pair, 'staging_preserved_live_owners')
    helpers.write(output / 'RESUME_ENTRYPOINT.json', entry)
    stage_record = dict(status='STAGED_CPU_AND_GUARD_VALIDATED', node='a40r', physical=physical,
        policy_sha256=POLICY_SHA, bundle=str(bundle), source_root=str(source), old_config=str(config_path),
        old_config_sha256=helpers.sha(config_path), old_plan=plan, processes=pair, device=device,
        new_config=str(control / 'GUARD.json'), new_config_sha256=helpers.sha(control / 'GUARD.json'),
        handler=launch_handler, source_proof_sha256=helpers.sha(output / 'SOURCE_PROOF.json'),
        operator_sha256=helpers.sha(Path(__file__)), cpu_script_sha256=helpers.sha(bundle / 'cpu_actual.py'),
        cpu_sha256=helpers.sha(output / 'CPU_POLICY.log'), frozen_cpu_sha256=helpers.sha(output / 'CPU_FROZEN.log'),
        strict_confinement='device_containment' in updated, predecessor_strict_confinement='device_containment' in config,
        legacy_addendum_sha256=addendum_sha, runtime_environment=runtime_environment,
        preflight_addendum_sha256=preflight_addendum_sha,
        preflight_cpu_sha256=helpers.sha(output / 'CPU_PREFLIGHT.log'),
        legacy_cpu_sha256=helpers.sha(output / 'CPU_LEGACY.log') if legacy else None,
        device_probe_sha256=helpers.sha(output / 'DEVICE_PROBE.json'), staged_unix=time.time(), signals_sent=0,
        builder_line='[Builder] 2026-09-17 R181 NODE4 actual-source CPU/provenance PASS; NEW16 no old rehearsal, same anchor, exact saved state and wall.')
    helpers.write(output / 'STAGED.json', stage_record)
    return {key: stage_record[key] for key in ('status', 'physical', 'source_root', 'strict_confinement', 'staged_unix')}


def saved_evidence(plan, saved, original, helpers):
    state = saved['state']
    stream = original.native.ContinualStream.restore(dict(state=state, sha256=saved['state_sha256']),
        expected_sha256=saved['state_sha256'])
    require(stream.checkpoint() == dict(state=state, sha256=saved['state_sha256']), 'complete_stream_roundtrip')
    contract = 'EXPLICIT_EXPERIMENT' if hasattr(original.native, 'verify_experiment_resume') else 'PINNED_LEGACY_FIXED_RANK8'
    if contract == 'EXPLICIT_EXPERIMENT':
        original.native.verify_experiment_resume(plan, stream.experiment)
    commit_path = Path(plan['root']) / 'checkpoints' / f"sleep_{saved['cycle']:06d}" / 'COMMIT.json'
    checkpoint = helpers.read(commit_path)
    require(Path(checkpoint['adapter_path']).is_relative_to(commit_path.parent)
            and Path(checkpoint['optimizer_rng_path']).is_relative_to(commit_path.parent), 'same_life_checkpoint_paths')
    original.native.NativeChild.verify_checkpoint(checkpoint)
    require(helpers.digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256
            and checkpoint.get('experiment') == getattr(stream, 'experiment', None)
            and stream.deadline_unix == plan['hard_end_unix'], 'exact_model_history_wall')
    import torch
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    helpers.verify_saved_schema(contract, plan, state, checkpoint, payload)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] > 0 and payload['parameter_names']
            and payload['optimizer']['state'] and payload['optimizer']['param_groups'], 'nonreset_optimizer_and_parameter_order')
    require(len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].device.type == 'cpu', 'complete_single_device_RNG')
    torch.Generator(device='cpu').set_state(payload['cpu_rng'])
    random.Random().setstate(payload['python_rng'])
    require(not torch.cuda.is_initialized(), 'CPU_provenance_only')
    return dict(record_path=saved['path'], record_sha256=saved['record_sha256'], state_sha256=saved['state_sha256'],
        checkpoint_path=str(commit_path), checkpoint_sha256=helpers.sha(commit_path), cycle=saved['cycle'],
        optimizer_steps=checkpoint['optimizer_steps'], adapter_state_sha256=checkpoint['adapter_state_sha256'],
        bundle_sha256=checkpoint['checkpoint_sha256'], full_AdamW_Python_CPU_CUDA_RNG=True)


def verify_readout_child(child, actor, command, source):
    require(child['parent'] == actor['pid'] and child['uid'] == actor['uid']
            and child['boot_id'] == actor['boot_id'] and child['cgroup'] == actor['cgroup']
            and child['group'] == child['pid'] and child['argv'] == command
            and child['cwd'] == source and child['environment'] == actor['environment'],
            'exact_existing_readout_child_not_another_GPU_owner')


def active_readout_child(plan, saved, actor, plan_path, native, helpers):
    name = native.readout_name(plan, saved['cycle'])
    root = Path(plan['root'])
    dispatch_path = root / 'readouts' / (name + '_DISPATCH.json')
    if not dispatch_path.exists():
        return None
    require(not (root / 'readouts' / (name + '_FAILED.json')).exists(), 'existing_readout_failed_no_replay')
    checkpoint_path = root / 'checkpoints' / f"sleep_{saved['cycle']:06d}" / 'COMMIT.json'
    command = [str(helpers.PYTHON), '-B', '-m', 'gpu.orch_r125_continual_readout',
        '--plan', str(plan_path), '--checkpoint', str(checkpoint_path), '--output', str(root / 'readouts' / name)]
    dispatch = helpers.read(dispatch_path)
    require(dispatch['resident_pid'] == actor['pid'] and dispatch['cycle'] == saved['cycle']
            and dispatch['command_sha256'] == helpers.digest(command)
            and dispatch['checkpoint_sha256'] == helpers.sha(checkpoint_path), 'exact_already_dispatched_readout')
    children = (Path('/proc') / str(actor['pid']) / 'task' / str(actor['pid']) / 'children').read_text().split()
    active = []
    for child_pid in children:
        try:
            fields = (Path('/proc') / child_pid / 'stat').read_text().rsplit(')', 1)[1].split()
            if fields[0] not in ('Z', 'X'):
                active.append(helpers.identity(int(child_pid)))
        except FileNotFoundError:
            pass
    if not active:
        return None
    require(len(active) == 1, 'one_existing_readout_child_only')
    verify_readout_child(active[0], actor, command, plan['source_root'])
    return active[0]


def ready_to_hold(drained, child):
    return bool(drained) or child is not None


def preflight_scan(output, request, helpers, original):
    source = request['source_root']
    scoped_request = deepcopy(request)
    plan = request['old_plan']
    saved = helpers.sleep_boundary(plan['root'])
    if saved is not None:
        child = active_readout_child(plan, saved, request['processes']['actor'],
            helpers.read(request['old_config'])['plan_path'], original.native, helpers)
        if child is not None:
            scoped_request['preflight_owned_readout'] = child
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + source, str(helpers.PYTHON), '-B', '-m', 'gpu.orch_r179_busy_preflight',
        '--config', request['new_config']]
    require(helpers.sha(Path(source) / PREFLIGHT) == PREFLIGHT_SHA, 'actual_exact_preflight_helper')
    report = json.loads(subprocess.check_output(command, text=True, cwd=source, timeout=90))
    report_path = output / ('PREFLIGHT_SCAN_' + str(time.time_ns()) + '.json')
    helpers.write(report_path, report)
    classifier = helpers.module_from_file('r179_actual_preflight_classifier', Path(source) / PREFLIGHT)
    proven = proven_argv_only(report, classifier.classify_argv_only)
    if scoped_request.get('preflight_owned_readout'):
        child = scoped_request['preflight_owned_readout']
        require(helpers.identity(child['pid']) == child, 'same_bound_readout_child_after_preflight_scan')
    validate_occupied_preflight(report, scoped_request, proven)
    helpers.write(output / ('PREFLIGHT_ACCEPTED_' + str(time.time_ns()) + '.json'),
        dict(status='KNOWN_OWNER_PREFLIGHT_ONLY_NOT_ADMISSION', report_path=str(report_path),
            report_sha256=helpers.sha(report_path), helper_sha256=PREFLIGHT_SHA,
            original_report_sha256=report['r179_preflight_evidence']['original_report_sha256'],
            proven_non_gpu_argv_only_pids=sorted(proven), original_clear=report['clear'],
            original_blocking_reasons=report['blocking_reasons'], owners=request['processes'],
            exact_already_dispatched_readout=scoped_request.get('preflight_owned_readout'),
            final_original_clear_admission_required=True, observed_unix=time.time()))
    return report


def proven_argv_only(report, classify):
    evidence = report['r179_preflight_evidence']
    original = {key: value for key, value in report.items() if key != 'r179_preflight_evidence'}
    canonical = json.dumps(original, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    require(evidence['schema'] == 'R179_BUSY_PREFLIGHT_EVIDENCE_ONLY_V1'
            and evidence['original_report_sha256'] == hashlib.sha256(canonical).hexdigest()
            and evidence['original_clear_and_blockers_unchanged'] is True
            and evidence['admission_receipt'] is False
            and evidence['scope'] == 'PRE_RETIREMENT_KNOWN_OWNER_PREFLIGHT_ONLY_FINAL_SCAN_UNCHANGED',
            'original_report_and_preflight_only_evidence_binding')
    eligible = evidence['eligible_non_gpu_argv_only_pids']
    require(isinstance(eligible, list) and all(type(pid) is int and pid > 0 for pid in eligible)
            and eligible == sorted(set(eligible)), 'exact_unique_proven_PID_list')
    require(set(evidence['observations']) == {str(pid) for pid in eligible}, 'complete_proven_observation_closure')
    observations = {pid: evidence['observations'][str(pid)] for pid in eligible}
    require(classify(original, observations) == eligible, 'rechecked_three_sample_kernel_executable_visibility_proof')
    require(json.dumps(original, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() == canonical,
            'preflight_classification_never_mutates_original')
    return set(eligible)


def validate_occupied_preflight(report, request, proven=()):
    require(report['scanner_euid'] == 0 and report['gpu']['uuid'] == request['old_plan']['gpu_uuid'], 'original_privileged_scanner')
    owned = {str(process['pid']) for process in request['processes'].values()}
    allowed_compute = {str(request['processes']['actor']['pid'])}
    if request.get('preflight_owned_readout'):
        owned.add(str(request['preflight_owned_readout']['pid']))
        allowed_compute.add(str(request['preflight_owned_readout']['pid']))
    require(not owned.intersection(str(pid) for pid in proven), 'known_GPU_owners_never_get_argv_exception')
    target_compute = {str(process['pid']) for process in report['compute_processes']
                      if process['gpu_uuid'] == request['old_plan']['gpu_uuid']}
    require(target_compute <= allowed_compute, 'no_foreign_target_compute_before_handoff')
    reasons = report['blocking_reasons']
    require(all((re.fullmatch(r'(open_device_pid|active_compute_pid|reserved_cvd_pid|uuid_reservation):[0-9]+', reason)
                 and reason.split(':')[1] in owned)
                or (reason in ('unexplained_device_memory', 'device_not_idle') and bool(target_compute))
                or (re.fullmatch(r'(' + '|'.join(DRIFT_PREFIXES) + r'):[0-9]+', reason)
                    and int(reason.split(':')[1]) in proven) for reason in reasons),
            'foreign_or_unknown_preflight_blockers:' + repr(reasons))


def monitor(output, request, evidence, helpers, seconds=600):
    control = output / 'control'
    old_index = int(Path(evidence['record_path']).stem)
    deadline = min(time.monotonic() + seconds, time.monotonic() + request['old_plan']['hard_end_unix'] - time.time() - 30)
    loaded = None
    before = helpers.read(evidence['record_path'])['document']['resume_state']['state']
    while time.monotonic() < deadline:
        require(not any((control / name).exists() for name in ('FAILED.json', 'EXIT.json', 'SERVICE_EXIT.json')),
                'successor_exited_preserve_no_retry')
        for path in helpers.records(request['old_plan']['root']):
            if int(path.stem) <= old_index:
                continue
            record = helpers.read(path)
            require(record['sha256'] == helpers.digest({key: value for key, value in record.items() if key != 'sha256'}),
                    'observed_record_hash')
            document = record['document']
            if record['kind'] == 'LOADED' and loaded is None:
                require(document['resume'] is True and document['optimizer_steps'] == evidence['optimizer_steps']
                        and document['adapter_sha256'] == evidence['adapter_state_sha256'], 'exact_saved_LOADED')
                actor = helpers.identity(document['pid'])
                require(actor['argv'] == [str(helpers.PYTHON), '-B', '-m', helpers.GUARD, 'native', '--config', request['new_config']]
                        and actor['cwd'] == request['source_root']
                        and actor['environment'] == request['processes']['actor']['environment'], 'actual_successor_source_and_environment')
                report = helpers.read(control / 'ADMISSION.json')
                require(report['clear'] and not report['blocking_reasons'] and report['scanner_euid'] == 0
                        and report['gpu']['uuid'] == request['old_plan']['gpu_uuid'], 'fresh_clear_original_admission')
                confinement = helpers.read(control / 'CONTAINMENT_VERIFIED.json')
                require(len(confinement.get('denied_foreign_minors', confinement.get('denied_devices', []))) == 7
                        and confinement['policy']['minor'] == request['device']['minor'], 'successor_strict_confinement')
                require(helpers.sha(Path(request['source_root']) / POLICY) == POLICY_SHA, 'actual_policy_bytes')
                loaded = dict(status='EXACT_SAVED_SUCCESSOR_LOADED', physical=request['physical'], actor=actor,
                    saved=evidence, record_index=record['index'], record_sha256=record['sha256'], observed_unix=time.time())
                helpers.write(output / 'LOADED_RECEIPT.json', loaded)
                print(json.dumps(loaded), flush=True)
            if loaded and record['kind'] == 'COMMITTED':
                envelope = document['state']
                state = envelope['state']
                require(envelope['sha256'] == helpers.digest(state) and state['pending'] is None
                        and state['rows'][:len(before['rows'])] == before['rows']
                        and state['model_state_sha256'] == helpers.digest(evidence['bundle_sha256']),
                        'new_generation_preserves_all_saved_rows_and_model')
                receipt = dict(status='EXACT_SAVED_LOADED_AND_NEW_GENERATION', physical=request['physical'],
                    saved_cycle=evidence['cycle'], optimizer_steps=evidence['optimizer_steps'],
                    loaded_sha256=helpers.sha(output / 'LOADED_RECEIPT.json'), record_index=record['index'],
                    record_sha256=record['sha256'], observed_unix=time.time(), retained_learning_claim=False)
                helpers.write(output / 'HANDOFF_COMPLETE.json', receipt)
                return receipt
        time.sleep(1)
    require(loaded is not None, 'no_successor_load_in_bound')
    return dict(status='LOADED_NEW_GENERATION_NOT_YET_OBSERVED', physical=request['physical'])


def validate_handoff_attempt(output, wait_seconds):
    require(type(wait_seconds) is int and 1 <= wait_seconds <= MAX_BOUNDARY_WAIT_SECONDS,
            'bounded_90_minute_boundary_wait')
    require(not any((output / name).exists() for name in ('RETIREMENT_STARTED.json', 'RETIRED.json',
            'DISPATCHED.json', 'LOADED_RECEIPT.json', 'HANDOFF_COMPLETE.json')), 'no_consumed_handoff_rearm')


def handoff(bundle, output, wait_seconds):
    helpers = helper_module(bundle)
    request = helpers.read(output / 'STAGED.json')
    require(request['strict_confinement'], 'R179_scope_requires_strict_confinement_legacy_lanes_staged_only')
    validate_handoff_attempt(output, wait_seconds)
    config_path, config, plan, original, pair = selected(request['physical'], helpers)
    require(preflight_authority(bundle, helpers) == request['preflight_addendum_sha256']
            and helpers.sha(output / 'CPU_PREFLIGHT.log') == request['preflight_cpu_sha256'],
            'exact_receiving_preflight_provenance_before_signal')
    if request['physical'] in (0, 1):
        require(legacy_authority(bundle, helpers) == request['legacy_addendum_sha256']
                and helpers.sha(output / 'CPU_LEGACY.log') == request['legacy_cpu_sha256']
                and legacy_runtime_environment(pair['actor']) == request['runtime_environment'], 'legacy_receiving_provenance_before_signal')
    require(pair == request['processes'] and helpers.sha(config_path) == request['old_config_sha256']
            and helpers.sha(request['new_config']) == request['new_config_sha256']
            and helpers.sha(Path(__file__)) == request['operator_sha256']
            and helpers.sha(bundle / 'cpu_actual.py') == request['cpu_script_sha256']
            and helpers.sha(output / 'CPU_POLICY.log') == request['cpu_sha256']
            and helpers.sha(output / 'CPU_FROZEN.log') == request['frozen_cpu_sha256'], 'bound_stage_owners_sources_CPU')
    require(helpers.sha(output / 'DEVICE_PROBE.json') == request['device_probe_sha256'], 'bound_receiving_device_proof')
    proof = helpers.read(output / 'SOURCE_PROOF.json')
    require(helpers.sha(output / 'SOURCE_PROOF.json') == request['source_proof_sha256']
            and helpers.inventory_files(proof['old_source']) == proof['old_inventory']
            and helpers.inventory_files(proof['new_source']) == proof['new_inventory'], 'full_immutable_source_provenance')
    require(helpers.verify_resume_entrypoint(request['source_root']) == helpers.read(output / 'RESUME_ENTRYPOINT.json'),
            'ordinary_exact_saved_resume_entrypoint')
    lock = os.open(output / 'OPERATOR.lock', os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    descriptors, paused = {}, []

    def interrupted(signum, frame):
        raise RuntimeError('bounded_operator_interrupted')

    handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)}
    deadline = min(time.monotonic() + wait_seconds, time.monotonic() + plan['hard_end_unix'] - time.time() - 180)
    try:
        for name, process in pair.items():
            require(helpers.identity(process['pid']) == process, 'exact_identity_before_pidfd')
            descriptors[name] = os.pidfd_open(process['pid'])
            require(helpers.identity(process['pid']) == process, 'exact_identity_after_pidfd')
        preflight_scan(output, request, helpers, original)
        while time.monotonic() < deadline:
            require(all(not select.select([descriptor], [], [], 0)[0] for descriptor in descriptors.values()), 'original_owner_still_alive')
            saved = helpers.sleep_boundary(plan['root'])
            if saved is None:
                time.sleep(.25)
                continue
            readout_name = original.native.readout_name(plan, saved['cycle'])
            dispatch_path = Path(plan['root']) / 'readouts' / (readout_name + '_DISPATCH.json')
            if not dispatch_path.exists():
                time.sleep(.25)
                continue
            dispatch = helpers.read(dispatch_path)
            require(dispatch['resident_pid'] == pair['actor']['pid'] and dispatch['cycle'] == saved['cycle']
                    and dispatch['checkpoint_sha256'] == helpers.sha(Path(plan['root']) / 'checkpoints' /
                        f"sleep_{saved['cycle']:06d}" / 'COMMIT.json'), 'exact_existing_readout_dispatch')
            drained = helpers.readout_drained(plan, saved, pair['actor']['pid'], config['plan_path'], original.native)
            child = None if drained else active_readout_child(plan, saved, pair['actor'],
                config['plan_path'], original.native, helpers)
            if not ready_to_hold(drained, child):
                time.sleep(.25)
                continue
            if helpers.sleep_boundary(plan['root']) != saved:
                continue
            for name in ('supervisor', 'timer', 'actor'):
                paused.append(name)
                helpers.pause_exact(pair[name], descriptors[name])
            if helpers.sleep_boundary(plan['root']) != saved:
                helpers.resume_paused(paused, descriptors)
                continue
            helpers.write(output / ('READOUT_HOLD_' + str(time.time_ns()) + '.json'),
                dict(cycle=saved['cycle'], exact_readout_child=child, already_drained=bool(drained),
                    all_threads_quiescent=True, old_owners_retired=False, observed_unix=time.time()))
            drain_deadline = min(deadline, time.monotonic() + 300)
            drained = None
            while time.monotonic() < drain_deadline:
                drained = helpers.readout_drained(plan, saved, pair['actor']['pid'], config['plan_path'], original.native)
                if drained:
                    break
                time.sleep(.5)
            if not drained:
                helpers.resume_paused(paused, descriptors)
                require(time.monotonic() < deadline, 'readout_not_drained_before_bound_owners_resumed')
                continue
            require(helpers.sleep_boundary(plan['root']) == saved, 'saved_boundary_after_readout_drains')
            evidence = saved_evidence(plan, saved, original, helpers)
            snapshot = output / ('snapshot_' + str(time.time_ns()))
            shutil.copytree(Path(plan['root']) / 'stream', snapshot)
            helpers.verify_snapshot(snapshot, plan['root'], saved['state_sha256'], original)
            require(helpers.sleep_boundary(plan['root']) == saved
                    and saved_evidence(plan, saved, original, helpers) == evidence, 'unchanged_boundary_after_full_snapshot')
            helpers.write(output / 'BOUNDARY.json', dict(saved=evidence, snapshot=str(snapshot), readout=drained,
                all_threads_quiescent=True, full_stream_history_preserved=True, observed_unix=time.time()))
            helpers.write(output / 'RETIREMENT_STARTED.json', dict(boundary_sha256=helpers.sha(output / 'BOUNDARY.json'),
                started_unix=time.time()))
            for name in ('actor', 'timer', 'supervisor'):
                require(helpers.identity(pair[name]['pid']) == pair[name], 'exact_identity_before_retirement')
                signal.pidfd_send_signal(descriptors[name], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
                require(bool(select.select([descriptors[name]], [], [], 30)[0]), 'exact_owner_exit_without_KILL')
            paused.clear()
            helpers.write(output / 'RETIRED.json', dict(processes=pair, retired_unix=time.time()))
            with original.journal.StreamJournal(Path(plan['root']) / 'stream', create=False) as journal:
                require(journal.latest_checkpoint()['expected_sha256'] == saved['state_sha256'], 'released_writer_exact_state')
            command = helpers.launch_command(request)
            with (output / 'control' / 'SUPERVISOR.log').open('x') as log:
                process = subprocess.Popen(command, cwd=request['source_root'], env=dict(os.environ,
                    CUDA_VISIBLE_DEVICES='', PYTHONPATH=request['source_root'], PYTHONDONTWRITEBYTECODE='1'),
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            helpers.write(output / 'DISPATCHED.json', dict(supervisor_pid=process.pid, command=command, started_unix=time.time()))
            return monitor(output, request, evidence, helpers)
        helpers.write(output / ('WAIT_EXPIRED_' + str(time.time_ns()) + '.json'), dict(status='NO_RETIREMENT', expired_unix=time.time()))
        return dict(status='NO_CLEAN_DRAINED_BOUNDARY_IN_BOUND', physical=request['physical'])
    except BaseException as error:
        helpers.write(output / ('ERROR_' + str(time.time_ns()) + '.json'), dict(error_type=type(error).__name__,
            error=str(error), retirement_started=(output / 'RETIREMENT_STARTED.json').exists(), observed_unix=time.time()))
        raise
    finally:
        helpers.resume_paused(paused, descriptors)
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)
        for signum, previous in handlers.items():
            signal.signal(signum, previous)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'handoff'))
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--physical', type=int, choices=tuple(ALLOWLIST), required=True)
    parser.add_argument('--wait-seconds', type=int, default=1800)
    arguments = parser.parse_args()
    bundle_path = arguments.bundle.resolve()
    require(bundle_path.parent == BASE and bundle_path.name.startswith('orch_r179_node4_'), 'bounded_NODE4_bundle')
    output_path = bundle_path / f'lane{arguments.physical}'
    result = (stage(bundle_path, output_path, arguments.physical) if arguments.action == 'stage' else
              handoff(bundle_path, output_path, arguments.wait_seconds))
    print(json.dumps(result, sort_keys=True), flush=True)
