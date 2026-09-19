"""Node3 physical3-7 staging and contained dispatch; no retirement or parent calls."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import uuid

from gpu import orch_r125_continual_guard as guard
from gpu import orch_r125_continual_native as native
from gpu import orch_r133_node3_creative as creative
from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
from gpu.orch_r133_stage_child import stage


BASE = Path('/localhome/local-rohing')
DEVICES = {
    3: 'GPU-e1277146-04f2-c38f-d1ae-1a98132f907e',
    4: 'GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4',
    5: 'GPU-bc211959-642d-664b-3581-42a0dbe434e9',
    6: 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8',
    7: 'GPU-319224de-e668-1822-d80b-4b24d15968ae',
}
LANES = {
    3: ('brain_guided', 'brain_lecture', 'parent_guided_distillation', 2, 'Explanatory, analogy-critical'),
    4: ('creative_free', 'creative_writing', 'free_distillation', 2, 'Workshop critique'),
    5: ('creative_none', 'creative_writing', 'no_distillation', 4, 'Playful, exploratory'),
    6: ('support_none', 'emotional_support', 'no_distillation', 5, 'Reflective, non-directive'),
    7: ('creative_select', 'creative_writing', 'reread_select', 3, 'Editorial, revision-focused'),
}
SUBJECTS = {
    'brain_lecture': 'Brain lecture. Explore ideas about learning, attention and memory using the supplied '
        'human-neuroscience source cards. Distinguish evidence about brains from unproven analogies to '
        'this language model or LoRA. Explain and test your understanding without claiming biological equivalence.',
    'creative_writing': 'Creative-writing seminar. Explore actual drafts, alternative scenes or voices, '
        'specific editorial criticism and revisions. Choose useful directions and compare what revisions '
        'change; neither length nor a recurring introspective format is a goal.',
    'emotional_support': 'Supportive self-reflection conversation. Explore your own recorded activity, '
        'judgments, uncertainty and confidence through open questions. This is not human therapy or a claim '
        'of subjective feelings. Do not adopt a dataset speaker\'s biography, identity or diagnosis.',
}


def spec(physical):
    native.require(type(physical) is int and physical in LANES, 'only_owned_node3_physical3_7')
    label, programme, replay, cadence, style = LANES[physical]
    return dict(physical=physical, gpu_uuid=DEVICES[physical], label=label, programme=programme,
                replay=replay, cadence=cadence, style=style, seed=0,
                branch=f'NODE3_{physical}_{label.upper()}_SPARSE{cadence}')


def programme_text(physical):
    lane = spec(physical)
    return (SUBJECTS[lane['programme']] + f" Astra's style is {lane['style']}. One autonomous Astra "
        f"parent leads this thread, scheduled after each {lane['cadence']} additional observed responses. "
        'Responses are asynchronous and useful silence is allowed; keep going while a reply is pending. '
        'Parent turns never receive sealed evaluation content or results.\n')


def startup_text(original, physical, source, workspace):
    lane = spec(physical)
    text = creative.startup(original, source, workspace)
    start = text.index('After two generated experience segments,')
    end = text.index('trains each new eligible segment', start)
    descriptions = {
        'free_distillation': 'After two experience segments, a third generated segment distills what you '
            'want to carry forward, then the runtime sleeps. This is free_distillation. Sleep ',
        'parent_guided_distillation': 'After two experience segments, a third generated segment re-reads '
            'available parent guidance to help distill what you want to carry forward, then sleeps. If '
            'no guidance is present, choose for yourself. This is parent_guided_distillation. Sleep ',
        'no_distillation': 'After two experience segments, the runtime sleeps directly. This is '
            'no_distillation: there is no third pre-sleep generation and no sleep-time compaction. Sleep ',
    }
    if lane['replay'] != 'reread_select':
        text = text[:start] + descriptions[lane['replay']] + text[end:]
    old = 'At sleep your nonempty selected text replaces earlier visible history; this is lossy, and the archive is not automatically searched.'
    if lane['replay'] == 'no_distillation':
        replacement = ('At sleep the available visible history is retained; only ordinary context-limit '
                       'eviction applies. No new summary replaces it. The archive is not automatically searched.')
    elif lane['replay'] != 'reread_select':
        replacement = ('At sleep your nonempty distillation replaces earlier visible history; this is '
                       'lossy, and the archive is not automatically searched.')
    else:
        replacement = old
    native.require(text.count(old) == 1, 'known_memory_description')
    text = text.replace(old, replacement).replace('physical1 through the ovx2 wrapper',
                                                 f'physical{physical} through the ovx2 wrapper')
    return text.split('### Programme:')[0] + '### Programme\n\n' + programme_text(physical)


def device_minor(gpu_uuid):
    native.require(gpu_uuid in DEVICES.values(), 'owned_UUID_only')
    from gpu.orch_rich_hot_a100_minor_scan import device_minor as resolve
    minor = resolve(gpu_uuid)
    metadata = Path('/dev/nvidia'+str(minor)).lstat()
    native.require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
                   and os.minor(metadata.st_rdev) == minor, 'kernel_UUID_character_device')
    return minor


def containment_command(plan, policy, command, lifetime):
    lane = spec(plan['physical'])
    native.require(plan['gpu_uuid'] == lane['gpu_uuid'], 'exact_owned_UUID')
    native.require(type(policy['minor']) is int and 0 <= policy['minor'] <= 255, 'verified_minor')
    native.require(type(policy['uid']) is int and policy['uid'] > 0
                   and type(policy['gid']) is int and policy['gid'] > 0, 'nonroot_identity')
    native.require(re.fullmatch(r'orch-r133-node3-[a-f0-9]{32}', policy['unit']), 'unique_own_unit')
    source = Path(plan['source_root'])
    native.require(source.is_absolute() and '..' not in source.parts, 'absolute_source')
    native.require(type(lifetime) is int and lifetime > 0, 'bounded_service_lifetime')
    properties = dict(User=str(policy['uid']), Group=str(policy['gid']), NoNewPrivileges='yes',
        DevicePolicy='strict', CapabilityBoundingSet='', AmbientCapabilities='',
        ProtectControlGroups='yes', RuntimeMaxSec=str(lifetime), TimeoutStopSec='5',
        KillMode='control-group', WorkingDirectory=str(source))
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
               f"/dev/nvidia{policy['minor']} rw", '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit='+policy['unit'],
        *['--property='+key+'='+value for key, value in properties.items()], '--property=DeviceAllow=',
        *['--property=DeviceAllow='+entry for entry in devices], '/usr/bin/env', '-i',
        'PATH=/usr/bin:/bin', 'HOME='+str(BASE), 'CUDA_VISIBLE_DEVICES='+lane['gpu_uuid'],
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH='+str(source), 'HF_HUB_OFFLINE=1',
        'TRANSFORMERS_OFFLINE=1', 'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1',
        'TOKENIZERS_PARALLELISM=false', *command]


def prepare(physical, source, template, startup_base, lease, frozen_cpu, cpu, builder_commit):
    lane = spec(physical)
    source = Path(source)
    expected = BASE/f"orch_r133_node3_{lane['label']}_20260916_attempt1"
    native.require(source == expected/'source1', 'exact_fresh_owned_namespace')
    native.require(not (expected/'run1').exists(), 'never_reset')
    native.require(native.sha(lease) == creative.LEASE_SHA256, 'exact_existing_lease')
    creative.verify_overlay(source, native.read(frozen_cpu))
    test_receipt = native.read(cpu)
    actual = {str(path.relative_to(source)): native.sha(path) for path in source.rglob('*.py')}
    native.require(test_receipt['passed'] is True and test_receipt['source_pins'] == actual,
                   'exact_tested_source_closure')
    plan = deepcopy(native.read(template))
    native.require('authorized_wall_extension' not in plan and 'preupdate_recovery' not in plan,
                   'fresh_plan_only')
    plan.update(seed=0, presleep_variant=lane['replay'],
                compaction_invitation=native.PRESLEEP_INVITATIONS[lane['replay']])
    native.write_once(source/'VARIANT_TEMPLATE.json', plan)
    with (source/'STARTUP.md').open('x') as output:
        output.write(startup_text(Path(startup_base).read_text(), physical, source, expected/'workspace'))
    with (source/'PROGRAMME.md').open('x') as output:
        output.write(programme_text(physical))
    staged = stage(source/'VARIANT_TEMPLATE.json', source, expected/'control1', expected/'run1',
                   source/'STARTUP.md', lease, physical, lane['gpu_uuid'], builder_commit, cpu)
    config, plan = guard.validate(staged['config_path'])
    native.require(plan['context_limit'] == 16384 and plan['segment_tokens'] == 512
                   and plan['readout_revision'] == 2 and plan['max_sleeps'] is None, 'unchanged_presentation')
    config['device_containment'] = dict(minor=device_minor(lane['gpu_uuid']), uid=os.getuid(),
        gid=os.getgid(), unit='orch-r133-node3-'+uuid.uuid4().hex)
    native.write_once(expected/'control1/GUARD_CONTAINED.json', config)
    native.write_once(expected/'control1/PROGRAMME_PROVENANCE.json', dict(lane=lane,
        programme_sha256=native.sha(source/'PROGRAMME.md'), startup_sha256=native.sha(source/'STARTUP.md'),
        cpu_sha256=native.sha(cpu), guard_sha256=native.sha(expected/'control1/GUARD_CONTAINED.json'),
        launch_attempted=False, fresh_release_and_admission_required=True))
    return dict(physical=physical, config=str(expected/'control1/GUARD_CONTAINED.json'), launch_attempted=False)


def verify_containment(config, plan):
    lane = spec(plan['physical'])
    native.require(plan['gpu_uuid'] == lane['gpu_uuid'], 'exact_owned_UUID')
    policy = config['device_containment']
    native.require(os.getuid() == policy['uid'] > 0 and os.getgid() == policy['gid'] > 0, 'nonroot_service')
    native.require(Path('/proc/self/cgroup').read_text().strip() ==
                   '0::/system.slice/'+policy['unit']+'.service', 'own_service_cgroup')
    native.require(device_minor(lane['gpu_uuid']) == policy['minor'], 'unchanged_kernel_minor')
    for path in Path('/proc/self/fd').iterdir():
        try:
            native.require(not os.readlink(path).startswith('/dev/nvidia'), 'no_inherited_GPU_fds')
        except FileNotFoundError:
            pass
    denied = []
    for path in Path('/dev').glob('nvidia[0-9]*'):
        if path.name == 'nvidia'+str(policy['minor']):
            continue
        try:
            descriptor = os.open(path, os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            denied.append(path.name)
        else:
            os.close(descriptor)
            raise ValueError('foreign_device_not_denied')
    native.require(len(denied) == 7, 'all_seven_foreign_minors_denied')
    native.require(os.environ.get('CUDA_VISIBLE_DEVICES') == lane['gpu_uuid'], 'one_GPU_environment')
    return dict(policy=policy, denied_devices=denied, pid=os.getpid(), checked_unix=time.time())


def contained_native(config_path):
    config, plan = guard.validate(config_path)
    attempt = Path(config['attempt_dir'])
    native.write_once(attempt/'CONTAINMENT_VERIFIED.json', verify_containment(config, plan))
    report = native.read(attempt/'ADMISSION.json')
    admitted = native.read(attempt/'ADMISSION_TIME.json')['verified_unix']
    native.require(report['clear'] is True and report['scanner_euid'] == 0
                   and not report['blocking_reasons'] and report['gpu']['uuid'] == plan['gpu_uuid']
                   and report['gpu']['index'] == plan['physical'] and 0 <= time.time()-admitted < 100,
                   'fresh_global_admission')
    remaining = int(plan['hard_end_unix']-time.time()-10)
    native.require(remaining > 10, 'time_for_native_load')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining)+'s', sys.executable,
               '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(config_path)]
    process = None
    try:
        with (attempt/'NATIVE.log').open('x') as output:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            publish_launch(attempt/'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=ticks,
                started_unix=time.time(), admission_verified_unix=admitted,
                admission_sha256=native.sha(attempt/'ADMISSION.json'), guard_sha256=native.sha(config_path),
                command_sha256=native.digest(command), plan_sha256=config['plan_sha256'],
                gpu_uuid=plan['gpu_uuid'], hard_end_unix=plan['hard_end_unix'], no_retry=True,
                containment_sha256=native.sha(attempt/'CONTAINMENT_VERIFIED.json')))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            status = process.wait()
        native.write_once(attempt/'EXIT.json', dict(exit_code=status, finished_unix=time.time()))
        native.require(status == 0, 'contained_native_failed_no_retry')
    except BaseException:
        reap_owned_child(process)
        raise


def supervise(config_path, release_path):
    config, plan = guard.validate(config_path)
    lane = spec(plan['physical'])
    release = native.read(release_path)
    native.require(release['status'] == 'RELEASED' and release['physical'] == lane['physical']
                   and release['uuid'] == lane['gpu_uuid'], 'verified_owned_release_required')
    attempt = Path(config['attempt_dir'])
    (attempt/'DISPATCH_ONCE').mkdir()
    native.write_once(attempt/'RELEASE_BINDING.json', dict(path=str(release_path), sha256=native.sha(release_path)))
    try:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONPATH='+plan['source_root'], sys.executable, '-B', '-m',
            'gpu.orch_r125_continual_guard', 'scan', '--config', str(config_path)]
        report = json.loads(subprocess.check_output(command, text=True, timeout=100))
        native.write_once(attempt/'ADMISSION.json', report)
        native.require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
                       and report['gpu']['uuid'] == lane['gpu_uuid'], 'unchanged_global_exclusive_admission')
        native.write_once(attempt/'ADMISSION_TIME.json', dict(verified_unix=time.time()))
        command = containment_command(plan, config['device_containment'], [sys.executable, '-B', '-m',
            'gpu.orch_r133_node3_programmes', 'contained-native', '--config', str(config_path)],
            max(1, int(plan['hard_end_unix']-time.time())))
        native.write_once(attempt/'CONTAINED_COMMAND.json', dict(command=command, started_unix=time.time()))
        result = subprocess.run(command, check=False)
        native.write_once(attempt/'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
        native.require(result.returncode == 0, 'contained_service_failed_no_retry')
    except BaseException as error:
        native.write_once(attempt/'FAILED.json', dict(error_type=type(error).__name__, error=str(error),
                                                    failed_unix=time.time(), no_retry=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    prepare_parser = commands.add_parser('prepare')
    prepare_parser.add_argument('--physical', type=int, required=True)
    for name in ('source', 'template', 'startup-base', 'lease', 'frozen-cpu', 'cpu'):
        prepare_parser.add_argument('--'+name, type=Path, required=True)
    prepare_parser.add_argument('--builder-commit', required=True)
    supervisor = commands.add_parser('supervise')
    supervisor.add_argument('--config', type=Path, required=True)
    supervisor.add_argument('--release', type=Path, required=True)
    child = commands.add_parser('contained-native')
    child.add_argument('--config', type=Path, required=True)
    arguments = vars(parser.parse_args())
    action = arguments.pop('action')
    if action == 'prepare':
        print(json.dumps(prepare(**arguments)))
    elif action == 'supervise':
        supervise(arguments['config'], arguments['release'])
    else:
        contained_native(arguments['config'])
