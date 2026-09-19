"""Rohin147: retire only a40r5/6/7 at exact saved, readout-drained boundaries."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import select
import shutil
import signal
import subprocess
import sys
import time
from types import FunctionType
import uuid


BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
PRIMITIVE_SHA = '6e4d91c9581d952924ae269d7f4831fc9840c741805ebcddf2f2c78e8d356270'
PRIMITIVE = 'orch_r144_a100_a40r_target_rollout.py'
ROLLOUT = BASE / 'orch_r144_target_rollout_a40r_suffix_20260916t1643z'
NONE = BASE / 'orch_r136_raw_unparented_none_a40r7_20260916_attempt1'
TARGETS = {
    5: dict(label='kernel_unparented', root=str(BASE / 'orch_r136_kernel_unparented_a40r5_20260916_attempt1/run1'),
            config=str(ROLLOUT / 'lane5/control/GUARD.json'), source=str(ROLLOUT / 'lane5/source'),
            guard_sha='35d2b7ad05ded031aa20a5bdef76a113c6269ee45b0f20dcea8a2cb57fa6e1bc',
            native_sha='d3cbd3b0053f0c7c5d3d8e36e37c52954bdb39a40fc4346e4e6d3ab4bf5a2ad1',
            uuid='GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30', pid=3053313, ticks='14887398',
            entry='gpu.orch_r125_continual_guard', supervisor='gpu.orch_r125_continual_guard', inner='supervise'),
    6: dict(label='raw_unparented_reread', root=str(BASE / 'orch_r136_raw_unparented_reread_a40r6_20260916_attempt1/run1'),
            config=str(ROLLOUT / 'lane6/readmission1/control/GUARD.json'), source=str(ROLLOUT / 'lane6/source'),
            guard_sha='be30a9a31dfe5f6c6cebdea0ba7aef84b32d99aa1593e7f311d8bba9ffb85b37',
            native_sha='bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6',
            uuid='GPU-06b31c8f-7a96-d812-23f3-df3444d95397', pid=2895043, ticks='14776663',
            entry='gpu.orch_r125_continual_guard', supervisor='gpu.orch_r137_node4_containment', inner='contained-native'),
    7: dict(label='raw_unparented_none', root=str(NONE / 'run1'),
            config=str(NONE / 'control_r152_a40r7_attempt3/GUARD.json'), source=str(NONE / 'source_r152_a40r7_attempt3'),
            guard_sha='1cfaede87cabc78b2ce583de940ebdfbd76a2f651b270b9759fbe13dd8cae4cf',
            native_sha='bcd716db469665d6c2070ed46d4b910d619b7366b66af2891c9ed71a5e069af6',
            uuid='GPU-6eac3b9d-551a-d786-f598-04ef6d701c98', pid=715453, ticks='16215555',
            entry='gpu.orch_r152_a40r7_recovery', supervisor='gpu.orch_r152_a40r7_recovery', inner='contained-native'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    path = Path(path)
    require(not any(item.is_symlink() for item in (path, *path.parents)), 'no_evidence_symlinks')
    result = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, document):
    with Path(path).open('x') as handle:
        json.dump(document, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    descriptor = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def ref(path):
    return dict(path=str(Path(path).absolute()), sha256=sha(path))


def primitives():
    path = Path(__file__).absolute().with_name(PRIMITIVE)
    require(sha(path) == PRIMITIVE_SHA, 'tested_boundary_primitive_bytes')
    spec = importlib.util.spec_from_file_location('r153_boundary_primitives', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scope(physical, config, plan, config_path):
    require(type(physical) is int and physical in TARGETS, 'only_Rohin147_a40r5_6_7')
    target = TARGETS[physical]
    require(plan['physical'] == physical and plan['gpu_uuid'] == target['uuid']
            and plan['root'] == target['root'] and plan['source_root'] == target['source']
            and str(config_path) == target['config'], 'exact_named_life_not_other_slots')
    require(config['hard_end_unix'] == plan['hard_end_unix']
            and ('device_containment' in config) == (physical in (6, 7)), 'unchanged_original_topology_wall')


def process_pair(core, physical, config, plan):
    target = TARGETS[physical]
    actor = core.identity(target['pid'])
    timer = core.identity(actor['parent'])
    supervisor = core.identity(timer['parent'])
    pair = dict(actor=actor, timer=timer, supervisor=supervisor)
    validate_pair(pair, physical, config, plan, read(Path(config['attempt_dir']) / 'LAUNCH.json'))
    return pair


def validate_pair(pair, physical, config, plan, launch):
    target = TARGETS[physical]
    actor, timer, supervisor = (pair[name] for name in ('actor', 'timer', 'supervisor'))
    command = [str(PYTHON), '-B', '-m', target['entry'], 'native', '--config', target['config']]
    require(actor['pid'] == target['pid'] and actor['start_ticks'] == target['ticks']
            and actor['argv'] == command, 'exact_original_actor_not_PID_reuse')
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3]) and timer['argv'][4:] == command,
            'exact_original_timer')
    require(supervisor['argv'] == [str(PYTHON), '-B', '-m', target['supervisor'], target['inner'],
                                   '--config', target['config']], 'exact_original_supervisor')
    require(actor['parent'] == timer['pid'] and timer['parent'] == supervisor['pid']
            and actor['group'] == timer['group'] == timer['pid'], 'exact_three_process_ancestry')
    require(launch['pid'] == timer['pid'] and launch['parent_start_ticks'] == timer['start_ticks']
            and launch['guard_sha256'] == target['guard_sha'] and launch['plan_sha256'] == config['plan_sha256']
            and launch['gpu_uuid'] == target['uuid'], 'original_launch_binding')
    for name, process in pair.items():
        require(process['uid'] == os.getuid() == 2524 and process['cwd'] == target['source']
                and process['boot_id'] == actor['boot_id'] and process['cgroup'] == actor['cgroup'],
                'same_owned_source_boot_cgroup')
        expected = ['CUDA_VISIBLE_DEVICES=' + ('' if physical == 5 and name == 'supervisor' else target['uuid'])]
        if physical == 7:
            expected.append('PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')
        require(sorted(process['environment']) == sorted(expected), 'original_CVD_allocator_unchanged')
    if physical in (6, 7):
        require(actor['cgroup'] == '0::/system.slice/' + config['device_containment']['unit'] + '.service',
                'exact_contained_unit')


def saved_evidence(core, physical, plan, saved, original):
    if physical != 5:
        result = core.saved_evidence(plan, saved, original)
    else:
        source = Path(plan['source_root'])
        require(sha(source / 'gpu/orch_r125_continual_native.py') == TARGETS[5]['native_sha']
                and sha(source / 'organism_v6/orch_r125_continual_stream.py') == core.LEGACY_STREAM_SHA,
                'exact_R144_R145_legacy_lane5_not_generic_skip')
        envelope = dict(state=saved['state'], sha256=saved['state_sha256'])
        stream = original.native.ContinualStream.restore(envelope, expected_sha256=saved['state_sha256'])
        commit = Path(plan['root']) / 'checkpoints' / f"sleep_{saved['cycle']:06d}" / 'COMMIT.json'
        checkpoint = read(commit)
        original.native.NativeChild.verify_checkpoint(checkpoint)
        require(core.digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256
                and stream.deadline_unix == plan['hard_end_unix'], 'same_legacy_saved_model_and_wall')
        import torch
        payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
        core.verify_saved_schema('PINNED_LEGACY_FIXED_RANK8', plan, saved['state'], checkpoint, payload)
        require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] > 0
                and payload['parameter_names'] and payload['optimizer']['state'] and payload['optimizer']['param_groups']
                and len(payload['cuda_rng']) == 1, 'full_legacy_AdamW_and_RNG')
        torch.Generator(device='cpu').set_state(payload['cpu_rng'])
        random.Random(0).setstate(payload['python_rng'])
        require(payload['cuda_rng'][0].device.type == 'cpu' and not torch.cuda.is_initialized(), 'CPU_only_saved_payload')
        result = dict(record_path=saved['path'], record_sha256=saved['record_sha256'], state_sha256=saved['state_sha256'],
                      checkpoint_path=str(commit), checkpoint_sha256=sha(commit), cycle=saved['cycle'],
                      optimizer_steps=checkpoint['optimizer_steps'], adapter_state_sha256=checkpoint['adapter_state_sha256'],
                      bundle_sha256=checkpoint['checkpoint_sha256'], full_AdamW_Python_CPU_CUDA_RNG=True)
    if physical == 7:
        require(result['cycle'] >= 32 and result['optimizer_steps'] >= 2000, 'preserve_R152_success_never_revert31')
    return result


def setup(physical, output, cpu_gate):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_operator')
    require(type(physical) is int and physical in TARGETS, 'only_Rohin147_a40r5_6_7')
    core = primitives()
    core.current_node('a40r')
    target = TARGETS[physical]
    require(sha(target['config']) == target['guard_sha'], 'original_immutable_guard')
    config, plan, original = core.originals(target['config'])
    scope(physical, config, plan, target['config'])
    require(sha(Path(plan['source_root']) / 'gpu/orch_r125_continual_native.py') == target['native_sha'],
            'original_native_with_current_R144_R145')
    cpu = read(cpu_gate)
    require(cpu['status'] == 'PASS' and cpu['exit_code'] == 0
            and cpu['operator_sha256'] == sha(Path(__file__).absolute())
            and cpu['primitive_sha256'] == PRIMITIVE_SHA and sha(cpu['tests']['path']) == cpu['tests']['sha256'],
            'bound_real_CPU_tests_before_signals')
    output = Path(output).absolute()
    require(output.parent.parent == BASE and output.parent.name.startswith('orch_r153_node4_retirement_')
            and output.name == 'lane' + str(physical), 'own_lane_output_only')
    output.mkdir()
    request = dict(status='WAITING_FOR_SAVED_BOUNDARY_NO_SIGNALS', physical=physical, label=target['label'],
                   original_guard=ref(target['config']), original_plan=ref(config['plan_path']),
                   source_pins=config['source_pins'], processes=process_pair(core, physical, config, plan),
                   device=core.actual_device(plan), cpu_gate=ref(cpu_gate), operator=ref(Path(__file__).absolute()),
                   authorization='Rohin147 five named retirements; node4 only physical5/6/7',
                   held_contents_read=False, observed_unix=time.time())
    write(output / 'REQUEST.json', request)
    return core, config, plan, original, request


def files(directory):
    return {str(path.relative_to(directory)): sha(path) for path in sorted(Path(directory).rglob('*')) if path.is_file()}


def copy_verified(source, destination):
    before = files(source)
    shutil.copytree(source, destination)
    require(files(destination) == before == files(source), 'exact_unchanged_preservation_copy')
    return before


def retirement_signal(core, expected, descriptor, kind):
    require(kind in (signal.SIGTERM, signal.SIGCONT), 'only_TERM_CONT_retirement')
    require(core.identity(expected['pid']) == expected, 'exact_identity_before_retirement_signal')
    signal.pidfd_send_signal(descriptor, kind)


def resume_config(config, directory):
    updated = deepcopy(config)
    updated.update(attempt_dir=str(directory), resume=True)
    if 'device_containment' in updated:
        updated['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    return updated


def prepare_resumption(physical, output, config, evidence, snapshot_inventory, checkpoint_inventory):
    directory = output / 'resume_control'
    directory.mkdir()
    updated = resume_config(config, directory)
    write(directory / 'GUARD.json', updated)
    result = dict(status='SAVED_STATE_RESUMABLE_NOT_LAUNCHED', physical=physical, saved=evidence,
                  source_root=TARGETS[physical]['source'], original_guard=ref(TARGETS[physical]['config']),
                  resume_guard=ref(directory / 'GUARD.json'), stream_copy=str(output / 'stream'),
                  checkpoint_copy=str(output / 'checkpoint'), stream_inventory=snapshot_inventory,
                  checkpoint_inventory=checkpoint_inventory, pending=None, raw_context_journal_preserved=True,
                  ordinary_native_resume=True, old_recovery_not_replayed=True, fresh_admission_required=True,
                  cwd=TARGETS[physical]['source'],
                  replacement_launched=False, command=[str(PYTHON), '-B', str(Path(__file__).absolute()), 'resume',
                      '--output', str(output), '--execute-resume'], recorded_unix=time.time())
    write(output / 'RESUMPTION.json', result)
    return result


def clearance(physical, config, plan, output):
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
               'PYTHONPATH=' + plan['source_root'], str(PYTHON), '-B', '-m',
               'gpu.orch_r125_continual_guard', 'scan', '--config', TARGETS[physical]['config']]
    for attempt in range(10):
        report = json.loads(subprocess.check_output(command, text=True, timeout=90, cwd=plan['source_root']))
        write(output / f'CLEARANCE_{attempt:02d}.json', report)
        if report['clear']:
            require(report['scanner_euid'] == 0 and not report['blocking_reasons']
                    and report['gpu']['uuid'] == TARGETS[physical]['uuid'], 'privileged_exact_GPU_clearance')
            write(output / 'GPU_CLEAR.json', dict(status='CLEAR', report=ref(output / f'CLEARANCE_{attempt:02d}.json'),
                physical=physical, gpu_uuid=TARGETS[physical]['uuid'], observed_unix=time.time(),
                fresh_replacement_admission_still_required=True))
            return
        time.sleep(2)
    raise ValueError('GPU_clearance_not_proven_no_replacement_launch')


def clear_retired(physical, output):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_clearance')
    require(type(physical) is int and physical in TARGETS, 'only_Rohin147_a40r5_6_7')
    output = Path(output)
    require(output.parent.parent == BASE and output.parent.name.startswith('orch_r153_node4_retirement_')
            and output.name == 'lane' + str(physical), 'own_retired_lane_output')
    retired = read(output / 'RETIRED.json')
    require(retired['physical'] == physical and retired['status'] == 'EXACT_THREE_OWNED_PROCESSES_EXITED'
            and sha(retired['boundary']['path']) == retired['boundary']['sha256']
            and sha(retired['resumption']['path']) == retired['resumption']['sha256'], 'preserved_retirement_receipts')
    core = primitives()
    core.current_node('a40r')
    require(sha(TARGETS[physical]['config']) == TARGETS[physical]['guard_sha'], 'original_immutable_guard')
    config, plan, original = core.originals(TARGETS[physical]['config'])
    scope(physical, config, plan, TARGETS[physical]['config'])
    saved = core.sleep_boundary(plan['root'])
    require(saved and saved_evidence(core, physical, plan, saved, original) == read(retired['boundary']['path'])['saved'],
            'retired_saved_state_still_exact')
    clearance(physical, config, plan, output)
    return dict(status='RETIRED_PRESERVED_GPU_CLEAR', physical=physical, clearance=ref(output / 'GPU_CLEAR.json'))


def retire(physical, output, cpu_gate, wait_seconds=7200):
    require(type(wait_seconds) is int and 1 <= wait_seconds <= 7200, 'bounded_retirement_wait')
    output = Path(output)
    core, config, plan, original, request = setup(physical, output, cpu_gate)
    pair = request['processes']
    descriptors, paused, handlers = {}, [], {}
    started = False
    try:
        for name, process in pair.items():
            descriptors[name] = os.pidfd_open(process['pid'])
        for signum in (signal.SIGINT, signal.SIGTERM):
            handlers[signum] = signal.signal(signum, lambda number, frame: (_ for _ in ()).throw(InterruptedError('operator_cancelled')))
        deadline = min(time.monotonic() + wait_seconds, time.monotonic() + plan['hard_end_unix'] - time.time() - 600)
        report_at = 0
        while time.monotonic() < deadline:
            if time.monotonic() >= report_at:
                print(json.dumps(dict(status='WAITING_FOR_READOUT_DRAINED_SAVED_BOUNDARY', physical=physical,
                                      observed_unix=time.time())), flush=True)
                report_at = time.monotonic() + 60
            require(process_pair(core, physical, config, plan) == pair, 'same_processes_while_waiting')
            saved = core.sleep_boundary(plan['root'])
            if saved is None:
                time.sleep(.2)
                continue
            drained = core.readout_drained(plan, saved, pair['actor']['pid'], config['plan_path'], original.native)
            if not drained:
                time.sleep(.2)
                continue
            for name in ('supervisor', 'timer', 'actor'):
                paused.append(name)
                core.pause_exact(pair[name], descriptors[name])
            if core.sleep_boundary(plan['root']) != saved:
                core.resume_paused(paused, descriptors)
                continue
            require(core.readout_drained(plan, saved, pair['actor']['pid'], config['plan_path'], original.native),
                    'readout_drained_after_exact_quiescence')
            evidence = saved_evidence(core, physical, plan, saved, original)
            snapshot_inventory = copy_verified(Path(plan['root']) / 'stream', output / 'stream')
            core.verify_snapshot(output / 'stream', plan['root'], saved['state_sha256'], original)
            checkpoint_inventory = copy_verified(Path(evidence['checkpoint_path']).parent, output / 'checkpoint')
            require(core.sleep_boundary(plan['root']) == saved
                    and saved_evidence(core, physical, plan, saved, original) == evidence,
                    'saved_adapter_optimizer_rng_context_unchanged_after_copy')
            write(output / 'BOUNDARY.json', dict(saved=evidence, readout=drained, snapshot=str(output / 'stream'),
                  all_threads_quiescent=True, held_contents_read=False, observed_unix=time.time()))
            prepare_resumption(physical, output, config, evidence, snapshot_inventory, checkpoint_inventory)
            write(output / 'RETIREMENT_STARTED.json', dict(boundary=ref(output / 'BOUNDARY.json'), started_unix=time.time()))
            started = True
            for name in ('actor', 'timer', 'supervisor'):
                retirement_signal(core, pair[name], descriptors[name], signal.SIGTERM)
                retirement_signal(core, pair[name], descriptors[name], signal.SIGCONT)
                require(bool(select.select([descriptors[name]], [], [], 30)[0]), 'exact_pidfd_exit_without_KILL')
            paused.clear()
            write(output / 'RETIRED.json', dict(status='EXACT_THREE_OWNED_PROCESSES_EXITED', physical=physical,
                  processes=pair, boundary=ref(output / 'BOUNDARY.json'), resumption=ref(output / 'RESUMPTION.json'),
                  other_slots_signalled=False, replacement_launched=False, retired_unix=time.time()))
            with original.journal.StreamJournal(Path(plan['root']) / 'stream', create=False) as journal:
                require(journal.latest_checkpoint()['expected_sha256'] == saved['state_sha256'],
                        'original_writer_released_at_exact_saved_boundary')
            clearance(physical, config, plan, output)
            return dict(status='RETIRED_PRESERVED_GPU_CLEAR', physical=physical, retired=ref(output / 'RETIRED.json'),
                        resumption=ref(output / 'RESUMPTION.json'), clearance=ref(output / 'GPU_CLEAR.json'))
        write(output / 'NO_RETIREMENT.json', dict(status='BOUNDARY_WAIT_EXPIRED_ORIGINALS_CONTINUE', observed_unix=time.time()))
        return dict(status='NO_RETIREMENT', physical=physical)
    except BaseException as error:
        write(output / 'FAILED.json', dict(status='FAILED', error_type=type(error).__name__, error=str(error),
              retirement_started=started, originals_resumed_if_not_retired=True, observed_unix=time.time()))
        raise
    finally:
        core.resume_paused(paused, descriptors)
        for descriptor in descriptors.values():
            os.close(descriptor)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


def resume(output, execute_resume=False):
    require(execute_resume is True and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'explicit_CPU_resume_operator')
    output = Path(output)
    request = read(output / 'REQUEST.json')
    require(read(output / 'RETIRED.json')['status'] == 'EXACT_THREE_OWNED_PROCESSES_EXITED', 'actually_retired_first')
    require(sha(Path(__file__).absolute()) == request['operator']['sha256'], 'same_tested_operator_for_resume')
    core = primitives()
    core.current_node('a40r')
    physical = request['physical']
    require(physical in TARGETS and output.name == 'lane' + str(physical), 'same_owned_retired_lane')
    receipt = read(output / 'RESUMPTION.json')
    require(sha(receipt['resume_guard']['path']) == receipt['resume_guard']['sha256'], 'saved_resume_guard_bytes')
    config, plan, original = core.originals(receipt['resume_guard']['path'])
    scope(physical, config, plan, TARGETS[physical]['config'])
    saved = core.sleep_boundary(plan['root'])
    require(saved and saved_evidence(core, physical, plan, saved, original) == receipt['saved'], 'exact_retired_saved_state')
    require(files(output / 'checkpoint') == receipt['checkpoint_inventory'], 'preserved_checkpoint_copy')
    require(config['resume'] is True and config['source_pins'] == request['source_pins'], 'same_source_ordinary_resume')
    os.chdir(plan['source_root'])
    if physical == 5:
        original.guard.supervise(receipt['resume_guard']['path'])
    else:
        from gpu import orch_r137_node4_containment as node
        namespace = dict(node.contained_supervise.__globals__)
        if physical == 7:
            from gpu.orch_r145_a40r7_recovery import allocator_command
            namespace['device_containment_command'] = lambda *args: allocator_command(node.device_containment_command(*args))
        function = FunctionType(node.contained_supervise.__code__, namespace, node.contained_supervise.__name__)
        function(receipt['resume_guard']['path'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('retire', 'resume', 'clear'))
    parser.add_argument('--physical', type=int, choices=(5, 6, 7))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cpu-gate', type=Path)
    parser.add_argument('--wait-seconds', type=int, default=7200)
    parser.add_argument('--execute-resume', action='store_true')
    args = parser.parse_args()
    if args.action == 'retire':
        print(json.dumps(retire(args.physical, args.output, args.cpu_gate, args.wait_seconds)), flush=True)
    elif args.action == 'clear':
        print(json.dumps(clear_retired(args.physical, args.output)), flush=True)
    else:
        resume(args.output, args.execute_resume)
